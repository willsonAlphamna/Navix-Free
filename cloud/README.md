# NavixX Cloud — protótipo de fundação 0.3.0-alpha

Status: **desenvolvimento, ainda NÃO conectado ao ChatGPT e NÃO autorizado para acesso remoto público**.

## Objetivo

Permitir que cada pessoa instale NavixX Desktop sem criar por conta própria um Secure MCP Tunnel, chave Runtime ou plugin privado. O **plugin público único** deverá usar MCP por HTTPS e OAuth 2.1, com usuário identificado e roteamento exclusivo ao dispositivo pareado. Consentimento do ChatGPT e autorização no Windows continuam obrigatórios.

O app Windows 0.2.11 e seu túnel privado continuam intactos enquanto este sistema é desenvolvido. Não publicar a 0.3.0 como estável nem enviar instalador final antes do teste com serviço hospedado, login real e dois computadores de donos diferentes.

## O que existe nesta etapa

- Módulo de domínio `src/pairing.mjs` com registro efêmero de dispositivos, códigos de pareamento de seis dígitos e prazo curto, bloqueio de reutilização, limite de tentativas, isolamento de identidade, autorização granular e revogação.
- Testes automáticos `tests/pairing.test.mjs` para isolamento, expiração, falhas, permissões e revogação.
- Inventário `MCP_CATALOG.md` da descrição e das 44 ferramentas atuais.
- Verificador de JWT OAuth em `src/auth.mjs`, com rejeição de assinatura adulterada, escopo insuficiente, emissor ou audiência errados.
- Worker Cloudflare em `src/worker.mjs` com Durable Object e WebSocket por usuário/dispositivo. **A rota `/mcp` permanece bloqueada (HTTP 503)** até a autenticação, pareamento e controle completos.
- GitHub Actions executa testes de isolamento e `wrangler deploy --dry-run`, sem publicar nada.

**Importante:** este registro é deliberadamente apenas memória de processo e **não pode** ser implantado diretamente como serviço público multi-instância. A próxima etapa deve persistir o pareamento em Durable Objects/SQLite com limites distribuídos e auditoria, integrá-lo a uma identidade OAuth REAL e ao cliente Windows; o Worker já valida JWT no gateway, mas não há provedor configurado nem despacho remoto de comandos. Nenhuma rota pública de controle está liberada. Os campos `ownerId` usados nos testes são identidades já verificadas em nível superior; **nunca** aceitar um `ownerId` enviado sem autenticação pelo cliente.

## Arquitetura de produção prevista

1. **GitHub:** código, CI, instalador Windows e site estático.
2. **Identidade:** provedor OAuth/OIDC confiável, consentimento por conta, JWT validado com JWKS, `iss`, `aud`, prazo e escopos.
3. **API MCP HTTPS:** plugin público único; autorização do próprio usuário para operar somente os seus dispositivos. Não compartilhar conta, credencial ou dispositivo.
4. **Relay em Cloudflare Durable Objects:** conexão WebSocket de saída de cada Windows; estado individual por usuário/dispositivo, expiração e reconexão sem abrir portas no roteador.
5. **Agente Windows:** cria identidade local, guarda segredo com proteção Windows, confirma pareamento e mantém permissões. `PARAR ACESSO` precisa revogar a sessão remotamente e localmente.
6. **Segurança:** ações irreversíveis pedem confirmação contextual; registro de auditoria sem conteúdo, credenciais ou capturas; limitação de taxa, teste de intrusão e revisão antes de uso público.

## Critérios antes de oferecer download público

- [ ] Serviço Cloudflare hospedado numa conta do projeto, HTTPS estável e domínio configurado.
- [ ] Autenticação OAuth 2.1 real compatível com ChatGPT, com confirmação do titular da conta.
- [ ] Identidade do agente Windows criptografada, pareamento e reconexão reais.
- [ ] Pelo menos dois donos/dispositivos diferentes testados contra acesso cruzado.
- [ ] 44 ferramentas MCP preservadas, porém sujeitas a sessão/escopo e confirmação sensível.
- [ ] Windows CI, instalação limpa, atualização e desinstalação aprovados.
- [ ] Assinatura, política de privacidade, termos, aprovação de plugin público e controles de abuso.

### Fontes oficiais

- https://developers.openai.com/plugins/build/mcp-server
- https://developers.openai.com/plugins/build/auth
- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/durable-objects/best-practices/websockets/
