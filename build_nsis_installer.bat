@echo off
REM ============================================================================
REM  MT5 Trading Bot - NSIS Installer Builder
REM  Crea un instalador profesional (.msi) del bot
REM ============================================================================

setlocal enabledelayedexpansion

color 0A
cls

echo.
echo ============================================================================
echo  MT5 TRADING BOT - GENERADOR DE INSTALADOR NSIS v1.0
echo ============================================================================
echo.

REM Verificar que el ejecutable existe
if not exist "dist\MT5TradingBot_v1.exe" (
    echo [ERROR] No se encuentra dist\MT5TradingBot_v1.exe
    echo [INSTRUCCION] Primero ejecuta build_installer.bat para compilar el EXE
    pause
    exit /b 1
)

if not exist "build_nsis_installer.nsi" (
    echo [ERROR] No se encuentra build_nsis_installer.nsi
    pause
    exit /b 1
)

echo [PASO 1] Verificando NSIS instalado...
if not exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    if not exist "C:\Program Files\NSIS\makensis.exe" (
        echo.
        echo [ADVERTENCIA] NSIS no está instalado
        echo.
        echo [INSTRUCCION] Para crear el instalador profesional (.exe):
        echo   1. Descargar NSIS desde: https://nsis.sourceforge.io/
        echo   2. Ejecutar el instalador de NSIS
        echo   3. Volver a ejecutar este script
        echo.
        echo [PARA AHORA] Puedes distribuir directamente:
        echo   - dist\MT5TradingBot_v1.exe (ejecutable standalone)
        pause
        exit /b 0
    )
    set NSIS_PATH=C:\Program Files\NSIS
) else (
    set NSIS_PATH=C:\Program Files (x86)\NSIS
)

echo [OK] NSIS encontrado en: !NSIS_PATH!
echo.

echo [PASO 2] Compilando instalador NSIS...
echo [INFO] Esto puede tomar 1-2 minutos...
echo.

"!NSIS_PATH!\makensis.exe" build_nsis_installer.nsi

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilación NSIS falló
    echo [CONSEJO] Verifica que build_nsis_installer.nsi sea válido
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo  INSTALADOR CREADO EXITOSAMENTE
echo ============================================================================
echo.
echo [OK] Instalador creado en: dist\MT5TradingBot_Setup_v1.0.exe
echo.
echo [TAMAÑO APROXIMADO] 300-500 MB
echo.
echo [PROXIMO PASO] Distribución:
echo   1. Anunciar el instalador como: MT5TradingBot_Setup_v1.0.exe
echo   2. Los usuarios lo descargarán y harán doble click
echo   3. Se instalará automáticamente en Program Files
echo.
echo [ALTERNATIVA] Si prefieres distribución portable:
echo   - Usa directamente: dist\MT5TradingBot_v1.exe
echo   - No requiere instalación (ejecutable standalone)
echo.
pause
