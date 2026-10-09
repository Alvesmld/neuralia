# ALVESMLD v6 — Laboratório de IA Generativa de Código (Linux)

Esta versão preserva o motor composicional existente e adiciona um **modelo experimental Transformer treinado do zero**. Ele usa PyTorch, embeddings de bytes e atenção causal; não carrega pesos pré-treinados e não precisa de Ollama nem de API para treinar/gerar.

## O que foi adicionado
- `codegen/modelo.py`: arquitetura neural, formato do corpus, geração e status do checkpoint.
- `dados_treinamento/codigo.jsonl`: 30 exemplos iniciais em português e Python.
- `treino_codigo.py`: treinamento do modelo desde pesos aleatórios.
- `gerar_codigo.py`: interface de terminal para gerar código.
- `avaliar_codigo.py`: valida a sintaxe dos exemplos do corpus sem executar código.
- `test_codegen.py`: testes do formato e carregamento do conjunto de dados.

## Instalação no Linux

Dentro da pasta `ALVESMLD_v2`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se você já tem um ambiente virtual da versão anterior, pode reutilizá-lo. PyTorch pode ser pesado para baixar; em CPU, o treinamento será mais lento.

## Passo 1 — verificar os exemplos e os testes

```bash
python avaliar_codigo.py
python -m unittest -v test_codegen.py
python -m unittest -v test_estudio_programacao.py
python -m py_compile codegen/modelo.py treino_codigo.py gerar_codigo.py avaliar_codigo.py
```

## Passo 2 — treinar seu próprio modelo

Comece com um treino curto para confirmar que tudo funciona:

```bash
python treino_codigo.py --passos 100 --contexto 128 --lote 8
```

Depois tente um treino maior:

```bash
python treino_codigo.py --passos 1500 --contexto 256 --lote 16
```

O modelo inicial é pequeno e o corpus de demonstração também. É esperado que o primeiro resultado seja limitado, repetitivo ou incorreto. Isso é normal para um modelo treinado do zero com poucos exemplos. Não interprete uma perda menor como prova de que o código está correto.

O checkpoint é criado em `codegen/modelos/alvesmld_codigo.pt`. Não foi incluído no ZIP porque precisa ser produzido no seu computador durante o treinamento.

## Passo 3 — gerar código

Depois de treinar:

```bash
python gerar_codigo.py "Crie uma função Python que calcule a média de uma lista"
```

Ou inicie o modo interativo:

```bash
python gerar_codigo.py
```

O gerador **apenas imprime o texto**. Ele não executa automaticamente o código criado.

## Como ensinar mais coisas ao ALVESMLD

Adicione linhas JSONL a `dados_treinamento/codigo.jsonl`, uma por exemplo:

```json
{"instruction":"Crie uma função Python que conte vogais","code":"def contar_vogais(texto):\n    return sum(1 for c in texto.lower() if c in 'aeiou')"}
```

Boas práticas:
1. Use exemplos que você tem permissão para utilizar.
2. Escreva instruções claras e códigos completos, consistentes e revisados.
3. Inclua casos comuns, casos extremos, tratamento de erros e testes.
4. Remova segredos, tokens, senhas, dados pessoais e código proprietário sem autorização.
5. Faça backup do corpus e registre de onde cada conjunto veio.
6. Rode o treinamento novamente depois de alterar os dados.

**Importante:** o corpus de 30 exemplos serve para validar o pipeline, não para ensinar Python de forma abrangente. Para melhorias reais, monte um corpus maior, licenciado e de alta qualidade; separe dados de treino e avaliação por projeto/fonte, evitando duplicatas entre os conjuntos.

## Limites atuais e próximos marcos

Esta versão é um primeiro modelo generativo real, mas **não é uma IA geral nem um modelo de programação competitivo**. O vocabulário é byte-level, o contexto é curto e não há fine-tuning de um modelo pré-treinado. Ele pode inventar APIs, produzir sintaxe inválida ou não seguir a instrução.

Próximas melhorias recomendadas:
- coletor e validador de dataset com proveniência/licenças;
- conjunto de avaliação separado, com testes unitários de tarefas;
- avaliação de sintaxe, execução em subprocesso isolado e limites de recursos;
- geração em múltiplos arquivos e ciclos de corrigir/testar;
- checkpoints, retomada de treino, logs e early stopping;
- tokenizer de código e arquitetura maior quando houver hardware/dados adequados;
- integração visual ao Estúdio após avaliar a estabilidade do módulo.

## Segurança

Nunca execute código gerado diretamente no seu sistema principal ou com privilégios de administrador. Revise o código e teste em ambiente isolado, sem credenciais e sem acesso desnecessário a arquivos ou rede. `avaliar_codigo.py` só analisa sintaxe; não é sandbox nem auditor de segurança.
