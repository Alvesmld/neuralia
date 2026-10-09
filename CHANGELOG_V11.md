# ALVESMLD v11

- Interface web responsiva para computador e celular.
- Tela de criação com exemplos rápidos, contador de caracteres, estado de conexão, resumo dos arquivos e download ZIP.
- API FastAPI para geração e download dos projetos.
- Endpoint `/health` para monitoramento.
- Limite básico de chamadas por IP e validação de identificadores de download.
- O servidor web não executa os testes/código do projeto gerado.
- Guias para publicar a API no Render e a interface na Vercel.

## Limitações preservadas
A lógica de geração continua sendo baseada em regras e blueprints da v10. A versão web não adiciona um modelo geral de programação nem autenticação de usuário persistente.
