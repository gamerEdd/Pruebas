@echo off
REM ============================================================================
REM BOTEDDVER1 - EJECUTABLE COMPILADO
REM ============================================================================
REM
REM Este archivo inicia boteddver1.exe con todas las configuraciones
REM necesarias para funcionamiento óptimo.
REM
REM ============================================================================

echo.
echo ============================================================================
echo  INICIANDO BOTEDDVER1 v1.0
echo ============================================================================
echo.

REM Obtener la ruta del script
setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0

REM Ruta del ejecutable
set EXE_PATH=%SCRIPT_DIR%dist\boteddver1\boteddver1.exe

REM Verificar que el ejecutable existe
if not exist "%EXE_PATH%" (
    echo [ERROR] No se encontró el ejecutable en:
    echo   %EXE_PATH%
    echo.
    echo Por favor asegúrate de:
    echo   1. Estar en la carpeta correcta (E:\trading\botrapido1)
    echo   2. Ejecutar simple_rebuild.py si aún no has compilado
    echo.
    pause
    exit /b 1
)

REM Mostrar información
echo [INFO] Ejecutable: %EXE_PATH%
echo [INFO] Tamaño: 57.55 MB
echo [INFO] Iniciando...
echo.

REM Iniciar la aplicación
start "" "%EXE_PATH%"

echo [OK] Aplicación iniciada
echo.
echo Para compilar nuevamente:
echo   python simple_rebuild.py
echo.

endlocal
