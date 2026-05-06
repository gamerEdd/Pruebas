#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST B: SILVER SOLO
Prueba abrir una operación únicamente en SILVER con USE_MULTIPLE_PARTS=False
"""

import sys
import time
import tkinter as tk
import MetaTrader5 as mt5

sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def log(msg):
    """Log safe - usa stderr para evitar problemas de stdout cerrado"""
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

def main():
    log("\n" + "="*80)
    log("TEST B: SILVER SOLO")
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
        
        # Configurar para SILVER solo
        log("\n[*] Configurando: USE_MULTIPLE_PARTS=False, SYMBOL=SILVER")
        bot.config['USE_MULTIPLE_PARTS'].set(False)
        bot.config['SYMBOL'].set('SILVER')
        time.sleep(1)
        
        # Verificar tick
        tick = mt5.symbol_info_tick('SILVER')
        if not tick:
            log("[-] No hay tick para SILVER")
            return 1
        
        log(f"[OK] SILVER tick: ask={tick.ask:.5f}, bid={tick.bid:.5f}")
        
        # Cerrar posiciones previas
        positions = mt5.positions_get() or []
        gold_positions = [p for p in positions if p.symbol == 'GOLD']
        silver_positions = [p for p in positions if p.symbol == 'SILVER']
        
        log(f"[*] Cerrar previas: GOLD({len(gold_positions)}), SILVER({len(silver_positions)})")
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
                "comment": "CLOSE-TEST-B",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(close_request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                log(f"  [+] Cerrado: {pos.symbol} ticket={pos.ticket}")
        
        time.sleep(1)
        
        # Abrir operación en SILVER
        log("\n[*] Llamando: bot.abrir_operacion_smart('BUY', force=True, startup=True)")
        result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
        
        time.sleep(2)
        
        # Verificar resultado
        positions = mt5.positions_get() or []
        gold_positions = [p for p in positions if p.symbol == 'GOLD']
        silver_positions = [p for p in positions if p.symbol == 'SILVER']
        
        log(f"\n[RESULTADO]")
        log(f"  GOLD: {len(gold_positions)} posición(es)")
        if len(gold_positions) > 0:
            log("    ❌ ERROR: Se abrió GOLD pero no debería")
        
        log(f"  SILVER: {len(silver_positions)} posición(es)")
        for pos in silver_positions:
            log(f"    - Ticket: {pos.ticket}")
            log(f"    - Type: {'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'}")
            log(f"    - Volume: {pos.volume}")
            log(f"    - Entry: {pos.price_open:.5f}")
            if pos.sl > 0:
                log(f"    - SL: {pos.sl:.5f}")
            if pos.tp > 0:
                log(f"    - TP: {pos.tp:.5f}")
        
        log(f"\n[RESULTADO FINAL]")
        if len(silver_positions) == 1 and len(gold_positions) == 0:
            log("  ✅ TEST B PASADO: Solo SILVER abierto")
            root.destroy()
            mt5.shutdown()
            return 0
        else:
            log(f"  ❌ TEST B FALLIDO: GOLD={len(gold_positions)}, SILVER={len(silver_positions)}")
            root.destroy()
            mt5.shutdown()
            return 1
        
    except Exception as e:
        log(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
