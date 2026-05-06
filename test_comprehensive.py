#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Apertura - GOLD, SILVER y AMBOS con USE_MULTIPLE_PARTS
"""

import sys
import time
import tkinter as tk
import MetaTrader5 as mt5

sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def close_all_positions():
    """Cierra todas las posiciones abiertas"""
    positions = mt5.positions_get() or []
    for pos in positions:
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": pos.ticket,
            "price": mt5.symbol_info_tick(pos.symbol).ask if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).bid,
            "deviation": 20,
            "magic": 123456,
            "comment": "CLOSE-TEST",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(close_request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  [+] Cerrado: {pos.symbol} ticket={pos.ticket}")
        else:
            print(f"  [-] Error cerrando {pos.symbol}: {result.retcode if result else 'None'}")
    time.sleep(1)

def test_single_symbol(bot, symbol, name):
    """Test para un único símbolo"""
    print("\n" + "="*80)
    print(f"TEST: {name}")
    print("="*80)
    
    # Desactivar múltiples pares
    bot.config['USE_MULTIPLE_PARTS'].set(False)
    bot.config['SYMBOL'].set(symbol)
    
    # Verificar datos
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"[-] No hay tick para {symbol}")
        return False
    
    print(f"[+] {symbol} tick: ask={tick.ask:.5f}, bid={tick.bid:.5f}")
    
    # Intentar abrir BUY
    print(f"[*] Abriendo BUY en {symbol}...")
    result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
    
    time.sleep(1)
    
    # Verificar posiciones
    positions = mt5.positions_get() or []
    symbol_positions = [p for p in positions if p.symbol == symbol]
    
    if len(symbol_positions) > 0:
        print(f"[OK] {name} abierto: {len(symbol_positions)} posición(es)")
        for pos in symbol_positions:
            print(f"     Ticket: {pos.ticket}, Type: {pos.type}, Vol: {pos.volume}")
        return True
    else:
        print(f"[-] {name} NO abierto")
        return False

def test_multiple_parts(bot):
    """Test para múltiples pares simultáneamente"""
    print("\n" + "="*80)
    print("TEST: GOLD + SILVER (USE_MULTIPLE_PARTS=True)")
    print("="*80)
    
    # Activar múltiples pares
    bot.config['USE_MULTIPLE_PARTS'].set(True)
    bot.config['SYMBOL'].set('GOLD')  # Símbolo base (se ignorará en modo múltiple)
    
    print("[*] Abriendo GOLD + SILVER simultáneamente con análisis independiente...")
    result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
    
    time.sleep(1)
    
    # Verificar posiciones
    positions = mt5.positions_get() or []
    gold_positions = [p for p in positions if p.symbol == 'GOLD']
    silver_positions = [p for p in positions if p.symbol == 'SILVER']
    
    print(f"\n[RESULTADO]")
    print(f"  GOLD: {len(gold_positions)} posición(es)", end="")
    if len(gold_positions) > 0:
        for pos in gold_positions:
            print(f"\n    - Ticket: {pos.ticket}, Type: {pos.type}, Vol: {pos.volume}", end="")
        print()
    else:
        print()
    
    print(f"  SILVER: {len(silver_positions)} posición(es)", end="")
    if len(silver_positions) > 0:
        for pos in silver_positions:
            print(f"\n    - Ticket: {pos.ticket}, Type: {pos.type}, Vol: {pos.volume}", end="")
        print()
    else:
        print()
    
    if len(gold_positions) > 0 and len(silver_positions) > 0:
        print(f"\n[OK] Ambos pares abiertos simultáneamente!")
        return True
    else:
        print(f"\n[-] No se abrieron ambos pares")
        return False

def main():
    print("\n" + "="*80)
    print("TEST COMPREHENSIVE - GOLD, SILVER y MULTIPLES PARES")
    print("="*80)
    
    try:
        # Inicializar MT5
        if not mt5.initialize():
            print("[-] MT5 no inicializado")
            return
        
        print("[OK] MT5 inicializado")
        
        # Crear bot
        print("[*] Creando bot...")
        root = tk.Tk()
        root.withdraw()
        
        from boteddver1 import MT5AdaptiveTradingBot
        bot = MT5AdaptiveTradingBot(root)
        bot.is_running = True
        bot._scheduler_running = True
        bot.force_stop_triggered = False
        
        time.sleep(2)
        print("[OK] Bot creado")
        
        # Test 1: GOLD solo
        close_all_positions()
        test1 = test_single_symbol(bot, 'GOLD', 'GOLD')
        
        # Test 2: SILVER solo
        close_all_positions()
        test2 = test_single_symbol(bot, 'SILVER', 'SILVER')
        
        # Test 3: GOLD + SILVER juntos
        close_all_positions()
        test3 = test_multiple_parts(bot)
        
        # Resumen
        print("\n" + "="*80)
        print("RESUMEN FINAL")
        print("="*80)
        print(f"GOLD solo:              {'PASS' if test1 else 'FAIL'}")
        print(f"SILVER solo:            {'PASS' if test2 else 'FAIL'}")
        print(f"GOLD + SILVER juntos:   {'PASS' if test3 else 'FAIL'}")
        
        if test1 and test2 and test3:
            print(f"\n[SUCCESS] Todos los tests pasaron!")
        else:
            print(f"\n[WARNING] Algunos tests fallaron")
        
        print("="*80 + "\n")
        
        # Cleanup
        close_all_positions()
        root.destroy()
        mt5.shutdown()
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
