import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
TRADE_FILE = os.path.join(LOG_DIR, 'trades.jsonl')
SUMMARY_FILE = os.path.join(LOG_DIR, 'trades_summary.json')
MARKET_FILE = os.path.join(LOG_DIR, 'market_snapshots.json')


def _append_line(path, line):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def log_trade(trade: dict):
    """Append a trade record as a JSON line and update summary."""
    # Ensure timestamp
    if 'timestamp' not in trade:
        trade['timestamp'] = datetime.now().isoformat()

    try:
        _append_line(TRADE_FILE, json.dumps(trade, ensure_ascii=False))
    except Exception:
        # Best-effort: ignore logging errors
        pass

    # Update summary aggregates
    try:
        summary = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_profit': 0.0,
            'last_update': datetime.now().isoformat()
        }
        if os.path.exists(SUMMARY_FILE):
            try:
                with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
            except Exception:
                pass

        summary['total_trades'] = summary.get('total_trades', 0) + 1
        profit = float(trade.get('profit', 0.0))
        summary['total_profit'] = float(summary.get('total_profit', 0.0)) + profit
        
        # ⭐ FIX: Separar ganancias reales, pérdidas y breakeven
        if profit > 0:  # Ganancia REAL (> 0, no >= 0)
            summary['wins'] = summary.get('wins', 0) + 1
        elif profit < 0:  # Pérdida REAL
            summary['losses'] = summary.get('losses', 0) + 1
        else:  # Exactamente $0 - breakeven
            summary['breakeven'] = summary.get('breakeven', 0) + 1
        
        summary['last_update'] = datetime.now().isoformat()

        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def read_trades(limit=None):
    """Read logged trades (generator)."""
    if not os.path.exists(TRADE_FILE):
        return []
    res = []
    with open(TRADE_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                res.append(json.loads(line))
            except Exception:
                continue
    return res


def append_json_line(obj):
    """Append an arbitrary JSON object as a line to the trades file."""
    try:
        if 'timestamp' not in obj:
            obj['timestamp'] = datetime.now().isoformat()
        _append_line(TRADE_FILE, json.dumps(obj, ensure_ascii=False))
    except Exception:
        pass


def write_market_snapshots(list_of_snapshots, symbol='XAUUSD', max_snapshots=1440):
    """Write/update market snapshots with HISTORICAL PERSISTENCE.
    
    ⭐ NUEVO: Instead of overwriting, APPENDS new snapshots to history.
    Maintains max_snapshots limit (rotates oldest data).
    
    Args:
        list_of_snapshots: List of snapshot dicts {timestamp, open, high, low, close, tick_volume}
        symbol: Symbol for metadata (default 'XAUUSD')
        max_snapshots: Max snapshots to keep (default 1440 = 24 hours M1)
    """
    try:
        # Read existing data (if any)
        existing_data = {}
        if os.path.exists(MARKET_FILE):
            try:
                with open(MARKET_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = {}
        
        # Ensure we have a proper structure
        if not isinstance(existing_data, dict) or "snapshots" not in existing_data:
            existing_data = {
                "metadata": {
                    "symbol": symbol,
                    "timeframe": "M1",
                    "retention_hours": 24,
                    "max_snapshots": max_snapshots
                },
                "snapshots": []
            }
        
        # Append new snapshots (avoid duplicates by timestamp)
        existing_snapshots = existing_data.get("snapshots", [])
        existing_timestamps = {s.get('timestamp') for s in existing_snapshots}
        
        for snap in list_of_snapshots:
            if snap.get('timestamp') not in existing_timestamps:
                existing_snapshots.append(snap)
                existing_timestamps.add(snap.get('timestamp'))
        
        # Rotate: keep only last max_snapshots
        if len(existing_snapshots) > max_snapshots:
            existing_snapshots = existing_snapshots[-max_snapshots:]
        
        # Update metadata
        if len(existing_snapshots) > 0:
            existing_data["metadata"]["snapshot_count"] = len(existing_snapshots)
            existing_data["metadata"]["last_update"] = datetime.now().isoformat()
            existing_data["metadata"]["oldest_snapshot"] = existing_snapshots[0].get('timestamp')
            existing_data["metadata"]["newest_snapshot"] = existing_snapshots[-1].get('timestamp')
        
        existing_data["snapshots"] = existing_snapshots
        
        # Write back
        with open(MARKET_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def append_market_snapshot(snapshot, symbol='XAUUSD', max_snapshots=1440):
    """Append a SINGLE market snapshot to historical file.
    
    ⭐ CONVENIENTE para agregar snapshots individuales cada 4 minutos.
    
    Args:
        snapshot: Dict {timestamp, open, high, low, close, tick_volume}
        symbol: Symbol for metadata
        max_snapshots: Max snapshots to keep
    """
    write_market_snapshots([snapshot], symbol=symbol, max_snapshots=max_snapshots)


def rotate_market_snapshots(max_snapshots=1440):
    """Manually rotate (trim) market snapshots to max_snapshots limit.
    
    Returns: (old_count, new_count, removed_count)
    """
    try:
        if not os.path.exists(MARKET_FILE):
            return (0, 0, 0)
        
        with open(MARKET_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict) or "snapshots" not in data:
            return (0, 0, 0)
        
        snapshots = data.get("snapshots", [])
        old_count = len(snapshots)
        
        if old_count <= max_snapshots:
            return (old_count, old_count, 0)
        
        # Trim to max_snapshots
        snapshots = snapshots[-max_snapshots:]
        data["snapshots"] = snapshots
        data["metadata"]["snapshot_count"] = len(snapshots)
        if snapshots:
            data["metadata"]["oldest_snapshot"] = snapshots[0].get('timestamp')
        
        with open(MARKET_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return (old_count, len(snapshots), old_count - len(snapshots))
    except Exception:
        return (0, 0, 0)


def read_market_snapshots():
    """Read market snapshots JSON file, return list or [] if missing."""
    try:
        if not os.path.exists(MARKET_FILE):
            return []
        with open(MARKET_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Si es dict con "snapshots", extrae el array
            if isinstance(data, dict) and "snapshots" in data:
                return data["snapshots"]
            # Si ya es lista, devuelve directamente
            elif isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def get_market_snapshots_metadata():
    """Read and return METADATA from market snapshots file.
    
    Returns: Dict with metadata or empty dict if file doesn't exist.
    """
    try:
        if not os.path.exists(MARKET_FILE):
            return {}
        with open(MARKET_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and "metadata" in data:
                return data["metadata"]
            return {}
    except Exception:
        return {}
