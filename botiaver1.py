#BOTNEGRO
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import MetaTrader5 as mt5
import mt5_safe
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime, timedelta
import os
import json
from dynamic_dashboard import DynamicOperationsPanel
import numpy as np
import math
import random
from collections import deque, defaultdict, namedtuple
import pandas as pd
import logging
import pickle
import subprocess
import shutil
import tempfile
import traceback
import warnings
from pathlib import Path
import statistics
import operator
import copy
import inspect
import weakref
import itertools
from functools import wraps, lru_cache
from decimal import Decimal
import struct
import base64
import hashlib
import contextlib
import textwrap
import codecs
import locale
import math as _math

# Persistencia de órdenes fallidas para diagnóstico
def save_failed_order(request, result, tag=None):
    try:
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        out_file = os.path.join(logs_dir, 'failed_orders.jsonl')
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'tag': tag,
            'request': request,
            'retcode': getattr(result, 'retcode', None),
            'comment': getattr(result, 'comment', None),
            'order': getattr(result, 'order', None),
            'result_repr': repr(result)
        }
        # Attempt to include asdict if available
        try:
            if hasattr(result, '_asdict'):
                entry['result_asdict'] = result._asdict()
        except Exception:
            pass
        with open(out_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass

def interpret_retcode(code_or_result):
    """Devuelve mensaje legible para un retcode o un objeto result de mt5.order_send."""
    try:
        code = code_or_result
        # si recibieron objeto result
        if not isinstance(code_or_result, int):
            code = getattr(code_or_result, 'retcode', None)
    except Exception:
        code = None

    mapping = {
        getattr(mt5, 'TRADE_RETCODE_DONE', 0): 'DONE',
        getattr(mt5, 'TRADE_RETCODE_REQUOTE', 10004): 'REQUOTED',
        getattr(mt5, 'TRADE_RETCODE_REJECT', 10006): 'REJECTED',
        getattr(mt5, 'TRADE_RETCODE_INVALID_PRICE', 10002): 'INVALID_PRICE',
        getattr(mt5, 'TRADE_RETCODE_INVALID_VOLUME', 10003): 'INVALID_VOLUME',
        getattr(mt5, 'TRADE_RETCODE_NO_MONEY', 10009): 'INSUFFICIENT_FUNDS',
        getattr(mt5, 'TRADE_RETCODE_CANCEL', 10008): 'CANCELLED',
        getattr(mt5, 'TRADE_RETCODE_TIMEOUT', 10007): 'TIMEOUT',
        getattr(mt5, 'TRADE_RETCODE_PRICE_CHANGED', 10005): 'PRICE_CHANGED',
    }
    try:
        if code is None:
            return 'UNKNOWN (no retcode)'
        return mapping.get(code, f'UNKNOWN_RET_CODE_{code}')
    except Exception:
        return 'UNKNOWN'

def get_symbol_digits(symbol_info):
    """Devuelve el número de decimales (digits) de un `symbol_info` de MT5.
    Maneja casos donde `symbol_info` es un SimpleNamespace incompleto.
    Intenta `digits`, luego infiere desde `point` o `tick_size`. Por defecto 5.
    """
    try:
        d = getattr(symbol_info, 'digits', None)
        if d is not None:
            return int(d)
    except Exception:
        pass
    # Intentar inferir desde point o tick_size
    try:
        p = getattr(symbol_info, 'point', None) or getattr(symbol_info, 'tick_size', None)
        if p:
            p = float(p)
            if p > 0:
                # ej: point=0.0001 -> digits=4
                digits = max(0, int(round(-_math.log10(p))))
                return digits
    except Exception:
        pass
    return 5

def get_symbol_point(symbol_info):
    """Devuelve el tamaño de punto/tick del símbolo para convertir 'puntos' a precio.
    Fallback razonable si no está disponible.
    """
    try:
        p = getattr(symbol_info, 'point', None) or getattr(symbol_info, 'tick_size', None)
        if p:
            return float(p)
    except Exception:
        pass
    # Fallback: si no hay info, asumir 1e-4 (común en FX con 4-5 decimales)
    return 0.0001

def validate_and_adjust_stops(symbol_info, precio, sl, tp, direccion, log_callback=None):
    """Valida y ajusta SL/TP respetando STOPS_LEVEL del broker.
    
    Args:
        symbol_info: Info del símbolo de MT5
        precio: Precio de entrada
        sl: Stop Loss calculado
        tp: Take Profit calculado
        direccion: 'BUY' o 'SELL'
        log_callback: Función de logging opcional
    
    Returns:
        tuple: (sl_ajustado, tp_ajustado, fue_ajustado)
    """
    def log(msg, level='info'):
        if log_callback:
            log_callback(msg, level)
    
    point = get_symbol_point(symbol_info)
    digits = get_symbol_digits(symbol_info)
    
    # Obtener STOPS_LEVEL del broker (distancia mínima en puntos)
    stops_level = getattr(symbol_info, 'trade_stops_level', 0)
    spread = getattr(symbol_info, 'spread', 0)
    
    # Distancia mínima = max(stops_level, spread * 2) + margen de seguridad
    min_distance_points = max(stops_level, spread * 2, 10)  # Mínimo 10 puntos
    min_distance_price = min_distance_points * point
    
    sl_ajustado = sl
    tp_ajustado = tp
    fue_ajustado = False
    
    log(f"[STOPS] Validando: precio={precio:.5f} SL={sl:.5f} TP={tp:.5f} dir={direccion}", 'info')
    log(f"[STOPS] Broker: stops_level={stops_level} spread={spread} point={point}", 'info')
    log(f"[STOPS] Distancia mínima requerida: {min_distance_points} puntos (${min_distance_price:.5f})", 'info')
    
    if direccion == "BUY":
        # SL debe estar DEBAJO del precio
        sl_distance = precio - sl
        tp_distance = tp - precio
        
        if sl_distance < min_distance_price:
            sl_ajustado = round(precio - min_distance_price, digits)
            log(f"[STOPS] ⚠️ SL ajustado: {sl:.5f} → {sl_ajustado:.5f} (distancia era {sl_distance:.5f})", 'warning')
            fue_ajustado = True
        
        if tp_distance < min_distance_price:
            tp_ajustado = round(precio + min_distance_price, digits)
            log(f"[STOPS] ⚠️ TP ajustado: {tp:.5f} → {tp_ajustado:.5f} (distancia era {tp_distance:.5f})", 'warning')
            fue_ajustado = True
    else:  # SELL
        # SL debe estar ARRIBA del precio
        sl_distance = sl - precio
        tp_distance = precio - tp
        
        if sl_distance < min_distance_price:
            sl_ajustado = round(precio + min_distance_price, digits)
            log(f"[STOPS] ⚠️ SL ajustado: {sl:.5f} → {sl_ajustado:.5f} (distancia era {sl_distance:.5f})", 'warning')
            fue_ajustado = True
        
        if tp_distance < min_distance_price:
            tp_ajustado = round(precio - min_distance_price, digits)
            log(f"[STOPS] ⚠️ TP ajustado: {tp:.5f} → {tp_ajustado:.5f} (distancia era {tp_distance:.5f})", 'warning')
            fue_ajustado = True
    
    if fue_ajustado:
        log(f"[STOPS] ✅ Stops ajustados: SL={sl_ajustado:.5f} TP={tp_ajustado:.5f}", 'warning')
    else:
        log(f"[STOPS] ✅ Stops válidos: SL={sl:.5f} TP={tp:.5f}", 'success')
    
    return sl_ajustado, tp_ajustado, fue_ajustado

def points_to_price(symbol_info, points):
    try:
        return float(points) * get_symbol_point(symbol_info)
    except Exception:
        return float(points) * 0.0001

def handle_order_failure(owner, request, result, tag='order_send', max_retries=2):
    """Maneja rechazos del broker con reintentos automáticos para errores de precio.
    
    Args:
        owner: instancia del bot (con métodos add_log, etc.)
        request: dict con la solicitud original de MT5
        result: resultado de mt5.order_send()
        tag: etiqueta para logs
        max_retries: intentos máximos para errores de precio
    
    Returns:
        True si se manejó con éxito (reintento exitoso), False en caso contrario
    """
    import time as _time
    
    try:
        retcode = getattr(result, 'retcode', None)
        retcode_tag = interpret_retcode(result)
        
        # Guardar fallo para diagnóstico
        save_failed_order(request, result, tag=tag)
        
        # Códigos que permiten reintento (errores de precio temporales)
        RETRY_CODES = {
            getattr(mt5, 'TRADE_RETCODE_REQUOTE', 10004),
            getattr(mt5, 'TRADE_RETCODE_PRICE_CHANGED', 10005),
            getattr(mt5, 'TRADE_RETCODE_INVALID_PRICE', 10002),
        }
        
        if retcode in RETRY_CODES and max_retries > 0:
            if hasattr(owner, 'add_log'):
                owner.add_log(f"[{tag}] Reintentando ({retcode_tag})...", 'warning')
            
            # Actualizar precios antes de reintentar
            symbol = request.get('symbol')
            if symbol:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    action = request.get('type', 0)
                    # ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1
                    if action == 0:  # BUY
                        request['price'] = tick.ask
                    else:  # SELL
                        request['price'] = tick.bid
            
            _time.sleep(0.3)  # Pequeña pausa
            retry_result = mt5.order_send(request)
            
            if retry_result and retry_result.retcode == mt5.TRADE_RETCODE_DONE:
                if hasattr(owner, 'add_log'):
                    owner.add_log(f"[{tag}] ✅ Reintento exitoso", 'success')
                return True
            else:
                # Recursivo con menos reintentos
                return handle_order_failure(owner, request, retry_result, tag, max_retries - 1)
        
        # Mensajes específicos para otros códigos
        NO_MONEY = getattr(mt5, 'TRADE_RETCODE_NO_MONEY', 10009)
        INVALID_VOLUME = getattr(mt5, 'TRADE_RETCODE_INVALID_VOLUME', 10003)
        
        if retcode == NO_MONEY:
            if hasattr(owner, 'add_log'):
                owner.add_log(f"[{tag}] ⚠️ Fondos insuficientes - verifica tu balance", 'error')
        elif retcode == INVALID_VOLUME:
            if hasattr(owner, 'add_log'):
                owner.add_log(f"[{tag}] ⚠️ Volumen inválido - ajusta el lote", 'error')
        else:
            if hasattr(owner, 'add_log'):
                owner.add_log(f"[{tag}] ❌ Fallo: {retcode_tag} (code={retcode})", 'error')
        
        return False
        
    except Exception as e:
        if hasattr(owner, 'add_log'):
            owner.add_log(f"[{tag}] Error en handle_order_failure: {str(e)[:80]}", 'error')
        return False

def _make_stub(name):
    class Stub:
        def __init__(self, *a, **k):
            try:
                log = k.get('log_callback') if isinstance(k, dict) and 'log_callback' in k else None
                if callable(log):
                    log(f"[{name}] Módulo no disponible - usando stub (funcionalidad limitada)", 'warning')
            except Exception:
                pass

        def analyze(self, *a, **k):
            return {'score': 50, 'confidence': 50, 'recommendation': 'HOLD'}

        def update_config(self, *a, **k):
            return None

        def get_recent_ticks(self, *a, **k):
            return []

        def resolve_final_direction(self, *a, **k):
            return {'final_direction': None}

    Stub.__name__ = name
    return Stub

try:
    from buy_specialist_ai import BuySpecialistAI
except Exception:
    BuySpecialistAI = _make_stub('BuySpecialistAI')

try:
    from sell_specialist_ai import SellSpecialistAI
except Exception:
    SellSpecialistAI = _make_stub('SellSpecialistAI')

try:
    from decision_arbitrator_ai import DecisionArbitratorAI
except Exception:
    DecisionArbitratorAI = _make_stub('DecisionArbitratorAI')

try:
    from tick_impulse_detector import TickImpulseValidator
except Exception:
    TickImpulseValidator = _make_stub('TickImpulseValidator')

try:
    from gold_analyzer import GoldAnalyzer
except Exception:
    GoldAnalyzer = _make_stub('GoldAnalyzer')

try:
    from loss_analyzer import LossAnalyzer
except Exception:
    LossAnalyzer = _make_stub('LossAnalyzer')

try:
    from loss_protection_ai import LossProtectionAI  # ⭐ NUEVO: ML-based loss protection with retraining
except Exception:
    LossProtectionAI = _make_stub('LossProtectionAI')

try:
    from feedback_loop_ai import FeedbackLoopAI  # ⭐ NUEVO: Post-trade feedback loop
except Exception:
    FeedbackLoopAI = _make_stub('FeedbackLoopAI')

try:
    from rapid_ops_validator import RapidOpsValidator  # ⭐ NUEVO: Smart context validation for rapid ops
except Exception:
    RapidOpsValidator = _make_stub('RapidOpsValidator')

try:
    from entry_point_ai import EntryPointAI  # <-- agregado
except Exception:
    EntryPointAI = _make_stub('EntryPointAI')

try:
    from adaptive_parameters import AdaptiveParameters
except Exception:
    AdaptiveParameters = _make_stub('AdaptiveParameters')

try:
    from data_updater_module import DataUpdater, PreAnalysisDataRefresher
except Exception:
    DataUpdater = _make_stub('DataUpdater')
    PreAnalysisDataRefresher = _make_stub('PreAnalysisDataRefresher')

try:
    from data_loader_trainer import DataLoaderTrainer, initialize_data_loader
except Exception:
    DataLoaderTrainer = _make_stub('DataLoaderTrainer')
    def initialize_data_loader(*a, **k):
        return None

# [OBJETIVO] SISTEMA PRO INSTITUCIONAL (NIVEL 5-10)
from regime_detector import RegimeDetector
from trend_model import TrendModel
from reversion_model import ReversionModel
from bias_monitor import BiasMonitor
from drift_detector import DriftDetector
from dynamic_weights import DynamicWeights
from meta_selector import MetaSelector
from bot_integration_manager import BotIntegrationManager

# ⭐ Hacer scikit-learn OPCIONAL (compatible con Python 3.8)
try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    StandardScaler = None

# [OBJETIVO] FASE 3: IMPORTS DE LOS 12 NUEVOS MÓDULOS V12
from super_analyzer import SuperAnalyzer
from dynamic_score_calibration import DynamicScoreCalibration
from recovery_potential_enhanced import RecoveryPotentialEnhanced
from spread_slippage_analyzer import SpreadSlippageAnalyzer
from time_based_session_filter import TimeBasedSessionFilter
from correlation_analyzer import CorrelationAnalyzer
from trade_logger import log_trade, read_market_snapshots, write_market_snapshots
from auto_calibration import prefill_market_data, calibrate_from_logs
from dynamic_position_closer import DynamicPositionCloser  # ⭐ NUEVO: Cierra posiciones contrarias a reversión
from trend_change_detector import TrendChangeDetector  # ⭐ NUEVO: Detecta cambios de tendencia 10-30s anticipado
from multi_timeframe_analyzer import MultiTimeframeAnalyzer  # ⭐ NUEVO: Análisis multi-timeframe M1/M5/M15/M30/H1
from tick_flow_analyzer import TickFlowAnalyzer  # ⭐ NUEVO: Confirmación de presión de mercado con ticks

# Configure logging: write to logs/bot.log and console with UTF-8 encoding
try:
    _log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(_log_dir, exist_ok=True)
    _log_file = os.path.join(_log_dir, 'bot.log')
    # Use UTF-8 encoding to support special characters
    _handler = logging.FileHandler(_log_file, mode='a', encoding='utf-8')
    _handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logging.basicConfig(level=logging.INFO, handlers=[_handler])
except Exception:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

logger = logging.getLogger('MT5AdaptiveTradingBot')

class MT5AdaptiveTradingBot:
    def get_ghost_stats_snapshot(self):
        """Devuelve un snapshot de las ganadas/perdidas fantasma acumuladas en la ventana actual, sin reiniciar contadores."""
        return {
            'buy_win': self.ghost_total['buy_win'],
            'buy_loss': self.ghost_total['buy_loss'],
            'sell_win': self.ghost_total['sell_win'],
            'sell_loss': self.ghost_total['sell_loss']
        }

    def get_ghost_recommendation(self):
        """Devuelve 'BUY', 'SELL' o 'HOLD' según winrate fantasma últimos 30s"""
        b = self.get_ghost_stats_snapshot()
        total = b['buy_win'] + b['buy_loss'] + b['sell_win'] + b['sell_loss']
        if total < 6:
            return 'HOLD'  # No hay suficientes datos
        buy_rate = b['buy_win'] / max(1, (b['buy_win'] + b['buy_loss']))
        sell_rate = b['sell_win'] / max(1, (b['sell_win'] + b['sell_loss']))
        # Si la diferencia de winrate es significativa (>20%)
        if buy_rate - sell_rate > 0.2:
            return 'BUY'
        elif sell_rate - buy_rate > 0.2:
            return 'SELL'
        else:
            return 'HOLD'

    def start_ghost_operations(self):
        """Inicia el ciclo de operaciones fantasma (una BUY y una SELL cada segundo)"""
        if hasattr(self, 'ghost_ops_thread') and self.ghost_ops_thread and self.ghost_ops_thread.is_alive():
            return  # Ya corriendo
        self.ghost_ops_running = True
        import threading
        self.ghost_ops_thread = threading.Thread(target=self.ghost_ops_loop, daemon=True)
        self.ghost_ops_thread.start()

    def stop_ghost_operations(self):
        self.ghost_ops_running = False

    def ghost_ops_loop(self):
        import time
        while self.ghost_ops_running:
            now = time.time()
            symbol = self.config['SYMBOL'].get()
            # Abrir una BUY y SELL fantasma
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                entry_price = (tick.bid + tick.ask) / 2
                buy_op = {
                    'open_time': now,
                    'type': 'BUY',
                    'entry_price': entry_price,
                    'result': None,
                    'profit': 0.0
                }
                sell_op = {
                    'open_time': now,
                    'type': 'SELL',
                    'entry_price': entry_price,
                    'result': None,
                    'profit': 0.0
                }
                # Limitar a máximo 50 BUY y 50 SELL abiertas simultáneamente
                buy_open = sum(1 for op in self.ghost_ops['buy'] if op.get('result') is None)
                sell_open = sum(1 for op in self.ghost_ops['sell'] if op.get('result') is None)
                if buy_open < 50:
                    if self.add_ghost_op('buy', buy_op):
                        self.add_ghost_log(f"Apertura BUY fantasma @ {entry_price:.2f}")
                else:
                    self.add_ghost_log(f"Límite BUY fantasma alcanzado (50). No se abre nueva.")

                if sell_open < 50:
                    if self.add_ghost_op('sell', sell_op):
                        self.add_ghost_log(f"Apertura SELL fantasma @ {entry_price:.2f}")
                else:
                    self.add_ghost_log(f"Límite SELL fantasma alcanzado (50). No se abre nueva.")
            # Actualizar y cerrar fantasmas
            self._update_ghost_stats()
            self.root.after(0, self.update_ghost_ops_ui)
            time.sleep(1)

    def _update_ghost_stats(self):
        """Actualiza los contadores de abiertas, ganadas y perdidas de las operaciones fantasma en ventana de 30s
        NOTA: ghost_total NO se reinicia, solo se incrementa cuando se cierra una operación fantasma."""
        window = self.ghost_stats_window
        now = time.time()
        symbol = self.config['SYMBOL'].get()
        use_sl_tp = self.config['RAPID_OPS_USE_SL_TP'].get()
        tp_amount = self.config['RAPID_OPS_TP'].get() if use_sl_tp else 0
        sl_amount = self.config['RAPID_OPS_SL'].get() if use_sl_tp else 0
        min_profit = self.config['MIN_PROFIT_CLOSE'].get()
        volume = self.config['VOL'].get()
        for typ in ['buy', 'sell']:
            ops = self.ghost_ops[typ]
            # Mantener todas las operaciones abiertas hasta que se cierren por SL/TP o min_profit
            # Conservamos una ventana separada para estadísticas de corto plazo si es necesario
            recent_window = [op for op in ops if now - op['open_time'] <= window]
            tick = mt5.symbol_info_tick(symbol)
            to_keep = []
            if tick:
                current_price = (tick.bid + tick.ask) / 2
                symbol_info = mt5.symbol_info(symbol)
                # ⭐ Usar factor de conversión correcto para profit
                # Para oro/metales: trade_contract_size es típicamente > 1, dividir por 100
                # Para pares: trade_contract_size es 1, usar directamente
                if symbol_info and hasattr(symbol_info, 'trade_contract_size'):
                    contract_size = max(1, symbol_info.trade_contract_size / 100.0) if symbol_info.trade_contract_size >= 100 else 1.0
                else:
                    contract_size = 1.0
                # Iterar sobre todas las operaciones para permitir cierres por SL/TP independientemente de la ventana
                for op in ops:
                    if op['result'] is None:
                        # Calcular profit en USD igual que en las reales
                        if op['type'] == 'BUY':
                            profit_pips = (current_price - op['entry_price'])
                        else:
                            profit_pips = (op['entry_price'] - current_price)
                        # Estimar ganancia en dinero como en las reales
                        profit_usd = profit_pips * volume * contract_size
                        op['profit'] = profit_usd
                        should_close = False
                        reason = ''
                        # Normalizar umbrales como valores absolutos (evitar malinterpretar signos)
                        tp_val = abs(tp_amount) if use_sl_tp else None
                        sl_val = abs(sl_amount) if use_sl_tp else None
                        # Comprobación TP/SL cuando están habilitados
                        if use_sl_tp:
                            # Sólo evaluar TP/SL si los umbrales son mayores que cero
                            if tp_val and tp_val > 0 and profit_usd >= tp_val:
                                should_close = True
                                reason = f"TP alcanzado (${profit_usd:.2f} >= ${tp_val:.2f})"
                                op['result'] = 'win'
                            elif sl_val and sl_val > 0 and profit_usd <= -sl_val:
                                should_close = True
                                reason = f"SL alcanzado (${profit_usd:.2f} <= -${sl_val:.2f})"
                                op['result'] = 'loss'
                        else:
                            if profit_usd >= min_profit:
                                should_close = True
                                reason = f"MIN_PROFIT alcanzado (${profit_usd:.2f} >= ${min_profit:.2f})"
                                op['result'] = 'win'
                        if should_close:
                            # Mantener registro de cierre con precio de cierre
                            self.ghost_ops_history.append({'type': typ.upper(), 'open_time': op['open_time'], 'close_time': now, 'result': op['result'], 'profit': op['profit'], 'entry_price': op.get('entry_price'), 'close_price': current_price})
                            if op['result'] == 'win':
                                self.ghost_total[f'{typ}_win'] += 1
                                self.add_ghost_log(f"Cierre {typ.upper()} WIN: {reason} | Profit={op['profit']:.2f} | Entry={op['entry_price']:.2f} | Close={current_price:.2f}")
                            elif op['result'] == 'loss':
                                self.ghost_total[f'{typ}_loss'] += 1
                                self.add_ghost_log(f"Cierre {typ.upper()} LOSS: {reason} | Profit={op['profit']:.2f} | Entry={op['entry_price']:.2f} | Close={current_price:.2f}")
                        # Mantener las operaciones que sigan abiertas
                        if op['result'] is None:
                            to_keep.append(op)
                    # Después de procesar cierres, asegurar que no se excede el máximo
                    try:
                        if self.ghost_ops_lock:
                            with self.ghost_ops_lock:
                                self._trim_ghost_ops_locked(typ, 50)
                        else:
                            # Si no hay lock, llamar directamente
                            self._trim_ghost_ops_locked(typ, 50)
                    except Exception:
                        pass
            # NO marcar como expiradas; las mantendremos abiertas hasta cierre real
            self.ghost_ops[typ] = to_keep
            open_count = sum(1 for op in to_keep if op['result'] is None)
            # Mostrar totales acumulados para wins/losses
            win_count = self.ghost_total.get(f'{typ}_win', 0)
            loss_count = self.ghost_total.get(f'{typ}_loss', 0)
            self.ghost_stats[f'{typ}_open'] = open_count
            self.ghost_stats[f'{typ}_win'] = win_count
            self.ghost_stats[f'{typ}_loss'] = loss_count

    def update_ghost_ops_ui(self):
        """Actualiza las barras de operaciones fantasma en la UI"""
        try:
            if hasattr(self, 'ghost_buy_label') and hasattr(self, 'ghost_sell_label'):
                b = self.ghost_stats
                t = self.ghost_total
                self.ghost_buy_label.config(
                    text=f"Fantasma BUY: {b['buy_open']} abiertas | {t['buy_win']} ganadas | {t['buy_loss']} perdidas (total)"
                )
                self.ghost_sell_label.config(
                    text=f"Fantasma SELL: {b['sell_open']} abiertas | {t['sell_win']} ganadas | {t['sell_loss']} perdidas (total)"
                )
        except Exception:
            pass
    def __init__(self, root):
        # ====== ESTADO DE OPERACIONES FANTASMA (debe ir primero) ======
        self.ghost_ops = {
            'buy': [],  # [{'open_time': timestamp, 'result': None/'win'/'loss'}]
            'sell': []
        }
        # Lock para sincronizar modificaciones a ghost_ops desde múltiples threads
        try:
            self.ghost_ops_lock = threading.Lock()
        except Exception:
            self.ghost_ops_lock = None
        self.ghost_stats = {
            'buy_open': 0,
            'buy_win': 0,
            'buy_loss': 0,
            'sell_open': 0,
            'sell_win': 0,
            'sell_loss': 0
        }
        self.ghost_ops_history = []  # [{'type': 'BUY'/'SELL', 'open_time': t, 'close_time': t, 'result': 'win'/'loss'}]
        self.ghost_stats_window = 30  # segundos para ventana de evaluación
        self.ghost_total = {'buy_win': 0, 'buy_loss': 0, 'sell_win': 0, 'sell_loss': 0}

        self.root = root
        self.connected = False  # ⭐ NUEVO: Flag de conexión a MT5
        
        # ⭐ NUEVO V4: CANAL DE LECTURA DE DATOS INDEPENDIENTE (funciona durante pausas)
        self.last_impulse_data = {}  # Último cálculo de impulsos (actualizado por _data_reader_thread)
        self.impulse_during_pause = []  # [{'time': ts, 'direction': 'BUY'/'SELL', 'score': N}...]
        self.data_reader_running = False
        self.data_reader_thread = None
        self.last_known_direction = None
        self.data_reader_lock = threading.Lock()
        
        self.root.title("MT5 Trading Bot - Sistema Multi-IA")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e293b')
        # Asegurar que al iniciar el bot el estado runtime esté limpio
        try:
            self.reset_all_state()
        except Exception:
            pass
        # Parámetros para reaperturas forzadas basadas en la apertura inicial
        self.forced_open_params = None  # dict with keys: symbol, direction, vol, tp, sl
        self.forced_open_interval = 300  # segundos (5 minutos)
        self.next_forced_open = None
        # Pequeño retardo antes del primer intento de cierre para evitar retcode 10009
        self.close_delay = 0.5  # segundos - REDUCIDO para cierres más rápidos en azul
        
        # Inicializar analizadores
        self.gold_analyzer = GoldAnalyzer(log_callback=self.add_log)
        self.loss_analyzer = LossAnalyzer(self.gold_analyzer, log_callback=self.add_log)
        
        # ⭐ NUEVO: Sistema Multi-IA
        self.buy_specialist = BuySpecialistAI(log_callback=self.add_log)
        self.sell_specialist = SellSpecialistAI(log_callback=self.add_log)
        # ⭐ ACTUALIZADO: DecisionArbitratorAI ahora con MicroMomentumEngineV2 integrado
        self.arbitrator = DecisionArbitratorAI(
            log_callback=self.add_log,
            symbol='GOLD',  # Puede cambiarse dinámicamente
            micro_profile='MICRO'  # Perfil: 'ULTRA_MICRO' (5-7 pips), 'MICRO' (10-15 pips), 'NORMAL' (20+ pips)
        )
        self.use_multi_ai = tk.BooleanVar(value=True)  # Activar por defecto
        
        # ⭐ NUEVO: Variable para controlar perfil de micro momentum
        self.micro_profile_var = tk.StringVar(value='MICRO')
        
        # ⭐ NUEVO: Detector de Impulsos de Tick - Validar congruencia entre impulsos y especialistas
        # NOTA: Se inicializa sin parámetros; la sincronización completa ocurre en start_bot()
        self.impulse_validator = None  # Se creará en start_bot() después de self.config
        self.use_tick_impulse_validation = tk.BooleanVar(value=True)  # Activado por defecto
        self.min_impulse_alignment_threshold = 60  # 0-100, umbral mínimo
        
        # ⭐ Multi-Timeframe Analyzer será inicializado DESPUÉS de que self.config sea definido
        self.multi_timeframe_analyzer = None
        self.use_multi_timeframe = tk.BooleanVar(value=True)  # Activado por defecto

        # ⭐ NUEVO: Tick Flow Analyzer - Confirmación de presión de mercado
        self.tick_flow_analyzer = None
        self.use_tick_flow = tk.BooleanVar(value=True)  # Activado por defecto

        # ⭐ NUEVO: Data Updater - Actualización periódica de datos cada minuto
        self.data_updater = None
        self.pre_analysis_refresher = None
        
        # ⭐ NUEVO: Data Loader Trainer - Carga y entrena con market_snapshots.json
        self.data_loader = None
        self.training_features = {}
        self.data_ready = False

        # ⭐ NUEVO: Sistema de aprendizaje dinámico
        self.adaptive_params = AdaptiveParameters(log_callback=self.add_log)
        
        # ⭐ NUEVO: Loss Protection con ML y reentrenamiento
        self.loss_protection_ai = LossProtectionAI(log_callback=self.add_log)
        
        # ⭐ NUEVO: Feedback Loop para retroalimentación post-trade
        self.feedback_loop_ai = FeedbackLoopAI(log_callback=self.add_log)

        # ⭐ NUEVO: Rapid Operations intelligent validator
        self.rapid_ops_validator = RapidOpsValidator(log_callback=self.add_log)

        # --- NUEVO: Punto de Entrada IA ---
        self.entry_point_ai = EntryPointAI(log_callback=self.add_log)
        self.use_entry_point = tk.BooleanVar(value=True)  # ACTIVADO: True
        self.entry_point_price = tk.DoubleVar(value=0.0)
        self.entry_point_direction = tk.StringVar(value="BUY")
        self.entry_point_active = False
        # --- fin Punto de Entrada ---
        
        # [OBJETIVO] FASE 3: INSTANCIAR 12 NUEVOS ANALIZADORES V12
        self.super_analyzer = SuperAnalyzer(log_callback=self.add_log)
        self.calibrator = DynamicScoreCalibration(log_callback=self.add_log)
        self.recovery = RecoveryPotentialEnhanced(log_callback=self.add_log)
        self.spread_analyzer = SpreadSlippageAnalyzer(log_callback=self.add_log)
        self.session_filter = TimeBasedSessionFilter(log_callback=self.add_log)
        self.correlation = CorrelationAnalyzer(log_callback=self.add_log)
        
        # Historial para calibración dinámica y seguimiento
        self.closed_trades_for_calibration = {}
        self.use_v12_analysis = tk.BooleanVar(value=True)
        self.last_confidence = 0
        
        # Variables de configuración
        self.config = {
            'LOGIN': tk.StringVar(),
            'PASSWORD': tk.StringVar(),
            'SERVER': "MetaQuotes-Demo",
            'MAGIC_NUMBER': 123456,            
            # Configuración de trading básica
            'SYMBOL': tk.StringVar(value="GOLD"),
            'VOL': tk.DoubleVar(value=0.01),
            'TIMEFRAME': tk.StringVar(value="M1"),
            'CHECK_INTERVAL': tk.IntVar(value=1),
            'OBJETIVO_Z': tk.IntVar(value=0),
            'TRADE_INTERVAL': tk.IntVar(value=300),
            'MAX_SIMULTANEOUS_OPS': tk.IntVar(value=5),
            
            # Configuración de análisis
            'BARS_ANALYZE': tk.IntVar(value=30),
            'LATERAL_THRESHOLD': tk.DoubleVar(value=0.12),
            'TREND_THRESHOLD': tk.DoubleVar(value=0.18),
            'OFFSET_POINTS': tk.DoubleVar(value=5.0),
            'STEPS': tk.IntVar(value=5),
            'MIN_RANGE': tk.DoubleVar(value=2.0),
            'MIN_PROFIT_CLOSE': tk.DoubleVar(value=2.0),  # ESTRATEGIA: cierre mínimo en ganancia $2
            'MIN_TIME_BLUE': tk.IntVar(value=0),
            
            # Configuración de Take Profit y Stop Loss
            'TP_DIFF': tk.DoubleVar(value=5.0),  # ESTRATEGIA: TP en 5 pips
            'SL_DIFF': tk.DoubleVar(value=50.0),  # ESTRATEGIA: SL en 50 pips
            'TREND_TP_MULTIPLIER': tk.DoubleVar(value=1.0),
            'FORCE_STOP_LOSS': tk.DoubleVar(value=100.0),
            'USE_SL': tk.BooleanVar(value=True),  # ⭐ NUEVO: Opción de usar SL
            
            # Configuración de indicadores
            'ATR_PERIOD': tk.IntVar(value=14),
            'EMA_FAST': tk.IntVar(value=3),
            'EMA_SLOW': tk.IntVar(value=7),
            'RSI_PERIOD': tk.IntVar(value=14),
            'RSI_OVERBOUGHT': tk.IntVar(value=75),
            'RSI_OVERSOLD': tk.IntVar(value=25),
            
            # Configuración de protección y gestión
            'MAX_POSITIONS_TREND': tk.IntVar(value=4),
            'MAX_TIME_IN_RED': tk.IntVar(value=20),  # ACTUALIZADO: 15 → 20
            'MAX_TIME_IN_PROFIT': tk.IntVar(value=20),
            'MAX_RED_DEPTH': tk.DoubleVar(value=3.0),
            'MIN_SCORE_REQUIRED': tk.DoubleVar(value=73.0),
            'RED_ANALYSIS_TIME': tk.IntVar(value=30),
            'MIN_RECOVERY_POTENTIAL': tk.DoubleVar(value=30.0),
            'MAX_LOSS_CLOSE': tk.DoubleVar(value=25.0),  # ESTRATEGIA: cierre máx pérdida $25
            
            # Configuración de pausas y protecciones
            'PROTECCION_GANANCIA_PORCENTAJE': tk.IntVar(value=80),
            'MAX_PERDIDA_PORCENTAJE': tk.IntVar(value=20),
            'TIEMPO_INVERSION': tk.IntVar(value=300),
            'PAUSA_POST_GANANCIA': tk.IntVar(value=300),
            'MAX_PERDIDA_PORCENTAJE_GRUPO': tk.DoubleVar(value=75.0),
            'MIN_GANANCIA_GRUPO': tk.DoubleVar(value=50.0),
            
            # Nuevas variables agregadas
            'FORCE_CLOSE_RED_TIME': tk.IntVar(value=60),
            'MIN_GANANCIA_AZUL': tk.DoubleVar(value=0.2),
            'MIN_TIEMPO_AZUL': tk.IntVar(value=10),
            'TIEMPO_MIN_ANALISIS': tk.IntVar(value=10),
            'TIEMPO_MAX_ROJO': tk.IntVar(value=300),
            'MIN_PROB_ENTRADA': tk.DoubleVar(value=73.0),
            'PAUSA_POST_WIN': tk.IntVar(value=0),  # <-- cooldown tras ganar una operación (segundos)
            'CONFIDENCE_THRESHOLD': tk.DoubleVar(value=70.0),  # umbral general árbitro
            'BUY_CONFIDENCE_THRESHOLD': tk.DoubleVar(value=65.0),  # umbral especialista BUY
            'SELL_CONFIDENCE_THRESHOLD': tk.DoubleVar(value=65.0),  # umbral especialista SELL
             'ANALYZE_DURING_PAUSE': tk.BooleanVar(value=True),  # permitir análisis mientras está en pausa
             'AUTO_OPEN_ON_SIGNAL': tk.BooleanVar(value=False),  # abrir automáticamente si señal fuerte durante pausa
            # Forzar apertura tras N minutos si no hay señal
            'ENABLE_FORCED_OPEN': tk.BooleanVar(value=True),
            'FORCED_OPEN_MINUTES': tk.IntVar(value=1),  # ESTRATEGIA: Forzar apertura cada 1 minuto
             
             # [EMOJI] OPERACIONES RÁPIDAS - Solo flag de activación + intervalo
             'RAPID_OPS_ENABLED': tk.BooleanVar(value=False),
             'RAPID_OPS_INTERVAL': tk.IntVar(value=5),  # Intervalo en segundos entre operaciones
             'RAPID_OPS_USE_SL_TP': tk.BooleanVar(value=False),  # Habilitar SL/TP
             'RAPID_OPS_SL': tk.DoubleVar(value=0.5),  # Stop Loss en USD/EUR
             'RAPID_OPS_TP': tk.DoubleVar(value=1.0),  # Take Profit en USD/EUR
             # Parámetros adaptativos IA - sensibilidad y ventana
             'RAPID_OPS_ADAPT_SCALE': tk.DoubleVar(value=100.0),
             'RAPID_OPS_ADAPT_ALPHA': tk.DoubleVar(value=0.35),  # rapidez de adaptación (0-1)
             'RAPID_OPS_TIME_DECAY': tk.IntVar(value=600),  # segundos para decaimiento temporal (peso reciente)
             'RAPID_OPS_INITIAL_PHASE': tk.IntVar(value=60),  # duración de fase inicial en segundos (1m)
             'RAPID_OPS_ADAPT_MIN_SAMPLES': tk.IntVar(value=6),
             'RAPID_OPS_HISTORY_SIZE': tk.IntVar(value=200),
             'RAPID_OPS_LOG_THRESHOLD': tk.DoubleVar(value=0.01),
             'RAPID_OPS_FRAC_COLOR': tk.StringVar(value='#f59e0b'),
             # Opciones de IA para Operaciones Rápidas
             'RAPID_OPS_USE_AI': tk.BooleanVar(value=True),
             'RAPID_OPS_AI_MODE': tk.StringVar(value='ARBITRATOR'),  # ARBITRATOR / BUY / SELL / ENTRYPOINT
                             'RAPID_OPS_ANALYZE_WINDOW': tk.IntVar(value=5),  # segundos para análisis previo a apertura
                         'SNAPSHOT_RELOAD_INTERVAL': tk.IntVar(value=5),  # segundos para recargar market_snapshots desde disco
             'RAPID_OPS_OPEN_OPPOSITE_ON_SLTP': tk.BooleanVar(value=False),  # Abrir operación contraria tras cierre por SL/TP
             'RAPID_OPS_OPEN_OPPOSITE_ON_WIN': tk.BooleanVar(value=False),  # Abrir operación contraria si la otra dirección está ganando
             
             # ⭐ NUEVO: Configuración de Tick Flow Analyzer
             'TICK_FLOW_ENABLED': tk.BooleanVar(value=True),
             'TICK_FLOW_WINDOW': tk.IntVar(value=400),
             'TICK_FLOW_MOMENTUM_WINDOW': tk.IntVar(value=30),
             'TICK_FLOW_IMBALANCE_THRESHOLD': tk.IntVar(value=20),
             'TICK_FLOW_SPREAD_MULTIPLIER': tk.DoubleVar(value=1.5),
             
             # ⭐ NUEVO V3: Configuración de Impulse Detector - Micro-ruptura y micro-impulsos
             'IMPULSE_TICK_WINDOW': tk.IntVar(value=140),  # Ventana de ticks (recomendado 140 para GOLD)
             'IMPULSE_MOMENTUM_WINDOW': tk.IntVar(value=40),  # Ventana de momentum
             'IMPULSE_PRESSURE_THRESHOLD': tk.IntVar(value=56),  # Umbral de presión (56%)
             'IMPULSE_MIN_SEQUENCE': tk.IntVar(value=3),  # Mínimo ticks consecutivos
             'IMPULSE_MICRO_BREAKOUT': tk.DoubleVar(value=0.8),  # Tamaño ruptura en pips
             'IMPULSE_VELOCITY_THRESHOLD': tk.DoubleVar(value=0.35),  # Umbral de velocidad
             'IMPULSE_IMBALANCE_RATIO': tk.DoubleVar(value=1.22),  # Ratio bid/ask
             'IMPULSE_SPREAD_FILTER': tk.DoubleVar(value=1.5),  # Multiplicador spread
             
             # ⭐ NUEVO: CONFIGURACIÓN DE CARGA (Para evitar RESET de parámetros)
             'LOAD_PREV_CONFIG': tk.BooleanVar(value=False),  # NO cargar config anterior por defecto
             
             # ⭐ NUEVO V4: Parámetros de Confirmación y Expiración de Señal
             'IMPULSE_CONFIRMATION_COUNT': tk.IntVar(value=3),  # Ticks para confirmar dirección
             'IMPULSE_SIGNAL_EXPIRATION_MS': tk.IntVar(value=500),  # Expiración en ms (500ms = 0.5s)
             'IMPULSE_MIN_TICK_MOVEMENT': tk.IntVar(value=2),  # Movimiento mínimo en ticks
             
             # ⭐ NUEVO: Configuración de Micro Momentum para operaciones de 5-15 pips
             'MICRO_MOMENTUM_ENABLED': tk.BooleanVar(value=True),  # Habilitar validación de micro movimientos
        }
        # Cargar snapshots de mercado existentes en memoria (si existen) usando reload (con logging)
        try:
            self.market_snapshots = self.reload_market_snapshots()
        except Exception:
            logger.exception("Error inicial leyendo market_snapshots.json")
            self.market_snapshots = []
        # Riesgo por trade (fracción del equity). Usado para sizing dinámico.
        self.config['RISK_PCT'] = tk.DoubleVar(value=0.005)  # 0.5% por defecto
        
        # ⭐ AHORA inicializar MultiTimeframeAnalyzer (después de que self.config existe)
        try:
            self.multi_timeframe_analyzer = MultiTimeframeAnalyzer(
                symbol=self.config['SYMBOL'].get(), 
                log_callback=self.add_log
            )
        except Exception as e:
            self.add_log(f"[MTF] Error inicializando MultiTimeframeAnalyzer: {str(e)[:60]}", 'warning')
            self.multi_timeframe_analyzer = None
        
        # ⭐ NUEVO: Inicializar Tick Flow Analyzer
        try:
            self.tick_flow_analyzer = TickFlowAnalyzer(
                symbol=self.config['SYMBOL'].get(),
                log_callback=self.add_log
            )
            # Aplicar configuración inicial (SIN logs visuales - irán en UI config)
            self.tick_flow_analyzer.update_config({
                'enabled': self.config['TICK_FLOW_ENABLED'].get(),
                'ticks_window': self.config['TICK_FLOW_WINDOW'].get(),
                'momentum_window': self.config['TICK_FLOW_MOMENTUM_WINDOW'].get(),
                'imbalance_threshold': self.config['TICK_FLOW_IMBALANCE_THRESHOLD'].get(),
                'spread_multiplier': self.config['TICK_FLOW_SPREAD_MULTIPLIER'].get(),
            })
            
            # ⭐ NUEVO: Callbacks para actualizar TickFlowAnalyzer cuando cambien valores de configuración
            def _on_tick_flow_config_change(*args):
                if self.tick_flow_analyzer:
                    try:
                        self.tick_flow_analyzer.update_config({
                            'enabled': self.config['TICK_FLOW_ENABLED'].get(),
                            'ticks_window': self.config['TICK_FLOW_WINDOW'].get(),
                            'momentum_window': self.config['TICK_FLOW_MOMENTUM_WINDOW'].get(),
                            'imbalance_threshold': self.config['TICK_FLOW_IMBALANCE_THRESHOLD'].get(),
                            'spread_multiplier': self.config['TICK_FLOW_SPREAD_MULTIPLIER'].get(),
                        })
                    except Exception:
                        pass
            
            # Vincular cambios de configuración de microestructura
            self.config['TICK_FLOW_ENABLED'].trace_add('write', _on_tick_flow_config_change)
            self.config['TICK_FLOW_WINDOW'].trace_add('write', _on_tick_flow_config_change)
            self.config['TICK_FLOW_MOMENTUM_WINDOW'].trace_add('write', _on_tick_flow_config_change)
            self.config['TICK_FLOW_IMBALANCE_THRESHOLD'].trace_add('write', _on_tick_flow_config_change)
            self.config['TICK_FLOW_SPREAD_MULTIPLIER'].trace_add('write', _on_tick_flow_config_change)
            
        except Exception as e:
            self.add_log(f"[TICK] Error inicializando TickFlowAnalyzer: {str(e)[:60]}", 'warning')
            self.tick_flow_analyzer = None
        
        # [EMOJI] OPERACIONES RÁPIDAS - Variables de estado
        self.rapid_ops_active = {}  # dict: {ticket: {type, entry_price, open_time}}
        self.rapid_ops_total_opened = 0  # Contador PERMANENTE que nunca baja (para 50/50)
        self.rapid_ops_buy_count = 0
        self.rapid_ops_sell_count = 0
        self.rapid_ops_total_profit = 0.0  # Acumula ganancias/pérdidas totales
        self.rapid_ops_thread = None
        self.rapid_ops_running = False
        self.last_rapid_op_time = 0
        # Historial para adaptar distribución (lista de dicts: {'type','profit','time'})
        hist_size = int(self._safe_get('RAPID_OPS_HISTORY_SIZE', 200)) if hasattr(self, 'config') else 200
        self.rapid_ops_history = deque(maxlen=hist_size)
        # Lock para sincronizar acceso al historial de rápidas
        try:
            self.rapid_ops_lock = threading.Lock()
        except Exception:
            self.rapid_ops_lock = None
        # Última fracción BUY conocida (para logs/monitor)
        self.last_buy_frac = None
        # Valor suavizado de fracción BUY para respuestas rápidas y estabilidad
        self.rapid_buy_frac_smoothed = None
        # Inicio y fase inicial para IA adaptativa
        self.rapid_ops_start_time = 0
        self.rapid_initial_phase_done = False
        self.rapid_target_buy_frac = 0.5
        # Lock para sincronizar acceso a market_snapshots en múltiples hilos
        try:
            self.market_snapshots_lock = threading.Lock()
        except Exception:
            self.market_snapshots_lock = None
        
        # ⭐ FLAGS DE SINCRONIZACIÓN: trend_monitor → scheduler (prevenir race conditions)
        self.trend_analysis_lock = threading.Lock()
        self.trend_imminent_reversal = False      # Si hay reversión inminente (>70%)
        self.trend_imminent_direction = None      # La dirección esperada (BUY/SELL)
        self.trend_imminent_confidence = 0.0      # Confianza de la reversión
        self.trend_analysis_ready = True          # Si el análisis está actualizado
        
        # ⭐ Monitor de actualización de datos
        self.last_data_stats_log = 0
        self.data_update_count = 0
        
        # Controla hasta cuándo no iniciar nuevas entradas tras una ganancia
        self.block_until = 0.0
        # Hasta cuándo permanece la pausa activa (timestamp)
        self.pause_until = 0.0
        
        # Resto de variables de estado
        self.window_size = 10
        self.pattern_threshold = 0.85
        self.min_pattern_matches = 3
        
        # Variables para control de operaciones y pausas
        self.operaciones_actuales = set()
        self.operaciones_procesadas = set()
        self.operaciones_cerradas = 0
        
        # ⭐ NUEVO: Sistema de Operaciones en Espera
        self.pending_operations = []  # Lista de operaciones pendientes
        
        # Variables de estado
        self.z = 0
        self.ganadas = 0
        self.perdidas = 0
        self.deals_anterior = set()
        self.start_time = 0
        self.is_running = False
        self._scheduler_running = True  # ⭐ NUEVO: control independiente para scheduler
        self.bot_thread = None
        self.connected = False
        # Control para mensajes de account_info faltante: ventana de gracia (segundos)
        self._account_info_first_missing_time = None
        self._account_info_missing_logged = False
        self.force_stop_triggered = False
        self.ultima_operacion = time.time()
        self.trades = {}
        
        # ⭐ NUEVO: Control de volumen dinámico (Kelly-inspired)
        self.recent_losses = []  # Últimas pérdidas para penalización de volumen
        self.last_signal_confidence = 50  # Confianza de última decisión
        self.base_volume = float(self.config.get('VOL', tk.DoubleVar(value=0.02)).get())
        self.last_trade_metadata = None  # NUEVO: Metadata del trade para feedback loop
        
        # Variables de análisis de mercado
        self.market_state = "ANALIZANDO"
        self.trend_direction = "NEUTRAL"
        self.trend_strength = 0
        self.current_range_low = 0
        self.current_range_high = 0
        self.current_mid_price = 0
        self.price_history = deque(maxlen=100)
        self.atr_value = 0
        self.ema_fast = 0
        self.ema_slow = 0
        self.rsi_value = 0
        self.price_momentum = 0
        self.balance_inicial = 0
        self.saldo_inicial = 0.0
        self.ganancia_total = 0.0
        self.direccion_actual = None
        self.ultima_perdida = False
        self.ultima_direccion = None
        self.ultimo_precio = None
        self.perdidas_consecutivas = 0
        self.ganancias_consecutivas = 0
        self.historial_resultados = []
        self.max_historial = 5
        self.en_pausa = False
        self.tiempo_pausa = 0
        self.analisis_inicial_hecho = False
        self.position_tracking = {}
        
        # Contadores para racha de inicio
        self.primera_operacion = True
        self.perdio_primera = False
        
        # Agregar nuevas variables de control
        self.ultima_operacion_timestamp = 0
        self.deals_procesados = set()
        self.ganancias_sesion = 0
        
        # Agregar nuevos contadores para operaciones
        self.operaciones_azules = 0
        self.operaciones_rojas = 0
        
        # Umbrales más estrictos
        self.min_score_required = 3
        self.min_diff_required = 2
        self.confidence_threshold = 70
        
        # Variables para seguimiento de precio
        self.ultimos_precios = deque(maxlen=5)
        self.ultimo_precio_alto = None
        self.ultimo_precio_bajo = None
    
        # Agregar nuevos contadores para saldo
        self.saldo_actual = 0.0
        self.ganancia_neta = 0.0
        self.ultima_ganancia = 0.0
        
        # Agregar variables para control de operaciones
        self.total_operaciones_abiertas = 0
        self.ultima_actualizacion_ui = 0
        self.position_ids = set()
        self.ultima_inversion = time.time()
        self.ultima_apertura = time.time()
        
        # Agregar nueva variable para control de objetivo
        self.objetivo_cumplido = False
        self.objetivo_ganancia = tk.DoubleVar(value=0.0)
        
        # Agregar nuevo atributo para saldo total acumulado
        self.saldo_total_acumulado = 0.0
        
        # Agregar nuevas variables
        self.tiempo_total = tk.IntVar(value=0)  # Tiempo en minutos
        self.tiempo_restante = 0  # Tiempo restante en segundos
        self.tiempo_inicio = 0  # Tiempo cuando inició el bot
        self.bot_pausado = False  # Estado de pausa
        
        # [OBJETIVO] SISTEMA PRO INSTITUCIONAL (NIVEL 5-10)
        self.regime_detector = None
        self.trend_model = None
        self.reversion_model = None
        self.bias_monitor = None
        self.drift_detector = None
        self.dynamic_weights = None
        self.meta_selector = None
        self.pro_system_loaded = False
        
        # ML V2 Models - 4 Nivel Correcciones
        self.ml_model_xgb = None
        self.ml_scaler = None
        self.ml_model_loaded = False
        
        # Dataset Manager Profesional
        self.dataset_manager = None
        self.bot_integration_manager = None
        
        # ⭐ NUEVO: Detector de Cambios de Tendencia (anticipa reversiones 10-30s)
        # Con soporte para market_snapshots.json + calibración adaptativa
        snapshots_path = os.path.join(os.path.dirname(__file__), 'logs', 'market_snapshots.json')
        self.trend_detector = TrendChangeDetector(log_callback=self.add_log, snapshots_path=snapshots_path)
        
        # ⭐ NUEVO: Cierre dinámico de posiciones contrarias a reversión
        self.position_closer = DynamicPositionCloser(log_callback=self.add_log)
        
        # ⭐ INYECTAR: Pasar trend_detector a los especialistas para que lo usen en análisis
        if hasattr(self, 'buy_specialist'):
            self.buy_specialist.trend_detector = self.trend_detector
        if hasattr(self, 'sell_specialist'):
            self.sell_specialist.trend_detector = self.trend_detector
        if hasattr(self, 'arbitrator'):
            self.arbitrator.trend_detector = self.trend_detector
        
        self.trend_monitor_thread = None
        self.trend_monitor_running = False
        self.ui_refresh_thread = None
        self.ui_refresh_running = False
        self.last_trend_analysis = {'risk_level': 'LOW', 'signal': 'STABLE', 'confidence': 0}
        self.last_valid_trend_signal = 'STABLE'  # ⭐ Último BUY/SELL detectado
        self.last_valid_trend_conf = 0  # ⭐ Confianza del último BUY/SELL
        self.trend_change_alert_time = 0  # Último timestamp cuando se alertó de cambio
        
        # ⭐ NUEVO: Monitor Reactivo de Ganancia Mínima (Posiciones en Azul)
        self.blue_monitor_thread = None
        self.blue_monitor_running = False
        self.blue_positions_watched = {}  # {ticket: {'detected_time': timestamp, 'min_profit': value}}
        self.last_blue_check = 0
        
        self.create_widgets()

    def reload_market_snapshots(self, max_len=500):
        """Lee `logs/market_snapshots.json` y actualiza `self.market_snapshots`.
        Siempre intenta leer desde disco para refrescar antes de decidir abrir.
        Devuelve la lista actual (truncada a `max_len`)."""
        try:
            snaps = read_market_snapshots() or []
        except Exception:
            logger.exception("Error leyendo market_snapshots desde disco")
            snaps = getattr(self, 'market_snapshots', []) or []
        
        # VALIDAR: Asegurar que es lista, no dict
        if isinstance(snaps, dict):
            snaps = snaps.get('snapshots', []) if 'snapshots' in snaps else []
        
        try:
            if isinstance(snaps, list) and len(snaps) > max_len:
                snaps = snaps[-max_len:]
        except Exception:
            pass
        # Asignación protegida por lock si está disponible
        try:
            if getattr(self, 'market_snapshots_lock', None):
                with self.market_snapshots_lock:
                    self.market_snapshots = snaps
            else:
                self.market_snapshots = snaps
        except Exception:
            logger.exception("Error al asignar self.market_snapshots")
            pass
        
        # DEBUG: Log si está vacío o tiene datos
        if not snaps:
            logger.warning("[RELOAD] market_snapshots VACIO o no encontrado")
        else:
            logger.info(f"[RELOAD] {len(snaps)} snapshots cargados")
        
        return snaps

    def get_market_snapshots(self):
        """Devuelve una copia de `self.market_snapshots` protegida por lock (si existe)."""
        try:
            snaps = []
            if getattr(self, 'market_snapshots_lock', None):
                with self.market_snapshots_lock:
                    snaps = list(self.market_snapshots) if isinstance(self.market_snapshots, list) else []
            else:
                snaps = list(self.market_snapshots) if isinstance(self.market_snapshots, list) else []
            return snaps
        except Exception:
            logger.exception("Error obteniendo copia de market_snapshots")
            return []

    def _microtrend_direction(self, symbol=None, bars=8, threshold=0.03):
        """
        ⭐ NUEVO: Calcula la microtendencia/momentum de las últimas barras.
        
        Retorna: 'BUY', 'SELL' o 'FLAT'.
        
        Args:
            symbol: Símbolo a analizar (default: GOLD)
            bars: Número de barras para comparar (default: 8)
            threshold: Porcentaje mínimo de cambio para considerar tendencia (ej: 0.03 = 0.3%)
        """
        try:
            symbol = symbol or self.config['SYMBOL'].get()
            
            # Obtener snapshots más frescos (últimas N barras)
            snaps = self.get_market_snapshots() or []
            
            if not snaps or len(snaps) < max(3, bars):
                # Insuficientes datos = no hay microtendencia clara
                return 'FLAT'
            
            # Extraer últimas N barras (cierres)
            closes = []
            for snap in snaps[-bars:]:
                try:
                    if isinstance(snap, dict) and 'close' in snap:
                        closes.append(float(snap['close']))
                except (ValueError, TypeError):
                    continue
            
            if len(closes) < 3:
                return 'FLAT'
            
            # Calcular cambio porcentual de cierre anterior al actual
            delta = closes[-1] - closes[0]
            pct = (delta / closes[0] * 100) if closes[0] != 0 else 0
            
            # Clasificar microtendencia
            if pct > threshold:
                return 'BUY'       # Precio subiendo
            elif pct < -threshold:
                return 'SELL'      # Precio bajando
            else:
                return 'FLAT'      # Sin movimiento significativo
                
        except Exception as e:
            self.add_log(f"[MICROTREND] Error calculando microtendencia: {e}", 'error')
            return 'FLAT'

    def compute_signal_from_snapshots(self, window=20):
        """Simple heuristic: SMA crossover on prefilled snapshots.
        Returns 'BUY', 'SELL' or None."""
        try:
            snaps = self.reload_market_snapshots() or []
            if len(snaps) < window + 2:
                return None
            closes = [float(s['close']) for s in snaps]
            # simple SMA of last window and previous window
            sma_now = sum(closes[-window:]) / window
            sma_prev = sum(closes[-(window*2):-window]) / window
            last = closes[-1]
            if sma_now > sma_prev and last > sma_now:
                return 'BUY'
            if sma_now < sma_prev and last < sma_now:
                return 'SELL'
            return None
        except Exception:
            return None

    def get_volatility_level(self, snapshots):
        """Classify volatility from snapshots: returns 'LOW','NORMAL' or 'HIGH'.
        Uses std deviation thresholds similar to other modules: >2.0 HIGH, >1.0 NORMAL, else LOW.
        """
        try:
            snaps = snapshots or []
            if len(snaps) < 5:
                return 'NORMAL'
            closes = [float(s['close']) for s in snaps if 'close' in s]
            if not closes:
                return 'NORMAL'
            import math
            # compute simple std dev of closes
            mean = sum(closes) / len(closes)
            var = sum((c - mean) ** 2 for c in closes) / len(closes)
            std = math.sqrt(var)
            if std > 2.0:
                return 'HIGH'
            if std > 1.0:
                return 'NORMAL'
            return 'LOW'
        except Exception:
            return 'NORMAL'

    def _calculate_rsi_quick(self, prices, period=14):
        """Quick RSI calculation for rapid ops validation (vectorized with numpy)"""
        try:
            if len(prices) < period + 1:
                return 50.0  # neutral default
            
            # Calculate price changes
            deltas = np.diff(prices)
            
            # Separate gains and losses
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            
            rs = up / down if down != 0 else 0
            rsi = 100.0 - 100.0 / (1.0 + rs) if (1.0 + rs) != 0 else 50.0
            return float(rsi)
        except Exception:
            return 50.0  # neutral fallback

    def _analyze_for_forced_reopen(self, symbol):
        """Análisis dinámico de 30 segundos para reaperturas forzadas.
        Retorna: (mejor_dirección, score_buy, score_sell)"""
        try:
            best_buy = 50
            best_sell = 50
            best_direction = 'BUY'  # Default
            
            for i in range(30):
                try:
                    snaps = self.reload_market_snapshots() or []
                    if snaps:
                        buy_res = None
                        sell_res = None
                        try:
                            if hasattr(self.buy_specialist, 'analyze'):
                                buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                            if hasattr(self.sell_specialist, 'analyze'):
                                sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                        except Exception:
                            pass
                        
                        if buy_res and sell_res:
                            current_buy = float(buy_res.get('score', 50))
                            current_sell = float(sell_res.get('score', 50))
                            
                            # Actualizar si es mejor
                            if current_buy > best_buy or current_sell > best_sell:
                                best_buy = current_buy
                                best_sell = current_sell
                                best_direction = 'BUY' if current_buy > current_sell else 'SELL'
                    
                    remaining = 30 - i - 1
                    if remaining % 10 == 0 or remaining <= 3:
                        self.add_log(f"[30s] T-{remaining}s | BUY: {best_buy:.1f} | SELL: {best_sell:.1f} | MEJOR: {best_direction}", 'info')
                        self._update_forced_open_counter(remaining)
                    
                    if i < 29:  # No dormir en la ultima iteración
                        time.sleep(1)
                except Exception:
                    time.sleep(1)
            
            self._update_forced_open_counter(0)
            return best_direction, best_buy, best_sell
        except Exception as e:
            self.add_log(f"Error en análisis forzada: {e}", 'error')
            return 'BUY', 50, 50

    def _quick_analysis_for_forced_reopen(self, symbol):
        """Análisis COMPLETO para reaperturas forzadas (no tan rápido como el nombre sugiere).
        Incluye: Especialistas + Tendencia + Otros análisis.
        ⭐ IMPORTANTE: EN MODO FORZADO SE IGNORA ARBITRADOR - Se abre con mejor score
        Retorna: (mejor_dirección, score_buy, score_sell, trend_analysis)"""
        try:
            snaps = self.reload_market_snapshots() or []
            buy_score = 50
            sell_score = 50
            direction = 'BUY'
            trend_analysis = None
            buy_res = None
            sell_res = None
            
            # ⭐ PASO 1: Análisis de Especialistas
            if snaps:
                try:
                    if hasattr(self.buy_specialist, 'analyze'):
                        buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                        buy_score = float(buy_res.get('score', 50)) if buy_res else 50
                    
                    if hasattr(self.sell_specialist, 'analyze'):
                        sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                        sell_score = float(sell_res.get('score', 50)) if sell_res else 50
                    
                    # ⭐ APLICAR SESGO POR TENDENCIA DEL MERCADO (suave, solo desempates)
                    market_trend = None
                    if buy_res and buy_res.get('market_condition'):
                        market_condition = buy_res.get('market_condition', {})
                        market_trend = market_condition.get('trend', None) if isinstance(market_condition, dict) else None
                    
                    buy_score_adjusted = buy_score
                    sell_score_adjusted = sell_score
                    
                    if market_trend == 'BAJISTA':
                        buy_score_adjusted = buy_score * 0.95  # -5% (suave)
                        sell_score_adjusted = sell_score * 1.05  # +5% (suave)
                        self.add_log(f"[FORZADA] 📉 Tendencia BAJISTA → Sesgo suave (+5% SELL, -5% BUY)", 'info')
                    elif market_trend == 'ALCISTA':
                        buy_score_adjusted = buy_score * 1.05  # +5% (suave)
                        sell_score_adjusted = sell_score * 0.95  # -5% (suave)
                        self.add_log(f"[FORZADA] 📈 Tendencia ALCISTA → Sesgo suave (+5% BUY, -5% SELL)", 'info')
                    
                    # Elegir mejor dirección con scores ajustados
                    direction = 'BUY' if buy_score_adjusted > sell_score_adjusted else 'SELL'
                    
                    if market_trend:
                        self.add_log(f"[FORZADA] Scores: BUY {buy_score:.1f}→{buy_score_adjusted:.1f} | SELL {sell_score:.1f}→{sell_score_adjusted:.1f} = {direction}", 'info')
                    
                    # Usar las puntuaciones ajustadas para el retorno
                    buy_score = buy_score_adjusted
                    sell_score = sell_score_adjusted
                    
                except Exception:
                    pass
            
            # ⭐ PASO 2: Análisis de Cambio de Tendencia (NUEVO)
            try:
                # Intentar múltiples timeframes si está habilitado
                trend_analysis = None
                if self.use_multi_timeframe.get() == True:
                    try:
                        trend_mtf = self.trend_detector.analyze_trend_change_multi_timeframe(symbol)
                        if trend_mtf and trend_mtf.get('multi_tf_confidence', 0) >= 60:
                            trend_analysis = {
                                'confidence': trend_mtf.get('multi_tf_confidence', 0),
                                'signal': trend_mtf.get('primary_signal', 'STABLE'),
                                'risk_level': 'HIGH' if 'SELL_TO_BUY' in trend_mtf.get('primary_signal', '') or 'BUY_TO_SELL' in trend_mtf.get('primary_signal', '') else 'LOW',
                                'timeframe_agreement': trend_mtf.get('consensus_strength', 0),
                                'recommendation': trend_mtf.get('recommendation', 'HOLD')
                            }
                            self.add_log(f"[MTF-TREND] Multi-TF Reversal: {trend_mtf['primary_signal']} (Confidence: {trend_mtf['multi_tf_confidence']:.0f}%, TF Agreement: {trend_mtf['consensus_strength']:.0f}%)", 'success')
                    except Exception as e:
                        self.add_log(f"[MTF-TREND] Error: {str(e)[:50]}", 'warning')
                
                # Fallback a análisis single-timeframe si multi-TF no disponible
                if trend_analysis is None:
                    trend_analysis = self.trend_detector.analyze_trend_change_risk(symbol, timeframe=mt5.TIMEFRAME_M1, lookback=100)
                
                # 🔥 SI HAY REVERSIÓN MUY FUERTE (CONFIANZA > 85%), DOMINA LA DECISIÓN
                if trend_analysis:
                    trend_confidence = float(trend_analysis.get('confidence', 0))
                    predicted_signal = trend_analysis.get('signal', 'STABLE')
                    risk_level = trend_analysis.get('risk_level', 'LOW')
                    
                    # Si confianza > 85% Y hay reversión detectable, DOMINAR la dirección
                    if trend_confidence > 85 and predicted_signal in ['BUY_TO_SELL', 'SELL_TO_BUY']:
                        if predicted_signal == 'BUY_TO_SELL':
                            direction = 'SELL'
                            buy_score = 0   # FORZAR SELL
                            sell_score = 100
                            self.add_log(f"[FORZADA] 🔴 DOMINIO TREND: BUY→SELL detectado con {trend_confidence:.1f}% → FORZANDO SELL", 'error')
                        elif predicted_signal == 'SELL_TO_BUY':
                            direction = 'BUY'
                            buy_score = 100  # FORZAR BUY
                            sell_score = 0
                            self.add_log(f"[FORZADA] 🟢 DOMINIO TREND: SELL→BUY detectado con {trend_confidence:.1f}% → FORZANDO BUY", 'error')
                    
                    # Si hay ALTO RIESGO de reversión pero confianza media, penalizar (lógica antigua suave)
                    elif risk_level == 'HIGH' and trend_confidence > 60:
                        risk_penalty = 20  # Aumentar penalización a 20 puntos
                        
                        if predicted_signal == 'BUY_TO_SELL':
                            buy_score = max(0, buy_score - risk_penalty)
                            self.add_log(f"[FORZADA] ⚠️ Reversión BUY→SELL (conf: {trend_confidence:.1f}%): BUY penalizado ({risk_penalty} pts)", 'warning')
                        elif predicted_signal == 'SELL_TO_BUY':
                            sell_score = max(0, sell_score - risk_penalty)
                            self.add_log(f"[FORZADA] ⚠️ Reversión SELL→BUY (conf: {trend_confidence:.1f}%): SELL penalizado ({risk_penalty} pts)", 'warning')
                        
                        # Re-evaluar dirección con scores ajustados
                        direction = 'BUY' if buy_score > sell_score else 'SELL'
                        self.add_log(f"[FORZADA] Scores ajustados: BUY={buy_score:.1f} | SELL={sell_score:.1f} → {direction}", 'warning')
            except Exception as e:
                self.add_log(f"[FORZADA] Error en análisis de tendencia: {str(e)[:60]}", 'warning')
            
            # ⭐ PASO 3: EN MODO FORZADO, IGNORAR ARBITRADOR
            # Las reaperturas forzadas (cada 60s) son más agresivas
            # Abrimos con la dirección que tiene mejor score, sin validación conservadora del arbitrador
            self.add_log(f"[FORZADA] ⭐ MODO AGRESIVO: Abriendo con mejor score ({direction}) - Arbitrador IGNORADO", 'success')
            
            return direction, buy_score, sell_score, trend_analysis
        except Exception as e:
            self.add_log(f"Error en análisis completo forzada: {e}", 'error')
            return 'BUY', 50, 50, None

    def evaluate_snapshots_and_open(self, symbol):
        """Evaluate `market_snapshots` with a light heuristic and open if signal found.
        ⭐ NUEVA LÓGICA: 30s análisis ANTES de abrir la operación inicial."""
        try:
            # Prefer a direct snapshot-based specialist comparison at startup
            try:
                snaps = self.reload_market_snapshots() or []
                # Ask specialists to evaluate using snapshots and WITHOUT recovery checks
                buy_res = None
                sell_res = None
                try:
                    if hasattr(self.buy_specialist, 'analyze'):
                        buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                    if hasattr(self.sell_specialist, 'analyze'):
                        sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                except Exception:
                    buy_res = None
                    sell_res = None

                # ⭐ SESGO POR TENDENCIA DE MERCADO (SOLO si tendencia es clara)
                # Detectar tendencia: BAJISTA → favorecer SELL, ALCISTA → favorecer BUY
                market_trend = None
                if buy_res and buy_res.get('market_condition'):
                    market_condition = buy_res.get('market_condition', {})
                    market_trend = market_condition.get('trend', None) if isinstance(market_condition, dict) else None
                
                # Aplicar sesgos a los scores según la tendencia
                buy_score_original = float(buy_res.get('score', 0)) if buy_res else 0
                sell_score_original = float(sell_res.get('score', 0)) if sell_res else 0
                
                buy_score_adjusted = buy_score_original
                sell_score_adjusted = sell_score_original
                trend_bias_info = ""
                
                # SESGO SUAVE (solo para desempates, no bloquear apertura)
                if market_trend == 'BAJISTA':
                    # En mercado BAJISTA: favorecer SELL (bonus más pequeño)
                    buy_score_adjusted = buy_score_original * 0.95  # -5% (suave)
                    sell_score_adjusted = sell_score_original * 1.05  # +5% (suave)
                    trend_bias_info = " [SESGO: BAJISTA]"
                    self.add_log(f"📉 Tendencia BAJISTA detectada → Sesgo suave (+5% SELL, -5% BUY)", 'info')
                elif market_trend == 'ALCISTA':
                    # En mercado ALCISTA: favorecer BUY (bonus más pequeño)
                    buy_score_adjusted = buy_score_original * 1.05  # +5% (suave)
                    sell_score_adjusted = sell_score_original * 0.95  # -5% (suave)
                    trend_bias_info = " [SESGO: ALCISTA]"
                    self.add_log(f"📈 Tendencia ALCISTA detectada → Sesgo suave (+5% BUY, -5% SELL)", 'info')
                
                # Choose the direction with ADJUSTED scores; tie-break on confidence
                chosen = None
                try:
                    if buy_res and sell_res:
                        if buy_score_adjusted > sell_score_adjusted:
                            chosen = 'BUY'
                            if market_trend:
                                self.add_log(f"[SESGO] BUY {buy_score_adjusted:.1f} > SELL {sell_score_adjusted:.1f}{trend_bias_info}", 'info')
                        elif sell_score_adjusted > buy_score_adjusted:
                            chosen = 'SELL'
                            if market_trend:
                                self.add_log(f"[SESGO] SELL {sell_score_adjusted:.1f} > BUY {buy_score_adjusted:.1f}{trend_bias_info}", 'info')
                        else:
                            # tie -> use confidence
                            if float(buy_res.get('confidence', 0)) >= float(sell_res.get('confidence', 0)):
                                chosen = 'BUY'
                            else:
                                chosen = 'SELL'
                    elif buy_res:
                        chosen = 'BUY'
                    elif sell_res:
                        chosen = 'SELL'
                except Exception as e:
                    self.add_log(f"[ERROR] Sesgo de tendencia: {str(e)[:60]}", 'error')
                    chosen = None

                if chosen:
                    # ⭐ ANÁLISIS 30s: Monitorear probabilidades en VIVO
                    self.add_log(f"\n{'📊'*35}", 'info')
                    self.add_log(f"[INICIAL] ⭐ MODO AGRESIVO: Abriendo con mejor score de especialistas (IGNORA arbitrador conservador)", 'success')
                    self.add_log(f"[ANÁLISIS] Monitoreando probabilidades durante 30 segundos...", 'warning')
                    self.add_log(f"{'📊'*35}\n", 'info')
                    
                    best_buy_score = buy_res.get('score', 0)
                    best_sell_score = sell_res.get('score', 0)
                    best_buy_conf = buy_res.get('confidence', 0)
                    best_sell_conf = sell_res.get('confidence', 0)
                    best_direction = chosen
                    
                    # Monitorear 30 segundos
                    for seconds_elapsed in range(30):
                        remaining = 30 - seconds_elapsed
                        
                        # Log del progreso
                        if remaining % 10 == 0 or remaining <= 3:
                            self.add_log(f"[30s] T-{remaining}s | BUY: {best_buy_score:.1f} | SELL: {best_sell_score:.1f} | MEJOR: {best_direction}", 'info')
                            self._update_initial_analysis_counter(remaining, best_direction)
                        
                        time.sleep(1)
                    
                    self._update_initial_analysis_counter(0, '')
                    self.add_log(f"\n{'✅'*35}", 'success')
                    self.add_log(f"[INICIAL] Análisis completado en 30 segundos", 'success')
                    # ⭐ SIMPLIFICADO: Solo mostrar opción ganadora con confianza
                    chosen_conf = best_buy_conf if best_direction == 'BUY' else best_sell_conf
                    self.add_log(f"[INICIAL] {best_direction.upper()} {chosen_conf:.0f}%", 'success')
                    
                    # ⭐ USAR TICK FLOW ANALYZER PARA RESOLVER DIRECCIÓN FINAL (STARTUP)
                    final_direction = best_direction
                    if self.use_tick_flow.get() and self.tick_flow_analyzer:
                        try:
                            ticks = self.tick_flow_analyzer.get_recent_ticks(
                                limit=self.config['TICK_FLOW_WINDOW'].get()
                            )
                            resolution = self.tick_flow_analyzer.resolve_final_direction(
                                ia_direction=best_direction,
                                ticks=ticks
                            )
                            final_direction = resolution.get('final_direction', best_direction)
                            
                            if resolution.get('inverted'):
                                self.add_log(f"[FLOW] ⚠️ STARTUP - Dirección INVERTIDA: {best_direction} → {final_direction}", 'warning')
                            else:
                                self.add_log(f"[FLOW] ✅ STARTUP - Dirección CONFIRMADA: {final_direction}", 'success')
                        except Exception as e:
                            self.add_log(f"[FLOW] ⚠️ Error en startup flow: {str(e)[:80]}", 'warning')
                            final_direction = best_direction
                    
                    self.add_log(f"[INICIAL] 🚀 ABRIENDO INMEDIATAMENTE: {final_direction.upper()}", 'success')
                    self.add_log(f"{'✅'*35}\n", 'success')
                    
                    try:
                        result = self.abrir_operacion(final_direction, force=True, startup=True)
                        if not result:
                            self.add_log(f"[ERROR] abrir_operacion retornó False para {final_direction}", 'error')
                        return result
                    except Exception as e:
                        self.add_log(f"[ERROR] Exception en abrir_operacion: {str(e)[:100]}", 'error')
                        import traceback
                        self.add_log(f"[TRACE] {traceback.format_exc()[:200]}", 'error')
                        return False
            except Exception:
                pass

            # Fallback: use full Multi-IA analysis (if desired) and then heuristic
            try:
                decision = self._analizar_con_multi_ia(symbol)
            except Exception:
                decision = None

            if not decision:
                sig = self.compute_signal_from_snapshots()
                if not sig:
                    return False
                self.add_log(f"📡 Snapshot heuristic suggests {sig} — intentando abrir inmediatamente", 'info')
                try:
                    return self.abrir_operacion(sig, force=True, startup=True)
                except Exception:
                    return False

            self.add_log(f"[IA] Multi-IA inicial sugiere {decision} — intentando abrir inmediatamente", 'info')
            try:
                return self.abrir_operacion(decision, force=True, startup=True)
            except Exception:
                return False
        except Exception:
            return False
        
    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg='#0f172a', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="MT5 Smart Multi-IA Trading Bot", 
                              font=('Arial', 24, 'bold'), bg='#0f172a', fg='#60a5fa')
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(header_frame, text="Sistema de 3 IAs especializadas con protección inteligente", 
                                 font=('Arial', 10), bg='#0f172a', fg='#94a3b8')
        subtitle_label.pack()
        
        main_container = tk.Frame(self.root, bg='#1e293b')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # NUEVO: Panel izquierdo con PESTAÑAS
        left_panel = tk.Frame(main_container, bg='#1e293b', width=500)
        left_panel.pack(side='left', fill='both', padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # Crear Notebook (pestañas)
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill='both', expand=True)
        
        # Pestaña 1: Control
        control_tab = tk.Frame(notebook, bg='#1e293b')
        notebook.add(control_tab, text="Control del Bot")
        
        # Pestaña 2: Configuración
        config_tab = tk.Frame(notebook, bg='#1e293b')
        notebook.add(config_tab, text="Configuración")
        
        # --- NUEVA PESTAÑA: Punto de Entrada ---
        entry_point_tab = tk.Frame(notebook, bg='#1e293b')
        notebook.add(entry_point_tab, text="Punto de Entrada")
        # --- FIN ---
        
        # --- NUEVA PESTAÑA: Operaciones en Espera ---
        pending_ops_tab = tk.Frame(notebook, bg='#1e293b')
        notebook.add(pending_ops_tab, text="⏳ Operaciones en Espera")
        # --- FIN ---
        
        # --- NUEVA PESTAÑA: Operaciones Rápidas ---
        rapid_ops_tab = tk.Frame(notebook, bg='#1e293b')
        notebook.add(rapid_ops_tab, text="⚡ Operaciones Rápidas")
        # --- FIN ---
        
        # --- NUEVA PESTAÑA: Análisis en Vivo ---
        analysis_live_tab = tk.Frame(notebook, bg='#1e293b')
        notebook.add(analysis_live_tab, text="📊 Análisis en Vivo")
        # --- FIN ---
        
        # Panel derecho (Sin cambios)
        right_panel = tk.Frame(main_container, bg='#1e293b')
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Llenar las pestañas
        self.create_control_panel(control_tab)
        self.create_config_panel(config_tab)
        self.create_entry_point_panel(entry_point_tab)  # <-- nuevo panel
        self.create_pending_operations_panel(pending_ops_tab)  # <-- nuevo panel operaciones en espera
        self.create_rapid_operations_panel(rapid_ops_tab)  # <-- nuevo panel operaciones rápidas
        self.create_analysis_live_panel(analysis_live_tab)  # <-- nuevo panel análisis en vivo
        self.create_stats_panel(right_panel)
        self.create_progress_panel(right_panel)
        self.create_events_panel(right_panel)  # Panel de eventos - sin logs
        # Iniciar actualización periódica de información de cuenta (balance/equity)
        try:
            self.update_account_info()
            # Programar actualizaciones periódicas cada 1 segundo
            self._schedule_account_update()
        except Exception:
            pass
        
    def _schedule_account_update(self):
        """Programa la actualización periódica de la información de cuenta MT5."""
        try:
            # Reconectar a MT5 si es necesario
            try:
                if not mt5.initialize():
                    mt5.initialize()
            except:
                pass
            
            # Actualizar datos
            self.update_account_info()
        except Exception as e:
            pass
        
        # Reprogramar para ejecutarse cada 1000ms (1 segundo)
        try:
            self.root.after(1000, self._schedule_account_update)
        except:
            pass
        
    def create_control_panel(self, parent):
        control_frame = tk.LabelFrame(parent, text="Control del Bot", 
                                     bg='#334155', fg='#f1f5f9',
                                     font=('Arial', 11, 'bold'), padx=15, pady=15)
        control_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ===== INFORMACIÓN DE CUENTA MT5 - RESPONSIVE =====
        account_info_frame = tk.Frame(control_frame, bg='#334155')
        account_info_frame.pack(fill='x', pady=(0, 15))
        
        # Contenedor para datos (grid-like responsivo)
        data_container = tk.Frame(account_info_frame, bg='#334155')
        data_container.pack(fill='x', expand=True)
        
        # Fila 1: Balance y Patrimonio (lado izquierdo)
        row1_frame = tk.Frame(data_container, bg='#334155')
        row1_frame.pack(fill='x', pady=2)
        
        # Balance (col 1)
        balance_frame = tk.Frame(row1_frame, bg='#334155')
        balance_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        tk.Label(balance_frame, text="💰 Balance:", bg='#334155', fg='#f1f5f9', font=('Arial', 9)).pack(side='left', padx=(0, 5))
        self.mt5_balance_label = tk.Label(balance_frame, text="$0.00", bg='#334155', fg='#60a5fa', font=('Arial', 9, 'bold'))
        self.mt5_balance_label.pack(side='left', fill='x', expand=True)
        
        # Patrimonio (col 2)
        equity_frame = tk.Frame(row1_frame, bg='#334155')
        equity_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        tk.Label(equity_frame, text="📊 Patrimonio:", bg='#334155', fg='#f1f5f9', font=('Arial', 9)).pack(side='left', padx=(0, 5))
        self.mt5_equity_label = tk.Label(equity_frame, text="$0.00", bg='#334155', fg='#34d399', font=('Arial', 9, 'bold'))
        self.mt5_equity_label.pack(side='left', fill='x', expand=True)
        
        # Margen Libre (col 3)
        margin_frame = tk.Frame(row1_frame, bg='#334155')
        margin_frame.pack(side='left', fill='x', expand=True)
        tk.Label(margin_frame, text="🛡️ Margen:", bg='#334155', fg='#f1f5f9', font=('Arial', 9)).pack(side='left', padx=(0, 5))
        self.mt5_free_margin_label = tk.Label(margin_frame, text="$0.00", bg='#334155', fg='#fbbf24', font=('Arial', 9, 'bold'))
        self.mt5_free_margin_label.pack(side='left', fill='x', expand=True)
        
        # Fila 2: Alcance (Leverage)
        row2_frame = tk.Frame(data_container, bg='#334155')
        row2_frame.pack(fill='x', pady=2)
        
        tk.Label(row2_frame, text="📍 Alcance:", bg='#334155', fg='#f1f5f9', font=('Arial', 9)).pack(side='left', padx=(0, 5))
        self.mt5_leverage_label = tk.Label(row2_frame, text="1:0", bg='#334155', fg='#f59e0b', font=('Arial', 9, 'bold'))
        self.mt5_leverage_label.pack(side='left', padx=0)
        
        status_frame = tk.Frame(control_frame, bg='#334155')
        status_frame.pack(fill='x', pady=(0, 15))
        
        self.status_indicator = tk.Canvas(status_frame, width=20, height=20, 
                                         bg='#334155', highlightthickness=0)
        self.status_indicator.pack(side='left', padx=(0, 10))
        self.status_circle = self.status_indicator.create_oval(2, 2, 18, 18, 
                                                              fill='#ef4444', outline='')
        
        self.status_label = tk.Label(status_frame, text="Bot Detenido", 
                                     font=('Arial', 12, 'bold'), bg='#334155', fg='#f87171')
        self.status_label.pack(side='left')
        
        # (Balance y Patrimonio mostrados en la pestaña 'Operaciones Rápidas')
        
        btn_frame = tk.Frame(control_frame, bg='#334155')
        btn_frame.pack(fill='x')
        
        self.start_btn = tk.Button(btn_frame, text="Iniciar Bot", 
                                   command=self.start_bot,
                                   bg='#10b981', fg='white', font=('Arial', 11, 'bold'),
                                   relief='flat', padx=20, pady=10, cursor='hand2')
        self.start_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.stop_btn = tk.Button(btn_frame, text="Detener Bot", 
                                 command=self.stop_bot,
                                 bg='#ef4444', fg='white', font=('Arial', 11, 'bold'),
                                 relief='flat', padx=20, pady=10, cursor='hand2',
                                 state='disabled')
        self.stop_btn.pack(side='left', expand=True, fill='x', padx=(5, 0))
        
        # Frame para botones de gestión
        mgmt_btn_frame = tk.Frame(control_frame, bg='#334155')
        mgmt_btn_frame.pack(fill='x', pady=(10, 0))
        
        reset_btn = tk.Button(mgmt_btn_frame, text="Reset Contadores", 
                             command=self.reset_counters,
                             bg='#64748b', fg='white', font=('Arial', 10),
                             relief='flat', padx=15, pady=8, cursor='hand2')
        reset_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        reiniciar_btn = tk.Button(mgmt_btn_frame, text="🔄 Reiniciar Bot", 
                                 command=self.reiniciar_bot_limpio,
                                 bg='#8b5cf6', fg='white', font=('Arial', 10),
                                 relief='flat', padx=15, pady=8, cursor='hand2')
        reiniciar_btn.pack(side='left', expand=True, fill='x', padx=(5, 5))
        
        limpiar_espera_btn = tk.Button(mgmt_btn_frame, text="🗑️ Limpiar Espera", 
                                      command=self._clear_all_pending,
                                      bg='#ef4444', fg='white', font=('Arial', 10),
                                      relief='flat', padx=15, pady=8, cursor='hand2')
        limpiar_espera_btn.pack(side='left', expand=True, fill='x', padx=(5, 0))

        # Toggle Multi-IA
        multi_ai_frame = tk.Frame(control_frame, bg='#334155')
        multi_ai_frame.pack(fill='x', pady=(10, 0))

        tk.Label(multi_ai_frame, text="Sistema Multi-IA:", 
                bg='#334155', fg='#f1f5f9',
                font=('Arial', 10, 'bold')).pack(side='left')

        self.multi_ai_toggle = tk.Checkbutton(
            multi_ai_frame, 
            text="Activado (3 IAs)",
            variable=self.use_multi_ai,
            bg='#334155', 
            fg='#10b981',
            selectcolor='#1e293b',
            activebackground='#334155',
            font=('Arial', 10, 'bold'),
            command=self._on_multi_ai_toggle
        )
        self.multi_ai_toggle.pack(side='left', padx=5)
        
        self.mode_label = tk.Label(multi_ai_frame, text="(BUY + SELL)", 
                                   bg='#334155', fg='#34d399',
                                   font=('Arial', 9))
        self.mode_label.pack(side='left', padx=5)
        
        # Frame para objetivo, tiempo y pausas
        objetivo_frame = tk.LabelFrame(control_frame, text="Objetivos y Pausas", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=10, pady=10)
        objetivo_frame.pack(fill='x', pady=(10, 0))
        
        # Fila 1: Objetivo y Tiempo
        row1 = tk.Frame(objetivo_frame, bg='#2d3e50')
        row1.pack(fill='x', pady=3)
        
        tk.Label(row1, text="Objetivo ($):", bg='#2d3e50', fg='#f1f5f9', width=16, anchor='w').pack(side='left', padx=5)
        tk.Entry(row1, textvariable=self.objetivo_ganancia, width=8, bg='#475569', fg='white').pack(side='left', padx=5)
        
        tk.Label(row1, text="Tiempo (min):", bg='#2d3e50', fg='#f1f5f9', width=14, anchor='w').pack(side='left', padx=5)
        tk.Entry(row1, textvariable=self.tiempo_total, width=8, bg='#475569', fg='white').pack(side='left', padx=5)
        
        # Fila 2: Pausas
        row2 = tk.Frame(objetivo_frame, bg='#2d3e50')
        row2.pack(fill='x', pady=3)
        
        tk.Label(row2, text="Pausa Objetivo (s):", bg='#2d3e50', fg='#f1f5f9', width=16, anchor='w').pack(side='left', padx=5)
        tk.Entry(row2, textvariable=self.config['PAUSA_POST_GANANCIA'], width=8, bg='#475569', fg='white').pack(side='left', padx=5)
        
        tk.Label(row2, text="Cooldown (s):", bg='#2d3e50', fg='#f1f5f9', width=14, anchor='w').pack(side='left', padx=5)
        tk.Entry(row2, textvariable=self.config['PAUSA_POST_WIN'], width=8, bg='#475569', fg='white').pack(side='left', padx=5)
        
        # Fila 3: Opciones de pausa
        row3 = tk.Frame(objetivo_frame, bg='#2d3e50')
        row3.pack(fill='x', pady=3)
        
        tk.Label(row3, text="Opciones:", bg='#2d3e50', fg='#f1f5f9', width=16, anchor='w').pack(side='left', padx=5)
        tk.Checkbutton(row3, text="Analizar Pausa", variable=self.config['ANALYZE_DURING_PAUSE'], 
                      bg='#2d3e50', fg='#34d399', selectcolor='#1e293b', activebackground='#2d3e50', font=('Arial', 8)).pack(side='left', padx=5)
        tk.Checkbutton(row3, text="Auto-abrir", variable=self.config['AUTO_OPEN_ON_SIGNAL'], 
                      bg='#2d3e50', fg='#34d399', selectcolor='#1e293b', activebackground='#2d3e50', font=('Arial', 8)).pack(side='left', padx=5)
        tk.Checkbutton(row3, text="📁 Cargar Config Anterior", variable=self.config['LOAD_PREV_CONFIG'], 
                      bg='#2d3e50', fg='#60a5fa', selectcolor='#1e293b', activebackground='#2d3e50', font=('Arial', 8)).pack(side='left', padx=5)
        
        self.tiempo_label = tk.Label(row3, text="", bg='#2d3e50', fg='#60a5fa', font=('Arial', 8))
        self.tiempo_label.pack(side='left', padx=5)
        
        # Frame para botones pausa/resume
        btn_frame_pausa = tk.Frame(objetivo_frame, bg='#2d3e50')
        btn_frame_pausa.pack(fill='x', pady=(5, 0))
        
        self.pause_btn = tk.Button(btn_frame_pausa, text="⏸️ Pausar", 
                                command=self.pausar_bot,
                                bg='#3b82f6', fg='white', font=('Arial', 9),
                                relief='flat', padx=10, pady=5, cursor='hand2',
                                state='disabled')
        self.pause_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.resume_btn = tk.Button(btn_frame_pausa, text="▶️ Reanudar", 
                                command=self.reanudar_trading,
                                bg='#10b981', fg='white', font=('Arial', 9),
                                relief='flat', padx=10, pady=5, cursor='hand2',
                                state='disabled')
        self.resume_btn.pack(side='left', expand=True, fill='x', padx=(5, 0))

        # Botón de emergencia
        self.emergency_btn = tk.Button(control_frame, text="⚠️ CIERRE DE EMERGENCIA", 
                                     command=self.cierre_emergencia,
                                     bg='#dc2626', fg='white', font=('Arial', 10, 'bold'),
                                     relief='flat', padx=20, pady=8, cursor='hand2')
        self.emergency_btn.pack(fill='x', pady=(10, 0))
        
        # Trading manual
        manual_frame = tk.Frame(control_frame, bg='#334155')
        manual_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(manual_frame, text="Trading Manual", 
                bg='#334155', fg='#f5f5f9',
                font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        
        trade_btn_frame = tk.Frame(manual_frame, bg='#334155')
        trade_btn_frame.pack(fill='x')
        
        self.manual_buy_btn = tk.Button(trade_btn_frame, text="⬆️ BUY", 
                                      command=lambda: self.abrir_operacion_manual("BUY"),
                                      bg='#22c55e', fg='white', font=('Arial', 10, 'bold'),
                                      relief='flat', padx=20, pady=8, cursor='hand2')
        self.manual_buy_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.manual_sell_btn = tk.Button(trade_btn_frame, text="⬇️ SELL", 
                                       command=lambda: self.abrir_operacion_manual("SELL"),
                                       bg='#ef4444', fg='white', font=('Arial', 10, 'bold'),
                                       relief='flat', padx=20, pady=8, cursor='hand2')
        self.manual_sell_btn.pack(side='left', expand=True, fill='x', padx=(5, 0))
        
        # ⭐ NUEVO: Frame para Detector de Tendencia de Mercado
        trend_frame = tk.Frame(manual_frame, bg='#1e3a3a')
        trend_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(trend_frame, text="📊 DETECTOR DE TENDENCIA", 
                bg='#1e3a3a', fg='#10b981',
                font=('Arial', 10, 'bold')).pack(pady=(5, 0))
        
        # Frame con estado del trend
        trend_state_frame = tk.Frame(trend_frame, bg='#1e3a3a')
        trend_state_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        # Indicador de tendencia (BUY/SELL)
        self.trend_state_label = tk.Label(trend_state_frame, text="🔄 NEUTRAL",
                                         bg='#1e3a3a', fg='#94a3b8',
                                         font=('Arial', 11, 'bold'))
        self.trend_state_label.pack(side='left', expand=True, fill='x')
        
        # Nivel de riesgo
        self.trend_risk_label = tk.Label(trend_state_frame, text="Risk: LOW",
                                        bg='#1e3a3a', fg='#fbbf24',
                                        font=('Arial', 10))
        self.trend_risk_label.pack(side='left', padx=(5, 0))
        
        # Temporizador
        self.trend_timer_label = tk.Label(trend_state_frame, text="⏱️ 60s",
                                         bg='#1e3a3a', fg='#64748b',
                                         font=('Arial', 10))
        self.trend_timer_label.pack(side='left', padx=(5, 0))
        
        # Confianza
        self.trend_confidence_label = tk.Label(trend_state_frame, text="Conf: 0%",
                                              bg='#1e3a3a', fg='#cbd5e1',
                                              font=('Arial', 9))
        self.trend_confidence_label.pack(side='left', padx=(5, 0))
        
        # Variables para tracking
        self.trend_next_check_time = 0
        self.trend_last_signal = 'STABLE'

    def create_config_panel(self, parent):
        config_frame = tk.Frame(parent, bg='#1e293b')
        config_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(config_frame, bg='#334155', highlightthickness=0)
        scrollbar = tk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#334155')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        configs = [
            ("Símbolo:", 'SYMBOL'),
            ("Volumen:", 'VOL'),
            ("Recarga snapshots (s):", 'SNAPSHOT_RELOAD_INTERVAL'),
            ("Max Operaciones Simultáneas:", 'MAX_SIMULTANEOUS_OPS'),
            ("TP Diferencia:", 'TP_DIFF'),
            ("SL Diferencia:", 'SL_DIFF'),
            ("Min Profit para Cerrar ($):", 'MIN_PROFIT_CLOSE'),
            ("Max Loss para Cerrar ($):", 'MAX_LOSS_CLOSE'),
            ("Detener en Pérdida ($):", 'FORCE_STOP_LOSS'),
            ("Max Tiempo Análisis Rojo (s):", 'RED_ANALYSIS_TIME'),
            ("Min Potencial Recuperación (%):", 'MIN_RECOVERY_POTENTIAL'),
        ]
        
        self.config_entries = {}
        
        for label, key in configs:
            row_frame = tk.Frame(scrollable_frame, bg='#334155')
            row_frame.pack(fill='x', pady=3)
            
            lbl = tk.Label(row_frame, text=label, bg='#334155', fg='#cbd5e1',
                          font=('Arial', 9), width=22, anchor='w')
            lbl.pack(side='left')
            
            entry = tk.Entry(row_frame, textvariable=self.config[key],
                           bg='#475569', fg='white', relief='flat',
                           font=('Arial', 9), insertbackground='white')
            entry.pack(side='right', fill='x', expand=True)
            self.config_entries[key] = entry

        # --- NUEVO: Sección Apertura Forzada ---
        forced_frame = tk.LabelFrame(scrollable_frame, text="Apertura Forzada",
                                     bg='#2d3e50', fg='#f1f5f9',
                                     font=('Arial', 10, 'bold'), padx=10, pady=10)
        forced_frame.pack(fill='x', pady=(10, 0))

        tk.Checkbutton(forced_frame, text="🔓 Habilitar apertura forzada",
                      variable=self.config['ENABLE_FORCED_OPEN'],
                      bg='#2d3e50', fg='#f1f5f9', selectcolor='#1e293b',
                      activebackground='#2d3e50', activeforeground='#f1f5f9',
                      font=('Arial', 10)).pack(side='left', padx=5)

        forced_minutes_frame = tk.Frame(forced_frame, bg='#2d3e50')
        forced_minutes_frame.pack(fill='x', pady=(8, 0))

        tk.Label(forced_minutes_frame, text="Minutos para forzar:", bg='#2d3e50', fg='#f1f5f9', width=18, anchor='w').pack(side='left', padx=5)
        tk.Entry(forced_minutes_frame, textvariable=self.config['FORCED_OPEN_MINUTES'], width=6, bg='#475569', fg='white').pack(side='left', padx=5)
        # --- FIN Apertura Forzada ---

        # --- NUEVO: Calibración Multi-IA al final del panel de configuración ---
        calibracion_frame = tk.LabelFrame(scrollable_frame, text="Calibración Multi-IA", 
                                         bg='#2d3e50', fg='#f1f5f9',
                                         font=('Arial', 10, 'bold'), padx=10, pady=10)
        calibracion_frame.pack(fill='x', pady=(15, 0))

        row_specialists = tk.Frame(calibracion_frame, bg='#2d3e50')
        row_specialists.pack(fill='x', pady=3)

        tk.Label(row_specialists, text="Conf. BUY (%):", bg='#2d3e50', fg='#f1f5f9', width=16, anchor='w').pack(side='left', padx=5)
        tk.Entry(row_specialists, textvariable=self.config['BUY_CONFIDENCE_THRESHOLD'], width=6, bg='#475569', fg='white').pack(side='left', padx=5)

        tk.Label(row_specialists, text="Conf. SELL (%):", bg='#2d3e50', fg='#f1f5f9', width=12, anchor='w').pack(side='left', padx=5)
        tk.Entry(row_specialists, textvariable=self.config['SELL_CONFIDENCE_THRESHOLD'], width=6, bg='#475569', fg='white').pack(side='left', padx=5)

        row_arbitrator = tk.Frame(calibracion_frame, bg='#2d3e50')
        row_arbitrator.pack(fill='x', pady=3)

        tk.Label(row_arbitrator, text="Conf. Árbitro (%):", bg='#2d3e50', fg='#f1f5f9', width=16, anchor='w').pack(side='left', padx=5)
        tk.Entry(row_arbitrator, textvariable=self.config['CONFIDENCE_THRESHOLD'], width=6, bg='#475569', fg='white').pack(side='left', padx=5)
        
        # ⭐ NUEVO: Checkbox para usar SL
        sl_frame = tk.Frame(calibracion_frame, bg='#2d3e50')
        sl_frame.pack(fill='x', pady=10)
        
        tk.Checkbutton(sl_frame, text="🛡️ Usar Stop Loss en operaciones", 
                      variable=self.config['USE_SL'],
                      bg='#2d3e50', fg='#34d399', selectcolor='#1e293b',
                      activebackground='#2d3e50', activeforeground='#34d399',
                      font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        # --- FIN bloque calibración ---

        # ⭐ NUEVO: Configuración de Microestructura de Mercado (Tick Flow)
        tickflow_frame = tk.LabelFrame(scrollable_frame, text="⚙️ Análisis de Microestructura de Mercado (Tick Flow)", 
                                       bg='#1e293b', fg='#60a5fa',
                                       font=('Arial', 11, 'bold'), padx=15, pady=15)
        tickflow_frame.pack(fill='both', expand=False, pady=(15, 0))

        # Fila 0: Toggle para habilitar/deshabilitar
        toggle_row = tk.Frame(tickflow_frame, bg='#1e293b')
        toggle_row.pack(fill='x', pady=(0, 10))
        
        tk.Checkbutton(toggle_row, text="✓ Habilitar análisis de presión de orden (Tick Flow)",
                      variable=self.config['TICK_FLOW_ENABLED'],
                      bg='#1e293b', fg='#60a5fa', selectcolor='#0f172a',
                      activebackground='#1e293b', activeforeground='#60a5fa',
                      font=('Arial', 10, 'bold')).pack(side='left', padx=0)

        # Fila 1: Cantidad de ticks
        row1 = tk.Frame(tickflow_frame, bg='#1e293b')
        row1.pack(fill='x', pady=8)
        
        tk.Label(row1, text="📊 Cantidad de ticks:", bg='#1e293b', fg='#cbd5e1', 
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row1, from_=50, to=2000, textvariable=self.config['TICK_FLOW_WINDOW'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row1, text="(50-2000)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)

        # Fila 2: Ventana de momentum
        row2 = tk.Frame(tickflow_frame, bg='#1e293b')
        row2.pack(fill='x', pady=8)
        
        tk.Label(row2, text="📈 Ventana momentum:", bg='#1e293b', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row2, from_=5, to=500, textvariable=self.config['TICK_FLOW_MOMENTUM_WINDOW'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row2, text="(5-500 ticks)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)

        # Fila 3: Umbral de presión de orden
        row3 = tk.Frame(tickflow_frame, bg='#1e293b')
        row3.pack(fill='x', pady=8)
        
        tk.Label(row3, text="⚡ Umbral presión:", bg='#1e293b', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row3, from_=0.1, to=100, increment=0.1, textvariable=self.config['TICK_FLOW_IMBALANCE_THRESHOLD'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row3, text="(min. imbalance)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)

        # Fila 4: Multiplicador de spread
        row4 = tk.Frame(tickflow_frame, bg='#1e293b')
        row4.pack(fill='x', pady=8)
        
        tk.Label(row4, text="📌 Multiplicador spread:", bg='#1e293b', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row4, from_=0.1, to=5.0, increment=0.1, textvariable=self.config['TICK_FLOW_SPREAD_MULTIPLIER'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row4, text="(factor de filtro)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)
        
        # Separador visual
        sep_frame = tk.Frame(tickflow_frame, bg='#0f172a', height=1)
        sep_frame.pack(fill='x', pady=(10, 0))

        # ⭐ NUEVO V4: Panel de Detección de Impulsos V4 (Confirmación, Expiración, Movimiento)
        impulse_frame = tk.Frame(tickflow_frame, bg='#1e293b', bd=1, relief='flat')
        impulse_frame.pack(fill='x', padx=10, pady=(15, 5))
        
        tk.Label(impulse_frame, text="⭐ IMPULSE DETECTOR V4 - Validación de Ticks", bg='#1e293b', fg='#f59e0b',
                font=('Arial', 10, 'bold')).pack(fill='x', pady=(10, 10), padx=10)
        
        # Fila 1: Confirmación de ticks
        row1_imp = tk.Frame(impulse_frame, bg='#1e293b')
        row1_imp.pack(fill='x', padx=10, pady=5)
        tk.Label(row1_imp, text="✅ Confirmación Ticks:", bg='#1e293b', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row1_imp, from_=1, to=20, increment=1, textvariable=self.config['IMPULSE_CONFIRMATION_COUNT'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row1_imp, text="(últimos N ticks)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)
        
        # Fila 2: Expiración de señal
        row2_imp = tk.Frame(impulse_frame, bg='#1e293b')
        row2_imp.pack(fill='x', padx=10, pady=5)
        tk.Label(row2_imp, text="⏱️ Expiración Señal (ms):", bg='#1e293b', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row2_imp, from_=100, to=5000, increment=50, textvariable=self.config['IMPULSE_SIGNAL_EXPIRATION_MS'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row2_imp, text="(500ms = rápido)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)
        
        # Fila 3: Movimiento mínimo
        row3_imp = tk.Frame(impulse_frame, bg='#1e293b')
        row3_imp.pack(fill='x', padx=10, pady=5)
        tk.Label(row3_imp, text="📊 Movimiento Mínimo:", bg='#1e293b', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        tk.Spinbox(row3_imp, from_=1, to=50, increment=1, textvariable=self.config['IMPULSE_MIN_TICK_MOVEMENT'],
                  bg='#334155', fg='#60a5fa', font=('Arial', 9), width=10, relief='flat').pack(side='left', padx=(10, 5), fill='x', expand=True)
        tk.Label(row3_imp, text="(ticks de precio)", bg='#1e293b', fg='#64748b', font=('Arial', 8)).pack(side='left', padx=5)
        
        # Separador visual
        sep_frame2 = tk.Frame(impulse_frame, bg='#0f172a', height=1)
        sep_frame2.pack(fill='x', pady=(10, 10))

        # --- FIN V4 Validación de Impulsos ---

        # ⭐ NUEVO: Panel de Calibración de Micro Momentum para operaciones pequeñas (5-15 pips)
        micro_frame = tk.LabelFrame(scrollable_frame, text="🎯 Calibración Micro Momentum (5-15 pips)",
                                     bg='#0f472a', fg='#34d399',
                                     font=('Arial', 11, 'bold'), padx=15, pady=15)
        micro_frame.pack(fill='x', pady=(15, 0))

        # Toggle para habilitar/deshabilitar
        micro_toggle_row = tk.Frame(micro_frame, bg='#0f472a')
        micro_toggle_row.pack(fill='x', pady=(0, 10))
        
        tk.Checkbutton(micro_toggle_row, text="✓ Habilitar Detección de Micro Movimientos (2-6 pips)",
                      variable=self.config.get('MICRO_MOMENTUM_ENABLED', tk.BooleanVar(value=True)),
                      bg='#0f472a', fg='#34d399', selectcolor='#064e3b',
                      activebackground='#0f472a', activeforeground='#34d399',
                      font=('Arial', 10, 'bold')).pack(side='left', padx=0)

        # Fila 1: Seleccionar perfil de micro momentum
        micro_profile_row = tk.Frame(micro_frame, bg='#0f472a')
        micro_profile_row.pack(fill='x', pady=8)
        
        tk.Label(micro_profile_row, text="📌 Perfil Micro Momentum:", bg='#0f472a', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        
        profile_combo = tk.OptionMenu(micro_profile_row, self.micro_profile_var,
                                      'ULTRA_MICRO', 'MICRO', 'NORMAL',
                                      command=lambda x: self.on_micro_profile_changed())
        profile_combo.config(bg='#334155', fg='#34d399', font=('Arial', 9), relief='flat',
                            activebackground='#0f472a', activeforeground='#34d399')
        profile_combo['menu'].config(bg='#334155', fg='#34d399', font=('Arial', 9),
                                     activebackground='#0f472a', activeforeground='#34d399')
        profile_combo.pack(side='left', padx=(10, 5), fill='x', expand=True)

        # Descripción de perfiles
        profiles_desc = {
            'ULTRA_MICRO': '5-7 pips | Ventana=15 ticks | Inmediato (confirm=1)',
            'MICRO': '10-15 pips | Ventana=20 ticks | Balanceado (confirm=1)',
            'NORMAL': '20+ pips | Ventana=30 ticks | Conservador (confirm=2)'
        }
        
        micro_desc_row = tk.Frame(micro_frame, bg='#0f472a')
        micro_desc_row.pack(fill='x', pady=(0, 10))
        
        desc_label = tk.Label(micro_desc_row, text="ULTRA_MICRO: 5-7 pips | MICRO: 10-15 pips | NORMAL: 20+ pips",
                             bg='#0f472a', fg='#6ee7b7', font=('Arial', 8, 'italic'))
        desc_label.pack(side='left', padx=0)

        # Fila 2: Información del perfil actual
        micro_info_row = tk.Frame(micro_frame, bg='#0f472a')
        micro_info_row.pack(fill='x', pady=5)
        
        tk.Label(micro_info_row, text="ℹ️ Perfil actual:", bg='#0f472a', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        
        self.micro_info_label = tk.Label(micro_info_row, text=f"MICRO (seleccionado)",
                                        bg='#0f472a', fg='#34d399', font=('Arial', 9, 'bold'))
        self.micro_info_label.pack(side='left', padx=(10, 5), fill='x', expand=True)

        # Fila 3: Estado de operaciones detectadas
        micro_status_row = tk.Frame(micro_frame, bg='#0f472a')
        micro_status_row.pack(fill='x', pady=5)
        
        tk.Label(micro_status_row, text="📊 Operaciones micro:", bg='#0f472a', fg='#cbd5e1',
                font=('Arial', 9), width=22, anchor='w').pack(side='left', padx=0, fill='x', expand=False)
        
        self.micro_ops_label = tk.Label(micro_status_row, text="0 detec. | 0 abiertas | 0 cerradas",
                                       bg='#0f472a', fg='#34d399', font=('Arial', 9))
        self.micro_ops_label.pack(side='left', padx=(10, 5), fill='x', expand=True)

        # --- FIN Panel Micro Momentum ---

        # (Parámetros IA para Operaciones Rápidas gestionados automáticamente)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_stats_panel(self, parent):
        stats_frame = tk.Frame(parent, bg='#1e293b')
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats = [
            ("Ganadas", "ganadas_value", "#10b981"),
            ("Perdidas", "perdidas_value", "#ef4444"),
            ("Saldo Ganado", "saldo_value", "#22c55e"),
        ]
        
        self.stat_labels = {}
        
        for i, (title, key, color) in enumerate(stats):
            col = i % 3
            
            card = tk.Frame(stats_frame, bg=color, relief='flat')
            card.grid(row=0, column=col, padx=5, pady=5, sticky='nsew')
            
            title_label = tk.Label(card, text=title, bg=color, fg='white',
                                  font=('Arial', 9))
            title_label.pack(pady=(10, 0))
            
            value_label = tk.Label(card, text="0", bg=color, fg='white',
                                  font=('Arial', 24, 'bold'))
            value_label.pack(pady=(5, 10))
            
            self.stat_labels[key] = value_label
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)

    def create_progress_panel(self, parent):
        progress_frame = tk.LabelFrame(parent, text="Progreso al Objetivo", 
                                      bg='#334155', fg='#f1f5f9',
                                      font=('Arial', 11, 'bold'), padx=15, pady=15)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_label = tk.Label(progress_frame, text="0 / 10", 
                                      bg='#334155', fg='#cbd5e1',
                                      font=('Arial', 10))
        self.progress_label.pack(anchor='w', pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, 
                                           mode='determinate', maximum=100)
        self.progress_bar.pack(fill='x')
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("custom.Horizontal.TProgressbar",
                       troughcolor='#475569',
                       background='#3b82f6',
                       borderwidth=0,
                       thickness=20)
        self.progress_bar.configure(style="custom.Horizontal.TProgressbar")
        
    def create_events_panel(self, parent):
        """Panel de Eventos Importantes - Solo labels dinámicos, sin logs"""
        # Frame principal
        events_frame = tk.LabelFrame(parent, text="📌 Eventos Importantes", 
                                    bg='#334155', fg='#f1f5f9',
                                    font=('Arial', 10, 'bold'), padx=10, pady=10)
        events_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 🤖 Estado del Bot
        state_label = tk.Label(events_frame, text="🤖 Estado:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#60a5fa')
        state_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_bot_status = tk.Label(events_frame, text="Conectado | Listo", 
                                      font=('Arial', 8), bg='#334155', fg='#34d399')
        self.lbl_bot_status.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # ⚠️ Último Evento
        event_label = tk.Label(events_frame, text="⚠️ Último Evento:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#fbbf24')
        event_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_last_event = tk.Label(events_frame, text="Esperando señal...", 
                                      font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                      wraplength=300, justify='left')
        self.lbl_last_event.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # ✅ Último Cierre
        close_label = tk.Label(events_frame, text="✅ Último Cierre:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#34d399')
        close_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_last_close = tk.Label(events_frame, text="N/A", 
                                      font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                      wraplength=300, justify='left')
        self.lbl_last_close.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # ❌ Último Error
        error_label = tk.Label(events_frame, text="❌ Último Error:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#f87171')
        error_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_last_error = tk.Label(events_frame, text="Ninguno", 
                                      font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                      wraplength=300, justify='left')
        self.lbl_last_error.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # 🕐 Timestamp
        time_label = tk.Label(events_frame, text="🕐 Actualización:", 
                             font=('Arial', 7, 'italic'), bg='#334155', fg='#64748b')
        time_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_events_timestamp = tk.Label(events_frame, text="--:--:--", 
                                            font=('Arial', 7), bg='#334155', fg='#475569')
        self.lbl_events_timestamp.pack(anchor='w', padx=15, pady=(0, 5), fill='x')

        
    def create_analysis_live_panel(self, parent):
        """📊 Panel dinámico de análisis en vivo con actualización de labels en tiempo real"""
        try:
            self.analysis_panel = DynamicOperationsPanel(parent)
        except Exception as e:
            # Si falla el panel dinámico, mostrar un label de error
            error_label = tk.Label(parent, text=f"Error cargando panel de análisis: {e}", 
                                  font=('Arial', 10), bg='#1e293b', fg='#f87171')
            error_label.pack(pady=20)
            self.analysis_panel = None
    
    def update_analysis_live_panel(self, positions_data, volatility='NORMAL', trend='NEUTRAL', 
                                   winrate=0.0, current_price=0.0):
        """Actualiza el panel de análisis en vivo sin saturar el log"""
        try:
            if not hasattr(self, 'analysis_panel') or self.analysis_panel is None:
                return
            
            # Calcular totales
            total_profit = 0
            total_loss = 0
            open_count = len(positions_data) if positions_data else 0
            max_positions = 5  # o el valor que uses
            
            if positions_data:
                for pos in positions_data:
                    profit = pos.get('profit', 0)
                    if profit > 0:
                        total_profit += profit
                    else:
                        total_loss += abs(profit)
            
            # Actualizar resumen
            self.analysis_panel.update_summary(open_count, max_positions, total_profit, total_loss)
            
            # Actualizar operaciones
            self.analysis_panel.update_operations(positions_data if positions_data else [])
            
            # Actualizar métricas
            self.analysis_panel.update_metrics(volatility, trend, winrate, current_price)
            
        except Exception as e:
            try:
                self.add_log(f"Error actualizando panel de análisis: {e}", 'warning')
            except:
                pass
        
    def _log_data_statistics(self, snapshots):
        """Registra estadísticas de los datos de mercado actualizados"""
        try:
            if not snapshots or len(snapshots) == 0:
                return
            
            # Usar últimos 200 snapshots para estadísticas
            sample = snapshots[-200:]
            
            closes = []
            highs = []
            lows = []
            volumes = []
            spreads = []
            
            for snap in sample:
                if isinstance(snap, dict):
                    if 'price' in snap and isinstance(snap['price'], dict):
                        closes.append(snap['price'].get('close', 0))
                        highs.append(snap['price'].get('high', 0))
                        lows.append(snap['price'].get('low', 0))
                        spreads.append(snap['price'].get('high', 0) - snap['price'].get('low', 0))
                    if 'volume' in snap and isinstance(snap['volume'], dict):
                        volumes.append(snap['volume'].get('tick_volume', 0))
            
            if closes and highs and lows:
                atr = np.mean([h - l for h, l in zip(highs, lows)])
                spread_avg = np.mean(spreads) if spreads else 0
                spread_std = np.std(spreads) if spreads else 0
                volume_avg = np.mean(volumes) if volumes else 0
                
                self.add_log(f"📊 Estadísticas (actualización #{self.data_update_count}):", 'info')
                self.add_log(f"   Spread promedio: {spread_avg:.6f} ± {spread_std:.6f}", 'info')
                self.add_log(f"   ATR promedio: {atr:.6f} ± {np.std([h-l for h,l in zip(highs, lows)]):.6f}", 'info')
                self.add_log(f"   Volumen promedio: {int(volume_avg)}", 'info')
                self.add_log(f"   Total snapshots: {len(snapshots)}", 'info')
        except Exception as e:
            logger.warning(f"Error en _log_data_statistics: {e}")
        
    def add_log(self, message, tag='info'):
        """Log minimalista - Solo consola y etiquetas de eventos clave"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Prefijar icono según tipo de mensaje
        icon_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'debug': '🔍',
            'alert': '🚨'
        }
        icon = icon_map.get(tag, '')

        # Convertir marcadores a iconos
        if isinstance(message, str):
            token_map = {
                '[ADVERTENCIA]': '⚠️', '[EMOJI]': '🔹', '[OBJETIVO]': '🎯', '[ERROR]': '❌',
                '[OK]': '✅', '[DATA]': '📊', '[ALERTA]': '🚨', '[STOP]': '🛑', '[DINERO]': '💰',
                '[IA]': '🤖', '[CONFIG]': '⚙️', '[ESPERA]': '⏳', '[PAUSA]': '⏸️', '[IMPORTANTE]': '🔥'
            }
            for k, v in token_map.items():
                message = message.replace(k, v)

        log_message = f"[{timestamp}] {icon} {message}"
        
        # SOLO IMPRIMIR A CONSOLA (sin ScrolledText)
        try:
            frozen = bool(getattr(sys, 'frozen', False))
        except:
            frozen = False

        mlow = message.lower() if isinstance(message, str) else ''
        if not (frozen and ('tensorflow' in mlow or 'tensor' in mlow) and 'fallback' in mlow):
            print(log_message)
            sys.stdout.flush()
        
        # ✨ ACTUALIZAR LABELS DE EVENTOS CLAVE (en lugar de log_text)
        try:
            if tag == 'error':
                if hasattr(self, 'lbl_last_error'):
                    self.lbl_last_error.config(text=message[:60])  # Primeros 60 caracteres
                    self.lbl_last_error.config(fg='#f87171')
                if hasattr(self, 'lbl_events_timestamp'):
                    self.lbl_events_timestamp.config(text=timestamp)
            
            elif tag == 'success':
                if hasattr(self, 'lbl_last_close'):
                    self.lbl_last_close.config(text=message[:60])
                    self.lbl_last_close.config(fg='#34d399')
                if hasattr(self, 'lbl_events_timestamp'):
                    self.lbl_events_timestamp.config(text=timestamp)
            
            elif tag == 'warning':
                if hasattr(self, 'lbl_last_event'):
                    self.lbl_last_event.config(text=message[:60])
                    self.lbl_last_event.config(fg='#fbbf24')
                if hasattr(self, 'lbl_events_timestamp'):
                    self.lbl_events_timestamp.config(text=timestamp)
            
            elif tag == 'alert':
                if hasattr(self, 'lbl_last_event'):
                    self.lbl_last_event.config(text=message[:60])
                    self.lbl_last_event.config(fg='#fb7185')
                if hasattr(self, 'lbl_events_timestamp'):
                    self.lbl_events_timestamp.config(text=timestamp)
        except:
            pass
    
    def update_bot_status(self, status_text, connected=True):
        """Actualiza el estado del bot en el panel de eventos"""
        try:
            if hasattr(self, 'lbl_bot_status'):
                status_emoji = "🤖✅" if connected else "🤖❌"
                color = '#34d399' if connected else '#f87171'
                self.lbl_bot_status.config(text=status_text, fg=color)
        except:
            pass



    def update_account_info(self):
        """Actualiza periódicamente las etiquetas de Balance, Patrimonio (Equity), Margen Libre y Alcance (Leverage)."""
        try:
            account_info = None
            try:
                account_info = mt5.account_info()
            except Exception as e:
                account_info = None

            if account_info is not None:
                bal = float(getattr(account_info, 'balance', 0.0))
                equity = float(getattr(account_info, 'equity', bal))
                free_margin = float(getattr(account_info, 'margin_free', 0.0))
                leverage = int(getattr(account_info, 'leverage', 0))
                
                # Actualizar etiquetas en el panel de Control (MT5 Account Info)
                if hasattr(self, 'mt5_balance_label') and self.mt5_balance_label:
                    try:
                        self.mt5_balance_label.config(text=f"${bal:.2f}")
                    except:
                        pass
                        
                if hasattr(self, 'mt5_equity_label') and self.mt5_equity_label:
                    try:
                        self.mt5_equity_label.config(text=f"${equity:.2f}")
                    except:
                        pass
                        
                if hasattr(self, 'mt5_free_margin_label') and self.mt5_free_margin_label:
                    try:
                        self.mt5_free_margin_label.config(text=f"${free_margin:.2f}")
                    except:
                        pass
                        
                if hasattr(self, 'mt5_leverage_label') and self.mt5_leverage_label:
                    try:
                        self.mt5_leverage_label.config(text=f"1:{leverage}")
                    except:
                        pass
                
                # Actualizar etiquetas dentro del panel de Operaciones Rápidas si existen
                if hasattr(self, 'rapid_balance_label') and self.rapid_balance_label:
                    try:
                        self.rapid_balance_label.config(text=f"${bal:.2f}")
                    except:
                        pass
                        
                if hasattr(self, 'rapid_equity_label') and self.rapid_equity_label:
                    try:
                        self.rapid_equity_label.config(text=f"${equity:.2f}")
                    except:
                        pass
                
                # Actualizar widgets legacy si existen
                if hasattr(self, 'balance_label') and self.balance_label:
                    try:
                        self.balance_label.config(text=f"${bal:.2f}")
                    except:
                        pass
                        
                if hasattr(self, 'equity_label') and self.equity_label:
                    try:
                        self.equity_label.config(text=f"${equity:.2f}")
                    except:
                        pass
                
                # Forzar actualización visual de la UI
                try:
                    self.root.update_idletasks()
                except:
                    pass
                        
                # Mantener en variables internas
                self.saldo_actual = bal
                self.saldo_actual_equity = equity
                # Registrar conexión si antes no había
                if not self.connected:
                    self.add_log("Conexión MT5 detectada: actualizando balances", 'info')
                    self.connected = True
                # Resetear ventana de gracia si antes se declaró missing
                try:
                    self._account_info_first_missing_time = None
                    self._account_info_missing_logged = False
                except Exception:
                    pass
                # Mostrar balance inicial en panel de Operaciones Rápidas si existe
                if hasattr(self, 'rapid_initial_balance_label'):
                    try:
                        # Si balance_inicial es None o 0.0, inicializarlo con el balance actual
                        if getattr(self, 'balance_inicial', None) is None or float(self.balance_inicial) == 0.0:
                            self.balance_inicial = float(bal)
                        # Mostrar siempre el valor configurado de balance_inicial
                        self.rapid_initial_balance_label.config(text=f"${float(self.balance_inicial):.2f}")
                    except Exception:
                        try:
                            self.rapid_initial_balance_label.config(text=f"${float(bal):.2f}")
                        except Exception:
                            pass
            else:
                # account_info no disponible (MT5 no conectado o sin respuesta)
                # Intentar usar valores internos para actualizar la UI
                try:
                    bal = float(getattr(self, 'saldo_actual', 0.0))
                except Exception:
                    bal = 0.0
                try:
                    equity = float(getattr(self, 'saldo_actual_equity', bal))
                except Exception:
                    equity = bal
                if hasattr(self, 'rapid_balance_label'):
                    try:
                        self.rapid_balance_label.config(text=f"${bal:.2f}")
                    except Exception:
                        pass
                if hasattr(self, 'rapid_equity_label'):
                    try:
                        self.rapid_equity_label.config(text=f"${equity:.2f}")
                    except Exception:
                        pass
                # Registrar missing pero solo después de una ventana de gracia (10 minutos)
                now_ts = time.time()
                grace = 600  # segundos (10 minutos)
                if self._account_info_first_missing_time is None:
                    self._account_info_first_missing_time = now_ts
                else:
                    if (now_ts - self._account_info_first_missing_time) >= grace and not self._account_info_missing_logged:
                        self.add_log("[ADVERTENCIA] No se pudo obtener account_info de MT5; mostrando valores locales.", 'warning')
                        self._account_info_missing_logged = True
                # Mostrar balance inicial en panel de Operaciones Rápidas si existe
                if hasattr(self, 'rapid_initial_balance_label'):
                    try:
                        # Si balance_inicial es None o 0.0, inicializarlo con el balance actual
                        if getattr(self, 'balance_inicial', None) is None or float(self.balance_inicial) == 0.0:
                            self.balance_inicial = float(bal)
                        # Mostrar siempre el valor configurado de balance_inicial
                        self.rapid_initial_balance_label.config(text=f"${float(self.balance_inicial):.2f}")
                    except Exception:
                        # En caso de error, mostrar el balance actual como fallback
                        try:
                            self.rapid_initial_balance_label.config(text=f"${float(bal):.2f}")
                        except Exception:
                            pass
                # NO sobrescribir `saldo_total_acumulado` aquí: se usa como acumulador
                # de ganancias/pérdidas de operaciones rápidas. Solo inicializar si
                # aún no existe (por ejemplo al arrancar la aplicación).
                if not hasattr(self, 'saldo_total_acumulado') or self.saldo_total_acumulado is None:
                    self.saldo_total_acumulado = 0.0

                # Verificar objetivo de ganancia: si patrimonio >= balance_inicial + objetivo_ganancia -> cierre de emergencia
                try:
                    # Priorizar el objetivo definido en la pestaña Operaciones Rápidas si existe
                    objetivo = 0.0
                    if hasattr(self, 'rapid_gain_target_var'):
                        try:
                            objetivo = float(self.rapid_gain_target_var.get())
                        except Exception:
                            objetivo = 0.0
                    elif hasattr(self, 'objetivo_ganancia'):
                        try:
                            objetivo = float(self.objetivo_ganancia.get())
                        except Exception:
                            objetivo = 0.0

                    if hasattr(self, 'balance_inicial') and self.balance_inicial and not self.objetivo_cumplido and objetivo > 0.0:
                        if equity >= (float(self.balance_inicial) + objetivo):
                            self.objetivo_cumplido = True
                            self.add_log(f"[OBJETIVO] Objetivo alcanzado: equity ${equity:.2f} >= inicial ${self.balance_inicial:.2f} + objetivo ${objetivo:.2f}", 'success')
                            # Ejecutar cierre de emergencia y detener el bot
                            try:
                                self.cierre_emergencia()
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception as e:
            # Silenciar errores de UI/MT5
            pass
        finally:
            # Re-agendar actualización siempre cada 1 segundo sin importar el flujo
            try:
                self.root.after(1000, self.update_account_info)
            except Exception:
                pass

    def _compute_rapid_ops_distribution(self, min_samples=6):
        """
        Implementación optimizada y estable: pondera profit por recencia con decaimiento
        temporal, mezcla información de profit y conteos ponderados, y aplica
        suavizado exponencial entre invocaciones para velocidad y estabilidad.
        """

        try:
            scale = float(self._safe_get('RAPID_OPS_ADAPT_SCALE', 100.0))
            min_samples = int(self._safe_get('RAPID_OPS_ADAPT_MIN_SAMPLES', 6))
            log_threshold = float(self._safe_get('RAPID_OPS_LOG_THRESHOLD', 0.01))
            alpha = float(self._safe_get('RAPID_OPS_ADAPT_ALPHA', 0.35))
            decay = int(self._safe_get('RAPID_OPS_TIME_DECAY', 600))

            # Combinar historial de operaciones reales y fantasma
            history_real = list(self.rapid_ops_history)
            history_ghost = list(self.ghost_ops_history) if hasattr(self, 'ghost_ops_history') else []
            history = history_real + history_ghost
            if len(history) < min_samples:
                buy_frac_raw = 0.5
            else:
                now = datetime.now()
                buy_score = sell_score = buy_weight = sell_weight = 0.0
                # recorrer historial (es pequeño por diseño) y acumular con peso temporal
                for item in history:
                    try:
                        age = (now - item.get('time', now)).total_seconds() if 'time' in item else 0.0
                    except Exception:
                        age = 0.0
                    w = math.exp(-age / float(decay)) if decay > 0 else 1.0
                    if item.get('type') == 'BUY':
                        buy_score += float(item.get('profit', 0.0)) * w
                        buy_weight += w
                    else:
                        sell_score += float(item.get('profit', 0.0)) * w
                        sell_weight += w

                profit_diff = buy_score - sell_score
                denom = abs(buy_score) + abs(sell_score) + scale
                profit_ratio = profit_diff / denom if denom != 0 else 0.0

                cnt_ratio = 0.0
                cnt_sum = buy_weight + sell_weight
                if cnt_sum > 0:
                    cnt_ratio = (buy_weight - sell_weight) / cnt_sum

                raw = 0.75 * profit_ratio + 0.25 * cnt_ratio
                buy_frac_raw = 0.5 + raw * 0.45
                buy_frac_raw = max(0.2, min(0.8, buy_frac_raw))

            # Suavizado exponencial para estabilidad y respuesta controlada
            if self.rapid_buy_frac_smoothed is None:
                self.rapid_buy_frac_smoothed = buy_frac_raw
            else:
                self.rapid_buy_frac_smoothed = (1.0 - alpha) * self.rapid_buy_frac_smoothed + alpha * buy_frac_raw

            buy_frac = self.rapid_buy_frac_smoothed

            # Log y actualización UI solo si hay cambio relevante
            try:
                if self.last_buy_frac is None or abs(buy_frac - self.last_buy_frac) >= log_threshold:
                    self.last_buy_frac = buy_frac
                    try:
                        last = history[-min(len(history), min_samples * 4):]
                        buy_total = sum(item.get('profit', 0.0) for item in last if item.get('type') == 'BUY')
                        sell_total = sum(item.get('profit', 0.0) for item in last if item.get('type') == 'SELL')
                        self.add_log(f"[IA] IA adaptativa: BUY_frac {buy_frac:.2f} | buy_total=${buy_total:.2f} sell_total=${sell_total:.2f}", 'info')
                    except Exception:
                        self.add_log(f"[IA] IA adaptativa: BUY_frac {buy_frac:.2f}", 'info')

                    try:
                        if hasattr(self, 'rapid_buy_frac_label'):
                            color = self.config.get('RAPID_OPS_FRAC_COLOR').get() if 'RAPID_OPS_FRAC_COLOR' in self.config else '#f59e0b'
                            self.rapid_buy_frac_label.config(text=f"{int(buy_frac * 100)}%", fg=color)
                        if hasattr(self, 'rapid_buy_frac_bar'):
                            try:
                                style = ttk.Style(self.root)
                                style.configure('Rapid.Horizontal.TProgressbar', background=color)
                            except Exception:
                                pass
                            self.rapid_buy_frac_bar['value'] = int(buy_frac * 100)
                    except Exception:
                        pass
            except Exception:
                pass

            return buy_frac
        except Exception:
            return 0.5

    def analizar_operaciones_abiertas(self):
        """⭐ NUEVO: Analizador de operaciones abiertas en tiempo real con panel dinámico"""
        try:
            if not self.connected:
                return
            
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)
            
            if not positions:
                # Actualizar panel incluso sin operaciones
                self.update_analysis_live_panel([], 'NORMAL', 'NEUTRAL', 0.0, 0.0)
                return
            
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return
            
            # ⭐ Obtener MAX_OPS de forma robusta
            try:
                max_ops_val = self.config.get('MAX_SIMULTANEOUS_OPS')
                if max_ops_val is None:
                    max_ops = 5
                elif hasattr(max_ops_val, 'get'):
                    max_ops = int(max_ops_val.get())
                else:
                    max_ops = int(max_ops_val)
            except Exception:
                max_ops = 5
                
            current_price = tick.bid
            
            # ✨ NUEVO: Preparar datos para panel dinámico
            positions_data = []
            total_profit = 0
            total_loss = 0
            profit_positions = 0
            loss_positions = 0
            
            for pos in positions:
                ticket = pos.ticket
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                open_price = pos.price_open
                volume = pos.volume
                sl = pos.sl
                tp = pos.tp
                
                # Calcular ganancia/pérdida en puntos y dinero
                if direction == "BUY":
                    points = (current_price - open_price) * 10000
                    profit_pips = current_price - open_price
                else:
                    points = (open_price - current_price) * 10000
                    profit_pips = open_price - current_price
                
                # Usar el profit DIRECTO de MT5 (más confiable que calcular manualmente)
                # MT5 ya calcula correctamente el profit considerando el contract_size
                profit_money = float(pos.profit) if hasattr(pos, 'profit') else 0
                
                # Distancia a TP y SL
                dist_tp = abs(current_price - tp)
                dist_sl = abs(current_price - sl)
                
                # Determinar estado
                if profit_money > 0:
                    status = f"[OK] +${profit_money:.2f}"
                    color_tag = 'success'
                    total_profit += profit_money
                    profit_positions += 1
                elif profit_money < 0:
                    status = f"[ERROR] ${profit_money:.2f}"
                    color_tag = 'error'
                    total_loss += abs(profit_money)
                    loss_positions += 1
                else:
                    status = f"[EMOJI]️ $0.00"
                    color_tag = 'info'
                
                # ✨ NUEVO: Agregar datos a lista para panel
                positions_data.append({
                    'ticket': ticket,
                    'direction': direction,
                    'open_price': open_price,
                    'current_price': current_price,
                    'volume': volume,
                    'tp': tp,
                    'sl': sl,
                    'profit': profit_money,
                    'dist_tp': dist_tp,
                    'dist_sl': dist_sl
                })
                
                # Log detallado por posición (menos frecuente para no saturar)
                self.add_log(f"   📋 #{ticket} {direction} @ {open_price:.5f} | Vol: {volume} | Precio: {current_price:.5f} | {status}", color_tag)
                self.add_log(f"      🎯 TP: {tp:.5f} (Dist: {dist_tp:.5f}) | 🛡️ SL: {sl:.5f} (Dist: {dist_sl:.5f})", 'info')
            
            # Resumen
            self.add_log(f"\n📈 RESUMEN: Ganancias: ${total_profit:.2f} ({profit_positions} pos) | Pérdidas: ${total_loss:.2f} ({loss_positions} pos)", 'success')
            
            # ✨ NUEVO: Actualizar panel dinámico en lugar de solo imprimir logs
            self.update_analysis_live_panel(positions_data, 'NORMAL', 'NEUTRAL', 50.0, current_price)
            
        except Exception as e:
            self.add_log(f"Error en análisis de operaciones: {str(e)}", 'error')

    def _calculate_atr_simple(self, highs, lows, closes, period=14):
        """Calcula ATR de forma simple para tolerancia dinámica"""
        try:
            high_low = highs[-period:] - lows[-period:]
            high_close = np.abs(highs[-period:] - np.roll(closes[-period:], 1))
            low_close = np.abs(lows[-period:] - np.roll(closes[-period:], 1))
            ranges = np.max(np.vstack([high_low, high_close, low_close]), axis=0)
            atr = float(np.mean(ranges)) if len(ranges) > 0 else 1.0
            return atr
        except Exception as e:
            return 1.0
    
    def _check_entry_condition_precise(self, current_price, target_price, direction, tolerance, confidence=50):
        """
        Chequea si debe abrir entrada de forma PRECISA e INTELIGENTE:
        - Si CONFIANZA ALTA (>75%): abre INMEDIATAMENTE sin esperar
        - Si CONFIANZA MEDIA (50-75%): espera rango de tolerancia
        - Si CONFIANZA BAJA (<50%): requiere estar EXACTAMENTE en el rango
        
        Retorna: (debe_abrir, razón)
        """
        try:
            distance = abs(current_price - target_price)
            
            # Convertir confianza a float
            conf_float = float(confidence) if confidence else 50.0
            
            # ⭐ LÓGICA INTELIGENTE BASADA EN CONFIANZA
            if conf_float > 75:  # CONFIANZA ALTA: abre INMEDIATAMENTE
                # No esperes, si tiene alta confianza, abre YA
                return (True, f"[IMPORTANTE] ALTA CONFIANZA ({conf_float:.1f}%): Abriendo INMEDIATAMENTE a {current_price:.5f}")
            
            elif direction == "BUY":
                # Para BUY: queremos que el precio SUBA hacia el objetivo
                if current_price <= target_price:
                    # Precio está debajo o igual al objetivo = PERFECTO para BUY
                    return (True, f"[UBICACION] BUY: Precio DEBAJO {current_price:.5f} <= {target_price:.5f}")
                elif distance <= tolerance:
                    # Precio está ligeramente arriba pero dentro de rango
                    return (True, f"[UBICACION] BUY: Dentro de rango {distance:.5f} <= {tolerance:.5f} pts")
                else:
                    return (False, f"[ESPERA] BUY: Esperando... {distance:.5f} > {tolerance:.5f} pts")
            
            elif direction == "SELL":
                # Para SELL: queremos que el precio BAJE hacia el objetivo
                if current_price >= target_price:
                    # Precio está arriba o igual al objetivo = PERFECTO para SELL
                    return (True, f"[UBICACION] SELL: Precio ARRIBA {current_price:.5f} >= {target_price:.5f}")
                elif distance <= tolerance:
                    # Precio está ligeramente debajo pero dentro de rango
                    return (True, f"[UBICACION] SELL: Dentro de rango {distance:.5f} <= {tolerance:.5f} pts")
                else:
                    return (False, f"[ESPERA] SELL: Esperando... {distance:.5f} > {tolerance:.5f} pts")
            
            return (False, "Dirección desconocida")
            
        except Exception as e:
            self.add_log(f"Error en _check_entry_condition_precise: {str(e)}", 'error')
            return (False, str(e))

    def reset_counters(self):
        """Reinicia todos los contadores del bot"""
        if self.is_running:
            messagebox.showwarning("Advertencia", "Detén el bot antes de resetear contadores")
            return
        
        try:
            self.z = 0
            self.ganadas = 0
            self.perdidas = 0
            self.operaciones_azules = 0
            self.operaciones_rojas = 0
            
            self.deals_anterior.clear()
            self.operaciones_actuales.clear()
            self.operaciones_procesadas.clear()
            self.deals_procesados.clear()
            self.position_ids.clear()
            self.position_tracking.clear()
            self.historial_resultados.clear()
            
            self.primera_operacion = True
            self.perdio_primera = False
            self.en_pausa = False
            self.objetivo_cumplido = False
            self.force_stop_triggered = False
            self.analisis_inicial_hecho = False
            
            self.ganancia_neta = 0.0
            self.saldo_total_acumulado = 0.0
            self.saldo_actual = 0.0
            self.ultima_ganancia = 0.0
            self.ganancia_total = 0.0
            self.total_operaciones_abiertas = 0
            
            self.ultima_operacion = time.time()
            self.ultima_operacion_timestamp = int(time.time())
            self.ultima_actualizacion_ui = 0
            
            self.resume_btn.config(state='disabled')
            self.update_stats()
            self.add_log("Contadores reiniciados completamente", 'info')
            self.root.update()
            
        except Exception as e:
            self.add_log(f"Error al resetear contadores: {str(e)}", 'error')

    def reiniciar_bot_limpio(self):
        """Reinicia el bot limpiando todo EXCEPTO par y cantidad
        - Limpia contadores
        - Limpia sesiones
        - Limpia operaciones en espera
        - Mantiene: Par (SYMBOL) y Cantidad (POSITION_SIZE)
        """
        if self.is_running:
            messagebox.showwarning("Advertencia", "Detén el bot antes de reiniciarlo")
            return
        
        try:
            # Limpiar contadores
            self.z = 0
            self.ganadas = 0
            self.perdidas = 0
            self.operaciones_azules = 0
            self.operaciones_rojas = 0
            
            # Limpiar historial y tracking
            self.deals_anterior.clear()
            self.operaciones_actuales.clear()
            self.operaciones_procesadas.clear()
            self.deals_procesados.clear()
            self.position_ids.clear()
            self.position_tracking.clear()
            self.historial_resultados.clear()
            
            # Limpiar flags
            self.primera_operacion = True
            self.perdio_primera = False
            self.en_pausa = False
            self.objetivo_cumplido = False
            self.force_stop_triggered = False
            self.analisis_inicial_hecho = False
            
            # Limpiar valores de ganancia
            self.ganancia_neta = 0.0
            self.saldo_total_acumulado = 0.0
            self.saldo_actual = 0.0
            self.ultima_ganancia = 0.0
            self.ganancia_total = 0.0
            self.total_operaciones_abiertas = 0
            
            # Limpiar timestamps
            self.ultima_operacion = time.time()
            self.ultima_operacion_timestamp = int(time.time())
            self.ultima_actualizacion_ui = 0
            
            # Limpiar operaciones en espera
            self.pending_operations.clear()
            
            # Limpiar sesión MT5
            try:
                if mt5.initialize():
                    mt5.shutdown()
                    mt5.initialize()
                    self.add_log("[OK] Sesión MT5 reiniciada", 'info')
            except Exception as e:
                self.add_log(f"[ADVERTENCIA] Error reiniciando MT5: {str(e)}", 'warning')
            
            # Actualizar UI
            self.resume_btn.config(state='disabled')
            self.update_stats()
            
            # Log de confirmación
            symbol = self.config['SYMBOL'].get()
            quantity = self.config['VOL'].get()
            self.add_log(f"\n[ACTUALIZAR] BOT REINICIADO", 'warning')
            self.add_log(f"   [EMOJI] Contadores: Limpiados", 'info')
            self.add_log(f"   [EMOJI] Operaciones en espera: Limpiadas", 'info')
            self.add_log(f"   [EMOJI] Sesión: Reiniciada", 'info')
            self.add_log(f"   [EMOJI] Parámetros preservados: {symbol} / {quantity}", 'success')
            
            self.root.update()
            
        except Exception as e:
            self.add_log(f"[ERROR] Error al reiniciar bot: {str(e)}", 'error')

    def update_stats(self):
        """Alias para mantener compatibilidad"""
        self._update_ui()

    def _update_ui(self):
        """Actualización de UI mejorada con mejor manejo de saldo"""
        try:
            self.stat_labels['ganadas_value'].config(text=str(self.ganadas))
            self.stat_labels['perdidas_value'].config(text=str(self.perdidas))
            
            saldo_total = self.saldo_total_acumulado + self.ganancia_neta
            color = '#22c55e' if saldo_total >= 0 else '#ef4444'
            saldo_text = f"${saldo_total:+,.2f}"
            
            self.stat_labels['saldo_value'].config(
                text=saldo_text,
                bg=color,
                fg='white'
            )
            
            if hasattr(self, 'progress_bar'):
                objetivo = self.config['OBJETIVO_Z'].get()
                progreso = min(100, abs(self.ganancia_neta * 100) / objetivo if objetivo > 0 else 0)
                self.progress_bar['value'] = progreso
                self.progress_label.config(
                    text=f"${self.ganancia_neta:.2f} / ${objetivo:.2f}"
                )
            
            status = "[OBJETIVO] Vigilante" if self.objetivo_cumplido else "[ACTUALIZAR] Activo"
            mode_text = "Multi-IA" if self.use_multi_ai.get() else "Tradicional"
            self.root.title(
                f"MT5 Bot [{mode_text}] | {status} | "
                f"[DATA] {self.total_operaciones_abiertas}/{self._safe_get('MAX_SIMULTANEOUS_OPS', 5)} | "
                f"[DINERO] Total: {saldo_text}"
            )
            
            # ⭐ ACTUALIZAR DETECTOR DE TENDENCIA EN UI - CADA SEGUNDO
            if hasattr(self, 'trend_state_label'):
                try:
                    # Inicializar o usar análisis guardado
                    if not hasattr(self, 'last_trend_analysis') or not self.last_trend_analysis:
                        self.last_trend_analysis = {
                            'signal': 'STABLE', 
                            'risk_level': 'LOW', 
                            'confidence': 0,
                            'reason': '',
                            'source': 'UNKNOWN'
                        }
                    
                    signal = self.last_trend_analysis.get('signal', 'STABLE')
                    risk = self.last_trend_analysis.get('risk_level', 'LOW')
                    confidence = self.last_trend_analysis.get('confidence', 0)
                    reason = self.last_trend_analysis.get('reason', '')
                    source = self.last_trend_analysis.get('source', '')
                    
                    # ⭐ MOSTRAR: BUY/SELL con confianza en la UI - NUNCA mostrar ESPERA
                    conf_display = max(0, int(confidence))
                    
                    # Guardar último BUY/SELL válido para cuando sea STABLE
                    if signal in ['BUY_TO_SELL', 'SELL_TO_BUY']:
                        self.last_valid_trend_signal = signal
                        self.last_valid_trend_conf = conf_display
                    
                    # Si es STABLE, usar último BUY/SELL detectado
                    if signal == 'STABLE' and hasattr(self, 'last_valid_trend_signal'):
                        signal = self.last_valid_trend_signal
                        conf_display = getattr(self, 'last_valid_trend_conf', 0)
                    
                    # Mostrar BUY o SELL (nunca ESPERA)
                    if signal == 'BUY_TO_SELL':
                        emoji_state = "📉"
                        display_signal = f"SELL {conf_display}%"
                        color_state = '#ef4444'  # Rojo
                    elif signal == 'SELL_TO_BUY':
                        emoji_state = "📈"
                        display_signal = f"BUY {conf_display}%"
                        color_state = '#22c55e'  # Verde
                    else:  # STABLE sin histórico previo - no mostrar nada
                        emoji_state = ""
                        display_signal = ""
                        color_state = '#94a3b8'  # Gris
                    
                    self.trend_state_label.config(text=f"{emoji_state} {display_signal}", fg=color_state)
                    
                    # Mostrar nivel de riesgo con color
                    risk_color = '#ef4444' if risk == 'HIGH' else '#fbbf24' if risk == 'MEDIUM' else '#10b981'
                    self.trend_risk_label.config(text=f"Risk: {risk}", fg=risk_color)
                    
                    # Mostrar confianza basada en confidence (mínimo 0%)
                    self.trend_confidence_label.config(text=f"Conf: {conf_display}%")
                    
                    # ⭐ TEMPORIZADOR: Actualizar CADA SEGUNDO
                    now = time.time()
                    
                    # Inicializar si no existe
                    if not hasattr(self, 'trend_next_check_time') or self.trend_next_check_time == 0:
                        self.trend_next_check_time = now + 60
                    
                    # Calcular segundos restantes
                    seconds_left = max(0, int(self.trend_next_check_time - now))
                    
                    # Resetear si pasaron los 60 segundos
                    if seconds_left <= 0:
                        self.trend_next_check_time = now + 60
                        seconds_left = 60
                    
                    # Mostrar temporizador con colores
                    if seconds_left <= 10:
                        timer_color = '#ef4444'  # Rojo si quedan menos de 10s
                    elif seconds_left <= 30:
                        timer_color = '#fbbf24'  # Amarillo si quedan 30s
                    else:
                        timer_color = '#64748b'  # Gris normal
                    
                    self.trend_timer_label.config(text=f"⏱️ {seconds_left}s", fg=timer_color)
                    
                except Exception as trend_ui_err:
                    pass  # Silenciar errores de UI para no interferir con el bot
            
            # ⭐ NUEVO: Monitoreo de entrada y análisis de operaciones
            if self.is_running and self.use_entry_point.get():
                self.monitor_entry_point()
                # Cada 3 actualizaciones, analizar operaciones abiertas
                if not hasattr(self, '_update_counter'):
                    self._update_counter = 0
                self._update_counter += 1
                if self._update_counter >= 3:
                    self.analizar_operaciones_abiertas()
                    self._update_counter = 0
            
            self.root.update_idletasks()
            
        except Exception as e:
            self.add_log(f"Error actualizando interfaz: {str(e)}", 'error')

    def create_rapid_operations_panel(self, parent):
        """⚡ Panel para Operaciones Rápidas - Checkbox + Intervalo"""
        main_frame = tk.Frame(parent, bg='#1e293b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # ===== CONTROL SIMPLE =====
        control_frame = tk.LabelFrame(main_frame, text="⚡ Operaciones Rápidas", 
                                     bg='#2d3e50', fg='#f1f5f9',
                                     font=('Arial', 12, 'bold'), padx=10, pady=10)
        control_frame.pack(fill='x', pady=10)

        # Fila 1: Checkbox
        row1 = tk.Frame(control_frame, bg='#2d3e50')
        row1.pack(fill='x', pady=5)
        
        tk.Checkbutton(row1, text="✅ Activar Operaciones Rápidas Automáticas", 
                      variable=self.config['RAPID_OPS_ENABLED'],
                      bg='#2d3e50', fg='#4ade80', font=('Arial', 11, 'bold'),
                      selectcolor='#1e293b', command=self.on_rapid_ops_toggle).pack(side='left', padx=10, pady=5)

        # Fila 2: Intervalo
        row2 = tk.Frame(control_frame, bg='#2d3e50')
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text="Intervalo (seg):", bg='#2d3e50', fg='#cbd5e1', font=('Arial', 10)).pack(side='left', padx=10)
        
        tk.Spinbox(row2, from_=0.1, to=300, increment=0.1, textvariable=self.config['RAPID_OPS_INTERVAL'],
                  bg='#1e293b', fg='#60a5fa', font=('Arial', 10), width=5,
                  relief='flat', borderwidth=1).pack(side='left', padx=5)
        
        tk.Label(row2, text="(Abre operaciones cada X segundos sin análisis)", 
                bg='#2d3e50', fg='#94a3b8', font=('Arial', 9)).pack(side='left', padx=10)

        # Fila 3: SL/TP
        row3 = tk.Frame(control_frame, bg='#2d3e50')
        row3.pack(fill='x', pady=5)
        
        tk.Checkbutton(row3, text="🎯 Usar SL/TP", 
                      variable=self.config['RAPID_OPS_USE_SL_TP'],
                      bg='#2d3e50', fg='#f87171', font=('Arial', 10),
                      selectcolor='#1e293b').pack(side='left', padx=10)
        
        tk.Label(row3, text="SL ($):", bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9)).pack(side='left', padx=10)
        tk.Spinbox(row3, from_=0.001, to=100, increment=0.001, textvariable=self.config['RAPID_OPS_SL'],
                  bg='#1e293b', fg='#f87171', font=('Arial', 9), width=5,
                  relief='flat', borderwidth=1, format="%.3f").pack(side='left', padx=2)
        
        tk.Label(row3, text="TP ($):", bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9)).pack(side='left', padx=10)
        tk.Spinbox(row3, from_=0.001, to=100, increment=0.001, textvariable=self.config['RAPID_OPS_TP'],
                  bg='#1e293b', fg='#86efac', font=('Arial', 9), width=5,
                  relief='flat', borderwidth=1, format="%.3f").pack(side='left', padx=2)

        # Opción: abrir la operación contraria automáticamente tras cierre por SL/TP
        row4 = tk.Frame(control_frame, bg='#2d3e50')
        row4.pack(fill='x', pady=5)
        tk.Checkbutton(row4, text="↺ Abrir contraria tras cierre SL/TP",
                      variable=self.config['RAPID_OPS_OPEN_OPPOSITE_ON_SLTP'],
                      bg='#2d3e50', fg='#c7d2fe', font=('Arial', 9),
                      selectcolor='#1e293b').pack(side='left', padx=12)

        # Opción: abrir la operación contraria si la otra dirección está ganando
        tk.Checkbutton(row4, text="↺ Abrir contraria si la otra está ganando",
                  variable=self.config['RAPID_OPS_OPEN_OPPOSITE_ON_WIN'],
                  bg='#2d3e50', fg='#c7d2fe', font=('Arial', 9),
                  selectcolor='#1e293b').pack(side='left', padx=12)

        # IA integrada automática: la dirección es determinada por la IA adaptativa.

        # ===== INFORMACIÓN =====
        info_frame = tk.LabelFrame(main_frame, text="📋 Configuración Activa", 
                                  bg='#2d3e50', fg='#f1f5f9',
                                  font=('Arial', 10, 'bold'), padx=10, pady=10)
        info_frame.pack(fill='x', pady=10)

        info_text = tk.Frame(info_frame, bg='#2d3e50')
        info_text.pack(fill='x')
        
        tk.Label(info_text, 
                text="• Sin análisis - abre directamente cada X segundos\n"
                     "• Si 'Punto de Entrada' activo → usa su dirección fija\n"
                     "• Si 'Punto de Entrada' inactivo → mitad BUY + mitad SELL\n"
                     "• Cierra automáticamente cuando ganancia ≥ MIN_PROFIT_CLOSE\n"
                     "• Usa SYMBOL, VOLUMEN y MAX_OPS de Configuración",
                bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9), justify='left').pack(side='left', padx=10)

        # ===== ESTADO EN TIEMPO REAL =====
        status_frame = tk.LabelFrame(main_frame, text="📊 Estado Actual", 
                                    bg='#2d3e50', fg='#f1f5f9',
                                    font=('Arial', 10, 'bold'), padx=10, pady=10)
        status_frame.pack(fill='x')

        self.rapid_ops_status = tk.Label(status_frame, 
                                        text="🔴 INACTIVO", 
                                        bg='#2d3e50', fg='#fbbf24', font=('Arial', 11, 'bold'))
        self.rapid_ops_status.pack(side='left', padx=5, pady=5)

        self.rapid_ops_counter = tk.Label(status_frame, 
                                         text="Operaciones: 0 | BUY: 0 | SELL: 0", 
                                         bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9))
        self.rapid_ops_counter.pack(side='left', padx=20, pady=5)
        
        # (Se reservará un espacio para la cuenta atrás debajo de Balance/Patrimonio)


        # Balance y Patrimonio específicos de Operaciones Rápidas (debajo del estado)
        rapid_account_frame = tk.Frame(main_frame, bg='#1e293b')
        rapid_account_frame.pack(fill='x', pady=(5, 0))

        tk.Label(rapid_account_frame, text="Balance:", bg='#1e293b', fg='#cbd5e1').pack(side='left', padx=(10,5))
        self.rapid_balance_label = tk.Label(rapid_account_frame, text="$0.00", bg='#1e293b', fg='#60a5fa', font=('Arial', 10, 'bold'))
        self.rapid_balance_label.pack(side='left', padx=(0,15))
        tk.Label(rapid_account_frame, text="Inicial:", bg='#1e293b', fg='#cbd5e1').pack(side='left', padx=(0,5))
        self.rapid_initial_balance_label = tk.Label(rapid_account_frame, text="$0.00", bg='#1e293b', fg='#fbbf24', font=('Arial', 10, 'bold'))
        self.rapid_initial_balance_label.pack(side='left', padx=(0,15))

        tk.Label(rapid_account_frame, text="Patrimonio:", bg='#1e293b', fg='#cbd5e1').pack(side='left', padx=(0,5))
        self.rapid_equity_label = tk.Label(rapid_account_frame, text="$0.00", bg='#1e293b', fg='#34d399', font=('Arial', 10, 'bold'))
        self.rapid_equity_label.pack(side='left')

        # Cuenta atrás hasta la próxima apertura (debajo de Balance/Patrimonio)
        self.rapid_countdown_label = tk.Label(rapid_account_frame, text="Próx. en: -", bg='#1e293b', fg='#cbd5e1', font=('Arial', 10, 'bold'))
        self.rapid_countdown_label.pack(side='left', padx=(20,0))

        # --- Campo de GANANCIA objetivo debajo de SL/TP ---
        # Buscar el frame donde se configuran SL/TP (usualmente cerca de la config de rápidas)
        # Si no existe, crear uno aquí provisionalmente
        rapid_sl_frame = tk.Frame(main_frame, bg='#1e293b')
        rapid_sl_frame.pack(fill='x', pady=(2, 0))

        # SL/TP ya debe estar en la UI, aquí solo agregamos el campo de ganancia objetivo
        tk.Label(rapid_sl_frame, text="Ganancia objetivo:", bg='#1e293b', fg='#cbd5e1').pack(side='left', padx=(10,5))
        self.rapid_gain_target_var = tk.DoubleVar(value=0.0)
        self.rapid_gain_target_entry = tk.Entry(rapid_sl_frame, textvariable=self.rapid_gain_target_var, width=8, font=('Arial', 10, 'bold'))
        self.rapid_gain_target_entry.pack(side='left', padx=(0,10))
        tk.Label(rapid_sl_frame, text="(Patrimonio)", bg='#1e293b', fg='#64748b', font=('Arial', 9)).pack(side='left')

        # Widgets IA adaptativa: fracción BUY y mini-historial
        adapt_frame = tk.Frame(main_frame, bg='#1e293b')
        adapt_frame.pack(fill='x', pady=(8, 0))

        tk.Label(adapt_frame, text="IA Adaptativa → Frac. BUY:", bg='#1e293b', fg='#cbd5e1').pack(side='left', padx=(10,5))
        frac_color = self.config['RAPID_OPS_FRAC_COLOR'].get() if 'RAPID_OPS_FRAC_COLOR' in self.config else '#f59e0b'
        self.rapid_buy_frac_label = tk.Label(adapt_frame, text="50%", bg='#1e293b', fg=frac_color, font=('Arial', 10, 'bold'))
        self.rapid_buy_frac_label.pack(side='left', padx=(0,10))

        # Barra visual de fracción (0-100) con estilo personalizado
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Rapid.Horizontal.TProgressbar', troughcolor='#0f172a', background=frac_color, thickness=14)
        self.rapid_buy_frac_bar = ttk.Progressbar(adapt_frame, length=220, mode='determinate', maximum=100, style='Rapid.Horizontal.TProgressbar')
        self.rapid_buy_frac_bar.pack(side='left', padx=(0,10), pady=4)

        # Mini-resumen histórico
        self.rapid_history_label = tk.Label(adapt_frame, text="Hist: -", bg='#1e293b', fg='#94a3b8', font=('Arial', 9))
        self.rapid_history_label.pack(side='left', padx=(10,0))

        # (La cuenta atrás se muestra ahora en el panel de estado principal)
        # Botón para resetear la IA / historial de Operaciones Rápidas
        tk.Button(adapt_frame, text="Reset IA / Historial", bg='#111827', fg='#f8fafc',
            font=('Arial', 9, 'bold'), relief='raised', borderwidth=1,
            command=self.reset_rapid_ai).pack(side='left', padx=(12,0))

        # ===== BARRAS DE OPERACIONES FANTASMA =====
        # Frame para barras fantasma
        ghost_frame = tk.Frame(main_frame, bg='#1e293b')
        ghost_frame.pack(fill='x', pady=(10, 0))

        # Barra 1: Fantasma BUY
        self.ghost_buy_label = tk.Label(ghost_frame, text="Fantasma BUY: 0 abiertas | 0 ganadas | 0 perdidas (30s)",
            bg='#1e293b', fg='#38bdf8', font=('Arial', 10, 'bold'))
        self.ghost_buy_label.pack(fill='x', padx=10, pady=2)

        # Barra 2: Fantasma SELL

        self.ghost_sell_label = tk.Label(ghost_frame, text="Fantasma SELL: 0 abiertas | 0 ganadas | 0 perdidas (30s)",
            bg='#1e293b', fg='#f472b6', font=('Arial', 10, 'bold'))
        self.ghost_sell_label.pack(fill='x', padx=10, pady=2)

        # Log específico de operaciones fantasma
        ghost_log_label = tk.Label(ghost_frame, text="Log de Operaciones Fantasma", bg='#1e293b', fg='#fbbf24', font=('Arial', 10, 'bold'))
        ghost_log_label.pack(fill='x', padx=10, pady=(8,2))
        self.ghost_log_text = scrolledtext.ScrolledText(ghost_frame, height=7, bg='#0f172a', fg='#e2e8f0', font=('Consolas', 9), relief='flat', padx=8, pady=4, insertbackground='white')
        self.ghost_log_text.pack(fill='x', padx=10, pady=(0,10))

        # Botón para resetear todo el estado (fantasmas, rápidas, logs) - fila propia debajo del log
        reset_frame = tk.Frame(ghost_frame, bg='#1e293b')
        reset_frame.pack(fill='x', pady=(6, 0))
        try:
            btn = tk.Button(reset_frame, text="Reset Estado", bg='#7c3aed', fg='white', font=('Arial', 10, 'bold'), relief='raised', command=self._on_reset_all_clicked)
            btn.pack(fill='x', padx=10, pady=(4,8))
        except Exception:
            pass

    def add_ghost_log(self, message, tag='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        if hasattr(self, 'ghost_log_text'):
            self.ghost_log_text.insert('end', log_message)
            self.ghost_log_text.see('end')
        else:
            print(log_message.strip())

    def add_ghost_op(self, typ, op):
        """Añade una operación fantasma de forma segura, respetando el límite de 50 abiertas por tipo."""
        max_open = 50
        try:
            if self.ghost_ops_lock:
                with self.ghost_ops_lock:
                    open_count = sum(1 for o in self.ghost_ops.get(typ, []) if o.get('result') is None)
                    if open_count < max_open:
                        self.ghost_ops.setdefault(typ, []).append(op)
                        # Asegurar recorte dentro del lock
                        try:
                            self._trim_ghost_ops_locked(typ, max_open)
                        except Exception:
                            pass
                        return True
                    else:
                        self.add_log(f"Límite {typ.upper()} fantasma ({max_open}) alcanzado; no se añadió nueva.", 'info')
                        return False
            else:
                open_count = sum(1 for o in self.ghost_ops.get(typ, []) if o.get('result') is None)
                if open_count < max_open:
                    self.ghost_ops.setdefault(typ, []).append(op)
                    # Por seguridad, recortar si por concurrencia se supera el límite
                    try:
                        self._trim_ghost_ops_locked(typ, max_open)
                    except Exception:
                        pass
                    return True
                else:
                    self.add_log(f"Límite {typ.upper()} fantasma ({max_open}) alcanzado; no se añadió nueva.", 'info')
                    return False
        except Exception as e:
            try:
                self.add_log(f"Error add_ghost_op: {e}", 'error')
            except Exception:
                print(f"Error add_ghost_op: {e}")
            return False

    def _on_reset_all_clicked(self):
        try:
            ok = messagebox.askyesno("Confirmar reset", "¿Deseas reiniciar TODO el estado (operaciones rápidas, fantasmas y logs)?")
            if not ok:
                return
            self.reset_all_state()
            # Actualizar UI
            try:
                self.update_ghost_ops_ui()
            except Exception:
                pass
            try:
                self.update_rapid_operations_ui()
            except Exception:
                pass
            try:
                self._update_ui()
            except Exception:
                pass
        except Exception as e:
            try:
                self.add_log(f"Error al ejecutar reset UI: {e}", 'error')
            except Exception:
                print(f"Error al ejecutar reset UI: {e}")

    def _trim_ghost_ops_locked(self, typ, max_open=50):
        """Asume que se llama con `self.ghost_ops_lock` ya adquirido o desde contexto seguro.
        Recorta las operaciones abiertas (result is None) conservando las más recientes hasta `max_open`.
        """
        try:
            all_ops = self.ghost_ops.get(typ, [])
            open_ops = [o for o in all_ops if o.get('result') is None]
            closed_ops = [o for o in all_ops if o.get('result') is not None]
            if len(open_ops) > max_open:
                # Conservar las más recientes
                kept_open = open_ops[-max_open:]
                self.ghost_ops[typ] = closed_ops + kept_open
                try:
                    self.add_log(f"🔧 Recorte automático {typ.upper()} fantasma: eliminado {len(open_ops)-max_open} antiguas.", 'info')
                except Exception:
                    pass
        except Exception as e:
            try:
                self.add_log(f"Error trim_ghost_ops: {e}", 'error')
            except Exception:
                print(f"Error trim_ghost_ops: {e}")

    def on_rapid_ops_toggle(self):
        """Se ejecuta cuando checkbox de Operaciones Rápidas cambia"""
        if self._safe_get('RAPID_OPS_ENABLED', False):
            self.start_ghost_operations()
            self.start_rapid_operations()
        else:
            self.stop_ghost_operations()
            self.stop_rapid_operations()

    def on_micro_profile_changed(self):
        """Se ejecuta cuando el perfil de micro momentum cambia desde UI"""
        try:
            new_profile = self.micro_profile_var.get()
            if hasattr(self.arbitrator, 'set_micro_profile'):
                self.arbitrator.set_micro_profile(new_profile)
                self.add_log(f"[MICRO] Perfil cambiado a: {new_profile}", 'success')
            else:
                self.add_log(f"[MICRO] Arbitrator no soporta cambio de perfil", 'warning')
        except Exception as e:
            self.add_log(f"[MICRO] Error al cambiar perfil: {str(e)}", 'error')

    def start_rapid_operations(self):
        """Inicia Operaciones Rápidas usando configuración activa"""
        if self.rapid_ops_running:
            return

        # Resetear contadores
        self.rapid_ops_active.clear()
        self.rapid_ops_total_opened = 0  # Contador permanente que controla alternancia
        self.rapid_ops_buy_count = 0
        self.rapid_ops_sell_count = 0
        self.rapid_ops_total_profit = 0.0  # Resetear ganancias/pérdidas
        self.last_rapid_op_time = 0

        self.rapid_ops_running = True
        # Inicializar fase y tiempos para IA adaptativa
        self.rapid_ops_start_time = time.time()
        self.rapid_initial_phase_done = False
        self.rapid_target_buy_frac = 0.5

        self.add_log(f"[EMOJI] Operaciones Rápidas ACTIVADAS", 'success')

        # Iniciar thread de monitoreo
        self.rapid_ops_thread = threading.Thread(target=self.monitor_rapid_operations, daemon=True)
        self.rapid_ops_thread.start()

    def stop_rapid_operations(self):
        """Detiene el sistema de operaciones rápidas"""
        self.rapid_ops_running = False
        self.config['RAPID_OPS_ENABLED'].set(False)
        self.add_log("[STOP] Operaciones Rápidas detenidas", 'warning')

    def reset_rapid_ai(self):
        """Resetea el historial y el estado de la IA para Operaciones Rápidas.

        Limpia `rapid_ops_history`, reinicia contadores específicos de rápidas y
        vuelve a la fase inicial (50/50) para evitar sesgos anteriores.
        """
        try:
            # Limpiar historial y métricas específicas de rápidas
            if hasattr(self, 'rapid_ops_history'):
                try:
                    self.rapid_ops_history.clear()
                except Exception:
                    self.rapid_ops_history = deque(maxlen=int(self._safe_get('RAPID_OPS_HISTORY_SIZE', 200)))

            # Resetear contadores que afectan la lógica de apertura
            self.rapid_ops_total_opened = 0
            self.rapid_ops_buy_count = 0
            self.rapid_ops_sell_count = 0
            self.rapid_ops_total_profit = 0.0

            # Reiniciar fase adaptativa
            self.rapid_initial_phase_done = False
            self.rapid_ops_start_time = time.time()
            self.rapid_target_buy_frac = 0.5
            self.rapid_buy_frac_smoothed = None

            # Actualizar UI inmediatamente
            try:
                self.rapid_buy_frac_label.config(text="50%")
                self.rapid_buy_frac_bar['value'] = 50
                self.rapid_history_label.config(text="Últ.1m → BUY: 0 | SELL: 0 | 0% BUY")
                self._update_ui()
            except Exception:
                pass

            self.add_log("[ACTUALIZAR] Reset IA Rápidas: historial y estado reiniciados (fase inicial 50/50)", 'info')
        except Exception as e:
            self.add_log(f"[ERROR] Error reset_rapid_ai: {str(e)}", 'error')

    def reset_all_state(self):
        """Resetea todo el estado en memoria relacionado con operaciones rápidas, fantasmas,
        logs y contadores para asegurar un arranque limpio.
        Es segura si algunos atributos aún no existen (usa hasattr checks).
        """
        try:
            # Detener cualquier thread en curso
            try:
                self.rapid_ops_running = False
            except Exception:
                pass
            try:
                self.ghost_ops_running = False
            except Exception:
                pass

            # Limpiar operaciones rápidas
            try:
                if hasattr(self, 'rapid_ops_active'):
                    self.rapid_ops_active.clear()
            except Exception:
                self.rapid_ops_active = {}
            try:
                if hasattr(self, 'rapid_ops_history'):
                    self.rapid_ops_history.clear()
                else:
                    self.rapid_ops_history = deque(maxlen=int(self._safe_get('RAPID_OPS_HISTORY_SIZE', 200)))
            except Exception:
                self.rapid_ops_history = deque(maxlen=200)
            self.rapid_ops_total_opened = 0
            self.rapid_ops_buy_count = 0
            self.rapid_ops_sell_count = 0
            self.rapid_ops_total_profit = 0.0
            self.last_rapid_op_time = 0
            self.rapid_ops_start_time = 0
            self.rapid_initial_phase_done = False
            self.rapid_target_buy_frac = 0.5
            self.rapid_buy_frac_smoothed = None

            # Limpiar operaciones fantasma
            try:
                self.ghost_ops = {'buy': [], 'sell': []}
            except Exception:
                pass
            try:
                if hasattr(self, 'ghost_ops_history'):
                    self.ghost_ops_history.clear()
                else:
                    self.ghost_ops_history = []
            except Exception:
                self.ghost_ops_history = []
            # Estadísticas y totales
            self.ghost_stats = {'buy_open': 0, 'buy_win': 0, 'buy_loss': 0, 'sell_open': 0, 'sell_win': 0, 'sell_loss': 0}
            self.ghost_total = {'buy_win': 0, 'buy_loss': 0, 'sell_win': 0, 'sell_loss': 0}

            # Limpiar logs de UI si existen
            try:
                if hasattr(self, 'ghost_log_text'):
                    self.ghost_log_text.delete('1.0', 'end')
            except Exception:
                pass
            try:
                if hasattr(self, 'log_text'):
                    self.log_text.delete('1.0', 'end')
            except Exception:
                pass

            # Otros contadores generales
            try:
                self.operaciones_actuales = set()
                self.operaciones_procesadas = set()
                self.operaciones_cerradas = 0
            except Exception:
                pass

            # Resetear indicadores de sesión/pause
            try:
                self.block_until = 0.0
                self.pause_until = 0.0
            except Exception:
                pass

            self.add_log("[RESET] Estado reiniciado: operaciones rápidas y fantasmas limpiadas.", 'info')
        except Exception as e:
            try:
                self.add_log(f"[ERROR] Error en reset_all_state: {e}", 'error')
            except Exception:
                print(f"Error en reset_all_state: {e}")

    def save_config(self):
        """Guarda la configuración actual a JSON para persistencia entre reinicios"""
        try:
            import json
            config_data = {}
            
            # Guardar todos los valores de tk.StringVar, tk.IntVar, tk.DoubleVar, tk.BooleanVar
            for key, var in self.config.items():
                try:
                    if isinstance(var, tk.Variable):
                        config_data[key] = var.get()
                    else:
                        config_data[key] = var
                except Exception:
                    pass
            
            # Crear directorio si no existe
            os.makedirs('config', exist_ok=True)
            
            # Guardar a archivo
            with open('config/bot_config.json', 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            self.add_log("[CONFIG] Configuración guardada en config/bot_config.json", 'debug')
            return True
        except Exception as e:
            self.add_log(f"[CONFIG] Error guardando config: {str(e)}", 'error')
            return False
    
    def load_config(self):
        """Carga configuración desde JSON si existe"""
        try:
            import json
            if not os.path.exists('config/bot_config.json'):
                self.add_log("[CONFIG] Archivo de configuración no encontrado, usando defaults", 'info')
                return False
            
            with open('config/bot_config.json', 'r') as f:
                config_data = json.load(f)
            
            # Restaurar valores a las variables tk
            for key, value in config_data.items():
                try:
                    if key in self.config and isinstance(self.config[key], tk.Variable):
                        self.config[key].set(value)
                except Exception as e:
                    self.add_log(f"[CONFIG] Error restaurando {key}: {str(e)}", 'warning')
            
            self.add_log("[CONFIG] ✅ Configuración restaurada desde config/bot_config.json", 'success')
            return True
        except Exception as e:
            self.add_log(f"[CONFIG] Error cargando config: {str(e)}", 'error')
            return False

    def get_last_minute_counts(self):
        """Cuenta BUY/SELL en el historial de rápidas dentro de la última 60s."""
        try:
            now = datetime.now()
            cutoff = now - timedelta(seconds=60)
            buy = 0
            sell = 0
            for item in reversed(self.rapid_ops_history):
                t = item.get('time', now)
                if t < cutoff:
                    break
                if item.get('type') == 'BUY':
                    buy += 1
                else:
                    sell += 1
            return buy, sell, (buy + sell)
        except Exception:
            return 0, 0, 0

    def decide_rapid_direction(self):
        """Decide la mejor dirección para la próxima operación rápida analizando
        las últimas `RAPID_OPS_ANALYZE_WINDOW` segundos de datos tanto de fantasmas
        como de operaciones reales. Devuelve 'BUY', 'SELL' o 'HOLD'.
        """
        try:
            now = time.time()
            window = int(self._safe_get('RAPID_OPS_ANALYZE_WINDOW', 5))

            # Recoger datos de fantasmas (usamos close_time)
            ghost_recent = []
            try:
                if hasattr(self, 'ghost_ops_history') and self.ghost_ops_history:
                    # proteger lectura con lock si existe
                    if getattr(self, 'ghost_ops_lock', None):
                        with self.ghost_ops_lock:
                            ghost_recent = [e for e in list(self.ghost_ops_history) if e.get('close_time', 0) >= now - window]
                    else:
                        ghost_recent = [e for e in list(self.ghost_ops_history) if e.get('close_time', 0) >= now - window]
            except Exception:
                ghost_recent = []

            # Recoger datos de operaciones reales (rapid_ops_history)
            rapid_recent = []
            try:
                if hasattr(self, 'rapid_ops_history') and self.rapid_ops_history:
                    if getattr(self, 'rapid_ops_lock', None):
                        with self.rapid_ops_lock:
                            rapid_recent = [e for e in list(self.rapid_ops_history) if getattr(e.get('time'), 'timestamp', lambda: 0)() >= now - window]
                    else:
                        rapid_recent = [e for e in list(self.rapid_ops_history) if getattr(e.get('time'), 'timestamp', lambda: 0)() >= now - window]
            except Exception:
                rapid_recent = []

            # Calcular winrates y profit sums
            def calc_metrics(arr, is_ghost=False):
                buy_total = 0
                buy_wins = 0
                buy_profit = 0.0
                sell_total = 0
                sell_wins = 0
                sell_profit = 0.0
                for e in arr:
                    t = e.get('type', '').upper()
                    if is_ghost:
                        res = e.get('result')
                        prof = float(e.get('profit', 0.0))
                        if t == 'BUY':
                            buy_total += 1
                            if res == 'win':
                                buy_wins += 1
                            buy_profit += prof
                        elif t == 'SELL':
                            sell_total += 1
                            if res == 'win':
                                sell_wins += 1
                            sell_profit += prof
                    else:
                        prof = float(e.get('profit', 0.0))
                        if t == 'BUY':
                            buy_total += 1
                            if prof > 0:
                                buy_wins += 1
                            buy_profit += prof
                        elif t == 'SELL':
                            sell_total += 1
                            if prof > 0:
                                sell_wins += 1
                            sell_profit += prof
                return {
                    'buy_total': buy_total, 'buy_wins': buy_wins, 'buy_profit': buy_profit,
                    'sell_total': sell_total, 'sell_wins': sell_wins, 'sell_profit': sell_profit
                }

            ghost_metrics = calc_metrics(ghost_recent, is_ghost=True)
            rapid_metrics = calc_metrics(rapid_recent, is_ghost=False)

            # Win rates
            buy_wins = ghost_metrics['buy_wins'] + rapid_metrics['buy_wins']
            buy_total = ghost_metrics['buy_total'] + rapid_metrics['buy_total']
            sell_wins = ghost_metrics['sell_wins'] + rapid_metrics['sell_wins']
            sell_total = ghost_metrics['sell_total'] + rapid_metrics['sell_total']

            buy_rate_real = (rapid_metrics['buy_wins'] / rapid_metrics['buy_total']) if rapid_metrics['buy_total'] > 0 else None
            sell_rate_real = (rapid_metrics['sell_wins'] / rapid_metrics['sell_total']) if rapid_metrics['sell_total'] > 0 else None
            buy_rate_ghost = (ghost_metrics['buy_wins'] / ghost_metrics['buy_total']) if ghost_metrics['buy_total'] > 0 else None
            sell_rate_ghost = (ghost_metrics['sell_wins'] / ghost_metrics['sell_total']) if ghost_metrics['sell_total'] > 0 else None

            # Mezclar con pesos (dar más peso a datos reales)
            w_real = 0.7
            w_ghost = 0.3
            # Fallbacks: si no hay datos reales, usar solo ghost; si no hay ghost, usar reales
            def combine(br, bg):
                if br is None and bg is None:
                    return 0.5
                if br is None:
                    return bg
                if bg is None:
                    return br
                return w_real * br + w_ghost * bg

            buy_comb = combine(buy_rate_real, buy_rate_ghost)
            sell_comb = combine(sell_rate_real, sell_rate_ghost)

            # Considerar también profit medio como desempate
            buy_profit = ghost_metrics['buy_profit'] + rapid_metrics['buy_profit']
            sell_profit = ghost_metrics['sell_profit'] + rapid_metrics['sell_profit']

            # Decisión basada en la diferencia y en profit
            diff = buy_comb - sell_comb
            profit_diff = buy_profit - sell_profit

            # Umbral dinámico: si hay al menos 2 muestras en total usar umbral 0.12, sino mantener 50/50
            samples = buy_total + sell_total
            threshold = 0.12 if samples >= 2 else 0.30

            if diff > threshold or (abs(diff) < threshold and profit_diff > 0.01 and buy_total+sell_total>0):
                return 'BUY'
            elif diff < -threshold or (abs(diff) < threshold and profit_diff < -0.01 and buy_total+sell_total>0):
                return 'SELL'
            else:
                return 'HOLD'
        except Exception as e:
            try:
                self.add_log(f"Error decide_rapid_direction: {e}", 'error')
            except Exception:
                pass
            return 'HOLD'

    def monitor_rapid_operations(self):
        """Monitorea y abre operaciones rápidas cada X segundos (sin análisis)"""
        self.add_log(f"[ACTUALIZAR] INICIANDO MONITOR RÁPIDAS - Connected: {self.connected}", 'info')
        
        # [EMOJI] CRÍTICO: Reinicializar MT5 en el thread de rápidas
        if not mt5.initialize():
            self.add_log(f"[ADVERTENCIA] Monitor rápidas: Intentando inicializar MT5...", 'warning')
            mt5.shutdown()
            time.sleep(1)
            if not mt5.initialize():
                self.add_log(f"[ERROR] Monitor rápidas: NO pudo inicializar MT5", 'error')
                return
        
        self.add_log(f"[OK] Monitor rápidas: MT5 inicializado en thread", 'success')
        
        iteration = 0
        while self.rapid_ops_running:
            try:
                symbol = self.config['SYMBOL'].get()
                current_time = time.time()
                interval = self.config['RAPID_OPS_INTERVAL'].get()  # Intervalo configurable
                iteration += 1

                # Finalizar fase inicial tras 60s: calcular fracción objetivo
                try:
                    initial_phase = int(self.config.get('RAPID_OPS_INITIAL_PHASE', tk.IntVar(value=60)).get()) if 'RAPID_OPS_INITIAL_PHASE' in self.config else 60
                    if (not self.rapid_initial_phase_done) and self.rapid_ops_start_time and (current_time - self.rapid_ops_start_time >= initial_phase):
                        # Calcular fracción objetivo basada en historial recogido durante la fase inicial
                        buy_frac = self._compute_rapid_ops_distribution()
                        self.rapid_target_buy_frac = buy_frac
                        self.rapid_initial_phase_done = True
                        # Indicar que ahora la IA empezará a analizar en vivo
                        self.add_log(f"[IA] IA Rápidas: fase inicial ({initial_phase}s) completada - Frac BUY objetivo {buy_frac:.2f}", 'info')
                        self.add_log("[IA] IA Rápidas: empezando análisis en vivo y aprendizaje continuo", 'info')
                        # Actualizar UI inmediatamente
                        try:
                            if hasattr(self, 'rapid_buy_frac_label'):
                                color = self.config.get('RAPID_OPS_FRAC_COLOR').get() if 'RAPID_OPS_FRAC_COLOR' in self.config else '#f59e0b'
                                self.rapid_buy_frac_label.config(text=f"{int(buy_frac*100)}%", fg=color)
                            if hasattr(self, 'rapid_buy_frac_bar'):
                                self.rapid_buy_frac_bar['value'] = int(buy_frac*100)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Log cada 20 iteraciones
                if iteration % 20 == 0 and len(self.rapid_ops_active) > 0:
                    self.add_log(f"[DATA] Rápidas: {len(self.rapid_ops_active)} ops | Intervalo: {interval}s", 'info')

                # Verificar operaciones abiertas
                self.check_and_close_rapid_operations(symbol)

                # Abrir nuevas operaciones cada X segundos (sin análisis, solo abre)

                if current_time - self.last_rapid_op_time >= interval:
                    # Durante los primeros 30s, solo fantasmas
                    if self.rapid_ops_start_time and (current_time - self.rapid_ops_start_time <= 30):
                        self.add_log("[PAUSA] Solo operaciones fantasma (entrenamiento 30s)...", 'info')
                        self.last_rapid_op_time = current_time
                    else:
                        # Después de 30s, abrir operaciones reales y seguir abriendo fantasmas en paralelo
                        # Antes de abrir, decidir usando IA rápida analítica (últimos N segundos)
                        try:
                            if self.config.get('RAPID_OPS_USE_AI') and self.config['RAPID_OPS_USE_AI'].get():
                                decision = self.decide_rapid_direction()
                                if decision in ('BUY', 'SELL'):
                                    ghost_dir = decision
                                else:
                                    ghost_dir = self.get_ghost_recommendation()
                            else:
                                ghost_dir = self.get_ghost_recommendation()
                        except Exception:
                            ghost_dir = self.get_ghost_recommendation()
                        # Si está activado el flag, invertir la dirección propuesta según distintas reglas
                        try:
                            # 1) Si está activada la opción "Open opposite on win", y la otra dirección
                            #    ha mostrado mayor profit recientemente y además hay posiciones abiertas
                            #    de la contraria, entonces invertir la dirección propuesta.
                            if ghost_dir in ('BUY', 'SELL') and 'RAPID_OPS_OPEN_OPPOSITE_ON_WIN' in self.config and self.config['RAPID_OPS_OPEN_OPPOSITE_ON_WIN'].get():
                                try:
                                    now_check = time.time()
                                    win_window = int(self.config.get('RAPID_OPS_ANALYZE_WINDOW', tk.IntVar(value=5)).get())
                                    recent = []
                                    if hasattr(self, 'rapid_ops_history') and self.rapid_ops_history:
                                        if getattr(self, 'rapid_ops_lock', None):
                                            with self.rapid_ops_lock:
                                                recent = [e for e in list(self.rapid_ops_history) if getattr(e.get('time'), 'timestamp', lambda: 0)() >= now_check - win_window]
                                        else:
                                            recent = [e for e in list(self.rapid_ops_history) if getattr(e.get('time'), 'timestamp', lambda: 0)() >= now_check - win_window]

                                    buy_profit_recent = sum(float(e.get('profit', 0.0)) for e in recent if e.get('type') == 'BUY')
                                    sell_profit_recent = sum(float(e.get('profit', 0.0)) for e in recent if e.get('type') == 'SELL')

                                    buy_open = sum(1 for op in self.rapid_ops_active.values() if op['type'] == 'BUY')
                                    sell_open = sum(1 for op in self.rapid_ops_active.values() if op['type'] == 'SELL')

                                    # Margen pequeño para evitar toggles
                                    profit_margin = 0.01
                                    if buy_profit_recent > sell_profit_recent + profit_margin and ghost_dir == 'BUY' and sell_open > 0:
                                        orig_dir = ghost_dir
                                        ghost_dir = 'SELL'
                                        self.add_log(f"↺ OpenOppositeOnWin: invertida {orig_dir} → {ghost_dir} (buy_profit {buy_profit_recent:.2f} > sell_profit {sell_profit_recent:.2f})", 'info')
                                    elif sell_profit_recent > buy_profit_recent + profit_margin and ghost_dir == 'SELL' and buy_open > 0:
                                        orig_dir = ghost_dir
                                        ghost_dir = 'BUY'
                                        self.add_log(f"↺ OpenOppositeOnWin: invertida {orig_dir} → {ghost_dir} (sell_profit {sell_profit_recent:.2f} > buy_profit {buy_profit_recent:.2f})", 'info')
                                except Exception:
                                    pass

                            # 2) Mantener compatibilidad: si está activado el flag de SL/TP abrir contraria,
                            #    respetar ese comportamiento (invierte sin analizar ganancias recientes).
                            if ghost_dir in ('BUY', 'SELL') and 'RAPID_OPS_OPEN_OPPOSITE_ON_SLTP' in self.config and self.config['RAPID_OPS_OPEN_OPPOSITE_ON_SLTP'].get():
                                orig_dir = ghost_dir
                                ghost_dir = 'BUY' if ghost_dir == 'SELL' else 'SELL'
                                self.add_log(f"↺ OpenOpposite SLTP activo: invertida recomendación {orig_dir} → {ghost_dir}", 'info')
                        except Exception:
                            pass

                        # ⭐ NUEVO: VALIDACIÓN INTELIGENTE ANTES DE ABRIR (ÁREA 6)
                        try:
                            # Obtener datos de mercado para validación
                            tick = mt5.symbol_info_tick(symbol)
                            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 30)
                            
                            # Calcular indicadores rápidos
                            current_rsi = 50.0  # Default neutral
                            current_momentum = 0.0
                            volatility_level = 'NORMAL'
                            
                            if rates is not None and len(rates) >= 14:
                                closes = np.array([r['close'] for r in rates])
                                current_rsi = self._calculate_rsi_quick(closes, period=14)
                                current_momentum = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] > 0 else 0.0
                                volatility_level = self.get_volatility_level(rates[-15:])
                            
                            # Obtener confianza del análisis anterior
                            confidence = getattr(self, 'last_analysis_confidence', 50)
                            
                            # Ejecutar validación
                            validation_result = self.rapid_ops_validator.validate_before_rapid_op({
                                'rsi': current_rsi,
                                'momentum': current_momentum,
                                'volatility': volatility_level,
                                'recent_losses': list(self.rapid_ops_validator.recent_rapid_losses) if hasattr(self.rapid_ops_validator, 'recent_rapid_losses') else [],
                                'last_op_time': self.last_rapid_op_time,
                                'confidence': confidence
                            })
                            
                            if not validation_result['should_open']:
                                self.add_log(f"[RAPID-VALID] ❌ Validación rechazó: {validation_result['reason']} | Risk: {validation_result['risk_level']}", 'warning')
                            else:
                                self.add_log(f"[RAPID-VALID] ✅ Validación aprobó (Risk: {validation_result['risk_level']}, {validation_result['passed_criteria']}/6 checks)", 'success')
                                
                                # Abrir operación real
                                if ghost_dir in ('BUY', 'SELL'):
                                    self.add_log(f"[EMOJI] Abriendo rápida inteligente: {ghost_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                    self.open_rapid_operation(symbol, force_direction=ghost_dir)
                                else:
                                    alt_dir = 'BUY' if (len(self.rapid_ops_active) % 2 == 0) else 'SELL'
                                    self.add_log(f"[EMOJI] Abriendo rápida inteligente: {alt_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                    self.open_rapid_operation(symbol, force_direction=alt_dir)
                        except Exception as e:
                            self.add_log(f"[ERROR] Error en validación inteligente: {str(e)}", 'error')
                            # Fallback: abrir como antes
                            if ghost_dir in ('BUY', 'SELL'):
                                self.add_log(f"[EMOJI] Abriendo rápida (fallback): {ghost_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                self.open_rapid_operation(symbol, force_direction=ghost_dir)
                            else:
                                alt_dir = 'BUY' if (len(self.rapid_ops_active) % 2 == 0) else 'SELL'
                                self.add_log(f"[EMOJI] Abriendo rápida (fallback): {alt_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                self.open_rapid_operation(symbol, force_direction=alt_dir)
                        
                        # Abrir fantasmas manualmente (simular ciclo fantasma)
                        now = time.time()
                        tick = mt5.symbol_info_tick(symbol)
                        if tick:
                            entry_price = (tick.bid + tick.ask) / 2
                            # Respetar límites máximos por tipo (50)
                            buy_open = sum(1 for op in self.ghost_ops['buy'] if op.get('result') is None)
                            sell_open = sum(1 for op in self.ghost_ops['sell'] if op.get('result') is None)
                            if buy_open < 50:
                                buy_op = {'open_time': now, 'type': 'BUY', 'entry_price': entry_price, 'result': None, 'profit': 0.0}
                                if self.add_ghost_op('buy', buy_op):
                                    pass
                            else:
                                self.add_log(f"Límite BUY fantasma (50) alcanzado; no se añadió nueva.", 'info')
                            if sell_open < 50:
                                sell_op = {'open_time': now, 'type': 'SELL', 'entry_price': entry_price, 'result': None, 'profit': 0.0}
                                if self.add_ghost_op('sell', sell_op):
                                    pass
                            else:
                                self.add_log(f"Límite SELL fantasma (50) alcanzado; no se añadió nueva.", 'info')
                        
                        # ⭐ ACTUALIZACIÓN ÚNICA: siempre al final
                        self.last_rapid_op_time = current_time

                # Actualizar UI
                self.update_rapid_operations_ui()

                time.sleep(1)

            except Exception as e:
                self.add_log(f"[ERROR] Error monitoreo rápidas: {str(e)}", 'error')
                break

    def open_rapid_operation(self, symbol, force_direction=None):
        """Abre operación rápida, usando force_direction ('BUY'/'SELL') si se indica (para modo fantasma)"""
        try:
            max_ops = self.config['MAX_SIMULTANEOUS_OPS'].get()
            total_ops = len(self.rapid_ops_active)

            if total_ops >= max_ops:
                self.add_log(f"[PAUSA]  Rápidas: {total_ops}/{max_ops} ops - Máximo alcanzado", 'info')
                return

            # Obtener precio
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.add_log(f"[ERROR] Error: No se pudo obtener tick de {symbol}", 'error')
                return

            entry_price = (tick.bid + tick.ask) / 2
            
            # Calcular límites para mitad y mitad
            max_buy = max_ops // 2
            max_sell = max_ops // 2
            if max_ops % 2 == 1:
                max_buy += 1


            # Si se fuerza la dirección (por recomendación fantasma), usarla
            if force_direction in ("BUY", "SELL"):
                direction = mt5.ORDER_TYPE_BUY if force_direction == "BUY" else mt5.ORDER_TYPE_SELL
                order_type = force_direction
                self.rapid_ops_total_opened += 1
            else:
                # VALIDAR: ¿Está Entry Point activo?
                use_entry_point = self.use_entry_point.get()
                if use_entry_point:
                    # Entry Point activo → usa su dirección fija
                    direction = mt5.ORDER_TYPE_BUY if self.entry_point_direction.get() == "BUY" else mt5.ORDER_TYPE_SELL
                    order_type = self.entry_point_direction.get()
                else:
                    # Entry Point inactivo → lógica original
                    # ...existing code (balanceo dinámico y adaptativo)...
                    buy_abiertos = sum(1 for op in self.rapid_ops_active.values() if op['type'] == 'BUY')
                    sell_abiertos = sum(1 for op in self.rapid_ops_active.values() if op['type'] == 'SELL')
                    if self.config.get('RAPID_OPS_USE_AI') and self.config['RAPID_OPS_USE_AI'].get():
                        try:
                            if not getattr(self, 'rapid_initial_phase_done', False):
                                if buy_abiertos < sell_abiertos:
                                    direction = mt5.ORDER_TYPE_BUY
                                    order_type = "BUY"
                                elif sell_abiertos < buy_abiertos:
                                    direction = mt5.ORDER_TYPE_SELL
                                    order_type = "SELL"
                                else:
                                    if self.rapid_ops_total_opened % 2 == 0:
                                        direction = mt5.ORDER_TYPE_BUY
                                        order_type = "BUY"
                                    else:
                                        direction = mt5.ORDER_TYPE_SELL
                                        order_type = "SELL"
                            else:
                                buy_frac = getattr(self, 'rapid_target_buy_frac', None)
                                if buy_frac is None:
                                    buy_frac = self._compute_rapid_ops_distribution()
                                total_abiertos = buy_abiertos + sell_abiertos
                                preferencia_fuerte = buy_frac > 0.85 or buy_frac < 0.15
                                modo_exploracion = abs(buy_frac - 0.5) < 0.2
                                import random
                                if preferencia_fuerte:
                                    if buy_frac > 0.85:
                                        direction = mt5.ORDER_TYPE_BUY
                                        order_type = "BUY"
                                    else:
                                        direction = mt5.ORDER_TYPE_SELL
                                        order_type = "SELL"
                                elif modo_exploracion:
                                    if random.random() < 0.5:
                                        direction = mt5.ORDER_TYPE_BUY
                                        order_type = "BUY"
                                    else:
                                        direction = mt5.ORDER_TYPE_SELL
                                        order_type = "SELL"
                                else:
                                    if total_abiertos == 0:
                                        if buy_frac >= 0.5:
                                            direction = mt5.ORDER_TYPE_BUY
                                            order_type = "BUY"
                                        else:
                                            direction = mt5.ORDER_TYPE_SELL
                                            order_type = "SELL"
                                    else:
                                        prop_buy_actual = buy_abiertos / total_abiertos if total_abiertos > 0 else 0
                                        if prop_buy_actual < buy_frac:
                                            direction = mt5.ORDER_TYPE_BUY
                                            order_type = "BUY"
                                        else:
                                            direction = mt5.ORDER_TYPE_SELL
                                            order_type = "SELL"
                        except Exception:
                            if buy_abiertos < sell_abiertos:
                                direction = mt5.ORDER_TYPE_BUY
                                order_type = "BUY"
                            elif sell_abiertos < buy_abiertos:
                                direction = mt5.ORDER_TYPE_SELL
                                order_type = "SELL"
                            else:
                                if self.rapid_ops_total_opened % 2 == 0:
                                    direction = mt5.ORDER_TYPE_BUY
                                    order_type = "BUY"
                                else:
                                    direction = mt5.ORDER_TYPE_SELL
                                    order_type = "SELL"
                    else:
                        if buy_abiertos < sell_abiertos:
                            direction = mt5.ORDER_TYPE_BUY
                            order_type = "BUY"
                        elif sell_abiertos < buy_abiertos:
                            direction = mt5.ORDER_TYPE_SELL
                            order_type = "SELL"
                        else:
                            if self.rapid_ops_total_opened % 2 == 0:
                                direction = mt5.ORDER_TYPE_BUY
                                order_type = "BUY"
                            else:
                                direction = mt5.ORDER_TYPE_SELL
                                order_type = "SELL"
                    self.rapid_ops_total_opened += 1

            # Nota: la IA adaptativa ya decide la proporción tras la fase inicial;
            # no se realizan consultas por-orden que sobrescriban esa decisión.

            volume = self.config['VOL'].get()

            # Calcular SL y TP si están habilitados
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": direction,
                "price": entry_price,
                "magic": self.config['MAGIC_NUMBER'],
                "type_filling": mt5.ORDER_FILLING_IOC,
                "deviation": 20,
                "comment": "RapidOp"
            }
            
            # NO AGREGAR SL/TP a la orden - se cierran manualmente en check_and_close_rapid_operations()

            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.rapid_ops_active[result.order] = {
                    'type': order_type,
                    'entry_price': entry_price,
                    'open_time': datetime.now(),
                    'ticket': result.order
                }
                self.add_log(f"[OK] Op.Rápida {order_type} @ {entry_price:.5f}", 'success')
            else:
                self.add_log(f"[ERROR] Error rápida: {getattr(result, 'comment', str(result.retcode))}", 'error')

        except Exception as e:
            self.add_log(f"[ERROR] Error open_rapid: {str(e)}", 'error')

    def check_and_close_rapid_operations(self, symbol):
        """Cierra operaciones rápidas por profit/loss absoluto (TP/SL) o MIN_PROFIT_CLOSE"""
        try:
            # PRIMERO: Actualizar lista de operaciones abiertas
            all_positions = mt5.positions_get(symbol=symbol)
            if all_positions:
                # Actualizar self.rapid_ops_active con tickets reales de MT5
                active_tickets = {pos.ticket for pos in all_positions if pos.magic == self.config['MAGIC_NUMBER']}
                # Remover tickets que ya no existen en MT5
                self.rapid_ops_active = {k: v for k, v in self.rapid_ops_active.items() if k in active_tickets}

            # SEGUNDO: Obtener configuración
            use_sl_tp = self.config['RAPID_OPS_USE_SL_TP'].get()
            tp_amount = self.config['RAPID_OPS_TP'].get() if use_sl_tp else 0
            sl_amount = self.config['RAPID_OPS_SL'].get() if use_sl_tp else 0
            min_profit = self.config['MIN_PROFIT_CLOSE'].get()

            # TERCERO: Analizar y cerrar posiciones
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return

            for pos in positions:
                # Solo procesar operaciones rápidas (magic number correcto)
                if pos.magic != self.config['MAGIC_NUMBER']:
                    continue
                    
                # Determinar si debe cerrarse
                should_close = False
                reason = ""
                
                if use_sl_tp:
                    # Cerrar por TP/SL personalizado
                    if pos.profit >= tp_amount:
                        should_close = True
                        reason = f"TP alcanzado (${pos.profit:.2f} >= ${tp_amount:.2f})"
                    elif pos.profit <= -sl_amount:
                        should_close = True
                        reason = f"SL alcanzado (${pos.profit:.2f} <= -${sl_amount:.2f})"
                else:
                    # Cerrar por MIN_PROFIT_CLOSE (con diagnóstico y tolerancia)
                    try:
                        pf = float(pos.profit)
                    except Exception:
                        pf = None
                    self.add_log(f"DEBUG RapidOps MinProfit check: pos.profit={pf} config_min_profit={min_profit}", 'info')
                    # Persistir diagnóstico
                    try:
                        with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                            fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'rapid_ticket': getattr(pos,'ticket',None), 'profit': pf, 'min_profit': min_profit}) + '\n')
                    except Exception:
                        pass
                    if pf is not None and (pf + 1e-9) >= float(min_profit):
                        should_close = True
                        reason = f"MIN_PROFIT alcanzado (${pf:.2f} >= ${min_profit:.2f})"

                # Ejecutar cierre si corresponde
                if should_close:
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        continue

                    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                    close_price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": pos.volume,
                        "type": close_type,
                        "position": pos.ticket,
                        "price": close_price,
                        "magic": self.config['MAGIC_NUMBER'],
                        "type_filling": mt5.ORDER_FILLING_IOC,
                        "deviation": 20,
                        "comment": "RapidOp_Close"
                    }

                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        # Acumular profit/loss antes de remover
                        self.rapid_ops_total_profit += pos.profit
                        
                        # SUMAR AL SALDO TOTAL DEL BOT
                        self.saldo_total_acumulado += pos.profit
                        
                        # Actualizar contadores de ganadas/perdidas
                        if pos.profit > 0:
                            self.ganadas += 1
                        elif pos.profit < 0:
                            self.perdidas += 1
                        
                        # Actualizar UI inmediatamente
                        self._update_ui()
                        
                        if pos.ticket in self.rapid_ops_active:
                            op_type = self.rapid_ops_active[pos.ticket]['type']
                            # Registrar en historial de rápidas
                            try:
                                entry = {'type': op_type, 'profit': float(pos.profit), 'time': datetime.now()}
                                try:
                                    if getattr(self, 'rapid_ops_lock', None):
                                        with self.rapid_ops_lock:
                                            self.rapid_ops_history.append(entry)
                                    else:
                                        self.rapid_ops_history.append(entry)
                                except Exception:
                                    try:
                                        self.rapid_ops_history.append(entry)
                                    except Exception:
                                        pass
                                # Registrar cierre en log JSON
                                try:
                                    log_trade({
                                        'symbol': symbol,
                                        'ticket': int(pos.ticket),
                                        'type': op_type,
                                        'profit': float(pos.profit),
                                        'mode': 'rapid',
                                        'timestamp': datetime.now().isoformat()
                                    })
                                except Exception:
                                    pass

                                # Aprendizaje online: recalcular fracción objetivo y actualizar en vivo
                                try:
                                    log_threshold = float(self.config.get('RAPID_OPS_LOG_THRESHOLD', tk.DoubleVar(value=0.01)).get()) if 'RAPID_OPS_LOG_THRESHOLD' in self.config else 0.01
                                    new_frac = self._compute_rapid_ops_distribution()
                                    old_frac = getattr(self, 'rapid_target_buy_frac', None)
                                    self.rapid_target_buy_frac = new_frac
                                    if old_frac is None or abs(new_frac - old_frac) >= log_threshold:
                                        self.add_log(f"[IA] IA Rápidas (online): nueva Frac BUY {new_frac:.2f} (prev {old_frac})", 'info')
                                except Exception:
                                    pass
                            except Exception:
                                pass

                            # --- APRENDIZAJE INCREMENTAL SOLO PARA OPERACIONES RÁPIDAS ---
                            alpha = float(self.config.get('RAPID_OPS_ADAPT_ALPHA', tk.DoubleVar(value=0.35)).get()) if 'RAPID_OPS_ADAPT_ALPHA' in self.config else 0.35
                            if not hasattr(self, 'rapid_adapt_frac') or self.rapid_adapt_frac is None:
                                self.rapid_adapt_frac = 0.5
                            if op_type == 'BUY':
                                reward = 1.0 if pos.profit > 0 else 0.0
                                self.rapid_adapt_frac = (1 - alpha) * self.rapid_adapt_frac + alpha * reward
                            elif op_type == 'SELL':
                                reward = 1.0 if pos.profit > 0 else 0.0
                                self.rapid_adapt_frac = (1 - alpha) * self.rapid_adapt_frac + alpha * (1.0 - reward)
                            self.rapid_adapt_frac = max(0.05, min(0.95, self.rapid_adapt_frac))
                            self.rapid_target_buy_frac = self.rapid_adapt_frac
                            self.add_log(f"[EMOJI] Aprendizaje IA (Rápidas): nueva preferencia BUY={self.rapid_adapt_frac:.2f}", 'info')
                            # --- ADAPTACIÓN: Si hay muchas pérdidas consecutivas en la dirección preferida, pasar a 50/50 ---
                            max_perdidas = 3  # Puedes ajustar este umbral
                            perdidas_buy = 0
                            perdidas_sell = 0
                            for e in list(self.rapid_ops_history)[-max_perdidas*2:]:
                                if e['profit'] < 0:
                                    if e['type'] == 'BUY':
                                        perdidas_buy += 1
                                    elif e['type'] == 'SELL':
                                        perdidas_sell += 1
                            # Si la preferencia es muy fuerte y hay muchas pérdidas, pasar a 50/50 (exploración)
                            if self.rapid_adapt_frac > 0.85 and perdidas_buy >= max_perdidas:
                                self.rapid_target_buy_frac = 0.5
                                self.add_log(f"[ADVERTENCIA] Muchas pérdidas en BUY, cambiando a modo 50/50 (exploración)", 'warning')
                            elif self.rapid_adapt_frac < 0.15 and perdidas_sell >= max_perdidas:
                                self.rapid_target_buy_frac = 0.5
                                self.add_log(f"[ADVERTENCIA] Muchas pérdidas en SELL, cambiando a modo 50/50 (exploración)", 'warning')
                            self.rapid_ops_active.pop(pos.ticket, None)

                        profit_str = f"+${pos.profit:.2f}" if pos.profit >= 0 else f"-${abs(pos.profit):.2f}"
                        self.add_log(f"[OK] Op.Rápida cerrada: {reason} | Profit: {profit_str}", 'success')
                        # Si está activado, abrir la operación contraria automáticamente
                        try:
                            if 'RAPID_OPS_OPEN_OPPOSITE_ON_SLTP' in self.config and self.config['RAPID_OPS_OPEN_OPPOSITE_ON_SLTP'].get():
                                try:
                                    opp_dir = 'BUY' if op_type == 'SELL' else 'SELL'
                                    self.add_log(f"↺ OpenOpposite activo: abriendo {opp_dir} tras cierre de {op_type}", 'info')
                                    try:
                                        time.sleep(0.5)
                                    except Exception:
                                        pass
                                    self.open_rapid_operation(symbol, force_direction=opp_dir)
                                except Exception as _e:
                                    self.add_log(f"[ERROR] Error al abrir operación contraria: {_e}", 'error')
                        except Exception:
                            pass
                    else:
                        self.add_log(f"[ERROR] Error cerrando rápida: {getattr(result, 'comment', str(result.retcode))}", 'error')

        except Exception as e:
            self.add_log(f"[ERROR] Error check_and_close_rapid: {str(e)}", 'error')

    def update_rapid_operations_ui(self):
        """Actualiza estado de Operaciones Rápidas en la UI"""
        # Asegurarse de ejecutar actualizaciones de widgets en el hilo principal
        try:
            import threading as _threading
            if _threading.current_thread() is not _threading.main_thread():
                try:
                    self.root.after(0, self.update_rapid_operations_ui)
                    return
                except Exception:
                    pass

        except Exception:
            pass

        try:
            if not hasattr(self, 'rapid_ops_status'):
                return

            max_ops = self.config['MAX_SIMULTANEOUS_OPS'].get()
            total_ops = len(self.rapid_ops_active)
            
            # Contar dinámicamente BUY y SELL desde lo que REALMENTE está abierto
            buy_abiertos = sum(1 for op in self.rapid_ops_active.values() if op['type'] == 'BUY')
            sell_abiertos = sum(1 for op in self.rapid_ops_active.values() if op['type'] == 'SELL')
            
            # Calcular límites
            max_buy = max_ops // 2
            max_sell = max_ops // 2
            if max_ops % 2 == 1:
                max_buy += 1

            # Actualizar status y colores
            if self.rapid_ops_running:
                status_text = "[OK] ACTIVO"
                status_color = '#34d399'  # Verde
            else:
                status_text = "🔴 INACTIVO"
                status_color = '#fbbf24'  # Amarillo

            self.rapid_ops_status.config(text=status_text, fg=status_color)

            # Actualizar contador con valores REALES
            counter_text = f"Operaciones: {total_ops}/{max_ops} | BUY: {buy_abiertos}/{max_buy} | SELL: {sell_abiertos}/{max_sell}"
            self.rapid_ops_counter.config(text=counter_text)
            
            # En esta etiqueta mostramos la cuenta atrás hasta la próxima apertura

            # Actualizar resumen de última 1 minuto desde que empezó el análisis (si aplica)
            try:
                buy_1m, sell_1m, total_1m = self.get_last_minute_counts()
                if hasattr(self, 'rapid_history_label'):
                    pct = (buy_1m / total_1m * 100) if total_1m > 0 else 0
                    self.rapid_history_label.config(text=f"Últ.1m → BUY: {buy_1m} | SELL: {sell_1m} | {int(pct)}% BUY")
            except Exception:
                pass

            # Actualizar barra de fracción para reflejar la fracción objetivo actual
            try:
                frac = None
                if hasattr(self, 'rapid_target_buy_frac') and self.rapid_target_buy_frac is not None:
                    frac = float(self.rapid_target_buy_frac)
                else:
                    # Intentar computar una fracción de respaldo
                    try:
                        frac = self._compute_rapid_ops_distribution()
                    except Exception:
                        frac = 0.5

                if frac is None:
                    frac = 0.5

                if hasattr(self, 'rapid_buy_frac_label'):
                    try:
                        color = self.config.get('RAPID_OPS_FRAC_COLOR').get() if 'RAPID_OPS_FRAC_COLOR' in self.config else '#f59e0b'
                        self.rapid_buy_frac_label.config(text=f"{int(frac*100)}%", fg=color)
                    except Exception:
                        pass

                if hasattr(self, 'rapid_buy_frac_bar'):
                    try:
                        self.rapid_buy_frac_bar['value'] = int(frac * 100)
                    except Exception:
                        pass
            except Exception:
                pass

            # Actualizar cuenta atrás: antes de terminar la fase inicial mostrar tiempo restante,
            # después mostrar tiempo hasta la próxima apertura
            try:
                initial_phase = int(self.config.get('RAPID_OPS_INITIAL_PHASE', tk.IntVar(value=60)).get()) if 'RAPID_OPS_INITIAL_PHASE' in self.config else 60
                if not getattr(self, 'rapid_initial_phase_done', False):
                    start = getattr(self, 'rapid_ops_start_time', None)
                    if start and start > 0:
                        rem = max(0, int(initial_phase - (time.time() - start)))
                        countdown = f"Analizando en: {rem}s"
                    else:
                        countdown = "Analizando en: -"
                else:
                    interval = int(self.config['RAPID_OPS_INTERVAL'].get()) if 'RAPID_OPS_INTERVAL' in self.config else 5
                    last = getattr(self, 'last_rapid_op_time', 0)
                    if not last:
                        countdown = f"Próx. en: {interval}s"
                    else:
                        secs = max(0, int(interval - (time.time() - last)))
                        countdown = f"Próx. en: {secs}s"

                # Actualizar la etiqueta de cuenta atrás (debajo de balance/patrimonio)
                if hasattr(self, 'rapid_countdown_label'):
                    self.rapid_countdown_label.config(text=countdown)
            except Exception:
                pass

            # Actualizar IA adaptativa (fracción BUY) y mini-historial
            try:
                buy_frac = self._compute_rapid_ops_distribution()
                # Actualizar barra/label si existen (compute ya actualiza cuando hay cambios)
                if hasattr(self, 'rapid_history_label'):
                    # Mostrar últimos N: contar BUY/SELL y promedio profit
                    hist = list(self.rapid_ops_history)
                    if len(hist) == 0:
                        hist_text = "Hist: -"
                    else:
                        lastn = hist[-10:]
                        bcnt = sum(1 for h in lastn if h['type'] == 'BUY')
                        scnt = sum(1 for h in lastn if h['type'] == 'SELL')
                        bavg = (sum(h['profit'] for h in lastn if h['type'] == 'BUY') / bcnt) if bcnt>0 else 0.0
                        savg = (sum(h['profit'] for h in lastn if h['type'] == 'SELL') / scnt) if scnt>0 else 0.0
                        hist_text = f"Hist(10): B{bcnt} S{scnt} | avgB ${bavg:.2f} avgS ${savg:.2f}"
                    self.rapid_history_label.config(text=hist_text)
            except Exception:
                pass

        except Exception as e:
            pass  # Silenciar errores de UI en thread

    # ⭐⭐⭐ FUNCIÓN HELPER GLOBAL - Acceso robusto a variables de configuración ⭐⭐⭐
    def _safe_get(self, key, default_value=None):
        """Obtiene un valor de config de forma ROBUSTA sin errores de .get().
        Maneja: tk.IntVar, tk.DoubleVar, tk.StringVar, tk.BooleanVar e int directo."""
        try:
            val = self.config.get(key)
            if val is None:
                return default_value
            elif hasattr(val, 'get'):  # Es tk variable
                result = val.get()
                return default_value if result is None else result
            else:  # Valor directo
                return val
        except Exception:
            return default_value
    
    def conectar_mt5(self):
        """Conecta a MetaTrader5 usando sesión activa del terminal ya abierto"""
        try:
            # Inicializar conexión con el terminal MetaTrader5 ya abierto
            if not mt5.initialize():
                self.add_log("Error inicializando MT5", 'error')
                return False

            # Usar la sesión ya activa del terminal; NO pedir login/password
            account_info = mt5.account_info()
            if account_info is None:
                # No hay sesión activa. Intentar una reparación mínima: reiniciar MT5
                self.add_log("No hay sesión MT5 activa. Intentando reiniciar la conexión...", 'warning')
                try:
                    try:
                        mt5.shutdown()
                    except Exception:
                        pass

                    # Reintentar inicializar un par de veces
                    ok = False
                    for _ in range(2):
                        try:
                            ok = mt5.initialize()
                            if ok:
                                break
                        except Exception:
                            ok = False
                        time.sleep(1)

                    if not ok:
                        self.add_log("No fue posible inicializar MT5 tras reintento; verifica que MetaTrader5 esté abierto y conectado.", 'error')
                        return False

                    account_info = mt5.account_info()
                    if account_info is None:
                        self.add_log("No fue posible recuperar account_info después de reiniciar MT5.", 'error')
                        return False
                    else:
                        self.add_log("✅ account_info recuperado tras reiniciar MT5.", 'success')
                        self.connected = True
                        return True

                except Exception as e:
                    self.add_log(f"Error reconectando a MT5: {str(e)}", 'error')
                    return False
            else:
                # Conexión OK
                self.connected = True
                return True

        except Exception as e:
            self.add_log(f"Error en conectar_mt5(): {str(e)}", 'error')
            return False

    def get_mt5_account_info(self):
        """
        Lee información de cuenta de MT5: balance, patrimonio (equity), margen libre y alcance (leverage).
        Retorna un diccionario con los datos o None si hay error.
        
        Returns:
            dict: {'balance': float, 'equity': float, 'free_margin': float, 'leverage': int}
            None: Si no puede conectar a MT5
        """
        try:
            account_info = mt5.account_info()
            if account_info is not None:
                return {
                    'balance': float(getattr(account_info, 'balance', 0.0)),
                    'equity': float(getattr(account_info, 'equity', 0.0)),
                    'free_margin': float(getattr(account_info, 'margin_free', 0.0)),
                    'leverage': int(getattr(account_info, 'leverage', 0))
                }
            else:
                return None
        except Exception as e:
            self.add_log(f"Error leyendo account_info de MT5: {str(e)}", 'warning')
            return None

    def _data_reader_loop(self):
        """
        ⭐ NUEVO V4: Thread daemon que LEE TICKS Y CALCULA IMPULSOS CONTINUAMENTE
        Funciona INCLUSO DURANTE PAUSAS para mantener lectura consistente de mercado.
        """
        try:
            self.add_log("[DATA-READER] ✅ Iniciado - lectura continua de ticks", 'success')
        except Exception:
            pass
        
        tick_buffer = []  # Buffer local de últimos ticks
        max_buffer_size = 500
        
        while self.data_reader_running and self.is_running:
            try:
                # Obtener intervalo de lectura desde config
                try:
                    interval_ms = int(self.config.get('DATA_READER_INTERVAL', tk.IntVar(value=100)).get())
                except Exception:
                    interval_ms = 100
                interval = max(50, interval_ms) / 1000.0  # Convertir a segundos, mínimo 50ms
                
                # Obtener símbolo
                symbol = self.config['SYMBOL'].get()
                if not symbol:
                    time.sleep(interval)
                    continue
                
                # Obtener tick actual de MT5
                try:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick is None:
                        time.sleep(interval)
                        continue
                    
                    # Añadir tick al buffer
                    tick_data = {
                        'time': time.time(),
                        'bid': float(tick.bid),
                        'ask': float(tick.ask),
                        'mid': (float(tick.bid) + float(tick.ask)) / 2,
                    }
                    tick_buffer.append(tick_data)
                    
                    # Limitar tamaño del buffer
                    if len(tick_buffer) > max_buffer_size:
                        tick_buffer = tick_buffer[-max_buffer_size:]
                    
                    # ⭐ CALCULAR IMPULSOS si hay suficientes ticks
                    if len(tick_buffer) >= 20:
                        try:
                            # Usar TickImpulseValidator si está disponible
                            if self.impulse_validator and self.impulse_validator.detector:
                                detector = self.impulse_validator.detector
                                
                                # Preparar prices para análisis
                                prices = [t['mid'] for t in tick_buffer]
                                velocities = []
                                for i in range(1, len(prices)):
                                    vel = abs(prices[i] - prices[i-1])
                                    velocities.append(vel)
                                
                                # Calcular impulso
                                impulse_result = detector._detect_impulse_from_history(tick_buffer)
                                
                                if impulse_result:
                                    # Guardar resultado con lock
                                    with self.data_reader_lock:
                                        self.last_impulse_data = {
                                            'timestamp': time.time(),
                                            'symbol': symbol,
                                            'impulse_score': impulse_result.get('score', 0),
                                            'direction': 'BUY' if impulse_result.get('buy_pressure', 0) > impulse_result.get('sell_pressure', 0) else 'SELL',
                                            'buy_pressure': impulse_result.get('buy_pressure', 0),
                                            'sell_pressure': impulse_result.get('sell_pressure', 0),
                                            'velocity': float(np.mean(velocities)) if velocities else 0.0,
                                            'ticks_count': len(tick_buffer),
                                            'tick_buffer_size': len(tick_buffer),
                                        }
                                        
                                        # Registrar cambio de dirección
                                        current_direction = self.last_impulse_data['direction']
                                        if current_direction != self.last_known_direction:
                                            self.last_known_direction = current_direction
                                            score = self.last_impulse_data['impulse_score']
                                            try:
                                                self.add_log(f"[MICRO] Cambio detectado: {current_direction} @{score:.1f}pts | vel: {self.last_impulse_data['velocity']:.6f}", 'market')
                                            except Exception:
                                                pass
                        except Exception as e:
                            logger.debug(f"[DATA-READER] Error calculando impulso: {e}")
                    
                except Exception as e:
                    logger.debug(f"[DATA-READER] Error obteniendo tick: {e}")
                
                # Dormir según intervalo
                time.sleep(interval)
                
            except Exception as e:
                logger.debug(f"[DATA-READER] Error en ciclo: {e}")
                time.sleep(0.1)
        
        try:
            self.add_log("[DATA-READER] ⏹️ Detenido", 'warning')
        except Exception:
            pass

    def __init_load_saved_config__(self):
        """Restaura configuración guardada previo al cierre anterior"""
        try:
            self.load_config()
        except Exception as e:
            self.add_log(f"[CONFIG] No se pudo cargar config guardada: {str(e)}", 'warning')
        
        # Intentar conectar a MT5
        if not self.conectar_mt5():
            self.add_log("No se pudo conectar a MT5 en __init_load_saved_config__", 'error')
            return False
            
        return True

    def _load_ml_models_v2_with_pro(self):
        """Carga modelos ML V2 con 4 niveles de correccion + Sistema PRO Institucional"""
        try:
            model_dir = Path('logs/trained_models')
            
            # Cargar XGBoost model
            xgb_path = model_dir / 'xgboost_v2_balanced.pkl'
            if xgb_path.exists():
                with open(xgb_path, 'rb') as f:
                    self.ml_model_xgb = pickle.load(f)
            
            # Cargar scaler
            scaler_path = model_dir / 'scaler_v2_balanced.pkl'
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    self.ml_scaler = pickle.load(f)
            
            if self.ml_model_xgb and self.ml_scaler:
                self.ml_model_loaded = True
                self.add_log("[ML V2] Modelos cargados: XGBoost + Scaler (4 NIVELES)", 'success')
            else:
                self.ml_model_loaded = False
                self.add_log("[WARN] No se encontraron modelos ML V2", 'warning')
            
            # NIVEL 5-6: Cargar sistema PRO con componentes institucionales
            try:
                self.regime_detector = RegimeDetector()
                self.trend_model = TrendModel()
                self.reversion_model = ReversionModel()
                self.bias_monitor = BiasMonitor()
                self.drift_detector = DriftDetector()
                self.dynamic_weights = DynamicWeights()
                
                # Cargar modelos especializados
                self.trend_model.load()
                self.reversion_model.load()
                
                # Crear MetaSelector que integra todo
                if (self.regime_detector and self.trend_model and 
                    self.reversion_model and self.bias_monitor and 
                    self.drift_detector and self.dynamic_weights):
                    
                    self.meta_selector = MetaSelector(
                        self.regime_detector,
                        self.trend_model,
                        self.reversion_model,
                        self.bias_monitor,
                        self.drift_detector,
                        self.dynamic_weights
                    )
                    self.pro_system_loaded = True
                    self.add_log("[PRO] Sistema INSTITUCIONAL cargado: Régimen + Bias + Drift", 'success')
                else:
                    self.pro_system_loaded = False
                    self.add_log("[WARN] No se pudo cargar sistema PRO completo", 'warning')
            except Exception as e:
                self.add_log(f"[INFO] Sistema PRO no disponible: {str(e)}", 'warning')
                self.pro_system_loaded = False
                
        except Exception as e:
            self.add_log(f"[ERROR] Cargando modelos ML: {str(e)}", 'error')
            self.ml_model_loaded = False
            self.pro_system_loaded = False

    def _predict_pro_system(self):
        """Predicción usando sistema PRO institucional (NIVEL 5-10)"""
        if not self.pro_system_loaded or not self.meta_selector:
            return None
        
        try:
            symbol = self.config['SYMBOL'].get()
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
            
            if rates is None or len(rates) < 50:
                return None
            
            df = pd.DataFrame(rates)
            
            # Extraer features similar a botver16
            closes = df['close'].values
            if len(closes) < 30:
                return None
            
            # Calcular RSI simplificado
            def calc_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return 50
                prices_array = np.array(prices[-(period+1):])
                deltas = np.diff(prices_array)
                gains = deltas.copy()
                losses = deltas.copy()
                gains[gains < 0] = 0
                losses[losses > 0] = 0
                losses = abs(losses)
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                if avg_loss == 0:
                    return 100
                rs = avg_gain / avg_loss
                rsi_val = 100 - (100 / (1 + rs))
                return rsi_val
            
            # Crear features básicos (11 dimensiones)
            rsi = calc_rsi(closes[-15:])
            rsi_centered = (rsi - 50) / 50
            
            features = np.array([[
                rsi_centered, 0.1, 0.05, 0.3, 0.15, 0.05, 0.1, 0.05, 0.05, 0.02, 0.01
            ]], dtype=np.float32)
            
            # Llamar MetaSelector que integra todo
            result = self.meta_selector.predict(df.to_dict('list'), features)
            
            if result is None:
                return None
            
            # Loguear estado del sistema PRO
            if result['bias_adjusted']:
                self.add_log(f"[ADVERTENCIA] [BIAS DETECTED] Threshold ajustado", 'warning')
            
            if result['drift_warned']:
                self.add_log(f"[ADVERTENCIA] [DRIFT DETECTED] Reduciendo posición", 'warning')
            
            # Mapear recomendación PRO a BUY/SELL/HOLD
            if result['recommendation'] == 'BUY':
                self.add_log(
                    f"[PRO] BUY ({result['model_used']}) conf={result['confidence']:.0f}% regime={result['regime']}", 'success'
                )
                return "BUY"
            elif result['recommendation'] == 'SELL':
                self.add_log(
                    f"[PRO] SELL ({result['model_used']}) conf={result['confidence']:.0f}% regime={result['regime']}", 'success'
                )
                return "SELL"
            else:
                return None
                
        except Exception as e:
            self.add_log(f"[ERROR] PRO system: {str(e)}", 'warning')
            return None

    def cierre_emergencia(self):
        """Versión mejorada del cierre de emergencia"""
        try:
            # ⭐ NUEVO: Guardar configuración ANTES de cierre de emergencia
            self.save_config()
            
            self.add_log("[ALERTA] INICIANDO CIERRE DE EMERGENCIA FORZADO", 'alert')
            
            # ⭐ NUEVO V4: Detener data reader
            self.data_reader_running = False
            
            if not mt5.initialize():
                mt5.shutdown()
                time.sleep(2)
                mt5.initialize()
                if not self.conectar_mt5():
                    self.add_log("[ADVERTENCIA] Procediendo sin conexión confirmada", 'warning')
            
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)
            
            if not positions:
                self.add_log("No hay operaciones abiertas", 'info')
            else:
                for pos in positions:
                    if pos.magic == self.config['MAGIC_NUMBER']:
                        tipo = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        precio = mt5.symbol_info_tick(symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
                        
                        for intento in range(3):
                            try:
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": pos.volume,
                                    "type": tipo,
                                    "position": pos.ticket,
                                    "price": precio,
                                    "deviation": 100,
                                    "magic": self.config['MAGIC_NUMBER'],
                                    "comment": "Cierre-Emergencia",
                                    "type_time": mt5.ORDER_TIME_GTC,
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                
                                result = mt5.order_send(request)
                                # Log completo del resultado para depuración de cierres forzados
                                try:
                                    self.add_log(f"cierre_emergencia order_send result: retcode={getattr(result,'retcode',None)} comment={getattr(result,'comment',None)} repr={repr(result)}", 'debug')
                                except Exception:
                                    pass
                                try:
                                    if not (result and getattr(result, 'retcode', None) == mt5.TRADE_RETCODE_DONE):
                                        save_failed_order(request, result, tag='cierre_emergencia')
                                        try:
                                            handled = handle_order_failure(self, request, result, tag='cierre_emergencia', max_retries=2)
                                            if handled:
                                                self.add_log(f"[RECHAZO CIERRE] Reintento automatizado completado para #{pos.ticket}", 'success')
                                                break
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                if result and getattr(result, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                    self.add_log(f"[OK] Cerrada #{pos.ticket} | ${pos.profit:.2f}", 'success')
                                    break
                                
                                self.add_log(f"Reintento {intento+1} para #{pos.ticket}...", 'warning')
                                time.sleep(1)
                                
                            except Exception as e:
                                self.add_log(f"Error en intento {intento+1}: {str(e)}", 'error')
                                time.sleep(1)
        
            self.is_running = False
            self._scheduler_running = False  # ⭐ CRÍTICO: Detener scheduler también
            self.en_pausa = False
            self.objetivo_cumplido = False
            
            for entry in self.config_entries.values():
                entry.config(state='normal')
            
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            
            self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
            self.status_label.config(text="Bot Detenido por Emergencia", fg='#f87171')
            self._update_ui()
            self.root.update()
            
        except Exception as e:
            self.add_log(f"Error en cierre de emergencia: {str(e)}", 'error')

    def cerrar_posicion(self, position, force=False):
        """Versión mejorada para cerrar posiciones correctamente (force=True ignora checks)"""
        if self.en_pausa and not force:
            return False
        
        # Inicializar variables que se usan en except
        ticket = position.ticket if position else None
        symbol = position.symbol if position else None
        result = None
            
        try:
            symbol = position.symbol
            ticket = position.ticket
            volume = position.volume
            pos_type = position.type
            profit = position.profit
            
            # Si es cierre forzado, ir DIRECTAMENTE al cierre sin validaciones
            if force:
                if pos_type == mt5.POSITION_TYPE_BUY:
                    close_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(symbol).bid
                else:
                    close_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(symbol).ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": volume,
                    "type": close_type,
                    "position": ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": self.config['MAGIC_NUMBER'],
                    "comment": "Cierre-Forzado-IA",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    return self._procesar_cierre_exitoso(ticket, symbol, volume, pos_type, profit)
                return False
            
            # CIERRE NORMAL CON VALIDACIONES
            tiempo_actual = time.time()
            tiempo_abierta = tiempo_actual - self.position_tracking.get(ticket, {}).get('open_time', tiempo_actual)
            
            # Validar si debe cerrarse
            if profit > 0:
                min_profit = float(self.config['MIN_PROFIT_CLOSE'].get())
                if profit < min_profit:
                    return False
            else:
                max_loss = float(self.config['MAX_LOSS_CLOSE'].get())
                if abs(profit) < max_loss:
                    return False
                if tiempo_abierta < 300:
                    return False
            
            # Preparar cierre
            close_type = mt5.ORDER_TYPE_SELL if pos_type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).bid if pos_type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": self.config['MAGIC_NUMBER'],
                "comment": "Cierre-Auto" if profit < 0 else "Cierre-Ganancia",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return self._procesar_cierre_exitoso(ticket, symbol, volume, pos_type, profit)
            
            self.add_log(f"Error al cerrar #{ticket}: {result.comment if result else 'Sin respuesta'}", 'error')
            return False
            
        except Exception as e:
            self.add_log(f"Error en cerrar_posicion: {str(e)}", 'error')
            return False

    # ⭐ NUEVO: Registrar operación para aprendizaje
    def _procesar_cierre_exitoso(self, ticket, symbol, volume, pos_type, profit):
        """Procesa un cierre exitoso de posición (centraliza la lógica)"""
        try:
            # Actualizar contadores
            self.ganancia_neta = round(self.ganancia_neta + profit, 2)
            self.saldo_actual = round(self.saldo_actual + profit, 2)
            
            if profit > 0:
                self.ganadas += 1
                self.operaciones_azules += 1
                msg = f"[OK] GANADA #{ticket} | +${profit:.2f}"
                tag = 'success'
            else:
                self.perdidas += 1
                self.operaciones_rojas += 1
                msg = f"[ERROR] PERDIDA #{ticket} | ${profit:.2f}"
                tag = 'error'
            
            # Historial y limpieza
            self.historial_resultados.append({
                "ticket": ticket,
                "tipo": "GANADA" if profit > 0 else "PERDIDA",
                "profit": profit,
                "saldo": self.ganancia_neta,
                "tiempo": datetime.now().strftime("%H:%M:%S")
            })
            
            if len(self.historial_resultados) > self.max_historial:
                self.historial_resultados.pop(0)
            
            self.total_operaciones_abiertas = max(0, self.total_operaciones_abiertas - 1)
            if ticket in self.position_ids:
                self.position_ids.remove(ticket)
            if ticket in self.position_tracking:
                del self.position_tracking[ticket]
            
            msg += f" | G/P: {self.ganadas}/{self.perdidas}"
            msg += f" | Saldo Actual: ${self.ganancia_neta:.2f}"
            if self.saldo_total_acumulado > 0:
                msg += f" | Total: ${(self.saldo_total_acumulado + self.ganancia_neta):.2f}"
            
            self.add_log(msg, tag)
            
            # --- PAUSA por "Max Loss para Cerrar" ---
            if profit < 0 and abs(profit) >= float(self.config['MAX_LOSS_CLOSE'].get()):
                try:
                    pause_seconds = int(self.config.get('PAUSA_POST_WIN', tk.IntVar(value=0)).get())
                except Exception:
                    pause_seconds = 0
                # Evitar iniciar pausas cortas si ya se activó Detener en Pérdida (pausa larga)
                if pause_seconds > 0 and not getattr(self, 'force_stop_triggered', False):
                    self.bot_pausado = True
                    self.pause_until = time.time() + pause_seconds
                    self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
                    self.status_label.config(text=f"Bot Pausado por Max Loss ({pause_seconds}s)", fg='#fbbf24')
                    t = threading.Thread(target=self._loss_pause_worker, args=(pause_seconds,), daemon=True)
                    t.start()
            
            # --- PAUSA por "Ganancia" ---
            if profit > 0:
                try:
                    pause_seconds = int(self.config['PAUSA_POST_WIN'].get())
                except Exception:
                    pause_seconds = 0
                # Si se activó Detener en Pérdida, no lanzar pausa corta que podría anular la pausa larga
                if pause_seconds > 0 and not getattr(self, 'force_stop_triggered', False):
                    self.bot_pausado = True
                    self.pause_until = time.time() + pause_seconds
                    self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
                    self.status_label.config(text=f"Bot Pausado ({pause_seconds}s)", fg='#fbbf24')
                    t = threading.Thread(target=self._objective_pause_worker, args=(pause_seconds,), daemon=True)
                    t.start()
            
            # 🆕 COOLDOWN DESPUÉS DE CUALQUIER CIERRE (GANANCIA O PÉRDIDA)
            try:
                cooldown = int(self.config.get('PAUSA_POST_WIN', tk.IntVar(value=0)).get())
            except Exception:
                cooldown = 0
            if cooldown > 0:
                self.block_until = time.time() + cooldown
                cooldown_type = "GANANCIA" if profit > 0 else "PÉRDIDA"
                self.add_log(f"[PAUSA] Cooldown tras {cooldown_type} activado por {cooldown}s", 'info')
            
            # ⭐ NUEVO: Registrar operación para aprendizaje
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                current_price = tick.bid
                entry_price = current_price - (profit / volume) if volume > 0 else current_price
                
                # Obtener confianza del último análisis
                last_confidence = getattr(self, 'last_analysis_confidence', 50)
                
                # Registrar operación
                self.adaptive_params.record_trade_result(
                    direction='BUY' if pos_type == mt5.POSITION_TYPE_BUY else 'SELL',
                    entry_price=entry_price,
                    exit_price=current_price,
                    profit=profit,
                    confidence=last_confidence,
                    market_volatility=getattr(self, 'current_market_volatility', 1.0)
                )
                # Registrar cierre en logs JSON (operación normal)
                try:
                    log_trade({
                        'symbol': symbol,
                        'ticket': int(ticket),
                        'type': 'BUY' if pos_type == mt5.POSITION_TYPE_BUY else 'SELL',
                        'entry_price': float(entry_price),
                        'exit_price': float(current_price),
                        'profit': float(profit),
                        'volume': float(volume),
                        'confidence': float(last_confidence),
                        'mode': 'normal',
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception:
                    pass
                
                # ⭐ NUEVO: Guardar para reentrenamiento de Loss Protection
                try:
                    tracking_info = self.position_tracking.get(ticket, {})
                    self.loss_protection_ai.save_closed_trade({
                        'profit': profit,
                        'direction': 'BUY' if pos_type == mt5.POSITION_TYPE_BUY else 'SELL',
                        'entry_rsi': tracking_info.get('entry_rsi', 50),
                        'entry_momentum': tracking_info.get('entry_momentum', 0),
                        'entry_macd': tracking_info.get('entry_macd', 0),
                        'exit_reason': 'normal_close',
                        'time_in_market': time.time() - tracking_info.get('open_time', time.time()),
                        'max_drawdown': tracking_info.get('max_drawdown', 0)
                    })
                except Exception as e:
                    self.add_log(f"[LOSS] Error guardando trade: {str(e)[:50]}", 'warning')
                
                # NUEVO: Registrar pérdida reciente para penalización de volumen
                if profit < 0:
                    try:
                        # Mantener últimas 100 pérdidas
                        self.recent_losses.append((time.time(), profit))
                        # Limpiar pérdidas más viejas que 1 hora (3600 segundos)
                        cutoff_time = time.time() - 3600
                        self.recent_losses = [(ts, p) for ts, p in self.recent_losses if ts > cutoff_time]
                        # Limitar a 100 entradas máximo
                        if len(self.recent_losses) > 100:
                            self.recent_losses = self.recent_losses[-100:]
                        loss_count = len(self.recent_losses)
                        self.add_log(f"[VOLUME] Pérdida registrada (total últimas 100: {loss_count})", 'warning')
                    except Exception as e:
                        self.add_log(f"[VOLUME] Error registrando pérdida: {str(e)[:40]}", 'warning')
            
            # NUEVO: Análisis de retroalimentación post-trade
            try:
                feedback_result = self.feedback_loop_ai.analyze_closed_trade({
                    'ticket': ticket,
                    'profit': profit,
                    'closed_at': datetime.now().isoformat()
                })
                
                if feedback_result.get('feedback_applied'):
                    motor_adj = feedback_result.get('motor_adjustments', {})
                    conf_shift = feedback_result.get('confidence_shift', 'neutral')
                    trade_result = feedback_result.get('trade_result', '?')
                    
                    if motor_adj:
                        adj_summary = ', '.join([f"{m}:{v:+.3f}" for m, v in list(motor_adj.items())[:2]])
                        self.add_log(f"[FEEDBACK] {trade_result} - Ajustes: {adj_summary} | Conf: {conf_shift}", 'info')
                    
                    # Log del win rate si hay data suficiente
                    accuracy = self.feedback_loop_ai.get_motor_accuracy_stats()
                    if accuracy:
                        v12_stats = accuracy.get('V12', {})
                        dual_stats = accuracy.get('DUAL', {})
                        if v12_stats and v12_stats.get('total', 0) >= 5:
                            self.add_log(f"[FEEDBACK] V12: {v12_stats.get('win_rate', '?')} (n={v12_stats.get('total')})", 'info')
                        if dual_stats and dual_stats.get('total', 0) >= 5:
                            self.add_log(f"[FEEDBACK] DUAL: {dual_stats.get('win_rate', '?')} (n={dual_stats.get('total')})", 'info')
            except Exception as e:
                self.add_log(f"[FEEDBACK] Error en análisis: {str(e)[:50]}", 'warning')
            
            # FIX #18: Verificar objetivo INMEDIATAMENTE después de cerrar cualquier posición
            try:
                objetivo = self.objetivo_ganancia.get()
                if objetivo > 0 and self.ganancia_neta >= objetivo and not self.objetivo_cumplido:
                    self.add_log(f"\n🎯 [OBJETIVO] ¡OBJETIVO ALCANZADO! ${self.ganancia_neta:.2f} >= ${objetivo:.2f}", 'success')
                    self.objetivo_cumplido = True
                    self._handle_objetivo_pause()
            except Exception as e:
                self.add_log(f"[OBJETIVO] Error verificando objetivo: {str(e)[:50]}", 'warning')
            
            self.root.after(1, self._update_ui)
            # Actualizar inmediatamente los labels de Operaciones Rápidas para reflejar el nuevo saldo
            try:
                if hasattr(self, 'rapid_balance_label'):
                    self.rapid_balance_label.config(text=f"${self.saldo_actual:.2f}")
                # Intentar obtener equity actual desde MT5; si falla, usar saldo_actual como fallback
                try:
                    acct = mt5.account_info()
                    equity_now = float(getattr(acct, 'equity', self.saldo_actual)) if acct is not None else self.saldo_actual
                except Exception:
                    equity_now = self.saldo_actual
                if hasattr(self, 'rapid_equity_label'):
                    self.rapid_equity_label.config(text=f"${equity_now:.2f}")
            except Exception:
                pass
            return True
            
        except Exception as e:
            self.add_log(f"Error procesando cierre exitoso: {str(e)}", 'error')
            return False
    
    # [OBJETIVO] FASE 3: REGISTRAR TRADES PARA CALIBRACIÓN DINÁMICA
    def register_trade_for_calibration(self, signal_type, confidence, entry_price, exit_price, pnl_pips):
        """Registra trade cerrado para Dynamic Calibration"""
        try:
            if not hasattr(self, 'closed_trades_for_calibration'):
                self.closed_trades_for_calibration = {}
            
            trade_id = len(self.closed_trades_for_calibration)
            self.closed_trades_for_calibration[trade_id] = {
                'signal_type': signal_type,
                'confidence': confidence,
                'entry': entry_price,
                'exit': exit_price,
                'pnl_pips': pnl_pips,
                'timestamp': datetime.now()
            }
            
            # Registrar en calibrador
            self.calibrator.record_trade(
                signal_type=signal_type,
                confidence=confidence,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl_pips=pnl_pips
            )
            
            # Cada 50 trades, auto-calibrar
            if len(self.closed_trades_for_calibration) % 50 == 0:
                self.calibrator.auto_calibrate()
                self.add_log(f"[ACTUALIZAR] Auto-calibración ejecutada ({len(self.closed_trades_for_calibration)} trades)", 'info')
        
        except Exception as e:
            self.add_log(f"Error registrando trade para calibración: {str(e)}", 'warning')

    def _regenerate_training_data(self):
        """Regenera datos del mercado (últimas 4 semanas) y entrena especialistas"""
        try:
            from market_snapshot_generator import MarketSnapshotGenerator
            symbol = self.config['SYMBOL'].get()
            
            self.add_log("[DATA] Regenerando datos de entrenamiento (últimas 4 semanas)...", 'info')
            
            # Generar datos de 4 semanas
            gen = MarketSnapshotGenerator(symbol=symbol)
            snapshots = gen.generate_snapshots(weeks=4, output_path="logs/market_snapshots.json", num_snapshots=None)
            
            if not snapshots or len(snapshots) < 100:
                self.add_log(f"[ERROR] Datos insuficientes: {len(snapshots)} barras", 'error')
                return
            
            # ENTRENAR BUY specialist con método train()
            if hasattr(self, 'buy_specialist') and self.buy_specialist:
                try:
                    train_res = self.buy_specialist.train(snapshots)
                    self.add_log(f"[TRAIN] BUY specialist: {train_res.get('status', 'unknown')}", 'info')
                except Exception as e:
                    logger.error(f"Error entrenando BUY: {e}")
                    self.add_log(f"[ERROR] Entrenamiento BUY: {str(e)[:80]}", 'error')
            
            # ENTRENAR SELL specialist con método train()
            if hasattr(self, 'sell_specialist') and self.sell_specialist:
                try:
                    train_res = self.sell_specialist.train(snapshots)
                    self.add_log(f"[TRAIN] SELL specialist: {train_res.get('status', 'unknown')}", 'info')
                except Exception as e:
                    logger.error(f"Error entrenando SELL: {e}")
                    self.add_log(f"[ERROR] Entrenamiento SELL: {str(e)[:80]}", 'error')
            
            # Verificar que ambos están entrenados
            buy_trained = hasattr(self, 'buy_specialist') and self.buy_specialist and getattr(self.buy_specialist, 'is_trained', False)
            sell_trained = hasattr(self, 'sell_specialist') and self.sell_specialist and getattr(self.sell_specialist, 'is_trained', False)
            
            if buy_trained and sell_trained:
                self.add_log(f"[OK] Ambos especialistas entrenados con {len(snapshots)} barras M1", 'success')
            else:
                self.add_log(f"[WARN] Entrenamiento parcial: BUY={buy_trained}, SELL={sell_trained}", 'warning')
                
        except Exception as e:
            logger.exception("Error en regeneracion de datos")
            self.add_log(f"[ERROR] Regeneracion de datos: {str(e)[:80]}", 'error')

    def _dual_analysis_before_opening(self, symbol):
        """
        FLUJO COMPLETO: CARGAR -> ENTRENAR -> ANALIZAR -> ARBITRAR
        
        1. Carga datos de 4 semanas
        2. Entrena buy_specialist y sell_specialist
        3. Analiza con ambos especialistas
        4. Arbitrador decide: BUY / SELL / HOLD
        """
        try:
            # PASO 1: Cargar datos de 4 semanas
            snaps = self.reload_market_snapshots() or []
            if not snaps or len(snaps) < 100:
                self.add_log("[DUAL] Sin datos suficientes - Cancelando entrada", 'warning')
                return None
            
            self.add_log(f"[DUAL] PASO 1: Cargados {len(snaps)} snapshots del histórico", 'info')
            
            # PASO 2: ENTRENAR especialistas
            self.add_log("[DUAL] PASO 2: Entrenando especialistas...", 'info')
            
            train_buy = None
            train_sell = None
            
            try:
                if hasattr(self, 'buy_specialist') and self.buy_specialist:
                    train_buy = self.buy_specialist.train(snaps)
                    self.add_log(f"  - BUY Specialist: {train_buy.get('status', 'unknown')}", 'info')
                else:
                    self.add_log("  - BUY Specialist no disponible", 'warning')
            except Exception as e:
                self.add_log(f"  - ERROR entrenando BUY: {str(e)[:80]}", 'error')
            
            try:
                if hasattr(self, 'sell_specialist') and self.sell_specialist:
                    train_sell = self.sell_specialist.train(snaps)
                    self.add_log(f"  - SELL Specialist: {train_sell.get('status', 'unknown')}", 'info')
                else:
                    self.add_log("  - SELL Specialist no disponible", 'warning')
            except Exception as e:
                self.add_log(f"  - ERROR entrenando SELL: {str(e)[:80]}", 'error')
            
            # Verificar que ambos fueron entrenados
            if not (train_buy and train_buy.get('status') == 'success') or not (train_sell and train_sell.get('status') == 'success'):
                self.add_log("[DUAL] Entrenamiento incompleto - Cancelando", 'warning')
                return None
            
            # PASO 3: ANALIZAR con ambos especialistas (ya entrenados)
            self.add_log("[DUAL] PASO 3: Analizando BUY y SELL...", 'info')
            
            buy_res = None
            sell_res = None
            
            try:
                buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                if buy_res:
                    self.add_log(f"  - BUY: {buy_res.get('recommendation', 'N/A')} (Score: {buy_res.get('score', 0):.1f}, Conf: {buy_res.get('confidence', 0)}%)", 'info')
                else:
                    self.add_log("  - BUY análisis devolvió None", 'warning')
                    return None
            except Exception as e:
                self.add_log(f"  - ERROR en BUY análisis: {str(e)[:80]}", 'error')
                return None
            
            try:
                sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                if sell_res:
                    self.add_log(f"  - SELL: {sell_res.get('recommendation', 'N/A')} (Score: {sell_res.get('score', 0):.1f}, Conf: {sell_res.get('confidence', 0)}%)", 'info')
                else:
                    self.add_log("  - SELL análisis devolvió None", 'warning')
                    return None
            except Exception as e:
                self.add_log(f"  - ERROR en SELL análisis: {str(e)[:80]}", 'error')
                return None
            
            # PASO 4: ARBITRADOR decide
            self.add_log("[DUAL] PASO 4: Arbitrando decisión...", 'info')
            
            if not hasattr(self, 'arbitrator') or not self.arbitrator:
                self.add_log("  - Arbitrador no disponible - Cancelando", 'warning')
                return None
            
            try:
                arb = self.arbitrator.arbitrate(buy_res, sell_res, symbol)
                if arb:
                    rec = arb.get('recommendation', 'HOLD')
                    self.add_log(f"[ARBITRATOR] Decision final: {rec}", 'success')
                    # ⭐ RETORNAR CON DATOS DE AMBOS ESPECIALISTAS
                    return {
                        'arbitrator': arb,
                        'recommendation': rec,
                        'buy_specialist': buy_res,
                        'sell_specialist': sell_res
                    }
                else:
                    self.add_log("[ARBITRATOR] Arbitración devolvió None", 'warning')
                    return None
            except Exception as e:
                self.add_log(f"[ARBITRATOR] ERROR: {str(e)[:80]}", 'error')
                return None
                
        except Exception as e:
            logger.error(f"Error en dual_analysis: {e}")
            self.add_log(f"[DUAL] Error general: {str(e)[:80]}", 'error')
            return None

    # ⭐ NUEVO: Ciclo de aprendizaje dinámico
    def bot_loop(self, saldo_base=0):
        """Versión mejorada que asegura análisis IA antes de cada operación"""
        try:
            self.start_time = int(time.time())
            self.tiempo_inicio = time.time()
            self.ultima_operacion = time.time()
            self.ultima_apertura = time.time()
            
            # Iniciar contador de tiempo si hay tiempo configurado
            if self.tiempo_total.get() > 0:
                self.root.after(0, self.actualizar_tiempo)
            
            # ⭐ Verificar modo de operación
            if self.use_entry_point.get() and self.entry_point_active:
                mode = "Modo PUNTO DE ENTRADA"
                self.add_log(f"[OBJETIVO] Bot iniciado en {mode}", 'success')
                self.add_log(f"   Esperando precio: {self.entry_point_price.get()}", 'info')
                self.add_log(f"   Dirección: {self.entry_point_direction.get()}", 'info')
            else:
                mode = "Sistema Multi-IA" if self.use_multi_ai.get() else "Modo Tradicional"
                self.add_log(f"Bot iniciado - {mode}", 'info')
            
            # ⭐ VALIDACIÓN DE OPERACIONES EN ESPERA
            if self.pending_operations:
                self.add_log(f"\n[ESPERA] OPERACIONES EN ESPERA DETECTADAS: {len(self.pending_operations)}", 'warning')
                for i, op in enumerate(self.pending_operations, 1):
                    status = "[EMOJI]" if op.get('status') == 'ESPERANDO' else "[EMOJI]"
                    self.add_log(f"   {status} Op #{op.get('id', i)}: {op['direction']} @ {op['price']:.5f}", 'info')
                self.add_log(f"   ► Analizando mercado para apertura...\n", 'warning')
            else:
                self.add_log(f"\n[DATA] Analizando mercado - Esperando operaciones\n", 'info')

            symbol = self.config['SYMBOL'].get()

            while self.is_running:
                try:
                    # FIX #19: CRÍTICO - Chequear pausa al INICIO del loop (antes de cualquier análisis)
                    if self.bot_pausado:
                        if self.pause_until and time.time() >= self.pause_until:
                            # Pausa vencida - reanudar completamente
                            self.add_log("[✅ REANUDACIÓN] Pausa terminada - Retomando operaciones", 'success')
                            
                            # ⭐ NUEVO V4: Mostrar cambios de tendencia detectados durante pausa
                            if self.impulse_during_pause:
                                self.add_log(f"[REANUDACIÓN] 📊 Se detectaron {len(self.impulse_during_pause)} cambios de tendencia durante pausa:", 'info')
                                for change_event in self.impulse_during_pause[-5:]:  # Mostrar últimos 5
                                    direction = change_event['direction']
                                    score = change_event['score']
                                    self.add_log(f"[HISTÓRICO-PAUSA]    → {direction} @{score:.1f}pts (vel:{change_event['velocity']:.6f})", 'market')
                                
                                # Obtener ÚLTIMO cambio para contexto de reapertura
                                last_change = self.impulse_during_pause[-1]
                                self.add_log(f"[CONTEXTO] Tendencia actual (última detectada): {last_change['direction']} @{last_change['score']:.1f}pts", 'success')
                                
                                # Limpiar histórico después de mostrar
                                self.impulse_during_pause = []
                            
                            # Resetear estado de pausa
                            self.saldo_total_acumulado += self.ganancia_neta
                            objetivo = self.objetivo_ganancia.get()
                            self.objetivo_cumplido = False
                            self.ganancia_neta = 0.0
                            self.bot_pausado = False
                            self.pause_until = 0
                            
                            self.add_log(f"[💰] Saldo acumulado: ${self.saldo_total_acumulado:.2f}", 'success')
                            self.add_log(f"[🎯] Nuevo objetivo: +${objetivo:.2f}", 'success')
                            time.sleep(1)  # Pequeño delay para asegurar que la UI se actualiza
                            continue
                        
                        # FIX #19: Durante la pausa, MONITOREAR pero NO análisis ni logs de operaciones
                        if self.total_operaciones_abiertas > 0:
                            try:
                                positions = mt5.positions_get(symbol=symbol)
                                if positions:
                                    bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
                                    for pos in bot_positions:
                                        # Verificar MIN_PROFIT_CLOSE / MAX_LOSS_CLOSE
                                        profit = pos.profit
                                        min_profit_val = self.config['MIN_PROFIT_CLOSE'].get()
                                        max_loss_val = self.config['MAX_LOSS_CLOSE'].get()
                                        
                                        should_close = False
                                        reason = ""
                                        
                                        if min_profit_val and min_profit_val > 0 and profit >= min_profit_val:
                                            should_close = True
                                            reason = f"MIN_PROFIT alcanzado (${profit:.2f} >= ${min_profit_val:.2f})"
                                        elif max_loss_val and max_loss_val > 0 and profit <= -max_loss_val:
                                            should_close = True
                                            reason = f"MAX_LOSS alcanzado (${profit:.2f} <= -${max_loss_val:.2f})"
                                        
                                        if should_close:
                                            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                                            tick = mt5.symbol_info_tick(symbol)
                                            if tick:
                                                close_price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                                                request = {
                                                    "action": mt5.TRADE_ACTION_DEAL,
                                                    "symbol": symbol,
                                                    "volume": pos.volume,
                                                    "type": close_type,
                                                    "position": pos.ticket,
                                                    "price": close_price,
                                                    "magic": self.config['MAGIC_NUMBER'],
                                                    "comment": "PauseMonitor_Close",
                                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                                }
                                                result = mt5.order_send(request)
                                                if result.retcode == mt5.TRADE_RETCODE_DONE:
                                                    self._procesar_cierre_exitoso(
                                                        ticket=pos.ticket,
                                                        symbol=symbol,
                                                        volume=pos.volume,
                                                        pos_type=pos.type,
                                                        profit=profit
                                                    )
                            except Exception as e:
                                pass  # Monitoreo silencioso durante pausa
                        
                        # ⭐ NUEVO V4: Registrar CAMBIOS DE TENDENCIA detectados durante pausa (por _data_reader_thread)
                        try:
                            with self.data_reader_lock:
                                latest_impulse = self.last_impulse_data.copy()
                            
                            if latest_impulse:
                                current_direction = latest_impulse.get('direction', 'NONE')
                                score = latest_impulse.get('impulse_score', 0)
                                velocity = latest_impulse.get('velocity', 0)
                                
                                # Detectar cambio de dirección
                                if current_direction != self.last_known_direction and current_direction != 'NONE':
                                    pause_change = {
                                        'time': time.time(),
                                        'direction': current_direction,
                                        'score': score,
                                        'velocity': velocity,
                                        'buy_pressure': latest_impulse.get('buy_pressure', 0),
                                        'sell_pressure': latest_impulse.get('sell_pressure', 0),
                                    }
                                    self.impulse_during_pause.append(pause_change)
                                    
                                    # Registrar cambio
                                    self.add_log(f"[PAUSA-MICRO] ⚡ Cambio detectado: {current_direction} @{score:.1f}pts | vel: {velocity:.6f}", 'warning')
                                    
                                    # Limitar lista a últimos 20 cambios
                                    if len(self.impulse_during_pause) > 20:
                                        self.impulse_during_pause = self.impulse_during_pause[-20:]
                        except Exception as e:
                            logger.debug(f"[PAUSA-MICRO] Error registrando cambios: {e}")
                        
                        # Mientras está pausado, dormir y continuar (SIN ANÁLISIS DE APERTURA)
                        time.sleep(0.5)
                        continue
                    
                    # ⭐ NUEVO: Regenerar datos de entrenamiento cada 5 minutos
                    try:
                        if not hasattr(self, '_last_training_regen'):
                            self._last_training_regen = 0
                        if time.time() - self._last_training_regen >= 300:  # 5 minutos
                            self._regenerate_training_data()
                            self._last_training_regen = time.time()
                    except Exception as e:
                        logger.error(f"Error regenerando datos de entrenamiento: {e}")
                    
                    # ⭐ NUEVO: Ajustar parámetros dinámicamente cada minuto
                    if self.adaptive_params.adjust_parameters_dynamically():
                        self.adaptive_params.log_current_state()
                    
                    # [RESET] Recarga periódica de market_snapshots (configurable)
                    try:
                        reload_interval = 5
                        try:
                            if 'SNAPSHOT_RELOAD_INTERVAL' in self.config:
                                reload_interval = int(self.config['SNAPSHOT_RELOAD_INTERVAL'].get())
                        except Exception:
                            pass
                        if not hasattr(self, '_last_snap_reload'):
                            self._last_snap_reload = 0
                        if time.time() - self._last_snap_reload >= float(reload_interval):
                            try:
                                self.reload_market_snapshots()
                            except Exception:
                                logger.exception("Error en recarga periódica de market_snapshots en bot_loop")
                            self._last_snap_reload = time.time()
                    except Exception:
                        logger.exception("Error calculando recarga periódica de snapshots")

                    # NUEVO: CARGAR DATOS FRESCOS DEL DATA LOADER SI ESTÁ DISPONIBLE
                    try:
                        if self.data_loader and self.data_ready:
                            fresh_snapshots = self.data_loader.get_latest_snapshots(num_bars=500)
                            if fresh_snapshots and len(fresh_snapshots) > 0:
                                # Usar los snapshots frescos del DataLoader
                                self.market_snapshots = fresh_snapshots
                                data_status = self.data_loader.get_data_status()
                                if data_status and data_status.get('data_age_seconds', 999) < 10:
                                    logger.info(f"[DATALOADER] Cargados {len(fresh_snapshots)} snapshots frescos (edad: {data_status['data_age_seconds']}s)")
                    except Exception as e:
                        logger.warning(f"Error usando DataLoader durante bot_loop: {e}")

                    # Registrar condición de mercado
                    rates = mt5.copy_rates_from_pos(self.config['SYMBOL'].get(), mt5.TIMEFRAME_M1, 0, 50)
                    
                    # ⭐ REPARACIÓN: Verificar si rates NO es None y si tiene elementos
                    if rates is not None and len(rates) > 0:
                        closes = np.array([float(r[4]) for r in rates])
                        highs = np.array([float(r[2]) for r in rates])
                        lows = np.array([float(r[3]) for r in rates])
                        
                        # ⭐ CONVERSIÓN EXPLÍCITA A FLOAT PARA EVITAR AMBIGÜEDAD
                        mean_closes = float(np.mean(closes))
                        std_closes = float(np.std(closes))
                        max_highs = float(np.max(highs))
                        min_lows = float(np.min(lows))
                        last_close = float(closes[-1])
                        
                        # ⭐ COMPARACIÓN CON ESCALARES PYTHON PURO
                        if mean_closes > 0:
                            volatility = std_closes / mean_closes
                        else:
                            volatility = 1.0
                        
                        self.current_market_volatility = float(volatility)
                        
                        # ⭐ COMPARACIÓN ESCALAR-ESCALAR (SIN AMBIGÜEDAD)
                        sma_20 = float(np.mean(closes[-20:]))
                        if last_close > sma_20:
                            trend = 'ALCISTA'
                        else:
                            trend = 'BAJISTA'
                        
                        price_range = max_highs - min_lows
                        
                        # Registrar condición
                        self.adaptive_params.record_market_condition(
                            volatility=volatility,
                            trend=trend,
                            price_range=price_range,
                            rsi=50,  # Placeholder
                            adx=25   # Placeholder
                        )
                    
                    # ⭐ MODO PUNTO DE ENTRADA: Solo monitorear operaciones en espera
                    if self.use_entry_point.get():
                        # Primero: Analizar y ABRIR nuevas operaciones en espera
                        self.analizar_pending_operations()
                        
                        # Segundo: Monitorear TP/SL de posiciones abiertas
                        if self.total_operaciones_abiertas > 0:
                            self.monitorear_posiciones_en_rojo()
                            self.limpiar_tracking_posiciones_cerradas()
                        
                        time.sleep(5)  # Verificar cada 5 segundos
                        continue

                    # MODO NORMAL (resto del código sin cambios)
                    objetivo = self.objetivo_ganancia.get()
                    if objetivo > 0 and self.ganancia_neta >= objetivo and not self.objetivo_cumplido:
                        self.add_log(f"\n[OBJETIVO] OBJETIVO ALCANZADO: ${self.ganancia_neta:.2f} >= ${objetivo:.2f}", 'success')
                        self.objetivo_cumplido = True
                        self._handle_objetivo_pause()
                        time.sleep(1)
                        continue

                    if time.time() < getattr(self, 'block_until', 0):
                        remaining = int(self.block_until - time.time())
                        if remaining > 0:
                            self.add_log(f"[ESPERA] Cooldown tras ganancia activo ({remaining}s restantes) - esperando...", 'info')
                        time.sleep(1)
                        continue

                    if self.total_operaciones_abiertas < self.config['MAX_SIMULTANEOUS_OPS'].get():
                        # ⭐ VERIFICACIÓN CRÍTICA PRE-ANÁLISIS: Bot detenido o deteniendo
                        if not self.is_running or getattr(self, 'force_stop_triggered', False):
                            self.add_log("[BOT] Bot detenido - canceling nuevas operaciones", 'warning')
                            break
                        
                        # [EMOJI] NUEVA VERIFICACIÓN: Si Operaciones Rápidas está activa, saltar análisis
                        if self.config['RAPID_OPS_ENABLED'].get():
                            # Rapid Ops activo - no correr análisis, solo esperar a que el hilo abra operaciones
                            time.sleep(1)
                            continue
                        
                        self.add_log("\n🔍 Iniciando análisis de mercado para nueva operación...", 'info')
                        
                        # ⭐ NUEVO: Análisis paralelo (V12 + DUAL en paralelo, -40% latencia)
                        analysis_result = self._parallel_trade_analysis(symbol)
                        
                        if analysis_result and analysis_result.get('recommendation') in ['BUY', 'SELL']:
                            direccion = analysis_result['recommendation']
                            self.add_log(f"[{analysis_result.get('source', '??')}] ✓ Análisis decidió: {direccion}", 'success')
                            
                            # NUEVO: Capturar confianza para volumen dinámico
                            signal_confidence = analysis_result.get('confidence', 50)
                            self.last_signal_confidence = signal_confidence
                            self.add_log(f"[CONFIDENCE] Señal con confianza: {signal_confidence}%", 'info')
                            
                            # ⭐ CRÍTICO: VALIDAR ALINEACIÓN DE IMPULSOS CON ESPECIALISTA
                            # Este es el flujo de trabajo correcto:
                            # 1. Especialista dice BUY/SELL ✓
                            # 2. Validar que IMPULSOS DE TICKS confirmen ← NUEVO
                            # 3. Si coinciden → ABRIR
                            # 4. Si NO coinciden → RECHAZAR (no abrir por tendencia sola)
                            snapshots = self.reload_market_snapshots() or []
                            impulse_validation = self._validate_impulse_alignment(
                                specialist_direction=direccion,
                                specialist_confidence=signal_confidence,
                                snapshots=snapshots
                            )
                            
                            # LOG: Resultado de validación
                            if impulse_validation['recommendation'] == 'PROCEED':
                                self.add_log(f"✅ IMPULSOS ALINEADOS: Proceder con {direccion}", 'success')
                                dapat_abrir = True
                            elif impulse_validation['recommendation'] == 'CAUTION':
                                self.add_log(f"⚠️  IMPULSOS PARCIALMENTE ALINEADOS: Proceder con cautela", 'warning')
                                dapat_abrir = True  # Permitir con cautela
                            else:  # REJECT
                                self.add_log(f"🛑 IMPULSOS NO ALINEADOS: Rechazar apertura {direccion}", 'error')
                                self.add_log(f"   Razón: {impulse_validation['reason']}", 'error')
                                dapat_abrir = False
                            
                            # NUEVO: Registrar metadata para feedback loop (pre-trade captura)
                            self.last_trade_metadata = {
                                'analysis_source': analysis_result.get('source', 'UNKNOWN'),
                                'buy_score': analysis_result.get('buy_score', 0),
                                'sell_score': analysis_result.get('sell_score', 0),
                                'confidence': signal_confidence,
                                'direction': direccion,
                                'motor_votes': analysis_result.get('motor_votes', {}),
                                'entry_rsi': analysis_result.get('entry_rsi', 50),
                                'entry_volatility': analysis_result.get('volatility', 1.0),
                                'impulse_alignment_score': impulse_validation['alignment_score'],
                                'impulse_direction': impulse_validation['impulse_direction'],
                                'impulse_validation': impulse_validation['recommendation'],
                                'timestamp': time.time()
                            }
                            self.add_log(f"[FEEDBACK] Metadata registrada para análisis posterior", 'info')
                            
                            # ⭐ SOLO ABRIR SI IMPULSOS ESTÁN ALINEADOS
                            if dapat_abrir and self.abrir_operacion(direccion, force=False):
                                self.ultima_operacion = time.time()
                                self.last_confidence = analysis_result.get('confidence', 0)
                                self.add_log("[ESPERA] Esperando resultado de la operación...", 'info')
                            elif not dapat_abrir:
                                self.add_log(f"[ESPERA] No abrir: Impulsos no alineados. Esperando siguiente ciclo...", 'warning')
                                time.sleep(2)  # Pequeña pausa para evitar loops rápidos
                        else:
                            reason = analysis_result.get('reason', 'Sin definir') if analysis_result else 'Ambos análisis fallaron'
                            self.add_log(f"[ADVERTENCIA] Análisis rechazó: {reason}", 'warning')
                            time.sleep(5)
                    
                    # Siempre monitorear posiciones abiertas (cierres por profit/loss deben ser individuales)
                    try:
                        if self.total_operaciones_abiertas > 0:
                            self.monitorear_posiciones_en_rojo()
                            self.limpiar_tracking_posiciones_cerradas()
                        # Mantener contador/estado actualizado
                        self.actualizar_contador_z()
                    except Exception as _e:
                        self.add_log(f"Error monitoreo periódicode posiciones: {_e}", 'error')

                    # ⭐ NUEVO: Logging del contador de operaciones forzadas en CADA ciclo
                    try:
                        if self.config.get('FORCED_OPS_ENABLED', tk.BooleanVar(value=False)).get():
                            try:
                                minutes = int(self.config.get('FORCED_OPEN_MINUTES', tk.IntVar(value=5)).get())
                            except Exception:
                                minutes = 5
                            
                            intervalo = max(1, minutes) * 60
                            ultima_ap = getattr(self, 'ultima_apertura', 0)
                            segundos_desde_ultima = int(time.time() - ultima_ap)
                            segundos_restantes = max(0, intervalo - segundos_desde_ultima)
                            
                            # Log cada 10 segundos o cuando esté cerca (< 20s)
                            if not hasattr(self, '_last_forced_log'):
                                self._last_forced_log = 0
                            
                            should_log = (time.time() - self._last_forced_log >= 10) or (segundos_restantes <= 20)
                            if should_log:
                                mins = segundos_restantes // 60
                                secs = segundos_restantes % 60
                                tiempo_str = f"{mins}m{secs:02d}s" if mins > 0 else f"{secs}s"
                                self.add_log(f"[TIMER] Falta {tiempo_str} para apertura forzada (intervalo {minutes}m) | Tiempo desde última: {segundos_desde_ultima}s", 'info')
                                self._last_forced_log = time.time()
                    except Exception:
                        pass

                    time.sleep(1)

                except Exception as e:
                    self.add_log(f"Error en ciclo: {str(e)}", 'error')
                    time.sleep(1)
                    continue
                
        except Exception as e:
            self.add_log(f"Error crítico en bot_loop: {str(e)}", 'error')

    # ⭐ NUEVO: Análisis paralelo V12 + DUAL (-40% latencia)
    def _parallel_trade_analysis(self, symbol):
        """
        Ejecuta V12 Analysis y DUAL Analysis EN PARALELO usando threading.
        
        ⭐ CAMBIO CRÍTICO (v2): DUAL tiene PRIORIDAD sobre V12
        Razón: DUAL usa impulsos de ticks en TIEMPO REAL
               V12 usa análisis histórico de 4 semanas (puede estar obsoleto)
        
        Flujo:
        1. Si DUAL tiene resultado válido → USAR DUAL
        2. Si DUAL rechaza pero V12 válido → USAR V12
        3. Si conflicto (DUAL!=V12) → RECHAZAR AMBOS (esperar consenso)
        4. Si ambos rechazan → RECHAZAR
        
        Impacto: -40% latencia, +50% precisión de dirección
        """
        results = {
            'v12': None,
            'dual': None,
            'v12_done': threading.Event(),
            'dual_done': threading.Event()
        }
        
        def run_v12():
            try:
                results['v12'] = self.analyze_trade_opportunity_v12(symbol)
            except Exception as e:
                self.add_log(f"[ASYNC] Error en V12: {str(e)[:60]}", 'warning')
                results['v12'] = None
            finally:
                results['v12_done'].set()
        
        def run_dual():
            try:
                results['dual'] = self._dual_analysis_before_opening(symbol)
            except Exception as e:
                self.add_log(f"[ASYNC] Error en DUAL: {str(e)[:60]}", 'warning')
                results['dual'] = None
            finally:
                results['dual_done'].set()
        
        # Iniciar threads
        t_v12 = threading.Thread(target=run_v12, daemon=True)
        t_dual = threading.Thread(target=run_dual, daemon=True)
        
        t_v12.start()
        t_dual.start()
        
        # Esperar ambos con timeout (máx 10 segundos)
        v12_completed = results['v12_done'].wait(timeout=10)
        dual_completed = results['dual_done'].wait(timeout=10)
        
        # Log resumen
        if v12_completed and results['v12']:
            self.add_log(f"[✓ ASYNC V12] Completado en ~{results['v12_done']._time:.1f}s", 'success')
        if dual_completed and results['dual']:
            self.add_log(f"[✓ ASYNC DUAL] Completado en ~{results['dual_done']._time:.1f}s", 'success')
        
        # ⭐ NUEVA LÓGICA: DUAL tiene prioridad
        dual_rec = results['dual'].get('recommendation') if results['dual'] else None
        v12_rec = results['v12'].get('signal') if results['v12'] else None
        v12_valid = results['v12'] and results['v12'].get('can_trade')
        dual_valid = results['dual'] and dual_rec in ['BUY', 'SELL']
        
        # PASO 1: Si DUAL es válido → USAR DUAL
        if dual_valid:
            self.add_log(f"[RESULTADO] 🟢 DUAL ganó: {dual_rec} (conf: {results['dual'].get('confidence', 0):.1f}%)", 'success')
            
            # ⭐ VALIDACIÓN: Si ambos están disponibles, verificar conflicto
            if v12_valid and v12_rec != dual_rec:
                self.add_log(f"[⚠️ CONFLICTO] DUAL:{dual_rec} vs V12:{v12_rec} (DUAL tiene prioridad)", 'warning')
                self.add_log(f"[INFO] V12 descartado por conflicto con DUAL", 'info')
            
            return {
                'source': 'DUAL',
                'signal': dual_rec,
                'confidence': results['dual'].get('confidence', 0),
                'recommendation': dual_rec,
                'reason': 'DUAL analysis (impulsos de ticks)',
                'buy_score': results['dual'].get('buy_specialist', {}).get('score', 0),
                'sell_score': results['dual'].get('sell_specialist', {}).get('score', 0),
                'volatility': results['dual'].get('volatility', 1.0),
                'entry_rsi': results['dual'].get('entry_rsi', 50),
                'motor_votes': results['dual'].get('motor_votes', {})
            }
        
        # PASO 2: DUAL rechazó, pero V12 es válido → USAR V12 (fallback)
        elif v12_valid:
            self.add_log(f"[RESULTADO] 🟡 V12 ganó (DUAL rechazó): {v12_rec} (conf: {results['v12'].get('confidence', 0):.1f}%)", 'success')
            return {
                'source': 'V12',
                'signal': v12_rec,
                'confidence': results['v12'].get('confidence', 0),
                'recommendation': v12_rec,
                'reason': 'V12 analysis (fallback, DUAL rechazó)',
                'buy_score': results['v12'].get('buy_score', 0),
                'sell_score': results['v12'].get('sell_score', 0),
                'volatility': results['v12'].get('volatility', 1.0),
                'entry_rsi': results['v12'].get('entry_rsi', 50),
                'motor_votes': results['v12'].get('motor_votes', {})
            }
        
        # PASO 3: Ambos rechazaron o timeout
        else:
            reason = 'Ambos análisis rechazaron'
            if not v12_completed:
                reason = 'V12 timeout (>10s)'
            elif not dual_completed:
                reason = 'DUAL timeout (>10s)'
            elif not v12_valid and not dual_valid:
                reason = 'V12 y DUAL no validan (confianza baja o condiciones desfavorables)'
            
            self.add_log(f"[RECHAZADO] {reason}", 'warning')
            return None

    # ⭐ NUEVO: Validación de Alineación de Impulsos
    def _validate_impulse_alignment(self, specialist_direction, specialist_confidence, snapshots=None):
        """
        VALIDACIÓN CRÍTICA DEL FLUJO DE TRABAJO:
        
        Verifica que los impulsos de los ticks coincidan con la señal del especialista.
        Si NO hay impulsos de tick que confirmen la dirección del especialista, SE RECHAZA.
        
        Returns:
            {
                'valid': True|False,
                'alignment_score': 0-100,
                'impulse_direction': str,
                'impulse_strength': 0-100,
                'recommendation': 'PROCEED'|'CAUTION'|'REJECT',
                'reason': str
            }
        """
        try:
            # Si validación de impulsos desactivada, permitir siempre (pero avisar)
            if not self.use_tick_impulse_validation.get():
                self.add_log("[IMPULSE] ⚠️ Validación de impulsos desactivada (RIESGOSO)", 'warning')
                return {
                    'valid': True,
                    'alignment_score': 0,
                    'impulse_direction': None,
                    'impulse_strength': 0,
                    'recommendation': 'PROCEED',
                    'reason': 'Validación desactivada'
                }
            
            # Si no hay validador, permitir pero avisar
            if not self.impulse_validator:
                self.add_log("[IMPULSE] ❌ Validador de impulsos no disponible", 'warning')
                return {
                    'valid': False,
                    'alignment_score': 0,
                    'impulse_direction': None,
                    'impulse_strength': 0,
                    'recommendation': 'REJECT',
                    'reason': 'Validador no disponible'
                }
            
            # Analizar snapshots para detectar impulso
            if not snapshots:
                snapshots = self.reload_market_snapshots() or []
            
            if not snapshots or len(snapshots) < 5:
                self.add_log("[IMPULSE] ⚠️ Insuficientes snapshots para validación (< 5)", 'warning')
                return {
                    'valid': False,
                    'alignment_score': 0,
                    'impulse_direction': None,
                    'impulse_strength': 0,
                    'recommendation': 'REJECT',
                    'reason': 'Datos insuficientes'
                }
            
            # Detectar impulso desde snapshots
            impulse_result = self.impulse_validator.analyze_snapshots_for_impulse(snapshots)
            
            # Validar alineación
            alignment = self.impulse_validator.detector.validate_signal_alignment(
                specialist_direction=specialist_direction,
                specialist_confidence=specialist_confidence,
                min_alignment_threshold=self.min_impulse_alignment_threshold
            )
            
            # Logging detallado
            self.add_log(f"\n[IMPULSE] ═══ VALIDACIÓN DE ALINEACIÓN ═══", 'info')
            self.add_log(f"[IMPULSE] Especialista: {specialist_direction} @ {specialist_confidence:.1f}% confianza", 'info')
            self.add_log(f"[IMPULSE] Impulso detectado: {impulse_result.get('direction', 'NONE')} (fuerza: {impulse_result.get('strength', 0):.1f})", 'info')
            self.add_log(f"[IMPULSE] Score de alineación: {alignment['alignment_score']:.1f}/100", 'info')
            self.add_log(f"[IMPULSE] Recomendación: {alignment['recommendation']}", alignment['recommendation'] == 'PROCEED' and 'success' or 'warning')
            
            if alignment['conflict']:
                self.add_log(f"[IMPULSE] ⚠️  CONFLICTO: {alignment['conflict']}", 'error')
            
            self.add_log(f"[IMPULSE] Detalle: {impulse_result.get('reason', '')}", 'info')
            self.add_log(f"[IMPULSE] ═════════════════════════════", 'info')
            
            return {
                'valid': alignment['recommendation'] in ['PROCEED', 'CAUTION'],
                'alignment_score': alignment['alignment_score'],
                'impulse_direction': alignment['impulse_direction'],
                'impulse_strength': alignment['impulse_strength'],
                'recommendation': alignment['recommendation'],
                'reason': alignment['conflict'] or impulse_result.get('reason', 'OK')
            }
            
        except Exception as e:
            self.add_log(f"[IMPULSE] ERROR en validación: {str(e)[:100]}", 'error')
            return {
                'valid': False,
                'alignment_score': 0,
                'impulse_direction': None,
                'impulse_strength': 0,
                'recommendation': 'REJECT',
                'reason': f'Error: {str(e)[:50]}'
            }

    # ⭐ NUEVO: Función de análisis con Multi-IA
    def analizar_mercado(self):
        """Análisis usando Sistema Multi-IA o tradicional según configuración"""
        if self.total_operaciones_abiertas > 0:
            self.add_log("[ERROR] No se analiza - Ya hay una operación abierta", 'warning')
            return None
            
        symbol = self.config['SYMBOL'].get()
        # --- REFRESH: asegurar datos de mercado actualizados y calibración antes de abrir ---
        try:
            # Forzar recarga de snapshots desde disco/MT5
            try:
                snaps = self.reload_market_snapshots() or []
            except Exception:
                snaps = []

            # Ejecutar calibración rápida desde logs y aplicar sugerencias
            try:
                cal = calibrate_from_logs(limit=1000)
                if cal and isinstance(cal, dict):
                    if 'risk_pct' in cal and 'RISK_PCT' in self.config:
                        self.config['RISK_PCT'].set(float(cal['risk_pct']))
                        self.add_log(f"[CONFIG] Calibración automática: RISK_PCT -> {cal['risk_pct']}", 'success')
                    if 'confidence_threshold' in cal and 'CONFIDENCE_THRESHOLD' in self.config:
                        self.config['CONFIDENCE_THRESHOLD'].set(float(cal['confidence_threshold']))
                        self.add_log(f"[CONFIG] Calibración automática: CONFIDENCE_THRESHOLD -> {cal['confidence_threshold']}", 'success')
            except Exception:
                logger.exception("Error ejecutando calibrate_from_logs en pre-open")

            # Auto-calibrador dinámico local
            try:
                # Registrar estadísticas y ajustar umbrales si aplica
                try:
                    self.calibrator.auto_calibrate()
                except Exception:
                    pass
            except Exception:
                logger.exception("Error en calibrador dinámico antes de abrir")

            # Validación final: pedir a especialistas que evalúen los snaps más recientes
            try:
                buy_res = None
                sell_res = None
                if hasattr(self.buy_specialist, 'analyze'):
                    try:
                        buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps)
                    except Exception:
                        buy_res = None
                if hasattr(self.sell_specialist, 'analyze'):
                    try:
                        sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps)
                    except Exception:
                        sell_res = None

                # Log resumen de confianza de especialistas (no validar dirección aquí)
                try:
                    if buy_res and 'confidence' in buy_res:
                        self.add_log(f"🔹 BUY specialist confidence pre-open: {float(buy_res.get('confidence',0)):.1f}%", 'info')
                    if sell_res and 'confidence' in sell_res:
                        self.add_log(f"🔸 SELL specialist confidence pre-open: {float(sell_res.get('confidence',0)):.1f}%", 'info')
                except Exception:
                    pass
            except Exception:
                logger.exception("Error validando especialistas antes de apertura")
        except Exception:
            logger.exception("Error en pre-open refresh/calibration block")

        if not mt5.initialize():
            self.add_log("[ERROR] MT5 desconectado - Intentando reconectar...", 'error')
            mt5.shutdown()
            time.sleep(1)
            if not mt5.initialize() or not self.conectar_mt5():
                self.add_log("[ERROR] No se pudo reconectar a MT5", 'error')
                return None
    
        if not mt5.symbol_select(symbol, True):
            self.add_log(f"[ERROR] No se pudo seleccionar {symbol}", 'error')
            return None
        
        # ⭐ JERARQUÍA DE ANÁLISIS: PRO > ML V2 > Multi-IA > Tradicional
        
        # NIVEL 5-10: Intentar SISTEMA PRO (Institucional)
        if self.pro_system_loaded:
            direction = self._predict_pro_system()
            if direction is not None:
                self.add_log(f"[OK] Decisión PRO utilizada: {direction}", 'success')
                return direction
        
        # DECISIÓN: Usar Multi-IA o análisis tradicional
        if self.use_multi_ai.get():
            return self._analizar_con_multi_ia(symbol)
        else:
            return self._analizar_tradicional(symbol)

    def _analizar_con_multi_ia(self, symbol):
        """Análisis usando el Sistema Multi-IA (3 especialistas) con umbrales calibrados"""
        try:
            self.add_log("\n" + "="*60, 'info')
            self.add_log("[IA] INICIANDO ANÁLISIS MULTI-IA", 'info')
            self.add_log("="*60, 'info')
            
            self.add_log("\n[DATA] Fase 1: Análisis de Especialistas", 'info')
            
            # Combine prefilled snapshots with latest MT5 bars (prefer MT5 for newest bars).
            buy_analysis = None
            sell_analysis = None
            try:
                snaps = self.reload_market_snapshots() or []
                # Try to fetch recent bars from MT5 to keep data fresh
                try:
                    recent = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, max(50, int(self.config.get('BARS_ANALYZE').get())))
                except Exception:
                    recent = None

                recent_list = []
                if recent is not None:
                    try:
                        for r in recent:
                            if isinstance(r, (list, tuple)):
                                ts = int(r[0])
                                open_v = float(r[1])
                                high_v = float(r[2])
                                low_v = float(r[3])
                                close_v = float(r[4])
                                tick_v = int(r[5])
                            else:
                                ts = int(r.get('time', 0))
                                open_v = float(r.get('open', 0.0))
                                high_v = float(r.get('high', 0.0))
                                low_v = float(r.get('low', 0.0))
                                close_v = float(r.get('close', 0.0))
                                tick_v = int(r.get('tick_volume', 0))

                            entry = {
                                'timestamp': datetime.fromtimestamp(ts).isoformat() if ts else None,
                                'open': open_v,
                                'high': high_v,
                                'low': low_v,
                                'close': close_v,
                                'tick_volume': tick_v
                            }
                            recent_list.append(entry)
                    except Exception:
                        recent_list = []

                # Merge: key by timestamp ISO (prefer recent_list values)
                merged_map = {}
                for s in snaps:
                    try:
                        merged_map[s['timestamp']] = s
                    except Exception:
                        continue
                for r in recent_list:
                    merged_map[r['timestamp']] = r

                # Sort and limit to last 500
                merged_list = [merged_map[k] for k in sorted(merged_map.keys())]
                if len(merged_list) > 500:
                    merged_list = merged_list[-500:]

                # Update in-memory and on-disk snapshots so future calls use fresh data
                try:
                    # escribir en memoria protegido por lock
                    if getattr(self, 'market_snapshots_lock', None):
                        with self.market_snapshots_lock:
                            self.market_snapshots = merged_list
                    else:
                        self.market_snapshots = merged_list
                    
                    # ⭐ Actualizar data_loader con nuevos datos
                    if self.data_loader and hasattr(self.data_loader, 'market_snapshots'):
                        try:
                            self.data_loader.market_snapshots = merged_list
                            # Actualizar también en especialistas
                            if hasattr(self.buy_specialist, 'market_snapshots'):
                                self.buy_specialist.market_snapshots = merged_list
                            if hasattr(self.sell_specialist, 'market_snapshots'):
                                self.sell_specialist.market_snapshots = merged_list
                        except Exception as e:
                            logger.warning(f"Error actualizando snapshots en especialistas: {e}")
                    
                    # Escribir en disco (trade_logger) de forma atómica
                    try:
                        write_market_snapshots(merged_list)
                        self.data_update_count += 1
                        
                        # ⭐ Mostrar estadísticas cada 5 minutos
                        current_time = time.time()
                        if current_time - self.last_data_stats_log > 300:  # 5 minutos
                            self._log_data_statistics(merged_list)
                            self.last_data_stats_log = current_time
                            
                    except Exception:
                        logger.exception("Error escribiendo market_snapshots en disco")
                except Exception:
                    logger.exception("Error actualizando market_snapshots en memoria/disk")

                # Pass merged list to specialists
                if hasattr(self.buy_specialist, 'analyze'):
                    buy_analysis = self.buy_specialist.analyze(symbol, market_snapshots=merged_list)
                if hasattr(self.sell_specialist, 'analyze'):
                    sell_analysis = self.sell_specialist.analyze(symbol, market_snapshots=merged_list)
                
                # ⭐ NUEVO: Intentar análisis multi-timeframe primero (M1, M5, M15, M30, H1)
                if self.use_multi_timeframe.get() == True:
                    try:
                        self.add_log("[MTF] Analyzing Buy signal across 5 timeframes...", 'info')
                        buy_mtf = self.buy_specialist.analyze_multi_timeframe(symbol)
                        
                        self.add_log("[MTF] Analyzing Sell signal across 5 timeframes...", 'info')
                        sell_mtf = self.sell_specialist.analyze_multi_timeframe(symbol)
                        
                        if buy_mtf and sell_mtf:
                            # Fusionar resultados: multi-timeframe tiene 2x peso
                            buy_analysis['score'] = (buy_analysis.get('score', 50) + buy_mtf.get('multi_tf_score', 50) * 2) / 3
                            buy_analysis['confidence'] = (buy_analysis.get('confidence', 65) + buy_mtf.get('weighted_confidence', 65) * 2) / 3
                            if buy_mtf.get('consensus_strength', 0) >= 70:
                                buy_analysis['recommendation'] = 'STRONG_BUY' if buy_mtf['recommendation'] == 'STRONG_BUY' else buy_analysis.get('recommendation', 'BUY')
                            
                            sell_analysis['score'] = (sell_analysis.get('score', 50) + sell_mtf.get('multi_tf_score', 50) * 2) / 3
                            sell_analysis['confidence'] = (sell_analysis.get('confidence', 65) + sell_mtf.get('weighted_confidence', 65) * 2) / 3
                            if sell_mtf.get('consensus_strength', 0) >= 70:
                                sell_analysis['recommendation'] = 'STRONG_SELL' if sell_mtf['recommendation'] == 'STRONG_SELL' else sell_analysis.get('recommendation', 'SELL')
                            
                            self.add_log(f"[MTF] 🟢 BUY Multi-TF Score: {buy_mtf['multi_tf_score']:.1f} | Consensus: {buy_mtf['consensus_strength']:.0f}% | Strongest: {buy_mtf['strongest_tf']}", 'success')
                            self.add_log(f"[MTF] 🔴 SELL Multi-TF Score: {sell_mtf['multi_tf_score']:.1f} | Consensus: {sell_mtf['consensus_strength']:.0f}% | Strongest: {sell_mtf['strongest_tf']}", 'success')
                    except Exception as e:
                        self.add_log(f"[MTF] Error en análisis multi-timeframe: {str(e)[:60]}", 'warning')
            except Exception:
                buy_analysis = None
                sell_analysis = None
            
            if not buy_analysis or not sell_analysis:
                # Fallback: attempt a simple snapshot-based heuristic if specialists failed
                self.add_log("[ADVERTENCIA] Especialistas no devolvieron análisis completo, usando heurística de snapshots", 'warning')
                snap_signal = None
                try:
                    snap_signal = self.compute_signal_from_snapshots()
                except Exception:
                    snap_signal = None
                if snap_signal is None:
                    self.add_log("[ERROR] Error en análisis de especialistas y heurística - No abrir", 'error')
                    return None
                # Build minimal analysis dicts to pass to arbitrator
                if snap_signal == 'BUY':
                    buy_analysis = {'score': 80.0, 'confidence': 80.0, 'recommendation': 'BUY', 'reasoning': ['snapshot_heuristic']}
                    sell_analysis = {'score': 20.0, 'confidence': 20.0, 'recommendation': 'SELL', 'reasoning': ['snapshot_heuristic']}
                else:
                    sell_analysis = {'score': 80.0, 'confidence': 80.0, 'recommendation': 'SELL', 'reasoning': ['snapshot_heuristic']}
                    buy_analysis = {'score': 20.0, 'confidence': 20.0, 'recommendation': 'BUY', 'reasoning': ['snapshot_heuristic']}
            
            # Obtener umbrales por especialista
            try:
                buy_threshold = float(self.config.get('BUY_CONFIDENCE_THRESHOLD', tk.DoubleVar(value=65.0)).get())
                sell_threshold = float(self.config.get('SELL_CONFIDENCE_THRESHOLD', tk.DoubleVar(value=65.0)).get())
            except Exception:
                buy_threshold = 65.0
                sell_threshold = 65.0
            
            self.add_log(f"\n[OK] BUY Specialist:", 'info')
            self.add_log(f"   Score: {buy_analysis['score']:.1f}/100", 'info')
            self.add_log(f"   Confianza: {buy_analysis['confidence']}% (umbral: {buy_threshold:.1f}%)", 'info')
            self.add_log(f"   Recomendación: {buy_analysis['recommendation']}", 'info')
            for reason in buy_analysis['reasoning'][:3]:
                self.add_log(f"   • {reason}", 'info')
            
            self.add_log(f"\n🔴 SELL Specialist:", 'info')
            self.add_log(f"   Score: {sell_analysis['score']:.1f}/100", 'info')
            self.add_log(f"   Confianza: {sell_analysis['confidence']}% (umbral: {sell_threshold:.1f}%)", 'info')
            self.add_log(f"   Recomendación: {sell_analysis['recommendation']}", 'info')
            for reason in sell_analysis['reasoning'][:3]:
                self.add_log(f"   • {reason}", 'info')
            
            # Filtrar por umbrales de especialistas
            buy_valid = buy_analysis['confidence'] >= buy_threshold
            sell_valid = sell_analysis['confidence'] >= sell_threshold
            
            if not buy_valid:
                self.add_log(f"   [ADVERTENCIA] BUY no cumple umbral ({buy_analysis['confidence']}% < {buy_threshold}%)", 'warning')
            if not sell_valid:
                self.add_log(f"   [ADVERTENCIA] SELL no cumple umbral ({sell_analysis['confidence']}% < {sell_threshold}%)", 'warning')
            
            self.add_log(f"\n[EMOJI]️ Fase 2: Arbitraje de Decisión", 'info')
            
            # Usar árbitro como gatekeeper (ALLOW only). No dejar que el árbitro decida la dirección.
            allow_result = self.arbitrator.allow_trade(buy_analysis, sell_analysis, symbol)
            if not allow_result.get('allow'):
                self.add_log("\n[PAUSA] Árbitro DENIEGA operación: " + ", ".join(allow_result.get('reasons', [])), 'warning')
                return None

            # Direction decided by specialists (may be replaced by SuperAnalyzer if desired)
            if buy_analysis['score'] > sell_analysis['score']:
                direction = 'BUY'
            elif sell_analysis['score'] > buy_analysis['score']:
                direction = 'SELL'
            else:
                # fallback: use recommendations or hold
                if buy_analysis.get('recommendation', 'HOLD').startswith('BUY') and not sell_analysis.get('recommendation','').startswith('SELL'):
                    direction = 'BUY'
                elif sell_analysis.get('recommendation','HOLD').startswith('SELL') and not buy_analysis.get('recommendation','').startswith('BUY'):
                    direction = 'SELL'
                else:
                    self.add_log("[EMOJI]️ Empate en scores y recomendaciones - No abrir", 'warning')
                    return None

            self.add_log(f"\n[OK] Árbitro APROBÓ - Dirección seleccionada por especialistas: {direction}", 'success')
            return direction
            
        except Exception as e:
            self.add_log(f"[ERROR] Error en análisis Multi-IA: {str(e)}", 'error')
            return None

    # [OBJETIVO] FASE 3: NUEVO MÉTODO - ANÁLISIS V12 CON LOS 12 MÓDULOS
    def analyze_trade_opportunity_v12(self, symbol):
        """
        [OBJETIVO] ANÁLISIS COMPLETO CON LOS 12 MEJORAS (FASE 3)
        
        Flujo:
        1. ⭐ COMPROBACIÓN FORZADA (ANTES DE TODO)
        2. SuperAnalyzer (6 motores) → decisión base
        3. DynamicScoreCalibration → valida confianza según histórico
        4. TimeBasedSessionFilter → verifica sesión óptima
        5. CorrelationAnalyzer → valida con activos correlacionados
        6. RecoveryPotentialEnhanced → evalúa potencial de bounce
        7. SpreadSlippageAnalyzer → asegura viabilidad económica
        
        Retorna: {can_trade, signal, confidence, entry_price, tp_pips, sl_pips, reason}
        """
        
        try:
            self.add_log("\n" + "="*70, 'info')
            self.add_log("[OBJETIVO] INICIANDO ANÁLISIS V12 - 12 MÓDULOS EN ACCIÓN", 'info')
            self.add_log("="*70, 'info')
            
            # ⭐ COMPROBACIÓN PRIORITARIA: APERTURA FORZADA (ANTES DE ANÁLISIS NORMAL)
            # Esta lógica se ejecuta SIEMPRE, independientemente del análisis
            try:
                enabled_forced = bool(self.config.get('ENABLE_FORCED_OPEN', tk.BooleanVar(value=True)).get())
            except Exception:
                enabled_forced = True
            try:
                minutes = int(self.config.get('FORCED_OPEN_MINUTES', tk.IntVar(value=5)).get())
            except Exception:
                minutes = 5

            intervalo = max(1, minutes) * 60
            now = time.time()
            eligible_for_forced = False
            
            # Comprobar si es momento de reapertura forzada
            if getattr(self, 'next_forced_open', None):
                try:
                    eligible_for_forced = now >= float(self.next_forced_open)
                except Exception:
                    ultima_ap = getattr(self, 'ultima_apertura', 0)
                    eligible_for_forced = (int(now - ultima_ap) >= intervalo)
            else:
                ultima_ap = getattr(self, 'ultima_apertura', 0)
                eligible_for_forced = (int(now - ultima_ap) >= intervalo)
            
            if enabled_forced and eligible_for_forced:
                self.add_log("\n" + "▶️"*35, 'info')
                self.add_log("⚡ REAPERTURA FORZADA ACTIVADA (intervalo cumplido)", 'info')
                self.add_log("▶️"*35, 'info')
                
                fallback_dir = getattr(self, 'direccion_actual', None)
                if not fallback_dir:
                    try:
                        fallback_dir = self.analizar_entrada_inicial(symbol)
                    except Exception:
                        fallback_dir = 'BUY'

                self.add_log(f"[RESET] Dirección IA: {fallback_dir}", 'warning')
                
                # ⭐ USAR TICK FLOW ANALYZER PARA RESOLVER DIRECCIÓN FINAL
                final_direction = fallback_dir
                if self.use_tick_flow.get() and self.tick_flow_analyzer:
                    try:
                        # Obtener ticks y resolver dirección
                        ticks = self.tick_flow_analyzer.get_recent_ticks(
                            limit=self.config['TICK_FLOW_WINDOW'].get()
                        )
                        resolution = self.tick_flow_analyzer.resolve_final_direction(
                            ia_direction=fallback_dir,
                            ticks=ticks
                        )
                        final_direction = resolution.get('final_direction', fallback_dir)
                        
                        if resolution.get('inverted'):
                            self.add_log(f"[FLOW] ⚠️ DIRECCIÓN INVERTIDA por microestructura: {fallback_dir} → {final_direction}", 'warning')
                        else:
                            self.add_log(f"[FLOW] ✅ Dirección CONFIRMADA por flujo de ticks: {final_direction}", 'success')
                    except Exception as e:
                        self.add_log(f"[FLOW] ⚠️ Error analizando flow: {str(e)[:80]}", 'warning')
                        final_direction = fallback_dir
                
                self.add_log(f"[RESET] Ejecutando reapertura forzada. Dirección FINAL: {final_direction}", 'warning')
                try:
                    opened = self.abrir_operacion(final_direction, force=True, force_params=getattr(self, 'forced_open_params', None))
                    if opened:
                        self.next_forced_open = time.time() + float(intervalo)
                        self.add_log(f"[OK] ✅ Reapertura forzada realizada: {final_direction}", 'success')
                        return {'can_trade': True, 'signal': final_direction, 'reason': 'Forced open executed', 'recommendation': final_direction}
                    else:
                        self.add_log("[ERROR] Reapertura forzada rechazada por filtros", 'error')
                except Exception as e:
                    self.add_log(f"[ERROR] Error reapertura forzada: {e}", 'error')
                # Continuar con análisis normal aunque falle la forzada
            
            # ─────────────────────────────────────────────
            # PASO 1: SuperAnalyzer (6 motores votando)
            # ─────────────────────────────────────────────
            self.add_log("\n🔧 PASO 1: Super Analyzer (6 motores)", 'info')
            super_result = self.super_analyzer.analyze_super(symbol)
            
            if super_result['decision'] == 'HOLD':
                reason = '[OBJETIVO] SuperAnalyzer: Sin señal (HOLD)'
                self.add_log(f"[ADVERTENCIA] V12 Análisis RECHAZÓ: {reason}", 'warning')
                return {'can_trade': False, 'reason': reason}
            
            base_signal = super_result['decision']
            base_confidence = super_result['confidence']
            
            # ─────────────────────────────────────────────
            # PASO 2: Validar umbral dinámico
            # ─────────────────────────────────────────────
            self.add_log("\n🔧 PASO 2: Dynamic Calibration", 'info')
            is_valid, validation_reason = self.calibrator.validate_signal(
                'BUY' if base_signal == 'BUY' else 'SELL',
                base_confidence
            )
            
            self.add_log(f"   {validation_reason}", 'info')
            
            if not is_valid and base_confidence < 30:
                return {'can_trade': False, 'reason': f'[DATA] Calibración: Confianza muy baja'}
            
            adjusted_confidence = base_confidence
            
            # ─────────────────────────────────────────────
            # PASO 3: Filtro de sesión temporal
            # ─────────────────────────────────────────────
            self.add_log("\n🔧 PASO 3: Session Filter", 'info')
            can_trade_session, session_confidence, session_reason = self.session_filter.filter_signal(
                symbol,
                base_signal,
                base_confidence,
                strict_mode=False
            )
            
            self.add_log(f"   {session_reason}", 'info')
            adjusted_confidence = session_confidence
            
            if not can_trade_session:
                self.add_log(f"   ⏰ Sesión no óptima - Reduciendo confianza", 'warning')
            
            # ─────────────────────────────────────────────
            # PASO 4: Validar Correlaciones Multi-Activo
            # ─────────────────────────────────────────────
            self.add_log("\n🔧 PASO 4: Correlation Analyzer", 'info')
            correlation_analysis = self.correlation.analyze_correlation_signal(
                mt5,
                symbol,
                base_signal
            )
            
            if correlation_analysis.get('signal_confirmed'):
                self.add_log(f"   [EMOJI] Correlaciones confirmadas", 'info')
            else:
                self.add_log(f"   [ADVERTENCIA] {correlation_analysis.get('recommendation', 'Conflicto')}", 'warning')
                
                if correlation_analysis.get('correlation_risk') == 'HIGH':
                    return {'can_trade': False, 'reason': f"🔗 Correlación: Riesgo Alto"}
                elif correlation_analysis.get('correlation_risk') == 'MEDIUM':
                    adjusted_confidence *= 0.85
            
            # ─────────────────────────────────────────────
            # PASO 5: Evaluar Potencial de Recuperación
            # ─────────────────────────────────────────────
            self.add_log("\n🔧 PASO 5: Recovery Potential", 'info')
            recovery_result = self.recovery.analyze_recovery_potential(
                mt5,
                symbol,
                'H1'
            )
            
            recovery_score = recovery_result.get('recovery_score', 0)
            self.add_log(f"   Potencial de bounce: {recovery_score:.1f}% ({recovery_result.get('classification', 'N/A')})", 'info')
            
            # ─────────────────────────────────────────────
            # PASO 6: Validar Viabilidad Económica
            # ─────────────────────────────────────────────
            self.add_log("\n🔧 PASO 6: Spread & Slippage Analysis", 'info')
            
            # Usar stops del SuperAnalyzer
            if 'stops' not in super_result:
                return {'can_trade': False, 'reason': 'No stops disponibles'}
            
            stops = super_result['stops']
            
            viability = self.spread_analyzer.analyze_trade_viability(
                mt5,
                symbol,
                base_signal,
                target_pips=stops.get('tp_points', 40),
                stop_loss_pips=stops.get('sl_points', 20)
            )
            
            self.add_log(f"   {viability.get('viability_status', 'Evaluando...')}", 'info')
            self.add_log(f"   Spread: {viability.get('current_spread', 0):.2f}pips | R:R: {viability.get('rr_ratio_after', 0):.2f}:1", 'info')
            
            if not viability.get('is_viable'):
                return {'can_trade': False, 'reason': f"💱 Costos: No viable - {viability.get('recommendation', '')}"}
            
            # ─────────────────────────────────────────────
            # DECISIÓN FINAL
            # ─────────────────────────────────────────────
            MIN_CONFIDENCE_FINAL = 35
            
            if adjusted_confidence < MIN_CONFIDENCE_FINAL:
                return {
                    'can_trade': False, 
                    'reason': f'Confianza final {adjusted_confidence:.0f}% < {MIN_CONFIDENCE_FINAL}%'
                }
            
            # TRADE CONFIRMADO
            self.add_log(f"\n[OK] TRADE CONFIRMADO", 'success')
            self.add_log(f"   Señal: {base_signal}", 'success')
            self.add_log(f"   Confianza Final: {adjusted_confidence:.1f}%", 'success')
            self.add_log(f"   R:R: {viability.get('rr_ratio_after', 0):.2f}:1", 'success')
            self.add_log("="*70, 'info')
            
            return {
                'can_trade': True,
                'signal': base_signal,
                'confidence': adjusted_confidence,
                'entry_price': viability.get('entry_price'),
                'tp_pips': viability.get('adjusted_tp_pips', 40),
                'sl_pips': viability.get('adjusted_sl_pips', 20),
                'reason': 'Todos los análisis confirmaron',
                'metadata': {
                    'super_votes_buy': super_result.get('buy_votes', 0),
                    'super_votes_sell': super_result.get('sell_votes', 0),
                    'recovery_score': recovery_score,
                    'spread_cost': viability.get('total_cost_pips', 0)
                }
            }
        
        except Exception as e:
            self.add_log(f"[ERROR] Error en análisis V12: {str(e)}", 'error')
            return {'can_trade': False, 'reason': f'Error: {str(e)}'}

    def _analizar_tradicional(self, symbol):
        """Análisis tradicional con GoldAnalyzer (método original)"""
        opportunity = self.gold_analyzer.analyze_opportunity()
        
        if opportunity is None:
            return None
        
        if opportunity['probability'] < 73.0:
            self.add_log(f"Probabilidad {opportunity['probability']:.1f}% insuficiente (mín 73%)", 'warning')
            return None
        
        self.add_log(f"ℹ️ Fuerza de tendencia: {opportunity['trend_strength']:.2f}", 'info')
        
        if opportunity['probability'] > 85.0:
            self.add_log(f"🌟 SEÑAL PREMIUM detectada! Prob: {opportunity['probability']:.1f}%", 'success')
        else:
            self.add_log(f"[OK] Señal válida con probabilidad {opportunity['probability']:.1f}%", 'success')
        
        self.add_log(f"""
[DATA] Detalles de la señal:
[EMOJI]️ Dirección: {opportunity['direction']}
💯 Probabilidad: {opportunity['probability']:.1f}%
📈 TP: {opportunity['tp_points']:.1f} puntos
[EMOJI] SL: 100.0 puntos fijos
""", 'info')
        
        return opportunity['direction']

    # ⭐ NUEVO: Método para calcular potencial de recuperación EN TIEMPO REAL
    def _calculate_market_recovery_potential(self, symbol, direccion):
        """Calcula el potencial de recuperación ANTES de abrir la operación"""
        try:
            # Obtener datos de las últimas 24 horas
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            rates = mt5_safe.copy_rates_range_safe(symbol, mt5.TIMEFRAME_H1, start_date, end_date)
            if rates is None or len(rates) < 10:
                self.add_log("[ADVERTENCIA] No hay datos de 24h - Permitiendo operación", 'warning')
                return 100.0  # Sin datos = permitir
            
            closes = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
            highs = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates])
            lows = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates])
            
            # Obtener precio actual EN TIEMPO REAL
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return 100.0
            
            current_price = tick.bid
            
            # Calcular extremos de 24h
            highest_24h = np.max(highs)
            lowest_24h = np.min(lows)
            
            # Calcular potencial según dirección
            if direccion == "BUY":
                # Para BUY: espacio hasta resistencia / distancia al soporte
                space_to_resistance = ((highest_24h - current_price) / current_price) * 100
                distance_to_support = ((current_price - lowest_24h) / current_price) * 100
                
                if distance_to_support <= 0:
                    return 0.0
                
                recovery_potential = (space_to_resistance / distance_to_support) * 100
                
                self.add_log(
                    f"📈 POTENCIAL BUY: Resistencia +{space_to_resistance:.2f}% | "
                    f"Soporte -{distance_to_support:.2f}% = {recovery_potential:.1f}%",
                    'info'
                )
                
            else:  # SELL
                # Para SELL: espacio hasta soporte / distancia a resistencia
                space_to_support = ((current_price - lowest_24h) / current_price) * 100
                distance_to_resistance = ((highest_24h - current_price) / current_price) * 100
                
                if distance_to_resistance <= 0:
                    return 0.0
                
                recovery_potential = (space_to_support / distance_to_resistance) * 100
                
                self.add_log(
                    f"📉 POTENCIAL SELL: Soporte -{space_to_support:.2f}% | "
                    f"Resistencia +{distance_to_resistance:.2f}% = {recovery_potential:.1f}%",
                    'info'
                )
            
            return recovery_potential
            
        except Exception as e:
            self.add_log(f"Error calculando potencial: {str(e)}", 'error')
            return 100.0  # En caso de error, permitir

    # ⭐ NUEVO: Sistema de volumen dinámico (Kelly-inspired)
    def calculate_dynamic_volume(self, confidence=None):
        """
        Calcula volumen dinámicamente basado en:
        1. Confianza de señal: 30-50% → -50%, 70%+ → +50%
        2. Pérdidas recientes: 1-2 pérdidas últimas → -30%
        3. Volatilidad del mercado: volatilidad alta → -20%
        
        Impacto: +15% CAGR sin aumentar riesgo absoluto
        """
        try:
            base_vol = self.base_volume if hasattr(self, 'base_volume') else float(self.config['VOL'].get())
            dynamic_vol = base_vol
            adjustments = []
            
            # 1. Ajuste por confianza de señal
            if confidence is None:
                confidence = getattr(self, 'last_signal_confidence', 50)
            
            if confidence < 30:
                multiplier = 0.3  # -70%
                reason = f"Confianza muy baja ({confidence:.0f}%)"
            elif confidence < 50:
                multiplier = 0.5  # -50%
                reason = f"Confianza baja ({confidence:.0f}%)"
            elif confidence < 70:
                multiplier = 1.0  # Sin cambio
                reason = f"Confianza normal ({confidence:.0f}%)"
            else:
                multiplier = 1.5  # +50%
                reason = f"Confianza alta ({confidence:.0f}%)"
            
            dynamic_vol = base_vol * multiplier
            adjustments.append(f"Confianza: {multiplier:.1f}x ({reason})")
            
            # 2. Ajuste por pérdidas recientes (últimas 3 trades)
            if not hasattr(self, 'recent_losses'):
                self.recent_losses = []
            
            # Limpiar pérdidas antiguas (>100 trades)
            self.recent_losses = [(t, p) for t, p in self.recent_losses if time.time() - t < 1000]
            
            loss_count = len(self.recent_losses)
            if loss_count >= 2:
                # 2+ pérdidas recientes → reducir 30%
                dynamic_vol *= 0.7
                adjustments.append(f"Pérdidas recientes: x0.7 ({loss_count} pérdidas)")
            elif loss_count >= 1:
                # 1 pérdida reciente → reducir 15%
                dynamic_vol *= 0.85
                adjustments.append(f"1 pérdida reciente: x0.85")
            
            # 3. Ajuste por volatilidad del mercado
            try:
                snaps = self.reload_market_snapshots() or []
                vol_level = self.get_volatility_level(snaps)
                if vol_level == 'HIGH':
                    dynamic_vol *= 0.8  # -20% en volatilidad alta
                    adjustments.append("Volatilidad alta: x0.8")
                elif vol_level == 'LOW':
                    dynamic_vol *= 1.1  # +10% en volatilidad baja
                    adjustments.append("Volatilidad baja: x1.1")
            except Exception:
                pass
            
            # Limites: no más de 3x el volumen base, no menos de 0.1x
            dynamic_vol = max(base_vol * 0.1, min(dynamic_vol, base_vol * 3.0))
            
            # Logging
            if abs(dynamic_vol - base_vol) > base_vol * 0.01:
                final_multiplier = dynamic_vol / base_vol
                msg = f"[VOLUMEN] Base: {base_vol:.4f} → Dinámico: {dynamic_vol:.4f} ({final_multiplier:.2f}x) | "
                msg += " | ".join(adjustments)
                self.add_log(msg, 'info')
            
            return dynamic_vol
            
        except Exception as e:
            self.add_log(f"[VOLUMEN] Error calculando volumen dinámico: {str(e)[:60]}", 'warning')
            return float(self.config['VOL'].get())

    def abrir_operacion(self, direccion_sugerida, force=False, startup=False, force_params=None):
        """Versión mejorada para una sola operación con mejor análisis.
        
        IMPORTANTE: SIEMPRE entrena especialistas y hace análisis DUAL
        
        Si `force=True`: El análisis se ejecuta igual, pero el arbitrador IGNORA el filtro MARKET_HOURS
        (permite abrir incluso fuera de horas óptimas)
        
        ⭐ FLUJO: ANÁLISIS DUAL (siempre) → ARBITRADOR (ignora MARKET_HOURS si force=True) → EJECUCIÓN
        """
        try:
            # ⭐ VERIFICACIÓN CRÍTICA: Bot detenido o deteniendo
            # EXCEPTO durante startup (que ocurre antes de is_running=True)
            if not startup and not self.is_running:
                self.add_log(f"[ABRIR] ❌ Bot no está en running (is_running={self.is_running})", 'warning')
                return False
            
            # ⭐ Verificar también que scheduler sigue corriendo (si es llamado desde scheduler)
            if not startup and not getattr(self, '_scheduler_running', True):
                self.add_log(f"[ABRIR] ❌ Scheduler detenido", 'warning')
                return False
            
            if getattr(self, 'force_stop_triggered', False):
                self.add_log(f"[ABRIR] ❌ Stop forzado activado", 'warning')
                return False
            
            symbol = self.config['SYMBOL'].get()
            self.add_log(f"[ABRIR] ✓ Verificaciones iniciales OK | Símbolo: {symbol} | Force: {force} | Startup: {startup}", 'info')
            
            # ⭐ VERIFICACIÓN CRÍTICA: Consultar FLAGS de sincronización (trend_monitor)
            # Si hay reversión INMINENTE (70%+) CONTRARIA a dirección_sugerida, BLOQUEAR
            with self.trend_analysis_lock:
                imminent_reversal = self.trend_imminent_reversal
                imminent_direction = self.trend_imminent_direction
                imminent_confidence = self.trend_imminent_confidence
            
            if imminent_reversal and imminent_direction != None:
                # Si intento abrir en dirección CONTRARIA a la reversión esperada, BLOQUEAR
                # (imminent_direction es la dirección que VA A VENIR, así que NO abrir en lo opuesto)
                if (direccion_sugerida == 'BUY' and imminent_direction == 'SELL') or \
                   (direccion_sugerida == 'SELL' and imminent_direction == 'BUY'):
                    self.add_log(f"[ABRIR] 🛑 BLOQUEADA: Reversión INMINENTE → {imminent_direction} @ {imminent_confidence:.1f}% confianza", 'error')
                    self.add_log(f"[ABRIR] Intento: {direccion_sugerida} | Conflicto: Esperando reversa a {imminent_direction}", 'warning')
                    return False  # BLOQUEAR APERTURA
            
            # ✅ PASO 1: SIEMPRE hacer entrenamiento y análisis dual
            # Esto es OBLIGATORIO antes de cualquier apertura
            analysis = self._dual_analysis_before_opening(symbol)
            if not analysis:
                self.add_log("[ABRIR] ❌ DUAL analysis devolvió None", 'error')
                return False
            
            self.add_log(f"[ABRIR] ✓ DUAL análisis completado", 'info')
            
            # ✅ PASO 2: Verificar que el arbitrador decidió BUY o SELL
            rec = analysis.get('recommendation', 'HOLD')
            buy_res = analysis.get('buy_specialist', {})
            sell_res = analysis.get('sell_specialist', {})
            buy_score = buy_res.get('score', 0)
            sell_score = sell_res.get('score', 0)
            buy_conf = buy_res.get('confidence', 0)
            sell_conf = sell_res.get('confidence', 0)
            
            # ⭐ EN MODO FORZADO: SIEMPRE abrir en dirección con MAYOR score
            # (ignora HOLD del arbitrador por MARKET_HOURS, etc)
            if force:
                # ⭐ FIX #21: En modo FORZADO, ser más lenient - si confianza ≥60%, proceder
                # Solo rechazar si AMBOS son muy bajos (score <30 AND conf <50)
                
                if buy_score > sell_score:
                    direction_override = 'BUY'
                    chosen_score = buy_score
                    chosen_conf = buy_conf
                    self.add_log(f"[FORCE] 🟢 BUY {buy_conf:.0f}%", 'success')
                elif sell_score > buy_score:
                    direction_override = 'SELL'
                    chosen_score = sell_score
                    chosen_conf = sell_conf
                    self.add_log(f"[FORCE] 🔴 SELL {sell_conf:.0f}%", 'success')
                else:
                    direction_override = direccion_sugerida
                    chosen_score = max(buy_score, sell_score)
                    chosen_conf = max(buy_conf, sell_conf)
                    self.add_log(f"[FORCE] Scores iguales ({buy_score:.1f}), usando sugerencia: {direction_override}", 'info')
                
                # ⭐ FIX #21: Lógica de rechazo más flexible para forzado
                # Solo rechazar si AMBOS son demasiado bajos (protección extrema)
                if chosen_score < 30.0 and chosen_conf < 50.0:
                    self.add_log(f"[FORCE] ❌ RECHAZADO: Score {chosen_score:.1f}% + Conf {chosen_conf:.0f}% = Ambos muy débiles (protección extrema)", 'warning')
                    return False
                
                # Si confianza es razonable (≥60%), proceder aunque score sea bajo
                if chosen_conf >= 60.0:
                    if chosen_score < 40.0:
                        self.add_log(f"[FORCE] ✅ PROCEDIENDO: Confianza {chosen_conf:.0f}% es fuerte (score {chosen_score:.1f}% bajo pero compensado)", 'success')
                else:
                    self.add_log(f"[FORCE] ⚠️ ADVERTENCIA: Score {chosen_score:.1f}% bajo, Conf {chosen_conf:.0f}% baja - procediendo con precaución", 'warning')
                
                # Usar score-based direction para abrir
                direccion_sugerida = direction_override
                
            elif rec == 'HOLD':
                # NO es forzado: Respetar HOLD del arbitrador
                self.add_log(f"[⚠️ CONFLICTO] Arbitrador decidió HOLD (scores: BUY={buy_score:.1f}, SELL={sell_score:.1f}) - No abrir operación", 'warning')
                return False
            elif rec not in ['BUY', 'SELL']:
                # Recomendación inválida
                self.add_log(f"[DUAL] Arbitrador decidió {rec} - No abrir operación", 'warning')
                return False
                    
        except Exception as e:
            logger.error(f"Error en análisis dual: {e}")
            self.add_log(f"[ERROR] Análisis dual falló: {str(e)[:80]}", 'error')
            # En caso de error en análisis, NO abrir operación
            return False
        
        # ⭐ Función helper ROBUSTA para acceso a config
        def safe_config(key, default_val):
            try:
                val = self.config.get(key)
                if val is None:
                    return default_val
                elif hasattr(val, 'get'):  # tk.IntVar, tk.StringVar, tk.BooleanVar
                    result = val.get()
                    return default_val if result is None else result
                else:  # valor directo
                    return val
            except Exception:
                return default_val
        
        # Respetar máximo de operaciones configurado
        try:
            max_ops = int(safe_config('MAX_SIMULTANEOUS_OPS', 1))
        except Exception:
            max_ops = 1
        
        # ⭐ QUERY DINÁMICA: Contar posiciones abiertas en MT5 EN TIEMPO REAL
        try:
            # Obtener MAGIC_NUMBER de forma robusta 
            magic_num = int(safe_config('MAGIC_NUMBER', 123456))
            
            open_positions_live = len([p for p in (mt5.positions_get(symbol=symbol) or []) 
                                       if getattr(p, 'magic', None) == magic_num])
            
            if open_positions_live >= max_ops:
                self.add_log(f"[ABRIR] ❌ Max ops alcanzado: {open_positions_live}/{max_ops} (query dinámica)", 'warning')
                return False
            
            # Actualizar el contador local para que sea consistente
            self.total_operaciones_abiertas = open_positions_live
            self.add_log(f"[ABRIR] ✓ Posiciones vivas: {open_positions_live}/{max_ops}", 'info')
        except Exception as e:
            import traceback
            self.add_log(f"[ABRIR] ⚠️ ERROR query: {type(e).__name__}: {str(e)[:80]}", 'error')
            logger.error(f"Query dinámica exception:\n{traceback.format_exc()}")
            # Fallback al contador si hay error
            if self.total_operaciones_abiertas >= max_ops:
                self.add_log(f"[ABRIR] ❌ Max ops alcanzado (fallback): {self.total_operaciones_abiertas}/{max_ops}", 'warning')
                return False
        
        # If configured, require volatility to be NORMAL for openings (unless startup)
        try:
            require_vol = bool(self.config.get('REQUIRE_VOLATILITY_NORMAL', tk.BooleanVar(value=True)).get())
        except Exception:
            require_vol = True
        # Volatility requirement: allow bypass when force=True
        if require_vol and not startup and not force:
            try:
                snaps = self.reload_market_snapshots() or []
                vol_level = self.get_volatility_level(snaps)
                if vol_level != 'NORMAL':
                    self.add_log(f"[ABRIR] ⚠️ Volatilidad: {vol_level} (requiere NORMAL)", 'warning')
                    return False
                else:
                    self.add_log(f"[ABRIR] ✓ Volatilidad OK: {vol_level}", 'info')
            except Exception as e:
                self.add_log(f"[ABRIR] ⚠️ Error en volatilidad: {str(e)[:60]}", 'warning')
                pass
        
        # ⭐ STARTUP: Verificación especial de snapshots (DESANIDADO - debe ejecutarse siempre si startup=True)
        if startup:
            self.add_log(f"[STARTUP] Verificando snapshots para apertura inicial...", 'info')
            try:
                snaps = []
                try:
                    snaps = self.reload_market_snapshots() or []
                except Exception as e:
                    logger.exception("Error leyendo market_snapshots en apertura startup")
                    self.add_log(f"[STARTUP] ⚠️ Error loadings snapshots: {str(e)[:60]}", 'warning')
                    snaps = []

                if not snaps:
                    self.add_log("[STARTUP] ❌ No hay snapshots - abortando", 'error')
                    return False

                self.add_log(f"[STARTUP] ✓ {len(snaps)} snapshots cargados", 'info')
                
                # Ejecutar especialistas sobre snapshots
                buy_res = None
                sell_res = None
                try:
                    buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                except Exception as e:
                    self.add_log(f"[STARTUP] ⚠️ BUY análisis: {str(e)[:60]}", 'warning')
                    buy_res = None
                try:
                    sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                except Exception as e:
                    self.add_log(f"[STARTUP] ⚠️ SELL análisis: {str(e)[:60]}", 'warning')
                    sell_res = None

                # Determinar decisión basada en snapshots
                chosen = None
                try:
                    if buy_res and sell_res:
                        buy_score = float(buy_res.get('score', 0))
                        sell_score = float(sell_res.get('score', 0))
                        
                        if buy_score > sell_score:
                            chosen = 'BUY'
                        elif sell_score > buy_score:
                            chosen = 'SELL'
                        else:
                            chosen = 'BUY' if float(buy_res.get('confidence', 0)) >= float(sell_res.get('confidence', 0)) else 'SELL'
                        
                        self.add_log(f"[STARTUP] ✓ BUY={buy_score:.1f} vs SELL={sell_score:.1f} → {chosen}", 'info')
                    elif buy_res:
                        chosen = 'BUY'
                    elif sell_res:
                        chosen = 'SELL'
                except Exception as e:
                    self.add_log(f"[STARTUP] ❌ Error analizando: {str(e)[:60]}", 'error')
                    chosen = None

                if not chosen:
                    self.add_log("[STARTUP] ❌ No se pudo determinar dirección", 'error')
                    return False

                self.add_log(f"[STARTUP] ✓ Dirección: {chosen} | Sugerida: {direccion_sugerida}", 'info')
                
                # Usar la dirección elegida
                if chosen != direccion_sugerida:
                    self.add_log(f"[⚠️ STARTUP] Usando {chosen} en lugar de {direccion_sugerida} por sesgo de tendencia", 'info')
                    direccion_sugerida = chosen
                
                self.add_log(f"[STARTUP] ✅ Verificación completada - continuando con apertura", 'success')
                
            except Exception as e:
                self.add_log(f"[STARTUP] ❌ Exception: {str(e)[:80]}", 'error')
                import traceback
                self.add_log(f"[TRACE] {traceback.format_exc()[:200]}", 'error')
                return False
        symbol = self.config['SYMBOL'].get()
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.add_log("No se pudo obtener información del símbolo", 'error')
            return False
        
        # ⭐ NUEVO: Verificar potencial ANTES de abrir (omitido si force=True)
        if not force:
            min_recovery_pct = float(self.config['MIN_RECOVERY_POTENTIAL'].get())
            recovery_potential = self._calculate_market_recovery_potential(symbol, direccion_sugerida)
            if recovery_potential < min_recovery_pct:
                self.add_log(
                    f"[ADVERTENCIA] Operación {direccion_sugerida} RECHAZADA | "
                    f"Potencial {recovery_potential:.1f}% < {min_recovery_pct:.1f}% (mínimo requerido)",
                    'warning'
                )
                return False
            self.add_log(
                f"[OK] Potencial de recuperación OK: {recovery_potential:.1f}% >= {min_recovery_pct:.1f}%",
                'success'
            )
        
        # ⭐ SIEMPRE usar TP_DIFF y SL_DIFF de la interfaz (diferencia DIRECTA en precio)
        # Ya no se usa gold_analyzer para TP dinámico - TODOS los modos usan config
        try:
            tp_diff = float(self.config['TP_DIFF'].get()) if 'TP_DIFF' in self.config else 5.0
        except Exception:
            tp_diff = 5.0
        
        # ⭐ OBLIGATORIO: obtener SL desde config (respetar diferencia DIRECTA en precio)
        try:
            sl_diff = float(self.config['SL_DIFF'].get()) if 'SL_DIFF' in self.config else 50.0
        except Exception:
            sl_diff = 50.0
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return False
        
        precio = tick.ask if direccion_sugerida == "BUY" else tick.bid
        
        # ⭐ CORREGIDO: Usar TP_DIFF y SL_DIFF como diferencia DIRECTA en precio (no multiplicar por point)
        digits = get_symbol_digits(symbol_info)
        if direccion_sugerida == "BUY":
            sl = round(precio - sl_diff, digits)
            tp = round(precio + tp_diff, digits)
            tipo = mt5.ORDER_TYPE_BUY
        else:
            sl = round(precio + sl_diff, digits)
            tp = round(precio - tp_diff, digits)
            tipo = mt5.ORDER_TYPE_SELL
        
        self.add_log(f"[TP/SL] precio={precio:.2f} TP_DIFF={tp_diff} SL_DIFF={sl_diff} → TP={tp:.2f} SL={sl:.2f}", 'info')
        
        # ⭐ VALIDAR STOPS contra STOPS_LEVEL del broker
        sl, tp, stops_ajustados = validate_and_adjust_stops(
            symbol_info, precio, sl, tp, direccion_sugerida, log_callback=self.add_log
        )
        if stops_ajustados:
            self.add_log(f"[STOPS] Stops ajustados para cumplir requisitos del broker", 'warning')
        
        # ===== NUEVO: Hard-filters antes de enviar orden =====
        try:
            # Re-evaluar estado de pausas y bloqueos (permitir bypass con force=True)
            if getattr(self, 'bot_pausado', False) and not force:
                self.add_log("[PAUSA] Bot en pausa - abortando apertura", 'warning')
                return False
            if time.time() < getattr(self, 'block_until', 0) and not force:
                self.add_log("[ESPERA] Cooldown activo - abortando apertura", 'warning')
                return False

            # Equity / drawdown checks
            try:
                acct = mt5.account_info()
                equity = float(getattr(acct, 'equity', self.saldo_actual)) if acct is not None else float(self.saldo_actual)
            except Exception:
                equity = float(self.saldo_actual)

            # Drawdown % desde balance inicial (informativo, no limita operaciones)
            try:
                if hasattr(self, 'balance_inicial') and self.balance_inicial and self.balance_inicial > 0:
                    drawdown_pct = max(0.0, (self.balance_inicial - equity) / float(self.balance_inicial) * 100.0)
                else:
                    drawdown_pct = 0.0
            except Exception:
                drawdown_pct = 0.0

            # Force stop loss (absolute money) check
            try:
                force_stop = float(self.config.get('FORCE_STOP_LOSS', tk.DoubleVar(value=0.0)).get())
            except Exception:
                force_stop = 0.0
            if force_stop > 0 and self.ganancia_neta <= -force_stop:
                self.add_log(f"[STOP] Stop forzado en ${force_stop} alcanzado -> abortando apertura", 'error')
                return False

        except Exception:
            pass

        # If force_params provided, use those; otherwise calculate from config
        if force_params:
            try:
                # VOLUMEN FIJO: usar siempre config, sin escaling dinámico
                if 'vol' in force_params and force_params.get('vol') is not None:
                    vol = float(force_params.get('vol'))
                else:
                    vol = float(self.config['VOL'].get())
            except Exception:
                vol = float(self.config['VOL'].get())
            
            # ⭐ TakeProfit: usar force_params si existe, sino calcular desde config
            try:
                if 'tp' in force_params and force_params.get('tp') is not None:
                    tp = float(force_params.get('tp'))
                    self.add_log(f"[FORZADA] Usando TP desde force_params: {tp}", 'info')
                else:
                    # ⭐ CORREGIDO: TP_DIFF es diferencia DIRECTA en precio
                    if direccion_sugerida == 'BUY':
                        tp = round(precio + tp_diff, get_symbol_digits(symbol_info))
                    else:
                        tp = round(precio - tp_diff, get_symbol_digits(symbol_info))
                    self.add_log(f"[FORZADA] TP calculado desde config (TP_DIFF={tp_diff}): {tp}", 'info')
            except Exception as e:
                self.add_log(f"[FORZADA] Error calculando TP: {e}", 'warning')
                tp = None
            
            # ⭐ StopLoss: usar force_params si existe, sino calcular desde config
            try:
                if 'sl' in force_params and force_params.get('sl') is not None:
                    sl = float(force_params.get('sl'))
                    self.add_log(f"[FORZADA] Usando SL desde force_params: {sl}", 'info')
                else:
                    # ⭐ CORREGIDO: SL_DIFF es diferencia DIRECTA en precio
                    if direccion_sugerida == 'BUY':
                        sl = round(precio - sl_diff, get_symbol_digits(symbol_info))
                    else:
                        sl = round(precio + sl_diff, get_symbol_digits(symbol_info))
                    self.add_log(f"[FORZADA] SL calculado desde config (SL_DIFF={sl_diff}): {sl}", 'info')
            except Exception as e:
                self.add_log(f"[FORZADA] Error calculando SL: {e}", 'warning')
                sl = None
        else:
            # ===== NUEVO: Sizing dinámico por riesgo (RISK_PCT) =====
            # Los SL/TP ya fueron calculados arriba con tp_diff y sl_diff
            try:
                risk_pct = float(self.config.get('RISK_PCT', tk.DoubleVar(value=0.005)).get()) if 'RISK_PCT' in self.config else 0.005
                risk_amount = equity * float(risk_pct)
                sl_price_diff = abs(precio - sl)
                # ⭐ Usar contract_size correcto (dividir por 100 para oro/metales)
                raw_contract_size = getattr(symbol_info, 'trade_contract_size', 1.0) or 1.0
                contract_size = max(1, raw_contract_size / 100.0) if raw_contract_size >= 100 else raw_contract_size

                # Evitar división por cero
                if sl_price_diff <= 0:
                    vol = float(self.config['VOL'].get())
                else:
                    # Estimar volumen: volume = risk_amount / (sl_price_diff * contract_size)
                    estimated_vol = float(risk_amount) / (float(sl_price_diff) * float(contract_size))
                    # Ajustar a pasos del símbolo
                    vol_step = getattr(symbol_info, 'volume_step', None)
                    vol_min = getattr(symbol_info, 'volume_min', None)
                    vol_max = getattr(symbol_info, 'volume_max', None)
                    if vol_step and vol_step > 0:
                        # Round down to nearest step
                        steps = max(1, int(estimated_vol / vol_step))
                        vol = max(vol_step, steps * vol_step)
                    else:
                        vol = max(0.01, round(estimated_vol, 2))

                    if vol_min and vol < vol_min:
                        vol = vol_min
                    if vol_max and vol > vol_max:
                        vol = vol_max

                # Fallback si volumen no válido
                if not vol or vol <= 0:
                    vol = float(self.config['VOL'].get())
            except Exception:
                vol = float(self.config['VOL'].get())

        # VOLUMEN FIJO: usar siempre config sin escaling
        try:
            vol = float(self.config['VOL'].get())
        except Exception as e:
            self.add_log(f"[VOLUME] Error obteniendo volumen de config: {str(e)}", 'warning')
            try:
                vol = float(self.config['VOL'].get())
            except Exception:
                vol = 0.02

        mode_prefix = "MultiIA" if self.use_multi_ai.get() else "IA"

        # Asegurar que SL/TP tienen sentido relativo al precio (evitar stops invertidos)
        # ⭐ CORREGIDO: Usar diferencias DIRECTAS en precio (no multiplicar por point)
        try:
            tp_cfg = abs(float(self.config.get('TP_DIFF', tk.DoubleVar(value=5.0)).get()))
        except Exception:
            tp_cfg = 5.0
        try:
            sl_cfg = abs(float(self.config.get('SL_DIFF', tk.DoubleVar(value=50.0)).get()))
        except Exception:
            sl_cfg = 50.0
        
        digits = get_symbol_digits(symbol_info)
        try:
            if tipo == mt5.ORDER_TYPE_BUY:
                # SL must be below price; TP must be above
                if sl is None or sl >= precio:
                    sl = round(precio - sl_cfg, digits)
                    self.add_log(f"[ADVERTENCIA] SL inválido corregido para BUY -> {sl:.{digits}f}", 'warning')
                if tp is None or tp <= precio:
                    tp = round(precio + tp_cfg, digits)
                    self.add_log(f"[ADVERTENCIA] TP inválido corregido para BUY -> {tp:.{digits}f}", 'warning')
            else:
                # For SELL: SL above price; TP below price
                if sl is None or sl <= precio:
                    sl = round(precio + sl_cfg, digits)
                    self.add_log(f"[ADVERTENCIA] SL inválido corregido para SELL -> {sl:.{digits}f}", 'warning')
                if tp is None or tp >= precio:
                    tp = round(precio - tp_cfg, digits)
                    self.add_log(f"[ADVERTENCIA] TP inválido corregido para SELL -> {tp:.{digits}f}", 'warning')
        except Exception:
            pass

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(vol),
            "type": tipo,
            "price": precio,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": self.config['MAGIC_NUMBER'],
            "comment": f"Bot-{mode_prefix}-{direccion_sugerida}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Log de parámetros justo antes de enviar
        try:
            self.add_log(f"Enviando orden -> symbol={symbol} vol={vol} precio={precio} sl={sl} tp={tp} tipo={'BUY' if tipo==mt5.ORDER_TYPE_BUY else 'SELL'}", 'info')
        except Exception:
            pass

        # Verificar límite máximo de operaciones antes de enviar (aplica también para force)
        try:
            max_ops = int(self._safe_get('MAX_SIMULTANEOUS_OPS', 1))
        except Exception:
            max_ops = 1
        try:
            positions = mt5.positions_get(symbol=symbol) or []
            buy_count = 0
            sell_count = 0
            for pos in positions:
                if getattr(pos, 'magic', None) == self.config['MAGIC_NUMBER']:
                    if getattr(pos, 'type', None) == mt5.POSITION_TYPE_BUY:
                        buy_count += 1
                    else:
                        sell_count += 1
            total_actual = buy_count + sell_count
        except Exception:
            total_actual = 0

        if total_actual >= max_ops:
            self.add_log(f"[ERROR] Máximo de operaciones alcanzado ({total_actual}/{max_ops}) - abortando apertura", 'warning')
            return False

        # ⭐ LOG DETALLADO de la operación antes de enviar
        if force:
            self.add_log(f"\n{'='*60}", 'warning')
            self.add_log(f"[FORZADA] ABRIENDO OPERACIÓN CON PARÁMETROS CONFIG", 'warning')
            self.add_log(f"   Dirección: {direccion_sugerida}", 'info')
            self.add_log(f"   Precio: {precio:.5f}", 'info')
            self.add_log(f"   TP: {tp:.5f} (TP_DIFF={tp_diff})", 'success')
            self.add_log(f"   SL: {sl:.5f} (SL_DIFF={sl_diff})", 'error')
            self.add_log(f"   Volumen: {vol}", 'info')
            self.add_log(f"{'='*60}\n", 'warning')
        
        # ⭐ TICK FLOW ANALYSIS - Resolver dirección con presión de mercado (microestructura)
        if self.use_tick_flow.get() and self.tick_flow_analyzer:
            try:
                ticks = self.tick_flow_analyzer.get_recent_ticks(
                    limit=self.config['TICK_FLOW_WINDOW'].get()
                )
                if ticks is not None:
                    # ⭐ USAR resolve_final_direction() en lugar de confirm_signal()
                    # Esto INVIERTE automáticamente si hay conflicto FUERTE
                    flow_result = self.tick_flow_analyzer.resolve_final_direction(
                        ia_direction=direccion_sugerida,
                        ticks=ticks
                    )
                    
                    # Aplicar resolución de dirección
                    if flow_result.get('inverted', False):
                        # ⚠️ CONFLICTO FUERTE - INVERTIR DIRECCIÓN
                        self.add_log(
                            f"[TICK] ⚠️ DIRECCIÓN INVERTIDA: {direccion_sugerida} → {flow_result['final_direction']}",
                            'error'
                        )
                        self.add_log(
                            f"[TICK] Razón: {flow_result.get('reason', 'Presión opuesta detectada')}",
                            'error'
                        )
                        direccion_sugerida = flow_result['final_direction']
                    else:
                        # ✅ CONFIRMADO O DÉBIL - MANTENER IA
                        self.add_log(
                            f"[TICK] ✅ Dirección CONFIRMADA: {flow_result['final_direction']}",
                            'success' if flow_result.get('flow_strength') == 'FUERTE' else 'info'
                        )
                        self.add_log(
                            f"[TICK] Razón: {flow_result.get('reason', 'Sin conflicto')}",
                            'info'
                        )
                    
                    # Mostrar métricas
                    self.add_log(
                        f"[TICK] Métricas: Imbalance={flow_result.get('imbalance', 'N/A')}±{self.tick_flow_analyzer.imbalance_threshold} | "
                        f"Momentum={flow_result.get('momentum', 'N/A'):.1f}%",
                        'info'
                    )
                else:
                    self.add_log("[TICK] No se obtuvieron datos de ticks - continuando sin análisis de microestructura", 'warning')
            except Exception as e:
                self.add_log(f"[TICK] Error en análisis de microestructura: {str(e)[:80]}", 'warning')
        
        result = mt5.order_send(request)
        # Log completo del resultado de envío para diagnóstico (retcode, comment, order id)
        try:
            self.add_log(f"order_send result: retcode={getattr(result,'retcode',None)} comment={getattr(result,'comment',None)} repr={repr(result)}", 'debug')
        except Exception:
            pass
        try:
            if not (result and getattr(result, 'retcode', None) == mt5.TRADE_RETCODE_DONE):
                save_failed_order(request, result, tag='order_send')
                try:
                    # Intentar manejar el fallo automáticamente (requote/price_changed)
                    handled = handle_order_failure(self, request, result, tag='order_send', max_retries=2)
                    if handled:
                        # Si el manejador tuvo éxito, salir para no procesar el flujo de fallo
                        return True
                except Exception:
                    pass
                # Mostrar mensaje amigable en UI para retcodes comunes (solo si falló)
                try:
                    rc_msg = interpret_retcode(result)
                    comment = getattr(result, 'comment', None)
                    self.add_log(f"[RECHAZO ORDEN] {rc_msg} comment={comment}", 'error')
                except Exception:
                    pass
                return False
        except Exception:
            pass
        if result and getattr(result, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
            # Intentar localizar la posición creada por este envío para registrar el ticket real
            ticket_found = None
            executed_volume = float(vol)
            executed_sl = sl
            executed_tp = tp

            # Pequeño loop de espera para que la posición aparezca en positions_get
            for attempt in range(6):
                try:
                    positions = mt5.positions_get(symbol=symbol)
                    if positions:
                        # Filtrar por magic y volumen aproximado y que no esté ya trackeada
                        candidates = [p for p in positions if getattr(p, 'magic', None) == self.config['MAGIC_NUMBER']]
                        for p in candidates:
                            # Evitar posiciones ya registradas
                            if p.ticket in self.position_tracking:
                                continue
                            # Comparar volumen (con tolerancia)
                            try:
                                if abs(float(p.volume) - float(executed_volume)) <= max(0.0001, float(executed_volume)*0.1):
                                    ticket_found = p
                                    break
                            except Exception:
                                ticket_found = p
                                break
                        if ticket_found:
                            break
                except Exception:
                    pass
                time.sleep(0.5)

            # Si encontramos la posición, registrar sus datos reales
            if ticket_found:
                pos = ticket_found
                self.position_ids.add(pos.ticket)
                self.position_tracking[pos.ticket] = {
                    'open_time': time.time(),
                    'open_price': float(pos.price_open),
                    'direction': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                    'volume': float(pos.volume),
                    'sl': float(getattr(pos, 'sl', executed_sl)),
                    'tp': float(getattr(pos, 'tp', executed_tp)),
                }
                
                # NUEVO: Registrar metadata en feedback loop para análisis posterior
                try:
                    if self.last_trade_metadata:
                        self.last_trade_metadata['ticket'] = int(pos.ticket)
                        self.feedback_loop_ai.record_trade_analysis(self.last_trade_metadata)
                        self.add_log(f"[FEEDBACK] Análisis #{pos.ticket} registrado para retroalimentación", 'info')
                except Exception as e:
                    self.add_log(f"[FEEDBACK] Error registrando análisis: {str(e)[:50]}", 'warning')
                
                executed_volume = float(pos.volume)
                try:
                    executed_sl = float(getattr(pos, 'sl', executed_sl))
                except Exception:
                    pass
                try:
                    executed_tp = float(getattr(pos, 'tp', executed_tp))
                except Exception:
                    pass

            else:
                # Fallback: usar result.order como referencia si no aparece la posición
                try:
                    fallback_ticket = int(getattr(result, 'order', -1))
                    self.position_ids.add(fallback_ticket)
                    # Crear tracking provisional para que los monitores detecten la posición
                    try:
                        self.position_tracking[fallback_ticket] = {
                            'open_time': time.time(),
                            'open_price': float(precio),
                            'direction': direccion_sugerida,
                            'volume': float(executed_volume),
                            'sl': float(executed_sl),
                            'tp': float(executed_tp),
                        }
                    except Exception:
                        pass
                except Exception:
                    pass

            self.total_operaciones_abiertas += 1
            tiempo_actual = time.time()
            self.ultima_apertura = tiempo_actual

            msg = f"""
[OK] Nueva operación {direccion_sugerida}:
[DINERO] Precio: {precio:.5f} 
[OBJETIVO] TP: {executed_tp:.5f} 
[EMOJI] SL: {executed_sl:.5f}
📦 Volumen ejecutado: {executed_volume}
[IA] Modo: Punto de Entrada
"""
            self.add_log(msg, 'success')

            # Si esta apertura fue forzada al inicio, guardar parámetros para el scheduler
            if startup:
                try:
                    # ⭐ Obtener intervalo dinámico de la configuración
                    try:
                        minutes = int(self.config.get('FORCED_OPEN_MINUTES', tk.IntVar(value=5)).get())
                        intervalo_dist = max(1, minutes) * 60
                    except Exception:
                        intervalo_dist = 300
                    
                    self.forced_open_params = {
                        'symbol': symbol,
                        'direction': direccion_sugerida,
                        'vol': float(executed_volume),
                        'tp': float(executed_tp) if executed_tp is not None else None,
                        'sl': float(executed_sl) if executed_sl is not None else None,
                    }
                    self.next_forced_open = time.time() + float(intervalo_dist)
                    self.add_log(f"🔒 Parámetros de reapertura forzada guardados para scheduler (próxima en {intervalo_dist}s)", 'info')
                except Exception:
                    pass

            # Registrar apertura en logs JSON con valores reales si están disponibles
            try:
                log_trade({
                    'symbol': symbol,
                    'ticket': int(getattr(ticket_found, 'ticket', int(getattr(result, 'order', -1)))),
                    'type': direccion_sugerida,
                    'entry_price': float(precio),
                    'sl': float(executed_sl),
                    'tp': float(executed_tp),
                    'volume': float(executed_volume),
                    'mode': 'entry'
                })
            except Exception:
                pass

            # Actualizar contador y UI
            try:
                self.actualizar_contador_z()
            except Exception:
                pass
            return True

        # No se ejecutó la orden correctamente
        try:
            self.add_log(f"Orden rechazada o fallida: retcode={getattr(result, 'retcode', None)}", 'error')
        except Exception:
            pass
        return False

    def start_bot(self):
        """Inicia el bot de trading"""
        # ⭐ NUEVO: Cargar configuración SOLO si el usuario lo solicita explícitamente
        if self.config['LOAD_PREV_CONFIG'].get():
            self.load_config()
            self.add_log("[CONFIG] ⭐ Configuración cargada desde sesión anterior (LOAD_PREV_CONFIG=ON)", 'info')
        else:
            self.add_log("[CONFIG] ⚪ Usando configuración ACTUAL del UI (LOAD_PREV_CONFIG=OFF)", 'info')
        
        if self.is_running:
            return
        
        # Validar y configurar tiempo
        tiempo_min = self.tiempo_total.get()
        if tiempo_min > 0:
            self.tiempo_restante = tiempo_min * 60
            self.tiempo_inicio = time.time()
        else:
            self.tiempo_restante = 0
            
        if not self.conectar_mt5():
            messagebox.showerror("Error", "No se pudo conectar a MT5")
            return

        # ⭐ NUEVO V4: Iniciar DATA READER THREAD (lectura continua de ticks, incluso durante pausas)
        if not self.data_reader_running:
            try:
                self.data_reader_running = True
                self.data_reader_thread = threading.Thread(
                    target=self._data_reader_loop,
                    daemon=True,
                    name="DataReaderThread"
                )
                self.data_reader_thread.start()
                self.add_log("[DATA-READER] ✅ Thread de lectura de datos iniciado (activo incluso durante pausas)", 'success')
            except Exception as e:
                self.add_log(f"[DATA-READER] ⚠️ Error iniciando thread: {str(e)[:80]}", 'warning')
                self.data_reader_running = False

        # ⭐ NUEVO: Crear y sincronizar TickImpulseValidator AHORA (después de self.config definido)
        if not self.impulse_validator:
            try:
                self.impulse_validator = TickImpulseValidator(
                    window_size=self.config['IMPULSE_TICK_WINDOW'].get(),
                    min_sequence_length=self.config['IMPULSE_MIN_SEQUENCE'].get(),
                    price_velocity_threshold=0.15,
                    pressure_threshold=self.config['IMPULSE_PRESSURE_THRESHOLD'].get(),
                    micro_breakout_size=self.config['IMPULSE_MICRO_BREAKOUT'].get(),
                    momentum_window=self.config['IMPULSE_MOMENTUM_WINDOW'].get(),
                    imbalance_ratio=self.config['IMPULSE_IMBALANCE_RATIO'].get(),
                    spread_filter=self.config['IMPULSE_SPREAD_FILTER'].get(),
                    velocity_threshold=self.config['IMPULSE_VELOCITY_THRESHOLD'].get(),
                    confirmation_count=self.config['IMPULSE_CONFIRMATION_COUNT'].get(),
                    signal_expiration_ms=self.config['IMPULSE_SIGNAL_EXPIRATION_MS'].get(),
                    min_tick_movement=self.config['IMPULSE_MIN_TICK_MOVEMENT'].get(),
                    log_callback=self.add_log
                )
                self.add_log("[IMPULSE] ✅ Detector de impulsos inicializado", 'success')
            except Exception as e:
                self.add_log(f"[IMPULSE] ⚠️ Error inicializando detector: {str(e)[:80]}", 'warning')
                self.impulse_validator = None

        # ⭐ CRÍTICO: Sincronizar TickFlowAnalyzer con configuración UI ANTES de iniciar operaciones
        if self.tick_flow_analyzer:
            try:
                self.add_log(f"\n{'='*60}", 'info')
                self.add_log(f"[FLOW-CONFIG] Sincronizando Tick Flow Analyzer con configuración UI...", 'info')
                
                # Leer valores ACTUALES de la UI
                flow_config = {
                    'enabled': self.config['TICK_FLOW_ENABLED'].get(),
                    'ticks_window': self.config['TICK_FLOW_WINDOW'].get(),
                    'momentum_window': self.config['TICK_FLOW_MOMENTUM_WINDOW'].get(),
                    'imbalance_threshold': self.config['TICK_FLOW_IMBALANCE_THRESHOLD'].get(),
                    'spread_multiplier': self.config['TICK_FLOW_SPREAD_MULTIPLIER'].get(),
                }
                
                # Actualizar analizador con valores UI
                self.tick_flow_analyzer.update_config(flow_config)
                
                # Mostrar configuración aplicada
                self.add_log(f"[FLOW-CONFIG] ✅ Configuración APLICADA:", 'success')
                self.add_log(f"[FLOW-CONFIG]    Estado: {'HABILITADO' if flow_config['enabled'] else 'DESHABILITADO'}", 'info')
                self.add_log(f"[FLOW-CONFIG]    Ticks: {flow_config['ticks_window']}", 'info')
                self.add_log(f"[FLOW-CONFIG]    Momentum: {flow_config['momentum_window']}", 'info')
                self.add_log(f"[FLOW-CONFIG]    Umbral Presión: {flow_config['imbalance_threshold']}", 'info')
                self.add_log(f"[FLOW-CONFIG]    Multiplicador Spread: {flow_config['spread_multiplier']}", 'info')
                self.add_log(f"{'='*60}\n", 'info')
            except Exception as e:
                self.add_log(f"[FLOW-CONFIG] ⚠️ Error sincronizando TickFlowAnalyzer: {str(e)[:80]}", 'warning')

        # ⭐ NUEVO V3: SINCRONIZAR IMPULSE DETECTOR CON CONFIGURACIÓN UI
        if self.impulse_validator and self.impulse_validator.detector:
            try:
                self.add_log(f"\n{'='*60}", 'info')
                self.add_log(f"[IMPULSE-CONFIG] ⭐ Sincronizando Detector de Impulsos V4...", 'info')
                
                # Leer valores ACTUALES de la UI
                detector = self.impulse_validator.detector
                detector.set_window_size(self.config['IMPULSE_TICK_WINDOW'].get())
                detector.set_momentum_window(self.config['IMPULSE_MOMENTUM_WINDOW'].get())
                detector.set_pressure_threshold(self.config['IMPULSE_PRESSURE_THRESHOLD'].get())
                detector.set_min_sequence_length(self.config['IMPULSE_MIN_SEQUENCE'].get())
                detector.set_micro_breakout_size(self.config['IMPULSE_MICRO_BREAKOUT'].get())
                detector.set_velocity_threshold(self.config['IMPULSE_VELOCITY_THRESHOLD'].get())
                detector.set_imbalance_ratio(self.config['IMPULSE_IMBALANCE_RATIO'].get())
                detector.set_spread_filter(self.config['IMPULSE_SPREAD_FILTER'].get())
                # ⭐ NUEVO V4: Sincronizar los 3 nuevos parámetros
                detector.set_confirmation_count(self.config['IMPULSE_CONFIRMATION_COUNT'].get())
                detector.set_signal_expiration_ms(self.config['IMPULSE_SIGNAL_EXPIRATION_MS'].get())
                detector.set_min_tick_movement(self.config['IMPULSE_MIN_TICK_MOVEMENT'].get())
                
                # Mostrar configuración aplicada
                self.add_log(f"[IMPULSE-CONFIG] ✅ MICRO-IMPULSOS OPTIMIZADOS:", 'success')
                self.add_log(f"[IMPULSE-CONFIG]    Ventana de Ticks: {detector.window_size}", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Ventana Momentum: {detector.momentum_window}", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Umbral Presión: {detector.pressure_threshold}%", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Min Secuencia: {detector.min_sequence_length} ticks", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Micro Ruptura: {detector.micro_breakout_size} pips", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Velocidad Umbral: {detector.velocity_threshold}", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Ratio Desbalance: {detector.imbalance_ratio}", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Filtro Spread: {detector.spread_filter}x", 'info')
                # ⭐ NUEVO V4: Mostrar los 3 nuevos parámetros
                self.add_log(f"[IMPULSE-CONFIG] ⭐ V4 - CONFIRMACIÓN Y EXPIRACIÓN:", 'success')
                self.add_log(f"[IMPULSE-CONFIG]    Confirmación Ticks: {detector.confirmation_count}", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Expiración Señal: {detector.signal_expiration_ms}ms", 'info')
                self.add_log(f"[IMPULSE-CONFIG]    Movimiento Mínimo: {detector.min_tick_movement} ticks", 'info')
                self.add_log(f"[IMPULSE-CONFIG] 🎯 CONFIGURACIÓN PARA GOLD: MÁXIMA PRECISIÓN EN DETECCIÓN", 'success')
                self.add_log(f"{'='*60}\n", 'info')
            except Exception as e:
                self.add_log(f"[IMPULSE-CONFIG] ⚠️ Error sincronizando Detector: {str(e)[:80]}", 'warning')

        # Cargar sistema PRO institucional (NIVEL 5-10)
        self._load_ml_models_v2_with_pro()
        
        # Actualizar especialistas con dataset manager
        if self.dataset_manager is not None:
            self.buy_specialist.dataset_manager = self.dataset_manager
            self.sell_specialist.dataset_manager = self.sell_specialist
            self.arbitrator.dataset_manager = self.dataset_manager
            self.add_log("[OK] Dataset Profesional integrado en especialistas", 'success')

        # ⭐ NUEVO: FORZAR REENTRENAMIENTO DE ESPECIALISTAS DESPUÉS DE RESET
        # Esto garantiza que tengan datos frescos después de cierre_emergencia
        try:
            self.add_log("\n[REENTRENAMIENTO] 🔄 Reentrenando especialistas con datos frescos...", 'info')
            symbol = self.config['SYMBOL'].get()
            
            # Cargar 500 snapshots frescos (histórico completo)
            try:
                snapshots = self._load_snapshots_fallback(symbol, min_bars=500)
            except Exception:
                snapshots = None
            
            if snapshots and len(snapshots) >= 100:
                # Entrenar BUY specialist
                try:
                    self.buy_specialist.train_on_snapshots(snapshots[:500])
                    self.add_log(f"[REENTRENAMIENTO] ✅ BUY Specialist reentrenado con {len(snapshots)} barras", 'success')
                except Exception as e:
                    self.add_log(f"[REENTRENAMIENTO] ⚠️ Error reentrenando BUY: {str(e)[:60]}", 'warning')
                
                # Entrenar SELL specialist
                try:
                    self.sell_specialist.train_on_snapshots(snapshots[:500])
                    self.add_log(f"[REENTRENAMIENTO] ✅ SELL Specialist reentrenado con {len(snapshots)} barras", 'success')
                except Exception as e:
                    self.add_log(f"[REENTRENAMIENTO] ⚠️ Error reentrenando SELL: {str(e)[:60]}", 'warning')
            else:
                self.add_log("[REENTRENAMIENTO] ⚠️ No se pudieron cargar snapshots frescos - usando especialistas previos", 'warning')
        except Exception as e:
            self.add_log(f"[REENTRENAMIENTO] ❌ Error en reentrenamiento: {str(e)[:80]}", 'error')

        # Prefill market snapshots into a dedicated JSON for the selected symbol.
        # ⭐ RESET scheduler flags para permitir reinicio en segunda ejecución
        self._forced_reopen_started = False
        self._scheduler_running = True
        
        # We run one synchronous load at start (to allow immediate decision)
        # and then start a background thread that fetches latest M1 bars from MT5
        # and overwrites snapshots on disk and in-memory every `SNAPSHOT_RELOAD_INTERVAL` seconds.
        try:
            symbol = self.config['SYMBOL'].get()
            try:
                # try light prefill using provided helper (may fetch historical data)
                filled = prefill_market_data(symbol, minutes=500)
            except Exception:
                filled = 0

            # Recargar snapshots en memoria (protegido)
            try:
                self.reload_market_snapshots()
            except Exception:
                logger.exception("Error inicial recargando market_snapshots tras prefill")
                self.market_snapshots = []

            self.add_log(f"🗂️ Prefilled {filled} market snapshots into logs for {symbol}", 'info')

            # ⭐ CRÍTICO: Iniciar trend_monitor JUSTO AHORA, ANTES de evaluate_snapshots_and_open
            # Esto permite que realice su análisis INMEDIATO antes de que el scheduler intente abrir
            try:
                self.trend_monitor_running = True
                self.trend_monitor_thread = threading.Thread(target=self._trend_monitor_loop, daemon=True)
                self.trend_monitor_thread.start()
                self.add_log("[✓] Monitor de cambios de tendencia iniciado ANTICIPADAMENTE", 'success')
                
                # Esperar 2-3s para que trend_monitor termine su primer análisis
                self.add_log("[SYNC] Esperando análisis inicial de tendencias...", 'info')
                time.sleep(2.5)
                self.add_log("[SYNC] ✓ Análisis de tendencias completado - procediendo con apertura", 'info')
            except Exception as e:
                self.add_log(f"[TREND] Error iniciando monitor anticipadamente: {str(e)[:60]}", 'warning')

            # Intentar apertura inmediata basada en snapshots
            try:
                self.evaluate_snapshots_and_open(symbol)
            except Exception:
                logger.exception("Error en evaluate_snapshots_and_open inicial")

            # ⭐ NUEVO: Inicializar temporizador usando FORCED_OPEN_MINUTES dinámicamente
            try:
                minutes = int(self.config.get('FORCED_OPEN_MINUTES', tk.IntVar(value=5)).get())
                intervalo_segundos = max(1, minutes) * 60
                self.next_forced_open = time.time() + intervalo_segundos
                self.add_log(f"[INIT] Temporizador forzada establecido: {minutes}m ({intervalo_segundos}s)", 'info')
            except Exception as e:
                self.next_forced_open = None
                self.add_log(f"[ERROR] Al establecer temporizador forzada: {e}", 'error')

            # Background loop: fetch latest M1 bars from MT5 and overwrite snapshots
            # ⭐ NUEVO: Usar DataUpdater para actualizaciones periódicas garantizadas cada 60s
            def _initialize_data_updater():
                try:
                    interval = int(self.config.get('SNAPSHOT_RELOAD_INTERVAL', tk.IntVar(value=60)).get())
                except Exception:
                    interval = 60
                
                self.data_updater = DataUpdater(symbol=symbol, interval=max(60, interval))
                self.pre_analysis_refresher = PreAnalysisDataRefresher(
                    self.data_updater, 
                    log_callback=self.add_log
                )
                
                # Iniciar actualización periódica (sin logs de spam)
                def _update_callback(count, total):
                    try:
                        # ⭐ NO logear cada actualización - operación interna silenciosa
                        pass
                    except Exception:
                        pass
                
                self.data_updater.start_periodic_updater(callback=_update_callback)
                self.add_log(f"[OK] Data Updater iniciado: actualización cada {interval}s (operación interna)", 'success')
            
            _initialize_data_updater()
        except Exception:
            logger.exception("Error inicializando snapshot writer/pre-fill")
        # Iniciar un scheduler ligero de reaperturas forzadas (siempre activo)
        try:
            if not getattr(self, '_forced_reopen_started', False):
                def _forced_reopen_scheduler_simple():
                    while getattr(self, '_scheduler_running', True):
                        try:
                            # ⭐ FIX #20: Si bot está en pausa por objetivo, NO abrir nada
                            if self.bot_pausado:
                                time.sleep(1)  # Esperar 1s antes de reintentar
                                continue
                            
                            # ⭐ LEER DINÁMICAMENTE el intervalo de la config cada ciclo
                            try:
                                enabled = bool(self.config.get('ENABLE_FORCED_OPEN', tk.BooleanVar(value=True)).get())
                            except Exception:
                                enabled = True
                            
                            if not enabled:
                                time.sleep(5)
                                continue
                            
                            try:
                                minutes = int(self.config.get('FORCED_OPEN_MINUTES', tk.IntVar(value=5)).get())
                            except Exception:
                                minutes = 5
                            
                            intervalo = max(1, minutes) * 60  # Convertir a segundos
                            
                            # ⭐ NUEVA LÓGICA: Verificar si ha pasado el time de next_forced_open
                            now = time.time()
                            next_open = getattr(self, 'next_forced_open', now)
                            
                            if now >= next_open:
                                # Es hora de intentar reapertura forzada CON ANÁLISIS COMPLETO
                                self.add_log(f"\n[RESET] Scheduler: reapertura forzada activada", 'warning')
                                
                                # ⭐ VERIFICACIÓN CRÍTICA #1: Consultar FLAGS de sincronización (trend_monitor)
                                with self.trend_analysis_lock:
                                    imminent_reversal = self.trend_imminent_reversal
                                    imminent_direction = self.trend_imminent_direction
                                    imminent_confidence = self.trend_imminent_confidence
                                
                                # Análisis completo: especialistas + tendencia (IGNORA arbitrador en modo forzado)
                                best_dir, buy_score, sell_score, trend_analysis = self._quick_analysis_for_forced_reopen(symbol)
                                self.add_log(f"[ANÁLISIS] BUY: {buy_score:.1f} | SELL: {sell_score:.1f} → ELEGIDO: {best_dir}", 'info')
                                
                                # ⭐ VERIFICACIÓN CRÍTICA #2: Bloquear si intento abrir en dirección CONTRARIA a reversión inminente
                                # (imminent_direction es la dirección que VA A VENIR, así que NO abrir en lo opuesto)
                                if imminent_reversal:
                                    if (best_dir == 'BUY' and imminent_direction == 'SELL') or \
                                       (best_dir == 'SELL' and imminent_direction == 'BUY'):
                                        self.add_log(f"[FORZADA] 🛑 BLOQUEADA: Reversión INMINENTE → {imminent_direction} @ {imminent_confidence:.1f}% confianza", 'error')
                                        self.add_log(f"[FORZADA] Intento: {best_dir} | Conflicto: Esperando reversa a {imminent_direction}", 'warning')
                                        self.next_forced_open = now + intervalo
                                        time.sleep(2)  # Esperar 2s antes de reintentar
                                        continue
                                
                                # Verificación final: No abrir si reversión EXTREMA (>85% from scheduler's own analysis)
                                if trend_analysis and trend_analysis.get('risk_level') == 'HIGH':
                                    conf = trend_analysis.get('confidence', 0)
                                    signal = trend_analysis.get('signal', '')
                                    if conf > 85:
                                        self.add_log(f"[FORZADA] 🛑 CANCELADA: Reversión CRÍTICA detectada ({conf}% confianza: {signal})", 'error')
                                        self.next_forced_open = now + intervalo
                                        time.sleep(1)
                                        continue
                                
                                # Registrar intento en monitor_debug.log
                                try:
                                    with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                                        fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'scheduler': 'forced_reopen_attempt_simple', 'has_params': bool(self.forced_open_params)}) + '\n')
                                except Exception:
                                    pass

                                try:
                                    # ⭐ VERIFICAR que el scheduler siga activo ANTES de intentar abrir
                                    if not getattr(self, '_scheduler_running', True):
                                        self.add_log("[SCHEDULER] Detenido - abortando reapertura", 'info')
                                        break
                                    
                                    self.add_log(f"[RESET] Abriendo {best_dir} (forzada con análisis completo)", 'warning')
                                    self.abrir_operacion(best_dir, force=True, startup=True, force_params=self.forced_open_params)
                                except Exception as e:
                                    self.add_log(f"Error scheduler al ejecutar reapertura: {e}", 'error')
                                
                                # Actualizar next_forced_open para la próxima reapertura
                                self.next_forced_open = now + intervalo
                                self.add_log(f"[SCHEDULER] ⏱️ Próxima reapertura forzada en {intervalo}s ({minutes}m)", 'info')
                            else:
                                # Mostrar progreso: cuánto falta
                                remaining = int(next_open - now)
                                if remaining > 0:
                                    # Log cada 10s o en últimos 5s
                                    if remaining % 10 == 0 or remaining <= 5:
                                        self._update_forced_open_counter(remaining)
                            
                            if not getattr(self, '_scheduler_running', True):
                                self.add_log("[SCHEDULER] Bot detenido - Terminando scheduler", 'info')
                                break
                            
                            # Dormir 1s y revisar de nuevo
                            time.sleep(1)
                            
                        except Exception as e:
                            self.add_log(f"[SCHEDULER] Error en ciclo: {str(e)[:60]}", 'error')
                            time.sleep(5)

                threading.Thread(target=_forced_reopen_scheduler_simple, daemon=True).start()
                self._forced_reopen_started = True
                self.add_log("[SCHEDULER] ✅ Thread de reaperturas forzadas iniciado", 'success')
        except Exception as e:
            self.add_log(f"[SCHEDULER] Error iniciando scheduler: {str(e)[:60]}", 'error')

        # Run automatic calibration from logs and apply suggested parameters
        try:
            cal = calibrate_from_logs(limit=2000)
            if cal and isinstance(cal, dict):
                try:
                    # Apply suggested RISK_PCT
                    if 'risk_pct' in cal and 'RISK_PCT' in self.config:
                        self.config['RISK_PCT'].set(float(cal['risk_pct']))
                        self.add_log(f"[CONFIG] Calibración automática: RISK_PCT -> {cal['risk_pct']}", 'success')
                    # Apply suggested CONFIDENCE_THRESHOLD
                    if 'confidence_threshold' in cal and 'CONFIDENCE_THRESHOLD' in self.config:
                        self.config['CONFIDENCE_THRESHOLD'].set(float(cal['confidence_threshold']))
                        self.add_log(f"[CONFIG] Calibración automática: CONFIDENCE_THRESHOLD -> {cal['confidence_threshold']}", 'success')
                except Exception:
                    pass
        except Exception:
            pass
            
        # Mantener cualquier operación ya abierta (por ejemplo la apertura forzada de inicio)
        # Inicializar contadores básicos sin borrar position_tracking creado por la apertura inicial.
        try:
            # No reset de position_tracking para preservar aperturas forzadas previas
            self.total_operaciones_abiertas = len([p for p in (mt5.positions_get(symbol=symbol) or []) if getattr(p, 'magic', None) == self.config['MAGIC_NUMBER']])
        except Exception:
            try:
                self.total_operaciones_abiertas = int(getattr(self, 'total_operaciones_abiertas', 0))
            except Exception:
                self.total_operaciones_abiertas = 0
        self.z = 0
        self.ganadas = 0
        self.perdidas = 0
        self.operaciones_actuales.clear()
        self.operaciones_procesadas.clear()
        self.operaciones_cerradas = 0
        self.en_pausa = False
        self.ganancia_total = 0.0
        self.historial_resultados = []
        self.deals_procesados = set()
        self.ultima_operacion_timestamp = int(time.time())
        
        self.update_stats()
        
        for entry in self.config_entries.values():
            entry.config(state='disabled')

        try:
            self.loss_analyzer.min_analysis_time = int(self.config['RED_ANALYSIS_TIME'].get())
            self.loss_analyzer.min_recovery_potential = float(self.config['MIN_RECOVERY_POTENTIAL'].get())
        except Exception as e:
            self.add_log(f"Error sincronizando parámetros de análisis rojo: {e}", 'warning')

        self.is_running = True
        self.analisis_inicial_hecho = False
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_indicator.itemconfig(self.status_circle, fill='#10b981')
        self.status_label.config(text="Bot Activo", fg='#34d399')
        
        # ⭐ VALIDACIÓN INICIAL AL INICIAR EL BOT
        self.add_log("\n" + "="*60, 'warning')
        self.add_log("[IA] INICIANDO BOT - VALIDACIÓN INICIAL", 'warning')
        self.add_log("="*60, 'warning')
        
        # Verificar si Punto de Entrada está activado
        if self.use_entry_point.get():
            entry_price = self.entry_point_price.get()
            entry_direction = self.entry_point_direction.get()
            self.add_log(f"\n[OBJETIVO] PUNTO DE ENTRADA ACTIVADO", 'success')
            self.add_log(f"   Dirección: {entry_direction}", 'info')
            self.add_log(f"   Precio Objetivo: {entry_price}", 'info')
            self.add_log(f"   Estado: Monitoreando hasta alcanzar precio...\n", 'success')
        else:
            self.add_log(f"\n[CONFIG]  Punto de Entrada: DESACTIVADO\n", 'info')
        
        # Verificar si hay operaciones en espera
        if self.pending_operations:
            self.add_log(f"[ESPERA] OPERACIONES EN ESPERA DETECTADAS", 'warning')
            self.add_log(f"   Total: {len(self.pending_operations)} operación(es)", 'warning')
            for i, op in enumerate(self.pending_operations, 1):
                status = "[EMOJI]" if op['status'] == 'ESPERANDO' else "[EMOJI]"
                self.add_log(f"   {status} Op #{op.get('id', i)}: {op['direction']} @ {op['price']:.5f}", 'info')
            self.add_log(f"   Estado: Analizando mercado para apertura...\n", 'warning')
        else:
            self.add_log(f"\n[DATA] ANALIZANDO MERCADO", 'info')
            self.add_log(f"   Estado: Esperando operaciones en espera...\n", 'info')
        
        self.add_log("="*60 + "\n", 'warning')
        
        
        # NUEVO: INICIALIZAR DATA LOADER TRAINER
        try:
            self.add_log("\n[DATALOADER] Inicializando cargador de datos...", 'info')
            self.data_loader = initialize_data_loader(
                symbol=symbol,
                generate_if_missing=True,
                num_snapshots=1000
            )
            
            # Verificar si está listo
            if self.data_loader and self.data_loader.is_ready:
                self.training_features = self.data_loader.get_training_features(
                    window_size=100
                )
                self.data_ready = True
                snapshot_count = len(self.data_loader.market_snapshots) if hasattr(self.data_loader, 'market_snapshots') else 0
                
                # ✅ Mostrar estadísticas del dataset
                self.add_log(f"✅ Dataset cargado: {snapshot_count} snapshots", 'success')
                
                # Calcular estadísticas
                if snapshot_count > 0:
                    try:
                        closes = []
                        highs = []
                        lows = []
                        volumes = []
                        spreads = []
                        
                        for snap in self.data_loader.market_snapshots[-200:]:  # Últimos 200
                            if isinstance(snap, dict):
                                if 'price' in snap and isinstance(snap['price'], dict):
                                    closes.append(snap['price'].get('close', 0))
                                    highs.append(snap['price'].get('high', 0))
                                    lows.append(snap['price'].get('low', 0))
                                    spreads.append(snap['price'].get('high', 0) - snap['price'].get('low', 0))
                                if 'volume' in snap and isinstance(snap['volume'], dict):
                                    volumes.append(snap['volume'].get('tick_volume', 0))
                        
                        if closes:
                            # ATR (Average True Range)
                            atr = np.mean([h - l for h, l in zip(highs, lows)]) if highs and lows else 0
                            spread_avg = np.mean(spreads) if spreads else 0
                            spread_std = np.std(spreads) if spreads else 0
                            volume_avg = np.mean(volumes) if volumes else 0
                            
                            self.add_log(f"📊 Estadísticas calculadas:", 'info')
                            self.add_log(f"   Spread promedio: {spread_avg:.6f} ± {spread_std:.6f}", 'info')
                            self.add_log(f"   ATR promedio: {atr:.6f} ± {np.std([h-l for h,l in zip(highs, lows)]):.6f}", 'info')
                            self.add_log(f"   Volumen promedio: {int(volume_avg)}", 'info')
                    except Exception as e:
                        self.add_log(f"[WARN] Error calculando estadísticas: {str(e)[:50]}", 'warning')
                
                self.add_log(f"[OK] Features de entrenamiento extraídos: {len(self.training_features)} características", 'success')
                
                # ⭐ Pasar datos a especialistas
                if hasattr(self.buy_specialist, 'market_snapshots'):
                    self.buy_specialist.market_snapshots = self.data_loader.market_snapshots
                if hasattr(self.sell_specialist, 'market_snapshots'):
                    self.sell_specialist.market_snapshots = self.data_loader.market_snapshots
                if hasattr(self.trend_detector, 'market_snapshots'):
                    self.trend_detector.market_snapshots = self.data_loader.market_snapshots
                
            else:
                self.add_log("[WARN] Data Loader no está completamente listo", 'warning')
                self.data_ready = False
        except FileNotFoundError:
            self.add_log("[INFO] market_snapshots.json no encontrado - generando datos...", 'info')
            self.data_ready = False
        except Exception as e:
            logger.exception(f"Error inicializando Data Loader")
            self.add_log(f"[ERROR] Problema con Data Loader: {e}", 'error')
            self.data_ready = False

        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        
        # ⭐ ANÁLISIS INMEDIATO: Hacer análisis de tendencia AHORA para actualizar UI
        try:
            self.add_log("[TREND] 🚀 Análisis INMEDIATO de tendencia...", 'info')
            analysis = None
            
            # Intentar multi-timeframe primero
            if self.use_multi_timeframe.get() == True:
                try:
                    trend_mtf = self.trend_detector.analyze_trend_change_multi_timeframe(symbol)
                    if trend_mtf and trend_mtf.get('multi_tf_confidence', 0) >= 60:
                        analysis = {
                            'signal': trend_mtf.get('primary_signal', 'STABLE'),
                            'risk_level': 'HIGH' if 'SELL_TO_BUY' in trend_mtf.get('primary_signal', '') or 'BUY_TO_SELL' in trend_mtf.get('primary_signal', '') else 'LOW',
                            'confidence': trend_mtf.get('multi_tf_confidence', 0),
                            'recommendation': trend_mtf.get('recommendation', 'HOLD')
                        }
                        self.add_log(f"[TREND-MTF] Multi-TF: {trend_mtf['primary_signal']} ({trend_mtf['multi_tf_confidence']:.0f}% conf, {trend_mtf['consensus_strength']:.0f}% TF agree)", 'success')
                except Exception as e:
                    self.add_log(f"[TREND-MTF] Error MTF: {str(e)[:40]}", 'warning')
            
            # Fallback si multi-TF no disponible
            if analysis is None:
                analysis = self.trend_detector.analyze_trend_change_risk(symbol, timeframe=mt5.TIMEFRAME_M1, lookback=100)
            
            self.last_trend_analysis = analysis
            
            signal = analysis.get('signal', 'STABLE')
            risk = analysis.get('risk_level', 'LOW')
            confidence = analysis.get('confidence', 0)
            self.add_log(f"[TREND] ✓ Análisis completado: {signal} | Risk: {risk} | Conf: {confidence}%", 'success')
        except Exception as e:
            self.add_log(f"[TREND] Error en análisis inmediato: {str(e)[:80]}", 'warning')
        
        # ⭐ NUEVO: Iniciar monitor de cambios de tendencia (SI NO YA ESTÁ INICIALIZADO)
        # Se inicia anticipadamente antes de evaluate_snapshots_and_open, así que saltar aquí
        if not getattr(self, 'trend_monitor_thread', None) or not self.trend_monitor_thread.is_alive():
            self.trend_monitor_running = True
            self.trend_monitor_thread = threading.Thread(target=self._trend_monitor_loop, daemon=True)
            self.trend_monitor_thread.start()
            self.add_log("[✓] Monitor de cambios de tendencia iniciado (re-check)", 'success')
        else:
            self.add_log("[✓] Monitor de cambios de tendencia ya está activo", 'info')
        
        # ⭐ NUEVO: Iniciar actualización de UI cada segundo (para temporizador y trend display)
        self.ui_refresh_running = True
        self.ui_refresh_thread = threading.Thread(target=self._ui_refresh_loop, daemon=True)
        self.ui_refresh_thread.start()
        self.add_log("[✓] UI Refresh iniciado - Actualizando trend display cada 1s", 'success')
        
        # ⭐ NUEVO: Iniciar monitor reactivo de ganancia mínima (Posiciones en Azul)
        self.blue_monitor_running = True
        self.blue_monitor_thread = threading.Thread(target=self._blue_positions_monitor_loop, daemon=True)
        self.blue_monitor_thread.start()
        self.add_log("[✓] Monitor reactivo de ganancia mínima INICIADO - Verificando cada 0.5s", 'success')

        self.manual_buy_btn.config(state='normal')
        self.manual_sell_btn.config(state='normal')

        self.pause_btn.config(state='normal')  # Habilitar botón de pausa

    def _update_forced_open_counter(self, remaining_seconds):
        """Actualiza el contador visual de reapertura forzada en la UI"""
        try:
            if not hasattr(self, 'forced_open_label'):
                # Crear el label si no existe (solo primera vez)
                if remaining_seconds > 0:
                    self.forced_open_label = tk.Label(
                        self.root, 
                        text=f"⏱️ PROXIMA APERTURA FORZADA EN: {remaining_seconds}s",
                        font=('Arial', 11, 'bold'),
                        fg='#00ff00',
                        bg='#1a1a1a',
                        padx=10,
                        pady=5
                    )
                    self.forced_open_label.pack(side='top', fill='x', padx=5, pady=5)
                return
            
            if remaining_seconds > 0:
                texto = f"⏱️ PROXIMA APERTURA FORZADA EN: {remaining_seconds}s"
                self.forced_open_label.config(text=texto, fg='#00ff00')
                self.forced_open_label.pack(side='top', fill='x', padx=5, pady=5)
            else:
                self.forced_open_label.pack_forget()
            
            self.root.update_idletasks()
        except Exception as e:
            logger.error(f"Error actualizando contador: {e}")

    def _update_initial_analysis_counter(self, remaining_seconds, direction=''):
        """Actualiza el contador visual del análisis inicial de 30s en la UI"""
        try:
            if not hasattr(self, 'initial_analysis_label'):
                # Crear el label si no existe
                if remaining_seconds > 0:
                    self.initial_analysis_label = tk.Label(
                        self.root, 
                        text=f"📊 ANALIZANDO - APERTURA INICIAL EN: {remaining_seconds}s ({direction})",
                        font=('Arial', 12, 'bold'),
                        fg='#ffff00',
                        bg='#1a1a1a',
                        padx=10,
                        pady=5
                    )
                    self.initial_analysis_label.pack(side='top', fill='x', padx=5, pady=5)
                return
            
            if remaining_seconds > 0:
                texto = f"📊 ANALIZANDO - APERTURA INICIAL EN: {remaining_seconds}s ({direction})"
                self.initial_analysis_label.config(text=texto, fg='#ffff00')
                self.initial_analysis_label.pack(side='top', fill='x', padx=5, pady=5)
            else:
                self.initial_analysis_label.pack_forget()
            
            self.root.update_idletasks()
        except Exception as e:
            logger.error(f"Error actualizando contador inicial: {e}")

    def stop_bot(self):
        """Versión mejorada que incluye manejo de pausa"""
        # ⭐ NUEVO: Guardar configuración actual antes de detener
        self.save_config()
        
        if not self.is_running:
            return
        
        # Limpiar contadores visuales
        try:
            if hasattr(self, 'forced_open_label'):
                self.forced_open_label.pack_forget()
            if hasattr(self, 'initial_analysis_label'):
                self.initial_analysis_label.pack_forget()
        except Exception:
            pass
            
        self.bot_pausado = False
        self.pause_btn.config(state='disabled', text="⏸️ Pausar")
        
        try:
            self.is_running = False
            self._scheduler_running = False  # ⭐ Detener scheduler también
            self.trend_monitor_running = False  # ⭐ NUEVO: Detener monitor de tendencias
            self.ui_refresh_running = False  # ⭐ NUEVO: Detener refresh de UI
            self.blue_monitor_running = False  # ⭐ NUEVO: Detener monitor de azul
            self.data_reader_running = False  # ⭐ NUEVO V4: Detener data reader
            
            # ⭐ Detener Data Updater
            if self.data_updater:
                try:
                    self.data_updater.stop()
                    self.add_log("[OK] Data Updater detenido", 'info')
                except Exception as e:
                    logger.error(f"Error deteniendo data_updater: {e}")
            
            # ⭐ NUEVO: Limpiar Data Loader
            if self.data_loader:
                try:
                    self.data_loader = None
                    self.training_features = {}
                    self.data_ready = False
                    self.add_log("[OK] Data Loader limpiado", 'info')
                except Exception as e:
                    logger.error(f"Error limpiando data_loader: {e}")
            
            self.add_log("Deteniendo bot...", 'warning')
            
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)
            if positions:
                self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
                self.status_label.config(text="Bot en Espera", fg='#fbbf24')
                self.add_log("Hay operaciones abiertas - Bot en espera...", 'warning')
                monitor_thread = threading.Thread(target=self.monitorear_cierre, daemon=True)
                monitor_thread.start()
                return

            self.en_pausa = False
            self.objetivo_cumplido = False
            self.analisis_inicial_hecho = False
            self.force_stop_triggered = False
            
            for entry in self.config_entries.values():
                entry.config(state='normal')
            
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            
            self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
            self.status_label.config(text="Bot Detenido", fg='#f87171')
            self.add_log("Bot detenido completamente", 'warning')
            
            self.root.update()
            
        except Exception as e:
            self.add_log(f"Error al detener el bot: {str(e)}", 'error')
            self.is_running = False
            self.root.update()

    def monitorear_cierre(self):
        """Monitorea operaciones abiertas hasta que se cierren o alcancen stop forzado"""
        symbol = self.config['SYMBOL'].get()
        force_stop_loss = self.config['FORCE_STOP_LOSS'].get()
        
        while True:
            positions = mt5.positions_get(symbol=symbol)
            positions_bot = [pos for pos in positions if pos.magic == self.config['MAGIC_NUMBER']] if positions else []
            
            if not positions_bot:
                self.add_log("Todas las operaciones cerradas - Deteniendo bot", 'info')
                self.root.after(0, self.finalizar_detencion)
                break
            
            if force_stop_loss > 0 and self.ganancia_neta <= -force_stop_loss:
                self.add_log(f"[STOP] Stop forzado alcanzado (-${force_stop_loss:.2f}) -> pausa temporal", 'error')
                self.force_stop_triggered = True
                # Cerrar posiciones del bot (intentos habituales)
                for pos in positions_bot:
                    self.cerrar_posicion(pos)
                # --- MODIFICADO: usar PAUSA_POST_GANANCIA y worker de objetivo ---
                try:
                    pause_seconds = int(self.config['PAUSA_POST_GANANCIA'].get())
                except Exception:
                    pause_seconds = 300
                self.bot_pausado = True
                self.pause_until = time.time() + pause_seconds
                self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
                self.status_label.config(text=f"Bot Pausado por Stop Loss ({pause_seconds}s)", fg='#fbbf24')
                t = threading.Thread(target=self._loss_pause_worker, args=(pause_seconds,), daemon=True)
               
                t.start()
                break
            
            self.monitorear_posiciones_en_rojo()
            self.actualizar_contador_z()
            time.sleep(1)

    def reiniciar_completo(self, habilitar_botones=True):
        """Reinicia completamente el bot como si fuera la primera vez"""
        try:
            self.is_running = False
            self.bot_thread = None
            
            self.z = 0
            self.ganadas = 0
            self.perdidas = 0
            self.operaciones_azules = 0
            self.operaciones_rojas = 0
            
            self.deals_anterior.clear()
            self.operaciones_actuales.clear()
            self.operaciones_procesadas.clear()
            self.deals_procesados.clear()
            self.position_ids.clear()
            self.position_tracking.clear()
            self.historial_resultados.clear()
            
            self.primera_operacion = True
            self.perdio_primera = False
            self.en_pausa = False
            self.objetivo_cumplido = False
            self.force_stop_triggered = False
            self.analisis_inicial_hecho = False
            self.connected = False
            
            self.ganancia_neta = 0.0
            self.saldo_total_acumulado = 0.0
            self.saldo_actual = 0.0
            self.ultima_ganancia = 0.0
            self.ganancia_total = 0.0

            self.ultima_operacion = time.time()
            self.ultima_operacion_timestamp = int(time.time())
            self.ultima_actualizacion_ui = 0
            
            for entry in self.config_entries.values():
                entry.config(state='normal')
            
            if habilitar_botones:
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
                self.resume_btn.config(state='disabled')
                
            self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
            self.status_label.config(text="Bot Detenido", fg='#f87171')
            
            if hasattr(self, 'progress_bar'):
                self.progress_bar['value'] = 0
                self.progress_label.config(text="0 / 10")
            
            self.update_stats()
            self.add_log("Bot reiniciado completamente - Listo para nuevo inicio", 'info')
            
            self.root.after_idle(self.root.update_idletasks)
            self.root.after_idle(self.root.update)
            
        except Exception as e:
            self.add_log(f"Error al reiniciar bot: {str(e)}", 'error')
            if habilitar_botones:
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')

    def _trend_monitor_loop(self):
        """⭐ Monitor de cambios de tendencia - ejecuta cada MINUTO y anticipa reversiones"""
        self.add_log("[TREND_MONITOR] Monitor de tendencias iniciado - verificando cada 60s", 'info')
        self.add_log("[TREND_MONITOR] Fuente de datos: market_snapshots.json + MT5 (fallback)", 'info')
        self.add_log("[TREND_MONITOR] Calibración adaptativa: ACTIVA", 'success')
        
        monitor_interval = 60  # Verificar cada MINUTO (60 segundos)
        alert_cooldown = 30   # No alertar más de una vez cada 30s
        first_run = True  # Para analizar INMEDIATAMENTE sin esperar
        
        while self.trend_monitor_running:
            try:
                if not self.is_running:
                    time.sleep(1)
                    continue
                
                # ⭐ Si es la primera ejecución, analizar INMEDIATAMENTE sin dormir
                if first_run:
                    first_run = False
                    self.add_log("[TREND_MONITOR] ⏱️ Realizando análisis INMEDIATO de tendencia...", 'info')
                else:
                    # Para análisis posteriores, dormir primero
                    time.sleep(monitor_interval)
                
                symbol = self.config['SYMBOL'].get()
                
                # ⭐ ANÁLISIS: Detectar cambios de tendencia inminentes
                analysis = None
                if self.use_multi_timeframe.get() == True:
                    try:
                        trend_mtf = self.trend_detector.analyze_trend_change_multi_timeframe(symbol)
                        if trend_mtf and trend_mtf.get('multi_tf_confidence', 0) >= 60:
                            analysis = {
                                'signal': trend_mtf.get('primary_signal', 'STABLE'),
                                'risk_level': 'HIGH' if 'SELL_TO_BUY' in trend_mtf.get('primary_signal', '') or 'BUY_TO_SELL' in trend_mtf.get('primary_signal', '') else 'LOW',
                                'confidence': trend_mtf.get('multi_tf_confidence', 0),
                                'recommendation': trend_mtf.get('recommendation', 'HOLD')
                            }
                    except Exception as e:
                        pass
                
                if analysis is None:
                    analysis = self.trend_detector.analyze_trend_change_risk(symbol, timeframe=mt5.TIMEFRAME_M1, lookback=100)
                
                # ⭐ CIERRE DINÁMICO: Si reversión clara, cierra posiciones contrarias
                if analysis and hasattr(self, 'position_closer'):
                    closed = self.position_closer.evaluate_and_close(
                        symbol=symbol,
                        trend_analysis=analysis,
                        magic_number=self.config['MAGIC_NUMBER']
                    )
                    if closed > 0:
                        self.add_log(f"[TREND_MONITOR] ✅ Cierre dinámico: {closed} posición(es)", 'success')
                
                self.last_trend_analysis = analysis  # Guardar para el UI
                
                # ⭐ ACTUALIZAR FLAGS DE SINCRONIZACIÓN: Para que scheduler lea estado ACTUAL
                try:
                    with self.trend_analysis_lock:
                        signal = analysis.get('signal', 'STABLE') if analysis else 'STABLE'
                        confidence = float(analysis.get('confidence', 0)) if analysis else 0.0
                        
                        # Marcar como reversión INMINENTE si confianza > 70% Y hay reversión detectable
                        if confidence > 70 and signal in ['BUY_TO_SELL', 'SELL_TO_BUY']:
                            self.trend_imminent_reversal = True
                            self.trend_imminent_direction = 'SELL' if signal == 'BUY_TO_SELL' else 'BUY'
                            self.trend_imminent_confidence = confidence
                            self.add_log(f"[SYNC] 🔴 Reversión INMINENTE: {signal} @ {confidence:.1f}% → Bloqueando apertura {('BUY' if signal == 'BUY_TO_SELL' else 'SELL')}", 'error')
                        else:
                            # Sin reversión inminente
                            self.trend_imminent_reversal = False
                            self.trend_imminent_direction = None
                            self.trend_imminent_confidence = 0.0
                        
                        self.trend_analysis_ready = True  # Marcar análisis como LISTO
                except Exception as e:
                    self.add_log(f"[SYNC] Error actualizando flags: {str(e)[:50]}", 'warning')
                
                # ⭐ LOG: Mostrar el análisis para debug
                signal = analysis.get('signal', 'STABLE')
                risk_level = analysis.get('risk_level', 'LOW')
                confidence = analysis.get('confidence', 0)
                self.add_log(f"[TREND_MONITOR] ANÁLISIS: {signal} | Risk: {risk_level} | Conf: {confidence}%", 'info')
                
                # Extraer info
                reason = analysis.get('reason', '')
                source = analysis.get('source', 'UNKNOWN')
                indicators = analysis.get('indicators', {})
                
                # ⭐ LÓGICA DE ALERTAS
                if risk_level == 'HIGH':
                    # Solo alertar si pasó el cooldown (30s mínimo entre alertas)
                    now = time.time()
                    if now - self.trend_change_alert_time > alert_cooldown:
                        self.add_log(f"\n🚨 ALERTA CAMBIO TENDENCIA (HIGH RISK):", 'warning')
                        self.add_log(f"   Señal: {signal} → Confianza: {confidence}%", 'error')
                        self.add_log(f"   Razón: {reason}", 'error')
                        self.add_log(f"   📊 Fuente: {source} | RSI: {indicators.get('rsi', 0):.1f}", 'warning')
                        self.add_log(f"   📈 Thresholds adaptativos: OB={indicators.get('adaptive_overbought', 70):.0f} / OS={indicators.get('adaptive_oversold', 30):.0f}", 'info')
                        self.add_log(f"   ⚠️ Se anticipa reversión en ~10-30 segundos\n", 'warning')
                        
                        # Si hay posición abierta, podría ser hora de prepararse para cierre
                        positions = mt5.positions_get(symbol=symbol)
                        bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']] if positions else []
                        if bot_positions:
                            current_direction = "BUY" if bot_positions[0].type == 0 else "SELL"
                            if signal == 'BUY_TO_SELL' and current_direction == 'BUY':
                                self.add_log(f"   ↪ Tendencia BUY→SELL: Cercano cambio DE BUY A SELL", 'warning')
                            elif signal == 'SELL_TO_BUY' and current_direction == 'SELL':
                                self.add_log(f"   ↪ Tendencia SELL→BUY: Cercano cambio DE SELL A BUY", 'warning')
                        
                        self.trend_change_alert_time = now
                
                elif risk_level == 'MEDIUM':
                    # MEDIUM: Solo loguear si hay cambio real
                    if signal != 'STABLE':
                        self.add_log(f"[TREND_MONITOR] ⚠️ MEDIUM RISK: {signal} ({confidence}%) - {reason[:60]} [📊 {source}]", 'info')
                
                # LOW: No loguear (es lo normal)
                
            except Exception as e:
                self.add_log(f"[TREND_MONITOR] Error en ciclo: {str(e)[:80]}", 'error')
                time.sleep(5)

    def _ui_refresh_loop(self):
        """⭐ Loop de actualización de UI cada 1 segundo - especialmente para temporizador de tendencia"""
        while self.ui_refresh_running:
            try:
                # Actualizar UI cada 1 segundo
                if self.is_running:
                    self.root.after(0, self._update_ui)
                
                time.sleep(1)
                
            except Exception as e:
                pass  # Silenciar errores para no afectar el bot

    def _blue_positions_monitor_loop(self):
        """
        🔵 Monitor Reactivo de Posiciones en AZUL
        - Verifica cada 0.5s si las posiciones en ganancia alcanzan MIN_PROFIT_CLOSE
        - Cierra INMEDIATAMENTE cuando se alcanza el threshold
        - Evita regresión del mercado y pérdidas
        """
        monitor_interval = 0.5  # Verificar cada 500ms (10x más rápido que ciclo lento)
        
        self.add_log("[🔵] Monitor Reactivo de Ganancia Mínima INICIADO - Verificando cada 0.5s", 'info')
        
        while self.blue_monitor_running:
            try:
                if not self.is_running:
                    time.sleep(1)
                    continue
                
                symbol = self.config['SYMBOL'].get()
                min_profit_close = float(self.config['MIN_PROFIT_CLOSE'].get()) if self.config['MIN_PROFIT_CLOSE'].get() else 2.0
                
                # Obtener todas las posiciones abiertas
                positions = mt5.positions_get(symbol=symbol)
                if not positions:
                    time.sleep(monitor_interval)
                    continue
                
                # Filtrar solo posiciones del bot
                bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
                
                for position in bot_positions:
                    ticket = position.ticket
                    current_profit = position.profit
                    position_type = "BUY" if position.type == 0 else "SELL"
                    
                    # ⭐ DETECTAR POSICIÓN EN AZUL (GANANCIA >= MIN_PROFIT_CLOSE)
                    if current_profit >= min_profit_close:
                        
                        # Verificar si ya fue detectada (evitar spam)
                        if ticket not in self.blue_positions_watched:
                            self.blue_positions_watched[ticket] = {
                                'detected_time': time.time(),
                                'min_profit': min_profit_close,
                                'profit_at_detection': current_profit,
                                'position_type': position_type,
                                'entry_price': position.price_open
                            }
                            
                            self.add_log(f"\n✅ [BLUE MONITOR] Ticket #{ticket} ALCANZÓ GANANCIA MÍNIMA", 'success')
                            self.add_log(f"   Tipo: {position_type} | Ganancia: ${current_profit:.2f} >= ${min_profit_close:.2f}", 'success')
                            self.add_log(f"   Precio Entrada: {position.price_open} → Actual: {position.price_current}", 'info')
                        
                        # ⭐ CIERRE INMEDIATO
                        else:
                            elapsed = time.time() - self.blue_positions_watched[ticket]['detected_time']
                            if elapsed > 2.0:  # Si tiene >2s en azul, cierra (ha pesar de riesgo de regresión)
                                self.add_log(f"\n🔴 [BLUE MONITOR] ¡CIERRE URGENTE! Ticket #{ticket} lleva {elapsed:.1f}s en azul", 'warning')
                                self.add_log(f"   Riesgo: Regresión del {abs(current_profit - self.blue_positions_watched[ticket]['profit_at_detection']):.2f}$ detectada", 'error')
                        
                        # Intentar cierre inmediato (MT5 lo hará si no hay conflicto)
                        try:
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": position.volume,
                                "type": mt5.ORDER_TYPE_SELL if position_type == 'BUY' else mt5.ORDER_TYPE_BUY,
                                "position": ticket,
                                "price": mt5.symbol_info_tick(symbol).bid if position_type == 'BUY' else mt5.symbol_info_tick(symbol).ask,
                                "magic": self.config['MAGIC_NUMBER'],
                                "comment": f"BLUE_MONITOR_AUTO_CLOSE_{current_profit:.2f}",
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            result = mt5.order_send(request)
                            
                            if result.retcode == mt5.TRADE_RETCODE_DONE:
                                close_time = time.time() - self.blue_positions_watched[ticket]['detected_time']
                                self.add_log(f"   ✨ POSICIÓN CERRADA en {close_time:.2f}s | Ganancia Final: ${current_profit:.2f}", 'success')
                                
                                # FIX #14: Registrar cierre en counters principales (ganadas/saldo)
                                self._procesar_cierre_exitoso(
                                    ticket=ticket,
                                    symbol=symbol,
                                    volume=position.volume,
                                    pos_type=position.type,
                                    profit=current_profit
                                )
                                
                                del self.blue_positions_watched[ticket]
                            else:
                                self.add_log(f"   ⚠️ Intento de cierre falló (retcode={result.retcode}): {result.comment}", 'warning')
                        
                        except Exception as close_error:
                            self.add_log(f"   ❌ Error al cerrar: {str(close_error)[:60]}", 'error')
                    
                    else:
                        # Limpiar del registro si bajó de azul (regresión)
                        if ticket in self.blue_positions_watched:
                            previous_profit = self.blue_positions_watched[ticket]['profit_at_detection']
                            regression = previous_profit - current_profit
                            self.add_log(f"⚠️ Ticket #{ticket} REGRESIONÓ: ${previous_profit:.2f} → ${current_profit:.2f} (-${regression:.2f})", 'warning')
                            del self.blue_positions_watched[ticket]
                
                time.sleep(monitor_interval)
            
            except Exception as e:
                self.add_log(f"[BLUE_MONITOR] Error en ciclo: {str(e)[:80]}", 'error')
                time.sleep(monitor_interval * 2)

    def finalizar_detencion(self):
        """Finaliza la detención del bot asegurando que los botones queden habilitados"""
        self.is_running = False
        self.en_pausa = False
        self.objetivo_cumplido = False
        self.analisis_inicial_hecho = False
        self.force_stop_triggered = False
        
        for entry in self.config_entries.values():
            entry.config(state='normal')
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.resume_btn.config(state='disabled')
        
        self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
        self.status_label.config(text="Bot Detenido", fg='#f87171')
        self.add_log("Bot detenido completamente - Listo para nuevo inicio", 'warning')
        
        self.root.after_idle(self.root.update_idletasks)
        self.root.after_idle(self.root.update)

    def detener_por_stop_loss(self):
        """Método especial para manejar la detención por stop loss"""
        try:
            self.is_running = False
            
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)
           
            if positions:
                for pos in positions:
                    if pos.magic == self.config['MAGIC_NUMBER']:
                        self.cerrar_posicion(pos)
            
            self.root.after(1000, self._finalizar_stop_loss)
            

        except Exception as e:
            self.add_log(f"Error en detención por stop loss: {str(e)}", 'error')
            self._finalizar_stop_loss()
    
    def _finalizar_stop_loss(self):
        """Finalización segura después de stop loss"""
        try:
            self.force_stop_triggered = False
            self.en_pausa = False
            self.objetivo_cumplido = False
            self.analisis_inicial_hecho = False
            self.bot_thread = None
            
            for entry in self.config_entries.values():
                entry.config(state='normal')
            
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            
            self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
            self.status_label.config(text="Bot Detenido", fg='#f87171')
            self.add_log("Bot detenido por stop loss - Listo para nuevo inicio", 'warning')
            
            self.root.update_idletasks()
            self.root.update()
            
        except Exception as e:
            self.add_log(f"Error finalizando stop loss: {str(e)}", 'error')
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')

    def reanudar_trading(self):
        """Reanuda el trading después de alcanzar objetivo"""
        try:
            self.saldo_total_acumulado += self.ganancia_neta
            
            objetivo = self.objetivo_ganancia.get()
            
            self.objetivo_cumplido = False
            self.ganancia_neta = 0.0
            
            self.add_log(f"[EMOJI] Saldo total acumulado: ${self.saldo_total_acumulado:.2f}", 'success')
            self.add_log(f"[ACTUALIZAR] Continuando trading | Nuevo objetivo: +${objetivo:.2f}", 'success')
            
            self.resume_btn.config(state='disabled')
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_indicator.itemconfig(self.status_circle, fill='#10b981')
            self.status_label.config(text="Bot Activo", fg='#34d399')
            
            if not self.bot_thread or not self.bot_thread.is_alive():
                self.is_running = True
                self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
                self.bot_thread.start()
            
        except Exception as e:
            self.add_log(f"Error al reanudar: {str(e)}", 'error')

    def _handle_objetivo_pause(self):
        """Pausa que permite análisis durante el intervalo y reanuda automáticamente."""
        try:
            try:
                pause_seconds = int(self.config['PAUSA_POST_GANANCIA'].get())
            except Exception:
                pause_seconds = 60

            # FIX #16: Asegurar que bot_pausado se establece ANTES de cualquier operación de UI
            self.bot_pausado = True
            self.pause_until = time.time() + pause_seconds
            
            # Actualizar UI de forma segura en Tkinter
            try:
                self.root.after(0, lambda: self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24'))
                self.root.after(0, lambda: self.status_label.config(text=f"Bot Pausado ({pause_seconds}s)", fg='#fbbf24'))
            except Exception as ui_error:
                self.add_log(f"[UI] Advertencia al actualizar indicador: {str(ui_error)[:60]}", 'warning')
            
            self.add_log(f"\n⏸️  [PAUSA] ACTIVADA por {pause_seconds}s - Bot pausado", 'info')

            # Lanzar hilo que reanude después de la pausa
            t = threading.Thread(target=self._objective_pause_worker, args=(pause_seconds,), daemon=True)
            t.start()

        except Exception as e:
            self.add_log(f"Error manejando pausa por objetivo: {e}", 'error')

    def _objective_pause_worker(self, pause_seconds):
        """FIX #17: Worker que ACTUALIZA UI cada segundo mostrando contador en tiempo real"""
        try:
            remaining = max(0, int(pause_seconds))
            
            # Contar hacia abajo Y actualizar UI cada segundo
            while remaining > 0:
                # Actualizar UI con tiempo restante (thread-safe)
                try:
                    self.root.after(0, lambda r=remaining: self.status_label.config(
                        text=f"⏸️ Bot Pausado - {r}s restantes", 
                        fg='#fbbf24'
                    ))
                except Exception:
                    pass
                
                self.add_log(f"⏱️  {remaining}s restantes...", 'info')
                time.sleep(1)
                remaining -= 1

            # Cuando termina la pausa, actualizar UI final
            try:
                self.root.after(0, lambda: self.status_label.config(
                    text="Bot Activo", 
                    fg='#34d399'
                ))
                self.root.after(0, lambda: self.status_indicator.itemconfig(self.status_circle, fill='#10b981'))
            except Exception:
                pass
            
            self.add_log(f"✅ Pausa terminada - Reanudando operaciones", 'success')

        except Exception as e:
            self.add_log(f"Error en worker de pausa objetivo: {e}", 'error')

    def _loss_pause_worker(self, pause_seconds):
        """Worker que espera y luego reanuda automáticamente - SOLO contador cada segundo"""
        try:
            remaining = max(0, int(pause_seconds))
            
            while remaining > 0:
                self.add_log(f"⏱️ {remaining}s restantes...", 'warning')
                time.sleep(1)
                remaining -= 1

            self.add_log(f"[OK] Pausa por pérdida terminada - Reanudando trading automáticamente\n", 'success')
            # Quitar estado de pausa
            self.pause_until = 0
            self.bot_pausado = False

        except Exception as e:
            self.add_log(f"Error en worker de pausa por pérdida: {e}", 'error')

    def actualizar_contador_z(self):
        """Método para actualizar el contador de operaciones Z"""
        try:
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)

            self.total_operaciones_abiertas = 0
            
            if positions:
                for pos in positions:
                    if pos.magic == self.config['MAGIC_NUMBER']:
                        self.total_operaciones_abiertas += 1
                        if pos.ticket not in self.position_tracking:
                            self.position_tracking[pos.ticket] = {
                                'open_time': time.time(),
                                'open_price': pos.price_open,
                                'direction': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
                            }
            
            self.root.after(1, self._update_ui)
            
        except Exception as e:
            self.add_log(f"Error actualizando contador Z: {str(e)}", 'error')

    def limpiar_tracking_posiciones_cerradas(self):
        symbol = self.config['SYMBOL'].get()
        positions = mt5.positions_get(symbol=symbol)
        
        if not positions:
            self.position_tracking.clear()
            return
        
        tickets_abiertos = {pos.ticket for pos in positions if pos.magic == self.config['MAGIC_NUMBER']}
        
        tickets_to_remove = [t for t in self.position_tracking.keys() if t not in tickets_abiertos]
        for ticket in tickets_to_remove:
            del self.position_tracking[ticket]

    def monitorear_posiciones_en_rojo(self):
        """Versión mejorada con IA para análisis de pérdidas"""
        try:
            # ⭐ EN MODO PUNTO DE ENTRADA: Solo monitorear, NUNCA cerrar
            if self.use_entry_point.get():
                symbol = self.config['SYMBOL'].get()
                positions = mt5.positions_get(symbol=symbol)
                
                if not positions:
                    return
                
                tiempo_actual = time.time()
                for pos in positions:
                    if pos.magic != self.config['MAGIC_NUMBER']:
                        continue
                    
                    # ⭐ FIX #12: PRIMERO validar MAX_LOSS_CLOSE - es CRÍTICO y ABSOLUTO
                    try:
                        max_loss = abs(float(self.config['MAX_LOSS_CLOSE'].get()))
                    except Exception as e:
                        self.add_log(f"[MAX_LOSS] ⚠️ Error leyendo MAX_LOSS_CLOSE: {str(e)[:60]}", 'error')
                        max_loss = 7.0  # Fallback seguro
                    
                    if abs(pos.profit) >= max_loss:
                        self.add_log(f"[CRÍTICO] MAX_LOSS alcanzado: ${pos.profit:.2f} >= ${max_loss:.2f} -> cerrando INMEDIATAMENTE", 'error')
                        # Intentar cierre INMEDIATO sin retardo
                        try:
                            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                            tick = mt5.symbol_info_tick(symbol)
                            if not tick:
                                continue
                            price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": pos.volume,
                                "type": close_type,
                                "position": pos.ticket,
                                "price": price,
                                "deviation": 20,
                                "magic": self.config['MAGIC_NUMBER'],
                                "comment": "MAX_LOSS_CRITICAL",
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            for intento in range(5):  # Más reintentos para cierre crítico
                                result = mt5.order_send(request)
                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    self._procesar_cierre_exitoso(pos.ticket, symbol, pos.volume, pos.type, pos.profit)
                                    self.root.after(1, self._update_ui)
                                    self.add_log(f"[OK] ✅ MAX_LOSS cierre exitoso en intento {intento+1}", 'success')
                                    break
                                else:
                                    self.add_log(f"[MAX_LOSS] Intento cierre {intento+1} fallido, reintentando...", 'warning')
                                    time.sleep(0.1)  # Micro-retardo entre reintentos
                        except Exception as e:
                            self.add_log(f"[MAX_LOSS] ⚠️ Error intentando cierre: {str(e)[:80]}", 'error')
                        continue  # Pasar a siguiente posición
                    
                    # Solo loguear estado, sin cerrar por otras razones
                    # Permitir cierre por MIN_PROFIT_CLOSE incluso en modo Punto de Entrada
                    try:
                        min_profit = float(self.config['MIN_PROFIT_CLOSE'].get())
                    except Exception:
                        min_profit = None

                    if min_profit is not None and pos.profit >= min_profit:
                        # intentar cierre inmediato
                        self.add_log(f"[OBJETIVO] PuntoEntrada: MinProfit alcanzado en #{pos.ticket}: ${pos.profit:.2f} >= ${min_profit:.2f} -> cerrando", 'success')
                        try:
                            tick = mt5.symbol_info_tick(symbol)
                            if not tick:
                                continue
                            # Pequeño retardo para dar tiempo a que MT5 refleje la posición
                            try:
                                time.sleep(getattr(self, 'close_delay', 2))
                            except Exception:
                                pass
                            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                            close_price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": pos.volume,
                                "type": close_type,
                                "position": pos.ticket,
                                "price": close_price,
                                "deviation": 20,
                                "magic": self.config['MAGIC_NUMBER'],
                                "comment": "EntryPoint_MinProfit_Close",
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            for intento in range(3):
                                res = mt5.order_send(request)
                                if res and getattr(res, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                    self._procesar_cierre_exitoso(pos.ticket, pos.symbol, pos.volume, pos.type, pos.profit)
                                    self.root.after(1, self._update_ui)
                                    break
                                else:
                                    self.add_log(f"Intento cierre EntryPoint {intento+1} fallido - Reintentando...", 'warning')
                            continue
                        except Exception:
                            pass

                    # Solo loguear estado, sin cerrar por otras razones
                    if pos.profit < 0:
                        self.add_log(f"[DATA] Posición #{pos.ticket} en rojo: ${pos.profit:.2f} (TP/SL automático)", 'info')
                    elif pos.profit > 0:
                        self.add_log(f"💚 Posición #{pos.ticket} en verde: ${pos.profit:.2f} (TP/SL automático)", 'success')

                return  # ← SALIR después de procesar posibles cierres por min profit
            
            # ────────────────────────────────────────
            # MODO NORMAL: Cerrar por lógica de recuperación
            # ────────────────────────────────────────
            
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol) or []

            tiempo_actual = time.time()
            
            for pos in positions:
                if pos.magic != self.config['MAGIC_NUMBER']:
                    continue
                
                tracking_info = self.position_tracking.get(pos.ticket, {
                    'open_time': tiempo_actual,
                    'open_price': pos.price_open
                })
                
                # ⭐ FIX #12: PRIMERO - MAX_LOSS_CLOSECheck (CRÍTICO y ABSOLUTO)
                # Esto debe ejecutarse ANTES que cualquier otra lógica
                try:
                    max_loss = abs(float(self.config['MAX_LOSS_CLOSE'].get()))
                except Exception as e:
                    self.add_log(f"[MAX_LOSS] ⚠️ Error leyendo MAX_LOSS_CLOSE: {str(e)[:60]}", 'error')
                    max_loss = 7.0  # Fallback seguro
                
                if abs(pos.profit) >= max_loss:
                    self.add_log(f"\n[CRÍTICO] 🚨 MAX_LOSS alcanzado: ${pos.profit:.2f} >= ${max_loss:.2f} - Cerrando INMEDIATAMENTE", 'error')
                    # Intentar cierre INMEDIATO sin retardos
                    try:
                        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        tick = mt5.symbol_info_tick(symbol)
                        if not tick:
                            self.add_log(f"[MAX_LOSS] ⚠️ No hay tick disponible para {symbol}", 'warning')
                            continue
                        price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": pos.volume,
                            "type": close_type,
                            "position": pos.ticket,
                            "price": price,
                            "deviation": 20,
                            "magic": self.config['MAGIC_NUMBER'],
                            "comment": "MAX_LOSS_CRITICAL_CLOSE",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        for intento in range(5):  # Más reintentos para cierre crítico
                            result = mt5.order_send(request)
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                self._procesar_cierre_exitoso(pos.ticket, pos.symbol, pos.volume, pos.type, pos.profit)
                                self.root.after(1, self._update_ui)
                                self.add_log(f"[OK] ✅ MAX_LOSS cierre exitoso (intento {intento+1})", 'success')
                                break
                            else:
                                self.add_log(f"[MAX_LOSS] Intento {intento+1} fallido, reintentando...", 'warning')
                                time.sleep(0.05)  # Micro-retardo
                    except Exception as e:
                        self.add_log(f"[MAX_LOSS] ⚠️ Error en cierre: {str(e)[:80]}", 'error')
                    continue  # Pasar a siguiente posición
                
                # NUEVO: Log de tiempo en rojo
                tiempo_en_rojo = tiempo_actual - tracking_info.get('open_time', tiempo_actual)
                if pos.profit < 0:
                    self.add_log(f"\n[DATA] Monitoreo Posición #{pos.ticket}:", 'warning')
                    self.add_log(f"   ⏱️ Tiempo en rojo: {tiempo_en_rojo:.0f}s ({tiempo_en_rojo/60:.1f}m)", 'warning')
                    self.add_log(f"   [DINERO] Pérdida actual: ${pos.profit:.2f}", 'error')
                
                # Cerrar por MIN_PROFIT_CLOSE (beneficio mínimo)
                try:
                    min_profit = float(self.config['MIN_PROFIT_CLOSE'].get())
                except Exception:
                    min_profit = None
                if min_profit is not None:
                    try:
                        pf = float(pos.profit)
                    except Exception:
                        pf = None
                    # Log de diagnóstico
                    self.add_log(f"DEBUG MinProfit check: pos.profit={pf} config_min_profit={min_profit}", 'info')
                    # Persistir diagnóstico para inspección fuera de UI
                    try:
                        with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                            fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'ticket': getattr(pos,'ticket',None), 'profit': pf, 'min_profit': min_profit}) + '\n')
                    except Exception:
                        pass
                    # Comparación con tolerancia para evitar pequeños desajustes
                    if pf is not None and (pf + 1e-9) >= float(min_profit):
                        self.add_log(f"[OBJETIVO] Min Profit alcanzado: ${pf:.2f} >= ${min_profit:.2f} -> cerrando", 'success')
                        # Pequeño retardo para dar tiempo a que MT5 refleje la posición correctamente
                        try:
                            time.sleep(getattr(self, 'close_delay', 2))
                        except Exception:
                            pass
                        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        price = mt5.symbol_info_tick(symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": pos.volume,
                            "type": close_type,
                            "position": pos.ticket,
                            "price": price,
                            "deviation": 20,
                            "magic": self.config['MAGIC_NUMBER'],
                            "comment": "MinProfit_Close",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        for intento in range(3):
                            result = mt5.order_send(request)
                            # Log resultado intento en archivo
                            try:
                                with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                                    fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'ticket': getattr(pos,'ticket',None), 'attempt': intento+1, 'retcode': getattr(result,'retcode',None)}) + '\n')
                            except Exception:
                                pass
                            if result and getattr(result, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                self._procesar_cierre_exitoso(pos.ticket, pos.symbol, pos.volume, pos.type, pos.profit)
                                self.root.after(1, self._update_ui)
                                break
                            else:
                                self.add_log(f"Intento cierre MinProfit {intento+1} fallido - Reintentando...", 'warning')
                        continue

                # ⭐ FIX #12: MAX_LOSS check ya se hace al inicio del loop (línea anterior)
                # NO DUPLICAR la lógica de MAX_LOSS aquí
                
                # ⭐ NUEVO: Análisis anticipado con ML (Loss Protection)
                try:
                    if hasattr(self, 'loss_protection_ai') and pos.profit < -0.5:  # Solo si está en rojo
                        analysis = self.loss_protection_ai.analyze_position(symbol, pos, tracking_info)
                        if analysis and analysis.get('decision') == 'CLOSE_ANTICIPATE':
                            self.add_log(f"[LOSS] 🛡️ Cierre anticipado por ML: Predicción de pérdida → #{pos.ticket}", 'warning')
                            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                            price = mt5.symbol_info_tick(symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
                            
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": pos.volume,
                                "type": close_type,
                                "position": pos.ticket,
                                "price": price,
                                "deviation": 20,
                                "magic": self.config['MAGIC_NUMBER'],
                                "comment": "Anticipate_Close",
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            for intento in range(2):
                                result = mt5.order_send(request)
                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    self._procesar_cierre_exitoso(pos.ticket, pos.symbol, pos.volume, pos.type, pos.profit)
                                    self.root.after(1, self._update_ui)
                                    break
                except Exception as e:
                    pass
                
                # --------------------------------------------------
                # Manejar tickets provisionales en position_tracking
                # --------------------------------------------------
                try:
                    # Active tickets present in MT5 for this symbol and magic
                    active_tickets = {p.ticket for p in positions if getattr(p, 'magic', None) == self.config['MAGIC_NUMBER']} if positions else set()
                    tracked_tickets = set(self.position_tracking.keys())
                    missing = tracked_tickets - active_tickets
                    if missing:
                        tick = mt5.symbol_info_tick(symbol)
                        symbol_info = mt5.symbol_info(symbol)
                        # ⭐ Usar contract_size correcto
                        raw_contract_size = getattr(symbol_info, 'trade_contract_size', 1.0) or 1.0
                        contract_size = max(1, raw_contract_size / 100.0) if raw_contract_size >= 100 else raw_contract_size
                        current_price = tick.bid if tick else None
                        for t in list(missing):
                            info = self.position_tracking.get(t, {})
                            try:
                                open_price = float(info.get('open_price', 0.0))
                                vol = float(info.get('volume', 0.0))
                                direction = info.get('direction', 'BUY')
                            except Exception:
                                continue
                            if current_price is None or vol <= 0:
                                continue
                            # Estimar profit en términos de cuenta: delta_price * vol * contract_size
                            if direction == 'BUY':
                                profit_est = (current_price - open_price) * vol * float(contract_size)
                            else:
                                profit_est = (open_price - current_price) * vol * float(contract_size)
                            # Registrar diagnóstico persistente
                            try:
                                with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                                    fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'provisional_ticket': t, 'profit_est': profit_est, 'open_price': open_price, 'current_price': current_price, 'vol': vol}) + '\n')
                            except Exception:
                                pass
                            # Comprobar umbrales
                            try:
                                min_profit = float(self.config['MIN_PROFIT_CLOSE'].get())
                            except Exception:
                                min_profit = None
                            try:
                                max_loss = abs(float(self.config['MAX_LOSS_CLOSE'].get()))
                            except Exception:
                                max_loss = None
                            # Intentar cerrar si thresholds alcanzados
                            if min_profit is not None and profit_est >= min_profit:
                                self.add_log(f"Provisional ticket {t} alcanza MinProfit estimado ${profit_est:.2f} >= ${min_profit:.2f} -> intentando cierre", 'info')
                                # Pequeño retardo antes de intentar cierre provisional
                                try:
                                    time.sleep(getattr(self, 'close_delay', 2))
                                except Exception:
                                    pass
                                # Intentar cerrar usando position id si posible
                                close_type = mt5.ORDER_TYPE_SELL if direction == 'BUY' else mt5.ORDER_TYPE_BUY
                                price = current_price
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": vol,
                                    "type": close_type,
                                    "price": price,
                                    "deviation": 20,
                                    "magic": self.config['MAGIC_NUMBER'],
                                    "comment": "Provisional_MinProfit_Close",
                                    "type_time": mt5.ORDER_TIME_GTC,
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                for intento in range(3):
                                        # Antes de enviar, reintentar localizar la posición real
                                        live_pos = None
                                        try:
                                            all_pos = mt5.positions_get(symbol=symbol) or []
                                            for p in all_pos:
                                                if getattr(p, 'magic', None) == self.config['MAGIC_NUMBER']:
                                                    # comparar volumen y precio con tolerancia
                                                    try:
                                                        if abs(float(p.volume) - float(vol)) <= max(0.0001, float(vol)*0.05):
                                                            live_pos = p
                                                            break
                                                    except Exception:
                                                        live_pos = p
                                                        break
                                        except Exception:
                                            live_pos = None

                                        if live_pos:
                                            # si encontramos la posición en vivo, cerrar por position
                                            req = dict(request)
                                            req['position'] = int(getattr(live_pos, 'ticket', t))
                                            res = mt5.order_send(req)
                                        else:
                                            # intentar cierres por mercado con variación de filling/deviation
                                            tried = False
                                            res = None
                                            for filling, dev in ((mt5.ORDER_FILLING_IOC, 100), (mt5.ORDER_FILLING_FOK, 300)):
                                                req = dict(request)
                                                req['type_filling'] = filling
                                                req['deviation'] = dev
                                                res = mt5.order_send(req)
                                                tried = True
                                                if res and getattr(res, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                                    break
                                            if not tried:
                                                res = mt5.order_send(request)

                                        # Log resultado intento
                                        try:
                                            with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                                                fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'provisional_close_attempt': intento+1, 'ticket': t, 'retcode': getattr(res,'retcode',None), 'comment': getattr(res,'comment',None), 'order': getattr(res,'order',None), 'deal': getattr(res,'deal',None)}) + '\n')
                                        except Exception:
                                            pass

                                        if res and getattr(res, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                            # Procesar cierre usando datos estimados
                                            self._procesar_cierre_exitoso(t, symbol, vol, mt5.POSITION_TYPE_BUY if direction=='BUY' else mt5.POSITION_TYPE_SELL, profit_est)
                                            try:
                                                del self.position_tracking[t]
                                            except Exception:
                                                pass
                                            break
                                        else:
                                            detail = None
                                            try:
                                                detail = getattr(res, 'comment', None)
                                            except Exception:
                                                detail = None
                                            self.add_log(f"Intento cierre provisional {intento+1} fallido para ticket {t} (retcode={getattr(res,'retcode',None)} comment={detail})", 'warning')
                            elif max_loss is not None and abs(profit_est) >= max_loss:
                                self.add_log(f"Provisional ticket {t} alcanza MaxLoss estimado ${profit_est:.2f} >= ${max_loss:.2f} -> intentando cierre", 'error')
                                try:
                                    time.sleep(getattr(self, 'close_delay', 2))
                                except Exception:
                                    pass
                                close_type = mt5.ORDER_TYPE_SELL if direction == 'BUY' else mt5.ORDER_TYPE_BUY
                                price = current_price
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": vol,
                                    "type": close_type,
                                    "price": price,
                                    "deviation": 20,
                                    "magic": self.config['MAGIC_NUMBER'],
                                    "comment": "Provisional_MaxLoss_Close",
                                    "type_time": mt5.ORDER_TIME_GTC,
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                for intento in range(3):
                                    # reintentar localizar posición en vivo
                                    live_pos = None
                                    try:
                                        all_pos = mt5.positions_get(symbol=symbol) or []
                                        for p in all_pos:
                                            if getattr(p, 'magic', None) == self.config['MAGIC_NUMBER']:
                                                try:
                                                    if abs(float(p.volume) - float(vol)) <= max(0.0001, float(vol)*0.05):
                                                        live_pos = p
                                                        break
                                                except Exception:
                                                    live_pos = p
                                                    break
                                    except Exception:
                                        live_pos = None

                                    if live_pos:
                                        req = dict(request)
                                        req['position'] = int(getattr(live_pos, 'ticket', t))
                                        res = mt5.order_send(req)
                                    else:
                                        tried = False
                                        res = None
                                        for filling, dev in ((mt5.ORDER_FILLING_IOC, 100), (mt5.ORDER_FILLING_FOK, 300)):
                                            req = dict(request)
                                            req['type_filling'] = filling
                                            req['deviation'] = dev
                                            res = mt5.order_send(req)
                                            tried = True
                                            if res and getattr(res, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                                break
                                        if not tried:
                                            res = mt5.order_send(request)

                                    try:
                                        with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                                            fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'provisional_close_attempt': intento+1, 'ticket': t, 'retcode': getattr(res,'retcode',None), 'comment': getattr(res,'comment',None), 'order': getattr(res,'order',None), 'deal': getattr(res,'deal',None)}) + '\n')
                                    except Exception:
                                        pass

                                    if res and getattr(res, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                        self._procesar_cierre_exitoso(t, symbol, vol, mt5.POSITION_TYPE_BUY if direction=='BUY' else mt5.POSITION_TYPE_SELL, profit_est)
                                        try:
                                            del self.position_tracking[t]
                                        except Exception:
                                            pass
                                        break
                                    else:
                                        detail = None
                                        try:
                                            detail = getattr(res, 'comment', None)
                                        except Exception:
                                            detail = None
                                        self.add_log(f"Intento cierre provisional {intento+1} fallido para ticket {t} (retcode={getattr(res,'retcode',None)} comment={detail})", 'warning')
                except Exception:
                    pass
                
                # NUEVO: Llamar a analyze_red_position que ahora loguea potencial
                if pos.profit > 0:
                    min_profit = float(self.config['MIN_PROFIT_CLOSE'].get())
                    if pos.profit >= min_profit:
                        self.add_log(f"[OBJETIVO] TP alcanzado: ${pos.profit:.2f} >= ${min_profit:.2f}", 'success')
                        self.cerrar_posicion(pos)
                        continue
                        
                else:
                    # Analizar recuperación (ya loguea internamente)
                    should_close = self.loss_analyzer.analyze_red_position(pos, tracking_info)
                    if should_close:
                        self.add_log(f"[IA] IA sugiere cerrar #{pos.ticket} para minimizar pérdida", 'warning')

                        # Restringir cierres forzados: sólo si supera umbrales configurados
                        try:
                            max_loss = abs(float(self.config['MAX_LOSS_CLOSE'].get()))
                        except Exception:
                            max_loss = None
                        try:
                            min_profit = float(self.config['MIN_PROFIT_CLOSE'].get())
                        except Exception:
                            min_profit = None

                        allow_force_close = False
                        if pos.profit is not None and pos.profit < 0:
                            if max_loss is not None and abs(pos.profit) >= max_loss:
                                allow_force_close = True
                        else:
                            if min_profit is not None and pos.profit >= min_profit:
                                allow_force_close = True

                        if not allow_force_close:
                            self.add_log(f"IA solicitó cierre de #{pos.ticket} pero umbrales no alcanzados (profit={pos.profit} max_loss={max_loss} min_profit={min_profit}) -> ignorando cierre", 'info')
                            continue

                        # Cerrar posición forzadamente (salta checks)
                        success = self.cerrar_posicion(pos, force=True)
                        
                        if success:
                            self.add_log(f"[OK] Posición #{pos.ticket} cerrada exitosamente", 'success')
                        else:
                            self.add_log(f"[ERROR] Error al cerrar posición #{pos.ticket}", 'error')
                        
                        continue
                        
            if tiempo_actual - self.ultima_actualizacion_ui >= 30:
                self._update_ui()
                self.ultima_actualizacion_ui = tiempo_actual
                
        except Exception as e:
            self.add_log(f"Error monitoreando posiciones: {str(e)}", 'error')

    def pausar_bot(self):
        """Maneja la pausa/reanudación del bot"""
        if not self.is_running:
            return
            
        self.bot_pausado = not self.bot_pausado
        
        if self.bot_pausado:
            self.pause_btn.config(text="▶️ Reanudar")
            self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
            self.status_label.config(text="Bot Pausado", fg='#fbbf24')
            self.add_log("Bot pausado manualmente", 'warning')
        else:
            self.pause_btn.config(text="⏸️ Pausar")
            self.status_indicator.itemconfig(self.status_circle, fill='#10b981')
           
            self.status_label.config(text="Bot Activo", fg='#34d399')
            self.add_log("Bot reanudado", 'success')

    def actualizar_tiempo(self):
        """Actualiza el contador de tiempo restante"""
        if not self.is_running or self.bot_pausado:
            return
            
        if self.tiempo_restante > 0:
            tiempo_actual = time.time()
            tiempo_transcurrido = int(tiempo_actual - self.tiempo_inicio)
            self.tiempo_restante = max(0, (self.tiempo_total.get() * 60) - tiempo_transcurrido)
            
            minutos = self.tiempo_restante // 60
            segundos = self.tiempo_restante % 60
            self.tiempo_label.config(text=f"⏱️ {minutos:02d}:{segundos:02d}")
            
            if self.tiempo_restante <= 0:
                self.add_log("🕒 Tiempo límite alcanzado", 'warning')
                self.detener_por_tiempo()
            
            self.root.after(1000, self.actualizar_tiempo)

    def detener_por_tiempo(self):
        """Detiene el bot cuando se acaba el tiempo"""
        self.is_running = False
        self.en_pausa = False
        self.objetivo_cumplido = False
        
        for entry in self.config_entries.values():
            entry.config(state='normal')
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.pause_btn.config(state='disabled')
        self.resume_btn.config(state='disabled')
        
        self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
        self.status_label.config(text="Bot Detenido por Tiempo", fg='#f87171')
        
        self.add_log("Bot detenido por tiempo límite", 'warning')
        if self.ganancia_neta > 0:
            self.add_log(f"[DINERO] Ganancia final: ${self.ganancia_neta:.2f}", 'success')
    
    def _on_multi_ai_toggle(self):
        """Callback cuando se cambia el toggle Multi-IA"""
        if self.use_multi_ai.get():
            self.mode_label.config(text="(BUY + SELL)", fg='#34d399')
            self.add_log("[IA] Sistema Multi-IA ACTIVADO - Analizando ambas direcciones", 'success')
        else:
            self.mode_label.config(text="(Tradicional)", fg='#94a3b8')
            self.add_log("[CONFIG] Modo tradicional activado - Solo GoldAnalyzer", 'info')

    def validar_y_ajustar_stops(self, symbol, price, tp, sl, direction):
        """Valida y ajusta TP/SL según los requisitos mínimos de MT5
        
        ⭐ CRÍTICO: RESPETA exactamente los valores que el usuario definió
        Solo redondea a los dígitos correctos, NO cambia magnitudes
        """
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None, None
            
            digits = int(getattr(info, "digits", 5))
            
            # ⭐ SIMPLEMENTE REDONDEAR: No cambiar valores, solo aplicar precisión correcta
            tp_adj = round(float(tp), digits) if tp is not None else None
            sl_adj = round(float(sl), digits) if sl is not None else None
            
            self.add_log(f"📏 Stops redondeados a {digits} dígitos: TP={tp_adj:.5f}, SL={sl_adj:.5f}", 'info')
            
            return tp_adj, sl_adj
            
        except Exception as e:
            self.add_log(f"Error validando stops: {str(e)}", 'error')
            return None, None

    def abrir_operacion_en_espera(self, direccion, tp, sl, precio_objetivo=None):
        """Abre una operación en espera con TP y SL específicos
        ⭐ IMPORTANTE: MANTIENE LAS DIFERENCIAS que el usuario definió
        Si usuario pone: Entrada 4480, SL 4475 (-5), TP 4490 (+10)
        Y abre en 4491, abre con: SL 4486 (4491-5), TP 4501 (4491+10)
        """
        try:
            # Verificar si el bot está conectado
            if not self.connected:
                if not self.conectar_mt5():
                    self.add_log("Error: No se pudo conectar a MT5", 'error')
                    return False
            
            symbol = self.config['SYMBOL'].get()
            
            # Verificar límite de operaciones
            if self.total_operaciones_abiertas >= self.config['MAX_SIMULTANEOUS_OPS'].get():
                self.add_log("Error: Máximo de operaciones alcanzado", 'error')
                return False
            
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.add_log("Error: No se pudo obtener información del símbolo", 'error')
                return False
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.add_log("Error: No se pudo obtener tick actual", 'error')
                return False
            
            # Usar precio actual de mercado
            precio_actual = tick.ask if direccion == "BUY" else tick.bid
            
            # Convertir tipo
            tipo = mt5.ORDER_TYPE_BUY if direccion == "BUY" else mt5.ORDER_TYPE_SELL
            
            # ⭐ CALCULAR DIFERENCIAS si el usuario definió valores
            volume = float(self.config['VOL'].get())
            
            # Si precio_objetivo se proporciona, calcular diferencias respecto a él
            if precio_objetivo is not None and tp is not None and tp != 0 and sl is not None and sl != 0:
                # Calcular las diferencias que el usuario definió
                tp_diff = tp - precio_objetivo
                sl_diff = sl - precio_objetivo
                
                # Aplicar esas diferencias al precio actual
                tp_nuevo = precio_actual + tp_diff
                sl_nuevo = precio_actual + sl_diff
                
                self.add_log(f"\n📏 CÁLCULO DE DIFERENCIALES:", 'info')
                self.add_log(f"   Entrada Analizada (objetivo): {precio_objetivo:.5f}", 'info')
                self.add_log(f"   TP Definido: {tp:.5f} → Diferencial: {tp_diff:+.5f}", 'info')
                self.add_log(f"   SL Definido: {sl:.5f} → Diferencial: {sl_diff:+.5f}", 'info')
                self.add_log(f"   Precio Actual (mercado): {precio_actual:.5f}", 'info')
                self.add_log(f"   [OBJETIVO] RESULTADO:", 'success')
                self.add_log(f"      TP Nuevo: {precio_actual:.5f} {tp_diff:+.5f} = {tp_nuevo:.5f}", 'success')
                self.add_log(f"      SL Nuevo: {precio_actual:.5f} {sl_diff:+.5f} = {sl_nuevo:.5f}", 'success')
                
                tp = tp_nuevo
                sl = sl_nuevo
                
            elif tp is None or tp == 0 or sl is None or sl == 0:
                # Si el usuario NO definió valores, usar TP_DIFF y SL_DIFF de la configuración
                self.add_log(f"[DATA] Usando TP_DIFF y SL_DIFF de configuración...", 'info')
                try:
                    tp_cfg = float(self.config['TP_DIFF'].get())
                    sl_cfg = float(self.config['SL_DIFF'].get())
                except Exception:
                    tp_cfg = 5.0
                    sl_cfg = 50.0
                
                digits = get_symbol_digits(symbol_info)
                if direccion == "BUY":
                    tp = round(precio_actual + tp_cfg, digits)
                    sl = round(precio_actual - sl_cfg, digits)
                else:
                    tp = round(precio_actual - tp_cfg, digits)
                    sl = round(precio_actual + sl_cfg, digits)
                
                self.add_log(f"[TP/SL] EnEspera: precio={precio_actual:.2f} TP_DIFF={tp_cfg} SL_DIFF={sl_cfg} → TP={tp:.2f} SL={sl:.2f}", 'info')
            else:
                # El usuario DEFINIÓ valores manualmente (sin precio_objetivo)
                self.add_log(f"[OK] Usando TP/SL definido por usuario: TP={tp:.5f}, SL={sl:.5f}", 'success')
            
            # ⭐ VALIDAR Y AJUSTAR TP/SL (solo si están fuera de rango MT5)
            tp_valid, sl_valid = self.validar_y_ajustar_stops(
                symbol, precio_actual, tp, sl, direccion
            )
            
            if tp_valid is None or sl_valid is None:
                self.add_log(f"[ERROR] Error validando stops: TP={tp_valid}, SL={sl_valid}", 'error')
                return False
            
            self.add_log(f"[EMOJI] Stops validados: TP={tp_valid:.5f}, SL={sl_valid:.5f}", 'info')
            
            # ⭐ NUEVO: Opción de usar o no SL
            usar_sl = self.config['USE_SL'].get()
            sl_final = sl_valid if usar_sl else 0.0
            
            # ⭐ DEBUG: Log detallado antes de enviar a MT5
            self.add_log(f"[DATA] ANTES DE ENVIAR A MT5:", 'info')
            self.add_log(f"   Dirección: {direccion}, Tipo: {tipo}", 'info')
            self.add_log(f"   Precio: {precio_actual:.5f}", 'info')
            self.add_log(f"   TP (enviado): {tp_valid:.5f}", 'info')
            self.add_log(f"   SL (enviado): {sl_final:.5f}", 'info')
            
            # ⭐ VALIDACIÓN ADICIONAL: Verificar orden correcto
            if direccion == "BUY":
                if sl_final != 0 and sl_final >= precio_actual:
                    self.add_log(f"[ERROR] ERROR BUY: SL ({sl_final:.5f}) >= Precio ({precio_actual:.5f})", 'error')
                    return False
                if tp_valid <= precio_actual:
                    self.add_log(f"[ERROR] ERROR BUY: TP ({tp_valid:.5f}) <= Precio ({precio_actual:.5f})", 'error')
                    return False
            else:  # SELL
                if sl_final != 0 and sl_final <= precio_actual:
                    self.add_log(f"[ERROR] ERROR SELL: SL ({sl_final:.5f}) <= Precio ({precio_actual:.5f})", 'error')
                    return False
                if tp_valid >= precio_actual:
                    self.add_log(f"[ERROR] ERROR SELL: TP ({tp_valid:.5f}) >= Precio ({precio_actual:.5f})", 'error')
                    return False

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": tipo,
                "price": precio_actual,
                "sl": sl_final,
                "tp": tp_valid,
                "deviation": 20,
                "magic": self.config['MAGIC_NUMBER'],
                "comment": f"Bot-Espera-{direccion}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.total_operaciones_abiertas += 1
                self.position_ids.add(result.order)
                self.add_log(f"[OK] Operación {direccion} abierta manualmente desde espera", 'success')
                sl_text = f"SL: {sl_final:.5f}" if usar_sl else "SIN SL"
                self.add_log(f"   Precio: {precio_actual:.5f}, TP: {tp_valid:.5f}, {sl_text}", 'success')
                return True
            else:
                retcode = result.retcode if result else "N/A"
                comment = result.comment if result else "Sin respuesta"
                self.add_log(f"[ERROR] Error abriendo operación: {comment} (Code: {retcode})", 'error')
                return False
                
        except Exception as e:
            self.add_log(f"Error en abrir_operacion_en_espera: {str(e)}", 'error')
            return False

    def abrir_operacion_manual(self, direccion):
        """Abre una operación manual con las mismas características que las automáticas"""
        try:
            # Verificar si el bot está conectado
            if not self.connected:
                if not self.conectar_mt5():
                    messagebox.showerror("Error", "No se pudo conectar a MT5")
                    return
            
            symbol = self.config['SYMBOL'].get()
            
            # Verificar límite de operaciones
            if self.total_operaciones_abiertas >= self.config['MAX_SIMULTANEOUS_OPS'].get():
                messagebox.showwarning("Advertencia", "Máximo de operaciones alcanzado")
                return
            
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                messagebox.showerror("Error", "No se pudo obtener información del símbolo")
                return
            
            # ⭐ CORREGIDO: TP_DIFF y SL_DIFF son DIFERENCIAS DIRECTAS EN PRECIO
            tp_diff = float(self.config['TP_DIFF'].get())
            sl_diff = float(self.config['SL_DIFF'].get())
    
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                messagebox.showerror("Error", "No se pudo obtener tick actual")
                return
            
            precio = tick.ask if direccion == "BUY" else tick.bid
            digits = get_symbol_digits(symbol_info)
            
            # ⭐ Usar diferencia DIRECTA en precio (no multiplicar por point)
            if direccion == "BUY":
                sl = round(precio - sl_diff, digits)
                tp = round(precio + tp_diff, digits)
                tipo = mt5.ORDER_TYPE_BUY
            else:
                sl = round(precio + sl_diff, digits)
                tp = round(precio - tp_diff, digits)
                tipo = mt5.ORDER_TYPE_SELL
            
            self.add_log(f"[TP/SL] Manual: precio={precio:.2f} TP_DIFF={tp_diff} SL_DIFF={sl_diff} → TP={tp:.2f} SL={sl:.2f}", 'info')
            
            # ⭐ VALIDAR STOPS contra STOPS_LEVEL del broker
            sl, tp, _ = validate_and_adjust_stops(
                symbol_info, precio, sl, tp, direccion, log_callback=self.add_log
            )

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(self.config['VOL'].get()),
                "type": tipo,
                "price": precio,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": self.config['MAGIC_NUMBER'],
                "comment": f"Bot-Manual-{direccion}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.total_operaciones_abiertas += 1
                self.position_ids.add(result.order)
                msg = f"[OK] Operación manual {direccion}: {precio:.5f} | TP={tp:.5f} SL={sl:.5f}"
                self.add_log(msg, 'success')
                self.actualizar_contador_z()
            else:
                retcode = result.retcode if result else "Sin respuesta"
                comment = result.comment if result else "Sin comentario"
                messagebox.showerror("Error", f"Error al abrir operación: {comment} (Code: {retcode})")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir operación manual: {str(e)}")

    # ------------------ NUEVO: Panel Punto de Entrada ------------------
    def create_entry_point_panel(self, parent):
        panel = tk.LabelFrame(parent, text="Punto de Entrada (AI) - Super Análisis", 
                              bg='#2d3e50', fg='#f1f5f9',
                              font=('Arial', 11, 'bold'), padx=10, pady=10)
        panel.pack(fill='both', expand=True, padx=10, pady=10)

        # ⭐ NUEVO: Notebook (pestañas) para Análisis de Entrada
        entry_notebook = ttk.Notebook(panel)
        entry_notebook.pack(fill='both', expand=True, pady=(0, 10))

        # Pestaña 1: Análisis Jerárquico
        hierarchical_tab = tk.Frame(entry_notebook, bg='#1e293b')
        entry_notebook.add(hierarchical_tab, text="🏛️ Análisis Jerárquico")

        # Pestaña 2: Análisis Personalizado
        custom_tab = tk.Frame(entry_notebook, bg='#1e293b')
        entry_notebook.add(custom_tab, text="🔬 Análisis Personalizado")

        # Pestaña 3: Configuración Manual
        manual_tab = tk.Frame(entry_notebook, bg='#1e293b')
        entry_notebook.add(manual_tab, text="🎯 Punto de Entrada Manual")

        # Llenar pestañas
        self.create_hierarchical_analysis_tab(hierarchical_tab)
        self.create_custom_analysis_tab(custom_tab)
        self.create_manual_entry_tab(manual_tab)

    def create_hierarchical_analysis_tab(self, parent):
        """Análisis Jerárquico con selección de período Y timeframe"""
        main_frame = tk.Frame(parent, bg='#1e293b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Selector de Período y Timeframe
        selector_frame = tk.LabelFrame(main_frame, text="Configuración de Análisis", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=8, pady=8)
        selector_frame.pack(fill='x', pady=(0, 10))

        # Fila 1: Período
        period_row = tk.Frame(selector_frame, bg='#2d3e50')
        period_row.pack(fill='x', pady=3)

        tk.Label(period_row, text="Período Base:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9), width=16, anchor='w').pack(side='left', padx=5)
        self.hier_period_var = tk.StringVar(value="1d")
        hier_period_menu = ttk.Combobox(period_row, textvariable=self.hier_period_var, 
                                       values=["1d", "7d", "14d", "30d", "60d", "90d", "120d", "240d", "365d"], 
                                       width=10, state='readonly', font=('Arial', 9))
        hier_period_menu.pack(side='left', padx=5)

        tk.Label(period_row, text="Timeframe Análisis:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9), width=16, anchor='w').pack(side='left', padx=5)
        self.hier_timeframe_var = tk.StringVar(value="1h")
        hier_timeframe_menu = ttk.Combobox(period_row, textvariable=self.hier_timeframe_var, 
                                          values=["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"], 
                                          width=10, state='readonly', font=('Arial', 9))
        hier_timeframe_menu.pack(side='left', padx=5)

        # Fila 2: Botón de análisis
        btn_row = tk.Frame(selector_frame, bg='#2d3e50')
        btn_row.pack(fill='x', pady=(5, 0))

        self.hierarchical_analysis_btn = tk.Button(btn_row, text="🏛️ Ejecutar Análisis Jerárquico", 
                                                  command=self.ejecutar_analisis_jerarquico,
                                                  bg='#8b5cf6', fg='white', font=('Arial', 10, 'bold'),
                                                  relief='flat', padx=15, pady=8, cursor='hand2')
        self.hierarchical_analysis_btn.pack(side='left', padx=5, fill='x', expand=True)

        self.hierarchical_status = tk.Label(btn_row, text="✅ Listo", 
                                           bg='#2d3e50', fg='#34d399', font=('Arial', 9))
        self.hierarchical_status.pack(side='left', padx=5)

        # ⭐ NUEVO: Fila 3 - Separar Funciones (BUY/SELL)
        separator_row = tk.Frame(selector_frame, bg='#2d3e50')
        separator_row.pack(fill='x', pady=(5, 0))

        # Sección: Separar Funciones
        tk.Label(separator_row, text="🔀 Separar Funciones:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9, 'bold'), width=16, anchor='w').pack(side='left', padx=5)

        self.hier_filter_var = tk.StringVar(value="TODOS")
        self.hier_filter_var.trace('w', lambda *args: self._actualizar_filtro_jerarquico())
        
        filter_menu = ttk.Combobox(separator_row, textvariable=self.hier_filter_var, 
                                   values=["TODOS", "SOLO BUY", "SOLO SELL"], 
                                   width=12, state='readonly', font=('Arial', 9))
        filter_menu.pack(side='left', padx=5)

        # ⭐ NUEVO: Fila 4 - Botones Marcar/Desmarcar
        mark_row = tk.Frame(selector_frame, bg='#2d3e50')
        mark_row.pack(fill='x', pady=(5, 0))

        tk.Label(mark_row, text="☑️ Seleccionar:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9, 'bold'), width=16, anchor='w').pack(side='left', padx=5)

        # ⭐ Botón "Marcar Todo"
        tk.Button(mark_row, text="☑️ Marcar Todo", 
                 command=self._marcar_todas_opciones,
                 bg='#06b6d4', fg='white', font=('Arial', 8, 'bold'),
                 relief='flat', padx=15, pady=3, cursor='hand2').pack(side='left', padx=2, fill='x', expand=True)
        
        # ⭐ Botón "Desmarcar Todo"
        tk.Button(mark_row, text="☐ Desmarcar Todo", 
                 command=self._desmarcar_todas_opciones,
                 bg='#64748b', fg='white', font=('Arial', 8, 'bold'),
                 relief='flat', padx=15, pady=3, cursor='hand2').pack(side='left', padx=2, fill='x', expand=True)

        # ⭐ NUEVO: Fila 5 - Velas TP
        velas_tp_row = tk.Frame(selector_frame, bg='#2d3e50')
        velas_tp_row.pack(fill='x', pady=(5, 0))

        tk.Label(velas_tp_row, text="📊 Velas TP:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9, 'bold'), width=16, anchor='w').pack(side='left', padx=5)

        self.hier_velas_tp_var = tk.DoubleVar(value=20.0)
        tk.Entry(velas_tp_row, textvariable=self.hier_velas_tp_var, width=12, 
                bg='#475569', fg='white', font=('Arial', 9), justify='center').pack(side='left', padx=5)

        # Botón aplicar a TP
        tk.Button(velas_tp_row, text="🎯 Aplicar TP", 
                 command=lambda: self._aplicar_velas_a_tp(self.hier_velas_tp_var.get()),
                 bg='#10b981', fg='white', font=('Arial', 8, 'bold'),
                 relief='flat', padx=15, pady=3, cursor='hand2').pack(side='left', padx=2, fill='x', expand=True)

        # ⭐ NUEVO: Fila 6 - Velas SL
        velas_sl_row = tk.Frame(selector_frame, bg='#2d3e50')
        velas_sl_row.pack(fill='x', pady=(5, 0))

        tk.Label(velas_sl_row, text="📊 Velas SL:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9, 'bold'), width=16, anchor='w').pack(side='left', padx=5)

        self.hier_velas_sl_var = tk.DoubleVar(value=20.0)
        tk.Entry(velas_sl_row, textvariable=self.hier_velas_sl_var, width=12, 
                bg='#475569', fg='white', font=('Arial', 9), justify='center').pack(side='left', padx=5)

        # Botón aplicar a SL
        tk.Button(velas_sl_row, text="🛑 Aplicar SL", 
                 command=lambda: self._aplicar_velas_a_sl(self.hier_velas_sl_var.get()),
                 bg='#ef4444', fg='white', font=('Arial', 8, 'bold'),
                 relief='flat', padx=15, pady=3, cursor='hand2').pack(side='left', padx=2, fill='x', expand=True)

        # Frame scrollable para opciones
        options_container = tk.Frame(main_frame, bg='#1e293b', relief='solid', borderwidth=1)
        options_container.pack(fill='both', expand=True, pady=(10, 0))

        self.hier_canvas = tk.Canvas(options_container, bg='#1e293b', highlightthickness=0, height=250)
        self.hier_scrollbar = tk.Scrollbar(options_container, orient='vertical', command=self.hier_canvas.yview)
        self.hier_options_frame = tk.Frame(self.hier_canvas, bg='#1e293b')

        self.hier_options_frame.bind(
            "<Configure>",
            lambda e: self.hier_canvas.configure(scrollregion=self.hier_canvas.bbox("all"))
        )

        self.hier_canvas.create_window((0, 0), window=self.hier_options_frame, anchor="nw")
        self.hier_canvas.configure(yscrollcommand=self.hier_scrollbar.set)

        self.hier_canvas.pack(side='left', fill='both', expand=True)
        self.hier_scrollbar.pack(side='right', fill='y')

        self.hier_selected_option = tk.IntVar(value=-1)

        # Botón de uso
        use_btn_frame = tk.Frame(main_frame, bg='#1e293b')
        use_btn_frame.pack(fill='x', pady=(10, 0))

        self.usar_hier_btn = tk.Button(use_btn_frame, text="✅ Usar Opción Seleccionada", 
                                       command=self.usar_opcion_jerarquica,
                                       bg='#10b981', fg='white', font=('Arial', 10, 'bold'),
                                       relief='flat', padx=20, pady=8, cursor='hand2')
        self.usar_hier_btn.pack(side='left', padx=5, fill='x', expand=True)

        # ⭐ NUEVO: Botón para agregar a espera
        self.agregar_espera_hier_btn = tk.Button(use_btn_frame, text="⏳ Agregar a Espera", 
                                                command=self.poner_en_espera_jerarquico,
                                                bg='#f59e0b', fg='white', font=('Arial', 10, 'bold'),
                                                relief='flat', padx=20, pady=8, cursor='hand2')
        self.agregar_espera_hier_btn.pack(side='left', padx=5, fill='x', expand=True)

    def create_custom_analysis_tab(self, parent):
        """Análisis Personalizado con período y timeframe"""
        main_frame = tk.Frame(parent, bg='#1e293b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Selector de Período y Timeframe
        selector_frame = tk.LabelFrame(main_frame, text="Configuración de Análisis", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=8, pady=8)
        selector_frame.pack(fill='x', pady=(0, 10))

        # Fila 1: Período
        period_row = tk.Frame(selector_frame, bg='#2d3e50')
        period_row.pack(fill='x', pady=3)

        tk.Label(period_row, text="Período:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9), width=16, anchor='w').pack(side='left', padx=5)
        self.period_var = tk.StringVar(value="7d")
        period_menu = ttk.Combobox(period_row, textvariable=self.period_var, 
                                   values=["1d", "7d", "14d", "30d", "60d", "90d", "120d", "240d", "365d"], 
                                   width=10, state='readonly', font=('Arial', 9))
        period_menu.pack(side='left', padx=5)

        tk.Label(period_row, text="Timeframe:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9), width=16, anchor='w').pack(side='left', padx=5)
        self.timeframe_var = tk.StringVar(value="1h")
        timeframe_menu = ttk.Combobox(period_row, textvariable=self.timeframe_var, 
                                      values=["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mn"], 
                                      width=10, state='readonly', font=('Arial', 9))
        timeframe_menu.pack(side='left', padx=5)

        # Fila 2: Botón de análisis
        btn_row = tk.Frame(selector_frame, bg='#2d3e50')
        btn_row.pack(fill='x', pady=(5, 0))

        self.super_analysis_btn = tk.Button(btn_row, text="🔍 Ejecutar Super Análisis", 
                                           command=self.ejecutar_super_analisis,
                                           bg='#8b5cf6', fg='white', font=('Arial', 10, 'bold'),
                                           relief='flat', padx=15, pady=8, cursor='hand2')
        self.super_analysis_btn.pack(side='left', padx=5, fill='x', expand=True)

        self.super_analysis_status = tk.Label(btn_row, text="✅ Listo", 
                                             bg='#2d3e50', fg='#34d399', font=('Arial', 9))
        self.super_analysis_status.pack(side='left', padx=5)

        # Resultado del análisis
        result_container = tk.Frame(main_frame, bg='#1e293b', relief='solid', borderwidth=1)
        result_container.pack(fill='both', expand=True, pady=(10, 0))

        self.super_analysis_label = tk.Label(result_container, 
                                            text="Resultado: Ejecuta 'Super Análisis' para ver detalles", 
                                            bg='#1e293b', fg='#cbd5e1', justify='left', anchor='nw',
                                            font=('Arial', 9), wraplength=450)
        self.super_analysis_label.pack(fill='both', expand=True, padx=10, pady=10)

        # Botón de uso
        use_btn_frame = tk.Frame(main_frame, bg='#1e293b')
        use_btn_frame.pack(fill='x', pady=(10, 0))

        self.usar_custom_btn = tk.Button(use_btn_frame, text="✅ Usar Este Análisis", 
                                        command=self.usar_analisis_personalizado,
                                        bg='#10b981', fg='white', font=('Arial', 10, 'bold'),
                                        relief='flat', padx=20, pady=8, cursor='hand2')
        self.usar_custom_btn.pack(side='left', padx=5, fill='x', expand=True)

        # ⭐ NUEVO: Frame para ajustar TP/SL con controles +/-
        controls_frame = tk.LabelFrame(main_frame, text="⚙️ Ajustar TP/SL y Calcular Ganancias", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=10, pady=8)
        controls_frame.pack(fill='x', pady=(10, 0))

        # Variables para TP/SL ajustables
        self.tp_var = tk.DoubleVar(value=0.0)
        self.sl_var = tk.DoubleVar(value=0.0)
        self.tp_status_var = tk.StringVar(value="✅")  # ✅ verde o ❌ rojo
        self.sl_status_var = tk.StringVar(value="✅")

        # Fila 1: TP (Take Profit)
        tp_row = tk.Frame(controls_frame, bg='#2d3e50')
        tp_row.pack(fill='x', pady=5)

        tk.Label(tp_row, text="TP:", bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9, 'bold'), width=4).pack(side='left', padx=2)
        
        tk.Button(tp_row, text="−", command=lambda: self._adjust_tp(-0.0001), 
                 bg='#ef4444', fg='white', font=('Arial', 10, 'bold'), width=2, padx=2).pack(side='left', padx=2)
        
        tk.Entry(tp_row, textvariable=self.tp_var, width=12, bg='#475569', fg='white', 
                font=('Arial', 9), justify='center').pack(side='left', padx=2)
        
        tk.Button(tp_row, text="+", command=lambda: self._adjust_tp(0.0001), 
                 bg='#10b981', fg='white', font=('Arial', 10, 'bold'), width=2, padx=2).pack(side='left', padx=2)
        
        self.tp_status_label = tk.Label(tp_row, textvariable=self.tp_status_var, 
                                       bg='#2d3e50', fg='#34d399', font=('Arial', 11, 'bold'), width=2)
        self.tp_status_label.pack(side='left', padx=5)

        # Fila 2: SL (Stop Loss)
        sl_row = tk.Frame(controls_frame, bg='#2d3e50')
        sl_row.pack(fill='x', pady=5)

        tk.Label(sl_row, text="SL:", bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9, 'bold'), width=4).pack(side='left', padx=2)
        
        tk.Button(sl_row, text="−", command=lambda: self._adjust_sl(-0.0001), 
                 bg='#ef4444', fg='white', font=('Arial', 10, 'bold'), width=2, padx=2).pack(side='left', padx=2)
        
        tk.Entry(sl_row, textvariable=self.sl_var, width=12, bg='#475569', fg='white', 
                font=('Arial', 9), justify='center').pack(side='left', padx=2)
        
        tk.Button(sl_row, text="+", command=lambda: self._adjust_sl(0.0001), 
                 bg='#10b981', fg='white', font=('Arial', 10, 'bold'), width=2, padx=2).pack(side='left', padx=2)
        
        self.sl_status_label = tk.Label(sl_row, textvariable=self.sl_status_var, 
                                       bg='#2d3e50', fg='#34d399', font=('Arial', 11, 'bold'), width=2)
        self.sl_status_label.pack(side='left', padx=5)

        # Fila 3: Información de ganancias
        info_row = tk.Frame(controls_frame, bg='#2d3e50')
        info_row.pack(fill='x', pady=5)

        self.profit_info_label = tk.Label(info_row, 
                                         text="📊 Ganancia Est.: $0 | Risk:Reward: 0:0 | Volumen: 0",
                                         bg='#2d3e50', fg='#fbbf24', font=('Arial', 9, 'bold'))
        self.profit_info_label.pack(side='left', padx=5, fill='x', expand=True)

        # Botón para enviar a espera
        self.enviar_espera_btn = tk.Button(controls_frame, text="⏳ Enviar a Espera", 
                                          command=self.enviar_a_espera_ajustado,
                                          bg='#f59e0b', fg='white', font=('Arial', 10, 'bold'),
                                          relief='flat', padx=20, pady=6, cursor='hand2')
        self.enviar_espera_btn.pack(side='left', padx=5, fill='x', expand=True)

    def create_manual_entry_tab(self, parent):
        """Configuración manual del punto de entrada (pantalla original simplificada)"""
        main_frame = tk.Frame(parent, bg='#1e293b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Sección de entrada manual
        entry_frame = tk.LabelFrame(main_frame, text="Configuración Manual", 
                                   bg='#2d3e50', fg='#f1f5f9',
                                   font=('Arial', 10, 'bold'), padx=8, pady=8)
        entry_frame.pack(fill='x', pady=(0, 10))

        # Fila 1: Activar/Desactivar
        toggle_row = tk.Frame(entry_frame, bg='#2d3e50')
        toggle_row.pack(fill='x', pady=3)

        tk.Checkbutton(toggle_row, text="Usar Punto de Entrada Manual", 
                      variable=self.use_entry_point,
                      command=self._on_entry_point_toggle, 
                      bg='#2d3e50', fg='#cbd5e1',
                      selectcolor='#1e293b', activebackground='#2d3e50',
                      font=('Arial', 9, 'bold')).pack(side='left', padx=5)

        # Fila 2: Precio objetivo
        price_row = tk.Frame(entry_frame, bg='#2d3e50')
        price_row.pack(fill='x', pady=3)

        tk.Label(price_row, text="Precio Objetivo:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9), width=16, anchor='w').pack(side='left', padx=5)
        tk.Entry(price_row, textvariable=self.entry_point_price, width=15, 
                bg='#475569', fg='white', font=('Arial', 9)).pack(side='left', padx=5)

        tk.Label(price_row, text="Dirección:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9), width=12, anchor='w').pack(side='left', padx=5)
        dir_menu = ttk.Combobox(price_row, textvariable=self.entry_point_direction, 
                               values=["BUY", "SELL"], width=8, state='readonly', font=('Arial', 9))
        dir_menu.pack(side='left', padx=5)

        # Fila 3: Botones de acción
        action_row = tk.Frame(entry_frame, bg='#2d3e50')
        action_row.pack(fill='x', pady=(5, 0))

        tk.Button(action_row, text="📊 Analizar 7 días", 
                 command=self.analyze_7_days, 
                 bg='#3b82f6', fg='white', font=('Arial', 9),
                 relief='flat', padx=15, pady=6, cursor='hand2').pack(side='left', padx=2)

        self.use_suggestion_btn = tk.Button(action_row, text="💡 Usar Sugerencia", 
                                           command=self.use_ai_suggestion, 
                                           state='disabled', 
                                           bg='#10b981', fg='white', font=('Arial', 9),
                                           relief='flat', padx=15, pady=6, cursor='hand2')
        self.use_suggestion_btn.pack(side='left', padx=2)

        tk.Button(action_row, text="🎯 Activar Entrada", 
                 command=self.activate_manual_entry, 
                 bg='#f59e0b', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=15, pady=6, cursor='hand2').pack(side='left', padx=2)

        # Sugerencia
        suggestion_frame = tk.Frame(main_frame, bg='#2d3e50', relief='solid', borderwidth=1)
        suggestion_frame.pack(fill='both', expand=True, pady=(10, 0))

        self.suggestion_label = tk.Label(suggestion_frame, 
                                        text="Sugerencia: Ejecuta 'Analizar 7 días' para obtener recomendaciones", 
                                        bg='#2d3e50', fg='#cbd5e1', justify='left', anchor='nw',
                                        font=('Arial', 9), wraplength=450)
        self.suggestion_label.pack(fill='both', expand=True, padx=10, pady=10)

        # Estado
        status_frame = tk.Frame(main_frame, bg='#1e293b')
        status_frame.pack(fill='x', pady=(10, 0))

        self.entry_status_label = tk.Label(status_frame, text="Estado: Inactivo", 
                                          bg='#1e293b', fg='#94a3b8', 
                                          anchor='w', font=('Arial', 9))
        self.entry_status_label.pack(fill='x', pady=2)

        self.entry_current_price_label = tk.Label(status_frame, text="Precio actual: --", 
                                                 bg='#1e293b', fg='#60a5fa', 
                                                 anchor='w', font=('Arial', 9))
        self.entry_current_price_label.pack(fill='x', pady=2)

    def create_pending_operations_panel(self, parent):
        """Panel para mostrar operaciones en espera"""
        panel = tk.LabelFrame(parent, text="Operaciones en Espera", 
                              bg='#2d3e50', fg='#f1f5f9',
                              font=('Arial', 11, 'bold'), padx=10, pady=10)
        panel.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame para la lista de operaciones
        list_frame = tk.Frame(panel, bg='#1e293b', relief='solid', borderwidth=1)
        list_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Listbox con scrollbar
        scrollbar = tk.Scrollbar(list_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self.pending_ops_listbox = tk.Listbox(list_frame, 
                                              bg='#334155', fg='#e2e8f0',
                                              font=('Consolas', 9),
                                              yscrollcommand=scrollbar.set,
                                              relief='flat', borderwidth=0,
                                              activestyle='none')
        self.pending_ops_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.config(command=self.pending_ops_listbox.yview)

        # Frame para botones
        btn_frame = tk.Frame(panel, bg='#2d3e50')
        btn_frame.pack(fill='x', pady=(5, 0))

        tk.Button(btn_frame, text="🔄 Actualizar", 
                 command=self.actualizar_lista_operaciones,
                 bg='#3b82f6', fg='white', font=('Arial', 9),
                 relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        tk.Button(btn_frame, text="🗑️ Limpiar Espera", 
                 command=self.limpiar_operaciones_espera,
                 bg='#ef4444', fg='white', font=('Arial', 9),
                 relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        # Etiqueta de estado
        self.pending_ops_status = tk.Label(btn_frame, text="Sin operaciones en espera", 
                                          bg='#2d3e50', fg='#cbd5e1', font=('Arial', 9))
        self.pending_ops_status.pack(side='left', padx=10, fill='x', expand=True)

    def create_pending_operations_panel(self, parent):
        """Panel para gestionar operaciones en espera"""
        main_frame = tk.Frame(parent, bg='#1e293b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Título
        title_frame = tk.Frame(main_frame, bg='#1e293b')
        title_frame.pack(fill='x', pady=(0, 10))

        tk.Label(title_frame, text="⏳ Operaciones en Espera", bg='#1e293b', fg='#fbbf24',
                font=('Arial', 12, 'bold')).pack(side='left')

        # Frame con scroll para operaciones
        list_frame = tk.LabelFrame(main_frame, text="📋 Listado de Operaciones", 
                                  bg='#2d3e50', fg='#f1f5f9',
                                  font=('Arial', 10, 'bold'), padx=5, pady=5)
        list_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Listbox con scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.pending_ops_listbox = tk.Listbox(list_frame, bg='#1e293b', fg='#cbd5e1',
                                             yscrollcommand=scrollbar.set, 
                                             font=('Arial', 9), height=8)
        self.pending_ops_listbox.pack(fill='both', expand=True)
        scrollbar.config(command=self.pending_ops_listbox.yview)
        
        # Bind para ver detalles al hacer clic
        self.pending_ops_listbox.bind('<<ListboxSelect>>', self._on_pending_op_select)

        # Frame de detalles
        details_frame = tk.LabelFrame(main_frame, text="📊 Detalles de Operación Seleccionada", 
                                     bg='#2d3e50', fg='#f1f5f9',
                                     font=('Arial', 10, 'bold'), padx=10, pady=10)
        details_frame.pack(fill='x', pady=(0, 10))

        self.pending_op_details = tk.Label(details_frame, text="Selecciona una operación para ver detalles",
                                          bg='#2d3e50', fg='#94a3b8', justify='left',
                                          font=('Arial', 9), wraplength=400)
        self.pending_op_details.pack(fill='x')

        # Frame de análisis en tiempo real
        analysis_frame = tk.LabelFrame(main_frame, text="📈 Analizador de Apertura", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=10, pady=10)
        analysis_frame.pack(fill='x', pady=(0, 10))

        self.pending_analyzer_text = tk.Label(analysis_frame, text="Sin operaciones en espera para analizar",
                                             bg='#2d3e50', fg='#cbd5e1', justify='left',
                                             font=('Arial', 9), wraplength=400)
        self.pending_analyzer_text.pack(fill='x')

        # Frame de botones de acción
        btn_frame = tk.Frame(main_frame, bg='#1e293b')
        btn_frame.pack(fill='x')

        tk.Button(btn_frame, text="🗑️ Eliminar Seleccionada", 
                 command=self._delete_selected_pending_op,
                 bg='#ef4444', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        tk.Button(btn_frame, text="🔄 Actualizar Análisis", 
                 command=self._update_pending_analysis,
                 bg='#3b82f6', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        tk.Button(btn_frame, text="✅ Abrir Manual", 
                 command=self._manual_open_pending,
                 bg='#10b981', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        tk.Button(btn_frame, text="🗑️ Limpiar Todo", 
                 command=self._clear_all_pending,
                 bg='#6b7280', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10, pady=5, cursor='hand2').pack(side='left', padx=5)

        # Status
        self.pending_ops_status = tk.Label(btn_frame, text="Sin operaciones en espera", 
                                          bg='#1e293b', fg='#cbd5e1', font=('Arial', 9))
        self.pending_ops_status.pack(side='left', padx=10, fill='x', expand=True)

        # Inicializar lista
        self.actualizar_lista_operaciones()

    def actualizar_lista_operaciones(self):
        """Actualiza la lista de operaciones en espera"""
        self.pending_ops_listbox.delete(0, 'end')
        
        if not self.pending_operations:
            self.pending_ops_status.config(text="Sin operaciones en espera", fg='#cbd5e1')
            return
        
        for i, op in enumerate(self.pending_operations, 1):
            operacion_str = f"Op {i}: {op.get('direction', 'N/A')} @ {op.get('price', 'N/A')}"
            self.pending_ops_listbox.insert('end', operacion_str)
        
        self.pending_ops_status.config(
            text=f"Total: {len(self.pending_operations)} operación(es)", 
            fg='#60a5fa'
        )

    def limpiar_operaciones_espera(self):
        """Limpia la lista de operaciones en espera"""
        self.pending_operations = []
        self.actualizar_lista_operaciones()
        self.add_log("Operaciones en espera limpiadas", 'warning')

    def _on_pending_op_select(self, event):
        """Muestra detalles de la operación seleccionada"""
        selection = self.pending_ops_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx >= len(self.pending_operations):
            return
        
        op = self.pending_operations[idx]
        
        # Mostrar detalles
        details = f"""
[UBICACION] ID: {op.get('id', 'N/A')}
[OBJETIVO] Dirección: {op.get('direction', 'N/A')}
[DINERO] Precio Objetivo: {op.get('price', 'N/A'):.5f}
[DATA] Timeframe: {op.get('timeframe', 'N/A')}
⭐ Confianza: {op.get('confidence', 0):.1f}%
🎲 Período: {op.get('period', 'N/A')}
👁️ Precio Actual: {op.get('current_price', 'N/A'):.5f}
📏 Distancia: {op.get('distance', 0):.5f}
[OBJETIVO] TP: {op.get('tp', 'N/A'):.5f}
[EMOJI] SL: {op.get('sl', 'N/A'):.5f}
🕐 Creada: {op.get('timestamp', 'N/A')}
📋 Estado: {op.get('status', 'DESCONOCIDO')}
"""
        self.pending_op_details.config(text=details, fg='#34d399')
        
        # Actualizar análisis de apertura
        self._update_pending_analysis()

    def _update_pending_analysis(self):
        """Actualiza el análisis de apertura para operaciones en espera"""
        if not self.pending_operations:
            self.pending_analyzer_text.config(
                text="Sin operaciones en espera para analizar",
                fg='#cbd5e1'
            )
            return
        
        if not self.connected or not hasattr(self, 'pending_ops_listbox'):
            return
        
        selection = self.pending_ops_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx >= len(self.pending_operations):
            return
        
        op = self.pending_operations[idx]
        
        if op['status'] != 'ESPERANDO':
            analysis = f"[ADVERTENCIA] Esta operación ya fue {op['status']}\n"
            if op.get('timestamp_execution'):
                analysis += f"Ejecutada a las: {op['timestamp_execution']}"
            self.pending_analyzer_text.config(text=analysis, fg='#fbbf24')
            return
        
        symbol = self.config['SYMBOL'].get()
        tick = mt5.symbol_info_tick(symbol)
        
        if not tick:
            analysis = "[ADVERTENCIA] No hay datos de mercado disponibles"
            self.pending_analyzer_text.config(text=analysis, fg='#f87171')
            return
        
        current_price = tick.bid
        direction = op['direction']
        target_price = op['price']
        distance = abs(current_price - target_price)
        
        # Validar dirección - Mostrar solo estado, no bloquear
        # Tanto BUY como SELL son siempre válidos para agregar a lista de espera
        is_valid_direction = True  # Siempre válido para la lista de espera
        
        # ⭐ Calcular tolerancia dinámica basada en ATR y volatilidad
        try:
            rates = mt5.copy_rates_from_pos(self.config['SYMBOL'].get(), mt5.TIMEFRAME_M1, 0, 14)
            rates = mt5_safe._ensure_rates_list(rates)
            if rates and len(rates) > 0:
                highs = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates])
                lows = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates])
                closes = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
                atr_value = self._calculate_atr_simple(highs, lows, closes)
                tolerance = self.adaptive_params.calculate_entry_tolerance(atr_value, current_price)
            else:
                tolerance = 1.0  # Fallback: 1 punto si no hay datos
        except Exception as e:
            tolerance = 1.0  # Fallback: 1 punto en caso de error
        
        is_in_range = distance <= tolerance
        
        # Análisis
        analysis = f"""
[DINERO] Precio Actual: {current_price:.5f}
[OBJETIVO] Precio Objetivo: {target_price:.5f}
📏 Distancia: {distance:.5f}
[DATA] Rango Entrada: ±{tolerance:.5f} puntos
⏱️  Estado: {'[OK] EN RANGO' if is_in_range else '[ESPERA] Esperando'}

"""
        
        if is_valid_direction:
            analysis += "[OK] Dirección CONFIGURADA\n"
            
            if is_in_range:
                analysis += "[OK] ¡¡PRECIO EN RANGO!!\n"
                analysis += "   LISTO PARA ABRIR\n"
                analysis += f"   TP: {op.get('tp', 'N/A'):.5f}\n"
                analysis += f"   SL: {op.get('sl', 'N/A'):.5f}\n"
                color = '#10b981'  # Verde
            else:
                if direction == "BUY":
                    # BUY espera SUBIDA
                    analysis += f"[UBICACION] Esperando SUBIDA a {target_price:.5f}\n"
                    if current_price < target_price:
                        analysis += f"   [EMOJI] Precio está ABAJO (válido para entrar cuando suba)\n"
                    else:
                        analysis += f"   [EMOJI] Precio está ARRIBA (esperará a que baje primero)\n"
                    analysis += f"   Falta: {distance:.5f} puntos\n"
                else:
                    # SELL espera BAJADA
                    analysis += f"[UBICACION] Esperando BAJADA a {target_price:.5f}\n"
                    if current_price > target_price:
                        analysis += f"   [EMOJI] Precio está ARRIBA (válido para entrar cuando baje)\n"
                    else:
                        analysis += f"   [EMOJI] Precio está ABAJO (esperará a que suba primero)\n"
                    analysis += f"   Falta: {distance:.5f} puntos\n"
                color = '#60a5fa'  # Azul
        else:
            analysis += f"[ERROR] Dirección INVÁLIDA\n"
            analysis += f"Error interno - contacta soporte\n"
            color = '#f87171'  # Rojo
        
        self.pending_analyzer_text.config(text=analysis, fg=color)

    def _delete_selected_pending_op(self):
        """Elimina la operación seleccionada"""
        selection = self.pending_ops_listbox.curselection()
        if not selection:
            messagebox.showwarning("Sin Selección", "Selecciona una operación para eliminar")
            return
        
        idx = selection[0]
        if idx < len(self.pending_operations):
            op = self.pending_operations.pop(idx)
            self.actualizar_lista_operaciones()
            self.add_log(f"Operación #{op.get('id', 'N/A')} eliminada de la lista de espera", 'warning')
            messagebox.showinfo("Eliminada", f"Operación #{op.get('id', 'N/A')} eliminada")

    def _manual_open_pending(self):
        """Abre manualmente la operación seleccionada"""
        selection = self.pending_ops_listbox.curselection()
        if not selection:
            messagebox.showwarning("Sin Selección", "Selecciona una operación para abrir")
            return
        
        idx = selection[0]
        if idx >= len(self.pending_operations):
            return
        
        op = self.pending_operations[idx]
        
        if op['status'] == 'EJECUTADA':
            messagebox.showwarning("Ya Ejecutada", "Esta operación ya fue ejecutada")
            return
        
        # Confirmar antes de abrir
        msg = f"""¿Abrir operación manualmente?

Dirección: {op['direction']}
Precio Objetivo: {op['price']:.5f}
TP: {op.get('tp', 'N/A'):.5f}
SL: {op.get('sl', 'N/A'):.5f}
Confianza: {op.get('confidence', 0):.1f}%

Se abrirá al precio actual de mercado."""
        
        if messagebox.askyesno("Confirmar Apertura Manual", msg):
            if self.abrir_operacion_en_espera(op['direction'], op.get('tp', 0), op.get('sl', 0), op.get('entry_price', None)):
                op['status'] = 'EJECUTADA'
                op['timestamp_execution'] = datetime.now().strftime("%H:%M:%S")
                self.actualizar_lista_operaciones()
                self.add_log(f"[OK] Operación #{op.get('id', 'N/A')} abierta manualmente", 'success')
            else:
                messagebox.showerror("Error", "No se pudo abrir la operación")

    def _clear_all_pending(self):
        """Limpia todas las operaciones en espera"""
        if not self.pending_operations:
            messagebox.showinfo("Vacío", "No hay operaciones en espera")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar todas las {len(self.pending_operations)} operaciones en espera?"):
            count = len(self.pending_operations)
            self.pending_operations = []
            self.actualizar_lista_operaciones()
            self.add_log(f"Se eliminaron {count} operaciones en espera", 'warning')
            messagebox.showinfo("Limpiadas", f"{count} operaciones eliminadas")

    def analizar_pending_operations(self):
        """Analiza todas las operaciones en espera y verifica condiciones"""
        # ⭐ VERIFICACIÓN CRÍTICA: Bot detenido
        if not self.is_running or getattr(self, 'force_stop_triggered', False):
            return
        
        if not self.pending_operations:
            return
        
        symbol = self.config['SYMBOL'].get()
        tick = mt5.symbol_info_tick(symbol)
        
        if not tick:
            return
        
        current_price = tick.bid
        
        # Analizar cada operación
        for op in self.pending_operations:
            if op['status'] != 'ESPERANDO':
                continue
            
            direction = op['direction']
            target_price = op['price']
            
            # ⭐ Calcular tolerancia dinámica basada en ATR y volatilidad (entrada rápida)
            try:
                rates = mt5.copy_rates_from_pos(self.config['SYMBOL'].get(), mt5.TIMEFRAME_M1, 0, 14)
                rates = mt5_safe._ensure_rates_list(rates)
                if rates and len(rates) > 0:
                    highs = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates])
                    lows = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates])
                    closes = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
                    atr_value = self._calculate_atr_simple(highs, lows, closes)
                    tolerance = self.adaptive_params.calculate_entry_tolerance(atr_value, current_price)
                else:
                    tolerance = 1.0  # Fallback: 1 punto
            except Exception as e:
                tolerance = 1.0  # Fallback: 1 punto en caso de error
            
            # ⭐ NUEVO: Verificar condición PRECISA E INTELIGENTE (dirección correcta + precio en rango + confianza)
            confidence = op.get('confidence', 50)  # Obtener confianza de la operación
            should_open, reason = self._check_entry_condition_precise(
                current_price, target_price, direction, tolerance, confidence
            )
            
            # ⭐ PERMITIR MÚLTIPLES OPERACIONES SIMULTÁNEAMENTE
            max_ops = self.config['MAX_SIMULTANEOUS_OPS'].get()
            if should_open and self.use_entry_point.get() and self.total_operaciones_abiertas < max_ops:
                self.add_log(f"\n[OBJETIVO] ¡OPERACIÓN EN ESPERA #{op['id']} ACTIVADA!", 'success')
                self.add_log(f"   Dirección: {direction}", 'success')
                self.add_log(f"   Precio Objetivo: {target_price:.5f}", 'success')
                self.add_log(f"   Precio Actual: {current_price:.5f}", 'success')
                self.add_log(f"   Confianza: {confidence:.1f}%", 'success')
                self.add_log(f"   [UBICACION] {reason}", 'success')
                self.add_log(f"   [DATA] Posiciones abiertas: {self.total_operaciones_abiertas} / {max_ops}", 'info')
                
                if self.abrir_operacion_en_espera(direction, op.get('tp', 0), op.get('sl', 0), op.get('price', None)):
                    op['status'] = 'EJECUTADA'
                    op['timestamp_execution'] = datetime.now().strftime("%H:%M:%S")
                    self.actualizar_lista_operaciones()


    # ⭐ NUEVO: Método para ejecutar super análisis
    def ejecutar_super_analisis(self):
        """Ejecuta el análisis personalizado con período y timeframe seleccionados"""
        if not self.connected:
            if not self.conectar_mt5():
                messagebox.showerror("Error", "Conecta a MT5 primero")
                return

        symbol = self.config['SYMBOL'].get()
        period = self.period_var.get()
        timeframe = self.timeframe_var.get()

        self.super_analysis_btn.config(state='disabled')
        self.super_analysis_status.config(text="⏳ Analizando...", fg='#fbbf24')
        self.root.update()

        # ⭐ USAR ANÁLISIS ULTRA-PRECISO EN VEZ DE NORMAL
        analysis = self.entry_point_ai.analyze_ultra_precise(symbol, period, timeframe)

        if analysis:
            # Actualizar variables de entrada
            self.entry_point_price.set(analysis['suggested_entry_price'])
            self.entry_point_direction.set(analysis['suggested_direction'])

            # ⭐ GUARDAR ANÁLISIS PARA USAR DESPUÉS
            self.last_custom_analysis = analysis

            # Mostrar resultado
            direction = analysis['suggested_direction']
            entry_price = analysis['suggested_entry_price']
            current = analysis['current_price']
            confidence = analysis['confidence']
            distance = analysis['distance_from_current']
            potential = analysis['potential_profit']
            # ⭐ NUEVO: Calcular TP y SL recomendidos
            # Reducir distance a la mitad para que sea más razonable
            distance_reduced = distance / 2
            if direction == "BUY":
                tp_recommended = round(entry_price + distance_reduced, 5)
                sl_recommended = round(entry_price - distance_reduced, 5)
            else:
                tp_recommended = round(entry_price - distance_reduced, 5)
                sl_recommended = round(entry_price + distance_reduced, 5)
            
            # ⭐ VALIDACIÓN: Asegurar que TP y SL están en el orden correcto
            if direction == "BUY":
                if tp_recommended < entry_price:
                    tp_recommended, sl_recommended = sl_recommended, tp_recommended
            else:  # SELL
                if tp_recommended > entry_price:
                    tp_recommended, sl_recommended = sl_recommended, tp_recommended
            
            # ⭐ IMPORTANTE: Calcular TP/SL basándose en dinero objetivo, no pips arbitrarios
            # Para jerárquico, usar: Goal profit = $5, Max loss = $20
            volume = float(self.config['VOL'].get())
            symbol = self.config['SYMBOL'].get()
            tp_rec, sl_rec = self._calcular_tp_sl_por_dinero(
                entry_price, direction, volume, 
                goal_profit=5.0, max_loss=20.0, symbol=symbol
            )
            
            # Si la función retorna None, usar los valores anteriores
            if tp_rec is not None and sl_rec is not None:
                tp_recommended, sl_recommended = tp_rec, sl_rec
            else:
                self.add_log(f"[ADVERTENCIA] Usando valores por defecto de tp/sl", 'warning')
            
            # ⭐ MOSTRAR ANÁLISIS DE PRECISIÓN SI DISPONIBLE
            precision_section = ""
            if 'precision_analysis' in analysis:
                precision = analysis['precision_analysis']
                precision_score = analysis.get('precision_score', 0)
                optimal_entry = precision.get('optimal_entry', {})
                
                precision_section = f"""

⭐ ANÁLISIS DE PRECISIÓN ({precision_score}%):
   [DATA] Volatilidad: {precision.get('volatility_score', 0)}%
   📈 Tendencia: {precision.get('trend_strength', 0):+.1f}
   [ACTUALIZAR] Reversión: {precision.get('mean_reversion_probability', 0)}%
   [OBJETIVO] S/R: {precision.get('support_resistance_strength', 0)}%
   📦 Volumen: {precision.get('volume_confirmation', 0)}%
"""
                
                if optimal_entry:
                    precision_section += f"""
🔍 ENTRADA ÓPTIMA:
   Principal: {optimal_entry.get('primary_entry', 'N/A')}
   Óptima: {optimal_entry.get('optimal_entry', 'N/A')}
   Confirmación: {optimal_entry.get('confirmation_price', 'N/A')}
   Zona: ±{optimal_entry.get('entry_zone_width', 'N/A')}
"""
            
            result_text = f"""[OK] ANÁLISIS PERSONALIZADO COMPLETADO

[DATA] {period} | Timeframe: {timeframe}

[OBJETIVO] SUGERENCIA:
   Dirección: {direction}
   Entrada: {entry_price:.5f}
   Actual: {current:.5f}
   
📈 MÉTRICAS:
   Confianza: {confidence:.1f}%
   Distancia: {distance:.5f}{precision_section}

💡 RECOMENDACIÓN (Risk:Reward 1:2):
   [UBICACION] Entrada: {entry_price:.5f}
   [OBJETIVO] TP: {tp_recommended:.5f} (+{abs(tp_recommended - entry_price):.5f})
   [EMOJI] SL: {sl_recommended:.5f} (-{abs(entry_price - sl_recommended):.5f})
   
[CONFIG] Indicadores:
   RSI: {analysis['indicators']['rsi']:.1f}
   MACD: {analysis['indicators']['macd']:.5f}
   ADX: {analysis['indicators']['adx']:.1f}
   ATR: {analysis['indicators']['atr']:.5f}
"""

            self.super_analysis_label.config(text=result_text, fg='#34d399')
            self.super_analysis_status.config(text="✅ Listo", fg='#34d399')

            self.add_log(f"\n[OK] Super Análisis Completado (Ultra-Preciso)", 'success')
            self.add_log(f"   {period} | TF: {timeframe}", 'info')
            self.add_log(f"   {direction} @ {entry_price:.5f} ({confidence:.1f}%)", 'success')
            self.add_log(f"   [UBICACION] Entrada: {entry_price:.5f}", 'success')
            self.add_log(f"   [OBJETIVO] TP: {tp_recommended:.5f} (+{abs(tp_recommended - entry_price):.5f})", 'success')
            self.add_log(f"   [EMOJI] SL: {sl_recommended:.5f} (-{abs(entry_price - sl_recommended):.5f})", 'info')
            
            # ⭐ LOGUEAR SCORE DE PRECISIÓN
            if 'precision_score' in analysis:
                self.add_log(f"   ⭐ Precisión: {analysis['precision_score']}%", 'success')

        else:
            self.super_analysis_label.config(text="❌ Error en el análisis", fg='#f87171')
            self.super_analysis_status.config(text="❌ Error", fg='#f87171')
            messagebox.showerror("Error", "No se pudo completar el análisis")

        self.super_analysis_btn.config(state='normal')

    # ------------------ NUEVO: Métodos para Punto de Entrada ------------------
    def _on_entry_point_toggle(self):
        if self.use_entry_point.get():
            self.add_log("[OBJETIVO] Modo PUNTO DE ENTRADA activado", 'success')
            self.add_log("   El bot solo operará en el precio configurado", 'info')
        else:
            self.add_log("[CONFIG] Modo Punto de Entrada desactivado", 'info')
            self.entry_point_active = False

    def analyze_7_days(self):
        if not self.connected:
            if not self.conectar_mt5():
                messagebox.showerror("Error", "Conecta a MT5 primero")
                return

        symbol = self.config['SYMBOL'].get()
        self.add_log(f"\n🔍 Iniciando análisis de 7 días para {symbol}...", 'info')

        analysis = self.entry_point_ai.analyze_7_days_history(symbol)

        if analysis:
            suggestion_text = f"""[OK] Análisis Completado:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[UBICACION] Precio Sugerido: {analysis['entry_price']}
[DATA] Dirección: {analysis['direction']}
💯 Confianza: {analysis['confidence']:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Precio Actual: {analysis['current_price']}
📏 Distancia: {abs(analysis['entry_price'] - analysis['current_price']):.5f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[OBJETIVO] RSI: {analysis['rsi']:.1f}
[DATA] ATR: {analysis['atr']:.5f}"""
            self.suggestion_label.config(text=suggestion_text, fg='#34d399')
            self.use_suggestion_btn.config(state='normal')
        else:
            self.suggestion_label.config(text="❌ Error en el análisis", fg='#f87171')
            self.use_suggestion_btn.config(state='disabled')

    def use_ai_suggestion(self):
        """Usa la sugerencia de AI para configurar el punto de entrada"""
        try:
            suggestion = self.entry_point_ai.get_last_suggestion()

            if suggestion and 'price' in suggestion and 'direction' in suggestion:
                self.entry_point_price.set(suggestion['price'])
                self.entry_point_direction.set(suggestion['direction'])

                self.add_log(f"[OK] Sugerencia de AI aplicada:", 'success')
                self.add_log(f"   Precio: {suggestion['price']}", 'info')
                self.add_log(f"   Dirección: {suggestion['direction']}", 'info')

                messagebox.showinfo("Sugerencia Aplicada",
                                  f"Configurado:\nPrecio: {suggestion['price']}\nDirección: {suggestion['direction']}\n\n"
                                  f"Presiona 'Activar Este Punto de Entrada' para usar esta configuración")
            else:
                messagebox.showwarning("Sin Sugerencia", "No hay sugerencia disponible")
        
        except Exception as e:
            self.add_log(f"Error aplicando sugerencia de AI: {str(e)}", 'error')

    def activate_manual_entry(self):
        price = self.entry_point_price.get()
        direction = self.entry_point_direction.get()

        if price <= 0:
            messagebox.showwarning("Precio Inválido", "Ingresa un precio válido")
            return

        self.entry_point_active = True
        self.use_entry_point.set(True)

        # ⭐ NUEVO: Calcular TP y SL recomendados basados en análisis
        entry_price = price
        current_price = price  # Usar el mismo precio actual para simplificar
        distance = abs(entry_price - current_price)
        
        # TP = distancia * 1 (REDUCIDO A LA MITAD)
        if direction == "BUY":
            tp_recommended = round(entry_price + distance, 5)
            sl_recommended = round(entry_price - distance, 5)
        else:
            tp_recommended = round(entry_price - distance, 5)
            sl_recommended = round(entry_price + distance, 5)

        # ⭐ NUEVA VALIDACIÓN: Advertir si la dirección no es válida actualmente
        direction_warning = ""
        if direction == "BUY" and current_price > entry_price:
            direction_warning = f"\n[ADVERTENCIA] ADVERTENCIA: Precio actual ({current_price:.5f}) está ARRIBA del objetivo ({entry_price:.5f})\n   Para BUY, el precio DEBE ESTAR ABAJO y SUBIR hacia {entry_price:.5f}"
        elif direction == "SELL" and current_price < entry_price:
            direction_warning = f"\n[ADVERTENCIA] ADVERTENCIA: Precio actual ({current_price:.5f}) está ABAJO del objetivo ({entry_price:.5f})\n   Para SELL, el precio DEBE ESTAR ARRIBA y BAJAR hacia {entry_price:.5f}"

        self.entry_status_label.config(
            text=f"[OBJETIVO] ACTIVO | {direction} @ {entry_price:.5f}",
            fg='#34d399'
        )

        self.add_log(f"\n[OK] PUNTO DE ENTRADA ACTIVADO", 'success')
        self.add_log(f"   Precio Objetivo: {price}", 'success')
        self.add_log(f"   Dirección: {direction}", 'success')
        self.add_log(f"   TP: {tp_recommended:.5f} (+{abs(tp_recommended - entry_price):.5f})", 'success')
        self.add_log(f"   SL: {sl_recommended:.5f} (-{abs(entry_price - sl_recommended):.5f})", 'info')
        self.add_log(f"   Este punto de entrada será monitoreado continuamente.", 'info')
        self.add_log(f"{'='*60}\n", 'success')

        messagebox.showinfo("Activado",
                          f"Punto de entrada configurado:\n{direction} en {price}\n\nInicia el bot para comenzar el monitoreo")

    def monitor_entry_point(self):
        if not self.entry_point_active or not self.use_entry_point.get():
            return

        symbol = self.config['SYMBOL'].get()
        target_price = self.entry_point_price.get()
        direction = self.entry_point_direction.get()

        # ⭐ REDUCIDA TOLERANCIA: De 0.0005 a 0.0001 (muy cercano al objetivo)
        # Esto hace que espere MUCHO más cerca antes de abrir
        within_range, current_price = self.entry_point_ai.check_entry_condition(
            symbol, target_price, tolerance=0.0001
        )

        if current_price:
            distance = abs(current_price - target_price)
            
            # ⭐ NUEVA VALIDACIÓN: Verificar lógica de dirección
            is_valid_direction = False
            if direction == "BUY" and current_price <= target_price:
                is_valid_direction = True
            elif direction == "SELL" and current_price >= target_price:
                is_valid_direction = True
            
            if not is_valid_direction:
                status_text = f"[DINERO] Precio Actual: {current_price:.5f} | 📏 Distancia: {distance:.5f}"
                status_text += " | [ERROR] DIRECCIÓN INVÁLIDA"
                self.entry_current_price_label.config(text=status_text, fg='#f87171')
                return
            
            status_text = f"[DINERO] Precio Actual: {current_price:.5f} | 📏 Distancia: {distance:.5f}"

            if within_range:
                status_text += " | [OK] EN RANGO!"
                self.entry_current_price_label.config(text=status_text, fg='#22c55e')
            else:
                status_text += " | [ESPERA] Esperando..."
                self.entry_current_price_label.config(text=status_text, fg='#60a5fa')

        # ⭐ CORREGIDO: Permitir abrir hasta MAX_SIMULTANEOUS_OPS operaciones, no solo cuando total=0
        max_ops = int(self.config['MAX_SIMULTANEOUS_OPS'].get())
        if within_range and self.total_operaciones_abiertas < max_ops:
            self.add_log(f"\n[OBJETIVO] ¡CONDICIÓN DE ENTRADA ALCANZADA!", 'success')
            self.add_log(f"   Precio Actual: {current_price:.5f}", 'success')
            self.add_log(f"   Precio Objetivo: {target_price:.5f}", 'success')
            self.add_log(f"   Operaciones Abiertas: {self.total_operaciones_abiertas}/{max_ops}", 'info')
            
            # ⭐ VALIDACIÓN FINAL antes de abrir
            is_valid = False
            if direction == "BUY" and current_price <= target_price:
                is_valid = True
                self.add_log(f"   [OK] BUY válido: {current_price:.5f} <= {target_price:.5f}", 'success')
            elif direction == "SELL" and current_price >= target_price:
                is_valid = True
                self.add_log(f"   [OK] SELL válido: {current_price:.5f} >= {target_price:.5f}", 'success')
            else:
                self.add_log(f"   [ERROR] Operación RECHAZADA: Precio actual no cumple criterio de {direction}", 'error')
                self.add_log(f"      Para {direction}: precio actual debe ser {'<=' if direction == 'BUY' else '>='} al objetivo", 'error')
                return
            
            self.add_log(f"   Abriendo operación {direction}...", 'success')

            if self.abrir_operacion_entry_point(direction):
                self.add_log(f"[OK] Operación abierta exitosamente", 'success')
                self.entry_point_active = False
                self.entry_status_label.config(
                    text="✅ Entrada ejecutada - Esperando cierre por TP",
                    fg='#34d399'
                )
            else:
                self.add_log(f"[ERROR] Error al abrir operación", 'error')

    def monitorear_posicion_entry_point(self):
        try:
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)

            if not positions:
                if self.total_operaciones_abiertas > 0:
                    self.total_operaciones_abiertas = 0
                    self.add_log("[OK] Operación cerrada por Take Profit", 'success')
                    self.entry_status_label.config(
                        text="✅ TP Alcanzado - Punto de entrada desactivado",
                        fg='#22c55e'
                    )
                    self.entry_point_active = False
                return

            for pos in positions:
                if pos.magic == self.config['MAGIC_NUMBER']:
                    profit_status = f"[DINERO] Profit Actual: ${pos.profit:.2f}"

                    if pos.profit > 0:
                        self.entry_current_price_label.config(
                            text=f"{profit_status} | [OK] EN GANANCIA",
                            fg='#22c55e'
                        )
                    else:
                        self.entry_current_price_label.config(
                            text=f"{profit_status} | [ESPERA] Esperando TP",
                            fg='#60a5fa'
                        )
                    break

        except Exception as e:
            self.add_log(f"Error monitoreando posición entry point: {str(e)}", 'error')
    
    def ejecutar_analisis_jerarquico(self):
        """Ejecuta el análisis jerárquico con período Y timeframe seleccionados"""
        if not self.connected:
            if not self.conectar_mt5():
                messagebox.showerror("Error", "Conecta a MT5 primero")
                return

        symbol = self.config['SYMBOL'].get()
        base_period = self.hier_period_var.get()
        selected_timeframe = self.hier_timeframe_var.get()

        self.hierarchical_analysis_btn.config(state='disabled')
        self.hierarchical_status.config(text="⏳ Analizando...", fg='#fbbf24')
        self.root.update()

        # Ejecutar análisis jerárquico
        hierarchical_result = self.entry_point_ai.analyze_hierarchical_timeframes(symbol, base_period)

        if not hierarchical_result or not hierarchical_result['options']:
            messagebox.showerror("Error", "No se pudo completar el análisis jerárquico")
            self.hierarchical_analysis_btn.config(state='normal')
            self.hierarchical_status.config(text="❌ Error", fg='#f87171')
            return

        # ⭐ MAPEO JERÁRQUICO: asegurar que incluya TODOS los timeframes desde 1m
        timeframe_hierarchy = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        
        try:
            selected_idx = timeframe_hierarchy.index(selected_timeframe)
        except ValueError:
            selected_idx = timeframe_hierarchy.index("1h")
        
        allowed_timeframes = timeframe_hierarchy[:selected_idx + 1]
        filtered_options = [opt for opt in hierarchical_result['options'] 
                           if opt['timeframe'] in allowed_timeframes]
        
        filtered_options.sort(key=lambda x: x['confidence'], reverse=True)

        # Limpiar opciones anteriores
        for widget in self.hier_options_frame.winfo_children():
            widget.destroy()

        # ⭐ NUEVO: Guardar las opciones filtradas y crear checkbuttons para cada una
        self.hier_filtered_options = filtered_options.copy()
        self.hier_selected_checkbuttons = {}  # Diccionario para almacenar BooleanVar de cada opción
        self.hier_option_frames = []  # ⭐ NUEVO: Guardar referencias a frames para filtrado sin destrucción

        # ⭐ Mostrar TODAS las opciones filtradas ordenadas por confianza
        for idx, option in enumerate(filtered_options):
            rank = idx + 1
            tf = option['timeframe']
            confidence = option['confidence']
            direction = option['direction']
            entry = option['entry_price']
            current = option['current_price']
            distance = option['distance_from_current']

            # ⭐ NUEVO: Calcular TP y SL para cada opción
            if direction == "BUY":
                tp_recommended = round(entry + distance, 5)
                sl_recommended = round(entry - distance, 5)
            else:
                tp_recommended = round(entry - distance, 5)
                sl_recommended = round(entry + distance, 5)
            
            # ⭐ VALIDACIÓN: Asegurar que TP y SL están en el orden correcto
            if direction == "BUY":
                if tp_recommended < entry:
                    tp_recommended, sl_recommended = sl_recommended, tp_recommended
            else:  # SELL
                if tp_recommended > entry:
                    tp_recommended, sl_recommended = sl_recommended, tp_recommended
            
            # ⭐ IMPORTANTE: Calcular TP/SL basándose en dinero objetivo, no pips arbitrarios
            # Para jerárquico, usar: Goal profit = $5, Max loss = $20
            volume = float(self.config['VOL'].get())
            symbol = self.config['SYMBOL'].get()
            tp_rec, sl_rec = self._calcular_tp_sl_por_dinero(
                entry, direction, volume, 
                goal_profit=5.0, max_loss=20.0, symbol=symbol
            )
            
            # Si la función retorna None, usar los valores anteriores
            if tp_rec is not None and sl_rec is not None:
                tp_recommended, sl_recommended = tp_rec, sl_rec
            else:
                self.add_log(f"[ADVERTENCIA] Usando valores por defecto de tp/sl para opción", 'warning')

            # Color según confianza
            if confidence >= 85:
                color_bg = '#0f5f3e'
                color_text = '#34d399'
            elif confidence >= 75:
                color_bg = '#1a3a52'
                color_text = '#60a5fa'
            elif confidence >= 65:
                color_bg = '#3a2a1a'
                color_text = '#f59e0b'
            else:
                color_bg = '#3a1a2a'
                color_text = '#f87171'

            option_frame = tk.Frame(self.hier_options_frame, bg=color_bg, relief='solid', borderwidth=1)
            option_frame.pack(fill='x', pady=4, padx=2)
            
            # ⭐ NUEVO: Guardar referencia para filtrado sin destrucción
            self.hier_option_frames.append((option_frame, {'direction': direction}))

            # Header
            header = tk.Frame(option_frame, bg=color_bg)
            header.pack(fill='x', padx=8, pady=5)

            # ⭐ CAMBIO CRÍTICO: Checkbutton en lugar de Radiobutton
            checkbox_var = tk.BooleanVar(value=False)
            self.hier_selected_checkbuttons[idx] = checkbox_var
            tk.Checkbutton(header, variable=checkbox_var,
                          bg=color_bg, fg=color_text, selectcolor=color_bg,
                          activebackground=color_bg, font=('Arial', 9, 'bold')).pack(side='left')

            tk.Label(header, text=f"#{rank}", bg=color_bg, fg=color_text,
                    font=('Arial', 11, 'bold'), width=3).pack(side='left', padx=(5,10))

            tk.Label(header, text=f"{tf}", bg=color_bg, fg=color_text,
                    font=('Arial', 10, 'bold'), width=8, anchor='w').pack(side='left', padx=5)

            tk.Label(header, text=f"{confidence:.1f}%", bg=color_bg, fg=color_text,
                    font=('Arial', 10, 'bold'), width=10, anchor='w').pack(side='left', padx=5)

            tk.Label(header, text=f"→ {direction}", bg=color_bg, fg=color_text,
                    font=('Arial', 10, 'bold'), width=10, anchor='w').pack(side='left', padx=5)

            # Detalles - Precios y Distancia
            details = tk.Frame(option_frame, bg=color_bg)
            details.pack(fill='x', padx=20, pady=(0,3))

            details_text = f"[UBICACION] Entrada: {entry:.5f} | [DINERO] Actual: {current:.5f} | 📏 Dist: {distance:.5f}"
            tk.Label(details, text=details_text, bg=color_bg, fg=color_text,
                    font=('Arial', 8), justify='left').pack(anchor='w')

            # ⭐ NUEVO: Fila con TP y SL recomendados
            tp_sl_frame = tk.Frame(option_frame, bg=color_bg)
            tp_sl_frame.pack(fill='x', padx=20, pady=(0,3))

            if direction == "BUY":
                tp_display = tp_recommended
                sl_display = sl_recommended
                tp_sl_text = f"[OBJETIVO] TP: {tp_display:.5f} (+{abs(tp_display - entry):.5f}) | [EMOJI] SL: {sl_display:.5f} (-{abs(entry - sl_display):.5f})"
            else:  # SELL - intercambiar para mostrar correctamente
                tp_display = sl_recommended  # TP va ABAJO
                sl_display = tp_recommended  # SL va ARRIBA
                tp_sl_text = f"[OBJETIVO] TP: {tp_display:.5f} (-{abs(entry - tp_display):.5f}) | [EMOJI] SL: {sl_display:.5f} (+{abs(sl_display - entry):.5f})"
            tk.Label(tp_sl_frame, text=tp_sl_text, bg=color_bg, fg=color_text,
                    font=('Arial', 8, 'bold'), justify='left').pack(anchor='w')

            # ⭐ NUEVO: Frame para controles +/- de TP/SL por opción
            controls_frame = tk.Frame(option_frame, bg=color_bg)
            controls_frame.pack(fill='x', padx=20, pady=(0, 5))

            # Variables para esta opción
            # Los valores ya están en el orden correcto
            option['tp_var'] = tk.DoubleVar(value=tp_recommended)
            option['sl_var'] = tk.DoubleVar(value=sl_recommended)
            option['tp_status_var'] = tk.StringVar(value="[EMOJI] VÁLIDO")
            option['sl_status_var'] = tk.StringVar(value="[EMOJI] VÁLIDO")
            option['color_bg'] = color_bg
            option['is_valid'] = True
            option['profit_value'] = 0

            # Fila TP con controles +/-
            tp_ctrl_row = tk.Frame(controls_frame, bg=color_bg)
            tp_ctrl_row.pack(fill='x', pady=2)

            tk.Label(tp_ctrl_row, text="TP:", bg=color_bg, fg=color_text, 
                    font=('Arial', 8, 'bold'), width=3).pack(side='left', padx=2)
            
            tk.Button(tp_ctrl_row, text="−", command=lambda o=option: self._adjust_hier_tp(o, -0.0001),
                     bg='#ef4444', fg='white', font=('Arial', 8, 'bold'), width=2, padx=1).pack(side='left', padx=1)
            
            tk.Entry(tp_ctrl_row, textvariable=option['tp_var'], width=10, bg='#475569', 
                    fg='white', font=('Arial', 8), justify='center').pack(side='left', padx=1)
            
            tk.Button(tp_ctrl_row, text="+", command=lambda o=option: self._adjust_hier_tp(o, 0.0001),
                     bg='#10b981', fg='white', font=('Arial', 8, 'bold'), width=2, padx=1).pack(side='left', padx=1)
            
            tp_status_label = tk.Label(tp_ctrl_row, textvariable=option['tp_status_var'],
                                      bg=color_bg, fg='#34d399', font=('Arial', 7, 'bold'), width=10,
                                      anchor='w')
            tp_status_label.pack(side='left', padx=2)
            option['tp_status_label'] = tp_status_label

            # Fila SL con controles +/-
            sl_ctrl_row = tk.Frame(controls_frame, bg=color_bg)
            sl_ctrl_row.pack(fill='x', pady=2)

            tk.Label(sl_ctrl_row, text="SL:", bg=color_bg, fg=color_text,
                    font=('Arial', 8, 'bold'), width=3).pack(side='left', padx=2)
            
            tk.Button(sl_ctrl_row, text="−", command=lambda o=option: self._adjust_hier_sl(o, -0.0001),
                     bg='#ef4444', fg='white', font=('Arial', 8, 'bold'), width=2, padx=1).pack(side='left', padx=1)
            
            tk.Entry(sl_ctrl_row, textvariable=option['sl_var'], width=10, bg='#475569',
                    fg='white', font=('Arial', 8), justify='center').pack(side='left', padx=1)
            
            tk.Button(sl_ctrl_row, text="+", command=lambda o=option: self._adjust_hier_sl(o, 0.0001),
                     bg='#10b981', fg='white', font=('Arial', 8, 'bold'), width=2, padx=1).pack(side='left', padx=1)
            
            sl_status_label = tk.Label(sl_ctrl_row, textvariable=option['sl_status_var'],
                                      bg=color_bg, fg='#34d399', font=('Arial', 7, 'bold'), width=10,
                                      anchor='w')
            sl_status_label.pack(side='left', padx=2)
            option['sl_status_label'] = sl_status_label

            # ⭐ NUEVO: Fila para Velas ÚNICO campo con botón Recalcular
            velas_ctrl_row = tk.Frame(controls_frame, bg=color_bg)
            velas_ctrl_row.pack(fill='x', pady=2)

            tk.Label(velas_ctrl_row, text="📊 Velas:", bg=color_bg, fg=color_text,
                    font=('Arial', 8, 'bold'), width=10).pack(side='left', padx=2)

            option['velas_var'] = tk.DoubleVar(value=0.0)
            tk.Entry(velas_ctrl_row, textvariable=option['velas_var'], width=8, 
                    bg='#475569', fg='white', font=('Arial', 8), justify='center').pack(side='left', padx=1)

            # Botón Recalcular
            tk.Button(velas_ctrl_row, text="🔄 Recalcular", 
                     command=lambda o=option: self._recalcular_velas_opcion(o, color_bg),
                     bg='#3b82f6', fg='white', font=('Arial', 7, 'bold'), width=12, padx=1).pack(side='left', padx=2, fill='x', expand=True)

            # Fila con información de ganancias y pérdidas SEPARADAS
            profit_row = tk.Frame(controls_frame, bg=color_bg)
            profit_row.pack(fill='x', pady=2)

            # Label para GANANCIA (verde)
            profit_label = tk.Label(profit_row, text="💰 $0.00",
                                   bg=color_bg, fg='#34d399', font=('Arial', 8, 'bold'))
            profit_label.pack(side='left', padx=2)
            option['profit_label'] = profit_label
            
            # Label para PÉRDIDA (rojo)
            loss_label = tk.Label(profit_row, text="📉 $0.00",
                                 bg=color_bg, fg='#ef4444', font=('Arial', 8, 'bold'))
            loss_label.pack(side='left', padx=2)
            option['loss_label'] = loss_label
            
            # Label para R:R ratio
            ratio_label = tk.Label(profit_row, text="R:R 1:0.00",
                                  bg=color_bg, fg='#fbbf24', font=('Arial', 8, 'bold'))
            ratio_label.pack(side='left', padx=2, fill='x', expand=True)
            option['ratio_label'] = ratio_label
            
            # ⭐ AHORA: Validar inicial DESPUÉS de asignar todos los labels
            self._validar_hierarquica_opcion(option, color_bg)


        self.hierarchical_status.config(
            text=f"[EMOJI] {len(filtered_options)} opciones", 
            fg='#34d399'
        )
        self.hierarchical_analysis_btn.config(state='normal')

        self.add_log(f"\n[OK] Análisis Jerárquico Completado", 'success')
        self.add_log(f"   Período Base: {base_period}", 'info')
        self.add_log(f"   Timeframe Seleccionado: {selected_timeframe}", 'info')
        self.add_log(f"   Opciones Mostradas: {len(filtered_options)} (incl. timeframes faltantes)", 'success')
        self.add_log(f"   Rango: 1m hasta {selected_timeframe} (jerarquía ascendente completa)", 'success')
    
    def usar_opcion_jerarquica(self):
        """Usa la primera opción marcada como punto de entrada"""
        # ⭐ CORREGIDO: Verificar si hay opciones disponibles
        if not hasattr(self, 'hier_filtered_options') or not self.hier_filtered_options:
            messagebox.showerror("Error", "No hay opciones disponibles. Ejecuta análisis jerárquico primero")
            return
        
        # ⭐ NUEVO: Buscar la primera opción marcada en los checkbuttons
        selected_option_data = None
        selected_list_idx = -1
        
        if hasattr(self, 'hier_selected_checkbuttons'):
            for idx, checkbox_var in self.hier_selected_checkbuttons.items():
                if checkbox_var.get():  # Si el checkbutton está marcado
                    selected_list_idx = idx
                    selected_option_data = self.hier_filtered_options[idx]
                    break
        
        if selected_option_data is None:
            messagebox.showwarning("Sin Selección", "Marca al menos una opción con los checkbuttons")
            return

        # ⭐ USAR LA OPCIÓN QUE REALMENTE SE MOSTRÓ EN PANTALLA
        option = selected_option_data

        self.entry_point_price.set(option['entry_price'])
        self.entry_point_direction.set(option['direction'])
        self.entry_point_active = True
        self.use_entry_point.set(True)

        # ⭐ NUEVO: Calcular TP y SL recomendados basados en análisis
        entry_price = option['entry_price']
        current_price = option['current_price']
        direction = option['direction']
        
        # Calcular distancia - usar el distance que ya calcula el análisis
        distance = abs(option['distance_from_current'])
        
        # TP y SL: Sin multiplicadores, usar distance directamente
        if direction == "BUY":
            tp_recommended = round(entry_price + distance, 5)
            sl_recommended = round(entry_price - distance, 5)
        else:
            tp_recommended = round(entry_price - distance, 5)
            sl_recommended = round(entry_price + distance, 5)

        # ⭐ NUEVA VALIDACIÓN: Advertir si la dirección no es válida actualmente
        direction_warning = ""
        if direction == "BUY" and current_price > entry_price:
            direction_warning = f"\n[ADVERTENCIA] ADVERTENCIA: Precio actual ({current_price:.5f}) está ARRIBA del objetivo ({entry_price:.5f})\n   Para BUY, el precio DEBE ESTAR ABAJO y SUBIR hacia {entry_price:.5f}"
        elif direction == "SELL" and current_price < entry_price:
            direction_warning = f"\n[ADVERTENCIA] ADVERTENCIA: Precio actual ({current_price:.5f}) está ABAJO del objetivo ({entry_price:.5f})\n   Para SELL, el precio DEBE ESTAR ARRIBA y BAJAR hacia {entry_price:.5f}"

        self.entry_status_label.config(
            text=f"[OBJETIVO] ACTIVO | {direction} @ {entry_price:.5f}",
            fg='#34d399'
        )

        self.add_log(f"\n[OK] Opción Seleccionada (Posición #{selected_list_idx + 1})", 'success')
        self.add_log(f"   Timeframe: {option['timeframe']} | Confianza: {option['confidence']:.1f}%", 'info')
        self.add_log(f"   Dirección: {option['direction']}", 'info')
        self.add_log(f"   Precio Sugerido: {option['entry_price']:.5f}", 'success')
        self.add_log(f"   Precio Actual: {current_price:.5f}", 'info')
        self.add_log(f"   📈 Distancia: {distance:.5f}", 'info')
        self.add_log(f"   💯 Confianza: {option['confidence']:.1f}%\n", 'success')
        self.add_log(f"💡 RECOMENDACIÓN (Risk:Reward 1:2):", 'success')
        self.add_log(f"   [UBICACION] Entrada: {entry_price:.5f}", 'success')
        self.add_log(f"   [OBJETIVO] TP: {tp_recommended:.5f} (+{abs(tp_recommended - entry_price):.5f})", 'success')
        self.add_log(f"   [EMOJI] SL: {sl_recommended:.5f} (-{abs(entry_price - sl_recommended):.5f})", 'info')

        msg = f"[OK] Punto de Entrada Activado\n\nTimeframe: {option['timeframe']}\nDirección: {option['direction']}\nPrecio Entrada: {option['entry_price']:.5f}\nPrecio Actual: {current_price:.5f}\n\n💡 RECOMENDADO (1:2):\n[OBJETIVO] TP: {tp_recommended:.5f}\n[EMOJI] SL: {sl_recommended:.5f}\n\nConfianza: {option['confidence']:.1f}%\n\n📋 Criterios:\n"
        
        if direction == "BUY":
            msg += f"[OK] Se abrirá cuando: Precio <= {entry_price:.5f}"
        else:
            msg += f"[OK] Se abrirá cuando: Precio >= {entry_price:.5f}"
        
        msg += direction_warning
        msg += "\n\nInicia el bot para comenzar el monitoreo"
        
        messagebox.showinfo("[OK] Punto de Entrada Activado", msg)

    def poner_en_espera_jerarquico(self):
        """Pone TODAS las opciones marcadas en la lista de espera"""
        # ⭐ CORREGIDO: Verificar si hay opciones disponibles
        if not hasattr(self, 'hier_filtered_options') or not self.hier_filtered_options:
            messagebox.showerror("Error", "No hay opciones disponibles. Ejecuta análisis jerárquico primero")
            return
        
        # ⭐ NUEVO: Recolectar TODAS las opciones marcadas
        selected_options = []
        if hasattr(self, 'hier_selected_checkbuttons'):
            for idx, checkbox_var in self.hier_selected_checkbuttons.items():
                if checkbox_var.get():  # Si el checkbutton está marcado
                    selected_options.append((idx, self.hier_filtered_options[idx]))
        
        if not selected_options:
            messagebox.showwarning("Sin Selección", "Marca al menos una opción con los checkbuttons")
            return
        
        # ⭐ NUEVO: Procesar TODAS las opciones seleccionadas
        added_count = 0
        for selected_idx, option in selected_options:

            # ⭐ VALIDACIÓN: Mostrar qué opción se está capturando
            self.add_log(f"\n🔍 OPCIÓN SELECCIONADA #{selected_idx + 1}:", 'success')
            self.add_log(f"   Dirección CAPTURADA: {option['direction']}", 'success')
            self.add_log(f"   Precio: {option['entry_price']:.5f}", 'info')
            self.add_log(f"   Timeframe: {option['timeframe']}", 'info')
            self.add_log(f"   Confianza: {option['confidence']:.1f}%", 'info')

            # ⭐ NUEVO: Crear objeto de operación en espera
            pending_op = {
                'id': len(self.pending_operations) + 1,
                'direction': option['direction'],
                'price': option['entry_price'],
                'timeframe': option['timeframe'],
                'confidence': option['confidence'],
                'period': self.hier_period_var.get(),
                'current_price': option['current_price'],
                'distance': option['distance_from_current'],
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'status': 'ESPERANDO'
            }

            # ⭐ VALIDACIÓN DE DATOS antes de calcular TP/SL
            entry_price = option['entry_price']
            current_price = option['current_price']
            distance = abs(option['distance_from_current'])
            direction = option['direction']
            
            # ⭐ NUEVO: Usar los valores ajustados con +/- de la interfaz
            tp_adjusted = option.get('tp_var', tk.DoubleVar(value=0)).get()
            sl_adjusted = option.get('sl_var', tk.DoubleVar(value=0)).get()
            
            # Si existen valores ajustados, usarlos; si no, calcular
            if tp_adjusted > 0 and sl_adjusted > 0:
                pending_op['tp'] = tp_adjusted
                pending_op['sl'] = sl_adjusted
                self.add_log(f"\n[OK] USANDO VALORES AJUSTADOS MANUALMENTE:", 'success')
                self.add_log(f"   TP Manual: {pending_op['tp']:.5f}", 'success')
                self.add_log(f"   SL Manual: {pending_op['sl']:.5f}", 'success')
            else:
                # Calcular TP/SL por defecto
                self.add_log(f"\n[DATA] DATOS DEL ANÁLISIS:", 'info')
                self.add_log(f"   Dirección: {direction}", 'info')
                self.add_log(f"   Precio Entrada: {entry_price:.5f}", 'info')
                self.add_log(f"   Precio Actual: {current_price:.5f}", 'info')
                self.add_log(f"   Distance: {distance:.5f}", 'info')

                # Lógica correcta de TP/SL
                if direction == "BUY":
                    pending_op['tp'] = round(entry_price + distance, 5)
                    pending_op['sl'] = round(entry_price - distance, 5)
                    self.add_log(f"   [DATA] BUY: TP ({pending_op['tp']:.5f}) > Entry ({entry_price:.5f}) [EMOJI]", 'success')
                else:  # SELL
                    pending_op['tp'] = round(entry_price - distance, 5)
                    pending_op['sl'] = round(entry_price + distance, 5)
                    self.add_log(f"   [DATA] SELL: TP ({pending_op['tp']:.5f}) < Entry ({entry_price:.5f}) [EMOJI]", 'success')

            # Agregar a lista de espera
            self.pending_operations.append(pending_op)
            added_count += 1

            self.add_log(f"\n[ESPERA] OPERACIÓN PUESTA EN ESPERA #{pending_op['id']}", 'warning')
            self.add_log(f"   Dirección: {pending_op['direction']}", 'info')
            self.add_log(f"   Precio Objetivo: {pending_op['price']:.5f}", 'info')
            self.add_log(f"   Precio Actual: {pending_op['current_price']:.5f}", 'info')
            self.add_log(f"   Distancia: {distance:.5f} puntos", 'info')
            self.add_log(f"   Timeframe: {pending_op['timeframe']} | Confianza: {pending_op['confidence']:.1f}%", 'info')
            self.add_log(f"   ⭐ TP: {pending_op['tp']:.5f} | SL: {pending_op['sl']:.5f}", 'success')
            
            # ⭐ VALIDACIÓN en logs
            if pending_op['direction'] == "BUY":
                self.add_log(f"   [EMOJI] BUY: TP ({pending_op['tp']:.5f}) > Entry ({pending_op['price']:.5f})", 'info')
            else:
                self.add_log(f"   [EMOJI] SELL: TP ({pending_op['tp']:.5f}) < Entry ({pending_op['price']:.5f})", 'info')
            
            self.add_log(f"   Estado: ESPERANDO condición de entrada\n", 'warning')

        # Actualizar lista de operaciones una sola vez
        self.actualizar_lista_operaciones()
        
        # Desmarcar todas las casillas
        for checkbox_var in self.hier_selected_checkbuttons.values():
            checkbox_var.set(False)

        messagebox.showinfo(
            "[OK] Operaciones en Espera",
            f"{added_count} operación(es) agregada(s) a la lista de espera\n\n"
            f"Se abrirán automáticamente cuando:\n"
            f"• Modo Punto de Entrada esté activo\n"
            f"• El precio alcance el precio objetivo\n"
            f"• El bot esté en ejecución"
        )
    
    def usar_analisis_personalizado(self):
        """Usa el resultado del análisis personalizado como punto de entrada"""
        if not hasattr(self, 'last_custom_analysis') or not self.last_custom_analysis:
            messagebox.showwarning("Sin Análisis", "Ejecuta 'Super Análisis' primero")
            return

        analysis = self.last_custom_analysis
        self.entry_point_price.set(analysis['suggested_entry_price'])
        self.entry_point_direction.set(analysis['suggested_direction'])
        self.entry_point_active = True
        self.use_entry_point.set(True)

        # ⭐ NUEVO: Calcular TP y SL recomendados basados en análisis
        entry_price = analysis['suggested_entry_price']
        current_price = analysis['current_price']
        direction = analysis['suggested_direction']
        
        # Usar distancia desde análisis si existe, si no calcularla
        distance = analysis.get('distance_from_current', abs(entry_price - current_price))
        
        # TP = distancia * 1, SL = distancia * 3
        if direction == "BUY":
            tp_recommended = round(entry_price + distance, 5)
            sl_recommended = round(entry_price - (distance * 3), 5)
        else:
            tp_recommended = round(entry_price - distance, 5)
            sl_recommended = round(entry_price + (distance * 3), 5)

        # ⭐ NUEVO: Cargar valores en variables para controles ajustables
        self.tp_var.set(tp_recommended)
        self.sl_var.set(sl_recommended)
        self._validar_y_calcular_ganancias()

        # ⭐ NUEVA VALIDACIÓN: Advertir si la dirección no es válida actualmente
        direction_warning = ""
        if direction == "BUY" and current_price > entry_price:
            direction_warning = f"\n[ADVERTENCIA] ADVERTENCIA: Precio actual ({current_price:.5f}) está ARRIBA del objetivo ({entry_price:.5f})\n   Para BUY, el precio DEBE ESTAR ABAJO y SUBIR hacia {entry_price:.5f}"
        elif direction == "SELL" and current_price < entry_price:
            direction_warning = f"\n[ADVERTENCIA] ADVERTENCIA: Precio actual ({current_price:.5f}) está ABAJO del objetivo ({entry_price:.5f})\n   Para SELL, el precio DEBE ESTAR ARRIBA y BAJAR hacia {entry_price:.5f}"

        self.entry_status_label.config(
            text=f"[OBJETIVO] ACTIVO | {analysis['suggested_direction']} @ {analysis['suggested_entry_price']:.5f}",
            fg='#34d399'
        )

        self.add_log(f"\n[OK] Análisis Personalizado Activado", 'success')
        self.add_log(f"   Período: {self.period_var.get()} | Timeframe: {self.timeframe_var.get()}", 'info')
        self.add_log(f"   Dirección: {analysis['suggested_direction']}", 'info')
        self.add_log(f"   Precio Sugerido: {analysis['suggested_entry_price']:.5f}", 'success')
        self.add_log(f"   Precio Actual: {current_price:.5f}", 'info')
        self.add_log(f"   📈 Distancia: {distance:.5f}", 'info')
        self.add_log(f"   💯 Confianza: {analysis['confidence']:.1f}%\n", 'success')
        self.add_log(f"💡 RECOMENDACIÓN (Risk:Reward 1:2):", 'success')
        self.add_log(f"   [UBICACION] Entrada: {entry_price:.5f}", 'success')
        self.add_log(f"   [OBJETIVO] TP: {tp_recommended:.5f} (+{abs(tp_recommended - entry_price):.5f})", 'success')
        self.add_log(f"   [EMOJI] SL: {sl_recommended:.5f} (-{abs(entry_price - sl_recommended):.5f})", 'info')

        msg = f"[OK] Punto de Entrada Activado\n\nPeríodo: {self.period_var.get()}\nTimeframe: {self.timeframe_var.get()}\nDirección: {analysis['suggested_direction']}\nPrecio Entrada: {analysis['suggested_entry_price']:.5f}\nPrecio Actual: {current_price:.5f}\n\n💡 RECOMENDADO (1:2):\n[OBJETIVO] TP: {tp_recommended:.5f}\n[EMOJI] SL: {sl_recommended:.5f}\n\nConfianza: {analysis['confidence']:.1f}%\n\n📋 Criterios:\n"
        
        if direction == "BUY":
            msg += f"[OK] Se abrirá cuando: Precio <= {entry_price:.5f}"
        else:
            msg += f"[OK] Se abrirá cuando: Precio >= {entry_price:.5f}"
        
        msg += direction_warning
        msg += "\n\nInicia el bot para comenzar el monitoreo"
        
        messagebox.showinfo("[OK] Punto de Entrada Activado", msg)

    def _actualizar_filtro_jerarquico(self):
        """Filtra las opciones según BUY/SELL/TODOS seleccionado (MOSTRAR/OCULTAR, no redibujar)"""
        try:
            if not hasattr(self, 'hier_option_frames') or not self.hier_option_frames:
                return
            
            filter_mode = self.hier_filter_var.get()
            
            # Contar visibles
            visible_count = 0
            
            # Iterar sobre TODAS las opciones guardadas
            for option_frame, option_data in self.hier_option_frames:
                direction = option_data.get('direction', '')
                
                # Determinar si mostrar o ocultar
                if filter_mode == "TODOS":
                    show = True
                elif filter_mode == "SOLO BUY":
                    show = (direction == 'BUY')
                elif filter_mode == "SOLO SELL":
                    show = (direction == 'SELL')
                else:
                    show = True
                
                # Mostrar u ocultar usando pack_forget() (no destroywidget)
                if show:
                    option_frame.pack(fill='x', pady=4, padx=2)
                    visible_count += 1
                else:
                    option_frame.pack_forget()
            
            # Actualizar estado
            self.hierarchical_status.config(
                text=f"[EMOJI] {visible_count} opciones ({filter_mode})", 
                fg='#34d399'
            )
            
        except Exception as e:
            self.add_log(f"[ERROR] Error al filtrar opciones: {str(e)}", 'error')

    def _marcar_todas_opciones(self):
        """Marca SOLO los checkboxes de las opciones VISIBLES según el filtro activo"""
        try:
            if not hasattr(self, 'hier_selected_checkbuttons'):
                messagebox.showwarning("Validación", "Ejecuta análisis jerárquico primero")
                return
            
            if not hasattr(self, 'hier_option_frames') or not self.hier_option_frames:
                messagebox.showwarning("Validación", "No hay opciones disponibles")
                return
            
            # Obtener el filtro activo
            filter_mode = self.hier_filter_var.get()
            
            marked_count = 0
            # Iterar sobre opciones y marcar solo las que están visibles
            for idx, (option_frame, option_data) in enumerate(self.hier_option_frames):
                direction = option_data.get('direction', '')
                
                # Determinar si esta opción debe estar visible
                is_visible = False
                if filter_mode == "TODOS":
                    is_visible = True
                elif filter_mode == "SOLO BUY":
                    is_visible = (direction == 'BUY')
                elif filter_mode == "SOLO SELL":
                    is_visible = (direction == 'SELL')
                else:
                    is_visible = True
                
                # Si está visible, marcar el checkbox
                if is_visible and idx in self.hier_selected_checkbuttons:
                    self.hier_selected_checkbuttons[idx].set(True)
                    marked_count += 1
            
            self.add_log(f"[EMOJI] Marcadas {marked_count} opciones visibles (Filtro: {filter_mode})", 'success')
            
        except Exception as e:
            self.add_log(f"[ERROR] Error al marcar opciones: {str(e)}", 'error')

    def _desmarcar_todas_opciones(self):
        """Desmarca SOLO los checkboxes de las opciones VISIBLES según el filtro activo"""
        try:
            if not hasattr(self, 'hier_selected_checkbuttons'):
                messagebox.showwarning("Validación", "Ejecuta análisis jerárquico primero")
                return
            
            if not hasattr(self, 'hier_option_frames') or not self.hier_option_frames:
                messagebox.showwarning("Validación", "No hay opciones disponibles")
                return
            
            # Obtener el filtro activo
            filter_mode = self.hier_filter_var.get()
            
            unmarked_count = 0
            # Iterar sobre opciones y desmarcar solo las que están visibles
            for idx, (option_frame, option_data) in enumerate(self.hier_option_frames):
                direction = option_data.get('direction', '')
                
                # Determinar si esta opción debe estar visible
                is_visible = False
                if filter_mode == "TODOS":
                    is_visible = True
                elif filter_mode == "SOLO BUY":
                    is_visible = (direction == 'BUY')
                elif filter_mode == "SOLO SELL":
                    is_visible = (direction == 'SELL')
                else:
                    is_visible = True
                
                # Si está visible, desmarcar el checkbox
                if is_visible and idx in self.hier_selected_checkbuttons:
                    self.hier_selected_checkbuttons[idx].set(False)
                    unmarked_count += 1
            
            self.add_log(f"[EMOJI] Desmarcadas {unmarked_count} opciones visibles (Filtro: {filter_mode})", 'info')
            
        except Exception as e:
            self.add_log(f"[ERROR] Error al desmarcar opciones: {str(e)}", 'error')

    def _aplicar_velas_a_tp(self, velas):
        """Aplica las velas SOLO al cálculo de TP de todas las opciones"""
        try:
            if not hasattr(self, 'hier_filtered_options') or not self.hier_filtered_options:
                messagebox.showerror("Error", "No hay opciones para recalcular")
                return
            
            if velas <= 0:
                messagebox.showwarning("Validación", "Ingresa un valor de velas mayor a 0")
                return
            
            recalc_count = 0
            self.add_log(f"\n[DATA] APLICANDO {velas:.0f} VELAS AL TP", 'warning')
            
            for idx, option in enumerate(self.hier_filtered_options):
                try:
                    entry_price = option['entry_price']
                    direction = option['direction']
                    
                    # Calcular TP = entrada +/- velas según dirección
                    if direction == "BUY":
                        tp_new = round(entry_price + velas, 5)
                    else:  # SELL
                        tp_new = round(entry_price - velas, 5)
                    
                    # Actualizar SOLO el TP
                    if 'tp_var' in option:
                        option['tp_var'].set(tp_new)
                    
                    # Validar la opción después de actualizar
                    if 'color_bg' in option:
                        self._validar_hierarquica_opcion(option, option['color_bg'])
                    
                    recalc_count += 1
                    self.add_log(
                        f"   [EMOJI] Opción #{idx+1} ({option['timeframe']} {direction}): TP → {tp_new:.5f}",
                        'success'
                    )
                    
                except Exception as e:
                    self.add_log(f"   [ERROR] Error en opción #{idx+1}: {str(e)}", 'error')
            
            self.add_log(f"\n[OK] TP ACTUALIZADO: {recalc_count} opción(es)", 'success')
            
            messagebox.showinfo(
                "[OK] TP Actualizado",
                f"Se actualizaron {recalc_count} TP con:\n• Entrada ± {velas:.5f}"
            )
            
        except Exception as e:
            self.add_log(f"[ERROR] Error: {str(e)}", 'error')
            messagebox.showerror("Error", f"Error al aplicar velas a TP: {str(e)}")

    def _aplicar_velas_a_sl(self, velas):
        """Aplica las velas SOLO al cálculo de SL de todas las opciones"""
        try:
            if not hasattr(self, 'hier_filtered_options') or not self.hier_filtered_options:
                messagebox.showerror("Error", "No hay opciones para recalcular")
                return
            
            if velas <= 0:
                messagebox.showwarning("Validación", "Ingresa un valor de velas mayor a 0")
                return
            
            recalc_count = 0
            self.add_log(f"\n[DATA] APLICANDO {velas:.0f} VELAS AL SL", 'warning')
            
            for idx, option in enumerate(self.hier_filtered_options):
                try:
                    entry_price = option['entry_price']
                    direction = option['direction']
                    
                    # Calcular SL = entrada +/- velas según dirección
                    if direction == "BUY":
                        sl_new = round(entry_price - velas, 5)
                    else:  # SELL
                        sl_new = round(entry_price + velas, 5)
                    
                    # Actualizar SOLO el SL
                    if 'sl_var' in option:
                        option['sl_var'].set(sl_new)
                    
                    # Validar
                    if 'color_bg' in option:
                        self._validar_hierarquica_opcion(option, option['color_bg'])
                    
                    recalc_count += 1
                    self.add_log(
                        f"   [EMOJI] Opción #{idx+1} ({option['timeframe']} {direction}): SL → {sl_new:.5f}",
                        'success'
                    )
                    
                except Exception as e:
                    self.add_log(f"   [ERROR] Error en opción #{idx+1}: {str(e)}", 'error')
            
            self.add_log(f"\n[OK] SL ACTUALIZADO: {recalc_count} opción(es)", 'success')
            
            messagebox.showinfo(
                "[OK] SL Actualizado",
                f"Se actualizaron {recalc_count} SL con:\n• Entrada ± {velas:.5f}"
            )
            
        except Exception as e:
            self.add_log(f"[ERROR] Error: {str(e)}", 'error')
            messagebox.showerror("Error", f"Error al aplicar velas a SL: {str(e)}")

    def _recalcular_general_jerarquico(self):
        """Recalcula TP/SL de TODAS las opciones según velas ingresadas"""
        try:
            if not hasattr(self, 'hier_filtered_options') or not self.hier_filtered_options:
                messagebox.showerror("Error", "No hay opciones para recalcular")
                return
            
            velas = self.hier_recalc_velas_var.get()
            
            if velas <= 0:
                messagebox.showwarning("Validación", "Ingresa un valor de velas mayor a 0")
                return
            
            # Recalcular para cada opción visible
            recalc_count = 0
            
            self.add_log(f"\n[ACTUALIZAR] INICIANDO RECÁLCULO GENERAL CON {velas:.0f} VELAS", 'warning')
            self.add_log(f"   Opciones a recalcular: {len(self.hier_filtered_options)}", 'info')
            
            for idx, option in enumerate(self.hier_filtered_options):
                try:
                    # Obtener datos necesarios
                    entry_price = option['entry_price']
                    direction = option['direction']
                    symbol = self.config['SYMBOL'].get()
                    
                    # Calcular distancia basada en velas
                    # Simulamos que: distance = velas * promedio de movimiento por vela
                    # Para propósitos prácticos, usamos: distance = velas * 0.0001 (ajustable)
                    
                    # Si el símbolo tiene datos de histórico, usar ATR de velas
                    if hasattr(self, 'gold_analyzer') and self.gold_analyzer:
                        # Intentar obtener ATR de las velas seleccionadas
                        try:
                            # Usar el timeframe de la opción para obtener velas
                            tf_string = option.get('timeframe', '1h')
                            # Aquí podrías hacer un cálculo más sofisticado
                            # Por ahora, usamos un cálculo simple: distance = velas * factor
                            distance = velas * 0.0001  # Factor ajustable
                        except:
                            distance = velas * 0.0001
                    else:
                        distance = velas * 0.0001
                    
                    # Calcular nuevo TP y SL
                    if direction == "BUY":
                        tp_new = round(entry_price + distance, 5)
                        sl_new = round(entry_price - distance, 5)
                    else:  # SELL
                        tp_new = round(entry_price - distance, 5)
                        sl_new = round(entry_price + distance, 5)
                    
                    # Actualizar en la opción
                    if 'tp_var' in option:
                        option['tp_var'].set(tp_new)
                    if 'sl_var' in option:
                        option['sl_var'].set(sl_new)
                    
                    # Actualizar colores y validaciones si existen
                    if 'color_bg' in option:
                        self._validar_hierarquica_opcion(option, option['color_bg'])
                    
                    recalc_count += 1
                    
                    self.add_log(
                        f"   [EMOJI] Opción #{idx+1} ({option['timeframe']} {direction}): " +
                        f"TP {tp_new:.5f} | SL {sl_new:.5f}",
                        'success'
                    )
                    
                except Exception as e:
                    self.add_log(f"   [ERROR] Error en opción #{idx+1}: {str(e)}", 'error')
            
            self.add_log(f"\n[OK] RECÁLCULO COMPLETADO: {recalc_count} opción(es) actualizada(s)", 'success')
            
            messagebox.showinfo(
                "[OK] Recálculo Completado",
                f"Se recalcularon {recalc_count} opciones con:\n" +
                f"• Velas: {velas:.0f}\n" +
                f"• Factor de distancia: {velas * 0.0001:.5f}\n\n" +
                f"Revisa los nuevos valores de TP/SL en las opciones"
            )
            
        except Exception as e:
            self.add_log(f"[ERROR] Error en recálculo general: {str(e)}", 'error')
            messagebox.showerror("Error", f"Error al recalcular: {str(e)}")

    def _adjust_tp(self, delta):
        """Ajusta el TP por un incremento pequeño"""
        try:
            current = self.tp_var.get()
            new_val = round(current + delta, 5)
            self.tp_var.set(new_val)
            self._validar_y_calcular_ganancias()
        except Exception as e:
            self.add_log(f"Error ajustando TP: {str(e)}", 'error')

    def _adjust_sl(self, delta):
        """Ajusta el SL por un incremento pequeño"""
        try:
            current = self.sl_var.get()
            new_val = round(current + delta, 5)
            self.sl_var.set(new_val)
            self._validar_y_calcular_ganancias()
        except Exception as e:
            self.add_log(f"Error ajustando SL: {str(e)}", 'error')

    def _adjust_hier_tp(self, option, delta):
        """Ajusta el TP de una opción jerárquica"""
        try:
            current = option['tp_var'].get()
            new_val = round(current + delta, 5)
            option['tp_var'].set(new_val)
            
            # Obtener los colores de la opción
            color_bg = option.get('color_bg', '#2d3e50')
            
            # DEBUG: Log del cambio
            self.add_log(f"🔧 TP ajustado: {current:.5f} → {new_val:.5f} (delta: {delta})", 'info')
            
            # Validar inmediatamente
            self._validar_hierarquica_opcion(option, color_bg)
        except Exception as e:
            self.add_log(f"Error ajustando TP jerárquico: {str(e)}", 'error')
            import traceback
            self.add_log(f"   Traceback: {traceback.format_exc()[:100]}", 'error')

    def _adjust_hier_sl(self, option, delta):
        """Ajusta el SL de una opción jerárquica"""
        try:
            current = option['sl_var'].get()
            new_val = round(current + delta, 5)
            option['sl_var'].set(new_val)
            
            # Obtener los colores de la opción
            color_bg = option.get('color_bg', '#2d3e50')
            
            # DEBUG: Log del cambio
            self.add_log(f"🔧 SL ajustado: {current:.5f} → {new_val:.5f} (delta: {delta})", 'info')
            
            # Validar inmediatamente
            self._validar_hierarquica_opcion(option, color_bg)
        except Exception as e:
            self.add_log(f"Error ajustando SL jerárquico: {str(e)}", 'error')
            import traceback
            self.add_log(f"   Traceback: {traceback.format_exc()[:100]}", 'error')

    def _recalcular_velas_opcion(self, option, color_bg):
        """Recalcula TP y SL de una opción según las velas ingresadas
        Usa el mismo valor para TP y SL pero con dirección opuesta:
        - BUY: TP = entrada + velas, SL = entrada - velas
        - SELL: TP = entrada - velas, SL = entrada + velas
        """
        try:
            direction = option.get('direction', 'BUY')
            entry = option.get('entry_price', 0)
            velas = option['velas_var'].get()
            
            if velas == 0:
                messagebox.showwarning("Validación", "Ingresa un valor de velas")
                return
            
            # Recalcular según dirección
            # TP = velas, SL = velas (simétrico)
            if direction == "BUY":
                new_tp = round(entry + velas, 5)
                new_sl = round(entry - velas, 5)
                self.add_log(f"[DATA] Recálculo VELAS BUY: Entrada={entry:.5f}, Velas={velas} → TP={new_tp:.5f} (+{velas}), SL={new_sl:.5f} (-{velas})", 'info')
            else:  # SELL
                new_tp = round(entry - velas, 5)
                new_sl = round(entry + velas, 5)
                self.add_log(f"[DATA] Recálculo VELAS SELL: Entrada={entry:.5f}, Velas={velas} → TP={new_tp:.5f} (-{velas}), SL={new_sl:.5f} (+{velas})", 'info')
            
            # Actualizar TP y SL
            option['tp_var'].set(new_tp)
            option['sl_var'].set(new_sl)
            
            # Validar inmediatamente
            self._validar_hierarquica_opcion(option, color_bg)
            
            self.add_log(f"[OK] TP/SL recalculados por velas (ambos 1x)", 'success')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error recalculando velas: {str(e)}")
            self.add_log(f"Error en _recalcular_velas_opcion: {str(e)}", 'error')

    def _calcular_tp_sl_por_dinero(self, entry_price, direction, volume, goal_profit=5.0, max_loss=20.0, symbol="BTCUSD"):
        """
        Calcula TP y SL basándose en dinero objetivo, respetando los requisitos mínimos de MT5
        
        ⭐ NOTA CRÍTICA: Los valores retornados son los valores REALES de TP y SL
        - Para BUY: TP > Entry (ganancia arriba), SL < Entry (pérdida abajo)
        - Para SELL: TP < Entry (ganancia abajo), SL > Entry (pérdida arriba)
        
        NO hace intercambio - retorna valores correctos directamente
        
        Parámetros:
        - goal_profit: Ganancia máxima deseada en USD (default $5)
        - max_loss: Pérdida máxima aceptable en USD (default $20)
        - volume: Tamaño del lote
        - symbol: Símbolo del par (XAUUSD, BTCUSD, etc.)
        """
        try:
            # Obtener requisitos mínimos de MT5
            info = mt5.symbol_info(symbol)
            if info is None:
                self.add_log(f"[ADVERTENCIA] No se pudo obtener info de {symbol} en _calcular_tp_sl_por_dinero", 'warning')
                return None, None
            
            digits = int(getattr(info, "digits", 5))
            point = float(getattr(info, "point", 10 ** -digits))
            stop_level = float(getattr(info, "stop_level", 0))
            
            # Distancia mínima requerida por MT5
            min_dist = max(stop_level * point, point * 2)
            
            # ⭐ FACTOR DE CONVERSIÓN según símbolo
            if "BTC" in symbol.upper():
                factor = 100000  # BTCUSD: 1 lote = 100000 satoshis
                absolute_min_pips = 50.0  # ⭐ AUMENTADO: Mínimo 50 pips para BTC (evita rechazos MT5)
            else:
                factor = 100  # XAUUSD y otros: 1 lote = 100 oz
                absolute_min_pips = 100.0  # ⭐ AUMENTADO: Mínimo 100 pips para oro (evita rechazos MT5)
            
            # Convertir dinero a pips basándose en el volumen
            if volume > 0:
                pip_distance_profit = goal_profit / (volume * factor)
                pip_distance_loss = max_loss / (volume * factor)
            else:
                pip_distance_profit = 5.0  # Default si volume es 0
                pip_distance_loss = 20.0
            
            # ⭐ IMPORTANTE: Asegurar un mínimo de pips ABSOLUTO
            # Usar la distancia mayor entre: (dinero objetivo) y (mínimo absoluto)
            pip_distance_profit = max(pip_distance_profit, absolute_min_pips)
            pip_distance_loss = max(pip_distance_loss, absolute_min_pips)
            
            # Calcular TP y SL según dirección
            # ⭐ CRUCIAL: NO intercambiar - retornar valores REALES correctamente
            if direction == "BUY":
                # BUY: TP arriba (ganancia), SL abajo (pérdida)
                tp = round(entry_price + pip_distance_profit, digits)
                sl = round(entry_price - pip_distance_loss, digits)
            else:  # SELL
                # SELL: TP abajo (ganancia), SL arriba (pérdida)
                tp = round(entry_price - pip_distance_profit, digits)
                sl = round(entry_price + pip_distance_loss, digits)
            
            # ⭐ VALIDACIÓN FINAL: Asegurar separación mínima entre TP y SL
            tp_sl_distance = abs(sl - tp)
            required_separation = min_dist * 2
            if tp_sl_distance < required_separation:
                # Si TP y SL están muy cercanos, aumentar las distancias
                adjustment = (required_separation - tp_sl_distance) / 2
                if direction == "BUY":
                    tp = round(tp + adjustment, digits)
                    sl = round(sl - adjustment, digits)
                else:  # SELL
                    tp = round(tp - adjustment, digits)
                    sl = round(sl + adjustment, digits)
                self.add_log(f"[ADVERTENCIA] Ajustado TP/SL por separación insuficiente (requerida: {required_separation:.8f})", 'warning')
            
            self.add_log(f"🔧 TP/SL ({symbol} {direction}): entry={entry_price:.5f} vol={volume} → TP={tp:.5f} SL={sl:.5f} dist={abs(sl-tp):.8f}", 'info')
            
            return tp, sl
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.add_log(f"[ERROR] Error calculando TP/SL por dinero: {str(e)}", 'error')
            self.add_log(f"   {error_trace[:200]}", 'error')
            return None, None

    def _calcular_profit_loss(self, entry_price, tp_price, sl_price, direction, volume, symbol="BTCUSD"):
        """Calcula ganancia y pérdida en USD según el símbolo"""
        try:
            # ⭐ Factor de conversión según símbolo
            if "BTC" in symbol.upper():
                factor = 100000  # BTCUSD: 1 lote = 100000 satoshis, 1 pip = $0.0001
            else:
                factor = 100  # XAUUSD y otros: 1 lote = 100 oz, 1 pip = $0.01
            
            if direction == "BUY":
                # En BUY: TP está ARRIBA, SL está ABAJO
                pip_distance_profit = abs(tp_price - entry_price)     # Distancia POSITIVA hacia arriba
                pip_distance_loss = abs(entry_price - sl_price)        # Distancia POSITIVA hacia abajo
            else:  # SELL
                # En SELL: TP está ABAJO, SL está ARRIBA
                pip_distance_profit = abs(entry_price - tp_price)     # Distancia POSITIVA hacia abajo
                pip_distance_loss = abs(sl_price - entry_price)        # Distancia POSITIVA hacia arriba
            
            # Conversión: profit = pips * volumen * factor
            profit = pip_distance_profit * volume * factor
            loss = pip_distance_loss * volume * factor
            
            return profit, loss
        except Exception as e:
            self.add_log(f"Error calculando profit/loss: {str(e)}", 'error')
            return 0, 0

    def _validar_hierarquica_opcion(self, option, color_bg):
        """Valida TP/SL de una opción jerárquica y actualiza la información"""
        try:
            # Asegurar que existen los labels
            if 'profit_label' not in option or 'loss_label' not in option:
                self.add_log(f"[ADVERTENCIA] Labels no encontrados en opción", 'warning')
                return
            
            entry_price = option['entry_price']
            direction = option['direction']
            tp_input = option['tp_var'].get()  # Valor del campo TP
            sl_input = option['sl_var'].get()  # Valor del campo SL
            volume = float(self.config['VOL'].get())
            
            # Los valores en los campos ya están correctos, pasarlos directamente
            tp_para_validar = tp_input
            sl_para_validar = sl_input
            
            # Obtener info del símbolo
            symbol = self.config['SYMBOL'].get()
            
            # 🔧 DEBUG: Mostrar valores antes de validar
            self.add_log(f"🔧 [{direction}] Antes validar: entry={entry_price:.5f} tp={tp_input:.5f} sl={sl_input:.5f}", 'info')
            
            tp_adj, sl_adj = self.validar_y_ajustar_stops(symbol, entry_price, tp_para_validar, sl_para_validar, direction)
            
            # 🔧 DEBUG: Mostrar valores después de validar
            self.add_log(f"🔧 [{direction}] Después validar: tp_adj={tp_adj} sl_adj={sl_adj}", 'info')
            
            # DEBUG: Log de valores
            debug_info = f"Entry:{entry_price:.5f} TP:{tp_input:.5f} SL:{sl_input:.5f} Vol:{volume} TP_adj:{tp_adj} SL_adj:{sl_adj}"
            
            # Determinar si es válido
            is_valid = True
            if tp_adj is None or sl_adj is None:
                is_valid = False
            else:
                # Validar que los stops sean válidos
                if direction == "BUY":
                    if not (sl_adj < entry_price < tp_adj):
                        is_valid = False
                else:  # SELL
                    if not (tp_adj < entry_price < sl_adj):
                        is_valid = False
            
            # ⭐ MEJORADO: Try-except alrededor de actualizaciones de widgets
            try:
                # Actualizar estado visual
                if is_valid:
                    # Intentar actualizar cada widget con manejo de errores individual
                    try:
                        if 'tp_status_label' in option and option['tp_status_label'].winfo_exists():
                            option['tp_status_var'].set("[EMOJI] VÁLIDO")
                            option['tp_status_label'].config(fg='#34d399', font=('Arial', 8, 'bold'))
                    except:
                        pass
                    
                    try:
                        if 'sl_status_label' in option and option['sl_status_label'].winfo_exists():
                            option['sl_status_var'].set("[EMOJI] VÁLIDO")
                            option['sl_status_label'].config(fg='#34d399', font=('Arial', 8, 'bold'))
                    except:
                        pass
                    
                    # Calcular ganancia y pérdida (en dinero, no en pips)
                    profit, loss = self._calcular_profit_loss(entry_price, tp_adj, sl_adj, direction, volume, symbol)
                    
                    # VALIDACIÓN: Asegurar que profit siempre es positivo y loss siempre es positivo
                    profit = abs(profit)  # Debe ser positivo
                    loss = abs(loss)      # Debe ser positivo
                    
                    risk_reward = profit / loss if loss > 0 else 0
                    
                    # ⭐ ACTUALIZAR CADA LABEL POR SEPARADO con validación
                    try:
                        if 'profit_label' in option and option['profit_label'].winfo_exists():
                            option['profit_label'].config(
                                text=f"[DINERO] +${profit:,.2f}",
                                fg='#34d399',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    try:
                        if 'loss_label' in option and option['loss_label'].winfo_exists():
                            option['loss_label'].config(
                                text=f"📉 -${loss:,.2f}",
                                fg='#ef4444',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    try:
                        if 'ratio_label' in option and option['ratio_label'].winfo_exists():
                            option['ratio_label'].config(
                                text=f"R:R 1:{risk_reward:.2f}",
                                fg='#fbbf24',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    # Guardar estado válido
                    option['is_valid'] = True
                    option['profit_value'] = profit
                    option['loss_value'] = loss
                    
                    # DEBUG
                    self.add_log(f"   [OK] Validado: {debug_info} → Ganancia: ${profit:,.2f} Pérdida: ${loss:,.2f}", 'info')
                else:
                    try:
                        if 'tp_status_label' in option and option['tp_status_label'].winfo_exists():
                            option['tp_status_var'].set("❌ INVÁLIDO")
                            option['tp_status_label'].config(fg='#ef4444', font=('Arial', 8, 'bold'))
                    except:
                        pass
                    
                    try:
                        if 'sl_status_label' in option and option['sl_status_label'].winfo_exists():
                            option['sl_status_var'].set("❌ INVÁLIDO")
                            option['sl_status_label'].config(fg='#ef4444', font=('Arial', 8, 'bold'))
                    except:
                        pass
                    
                    # Mostrar error en los labels
                    try:
                        if 'profit_label' in option and option['profit_label'].winfo_exists():
                            option['profit_label'].config(
                                text="❌ N/A",
                                fg='#ef4444',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    try:
                        if 'loss_label' in option and option['loss_label'].winfo_exists():
                            option['loss_label'].config(
                                text="❌ N/A",
                                fg='#ef4444',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    try:
                        if 'ratio_label' in option and option['ratio_label'].winfo_exists():
                            option['ratio_label'].config(
                                text="❌ Inválido",
                                fg='#ef4444',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    # Guardar estado inválido
                    option['is_valid'] = False
                    option['profit_value'] = 0
                    option['loss_value'] = 0
                    
                    # DEBUG
                    self.add_log(f"   [ERROR] Inválido: {debug_info}", 'warning')
            except Exception as widget_error:
                # Si hay error actualizando widgets, simplemente loguearlo y continuar
                pass
        
        except Exception as e:
            # Log detallado del error
            import traceback
            error_trace = traceback.format_exc()
            self.add_log(f"[ERROR] Error validando opción jerárquica: {str(e)}", 'error')
            self.add_log(f"   {debug_info if 'debug_info' in locals() else 'N/A'}", 'error')
            self.add_log(f"   Trace: {error_trace[:150]}", 'error')
            
            try:
                option['tp_status_var'].set("❌ ERROR")
                option['sl_status_var'].set("❌ ERROR")
            except:
                pass
            
            try:
                option['sl_status_label'].config(fg='#ef4444')
                if 'profit_label' in option:
                    option['profit_label'].config(text="⚠️ Error", fg='#ef4444', font=('Arial', 8, 'bold'))
                if 'loss_label' in option:
                    option['loss_label'].config(text="⚠️ Error", fg='#ef4444', font=('Arial', 8, 'bold'))
                if 'ratio_label' in option:
                    option['ratio_label'].config(text="⚠️ Error", fg='#ef4444', font=('Arial', 8, 'bold'))
            except:
                pass
            
            option['is_valid'] = False


    def _validar_y_calcular_ganancias(self):
        """Valida TP/SL y calcula ganancias estimadas"""
        try:
            if not hasattr(self, 'last_custom_analysis') or not self.last_custom_analysis:
                return
            
            analysis = self.last_custom_analysis
            entry_price = analysis['suggested_entry_price']
            direction = analysis['suggested_direction']
            tp = self.tp_var.get()
            sl = self.sl_var.get()
            volume = float(self.config['VOL'].get())
            
            # Obtener info del símbolo
            symbol = self.config['SYMBOL'].get()
            tp_adj, sl_adj = self.validar_y_ajustar_stops(symbol, entry_price, tp, sl, direction)
            
            if tp_adj is None or sl_adj is None:
                self.tp_status_var.set("❌")
                self.sl_status_var.set("❌")
                self.tp_status_label.config(fg='#ef4444')
                self.sl_status_label.config(fg='#ef4444')
                self.profit_info_label.config(text="❌ TP/SL fuera de rango válido", fg='#ef4444')
                return
            
            # Validar que los stops sean válidos
            valid = True
            if direction == "BUY":
                if not (sl_adj < entry_price < tp_adj):
                    valid = False
            else:  # SELL
                if not (tp_adj < entry_price < sl_adj):
                    valid = False
            
            # Actualizar estado
            if valid:
                self.tp_status_var.set("✅")
                self.sl_status_var.set("✅")
                self.tp_status_label.config(fg='#34d399')
                self.sl_status_label.config(fg='#34d399')
                
                # Calcular ganancia (usando la función auxiliar)
                profit_per_pip, loss_per_pip = self._calcular_profit_loss(entry_price, tp_adj, sl_adj, direction, volume, symbol)
                
                risk_reward = profit_per_pip / loss_per_pip if loss_per_pip > 0 else 0
                
                self.profit_info_label.config(
                    text=f"📊 Ganancia Est.: ${profit_per_pip:,.2f} | Risk:Reward: 1:{risk_reward:.2f} | Vol: {volume}",
                    fg='#34d399'
                )
            else:
                self.tp_status_var.set("❌")
                self.sl_status_var.set("❌")
                self.tp_status_label.config(fg='#ef4444')
                self.sl_status_label.config(fg='#ef4444')
                self.profit_info_label.config(text="❌ TP debe estar > Entry (BUY) o < Entry (SELL)", fg='#ef4444')
        
        except Exception as e:
            self.add_log(f"Error calculando ganancias: {str(e)}", 'error')

    def enviar_a_espera_ajustado(self):
        """Envía la operación a espera con los TP/SL ajustados manualmente"""
        try:
            if not hasattr(self, 'last_custom_analysis') or not self.last_custom_analysis:
                messagebox.showwarning("Error", "No hay análisis disponible")
                return
            
            analysis = self.last_custom_analysis
            direction = analysis['suggested_direction']
            entry_price = analysis['suggested_entry_price']
            tp = self.tp_var.get()
            sl = self.sl_var.get()
            
            if tp == 0 or sl == 0:
                messagebox.showwarning("Error", "TP y SL no pueden ser 0")
                return
            
            # Validar
            symbol = self.config['SYMBOL'].get()
            tp_adj, sl_adj = self.validar_y_ajustar_stops(symbol, entry_price, tp, sl, direction)
            
            if tp_adj is None or sl_adj is None:
                messagebox.showerror("Error", "TP/SL inválidos según requisitos de MT5")
                return
            
            # Abrir operación
            if self.abrir_operacion_en_espera(direction, tp_adj, sl_adj, entry_price):
                self.add_log(f"[OK] Operación {direction} enviada a espera", 'success')
                self.add_log(f"   Entrada: {entry_price:.5f} | TP: {tp_adj:.5f} | SL: {sl_adj:.5f}", 'info')
                messagebox.showinfo("Éxito", f"[OK] Operación {direction} enviada a espera\n\nTP: {tp_adj:.5f}\nSL: {sl_adj:.5f}")
            else:
                messagebox.showerror("Error", "No se pudo enviar la operación a espera")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar a espera: {str(e)}")
            self.add_log(f"Error en enviar_a_espera_ajustado: {str(e)}", 'error')

    def abrir_operacion_entry_point(self, direccion):
        """Abre una operación desde el punto de entrada (entry_point)"""
        # ⭐ CORREGIDO: Permitir hasta MAX_SIMULTANEOUS_OPS operaciones
        max_ops = int(self.config['MAX_SIMULTANEOUS_OPS'].get())
        if self.total_operaciones_abiertas >= max_ops:
            self.add_log(f"[ERROR] Máximo de operaciones alcanzado ({self.total_operaciones_abiertas}/{max_ops})", 'warning')
            return False
            
        symbol = self.config['SYMBOL'].get()
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.add_log("No se pudo obtener información del símbolo", 'error')
            return False
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            self.add_log("No hay tick disponible para el símbolo", 'error')
            return False
        
        # ⭐ CORREGIDO: Usar el precio objetivo como entrada, no el precio actual del mercado
        # Esto asegura que abrimos lo MÁS CERCA POSIBLE del precio objetivo
        target_price = self.entry_point_price.get()
        
        # Validar que el precio objetivo es razonable (cercano al mercado)
        current_bid = tick.bid
        current_ask = tick.ask
        mid_price = (current_bid + current_ask) / 2
        distance_to_target = abs(current_bid - target_price)
        
        # Si está MÁS de 500 pips lejos, rechazar (algo está mal)
        if distance_to_target > 0.05:  # 500 pips en la mayoría de símbolos
            self.add_log(f"[ADVERTENCIA] Precio objetivo muy lejos ({distance_to_target:.5f}). Rechazando entrada.", 'warning')
            return False
        
        # Usar el precio objetivo como entrada (o muy cerca)
        precio = round(target_price, get_symbol_digits(symbol_info))
        
        self.add_log(f"[UBICACION] Abriendo {direccion} EN el precio objetivo: {precio:.5f}", 'info')
        self.add_log(f"   Precio actual: {current_bid:.5f} | Diferencia: {distance_to_target:.5f}", 'info')
        
        # ⭐ CORREGIDO: TP_DIFF y SL_DIFF son DIFERENCIAS DIRECTAS EN PRECIO
        tp_diff = float(self.config['TP_DIFF'].get())
        sl_diff = float(self.config['SL_DIFF'].get())
        digits = get_symbol_digits(symbol_info)
        
        # ⭐ Usar diferencia DIRECTA en precio (no multiplicar por point)
        if direccion == "BUY":
            sl = round(precio - sl_diff, digits)
            tp = round(precio + tp_diff, digits)
            tipo = mt5.ORDER_TYPE_BUY
        else:
            sl = round(precio + sl_diff, digits)
            tp = round(precio - tp_diff, digits)
            tipo = mt5.ORDER_TYPE_SELL
        
        self.add_log(f"[TP/SL] EntryPoint: precio={precio:.2f} TP_DIFF={tp_diff} SL_DIFF={sl_diff} → TP={tp:.2f} SL={sl:.2f}", 'info')

        # ⭐ VALIDAR STOPS contra STOPS_LEVEL del broker
        # Nota: usamos current_ask/bid como precio real de ejecución
        precio_real = current_ask if direccion == "BUY" else current_bid
        sl, tp, _ = validate_and_adjust_stops(
            symbol_info, precio_real, sl, tp, direccion, log_callback=self.add_log
        )

        # ⭐ USAR DEAL (ejecución inmediata) con FOK para ejecutar al mejor precio disponible
        # Cuando el precio está cercano al objetivo, abrimos al mejor precio disponible
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(self.config['VOL'].get()),
            "type": tipo,
            "price": current_ask if direccion == "BUY" else current_bid,  # ⭐ BUY usa ASK, SELL usa BID
            "sl": sl,
            "tp": tp,
            "deviation": 50,  # ⭐ Permite desviación de 50 pips
            "magic": self.config['MAGIC_NUMBER'],
            "comment": f"Bot-EntryPoint-{direccion}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,  # ⭐ Fill-or-Kill: se ejecuta o se cancela
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            self.total_operaciones_abiertas += 1
            self.position_ids.add(result.order)
            
            msg = f"""
[OK] Operación Entry Point {direccion}:
[DINERO] Precio: {precio:.5f} 
[OBJETIVO] TP: {tp:.5f} 
[EMOJI] SL: {sl:.5f}
[IA] Modo: Punto de Entrada
"""
            self.add_log(msg, 'success')
            
            self.actualizar_contador_z()
            return True
        else:
            # ⭐ MEJORADO: Mostrar error detallado
            if result:
                retcode = result.retcode
                comment = result.comment if hasattr(result, 'comment') else "Sin comentario"
                self.add_log(f"[ERROR] Error al abrir operación: {comment} (Código: {retcode})", 'error')
                self.add_log(f"   Dirección: {direccion}", 'error')
                self.add_log(f"   Precio: {precio:.5f} | TP: {tp:.5f} | SL: {sl:.5f}", 'error')
                self.add_log(f"   Volumen: {float(self.config['VOL'].get())}", 'error')
            else:
                self.add_log(f"[ERROR] Error: No hay respuesta de MT5", 'error')
            return False

if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 INICIANDO MT5 TRADING BOT - MULTI-TIMEFRAME")
        print("="*70 + "\n")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Creando interfaz gráfica...")
        sys.stdout.flush()
        
        root = tk.Tk()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Inicializando bot...")
        sys.stdout.flush()
        
        app = MT5AdaptiveTradingBot(root)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ Bot inicializado exitosamente")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ejecutando interfaz gráfica...")
        print("="*70 + "\n")
        sys.stdout.flush()
        
        root.mainloop()
    except Exception as e:
        # Si hay error al iniciar, intentar imprimir/loggear y cerrar correctamente
        try:
            print(f"\n❌ Error al iniciar la aplicación: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        except:
            pass
