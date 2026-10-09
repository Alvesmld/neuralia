"""Gera código, verifica sintaxe e permite tentativas limitadas de correção.

O código gerado nunca é executado por este script.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import sys
from codegen.modelo import gerar_codigo, status_modelo
from codegen.qualidade import validar_python

ROOT = Path(__file__).resolve().parent

def gerar_com_validacao(instrucao: str, tentativas: int = 2, max_bytes: int = 1200,
                        temperatura: float = 0.4, checkpoint=None):
    if tentativas < 1 or tentativas > 5:
        raise ValueError("tentativas deve ficar entre 1 e 5")
    pedido = instrucao.strip()
    ultimo = ""
    for tentativa in range(1, tentativas + 1):
        ultimo = gerar_codigo(pedido, checkpoint=checkpoint or status_modelo()["caminho"],
                              max_novos_bytes=max_bytes, temperatura=temperatura)
        resultado = validar_python(ultimo)
        print(f"Tentativa {tentativa}/{tentativas}: {resultado.mensagem}")
        if resultado.valido:
            return ultimo, resultado, tentativa
        pedido = (f"{instrucao}\n\nA tentativa anterior falhou na sintaxe Python: "
                  f"{resultado.mensagem}, linha {resultado.linha}, coluna {resultado.coluna}. "
                  "Reescreva o código completo, corrigindo a sintaxe. Retorne somente código Python.")
    return ultimo, validar_python(ultimo), tentativas

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instrucao", nargs="?", help="O que o código deve fazer")
    parser.add_argument("--tentativas", type=int, default=2)
    parser.add_argument("--max-bytes", type=int, default=1200)
    parser.add_argument("--temperatura", type=float, default=0.4)
    parser.add_argument("--saida", help="Arquivo de saída .py; por padrão cria em saidas/")
    args = parser.parse_args()
    instrucao = args.instrucao or input("Descreva o programa: ")
    status = status_modelo()
    if not status.get("treinado"):
        print("Modelo ainda não treinado. Rode: python treino_codigo.py --passos 100 --contexto 128 --lote 8", file=sys.stderr)
        raise SystemExit(2)
    codigo, resultado, tentativas = gerar_com_validacao(instrucao, args.tentativas,
                                                        args.max_bytes, args.temperatura,
                                                        status["caminho"])
    destino = Path(args.saida) if args.saida else ROOT / "saidas" / f"codigo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(codigo.rstrip() + "\n", encoding="utf-8")
    print(f"\nArquivo salvo: {destino}")
    print(f"Validação sintática: {'OK' if resultado.valido else 'FALHOU'}; tentativas: {tentativas}")
    print("O arquivo NÃO foi executado. Revise-o antes de usar.")
    if not resultado.valido:
        print(f"Erro final: {resultado.mensagem} (linha {resultado.linha}, coluna {resultado.coluna})")
        raise SystemExit(1)
if __name__ == "__main__":
    main()
