# -*- coding: utf-8 -*-
"""Test para verificar que TickFlowAnalyzer obtiene ticks correctamente"""

import sys
import MetaTrader5 as mt5
from datetime import datetime, timedelta

sys.path.insert(0, 'c:/Users/eddgt/Desktop/newtradebots')
from tick_flow_analyzer import TickFlowAnalyzer

# Crear logger simple
def simple_log(msg, level='info'):
    time_str = datetime.now().strftime('%H:%M:%S')
    print(f"[{time_str}] {msg}")

print("="*70)
print("[TEST] TICK FLOW ANALYZER")
print("="*70)

# Conectar a MT5
print("\n[1] CONECTANDO A MT5...\n")
if mt5.initialize():
    print("[OK] MT5 CONECTADO")
    account = mt5.account_info()
    print(f"    Cuenta: {account.login}")
    
    # Crear analizador
    print("\n[2] CREANDO TICK FLOW ANALYZER...\n")
    analyzer = TickFlowAnalyzer(symbol='XAUUSD', log_callback=simple_log)
    analyzer.enabled = True
    print(f"[OK] Analizador creado")
    
    # Test 1: Obtener ticks
    print("\n[3] OBTENIENDO TICKS (ESTRATEGIAS EN CASCADA)...\n")
    ticks = analyzer.get_recent_ticks(limit=400)
    
    if ticks is not None and len(ticks) > 0:
        print(f"\n[OK] EXITO: {len(ticks)} ticks obtenidos")
        print(f"    Primer tick: {ticks[0]['time']} | Ask: {ticks[0]['ask']:.5f}")
        print(f"    Ultimo tick: {ticks[-1]['time']} | Ask: {ticks[-1]['ask']:.5f}")
        
        # Test 2: Calcular imbalance
        print("\n[4] CALCULANDO IMBALANCE...\n")
        imbalance = analyzer.calculate_order_flow_imbalance(ticks)
        print(f"[OK] Imbalance: {imbalance:+.0f}")
        
        # Test 3: Confirmar señal
        print("\n[5] CONFIRMANDO SEÑAL BUY...\n")
        result_buy = analyzer.confirm_signal('BUY', ticks=ticks)
        print(f"[OK] Resultado BUY: Confirmada={result_buy.get('confirmed')} | Razon={result_buy.get('reason')}")
        
        print("\n[6] CONFIRMANDO SEÑAL SELL...\n")
        result_sell = analyzer.confirm_signal('SELL', ticks=ticks)
        print(f"[OK] Resultado SELL: Confirmada={result_sell.get('confirmed')} | Razon={result_sell.get('reason')}")
        
        # Test 4: Resolver dirección final
        print("\n[7] RESOLVIENDO DIRECCION FINAL (BUY)...\n")
        resolution_buy = analyzer.resolve_final_direction('BUY', ticks=ticks)
        print(f"[OK] Direccion Final: {resolution_buy.get('final_direction')} | Invertida: {resolution_buy.get('inverted')}")
        
        print("\n[8] RESOLVIENDO DIRECCION FINAL (SELL)...\n")
        resolution_sell = analyzer.resolve_final_direction('SELL', ticks=ticks)
        print(f"[OK] Direccion Final: {resolution_sell.get('final_direction')} | Invertida: {resolution_sell.get('inverted')}")
        
    else:
        print("[ERROR] FALLÓ: No se obtuvieron ticks")
        print(f"        Resultado: {ticks}")
    
    print("\n" + "="*70)
    print("[OK] TEST COMPLETADO")
    print("="*70)
    
    mt5.shutdown()
else:
    print("[ERROR] No se pudo conectar a MT5")
