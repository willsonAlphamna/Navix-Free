# AEGIS Control — arquitetura de desenvolvimento

Esta ramificação isola o projeto AEGIS do projeto Samsung existente.

## Implementado no código desta ramificação
- Inventário e SHA-256 de arquivos em workspace com validação de caminhos.
- Cópias exclusivas sem sobrescrita.
- Diagnósticos por lista de comandos permitidos, timeout e sem shell.
- Orquestrador de tarefas concorrentes com estados, erros e auditoria JSONL.
- Aprovação de uso único para operações (o usuário da interface precisa aprovar; o sistema não fornece aprovação automática).
- Adaptador Playwright para Chromium com navegador visível, navegação HTTPS por domínio permitido, cliques, preenchimento e captura de tela.
- Testes unitários em Windows e Linux via GitHub Actions.

## Preparação local
Requer Python 3.12. Testes: `python -m unittest discover -s tests -v`.
Para usar o adaptador de navegador: `pip install playwright` e `python -m playwright install chromium`.

## O que ainda NÃO está pronto
- Servidor de controle remoto seguro com pareamento, autenticação, TLS e revogação.
- Interface do AEGIS conectada a estes novos módulos.
- Integração real com um provedor de IA (precisa de credenciais fornecidas com segurança pelo usuário e limites de ações).
- Automação de mouse/teclado do Windows com consentimento.
- Empacotamento do agente, assinatura do instalador, desinstalador e atualização automática.
- Testes E2E com navegador, redes reais e UI do Windows, e auditoria de segurança externa.

Não exponha o agente na internet sem autenticação, TLS, confirmação e mecanismos de revogação. **Esta ramificação não demonstra superioridade de três vezes sobre o Desktop Commander.**
