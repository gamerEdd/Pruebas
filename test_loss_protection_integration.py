#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test para validar integración de Loss Protection AI con reentrenamiento"""

import sys

try:
    # 1. Test import de loss_protection_ai
    print("[1] Importando loss_protection_ai...")
    from loss_protection_ai import LossProtectionAI
    print("    ✅ Import exitoso")
    
    # 2. Test instanciación
    print("[2] Instanciando LossProtectionAI...")
    def dummy_log(msg, tag='info'):
        print(f"    [LOG_{tag.upper()}] {msg}")
    
    lp = LossProtectionAI(log_callback=dummy_log)
    print("    ✅ Instancia creada")
    
    # 3. Test métodos existentes
    print("[3] Verificando métodos...")
    methods = [
        'analyze_position',
        'save_closed_trade',
        'retrain_loss_predictor',
        '_predict_loss_anticipation',
        'load_trades_history'
    ]
    for method in methods:
        if hasattr(lp, method):
            print(f"    ✅ {method}")
        else:
            print(f"    ❌ {method} NO ENCONTRADO")
            sys.exit(1)
    
    # 4. Test variables estatales
    print("[4] Verificando estado...")
    assert hasattr(lp, 'model_trained'), "model_trained missing"
    assert hasattr(lp, 'trades_count'), "trades_count missing"
    assert hasattr(lp, 'loss_predictor'), "loss_predictor missing"
    print("    ✅ Todas las variables de estado presentes")
    
    # 5. Test guardado de trade
    print("[5] Test guardado de trade...")
    lp.save_closed_trade({
        'profit': 5.0,
        'direction': 'BUY',
        'entry_rsi': 45,
        'entry_momentum': 2.5,
        'entry_macd': 0.01,
        'exit_reason': 'test',
        'time_in_market': 120,
        'max_drawdown': 0
    })
    print("    ✅ Trade guardado sin errores")
    
    print("\n✅ VALIDACION COMPLETA - Loss Protection ML integrado correctamente")
    
except ImportError as e:
    print(f"❌ Error de import: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
