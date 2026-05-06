#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST C DEBUG: GOLD + SILVER con logs detallados
"""

import sys
import time
import tkinter as tk
import MetaTrader5 as mt5

sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def log(msg):
    """Log safe"""
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

def main():
    log("\n" + "="*80)
    log("TEST C DEBUG: GOLD + SILVER SIMULTÁNEOS")
    log("="*80)
    
    try:
        if not mt5.initialize():
            log("[-] MT5 no inicializado")
            return 1
        
        log("[OK] MT5 inicializado")
        
        root = tk.Tk()
        root.withdraw()
        
        from boteddver1 import MT5AdaptiveTradingBot
        bot = MT5AdaptiveTradingBot(root)
        bot.is_running = True
        bot._scheduler_running = True
        
        time.sleep(2)
        log("[OK] Bot creado")
        
        # Capturar logs
        bot_logs = []
        original_add_log = bot.add_log
        def capture_log(msg, tag='info'):
            bot_logs.append((msg, tag))
            return original_add_log(msg, tag)
        bot.add_log = capture_log
        
        # Configurar múltiples pares
        log("\n[*] Configurando: USE_MULTIPLE_PARTS=True")
        bot.config['USE_MULTIPLE_PARTS'].set(True)
        bot.config['SYMBOL'].set('GOLD')
        time.sleep(1)
        
        # Cerrar previas
        positions = mt5.positions_get() or []
        for pos in positions:
            try:
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "position": pos.ticket,
                    "price": mt5.symbol_info_tick(pos.symbol).ask if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).bid,
                    "deviation": 20,
                    "magic": 123456,
                    "comment": "CLOSE",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                mt5.order_send(close_request)
            except:
                pass
        time.sleep(1)
        
        # Abrir
        log("\n[*] Llamando: bot.abrir_operacion_smart('BUY', force=True, startup=True)")
        result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
        log(f"[*] Resultado: {result}")
        
        time.sleep(2)
        
        # Mostrar logs
        log(f"\n[BOT LOGS - ÚLTIMOS 40]")
        for msg, tag in bot_logs[-40:]:
            log(f"  [{tag.upper():8}] {msg}")
        
        # Resultado
        positions = mt5.positions_get() or []
        gold_count = len([p for p in positions if p.symbol == 'GOLD'])
        silver_count = len([p for p in positions if p.symbol == 'SILVER'])
        
        log(f"\n[RESULTADO]")
        log(f"  GOLD: {gold_count} posiciones")
        log(f"  SILVER: {silver_count} posiciones")
        
        if gold_count >= 1 and silver_count >= 1:
            log(f"  ✅ TEST C PASADO")
            return 0
        else:
            log(f"  ❌ TEST C FALLO")
            return 1
        
    except Exception as e:
        log(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
