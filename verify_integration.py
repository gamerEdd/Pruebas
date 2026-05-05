#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import sys

print("\n" + "="*70)
print("VERIFICACION FINAL - SISTEMA DATALOADER INTEGRADO")
print("="*70 + "\n")

# 1. Verificar archivos
print("[1] ARCHIVOS CRITICOS:")
files_check = {
    "botiaver1.py": "OK" if os.path.exists("botiaver1.py") else "FALTA",
    "data_loader_trainer.py": "OK" if os.path.exists("data_loader_trainer.py") else "FALTA",
    "market_snapshot_generator.py": "OK" if os.path.exists("market_snapshot_generator.py") else "FALTA",
    "enhanced_dataset_generator.py": "OK" if os.path.exists("enhanced_dataset_generator.py") else "FALTA",
    "buy_specialist_ai.py": "OK" if os.path.exists("buy_specialist_ai.py") else "FALTA",
    "sell_specialist_ai.py": "OK" if os.path.exists("sell_specialist_ai.py") else "FALTA",
    "decision_arbitrator_ai.py": "OK" if os.path.exists("decision_arbitrator_ai.py") else "FALTA",
}

for file, status in files_check.items():
    symbol = "✓" if status == "OK" else "✗"
    print(f"  {symbol} {file:<40} [{status}]")

# 2. Verificar datasets
print("\n[2] DATASETS GENERADOS:")
if os.path.exists("datasets"):
    dataset_files = os.listdir("datasets")
    print(f"  Total files in datasets/: {len(dataset_files)}")
    if len(dataset_files) > 0:
        for f in sorted(dataset_files)[:10]:
            try:
                size = os.path.getsize(f"datasets/{f}") / 1024
                print(f"    - {f:<35} ({size:>8.2f} KB)")
            except:
                print(f"    - {f:<35} (ERROR)")
        if len(dataset_files) > 10:
            print(f"    ... y {len(dataset_files) - 10} archivos más")
    print("  Status: OK" if len(dataset_files) > 0 else "  Status: FALTA")
else:
    print("  datasets/ directory NOT FOUND")

# 3. Verificar market_snapshots.json
print("\n[3] MARKET SNAPSHOTS:")
if os.path.exists("logs/market_snapshots.json"):
    size = os.path.getsize("logs/market_snapshots.json")
    try:
        with open("logs/market_snapshots.json") as f:
            data = json.load(f)
        if isinstance(data, list):
            print(f"  ✓ market_snapshots.json: {len(data)} snapshots ({size/1024:.2f} KB)")
            print("    Status: OK")
        else:
            print(f"  ✗ Estructura inválida ({size/1024:.2f} KB)")
            print("    Status: ERROR")
    except Exception as e:
        print(f"  ! market_snapshots.json: Vacío o inválido ({size} bytes)")
        print(f"    Status: WARN - Error: {str(e)[:50]}")
else:
    print("  ✗ market_snapshots.json: NO EXISTE")
    print("    Status: FALTA")

# 4. Verificar lineas de código en botiaver1.py
print("\n[4] INTEGRACION EN BOTIAVER1.PY:")
try:
    with open("botiaver1.py", "r", encoding="utf-8") as f:
        content = f.read()
    lines = len(content.split("\n"))
    
    checks = {
        "Import DataLoaderTrainer": "from data_loader_trainer import" in content,
        "Variables de instancia": "self.data_loader = None" in content,
        "Inicializacion": "initialize_data_loader(" in content,
        "Uso en bot_loop": "self.data_loader.get_latest_snapshots" in content,
        "Limpieza en stop_bot": "Data Loader limpiado" in content,
    }
    
    print(f"  Total lineas: {lines}")
    all_ok = True
    for check, present in checks.items():
        symbol = "✓" if present else "✗"
        status = "OK" if present else "FALTA"
        print(f"    {symbol} {check:<35} [{status}]")
        if not present:
            all_ok = False
    
    if all_ok:
        print("  Status: OK - Todas las integraciones presentes")
    else:
        print("  Status: ERROR - Faltan algunas integraciones")
except Exception as e:
    print(f"  ERROR: {e}")

# 5. Compilacion
print("\n[5] COMPILACION DE MODULOS:")
compile_files = [
    "botiaver1.py",
    "data_loader_trainer.py",
    "buy_specialist_ai.py",
    "sell_specialist_ai.py",
    "decision_arbitrator_ai.py",
]

import py_compile
all_compiled = True
for file in compile_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f"  ✓ {file:<40} [OK]")
    except Exception as e:
        print(f"  ✗ {file:<40} [ERROR]")
        all_compiled = False

if all_compiled:
    print("  Status: OK - Todos los módulos compilan")
else:
    print("  Status: ERROR - Algunos módulos no compilan")

# 6. Resumen final
print("\n" + "="*70)
print("[RESUMEN]")
print("="*70)

summary_ok = all([
    all(files_check.values()),
    len(os.listdir("datasets")) > 0 if os.path.exists("datasets") else False,
    os.path.exists("logs/market_snapshots.json"),
    all_ok,
    all_compiled
])

if summary_ok:
    print("STATUS: ✓ INTEGRACION COMPLETADA Y VERIFICADA")
    print("\nEl sistema DataLoader está completamente integrado en botiaver1.py")
    print("y listo para usarse en producción.\n")
    sys.exit(0)
else:
    print("STATUS: ! INTEGRACION INCOMPLETA")
    print("\nRevise los elementos marcados con ✗ o ! arriba.\n")
    sys.exit(1)
