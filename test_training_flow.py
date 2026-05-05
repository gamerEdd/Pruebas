#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test del flujo completo: ENTRENAR -> ANALIZAR -> ARBITRAR"""

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_training_analysis_flow():
    print("\n" + "="*80)
    print("[FLUJO COMPLETO] ENTRENAR - ANALIZAR - ARBITRAR")
    print("="*80)
    
    # Step 1: Cargar datos
    print("\n[PASO 1] Cargando 4 semanas de datos...")
    try:
        from trade_logger import read_market_snapshots
        snapshots = read_market_snapshots()
        
        if not snapshots or len(snapshots) < 100:
            print(f"[ERROR] Datos insuficientes: {len(snapshots)}")
            return False
        
        print(f"[OK] Cargados {len(snapshots)} snapshots")
    except Exception as e:
        print(f"[ERROR] Cargando snapshots: {e}")
        return False
    
    # Step 2: ENTRENAR especialistas
    print("\n[PASO 2] ENTRENANDO especialistas con los datos...")
    try:
        from buy_specialist_ai import BuySpecialistAI
        from sell_specialist_ai import SellSpecialistAI
        
        def log_cb(msg, tag='info'):
            print(f"    [{tag}] {msg}")
        
        # CREAR y ENTRENAR BUY specialist
        print("  - Creando BUY specialist...")
        buy = BuySpecialistAI(log_callback=log_cb)
        print(f"    Entrenando con {len(snapshots)} barras...")
        train_buy = buy.train(snapshots)
        print(f"    Resultado: {train_buy}")
        
        if train_buy.get('status') != 'success':
            print(f"[ERROR] BUY training failed: {train_buy}")
            return False
        
        # CREAR y ENTRENAR SELL specialist
        print("  - Creando SELL specialist...")
        sell = SellSpecialistAI(log_callback=log_cb)
        print(f"    Entrenando con {len(snapshots)} barras...")
        train_sell = sell.train(snapshots)
        print(f"    Resultado: {train_sell}")
        
        if train_sell.get('status') != 'success':
            print(f"[ERROR] SELL training failed: {train_sell}")
            return False
        
        print(f"[OK] AMBOS ESPECIALISTAS ENTRENADOS")
        print(f"    BUY Baseline: RSI={train_buy['baseline']['rsi_mean']:.1f}, Vol={train_buy['baseline']['volatility']:.4f}")
        print(f"    SELL Baseline: RSI={train_sell['baseline']['rsi_mean']:.1f}, Vol={train_sell['baseline']['volatility']:.4f}")
        
    except Exception as e:
        print(f"[ERROR] Entrenando especialistas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: ANALIZAR con especialistas entrenados
    print("\n[PASO 3] ANALIZANDO con especialistas entrenados...")
    try:
        symbol = "XAUUSD"
        
        # BUY analysis (usa baseline de entrenamiento internamente)
        print(f"  - Analizando BUY...")
        buy_result = buy.analyze(symbol, market_snapshots=snapshots, check_recovery_potential=False)
        
        if not buy_result:
            print(f"[ERROR] BUY analysis returned None")
            return False
        
        print(f"[OK] BUY Analisis:")
        print(f"    Score: {buy_result.get('score', 0):.1f}")
        print(f"    Confidence: {buy_result.get('confidence', 0)}%")
        print(f"    Recommendation: {buy_result.get('recommendation', 'N/A')}")
        
        # SELL analysis (usa baseline de entrenamiento internamente)
        print(f"  - Analizando SELL...")
        sell_result = sell.analyze(symbol, market_snapshots=snapshots, check_recovery_potential=False)
        
        if not sell_result:
            print(f"[ERROR] SELL analysis returned None")
            return False
        
        print(f"[OK] SELL Analisis:")
        print(f"    Score: {sell_result.get('score', 0):.1f}")
        print(f"    Confidence: {sell_result.get('confidence', 0)}%")
        print(f"    Recommendation: {sell_result.get('recommendation', 'N/A')}")
        
    except Exception as e:
        print(f"[ERROR] Analizando: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: ARBITRADOR decide
    print("\n[PASO 4] ARBITRADOR decide entre BUY y SELL...")
    try:
        from decision_arbitrator_ai import DecisionArbitratorAI
        
        arb = DecisionArbitratorAI()
        
        print(f"  - BUY: {buy_result.get('recommendation')} (Score: {buy_result.get('score'):.1f}, Conf: {buy_result.get('confidence')}%)")
        print(f"  - SELL: {sell_result.get('recommendation')} (Score: {sell_result.get('score'):.1f}, Conf: {sell_result.get('confidence')}%)")
        
        # Arbitrar
        arb_result = arb.arbitrate(buy_result, sell_result, symbol)
        
        if not arb_result:
            print(f"[ERROR] Arbitración devolvió None")
            return False
        
        print(f"\n[OK] DECISION FINAL DEL ARBITRADOR:")
        print(f"    Recommendation: {arb_result.get('recommendation', 'N/A')}")
        print(f"    Reasoning: {str(arb_result.get('reasoning', 'N/A'))[:120]}")
        
    except Exception as e:
        print(f"[ERROR] Arbitrando: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("[EXITO] FLUJO COMPLETO FUNCIONA:")
    print("  1. Datos (4 semanas) -> CARGADOS")
    print("  2. Especialistas -> ENTRENADOS")
    print("  3. Análisis -> COMPLETADO")
    print("  4. Arbitrador -> DECIDIÓ")
    print("="*80 + "\n")
    return True

if __name__ == "__main__":
    try:
        success = test_training_analysis_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUMPIDO]")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
