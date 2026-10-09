# ALVESMLD v9 — Planejamento de projetos por linguagem natural

A v9 acrescenta uma camada que recebe uma descrição em português, seleciona um blueprint, gera uma especificação de múltiplos arquivos, valida a sintaxe e monta um projeto com documentação, plano e testes.

## Executar

```bash
source .venv/bin/activate
python -m unittest -v test_codegen.py test_qualidade.py test_estudio_programacao.py test_projeto_multiarquivo.py test_gerar_projeto_natural.py
```

## Gerar projetos a partir de uma descrição

```bash
python gerar_projeto_natural.py "Crie uma calculadora com soma, subtração, multiplicação e divisão"
python gerar_projeto_natural.py "Quero uma lista de tarefas para adicionar, listar e remover tarefas" --nome minhas_tarefas
python gerar_projeto_natural.py "Crie um RPG de texto com combate por turnos"
```

Para interagir pelo terminal sem passar a descrição como argumento:

```bash
python gerar_projeto_natural.py
```

Para ver os blueprints disponíveis:

```bash
python gerar_projeto_natural.py --listar-blueprints
```

Os projetos são criados em `projetos_gerados/`. O gerador não sobrescreve pastas existentes. Cada projeto inclui `app.py`, `tests/test_app.py`, `README.md` e `PLANO.md`. Uma especificação JSON também é preservada para auditoria.

## O que funciona nesta versão

- Classificação por regras de três tipos conhecidos: calculadora, lista de tarefas e mini RPG de terminal.
- Blueprint genérico para outras descrições, com o pedido original preservado e um scaffold explicitamente marcado como incompleto.
- Identificação de algumas necessidades que exigem trabalho adicional, como interface gráfica, web, banco de dados e autenticação.
- Validação de caminhos, limites e sintaxe usando o montador da v8.
- Testes automáticos gerados junto do projeto.

## Limites importantes

Esta camada ainda **não é um modelo generativo geral que compreende e implementa qualquer software**. A seleção é baseada em regras e os tipos conhecidos usam blueprints escritos previamente. Para descrições fora desses casos, o sistema cria um scaffold e um plano, não uma implementação inventada. O modelo neural experimental da v6–v8 ainda não está integrado como planejador confiável. Não use código gerado sem revisão e testes; sintaxe válida não prova correção nem segurança.

## Próximo passo técnico

Construir um planejador avaliável com exemplos de pedidos e especificações revisadas, pontuação de requisitos cobertos, validação estrutural e integração opcional do modelo neural apenas quando houver benchmark que demonstre ganho real.
