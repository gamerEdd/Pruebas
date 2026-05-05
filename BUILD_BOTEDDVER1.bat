@echo off
REM Build script for boteddver1.exe
REM Automatically installs dependencies and compiles the bot to an executable

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo BUILD BOTEDDVER1 - Compilador Automatico
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Asegúrate de que Python esté instalado y en PATH.
    pause
    exit /b 1
)

echo [INFO] Python encontrado
python --version

REM Navigate to script directory
cd /d "%~dp0"

REM Determine build options
set BUILD_OPTS=

if "%1"=="console" (
    echo [INFO] Modo: Console habilitado
    set BUILD_OPTS=--console
)

if "%1"=="mt5" (
    echo [INFO] Modo: MetaTrader5 incluido
    set BUILD_OPTS=--include-mt5
)

if "%1"=="console-mt5" (
    echo [INFO] Modo: Console + MetaTrader5
    set BUILD_OPTS=--console --include-mt5
)

echo.
echo ============================================================
echo Iniciando compilacion...
echo ============================================================
echo.

REM Run the build script
python build_exe.py %BUILD_OPTS%

REM Check result
if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo. Revisa los errores arriba.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================
    echo [EXITO] Compilacion completada
    echo ============================================================
    echo.
    echo El ejecutable se encuentra en: dist\boteddver1.exe
    echo.
    echo Para ejecutar el bot:
    echo   • Doble-click en: dist\boteddver1.exe
    echo   • O desde terminal: dist\boteddver1.exe
    echo.
    pause
)

endlocal
