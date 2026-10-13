# Validacao AEGIS

## Executar no Windows
Instale Python 3.12 e rode na raiz do repositório:

```powershell
python -m unittest discover -s tests -v
python aegis_cli.py --workspace . system
python aegis_cli.py --workspace . inventory
python aegis_cli.py --workspace . sha256 aegis_cli.py
python aegis_cli.py --workspace . diagnostic hostname
```

## Automação de navegador
Instale Playwright e o Chromium (`pip install playwright` e `python -m playwright install chromium`). O adaptador de navegador só pode navegar em destinos HTTPS cadastrados numa lista de permissões.

## Critérios de homologação pendentes
- Teste de instalação e de desinstalação em Windows limpo.
- Teste completo e visual de clique, texto, screenshot, permissões e navegação.
- Agente remoto autenticado, criptografado, com revogação e limites de escopo.
- Auditoria independente, testes de segurança adversariais e avaliação de recuperação de falhas.
- Benchmarks repetíveis comparando cada recurso com o Desktop Commander.

O GitHub executa CI, mas não substitui testes de integração com desktop real. Não publique endpoints administrativos abertos na internet.
