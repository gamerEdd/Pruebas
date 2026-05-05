#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AUDITORIA FINAL PRE-COMPILACION
Verifica que TODOS los módulos estén disponibles para compilar el .exe
"""

import os
import sys
import ast
from pathlib import Path

# Lista master de 38 módulos requeridos
REQUIRED_MODULES = [
    'boteddver1',
    # Core specialists
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
    # Data management
    'data_updater_module',
    'data_loader_trainer',
    # Pro system (Nivel 5-10)
    'regime_detector',
    'trend_model',
    'reversion_model',
    'bias_monitor',
    'drift_detector',
    'dynamic_weights',
    'meta_selector',
    'bot_integration_manager',
    # Advanced V12 modules
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
    # P3 Phase utilities
    'indicator_base',
    'temporal_weighting',
    'outlier_filter',
    'candle_validator',
    'market_snapshot_generator',
    'safety_filters_manager',
]

def get_hiddenimports_from_build_script():
    """Extraer la lista de hiddenimports de build_bot_exe.py"""
    with open('build_bot_exe.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la sección hiddenimports
    start = content.find("'boteddver1',")
    end = content.find("],", start)
    section = content[start:end+2]
    
    # Extraer módulos
    modules = []
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith("'") and line.endswith("',"):
            module = line.strip("',")
            modules.append(module)
        elif line.startswith("'") and line.endswith("'"):
            module = line.strip("'")
            if module:
                modules.append(module)
    
    return modules

def get_modules_from_boteddver1():
    """Extraer imports de boteddver1.py"""
    imports = set()
    with open('boteddver1.py', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('from ') and ' import ' in line:
                module = line.split(' import ')[0].replace('from ', '').strip()
                imports.add(module)
    return imports

def main():
    """Ejecutar auditoría final"""
    print("\n" + "="*80)
    print("AUDITORIA FINAL PRE-COMPILACION .EXE")
    print("="*80 + "\n")
    
    all_ok = True
    
    # [1] Verificar que existan los 38 módulos
    print("[1] Verificando existencia de 38 módulos requeridos...\n")
    missing_files = []
    for module in REQUIRED_MODULES:
        file_path = Path(f"{module}.py")
        if not file_path.exists():
            print(f"    [MISSING] {module}.py", file=sys.stderr)
            missing_files.append(module)
            all_ok = False
        else:
            print(f"    [OK] {module}.py")
    
    print(f"\n    Resultado: {len(REQUIRED_MODULES) - len(missing_files)}/{len(REQUIRED_MODULES)} módulos encontrados\n")
    
    # [2] Verificar que build_bot_exe.py incluya TODOS los módulos
    print("[2] Verificando que build_bot_exe.py incluya todos los módulos...\n")
    try:
        modules_in_build = set(get_hiddenimports_from_build_script())
        # Filtrar solo los módulos Python (no librerías externas)
        modules_in_build = {m for m in modules_in_build if m not in ['MetaTrader5', 'xgboost', 'numpy', 'pandas', 'sklearn', 'scipy']}
        
        required_set = set(REQUIRED_MODULES)
        
        missing_in_build = required_set - modules_in_build
        extra_in_build = modules_in_build - required_set
        
        if missing_in_build:
            print(f"    [ERROR] Módulos faltantes en build_bot_exe.py:")
            for module in sorted(missing_in_build):
                print(f"            - {module}")
            all_ok = False
        else:
            print(f"    [OK] Todos los módulos requeridos están en build_bot_exe.py")
        
        if extra_in_build:
            print(f"\n    [WARNING] Módulos extra en build_bot_exe.py:")
            for module in sorted(extra_in_build):
                print(f"             - {module} (no está en boteddver1.py)")
        
        print(f"\n    Resultado: {len(modules_in_build)} módulos en build_bot_exe.py\n")
    except Exception as e:
        print(f"    [ERROR] No se pudo leer build_bot_exe.py: {e}\n")
        all_ok = False
    
    # [3] Verificar imports en boteddver1.py
    print("[3] Verificando imports en boteddver1.py...\n")
    imports = get_modules_from_boteddver1()
    print(f"    Módulos importados: {len(imports)}")
    print(f"    Módulos requeridos: {len(REQUIRED_MODULES)}\n")
    
    # [4] Conclusión
    print("="*80)
    if all_ok and not missing_files:
        print("[SUCCESS] AUDITORIA EXITOSA - SISTEMA LISTO PARA COMPILACION")
        print("\nInstrucción para compilar:")
        print("  python build_bot_exe.py")
        print("\nEl ejecutable se generará en: dist/MT5TradingBot_v16_Edd.exe")
        print("="*80 + "\n")
        return 0
    else:
        print("[FAILURE] AUDITORIA FALLIDA - HAY PROBLEMAS")
        if missing_files:
            print(f"\n  - Faltan {len(missing_files)} archivos .py")
        print("="*80 + "\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
