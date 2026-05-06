#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST A DEBUG: GOLD SOLO - CON LOGS DETALLADOS
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
    log("TEST A DEBUG: GOLD SOLO - CON LOGS DETALLADOS")
    log("="*80)
    
    try:
        # Inicializar MT5
        if not mt5.initialize():
            log("[-] MT5 no inicializado")
            return 1
        
        log("[OK] MT5 inicializado")
        
        # Crear GUI y bot
        root = tk.Tk()
        root.withdraw()
        
        from boteddver1 import MT5AdaptiveTradingBot
        bot = MT5AdaptiveTradingBot(root)
        bot.is_running = True
        bot._scheduler_running = True
        
        time.sleep(2)
        log("[OK] Bot creado")
        
        # Capturar logs del bot
        bot_logs = []
        original_add_log = bot.add_log
        def capture_log(msg, tag='info'):
            bot_logs.append((msg, tag))
            return original_add_log(msg, tag)
        bot.add_log = capture_log
        
        # Configurar
        log("\n[*] Configurando: USE_MULTIPLE_PARTS=False, SYMBOL=GOLD")
        bot.config['USE_MULTIPLE_PARTS'].set(False)
        bot.config['SYMBOL'].set('GOLD')
        time.sleep(1)
        
        # Verificar
        tick = mt5.symbol_info_tick('GOLD')
        if not tick:
            log("[-] No hay tick para GOLD")
            return 1
        
        log(f"[OK] GOLD tick: ask={tick.ask:.5f}, bid={tick.bid:.5f}")
        
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
                    "comment": "CLOSE-TEST",
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
        log(f"[*] Resultado de abrir_operacion_smart(): {result}")
        
        time.sleep(2)
        
        # Mostrar logs capturados
        log(f"\n[BOT LOGS CAPTURADOS]")
        for msg, tag in bot_logs[-20:]:  # Últimos 20 logs
            log(f"  [{tag.upper()}] {msg}")
        
        # Verificar resultado
        positions = mt5.positions_get() or []
        gold_pos = [p for p in positions if p.symbol == 'GOLD']
        silver_pos = [p for p in positions if p.symbol == 'SILVER']
        
        log(f"\n[RESULTADO FINAL]")
        log(f"  GOLD: {len(gold_pos)} posición(es)")
        if len(gold_pos) == 1:
            p = gold_pos[0]
            log(f"    ✅ Ticket={p.ticket}, {'BUY' if p.type == mt5.POSITION_TYPE_BUY else 'SELL'}, Vol={p.volume}")
            return 0
        else:
            log(f"  ❌ FALLO: No se abrió GOLD")
            return 1
        
    except Exception as e:
        log(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
