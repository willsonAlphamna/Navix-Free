# NavixX Desktop — pré-lançamento Windows

## Nova interface alpha.9: formulário de ID + código

Na tela **Permissões**, clique em **Vincular ao ChatGPT**. A janela agora é rolável, mostra ID e código e tem um botão **Abrir página para digitar ID e código**. O navegador abre o endereço HTTPS da **mesma nuvem configurada no aplicativo**, rota `/vincular`, sem transportar o código pela URL. O site valida os dados de seis números contra o pareamento temporário no servidor. Código errado ou expirado é recusado com limite de tentativas.

**Atenção:** essa validação inicial NÃO substitui o consentimento OAuth do ChatGPT: depois é necessário abrir o plugin NavixX Desktop Cloud no ChatGPT e concluir a autorização na página que ele apresentar. Sem a etapa OAuth, o Windows permanece inacessível ao ChatGPT. Não use o ConectaX antigo, nem crie novas chaves. A versão no GitHub não entra no programa já instalado até a entrega e instalação de um novo executável.



## NavixX Cloud Preview 0.3.0-alpha.7 — vínculo legível e reconexão

Correção observada no Windows: os campos de identificação e código apareciam
claros/vazios ao entrar no modo somente leitura do Tk. Agora são apresentados
em rótulos de alto contraste, com botões para copiar e confirmação visual.
O diálogo mostra quanto tempo falta para o código expirar, informa o próximo
passo no ChatGPT e esclarece que erro 401 do plugin exige reautorização no
ChatGPT — o aplicativo não pode contornar o controle de acesso da conta.

Esta edição é instalada separadamente em `%LOCALAPPDATA%\Programs\NavixDesktopCloudPreview`
e mantém seu perfil próprio em `%LOCALAPPDATA%\NavixDesktopCloudPreview`. Não altera o
NavixX Desktop 0.2.11. O instalador é um pré-lançamento **não assinado**.

1. Abra o Cloud Preview com sua senha local. Escolha as permissões, o prazo e clique
   **Conectar / Autorizar**. A permissão continua sendo concedida pelo proprietário;
   abrir o aplicativo sozinho não autoriza acesso remoto.
2. Se o computador já foi vinculado, a conexão Cloud será iniciada automaticamente
   depois que o MCP local estiver pronto, independentemente da porta aleatória.
3. Se ainda não houve vínculo ou se a autorização foi recusada, use **Vincular ao
   ChatGPT** e confirme o código de 6 dígitos no serviço. Isso não pode ser feito
   automaticamente em seu nome.
4. A tela Ferramentas mostra o estado Cloud e a causa provável de falhas. Use
   **Reparar conexão Cloud** quando necessário. O assistente desta edição não
   pede chave Runtime do túnel antigo.

Após uma queda de rede, o canal tenta retornar com espera progressiva de até 60 s,
sem alterar as permissões. Se o servidor MCP local parar inesperadamente, o painel
tenta reabri-lo e acompanha a nova porta. A sessão expirada, uma ação de **PARAR
ACESSO**, um vínculo ausente e uma autorização recusada exigem intervenção explícita.

**Estados distintos:** “Canal ativo” comprova apenas o WebSocket com a nuvem;
“ChatGPT confirmado” aparece somente depois que uma chamada de ferramenta real
é atendida. Testes automáticos e instalação de CI não substituem o teste no PC
do proprietário, incluindo sair e voltar ao chat.

O restante deste documento registra a linha anterior 0.2.11 e seu túnel Runtime
separado. **Não use as instruções de chave Runtime da 0.2.11 para configurar o
Cloud Preview 0.3.**

---

## NavixX Desktop 0.2.11 — linha anterior

Aplicativo novo, independente das versões anteriores do Navix. Painel em português, inglês e espanhol,
servidor MCP local com credencial por execução, porta automática, ícone na bandeja, navegador integrado, suporte experimental
a Opera, automação de desktop, arquivos e comandos autorizados por sessão.

## Uso do instalador

1. Instale `NavixDesktop-Setup-0.2.11.exe`, sem administrador. Escolha PT-BR (padrão), English ou Español.
2. Ao abrir, **crie uma senha local do NavixX** (mínimo 10 caracteres). Na próxima abertura, entre com essa senha. Este não é um login OpenAI ou conta sincronizada na nuvem.
3. Selecione as permissões e clique em **Conectar / Autorizar**. A autorização nunca é automática.
4. Para acesso ChatGPT, abra **Assistente**. Siga os cartões ilustrados: entrar na Plataforma OpenAI, criar o túnel, gerar uma **chave Runtime OpenAI com Tunnels Read + Use** e colar o ID e a credencial. O programa oferece links diretos ao painel oficial. O cliente de túnel está incorporado: **não precisa de PowerShell**.

**Confiabilidade da conexão (em desenvolvimento):** o processo de túnel aberto **não significa** que o ChatGPT está conectado. O painel verifica as rotas locais `/healthz`, `/readyz` e, quando disponível, a saúde do plano de controle do cliente oficial. Uma sessão externa só é homologada após uma chamada de ferramenta real no ChatGPT. O NavixX recomeça tentativas de rede transitórias com intervalo progressivo (máximo de 90 s), sem insistir indefinidamente em falhas permanentes de credencial. O botão **Reparar conexão** reinicia o cliente com a autorização atual, sem pedir a chave novamente. Caso a autorização do plugin no ChatGPT seja revogada ou sua sessão termine, o usuário precisará reautorizar no próprio ChatGPT.

O instalador oferece opção **desmarcada por padrão** para abrir o painel no login do Windows. Essa opção **não autoriza controle remoto nem desbloqueia o painel automaticamente**; o proprietário continua responsável por iniciar sua sessão autorizada.
5. Marque **Lembrar chave criptografada neste usuário Windows (DPAPI)**. Ela nunca aparece automaticamente no formulário. No **Meu cofre**, é possível consultá-la temporariamente após informar novamente a senha local; uma sessão remota ativa será encerrada antes de revelar a chave. Não compartilhe capturas de tela com segredos.
6. No ChatGPT, vincule o túnel em **Plugins → + → Adicionar servidor MCP personalizado → Tunnel** e aceite os avisos. Esse consentimento individual não pode ser automatizado.
7. **PARAR ACESSO** revoga a sessão e interrompe o túnel. **Bloquear painel** também encerra o acesso e exige novamente o login local. O acesso temporário dura 30, 60, 120 ou 240 minutos; **Sem prazo** é opcional, exige confirmação extra e só dura enquanto o programa estiver aberto.

**Cuidado com senhas:** o login local protege o painel, mas **não é uma conta online e não elimina os riscos de malware ou de processos que já executam como o mesmo usuário Windows**. A senha local não é recuperável por e-mail. Se você a esquecer, precisará seguir um procedimento local de recuperação/reconfiguração; preserve as credenciais da OpenAI em um gerenciador de senhas confiável. A chave Runtime é distinta de uma chave de API genérica que não possui Tunnels Read + Use.

Não exige Python instalado na máquina de quem recebe o instalador. O Chromium é
empacotado com o aplicativo. Os perfis de automação ficam separados do navegador habitual.
Não inicia com o Windows e não abre portas no roteador.

O painel permite selecionar navegador, desktop, arquivos e comandos. A autorização vale
para a sessão: não é necessário aprovar cada clique, leitura ou comando novamente.
Upload e download pelo navegador exigem também a permissão de arquivos. Comandos
executam com os privilégios da conta Windows que abriu o aplicativo.

`command_run` aceita `powershell`, `cmd` e `python`. A distribuição inclui um executor
`python-runtime/NavixPython.exe`, com suporte a código (`-c`), módulos (`-m`) e scripts,
além de Playwright, PyAutoGUI, Pillow e MCP. Ele não é uma instalação geral de Python
nem um gerenciador pip; para pacotes adicionais use um interpretador instalado. Na
execução a partir dos fontes, usa o mesmo Python que iniciou o aplicativo.


## Visual e instalação — versão 0.2.4

O painel Windows foi reorganizado em **Visão geral**, **Permissões**,
**Ferramentas** e **Atividade**. Todas as ações do piloto anterior continuam
acessíveis, inclusive autorização explícita e revogação de sessão. O novo
ícone é uma interpretação própria de circuitos eletrônicos e da letra N.
Na versão 0.2.4, a identidade visual usa o símbolo 3D do Circuito Vivo
fornecido pelo próprio proprietário, isolado de uma captura de tela.
O símbolo é incluído no instalador como imagem, no ícone da janela e na bandeja.

O instalador tem visual NAVIX e uma opção **Abrir NAVIX Desktop agora** ao
final. O navegador e o Windows controlam a barra de downloads e o diálogo
de reputação do SmartScreen. Uma página ou instalador não consegue forçar o
botão **Abrir** no navegador nem transformar o alerta do SmartScreen em dois
botões disponíveis inicialmente. Para distribuição profissional, assinar o
executável com certificado confiável e avaliar a Microsoft Store. A assinatura
não garante eliminação imediata de avisos; reputação pode levar tempo.

Usuários devem baixar apenas do GitHub Releases oficial e conferir a origem
e o hash publicado. Não é necessário desligar o SmartScreen.

## Novidades da versão 0.2.11

- **Status honesto:** um processo em execução não equivale a uma sessão ativa
  no ChatGPT. A confirmação final exige chamar uma ferramenta no próprio chat.
- **Saúde em segundo plano:** a aplicação lê `/healthz`, `/readyz` e detalhes
  de controle do `tunnel-client`, quando presentes; nunca expõe essas portas
  à rede externa.
- **Recuperação controlada:** reinicia o processo quando a sondagem local fica
  indisponível repetidamente, tenta novamente falhas transitórias com
  espera progressiva e interrompe tentativas após erros persistentes de acesso.
- **Um clique para reparo:** o botão existente agora também reinicia o túnel
  sem revogar a sessão autorizada e mantém registros sem chaves.
- **Inicialização opcional com o Windows:** somente abre o painel quando o
  usuário seleciona a tarefa no instalador. Nenhuma autorização remota é
  concedida automaticamente.

## Novidades da versão 0.2.10

- **Sem quadrado no logotipo de instalação:** a arte menor no topo do instalador
  agora tem transparência real e preserva o símbolo Circuito Vivo/NavixX isolado.
  O ícone do executável também continua com transparência.
- **Ícones modernos:** navegação com traços refinados e brilho discreto,
  sem tiles ou placas quadradas azuis. O menu recebe azul-petróleo e um
  contraste mais alto no item selecionado.
- **Painel mais compacto:** ao detectar monitor pequeno ou DPI que reduz o
  espaço útil, botões, cartões e espaçamentos encolhem; os textos usam quebras
  para caber na área disponível. A rolagem continua quando o conteúdo não cabe.
- **Idioma sempre à vista:** o seletor saiu da lista que rola e ficou fixo no
  rodapé lateral, para não desaparecer ao rolar o menu.
- **Acesso à máquina de familiar por convite:** registrado como arquitetura
  futura em `ACESSO_ASSISTIDO_MULTI_PC.md`; não está implementado ou ativo.

## Melhorias anteriores da versão 0.2.9

- **Layout:** menu lateral e páginas de conteúdo têm rolagem independente. O campo **Idioma**,
  o copyright e a bandeira permanecem acessíveis em monitores pequenos ou com ampliação DPI.
- **Desinstalador acessível:** botão **Ferramentas → Desinstalar NavixX Desktop**,
  atalho no menu Iniciar e entrada normal em Configurações do Windows → Aplicativos.
  O instalador Inno Setup já incluía `unins000.exe`; a interface agora permite encontrá-lo.
- **Remoção de dados com escolha explícita:** ao desinstalar com interface, o usuário decide
  se também quer apagar `%LOCALAPPDATA%\NavixDesktop` (preferências, credenciais DPAPI,
  perfis de navegador e logs). Se responder Não, esses dados são preservados.
  Na desinstalação silenciosa os dados locais são mantidos por segurança.
- **Apoie o projeto:** página opcional com QR Code e Pix Copia e Cola fornecidos pelo
  proprietário, mais uma chave Pix aleatória separada. O QR foi validado por TLV e CRC16;
  **não foi confirmada a titularidade bancária**. O destinatário e a instituição devem
  ser conferidos no aplicativo bancário antes de pagar. O NavixX não inicia transferências.
- **Distribuição:** continua em pré-lançamento, sem assinatura Authenticode.
  A publicação na Microsoft Store, Google Play e App Store não foi realizada.
  O app móvel Android/iOS exige projeto separado e autenticação segura por usuário.

## Limites reais

### O que mudou na candidata 0.2.8

- Login **local** com derivação PBKDF2-SHA256, salt exclusivo e bloqueio temporário após tentativas falhas; nenhum compartilhamento de senha ou cadastro na nuvem.
- Nova ação **Bloquear painel** revoga o acesso remoto antes de exigir login novamente.
- Assistente ilustrado com passos curtos e links oficiais para túnel e geração de chave Runtime. Credencial salva não é mais pré-carregada no campo da interface.
- Cofre com chave criptografada pelo Windows (DPAPI); visualização por 12 segundos, com confirmação da senha local e revogação prévia da sessão remota.
- Logotipo contínuo e em alto-relevo, título e menu com efeito de profundidade, ícones de navegação com gradiente e acabamento 3D.
- **Ainda não é login público multiusuário**, nem dispensa a credencial/consentimento da OpenAI. O plano de arquitetura pública está em `ONE_CLICK_PUBLIC.md`.


### Correção 0.2.7

Após um relato real de **túnel que iniciava e caía**, foi detectado que o instalador
0.2.6 incluía apenas `tunnel-client.exe`, omitindo `cloudflared.exe` e o manifesto
do arquivo de distribuição oficial. Não foi possível provar que isso causou a
queda relatada, mas a omissão do pacote precisava ser corrigida.

A 0.2.7 copia os três arquivos a partir do ZIP upstream com SHA-256 validado e
testa o reconhecimento do companion. Também utiliza uma porta local dinâmica
para a interface de saúde (evitando o conflito da porta 8080), desconsidera
perfis antigos herdados do terminal, e identifica códigos de autenticação,
permissão e falha de rede sem gravar mensagens brutas ou credenciais em logs.
Um diagnóstico local bem-sucedido **não garante** que o serviço remoto aceite
uma chave; se o processo terminar, o motivo classificado aparece na Atividade.
Esta versão continua **pré-lançamento** até o teste real no PC proprietário.

- O servidor escuta apenas `127.0.0.1`, numa porta livre selecionada automaticamente. Outra máquina não pode conectar diretamente.
- O programa **inicia o túnel sem terminal** depois de você informar sua própria identidade e chave. Ele não pode criar contas OpenAI, aprovar termos ou vincular um plugin ChatGPT sem sua ação. OAuth e serviço público multiusuário ainda não estão implementados.
- O token é individual, mas não é um sistema de contas nem um código público de convite.
  Nunca publique o conteúdo copiado. Desconectar revoga o token.
- Automação de desktop controla a janela em foco. O proprietário deve acompanhar a sessão.
  O botão Parar bloqueia novas ações e novos caracteres; uma ação de navegador já enviada
  pode concluir antes da interrupção. Movimento/arraste já iniciado pode levar até cinco
  segundos para terminar. Comandos em execução são monitorados e sua árvore de processos
  é encerrada após revogação ou timeout. Programas lançados de forma independente e
  comandos já concluídos não são revertidos. Fechar o painel encerra seu navegador de automação.
- O Opera é detectado em caminhos comuns do Windows; outras instalações podem não ser
  reconhecidas. Usa perfil dedicado e porta loopback 9223, independentemente da 9222 antiga.
- Não há atualização automática, assinatura Authenticode, serviço independente do painel,
  homologação no PC do usuário ou garantia de compatibilidade com todos os clientes MCP.
- O instalador é piloto sem assinatura. Distribuição pública depende de homologação e
  estratégia de assinatura. Não desative as proteções do Windows.
- Desinstalar preserva perfis e logs em `%LOCALAPPDATA%\NavixDesktop` por padrão.
  Na desinstalação interativa, uma segunda confirmação permite apagar tudo que está
  **nessa pasta específica**. Não são removidos arquivos pessoais fora dela,
  backups externos, componentes do Windows ou outras instalações de software.

## Ferramentas

`status`, `browser_tabs`, `browser_open`, `browser_read`, `browser_click`, `browser_fill`,
`browser_scroll`, `browser_screenshot`, `desktop_screenshot`, `desktop_click`,
`desktop_type`, `desktop_key`, `desktop_scroll`.

Novas ferramentas:

- Navegador: `browser_start`, `browser_navigate`, `browser_close_tab`, `browser_back`,
  `browser_forward`, `browser_reload`, `browser_snapshot`, `browser_select`,
  `browser_press`, `browser_hover`, `browser_wait`, `browser_upload`, `browser_download`.
- Desktop: `desktop_position`, `desktop_screen_info`, `desktop_move`, `desktop_drag`,
  `desktop_hotkey`. `desktop_click` aceita botão e quantidade de cliques;
  `desktop_key` reconhece as teclas do PyAutoGUI e `desktop_type` aceita até 10 mil caracteres.
- Arquivos: `files_list`, `files_read`, `files_write`, `files_edit`, `files_mkdir`,
  `files_copy`, `files_move`, `files_delete`, `files_read_binary`, `files_write_binary`,
  `files_download`. Os caminhos pertencem ao computador Windows que executa o Navix.
- Programas: `command_run` e `command_exec` (lista de argumentos, sem shell implícito).

Gravação e transferências preservam arquivos existentes por padrão; quando suportada,
a substituição exige `overwrite=true`. Exclusão é permanente; pastas não vazias exigem
`recursive=true`. Edição textual exige correspondência exata e recusa trechos ambíguos.
Movimentação é atômica dentro do mesmo volume. Entre volumes, a ferramenta recusa
a operação e mantém a origem; use cópia, confira o resultado e só então apague a origem.
Arquivos UTF-8 têm limite de 5 MB por chamada e binários Base64 de 10 MB. Para transferir
um arquivo entre cliente e computador use `files_read_binary`/`files_write_binary`; o
upload de uma página usa `browser_upload` no campo de arquivo do site.

`browser_download` aguarda o início e término da transferência com timeout, confirma
permissões e salva somente no destino explícito. Downloads utilizam eventos CDP do Chromium,
inclusive quando conectado ao Opera; sua compatibilidade deve ser validada no Opera real.
`files_download` permite baixar diretamente por HTTP/HTTPS com limite de tamanho,
tempo e hash SHA-256. As credenciais da página continuam no perfil do navegador.

Comandos têm timeout de 1 a 300 segundos, saída de até 1 MB por fluxo e retorno de
`exit_code`, `stdout`, `stderr`, `timed_out` e `output_truncated`. Não confundir o retorno
da ferramenta com sucesso do programa: verificar também o código de saída e a evidência
da operação. Ajuste o timeout de leitura do cliente MCP para comandos mais longos.

A navegação usa papel acessível e nome exato para evitar cliques ambíguos. Capturas são
retornadas como imagens MCP, sem gravação automática. Logs registram somente horário,
nome da ação e resultado; não guardam textos digitados, páginas ou tokens.

## Desenvolvimento

Python 3.12, Windows x64. Em ambiente virtual:

```powershell
python -m pip install -r requirements.txt pytest pyinstaller
python -m playwright install chromium
python -m pytest -q
python launcher.py
```

Para testar navegação real: defina `NAVIX_TEST_BROWSER=1` antes de executar pytest.
O workflow `Navix Desktop - Windows piloto` instala o Chromium, testa, compila com
PyInstaller, abre o executável, gera Inno Setup e testa instalar/desinstalar.
Seu artefato fica no GitHub Actions, com SHA256 e versões resolvidas das dependências.
Não confundir configuração do workflow com resultado aprovado.

O autoteste do pacote executa ações em arquivos temporários, páginas locais e janela
própria. A verificação local em Linux não comprova teclado/mouse nativos no Windows,
instalação do executável, Opera nem integração remota com o ChatGPT. Esses resultados
devem ser obtidos no runner Windows e no computador de destino antes da homologação.

## Fontes técnicas

- https://github.com/modelcontextprotocol/python-sdk
- https://playwright.dev/python/docs/library
- https://pyinstaller.org/en/stable/usage.html
- https://pyautogui.readthedocs.io/en/latest/
- https://jrsoftware.org/ishelp/

## Correção 0.1.1

Reparar conexão preserva a sessão ativa e seu prazo original. Não renova credenciais nem autoriza sessões encerradas. Servidores encerrados são recriados e iniciados; nesse caso, copie novamente o pareamento pela nova porta. Abrir navegador sem autorização mostra a ação necessária no painel. A integração remota com ChatGPT continua pendente.

## Instalação por outras pessoas e configuração guiada

No painel, clique em **Assistente**. O assistente configura e inicia o cliente
Secure MCP Tunnel incorporado, sem PowerShell. ID e chave de cada pessoa são
informados na primeira conexão e a chave só é persistida quando o usuário
opta pela criptografia DPAPI vinculada ao login Windows. O pareamento manual
local continua disponível como opção avançada; não há credenciais no instalador.

O instalador é distribuível como programa Windows independente. Isso **não**
significa que cada usuário terá ChatGPT remoto automaticamente: o usuário ou
uma futura plataforma de pareamento deverá configurar identidade e conexão.
O Secure MCP Tunnel é uma solução privada; publicar um plugin com servidor
remoto exige HTTPS estável e autenticação. A publicação de plugins MCP locais
de execução desktop está sujeita a elegibilidade de parceiros aprovados.

Documentação:
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://developers.openai.com/plugins/deploy/desktop-only
- https://developers.openai.com/plugins/build/mcp-server

A configuração de uma infraestrutura pública e multiusuário é um trabalho
separado, com autenticação por usuário, isolamento de dispositivos, consentimento
granular, auditoria e hospedagem. Não se deve compartilhar tokens nem túneis
entre instalações.

## Ajustes visuais e verificação 0.2.4

- Marca na interface: **NavixX**, com x minúsculo e X final maior.
- Título de boas-vindas: vermelho escuro, palavra de ligação branca, marca azul.
- Barra lateral: rótulos compactos, status local atualizado a cada meio segundo,
  porta e prazo da sessão; sem indicação enganosa de conexão remota.
- Assistente: conteúdo rolável com botões finais visíveis e versões detectadas.
- Cartões e botões: bordas em camadas com contraste e leve relevo.
- Emblema: `desktop/assets/circuitovivo_navix.png`, autorizado pelo proprietário
  que enviou a referência do canal. As imagens de referência completas do celular
  não são distribuídas no programa.

### Componentes incorporados

O instalador Windows inclui o executável Python integrado, Playwright, Chromium,
PyAutoGUI, Pillow e servidor MCP. O destinatário não precisa instalar esses pacotes
separadamente. O script de validação em CI testa o executável empacotado,
importações do Python, navegação, arquivos, comandos, abertura da GUI e instalação/
desinstalação. O botão **Diagnosticar** informa versões no PC de destino.
Essa verificação **não comprova** que a conexão remota da conta ChatGPT ou o Opera
real do usuário estejam pareados; esses testes exigem autenticação e execução local.

## Versão 0.2.6 — mudanças e limitações

- Cliente `tunnel-client` v0.0.18 oficial, incorporado no instalador após validar SHA-256 do release OpenAI.
- Assistente gráfico para ID/chave restrita, diagnóstico, início do túnel e reconexão supervisionada. Não compartilhe o mesmo túnel ou a mesma chave com outras pessoas.
- PT-BR, English e Español no instalador e principais elementos do painel, com seletor de idioma persistente. A revisão de mensagens técnicas e cobertura integral de traduções ainda precisa de homologação multilíngue.
- Ícones próprios por imagem nos seis menus, margem do logotipo do instalador corrigida, rodapé ALFAMNA © 2026 e bandeira animada discreta. `NAVIX_REDUCED_MOTION=1` desativa a animação.
- Botões **Ver logs** e **Exportar diagnóstico**: eventos locais estruturados, sem gravar senhas, chaves, conteúdo de páginas ou teclas.
- **Sem prazo** é uma opção não padrão, válida somente durante o processo atual, revogável por PARAR ACESSO. Não se deve presumir proteção em tela bloqueada nem conexão garantida após reiniciar o Windows.

É necessário validar o assistente no PC Windows de destino e em instalações limpas antes de ampla distribuição. Secure MCP Tunnel atende conexões **privadas**; um serviço público multiusuário exige infraestrutura HTTPS própria e autenticação de contas com consentimento e isolamento por dispositivo.
