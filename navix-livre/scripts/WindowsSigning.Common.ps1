#requires -Version 7.0

Set-StrictMode -Version Latest

function Resolve-NavixSignTool {
    [CmdletBinding()]
    param()

    if (-not $IsWindows) {
        throw 'A assinatura do Navix exige um ambiente Windows.'
    }

    if (-not [string]::IsNullOrWhiteSpace($env:NAVIX_SIGNTOOL)) {
        if (-not [System.IO.Path]::IsPathFullyQualified($env:NAVIX_SIGNTOOL)) {
            throw 'NAVIX_SIGNTOOL deve indicar o caminho absoluto de signtool.exe.'
        }
        $tool = Get-Item -LiteralPath $env:NAVIX_SIGNTOOL -ErrorAction Stop
        if ($tool -isnot [System.IO.FileInfo] -or $tool.Name -ine 'signtool.exe') {
            throw 'NAVIX_SIGNTOOL deve indicar um arquivo signtool.exe existente.'
        }
        return $tool.FullName
    }

    $programFilesX86 = [Environment]::GetFolderPath('ProgramFilesX86')
    if ([string]::IsNullOrWhiteSpace($programFilesX86)) {
        throw 'Nao foi possivel localizar o Windows SDK.'
    }
    $sdkBin = Join-Path $programFilesX86 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $sdkBin -PathType Container) {
        $versions = Get-ChildItem -LiteralPath $sdkBin -Directory |
            Where-Object { $_.Name -match '^\d+\.\d+\.\d+\.\d+$' } |
            Sort-Object -Property { [version]$_.Name } -Descending
        foreach ($version in $versions) {
            $candidate = Join-Path $version.FullName 'x64\signtool.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                return (Get-Item -LiteralPath $candidate -ErrorAction Stop).FullName
            }
        }
    }

    throw 'signtool.exe x64 nao encontrado. Instale o Windows 10/11 SDK ou configure NAVIX_SIGNTOOL.'
}

function Resolve-NavixArtifactPaths {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string[]] $Path
    )

    foreach ($artifactPath in $Path) {
        if ([string]::IsNullOrWhiteSpace($artifactPath)) {
            throw 'O caminho de um artefato esta vazio.'
        }
        $artifact = Get-Item -LiteralPath $artifactPath -ErrorAction Stop
        if ($artifact -isnot [System.IO.FileInfo]) {
            throw 'A assinatura aceita apenas arquivos existentes.'
        }
        $artifact.FullName
    }
}

function Invoke-NavixSignTool {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $SignTool,
        [Parameter(Mandatory)]
        [string[]] $Arguments,
        [Parameter(Mandatory)]
        [string] $Operation
    )

    # Exit code 2 is a warning in SignTool and must also block publication.
    $PSNativeCommandUseErrorActionPreference = $false
    & $SignTool @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "SignTool falhou durante $Operation (codigo $LASTEXITCODE)."
    }
}
