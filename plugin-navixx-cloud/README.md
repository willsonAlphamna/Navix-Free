# NavixX Desktop Cloud — pacote de plugin

Versão 0.3.0, para teste. Esta pasta contém o pacote do plugin remoto MCP para
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
