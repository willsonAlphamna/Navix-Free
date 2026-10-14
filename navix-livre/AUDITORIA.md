# Auditoria técnica — Navix Livre
Data: 14/10/2026 | Versão: 0.3.0 | Branch: feature/navix-livre-mcp

## Escopo

Revisão de segurança, protocolo MCP, arquivos, painel gráfico Windows, processo de
compilação, instalador, remoção, dependências e documentação. Esta auditoria não é
uma homologação do computador do usuário, nem um pentest independente.

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
   de artefatos no GitHub Actions. Testes de desinstalação verificam remoção
   de executáveis e token de teste.
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
- Exemplo de build 0.3 concluído e íntegro:
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

**P2 — Assinatura digital comercial:** NÃO disponível; SmartScreen pode
alertar sobre aplicativo novo. Não desabilitar antivírus.

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
compilação verdes no commit final, download verificado por SHA-256,
instalação e desinstalação comprovadas no Windows dele, GUI funcional e
comprovação da conexão remota somente se um canal externo seguro for
configurado e autorizado. Até lá, o produto é um MVP experimental auditado,
não um substituto integral certificado do Desktop Commander.
