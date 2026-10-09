"""Gera código com o modelo ALVESMLD já treinado."""
import argparse
from codegen.modelo import gerar_codigo, status_modelo

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("instrucao", nargs="?", help="Descrição do código desejado")
    p.add_argument("--max-bytes", type=int, default=1200)
    p.add_argument("--temperatura", type=float, default=0.7)
    args=p.parse_args()
    print(status_modelo())
    instrucao=args.instrucao or input("Descreva o código que deseja gerar: ")
    print("\n--- CÓDIGO GERADO (revise antes de usar) ---\n")
    print(gerar_codigo(instrucao, max_novos_bytes=args.max_bytes, temperatura=args.temperatura))
    print("\n--- Fim. O código não foi executado. ---")
if __name__=="__main__": main()
