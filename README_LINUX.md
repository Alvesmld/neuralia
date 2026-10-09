# ALVESMLD — Linux + VS Code

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra o endereço local indicado pelo Streamlit. Para abrir projetos no VS Code, o comando `code --version` precisa funcionar no mesmo ambiente Linux que executa o Streamlit. VSCodium também é aceito via `codium`.

## Novo motor composicional

Na seção **Estúdio de Programação**, descreva o projeto e escolha a tecnologia. O motor compõe projetos a partir de capacidades: interface Tkinter ou terminal, camada de dados, persistência JSON e testes; também cria bases iniciais Web, Flask e Flutter. É local, não usa Ollama nem APIs externas.

**Limitação honesta:** não é um modelo generativo de linguagem. Não consegue criar qualquer programa arbitrário apenas com texto; para isso será necessário desenvolver/treinar um modelo generativo de código ou usar outro motor generativo. O treinamento neural de perguntas e respostas do ALVESMLD não é, por si só, um gerador de código.

## Segurança

Revise o código gerado antes de executá-lo. O botão de execução local só executa `main.py` após autorização explícita, com limite de 10 segundos. Não execute código desconhecido.

## Testes do motor

```bash
python -m unittest -v test_estudio_programacao.py
python -m py_compile app.py alvesmld_neural.py estudio_programacao.py
```

Se o projeto já possui um banco SQLite, faça backup antes de substituir arquivos da aplicação.


## ALVESMLD v6 — Modelo generativo de código

Foi adicionado um laboratório experimental de geração neural treinada do zero. Consulte `README_CODEGEN_LINUX.md` para instalação, treinamento, geração, avaliação e limitações. Comandos iniciais: `python avaliar_codigo.py`, `python -m unittest -v test_codegen.py` e `python treino_codigo.py --passos 100 --contexto 128 --lote 8`.
