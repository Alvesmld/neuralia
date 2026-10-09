# ALVESMLD v10 — Planejador, rastreamento e avaliação

A v10 evolui a v9 com uma matriz de requisitos rastreável, execução dos testes gerados, relatório de qualidade em JSON e registro de experiências locais para acompanhar resultados entre execuções.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Se já estiver usando o ambiente virtual de uma versão anterior, confirme que ele contém as dependências do projeto.

## Gerar e avaliar um projeto

```bash
python gerar_projeto_v10.py "Crie uma calculadora com soma e divisão"
python gerar_projeto_v10.py "Crie um site com login e banco de dados SQLite" --nome portal_exemplo
```

A saída fica em `projetos_gerados/`. Cada projeto inclui `MATRIZ_REQUISITOS.md` e `RELATORIO_QUALIDADE.json`. Requisitos detectados que não estejam implementados aparecem como pendentes, não como concluídos.

Para desativar a execução dos testes do projeto gerado:

```bash
python gerar_projeto_v10.py "Crie uma calculadora" --sem-testes
```

## Testes da versão

```bash
python -m unittest -v test_codegen.py test_qualidade.py test_estudio_programacao.py test_projeto_multiarquivo.py test_gerar_projeto_natural.py test_gerar_projeto_v10.py
```

## O que a v10 faz de verdade

- Reutiliza os blueprints locais da v9.
- Detecta alguns requisitos transversais (interface web/gráfica, persistência, autenticação, exportação e integração) e registra como pendentes quando não implementados.
- Executa `unittest` do projeto gerado em subprocesso com limite de tempo e salva o resultado.
- Produz um relatório de arquivos, testes e requisitos; registra cada execução em `memoria_experiencias.jsonl`.

## Limites

Esta versão não aprende automaticamente novos algoritmos nem altera pesos neurais. A memória é um histórico de experiências, não treinamento de modelo. A avaliação usa testes fornecidos pelo próprio blueprint; passar nos testes não prova correção completa ou segurança. Os testes de projeto gerado são executados localmente no mesmo usuário do processo, não em sandbox isolado. Não execute projetos não confiáveis nesta etapa.
