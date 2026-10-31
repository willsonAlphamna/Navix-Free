# NavixX Desktop 0.2.12 — correção experimental de estabilidade

Base: tag `navix-desktop-v0.2.11`. Não altera nem substitui o código da linha Cloud Preview 0.3.

## Falha observada no computador do proprietário (31/10/2026)
- Com a janela minimizada, ocorreram atrasos do processo e timeouts nas sondagens locais.
- O supervisor reiniciou `tunnel-client` após falhas de saúde, seguido de tentativas `tunnel.start_failed`.
- O processo voltou a iniciar e as sondagens recuperaram HTTP 200 após alguns minutos.
- Não está comprovado que minimizar seja a causa raiz; rede e responsividade local podem contribuir.

## Alterações
1. Limiares de saúde: em vez de matar um cliente vivo após três falhas curtas, exige três falhas e ao menos 120 segundos de indisponibilidade local **contínua**. Resposta saudável zera a janela de falhas.
2. Supervisor em thread de segundo plano: chama `check()` e `connect()` para recuperar uma sessão **já autorizada**, independente do `tk.after` da interface e da visibilidade da janela.
3. Revogação: `stop()` invalida o supervisor; não reconecta após sessão encerrada.
4. Testes offline de travamento transitório e de repetição de conexão em segundo plano.

## Limites e liberação
- Builds/artefatos dependem de testes Windows no GitHub Actions.
- Autorização do proprietário e consentimento do ChatGPT não são contornados.
- A versão anterior 0.2.11 instalada deve permanecer intocada até o proprietário instalar manualmente a atualização.
- Homologação exige teste de pelo menos 60 minutos minimizado com observação independente de acesso real e registros `health_*`/ `start_failed`.
- Este hotfix **não comprova** sozinho a causa exata do congelamento do Windows.
