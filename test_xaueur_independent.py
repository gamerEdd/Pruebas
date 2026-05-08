#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST: GOLD y XAUEUR CON ANÁLISIS INDEPENDIENTE
✅ Prueba 1: Abre GOLD solo (USE_MULTIPLE_PARTS=False)
✅ Prueba 2: Abre XAUEUR solo (USE_MULTIPLE_PARTS=False)
✅ Prueba 3: Abre GOLD + XAUEUR simultáneamente (USE_MULTIPLE_PARTS=True)
             → Cada par tiene su propio análisis independiente
             → Pueden abrir en direcciones DIFERENTES
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

def clean_positions(symbols=None):
    """Cierra todas las posiciones de los símbolos especificados"""
    if symbols is None:
        symbols = ['GOLD', 'XAUEUR']
    
    positions = mt5.positions_get() or []
    closed = 0
    
    for pos in positions:
        if pos.symbol in symbols:
            tick = mt5.symbol_info_tick(pos.symbol)
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": pos.ticket,
                "price": tick.ask if pos.type == mt5.POSITION_TYPE_BUY else tick.bid,
                "deviation": 20,
                "magic": 123456,
                "comment": "CLOSE-TEST",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(close_request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                log(f"  [+] Cerrado: {pos.symbol} ticket={pos.ticket}")
                closed += 1
            time.sleep(0.2)
    
    time.sleep(1)
    return closed

def test_gold_only(bot):
    """✅ Prueba 1: Abrir solo GOLD (análisis independiente)"""
    log("\n" + "="*80)
    log("PRUEBA 1: GOLD SOLO (USE_MULTIPLE_PARTS=False)")
    log("="*80)
    
    # Configurar
    bot.config['USE_MULTIPLE_PARTS'].set(False)
    bot.config['SYMBOL'].set('GOLD')
    time.sleep(0.5)
    
    # Limpiar previas
    log("[*] Limpiando posiciones previas...")
    clean_positions(['GOLD'])
    
    # Verificar datos
    tick = mt5.symbol_info_tick('GOLD')
    if not tick:
        log("[-] ERROR: No hay tick para GOLD")
        return False
    
    log(f"[OK] GOLD: bid={tick.bid:.2f}, ask={tick.ask:.2f}")
    
    # Abrir
    log("[*] Abriendo operación en GOLD con análisis independiente...")
    result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
    
    time.sleep(2)
    
    # Verificar
    positions = mt5.positions_get() or []
    gold_positions = [p for p in positions if p.symbol == 'GOLD']
    
    if gold_positions:
        pos = gold_positions[0]
        log(f"[✅ ÉXITO] GOLD abierto: ticket={pos.ticket}, tipo={('BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL')}, vol={pos.volume}")
        return True
    else:
        log("[-] ERROR: GOLD no se abrió")
        return False

def test_xaueur_only(bot):
    """✅ Prueba 2: Abrir solo XAUEUR (análisis independiente)"""
    log("\n" + "="*80)
    log("PRUEBA 2: XAUEUR SOLO (USE_MULTIPLE_PARTS=False)")
    log("="*80)
    
    # Configurar
    bot.config['USE_MULTIPLE_PARTS'].set(False)
    bot.config['SYMBOL'].set('XAUEUR')
    time.sleep(0.5)
    
    # Limpiar previas
    log("[*] Limpiando posiciones previas...")
    clean_positions(['XAUEUR'])
    
    # Verificar datos
    tick = mt5.symbol_info_tick('XAUEUR')
    if not tick:
        log("[-] ERROR: No hay tick para XAUEUR")
        return False
    
    log(f"[OK] XAUEUR: bid={tick.bid:.2f}, ask={tick.ask:.2f}")
    
    # Abrir
    log("[*] Abriendo operación en XAUEUR con análisis independiente...")
    result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
    
    time.sleep(2)
    
    # Verificar
    positions = mt5.positions_get() or []
    xaueur_positions = [p for p in positions if p.symbol == 'XAUEUR']
    
    if xaueur_positions:
        pos = xaueur_positions[0]
        log(f"[✅ ÉXITO] XAUEUR abierto: ticket={pos.ticket}, tipo={('BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL')}, vol={pos.volume}")
        return True
    else:
        log("[-] ERROR: XAUEUR no se abrió")
        return False

def test_both_pairs(bot):
    """✅ Prueba 3: Abrir GOLD + XAUEUR simultáneamente (análisis INDEPENDIENTE)"""
    log("\n" + "="*80)
    log("PRUEBA 3: GOLD + XAUEUR SIMULTÁNEAMENTE (USE_MULTIPLE_PARTS=True)")
    log("="*80)
    log("[*] Cada par será analizado INDEPENDIENTEMENTE")
    log("[*] Pueden abrir en direcciones DIFERENTES (BUY/SELL)")
    log("="*80)
    
    # Configurar
    bot.config['USE_MULTIPLE_PARTS'].set(True)
    time.sleep(0.5)
    
    # Limpiar previas
    log("[*] Limpiando posiciones previas...")
    clean_positions(['GOLD', 'XAUEUR'])
    
    # Verificar datos
    tick_gold = mt5.symbol_info_tick('GOLD')
    tick_xaueur = mt5.symbol_info_tick('XAUEUR')
    
    if not tick_gold or not tick_xaueur:
        log("[-] ERROR: No hay ticks para GOLD y/o XAUEUR")
        return False
    
    log(f"[OK] GOLD:   bid={tick_gold.bid:.2f}, ask={tick_gold.ask:.2f}")
    log(f"[OK] XAUEUR: bid={tick_xaueur.bid:.2f}, ask={tick_xaueur.ask:.2f}")
    
    # Abrir ambos
    log("[*] Abriendo GOLD y XAUEUR con análisis INDEPENDIENTE...")
    result = bot.abrir_operacion_smart('BUY', force=True, startup=True)
    
    time.sleep(2)
    
    # Verificar
    positions = mt5.positions_get() or []
    gold_positions = [p for p in positions if p.symbol == 'GOLD']
    xaueur_positions = [p for p in positions if p.symbol == 'XAUEUR']
    
    success = True
    
    if gold_positions:
        pos = gold_positions[0]
        gold_type = 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
        log(f"[✅] GOLD abierto: ticket={pos.ticket}, tipo={gold_type}, vol={pos.volume}")
    else:
        log("[-] GOLD no se abrió")
        success = False
    
    if xaueur_positions:
        pos = xaueur_positions[0]
        xaueur_type = 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
        log(f"[✅] XAUEUR abierto: ticket={pos.ticket}, tipo={xaueur_type}, vol={pos.volume}")
        
        # Verificar independencia
        if gold_positions and (gold_type != xaueur_type):
            log(f"[🎯 INDEPENDENCIA CONFIRMADA] GOLD={gold_type} ≠ XAUEUR={xaueur_type}")
        elif gold_positions and (gold_type == xaueur_type):
            log(f"[ℹ️  INFO] GOLD={gold_type} = XAUEUR={xaueur_type} (misma dirección en este caso)")
    else:
        log("[-] XAUEUR no se abrió")
        success = False
    
    if success:
        log("\n[✅ ÉXITO] Ambos pares abiertos simultáneamente con análisis INDEPENDIENTE")
    else:
        log("\n[-] ERROR: No se abrieron ambos pares")
    
    return success

def main():
    log("\n" + "="*100)
    log("TEST: GOLD y XAUEUR CON ANÁLISIS INDEPENDIENTE")
    log("="*100)
    
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
        
        # Ejecutar pruebas
        results = {}
        
        results['GOLD_SOLO'] = test_gold_only(bot)
        time.sleep(2)
        
        results['XAUEUR_SOLO'] = test_xaueur_only(bot)
        time.sleep(2)
        
        results['AMBOS_SIMULTANEOS'] = test_both_pairs(bot)
        time.sleep(2)
        
        # Resumen
        log("\n" + "="*100)
        log("RESUMEN DE PRUEBAS")
        log("="*100)
        log(f"✅ GOLD SOLO (USE_MULTIPLE_PARTS=False):      {'PASS ✅' if results['GOLD_SOLO'] else 'FAIL ❌'}")
        log(f"✅ XAUEUR SOLO (USE_MULTIPLE_PARTS=False):    {'PASS ✅' if results['XAUEUR_SOLO'] else 'FAIL ❌'}")
        log(f"✅ AMBOS SIMULTÁNEOS (USE_MULTIPLE_PARTS=True): {'PASS ✅' if results['AMBOS_SIMULTANEOS'] else 'FAIL ❌'}")
        
        total_pass = sum(1 for v in results.values() if v)
        log(f"\n📊 Total: {total_pass}/3 pruebas pasaron")
        log("="*100)
        
        # Limpiar
        clean_positions(['GOLD', 'XAUEUR'])
        
        bot.is_running = False
        root.quit()
        root.destroy()
        mt5.shutdown()
        
        return 0 if total_pass == 3 else 1
        
    except Exception as e:
        log(f"[-] EXCEPCIÓN: {str(e)}")
        import traceback
        log(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
