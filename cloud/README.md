# NavixX Cloud 0.3.0-alpha.2 — fundação multiusuário

**Estado: desenvolvimento. NÃO é um instalador pronto e NÃO existe ainda um plugin
público funcionando.** O NavixX Desktop 0.2.11 do proprietário permanece intocado.
Não anunciar, distribuir ou enviar por e-mail a versão 0.3 como produto final.

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
- **OAuth:** validação JWT com JWKS, emissor, público-alvo, prazo, escopo
  `navix:control` e recurso protegido RFC 9728. Necessita IdP real configurado.
- **Canal WebSocket:** segregação por dispositivo, substituição de sessão,
  limite de tamanho, identificação de respostas, cancelamento em desconexão e
  bloqueio de chamadas simultâneas conflitantes.
- **Windows opcional:** cliente WebSocket com reconexão limitada, verificação da
  sessão local em cada chamada, ponte para o servidor FastMCP em 127.0.0.1,
  revogação que cancela imediatamente o WebSocket e controlador que só liga por
  ação explícita. Por enquanto requer URL de staging configurada e **não inicia
  sozinho**. O instalador 0.2.11 continua usando o túnel anterior.
- **Catálogo preservado:** descrição original do plugin `conectaX` e nomes
  das 44 ferramentas em `MCP_CATALOG.md`.

**Segurança: a rota `/mcp` permanece bloqueada (503) mesmo com token OAuth.**
A rota interna experimental `/api/device/execute` permite **somente `status`**
do dispositivo previamente pareado. Mouse, arquivos e comandos remotos ainda
não são liberados pelo gateway público. Não trate testes de unidade como
prova de acesso remoto ponta a ponta.

## Execução local de testes

- Node em `cloud/`: `npm install` e `npm test`
- Empacotamento Cloudflare sem implantação: `npx wrangler deploy --dry-run`
- Windows em `desktop/`: instalar `requirements.txt`, executar
  `python -m pytest -q tests/test_cloud*.py tests/test_browser_actions.py
  tests/test_browser_real.py`
- GitHub Actions: `.github/workflows/navix-cloud.yml`

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

## Impedimentos reais para a versão instalável

1. Provisionar a conta do projeto no serviço Cloudflare. O cadastro na sessão
   de navegador atual exibiu bloqueio de verificação de segurança; não o contornar.
2. Configurar um provedor OAuth 2.1/OIDC confiável que aceite clientes ChatGPT
   com PKCE/CIMD ou DCR. Nenhuma senha universal ou login falso.
3. Concluir página autenticada para aprovar/revogar pareamento e selecionar
   dispositivo padrão de cada dono; testar dois donos em computadores reais.
4. Implementar e auditar o MCP Streamable HTTP completo, encaminhando as 44
   ferramentas com autorização granular e aprovação contextual de ações sensíveis.
5. Finalizar assistente visual de instalação, domínio público, teste integral
   no Windows e revisão/publicação do plugin; só então produzir o instalador 0.3
   e enviar o link por e-mail.

**Não ativar `/mcp` por simples remoção do 503:** isso exporia execução de
comandos sem os pré-requisitos de segurança acima.
