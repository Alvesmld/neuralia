# -*- coding: utf-8 -*-
"""
ALVESMLD Neural Core — módulo de rede neural para integrar ao app.py existente.

O que faz:
- Lê pares pergunta/resposta da tabela SQLite `memoria`.
- Treina uma MLP (PyTorch) para estimar a resposta mais provável para uma pergunta.
- Mantém recuperação probabilística TF-IDF como fallback e como sinal adicional.
- Guarda/carrega o modelo treinado em arquivo local.
- Registra feedback no SQLite, sem executar código gerado automaticamente.

Instalação:
    pip install torch scikit-learn pandas

Uso mínimo no app.py:
    from alvesml_neural import treinar_modelo, responder_inteligente

    # Botão "Treinar rede neural":
    info = treinar_modelo("alvesmld_cerebro.db")
    st.success(info["mensagem"])

    # Ao responder uma pergunta:
    resultado = responder_inteligente(pergunta, "alvesmld_cerebro.db")
    resposta = resultado["resposta"]
    # resultado também contém confiança, método e correspondências.

IMPORTANTE:
- Para aprender padrões generalizáveis, é necessário ter exemplos suficientes e variados.
- Com poucos dados, o modelo pode memorizar exemplos e errar. A confiança é uma estimativa,
  não uma garantia de verdade.
- Esta rede neural seleciona respostas já existentes no banco; NÃO é um LLM e não inventa
  programas arbitrários. Para programação, use-a para classificar a intenção e encaminhar
  para geradores/templates de código ou para um modelo generativo separado.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import unicodedata
import time
from typing import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as exc:
    raise ImportError(
        "Dependências ausentes. Execute: pip install torch scikit-learn numpy"
    ) from exc


DEFAULT_DB = os.environ.get("ALVESMLD_DB", "alvesmld_cerebro.db")
MODEL_DIR = Path(os.environ.get("ALVESMLD_MODEL_DIR", "alvesmld_modelo"))
MODEL_FILE = MODEL_DIR / "rede_neural.pt"
META_FILE = MODEL_DIR / "metadados.json"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def normalizar(texto: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "").lower().strip())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^\w\s+#./-]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def conectar(db_path: str | os.PathLike = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=20000")
    return conn


def garantir_tabelas(db_path: str | os.PathLike = DEFAULT_DB) -> None:
    with conectar(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback_respostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pergunta TEXT NOT NULL,
                resposta TEXT NOT NULL,
                avaliacao INTEGER NOT NULL CHECK(avaliacao IN (-1, 1)),
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS estado_modelo (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


class RedePerguntaResposta(nn.Module):
    """MLP que mapeia vetores TF-IDF para classes de respostas conhecidas."""
    def __init__(self, tamanho_entrada: int, tamanho_saida: int):
        super().__init__()
        oculto1 = min(512, max(64, tamanho_entrada // 2))
        oculto2 = min(256, max(32, oculto1 // 2))
        self.rede = nn.Sequential(
            nn.Linear(tamanho_entrada, oculto1),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(oculto1, oculto2),
            nn.ReLU(),
            nn.Dropout(0.10),
            nn.Linear(oculto2, tamanho_saida),
        )

    def forward(self, x):
        return self.rede(x)


@dataclass
class DadosTreino:
    perguntas: list[str]
    respostas: list[str]
    classes: list[str]
    labels: list[int]


def carregar_pares(db_path: str | os.PathLike = DEFAULT_DB) -> DadosTreino:
    with conectar(db_path) as conn:
        # Suporta o esquema usado pelo ALVESMLD.
        # Limite explícito para não tentar transformar dezenas de milhares de linhas
        # em uma matriz densa gigante. Preferimos exemplos recentes e válidos.
        rows = conn.execute("""
            SELECT busca_txt, resposta_txt
            FROM memoria
            WHERE trim(coalesce(busca_txt,'')) <> ''
              AND trim(coalesce(resposta_txt,'')) <> ''
            ORDER BY id DESC
            LIMIT 2500
        """).fetchall()
        # Feedback positivo adiciona exemplos ao treinamento.
        try:
            feedback = conn.execute("""
                SELECT pergunta, resposta FROM feedback_respostas
                WHERE avaliacao = 1
                  AND trim(coalesce(pergunta,'')) <> ''
                  AND trim(coalesce(resposta,'')) <> ''
            """).fetchall()
        except sqlite3.OperationalError:
            feedback = []

    perguntas, respostas = [], []
    for row in rows:
        q, a = str(row[0]).strip(), str(row[1]).strip()
        if q and a:
            perguntas.append(q)
            respostas.append(a)
    for row in feedback:
        q, a = str(row[0]).strip(), str(row[1]).strip()
        if q and a:
            perguntas.append(q)
            respostas.append(a)

    # Remove pares repetidos; isso reduz custo e evita que duplicatas dominem o treino.
    pares_unicos = []
    vistos = set()
    for q, a in zip(perguntas, respostas):
        chave_par = (normalizar(q), a.strip())
        if chave_par[0] and chave_par not in vistos:
            vistos.add(chave_par)
            pares_unicos.append((q, a.strip()))
    perguntas = [p[0] for p in pares_unicos]
    respostas = [p[1] for p in pares_unicos]

    # Uma saída por resposta distinta fica enorme em bases de conversa; manter as
    # 300 respostas mais frequentes torna o classificador treinável em CPU.
    from collections import Counter
    frequencias = Counter(respostas)
    respostas_permitidas = {a for a, _ in frequencias.most_common(200)}
    filtrados = [(q, a) for q, a in zip(perguntas, respostas) if a in respostas_permitidas]
    perguntas = [p[0] for p in filtrados]
    respostas = [p[1] for p in filtrados]
    classes: list[str] = []
    mapa: dict[str, int] = {}
    labels: list[int] = []
    for resposta in respostas:
        chave = resposta.strip()
        if chave not in mapa:
            mapa[chave] = len(classes)
            classes.append(chave)
        labels.append(mapa[chave])
    return DadosTreino(perguntas, respostas, classes, labels)


def treinar_modelo(
    db_path: str | os.PathLike = DEFAULT_DB,
    epocas: int = 60,
    taxa_aprendizado: float = 0.001,
    tamanho_lote: int = 16,
    max_features: int = 12000,
    callback_progresso: Callable[[int, int, float], None] | None = None,
) -> dict[str, Any]:
    """Treina e salva a MLP usando os pares que já estão no SQLite."""
    garantir_tabelas(db_path)
    dados = carregar_pares(db_path)
    n = len(dados.perguntas)
    if n < 4:
        return {
            "ok": False,
            "mensagem": f"Há apenas {n} pares pergunta/resposta. Importe pelo menos 4; idealmente centenas ou milhares de exemplos variados.",
            "amostras": n,
        }
    if len(dados.classes) < 2:
        return {
            "ok": False,
            "mensagem": "O banco tem respostas distintas insuficientes para treinar um classificador. Adicione exemplos com respostas diferentes.",
            "amostras": n,
        }

    # Vocabulário ajustado apenas aos textos de pergunta; a saída são respostas conhecidas.
    # Reduzir vocabulário evita estouro de RAM na matriz densa usada pelo PyTorch.
    max_features = min(int(max_features), 2000)
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=max_features,
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
    )
    x_np = vectorizer.fit_transform(dados.perguntas).toarray().astype("float32")
    y_np = np.asarray(dados.labels, dtype="int64")
    x = torch.tensor(x_np, dtype=torch.float32)
    y = torch.tensor(y_np, dtype=torch.long)

    torch.manual_seed(42)
    modelo = RedePerguntaResposta(x.shape[1], len(dados.classes)).to(DEVICE)
    dataset = TensorDataset(x, y)
    loader = DataLoader(dataset, batch_size=max(1, min(tamanho_lote, n)), shuffle=True)
    otimizador = torch.optim.AdamW(modelo.parameters(), lr=taxa_aprendizado, weight_decay=0.01)
    perda_fn = nn.CrossEntropyLoss()

    modelo.train()
    perdas = []
    epocas_total = max(1, int(epocas))
    inicio_treino = time.time()
    for epoca_atual in range(1, epocas_total + 1):
        total_perda = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            otimizador.zero_grad()
            logits = modelo(xb)
            perda = perda_fn(logits, yb)
            perda.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otimizador.step()
            total_perda += float(perda.item()) * len(xb)
        perdas.append(total_perda / n)
        if callback_progresso is not None:
            try:
                callback_progresso(epoca_atual, epocas_total, float(perdas[-1]))
            except Exception:
                pass

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    # Salvar parâmetros + metadados serializáveis do vectorizer/classes.
    checkpoint = {
        "state_dict": modelo.cpu().state_dict(),
        "input_size": int(x.shape[1]),
        "output_size": len(dados.classes),
        "classes": dados.classes,
        "vectorizer_vocabulary": vectorizer.vocabulary_,
        "vectorizer_idf": vectorizer.idf_.tolist(),
        "vectorizer_params": {
            "ngram_range": [1, 2],
            "max_features": max_features,
            "sublinear_tf": True,
            "strip_accents": "unicode",
            "min_df": 1,
        },
        "amostras": n,
        "epocas": int(epocas),
        "perda_final": round(perdas[-1], 5),
    }
    # Escrita atómica: não deixa checkpoint parcialmente escrito se o processo for interrompido.
    temp_file = MODEL_FILE.with_suffix(MODEL_FILE.suffix + ".tmp")
    torch.save(checkpoint, temp_file)
    os.replace(temp_file, MODEL_FILE)
    with conectar(db_path) as conn:
        conn.execute("""
            INSERT INTO estado_modelo(chave, valor) VALUES('ultimo_treino', ?)
            ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor,
                atualizado_em=CURRENT_TIMESTAMP
        """, (json.dumps({
            "amostras": n,
            "classes": len(dados.classes),
            "epocas": int(epocas),
            "perda_final": round(perdas[-1], 5),
            "arquivo": str(MODEL_FILE),
            "duracao_segundos": round(time.time() - inicio_treino, 2),
        }, ensure_ascii=False),))
    return {
        "ok": True,
        "mensagem": f"Rede neural treinada com {n} exemplos e {len(dados.classes)} respostas possíveis. Perda final: {perdas[-1]:.4f}.",
        "amostras": n,
        "classes": len(dados.classes),
        "perda_final": round(perdas[-1], 5),
        "arquivo": str(MODEL_FILE),
        "duracao_segundos": round(time.time() - inicio_treino, 2),
        "dispositivo": str(DEVICE),
        "nota": "A perda de treino não mede sozinha a qualidade real. Teste com perguntas que não estavam no conjunto.",
    }


def _carregar_modelo() -> tuple[RedePerguntaResposta, TfidfVectorizer, list[str]] | None:
    if not MODEL_FILE.exists():
        return None
    try:
        ckpt = torch.load(MODEL_FILE, map_location="cpu", weights_only=False)
        params = ckpt["vectorizer_params"]
        vectorizer = TfidfVectorizer(
            ngram_range=tuple(params["ngram_range"]),
            max_features=params["max_features"],
            sublinear_tf=params["sublinear_tf"],
            strip_accents=params["strip_accents"],
            min_df=params["min_df"],
            vocabulary=ckpt["vectorizer_vocabulary"],
        )
        # Fit mínimo para reconstruir internamente os atributos do vectorizer.
        # A atribuição explícita preserva o IDF treinado.
        vectorizer.vocabulary_ = ckpt["vectorizer_vocabulary"]
        vectorizer.fixed_vocabulary_ = True
        vectorizer._tfidf.idf_ = np.asarray(ckpt["vectorizer_idf"], dtype=np.float64)
        vectorizer._tfidf.n_features_in_ = len(ckpt["vectorizer_vocabulary"])
        model = RedePerguntaResposta(ckpt["input_size"], ckpt["output_size"])
        model.load_state_dict(ckpt["state_dict"])
        model.eval()
        return model, vectorizer, ckpt["classes"]
    except Exception:
        return None


def buscar_probabilistico(pergunta: str, db_path: str | os.PathLike = DEFAULT_DB, limite: int = 5) -> list[dict[str, Any]]:
    """Fallback de similaridade lexical; não é probabilidade calibrada."""
    with conectar(db_path) as conn:
        rows = conn.execute("""
            SELECT busca_txt, resposta_txt FROM memoria
            WHERE trim(coalesce(busca_txt,'')) <> ''
              AND trim(coalesce(resposta_txt,'')) <> ''
        """).fetchall()
    if not rows:
        return []
    textos = [normalizar(r["busca_txt"]) for r in rows]
    q = normalizar(pergunta)
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        mat = vec.fit_transform(textos + [q])
        scores = cosine_similarity(mat[-1], mat[:-1]).ravel()
    except ValueError:
        return []
    indices = np.argsort(scores)[::-1][:limite]
    return [
        {
            "pergunta": str(rows[i]["busca_txt"]),
            "resposta": str(rows[i]["resposta_txt"]),
            "similaridade": round(float(scores[i]) * 100, 1),
        }
        for i in indices if scores[i] > 0
    ]


def responder_inteligente(
    pergunta: str,
    db_path: str | os.PathLike = DEFAULT_DB,
    minimo_confianca: float = 0.55,
) -> dict[str, Any]:
    """
    Faz inferência neural e cruza com recuperação lexical.
    Retorno: resposta, confianca, metodo, correspondencias, precisa_confirmacao.
    """
    modelo_carregado = _carregar_modelo()
    recuperados = buscar_probabilistico(pergunta, db_path, limite=5)

    neural = None
    if modelo_carregado is not None:
        modelo, vectorizer, classes = modelo_carregado
        try:
            vetor = vectorizer.transform([pergunta]).toarray().astype("float32")
            if vetor.sum() > 0:
                with torch.no_grad():
                    logits = modelo(torch.tensor(vetor, dtype=torch.float32))
                    probs = torch.softmax(logits, dim=1)[0]
                    indice = int(torch.argmax(probs).item())
                    neural = {
                        "resposta": classes[indice],
                        "confianca": float(probs[indice].item()),
                    }
        except Exception:
            neural = None

    melhor_lexical = recuperados[0] if recuperados else None
    # Não escolher resposta neural se a pergunta não tem vocabulário conhecido.
    if neural and neural["confianca"] >= minimo_confianca:
        # Uma correspondência lexical muito forte pode ter precedência.
        if melhor_lexical and melhor_lexical["similaridade"] >= 80:
            resposta = melhor_lexical["resposta"]
            metodo = "recuperação TF-IDF"
            confianca = min(0.99, melhor_lexical["similaridade"] / 100)
        else:
            resposta = neural["resposta"]
            metodo = "rede neural MLP"
            confianca = neural["confianca"]
        return {
            "resposta": resposta,
            "confianca": round(confianca, 3),
            "metodo": metodo,
            "correspondencias": recuperados,
            "precisa_confirmacao": confianca < 0.70,
        }

    if melhor_lexical and melhor_lexical["similaridade"] >= 0.30 * 100:
        return {
            "resposta": melhor_lexical["resposta"],
            "confianca": round(melhor_lexical["similaridade"] / 100, 3),
            "metodo": "recuperação TF-IDF",
            "correspondencias": recuperados,
            "precisa_confirmacao": melhor_lexical["similaridade"] < 55,
        }

    return {
        "resposta": "Ainda não tenho evidência suficiente na minha memória para responder com confiança. Ensine-me com exemplos relevantes ou registre uma resposta correta para esta pergunta.",
        "confianca": 0.0,
        "metodo": "sem correspondência confiável",
        "correspondencias": recuperados,
        "precisa_confirmacao": True,
    }


def registrar_feedback(
    pergunta: str,
    resposta: str,
    util: bool,
    db_path: str | os.PathLike = DEFAULT_DB,
) -> None:
    """Armazena feedback; para incorporar ao treino, treine novamente."""
    garantir_tabelas(db_path)
    with conectar(db_path) as conn:
        conn.execute(
            "INSERT INTO feedback_respostas(pergunta,resposta,avaliacao) VALUES(?,?,?)",
            (pergunta.strip(), resposta.strip(), 1 if util else -1),
        )


def status_modelo() -> dict[str, Any]:
    if not MODEL_FILE.exists():
        return {"treinado": False, "arquivo": str(MODEL_FILE)}
    try:
        ckpt = torch.load(MODEL_FILE, map_location="cpu", weights_only=False)
        return {
            "treinado": True,
            "arquivo": str(MODEL_FILE),
            "amostras": ckpt.get("amostras", 0),
            "respostas_conhecidas": ckpt.get("output_size", 0),
            "epocas": ckpt.get("epocas", 0),
            "dispositivo_treino": str(DEVICE),
            "ultima_modificacao": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(MODEL_FILE.stat().st_mtime)),
            "perda_final": ckpt.get("perda_final"),
        }
    except Exception as exc:
        return {"treinado": False, "arquivo": str(MODEL_FILE), "erro": str(exc)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Treinar e testar o núcleo neural do ALVESMLD")
    parser.add_argument("--db", default=DEFAULT_DB, help="Caminho do SQLite usado pelo app.py")
    parser.add_argument("--treinar", action="store_true", help="Treina a rede neural a partir do SQLite")
    parser.add_argument("--epocas", type=int, default=60)
    parser.add_argument("--pergunta", help="Faz uma pergunta de teste após carregar o modelo")
    args = parser.parse_args()

    if args.treinar:
        print(json.dumps(treinar_modelo(args.db, epocas=args.epocas), ensure_ascii=False, indent=2))
    print(json.dumps(status_modelo(), ensure_ascii=False, indent=2))
    if args.pergunta:
        print(json.dumps(responder_inteligente(args.pergunta, args.db), ensure_ascii=False, indent=2))
