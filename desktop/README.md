# Navix Desktop 0.1.0 — piloto Windows

Aplicativo novo, independente das versões anteriores do Navix. Painel em português,
servidor MCP local com credencial por execução, navegador integrado, suporte experimental
a Opera e automação de desktop autorizada por sessão.

## Uso do instalador

1. Instale `NavixDesktop-Setup-0.1.0.exe` na sua conta Windows, sem administrador.
2. Abra Navix Desktop, selecione as permissões e clique em **Conectar / Autorizar**.
3. Aguarde **LOCAL PRONTO**. Abra o navegador integrado ou o Opera pelo painel.
4. Clique em **Copiar pareamento** e configure um cliente MCP local compatível com
   Streamable HTTP e cabeçalho `Authorization: Bearer …`.
5. Encerre com **PARAR ACESSO**. O token anterior perde validade; nova conexão exige
   copiar o novo pareamento. A sessão expira após 30 minutos.

Não exige Python instalado na máquina de quem recebe o instalador. O Chromium é
empacotado com o aplicativo. Os perfis de automação ficam separados do navegador habitual.
Não inicia com o Windows e não abre portas no roteador.

## Limites reais

- O servidor escuta apenas `127.0.0.1:8765`. Outra máquina não pode conectar diretamente.
- O programa **não conecta esta conversa do ChatGPT automaticamente**. A integração
  externa requer transporte seguro e autenticação compatíveis com o cliente escolhido.
  OAuth e serviço de pareamento remoto para terceiros ainda não estão implementados.
- O token é individual, mas não é um sistema de contas nem um código público de convite.
  Nunca publique o conteúdo copiado. Desconectar revoga o token.
- Automação de desktop controla a janela em foco. O proprietário deve acompanhar a sessão.
  O botão Parar bloqueia novas ações e novos caracteres; uma ação de navegador já enviada
  pode concluir antes da interrupção. Fechar o painel encerra seu navegador de automação.
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

## Fontes técnicas

- https://github.com/modelcontextprotocol/python-sdk
- https://playwright.dev/python/docs/library
- https://pyinstaller.org/en/stable/usage.html
- https://pyautogui.readthedocs.io/en/latest/
- https://jrsoftware.org/ishelp/
