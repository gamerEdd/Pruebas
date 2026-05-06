#!/usr/bin/env python3
"""
Script para envolver el bot y mostrar TODOS los errores en consola
"""
import sys
import traceback

# Redirigir stderr para que NO se pierda nada
original_stderr = sys.stderr

class ErrorCapture:
    def __init__(self):
        self.lines = []
    
    def write(self, msg):
        if msg and msg.strip():
            print(f"[STDERR] {msg.rstrip()}", file=original_stderr)
        original_stderr.write(msg)
    
    def flush(self):
        original_stderr.flush()

# Aplicar captura
sys.stderr = ErrorCapture()

# Ahora importar y ejecutar el bot
try:
    from boteddver1 import MT5AdaptiveTradingBot
    import tkinter as tk
    
    root = tk.Tk()
    bot = MT5AdaptiveTradingBot(root)
    root.mainloop()
except Exception as e:
    print("\n" + "="*70, file=sys.stderr)
    print("FATAL ERROR EN BOT", file=sys.stderr)
    print("="*70, file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print("="*70, file=sys.stderr)
    sys.exit(1)
