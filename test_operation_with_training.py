#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test práctico: Simula apertura de operación con entrenamiento garantizado"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_operation_opening():
    print("\n" + "="*80)
    print("[SIMULACION] APERTURA DE OPERACION CON ENTRENAMIENTO GARANTIZADO")
    print("="*80)
    
    try:
        # Step 0: Importar necesarios
        print("\n[SETUP] Inicializando componentes...")
        from buy_specialist_ai import BuySpecialistAI
        from sell_specialist_ai import SellSpecialistAI
        from decision_arbitrator_ai import DecisionArbitratorAI
        from trade_logger import read_market_snapshots
        
        def log_fn(msg, tag='info'):
            print(f"    [{tag}] {msg}")
        
        print("[OK] Componentes listos")
        
        # Step 1: Cargar datos
        print("\n[PASO 1] Cargar datos frescos (4 semanas)")
        snapshots = read_market_snapshots()
        print(f"[OK] Cargados {len(snapshots)} snapshots")
        
        if len(snapshots) < 100:
            print("[ERROR] Datos insuficientes")
            return False
        
        # Step 2: Crear especialistas
        print("\n[PASO 2] Crear especialistas")
        buy = BuySpecialistAI(log_callback=log_fn)
        sell = SellSpecialistAI(log_callback=log_fn)
        arb = DecisionArbitratorAI()
        print("[OK] Especialistas creados")
        
        # Step 3: ENTRENAR especialistas
        print("\n[PASO 3] ENTRENAR buy_specialist con {} barras".format(len(snapshots)))
        train_buy = buy.train(snapshots)
        if train_buy['status'] != 'success':
            print("[ERROR] Entrenamiento BUY fallido")
            return False
        print(f"[OK] BUY entrenado - RSI baseline: {train_buy['baseline']['rsi_mean']:.1f}")
        
        print("\n[PASO 4] ENTRENAR sell_specialist con {} barras".format(len(snapshots)))
        train_sell = sell.train(snapshots)
        if train_sell['status'] != 'success':
            print("[ERROR] Entrenamiento SELL fallido")
            return False
        print(f"[OK] SELL entrenado - RSI baseline: {train_sell['baseline']['rsi_mean']:.1f}")
        
        # Step 5: Analizar con especialistas entrenados
        print("\n[PASO 5] Analizar BUY con baseline de entrenamiento")
        buy_res = buy.analyze("XAUUSD", market_snapshots=snapshots, check_recovery_potential=False)
        if not buy_res:
            print("[ERROR] Análisis BUY fallido")
            return False
        print(f"[OK] BUY Score: {buy_res['score']:.1f} | Conf: {buy_res['confidence']}%")
        
        print("\n[PASO 6] Analizar SELL con baseline de entrenamiento")
        sell_res = sell.analyze("XAUUSD", market_snapshots=snapshots, check_recovery_potential=False)
        if not sell_res:
            print("[ERROR] Análisis SELL fallido")
            return False
        print(f"[OK] SELL Score: {sell_res['score']:.1f} | Conf: {sell_res['confidence']}%")
        
        # Step 6: Arbitrador decide
        print("\n[PASO 7] Arbitrador arbitra entre BUY y SELL")
        arb_res = arb.arbitrate(buy_res, sell_res, "XAUUSD")
        if not arb_res:
            print("[ERROR] Arbitración fallida")
            return False
        
        rec = arb_res.get('recommendation', 'N/A')
        print(f"[OK] Arbitrador decidió: {rec}")
        
        # Step 7: Decidir si abrir operación
        print("\n[PASO 8] Decidir si abrir operación")
        if rec in ['BUY', 'SELL']:
            print(f"[OK] Arbitrador autoriza abrir {rec}")
            print(f"\n[OPERACION] Abriendo {rec} en XAUUSD")
            print(f"            (Con análisis basado en:)")
            print(f"            - 4 semanas de histórico")
            print(f"            - Especialistas ENTRENADOS")
            print(f"            - Arbitrador VERIFICÓ")
        else:
            print(f"[HOLD] Arbitrador NO autoriza ({rec}) - NO ABRIR")
            print(f"\n[OK] Sistema protegido - No abrió operación especulativa")
        
        print("\n" + "="*80)
        print("[EXITO] SIMULACION COMPLETADA")
        print("\nLO QUE PASABA ANTES:")
        print("  - Abría operación casi SIN análisis")
        print("  - Solo usaba MT5 en vivo, sin histórico")
        print("  - No verificaba ambos especialistas")
        print("  - Resultado: MUCHAS operaciones BUY innecesarias")
        print("\nLO QUE PASA AHORA:")
        print("  - SIEMPRE entrena especalistas primero")
        print("  - Usa 4 semanas de histórico para baseline")
        print("  - Verifica AMBOS especialistas (BUY + SELL)")
        print("  - Arbitrador decide: ABRIR o NO ABRIR")
        print("  - Resultado: Operaciones SOLO cuando AMBOS aprueban")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = simulate_operation_opening()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        sys.exit(1)
