#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST C: GOLD + SILVER SIMULTÁNEOS
Prueba abrir operaciones en ambos pares simultáneamente con USE_MULTIPLE_PARTS=True
Cada símbolo se analiza independientemente y se determina su propia dirección óptima
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
    log("TEST C: GOLD + SILVER SIMULTÁNEOS (USE_MULTIPLE_PARTS=True)")
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
        
        # Configurar para múltiples pares
        log("\n[*] Configurando: USE_MULTIPLE_PARTS=True (análisis independiente de GOLD + SILVER)")
        bot.config['USE_MULTIPLE_PARTS'].set(True)
        bot.config['SYMBOL'].set('GOLD')  # Base symbol (será ignorado en modo múltiple)
        time.sleep(1)
        
        # Verificar ticks
        tick_gold = mt5.symbol_info_tick('GOLD')
        tick_silver = mt5.symbol_info_tick('SILVER')
        
        if not tick_gold or not tick_silver:
            log("[-] No hay ticks para GOLD y/o SILVER")
            return 1
        
        log(f"[OK] GOLD tick: ask={tick_gold.ask:.5f}, bid={tick_gold.bid:.5f}")
        log(f"[OK] SILVER tick: ask={tick_silver.ask:.5f}, bid={tick_silver.bid:.5f}")
        
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
                "comment": "CLOSE-TEST-C",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(close_request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                log(f"  [+] Cerrado: {pos.symbol} ticket={pos.ticket}")
        
        time.sleep(1)
        
        # Abrir operación con análisis independiente
        log("\n[*] Llamando: bot.abrir_operacion_smart('BUY', force=True, startup=True)")
        log("[*] En modo USE_MULTIPLE_PARTS=True, se analizará:")
        log("    - GOLD independientemente (determinará BUY o SELL)")
        log("    - SILVER independientemente (determinará BUY o SELL)")
        result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
        
        time.sleep(2)
        
        # Verificar resultado
        positions = mt5.positions_get() or []
        gold_positions = [p for p in positions if p.symbol == 'GOLD']
        silver_positions = [p for p in positions if p.symbol == 'SILVER']
        
        log(f"\n[RESULTADO]")
        
        log(f"\n  GOLD: {len(gold_positions)} posición(es)")
        if len(gold_positions) > 0:
            for pos in gold_positions:
                direction = 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
                log(f"    ✅ Abierto: Ticket={pos.ticket}, {direction}, Vol={pos.volume}, Entry={pos.price_open:.5f}")
                if pos.sl > 0:
                    log(f"       SL={pos.sl:.5f}, TP={pos.tp:.5f}" if pos.tp > 0 else f"       SL={pos.sl:.5f}")
        else:
            log(f"    ❌ No abierto")
        
        log(f"\n  SILVER: {len(silver_positions)} posición(es)")
        if len(silver_positions) > 0:
            for pos in silver_positions:
                direction = 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
                log(f"    ✅ Abierto: Ticket={pos.ticket}, {direction}, Vol={pos.volume}, Entry={pos.price_open:.5f}")
                if pos.sl > 0:
                    log(f"       SL={pos.sl:.5f}, TP={pos.tp:.5f}" if pos.tp > 0 else f"       SL={pos.sl:.5f}")
        else:
            log(f"    ❌ No abierto")
        
        log(f"\n[RESULTADO FINAL]")
        if len(gold_positions) == 1 and len(silver_positions) == 1:
            log("  ✅ TEST C PASADO: Ambos pares abiertos simultáneamente")
            root.destroy()
            mt5.shutdown()
            return 0
        elif len(gold_positions) > 0 or len(silver_positions) > 0:
            log(f"  ⚠️  TEST C PARCIAL: Solo {len(gold_positions) + len(silver_positions)} de 2 pares abiertos")
            root.destroy()
            mt5.shutdown()
            return 1
        else:
            log(f"  ❌ TEST C FALLIDO: Ningún par abierto")
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
