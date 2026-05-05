param(
    [switch]$UserInstall = $true
)

$wheelsDir = Join-Path -Path $PSScriptRoot -ChildPath "..\wheels"
$wheelsDir = (Resolve-Path $wheelsDir).ProviderPath

if (-not (Test-Path $wheelsDir)) {
    Write-Error "No existe la carpeta de ruedas: $wheelsDir"
    exit 1
}

$wheels = Get-ChildItem -Path $wheelsDir -Filter *.whl -File
if ($wheels.Count -eq 0) {
    Write-Host "No se encontraron archivos .whl en $wheelsDir"
    exit 1
}

# Construir comando pip
$pipArgs = @('install')
if ($UserInstall) { $pipArgs += '--user' }
$pipArgs += '--no-index'
$pipArgs += "--find-links=$wheelsDir"
$pipArgs += $wheels | ForEach-Object { $_.FullName }

Write-Host "Ejecutando: python -m pip $($pipArgs -join ' ')"
python -m pip @pipArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "pip falló con código $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Instalación completada."