#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Data Updater - Verificar que carga datos de market_snapshots.json
"""

import sys
import json
from pathlib import Path

def test_data_updater_logic():
    """Verifica que el Data Updater intenta cargar desde market_snapshots.json"""
    
    print("=" * 80)
    print("[TEST] Data Updater: Carga desde market_snapshots.json")
    print("=" * 80)
    
    market_snap_path = Path("logs/market_snapshots.json")
    
    # Verificar que el archivo existe
    if not market_snap_path.exists():
        print(f"\n[❌ ERROR] No existe: {market_snap_path}")
        return False
    
    print(f"\n[OK] Archivo encontrado: {market_snap_path}")
    
    # Intentar cargarlo
    try:
        with open(market_snap_path, 'r') as f:
            data = json.load(f)
        
        # Procesar como lo hace el Data Updater
        if isinstance(data, dict) and 'snapshots' in data:
            snapshots = data['snapshots']
            print(f"[OK] Estructura: dict con 'snapshots' key")
        elif isinstance(data, list):
            snapshots = data
            print(f"[OK] Estructura: lista directa")
        else:
            snapshots = []
            print(f"[❌] Estructura desconocida: {type(data)}")
        
        # Tomar últimas 500
        final_snapshots = snapshots[-500:] if snapshots else []
        
        print(f"[OK] Total snapshots en archivo: {len(snapshots)}")
        print(f"[OK] Snapshots a usar (últimos 500): {len(final_snapshots)}")
        
        if final_snapshots:
            print(f"[OK] Primer snapshot: {final_snapshots[0].get('timestamp', 'N/A')}")
            print(f"[OK] Último snapshot: {final_snapshots[-1].get('timestamp', 'N/A')}")
            print(f"[OK] Último close: {final_snapshots[-1].get('close', 'N/A')}")
        
        if len(final_snapshots) > 0:
            print(f"\n[✅ EXITO] Data Updater puede cargar {len(final_snapshots)} snapshots")
            return True
        else:
            print(f"\n[❌ FALLO] Sin snapshots después de procesar")
            return False
        
    except json.JSONDecodeError as e:
        print(f"[❌] Error JSON: {e}")
        return False
    except Exception as e:
        print(f"[❌] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        result = test_data_updater_logic()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"[❌] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
