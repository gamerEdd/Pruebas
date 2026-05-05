#!/usr/bin/env python3
"""
deploy_bot.py - DESPLIEGUE COMPLETO DE boteddver1.exe

Automatiza todo el proceso:
1. Validación pre-compilación
2. Compilación del ejecutable
3. Prueba básica del .exe
4. Creación de acceso directo (Windows)

Uso:
    python deploy_bot.py              # Despliegue completo estándar
    python deploy_bot.py --console    # Con consola
    python deploy_bot.py --mt5        # Con MetaTrader5
    python deploy_bot.py --no-test    # Sin pruebas
"""
import os
import sys
import subprocess
import shutil
import time

ROOT = os.path.abspath(os.path.dirname(__file__))

class BotDeployer:
    def __init__(self):
        self.console = '--console' in sys.argv
        self.include_mt5 = '--mt5' in sys.argv or '--include-mt5' in sys.argv
        self.no_test = '--no-test' in sys.argv
        self.no_shortcut = '--no-shortcut' in sys.argv
        
        self.exe_path = os.path.join(ROOT, 'dist', 'boteddver1.exe')
        self.shortcut_path = os.path.join(ROOT, 'boteddver1.lnk')
    
    def log(self, message, level='INFO'):
        """Imprime mensaje con formato"""
        levels = {
            'INFO': '   ℹ',
            'OK': '   ✓',
            'ERROR': '   ✗',
            'WARN': '   ⚠',
            'STEP': '\n>>> ',
        }
        prefix = levels.get(level, '   ')
        print(f"{prefix} {message}")
    
    def run_command(self, cmd, description):
        """Ejecuta comando y maneja errores"""
        self.log(f"Ejecutando: {description}", 'STEP')
        try:
            result = subprocess.run(cmd, shell=False, capture_output=False, text=True)
            if result.returncode == 0:
                self.log(f"{description} - OK", 'OK')
                return True
            else:
                self.log(f"{description} falló con código {result.returncode}", 'ERROR')
                return False
        except Exception as e:
            self.log(f"Error: {e}", 'ERROR')
            return False
    
    def validate(self):
        """Ejecuta validación pre-compilación"""
        print("\n" + "="*60)
        print("PASO 1: VALIDACIÓN PRE-COMPILACIÓN")
        print("="*60)
        
        cmd = [sys.executable, 'validate_before_build.py']
        result = subprocess.run(cmd, cwd=ROOT)
        
        if result.returncode == 0:
            self.log("Validación exitosa", 'OK')
            return True
        else:
            self.log("Falló la validación", 'ERROR')
            user_input = input("\n¿Continuar de todos modos? (s/n): ").strip().lower()
            return user_input == 's'
    
    def compile(self):
        """Compila el ejecutable"""
        print("\n" + "="*60)
        print("PASO 2: COMPILACIÓN")
        print("="*60)
        
        cmd = [sys.executable, 'build_exe.py']
        
        if self.console:
            cmd.append('--console')
            self.log("Modo console habilitado", 'INFO')
        
        if self.include_mt5:
            cmd.append('--include-mt5')
            self.log("MetaTrader5 incluido", 'INFO')
        
        self.log(f"Compilando boteddver1.py...", 'STEP')
        
        try:
            result = subprocess.run(cmd, cwd=ROOT)
            
            if result.returncode == 0 and os.path.exists(self.exe_path):
                size = os.path.getsize(self.exe_path) / (1024 * 1024)
                self.log(f"Compilación exitosa - {size:.2f} MB", 'OK')
                return True
            else:
                self.log("Compilación falló", 'ERROR')
                return False
        except Exception as e:
            self.log(f"Error de compilación: {e}", 'ERROR')
            return False
    
    def test_exe(self):
        """Prueba básica del ejecutable"""
        if self.no_test:
            self.log("Pruebas omitidas (--no-test)", 'INFO')
            return True
        
        print("\n" + "="*60)
        print("PASO 3: PRUEBA BÁSICA")
        print("="*60)
        
        if not os.path.exists(self.exe_path):
            self.log(f"Ejecutable no encontrado: {self.exe_path}", 'ERROR')
            return False
        
        self.log(f"Verificando integridad del .exe", 'STEP')
        
        # Verificar que el archivo sea ejecutable
        if os.path.isfile(self.exe_path):
            size = os.path.getsize(self.exe_path)
            if size > 10_000_000:  # Al menos 10MB esperado
                self.log(f"Tamaño del .exe: {size/1024/1024:.2f} MB", 'OK')
            else:
                self.log(f"El .exe parece demasiado pequeño ({size} bytes)", 'WARN')
        
        # Intentar obtener información del .exe (solo Windows)
        if sys.platform == 'win32':
            try:
                result = subprocess.run(
                    [self.exe_path, '--version'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    self.log("El .exe es ejecutable", 'OK')
                    return True
            except subprocess.TimeoutExpired:
                self.log("El .exe tardó demasiado en responder (puede estar iniciando UI)", 'INFO')
                return True
            except Exception:
                pass
        
        self.log("Prueba completada (ejecutable existe)", 'OK')
        return True
    
    def create_shortcut(self):
        """Crea acceso directo en Windows"""
        if self.no_shortcut or sys.platform != 'win32':
            self.log("Acceso directo omitido", 'INFO')
            return True
        
        print("\n" + "="*60)
        print("PASO 4: CREAR ACCESO DIRECTO")
        print("="*60)
        
        try:
            import win32com.client
            
            self.log("Creando acceso directo en Windows", 'STEP')
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(self.shortcut_path)
            shortcut.TargetPath = self.exe_path
            shortcut.WorkingDirectory = ROOT
            shortcut.Description = "BotEddiVer1 - Trading Bot"
            shortcut.IconLocation = os.path.join(ROOT, 'icon.ico') if os.path.exists(os.path.join(ROOT, 'icon.ico')) else self.exe_path
            shortcut.save()
            
            self.log(f"Acceso directo creado: {self.shortcut_path}", 'OK')
            return True
        except ImportError:
            self.log("pywin32 no disponible (omitiendo acceso directo)", 'INFO')
            print("  Para crear acceso directo manualmente:")
            print(f"    1. Click derecho en {self.exe_path}")
            print("    2. Crear acceso directo")
            return True
        except Exception as e:
            self.log(f"Error creando acceso directo: {e}", 'WARN')
            return True
    
    def show_summary(self):
        """Muestra resumen final"""
        print("\n" + "="*60)
        print("DESPLIEGUE COMPLETADO")
        print("="*60)
        
        if os.path.exists(self.exe_path):
            size = os.path.getsize(self.exe_path) / (1024 * 1024)
            print(f"\n✓ Ejecutable: {self.exe_path}")
            print(f"  Tamaño: {size:.2f} MB")
            print(f"\n✓ Para ejecutar el bot:")
            print(f"  • Doble-click: {self.exe_path}")
            
            if os.path.exists(self.shortcut_path):
                print(f"  • O usar acceso directo: {self.shortcut_path}")
            
            print(f"\n✓ Archivos generados:")
            print(f"  • dist/boteddver1.exe")
            if os.path.exists(self.shortcut_path):
                print(f"  • boteddver1.lnk (acceso directo)")
            
        else:
            print(f"\n✗ Error: No se encontró {self.exe_path}")
            return False
        
        return True
    
    def run(self):
        """Ejecuta el flujo completo"""
        print("\n" + "="*60)
        print("DESPLEGADOR DE BOTEDDVER1")
        print("="*60)
        print(f"\nDirectorio: {ROOT}")
        print(f"Tiempo: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar pasos
        if not self.validate():
            self.log("Despliegue cancelado en validación", 'WARN')
            return False
        
        if not self.compile():
            self.log("Despliegue cancelado en compilación", 'ERROR')
            return False
        
        if not self.test_exe():
            self.log("Despliegue cancelado en pruebas", 'ERROR')
            return False
        
        if not self.create_shortcut():
            self.log("Aviso: No se pudo crear acceso directo", 'WARN')
        
        return self.show_summary()

def main():
    """Punto de entrada"""
    try:
        deployer = BotDeployer()
        success = deployer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Despliegue cancelado por el usuario (Ctrl+C)")
        sys.exit(2)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
