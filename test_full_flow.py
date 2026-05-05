#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test completo del flujo: Genrar -> Cargar -> Analizar -> Arbitrar"""

import json
import sys
import os
from pathlib import Path

# Agregar rutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flow():
    print("\n" + "="*80)
    print("[TEST] Iniciando prueba del flujo completo")
    print("="*80)
    
    # Step 1: Generar datos
    print("\n[STEP 1] Generando 4 semanas de datos...")
    try:
        from market_snapshot_generator import MarketSnapshotGenerator
        gen = MarketSnapshotGenerator(symbol="XAUUSD")
        snapshots = gen.generate_snapshots(weeks=4, num_snapshots=None)
        print(f"[OK] Generados {len(snapshots)} snapshots")
        if len(snapshots) < 5000:
            print(f"[WARN] Solo {len(snapshots)} snapshots, esperaba ~20,160 para 4 semanas")
    except Exception as e:
        print(f"[ERROR] Generando datos: {e}")
        return False
    
    # Step 2: Verificar json
    print("\n[STEP 2] Verificando estructura de market_snapshots.json...")
    try:
        snap_file = Path("logs/market_snapshots.json")
        if not snap_file.exists():
            print(f"[ERROR] No existe {snap_file}")
            return False
        
        with open(snap_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar estructura
        if isinstance(data, dict) and 'snapshots' in data:
            snaps = data['snapshots']
            print(f"[OK] JSON es DICT con 'snapshots' key: {len(snaps)} elementos")
        elif isinstance(data, list):
            snaps = data
            print(f"[OK] JSON es LISTA directa: {len(snaps)} elementos")
        else:
            print(f"[ERROR] Estructura inesperada: {type(data)}")
            return False
        
        if snaps:
            snap0 = snaps[0]
            keys = list(snap0.keys())[:5]
            print(f"      Primeras claves: {keys}")
    except Exception as e:
        print(f"[ERROR] Verificando JSON: {e}")
        return False
    
    # Step 3: Cargar snapshots via trade_logger
    print("\n[STEP 3] Cargando snapshots con read_market_snapshots()...")
    try:
        from trade_logger import read_market_snapshots
        loaded_snaps = read_market_snapshots()
        
        if isinstance(loaded_snaps, list):
            print(f"[OK] Devuelve LIST: {len(loaded_snaps)} elementos")
        elif isinstance(loaded_snaps, dict):
            print(f"[ERROR] Devuelve DICT (ya deberia estar fijo): {list(loaded_snaps.keys())}")
            return False
        else:
            print(f"[ERROR] Tipo inesperado: {type(loaded_snaps)}")
            return False
    except Exception as e:
        print(f"[ERROR] Cargando: {e}")
        return False
    
    # Step 4: Analizar con BUY specialist
    print("\n[STEP 4] Analizando con BUY specialist...")
    try:
        from buy_specialist_ai import BuySpecialistAI
        
        # Crear especialista con logging callback
        def log_callback(msg, tag='info'):
            print(f"    [{tag}] {msg}")
        
        buy = BuySpecialistAI(log_callback=log_callback)
        
        print(f"      Creado BUY specialist")
        print(f"      Llamando analyze() con {len(loaded_snaps[:100])} snapshots...")
        
        # Usar check_recovery_potential=False para no acceder a MT5
        result = buy.analyze("XAUUSD", market_snapshots=loaded_snaps[:100], check_recovery_potential=False)
        
        if result is None:
            print(f"[ERROR] BUY analisis devolvio None")
            return False
        
        print(f"[OK] BUY analisis completado")
        print(f"      Score: {result.get('score', 'N/A')}")
        print(f"      Confidence: {result.get('confidence', 'N/A')}%")
        print(f"      Recommendation: {result.get('recommendation', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] En BUY: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Analizar con SELL specialist
    print("\n[STEP 5] Analizando con SELL specialist...")
    try:
        from sell_specialist_ai import SellSpecialistAI
        sell = SellSpecialistAI(log_callback=log_callback)
        # Usar check_recovery_potential=False para no acceder a MT5
        result = sell.analyze("XAUUSD", market_snapshots=loaded_snaps[:100], check_recovery_potential=False)
        
        if result is None:
            print(f"[ERROR] SELL analisis devolvio None")
            return False
        
        print(f"[OK] SELL analisis completado")
        print(f"      Score: {result.get('score', 'N/A')}")
        print(f"      Confidence: {result.get('confidence', 'N/A')}%")
        print(f"      Recommendation: {result.get('recommendation', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] En SELL: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Arbitrar
    print("\n[STEP 6] Arbitrando BUY vs SELL con symbol='XAUUSD'...")
    try:
        from decision_arbitrator_ai import DecisionArbitratorAI
        arb = DecisionArbitratorAI()
        
        buy_res = buy.analyze("XAUUSD", market_snapshots=loaded_snaps[:100], check_recovery_potential=False)
        sell_res = sell.analyze("XAUUSD", market_snapshots=loaded_snaps[:100], check_recovery_potential=False)
        
        if not buy_res or not sell_res:
            print("[ERROR] Analisis previos fallaron")
            return False
        
        # Paso CORRECTO: pasar symbol (string)
        arb_result = arb.arbitrate(buy_res, sell_res, "XAUUSD")
        
        if arb_result is None:
            print(f"[ERROR] Arbitracion devolvio None")
            return False
        
        print(f"[OK] Arbitracion completada")
        print(f"      Recommendation: {arb_result.get('recommendation', 'N/A')}")
        print(f"      Reasoning: {str(arb_result.get('reasoning', 'N/A'))[:80]}")
    except Exception as e:
        print(f"[ERROR] En arbitracion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("[OK] FLUJO COMPLETO: EXITO")
    print("="*80 + "\n")
    return True

if __name__ == "__main__":
    try:
        success = test_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUMPIDO]")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
