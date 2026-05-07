#!/usr/bin/env python3
"""
Script de prueba para verificar que el .exe genera logs correctamente
"""
import os
import subprocess
import time
import sys

# Forzar UTF-8
sys.stdout.reconfigure(encoding='utf-8')

LOG_FILE = 'bot_execution.log'

print("="*80)
print("TEST: Ejecutable con Console y Logging")
print("="*80)

exe_path = "dist\\boteddver1.exe"

if not os.path.exists(exe_path):
    print(f"ERROR: No se encontro {exe_path}")
    print("Debes compilar primero: python build_exe.py --no-install")
    exit(1)

print(f"\nOK - Ejecutable encontrado: {exe_path}")
print(f"  Tamanio: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")

# Limpiar log anterior
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
    print(f"\nOK - Log anterior eliminado")

print("\n" + "="*80)
print("EJECUTANDO BOT (timeout: 5 segundos)...")
print("="*80 + "\n")

try:
    # Ejecutar el .exe con timeout de 5 segundos
    proc = subprocess.Popen(exe_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        stdout, _ = proc.communicate(timeout=5)
        print(stdout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()
        print(stdout)
        print("\nTimeout - Bot ejecutandose... (detenido despues de 5 segundos)")
except Exception as e:
    print(f"ERROR ejecutando bot: {e}")

# Verificar si se creó el log
time.sleep(1)

if os.path.exists(LOG_FILE):
    print("\n" + "="*80)
    print(f"OK - LOG CREADO: {LOG_FILE}")
    print("="*80)
    
    with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
        contents = f.read()
        print("\nCONTENIDO DEL LOG:")
        print("-"*80)
        print(contents[:2000])  # Primeros 2000 caracteres
        if len(contents) > 2000:
            print(f"\n... (archivo completo: {len(contents)} caracteres)")
else:
    print(f"\nWARNING: No se creo {LOG_FILE}")

print("\n" + "="*80)
print("OK - TEST COMPLETADO")
print("="*80)
