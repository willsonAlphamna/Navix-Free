# NavixX — plano para acessar outro computador por convite (não implementado)

## Cenário solicitado pelo proprietário

Wilson usa seu próprio NavixX Desktop e gostaria de ajudar, por exemplo, a mãe
com outro computador, sem exigir que ela instale Python, Playwright ou configure
túnel MCP. O programa central escolheria o computador autorizado antes de
oferecer ferramentas ao assistente, com consentimento da dona do dispositivo.

## Limite técnico inegociável

Uma conexão ativa no computador do Wilson **não concede controle automático**
do computador de sua mãe. O outro Windows precisa executar algum agente próprio
ou um serviço nativo de acesso remoto já instalado e configurado. O instalador
leve pode conter só o módulo necessário para receber convites, sem Python e sem
um navegador de automação completo. Permissões concedidas no PC do Wilson não
valem no outro dispositivo.

## Arquitetura proposta

1. **NavixX Central:** mostra lista de máquinas pareadas com nome, proprietário,
   status e permissões individuais. Cada ação deve explicitar o computador-alvo.
2. **NavixX Assistido:** executável leve e assinado no computador da pessoa;
   obtém a aprovação de controle na tela local e mantém botão visível de encerrar.
3. **Convite temporário:** código de uso único, com prazo curto e confirmação
   explícita em ambos os lados. Nenhuma reutilização da chave OpenAI do Wilson.
4. **Transporte protegido:** canal autenticado por dispositivo, criptografado,
   usando HTTPS/TLS ou rede privada gerenciada. O PC do Wilson pode servir de
   painel/orquestrador, mas não deve virar um proxy público aberto.
5. **Isolamento:** permissões por destino (`ver_tela`, `clicar`, `digitar`,
   `arquivos`, `comandos`), princípio do menor privilégio, logs por sessão e
   identidade dos dois titulares. Comandos ou exclusões exigem consentimento
   renovado no destino; nunca assumir acesso geral por padrão.
6. **Revogação:** fechamento da janela, bloqueio local, expiração, desconexão ou
   clique em **Parar** encerram a sessão e invalidam o código. Não haverá agente
   oculto, acesso persistente sem consentimento nem compartilhamento de tokens.

## Fases de entrega

- MVP: visualização remota, ponteiro, teclado e rolagem; convite de uso único;
  aprovação local; dois Windows em redes diferentes; revogação testada.
- Depois: transferência de arquivo com confirmação, auditoria e assistente IA
  direcionado por computador, sem misturar contextos ou credenciais.
- Apps Android/iPhone: clientes de gerenciamento de sessões, somente após
  validação de segurança, autenticação e limites das plataformas móveis.

## Testes de aceite antes de publicar

- Não conectar sem o segundo computador aceitar o convite.
- Cada sessão apresenta permanentemente o nome do computador controlado.
- Impedir ferramenta dirigida ao PC A de executar acidentalmente no PC B.
- Cortar acesso quando a pessoa assistida aperta **Parar**.
- Expirar convite, impedir repetição e bloquear reutilização após revogação.
- Provar que credenciais, capturas privadas e teclas não aparecem em logs.
- Testar Windows 10, Windows 11, internet lenta, queda de rede e reconexão.

**Status:** especificação, não há software, servidor de retransmissão ou
publicação de cliente assistido nesta versão.
