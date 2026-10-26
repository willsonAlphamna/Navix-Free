# NavixX Companion — Android e iPhone (projeto futuro, ainda sem APK/IPA)

Este documento **não é um aplicativo móvel publicado**. A versão Windows 0.2.9
permanece o componente operacional. A solicitação de app móvel foi registrada
para desenvolvimento específico, com a seguinte arquitetura.

## Funcionalidades planejadas

1. **Login e pareamento individual:** cada pessoa tem identidade própria,
   dispositivos autorizados e opção de revogar o acesso. QR/token de pareamento
   de uso único e curta duração; nunca inserir chaves OpenAI no código do app.
2. **Início / Computadores:** lista dos computadores permitidos, estado
   conectado/desconectado e notificações sobre perda de conexão.
3. **Controle remoto:** teclado, clique, rolagem, arquivos, comandos e captura
   quando o usuário do Windows e o operador estiverem autenticados.
   Consentimento claro e sinalização de sessão remota ativa.
4. **Atividade / segurança:** logs de erros sem dados pessoais e botão Parar
   que revogue imediatamente os tokens de sessão.
5. **Apoie o projeto:** interface adaptável com QR Pix, Pix Copia e Cola,
   valores livres, sem exigir doação para funcionar; confirmar regras de cada loja.
6. **Interface:** Material 3, menu inferior em telas pequenas, áreas de toque
   confortáveis, idioma PT-BR/EN/ES e suporte a acessibilidade.

## Etapas verificáveis

- [ ] Autenticação própria com backend seguro e troca de tokens.
- [ ] Integração com NavixX Windows sem expor a porta local ao público.
- [ ] Testes Android em aparelhos reais de baixa memória e alta resolução.
- [ ] Pacote Android assinado para testes fechados; publicação Play Console.
- [ ] Projeto iOS assinado, testes com TestFlight e revisão na App Store.
- [ ] Auditoria independente de segurança, consentimento e privacidade.

**Bloqueios reais:** contas de desenvolvedor das lojas, certificados de assinatura,
backend público seguro e escolha da política de acesso remoto para terceiros.
Não representar um protótipo Android anterior denominado Samsung Remote Teste
como se fosse o aplicativo NavixX Companion.
