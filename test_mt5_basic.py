#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import MetaTrader5 as mt5

sys.path.insert(0, 'c:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas')

# Init MT5 directly
if not mt5.initialize():
    print("MT5 init failed")
    sys.exit(1)

print("\n=== TEST: GOLD y SILVER operations ===\n")

# Check initial positions
pos_before = mt5.positions_get() or []
print("[1] Initial positions: {}".format(len(pos_before)))

# Open BUY in GOLD
print("[2] Testing GOLD BUY via MT5 direct...")
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "GOLD",
    "volume": 0.01,
    "type": mt5.ORDER_TYPE_BUY,
    "price": 4620.0,
    "sl": 4600.0,
    "tp": 4650.0,
    "magic": 123456,
    "comment": "TEST-GOLD",
}
result_gold = mt5.order_send(request)
if result_gold and result_gold.retcode == mt5.TRADE_RETCODE_DONE:
    print("    SUCCESS - GOLD order placed: ticket={}".format(result_gold.order))
else:
    print("    FAILED - retcode: {}".format(result_gold.retcode if result_gold else "None"))

time.sleep(1)

# Open BUY in SILVER
print("[3] Testing SILVER BUY via MT5 direct...")
request_silver = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "SILVER",
    "volume": 0.1,
    "type": mt5.ORDER_TYPE_BUY,
    "price": 74.8,
    "sl": 74.0,
    "tp": 76.0,
    "magic": 123456,
    "comment": "TEST-SILVER",
}
result_silver = mt5.order_send(request_silver)
if result_silver and result_silver.retcode == mt5.TRADE_RETCODE_DONE:
    print("    SUCCESS - SILVER order placed: ticket={}".format(result_silver.order))
else:
    print("    FAILED - retcode: {}".format(result_silver.retcode if result_silver else "None"))

time.sleep(1)

# Check final positions
pos_after = mt5.positions_get() or []
gold_pos = [p for p in pos_after if p.symbol == 'GOLD']
silver_pos = [p for p in pos_after if p.symbol == 'SILVER']

print("\n[4] Results:")
print("    Total positions: {}".format(len(pos_after)))
print("    GOLD: {} position(s)".format(len(gold_pos)))
print("    SILVER: {} position(s)".format(len(silver_pos)))

if len(gold_pos) > 0 or len(silver_pos) > 0:
    print("\n[OK] Operations can open in both GOLD and SILVER")
else:
    print("\n[FAIL] No positions opened")

mt5.shutdown()
