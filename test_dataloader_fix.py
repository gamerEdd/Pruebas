#!/usr/bin/env python3
# Test del DataLoader fix

import sys
sys.path.insert(0, '.')

from data_loader_trainer import DataLoaderTrainer, initialize_data_loader

print("[TEST] Probando DataLoader con fix de broadcasting...")

try:
    # Inicializar data loader
    print("\n[STEP 1] Inicializando DataLoader...")
    data_loader = initialize_data_loader(
        symbol="XAUUSD",
        generate_if_missing=True,
        num_snapshots=1000
    )
    
    if not data_loader:
        print("[ERROR] No se pudo inicializar DataLoader")
        sys.exit(1)
    
    print(f"[OK] DataLoader inicializado")
    print(f"     Snapshots listos: {len(data_loader.market_snapshots)}")
    
    # Obtener features
    print("\n[STEP 2] Extrayendo features de entrenamiento...")
    features = data_loader.get_training_features(window_size=100)
    
    if not features:
        print("[ERROR] No se extrajeron features")
        sys.exit(1)
    
    print(f"[OK] Features extraidos:")
    for key, val in features.items():
        if isinstance(val, (int, float)):
            print(f"     {key}: {val:.4f}")
        else:
            print(f"     {key}: {val}")
    
    # Obtener snapshots
    print("\n[STEP 3] Obteniendo ultimos snapshots...")
    snapshots = data_loader.get_latest_snapshots(num_bars=50)
    print(f"[OK] Obtenidos {len(snapshots)} snapshots")
    
    print("\n" + "="*60)
    print("[OK] DATALOADER COMPLETAMENTE FUNCIONAL")
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
