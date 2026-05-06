#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST RUNNER: Ejecuta todos los tests en secuencia
Test A: GOLD solo
Test B: SILVER solo
Test C: GOLD + SILVER (USE_MULTIPLE_PARTS=True)
"""

import sys
import subprocess
import time

tests = [
    ('test_gold_only.py', 'TEST A: GOLD SOLO'),
    ('test_silver_only.py', 'TEST B: SILVER SOLO'),
    ('test_both_pairs.py', 'TEST C: GOLD+SILVER MÚLTIPLES PARES'),
]

def run_test(script, name):
    """Ejecuta un test y retorna True si pasó"""
    print(f"\n{'='*80}")
    print(f"EJECUTANDO: {name}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd='c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas',
            capture_output=False,
            timeout=60
        )
        # Analizar output para determinar si pasó
        # (En un caso real, deberías parsear stdout)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name} tardó más de 60 segundos")
        return False
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("TEST RUNNER - COMPREHENSIVE TRADING BOT VALIDATION")
    print("="*80)
    print("\nEste script ejecutará 3 tests secuencialmente:")
    print("  1. TEST A: Apertura GOLD solo (USE_MULTIPLE_PARTS=False)")
    print("  2. TEST B: Apertura SILVER solo (USE_MULTIPLE_PARTS=False)")
    print("  3. TEST C: Apertura GOLD+SILVER (USE_MULTIPLE_PARTS=True)")
    print("\nCada test incluye:")
    print("  - Cierre de posiciones previas")
    print("  - Configuración del modo")
    print("  - Llamada a abrir_operacion_smart()")
    print("  - Verificación de posiciones abiertas")
    print("\n" + "="*80 + "\n")
    
    results = {}
    
    for script, name in tests:
        results[name] = run_test(script, name)
        time.sleep(3)  # Pausa entre tests
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80 + "\n")
    
    for name, passed in results.items():
        status = "✅ PASADO" if passed else "❌ FALLIDO"
        print(f"{status:12} | {name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n{'='*40}")
    print(f"Total: {passed}/{total} tests pasados")
    print(f"{'='*40}\n")
    
    if passed == total:
        print("🎉 ÉXITO: Todos los tests pasaron!")
        print("\nEl bot ahora puede:")
        print("  ✅ Abrir en GOLD solo")
        print("  ✅ Abrir en SILVER solo")
        print("  ✅ Abrir en GOLD + SILVER simultáneamente")
        print("  ✅ Usar análisis independiente para cada par")
        print("  ✅ Determinar dirección óptima automáticamente")
    elif passed > 0:
        print("⚠️  PARCIAL: Algunos tests pasaron, revisar los fallos")
    else:
        print("❌ FALLO: Ningún test pasó")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
