#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string[]] $Path,
    [ValidateNotNullOrEmpty()]
    [string] $ExpectedPublisher = $env:NAVIX_EXPECTED_PUBLISHER,
    [string] $TimestampUrl = 'http://timestamp.digicert.com'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'WindowsSigning.Common.ps1')

if ([string]::IsNullOrWhiteSpace($ExpectedPublisher)) {
    throw 'O titular esperado do certificado deve ser configurado.'
}
$signTool = Resolve-NavixSignTool
$artifacts = @(Resolve-NavixArtifactPaths -Path $Path)

$thumbprint = $env:NAVIX_SIGNING_THUMBPRINT
if ([string]::IsNullOrWhiteSpace($thumbprint) -or $thumbprint.Trim() -notmatch '^[0-9a-fA-F]{40}$') {
    throw 'NAVIX_SIGNING_THUMBPRINT deve identificar o certificado de assinatura importado.'
}
$certificate = Get-Item -LiteralPath "Cert:\CurrentUser\My\$($thumbprint.Trim())" -ErrorAction Stop
if (-not [string]::Equals($certificate.Subject, $ExpectedPublisher, [StringComparison]::Ordinal)) {
    throw 'O titular do certificado de assinatura difere do titular esperado.'
}
if (-not $certificate.HasPrivateKey) {
    throw 'O certificado de assinatura nao possui chave privada disponivel.'
}
$now = [DateTime]::UtcNow
if ($now -lt $certificate.NotBefore.ToUniversalTime() -or $now -ge $certificate.NotAfter.ToUniversalTime()) {
    throw 'O certificado de assinatura nao esta dentro do periodo de validade.'
}
$codeSigningEku = @($certificate.Extensions |
    Where-Object { $_.Oid.Value -eq '2.5.29.37' } |
    ForEach-Object { $_.EnhancedKeyUsages } |
    Where-Object { $_.Value -eq '1.3.6.1.5.5.7.3.3' })
if ($codeSigningEku.Count -eq 0) {
    throw 'O certificado nao declara o uso estendido de assinatura de codigo.'
}

$timestampUri = $null
if (-not [Uri]::TryCreate($TimestampUrl, [UriKind]::Absolute, [ref]$timestampUri) -or
    $timestampUri.Scheme -notin @('http', 'https') -or
    [string]::IsNullOrWhiteSpace($timestampUri.Host) -or
    -not [string]::IsNullOrEmpty($timestampUri.UserInfo)) {
    throw 'O carimbo de tempo exige uma URL HTTP ou HTTPS absoluta, sem credenciais.'
}

foreach ($artifact in $artifacts) {
    Invoke-NavixSignTool -SignTool $signTool -Operation 'a assinatura' -Arguments @(
        'sign', '/s', 'My', '/sha1', $thumbprint.Trim(), '/fd', 'SHA256',
        '/tr', $timestampUri.AbsoluteUri, '/td', 'SHA256', $artifact
    )
}

# Signing alone is insufficient: enforce Windows trust, identity and timestamp.
& (Join-Path $PSScriptRoot 'Test-WindowsSignature.ps1') -Path $artifacts -ExpectedPublisher $ExpectedPublisher
