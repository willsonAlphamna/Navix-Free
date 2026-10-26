# NavixX público — conexão em poucos cliques (proposta arquitetural)

Este documento registra o requisito do proprietário: **quem instala o NavixX não deve
abrir PowerShell, criar perfis YAML, procurar portas locais nem copiar tokens Bearer**.

## O que o piloto atual automatiza

- Empacota o `tunnel-client` oficial com SHA-256 verificado.
- Pede ID de túnel e chave própria **uma vez** no assistente gráfico, valida com `doctor`
  e executa `run` em processo separado; tenta recuperar falhas e mudança de porta.
- Pode guardar a chave com DPAPI no usuário Windows, somente com consentimento explícito.
- Só inicia acesso remoto depois de autorização local; PARAR ACESSO revoga o token e
  encerra o cliente de túnel. Nenhuma chave do desenvolvedor é embutida.
- A etapa de consentimento para instalar/vincular o plugin dentro do ChatGPT ainda
  precisa ser realizada pelo titular da conta. É imposição de segurança da plataforma.
- A candidata **0.2.8** adiciona login **local**, trava do painel, cofre DPAPI com senha
  para revelação de chave, ilustrações no assistente e links diretos à Plataforma.
  Esse login **não** é autenticação de conta pública nem substitui OAuth.

## Requisitos registrados para as próximas versões

| Pedido do proprietário | Situação e aceitação |
| --- | --- |
| Instalar e conectar sem comandos | Instalador e cliente de túnel incorporados; a criação de identidade OpenAI ainda é manual. Aceitar somente com teste de conta nova sem PowerShell. |
| Recuperação automática de falhas | Retry e watchdog locais existem; testar queda de internet, reinicialização do túnel e proteção contra loops. |
| Downloads, arquivos e comandos | Ferramentas existem; em 25/10/2026 um download HTTPS para pasta temporária foi validado, lido e removido. Testar também download de navegador, conflitos e limites. |
| Permissões, auditoria e proteção de credenciais | Permissões e logs redigidos existem. 0.2.8 introduz login local e cofre. Faltam auditoria independente, cenários multiusuário e atualização assinada. |
| Produto público profissional | Idiomas PT-BR/EN/ES, telas e instalador existem. Faltam contas online, backend multiusuário, assinatura do EXE e homologação de PC limpo. |

Nunca promover um recurso de **implementado** para **homologado** sem um teste real no
Windows instalado, com registro de versão, caminho de teste e resultado observável.

**Isso é uma melhoria para uso privado e pilotos, não uma solução pública definitiva.**
O Secure MCP Tunnel é documentado para servidores privados/testes e não satisfaz os
requisitos de distribuição pública de plugins.

## Arquitetura proposta para v1.0 pública

1. **Instalar:** aplicativo assinado; componentes incluídos; proteção do Windows intacta.
2. **Entrar:** botão único `Conectar ao ChatGPT`; login por provedor de identidade
   confiável (OAuth/OIDC) em navegador seguro; nenhuma API key da OpenAI solicitada
   ao consumidor final.
3. **Parear dispositivo:** backend Navix Cloud gera desafio de curta duração,
   confirmado pelo proprietário no Windows. A pessoa vê seu computador, identidade
   e permissões solicitadas antes de permitir a conexão.
4. **Canal de transporte:** agente Windows faz conexão **de saída** por TLS a um
   relay HTTPS administrado; não abre porta de entrada no roteador. Identidade e
   autorização são individualizadas por usuário/dispositivo, sem token mestre comum.
5. **Plugin ChatGPT:** endpoint HTTPS estável próprio com OAuth 2.1 e validação de
   origem/mTLS da OpenAI; cada solicitação é roteada apenas para o dispositivo
   pareado daquele usuário. Não conceder acesso de um computador a outra conta.
6. **Autorização de recursos:** navegador, desktop, arquivos e comandos com escopos
   independentes; operações de alto impacto exigem confirmação contextual quando
   pertinente. Não aceitar acesso completo por padrão.
7. **Operação:** indicador ativo, lista de dispositivos, PARAR ACESSO e REVOGAR TODOS;
   watchdog, atualização assinada, logs redigidos, limite de taxa, bloqueio de
   solicitações após perda de identidade, auditoria e testes de intrusão.
8. **Distribuição:** testes Windows 10/11 e idiomas PT-BR/EN/ES, assinatura
   Authenticode, política de privacidade, termos e retenção limitada de dados.

## Critérios de aceitação público

- Novo usuário, PC limpo, sem Python nem ferramentas de desenvolvimento:
  instalação → login → confirmação de pareamento → teste de leitura em ChatGPT.
- A UI não pede `tunnel_id`, API key, token Bearer, PowerShell ou configuração de porta.
- Segunda abertura e quedas de rede recuperam conexão autorizada sem novo terminal.
- Sessão expirada, conta desvinculada ou PARAR ACESSO impedem novas ferramentas.
- Dois usuários/dispositivos não conseguem acessar recursos um do outro; validação
  com testes automatizados e revisão independente de segurança.
- Acesso de terceiros exige conta, consentimento e identidade própria; nunca
  compartilhar a conta/túnel do proprietário com todos que instalarem.

## Dependências ainda não providas

Hospedagem HTTPS, banco/identidades, domínio, aprovação da integração pública,
infraestrutura de relay, testes externos e certificação/assinatura do instalador.
Esses recursos podem gerar custo mensal e obrigações operacionais. O NavixX não
deve anunciar conexão pública `um clique` até existir essa infraestrutura real.

Fontes oficiais:

- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://developers.openai.com/plugins/build/auth
- https://developers.openai.com/plugins/build/mcp-server
