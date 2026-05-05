import tkinter as tk
import time
from botiaver1 import MT5AdaptiveTradingBot

root = tk.Tk()
root.title('Bot Demo Runner')
# Don't withdraw — keep UI alive for Tcl
bot = MT5AdaptiveTradingBot(root)
# Safer demo settings
try:
    bot.config['MAX_SIMULTANEOUS_OPS'].set(1)
    bot.config['RAPID_OPS_ENABLED'].set(False)
    bot.config['SNAPSHOT_RELOAD_INTERVAL'].set(5)
    bot.config['FORCED_OPEN_MINUTES'].set(1)
except Exception:
    pass

bot.start_bot()

# After 120s stop bot and close UI
def stop_and_exit():
    try:
        bot.stop_bot()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass

root.after(120000, stop_and_exit)
root.mainloop()
