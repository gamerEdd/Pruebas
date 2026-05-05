#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test rápido: Verificar que MT5 devuelve datos de cuenta correctamente
"""
import MetaTrader5 as mt5
from datetime import datetime

print(f"[{datetime.now().strftime('%H:%M:%S')}] Conectando a MT5...")

# Conectar
if mt5.initialize():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ MT5 inicializado")
    
    # Obtener información de cuenta
    account_info = mt5.account_info()
    
    if account_info is not None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ account_info obtenida:")
        print(f"\n  💰 Balance: ${float(getattr(account_info, 'balance', 0.0)):.2f}")
        print(f"  📊 Equity: ${float(getattr(account_info, 'equity', 0.0)):.2f}")
        print(f"  🛡️ Free Margin: ${float(getattr(account_info, 'margin_free', 0.0)):.2f}")
        print(f"  📍 Leverage: 1:{int(getattr(account_info, 'leverage', 0))}")
        print(f"\n[✅ ÉXITO] Los datos de MT5 se leen correctamente\n")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ account_info es None - MT5 no conectado")
    
    mt5.shutdown()
else:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error al inicializar MT5")
