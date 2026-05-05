#!/usr/bin/env python3
"""
🔄 Regenera 1000 snapshots con símbolo GOLD
"""
from market_snapshot_generator import MarketSnapshotGenerator
import datetime

print('🔄 Generando 1000 snapshots con símbolo GOLD...')
generator = MarketSnapshotGenerator(base_price=5377.50, symbol='GOLD')
start_time = datetime.datetime(2024, 1, 15, 0, 0, 0)
snapshots = generator.generate_1000_snapshots(start_time, 'logs/market_snapshots.json', num_snapshots=1000)

print(f'✅ Generados {len(snapshots)} snapshots')
print(f'📍 Símbolo: {snapshots[0].get("symbol", "N/A")}')
print(f'💾 Guardados en: logs/market_snapshots.json')
