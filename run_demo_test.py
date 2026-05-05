import tkinter as tk
import time
from botiaver1 import MT5AdaptiveTradingBot

root = tk.Tk()
root.withdraw()
bot = MT5AdaptiveTradingBot(root)

# Safer demo settings
try:
    bot.config['MAX_SIMULTANEOUS_OPS'].set(1)
    bot.config['RAPID_OPS_ENABLED'].set(False)
    bot.config['SNAPSHOT_RELOAD_INTERVAL'].set(5)
    bot.config['FORCED_OPEN_MINUTES'].set(1)
except Exception:
    pass

print('Starting bot in demo mode for 2 minutes...')
bot.start_bot()
# Let it run for 120 seconds
start = time.time()
try:
    while time.time() - start < 120:
        time.sleep(1)
except KeyboardInterrupt:
    pass

print('Stopping bot...')
bot.stop_bot()
print('Bot stopped. Check logs/bot.log and logs/monitor_debug.log for details.')
