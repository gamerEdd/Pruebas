#!/usr/bin/env python3
"""
build_exe.py - OPTIMIZADO PARA boteddver1.py

Script para generar un ejecutable "single-file" de `boteddver1.py` usando PyInstaller.
Instala e integra automáticamente todas las dependencias necesarias.

Uso:
    python build_exe.py [OPTIONS]

Opciones:
  --console       : Generar exe con consola (útil para debug)
  --no-install    : No instalar paquetes (requiere que todo esté instalado)
  --dry-run       : Solo mostrar el comando PyInstaller sin ejecutar
  --include-mt5   : Incluir archivos de MetaTrader5 en el bundle
  --wheel FILE    : Instalar wheel local antes de compilar
  --wheel-dir DIR : Instalar todos los wheels de un directorio

Ejemplo:
    python build_exe.py --console                    # Build con consola
    python build_exe.py --include-mt5               # Build con MT5 integrado
    python build_exe.py --wheel path/MetaTrader5.whl # Instalar wheel y compilar
"""
import os
import sys
import subprocess
import shutil
import glob
import importlib.util

ROOT = os.path.abspath(os.path.dirname(__file__))
MAIN = os.path.join(ROOT, 'boteddver1.py')
SESSION = os.path.join(ROOT, 'mi_sesion.session')
CONFIG_DIR = os.path.join(ROOT, 'config')
MODELS_DIR = os.path.join(ROOT, 'models')
DATASETS_DIR = os.path.join(ROOT, 'datasets')


def run(cmd, env=None):
    """Ejecuta comando e imprime salida"""
    print('>>> ' + ' '.join(cmd))
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)

def ensure_package(pkg):
    """Verifica si un paquete está disponible"""
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False

def get_package_location(pkg_name):
    """Obtiene la ruta del paquete instalado"""
    try:
        spec = importlib.util.find_spec(pkg_name)
        if spec and spec.origin:
            return os.path.dirname(spec.origin)
        return None
    except Exception:
        return None

def collect_hidden_imports():
    """Recopila todos los hidden imports necesarios para boteddver1"""
    base_imports = [
        'MetaTrader5',
        'numpy',
        'pandas',
        'sklearn',
        'scikit_learn',
        'xgboost',
        'scipy',
        'tkinter',
        'threading',
        'json',
        'pickle',
    ]
    
    # Módulos personalizados de boteddver1
    bot_modules = [
        'mt5_safe',
        'buy_specialist_ai',
        'sell_specialist_ai',
        'decision_arbitrator_ai',
        'gold_analyzer',
        'loss_analyzer',
        'loss_protection_ai',
        'recovery_based_closer',
        'feedback_loop_ai',
        'rapid_ops_validator',
        'entry_point_ai',
        'adaptive_parameters',
        'data_updater_module',
        'data_loader_trainer',
        'regime_detector',
        'trend_model',
        'reversion_model',
        'bias_monitor',
        'drift_detector',
        'dynamic_weights',
        'meta_selector',
        'bot_integration_manager',
        'super_analyzer',
        'dynamic_score_calibration',
        'recovery_potential_enhanced',
        'spread_slippage_analyzer',
        'time_based_session_filter',
        'correlation_analyzer',
        'trade_logger',
        'auto_calibration',
        'dynamic_position_closer',
        'trend_change_detector',
        'multi_timeframe_analyzer',
        'indicator_base',
        'temporal_weighting',
        'outlier_filter',
        'candle_validator',
        'market_snapshot_generator',
        'safety_filters_manager',
    ]
    
    hidden = []
    
    # Agregar imports estándar disponibles
    for mod in base_imports:
        if ensure_package(mod) or mod in ['tkinter', 'threading', 'json', 'pickle']:
            hidden.append(mod)
    
    # Agregar módulos del bot (estos existen en el directorio actual)
    for mod in bot_modules:
        hidden.append(mod)
    
    return hidden

def collect_data_files():
    """Recopila archivos de datos a incluir en el bundle"""
    data_files = []
    
    # Archivos críticos
    if os.path.exists(SESSION):
        data_files.append((SESSION, '.'))
        print(f'✓ Incluido: mi_sesion.session')
    
    # Directorio de configuración
    if os.path.exists(CONFIG_DIR):
        data_files.append((CONFIG_DIR, 'config'))
        print(f'✓ Incluido: carpeta config/')
    
    # Directorio de modelos (opcional)
    if os.path.exists(MODELS_DIR):
        data_files.append((MODELS_DIR, 'models'))
        print(f'✓ Incluido: carpeta models/')
    
    # Directorio de datasets (opcional, podría ser grande)
    if os.path.exists(DATASETS_DIR) and '--include-datasets' in sys.argv:
        data_files.append((DATASETS_DIR, 'datasets'))
        print(f'✓ Incluido: carpeta datasets/')
    
    return data_files

def verify_boteddver1():
    """Verifica que boteddver1.py exista y sea válido"""
    if not os.path.exists(MAIN):
        print(f'ERROR: {MAIN} no encontrado')
        sys.exit(1)
    
    print(f'✓ Encontrado: {MAIN}')
    
    # Verificar que pueda parsearse
    try:
        with open(MAIN, 'r', encoding='utf-8') as f:
            compile(f.read(), MAIN, 'exec')
        print(f'✓ Sintaxis de {os.path.basename(MAIN)} es válida')
    except SyntaxError as e:
        print(f'ERROR de sintaxis en {MAIN}:')
        print(f'  {e}')
        sys.exit(1)

def pip_install_requirements():
    """Instala dependencias desde requirements.txt"""
    req_path = os.path.join(ROOT, 'requirements.txt')
    if not os.path.exists(req_path):
        print('Aviso: requirements.txt no encontrado')
        return False
    
    try:
        print('\n' + '='*60)
        print('Instalando dependencias desde requirements.txt...')
        print('='*60)
        run([sys.executable, '-m', 'pip', 'install', '-r', req_path])
        return True
    except subprocess.CalledProcessError as e:
        print(f'\nERROR al instalar dependencias: {e}')
        print('Posibles soluciones:')
        print('  1. Instalar MetaTrader5 manualmente desde su instalador oficial')
        print('  2. Usar una rueda (.whl) local: python build_exe.py --wheel path/to/wheel.whl')
        print('  3. Ejecutar con --no-install si ya tienen todo instalado')
        return False

def ensure_pyinstaller():
    """Asegura que PyInstaller esté instalado"""
    try:
        import PyInstaller
        print(f'✓ PyInstaller {PyInstaller.__version__} ya está instalado')
        return True
    except ImportError:
        print('PyInstaller no encontrado. Instalando...')
        try:
            run([sys.executable, '-m', 'pip', 'install', 'pyinstaller>=5.1'])
            print('✓ PyInstaller instalado correctamente')
            return True
        except subprocess.CalledProcessError:
            print('ERROR: No se pudo instalar PyInstaller')
            return False



def main():
    """Función principal de construcción"""
    args = sys.argv[1:]
    
    # Parsear argumentos
    console = '--console' in args
    no_install = '--no-install' in args
    dry_run = '--dry-run' in args
    include_mt5 = '--include-mt5' in args
    skip_verify = '--skip-verify' in args
    
    wheel_files = []
    wheel_dir = None
    
    # Procesar opciones de wheels
    for i, arg in enumerate(args):
        if arg == '--wheel' and i + 1 < len(args):
            wheel_files.append(args[i + 1])
        elif arg == '--wheel-dir' and i + 1 < len(args):
            wheel_dir = args[i + 1]
    
    print('\n' + '='*60)
    print('BOT BUILDER - COMPILADOR PARA boteddver1.py')
    print('='*60)
    
    # Paso 0: Verificar boteddver1.py
    if not skip_verify:
        print('\n[PASO 1/5] Verificando boteddver1.py...')
        verify_boteddver1()
    
    # Paso 1: Instalar dependencias
    print('\n[PASO 2/5] Preparando dependencias...')
    
    if not no_install:
        # Instalar wheels locales si se proporcionan
        if wheel_files or wheel_dir:
            print('\n  Instalando wheels locales...')
            
            for wf in wheel_files:
                if os.path.exists(wf):
                    print(f'  • Instalando: {wf}')
                    try:
                        run([sys.executable, '-m', 'pip', 'install', wf])
                    except subprocess.CalledProcessError as e:
                        print(f'  Aviso: No se pudo instalar {wf}: {e}')
                else:
                    print(f'  ✗ Wheel no encontrado: {wf}')
            
            if wheel_dir and os.path.isdir(wheel_dir):
                print(f'  • Instalando wheels desde: {wheel_dir}')
                whls = glob.glob(os.path.join(wheel_dir, '*.whl'))
                for w in whls:
                    try:
                        print(f'    → {os.path.basename(w)}')
                        run([sys.executable, '-m', 'pip', 'install', w])
                    except subprocess.CalledProcessError as e:
                        print(f'    ✗ Error: {e}')
        
        # Instalar requirements.txt
        if not pip_install_requirements():
            print('\n  AVISO: Algunos paquetes pueden no estar disponibles.')
            print('  El build continuará, pero puede fallar si faltan dependencias críticas.')
    else:
        print('  (--no-install usado: omitiendo instalación de dependencias)')
    
    # Paso 2: Asegurar PyInstaller
    print('\n[PASO 3/5] Verificando PyInstaller...')
    if not ensure_pyinstaller():
        print('ERROR: PyInstaller no disponible y no se pudo instalar')
        sys.exit(1)
    
    # Paso 3: Recopilar imports y datos
    print('\n[PASO 4/5] Verificando spec file...')
    
    spec_file = os.path.join(ROOT, 'boteddver1.spec')
    if not os.path.exists(spec_file):
        print(f'  ✗ ERROR: {spec_file} no encontrado')
        sys.exit(1)
    
    print(f'  ✓ Spec file encontrado: {os.path.basename(spec_file)}')
    
    # Paso 4: Construir comando PyInstaller usando spec file
    print('\n[PASO 5/5] Construyendo con spec file...')
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        spec_file,  # ⭐ USAR SPEC FILE DIRECTAMENTE (más eficiente)
    ]
    
    print('  → Usando spec file (evita análisis innecesario de módulos)')
    print('  → Usando spec file (evita análisis innecesario de módulos)')
    print('  → Con ventana de consola y traceback habilitado')
    
    # Agregar icono si existe
    icon_path = os.path.join(ROOT, 'icon.ico')
    if os.path.exists(icon_path):
        print(f'  ✓ Icono incluido: icon.ico')
    
    # Incluir archivos de MetaTrader5
    if include_mt5:
        print('  • Buscando archivos de MetaTrader5...')
        
        # Intenta encontrar el paquete Python primero
        mt5_dir = get_package_location('MetaTrader5')
        if mt5_dir:
            cmd += ['--add-data', f'{mt5_dir};MetaTrader5']
            print(f'    ✓ Paquete MetaTrader5 encontrado')
        else:
            # Buscar en rutas conocidas
            mt5_paths = [
                r'C:\Program Files\MetaTrader 5',
                r'C:\Program Files (x86)\MetaTrader 5',
                os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'MetaQuotes', 'Terminal'),
            ]
            
            for base_path in mt5_paths:
                if os.path.exists(base_path):
                    dlls = glob.glob(os.path.join(base_path, '*.dll'))
                    for dll in dlls:
                        cmd += ['--add-data', f'{dll};.']
                    print(f'    ✓ Archivos MT5 encontrados en: {base_path}')
                    break
    
    # Archivo principal
    cmd.append(MAIN)
    
    # Modo dry-run: solo mostrar comando
    if dry_run:
        print('\n' + '='*60)
        print('MODO DRY-RUN: Comando que se ejecutaría:')
        print('='*60)
        print(' '.join(cmd))
        sys.exit(0)
    
    # Compilar
    print('\n' + '='*60)
    print('COMPILANDO EJECUTABLE...')
    print('Esto puede tardar de 2-10 minutos (presiona Ctrl+C para cancelar)')
    print('='*60)
    
    try:
        run(cmd)
    except subprocess.CalledProcessError as e:
        print(f'\n✗ ERROR: PyInstaller falló')
        print(f'  {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        print('\n\nCompilación cancelada por el usuario (Ctrl+C)')
        sys.exit(2)
    
    # Verificar resultado
    print('\n' + '='*60)
    output_exe = os.path.join(ROOT, 'dist', 'boteddver1.exe')
    
    if os.path.exists(output_exe):
        file_size = os.path.getsize(output_exe) / (1024 * 1024)
        print('✓ COMPILACIÓN EXITOSA')
        print('='*60)
        print(f'\nEjecutable: {output_exe}')
        print(f'Tamaño: {file_size:.2f} MB')
        print(f'\n✓ El bot está listo para ejecutar:')
        print(f'  dist\\boteddver1.exe')
        print('\nPuedes hacer clic directamente en el .exe para ejecutarlo')
        print('o desde terminal: dist\\boteddver1.exe')
    else:
        print('✗ COMPILACIÓN COMPLETADA PERO SIN RESULTADO')
        print('='*60)
        print(f'\nNo se encontró: {output_exe}')
        print('Revisa los errores de PyInstaller arriba')
        sys.exit(1)




if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'\n✗ ERROR INESPERADO: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


