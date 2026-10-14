# NAVIX LIVRE — REGISTRO DE CONTINUIDADE DO PROJETO
**Atualizado em:** 14/10/2026  
**Projeto:** Navix Livre — Windows / ponte MCP local  
**Situação:** 0.3.0 publicada sem assinatura; 0.3.1 em desenvolvimento com publicação condicionada a uma identidade Authenticode confiável. Acesso remoto externo e homologação no PC ainda pendentes.
**Objetivo do registro:** permitir retomar o desenvolvimento em outras conversas sem reconstruir decisões e avanços.

> Este repositório é público. NUNCA adicionar senhas, tokens de acesso, credenciais, chaves privadas, capturas pessoais ou outros dados sigilosos.

## Atualização: bloqueio SmartScreen e assinatura Windows

**Continuação:** preparada uma rota alternativa MSIX/Microsoft Store, sem
compra de certificado. `navix-livre/store/build_msix.py` gera um pacote de
submissão com a identidade oficial do Partner Center; a CI valida também um
pacote com identidade de teste. O workflow manual aceita `prepare_store=true`
e os campos de identidade da Store. **Não confundir pacote de submissão sem
assinatura com instalador pronto.** A conta do titular, a reserva do aplicativo,
a análise e a assinatura pela Microsoft ainda estão pendentes. Roteiro em
`navix-livre/PUBLICAR_NA_MICROSOFT_STORE.md`; política de privacidade em
`navix-livre/PRIVACIDADE.md`. Não enviar novo link de instalação por e-mail
antes de haver uma versão publicada e verificada.

O usuário encontrou o aviso "O Windows protegeu o computador" ao abrir a
0.3.0. O instalador exato foi baixado e conferido pelo SHA-256 registrado
abaixo: a tabela de certificados PE tem offset=0 e size=0, confirmando
ausência de assinatura Authenticode incorporada.

A correção do fluxo de publicação está preparada para a 0.3.1:

- Builds automáticos produzem somente artefatos de desenvolvimento,
  explicitamente sem assinatura; não substituem mais uma release pública.
- Publicação manual exige identidade de assinatura real, titular esperado,
  assinatura e timestamp verificados no painel, ponte, instalador e
  desinstalador, além de testes de instalação e remoção no runner Windows.
- Cada release nova tem tag própria, commit de origem e hashes em
  `BUILD_INFO.json`; o workflow não usa mais `--clobber`.
- **Certificado/serviço de assinatura ainda não disponibilizado.** Não
  apresentar a 0.3.1 como release assinada pronta para instalar. Ver
  [configuração e limites](navix-livre/ASSINATURA_WINDOWS.md).
- Assinatura confiável não garante reputação imediata no SmartScreen. Não
  desativar proteções do Windows nem usar certificado autoassinado como
  correção para distribuição pública.

Os resultados e links da 0.3.0 nas seções seguintes são históricos e não
comprovam assinatura, validação ou publicação da 0.3.1.

## 1. Endereços que importam
- Repositório: https://github.com/willsonAlphamna/SamsungRemoteTeste
- Branch de trabalho: `feature/navix-livre-mcp`
- Pull request de integração, ainda aberto: https://github.com/willsonAlphamna/SamsungRemoteTeste/pull/2
- Código do Navix: https://github.com/willsonAlphamna/SamsungRemoteTeste/tree/feature/navix-livre-mcp/navix-livre
- Relatório técnico de auditoria: https://github.com/willsonAlphamna/SamsungRemoteTeste/blob/feature/navix-livre-mcp/navix-livre/AUDITORIA.md
- Release 0.3.0 (download do instalador e checksum): https://github.com/willsonAlphamna/SamsungRemoteTeste/releases/tag/navix-livre-v0.3.0
- Instalador Windows diretamente: https://github.com/willsonAlphamna/SamsungRemoteTeste/releases/download/navix-livre-v0.3.0/NavixLivre-Setup-Windows.exe
- SHA-256 para conferir download: https://github.com/willsonAlphamna/SamsungRemoteTeste/releases/download/navix-livre-v0.3.0/SHA256.txt
- Workflow de build: https://github.com/willsonAlphamna/SamsungRemoteTeste/actions/workflows/navix-livre-build.yml
- Workflow de testes: https://github.com/willsonAlphamna/SamsungRemoteTeste/actions/workflows/navix-livre-tests.yml
- **Execução aprovada:** https://github.com/willsonAlphamna/SamsungRemoteTeste/actions/runs/38593316944
- Commit auditado que gerou o instalador da execução acima: `a4982115076553b38df0a4237ed755a0483e2265`
- Artefatos: `NavixLivre-Instalador-Windows` e `NavixLivre-Portatil-Windows`.

## 2. Resultado técnico comprovado até este registro
- O GitHub Actions concluiu com **success** o workflow **Navix Livre - Instalador Windows** nº 38593316944.
- Nesse workflow passaram testes unitários, geração de ícones, compilação do painel, teste de abertura do programa, compilação da ponte, teste do executável da ponte, criação do instalador, instalação/desinstalação automatizada, SHA-256 e publicação dos artefatos/release.
- **19 testes automatizados passaram** em uma execução do último commit avaliado, incluindo testes de acesso negado, escopo de arquivos, leitura e escrita protegidas, chamadas MCP, Host e Origin.
- Instalador `NavixLivre-Setup-Windows.exe` publicado na release acima; não significa que tenha sido instalado no PC do usuário.
- GitHub mostra a versão 0.3.0 e disponibiliza o checksum para download.

## 3. Arquitetura implementada
- `navix-livre/navix_livre.py`: agente local, ferramentas MCP e permissões.
- `navix-livre/navix_gui.py`: interface Windows Tkinter com tema escuro.
- `navix-livre/navix_remote.py`: ponte HTTP/MCP somente em `127.0.0.1:8765`, autenticada por token local.
- `navix-livre/make_assets.py`: gera ícone de pena e imagens do assistente de instalação.
- `navix-livre/installer.iss`: instalador e desinstalador Inno Setup.
- `navix-livre/test_navix.py` e `navix-livre/test_remote.py`: testes.
- `navix-livre/COMO_INSTALAR.md`, `README.md`, `AUDITORIA.md`: instruções, escopo, evidências e limitações.
- `.github/workflows/navix-livre-build.yml` e `navix-livre-tests.yml`: builds e testes Windows.

## 4. Funções MCP existentes na v0.3.0
**Leitura, disponíveis por padrão:** `status`, `list_directory`, `search_files`, `read_text`, `get_file_info`, `list_processes`.

**Escrita, opcionais e desligadas por padrão:** `write_text`, `create_directory`, `move_file`.

**Terminal, opcional e desligado por padrão:** `run_command`.

**Controle visual, opcional e desligado por padrão:** `open_url`, `open_path`, `click`, `screenshot`.

Total: **14 ferramentas MCP**, com autorização seletiva. A interface gráfica inclui explorador de arquivos, busca, detalhes, importação/exportação manual de arquivos, terminal, processos, captura de tela, configurações e controles para iniciar/parar ponte local. NÃO apresentar funções inexistentes como concluídas.

## 5. Design desejado e o que efetivamente existe
- Usuário pediu interface profissional semelhante ao Desktop Commander, preferencialmente igual ou melhor, com painel escuro, explorador, terminal, processos, visual robusto, ícone de pena, progresso do instalador, atalhos e desinstalador.
- **Uma imagem apresentada na conversa foi gerada como conceito**, e NÃO é captura real do software. Não mostrar essa imagem como prova da versão instalada.
- O painel escuro real foi implementado com Tkinter e compilado, mas não foi verificado visualmente no computador do usuário, portanto NÃO garantir paridade pixel a pixel com conceito.
- O instalador Inno Setup possui a barra de progresso padrão e imagens de marca.
- O programa NÃO deve iniciar automaticamente com o Windows, reiniciar o PC ou exigir permissão de Administrador sem necessidade.

## 6. Segurança e arquitetura de acesso
- Ponte 100% local, na interface loopback; não abrir porta `8765` no roteador.
- Token local privado; não compartilhar ou incluir em arquivos públicos.
- Escrita, comandos do terminal e controle visual só com permissão explícita.
- Adicionadas verificações de Host, Origin, formato da mensagem e limites de tamanho.
- Escopo padrão de leitura restrito à Área de Trabalho; ampliar somente para caminhos escolhidos pelo proprietário.
- Software de código aberto licença MIT, sem mensalidade do próprio projeto. **Isso não significa integração gratuita e ilimitada com serviços externos nem substituição automática de limites de uso do ChatGPT.**
- Executável não tem certificado comercial de assinatura; verificar proveniência e checksum e não desabilitar antivírus.

## 7. O que foi corrigido na auditoria de 14/10/2026
1. Proteções HTTP/MCP e testes de requisições inválidas.
2. Restrições de Host e Origin para proteger a ponte local.
3. Restrições de leitura de arquivos grandes/binários; sinalização de listagens incompletas e limite na varredura de arquivos.
4. Melhorias de UX para arquivo, buscas, detalhes e consulta de processos.
5. Ícone e telas de instalação do Navix; confirmação antes de abrir arquivos executáveis manualmente.
6. Inclusão de metadados, criação de pastas, movimentação e listagem de processos como ferramentas MCP.
7. Testes de abertura real do executável no ambiente automatizado Windows.
8. Testes de instalação, desinstalação e remoção do token/arquivos no ambiente de CI.
9. Redução de compilações Android desnecessárias e cancelamento de execuções antigas de CI.
10. Documentação de lacunas e evidências no `AUDITORIA.md`.

## 8. Pontos NÃO concluídos — NÃO afirmar que estão prontos
**Alta prioridade**
1. Testar na máquina Windows real do proprietário com atenção à pouca memória RAM, permissões, atalhos, interface, funcionamento em OneDrive, instalador, execução e limpeza da desinstalação.
2. Desenvolver/autorizar canal remoto seguro via HTTPS, identidade e autenticação de cliente MCP compatível; apenas então testar conversa do ChatGPT → PC com autorização. A versão atual NÃO dá a esta conversa acesso automático ao computador.
3. Validar limites de acesso, expiração/revogação de sessão, autorização antes de comandos destrutivos e proteção dos arquivos pessoais no cenário de rede real.

**Próximas evoluções**
4. Comparar recursos com o Desktop Commander sem prometer equivalência inexistente (PDF/DOCX, operações avançadas, sessões/processos, integração do navegador, dispositivos múltiplos, automação visual e melhor tratamento de erros).
5. Testar fidelidade visual à interface-conceito; corrigir usabilidade e acessibilidade da janela em telas menores.
6. Verificar se o Windows exibe alertas de software não assinado e estudar assinatura digital se necessária.
7. Caso haja interesse, avaliar voz sintética e IA integrada apenas com serviço/licença autorizados e custos claros.
8. Melhorar logs, relatórios de falhas, testes automatizados de segurança e revisão independente de código.
9. Avaliar merge do PR #2 na main após homologação, sem afetar projeto Android existente.

## 9. Roteiro para retomar com o usuário
1. Abrir ESTE arquivo e `AUDITORIA.md`.
2. Consultar PR #2, branch, últimos commits e última execução verde do workflow. A 0.3.0 é histórica e sem assinatura; conferir identidade, versão, commit e hashes antes de indicar uma release nova ao usuário.
3. Inspecionar o código antes de alegar novas funcionalidades.
4. Se acesso remoto ao PC estiver disponível e autorizado, verificar a máquina, com ações não destrutivas primeiro; caso haja limite do Desktop Commander, não afirmar que consegue controlar o Windows.
5. Confirmar se versão instalada corresponde ao checksum/commit auditado.
6. Para funções sensíveis, requerer autorização e usar permissões mínimas.
7. Registrar neste arquivo (ou em novo relatório) o que foi realmente testado e corrigido.
8. Relatar de maneira objetiva: concluído, pendente, problema e próximos passos.

## 10. Pedido que originou este registro
Depois de solicitar uma auditoria geral com correção das faltas, o usuário disse: **“Grava tudo”**. Assim, este documento conserva a situação do projeto, links, evidências e a lista de trabalho. A informação foi salva no próprio GitHub, não em uma configuração de memória pessoal. Não adicionar dados pessoais nem credenciais ao repositório público.
