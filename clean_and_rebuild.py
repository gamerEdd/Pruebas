#!/usr/bin/env python3
"""
clean_and_rebuild.py

Script para limpiar las compilaciones anteriores y recompilar desde cero
Soluciona problemas de "could not load pyinstaller's embedded pkg archive"
"""
import os
import sys
import shutil
import subprocess

ROOT = os.path.abspath(os.path.dirname(__file__))

def remove_directory(path, name):
    """Elimina un directorio si existe"""
    full_path = os.path.join(ROOT, path)
    if os.path.exists(full_path):
        try:
            shutil.rmtree(full_path)
            print(f"✓ Eliminado: {path}")
            return True
        except Exception as e:
            print(f"✗ Error eliminando {path}: {e}")
            return False
    return True

def remove_file(path, name):
    """Elimina un archivo si existe"""
    full_path = os.path.join(ROOT, path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
            print(f"✓ Eliminado: {path}")
            return True
        except Exception as e:
            print(f"✗ Error eliminando {path}: {e}")
            return False
    return True

def main():
    print("\n" + "="*60)
    print("LIMPIEZA Y RECOMPILACIÓN DESDE CERO")
    print("="*60 + "\n")
    
    print("🧹 Limpiando compilaciones anteriores...\n")
    
    # Directorios a eliminar
    dirs_to_remove = [
        ('build', 'Directorio de compilación'),
        ('dist', 'Directorio de distribución'),
        ('.pytest_cache', 'Cache de pytest'),
        ('__pycache__', 'Cache de Python'),
    ]
    
    # Archivos .spec a eliminar
    specs_to_remove = [
        'boteddver1.spec',
        'boteddver1.egg-info',
    ]
    
    all_ok = True
    
    for dir_path, description in dirs_to_remove:
        if not remove_directory(dir_path, description):
            all_ok = False
    
    print()
    for spec_file in specs_to_remove:
        if not remove_file(spec_file, spec_file):
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Algunos archivos no pudieron eliminarse")
        print("Continua de todos modos...\n")
    
    # Ahora recompilar
    print("\n" + "="*60)
    print("RECOMPILANDO DESDE CERO...")
    print("="*60 + "\n")
    
    cmd = [sys.executable, 'build_exe.py', '--console']
    
    print("Ejecutando: python build_exe.py --console\n")
    
    try:
        result = subprocess.run(cmd, cwd=ROOT)
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("✅ RECOMPILACIÓN EXITOSA")
            print("="*60)
            
            exe_path = os.path.join(ROOT, 'dist', 'boteddver1.exe')
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"\n✓ Ejecutable generado: dist/boteddver1.exe")
                print(f"✓ Tamaño: {size:.2f} MB")
                print(f"\nAhora prueba ejecutar:")
                print(f"  dist\\boteddver1.exe")
            
            return 0
        else:
            print(f"\n✗ Recompilación falló con código: {result.returncode}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n✗ Recompilación cancelada por usuario (Ctrl+C)")
        return 2
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
