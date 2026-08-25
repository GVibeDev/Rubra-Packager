param(
    [Parameter(Mandatory=$true)]
    [string]$Path
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:WINDOWS_CERTIFICATE_BASE64)) {
    Write-Host 'Code signing secrets are not configured. Release remains unsigned.'
    exit 0
}
if ([string]::IsNullOrWhiteSpace($env:WINDOWS_CERTIFICATE_PASSWORD)) {
    throw 'WINDOWS_CERTIFICATE_BASE64 is configured but WINDOWS_CERTIFICATE_PASSWORD is missing.'
}

$target = (Resolve-Path -LiteralPath $Path).Path
$signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
if (-not $signtool) {
    $kits = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $kits) {
        $signtool = Get-ChildItem -LiteralPath $kits -Filter signtool.exe -Recurse -File |
            Sort-Object FullName -Descending |
            Select-Object -First 1 -ExpandProperty FullName
    }
}
if (-not $signtool) {
    throw 'signtool.exe was not found.'
}

$tempPfx = Join-Path $env:RUNNER_TEMP 'rubra-packager-signing.pfx'
try {
    [IO.File]::WriteAllBytes($tempPfx, [Convert]::FromBase64String($env:WINDOWS_CERTIFICATE_BASE64))
    & $signtool sign /fd SHA256 /f $tempPfx /p $env:WINDOWS_CERTIFICATE_PASSWORD /tr http://timestamp.digicert.com /td SHA256 $target
    if ($LASTEXITCODE -ne 0) { throw "signtool failed with exit code $LASTEXITCODE" }
    & $signtool verify /pa /v $target
    if ($LASTEXITCODE -ne 0) { throw "signature verification failed with exit code $LASTEXITCODE" }
}
finally {
    Remove-Item -LiteralPath $tempPfx -Force -ErrorAction SilentlyContinue
}
