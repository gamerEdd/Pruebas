#!/usr/bin/env python
"""Test para verificar que run_all_checks() siempre retorna un dict"""

from safety_filters_manager import SafetyFiltersManager

print("\n" + "="*60)
print("TEST: run_all_checks() Return Type")
print("="*60)

manager = SafetyFiltersManager()

# Test 1: Sin snapshots (caso que causaba el error)
print("\n[TEST 1] Sin snapshots cargados:")
is_safe, checks = manager.run_all_checks()
print(f"  is_safe: {is_safe}")
print(f"  checks type: {type(checks)}")
print(f"  checks is dict: {isinstance(checks, dict)}")
if isinstance(checks, dict):
    print(f"  ✅ CORRECTO: safety_checks es dict")
    print(f"  Contents: {list(checks.keys())}")
else:
    print(f"  ❌ ERROR: safety_checks no es dict, es {type(checks)}")
    print(f"  Value: {checks}")

# Test 2: Verificar que get_filter_summary funciona
print("\n[TEST 2] get_filter_summary() funciona:")
try:
    summary = manager.get_filter_summary(checks)
    print(f"  ✅ Resumen generado correctamente")
    print(summary)
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "="*60)
print("✅ TEST COMPLETADO")
print("="*60 + "\n")
