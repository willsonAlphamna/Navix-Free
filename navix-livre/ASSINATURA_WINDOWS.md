# Assinatura e distribuição do Navix Livre no Windows

Atualizado em 14/10/2026. A 0.3.1 está em desenvolvimento. **Uma nova release
assinada ainda não está pronta:** falta disponibilizar/configurar uma identidade
de assinatura de código confiável. Alterar o workflow não cria um certificado.

## O que ocorreu na 0.3.0

O arquivo da [release 0.3.0](https://github.com/willsonAlphamna/SamsungRemoteTeste/releases/tag/navix-livre-v0.3.0),
`NavixLivre-Setup-Windows.exe`, possui SHA-256:

```text
3ef81d2e7eba81e8fcf51a177d7329bc9743d4aec7b5a798def805be888c676b
```

A inspeção do executável baixado encontrou **Certificate Table: offset=0,
size=0**. Portanto, ele não possui assinatura Authenticode incorporada.
Isso segue a estrutura documentada no
[formato PE da Microsoft](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#the-attribute-certificate-table-image-only).
O resultado identifica o arquivo antigo e a ausência de assinatura; não é
uma homologação do Windows do usuário nem um laudo de ausência de malware.

## Configuração exigida antes de publicar

1. No GitHub, configure o ambiente **windows-release** com regras efetivas de
   proteção: restrinja a branch de implantação a `feature/navix-livre-mcp` e
   configure a aprovação de responsáveis antes de liberar credenciais.
   Confira os recursos disponíveis no plano do repositório.
   **Referenciar o nome do ambiente no YAML não ativa essas proteções.**
2. Disponibilize uma identidade real de assinatura Authenticode, com uso de
   assinatura de código e cadeia confiável no Windows. Não use certificado
   autoassinado como substituto para distribuição pública.
3. O caminho implementado aceita um **PFX exportável legítimo já existente**.
   Armazene no ambiente protegido os secrets
   `NAVIX_SIGNING_CERTIFICATE_BASE64` (PFX em base64) e
   `NAVIX_SIGNING_CERTIFICATE_PASSWORD` (senha). Não coloque essas credenciais
   em commits, issues, logs, anexos ou artefatos do build.
4. Configure a variável `NAVIX_SIGNING_PUBLISHER`, no repositório ou no ambiente,
   com o **Subject X.509 completo e exato** do certificado esperado. Não use
   apenas o nome do produto ou uma parte do nome do editor. Essa variável não
   é uma credencial, mas precisa ser definida independentemente do certificado
   recebido para permitir a comparação.
5. Revise o commit final e execute manualmente **Navix Livre - Instalador
   Windows**, na branch confiável, com `publish=true`. Sem essa opção, o fluxo
   produz apenas compilação de desenvolvimento sem assinatura.

Certificados públicos atuais normalmente mantêm a chave em HSM/token ou
serviço de nuvem. O caminho PFX **não integra automaticamente esses serviços**
e não é uma orientação para exportar uma chave que deve permanecer protegida.
O uso de token/HSM, Artifact Signing ou outro provedor exige uma integração
própria e validação antes de publicar. Consulte as
[opções de assinatura da Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).
Nenhum certificado, assinatura paga ou serviço de nuvem está incluído por esta
alteração no código.

## Ordem e verificações da publicação

1. Compilar `NavixLivre.exe` e `NavixBridge.exe` a partir do commit selecionado.
2. Assinar os dois executáveis com SHA-256 e carimbo RFC 3161 da DigiCert
   (`http://timestamp.digicert.com`, `/tr` e `/td SHA256`).
3. Empacotar os executáveis já assinados com o Inno Setup, assinando também
   o instalador e o desinstalador.
4. Conferir, em cada executável pertinente, `Get-AuthenticodeSignature` com
   status `Valid`, o Subject exato esperado e um certificado de carimbo de tempo.
   Confirmar a assinatura com `signtool verify /pa /all /v /tw`, recusando
   qualquer retorno diferente de zero, inclusive avisos.
5. Executar os testes Windows de abertura, instalação e desinstalação. Conferir
   também os executáveis efetivamente instalados, incluindo o desinstalador.
6. Gerar os hashes dos arquivos finais após assinatura e `BUILD_INFO.json`
   com commit de origem e hashes. Criar um rascunho de release, baixar e
   verificar seus bytes e assinatura; publicar somente depois dessa conferência.

O [SignTool do Windows SDK](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool)
documenta as opções de assinatura, timestamp e verificação. A validação precisa
falhar quando assinatura, editor ou timestamp não atendem aos critérios; não
publicar um instalador sem assinatura como alternativa automática.

A tag da versão deve corresponder ao commit que gerou o instalador. Não use
`--clobber`, não mova tags existentes e não substitua silenciosamente o arquivo
de uma release antiga. Se uma nova compilação for necessária, publique uma
nova versão com sua própria origem e seus hashes.

## Assinatura e SmartScreen

Assinatura válida não garante ausência de aviso. Novos arquivos assinados com
OV, EV ou Artifact Signing ainda podem gerar alertas de reputação; EV não
garante liberação imediata. Veja a explicação oficial sobre
[reputação SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

Distribuição pela Microsoft Store é outra opção, ainda não implementada no
Navix. Na rota MSIX, a Store reassina após certificação; na rota EXE/MSI,
o responsável ainda precisa assinar o instalador antes da submissão. Essas
rotas exigem empacotamento, cadastro e revisão, conforme as
[opções de distribuição e assinatura](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).

Não desative SmartScreen, antivírus ou Smart App Control para compensar a falta
de assinatura ou reputação. A instalação e o comportamento no computador real
do usuário continuam pendentes de validação. Os recursos e permissões do
aplicativo permanecem descritos no [README](README.md).
