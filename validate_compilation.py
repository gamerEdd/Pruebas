#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Trading Bot - Validador de Compilación
Verifica que todos los módulos necesarios existan y sean válidos
"""

import os
import sys
import importlib.util
from pathlib import Path

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE} {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")

def print_ok(text):
    print(f"{Colors.GREEN}[OK]{Colors.ENDC} {text}")

def print_error(text):
    print(f"{Colors.RED}[ERROR]{Colors.ENDC} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}[ADVERTENCIA]{Colors.ENDC} {text}")

def print_info(text):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {text}")

def check_module_exists(module_name):
    """Verifica si un módulo local .py existe"""
    file_path = Path(f"{module_name}.py")
    if file_path.exists():
        return True, str(file_path.absolute())
    return False, None

def check_module_importable(module_name):
    """Verifica si un módulo puede ser importado"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

def check_python_version():
    """Verifica versión de Python"""
    print_header("1. VERIFICACION DE PYTHON")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Versión Python: {version_str}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Se requiere Python 3.8+, tienes {version_str}")
        return False
    
    print_ok(f"Python {version_str} es compatible")
    return True

def check_local_modules():
    """Verifica que todos los módulos locales existan"""
    print_header("2. VERIFICACION DE MODULOS LOCALES")
    
    local_modules = [
        # Especialistas IA
        'buy_specialist_ai',
        'sell_specialist_ai',
        'decision_arbitrator_ai',
        'loss_protection_ai',
        'feedback_loop_ai',
        'rapid_ops_validator',
        'entry_point_ai',
        'adaptive_parameters',
        
        # Data & Analysis
        'gold_analyzer',
        'loss_analyzer',
        'data_updater_module',
        'data_loader_trainer',
        'trade_logger',
        'auto_calibration',
        
        # Institutional Level
        'regime_detector',
        'trend_model',
        'reversion_model',
        'bias_monitor',
        'drift_detector',
        'dynamic_weights',
        'meta_selector',
        'bot_integration_manager',
        
        # V12 Advanced
        'super_analyzer',
        'dynamic_score_calibration',
        'recovery_potential_enhanced',
        'spread_slippage_analyzer',
        'time_based_session_filter',
        'correlation_analyzer',
        'trend_change_detector',
    ]
    
    all_ok = True
    missing_modules = []
    
    for module in sorted(local_modules):
        exists, path = check_module_exists(module)
        if exists:
            print_ok(f"{module:40s} -> {path}")
        else:
            print_error(f"{module:40s} [NO ENCONTRADO]")
            missing_modules.append(module)
            all_ok = False
    
    if not all_ok:
        print(f"\n{Colors.RED}Faltan {len(missing_modules)} módulos:{Colors.ENDC}")
        for m in missing_modules:
            print(f"  - {m}.py")
    
    return all_ok

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    print_header("3. VERIFICACION DE DEPENDENCIAS EXTERNAS")
    
    dependencies = [
        'MetaTrader5',
        'numpy',
        'pandas',
        'sklearn',
        'joblib',
        'dateutil',
        'pytz',
    ]
    
    missing_deps = []
    
    for dep in sorted(dependencies):
        try:
            importable, error = check_module_importable(dep)
            if importable:
                print_ok(f"{dep:30s} está instalado")
            else:
                print_warning(f"{dep:30s} NO está instalado")
                missing_deps.append(dep)
        except:
            print_warning(f"{dep:30s} No se pudo verificar")
    
    if missing_deps:
        print(f"\n{Colors.YELLOW}Para instalar las dependencias faltantes, ejecuta:{Colors.ENDC}")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True

def check_main_file():
    """Verifica que el archivo principal exista"""
    print_header("4. VERIFICACION DEL ARCHIVO PRINCIPAL")
    
    if Path("botiaver1.py").exists():
        print_ok("botiaver1.py encontrado")
        return True
    else:
        print_error("botiaver1.py NO encontrado")
        return False

def check_spec_file():
    """Verifica que el archivo .spec exista y sea válido"""
    print_header("5. VERIFICACION DEL ARCHIVO SPEC")
    
    if not Path("botiaver1.spec").exists():
        print_error("botiaver1.spec NO encontrado")
        return False
    
    print_ok("botiaver1.spec encontrado")
    
    # Verificar contenido básico
    with open("botiaver1.spec", "r") as f:
        content = f.read()
    
    checks = {
        "hiddenimports": "Lista de módulos ocultos",
        "buy_specialist_ai": "Al menos un módulo local",
        "Analysis": "Configuración PyInstaller",
        "EXE": "Sección de ejecutable",
    }
    
    for key, description in checks.items():
        if key in content:
            print_ok(f"Contiene: {description}")
        else:
            print_warning(f"Falta: {description}")
    
    return True

def check_build_scripts():
    """Verifica que los scripts de compilación existan"""
    print_header("6. VERIFICACION DE SCRIPTS DE COMPILACION")
    
    scripts = {
        'build_installer.bat': 'Script PyInstaller',
        'build_nsis_installer.bat': 'Script NSIS',
        'build_nsis_installer.nsi': 'Configuración NSIS',
    }
    
    all_ok = True
    for script, description in scripts.items():
        if Path(script).exists():
            print_ok(f"{script:35s} -> {description}")
        else:
            print_warning(f"{script:35s} -> NO ENCONTRADO")
            all_ok = False
    
    return all_ok

def check_logs_directory():
    """Verifica que la carpeta logs existe"""
    print_header("7. VERIFICACION DE DIRECTORIOS")
    
    if Path("logs").exists():
        print_ok("Directorio logs/ existe")
        return True
    else:
        print_warning("Directorio logs/ NO existe")
        print_info("Creando logs/...")
        Path("logs").mkdir(exist_ok=True)
        print_ok("Directorio logs/ creado")
        return True

def print_summary(results):
    """Imprime resumen de verificación"""
    print_header("RESUMEN DE VERIFICACION")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for check_name, result in results.items():
        status = f"{Colors.GREEN}[OK]{Colors.ENDC}" if result else f"{Colors.RED}[FALLÓ]{Colors.ENDC}"
        print(f"{status} {check_name}")
    
    print(f"\n{Colors.BOLD}Total:{Colors.ENDC} {passed}/{total} checks pasados")
    
    if all(results.values()):
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ LISTO PARA COMPILAR{Colors.ENDC}")
        print(f"\nEjecuta uno de estos comandos:")
        print(f"  1. {Colors.BOLD}build_installer.bat{Colors.ENDC}          <- Compilar EXE con PyInstaller")
        print(f"  2. {Colors.BOLD}build_nsis_installer.bat{Colors.ENDC}    <- Crear instalador NSIS")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ ERRORES DETECTADOS - Corrige los problemas arriba{Colors.ENDC}")
        return False

def main():
    """Función principal"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     MT5 TRADING BOT - VALIDADOR DE COMPILACION                     ║")
    print("║     Verificando que todos los módulos estén listos                ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    results = {}
    
    # Ejecutar verificaciones
    results['Python version'] = check_python_version()
    results['Local modules'] = check_local_modules()
    results['Dependencies'] = check_dependencies()
    results['Main file'] = check_main_file()
    results['Spec file'] = check_spec_file()
    results['Build scripts'] = check_build_scripts()
    results['Logs directory'] = check_logs_directory()
    
    # Resumen
    success = print_summary(results)
    
    print("\n")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
