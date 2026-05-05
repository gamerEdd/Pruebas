#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AUDITORIA COMPLETA DE MODULOS PARA COMPILACION
Verifica que todos los módulos requeridos existan y sean válidos
"""

import os
import sys
from pathlib import Path

# Lista de módulos requeridos en boteddver1.py
REQUIRED_MODULES = [
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

def check_module_exists(module_name):
    """Verificar que el módulo existe y es un archivo .py válido"""
    file_path = Path(f"{module_name}.py")
    if not file_path.exists():
        return False, "No existe"
    
    # Verificar que es un archivo válido (tamaño > 0)
    if file_path.stat().st_size == 0:
        return False, "Archivo vacío"
    
    return True, "OK"

def main():
    """Ejecutar auditoría"""
    print("\n" + "="*70)
    print("AUDITORIA DE MODULOS PARA COMPILACION.EXE")
    print("="*70 + "\n")
    
    found = 0
    missing = 0
    errors = []
    
    print(f"Verificando {len(REQUIRED_MODULES)} módulos requeridos...\n")
    
    for module in REQUIRED_MODULES:
        exists, status = check_module_exists(module)
        
        if exists:
            print(f"  [OK] {module:40} {status}")
            found += 1
        else:
            print(f"  [MISSING] {module:40} {status}", file=sys.stderr)
            missing += 1
            errors.append(module)
    
    print("\n" + "="*70)
    print(f"RESULTADO: {found}/{len(REQUIRED_MODULES)} módulos encontrados")
    print("="*70)
    
    if missing > 0:
        print(f"\n[ERROR] {missing} módulos faltantes:")
        for module in errors:
            print(f"        - {module}.py")
        print("\nNo se puede proceder con la compilación.")
        return 1
    else:
        print("\n[SUCCESS] Todos los módulos están disponibles")
        print("El sistema está listo para compilación con PyInstaller")
        return 0

if __name__ == '__main__':
    sys.exit(main())
