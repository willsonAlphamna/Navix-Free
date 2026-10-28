# NavixX Cloud 0.3.0-alpha.3 — piloto isolado

**Estado: pré-lançamento técnico. Ainda não existe plugin público funcionando.**
O NavixX Desktop 0.2.11 permanece intacto. O servidor de testes responde em
https://navixx-cloud-staging.navixx-alfamna.workers.dev/healthz, mas `/mcp`
continua desativado (503). Não anunciar a versão 0.3 como produto final.

## Objetivo

Uma única integração MCP pública no ChatGPT, compatível com múltiplos computadores
e proprietários, para que cada usuário final **não precise** criar túnel individual,
chave da Plataforma OpenAI ou plugin privado. A pessoa deverá apenas instalar o
programa, autorizar as permissões no próprio Windows, vincular o dispositivo com
código temporário e entrar na sua conta para consentir com o plugin. Essa etapa de
consentimento pessoal não pode ser ignorada por instalador algum.

## Implementado nesta branch

- **Identidade individual:** Windows gera ID aleatório e segredo por dispositivo.
  O arquivo local é cifrado via DPAPI, vinculado ao usuário do Windows. Não usar a
  chave Runtime OpenAI do proprietário nem mandar credenciais por e-mail.
- **Pareamento no backend:** código de seis dígitos (120 segundos), cinco
  tentativas, SHA-256 dos códigos/segredos, dispositivo por dono verificado,
  persistência isolada em Durable Object SQLite e revogação.
- **OAuth:** servidor OAuth 2.1 próprio, fluxo authorization-code com PKCE S256,
  metadados de descoberta, código do dispositivo exibido pelo Windows, tokens
  individuais, renovação e revogação. O fluxo real no ChatGPT ainda requer teste.
- **Canal WebSocket:** segregação por dispositivo, substituição de sessão,
  limite de tamanho, identificação de respostas, cancelamento em desconexão e
  bloqueio de chamadas simultâneas conflitantes.
- **Windows opcional:** cliente WebSocket com reconexão limitada, verificação da
  sessão local em cada chamada, ponte para FastMCP em 127.0.0.1 e controlador
  que só liga por ação explícita. O painel tem os botões **Vincular ao ChatGPT**
  e **Reconectar nuvem**. O instalador de preview 0.3 usa diretório, identidade
  e perfil próprios, sem substituir o NavixX 0.2.11.
- **MCP real:** rota Streamable HTTP com inicialização, catálogo das 44 ferramentas,
  validação de entradas e encaminhamento via WebSocket, ainda bloqueada no
  servidor público até a validação de execução no Windows e revisão de risco.
- **Implantação:** Cloudflare Worker com Durable Objects SQLite provisionado,
  autenticação, pareamento, WebSocket e revogação testados ao vivo usando um
  dispositivo simulado. 51 testes Node passaram na branch de desenvolvimento.
- **Catálogo preservado:** descrição original do plugin `conectaX` e nomes
  das 44 ferramentas em `MCP_CATALOG.md`.

**Segurança: a rota `/mcp` permanece bloqueada (503) mesmo com token OAuth.**
Mouse, arquivos e comandos remotos não estão liberados pelo gateway público.
Os testes de pareamento e transporte não constituem prova de execução remota no Windows.

## Execução local de testes

- Node em `cloud/`: `npm install` e `npm test`
- Empacotamento Cloudflare sem implantação: `npx wrangler deploy --dry-run`
- Windows em `desktop/`: instalar `requirements.txt`, executar
  `python -m pytest -q tests/test_cloud*.py tests/test_browser_actions.py
  tests/test_browser_real.py`
- Testes ao vivo seguros: `NAVIX_LIVE_STAGING_URL=https://navixx-cloud-staging.navixx-alfamna.workers.dev node live-smoke.mjs`
- GitHub Actions: `.github/workflows/navix-cloud.yml` e
  `.github/workflows/navix-cloud-preview-windows.yml`.

## Escolha da infraestrutura

O GitHub armazena gratuitamente código, histórico, CI e instaladores; ele **não**
funciona como servidor WebSocket/MCP com estado e autenticação. A conta Vercel
do projeto já está acessível e suas Functions suportam WebSockets; contudo,
conexões de diferentes instâncias exigem armazenamento/coordenação externos
(e há duração máxima por conexão). Como Cloudflare Durable Objects com SQLite
está disponível no plano gratuito, mantivemos a arquitetura de relay por
dispositivo na Cloudflare — sujeita a limites de uso.

Documentações:
- https://developers.cloudflare.com/durable-objects/platform/pricing/
- https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/
- https://vercel.com/docs/functions/websockets
- https://developers.openai.com/plugins/build/mcp-server
- https://developers.openai.com/plugins/build/auth

## Pendências antes da publicação pública

1. Comprovar as chamadas remotas com um Windows real e consentimento explícito,
   incluindo revogação, expiração e limites por ferramenta.
2. Revisar o risco das ferramentas de arquivo e PowerShell e limitar tentativas
   e criação de dispositivos para não gerar custos ou abuso público.
3. Conectar o OAuth na interface real de plugins do ChatGPT; obter revisão e
   publicar o conector único. Os usuários ainda precisarão consentir na conta.
4. Acompanhar a compilação/instalação/desinstalação do instalador isolado e
   disponibilizar um binário testado (não assinado, com SHA-256).
5. Para vários PCs da mesma conta ChatGPT, criar seletor de dispositivos e
   autenticação de titular independente de cada computador.

**Não ativar `/mcp` por simples remoção do 503:** isso exporia execução de
comandos sem os pré-requisitos de segurança acima.
