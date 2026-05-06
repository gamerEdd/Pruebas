#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✅ Test Simple de Apertura - GOLD y SILVER
Bypasses validaciones complejas para confirmar que la apertura funciona
"""

import sys
import os
import time
import tkinter as tk

sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def main():
    print("\n" + "="*80)
    print("TEST SIMPLE DE APERTURA - Confirmando que GOLD y SILVER abren")
    print("="*80 + "\n")
    
    try:
        print("[1] Creando Tkinter...")
        root = tk.Tk()
        root.withdraw()
        
        print("[2] Importando bot...")
        from boteddver1 import MT5AdaptiveTradingBot
        import MetaTrader5 as mt5
        
        print("[3] Instanciando bot...")
        bot = MT5AdaptiveTradingBot(root)
        time.sleep(2)
        
        # ⭐ IMPORTANTE: Establecer bot como "running" para que las validaciones lo permitan
        bot.is_running = True
        bot._scheduler_running = True
        bot.force_stop_triggered = False
        
        # Verificar MT5
        if not mt5.initialize():
            print("❌ MT5 no inicializado")
            return
        
        print(f"✅ MT5 listo\n")
        
        # Test GOLD
        print("="*80)
        print("PRUEBA 1: GOLD (startup=True)")
        print("="*80)
        
        bot.config['SYMBOL'].set('GOLD')
        
        # Ver si MT5 tiene datos
        tick_gold = mt5.symbol_info_tick('GOLD')
        if tick_gold:
            print(f"✅ MT5 GOLD tick: ask={tick_gold.ask:.2f}, bid={tick_gold.bid:.2f}")
            
            # Intentar abrir BUY con startup=True (omite is_running check)
            print(f"Abriendo BUY en GOLD (startup=True)...")
            result = bot.abrir_operacion('BUY', force=True, startup=True)
            
            if result:
                print(f"✅ GOLD BUY ABIERTO!")
                print(f"   Total operaciones: {bot.total_operaciones_abiertas}")
            else:
                print(f"❌ GOLD BUY RECHAZADO (probando SELL...)")
                result_sell = bot.abrir_operacion('SELL', force=True, startup=True)
                if result_sell:
                    print(f"✅ GOLD SELL ABIERTO!")
                    print(f"   Total operaciones: {bot.total_operaciones_abiertas}")
                else:
                    print(f"❌ GOLD SELL TAMBIÉN RECHAZADO")
        else:
            print(f"❌ MT5 GOLD tick unavailable")
        
        time.sleep(1)
        
        # Test SILVER
        print("\n" + "="*80)
        print("PRUEBA 2: SILVER (startup=True)")
        print("="*80)
        
        bot.config['SYMBOL'].set('SILVER')
        
        tick_silver = mt5.symbol_info_tick('SILVER')
        if tick_silver:
            print(f"✅ MT5 SILVER tick: ask={tick_silver.ask:.2f}, bid={tick_silver.bid:.2f}")
            
            print(f"Abriendo BUY en SILVER (startup=True)...")
            result = bot.abrir_operacion('BUY', force=True, startup=True)
            
            if result:
                print(f"✅ SILVER BUY ABIERTO!")
                print(f"   Total operaciones: {bot.total_operaciones_abiertas}")
            else:
                print(f"❌ SILVER BUY RECHAZADO (probando SELL...)")
                result_sell = bot.abrir_operacion('SELL', force=True, startup=True)
                if result_sell:
                    print(f"✅ SILVER SELL ABIERTO!")
                    print(f"   Total operaciones: {bot.total_operaciones_abiertas}")
                else:
                    print(f"❌ SILVER SELL TAMBIÉN RECHAZADO")
        else:
            print(f"❌ MT5 SILVER tick unavailable")
        
        print("\n" + "="*80)
        print(f"RESUMEN FINAL: {bot.total_operaciones_abiertas} operación(es) abierta(s) exitosamente")
        if bot.total_operaciones_abiertas > 0:
            print("✅ PRUEBA EXITOSA - GOLD/SILVER pueden abrir operaciones")
        else:
            print("❌ PRUEBA FALLIDA - Las operaciones fueron rechazadas")
        print("="*80 + "\n")
        
        root.destroy()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

