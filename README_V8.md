# ALVESMLD v8 — Projetos multi-arquivo e testes isolados

A v8 acrescenta uma ponte prática entre a geração de código e projetos com vários arquivos. O motor neural permanece experimental; esta versão **não** transforma um modelo pequeno em uma IA avançada automaticamente.

## Novidades

- `projeto_multiarquivo.py`: monta projetos a partir de um JSON, recusa caminhos absolutos e `..`, limita quantidade/tamanho de arquivos e valida sintaxe dos `.py` antes de gravar.
- `exemplo_projeto.json`: exemplo funcional de projeto com módulo e testes.
- `executar_testes_docker.py`: executa a suíte `unittest` dentro de um container Docker com rede desativada, raiz somente leitura, usuário sem privilégios, limites de memória/CPU/processos e timeout.
- `test_projeto_multiarquivo.py`: testes das validações e criação do projeto.

## Verificações

```bash
source .venv/bin/activate
python -m unittest -v test_codegen.py test_qualidade.py test_estudio_programacao.py test_projeto_multiarquivo.py
python avaliar_codigo.py
```

## Montar um projeto multi-arquivo

```bash
python projeto_multiarquivo.py exemplo_projeto.json
```

O projeto será criado em `projetos_gerados/exemplo_calculadora`. O comando não sobrescreve destinos existentes.

O JSON deve conter `name` e `files`, onde `files` é um mapa de caminho relativo para conteúdo textual. Os caminhos não podem ser absolutos, conter `..` ou apontar para arquivos/pastas ocultos. Limites atuais: 100 arquivos e 1 MB por arquivo.

## Testar em Docker

Instale e inicie Docker e baixe a imagem previamente, por exemplo:

```bash
docker pull python:3.12-slim
python executar_testes_docker.py projetos_gerados/exemplo_calculadora
```

O projeto precisa conter `tests/`. O executor não baixa imagens por conta própria e falha se a imagem não estiver local. A execução fica sem rede e com limites de recursos; ainda assim, containers não são uma fronteira de segurança perfeita para código hostil. Para código realmente não confiável, prefira uma VM descartável e atualizada.

## Fluxo sugerido

1. Treine o modelo com dados revisados e licenciados.
2. Gere um arquivo Python com `gerar_validar.py` e inspecione o resultado.
3. Para projetos de vários arquivos, descreva os arquivos no JSON e monte com `projeto_multiarquivo.py`.
4. Revise o projeto antes de executar testes; use Docker isolado quando disponível.
5. Registre tarefas, resultados e correções para criar um benchmark revisado por humanos.

## Limites conhecidos

- O modelo não planeja automaticamente um JSON multi-arquivo a partir de linguagem natural nesta versão; o formato JSON é a interface de entrada para montagem.
- Validar sintaxe não prova lógica correta, segurança ou qualidade.
- Docker reduz riscos, mas não elimina todas as vulnerabilidades de isolamento.
- Nenhum código gerado deve receber segredos, credenciais ou acesso desnecessário ao sistema.
