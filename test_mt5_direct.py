#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Directo MT5 - Verificar si operaciones se abren realmente
"""

import sys
import time
import tkinter as tk
import MetaTrader5 as mt5

sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def main():
    print("\n" + "="*80)
    print("TEST DIRECTO MT5 - Verificar operaciones")
    print("="*80 + "\n")
    
    try:
        # Init MT5
        if not mt5.initialize():
            print("[!] MT5 no inicializado")
            return
        
        print("[OK] MT5 inicializado\n")
        
        # Get magic number
        MAGIC_NUMBER = 123456
        
        # Crear Tk y bot
        print("[1] Creando bot...")
        root = tk.Tk()
        root.withdraw()
        
        from boteddver1 import MT5AdaptiveTradingBot
        bot = MT5AdaptiveTradingBot(root)
        bot.is_running = True
        bot._scheduler_running = True
        bot.force_stop_triggered = False
        bot.config['MAGIC_NUMBER'] = MAGIC_NUMBER
        
        time.sleep(2)
        print("[OK] Bot creado\n")
        
        # Verificar posiciones iniciales
        print("[2] Posiciones actuales en MT5:")
        positions_before = mt5.positions_get() or []
        for pos in positions_before:
            print("    - {}: {} vol={}".format(pos.symbol, pos.type, pos.volume))
        print("    Total: {} posiciones\n".format(len(positions_before)))
        
        # Intentar abrir en GOLD
        print("[3] Abriendo operacion en GOLD...")
        bot.config['SYMBOL'].set('GOLD')
        result_gold = bot.abrir_operacion('BUY', force=True, startup=True)
        print("    Resultado: {}".format(result_gold))
        time.sleep(1)
        
        # Verificar posiciones después de GOLD
        print("\n[4] Posiciones después de intento GOLD:")
        positions_after_gold = mt5.positions_get() or []
        gold_positions = [p for p in positions_after_gold if p.symbol == 'GOLD']
        for pos in gold_positions:
            print("    [+] GOLD {} vol={} entry={}".format(pos.type, pos.volume, pos.price_open))
        if not gold_positions:
            print("    [-] No hay posiciones GOLD")
        print("    Total: {} posiciones\n".format(len(positions_after_gold)))
        
        # Intentar abrir en SILVER
        print("[5] Abriendo operacion en SILVER...")
        bot.config['SYMBOL'].set('SILVER')
        result_silver = bot.abrir_operacion('BUY', force=True, startup=True)
        print("    Resultado: {}".format(result_silver))
        time.sleep(1)
        
        # Verificar posiciones finales
        print("\n[6] Posiciones finales:")
        positions_final = mt5.positions_get() or []
        gold_final = [p for p in positions_final if p.symbol == 'GOLD']
        silver_final = [p for p in positions_final if p.symbol == 'SILVER']
        
        print("    GOLD: {} posicion(es)".format(len(gold_final)))
        for pos in gold_final:
            print("      - Ticket: {}, Type: {}, Vol: {}".format(pos.ticket, pos.type, pos.volume))
        
        print("    SILVER: {} posicion(es)".format(len(silver_final)))
        for pos in silver_final:
            print("      - Ticket: {}, Type: {}, Vol: {}".format(pos.ticket, pos.type, pos.volume))
        
        print("    Total: {} posiciones\n".format(len(positions_final)))
        
        # Resumen
        print("="*80)
        if len(gold_final) > 0 or len(silver_final) > 0:
            print("[SUCCESS] Operaciones abiertas:")
            if len(gold_final) > 0:
                print("   - GOLD: {} posicion(es)".format(len(gold_final)))
            if len(silver_final) > 0:
                print("   - SILVER: {} posicion(es)".format(len(silver_final)))
        else:
            print("[FAIL] No se abrieron operaciones")
        print("="*80 + "\n")
        
        root.destroy()
        mt5.shutdown()
        
    except Exception as e:
        print("[ERROR] {}".format(e))
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
