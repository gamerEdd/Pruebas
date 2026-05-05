@echo off
REM FIX_EXE_ERROR.bat - Reparar error de embedded pkg archive
REM 
REM Este script ayuda a solucionar:
REM "could not load pyinstaller's embedded pkg archive from the executable"

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo REPARADOR - Error de embedded pkg archive
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1] Limpiar y recompilar desde cero
echo [2] Diagnosticar el problema
echo [3] Recompilar con opciones alternas
echo.

set /p choice="Elige opcion (1-3): "

if "%choice%"=="1" (
    echo.
    echo Limpiando y recompilando...
    python clean_and_rebuild.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Diagnosticando...
    python fix_exe_error.py
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Recompilando con opciones alternas...
    python build_exe.py --console --no-install
    goto end
)

echo Opcion invalida
:end
pause
