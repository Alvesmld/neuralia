# ALVESMLD v11 — publicar para usar no celular

Esta versão adiciona uma interface web responsiva e uma API Python. **A publicação não é automática**: você precisa criar os serviços nas suas próprias contas. A interface pode ficar na Vercel; o motor Python deve ficar em um serviço Python, como Render.

## Estrutura
- `web/`: site responsivo, publicado na Vercel.
- `api_server.py`: API FastAPI que conecta a interface ao gerador v10.
- `requirements-web.txt`: dependências da API web.
- `render.yaml`: configuração inicial para Render.

## Parte 1 — publicar o motor Python no Render
1. Envie a pasta inteira deste projeto para um repositório GitHub privado. Não envie arquivos pessoais ou segredos.
2. No Render, crie um **Web Service** e conecte esse repositório.
3. Root Directory: deixe vazio (raiz do repositório).
4. Build Command: `pip install -r requirements-web.txt`
5. Start Command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
6. Depois que o serviço ficar online, abra `https://SUA-API.onrender.com/health`. Deve retornar JSON com `"status":"ok"`.
7. Copie a URL pública do serviço. Se o serviço gratuito ficar inativo, a primeira chamada pode demorar para acordar.

## Parte 2 — configurar e publicar o site na Vercel
1. Edite `web/config.js` e troque `https://COLOQUE-A-URL-DA-SUA-API.onrender.com` pela URL real da API do passo anterior, sem barra no final.
2. Envie a alteração para o GitHub.
3. Na Vercel, crie um projeto importando o mesmo repositório.
4. Em **Root Directory**, escolha `web`.
5. Framework Preset: `Other`. Build Command pode ficar vazio; Output Directory: `.`.
6. Clique em Deploy. Abra o endereço `*.vercel.app` no computador e no celular.

## Segurança e limitações importantes
- O servidor web **não executa** os testes nem o código que o usuário pediu para gerar. Isso evita executar automaticamente código arbitrário na API pública. A interface mostra os testes como não executados.
- A geração continua baseada nos blueprints locais (calculadora, tarefas, RPG de texto e scaffold genérico); não é um LLM geral e não inventa implementações completas para qualquer descrição.
- O limite de uso incluído é simples e fica na memória do processo; antes de abrir ao público, adicione autenticação, rate limiting no gateway e monitoramento. A configuração CORS inicial usa `*` para facilitar o primeiro deploy; restrinja `ALVESMLD_CORS_ORIGINS` ao domínio da Vercel antes de disponibilizar amplamente.
- Não execute projetos baixados sem revisar o código. Testes do projeto gerado não foram executados no servidor.
- O arquivo `projetos_web/` guarda projetos e ZIPs no disco do serviço. Em instâncias efêmeras, os arquivos podem desaparecer após reinício ou novo deploy. Para uso persistente, configure armazenamento de objetos/bucket.

## Teste local da API
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
uvicorn api_server:app --reload --port 8000
```
Abra `http://127.0.0.1:8000/health`. Para ver a documentação da API, abra `http://127.0.0.1:8000/docs`.

## Teste local da interface
Sirva a pasta `web/` por um servidor estático e configure `web/config.js` para `http://127.0.0.1:8000`. Em produção, use a URL HTTPS da API.
