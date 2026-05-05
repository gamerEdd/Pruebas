import MetaTrader5 as mt5
from auto_calibration import prefill_market_data

print('mt5 module:', mt5)
try:
    ok = mt5.initialize()
    print('mt5.initialize() ->', ok)
except Exception as e:
    print('mt5.initialize() raised', e)

try:
    syms = mt5.symbols_get()
    print('symbols_get ->', len(syms))
    if len(syms)>0:
        print('first symbol sample:', syms[0].name)
except Exception as e:
    print('symbols_get raised', e)

try:
    rates = mt5.copy_rates_from('GOLD', mt5.TIMEFRAME_M1, mt5.datetime.now(), 10)
    print('copy_rates_from GOLD ->', None if rates is None else len(rates))
except Exception as e:
    print('copy_rates_from raised', e)

print('calling prefill...')
print('prefill result:', prefill_market_data('GOLD', minutes=500))
