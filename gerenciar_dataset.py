"""Audita o corpus JSONL e opcionalmente grava uma cópia limpa sem duplicatas."""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from codegen.modelo import DEFAULT_DATASET

def auditar(caminho):
    caminho = Path(caminho)
    linhas = validos = duplicados = 0
    erros, vistos, registros = [], set(), []
    tamanhos = []
    if not caminho.exists():
        raise FileNotFoundError(caminho)
    with caminho.open(encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            if not linha.strip():
                continue
            linhas += 1
            try:
                item = json.loads(linha)
                instrucao, codigo = item.get("instruction"), item.get("code")
                if not isinstance(instrucao, str) or not instrucao.strip() or not isinstance(codigo, str) or not codigo.strip():
                    raise ValueError("campos instruction/code devem ser textos não vazios")
                canonico = json.dumps({"instruction": instrucao.strip(), "code": codigo.strip()}, sort_keys=True, ensure_ascii=False)
                chave = hashlib.sha256(canonico.encode()).hexdigest()
                if chave in vistos:
                    duplicados += 1
                    continue
                vistos.add(chave)
                registros.append({"instruction": instrucao.strip(), "code": codigo.strip()})
                tamanhos.append(len(instrucao) + len(codigo))
                validos += 1
            except (json.JSONDecodeError, ValueError, AttributeError) as exc:
                erros.append(f"linha {numero}: {exc}")
    return {"arquivo": str(caminho), "linhas_lidas": linhas, "registros_validos_unicos": validos,
            "duplicados": duplicados, "erros": erros, "caracteres_medios_por_exemplo": round(sum(tamanhos)/len(tamanhos), 1) if tamanhos else 0,
            "registros": registros}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", default=str(DEFAULT_DATASET))
    p.add_argument("--limpo", help="Grava corpus JSONL limpo em um novo arquivo")
    args = p.parse_args()
    r = auditar(args.dados)
    print(f"Arquivo: {r['arquivo']}\nLinhas: {r['linhas_lidas']}\nExemplos válidos únicos: {r['registros_validos_unicos']}\nDuplicados removíveis: {r['duplicados']}\nMédia de caracteres por exemplo: {r['caracteres_medios_por_exemplo']}")
    for erro in r["erros"]: print("ERRO:", erro)
    if args.limpo:
        destino = Path(args.limpo)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8") as f:
            for item in r["registros"]: f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Corpus limpo salvo em: {destino}")
    if r["erros"]: raise SystemExit(1)
if __name__ == "__main__": main()
