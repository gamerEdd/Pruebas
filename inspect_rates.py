import MetaTrader5 as mt5
from datetime import datetime
mt5.initialize()
r = mt5.copy_rates_from('GOLD', mt5.TIMEFRAME_M1, datetime.now(), 5)
print('rates type:', type(r))
for i, row in enumerate(r):
    try:
        print(i, row['time'], row['open'], row['close'])
    except Exception as e:
        print('row access error', e)
