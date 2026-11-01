# NavixX Desktop 0.2.12 + AdminBridge 0.2.0

Esta compilacao usa exatamente a tag navix-desktop-v0.2.12 como base. O
instalador AdminBridge substitui o executavel do NavixX na mesma pasta, preserva
configuracoes e usa seu servidor MCP, sua sessao e suas 44 ferramentas. Nao usa
o agente independente Windows_Admin_Full_v0.1.0; nao execute aquele instalador.

## Fluxo

1. Feche o NavixX antes de instalar a compilacao AdminBridge.
2. O instalador abre NavixX Desktop Admin e solicita a elevacao normal UAC.
3. Entre com o login local do NavixX. Ele continua obrigatorio; nenhuma senha e burlada.
4. Neste modo, o NavixX ativa os quatro recursos sem prazo neste processo,
   registra o PC automaticamente na ponte HTTPS e abre o navegador para vinculo.
5. No navegador aberto, acesse Windows Admin Full no ChatGPT e autorize a conexao.
   O navegador precisa ser o mesmo no qual o instalador vinculou o PC.
6. A partir dai a ponte reaproveita o registro e se reconecta sozinha durante a
   sessao. O atalho NavixX Desktop Admin repete UAC e login local quando necessario.

Nao ha chave de API OpenAI ou ID de tunel para copiar. A autorizacao inicial do
ChatGPT e o UAC pertencem aos respectivos sistemas e nao sao suprimidos.

O botao ChatGPT Admin integrado permite ativar o modo no painel; Vincular
navegador ao PC recupera o vinculo em outro navegador. PARAR ACESSO e Bloquear
revogam as permissoes locais. Mudancas de porta e token local sao acompanhadas
pela ponte em memoria. Credenciais remotas ficam em admin-bridge.dpapi, ligadas
ao mesmo usuario Windows. Os tokens locais MCP nao sao gravados nem enviados a nuvem.

Nao habilita inicializacao com Windows nem ignora a senha local. Um pedido
remoto nunca ativa uma sessao local revogada. Nao cria privilegio SYSTEM, nao
controla a tela segura e nao desativa protecoes do Windows.

## Limites

A ponte aceita comandos de ate 35 segundos, argumentos de ate 48 KB e respostas
de ate 1,9 MB. Tarefas longas podem ser iniciadas em segundo plano e consultadas.
Se houver timeout depois do envio, o resultado e incerto: nao repita cegamente.
A reconexao repete o envio de um resultado pendente, nunca o comando do Windows.
A fila permite no maximo uma chamada em andamento por PC.

A ponte armazena temporariamente comandos e resultados por ate cinco minutos;
a coleta ocorre periodicamente. A Cloudflare pode reter backups de armazenamento
conforme sua politica. Tokens e credenciais nao sao incluidos no repositorio ou
instalador; observabilidade e logs de requisicoes do Worker estao desativados.
Os limites e disponibilidade do plano Cloudflare se aplicam. Nao ha promessa de
acesso eterno nem de funcionamento durante PC desligado, bloqueado ou sem rede.

## Validacao

Testes locais de ponte: OAuth PKCE, replay de codigo/refresh/pareamento,
isolamento de dispositivos, bloqueio de chamada sem autenticacao e quando offline,
fila com resposta em blocos. Testes locais de integracao: porta/token atuais,
parada/retomada e segredo fora de logs. A suite Windows existente e os testes de
instalacao/desinstalacao rodam no CI. Essas evidencias nao substituem o teste real
ChatGPT -> computador do Wilson.
