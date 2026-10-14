# Navix Free 0.3.1 em desenvolvimento — painel Windows gratuito e código aberto

Projeto independente de código aberto (MIT), sem mensalidade e sem vinculo com Desktop Commander.

## Instalação

Estamos preparando a distribuição **MSIX pela Microsoft Store**, que assina o
pacote após a certificação e dispensa a compra de um certificado pelo projeto.
O pacote ainda aguarda cadastro/identidade do aplicativo e aprovação da Store;
não há link público de instalação por essa rota neste momento. O roteiro do
titular está em [PUBLICAR_NA_MICROSOFT_STORE.md](PUBLICAR_NA_MICROSOFT_STORE.md).

**Ainda não há uma nova versão assinada pronta para instalar.** O instalador
0.3.0 distribuído anteriormente não contém assinatura Authenticode. A 0.3.1
está em desenvolvimento; sua publicação exige uma identidade de assinatura
de código confiável, ainda não disponibilizada/configurada.

Para uso final, baixe somente uma versão pública assinada em
[Releases](https://github.com/willsonAlphamna/Navix-Free/releases),
depois de conferir assinatura, editor e SHA-256 conforme
[COMO_INSTALAR.md](COMO_INSTALAR.md). Artefatos do GitHub Actions identificados
como **desenvolvimento, sem assinatura** destinam-se a desenvolvedores e não
são o instalador recomendado ao usuário.

Inclui painel NavixLivre.exe e ponte MCP local NavixBridge.exe, alem de atalhos e desinstalador. Nao necessita Python no Windows, nao inicia automaticamente com o sistema e nao deve reiniciar o PC. Veja tambem [COMO_INSTALAR.md](COMO_INSTALAR.md).

## Interface 0.3

- Painel escuro com barra lateral: Arquivos, Terminal, Processos, Captura de Tela, Comandos, Configurações e Sobre.
- Explorador de arquivos, busca, detalhes, cópia para importar/exportar, abrir pasta e leitura de textos.
- Ações sensíveis (criar, renomear e excluir arquivos) só ficam disponíveis com autorização explícita de escrita; exclusão de pasta somente se vazia.
- Terminal com saída visível e seleção PowerShell/CMD, habilitado apenas quando autorizado.
- Consulta de processos, status real da ponte local e captura de tela opcional.
- Não afirma conexão com ChatGPT quando a ponte só está ativa localmente.

## Funcoes atuais

- Detecta a Area de Trabalho mesmo quando movida ao OneDrive.
- Lista pastas e busca arquivos.
- Le texto de arquivos de ate 1 MB.
- Quando habilitado conscientemente: escrita de texto, PowerShell/CMD, clique do mouse, captura de tela e abertura de arquivos ou sites.
- Painel com botoes para iniciar e parar a ponte MCP local.
- Servidor MCP local via stdio e ponte HTTP experimental em 127.0.0.1:8765 autenticada por token.

## Seguranca

Por padrao a ferramenta apenas le a Area de Trabalho. Escrita, comandos e controle visual ficam desligados. A ponte de rede so atende no proprio computador; nao abre porta publica. Nao abra a porta 8765 no roteador, nao use como Administrador e nao compartilhe o token de autenticacao.

## Limites atuais

A instalacao **nao conecta automaticamente esta conversa do ChatGPT ao computador**. Para conexao pela internet e necessario desenvolver ou configurar um canal HTTPS confiavel, autenticacao apropriada e um cliente MCP autorizado. O modulo local nao implementa OAuth completo nem substitui limites do ChatGPT. APIs e outros servicos externos podem cobrar.

O software permanece experimental; a instalação no computador real do usuário
não foi validada. Uma assinatura válida identifica o editor e protege a
integridade, mas um arquivo novo ainda pode receber alerta de reputação do
[SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).
Não desative as proteções do Windows para instalar.

O fluxo da 0.3.1 separa compilações de desenvolvimento de publicação assinada.
Consulte [ASSINATURA_WINDOWS.md](ASSINATURA_WINDOWS.md) para o diagnóstico
da 0.3.0, a configuração necessária e os bloqueios de publicação.

## Auditoria técnica e limites

Leia [AUDITORIA.md](AUDITORIA.md) para resultados de testes, riscos
de segurança e recursos que ainda não substituem o Desktop Commander.
A interface possui ícone de pena gerado por `make_assets.py` durante
a compilação. A barra de progresso do instalador é a do Inno Setup.

O agente fornece **14 comandos MCP**. Listar processos e consultar
metadados são somente leitura; criar pastas e mover arquivos exigem
permissão de escrita, desligada por padrão. A ponte continua **somente local**.

## Desenvolvimento

Para executar o codigo diretamente com Python 3.10+:

    py -3 navix_livre.py --gui
    py -3 navix_livre.py --mcp
    py -3 navix_remote.py
    py -3 -m unittest discover -s . -p "test*.py" -v

As permissoes opcionais sao ativadas pelas variaveis NAVIX_ALLOWED_DIRS, NAVIX_ALLOW_WRITE, NAVIX_ALLOW_COMMANDS e NAVIX_ALLOW_UI somente em ambiente local confiavel.

Licenca MIT.
