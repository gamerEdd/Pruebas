#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG SCRIPT: Verifica que el scheduler y microtrend estén funcionando
Ejecución: python debug_scheduler_issue.py
"""

import sys
import time
import json
import threading
from datetime import datetime

# Intenta cargar el bot
try:
    print("🔍 [DEBUG] Cargando módulos necesarios...", flush=True)
    import tkinter as tk
    from tkinter import ttk
    print("✅ tkinter cargado", flush=True)
except Exception as e:
    print(f"❌ Error cargando tkinter: {e}", flush=True)
    sys.exit(1)

print("""
╔════════════════════════════════════════════════════════════════╗
║  🔍 DEBUG SCHEDULER - Validación de Apertura Forzada           ║
║  ⏰ Espera 5 segundos para que el bot se inicialice...         ║
╚════════════════════════════════════════════════════════════════╝
""")

# Esperar a que el bot se inicialice
time.sleep(3)

print("""
📋 CHECKLIST DE VALIDACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Paso 1: Verifica que el bot esté corriendo en otra terminal
  - Comando: python boteddver1.py
  - Deberías ver logs: "[RESET] Scheduler: reapertura forzada activada"

✓ Paso 2: Verifica en los LOGS las siguientes líneas:
  
  [MICROTREND] Resultado: (BUY | SELL | FLAT)
  └─ Si ves esto = método está funcionando correctamente
  
  [CALIBRACIÓN] → indica que la validación se ejecutó
  [FINAL] Dirección a abrir: (BUY | SELL)
  └─ Si ves esto = decisión fue tomada

✓ Paso 3: Busca errores:
  [ERROR] microtrend_direction (NO debería aparecer)
  [ERROR] scheduler (NO debería aparecer)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 SI NO VES APERTURAS:

1. Verifica que ENABLE_FORCED_OPEN = True en config
2. Verifica FORCED_OPEN_MINUTES = 0.5 (30 segundos)
3. Revisa si hay [SCHEDULER] en los logs
4. Busca si dice "[ERROR] scheduler al ejecutar reapertura"

🔥 SOLUCIÓN RÁPIDA - Deshabilitar temporalmente calibración:

Si el scheduler no abre nada, la validación microtrend podría estar
causando silenciosamente una excepción. Para verificar:

Busca en boteddver1.py la línea:
    microtrend = self._microtrend_direction(symbol, bars=8, threshold=0.003)

Y reemplázala por:
    microtrend = 'FLAT'  # Temp: deshabilitar para debug

Luego reinicia el bot. Si ahora abre operaciones = es un problema en microtrend.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 INFORMACIÓN ÚTIL:

NORMAL: El scheduler intenta abrir cada 30 segundos (0.5 minutos)
- Deberías ver: [RESET] Scheduler: reapertura forzada activada
- Cada 30 segundos aproximadamente

SI VES:
[SCHEDULER] ⏱️ Próxima reapertura en 30s
└─ Todo está marchando bien, próxima apertura en 30 segundos

SI ERES FRUSTRATE - OPCIÓN NUCLEAR:

Abre boteddver1.py línea 736-737 y cambia:
    'ENABLE_FORCED_OPEN': tk.BooleanVar(value=True),      # → False
    'FORCED_OPEN_MINUTES': tk.DoubleVar(value=0.5),       # → 1.0

Eso desactiva forced opens y deja solo operaciones por señales.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

print("""
✅ Script de debug completado. Ahora verifica los LOGS del bot en otra terminal.

Busca líneas como:
[RESET] Scheduler: reapertura forzada activada
[MICROTREND] Resultado: BUY
[FINAL] Dirección a abrir: BUY
✅ ABRIENDO: BUY

Si NO ves estas líneas en ~30 segundos, hay un problema.
Reporta qué líneas SÍ ves en los logs.
""")
