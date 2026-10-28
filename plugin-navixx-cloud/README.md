# NavixX Desktop Cloud — pacote de plugin

Versão do plugin 0.3.1 (Cloud Desktop 0.3.0-alpha.8), para teste. Esta pasta contém o pacote do plugin remoto MCP para
ChatGPT. O usuário final não precisa criar chave de API ou túnel individual.

## Uso previsto

1. Instalar o aplicativo NavixX Desktop Cloud no Windows.
2. Autorizar uma sessão local e selecionar as permissões.
3. Clicar em **Vincular ao ChatGPT** e guardar o ID e código de 6 dígitos.
4. No ChatGPT, conectar o plugin NavixX e inserir o ID e o código quando a
   página de autorização aparecer.
5. Iniciar a conexão Cloud no Windows. Revogar/parar encerra o acesso.

A versão 0.2.11 usa uma pasta, perfil e conexão diferentes e não deve ser
desinstalada durante os testes.

## Publicação

A integração remota é operada no servidor Cloudflare de staging. Para
distribuição geral, será necessária a verificação de domínio e identidade,
teste do MCP, revisão e aprovação pela OpenAI. Não publicar um pacote com
ferramentas de execução remota antes dos testes de autorização/revogação.

Fonte: https://developers.openai.com/plugins/deploy/submission

## Autenticação
O plugin usa MCP Streamable HTTP com modo misto: ferramentas são descobertas sem login, mas o controle do Windows continua bloqueado até o OAuth e a autorização local. A ferramenta exclusiva `navixx_cloud_connection_status` anuncia se o canal está online; não confundir isso com execução remota verificada. Atualizar arquivos do GitHub não atualiza automaticamente o plugin já instalado no ChatGPT. Nunca configurar o conectaX antigo como substituto.
