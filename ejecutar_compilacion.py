#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INSTRUCCIONES PARA COMPILAR EL BOT A .EXE
Actualizado con nuevos módulos incluidos

Este script prepara, verifica e invoca build_bot_exe.py
"""

import os
import subprocess
import sys

print("\n" + "="*70)
print("  COMPILADOR DE BOT EJECUTABLE")
print("  Versión: v1 con Tick Flow + Safety Filters")
print("="*70 + "\n")

# PASO 1: Verificar que estamos en el venv correcto
print("[PASO 1] Verificando entorno Python...")
print("[PASO 1] Usando el intérprete Python del sistema: {0}".format(sys.executable))

# PASO 2: Verificar PyInstaller
print("\n[PASO 2] Verificando PyInstaller...")
try:
    result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✓ PyInstaller encontrado: {result.stdout.strip()}")
    else:
        print("  [!] PyInstaller no encontrado")
        print("      Instalar con: pip install pyinstaller")
        sys.exit(1)
except Exception as e:
    print(f"  [!] Error: {e}")
    sys.exit(1)

# PASO 3: Mostrar módulos que se incluirán
print("\n[PASO 3] Módulos que se incluirán en el .exe:")
nuevos_modulos = [
    'tick_flow_analyzer      → Análisis de flujo de órdenes',
    'safety_filters_manager  → Gestión de filtros de seguridad',
    'advanced_feature_engine → Motor de características avanzadas',
    'ensemble_predictor_ai   → Predictor con ensemble',
    'pattern_recognizer      → Reconocimiento de patrones',
    'divergence_detector     → Detector de divergencias',
]
for mod in nuevos_modulos:
    print(f"  ✓ {mod}")

print("\n  ADEMÁS:")
print("  ✓ buy_specialist_ai, sell_specialist_ai")
print("  ✓ decision_arbitrator_ai, loss_protection_ai")
print("  ✓ trend_change_detector, trend_model, reversion_model")
print("  ✓ Y 20+ módulos más...")

# PASO 4: Opción para proceder
print("\n[PASO 4] ¿Deseas continuar con la compilación?")
print("  (Este proceso puede tomar 5-15 minutos)")
response = input("\n  Escribe 'SI' para continuar: ").strip().upper()

if response != 'SI':
    print("\n  ✗ Compilación cancelada")
    sys.exit(0)

# PASO 5: Ejecutar el build
print("\n" + "="*70)
print("  INICIANDO COMPILACIÓN...")
print("="*70 + "\n")

try:
    result = subprocess.run([sys.executable, 'build_bot_exe.py'], cwd=os.getcwd())
    sys.exit(result.returncode)
except Exception as e:
    print(f"\n✗ Error: {e}")
    sys.exit(1)
