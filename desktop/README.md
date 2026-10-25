# Navix Desktop 0.2.3 — piloto Windows

Aplicativo novo, independente das versões anteriores do Navix. Painel em português,
servidor MCP local com credencial por execução, porta automática, ícone na bandeja, navegador integrado, suporte experimental
a Opera, automação de desktop, arquivos e comandos autorizados por sessão.

## Uso do instalador

1. Instale `NavixDesktop-Setup-0.2.3.exe` na sua conta Windows, sem administrador.
2. Abra Navix Desktop, selecione as permissões (ou **Marcar todas**), escolha a duração e clique em **Conectar / Autorizar**. O acesso completo exige confirmação explícita.
3. Aguarde **LOCAL PRONTO**. Abra o navegador integrado ou o Opera pelo painel.
4. Clique em **Copiar pareamento** e configure um cliente MCP local compatível com
   Streamable HTTP e cabeçalho `Authorization: Bearer …`.
5. Encerre com **PARAR ACESSO**. O token anterior perde validade; nova conexão exige
   copiar o novo pareamento. A sessão expira após o tempo escolhido (30, 60, 120 ou 240 minutos).

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


## Visual e instalação — versão 0.2.3

O painel Windows foi reorganizado em **Visão geral**, **Permissões**,
**Ferramentas** e **Atividade**. Todas as ações do piloto anterior continuam
acessíveis, inclusive autorização explícita e revogação de sessão. O novo
ícone é uma interpretação própria de circuitos eletrônicos e da letra N.
O logotipo original do canal Circuito Vivo não foi incorporado porque o
arquivo-fonte exato ainda não foi confirmado.

O instalador tem visual NAVIX e uma opção **Abrir NAVIX Desktop agora** ao
final. O navegador e o Windows controlam a barra de downloads e o diálogo
de reputação do SmartScreen. Uma página ou instalador não consegue forçar o
botão **Abrir** no navegador nem transformar o alerta do SmartScreen em dois
botões disponíveis inicialmente. Para distribuição profissional, assinar o
executável com certificado confiável e avaliar a Microsoft Store. A assinatura
não garante eliminação imediata de avisos; reputação pode levar tempo.

Usuários devem baixar apenas do GitHub Releases oficial e conferir a origem
e o hash publicado. Não é necessário desligar o SmartScreen.

## Limites reais

- O servidor escuta apenas `127.0.0.1`, numa porta livre selecionada automaticamente. Outra máquina não pode conectar diretamente.
- O programa **não conecta esta conversa do ChatGPT automaticamente**. A integração
  externa requer transporte seguro e autenticação compatíveis com o cliente escolhido.
  OAuth e serviço de pareamento remoto para terceiros ainda não estão implementados.
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
- Não há atualização automática, assinatura Authenticode, serviço em segundo plano,
  homologação no PC do usuário ou garantia de compatibilidade com todos os clientes MCP.
- O instalador é piloto sem assinatura. Distribuição pública depende de homologação e
  estratégia de assinatura. Não desative as proteções do Windows.
- Desinstalar preserva perfis e logs em `%LOCALAPPDATA%\NavixDesktop`. Para apagar todos
  os dados, feche o programa e remova essa pasta deliberadamente.

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

No painel, clique em **Assistente para novos usuários**. Ele mostra as três
etapas: autorizar no próprio Windows, parear um cliente MCP local e consultar
as opções oficiais para uma conexão externa autenticada. O botão de pareamento
só copia a credencial quando a sessão local estiver ativa; não envia token
à internet nem inclui nenhuma chave de API no instalador.

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
