# ALVESMLD v10 — Planejador e Avaliador

**Nova etapa:** transformar uma descrição em projeto, mapear requisitos, executar os testes do projeto gerado e produzir um relatório verificável.

## Começar no Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python gerar_projeto_v10.py "Crie uma calculadora com soma e divisão"
```

Os projetos ficam em `projetos_gerados/`. Abra `MATRIZ_REQUISITOS.md` para ver o que foi incluído e o que continua pendente; `RELATORIO_QUALIDADE.json` guarda o resultado dos testes.

## Verificar a instalação

```bash
python -m unittest -v test_codegen.py test_qualidade.py test_estudio_programacao.py test_projeto_multiarquivo.py test_gerar_projeto_natural.py test_gerar_projeto_v10.py
```

Veja `README_V10.md` para documentação detalhada, limitações e exemplos.

**Limite importante:** a v10 não é um modelo de linguagem geral. Ela usa blueprints e regras locais herdadas da v9. A memória de experiências é um histórico de resultados, não aprendizado automático dos pesos. Os testes do código gerado são executados localmente; só gere/executa projetos que você confia.
