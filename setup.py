import subprocess
import sys
import os

def install_requirements():
    print("Instalando dependencias necesarias...")
    
    # Lista de paquetes requeridos
    requirements = [
        'MetaTrader5',
        'numpy',
        'pandas',
        'tk'  # Para la interfaz gráfica
    ]
    
    # Instalar cada paquete
    for package in requirements:
        print(f"\nInstalando {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado correctamente")
        except Exception as e:
            print(f"❌ Error instalando {package}: {str(e)}")
            
    print("\n✨ Instalación completada")

def create_bat_file():
    """Crear archivo .bat para ejecutar el bot"""
    bat_content = """@echo off
python botiaver1.py
pause
"""
    
    try:
        with open('start_bot.bat', 'w') as f:
            f.write(bat_content)
        print("✅ Archivo start_bot.bat creado correctamente")
    except Exception as e:
        print(f"❌ Error creando archivo .bat: {str(e)}")

def main():
    print("=== Instalador Bot Trading MT5 ===")
    
    # Verificar Python
    python_version = sys.version_info
    if python_version.major != 3:
        print("❌ Error: Se requiere Python 3")
        sys.exit(1)
        
    # Verificar pip
    try:
        import pip
    except ImportError:
        print("❌ Error: pip no está instalado")
        sys.exit(1)
        
    # Instalar dependencias
    install_requirements()
    
    # Crear archivo .bat
    create_bat_file()
    
    print("\n=== Instalación Completa ===")
    print("Para ejecutar el bot:")
    print("1. Asegúrate que MetaTrader 5 esté instalado y configurado")
    print("2. Ejecuta el archivo start_bot.bat")
    print("\nPulsa ENTER para salir...")
    input()

if __name__ == "__main__":
    main()
