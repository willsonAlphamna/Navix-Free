# GUIA: instalar Navix Livre no Windows

**Situação em 14/10/2026:** o instalador 0.3.0 enviado anteriormente está sem
assinatura digital. A versão 0.3.1 está em desenvolvimento e não tem uma
publicação assinada pronta. Aguarde uma release que cumpra as verificações
abaixo; não use o instalador antigo para contornar o alerta.

## 1. Baixar

1. Acesse somente as [Releases oficiais](https://github.com/willsonAlphamna/SamsungRemoteTeste/releases).
2. Escolha uma versão pública cujas notas confirmem assinatura válida e informem
   o editor esperado, o commit de origem e os arquivos de verificação.
3. Baixe **NavixLivre-Setup-Windows.exe**, **SHA256.txt** e **BUILD_INFO.json**
   da mesma versão. Os hashes correspondem aos arquivos finais após assinatura.
4. Não use os artefatos de desenvolvimento do GitHub Actions para esta instalação:
   eles são compilados sem assinatura e identificados dessa forma.

## 2. Conferir antes de instalar

1. No Explorador de Arquivos, clique com o botão direito no instalador e abra
   **Propriedades > Assinaturas Digitais > Detalhes**. A assinatura precisa ser
   válida e o editor deve corresponder à identidade indicada na release.
2. No PowerShell, na pasta do download, consulte:

   ```powershell
   Get-FileHash .\NavixLivre-Setup-Windows.exe -Algorithm SHA256
   Get-AuthenticodeSignature .\NavixLivre-Setup-Windows.exe |
     Format-List Status, StatusMessage, SignerCertificate, TimeStamperCertificate
   ```

3. Compare o hash com **SHA256.txt**. Confira `Status: Valid`, o editor
   esperado e a presença do certificado de carimbo de tempo. O hash sozinho
   não comprova que o editor é confiável.
4. Se faltar assinatura, houver divergência ou o Windows bloquear a execução,
   pare e informe a versão e o texto do aviso. Não desative o SmartScreen,
   o antivírus ou outras proteções.

## 3. Instalar

1. Execute NavixLivre-Setup-Windows.exe.
2. Siga o assistente em português e marque o atalho da Área de Trabalho, se desejar.
3. O programa instala na pasta de aplicativos do usuário (não precisa de acesso de Administrador).
4. Ele NÃO liga sozinho com o Windows e NÃO reinicia o computador.
5. Ao final, abra o atalho **Navix Livre**.

## 4. Testar

1. Na aba **Arquivos**, confira a pasta Área de Trabalho e abra pastas com dois cliques.
2. Na aba **Configurações**, confira as permissões (escrita e terminal vêm bloqueados por padrão).
3. Na aba **Configurações**, clique em **Iniciar ponte MCP local**. Abre uma janela de console da ponte. Deixe essa janela aberta durante o teste.
4. O endereço local é http://127.0.0.1:8765/mcp, mas a página não abre como site comum. É um endpoint MCP e exige autenticação.
5. Para encerrar, clique em **Parar conexão MCP local** (se iniciou pelo painel) ou feche a janela da ponte.
6. Se a conexão local falhar, copie apenas a mensagem de erro, sem compartilhar credenciais.

## 5. Acesso remoto e ChatGPT

O software **não conecta esta conversa do ChatGPT automaticamente ao PC**. Ele inclui uma ponte MCP **local** com token em um arquivo privado do usuário. Ela só escuta no endereço 127.0.0.1, sem abrir portas públicas.

Para acesso por outra máquina ou para uso com serviços em nuvem, são necessárias configurações adicionais de rede segura, compatibilidade com o cliente MCP e autorização da conta. Não publique a porta 8765 no roteador nem divulgue o token. O programa e o instalador são gratuitos, mas serviços de IA, internet ou nuvem externos podem cobrar.

## 6. Desinstalar

Use **Menu Iniciar > Navix Livre > Desinstalar Navix Livre**, ou **Configurações > Aplicativos**. A remoção apaga os executáveis instalados e a credencial privada gerada pela ponte; não mexe nos seus arquivos pessoais.

## 7. Sem mensalidade própria

O software é de código aberto sob licença MIT; não há cobrança por instalação ou pelo número de comandos. Isso não elimina cobranças de plataformas externas ou custos do responsável pela distribuição, como um serviço de assinatura de código.

## 8. Se o Windows mostrar alerta

O arquivo 0.3.0 antigo foi confirmado sem assinatura. Na 0.3.1, o fluxo de
publicação exige assinatura, mas isso não garante ausência de aviso para um
executável novo. A Microsoft explica a diferença entre assinatura e
[reputação SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).
Não prossiga apenas porque o nome do arquivo parece correto. Registre o
aviso para análise e mantenha as proteções ativas. Veja o diagnóstico em
[ASSINATURA_WINDOWS.md](ASSINATURA_WINDOWS.md).

## 9. Suporte técnico

Se ocorrer algum erro, anote a etapa (baixar, instalar, listar arquivos, iniciar ponte) e o texto da falha. Não envie senhas, tokens ou arquivos pessoais.
