#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEST - Operaciones Rápidas
Simula el flujo de Operaciones Rápidas sin GUI
"""

import MetaTrader5 as mt5
import time
from datetime import datetime

print("="*60)
print("TEST - OPERACIONES RÁPIDAS")
print("="*60)

# ===== PRUEBA 1: Conexión MT5 =====
print("\n[1/6] Conectando a MT5...")
if mt5.initialize():
    print("✅ MT5 inicializado")
    info = mt5.terminal_info()
    print(f"   - Balance: ${info.balance}")
    print(f"   - Conexión: {'CONECTADO' if info.connected else 'DESCONECTADO'}")
else:
    print("❌ Error inicializando MT5")
    exit(1)

# ===== PRUEBA 2: Verificar símbolo =====
print("\n[2/6] Verificando símbolo GOLD...")
symbol_info = mt5.symbol_info("GOLD")
if symbol_info:
    print(f"✅ GOLD encontrado")
    print(f"   - Bid: {symbol_info.bid}")
    print(f"   - Ask: {symbol_info.ask}")
else:
    print("❌ GOLD no encontrado en MT5")
    symbols = mt5.symbols_get(group="*GOLD*")
    print(f"   Símbolos disponibles con GOLD: {[s.name for s in symbols[:5]]}")
    exit(1)

# ===== PRUEBA 3: Obtener tick =====
print("\n[3/6] Obteniendo tick actual...")
tick = mt5.symbol_info_tick("GOLD")
if tick:
    print(f"✅ Tick obtenido")
    print(f"   - Bid: {tick.bid}")
    print(f"   - Ask: {tick.ask}")
    midpoint = (tick.bid + tick.ask) / 2
    print(f"   - Midpoint: {midpoint:.5f}")
else:
    print("❌ No se pudo obtener tick")
    exit(1)

# ===== PRUEBA 4: Simular orden en DEMO =====
print("\n[4/6] Simulando parámetros de orden...")
volume = 0.05
magic = 123456
print(f"✅ Parámetros:")
print(f"   - Símbolo: GOLD")
print(f"   - Tipo: BUY")
print(f"   - Volumen: {volume}")
print(f"   - Precio: {midpoint:.5f}")
print(f"   - Magic: {magic}")

# Construir request
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "GOLD",
    "volume": volume,
    "type": mt5.ORDER_BUY,
    "price": midpoint,
    "magic": magic,
    "comment": "RapidOp_BUY_TEST"
}

print("\n[5/6] Enviando orden (solo en DEMO)...")
result = mt5.order_send(request)

print(f"📋 Resultado:")
print(f"   - Return Code: {result.retcode}")
print(f"   - Order: {result.order if hasattr(result, 'order') else 'N/A'}")
print(f"   - Comment: {result.comment if hasattr(result, 'comment') else 'N/A'}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"✅ ORDEN EJECUTADA (Ticket: {result.order})")
elif result.retcode == mt5.TRADE_RETCODE_MARKET_CLOSED:
    print(f"⚠️  Mercado cerrado")
elif result.retcode == mt5.TRADE_RETCODE_NO_MONEY:
    print(f"⚠️  Sin saldo")
else:
    print(f"❌ Error: {result.comment if hasattr(result, 'comment') else result.retcode}")

# ===== PRUEBA 6: Analizar retcodes comunes =====
print("\n[6/6] Retcodes comunes en MT5:")
print(f"   TRADE_RETCODE_DONE={mt5.TRADE_RETCODE_DONE} (Éxito)")
print(f"   TRADE_RETCODE_MARKET_CLOSED={mt5.TRADE_RETCODE_MARKET_CLOSED} (Mercado cerrado)")
print(f"   TRADE_RETCODE_NO_MONEY={mt5.TRADE_RETCODE_NO_MONEY} (Sin saldo)")
print(f"   TRADE_RETCODE_INVALID_PRICE={mt5.TRADE_RETCODE_INVALID_PRICE} (Precio inválido)")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)

mt5.shutdown()
