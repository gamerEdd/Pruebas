#!/usr/bin/env python
"""Test para verificar que trend_change_detector.py compila correctamente"""

import sys
import traceback

try:
    import trend_change_detector
    print("✅ trend_change_detector.py importado correctamente")
    
    # Verificar que la clase existe
    detector = trend_change_detector.TrendChangeDetector()
    print(f"✅ TrendChangeDetector instanciada: {detector.name}")
    
except SyntaxError as e:
    print(f"❌ ERROR DE SINTAXIS: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✅ COMPILACIÓN EXITOSA - Sin errores de sintaxis")
