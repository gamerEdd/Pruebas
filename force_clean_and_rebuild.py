#!/usr/bin/env python3
"""
force_clean_and_rebuild.py

Script para limpiar FORZADAMENTE archivos bloqueados y recompilar
Soluciona: PermissionError - El proceso no tiene acceso al archivo
"""
import os
import sys
import shutil
import subprocess
import time

ROOT = os.path.abspath(os.path.dirname(__file__))

def force_remove_directory(path, retries=3):
    """Intenta eliminar un directorio forzadamente"""
    full_path = os.path.join(ROOT, path)
    
    if not os.path.exists(full_path):
        return True
    
    for attempt in range(retries):
        try:
            print(f"Eliminando {path}... (intento {attempt + 1}/{retries})")
            
            # En Windows, usar rmdir
            if sys.platform == 'win32':
                import ctypes
                
                # Atributo de solo lectura
                ctypes.windll.kernel32.SetFileAttributesW(full_path, 0x80)
            
            # Intentar eliminación recursiva
            if os.path.isdir(full_path):
                shutil.rmtree(full_path, ignore_errors=True)
                
                # Esperar y verificar
                time.sleep(1)
                
                if not os.path.exists(full_path):
                    print(f"✓ Eliminado: {path}")
                    return True
            
            # Si sigue existiendo, esperar y reintentar
            if os.path.exists(full_path):
                print(f"⚠ Aún existe, esperando...")
                time.sleep(2)
        
        except Exception as e:
            print(f"✗ Error en intento {attempt + 1}: {e}")
            time.sleep(1)
    
    print(f"⚠ No se pudo eliminar completamente: {path}")
    return False

def main():
    print("\n" + "="*60)
    print("LIMPIEZA FORZADA Y RECOMPILACIÓN")
    print("="*60 + "\n")
    
    print("⚠️  Limpiando archivos bloqueados...\n")
    
    # Directorios a eliminar (cuidadosamente)
    dirs_to_remove = [
        'build',
        'dist',
        '__pycache__',
        '.pytest_cache',
    ]
    
    # Intentar eliminar cada uno
    for dir_name in dirs_to_remove:
        force_remove_directory(dir_name, retries=3)
        print()
    
    # Archivos spec a eliminar
    spec_file = os.path.join(ROOT, 'boteddver1.spec')
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"✓ Eliminado: boteddver1.spec")
        except Exception as e:
            print(f"⚠ Error eliminando spec: {e}")
    
    # Esperar un momento
    print("\n⏳ Esperando 2 segundos...")
    time.sleep(2)
    
    # Verificar que realmente se eliminaron
    print("\n✓ Directorios limpios, comenzando recompilación...\n")
    
    print("="*60)
    print("RECOMPILANDO (MODO ONE-DIR - más estable)")
    print("="*60 + "\n")
    
    # Usar one-dir en lugar de one-file (más estable)
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onedir',  # one-dir en lugar de one-file
        '--console',
        '--name', 'boteddver1',
        '--bootloader-ignore-signals',
        'boteddver1.py'
    ]
    
    try:
        result = subprocess.run(cmd, cwd=ROOT)
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("✅ RECOMPILACIÓN EXITOSA")
            print("="*60)
            
            exe_path = os.path.join(ROOT, 'dist', 'boteddver1', 'boteddver1.exe')
            
            if os.path.exists(exe_path):
                print(f"\n✓ Ejecutable generado: dist/boteddver1/boteddver1.exe")
                
                size = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"✓ Tamaño: {size:.2f} MB")
                
                print(f"\n🚀 Para ejecutar:")
                print(f"   dist\\boteddver1\\boteddver1.exe")
                
                return 0
        
        return 1
    
    except KeyboardInterrupt:
        print("\n\n✗ Cancelado por usuario (Ctrl+C)")
        return 2
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
