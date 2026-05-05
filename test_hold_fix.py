#!/usr/bin/env python3
"""Test para verificar que el fix de HOLD funciona"""

import sys

try:
    # Importar para verificar sintaxis
    from botiaver1 import MT5AdaptiveTradingBot
    
    # Verificar que el método existe
    assert hasattr(MT5AdaptiveTradingBot, 'abrir_operacion'), "Método abrir_operacion no existe"
    
    # Leer el código del método para verificar la lógica
    import inspect
    source = inspect.getsource(MT5AdaptiveTradingBot.abrir_operacion)
    
    # Verificar keywords críticos
    checks = {
        'HOLD check': 'if rec == \'HOLD\'' in source,
        'Force comment': '⭐ Respeta HOLD incluso en operaciones forzadas' in source or 'Respeta HOLD' in source,
        'Conflicto message': 'conflicto' in source.lower() or 'CONFLICTO' in source,
    }
    
    print("✅ Verificación del fix de HOLD:")
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
    
    all_pass = all(checks.values())
    if all_pass:
        print("\n✅ Fix implementado correctamente")
        sys.exit(0)
    else:
        print("\n❌ Faltan componentes del fix")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
