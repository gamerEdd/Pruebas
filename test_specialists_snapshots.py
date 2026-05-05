from buy_specialist_ai import BuySpecialistAI
from sell_specialist_ai import SellSpecialistAI
from trade_logger import read_market_snapshots

b = BuySpecialistAI()
s = SellSpecialistAI()
snaps = read_market_snapshots()
print('snapshots len', len(snaps))
resb = b.analyze('GOLD', market_snapshots=snaps)
ress = s.analyze('GOLD', market_snapshots=snaps)
print('buy res', resb is not None)
print('sell res', ress is not None)
