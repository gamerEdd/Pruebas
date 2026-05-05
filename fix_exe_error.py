#!/usr/bin/env python3
"""
fix_exe_error.py

Script para diagnosticar y arreglar el error:
"could not load pyinstaller's embedded pkg archive from the executable"

Este error usualmente significa:
1. El .exe está corrupto
2. Falta un archivo crítico en el bundle
3. Conflicto entre opciones de PyInstaller
"""
import os
import sys
import subprocess
import shutil

ROOT = os.path.abspath(os.path.dirname(__file__))

def diagnose():
    """Diagnostica el problema"""
    print("\n" + "="*60)
    print("DIAGNÓSTICO: Error de embedded pkg archive")
    print("="*60 + "\n")
    
    exe_path = os.path.join(ROOT, 'dist', 'boteddver1.exe')
    
    if not os.path.exists(exe_path):
        print("✗ El .exe no existe en: dist/boteddver1.exe")
        print("\nSolución: Compila primero con:")
        print("  python build_exe.py")
        return False
    
    size = os.path.getsize(exe_path)
    size_mb = size / (1024 * 1024)
    
    print(f"ℹ Archivo encontrado: {exe_path}")
    print(f"ℹ Tamaño: {size_mb:.2f} MB")
    
    if size_mb < 50:
        print("\n✗ ¡El .exe es demasiado pequeño!")
        print(f"  Tamaño detectado: {size_mb:.2f} MB")
        print(f"  Tamaño esperado: 150-300 MB")
        print("\nCausas posibles:")
        print("  1. Compilación incompleta")
        print("  2. Falta la carpeta de dependencias")
        print("  3. PyInstaller no empaquetó correctamente")
        return False
    
    print(f"\n✓ Tamaño OK ({size_mb:.2f} MB)")
    print("ℹ El .exe parece estar completo")
    
    return True

def strategy_1_rebuild_clean():
    """Estrategia 1: Limpiar y recompilar"""
    print("\n" + "="*60)
    print("ESTRATEGIA 1: Limpiar y Recompilar")
    print("="*60 + "\n")
    
    print("🧹 Eliminando compilaciones anteriores...")
    
    dirs = ['build', 'dist', '.pytest_cache', '__pycache__']
    for d in dirs:
        path = os.path.join(ROOT, d)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"  ✓ Eliminado: {d}")
            except Exception as e:
                print(f"  ⚠ Error: {e}")
    
    print("\n🔨 Recompilando con opciones robustas...\n")
    
    cmd = [sys.executable, 'clean_and_rebuild.py']
    result = subprocess.run(cmd, cwd=ROOT)
    
    return result.returncode == 0

def strategy_2_rebuild_onedir():
    """Estrategia 2: Compilar como directorio (no one-file)"""
    print("\n" + "="*60)
    print("ESTRATEGIA 2: Compilar como directorio (one-dir)")
    print("="*60 + "\n")
    
    print("🔨 Recompilando como directorio...\n")
    
    # Crear comando PyInstaller personalizado
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onedir',  # Cambiar a directorio en lugar de one-file
        '--console',
        '--name', 'boteddver1',
        '--bootloader-ignore-signals',
        'boteddver1.py'
    ]
    
    print(f"Ejecutando: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=ROOT)
        
        if result.returncode == 0:
            exe_path = os.path.join(ROOT, 'dist', 'boteddver1', 'boteddver1.exe')
            if os.path.exists(exe_path):
                print(f"\n✓ Ejecutable generado en: {exe_path}")
                print(f"\nIntenta ejecutar:")
                print(f"  dist\\boteddver1\\boteddver1.exe")
                return True
        
        return result.returncode == 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def strategy_3_rebuild_without_onefile():
    """Estrategia 3: Compilar sin --onefile"""
    print("\n" + "="*60)
    print("ESTRATEGIA 3: Recompilar sin --onefile")
    print("="*60 + "\n")
    
    print("🔨 Recompilando sin compresión de one-file...\n")
    
    # Limpiar primero
    for d in ['build', 'dist']:
        path = os.path.join(ROOT, d)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except:
                pass
    
    cmd = [
        sys.executable, 'build_exe.py',
        '--console'
    ]
    
    print(f"Ejecutando: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=ROOT)
    
    return result.returncode == 0

def main():
    print("\n" + "="*60)
    print("REPARADOR: Error de embedded pkg archive")
    print("="*60)
    
    # Diagnosticar
    if not diagnose():
        print("\n⚠️  Ejecuta primero:")
        print("  python build_exe.py")
        print("\nO intenta limpiar y recompilar:")
        print("  python clean_and_rebuild.py")
        return 1
    
    # Opciones
    print("\n" + "="*60)
    print("OPCIONES DE REPARACIÓN")
    print("="*60)
    print("\n1. Limpiar y recompilar (RECOMENDADO)")
    print("2. Compilar como directorio (one-dir)")
    print("3. Recompilar con opciones alternativas")
    print("4. Salir")
    
    try:
        choice = input("\nElige opción (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n\nCancelado")
        return 2
    
    if choice == '1':
        print("\nEjecutando estrategia 1...")
        success = strategy_1_rebuild_clean()
    elif choice == '2':
        print("\nEjecutando estrategia 2...")
        success = strategy_2_rebuild_onedir()
    elif choice == '3':
        print("\nEjecutando estrategia 3...")
        success = strategy_3_rebuild_without_onefile()
    else:
        print("Cancelado")
        return 0
    
    if success:
        print("\n" + "="*60)
        print("✅ ¡REPARACIÓN EXITOSA!")
        print("="*60)
        print("\nAhora prueba ejecutar el bot:")
        exe_path = os.path.join(ROOT, 'dist', 'boteddver1.exe')
        if os.path.exists(exe_path):
            print(f"  dist\\boteddver1.exe")
        else:
            exe_path = os.path.join(ROOT, 'dist', 'boteddver1', 'boteddver1.exe')
            if os.path.exists(exe_path):
                print(f"  dist\\boteddver1\\boteddver1.exe")
        return 0
    else:
        print("\n" + "="*60)
        print("✗ LA ESTRATEGIA NO FUNCIONÓ")
        print("="*60)
        print("\nPrueba otra estrategia ejecutando de nuevo:")
        print("  python fix_exe_error.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())
