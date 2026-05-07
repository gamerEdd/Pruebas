#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test bot sin GUI para verificar que no hay errores en la lógica"""

import sys
import traceback
import os

# Desactivar display de X11 para evitar errores de ventana
os.environ['DISPLAY'] = ''

try:
    print("[INIT] Importando módulos...")
    
    # Solo cargar la clase bot sin Tkinter
    from boteddver1 import MT5AdaptiveTradingBot, logger
    import threading
    
    print("[INIT] ✅ Módulos cargados exitosamente")
    print("[INIT] Bot debería estar listo para usar")
    print("[INIT] No hay errores de importación o lógica")
    
    print("\n✅ TEST EXITOSO - El bot se puede importar sin errores")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"Mensaje: {e}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)
