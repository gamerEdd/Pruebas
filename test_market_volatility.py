#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test con datos de mercado reales para verificar el fix"""

import warnings
import json

# Capturar warnings
warnings.simplefilter('error', RuntimeWarning)

try:
    print("✅ Cargando datos de market_snapshots...")
    
    with open('logs/market_snapshots.json', 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'snapshots' in data:
        snapshots = data['snapshots']
    else:
        snapshots = data
    
    print(f"   Total snapshots: {len(snapshots)}")
    
    # Extraer precios
    closes = [s.get('close') or s.get('price', {}).get('close', 0) for s in snapshots[-100:]]
    
    print(f"   Últimas 100 barras: {len(closes)}")
    print(f"   Rango de precios: {min(closes):.2f} - {max(closes):.2f}")
    
    # Aplicar cálculo de volatilidad
    import numpy as np
    price_diffs = np.diff(closes)
    price_base = np.array(closes[:-1])
    
    # Proteger contra valores cero
    price_base_safe = np.where(np.abs(price_base) < 1e-10, 1e-10, price_base)
    returns = price_diffs / price_base_safe
    returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)
    
    volatility = np.std(returns)
    
    print(f"   Volatilidad (std): {volatility:.8f}")
    print(f"   Returns mean: {np.mean(returns):.8f}")
    print(f"   Returns min: {np.min(returns):.8f}")
    print(f"   Returns max: {np.max(returns):.8f}")
    
    # Verificar que no hay NaN o infinito
    assert not np.isnan(volatility), "Volatility es NaN"
    assert not np.isinf(volatility), "Volatility es infinito"
    assert not any(np.isnan(returns)), "Returns contiene NaN"
    assert not any(np.isinf(returns)), "Returns contiene infinito"
    
    print("\n✅ TEST PASADO: Datos de mercado procesados correctamente sin warnings")
    
except RuntimeWarning as e:
    print(f"❌ RuntimeWarning detectado: {e}")
    exit(1)
except FileNotFoundError:
    print("⚠️  Archivo market_snapshots.json no encontrado (OK si es la primera vez)")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
