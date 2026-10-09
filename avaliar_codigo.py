"""Avaliação inicial do corpus: valida JSONL e sintaxe dos exemplos Python.

Não executa nenhum código. É um teste de qualidade básico, não uma prova
de correção funcional ou de segurança do modelo.
"""
import ast, json, sys
from pathlib import Path
from codegen.modelo import carregar_corpus, DEFAULT_DATASET

def main():
    textos=carregar_corpus()
    erros=[]
    for i, texto in enumerate(textos, 1):
        codigo=texto.split("### CÓDIGO\n",1)[1].split("### FIM",1)[0]
        try: ast.parse(codigo)
        except SyntaxError as exc: erros.append((i,str(exc)))
    print(f"Exemplos carregados: {len(textos)}")
    print(f"Exemplos com sintaxe Python válida: {len(textos)-len(erros)}")
    if erros:
        for i,e in erros: print(f"Exemplo {i}: {e}")
        raise SystemExit(1)
    if not textos: raise SystemExit("Corpus vazio.")
    print("Resultado: verificações sintáticas concluídas. A semântica ainda precisa de testes.")
if __name__=="__main__": main()
