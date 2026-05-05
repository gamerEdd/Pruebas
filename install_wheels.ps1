<#
.SYNOPSIS
  Instala todas las ruedas (.whl) encontradas en una carpeta local usando pip.

.DESCRIPTION
  Descarga las ruedas compatibles para Python 3.8 (win_amd64) y colócalas
  en una carpeta (por defecto C:\temp\wheels). Ejecuta este script para
  instalarlas todas sin intentar descargar de Internet.

.PARAMETER WheelsPath
  Carpeta donde están las ruedas (.whl). Por defecto C:\temp\wheels

.PARAMETER UserInstall
  Si se especifica, añade el flag --user a pip para instalar en el perfil del usuario.

USO
  # Descargar ruedas en C:\temp\wheels y ejecutar:
  .\install_wheels.ps1 -WheelsPath C:\temp\wheels

  # Instalar para el usuario (sin permisos Admin):
  .\install_wheels.ps1 -WheelsPath C:\temp\wheels -UserInstall
#>

param(
    [string]$WheelsPath = 'C:\temp\wheels',
    [switch]$UserInstall
)

if (-not (Test-Path $WheelsPath)) {
    Write-Host "Carpeta no encontrada: $WheelsPath" -ForegroundColor Red
    exit 1
}

$wheels = Get-ChildItem -Path $WheelsPath -Filter *.whl | Sort-Object Name
if ($wheels.Count -eq 0) {
    Write-Host "No se encontraron archivos .whl en $WheelsPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Se instalarán las siguientes ruedas desde: $WheelsPath" -ForegroundColor Cyan
$wheels | ForEach-Object { Write-Host " - $_.Name" }

$pipArgs = @('--no-index', '--find-links', "$WheelsPath")

if ($UserInstall) {
    $pipArgs += '--user'
}

# Instalar todas las ruedas encontradas (pip resolverá dependencias entre ellas si están presentes)
foreach ($w in $wheels) {
    Write-Host "Instalando $($w.Name) ..." -ForegroundColor Green
    $cmd = @('python', '-m', 'pip', 'install') + $pipArgs + @($w.FullName)
    $proc = Start-Process -FilePath $cmd[0] -ArgumentList $cmd[1..($cmd.Length-1)] -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-Host "ERROR: pip retornó código $($proc.ExitCode) al instalar $($w.Name)" -ForegroundColor Red
        exit $proc.ExitCode
    }
}

Write-Host "Instalación completada." -ForegroundColor Green
Write-Host "Ahora puedes ejecutar: python -c \"import scipy; import sklearn; print(scipy.__version__, sklearn.__version__)\"" -ForegroundColor Cyan
