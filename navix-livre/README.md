# Navix Livre — alternativa gratuita ao Desktop Commander

Versão experimental 0.1.0. Projeto independente, sem vínculo com os criadores do Desktop Commander.

Este é um agente MCP **LOCAL**, escrito em Python padrão, com painel Tkinter. O código usa licença MIT, não pede conta, não depende de servidores pagos e não cobra por comandos.

## Funções disponíveis

- Localização e listagem da Área de Trabalho, inclusive se movida ao OneDrive.
- Pesquisa de arquivos pelo nome e leitura de texto.
- Gravação de texto, execução de PowerShell e CMD, abertura do navegador e caminhos (opt-in).
- Clique de mouse e captura da tela principal do Windows (opt-in).
- Servidor MCP (JSON-RPC sobre stdin/stdout) para clientes que aceitem MCP local.
- Diagnóstico e painel gráfico de controle.
- Restrição de caminhos fora das pastas autorizadas.

## Instalar e executar no Windows

Requer Windows 10 ou 11 e Python 3.10+ com Tkinter. Não instala bibliotecas extras.

1. Baixe a pasta navix-livre deste repositório.
2. Execute INICIAR_PAINEL.bat.
3. Para testar: execute VERIFICAR.bat.

Terminal alternativo:

    py -3 navix_livre.py --gui
    py -3 navix_livre.py --doctor
    py -3 navix_livre.py --mcp

## Configuração MCP local

No cliente MCP com suporte a stdio, configure:
- command: caminho completo de python.exe (ou py.exe)
- args: caminho completo de navix_livre.py, seguido de --mcp
- se utilizar py.exe, acrescente -3 no começo de args

**Não** cole diretamente esse endereço num navegador. É um processo MCP local, não um site.

## Permissões: desligadas por padrão

Por padrão, apenas a pasta Desktop pode ser lida. Para habilitar mais capacidades, antes de executar o MCP no PowerShell:

    $env:NAVIX_ALLOWED_DIRS = "$env:USERPROFILE"
    $env:NAVIX_ALLOW_WRITE = "1"
    $env:NAVIX_ALLOW_COMMANDS = "1"
    $env:NAVIX_ALLOW_UI = "1"
    py -3 navix_livre.py --mcp

**Cuidado:** a permissão de comandos permite modificar e apagar arquivos da conta do Windows. Ative somente para um cliente local confiável, nunca execute como Administrador e jamais exponha o terminal diretamente à internet.

## Gratuito: alcance e limites

O software próprio não impõe mensalidade, licença de uso nem limite de chamadas. Todavia, energia, internet, serviços de nuvem, APIs de IA e serviços de terceiros podem cobrar. Este código **não elimina limites nem cobranças do ChatGPT**.

O MCP por stdio só funciona com cliente local compatível. **Esta versão não possui relay seguro de acesso remoto via internet e não se conecta automaticamente ao ChatGPT na nuvem**. Para isso será necessária uma fase de desenvolvimento com gateway HTTPS autenticado ou VPN, sem expor comandos na rede pública.

Limitações atuais: não há instalador EXE, conexão remota, controle especializado do Opera, digitação por teclado ou atualizador automático. Os testes automatizados verificam somente funções básicas; as rotinas visuais ainda precisam ser testadas em um Windows com sessão gráfica.

## Testes

    py -3 -m unittest test_navix -v

Licença: MIT. Sem código proprietário copiado.
