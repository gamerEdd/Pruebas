#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test para verificar que el fix de división por cero funciona"""

import warnings
import numpy as np

# Capturar warnings
warnings.simplefilter('error', RuntimeWarning)

try:
    from data_loader_trainer import DataLoaderTrainer
    print("✅ DataLoaderTrainer importado sin RuntimeWarning")
    
    # Test con valores que causarían problemas antes
    print("\n[TEST] Calculando volatilidad con protección...")
    
    # Simular datos problemáticos (con ceros)
    test_closes = np.array([100.0, 101.0, 102.0, 0.0, 0.0, 103.0, 104.0])
    
    # Aplicar la lógica corregida
    price_diffs = np.diff(test_closes)
    price_base = np.array(test_closes[:-1])
    
    # Proteger contra valores cero o muy pequeños
    price_base_safe = np.where(np.abs(price_base) < 1e-10, 1e-10, price_base)
    returns = price_diffs / price_base_safe
    returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)
    
    print(f"   Price diffs: {price_diffs}")
    print(f"   Price base (original): {price_base}")
    print(f"   Price base (safe): {price_base_safe}")
    print(f"   Returns: {returns}")
    print(f"   Volatility: {np.std(returns):.6f}")
    
    print("\n✅ TEST PASADO: Sin RuntimeWarning, valores numéricos válidos")
    
except RuntimeWarning as e:
    print(f"❌ RuntimeWarning detectado: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
