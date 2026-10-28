# Auditoria NavixX Desktop Cloud — alpha.8

## Falhas reproduzidas / evidências
- No ChatGPT, o plugin NavixX Desktop Cloud aparecia instalado, mas a conversa escolheu a ferramenta `status` do plugin **conectaX**. A presença do plugin na lista não prova inicialização/autorização MCP.
- A ferramenta `status` era genérica e idêntica à do conectaX. **Não é possível controlar a escolha de ferramentas do ChatGPT pelo aplicativo Windows.** O conector Cloud precisa anunciar ferramentas com nomes e descrições inequívocas.
- O gateway antes respondia 503 antes de fornecer desafio OAuth quando a variável de controle estava desativada; isso bloqueava a autorização e ocultava a causa.
- O servidor remoto e o cliente Windows têm estados diferentes: MCP local pronto não comprova WebSocket; WebSocket ativo não comprova comando executado.
- Cloudflare `navixx-cloud-staging` tem `NAVIX_PUBLIC_CONTROL=enabled` (constatado na conta em 2026-10-28), sem canary no ambiente consultado. O README antigo descrevia uma configuração anterior. **Publicação não equivale a teste real de controle.**

## Ajustes no ramo
1. Um `navixx_cloud_connection_status` somente leitura, com nome inequívoco, informa: OAuth válido, vínculo, liberação do gateway, canal ativo e ausência de prova de chamada Windows. Não envia comandos ao PC.
2. A descoberta OAuth e a inicialização MCP continuam disponíveis mesmo se o controle remoto estiver desabilitado; nesse caso apenas o diagnóstico aparece. Chamadas de controle são rejeitadas no servidor.
3. Quando o dispositivo responde com erro, o plugin devolve falha explicativa e categoria segura em vez de esconder o motivo.
4. Timeout de consulta remota `status` reduzido para 8 s; outras chamadas permanecem com limite de 30 s.
5. Plugin recebe descrição específica, distinguindo-o do conectaX. Ações remotas seguem exigindo vínculo OAuth e sessão local.
6. Testes automatizados cobrem o diagnóstico exclusivo, ausência de comandos quando bloqueado e catálogo 45 vs. 44 ferramentas.

## Critérios objetivos pendentes antes de declarar pronto
- Validar OAuth no próprio ChatGPT: 401 + WWW-Authenticate → autorização por código → troca PKCE → `tools/list` carregado.
- Em **Windows real**: chamar `navixx_cloud_connection_status`, executar `status` exclusivamente pelo NavixX Cloud, encerrar e reabrir chat, validar reconexão e revogação.
- Validar atualização do plugin instalado: alterar fonte GitHub **não atualiza sozinho** a instalação do ChatGPT.
- Revisão de segurança antes de abertura indiscriminada: especialmente PowerShell, escrita/remoção de arquivos, limites de sessão, observabilidade e auditoria.
- Não divulgar garantia de conexão contínua se o Windows estiver desligado, internet indisponível ou OAuth revogado.

**Nenhuma alteração foi feita no ConectaX antigo.**

## Verificação externa automatizada
O fluxo de CI faz testes sem credenciais contra o servidor de staging para validar a disponibilidade HTTPS, descoberta OAuth, desafio 401 e página de autorização. Não envia comandos ao Windows nem utiliza códigos temporários reais.
