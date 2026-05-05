import MetaTrader5 as mt5
mt5.initialize()
syms = mt5.symbols_get()
matches = [s.name for s in syms if 'GOLD' in s.name.upper() or 'XAU' in s.name.upper()]
print('matches count', len(matches))
print(matches[:200])
