#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⭐ Test script para verificar si el bot abre operaciones correctamente.
Ejecuta el bot en modo directo sin GUI para ver logs de consola.
"""

import sys
import os
import time

# Agregar el path al workspace
sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def main():
    print("="*80)
    print("INICIANDO TEST DEL BOT - Verificar apertura de operaciones")
    print("="*80)
    print()
    
    # Importar el bot - esto iniciará logging a consola
    from boteddver1 import MT5AdaptiveTradingBot
    import threading
    
    print("[TEST] Creando instancia del bot...")
    try:
        bot = MT5AdaptiveTradingBot()
        print("[✓] Bot creado exitosamente")
    except Exception as e:
        print(f"[ERROR] Fallo al crear bot: {e}")
        return
    
    print("[TEST] Iniciando bot en thread separado...")
    try:
        # Iniciar el root en thread separado
        def run_bot():
            try:
                bot.root.mainloop()
            except Exception as e:
                print(f"[ERROR] En mainloop: {e}")
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Esperar a que el bot se inicialice
        print("[TEST] Esperando inicialización del bot (5 segundos)...")
        time.sleep(5)
        
        # Verificar estado
        print()
        print("[TEST] Estado del bot después de 5 segundos:")
        print(f"  - is_running: {bot.is_running}")
        print(f"  - total_operaciones_abiertas: {bot.total_operaciones_abiertas}")
        print(f"  - Symbol config: {bot._get_symbol()}")
        print(f"  - TRADE_INTERVAL: {bot.config['TRADE_INTERVAL'].get()}")
        print(f"  - MAX_SIMULTANEOUS_OPS: {bot.config['MAX_SIMULTANEOUS_OPS'].get()}")
        print()
        
        # Esperar más tiempo observando el bot
        print("[TEST] Observando bot durante 15 segundos más...")
        for i in range(15):
            time.sleep(1)
            ops = bot.total_operaciones_abiertas
            if ops > 0:
                print(f"[✓] [{i+1}s] ¡OPERACIÓN ABIERTA! Total: {ops}")
            else:
                print(f"[  ] [{i+1}s] Sin operaciones aún...")
        
        print()
        print("[TEST] Estadísticas finales:")
        print(f"  - Total operaciones ejecutadas: {getattr(bot, 'total_operaciones_ejecutadas', 'N/A')}")
        print(f"  - Operaciones abiertas ahora: {bot.total_operaciones_abiertas}")
        print(f"  - Última ganancia: {bot.ganancia_neta:.2f}")
        
    except Exception as e:
        print(f"[ERROR] Error en test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
