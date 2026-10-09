# ALVESMLD v7 — Ciclo de qualidade para código gerado

A v7 estende o laboratório neural da v6 com ferramentas reais para auditar dados e validar sintaxe de código gerado. Continua sem Ollama, APIs externas ou pesos pré-treinados. O modelo continua experimental e sua qualidade depende dos dados e do treinamento.

## Novidades

- `codegen/qualidade.py`: validação sintática de Python usando AST, com localização de erros.
- `gerar_validar.py`: gera código, valida a sintaxe e, quando falha, faz tentativas limitadas de regeneração com o diagnóstico no prompt. Salva o resultado em `saidas/` ou no caminho passado com `--saida`.
- `gerenciar_dataset.py`: analisa JSONL, identifica linhas inválidas, conta duplicatas exatas e pode gravar uma cópia limpa sem duplicatas.
- `test_qualidade.py`: testes automatizados para a validação e auditoria de dados.

## Instalação e verificações

Ative o ambiente virtual já usado na v6 e, se necessário, instale as dependências:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python gerenciar_dataset.py
python avaliar_codigo.py
python -m unittest -v test_codegen.py test_qualidade.py test_estudio_programacao.py
python -m py_compile codegen/modelo.py codegen/qualidade.py treino_codigo.py gerar_codigo.py gerar_validar.py gerenciar_dataset.py
```

## Auditar e limpar dados

A auditoria padrão não altera o corpus:

```bash
python gerenciar_dataset.py
```

Para gravar um novo arquivo limpo, preservando o original:

```bash
python gerenciar_dataset.py --limpo dados_treinamento/codigo_limpo.jsonl
```

Revise os erros e a origem/licença dos exemplos antes de treinar. A ferramenta remove apenas duplicatas exatas de instrução + código; ela não avalia se o código é correto, seguro ou licenciado.

## Treinar e gerar com validação

Se ainda não tiver um checkpoint treinado:

```bash
python treino_codigo.py --passos 100 --contexto 128 --lote 8
```

Depois:

```bash
python gerar_validar.py "Crie uma função Python que calcule a média de uma lista"
```

Você pode controlar tentativas e destino:

```bash
python gerar_validar.py "Crie uma função que some dois números" --tentativas 3 --saida saidas/soma.py
```

O sistema faz no máximo cinco tentativas. Uma nova tentativa não garante correção: o modelo pequeno pode ignorar o diagnóstico ou repetir o erro. O script não executa o código produzido.

## Limites de segurança e qualidade

- `ast.parse` verifica sintaxe, não comportamento, lógica, desempenho ou segurança.
- Não existe sandbox de execução nesta versão. Não execute código gerado no sistema principal, com credenciais ou privilégios elevados.
- O corpus de demonstração é pequeno. O gerador byte-level pode produzir texto repetitivo ou inválido e não equivale a uma IA de programação avançada.
- A próxima etapa possível é montar um benchmark de tarefas com testes esperados revisados por humanos, métricas de pass@k e execução em contêiner realmente isolado, com rede desativada, limites de CPU/memória e usuário sem privilégios.
