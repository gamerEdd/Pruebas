"""Wrappers seguros para llamadas a MetaTrader5.
Convierte formatos (tuplas/arrays/dicts) a listas de dicts homogéneas
y provee funciones fallback cuando ciertas APIs no están presentes.
"""
from datetime import datetime
import MetaTrader5 as mt5

# Ensure a RateLike wrapper is available for compatibility with code
# that expects numeric indexing (r[4] -> 'close'). Prefer mt5.RateLike
# if provided by the shim; otherwise provide a lightweight fallback.
if hasattr(mt5, 'RateLike'):
    RateLike = mt5.RateLike
else:
    class RateLike(dict):
        _idx_map = {
            0: 'time', 1: 'open', 2: 'high', 3: 'low', 4: 'close',
            5: 'tick_volume', 6: 'spread', 7: 'real_volume'
        }
        def __getitem__(self, key):
            if isinstance(key, int):
                return super().get(self._idx_map.get(key))
            return super().__getitem__(key)


def _rate_tuple_to_dict(t):
    # Espera tupla: (time, open, high, low, close, tick_volume, spread, real_volume)
    return {
        'time': int(t[0]),
        'open': float(t[1]),
        'high': float(t[2]),
        'low': float(t[3]),
        'close': float(t[4]),
        'tick_volume': int(t[5]) if len(t) > 5 else 0,
        'spread': int(t[6]) if len(t) > 6 else 0,
        'real_volume': int(t[7]) if len(t) > 7 else 0,
    }


def _ensure_rates_list(rates):
    if rates is None:
        return None
    out = []
    for r in rates:
        if isinstance(r, (list, tuple)):
            out.append(RateLike(_rate_tuple_to_dict(r)))
        elif isinstance(r, dict):
            out.append(RateLike(r))
        else:
            # try attribute access (numpy recarray)
            try:
                out.append(RateLike({
                    'time': int(r.time),
                    'open': float(r.open),
                    'high': float(r.high),
                    'low': float(r.low),
                    'close': float(r.close),
                    'tick_volume': int(getattr(r, 'tick_volume', 0)),
                    'spread': int(getattr(r, 'spread', 0)),
                    'real_volume': int(getattr(r, 'real_volume', 0)),
                }))
            except Exception:
                # último recurso: try indexing like tuple
                try:
                    out.append(RateLike(_rate_tuple_to_dict(r)))
                except Exception:
                    continue
    return out


def copy_rates_from_pos_safe(symbol, timeframe, pos, count):
    # Try the available mt5 functions in order
    if hasattr(mt5, 'copy_rates_from_pos'):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, pos, count)
        return _ensure_rates_list(rates)
    if hasattr(mt5, 'copy_rates_from'):
        rates = mt5.copy_rates_from(symbol, timeframe, pos, count)
        return _ensure_rates_list(rates)
    if hasattr(mt5, 'copy_rates_range'):
        # approximate using range of minutes
        from datetime import timedelta
        now = datetime.now()
        date_from = now - timedelta(minutes=count)
        rates = mt5.copy_rates_range(symbol, timeframe, date_from, now)
        return _ensure_rates_list(rates)
    return None


def copy_rates_range_safe(symbol, timeframe, date_from, date_to):
    if hasattr(mt5, 'copy_rates_range'):
        rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        return _ensure_rates_list(rates)
    # fallback to from_pos
    delta = date_to - date_from
    minutes = int(delta.total_seconds() // 60)
    return copy_rates_from_pos_safe(symbol, timeframe, 0, max(1, minutes))


def _tick_from_rate(rate):
    return {
        'time': rate.get('time'),
        'bid': rate.get('low'),
        'ask': rate.get('close'),
        'last': rate.get('close'),
        'volume': int(rate.get('tick_volume', 1))
    }


def _ensure_ticks_list(ticks):
    if ticks is None:
        return None
    out = []
    for t in ticks:
        if isinstance(t, (list, tuple)):
            # common structured tuple: (time, bid, ask, last, volume)
            try:
                out.append({
                    'time': int(t[0]),
                    'bid': float(t[1]),
                    'ask': float(t[2]) if len(t) > 2 else float(t[1]),
                    'last': float(t[3]) if len(t) > 3 else float(t[2]) if len(t) > 2 else float(t[1]),
                    'volume': int(t[4]) if len(t) > 4 else 1
                })
            except Exception:
                continue
        elif isinstance(t, dict):
            out.append(t)
        else:
            try:
                out.append({
                    'time': int(t.time),
                    'bid': float(t.bid),
                    'ask': float(t.ask),
                    'last': float(getattr(t, 'last', t.ask)),
                    'volume': int(getattr(t, 'volume', 1))
                })
            except Exception:
                continue
    return out


def copy_ticks_from_safe(symbol, datetime_from, count, flags=None):
    if hasattr(mt5, 'copy_ticks_from'):
        ticks = mt5.copy_ticks_from(symbol, datetime_from, count, flags) if flags is not None else mt5.copy_ticks_from(symbol, datetime_from, count)
        return _ensure_ticks_list(ticks)
    # fallback to rates
    rates = copy_rates_from_pos_safe(symbol, mt5.TIMEFRAME_M1 if hasattr(mt5, 'TIMEFRAME_M1') else 1, 0, max(1, int(count)))
    if rates:
        return [_tick_from_rate(r) for r in rates]
    return None


def copy_ticks_range_safe(symbol, datetime_from, datetime_to, flags=None):
    if hasattr(mt5, 'copy_ticks_range'):
        ticks = mt5.copy_ticks_range(symbol, datetime_from, datetime_to, flags) if flags is not None else mt5.copy_ticks_range(symbol, datetime_from, datetime_to)
        return _ensure_ticks_list(ticks)
    # fallback to rates
    rates = copy_rates_range_safe(symbol, mt5.TIMEFRAME_M1 if hasattr(mt5, 'TIMEFRAME_M1') else 1, datetime_from, datetime_to)
    if rates:
        return [_tick_from_rate(r) for r in rates]
    return None


def get_ticks_safe(symbol, limit=400, log=None):
    """Higher-level helper: try range -> from -> rates -> cache"""
    from datetime import datetime, timedelta
    now = datetime.now()
    try:
        # try 3-hour range
        time_from = now - timedelta(hours=3)
        ticks = copy_ticks_range_safe(symbol, time_from, now, flags=getattr(mt5, 'COPY_TICKS_ALL', None))
        if ticks:
            return ticks[-limit:]
    except Exception as e:
        if log:
            log(f"[mt5_safe] copy_ticks_range_safe error: {e}", 'debug')

    try:
        ticks = copy_ticks_from_safe(symbol, now, limit)
        if ticks:
            return ticks[-limit:]
    except Exception as e:
        if log:
            log(f"[mt5_safe] copy_ticks_from_safe error: {e}", 'debug')

    try:
        # fallback: generate from rates
        time_from = now - timedelta(hours=2)
        rates = copy_rates_range_safe(symbol, mt5.TIMEFRAME_M1 if hasattr(mt5, 'TIMEFRAME_M1') else 1, time_from, now)
        if rates:
            ticks = [_tick_from_rate(r) for r in rates]
            return ticks[-limit:]
    except Exception as e:
        if log:
            log(f"[mt5_safe] fallback rates->ticks error: {e}", 'debug')

    return None
