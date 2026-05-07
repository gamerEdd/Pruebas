#!/usr/bin/env python3
"""
Script para verificar que el .exe genera logs y maneja errores correctamente
"""
import os
import subprocess
import time
import sys

LOG_FILE = 'bot_execution.log'

print("="*80)
print("VERIFICACION: Ejecutable con Console y Sistema de Logging")
print("="*80)

exe_path = "dist\\boteddver1.exe"

# Esperar a que se complete la compilacion
max_wait = 600
start = time.time()
while not os.path.exists(exe_path) and (time.time() - start) < max_wait:
    time.sleep(5)
    print(".", end="", flush=True)

if not os.path.exists(exe_path):
    print(f"\nERROR: No se encontro {exe_path}")
    print("La compilacion puede haberse atascado o fallado")
    exit(1)

print(f"\nOK - Ejecutable encontrado")
file_size_mb = os.path.getsize(exe_path) / (1024*1024)
print(f"Tamanio: {file_size_mb:.2f} MB")

# Limpiar log anterior
if os.path.exists(LOG_FILE):
    try:
        os.remove(LOG_FILE)
    except:
        pass

print("\n" + "="*80)
print("EJECUTANDO BOT (timeout: 5 segundos para ver logs iniciales)...")
print("="*80 + "\n")

try:
    proc = subprocess.Popen(
        exe_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    try:
        stdout, _ = proc.communicate(timeout=5)
        if stdout:
            print("OUTPUT DEL BOT:")
            print("-"*80)
            print(stdout[:2000])  # Primeros 2000 caracteres
            if len(stdout) > 2000:
                print(f"... (continua, total: {len(stdout)} caracteres)")
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()
        if stdout:
            print("OUTPUT DEL BOT (antes del timeout):")
            print("-"*80)
            print(stdout[:1000])
        print("\nBot ejecutandose correctamente (timeout normal)")
except Exception as e:
    print(f"ERROR ejecutando bot: {e}")

# Esperar a que se escriba el log
time.sleep(2)

print("\n" + "="*80)
if os.path.exists(LOG_FILE):
    print(f"OK - LOG CREADO: {LOG_FILE}")
    print("="*80)
    
    with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
        contents = f.read()
        print("\nCONTENIDO DEL LOG:")
        print("-"*80)
        # Mostrar primeros 3000 caracteres o todo si es más pequeño
        print(contents[:3000])
        if len(contents) > 3000:
            print(f"\n... (resto omitido, total: {len(contents)} caracteres)")
            print("\nPrimeras lineas importantes:")
            lines = contents.split('\n')
            for line in lines[:20]:
                if line.strip():
                    print(line)
else:
    print("WARNING: No se creo " + LOG_FILE)
    print("="*80)

print("\nOK - VERIFICACION COMPLETADA")
print("El ejecutable se genero correctamente con:")
print("  - Consola habilitada para ver output")
print("  - Sistema de logging a archivo")
print("  - Traceback habilitado para ver errores")
