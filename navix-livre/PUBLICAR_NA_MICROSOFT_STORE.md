# Publicar Navix Free na Microsoft Store

## Situação e objetivo

O caminho MSIX foi preparado para submeter o aplicativo à Microsoft Store sem
comprar um certificado de assinatura. **Ainda não existe publicação aprovada
nem link de instalação da Store.** O funcionamento como aplicativo empacotado
e a aprovação de `runFullTrust` precisam ser validados; gerar o pacote não
conclui esses testes nem garante certificação.

A Microsoft assina o **MSIX após a certificação**. O pacote de submissão não
assinado não deve ser enviado ao usuário como instalador. Submeter o antigo
EXE/MSI à Store não resolve sua assinatura: esses formatos não são reassinados.
Não desative SmartScreen, antivírus ou verificação de assinatura para testar.

## Etapas do responsável pela conta

1. Comece em <https://storedeveloper.microsoft.com>. O novo cadastro individual
   é gratuito nesse fluxo. Use sua própria conta Microsoft e conclua a
   verificação de documento oficial e selfie diretamente na Microsoft.
   Não envie documento, senha ou código de acesso ao projeto ou a esta conversa.
   Se publicar em nome de uma empresa, escolha o tipo de conta apropriado.
2. No Partner Center, abra **Apps and games**, crie um produto MSIX e reserve
   **Navix Free**, se disponível. Se precisar escolher outro nome, ajuste
   também o nome apresentado pelo aplicativo e pelo pacote antes de submeter.
3. Em **Product management > Product identity** / **View app identity details**,
   copie exatamente os três campos abaixo. Preserve maiúsculas e pontuação:

   | Campo da Microsoft | Entrada do workflow |
   | --- | --- |
   | `Package/Identity/Name` | `store_identity_name` |
   | `Package/Identity/Publisher` (incluindo `CN=`) | `store_publisher` |
   | Nome de exibição do editor | `store_publisher_display_name` |

   Esses identificadores não são senhas. Nunca invente a identidade nem use
   os valores fictícios dos testes. Eles devem pertencer ao produto reservado.
4. No GitHub, abra **Actions > Navix Livre - Instalador Windows > Run workflow**.
   Escolha a branch `feature/navix-livre-mcp`, mantenha **`publish=false`**,
   marque **`prepare_store=true`** e preencha os três valores oficiais.
5. Aguarde os testes e a preparação do pacote. Baixe o artefato
   **`NavixLivre-Microsoft-Store-Submission`** da mesma execução. Confira o
   commit e os metadados em `BUILD_INFO.json`, além dos hashes fornecidos.
   O `.msix` não assinado desse artefato serve **somente para submissão à Store**.
   Qualquer pacote com identidade fictícia criado pelo CI é fixture de teste,
   separado da submissão, e não pode ser distribuído ou instalado pelo usuário.
6. Antes de certificar, valide uma instalação de desenvolvimento em Windows
   isolado, sob a mesma identidade reservada e com assinatura de teste limitada
   a esse ambiente. Execute o Windows App Certification Kit e teste abertura,
   arquivos, ponte local, encerramento e desinstalação. A confiança de teste
   nunca deve ser instalada no computador do usuário como solução de entrega.
7. Crie a submissão no Partner Center e envie o `.msix` em **Packages**.
   Selecione preço gratuito, categoria apropriada, mercados, classificação
   etária e idioma português do Brasil. Inclua capturas reais da versão validada,
   contato de suporte e a URL pública de [PRIVACIDADE.md](PRIVACIDADE.md).
   Revise e adote essa política antes de publicá-la como política do produto.
8. Informe os recursos e limites abaixo e justifique `runFullTrust`. Solicite
   a certificação, acompanhe exigências da Microsoft e corrija eventuais recusas.
9. Depois da aprovação, teste a instalação pelo link oficial da Store e a
   desinstalação em Windows. Somente então compartilhe esse link como versão
   pronta para instalar. Não reutilize o link do EXE 0.3.0 sem assinatura.

## Texto sugerido para a página do produto

**Descrição curta:** Painel gratuito para arquivos, processos e conexão MCP local no Windows.

**Descrição:**

Navix Free é um aplicativo independente, gratuito e de código aberto para
trabalhar com arquivos e consultar processos no seu computador Windows.
Oferece navegação por pastas autorizadas, busca por nome, informações de
arquivos e leitura de textos. O acesso inicial aos arquivos limita-se à
Área de Trabalho; outras pastas podem ser configuradas pelo usuário.

Escrita de arquivos, terminal PowerShell/CMD, cliques do mouse e captura da
tela principal são opcionais e ficam desativados por padrão. O painel mostra
as permissões em uso. A ponte MCP opcional atende somente no próprio
computador, com autenticação por token, para clientes configurados pelo usuário.

Instalar o Navix Livre não conecta automaticamente o ChatGPT ao computador.
É necessário um cliente MCP compatível e configuração própria. Não há controle
remoto pela internet incluído, assinatura de serviços de IA nem vínculo com
Desktop Commander. O aplicativo não possui mensalidade; serviços externos
escolhidos pelo usuário podem cobrar. A interface está em português do Brasil.

## Justificativa de `runFullTrust` e notas para certificação

Texto proposto, a confirmar com os testes do pacote:

> Navix Livre é um aplicativo Win32 de desktop, feito em Python/Tkinter e
> empacotado com PyInstaller. Precisa executar em confiança plena, no contexto
> normal do usuário, para navegar em pastas autorizadas, consultar processos
> via tasklist e iniciar seu executável auxiliar NavixBridge.exe. A ponte é
> opcional, atende somente em 127.0.0.1:8765 e exige token. Escrita, execução
> de PowerShell/CMD, mouse e captura de tela ficam desligados por padrão e
> exigem configuração explícita do usuário. Não requer elevação, serviço do
> sistema nem início automático. Comandos autorizados executam com as
> permissões do usuário e podem acessar a rede ou arquivos fora das pastas
> limitadas pelo navegador de arquivos. O aplicativo não inclui integração
> automática com ChatGPT nem serviço de acesso remoto externo.

Para testar o modo padrão, abra **Navix Livre**, consulte **Arquivos** e
**Processos** e, em **Configurações**, inicie e pare a ponte local. Não são
necessárias conta no aplicativo nem credenciais de produção. As permissões
opcionais dependem de configuração de ambiente e reinício; sua operação no
pacote deve ser validada antes de anunciar compatibilidade na Store.

## Referências oficiais

- [Cadastro gratuito e verificação da conta](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account).
- [Identidade, requisitos e assinatura MSIX pela Store; diferença para EXE/MSI](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements).
- [Criar a submissão MSIX e preencher a página do produto](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/create-app-submission).
- [Declaração de recursos e aplicativos desktop](https://learn.microsoft.com/en-us/windows/uwp/packaging/app-capability-declarations).

Uma alternativa para distribuição direta por EXE é solicitar assinatura OSS
ao [SignPath Foundation](https://signpath.org/terms), sujeita à aprovação do
projeto, políticas de segurança e aprovação das publicações pelo mantenedor.
