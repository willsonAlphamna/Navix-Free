# Auditoria técnica — Navix Livre
Data: 14/10/2026 | Versão em desenvolvimento: 0.3.1 | Branch: feature/navix-livre-mcp

## Escopo

Revisão de segurança, protocolo MCP, arquivos, painel gráfico Windows, processo de
compilação, instalador, remoção, dependências e documentação. Esta auditoria não é
uma homologação do computador do usuário, nem um pentest independente.

## Diagnóstico do instalador 0.3.0

O instalador oficial anteriormente enviado, **NavixLivre-Setup-Windows.exe**
da release `navix-livre-v0.3.0`, foi baixado e inspecionado sem executá-lo.
Seu SHA-256 é
`3ef81d2e7eba81e8fcf51a177d7329bc9743d4aec7b5a798def805be888c676b`.
No cabeçalho PE, a entrada Certificate Table tem **offset 0 e tamanho 0**:
o arquivo não contém assinatura Authenticode incorporada. Esse resultado
confirma a ausência de assinatura no instalador analisado; a foto do alerta,
isoladamente, não demonstraria uma assinatura inválida ou detecção de malware.
O alerta mostrado é do SmartScreen para aplicativo não reconhecido.

A 0.3.1 prepara a correção do processo de distribuição. Não existe evidência
de uma identidade de assinatura confiável disponível/configurada nem de uma
nova release assinada validada. A publicação permanece bloqueada até isso ser
resolvido. O instalador antigo não é recomendado para nova instalação.

## Fluxo de assinatura e publicação da 0.3.1

- Push e pull request geram somente artefatos de desenvolvimento, rotulados
  sem assinatura, sem publicação pública automática.
- Publicação exige `workflow_dispatch` com `publish=true`, na branch confiável
  `feature/navix-livre-mcp`, com ambiente `windows-release`.
- O administrador precisa configurar efetivamente as proteções desse ambiente
  no GitHub. O nome `windows-release`, sozinho, não cria proteção.
- O painel e a ponte são assinados antes do empacotamento; o Inno Setup deve
  assinar o instalador e o desinstalador. A verificação exige assinatura `Valid`,
  editor esperado, carimbo de tempo e aprovação do SignTool.
- `BUILD_INFO.json` registra o commit de origem e os hashes dos executáveis
  finais; a tag da versão deve apontar para esse commit. Não substituir assets
  ou tags de uma release existente para disfarçar uma recompilação.

Pré-requisitos, variáveis e limitações estão em
[ASSINATURA_WINDOWS.md](ASSINATURA_WINDOWS.md). Esses controles de publicação
não comprovam funcionamento do produto no PC do usuário.

## Itens corrigidos no código

1. Ponte HTTP: autenticada com token privado, limitada a 127.0.0.1, valida Host,
   nega Origin de sites, recusa GET /mcp não implementado e métodos JSON-RPC inválidos.
2. Controle de acesso: leitura por padrão; escrita, comandos do terminal e controle
   de interface exigem autorização específica no ambiente. O processo remoto expõe
   somente as ferramentas liberadas.
3. Limites: corpo HTTP até 128 KiB; leitura de arquivo até 1 MB efetivo; captura até
   6 MB; comandos até 30 s; busca limitada a 30 mil entradas; listagem sinaliza
   quando mais de 500 arquivos existem.
4. Arquivos: leitura UTF-8 protegida contra binários, metadados, listagem, pesquisa,
   criação de pastas e movimentação com checagem de escopo e colisões.
5. Processos Windows: listagem de até 400 processos sem oferecer terminação
   automática. Interface utiliza a mesma camada do agente.
6. Painel: janela de arquivos, busca, terminal opcional, processos, captura,
   comandos, configurações e página Sobre; visual escuro e ícone próprio.
   Abertura manual de executáveis requer confirmação.
7. Instalador: Inno Setup em português, sem administrador por padrão, sem iniciar
   com Windows, sem reiniciar o Windows; inclui atalho e desinstalador.
8. Compilação Windows: testes unitários, abertura do executável, compilação da
   ponte, instalação e desinstalação automatizadas, hash SHA-256 e publicação
   de artefatos de desenvolvimento no GitHub Actions. Testes de desinstalação
   verificam remoção de executáveis e token de teste. Uma publicação assinada
   exige também os controles descritos acima.
9. CI: mudanças Windows não devem acionar builds Android; compilações
   obsoletas são canceladas pela concorrência do workflow.
10. Identidade visual: imagem de pena gerada localmente, com licença própria
    do projeto, incorporada ao executável e ao assistente de instalação.

## Comandos MCP disponíveis

Leitura por padrão:
status, list_directory, search_files, read_text, get_file_info, list_processes.

Escrita opcional:
write_text, create_directory, move_file.

Terminal opcional:
run_command.

Controle visual opcional:
open_url, open_path, click, screenshot.

Total: 14 comandos. Nenhum comando executa silenciosamente por ativar
o Windows; permissões adicionais exigem configurar variáveis locais e
iniciar o agente com essas configurações.

## Evidências técnicas

- Workflow: https://github.com/willsonAlphamna/SamsungRemoteTeste/actions/workflows/navix-livre-build.yml
- Testes: https://github.com/willsonAlphamna/SamsungRemoteTeste/actions/workflows/navix-livre-tests.yml
- Exemplo histórico de build 0.3 (não comprova assinatura nem valida a 0.3.1):
  https://github.com/willsonAlphamna/SamsungRemoteTeste/actions/runs/38592516981
- Código disponível no PR:
  https://github.com/willsonAlphamna/SamsungRemoteTeste/pull/2

Uma execução verde confirma apenas os cenários automatizados naquele commit;
novas alterações precisam de nova execução bem-sucedida.

## Pendências não homologadas

**P1 — Conexão ChatGPT pela internet:** NÃO implementada. O MCP é local e
não conecta automaticamente esta conversa à máquina. Integração externa
depende de HTTPS confiável, autenticação/OAuth, autorização do cliente MCP,
rede e suporte no ChatGPT. Não publicar a porta 8765 no roteador.

**P1 — Teste no computador do usuário:** NÃO realizado. Conferir Windows,
consumo de RAM, antivírus/SmartScreen, instalação/desinstalação, arquivos
do OneDrive e ponte local na máquina autorizada.

**P2 — Paridade Desktop Commander:** NÃO comprovada. Faltam processamento
PDF/DOCX, edição estruturada avançada, gerenciamento de sessões e processos,
automação de navegador, streaming de telas, múltiplos dispositivos e outras
funções. O Navix é programa independente, não cópia do Desktop Commander.

**P1 — Publicação assinada:** bloqueada por ausência de identidade de assinatura
confiável configurada. O fluxo 0.3.1 precisa passar por uma execução Windows com
essa identidade e por validação dos arquivos publicados. Não há garantia de
ausência de avisos de reputação mesmo depois da assinatura. Não desabilitar
proteções para substituir essa etapa.

**P2 — Integração de voz ou narrador de IA:** NÃO implementada e não
incluída no custo zero. Eventuais serviços de IA podem cobrar.

**P3 — Aparência idêntica à imagem conceitual:** NÃO verificada por captura
real. Tkinter é a implementação atual; não equivale automaticamente
à arte ilustrativa mostrada na conversa.

## Segurança operacional

- Não executar como Administrador.
- Não compartilhar arquivo bridge.token e não usar token de teste como segredo real.
- Evitar conceder escrita/comandos/controle visual a agentes não confiáveis.
- Não abrir a porta 8765 para a internet.
- Não desativar antivírus nem proteções do Windows.
- Não confundir software sem mensalidade própria com serviços externos
  sem custo ou com acesso remoto ilimitado.

## Critério de conclusão

Para considerar esta versão homologada na máquina do usuário: testes e
compilação verdes no commit final, publicação assinada com editor esperado,
carimbo de tempo e tag no mesmo commit, download verificado por SHA-256,
instalação e desinstalação comprovadas no Windows dele, GUI funcional e
comprovação da conexão remota somente se um canal externo seguro for
configurado e autorizado. Até lá, o produto é um MVP experimental auditado,
não um substituto integral certificado do Desktop Commander.
