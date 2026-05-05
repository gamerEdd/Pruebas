import MetaTrader5 as mt5
from datetime import datetime, timedelta
import random

print('init mt5 ->', mt5.initialize())
try:
    rates = mt5.copy_rates_from('GOLD', mt5.TIMEFRAME_M1, datetime.now(), 500)
    print('rates raw ->', None if rates is None else len(rates), type(rates))
except Exception as e:
    print('copy_rates_from exception', e)
    rates = None

snapshots = []
if rates:
    try:
        for i, r in enumerate(rates[:5]):
            print('sample r[0]:', r['time'], r['open'], r['close'])
        for r in rates:
            snapshots.append({
                'timestamp': datetime.fromtimestamp(r['time']).isoformat(),
                'open': float(r['open']),
                'high': float(r['high']),
                'low': float(r['low']),
                'close': float(r['close']),
                'tick_volume': int(r.get('tick_volume', 0)) if hasattr(r, 'dtype') else 0
            })
        print('built snapshots from rates ->', len(snapshots))
    except Exception as e:
        print('error building snapshots from rates:', e)
        snapshots = []

if not snapshots:
    print('will build synthetic')
    last_price = None
    try:
        tick = mt5.symbol_info_tick('GOLD')
        print('tick ->', tick)
        if tick:
            last_price = (tick.ask + tick.bid) / 2
    except Exception as e:
        print('tick exception', e)
    if last_price is None:
        last_price = 1900.0
    price = float(last_price)
    now = datetime.now()
    for i in range(500):
        t = now - timedelta(minutes=500 - i)
        o = price + random.uniform(-0.15, 0.15)
        c = o + random.uniform(-0.2, 0.2)
        h = max(o, c) + random.uniform(0, 0.1)
        l = min(o, c) - random.uniform(0, 0.1)
        snapshots.append({
            'timestamp': t.isoformat(),
            'open': round(o, 6),
            'high': round(h, 6),
            'low': round(l, 6),
            'close': round(c, 6),
            'tick_volume': 0
        })
        price = c
    print('synthetic built ->', len(snapshots))

import json, os
mf = os.path.join(os.path.dirname(__file__), 'logs', 'market_snapshots.json')
with open(mf, 'w', encoding='utf-8') as f:
    json.dump(snapshots, f, ensure_ascii=False, indent=2)

print('wrote file ->', mf)
