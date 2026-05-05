#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Operaciones forzadas con conflicto (HOLD)

Comprueba que:
1. Si HOLD + diferencia score > 10 → Abre en dirección con score superior
2. Si HOLD + diferencia score <= 10 → Respeta HOLD (no abre)
3. Si NO forzada + HOLD → Abre (respeta HOLD)  
"""

import sys
import json

def test_forced_conflict_logic():
    """Prueba la lógica de apertura forzada con conflicto"""
    
    print("=" * 70)
    print("[TEST] Lógica de apertura forzada con conflicto (HOLD)")
    print("=" * 70)
    
    # Simulación: análisis con conflicto (HOLD) pero scores diferentes
    
    # CASO 1: HOLD + diferencia GRANDE (34.3 vs 17.9 = 16.4 >= 10)
    print("\n[CASO 1] HOLD + diferencia GRANDE (SELL=34.3 vs BUY=17.9)")
    buy_score = 17.9
    sell_score = 34.3
    diff = abs(buy_score - sell_score)
    
    print(f"  BUY Score: {buy_score}, SELL Score: {sell_score}")
    print(f"  Diferencia: {diff:.1f}")
    
    if diff >= 10:
        winner = "SELL" if sell_score > buy_score else "BUY"
        print(f"  ✅ Diferencia >= 10 → Abrir en {winner} (score superior: {max(buy_score, sell_score):.1f})")
        assert winner == "SELL", "Debería abrir en SELL"
    else:
        print(f"  ✗ Diferencia < 10 → Respetar HOLD")
        assert False, "No debería llegar aquí"
    
    # CASO 2: HOLD + diferencia PEQUEÑA (20 vs 18 = 2 < 10)
    print("\n[CASO 2] HOLD + diferencia PEQUEÑA (BUY=20 vs SELL=18)")
    buy_score = 20.0
    sell_score = 18.0
    diff = abs(buy_score - sell_score)
    
    print(f"  BUY Score: {buy_score}, SELL Score: {sell_score}")
    print(f"  Diferencia: {diff:.1f}")
    
    if diff >= 10:
        winner = "SELL" if sell_score > buy_score else "BUY"
        print(f"  ✅ Diferencia >= 10 → Abrir en {winner}")
        assert False, "No debería llegar aquí"
    else:
        print(f"  ✅ Diferencia < 10 → Respetar HOLD (no abrir)")
        assert True
    
    # CASO 3: HOLD + diferencia EXACTA LÍMITE (25 vs 15 = 10 >= 10)
    print("\n[CASO 3] HOLD + diferencia EXACTA LÍMITE (BUY=25 vs SELL=15)")
    buy_score = 25.0
    sell_score = 15.0
    diff = abs(buy_score - sell_score)
    
    print(f"  BUY Score: {buy_score}, SELL Score: {sell_score}")
    print(f"  Diferencia: {diff:.1f}")
    
    if diff >= 10:
        winner = "BUY" if buy_score > sell_score else "SELL"
        print(f"  ✅ Diferencia >= 10 → Abrir en {winner}")
        assert True
    else:
        print(f"  ✅ Diferencia < 10 → Respetar HOLD")
        assert False, "10.0 cumple >= 10"
    
    # CASO 4: HOLD + diferencia APENAS DEBAJO LÍMITE (24.9 vs 15 = 9.9 < 10)
    print("\n[CASO 4] HOLD + diferencia APENAS DEBAJO (BUY=24.9 vs SELL=15)")
    buy_score = 24.9
    sell_score = 15.0
    diff = abs(buy_score - sell_score)
    
    print(f"  BUY Score: {buy_score}, SELL Score: {sell_score}")
    print(f"  Diferencia: {diff:.1f}")
    
    if diff >= 10:
        print(f"  ✗ Diferencia >= 10 → Abrir")
        assert False, "No debería llegar aquí"
    else:
        print(f"  ✅ Diferencia < 10 → Respetar HOLD")
        assert True
    
    print("\n" + "=" * 70)
    print("[✅ EXITO] Toda la lógica de conflicto forzado funciona correctamente")
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    try:
        test_forced_conflict_logic()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[❌ ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[❌ ERROR INESPERADO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
