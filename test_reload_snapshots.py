import tkinter as tk
from botiaver1 import MT5AdaptiveTradingBot

root = tk.Tk()
root.withdraw()
bot = MT5AdaptiveTradingBot(root)

snaps = bot.reload_market_snapshots()
print('Snapshots loaded:', len(snaps))
if snaps:
    print('Last timestamp:', snaps[-1].get('timestamp'))

root.destroy()
