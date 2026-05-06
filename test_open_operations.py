#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⭐ Test de Apertura de Operaciones - Prueba GOLD y SILVER
"""

import sys
import os
import time
import tkinter as tk

# Setup path
sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

def test_symbol_operations(bot, symbol):
    """Prueba apertura de operaciones para un símbolo específico"""
    print(f"\n{'='*80}")
    print(f"PRUEBA: {symbol}")
    print(f"{'='*80}\n")
    
    try:
        # 1. Verificar datos JSON cargados
        print(f"[1/4] Verificando snapshots JSON para {symbol}...")
        from trade_logger import read_market_snapshots
        snapshots = read_market_snapshots(symbol)
        if snapshots and len(snapshots) > 0:
            print(f"  ✅ {len(snapshots)} snapshots cargados para {symbol}")
            # Mostrar último snapshot
            last = snapshots[-1]
            print(f"     Último: close={last.get('close', 0):.2f}, time={last.get('time', 'N/A')}")
        else:
            print(f"  ❌ No hay snapshots para {symbol}")
            return False
        
        # 2. Análisis pre-apertura
        print(f"\n[2/4] Ejecutando análisis dual para {symbol}...")
        try:
            # Temporalmente cambiar símbolo
            original_symbol = bot._get_symbol()
            bot.config['SYMBOL'].set(symbol)
            
            analysis = bot._dual_analysis_before_opening(symbol)
            if analysis:
                print(f"  ✅ Análisis completado para {symbol}")
                print(f"     Recomendación: {analysis.get('recommendation', 'HOLD')}")
                buy_score = analysis.get('buy_specialist', {}).get('score', 0)
                sell_score = analysis.get('sell_specialist', {}).get('score', 0)
                print(f"     Buy Score: {buy_score:.3f}")
                print(f"     Sell Score: {sell_score:.3f}")
            else:
                print(f"  ⚠️  Análisis retornó None para {symbol}")
        except Exception as e:
            print(f"  ❌ Error en análisis: {str(e)[:80]}")
            import traceback
            traceback.print_exc()
            return False
        
        # 3. Obtener precio actual
        print(f"\n[3/4] Obteniendo precio actual para {symbol}...")
        try:
            tick = bot.get_fresh_market_data(symbol, bars=1)
            if tick and len(tick) > 0:
                last_rate = tick[-1]
                price = last_rate.get('close', 0)
                print(f"  ✅ Precio obtenido para {symbol}: {price:.5f}")
            else:
                print(f"  ⚠️  No hay datos de precio para {symbol}")
        except Exception as e:
            print(f"  ❌ Error obteniendo precio: {str(e)[:80]}")
        
        # 4. Intentar abrir operación
        print(f"\n[4/4] Intentando abrir operación BUY en {symbol}...")
        try:
            # Asegurar que el símbolo es correcto
            bot.config['SYMBOL'].set(symbol)
            
            # Intercept the operation opening by monitoring logs
            import MetaTrader5 as mt5
            if mt5.initialize():
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"  ℹ️  MT5 Tick disponible: ask={tick.ask}, bid={tick.bid}")
                else:
                    print(f"  ⚠️  MT5 Tick retornó None para {symbol}")
            
            result = bot.abrir_operacion('BUY', force=True, startup=True)
            if result:
                print(f"  ✅ Operación abierta exitosamente en {symbol}")
                ops = bot.operaciones_activas
                if ops and len(ops) > 0:
                    last_op = list(ops.values())[0]
                    print(f"     ID: {last_op.get('ticket', 'N/A')}")
                    print(f"     Symbol: {last_op.get('symbol', 'N/A')}")
                    print(f"     Entry: {last_op.get('entry_price', 0):.5f}")
                    print(f"     Volume: {last_op.get('volume', 0)}")
                print(f"  Total operaciones activas: {bot.total_operaciones_abiertas}")
                return True
            else:
                print(f"  ❌ Apertura fue rechazada para {symbol}")
                # Intentar obtener más información del estado
                print(f"     total_operaciones_abiertas: {bot.total_operaciones_abiertas}")
                print(f"     bot_pausado: {getattr(bot, 'bot_pausado', 'N/A')}")
                return False
        except Exception as e:
            print(f"  ❌ Error abriendo operación: {str(e)[:80]}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"  ❌ Error general en prueba: {str(e)[:80]}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("TEST DE APERTURA DE OPERACIONES - GOLD & SILVER")
    print("="*80)
    
    try:
        print("\n[SETUP] Creando ventana Tk...")
        root = tk.Tk()
        root.withdraw()
        print("[OK] Ventana creada")
        
        print("\n[IMPORT] Importando bot...")
        from boteddver1 import MT5AdaptiveTradingBot
        print("[OK] Bot importado")
        
        print("\n[INIT] Creando instancia del bot...")
        bot = MT5AdaptiveTradingBot(root)
        print("[OK] Bot instanciado exitosamente\n")
        
        # Esperar un poco para que estabilice
        time.sleep(2)
        
        # Prueba GOLD
        gold_ok = test_symbol_operations(bot, 'GOLD')
        
        # Prueba SILVER
        silver_ok = test_symbol_operations(bot, 'SILVER')
        
        # Resumen final
        print(f"\n{'='*80}")
        print("RESUMEN")
        print(f"{'='*80}")
        print(f"GOLD:   {'✅ PASS' if gold_ok else '❌ FAIL'}")
        print(f"SILVER: {'✅ PASS' if silver_ok else '❌ FAIL'}")
        print(f"\nTotal operaciones activas: {bot.total_operaciones_abiertas}")
        
        if gold_ok and silver_ok:
            print("\n🎉 ¡AMBOS SÍMBOLOS FUNCIONAN CORRECTAMENTE!")
        else:
            print("\n⚠️  ALGUNOS SÍMBOLOS PRESENTARON PROBLEMAS")
        
        print(f"{'='*80}\n")
        
        # Cleanup
        root.destroy()
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
