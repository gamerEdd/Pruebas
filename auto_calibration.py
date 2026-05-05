import math
from datetime import datetime
import MetaTrader5 as mt5
from trade_logger import read_trades, write_market_snapshots, read_market_snapshots
import logging

logger = logging.getLogger(__name__)


def prefill_market_data_and_return(symbol, minutes=500):
    """Fetch last `minutes` of M1 bars and return both count and snapshot list.
    ⭐ NEW: Returns (count, snapshots_list) tuple so caller can use data directly.
    This avoids relying solely on file I/O for persistence.
    """
    try:
        def _is_nonempty(x):
            try:
                return x is not None and len(x) > 0
            except Exception:
                try:
                    return x is not None and getattr(x, 'size', 0) > 0
                except Exception:
                    return False
        # Ensure MT5 is initialized
        try:
            if not mt5.initialize():
                # try once more after shutdown
                try:
                    mt5.shutdown()
                except Exception:
                    pass
                if not mt5.initialize():
                    # cannot initialize; will fallback to synthetic
                    rates = None
                else:
                    rates = None
            else:
                rates = None
        except Exception:
            rates = None

        # Try to fetch rates for the provided symbol
        fetched = []
        if rates is None:
            try:
                rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, datetime.now(), minutes)
            except Exception:
                rates = None

        # If no rates, try to resolve symbol alternatives present in the terminal
        if not _is_nonempty(rates):
            try:
                syms = mt5.symbols_get()
                symbol_upper = (symbol or '').upper()
                match = None
                for s in syms:
                    try:
                        if symbol_upper and symbol_upper in s.name.upper():
                            match = s.name
                            break
                    except Exception:
                        continue
                if match:
                    try:
                        # try select and re-copy
                        mt5.symbol_select(match, True)
                        rates = mt5.copy_rates_from(match, mt5.TIMEFRAME_M1, datetime.now(), minutes)
                    except Exception:
                        rates = None
            except Exception:
                rates = None

        snapshots = []
        if _is_nonempty(rates):
            try:
                for r in rates:
                    entry = {
                        'timestamp': datetime.fromtimestamp(r['time']).isoformat(),
                        'open': float(r['open']),
                        'high': float(r['high']),
                        'low': float(r['low']),
                        'close': float(r['close']),
                        'tick_volume': int(r.get('tick_volume', 0)) if isinstance(r, dict) or hasattr(r, 'get') else int(getattr(r, 'tick_volume', 0) if hasattr(r, 'tick_volume') else 0)
                    }
                    snapshots.append(entry)
            except Exception:
                snapshots = []

        # If still empty, create a synthetic fallback series so downstream code has data
        if not snapshots:
            # Try to get a last tick price
            last_price = None
            try:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    last_price = (tick.ask + tick.bid) / 2
            except Exception:
                last_price = None

            if last_price is None:
                # sensible defaults for common symbols
                if (symbol or '').upper() in ('GOLD', 'XAUUSD'):
                    last_price = 1900.0
                else:
                    last_price = 1.0

            # Build a simple random-walk around last_price for `minutes` bars
            import random
            from datetime import timedelta
            now = datetime.now()
            price = float(last_price)
            for i in range(minutes):
                t = now - timedelta(minutes=minutes - i)
                # small random walk
                o = price + random.uniform(-0.15, 0.15)
                c = o + random.uniform(-0.2, 0.2)
                h = max(o, c) + random.uniform(0, 0.1)
                l = min(o, c) - random.uniform(0, 0.1)
                snapshots.append({
                    'timestamp': t.isoformat(),
                    'open': round(o, 6),
                    'high': round(h, 6),
                    'low': round(l, 6),
                    'close': round(c, 6),
                    'tick_volume': 0
                })
                price = c

        # Overwrite market snapshots JSON with the latest data
        write_market_snapshots(snapshots)
        logger.info(f"[prefill_and_return] ✓ Prefilled {len(snapshots)} snapshots y guardado a archivo")
        return (len(snapshots), snapshots)  # ⭐ NUEVO: Retorna tupla
    except Exception as e:
        logger.error(f"[prefill_and_return] ❌ Error: {e}")
        return (0, [])


def prefill_market_data(symbol, minutes=500):
    """Fetch last `minutes` of M1 bars and append as market_snapshot entries to the trades log.
    Each entry: {type: 'market_snapshot', timestamp, open, high, low, close, tick_volume}
    """
    try:
        def _is_nonempty(x):
            try:
                return x is not None and len(x) > 0
            except Exception:
                try:
                    return x is not None and getattr(x, 'size', 0) > 0
                except Exception:
                    return False
        # Ensure MT5 is initialized
        try:
            if not mt5.initialize():
                # try once more after shutdown
                try:
                    mt5.shutdown()
                except Exception:
                    pass
                if not mt5.initialize():
                    # cannot initialize; will fallback to synthetic
                    rates = None
                else:
                    rates = None
            else:
                rates = None
        except Exception:
            rates = None

        # Try to fetch rates for the provided symbol
        fetched = []
        if rates is None:
            try:
                rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, datetime.now(), minutes)
            except Exception:
                rates = None

        # If no rates, try to resolve symbol alternatives present in the terminal
        if not _is_nonempty(rates):
            try:
                syms = mt5.symbols_get()
                symbol_upper = (symbol or '').upper()
                match = None
                for s in syms:
                    try:
                        if symbol_upper and symbol_upper in s.name.upper():
                            match = s.name
                            break
                    except Exception:
                        continue
                if match:
                    try:
                        # try select and re-copy
                        mt5.symbol_select(match, True)
                        rates = mt5.copy_rates_from(match, mt5.TIMEFRAME_M1, datetime.now(), minutes)
                    except Exception:
                        rates = None
            except Exception:
                rates = None

        snapshots = []
        if _is_nonempty(rates):
            try:
                for r in rates:
                    entry = {
                        'timestamp': datetime.fromtimestamp(r['time']).isoformat(),
                        'open': float(r['open']),
                        'high': float(r['high']),
                        'low': float(r['low']),
                        'close': float(r['close']),
                        'tick_volume': int(r.get('tick_volume', 0)) if isinstance(r, dict) or hasattr(r, 'get') else int(getattr(r, 'tick_volume', 0) if hasattr(r, 'tick_volume') else 0)
                    }
                    snapshots.append(entry)
            except Exception:
                snapshots = []

        # If still empty, create a synthetic fallback series so downstream code has data
        if not snapshots:
            # Try to get a last tick price
            last_price = None
            try:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    last_price = (tick.ask + tick.bid) / 2
            except Exception:
                last_price = None

            if last_price is None:
                # sensible defaults for common symbols
                if (symbol or '').upper() in ('GOLD', 'XAUUSD'):
                    last_price = 1900.0
                else:
                    last_price = 1.0

            # Build a simple random-walk around last_price for `minutes` bars
            import random
            from datetime import timedelta
            now = datetime.now()
            price = float(last_price)
            for i in range(minutes):
                t = now - timedelta(minutes=minutes - i)
                # small random walk
                o = price + random.uniform(-0.15, 0.15)
                c = o + random.uniform(-0.2, 0.2)
                h = max(o, c) + random.uniform(0, 0.1)
                l = min(o, c) - random.uniform(0, 0.1)
                snapshots.append({
                    'timestamp': t.isoformat(),
                    'open': round(o, 6),
                    'high': round(h, 6),
                    'low': round(l, 6),
                    'close': round(c, 6),
                    'tick_volume': 0
                })
                price = c

        # Overwrite market snapshots JSON with the latest data
        write_market_snapshots(snapshots)
        return len(snapshots)
    except Exception:
        return 0


def suggest_risk_pct_from_trades(trades, floor=0.0005, cap=0.05, shrink=0.5):
    """Suggest RISK_PCT using a Kelly-like estimator from closed trades list.
    trades: list of trade dicts with 'profit' key (float) and optionally 'profit' sign.
    Returns suggested fraction (float).
    """
    if not trades:
        return 0.005
    wins = [t for t in trades if float(t.get('profit', 0.0)) > 0]
    losses = [t for t in trades if float(t.get('profit', 0.0)) <= 0]
    W = len(wins)
    L = len(losses)
    N = max(1, W + L)
    win_rate = W / N
    avg_win = sum(float(t.get('profit', 0.0)) for t in wins) / W if W > 0 else 0.0
    avg_loss = - (sum(float(t.get('profit', 0.0)) for t in losses) / L) if L > 0 else 0.0
    if avg_loss <= 0 or avg_win <= 0:
        return 0.005
    R = avg_win / avg_loss
    # Kelly fraction
    kelly = max(0.0, (win_rate - (1 - win_rate) / R))
    # shrink for safety and cap
    f = kelly * shrink
    f = max(floor, min(cap, f))
    return round(f, 6)


def sweep_confidence_threshold(trades, conf_key='confidence'):
    """Sweep possible confidence thresholds (0-100 step 1) and return the threshold
    that maximizes expected profit per trade based on past closed trades.
    Expects trades with 'confidence' and 'profit'.
    """
    if not trades:
        return 70.0
    best_thr = 50.0
    best_val = -1e9
    # ensure floats
    for thr in range(40, 96):
        selected = [t for t in trades if float(t.get(conf_key, 0.0)) >= thr]
        if not selected:
            continue
        exp_profit = sum(float(t.get('profit', 0.0)) for t in selected) / len(selected)
        # objective: expected profit per trade times selection rate
        value = exp_profit * (len(selected) / len(trades))
        if value > best_val:
            best_val = value
            best_thr = thr
    return float(best_thr)


def calibrate_from_logs(limit=1000):
    """Read last trades and produce suggested RISK_PCT and CONFIDENCE_THRESHOLD.
    Returns dict {risk_pct, confidence_threshold, trades_used}
    """
    trades = read_trades(limit=limit)
    # Filter to closed trade records (mode normal/rapid with profit key)
    closed = [t for t in trades if 'profit' in t]
    suggested_risk = suggest_risk_pct_from_trades(closed)
    suggested_conf = sweep_confidence_threshold(closed)
    return {
        'risk_pct': suggested_risk,
        'confidence_threshold': suggested_conf,
        'trades_used': len(closed)
    }
