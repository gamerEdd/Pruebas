@echo off
REM ============================================================================
REM  MT5 Trading Bot - PyInstaller Build Script
REM  Compila botiaver1.py en un ejecutable con todas las dependencias
REM ============================================================================

setlocal enabledelayedexpansion

REM Colores y formatos
color 0A
cls

echo.
echo ============================================================================
echo  MT5 TRADING BOT - COMPILADOR DE INSTALADOR v1.0
echo ============================================================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "botiaver1.py" (
    echo [ERROR] No se encuentra botiaver1.py en el directorio actual
    echo [ERROR] Asegúrate de ejecutar este script desde la raíz del proyecto
    pause
    exit /b 1
)

if not exist "botiaver1.spec" (
    echo [ERROR] No se encuentra botiaver1.spec en el directorio actual
    echo [ERROR] El archivo .spec debe estar presente
    pause
    exit /b 1
)

echo [PASO 1] Verificando Python instalado...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no está en PATH
    pause
    exit /b 1
)
python --version
echo [OK] Python encontrado
echo.

echo [PASO 2] Verificando PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] PyInstaller no está instalado
    echo [INSTALANDO] PyInstaller...
    python -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al instalar PyInstaller
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller está disponible
echo.

echo [PASO 3] Verificando dependencias...
python -m pip show MetaTrader5 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] MetaTrader5 no está instalado
    echo [INSTALANDO] MetaTrader5...
    python -m pip install MetaTrader5
)

python -m pip show pandas >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] pandas no está instalado
    echo [INSTALANDO] pandas...
    python -m pip install pandas
)

python -m pip show numpy >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] numpy no está instalado
    echo [INSTALANDO] numpy...
    python -m pip install numpy
)

python -m pip show scikit-learn >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] scikit-learn no está instalado
    echo [INSTALANDO] scikit-learn...
    python -m pip install scikit-learn
)

echo [OK] Dependencias verificadas
echo.

REM Crear directorio logs si no existe
if not exist "logs" (
    echo [PASO 4] Creando directorio de logs...
    mkdir logs
    echo [OK] Directorio logs creado
) else (
    echo [OK] Directorio logs ya existe
)
echo.

echo [PASO 5] Limpiando compilaciones anteriores...
if exist "build" (
    rmdir /s /q build
    echo [OK] Carpeta build eliminada
)
if exist "dist" (
    rmdir /s /q dist
    echo [ADVERTENCIA] La carpeta dist será reemplazada
)
echo.

echo [PASO 6] Compilando con PyInstaller...
echo [INFO] Esto puede tomar 3-5 minutos (tamaño aproximado: 300-500 MB)
echo.

python -m PyInstaller botiaver1.spec ^
    --onefile ^
    --distpath dist ^
    --buildpath build ^
    --specpath . ^
    --workpath build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilación falló
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo  COMPILACION COMPLETADA EXITOSAMENTE
echo ============================================================================
echo.
echo [OK] Ejecutable creado en: dist\MT5TradingBot_v1.exe
echo.
echo [PROXIMO PASO] Opciones:
echo   1. Copiar el ejecutable a Program Files\MT5TradingBot\
echo   2. Crear un acceso directo en el escritorio
echo   3. Crear un instalador (NSIS) - requiere NSIS instalado
echo.
echo [RECOMENDACION] Para crear un instalador .msi, ejecuta:
echo   python -m pip install pyinstaller-hooks
echo   Y utiliza NSIS o InnoSetup para empaquetar el EXE
echo.
pause
