#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wrapper para ejecutar bot con mejor captura de errores"""

import sys
import traceback

try:
    # Importar e ejecutar bot
    from boteddver1 import *
    import tkinter as tk
    
    print("\n[TEST] Creando ventana Tkinter...")
    root = tk.Tk()
    root.title("MT5 Adaptive Trading Bot v1.0")
    root.geometry("1200x800")
    
    print("[TEST] Inicializando bot...")
    app = MT5AdaptiveTradingBot(root)
    
    print("[TEST] ✅ Bot inicializado exitosamente")
    print("[TEST] Ejecutando mainloop...")
    root.mainloop()
    
except Exception as e:
    print(f"\n❌ ERROR CAPTURADO: {type(e).__name__}")
    print(f"Mensaje: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()
    sys.exit(1)
