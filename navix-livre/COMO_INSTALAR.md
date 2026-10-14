# GUIA: instalar Navix Livre no Windows

## 1. Baixar
1. Acesse a execução mais recente de **Navix Livre - Instalador Windows** no GitHub Actions deste repositório.
2. Entre com sua conta GitHub, se solicitado.
3. Na seção **Artifacts**, escolha **NavixLivre-Instalador-Windows** e baixe o ZIP.
4. Extraia o ZIP no Windows; o instalador se chama **NavixLivre-Setup-Windows.exe**.
5. Verifique que está baixando do seu repositório oficial e NÃO de links enviados por desconhecidos.

## 2. Instalar
1. Execute NavixLivre-Setup-Windows.exe.
2. Siga o assistente em português e marque o atalho da Área de Trabalho, se desejar.
3. O programa instala na pasta de aplicativos do usuário (não precisa de acesso de Administrador).
4. Ele NÃO liga sozinho com o Windows e NÃO reinicia o computador.
5. Ao final, abra o atalho **Navix Livre**.

## 3. Testar
1. Na aba **Arquivos**, confira a pasta Área de Trabalho e abra pastas com dois cliques.
2. Na aba **Configurações**, confira as permissões (escrita e terminal vêm bloqueados por padrão).
3. Na aba **Configurações**, clique em **Iniciar ponte MCP local**. Abre uma janela de console da ponte. Deixe essa janela aberta durante o teste.
4. O endereço local é http://127.0.0.1:8765/mcp, mas a página não abre como site comum. É um endpoint MCP e exige autenticação.
5. Para encerrar, clique em **Parar conexão MCP local** (se iniciou pelo painel) ou feche a janela da ponte.
6. Se a conexão local falhar, copie apenas a mensagem de erro, sem compartilhar credenciais.

## 4. Acesso remoto e ChatGPT
A versão entregue agora **não conecta esta conversa do ChatGPT automaticamente ao PC**. O software inclui uma ponte MCP **local** com token em um arquivo privado do usuário. Ela só escuta no endereço 127.0.0.1, sem abrir portas públicas.

Para acesso por outra máquina ou para uso com serviços em nuvem, são necessárias configurações adicionais de rede segura, compatibilidade com o cliente MCP e autorização da conta. Não publique a porta 8765 no roteador nem divulgue o token. O programa e o instalador são gratuitos, mas serviços de IA, internet ou nuvem externos podem cobrar.

## 5. Desinstalar
Use **Menu Iniciar > Navix Livre > Desinstalar Navix Livre**, ou **Configurações > Aplicativos**. A remoção apaga os executáveis instalados e a credencial privada gerada pela ponte; não mexe nos seus arquivos pessoais.

## 6. Sem mensalidade
O software é de código aberto sob licença MIT; não há cobrança por instalação ou pelo número de comandos. Isso não elimina cobranças de plataformas externas.

## 7. Se o Windows mostrar alerta
Como o instalador não possui certificado de assinatura de código comercial, o Windows pode exibir uma confirmação de reputação. Confira o nome do arquivo e que veio do seu GitHub antes de executar. Nunca desative o antivírus só para instalá-lo.

## 8. Suporte técnico
Se ocorrer algum erro, anote a etapa (baixar, instalar, listar arquivos, iniciar ponte) e o texto da falha. Não envie senhas, tokens ou arquivos pessoais.
