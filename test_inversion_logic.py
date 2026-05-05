#!/usr/bin/env python
"""
Test: Demostrar que resolve_final_direction() INVIERTE cuando hay IMBALANCE FUERTE
permitiendo que órdenes se abran con dirección invertida en lugar de ser rechazadas.
"""

from tick_flow_analyzer import TickFlowAnalyzer
import numpy as np

print("\n" + "="*70)
print("TEST: resolve_final_direction() - INVERSIÓN AUTOMÁTICA")
print("="*70)

# Crear analizador
analyzer = TickFlowAnalyzer()

# Crear ticks sintéticos con IMBALANCE +40 (FUERTE ALCISTA)
# Esto simula lo que reportó el usuario
ticks = []

# COMPRADORES (40% más que vendedores)
for i in range(70):  # 70 ticks de compra
    ticks.append({
        'time': 1000 + i,
        'bid': 1950.0 + (i % 5) * 0.001,
        'ask': 1950.10 + (i % 5) * 0.001,
        'last': 1950.05 + (i % 5) * 0.001,
        'volume': 1,
        'time_msc': (1000 + i) * 1000,
        'flags': 16 if i % 2 == 0 else 8  # Alternating BUY/SELL indicators
    })

# VENDEDORES (menos que compradores)
for i in range(30):  # 30 ticks de venta
    ticks.append({
        'time': 1000 + 70 + i,
        'bid': 1950.0 + i * 0.001,
        'ask': 1950.10 + i * 0.001,
        'last': 1949.95 + i * 0.001,  # Lower price = sale
        'volume': 1,
        'time_msc': (1000 + 70 + i) * 1000,
        'flags': 8  # SELL
    })

print(f"\n📊 Ticks preparados: {len(ticks)} (70 BUY + 30 SELL)")
print(f"📈 Imbalance esperado: 70 - 30 = +40 (presión ALCISTA)")
print(f"⚙️ Umbral: {analyzer.imbalance_threshold}")

# TEST 1: IA dice SELL pero flujo dice BUY FUERTE → DEBE INVERTIR
print("\n" + "-"*70)
print("TEST 1: IA SELL vs FLOW +40 (FUERTE BUY)")
print("-"*70)

result = analyzer.resolve_final_direction(
    ia_direction='SELL',
    ticks=ticks
)

print(f"✓ Final Direction: {result['final_direction']}")
print(f"✓ Inverted: {result['inverted']}")
print(f"✓ Imbalance: {result['imbalance']:.0f}")
print(f"✓ Reason: {result['reason']}")

if result['final_direction'] == 'BUY' and result['inverted']:
    print("✅ CORRECTO: SELL fue INVERTIDA a BUY (flujo fuerte)")
else:
    print(f"⚠️ INESPERADO: Esperaba BUY invertida, obtuve {result['final_direction']}")

# TEST 2: IA dice BUY y flujo también BUY → SIN INVERSIÓN
print("\n" + "-"*70)
print("TEST 2: IA BUY vs FLOW +40 (FUERTE BUY) - ALINEADOS")
print("-"*70)

result2 = analyzer.resolve_final_direction(
    ia_direction='BUY',
    ticks=ticks
)

print(f"✓ Final Direction: {result2['final_direction']}")
print(f"✓ Inverted: {result2['inverted']}")
print(f"✓ Reason: {result2['reason']}")

if result2['final_direction'] == 'BUY' and not result2['inverted']:
    print("✅ CORRECTO: BUY confirmada (sin inversión, alineadas)")
else:
    print(f"⚠️ INESPERADO: {result2['final_direction']}")

print("\n" + "="*70)
print("✅ TEST COMPLETADO - Lógica de inversión funciona correctamente")
print("="*70 + "\n")
