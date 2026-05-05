#!/usr/bin/env python
"""Quick test to verify specialists have all required methods"""

from buy_specialist_ai import BuySpecialistAI
from sell_specialist_ai import SellSpecialistAI

print("[TEST] Verifying Specialist Methods...\n")

buy = BuySpecialistAI()
sell = SellSpecialistAI()

# Check BUY specialist
buy_has_velocity = hasattr(buy, '_detect_direction_velocity')
buy_has_recommendation = hasattr(buy, '_make_buy_recommendation')

print(f"BUY Specialist:")
print(f"  ✓ _detect_direction_velocity: {buy_has_velocity}")
print(f"  ✓ _make_buy_recommendation: {buy_has_recommendation}")

# Check SELL specialist
sell_has_velocity = hasattr(sell, '_detect_direction_velocity')
sell_has_recommendation = hasattr(sell, '_make_sell_recommendation')

print(f"\nSELL Specialist:")
print(f"  ✓ _detect_direction_velocity: {sell_has_velocity}")
print(f"  ✓ _make_sell_recommendation: {sell_has_recommendation}")

# Overall status
all_ok = all([buy_has_velocity, buy_has_recommendation, sell_has_velocity, sell_has_recommendation])

if all_ok:
    print("\n✅ All Methods Present - Specialists Ready")
else:
    print("\n❌ Missing Methods - Check Implementation")
    exit(1)
