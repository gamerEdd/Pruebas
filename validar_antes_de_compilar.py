#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VALIDACIÓN PREVIA ANTES DE COMPILAR
Verifica que todos los módulos críticos existan y sean compilables
"""

import os
import sys
import traceback
from pathlib import Path

print("\n" + "="*70)
print("  VALIDACIÓN PREVIA - VERIFICAR MÓDULOS ANTES DE COMPILAR")
print("="*70 + "\n")

# Lista de módulos que se van a incluir en el .exe
MODULOS_CRITICOS = [
    # Core del bot
    'botiaver1',
    'buy_specialist_ai',
    'sell_specialist_ai',
    'decision_arbitrator_ai',
    
    # NUEVOS MÓDULOS
    'tick_flow_analyzer',
    'safety_filters_manager',
    
    # Análisis de mercado
    'trend_change_detector',
    'gold_analyzer',
    'super_analyzer',
    
    # Protecting & Risk
    'loss_protection_ai',
    'loss_analyzer',
    
    # Data & Training
    'feedback_loop_ai',
    'data_updater_module',
    'ml_training_engine_v2',
    
    # Utilidades
    'rapid_ops_validator',
    'entry_point_ai',
    'adaptive_parameters',
    'trade_logger',
]

print("[PASO 1] Verificando archivos .py existen...")
archivo_count = 0
missing_files = []

for modulo in MODULOS_CRITICOS:
    filepath = f"{modulo}.py"
    if os.path.exists(filepath):
        print(f"  ✓ {modulo}.py")
        archivo_count += 1
    else:
        print(f"  ✗ {modulo}.py (FALTA)")
        missing_files.append(modulo)

print(f"\nTotal: {archivo_count}/{len(MODULOS_CRITICOS)} archivos encontrados\n")

if missing_files:
    print("[!] ADVERTENCIA: Faltan los siguientes módulos:")
    for mod in missing_files:
        print(f"    - {mod}.py")
    print("\nEstos módulos se intentarán compilar de todas formas,")
    print("pero puede que falten en el .exe final.\n")

# PASO 2: Verificar compilación de cada módulo
print("[PASO 2] Verificando que cada módulo compila sin errores...")
compile_errors = []

for modulo in MODULOS_CRITICOS:
    filepath = f"{modulo}.py"
    if not os.path.exists(filepath):
        continue
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, filepath, 'exec')
        print(f"  ✓ {modulo}.py (sintaxis OK)")
    except SyntaxError as e:
        print(f"  ✗ {modulo}.py (ERROR DE SINTAXIS)")
        compile_errors.append((modulo, str(e)))
    except Exception as e:
        print(f"  ⚠️  {modulo}.py ({type(e).__name__})")

print()

if compile_errors:
    print("[!] ERRORES DE COMPILACIÓN ENCONTRADOS:")
    for mod, error in compile_errors:
        print(f"    {mod}: {error[:60]}...")
    print("\n✗ NO SE PUEDE COMPILAR - Corrige los errores primero\n")
    sys.exit(1)

# PASO 3: Verificar módulos críticos de librerías
print("[PASO 3] Verificando dependencias críticas...")
dependencias = [
    ('MetaTrader5', 'MetaTrader5'),
    ('numpy', 'NumPy'),
    ('pandas', 'Pandas'),
    ('sklearn', 'scikit-learn'),
    ('xgboost', 'XGBoost'),
    ('joblib', 'joblib'),
]

todas_ok = True
for import_name, display_name in dependencias:
    try:
        __import__(import_name)
        print(f"  ✓ {display_name}")
    except ImportError:
        print(f"  ✗ {display_name} (NO INSTALADO)")
        todas_ok = False

print()

if not todas_ok:
    print("[!] Faltan dependencias. Instalar con:")
    print("    pip install -r requirements.txt\n")
    sys.exit(1)

# PASO 4: Listar archivos que se compilarán
print("[PASO 4] Configuración de compilación:")
print(f"  • Modules: {len(MODULOS_CRITICOS)} módulos")
print(f"  • Input: botiaver1.py")
print(f"  • Output: dist/MT5TradingBot_v1.exe (~200-300 MB)")
print(f"  • Build spec: botiaver1_onefile.spec")

# PASO 5: Resumen
print("\n" + "="*70)
if archivo_count == len(MODULOS_CRITICOS):
    print("✅ VALIDACIÓN COMPLETADA - TODO OK")
    print("   Puedes compilar con: python ejecutar_compilacion.py")
else:
    print("⚠️  VALIDACIÓN COMPLETADA - CON ADVERTENCIAS")
    print("   Algunos módulos faltan pero puedes intentar compilar")
    print("   python ejecutar_compilacion.py")

print("="*70 + "\n")
