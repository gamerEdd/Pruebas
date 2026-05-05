import MetaTrader5 as mt5
from datetime import datetime
mt5.initialize()
r = mt5.copy_rates_from('GOLD', mt5.TIMEFRAME_M1, datetime.now(), 10)
print('type', type(r), 'len', None if r is None else len(r))
print('sample', r[:2])
