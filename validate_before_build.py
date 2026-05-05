#!/usr/bin/env python3
"""
validate_before_build.py

Script de validación pre-compilación para boteddver1.py
Verifica que todos los requisitos estén en orden antes de compilar.
"""
import os
import sys
import importlib.util
import subprocess

ROOT = os.path.abspath(os.path.dirname(__file__))

def check_python_version():
    """Verifica que Python sea 3.8 o superior"""
    print("🔍 Verificando versión de Python...")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print(f"   ✗ Python {major}.{minor} detectado")
        print(f"   ✗ Se requiere Python 3.8 o superior")
        return False
    print(f"   ✓ Python {major}.{minor}.{sys.version_info[2]} OK")
    return True

def check_boteddver1():
    """Verifica que boteddver1.py exista y sea válido"""
    print("\n🔍 Verificando boteddver1.py...")
    path = os.path.join(ROOT, 'boteddver1.py')
    
    if not os.path.exists(path):
        print(f"   ✗ boteddver1.py no encontrado en {ROOT}")
        return False
    
    print(f"   ✓ Archivo encontrado")
    
    # Verificar sintaxis
    try:
        with open(path, 'r', encoding='utf-8') as f:
            compile(f.read(), path, 'exec')
        print(f"   ✓ Sintaxis válida")
        return True
    except SyntaxError as e:
        print(f"   ✗ ERROR de sintaxis: {e}")
        return False

def check_file_exists(filename, description):
    """Verifica que un archivo exista"""
    path = os.path.join(ROOT, filename)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"   ✓ {description}: {filename} ({size} bytes)")
        return True
    else:
        print(f"   ⚠ {description}: {filename} (NO ENCONTRADO)")
        return False

def check_dependencies():
    """Verifica que las dependencias críticas estén disponibles"""
    print("\n🔍 Verificando dependencias...")
    
    critical = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'xgboost': 'XGBoost',
    }
    
    optional = {
        'MetaTrader5': 'MetaTrader5',
        'sklearn': 'Scikit-Learn',
        'scipy': 'SciPy',
    }
    
    results = {'critical': True, 'optional': []}
    
    print("   Dependencias críticas:")
    for pkg, name in critical.items():
        if importlib.util.find_spec(pkg) is not None:
            print(f"      ✓ {name}")
        else:
            print(f"      ✗ {name} (FALTA)")
            results['critical'] = False
    
    print("   Dependencias opcionales:")
    for pkg, name in optional.items():
        if importlib.util.find_spec(pkg) is not None:
            print(f"      ✓ {name}")
        else:
            print(f"      ⚠ {name} (no encontrada - se instalará)")
            results['optional'].append(name)
    
    return results

def check_modules():
    """Verifica que los módulos personalizados existan"""
    print("\n🔍 Verificando módulos personalizados...")
    
    modules = [
        'mt5_safe.py',
        'buy_specialist_ai.py',
        'sell_specialist_ai.py',
        'decision_arbitrator_ai.py',
        'gold_analyzer.py',
        'loss_analyzer.py',
        'adaptive_parameters.py',
        'data_updater_module.py',
        'data_loader_trainer.py',
    ]
    
    missing = []
    for mod in modules:
        path = os.path.join(ROOT, mod)
        if os.path.exists(path):
            print(f"   ✓ {mod}")
        else:
            print(f"   ✗ {mod} (FALTA)")
            missing.append(mod)
    
    return len(missing) == 0, missing

def check_pyinstaller():
    """Verifica que PyInstaller esté disponible"""
    print("\n🔍 Verificando PyInstaller...")
    
    if importlib.util.find_spec('PyInstaller') is not None:
        import PyInstaller
        print(f"   ✓ PyInstaller {PyInstaller.__version__} instalado")
        return True
    else:
        print(f"   ✗ PyInstaller no encontrado")
        print(f"      Instálalo con: python -m pip install pyinstaller")
        return False

def check_data_files():
    """Verifica que los archivos de datos existan"""
    print("\n🔍 Verificando archivos de datos...")
    
    data_files = {
        'mi_sesion.session': 'Sesión MT5',
        'config': 'Directorio de configuración',
    }
    
    for name, desc in data_files.items():
        path = os.path.join(ROOT, name)
        if os.path.exists(path):
            if os.path.isdir(path):
                count = len(os.listdir(path))
                print(f"   ✓ {desc}: {name} ({count} items)")
            else:
                size = os.path.getsize(path)
                print(f"   ✓ {desc}: {name} ({size} bytes)")
        else:
            print(f"   ⚠ {desc}: {name} (no encontrado)")

def main():
    print("=" * 60)
    print("VALIDACIÓN PRE-COMPILACIÓN - boteddver1.exe")
    print("=" * 60)
    
    checks = []
    
    # Verificaciones críticas
    checks.append(("Versión Python", check_python_version()))
    checks.append(("boteddver1.py", check_boteddver1()))
    
    modules_ok, missing = check_modules()
    checks.append(("Módulos personalizados", modules_ok))
    if missing:
        print(f"\n⚠ Módulos faltantes: {', '.join(missing)}")
        print("  El bot puede no funcionar sin estos módulos")
    
    checks.append(("PyInstaller", check_pyinstaller()))
    
    # Verificaciones no críticas
    deps = check_dependencies()
    checks.append(("Dependencias críticas", deps['critical']))
    
    check_data_files()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print("=" * 60)
    
    all_passed = True
    for name, result in checks:
        status = "✓ OK" if result else "✗ FALTA"
        print(f"{status:10} {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ LISTO PARA COMPILAR")
        print("\nEjecutar:")
        print("   python build_exe.py")
        return 0
    else:
        print("\n✗ FALTAN REQUISITOS")
        print("\nAcciones recomendadas:")
        print("1. Instala las dependencias:")
        print("   python -m pip install -r requirements.txt")
        print("2. O ejecuta directamente:")
        print("   python build_exe.py")
        print("   (Instalará las dependencias automáticamente)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
