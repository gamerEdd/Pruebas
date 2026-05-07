#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bot sin GUI para verificar que no hay errores en la lógica"""

import sys
sys.path.insert(0, '.')

try:
    print("[STEP 1] Importando módulos...")
    from boteddver1 import MT5AdaptiveTradingBot
    import tkinter as tk
    print("[STEP 1] ✅ Módulos importados")
    
    print("[STEP 2] Creando ventana Tkinter...")
    root = tk.Tk()
    root.title("Test Bot")
    root.geometry("100x100")
    print("[STEP 2] ✅ Ventana creada")
    
    print("[STEP 3] Inicializando bot...")
    try:
        app = MT5AdaptiveTradingBot(root)
        print("[STEP 3] ✅ Bot inicializado")
    except Exception as e:
        print(f"[STEP 3] ❌ Error inicializando bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("[STEP 4] Ejecutando después_de 1s...")
    root.after(1000, lambda: root.quit())
    
    try:
        root.mainloop()
        print("[STEP 4] ✅ Mainloop completado")
    except Exception as e:
        print(f"[STEP 4] ❌ Error en mainloop: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ TODO OK - No hay errores")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
