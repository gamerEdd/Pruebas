#!/usr/bin/env python3
"""Test script to verify dual symbol initialization"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock Tkinter para pruebas sin GUI
import unittest.mock as mock
sys.modules['tkinter'] = mock.MagicMock()
sys.modules['tkinter.ttk'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print("\n" + "="*60)
print("TEST: Inicialización de Bot con Dual Symbol Support")
print("="*60 + "\n")

# Test 1: Verificar atributo pending_operations
print("[TEST 1] Verificar inicialización de pending_operations...")
try:
    from boteddver1 import MT5AdaptiveTradingBot
    print("✓ Módulo boteddver1 importado correctamente")
    
    # Crear bot con mock (sin conectar a MT5)
    with mock.patch('mt5_safe.mt5'):
        bot = MT5AdaptiveTradingBot()
        
        # Verificar que pending_operations existe
        if hasattr(bot, 'pending_operations'):
            print(f"✓ pending_operations inicializado: {type(bot.pending_operations)}")
            if isinstance(bot.pending_operations, list):
                print(f"✓ pending_operations es una lista vacía: {bot.pending_operations}")
        else:
            print("✗ FALLO: pending_operations no inicializado")
            sys.exit(1)
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Verificar market_snapshots_by_symbol
print("\n[TEST 2] Verificar market_snapshots_by_symbol para GOLD y SILVER...")
try:
    if hasattr(bot, 'market_snapshots_by_symbol'):
        print(f"✓ market_snapshots_by_symbol existe: {list(bot.market_snapshots_by_symbol.keys())}")
        
        for symbol in ['GOLD', 'SILVER']:
            if symbol in bot.market_snapshots_by_symbol:
                print(f"✓ {symbol} en market_snapshots_by_symbol")
            else:
                print(f"✗ FALLO: {symbol} no en market_snapshots_by_symbol")
                sys.exit(1)
    else:
        print("✗ FALLO: market_snapshots_by_symbol no existe")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 3: Verificar locks por símbolo
print("\n[TEST 3] Verificar locks por símbolo...")
try:
    if hasattr(bot, 'market_snapshots_lock_by_symbol'):
        for symbol in ['GOLD', 'SILVER']:
            if symbol in bot.market_snapshots_lock_by_symbol:
                print(f"✓ Lock para {symbol} existe")
            else:
                print(f"✗ FALLO: Lock para {symbol} no existe")
                sys.exit(1)
    else:
        print("✗ FALLO: market_snapshots_lock_by_symbol no existe")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 4: Verificar método reload_all_symbols_snapshots
print("\n[TEST 4] Verificar método reload_all_symbols_snapshots...")
try:
    if hasattr(bot, 'reload_all_symbols_snapshots'):
        print(f"✓ reload_all_symbols_snapshots existe")
    else:
        print(f"✗ FALLO: reload_all_symbols_snapshots no existe")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✓ TODOS LOS TESTS PASARON")
print("="*60 + "\n")
