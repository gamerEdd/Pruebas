param(
    [switch]$IncludeTensorflow = $false,
    [switch]$IncludeMT5 = $false,
    [string]$IndexUrl = ''
)

# Script para descargar ruedas (.whl) a la carpeta wheels\ usando pip download
# Uso: .\scripts\download_wheels.ps1 -IncludeTensorflow -IncludeMT5

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
$target = Join-Path -Path $scriptDir -ChildPath "..\wheels"
$target = (Resolve-Path $target).ProviderPath

if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target | Out-Null }

# Lista base de paquetes y versiones recomendadas para CPython 3.8 / win_amd64
$packages = @(
    'numpy==1.24.4',
    'scipy==1.10.1',
    'pandas==1.5.3',
    'scikit_learn==1.2.2',
    'joblib==1.3.1',
    'xgboost==1.7.6'
)

if ($IncludeTensorflow) {
    $packages += 'tensorflow==2.13.0'
}
if ($IncludeMT5) {
    $packages += 'MetaTrader5'
}

# Construir comando pip download
$pipBase = "python -m pip download --only-binary=:all: -d `"$target`""
if ($IndexUrl -ne '') { $pipBase += " --index-url $IndexUrl" }

foreach ($pkg in $packages) {
    Write-Host "Descargando $pkg ..."
    $cmd = "$pipBase $pkg"
    Write-Host $cmd
    iex $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Fallo descargando $pkg (código $LASTEXITCODE). Puedes intentar ejecutar el comando manualmente."
    }
}

Write-Host "Descarga finalizada. Revisa la carpeta: $target"