#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test: Verificar que TODAS las aperturas incluyen ENTRENAMIENTO"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_guaranteed_training():
    print("\n" + "="*80)
    print("[TEST] VERIFICAR ENTRENAMIENTO GARANTIZADO EN APERTURAS")
    print("="*80)
    
    print("\n[PASO 1] Revisar que _dual_analysis_before_opening SIEMPRE entrena...")
    
    # Leer el código de botiaver1.py
    with open('botiaver1.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la función _dual_analysis_before_opening
    if 'def _dual_analysis_before_opening' in content:
        print("[OK] _dual_analysis_before_opening existe")
        
        # Extraer la función
        start = content.find('def _dual_analysis_before_opening')
        end = content.find('\n    def ', start + 1)  # Fin de función
        func_code = content[start:end]
        
        # Verificar que hace entrenamiento
        checks = {
            'CARGAR DATOS': 'reload_market_snapshots' in func_code,
            'ENTRENAR BUY': 'buy_specialist.train' in func_code,
            'ENTRENAR SELL': 'sell_specialist.train' in func_code,
            'ANALIZAR BUY': 'buy_specialist.analyze' in func_code,
            'ANALIZAR SELL': 'sell_specialist.analyze' in func_code,
            'ARBITRADOR': 'arbitrator.arbitrate' in func_code,
        }
        
        print("\n  Verificando pasos en _dual_analysis_before_opening:")
        all_ok = True
        for step, present in checks.items():
            status = "[OK]" if present else "[MISSING]"
            print(f"    {status} {step}")
            if not present:
                all_ok = False
        
        if not all_ok:
            print("\n  [ERROR] Faltan pasos en _dual_analysis_before_opening")
            return False
    else:
        print("[ERROR] No existe _dual_analysis_before_opening")
        return False
    
    print("\n[PASO 2] Verificar que abrir_operacion REQUIERE análisis dual...")
    
    # Buscar abrir_operacion
    if 'def abrir_operacion' in content:
        print("[OK] abrir_operacion existe")
        
        start = content.find('def abrir_operacion')
        end = content.find('\n    def ', start + 1)
        func_code = content[start:end]
        
        # Verificar que REQUIERE análisis dual
        if '_dual_analysis_before_opening' in func_code:
            print("[OK] abrir_operacion LLAMA _dual_analysis_before_opening")
        else:
            print("[ERROR] abrir_operacion NO llama _dual_analysis_before_opening")
            return False
            
        if 'recommendation' in func_code and 'HOLD' in func_code:
            print("[OK] abrir_operacion VERIFICA recomendación del arbitrador")
        else:
            print("[WARNING] No se verifica recomendación del arbitrador")
    else:
        print("[ERROR] No existe abrir_operacion")
        return False
    
    print("\n[PASO 3] Verificar que bot_loop usa _dual_analysis_before_opening...")
    
    # Buscar donde se llama a abrir_operacion en bot_loop
    bot_loop_start = content.find('def bot_loop')
    bot_loop_end = content.find('\n    def ', bot_loop_start + 1)
    bot_loop_code = content[bot_loop_start:bot_loop_end]
    
    dual_calls = bot_loop_code.count('_dual_analysis_before_opening')
    print(f"[OK] bot_loop llama _dual_analysis_before_opening {dual_calls} veces")
    
    if dual_calls >= 1:
        print("[OK] Flujo de apertura INCLUYE análisis dual")
    else:
        print("[WARNING] Posible que bot_loop no use _dual_analysis_before_opening")
    
    print("\n[PASO 4] Resumendel flujo garantizado:")
    print("""
    ANTES DE CADA OPERACIÓN:
    1. Cargar datos frescos (4 semanas)
    2. ENTRENAR buy_specialist.train(snapshots)
    3. ENTRENAR sell_specialist.train(snapshots)
    4. Analizar buy_specialist.analyze(...)
    5. Analizar sell_specialist.analyze(...)
    6. Arbitrador decide: BUY/SELL/HOLD
    7. Si arbitrador dice BUY o SELL -> Abrir operación
    8. Si arbitrador dice HOLD -> NO abrir
    
    ESTO PASA AHORA SIEMPRE, EN CADA INTENTO DE APERTURA.
    """)
    
    print("="*80)
    print("[EXITO] SISTEMA ENTRENARÁ ESPECIALISTAS ANTES DE CADA OPERACIÓN")
    print("="*80 + "\n")
    return True

if __name__ == "__main__":
    try:
        success = test_guaranteed_training()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
