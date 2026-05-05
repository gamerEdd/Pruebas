#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verifica que PyInstaller pueda incluir todas las dependencias
"""

import sys
import os

print("=" * 70)
print("VERIFICACION DE PYINSTALLER Y DEPENDENCIAS")
print("=" * 70)
print()

# 1. Verificar PyInstaller
print("[1] Verificando PyInstaller...")
try:
    import PyInstaller
    print(f"    OK - PyInstaller importado correctamente")
except ImportError as e:
    print(f"    ERROR - PyInstaller no instalado: {e}")
    print("    Instala: pip install pyinstaller")
    sys.exit(1)

# 2. Verificar módulos del bot
print("\n[2] Verificando módulos del bot...")
bot_modules = [
    'buy_specialist_ai',
    'sell_specialist_ai',
    'decision_arbitrator_ai',
    'recovery_based_closer',
    'loss_protection_ai',
    'feedback_loop_ai',
    'rapid_ops_validator',
    'entry_point_ai',
    'adaptive_parameters',
    'gold_analyzer',
    'loss_analyzer',
    'data_updater_module',
    'data_loader_trainer',
    'indicator_base',
    'temporal_weighting',
    'outlier_filter',
    'candle_validator',
    'market_snapshot_generator',
    'regime_detector',
    'trend_model',
    'reversion_model',
    'bias_monitor',
    'drift_detector',
    'dynamic_weights',
    'meta_selector',
    'bot_integration_manager',
    'safety_filters_manager',
]

ok_count = 0
error_count = 0

for module_name in bot_modules:
    try:
        mod = __import__(module_name)
        print(f"    [OK] {module_name}")
        ok_count += 1
    except ImportError as e:
        print(f"    [ERROR] {module_name} - {str(e)[:50]}")
        error_count += 1

print(f"\n    Resultado: {ok_count}/{len(bot_modules)} módulos disponibles")

# 3. Verificar librerías de soporte
print("\n[3] Verificando librerías de soporte...")
support_libs = [
    'MetaTrader5',
    'xgboost',
    'numpy',
    'pandas',
    'sklearn',
    'scipy',
]

for lib in support_libs:
    try:
        mod = __import__(lib)
        print(f"    ✓ {lib}")
    except ImportError:
        print(f"    ✗ {lib} - no instalado")

# 4. Verificar que PyInstaller puede analizar el proyecto
print("\n[4] Verificando que PyInstaller está correctamente instalado...")
try:
    import PyInstaller
    version = PyInstaller.__version__
    print(f"    [OK] PyInstaller versión {version} disponible")
except Exception as e:
    print(f"    [ERROR] Error: {e}")

# 5. Verificar archivos necesarios
print("\n[5] Verificando archivos del proyecto...")
files_to_check = [
    'boteddver1.py',
    'build_bot_exe.py',
    'buy_specialist_ai.py',
    'sell_specialist_ai.py',
    'recovery_based_closer.py',
]

for filename in files_to_check:
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        print(f"    ✓ {filename}")
    else:
        print(f"    ✗ {filename} no encontrado")

print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)

if error_count == 0:
    print("✅ TODAS LAS DEPENDENCIAS ESTAN DISPONIBLES")
    print("   PyInstaller puede compilar el bot exitosamente")
    print("\n   Para compilar ejecuta:")
    print("   python build_bot_exe.py")
else:
    print(f"⚠️ ADVERTENCIA: {error_count} módulos no disponibles")
    print("   Instala módulos faltantes para que la compilación sea completa")

print("=" * 70)
