@echo off
REM Script para compilar el bot MT5 como ejecutable
REM USA PYTHON DEL SISTEMA, NO DEL VENV

cd /d "%~dp0"

echo.
echo ========================================================================
echo  COMPILADOR DE BOT - MT5 Trading Bot v1
echo ========================================================================
echo.

REM Ejecutar con Python del sistema
python.exe build_bot_exe.py

if %errorlevel% equ 0 (
    echo.
    echo [OK] Presiona cualquier tecla para salir...
    pause >nul
) else (
    echo.
    echo [ERROR] Presiona cualquier tecla para salir...
    pause >nul
    exit /b 1
)
