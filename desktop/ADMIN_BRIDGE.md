# NavixX Desktop 0.2.12 + AdminBridge 0.2.1

Esta compilacao usa exatamente a tag navix-desktop-v0.2.12 como base. O
instalador AdminBridge substitui o executavel do NavixX na mesma pasta, preserva
configuracoes e usa seu servidor MCP, sua sessao e suas 44 ferramentas. Nao usa
o agente independente Windows_Admin_Full_v0.1.0; nao execute aquele instalador.

## Fluxo

1. Feche o NavixX antes de instalar a compilacao AdminBridge.
2. Instale **somente o NavixX Desktop com AdminBridge** no Windows: a ponte ja
   vem dentro do aplicativo, nao existe um segundo EXE para instalar.
3. Abra NavixX Desktop Admin (o Windows pode solicitar UAC) e entre com o
   login local. Nenhuma senha ou aprovacao e ignorada.
4. Escolha as permissoes e clique em **Conectar / Autorizar**. O mesmo botao
   inicia o MCP local e a ponte ChatGPT em segundo plano.
5. Na primeira utilizacao, o NavixX registra o PC e abre um navegador para
   vinculo. No ChatGPT, habilite o plugin **Windows Admin Full** e autorize
   a conexao. Use o mesmo navegador que fez o primeiro pareamento.
6. Depois do primeiro vinculo, os proximos cliques em Conectar reutilizam a
   credencial local DPAPI e a ponte se reconecta automaticamente enquanto
   a sessao estiver ativa. PARAR ACESSO interrompe o controle remoto.

Nao ha chave de API OpenAI ou ID de tunel para copiar. A autorizacao inicial do
ChatGPT e o UAC pertencem aos respectivos sistemas e nao sao suprimidos.

O botao Conectar / Autorizar tambem inicia a ponte sem ampliar as permissoes
selecionadas. ChatGPT Admin integrado e um modo opcional de acesso completo
com UAC; Vincular navegador ao PC recupera o vinculo em outro navegador,
sem conceder permissoes locais automaticamente. PARAR ACESSO e Bloquear
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
O agente aguarda dez segundos entre consultas sem trabalho, evitando excesso de
requisicoes. Erros temporarios usam espera exponencial com variacao aleatoria,
respeitando o cabecalho Retry-After (incluindo HTTP 429). Resultados pendentes
passam a ser armazenados com protecao DPAPI no mesmo usuario Windows e sao
reenviados apos reiniciar o aplicativo, ate confirmacao ou expiracao. Isso nao
repete comandos ou cliques remotos. Um resultado corrompido ou pertencente a
outro dispositivo e ignorado; o arquivo original e preservado para diagnostico.
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

## Continuidade e limites da disponibilidade

O ajuste reduz riscos de HTTP 429 causado por consultas muito frequentes no
proprio AdminBridge, mas nao elimina limites impostos pelo ChatGPT/MCP,
Cloudflare, rede local, energia ou autorizacao do usuario. O erro 429 no
gateway ConectaX antigo nao e corrigido por esta ponte de outro servico.
Nao ha failover para outro Worker sem demonstrar armazenamento, identidade
e fila compartilhados: alternar para uma ponte sem o mesmo estado pode
duplicar ou perder comandos. Antes de habilitar um caminho redundante,
validar dois enderecos contra a **mesma** fila protegida, revogacao,
permissoes e auditoria em teste de corte de conexao.

Nao ha tolerancia a falhas completa: se o processo for encerrado durante uma
acao Windows, nao e possivel saber com certeza se ela foi executada. Nesse
caso, a ponte nao repete automaticamente. A retomada depende de sessao
local autorizada e de novo contato com o servico.
