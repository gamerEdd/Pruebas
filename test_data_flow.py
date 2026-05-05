# -*- coding: utf-8 -*-
"""Test bot with periodic data updates"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import tkinter as tk
import time
from datetime import datetime

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Bot Initialization & Data Update Test\n")

try:
    root = tk.Tk()
    root.withdraw()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Step 1: Import MT5AdaptiveTradingBot")
    sys.stdout.flush()
    
    from botiaver1 import MT5AdaptiveTradingBot
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Step 2: Create bot instance (note: bot_loop runs in daemon thread)")
    sys.stdout.flush()
    
    bot = MT5AdaptiveTradingBot(root)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waiting 2 seconds for initialization logs...")
    sys.stdout.flush()
    time.sleep(2)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking bot properties:")
    
    # Get bot status
    print(f"   - Bot running: {bot.is_running if hasattr(bot, 'is_running') else 'Unknown'}")
    print(f"   - Data ready: {bot.data_ready}")
    print(f"   - Data loader: {'✅' if bot.data_loader else '❌'}")
    
    if bot.data_loader:
        snapshot_count = len(bot.data_loader.market_snapshots)
        print(f"   - Snapshots in loader: {snapshot_count}")
        
        # Check if specialists have data
        buy_data = getattr(bot.buy_specialist, 'market_snapshots', None)
        sell_data = getattr(bot.sell_specialist, 'market_snapshots', None)
        
        print(f"   - Buy specialist has data: {'✅' if buy_data else '❌'}")
        print(f"   - Sell specialist has data: {'✅' if sell_data else '❌'}")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Test completed successfully!")
    
    # Stop the bot gracefully
    bot.is_running = False
    time.sleep(0.5)
    
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {type(e).__name__}: {str(e)[:100]}")
    import traceback
    traceback.print_exc()
finally:
    try:
        root.destroy()
    except:
        pass

