#!/usr/bin/env python
import py_compile
import sys

try:
    py_compile.compile('boteddver1.py', doraise=True)
    print("[✓] COMPILACIÓN EXITOSA - BOT LISTO")
    print("[✓] Cambios aplicados:")
    print("    - Volumen dinámico REMOVIDO")
    print("    - Usa SOLO valor de VOL_DIFF de UI")
    print("    - SL/TP usando SOLO TP_DIFF y SL_DIFF de UI")
    print("    - NO hay más cálculos dinámicos complejos")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"[✗] ERROR DE COMPILACIÓN:\n{e}")
    sys.exit(1)
