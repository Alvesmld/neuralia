# ALVESMLD v11 — Web Ready

A v11 adiciona uma interface web responsiva e uma API para você acessar a ALVESMLD pelo navegador do computador ou do celular.

## Antes de começar
A interface pode ser hospedada na Vercel, mas o motor Python precisa de um servidor Python separado (este projeto usa Render como exemplo). Este ZIP **não publica automaticamente** o sistema nem cria contas/serviços em seu nome.

## Publicação
Siga o guia passo a passo em [`DEPLOY_V11.md`](DEPLOY_V11.md).

- Site: diretório `web/` → Vercel, preset `Other`, sem build command.
- API: raiz do repositório → Render, `pip install -r requirements-web.txt`, `uvicorn api_server:app --host 0.0.0.0 --port $PORT`.
- Após publicar a API, edite `web/config.js` com a URL pública dela e faça novo deploy da Vercel.

## O que está implementado
- Interface responsiva para celular e desktop.
- API FastAPI com verificação de saúde, geração de projetos e download ZIP.
- Lista de arquivos e aviso explícito de limitações.
- O servidor web não executa os testes nem o código gerado.

## Limitações honestas
O motor de geração continua sendo o sistema de blueprints e regras da v10: calculadora, lista de tarefas, RPG de texto e scaffold genérico. Não é um modelo de programação geral. Os testes de cada projeto gerado ficam marcados como não executados pela API. Para um deploy público de produção, adicione autenticação, rate limiting robusto e armazenamento persistente para os ZIPs.
