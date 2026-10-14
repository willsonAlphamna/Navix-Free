# Política de privacidade — Navix Livre

Versão: 14/10/2026. Aplica-se ao código atual do Navix Livre 0.3.1.
O responsável pela publicação deve revisar e adotar este texto antes de
utilizá-lo na Microsoft Store; a versão empacotada ainda precisa de validação.

## Tratamento local dos dados

O aplicativo não inclui publicidade, rastreadores, análise de uso ou envio
automático de telemetria ao desenvolvedor. Não exige conta própria nem
mantém um servidor do projeto para receber seus arquivos ou capturas.

Para executar as funções solicitadas, o aplicativo pode ler nomes e caminhos
de arquivos, conteúdo de textos, metadados, nome do computador, informações
do Windows e lista de processos. Por padrão, o acesso aos arquivos fica
restrito à Área de Trabalho. As pastas permitidas podem ser configuradas.
As saídas são exibidas no painel ou devolvidas ao cliente MCP autorizado.

Escrita, comandos, mouse e captura de tela ficam desativados por padrão.
Quando autorizados, permitem alterar arquivos, executar comandos e capturar
a tela principal, que pode conter informações pessoais ou de outros aplicativos.
Comandos PowerShell/CMD usam as permissões do usuário; a limitação de pastas
do navegador de arquivos não restringe o que esses comandos podem fazer.

## Ponte MCP, clientes e serviços externos

A ponte HTTP é opcional e escuta apenas em `127.0.0.1`, normalmente na porta
8765. Exige token de autenticação. O token é criado no perfil local do
usuário, normalmente em `%LOCALAPPDATA%\NavixLivre\bridge.token`; o Windows
pode redirecionar esse armazenamento no contexto de um aplicativo empacotado.
Não publique o token nem exponha a porta na internet.

Quem tiver acesso ao token e ao computador poderá usar os recursos habilitados
na ponte. As chamadas autenticadas não exigem confirmação individual no painel.
O cliente MCP recebe os resultados solicitados, inclusive textos ou capturas
quando essas funções estiverem autorizadas. Se o cliente usar um serviço de IA
ou nuvem, esse serviço poderá processar esses dados segundo sua própria política.
Instalar ou iniciar a ponte não conecta automaticamente o ChatGPT.

Abrir um site, executar um comando ou abrir um arquivo com um aplicativo
externo por solicitação do usuário pode gerar tráfego de rede e compartilhar
dados com os destinos escolhidos. Aplicativos, clientes MCP, serviços de IA,
GitHub, Microsoft Store e Windows possuem suas próprias práticas de privacidade.
A ausência de telemetria do Navix não impede esse tratamento por terceiros.

## Armazenamento, remoção e suporte

O token permanece no computador para autenticar sessões posteriores. Capturas
geradas no painel são salvas na pasta temporária do usuário e podem permanecer
até sua remoção. A captura temporária interna da função MCP é apagada ao
terminar a operação. Arquivos salvos ou alterados pelo usuário permanecem nos
destinos escolhidos. O aplicativo não mantém um histórico próprio persistente
das chamadas HTTP; clientes e comandos externos podem manter seus próprios logs.

Para interromper o acesso, pare a ponte e encerre clientes autorizados. Com a
ponte desligada, remover seu arquivo de token invalida a credencial anterior;
ao iniciar novamente, uma nova credencial será criada. Apague capturas e
arquivos salvos que não desejar conservar. A remoção do aplicativo pela Store
e a limpeza dos dados locais precisam ser verificadas no pacote final.

Para dúvidas sobre o projeto, consulte
[o repositório e o suporte público](https://github.com/willsonAlphamna/SamsungRemoteTeste/issues).
Não publique senhas, tokens, documentos de identidade, capturas com dados
pessoais ou conteúdo privado nos issues. Relate somente a versão, a etapa
e a mensagem de erro sem informações sensíveis.
