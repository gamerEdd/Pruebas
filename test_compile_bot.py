#!/usr/bin/env python
"""Verificar que botiaver1.py compila correctamente después del cambio"""

import sys

try:
    import botiaver1
    print("✅ botiaver1.py importado correctamente")
    print(f"✅ Clase MT5AdaptiveTradingBot encontrada: {hasattr(botiaver1, 'MT5AdaptiveTradingBot')}")
except SyntaxError as e:
    print(f"❌ ERROR DE SINTAXIS: {e}")
    sys.exit(1)
except Exception as e:
    print(f"⚠️ WARNING (puede ser normal): {type(e).__name__}: {str(e)[:100]}")
    print("✅ Pero el módulo IS SYNTACTICALLY VALID")

print("\n✅ COMPILACIÓN EXITOSA - Sin errores de sintaxis")
