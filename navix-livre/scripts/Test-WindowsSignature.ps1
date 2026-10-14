#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string[]] $Path,
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string] $ExpectedPublisher
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'WindowsSigning.Common.ps1')

if ([string]::IsNullOrWhiteSpace($ExpectedPublisher)) {
    throw 'O titular esperado do certificado deve ser configurado.'
}
$signTool = Resolve-NavixSignTool
$artifacts = @(Resolve-NavixArtifactPaths -Path $Path)

foreach ($artifact in $artifacts) {
    $signature = Get-AuthenticodeSignature -LiteralPath $artifact -ErrorAction Stop
    if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
        throw "Assinatura Authenticode invalida ou ausente em $([System.IO.Path]::GetFileName($artifact))."
    }
    if ($null -eq $signature.SignerCertificate -or
        -not [string]::Equals($signature.SignerCertificate.Subject, $ExpectedPublisher, [StringComparison]::Ordinal)) {
        throw 'O titular da assinatura difere do titular esperado.'
    }
    if ($null -eq $signature.TimeStamperCertificate) {
        throw 'A assinatura nao possui carimbo de tempo verificavel.'
    }
    Invoke-NavixSignTool -SignTool $signTool -Operation 'a verificacao' -Arguments @(
        'verify', '/pa', '/all', '/v', '/tw', $artifact
    )
}

Write-Host 'Assinaturas Authenticode, titular e carimbos de tempo verificados.'
