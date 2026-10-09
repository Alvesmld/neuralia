"""Modelo generativo de código ALVESMLD treinável do zero.

Modelo experimental byte-level: não usa pesos pré-treinados, Ollama nem APIs.
A qualidade depende diretamente do corpus e do treinamento realizado.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

try:
    import torch
    from torch import nn
except ImportError:  # permite importar ferramentas de dados sem PyTorch
    torch = None
    nn = None

ROOT = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = ROOT / "modelos" / "alvesmld_codigo.pt"
DEFAULT_DATASET = ROOT.parent / "dados_treinamento" / "codigo.jsonl"

def formatar_exemplo(instrucao: str, codigo: str) -> str:
    return f"### INSTRUÇÃO\n{instrucao.strip()}\n### CÓDIGO\n{codigo.rstrip()}\n### FIM\n"

def carregar_corpus(caminho=DEFAULT_DATASET):
    caminho = Path(caminho)
    exemplos = []
    if not caminho.exists():
        return exemplos
    with caminho.open(encoding="utf-8") as f:
        for n, linha in enumerate(f, 1):
            if not linha.strip():
                continue
            try:
                item = json.loads(linha)
                instrucao, codigo = item["instruction"], item["code"]
                if isinstance(instrucao, str) and isinstance(codigo, str) and instrucao.strip() and codigo.strip():
                    exemplos.append(formatar_exemplo(instrucao, codigo))
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"Registro inválido na linha {n}: {exc}") from exc
    return exemplos

if torch is not None:
    class ModeloCodigo(nn.Module):
        """Pequeno Transformer decoder causal, com vocabulário de bytes (0-255)."""
        def __init__(self, d_model=128, nhead=4, camadas=4, contexto=256, dropout=0.1):
            super().__init__()
            if d_model % nhead:
                raise ValueError("d_model precisa ser divisível por nhead")
            self.contexto = contexto
            self.embedding = nn.Embedding(256, d_model)
            self.posicao = nn.Embedding(contexto, d_model)
            bloco = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4,
                dropout=dropout, batch_first=True, norm_first=True, activation="gelu"
            )
            self.transformer = nn.TransformerEncoder(bloco, num_layers=camadas,
                                                      enable_nested_tensor=False)
            self.norma = nn.LayerNorm(d_model)
            self.saida = nn.Linear(d_model, 256, bias=False)
            self.saida.weight = self.embedding.weight
            self.apply(self._init)
        @staticmethod
        def _init(mod):
            if isinstance(mod, (nn.Linear, nn.Embedding)):
                nn.init.normal_(mod.weight, mean=0.0, std=0.02)
                if isinstance(mod, nn.Linear) and mod.bias is not None:
                    nn.init.zeros_(mod.bias)
        def forward(self, tokens):
            b, t = tokens.shape
            if t > self.contexto:
                raise ValueError(f"Sequência {t} maior que contexto {self.contexto}")
            pos = torch.arange(t, device=tokens.device)
            x = self.embedding(tokens) + self.posicao(pos)[None, :, :]
            mascara = torch.triu(torch.ones(t, t, device=tokens.device, dtype=torch.bool), diagonal=1)
            x = self.transformer(x, mask=mascara)
            return self.saida(self.norma(x))

def selecionar_dispositivo():
    if torch is None:
        raise RuntimeError("PyTorch não instalado. Execute: python -m pip install torch")
    return "cuda" if torch.cuda.is_available() else "cpu"

def gerar_codigo(instrucao: str, checkpoint=DEFAULT_CHECKPOINT, max_novos_bytes=1200,
                 temperatura=0.7, top_k=40):
    """Gera texto com modelo treinado; não executa o código produzido."""
    if torch is None:
        raise RuntimeError("PyTorch não instalado.")
    if not 0.05 <= temperatura <= 2.0:
        raise ValueError("temperatura deve ficar entre 0.05 e 2.0")
    checkpoint = Path(checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(f"Modelo ainda não treinado: {checkpoint}. Rode treino_codigo.py.")
    dados = torch.load(checkpoint, map_location="cpu", weights_only=False)
    cfg = dados["config"]
    modelo = ModeloCodigo(**cfg)
    modelo.load_state_dict(dados["state_dict"])
    device = selecionar_dispositivo()
    modelo.to(device).eval()
    prompt = f"### INSTRUÇÃO\n{instrucao.strip()}\n### CÓDIGO\n".encode("utf-8")
    tokens = torch.tensor(list(prompt), dtype=torch.long, device=device)[None, :]
    if tokens.shape[1] > modelo.contexto:
        tokens = tokens[:, -modelo.contexto:]
    fim = "### FIM\n".encode()
    gerados = []
    with torch.no_grad():
        for _ in range(max_novos_bytes):
            entrada = tokens[:, -modelo.contexto:]
            logits = modelo(entrada)[:, -1, :] / temperatura
            if top_k and 1 < top_k < logits.shape[-1]:
                valores, _ = torch.topk(logits, top_k)
                logits[logits < valores[:, [-1]]] = -float("inf")
            prox = torch.multinomial(torch.softmax(logits, dim=-1), num_samples=1)
            valor = int(prox.item())
            gerados.append(valor)
            tokens = torch.cat([tokens, prox], dim=1)
            if bytes(gerados).endswith(fim):
                break
    texto = bytes(gerados).decode("utf-8", errors="replace")
    return texto.split("### FIM", 1)[0].strip()

def status_modelo(checkpoint=DEFAULT_CHECKPOINT):
    caminho = Path(checkpoint)
    if not caminho.exists():
        return {"treinado": False, "caminho": str(caminho), "mensagem": "Treine o modelo primeiro."}
    if torch is None:
        return {"treinado": True, "caminho": str(caminho), "mensagem": "Checkpoint existe; instale PyTorch para carregar."}
    dados = torch.load(caminho, map_location="cpu", weights_only=False)
    return {"treinado": True, "caminho": str(caminho), "passos": dados.get("passos", 0),
            "perda_final": dados.get("perda_final"), "config": dados.get("config")}
