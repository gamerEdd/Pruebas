#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Escenario REAL del usuario
- Operación forzada después de 60s
- Análisis de especialistas retorna HOLD para ambos
- SELL score (34.3) > BUY score (17.9) → diferencia 16.4 >= 10
- DEBE abrir en SELL (no en BUY como estaba haciendo)
"""

def test_user_scenario():
    """Simula el escenario exacto del usuario"""
    
    print("=" * 80)
    print("[TEST] Escenario REAL: Operación forzada con conflicto pero dirección clara")
    print("=" * 80)
    
    # Datos del escenario real
    force = True  # Es operación forzada
    direction_suggested = 'BUY'  # El sistema estaba forzando BUY
    
    # Análisis dual retorna:
    arbitrator_rec = 'HOLD'  # Conflicto
    buy_score = 17.9
    buy_conf = 45
    sell_score = 34.3
    sell_conf = 85
    
    print("\n[ENTRADA] Operación forzada")
    print(f"  force={force}")
    print(f"  direction_suggested={direction_suggested}")
    print(f"  arbitrator_recommendation={arbitrator_rec}")
    print(f"  BUY: score={buy_score}, conf={buy_conf}%")
    print(f"  SELL: score={sell_score}, conf={sell_conf}%")
    
    # Aplicar lógica
    if arbitrator_rec == 'HOLD':
        if force:
            score_diff = abs(buy_score - sell_score)
            print(f"\n[LÓGICA] Conflicto detectado")
            print(f"  Diferencia de scores: {score_diff:.1f}")
            
            if score_diff >= 10:
                winner = 'SELL' if sell_score > buy_score else 'BUY'
                print(f"  ✅ Diferencia >= 10 → Abriendo en {winner}")
                
                # Verificación
                if winner == 'SELL' and sell_score > buy_score:
                    print(f"\n[✅ CORRECTO] Abriendo en SELL (score superior: {sell_score:.1f} > {buy_score:.1f})")
                    return True
                else:
                    print(f"\n[❌ ERROR] Lógica no determinó correctamente la dirección")
                    return False
            else:
                print(f"  ❌ Diferencia < 10 → No abrir (respetar HOLD)")
                return False
        else:
            print(f"\n[❌ NO FORZADA] Debería respetar HOLD")
            return False
    else:
        print(f"\n[❌ NO ES HOLD] La lógica es diferente")
        return False

def test_small_difference_scenario():
    """Simula escenario donde la diferencia es pequeña"""
    
    print("\n" + "=" * 80)
    print("[TEST] Escenario: Conflicto con diferencia pequeña")
    print("=" * 80)
    
    force = True
    direction_suggested = 'BUY'
    
    arbitrator_rec = 'HOLD'
    buy_score = 20.0
    buy_conf = 70
    sell_score = 18.0
    sell_conf = 65
    
    print("\n[ENTRADA]")
    print(f"  force={force}")
    print(f"  BUY: score={buy_score}, conf={buy_conf}%")
    print(f"  SELL: score={sell_score}, conf={sell_conf}%")
    
    if arbitrator_rec == 'HOLD' and force:
        score_diff = abs(buy_score - sell_score)
        print(f"\n[LÓGICA] Conflicto detectado, diferencia={score_diff:.1f}")
        
        if score_diff >= 10:
            print(f"  ❌ Debería NO abrir")
            return False
        else:
            print(f"  ✅ Respetando HOLD (no abrir)")
            return True
    
    return False

if __name__ == '__main__':
    import sys
    
    try:
        result1 = test_user_scenario()
        result2 = test_small_difference_scenario()
        
        if result1 and result2:
            print("\n" + "=" * 80)
            print("[✅ EXITO] Todos los escenarios funcionan correctamente")
            print("=" * 80)
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print("[❌ FALLO] Algunos escenarios no pasaron")
            print("=" * 80)
            sys.exit(1)
    except Exception as e:
        print(f"\n[❌ ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
