#!/usr/bin/env python3
"""
simple_rebuild.py

Recompilación EXTREMADAMENTE SIMPLE
- Borra COMPLETAMENTE todo
- Compila con mínimas opciones
- Evita archivos .spec
"""
import os
import sys
import shutil
import subprocess

ROOT = os.path.abspath(os.path.dirname(__file__))

def main():
    print("\n" + "="*70)
    print("RECOMPILACIÓN SIMPLE Y DIRECTA")
    print("="*70 + "\n")
    
    # PASO 1: Borrar TODO
    print("🗑️  PASO 1: Eliminando todas las compilaciones anteriores...")
    print()
    
    dirs = ['build', 'dist', '__pycache__', '.pytest_cache']
    for d in dirs:
        path = os.path.join(ROOT, d)
        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
                print(f"   ✓ {d}/")
            except Exception as e:
                print(f"   ⚠ {d}: {e}")
    
    # Borrar spec
    spec_file = 'boteddver1.spec'
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"   ✓ {spec_file}")
        except Exception as e:
            print(f"   ⚠ {spec_file}: {e}")
    
    print()
    
    # PASO 2: Compilar de forma SIMPLE
    print("🔨 PASO 2: Compilando...")
    print()
    
    # Comando MINIMALISTA - sin argumentos complicados
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onedir',                  # Directorio en lugar de archivo único
        '--console',                 # Con consola
        '--clean',                   # Limpiar antes
        'boteddver1.py'              # Archivo principal
    ]
    
    print(f"Comando: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=ROOT)
        
        if result.returncode == 0:
            exe_path = os.path.join(ROOT, 'dist', 'boteddver1', 'boteddver1.exe')
            
            if os.path.exists(exe_path):
                print("\n" + "="*70)
                print("✅ ¡ÉXITO! Ejecutable generado correctamente")
                print("="*70)
                
                size = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"\n📁 Ubicación: {exe_path}")
                print(f"📊 Tamaño: {size:.2f} MB")
                
                print("\n🚀 Para ejecutar:")
                print(f"   dist\\boteddver1\\boteddver1.exe")
                
                print("\n💡 O crear acceso directo a:")
                print(f"   {os.path.join(ROOT, 'dist', 'boteddver1')}")
                
                return 0
            else:
                print("\n⚠ PyInstaller terminó pero no se encontró el .exe")
                return 1
        else:
            print(f"\n✗ PyInstaller falló con código: {result.returncode}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n✗ Compilación cancelada (Ctrl+C)")
        return 2
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
