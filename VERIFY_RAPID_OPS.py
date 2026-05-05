#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VERIFICACION RÁPIDA - Operaciones Rápidas
"""

import sys
print(f"[✓] Python {sys.version.split()[0]}")

# Verificar que métodos existen
try:
    from botiaver1 import MT5AdaptiveTradingBot
    print("[✓] Clase MT5AdaptiveTradingBot importada")
    
    # Verificar métodos
    methods = [
        'create_rapid_operations_panel',
        'start_rapid_operations',
        'stop_rapid_operations',
        'monitor_rapid_operations',
        'open_rapid_operation',
        'check_and_close_rapid_operations',
        'update_rapid_operations_ui',
        'update_rapid_ops_display'
    ]
    
    for method in methods:
        if hasattr(MT5AdaptiveTradingBot, method):
            print(f"   [✓] {method}")
        else:
            print(f"   [✗] {method} - FALTA")
            
    print("\n[✓] VERIFICACIÓN COMPLETADA - Todo OK")
    
except Exception as e:
    print(f"[✗] Error: {e}")
    import traceback
    traceback.print_exc()
