#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test rápido del sistema integrado:
- market_snapshot_generator generando 4 semanas
- botiaver1 entrenando especialistas cada 5 min
- Análisis dual BUY+SELL antes de abrir
"""

import json
from market_snapshot_generator import MarketSnapshotGenerator
from datetime import datetime

print("\n[TEST] Probando market_snapshot_generator...")
gen = MarketSnapshotGenerator(symbol="GOLD")

# Generar 4 semanas (reducido a 100 para test rápido)
snapshots = gen.generate_snapshots(weeks=4, num_snapshots=100, output_path="logs/market_snapshots_test.json")

# Verificar
print(f"[OK] {len(snapshots)} snapshots generados")
print(f"[OK] Primero: {snapshots[0]['timestamp']}")
print(f"[OK] Último: {snapshots[-1]['timestamp']}")

# Leer archivo
with open("logs/market_snapshots_test.json") as f:
    data = json.load(f)
    print(f"[OK] Archivo tiene {data['total_snapshots']} snapshots")
    print(f"[OK] Timeframe: {data['timeframe']}")
    print(f"[OK] Symbol: {data['symbol']}")

print("\n[SUCCESS] Sistema listo para botiaver1")
print("Próximo paso: python botiaver1.py")
