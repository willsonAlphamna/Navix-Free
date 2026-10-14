#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string] $Installer,
    [string] $ExpectedPublisher
)

$ErrorActionPreference = 'Stop'
$setup = (Resolve-Path -LiteralPath $Installer).Path
$target = Join-Path $env:LOCALAPPDATA 'Programs\NavixLivre'
$process = Start-Process -FilePath $setup -ArgumentList '/VERYSILENT', '/NORESTART' -Wait -PassThru
if ($process.ExitCode -ne 0) { throw 'Falha ao instalar no runner Windows.' }
try {
    $installed = @('NavixLivre.exe', 'NavixBridge.exe', 'unins000.exe') | ForEach-Object {
        $file = Join-Path $target $_
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Arquivo nao instalado: $_" }
        $file
    }
    if ($ExpectedPublisher) {
        & (Join-Path $PSScriptRoot 'Test-WindowsSignature.ps1') -Path $installed -ExpectedPublisher $ExpectedPublisher
        $panel = Start-Process -FilePath (Join-Path $target 'NavixLivre.exe') -PassThru
        try {
            Start-Sleep -Seconds 9
            $panel.Refresh()
            if ($panel.HasExited) { throw 'Painel assinado terminou inesperadamente.' }
        } finally {
            $panel.Refresh()
            if (-not $panel.HasExited) { Stop-Process -Id $panel.Id -Force }
        }
        $tokenPath = & (Join-Path $target 'NavixBridge.exe') --show-token-path
        if ($LASTEXITCODE -ne 0 -or $tokenPath -notmatch 'bridge.token') { throw 'Ponte assinada falhou.' }
    }
    $secretFolder = Join-Path $env:LOCALAPPDATA 'NavixLivre'
    New-Item -ItemType Directory -Path $secretFolder -Force | Out-Null
    Set-Content -Path (Join-Path $secretFolder 'bridge.token') -Value 'fake-test-secret-only'
} finally {
    $uninstaller = Join-Path $target 'unins000.exe'
    if (Test-Path -LiteralPath $uninstaller) {
        $remove = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT', '/NORESTART' -Wait -PassThru
        if ($remove.ExitCode -ne 0) { throw 'Falha ao desinstalar no runner Windows.' }
    }
}
foreach ($name in @('NavixLivre.exe', 'NavixBridge.exe')) {
    if (Test-Path -LiteralPath (Join-Path $target $name)) { throw "Executavel permaneceu instalado: $name" }
}
if (Test-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'NavixLivre\bridge.token')) {
    throw 'Credencial permaneceu apos desinstalacao.'
}
