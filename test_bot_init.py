# -*- coding: utf-8 -*-
"""Test initialization without Tkinter GUI"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import tkinter as tk
from datetime import datetime

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting bot initialization test...")

try:
    # Intentar cosas paso a paso
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Step 1: Creating Tk root...")
    sys.stdout.flush()
    
    root = tk.Tk()
    root.withdraw()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Step 2: Importing botiaver1 module...")
    sys.stdout.flush()
    
    from botiaver1 import MT5AdaptiveTradingBot
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Step 3: Creating bot instance (this might take time)...")
    sys.stdout.flush()
    
    timeout_sec = 5
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Bot initialization took more than {timeout_sec} seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    
    bot = MT5AdaptiveTradingBot(root)
    
    signal.alarm(0)  # Disable timeout
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Bot initialized successfully!")
    sys.stdout.flush()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot config keys: {len(bot.config)} configuration items")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Multi-timeframe analyzer: {bot.multi_timeframe_analyzer is not None}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Specialists: BUY={bot.buy_specialist is not None}, SELL={bot.sell_specialist is not None}")
    
    # Try to access key config values
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Symbol: {bot.config['SYMBOL'].get()}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Volume: {bot.config['VOL'].get()}")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ All tests passed!")
    sys.stdout.flush()
    root.destroy()
    
except TimeoutError as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ Timeout: {e}")
    sys.stdout.flush()
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {type(e).__name__}: {str(e)[:100]}")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.exit(1)
