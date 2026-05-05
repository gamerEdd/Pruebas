#!/usr/bin/env python3
"""
test_build_setup.py

Script de test rápido para verificar que build_exe.py está correctamente configurado
"""
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))

def check_file(path, description):
    """Verifica que un archivo exista"""
    full_path = os.path.join(ROOT, path)
    exists = os.path.exists(full_path)
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {path}")
    return exists

def check_contains(path, text, description):
    """Verifica que un archivo contenga un texto"""
    full_path = os.path.join(ROOT, path)
    if not os.path.exists(full_path):
        print(f"  ✗ {description}: {path} (NO EXISTE)")
        return False
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            found = text in content
            status = "✓" if found else "✗"
            print(f"  {status} {description}")
            return found
    except Exception as e:
        print(f"  ✗ Error leyendo {path}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("TEST: Verificación de configuración build_exe.py")
    print("="*60 + "\n")
    
    all_ok = True
    
    # Verificar archivos principales
    print("1️⃣  Archivos creados:")
    all_ok &= check_file("build_exe.py", "Script build_exe.py mejorado")
    all_ok &= check_file("BUILD_BOTEDDVER1.bat", "Script batch Windows")
    all_ok &= check_file("deploy_bot.py", "Script de despliegue")
    all_ok &= check_file("validate_before_build.py", "Script de validación")
    all_ok &= check_file("boteddver1.py", "Bot principal")
    
    # Verificar contenido de build_exe.py
    print("\n2️⃣  Contenido de build_exe.py:")
    all_ok &= check_contains("build_exe.py", "boteddver1.py", "Target: boteddver1.py")
    all_ok &= check_contains("build_exe.py", "def collect_hidden_imports", "Función recopilación imports")
    all_ok &= check_contains("build_exe.py", "def collect_data_files", "Función archivos de datos")
    all_ok &= check_contains("build_exe.py", "def main", "Función main()")
    all_ok &= check_contains("build_exe.py", "PyInstaller", "Soporte PyInstaller")
    all_ok &= check_contains("build_exe.py", "MetaTrader5", "Soporte MetaTrader5")
    
    # Verificar documentación
    print("\n3️⃣  Documentación:")
    all_ok &= check_file("BUILD_QUICK_REFERENCE.md", "Referencia rápida")
    all_ok &= check_file("BUILD_BOTEDDVER1_GUIDE.md", "Guía completa")
    all_ok &= check_file("BUILD_STATUS.md", "Estado del build")
    
    # Verificar archivos necesarios
    print("\n4️⃣  Archivos necesarios del bot:")
    all_ok &= check_file("requirements.txt", "Dependencias")
    all_ok &= check_file("mi_sesion.session", "Sesión MT5")
    
    # Resumen
    print("\n" + "="*60)
    if all_ok:
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
        print("\n🚀 ¡Listo para compilar!")
        print("\nEjecuta uno de estos comandos:\n")
        print("  1. python build_exe.py")
        print("  2. BUILD_BOTEDDVER1.bat (Windows)")
        print("  3. python deploy_bot.py")
        return 0
    else:
        print("⚠️  ALGUNOS TESTS FALLARON")
        print("="*60)
        print("\nVerifica los errores arriba e intenta de nuevo.")
        print("Si falta algún archivo, ejecuta validate_before_build.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())
