import json
import sys

# Revisar market_snapshots.json
try:
    with open("logs/market_snapshots.json") as f:
        data = json.load(f)
        if isinstance(data, dict) and "snapshots" in data:
            snaps = data["snapshots"]
            print(f"[STRUCTURE] Tipo: dict con 'snapshots'")
            print(f"[DATA] Total: {len(snaps)} snapshots")
            if len(snaps) > 0:
                first = snaps[0]
                last = snaps[-1]
                print(f"[FIRST] Close: {first.get('price', {}).get('close')}")
                print(f"[LAST] Close: {last.get('price', {}).get('close')}")
                print(f"[KEYS] {list(first.keys())}")
        elif isinstance(data, list):
            print(f"[STRUCTURE] Tipo: lista")
            print(f"[DATA] Total: {len(data)} snapshots")
            if len(data) > 0:
                first = data[0]
                last = data[-1]
                print(f"[FIRST] Keys: {list(first.keys())[:5]}")
                print(f"[LAST] Keys: {list(last.keys())[:5]}")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Revisar cómo se carga en botiaver1
print("\n[CHECKING] reload_market_snapshots() en botiaver1.py...")
try:
    with open("botiaver1.py") as f:
        content = f.read()
        if "def reload_market_snapshots" in content:
            # Encontrar la función
            start = content.find("def reload_market_snapshots")
            end = content.find("\n    def ", start + 1)
            func = content[start:end]
            # Buscar si convierte a lista
            if "json.load" in func:
                print("[OK] Usa json.load()")
            if "['snapshots']" in func:
                print("[OK] Accede a ['snapshots']")
            elif ".get('snapshots')" in func:
                print("[OK] Usa .get('snapshots')")
            else:
                print("[WARN] No parece acceder correctamente a snapshots")
except Exception as e:
    print(f"[ERROR] {e}")
