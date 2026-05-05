@echo off
REM ============================================================================
REM  MT5 Trading Bot - Main Build Menu
REM  Centro de control para compilación, validación e instalación
REM ============================================================================

setlocal enabledelayedexpansion

:menu
cls
color 0A

echo.
echo ============================================================================
echo     MT5 TRADING BOT - CENTRO DE COMPILACION v1.0
echo ============================================================================
echo.
echo [OPCIONES]:
echo.
echo   1. Validar que todo esté listo (RECOMENDADO PRIMERO)
echo   2. Instalar/Actualizar dependencias
echo   3. Compilar ejecutable (EXE file) - PASO MAIN
echo   4. Verificar compilado (revisar dist\MT5TradingBot_v1.exe)
echo   5. Crear instalador NSIS (instalador .exe profesional)
echo   6. Ejecutar el bot compilado
echo.
echo   7. Limpiar compilaciones anteriores
echo   8. Ver logs del bot
echo   9. Abrir carpeta del proyecto
echo.
echo   0. Salir
echo.
echo ============================================================================
set /p choice="Selecciona una opción (0-9): "

if "%choice%"=="1" goto validate
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto compile_exe
if "%choice%"=="4" goto check_exe
if "%choice%"=="5" goto install_nsis
if "%choice%"=="6" goto run_exe
if "%choice%"=="7" goto clean
if "%choice%"=="8" goto view_logs
if "%choice%"=="9" goto open_folder
if "%choice%"=="0" goto exit_menu

echo.
echo [ERROR] Opción no válida. Intenta de nuevo.
timeout /t 2 >nul
goto menu

REM ============================================================================
REM OPCION 1: VALIDAR
REM ============================================================================
:validate
cls
echo.
echo [VALIDANDO COMPILACION]
echo.
python validate_compilation.py
pause
goto menu

REM ============================================================================
REM OPCION 2: INSTALAR DEPENDENCIAS
REM ============================================================================
:install_deps
cls
echo.
echo [INSTALANDO DEPENDENCIAS]
echo.
echo Esto puede tomar 5-10 minutos...
echo.

python -m pip install --upgrade pip
python -m pip install MetaTrader5 pandas numpy scikit-learn pyinstaller joblib python-dateutil pytz

echo.
echo [OK] Dependencias instaladas
pause
goto menu

REM ============================================================================
REM OPCION 3: COMPILAR EJECUTABLE
REM ============================================================================
:compile_exe
cls
echo.
echo [INICIANDO COMPILACION]
echo.
echo Esto puede tomar 3-5 minutos...
echo.

call build_installer.bat
goto menu

REM ============================================================================
REM OPCION 4: VERIFICAR COMPILADO
REM ============================================================================
:check_exe
cls
echo.
if exist "dist\MT5TradingBot_v1.exe" (
    echo [OK] Ejecutable encontrado
    echo.
    for /f "usebackq" %%A in ('dir "dist\MT5TradingBot_v1.exe" ^| find "MT5TradingBot"') do (
        echo %%A
    )
    echo.
    echo [UBICACION] dist\MT5TradingBot_v1.exe
) else (
    echo [ERROR] El ejecutable no fue encontrado
    echo [INSTRUCCION] Primero ejecuta la opción 3 para compilar
)
echo.
pause
goto menu

REM ============================================================================
REM OPCION 5: CREAR INSTALADOR NSIS
REM ============================================================================
:install_nsis
cls
echo.
if not exist "dist\MT5TradingBot_v1.exe" (
    echo [ERROR] Primero debes compilar el ejecutable (opcion 3)
    pause
    goto menu
)
echo [CREAR INSTALADOR NSIS]
echo.
call build_nsis_installer.bat
goto menu

REM ============================================================================
REM OPCION 6: EJECUTAR EXE
REM ============================================================================
:run_exe
cls
echo.
if not exist "dist\MT5TradingBot_v1.exe" (
    echo [ERROR] El ejecutable no existe
    echo [INSTRUCCION] Primero ejecuta la opción 3
    pause
    goto menu
)
echo [INICIANDO BOT]
echo.
start "" "dist\MT5TradingBot_v1.exe"
echo [OK] Bot iniciado en background
echo.
pause
goto menu

REM ============================================================================
REM OPCION 7: LIMPIAR
REM ============================================================================
:clean
cls
echo.
echo [LIMPIANDO COMPILACIONES ANTERIORES]
echo.

if exist "build" (
    echo Eliminando carpeta build...
    rmdir /s /q build
    echo [OK] build eliminado
)

if exist "dist" (
    echo Eliminando carpeta dist...
    rmdir /s /q dist
    echo [OK] dist eliminado
)

if exist "__pycache__" (
    echo Eliminando __pycache__...
    rmdir /s /q __pycache__
    echo [OK] __pycache__ eliminado
)

if exist "*.pyc" (
    echo Eliminando archivos .pyc...
    del /q *.pyc
)

echo.
echo [OK] Limpeza completada
echo.
pause
goto menu

REM ============================================================================
REM OPCION 8: VER LOGS
REM ============================================================================
:view_logs
cls
echo.
if exist "logs\bot.log" (
    echo [MOSTRANDO ULTIMAS 50 LINEAS DE LOGS]
    echo.
    powershell -Command "Get-Content logs\bot.log -Tail 50"
) else (
    echo [INFO] No hay logs aún. Ejecuta el bot primero (opción 6)
)

echo.
pause
goto menu

REM ============================================================================
REM OPCION 9: ABRIR CARPETA
REM ============================================================================
:open_folder
echo.
echo [ABRIENDO CARPETA DEL PROYECTO]
start "" "%CD%"
goto menu

REM ============================================================================
REM OPCION 0: SALIR
REM ============================================================================
:exit_menu
exit /b 0
