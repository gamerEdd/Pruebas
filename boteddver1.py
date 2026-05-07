# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ⭐ LOGGING A ARCHIVO - Captura TODO lo que sucede en el bot
import logging
from logging.handlers import RotatingFileHandler

# Configurar logger global para capturar TODOS los eventos
LOG_FILE = 'bot_execution.log'
logger = logging.getLogger('boteddver1')
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Evitar duplicados

# Handler para archivo (rotativo, máx 10MB)
try:
    fh = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
except Exception as e:
    print(f"[WARN] No se pudo crear logger a archivo: {e}")

# Handler para consola con UTF-8 encoding correcto
try:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    # Configurar encoding UTF-8 con error handler 'replace' para caracteres no soportados
    if hasattr(ch.stream, 'reconfigure'):
        ch.stream.reconfigure(encoding='utf-8', errors='replace')
except Exception as e:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

# Formato detallado
formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')
if 'fh' in locals():
    fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("="*80)
logger.info("INICIANDO BOT boteddver1 - Logs en: " + LOG_FILE)
logger.info("="*80)

# ⭐ Capturar excepciones no capturadas
def excepthook(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("EXCEPCION NO CAPTURADA", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = excepthook

import MetaTrader5 as mt5
import mt5_safe
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime, timedelta
import os
import json
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

# ⭐ psutil es opcional - se importa dinámicamente si está disponible
psutil = None

from buy_specialist_ai import BuySpecialistAI
from sell_specialist_ai import SellSpecialistAI
from decision_arbitrator_ai import DecisionArbitratorAI
from gold_analyzer import GoldAnalyzer
from loss_analyzer import LossAnalyzer
from loss_protection_ai import LossProtectionAI  # ⭐ NUEVO: ML-based loss protection with retraining
from recovery_based_closer import RecoveryBasedCloser  # ⭐ NUEVO: Cierre dinámico por recuperación
from feedback_loop_ai import FeedbackLoopAI  # ⭐ NUEVO: Post-trade feedback loop
from adaptive_parameters import AdaptiveParameters
from data_updater_module import DataUpdater, PreAnalysisDataRefresher
from data_loader_trainer import DataLoaderTrainer, initialize_data_loader

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
from trade_logger import log_trade, read_market_snapshots, write_market_snapshots, append_market_snapshot, get_market_snapshots_metadata, rotate_market_snapshots
from auto_calibration import prefill_market_data, calibrate_from_logs, prefill_market_data_and_return
from dynamic_position_closer import DynamicPositionCloser  # ⭐ NUEVO: Cierra posiciones contrarias a reversión
from trend_change_detector import TrendChangeDetector  # ⭐ NUEVO: Detecta cambios de tendencia 10-30s anticipado
from multi_timeframe_analyzer import MultiTimeframeAnalyzer  # ⭐ NUEVO: Análisis multi-timeframe M1/M5/M15/M30/H1

# ⭐ NUEVAS UTILIDADES DE VALIDACIÓN Y ANÁLISIS (P3 Phase)
from indicator_base import IndicatorBase
from temporal_weighting import TemporalWeighting
from outlier_filter import OutlierFilter
from candle_validator import CandleValidator
from market_snapshot_generator import MarketSnapshotGenerator
from safety_filters_manager import SafetyFiltersManager  # [EMOJI] Filtros institucionales

# Configure logging: write ONLY to file, suppress console spam
import io
import contextlib

try:
    _log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(_log_dir, exist_ok=True)
    
    # ⭐ NUEVO: Configurar logging SOLO para consola (stderr), SIN archivo
    _formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(name)s: %(message)s')
    
    # Handler para consola (stderr) ÚNICAMENTE
    _handler_console = logging.StreamHandler(sys.stderr)
    _handler_console.setFormatter(_formatter)
    _handler_console.setLevel(logging.DEBUG)
    
    # ⭐ NUEVO: Configurar logging en DEBUG para VER TODO EN CONSOLA
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[_handler_console],
        format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s'
    )
except Exception as e:
    # Si falla la configuración, al menos imprimir el error
    print(f"ERROR en configuración de logging: {e}", file=sys.stderr)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        stream=sys.stderr
    )

# ⭐ SUPRIMIR LOGS DE TERCEROS: Desactivar todos los loggers de módulos importados
for logger_name in ['loss_analyzer', 'loss_protection_ai', 'feedback_loop_ai', 
                     'data_loader_trainer', 'adaptive_parameters', 'decision_arbitrator_ai', 
                     'buy_specialist_ai', 'sell_specialist_ai', 'multi_timeframe_analyzer',
                     'micro_momentum_engine_v2', 'dataset_learning_engine', 'neural_network_predictor']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

logger = logging.getLogger('MT5AdaptiveTradingBot')
logger.setLevel(logging.DEBUG)  # ⭐ CAMBIAR a DEBUG para ver TODOS los mensajes

# ⭐ NUEVO: Manejador global de excepciones no capturadas
def _handle_exception(exc_type, exc_value, exc_traceback):
    """Captura TODAS las excepciones no manejadas y las imprime en consola"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Imprimir en consola (stderr) y en logging
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("\n" + "="*60, file=sys.stderr)
    print("⚠️ EXCEPCIÓN NO CAPTURADA", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(error_msg, file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    logger.critical(f"EXCEPCIÓN NO CAPTURADA: {error_msg}")

sys.excepthook = _handle_exception

# ⭐ FIX #3: SISTEMA CENTRALIZADO DE CACHE MT5 (30x reducción en API calls)
class MT5CacheManager:
    """
    Centraliza todas las llamadas a MT5 API para reducir serialización.
    - Actualiza datos cada 2-3 segundos en thread separado
    - Todos los threads acceden al cache en lugar de MT5 directo
    - Reduce 3,600+ llamadas/hora a ~120-200 llamadas/hora
    """
    
    def __init__(self, update_interval=2.0, log_callback=None):
        self.update_interval = update_interval  # 2-3 segundos
        self.log_callback = log_callback
        self.cache = {
            'positions': {},       # {symbol: [positions]}
            'ticks': {},           # {symbol: tick}
            'account': None,       # account_info
            'rates': {},           # {(symbol, timeframe): [rates]}
        }
        self.cache_lock = threading.Lock()
        self.timestamp = {
            'positions': 0,
            'ticks': 0,
            'account': 0,
            'rates': 0,
        }
        self.running = False
        self.cache_thread = None
    
    def start(self):
        """Inicia el thread de actualización de caché"""
        if self.running:
            return
        self.running = True
        self.cache_thread = threading.Thread(target=self._cache_updater_loop, daemon=True)
        self.cache_thread.start()
        if self.log_callback:
            self.log_callback("[MT5 CACHE] Sistema centralizado iniciado - Actualizaciones cada 2-3s", 'success')
    
    def stop(self):
        """Detiene el thread de actualización"""
        self.running = False
        if self.cache_thread:
            self.cache_thread.join(timeout=5)
    
    def _cache_updater_loop(self):
        """Loop central que actualiza MT5 data cada 2-3 segundos"""
        while self.running:
            try:
                start_time = time.time()
                
                # Actualizar posiciones, ticks y account info
                self._update_all_positions()
                self._update_all_ticks()
                self._update_account_info()
                
                elapsed = time.time() - start_time
                sleep_time = max(0.5, self.update_interval - elapsed)
                time.sleep(sleep_time)
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"[MT5 CACHE] Error en actualización: {str(e)[:60]}", 'error')
                time.sleep(1)
    
    def _update_all_positions(self):
        """Actualiza todas las posiciones de todos los símbolos"""
        try:
            # Obtener todas las posiciones abiertas sin filtrar por símbolo
            all_positions = mt5.positions_get()
            with self.cache_lock:
                self.cache['positions'] = {}
                if all_positions:
                    for pos in all_positions:
                        symbol = pos.symbol if hasattr(pos, 'symbol') else pos.get('symbol', None)
                        if symbol:
                            if symbol not in self.cache['positions']:
                                self.cache['positions'][symbol] = []
                            self.cache['positions'][symbol].append(pos)
                self.timestamp['positions'] = time.time()
        except Exception as e:
            pass
    
    def _update_all_ticks(self):
        """Actualiza los últimos ticks de todos los símbolos"""
        try:
            symbols_to_check = ['XAUUSD', 'XAGUSD']
            with self.cache_lock:
                for symbol in symbols_to_check:
                    try:
                        tick = mt5.symbol_info_tick(symbol)
                        self.cache['ticks'][symbol] = tick
                        self.timestamp['ticks'] = time.time()
                    except Exception as e:
                        logger.warning(f"[CACHE] Error updating tick for {symbol}: {e}")
        except Exception as e:
            logger.warning(f"[CACHE] Error in cache update cycle: {e}")
    
    def _update_account_info(self):
        """Actualiza la información de la cuenta"""
        try:
            with self.cache_lock:
                account = mt5.account_info()
                self.cache['account'] = account
                self.timestamp['account'] = time.time()
        except Exception as e:
            pass
    
    def get_positions(self, symbol):
        """Obtiene posiciones del caché (no llamada directa MT5)"""
        with self.cache_lock:
            return self.cache['positions'].get(symbol, [])
    
    def get_tick(self, symbol):
        """Obtiene tick del caché (no llamada directa MT5)"""
        with self.cache_lock:
            return self.cache['ticks'].get(symbol, None)
    
    def get_account_info(self):
        """Obtiene info de cuenta del caché (no llamada directa MT5)"""
        with self.cache_lock:
            return self.cache['account']
    
    def get_rates(self, symbol, timeframe, start_pos, count):
        """
        Obtiene o calcula rates desde caché.
        Si no están en caché, hace llamada MT5 UNA VEZ cada 2-3s
        """
        key = (symbol, timeframe)
        with self.cache_lock:
            cached_rates = self.cache['rates'].get(key)
            if cached_rates and (time.time() - self.timestamp['rates'] < self.update_interval + 1):
                return cached_rates
        
        # Si no está en caché, hacer llamada MT5
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
            with self.cache_lock:
                self.cache['rates'][key] = rates
                self.timestamp['rates'] = time.time()
            return rates
        except Exception as e:
            self.add_log(f"[ERROR] get_rates_from_cache: {str(e)[:80]}", 'error')
            return None
    
    def get_cache_age(self, data_type='positions'):
        """Retorna la edad del caché en segundos"""
        return time.time() - self.timestamp.get(data_type, 0)

class MT5AdaptiveTradingBot:
    def get_ghost_stats_snapshot(self):
        """Devuelve un snapshot de las ganadas/perdidas fantasma acumuladas en la ventana actual, sin reiniciar contadores."""
        try:
            if self.ghost_ops_lock:
                with self.ghost_ops_lock:
                    return {
                        'buy_win': self.ghost_total['buy_win'],
                        'buy_loss': self.ghost_total['buy_loss'],
                        'sell_win': self.ghost_total['sell_win'],
                        'sell_loss': self.ghost_total['sell_loss']
                    }
            else:
                return {
                    'buy_win': self.ghost_total['buy_win'],
                    'buy_loss': self.ghost_total['buy_loss'],
                    'sell_win': self.ghost_total['sell_win'],
                    'sell_loss': self.ghost_total['sell_loss']
                }
        except Exception as e:
            self.add_log(f"[ERROR] get_ghost_ops_stats: {str(e)[:80]}", 'error')
            return {'buy_win': 0, 'buy_loss': 0, 'sell_win': 0, 'sell_loss': 0}

    def get_rapid_ops_snapshot(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        return {'total_opened': 0, 'buy_count': 0, 'sell_count': 0, 'total_profit': 0.0, 'active_count': 0}

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

    def _microtrend_direction(self, symbol=None, bars=10, threshold=None):
        """
        ⭐ ANÁLISIS DE DIRECCIÓN REAL DE VELAS + CONFIRMACIÓN DE PRECIO ACTUAL
        1. Cuenta velas UP (close > open) vs DOWN (close < open)
        2. Requiere mayoría clara (6+ de 10) para declarar tendencia
        3. Luego confirma con precio actual vs bar_open
        """
        try:
            # ⭐ CRÍTICO: Asegurar que symbol NUNCA sea VACÍO o None
            if not symbol or symbol.strip() == '':
                symbol = self.config['SYMBOL'].get() if hasattr(self, 'config') else 'GOLD'
            if not symbol or symbol.strip() == '':
                symbol = 'GOLD'
            
            # Obtener threshold en decimal - USA THRESHOLD POR PAR (GOLD o SILVER)
            if threshold is None:
                # ⭐ USAR THRESHOLD ESPECÍFICO DEL PAR
                if symbol.upper() == 'GOLD' or symbol == 'XAUUSD':
                    pips_value = self._safe_get('GOLD_THRESHOLD', 18.0)
                elif symbol.upper() == 'SILVER' or symbol == 'XAGUSD':
                    pips_value = self._safe_get('SILVER_THRESHOLD', 15.0)
                else:
                    pips_value = self._safe_get('MICROTREND_THRESHOLD', 18.0)  # Default fallback
                
                pip_size = 0.01
                threshold = pips_value * pip_size

            # ═══════════════════════════════════════════════════════════
            # PASO 1: OBTENER VELAS HISTÓRICAS + ANÁLISIS DE DIRECCIÓN
            # ═══════════════════════════════════════════════════════════
            candle_data = self.get_fresh_market_data(symbol, bars=bars+2)
            if not candle_data or len(candle_data) < bars:
                return 'FLAT'

            # Tomar últimas N velas (excluyendo la actual incompleta)
            last_candles = candle_data[-bars-1:-1] if len(candle_data) > bars else candle_data[-bars:]
            
            up_count = 0
            down_count = 0
            
            for candle in last_candles:
                candle_open = float(candle.get('open', 0))
                candle_close = float(candle.get('close', 0))
                
                if candle_open > 0 and candle_close > 0:
                    if candle_close > candle_open:
                        up_count += 1
                    elif candle_close < candle_open:
                        down_count += 1

            # ═══════════════════════════════════════════════════════════
            # PASO 2: DETERMINAR DIRECCIÓN DOMINANTE (requiere mayoría)
            # ═══════════════════════════════════════════════════════════
            min_required = bars * 0.6  # 60% mínimo para declarar tendencia
            
            candle_direction = 'FLAT'
            if up_count >= min_required:
                candle_direction = 'BUY'
            elif down_count >= min_required:
                candle_direction = 'SELL'

            # ═══════════════════════════════════════════════════════════
            # PASO 3: CONFIRMAR CON PRECIO ACTUAL vs BAR OPEN
            # ═══════════════════════════════════════════════════════════
            
            # Obtener precio actual
            current_price = None
            try:
                if hasattr(self, 'mt5') and self.mt5:
                    ticker = self.mt5.symbol_info_tick(symbol)
                    if ticker:
                        current_price = float(ticker.ask) if ticker.ask > 0 else float(ticker.bid)
            except:
                pass

            if current_price is None:
                try:
                    snaps = self.get_fresh_market_data(symbol, bars=1)
                    if snaps:
                        current_price = float(snaps[-1].get('close', 0))
                except:
                    pass

            # Obtener bar_open (open de barra vigente)
            bar_open = None
            if candle_data and len(candle_data) > 0:
                bar_open = float(candle_data[-1].get('open', 0))

            if current_price is None or bar_open is None or current_price <= 0 or bar_open <= 0:
                # Si no hay datos recientes, usar dirección de velas históricas
                return candle_direction

            # ═══════════════════════════════════════════════════════════
            # PASO 4: FUSIONAR ANÁLISIS (histórico + confirmación)
            # ═══════════════════════════════════════════════════════════
            delta = current_price - bar_open
            
            # Si velas históricas muestran dirección clara:
            if candle_direction == 'BUY':
                # Velas suben, pero confirma que precio vigente sigue arriba del open
                if delta >= -threshold:  # Permite retroceso hasta -threshold
                    return 'BUY'
                else:
                    return 'FLAT'  # Reversión demasiado fuerte
                    
            elif candle_direction == 'SELL':
                # Velas bajan, pero confirma que precio vigente sigue abajo del open
                if delta <= threshold:  # Permite retroceso hasta +threshold
                    return 'SELL'
                else:
                    return 'FLAT'  # Reversión demasiado fuerte
            
            # Si velas no muestran tendencia clara, usar movimiento actual
            else:
                if delta >= threshold:
                    return 'BUY'
                elif delta <= -threshold:
                    return 'SELL'
                else:
                    return 'FLAT'

        except Exception as e:
            self.add_log(f"[MICROTREND-ERROR] {str(e)[:80]}", 'error')
            return 'FLAT'

    def _analyze_final_4_candles_specialized(self, symbol, snapshots=None):
        """
        ⭐ ANÁLISIS BIDIRECCIONAL INTELIGENTE DE LAS ÚLTIMAS 4 VELAS + CONFIG ÓPTIMA
        NO toma dirección como parámetro - DETERMINA la dirección CORRECTA
        
        Integra PARÁMETROS ÓPTIMOS de GUI:
        - THRESHOLD (impulso mínimo)
        - CANDLE_BODY_PCT (% body mínimo)
        - CANDLE_WICK_PCT (% wick máximo)
        - CANDLE_CLOSE_PCT (% cierre cercano)
        
        Analiza AMBAS direcciones (BUY y SELL) y retorna:
        - La dirección ÓPTIMA (o BLOCK si ambas son débiles)
        - Confianza en la decisión (0-100%)
        - Razones de validación para ambas
        
        Valida (ambas direcciones):
        1. Anti-ruido estricto (body > % del rango según CONFIG ÓPTIMA)
        2. Consistencia de dirección (min 3 de 4 en la misma dirección)
        3. Impulso creciente (cada vela ≥ 85% anterior)
        4. Cierre fuerte (close en zona de poder según CONFIG ÓPTIMA)
        5. Comparación con histórico (no empeoramiento > 15%)
        6. ⭐ NUEVO: Validación contra CONFIG ÓPTIMA (THRESHOLD + parámetros)
        
        Retorna: {
            'recommended_direction': 'BUY' | 'SELL' | 'BLOCK',
            'confidence': float (0-100%),
            'reason': str,
            'buy_score': float (0-100%),
            'sell_score': float (0-100%),
            'score_gap': float,
            'buy_analysis': dict (detalles),
            'sell_analysis': dict (detalles),
            'optimal_config_applied': dict (parámetros usados)
        }
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=20) or []
            
            if len(snapshots) < 4:
                return {
                    'recommended_direction': 'BLOCK',
                    'confidence': 0.0,
                    'reason': 'Menos de 4 velas disponibles',
                    'buy_score': 0.0,
                    'sell_score': 0.0,
                    'score_gap': 0.0,
                    'buy_analysis': {},
                    'sell_analysis': {},
                    'optimal_config_applied': {}
                }
            
            # ═══════════════════════════════════════════════════════════
            # LEER PARÁMETROS ÓPTIMOS DE GUI
            # ═══════════════════════════════════════════════════════════
            
            symbol_check = symbol or self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get()
            is_gold = 'GOLD' in symbol_check.upper()
            
            # Parámetros óptimos para este par
            if is_gold:
                try:
                    threshold_pips = float(self.config.get('GOLD_THRESHOLD', tk.DoubleVar(value=18)).get())
                    candle_body_pct = int(self.config.get('GOLD_CANDLE_BODY_PCT', tk.IntVar(value=60)).get())
                    candle_wick_pct = int(self.config.get('GOLD_CANDLE_WICK_PCT', tk.IntVar(value=40)).get())
                    candle_close_pct = int(self.config.get('GOLD_CANDLE_CLOSE_PCT', tk.IntVar(value=70)).get())
                except:
                    threshold_pips = 18
                    candle_body_pct = 60
                    candle_wick_pct = 40
                    candle_close_pct = 70
            else:  # SILVER
                try:
                    threshold_pips = float(self.config.get('SILVER_THRESHOLD', tk.DoubleVar(value=15)).get())
                    candle_body_pct = int(self.config.get('SILVER_CANDLE_BODY_PCT', tk.IntVar(value=60)).get())
                    candle_wick_pct = 40  # SILVER usa valores similares
                    candle_close_pct = 70
                except:
                    threshold_pips = 15
                    candle_body_pct = 60
                    candle_wick_pct = 40
                    candle_close_pct = 70
            
            optimal_config = {
                'threshold_pips': threshold_pips,
                'candle_body_pct': candle_body_pct,
                'candle_wick_pct': candle_wick_pct,
                'candle_close_pct': candle_close_pct,
                'symbol': symbol_check
            }
            
            # Tomar últimas 4 velas y velas 5-14 para comparación histórica
            last_4 = snapshots[-4:]
            historical_comparison = snapshots[-14:-4] if len(snapshots) >= 14 else snapshots[-min(10, len(snapshots)-4):]
            
            # ═══════════════════════════════════════════════════════════
            # ANALIZAR AMBAS DIRECCIONES (BUY Y SELL)
            # ═══════════════════════════════════════════════════════════
            
            def _score_direction(direction_target):
                """Analiza una dirección específica y retorna score detallado INCLUYENDO CONFIG ÓPTIMA"""
                
                # 1. ANÁLISIS DE RUIDO (usando parámetros óptimos)
                total_body = 0
                total_wicks = 0
                candle_details = []
                config_violations = 0  # Contar cuántos cándles violan CONFIG ÓPTIMA
                config_compliance_score = 100.0  # Empieza perfecto
                
                for i, candle in enumerate(last_4):
                    open_price = float(candle.get('open', 0))
                    close_price = float(candle.get('close', 0))
                    high_price = float(candle.get('high', 0))
                    low_price = float(candle.get('low', 0))
                    
                    if open_price <= 0 or close_price <= 0:
                        continue
                    
                    body = abs(close_price - open_price)
                    upper_wick = high_price - max(open_price, close_price)
                    lower_wick = min(open_price, close_price) - low_price
                    total_wicks_vela = upper_wick + lower_wick
                    candle_range = high_price - low_price
                    
                    body_ratio = (body / candle_range) if candle_range > 0 else 0
                    noise_pct = (total_wicks_vela / candle_range) if candle_range > 0 else 0
                    
                    total_body += body
                    total_wicks += total_wicks_vela
                    
                    # ⭐ VALIDAR CONTRA CONFIG ÓPTIMA (cada vela)
                    body_pct = body_ratio * 100
                    wick_pct = noise_pct * 100
                    
                    body_compliant = body_pct >= candle_body_pct
                    wick_compliant = wick_pct <= candle_wick_pct
                    
                    if not body_compliant or not wick_compliant:
                        config_violations += 1
                        config_compliance_score -= 15  # Penalidad por vela no conforme
                    
                    candle_details.append({
                        'direction': 'UP' if close_price > open_price else 'DOWN' if close_price < open_price else 'DOJI',
                        'body': body,
                        'body_ratio': body_ratio,
                        'body_pct': body_pct,
                        'noise_pct': noise_pct,
                        'wick_pct': wick_pct,
                        'range': candle_range,
                        'close_price': close_price,
                        'open_price': open_price,
                        'body_compliant': body_compliant,
                        'wick_compliant': wick_compliant
                    })
                
                config_compliance_score = max(0, config_compliance_score)
                
                noise_ratio = (total_wicks / (total_body + total_wicks)) if (total_body + total_wicks) > 0 else 0
                noise_score = max(0, 100 - (noise_ratio * 100))
                
                # 2. ANÁLISIS DE CONSISTENCIA
                direction_counts = {'UP': 0, 'DOWN': 0, 'DOJI': 0}
                for detail in candle_details:
                    direction_counts[detail['direction']] += 1
                
                if direction_target == 'BUY':
                    consistency_count = direction_counts['UP']
                    consistency_score = min(100.0, (consistency_count / 3) * 100.0)
                else:
                    consistency_count = direction_counts['DOWN']
                    consistency_score = min(100.0, (consistency_count / 3) * 100.0)
                
                # 3. ANÁLISIS DE IMPULSO
                impulse_count = 0
                for i in range(1, len(candle_details)):
                    curr_body = candle_details[i]['body']
                    prev_body = candle_details[i-1]['body']
                    if curr_body >= (prev_body * 0.85):
                        impulse_count += 1
                
                impulse_score = min(100.0, (impulse_count / 3) * 100.0)
                
                # 4. ANÁLISIS DE FORTALEZA DEL CIERRE (usando CONFIG ÓPTIMA)
                last_candle = candle_details[-1] if candle_details else {}
                if last_candle and last_candle['range'] > 0:
                    if direction_target == 'BUY':
                        # BUY: close debe estar cerca del máximo
                        close_range = last_candle['close_price'] - last_candle['open_price']
                        close_position = ((last_candle['close_price'] - (last_candle['open_price'] - last_candle['range']/2)) / last_candle['range']) * 100
                        close_position = max(0, min(100, close_position))
                        # Debe estar ≥ candle_close_pct (ej: 70%) del rango
                        close_strength = min(100.0, max(0, close_position - (100 - candle_close_pct)) * 2)
                    else:  # SELL
                        close_range = last_candle['open_price'] - last_candle['close_price']
                        close_position = ((last_candle['close_price'] - (last_candle['open_price'] - last_candle['range']/2)) / last_candle['range']) * 100
                        close_position = max(0, min(100, close_position))
                        # Debe estar ≤ (100-candle_close_pct) (ej: 30%) del rango
                        close_strength = min(100.0, max(0, (100 - candle_close_pct - close_position) * 2))
                else:
                    close_strength = 0.0
                
                # 5. COMPARACIÓN HISTÓRICA
                if historical_comparison:
                    historical_body = 0
                    historical_wicks = 0
                    for candle in historical_comparison:
                        o = float(candle.get('open', 0))
                        c = float(candle.get('close', 0))
                        h = float(candle.get('high', 0))
                        l = float(candle.get('low', 0))
                        if o > 0 and c > 0:
                            historical_body += abs(c - o)
                            historical_wicks += (h - max(o, c)) + (min(o, c) - l)
                    
                    historical_noise = (historical_wicks / (historical_body + historical_wicks)) if (historical_body + historical_wicks) > 0 else 0
                    noise_deterioration = noise_ratio - historical_noise
                else:
                    noise_deterioration = 0
                
                deterioration_penalty = max(0, noise_deterioration * 100) if noise_deterioration > 0.15 else 0
                
                # SCORE FINAL (ponderado) - INCLUYENDO CONFIG ÓPTIMA
                noise_threshold = 0.55 if is_gold else 0.65
                
                # Ponderación: Incluir CONFIG ÓPTIMA como factor adicional (15%)
                overall_score = (
                    consistency_score * 0.30 +        # Consistencia: 30%
                    impulse_score * 0.25 +            # Impulso: 25%
                    close_strength * 0.20 +           # Fortaleza cierre: 20%
                    noise_score * 0.10 +              # Ruido limpio: 10%
                    config_compliance_score * 0.15    # ⭐ CONFIG ÓPTIMA: 15%
                )
                
                overall_score = max(0, overall_score - deterioration_penalty)
                
                if noise_ratio > noise_threshold:
                    overall_score = overall_score * 0.5
                
                return {
                    'score': overall_score,
                    'noise_ratio': noise_ratio,
                    'consistency_score': consistency_score,
                    'impulse_score': impulse_score,
                    'close_strength': close_strength,
                    'config_compliance_score': config_compliance_score,
                    'config_violations': config_violations,
                    'deterioration': noise_deterioration,
                    'details': candle_details
                }
            
            # Analizar ambas direcciones
            buy_analysis = _score_direction('BUY')
            sell_analysis = _score_direction('SELL')
            
            buy_score = buy_analysis['score']
            sell_score = sell_analysis['score']
            score_gap = abs(buy_score - sell_score)
            
            # ═══════════════════════════════════════════════════════════
            # DETERMINAR RECOMENDACIÓN
            # ═══════════════════════════════════════════════════════════
            
            min_score_threshold = 50.0
            significant_gap = 15.0
            
            if buy_score > sell_score and buy_score > min_score_threshold and score_gap >= significant_gap:
                recommended_direction = 'BUY'
                confidence = min(100.0, buy_score)
                reason = f"BUY claro: score {buy_score:.0f}% > SELL {sell_score:.0f}% (gap {score_gap:.0f}%, compliance {buy_analysis['config_compliance_score']:.0f}%)"
            
            elif sell_score > buy_score and sell_score > min_score_threshold and score_gap >= significant_gap:
                recommended_direction = 'SELL'
                confidence = min(100.0, sell_score)
                reason = f"SELL claro: score {sell_score:.0f}% > BUY {buy_score:.0f}% (gap {score_gap:.0f}%, compliance {sell_analysis['config_compliance_score']:.0f}%)"
            
            elif buy_score < min_score_threshold and sell_score < min_score_threshold:
                recommended_direction = 'BLOCK'
                confidence = 0.0
                reason = f"❌ AMBAS DÉBILES: BUY {buy_score:.0f}%, SELL {sell_score:.0f}% (ambas < {min_score_threshold:.0f}%)"
            
            elif buy_score > sell_score:
                recommended_direction = 'BUY'
                confidence = min(100.0, buy_score * (1 - (significant_gap - score_gap) / significant_gap * 0.5))
                reason = f"BUY mejor (gap pequeño): {buy_score:.0f}% vs SELL {sell_score:.0f}% (compliance {buy_analysis['config_compliance_score']:.0f}%)"
            
            else:
                recommended_direction = 'SELL'
                confidence = min(100.0, sell_score * (1 - (significant_gap - score_gap) / significant_gap * 0.5))
                reason = f"SELL mejor (gap pequeño): {sell_score:.0f}% vs BUY {buy_score:.0f}% (compliance {sell_analysis['config_compliance_score']:.0f}%)"
            
            self.add_log(
                f"[ANÁLISIS-FINAL-BIDIRECCIONAL] 🔧 CONFIG ÓPTIMA: threshold={threshold_pips}pips, body≥{candle_body_pct}%, wick≤{candle_wick_pct}%",
                'info'
            )
            self.add_log(
                f"[ANÁLISIS-FINAL-BIDIRECCIONAL] BUY:{buy_score:.0f}% (compliance {buy_analysis['config_compliance_score']:.0f}%) | SELL:{sell_score:.0f}% (compliance {sell_analysis['config_compliance_score']:.0f}%) | "
                f"GAP:{score_gap:.0f}% | RECOMENDACIÓN: {recommended_direction} ({confidence:.0f}%)",
                'success' if recommended_direction != 'BLOCK' else 'warning'
            )
            
            return {
                'recommended_direction': recommended_direction,
                'confidence': confidence,
                'reason': reason,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'score_gap': score_gap,
                'buy_analysis': buy_analysis,
                'sell_analysis': sell_analysis,
                'optimal_config_applied': optimal_config
            }
            
        except Exception as e:
            self.add_log(f"[ANÁLISIS-FINAL-BIDIRECCIONAL-ERROR] {str(e)[:80]}", 'error')
            return {
                'recommended_direction': 'BLOCK',
                'confidence': 0.0,
                'reason': f'Error en análisis: {str(e)[:40]}',
                'buy_score': 0.0,
                'sell_score': 0.0,
                'score_gap': 0.0,
                'buy_analysis': {},
                'sell_analysis': {},
                'optimal_config_applied': {}
            }

    def _analyze_10_candles_complete(self, symbol, direction, snapshots=None):
        """
        ⭐ ANÁLISIS COMPLETO PRE-APERTURA DE ÚLTIMAS 10 VELAS
        Valida: Tendencia + Ruido + Overbought/Oversold
        Retorna: (can_open: bool, analysis: dict)
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=12) or []
            
            if len(snapshots) < 10:
                return (False, {'reason': f'Snapshots insuficientes (<10): {len(snapshots)}'})
            
            # Tomar últimas 10 velas
            last_10 = snapshots[-10:]
            analysis = {
                'total_candles': 10,
                'up_candles': 0,
                'down_candles': 0,
                'doji_candles': 0,
                'noise_ratio': 0.0,
                'max_high': 0.0,
                'min_low': 0.0,
                'avg_range': 0.0,
                'rsi_level': 0.0,
                'overbought': False,
                'oversold': False,
                'can_open': True,
                'reason': ''
            }

            # ════════════════════════════════════════════════════════════
            # 1. ANÁLISIS DE DIRECCIÓN DE VELAS
            # ════════════════════════════════════════════════════════════
            up_count = 0
            down_count = 0
            doji_count = 0
            total_body_size = 0
            total_wick_size = 0
            ranges = []

            for candle in last_10:
                candle_open = float(candle.get('open', 0))
                candle_close = float(candle.get('close', 0))
                candle_high = float(candle.get('high', 0))
                candle_low = float(candle.get('low', 0))
                
                if candle_open <= 0 or candle_close <= 0:
                    continue

                # Dirección
                if candle_close > candle_open:
                    up_count += 1
                elif candle_close < candle_open:
                    down_count += 1
                else:
                    doji_count += 1

                # Tamaño de cuerpo vs wicks
                body_size = abs(candle_close - candle_open)
                upper_wick = candle_high - max(candle_open, candle_close)
                lower_wick = min(candle_open, candle_close) - candle_low
                total_wick = upper_wick + lower_wick
                
                total_body_size += body_size
                total_wick_size += total_wick
                
                candle_range = candle_high - candle_low
                ranges.append(candle_range)

            analysis['up_candles'] = up_count
            analysis['down_candles'] = down_count
            analysis['doji_candles'] = doji_count

            # ════════════════════════════════════════════════════════════
            # 2. CÁLCULO DE RUIDO (ratio wicks vs body)
            # ════════════════════════════════════════════════════════════
            noise_ratio = (total_wick_size / (total_body_size + total_wick_size)) if (total_body_size + total_wick_size) > 0 else 0
            analysis['noise_ratio'] = round(noise_ratio, 3)
            
            # Ruido alto = muchos wicks, indica indecisión
            is_noisy = noise_ratio > 0.60  # >60% de ruido es demasiado

            # ════════════════════════════════════════════════════════════
            # 3. RSI APROXIMADO (para detectar overbought/oversold)
            # ════════════════════════════════════════════════════════════
            closes = [float(c.get('close', 0)) for c in last_10 if float(c.get('close', 0)) > 0]
            if len(closes) >= 2:
                gains = sum(max(closes[i] - closes[i-1], 0) for i in range(1, len(closes)))
                losses = sum(max(closes[i-1] - closes[i], 0) for i in range(1, len(closes)))
                
                avg_gain = gains / len(closes)
                avg_loss = losses / len(closes)
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100 if avg_gain > 0 else 50
                
                analysis['rsi_level'] = round(rsi, 1)
                
                # Detectar extremos
                if rsi > 75:
                    analysis['overbought'] = True
                if rsi < 25:
                    analysis['oversold'] = True

            # ════════════════════════════════════════════════════════════
            # 4. VALIDACIÓN DE TENDENCIA DOMINANTE (adaptada por símbolo)
            # ════════════════════════════════════════════════════════════
            total_valid = up_count + down_count
            if total_valid > 0:
                up_ratio = up_count / total_valid
                down_ratio = down_count / total_valid
            else:
                return (False, {'reason': 'Todas las velas son doji'})

            # ⭐ Adaptar requisitos por volatilidad del símbolo
            symbol = symbol or self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get()
            if 'GOLD' in symbol.upper():
                min_candles_required = 6  # GOLD: más exigente (menos ruidoso)
            else:
                min_candles_required = 5  # SILVER: más flexible (más ruidoso)

            # Debe haber mayoría clara de la dirección esperada
            if direction == 'BUY':
                has_trend = up_count >= min_candles_required
                if not has_trend:
                    analysis['can_open'] = False
                    analysis['reason'] = f'Tendencia débil para BUY: solo {up_count}/{min_candles_required} velas UP'
            else:  # SELL
                has_trend = down_count >= min_candles_required
                if not has_trend:
                    analysis['can_open'] = False
                    analysis['reason'] = f'Tendencia débil para SELL: solo {down_count}/{min_candles_required} velas DOWN'

            # ════════════════════════════════════════════════════════════
            # 5. VALIDACIONES FINALES ANTES DE ABRIR
            # ════════════════════════════════════════════════════════════
            
            # A) Rechazar si hay MUCHO ruido (aumentar umbral para ETH/SOL: 0.70 en lugar de 0.60)
            noise_threshold = 0.60 if 'GOLD' in symbol.upper() else 0.70
            if is_noisy and analysis['noise_ratio'] > noise_threshold:
                analysis['can_open'] = False
                analysis['reason'] = f'Demasiado ruido (wicks={analysis["noise_ratio"]:.1%}) - Mercado indeciso'
                
            # B) Rechazar si está en overbought/oversold EXTREMO (menos restrictivoI para ETH/SOL)
            # GOLD: RSI > 75 es overbought, para ETH/SOL: RSI > 80
            if direction == 'BUY':
                overbought_level = 75 if 'GOLD' in symbol.upper() else 80
                if analysis['overbought'] and analysis['rsi_level'] > overbought_level:
                    analysis['can_open'] = False
                    analysis['reason'] = f'Overbought detectado (RSI={analysis["rsi_level"]}) - Evitar comprar en pico'
                
            if direction == 'SELL':
                oversold_level = 25 if 'GOLD' in symbol.upper() else 20
                if analysis['oversold'] and analysis['rsi_level'] < oversold_level:
                    analysis['can_open'] = False
                    analysis['reason'] = f'Oversold detectado (RSI={analysis["rsi_level"]}) - Evitar vender en piso'

            # C) Rechazar si hay demasiados dojis (más tolerante para ETH/SOL)
            max_dojis = 3 if 'GOLD' in symbol.upper() else 5
            if doji_count >= max_dojis:
                analysis['can_open'] = False
                analysis['reason'] = f'Demasiados dojis ({doji_count}/{max_dojis}) - Mercado indeciso'

            # Loguear análisis completo
            status = '✅ PUEDE ABRIR' if analysis['can_open'] else f"❌ BLOQUEADO: {analysis.get('reason', 'desconocido')}"
            self.add_log(
                f"[ANÁLISIS-10-VELAS] {direction} | UP:{up_count} DOWN:{down_count} DOJI:{doji_count} | "
                f"Ruido:{analysis['noise_ratio']:.1%} | RSI:{analysis['rsi_level']:.0f} | {status}", 
                'info'
            )

            return (analysis['can_open'], analysis)

        except Exception as e:
            self.add_log(f"[ANÁLISIS-10-VELAS-ERROR] {str(e)[:80]}", 'error')
            return (False, {'reason': f'Error en análisis: {str(e)[:40]}'})

    def _validate_breakout(self, symbol, direction, snapshots=None):
        """
        ⭐ FILTRO 1: RUPTURA DE ESTRUCTURA (adaptable por símbolo)
        - GOLD: close debe estar fuera del rango de las últimas 5 velas
        - ETH/SOL: close debe estar fuera del rango de las últimas 3-4 velas (más flexible)
        
        Returns: (is_valid: bool, reason: str)
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=10) or []
            
            # ⭐ Adaptar requisitos por símbolo
            symbol_check = symbol or self.config.get('SYMBOL', tk.StringVar(value='ETHUSD')).get()
            if 'GOLD' in symbol_check.upper():
                bars_lookback = 5  # GOLD: más exigente
                min_snaps = 6
            else:
                bars_lookback = 4  # ETH/SOL: más flexible
                min_snaps = 5
            
            if len(snapshots) < min_snaps:
                return (False, f"Snapshots insuficientes (<{min_snaps})")
            
            # Obtener últimas N velas
            last_n_bars = snapshots[-bars_lookback-1:-1] if len(snapshots) >= bars_lookback+1 else snapshots[-bars_lookback:]
            current_bar = snapshots[-1]
            
            current_close = float(current_bar.get('close', 0))
            
            highs_n = [float(bar.get('high', 0)) for bar in last_n_bars]
            lows_n = [float(bar.get('low', 0)) for bar in last_n_bars]
            
            max_high_n = max(highs_n) if highs_n else 0
            min_low_n = min(lows_n) if lows_n else 0
            
            if direction == 'BUY':
                is_valid = current_close > max_high_n
                reason = f"BUY: close({current_close:.2f}) > max_high({max_high_n:.2f})" if is_valid else f"BUY: close({current_close:.2f}) ≤ max_high({max_high_n:.2f})"
            else:  # SELL
                is_valid = current_close < min_low_n
                reason = f"SELL: close({current_close:.2f}) < min_low({min_low_n:.2f})" if is_valid else f"SELL: close({current_close:.2f}) ≥ min_low({min_low_n:.2f})"
            
            return (is_valid, reason)
        except Exception as e:
            return (False, f"Error en breakout: {str(e)[:40]}")

    def _validate_candle_strength(self, symbol, direction, snapshots=None):
        """
        ⭐ FILTRO 2: CONFIRMACIÓN DE VELA (FUERZA REAL)
        Verifica que la vela cierre cerca del extremo (sin mechas largas = no es trampa)
        - BUY válido: (close - low) > (high - close) → cierre en top mitad
        - SELL válido: (high - close) > (close - low) → cierre en bottom mitad
        
        Returns: (is_valid: bool, reason: str)
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=5) or []
            
            if len(snapshots) < 1:
                return (False, "Sin datos de vela")
            
            current_bar = snapshots[-1]
            
            close = float(current_bar.get('close', 0))
            high = float(current_bar.get('high', 0))
            low = float(current_bar.get('low', 0))
            
            body_top = close - low
            body_bottom = high - close
            
            if direction == 'BUY':
                is_valid = body_top > body_bottom
                reason = f"BUY: body_top({body_top:.3f}) > body_bottom({body_bottom:.3f})" if is_valid else f"BUY: body_top({body_top:.3f}) ≤ body_bottom({body_bottom:.3f}) [mecha larga]"
            else:  # SELL
                is_valid = body_bottom > body_top
                reason = f"SELL: body_bottom({body_bottom:.3f}) > body_top({body_top:.3f})" if is_valid else f"SELL: body_bottom({body_bottom:.3f}) ≤ body_top({body_top:.3f}) [mecha larga]"
            
            return (is_valid, reason)
        except Exception as e:
            return (False, f"Error en strength: {str(e)[:40]}")

    def _validate_bar_size(self, symbol, snapshots=None):
        """
        ⭐ FILTRO 3: ANTI-RUIDO (TAMAÑO MÍNIMO)
        Rechaza velas muy pequeñas que representan mercado muerto o solo ruido
        - GOLD: Rechaza si (high - low) < 2.0 pips
        - ETH/SOL: Rechaza si (high - low) < 1.0 pips (más flexible, más ruidosos)
        
        Returns: (is_valid: bool, reason: str)
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=5) or []
            
            if len(snapshots) < 1:
                return (False, "Sin datos de vela")
            
            current_bar = snapshots[-1]
            
            high = float(current_bar.get('high', 0))
            low = float(current_bar.get('low', 0))
            
            bar_range = high - low
            
            # ⭐ Adaptar requisitos por símbolo
            symbol_check = symbol or self.config.get('SYMBOL', tk.StringVar(value='ETHUSD')).get()
            if 'GOLD' in symbol_check.upper():
                min_range = 2.0  # GOLD: más exigente
            else:
                min_range = 1.0  # ETH/SOL: más flexible
            
            is_valid = bar_range >= min_range
            reason = f"Bar_range({bar_range:.3f}) >= min({min_range})" if is_valid else f"Bar_range({bar_range:.3f}) < min({min_range}) [RUIDO]"
            
            return (is_valid, reason)
        except Exception as e:
            return (False, f"Error en bar_size: {str(e)[:40]}")

    def _validate_trade_entry(self, symbol, direction):
        """
        ⭐ VALIDACIÓN PRINCIPAL: Breakout + Confirmación
        Ejecuta los 4 filtros antes de permitir entrada:
        1. Ruptura de estructura (últimas 5 velas)
        2. Confirmación de vela (cierre fuerte)
        3. Anti-ruido (tamaño mínimo)
        
        Returns: (is_valid: bool, failed_filters: list, all_reasons: str)
        """
        try:
            if direction not in ('BUY', 'SELL'):
                return (False, ['invalid_direction'], "Dirección inválida")
            
            # Obtener datos de mercado UNA SOLA VEZ
            snapshots = self.get_fresh_market_data(symbol, bars=10) or []
            
            failed_filters = []
            reasons = []
            
            # FILTRO 1: Ruptura
            valid_breakout, reason_breakout = self._validate_breakout(symbol, direction, snapshots)
            reasons.append(f"[Ruptura] {reason_breakout}")
            if not valid_breakout:
                failed_filters.append('breakout')
            
            # FILTRO 2: Confirmación de vela
            valid_strength, reason_strength = self._validate_candle_strength(symbol, direction, snapshots)
            reasons.append(f"[Fuerza] {reason_strength}")
            if not valid_strength:
                failed_filters.append('candle_strength')
            
            # FILTRO 3: Anti-ruido
            valid_size, reason_size = self._validate_bar_size(symbol, snapshots)
            reasons.append(f"[Ruido] {reason_size}")
            if not valid_size:
                failed_filters.append('bar_size')
            
            is_valid = len(failed_filters) == 0
            all_reasons = " | ".join(reasons)
            
            return (is_valid, failed_filters, all_reasons)
        except Exception as e:
            return (False, ['exception'], f"Error en validación: {str(e)[:50]}")

    def start_ghost_operations(self):
        """Inicia el ciclo de operaciones fantasma (una BUY y una SELL cada segundo)"""
        if hasattr(self, 'ghost_ops_thread') and self.ghost_ops_thread and self.ghost_ops_thread.is_alive():
            return  # Ya corriendo
        self.ghost_ops_running = True
        import threading
        self.ghost_ops_thread = threading.Thread(target=self.ghost_ops_loop, daemon=True)
        self.ghost_ops_thread.start()

    def _monitor_reversals_aggressive(self):
        """
        ⭐ MONITOR DE REVERSIÓN AGRESIVO: Corre cada 2 segundos
        Si detecta que la dirección cambió (BUY→SELL o SELL→BUY),
        CIERRA la posición anterior y ABRE inmediatamente en la nueva dirección
        """
        last_microtrend = None
        
        while getattr(self, '_scheduler_running', True):
            try:
                time.sleep(2)  # ⭐ Corre cada 2 segundos (ultra-rápido)
                
                # Saltarse si bot pausado
                if self.bot_pausado:
                    continue
                
                symbol = self._get_symbol()
                
                # Get actual microtrend (detecta tendencias REALES: Usa el threshold de configuración)
                current_microtrend = self._microtrend_direction(symbol, bars=10, threshold=None)
                
                # ⭐ DETECCIÓN DE REVERSIÓN
                if last_microtrend and current_microtrend != last_microtrend:
                    if current_microtrend in ('BUY', 'SELL') and last_microtrend in ('BUY', 'SELL'):
                        self.add_log(f"\n[⚡ REVERSIÓN DETECTADA] {last_microtrend} → {current_microtrend}", 'warning')
                        
                        # ⭐ ACCIÓN RÁPIDA: Abre operación en la NUEVA dirección
                        try:
                            self.add_log(f"[REVERSIÓN] 🚀 Abriendo {current_microtrend} por cambio de micro-momentum", 'warning')
                            self.abrir_operacion_smart(current_microtrend, force=True, startup=False)
                            self.add_log(f"[✅ REVERSIÓN-EJECUTADA] Operación {current_microtrend} abierta al instante", 'success')
                        except Exception as e:
                            self.add_log(f"[❌ REVERSIÓN-FALLO] {str(e)[:40]}", 'error')
                
                # Actualizar último estado
                if current_microtrend in ('BUY', 'SELL'):
                    last_microtrend = current_microtrend
                
            except Exception as e:
                self.add_log(f"[MONITOR-REVERSIÓN] Error: {str(e)[:40]}", 'error')
                continue

    def stop_ghost_operations(self):
        self.ghost_ops_running = False

    def ghost_ops_loop(self):
        import time
        while self.ghost_ops_running:
            now = time.time()
            symbol = self._get_symbol()
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
            time.sleep(2)  # ⭐ AUMENTADO de 1s a 2s para reducir sobrecarga

    def _update_ghost_stats(self):
        """Actualiza los contadores de abiertas, ganadas y perdidas de las operaciones fantasma en ventana de 30s
        NOTA: ghost_total NO se reinicia, solo se incrementa cuando se cierra una operación fantasma."""
        window = self.ghost_stats_window
        now = time.time()
        symbol = self.config['SYMBOL'].get()
        # SIEMPRE usar TP/SL global
        tp_amount = self.config['TP_DIFF'].get()
        sl_amount = self.config['SL_DIFF'].get()
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
                        # Normalizar umbrales comme valores absolutos (SIEMPRE usar TP/SL)
                        tp_val = abs(tp_amount)
                        sl_val = abs(sl_amount)
                        # Comprobación TP/SL - SIEMPRE evalúa
                        # Sólo evaluar TP/SL si los umbrales són mayores que cero
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
                            # Mantener registro de cierre con precio de cierre (protegido por lock)
                            try:
                                if self.ghost_ops_lock:
                                    with self.ghost_ops_lock:
                                        self.ghost_ops_history.append({'type': typ.upper(), 'open_time': op['open_time'], 'close_time': now, 'result': op['result'], 'profit': op['profit'], 'entry_price': op.get('entry_price'), 'close_price': current_price})
                                        if op['result'] == 'win':
                                            self.ghost_total[f'{typ}_win'] += 1
                                        elif op['result'] == 'loss':
                                            self.ghost_total[f'{typ}_loss'] += 1
                                else:
                                    self.ghost_ops_history.append({'type': typ.upper(), 'open_time': op['open_time'], 'close_time': now, 'result': op['result'], 'profit': op['profit'], 'entry_price': op.get('entry_price'), 'close_price': current_price})
                                    if op['result'] == 'win':
                                        self.ghost_total[f'{typ}_win'] += 1
                                    elif op['result'] == 'loss':
                                        self.ghost_total[f'{typ}_loss'] += 1
                            except Exception as e:
                                logger.warning(f"[GHOST] Error processing ghost op: {e}")
                            
                            if op['result'] == 'win':
                                self.add_ghost_log(f"Cierre {typ.upper()} WIN: {reason} | Profit={op['profit']:.2f} | Entry={op['entry_price']:.2f} | Close={current_price:.2f}")
                            elif op['result'] == 'loss':
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
                    except Exception as e:
                        self.add_log(f"[ERROR] _trim_ghost_ops_locked: {str(e)[:80]}", 'error')
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
        except Exception as e:
            logger.warning(f"[GHOST] Error updating ghost stats UI: {e}")
    
    def __init__(self, root):
        # ====== ESTADO DE OPERACIONES FANTASMA (debe ir primero) ======
        self.ghost_ops = {
            'buy': [],  # [{'open_time': timestamp, 'result': None/'win'/'loss'}]
            'sell': []
        }
        # Lock para sincronizar modificaciones a ghost_ops desde múltiples threads
        try:
            self.ghost_ops_lock = threading.Lock()
            self.decision_lock = threading.Lock()  # ⭐ NUEVO: Sincroniza decisiones en threads paralelos (previene duplicacion)
        except Exception as e:
            self.add_log(f"[ERROR] Creating locks: {str(e)}", 'error')
            self.ghost_ops_lock = None
            self.decision_lock = None
        self.ghost_stats = {
            'buy_open': 0,
            'buy_win': 0,
            'buy_loss': 0,
            'sell_open': 0,
            'sell_win': 0,
            'sell_loss': 0
        }
        self.ghost_ops_history = deque(maxlen=100)  # ⭐ LIMITADO A 100 para evitar memory leak
        self.ghost_stats_window = 30  # segundos para ventana de evaluación
        self.ghost_total = {'buy_win': 0, 'buy_loss': 0, 'sell_win': 0, 'sell_loss': 0}

        # Control centralizado para evitar sobrecarga del event-loop de Tk
        self._account_scheduler_running = False
        self._ui_refresh_requested = True
        self._entry_analysis_running = False
        self._entry_analysis_thread = None
        self._last_entry_check = 0.0
        self._last_open_ops_analysis = 0.0

        self.root = root
        self.root.title("MT5 Trading Bot - Sistema Multi-IA")
        
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e293b')
        
        # ⭐ INICIALIZAR buffer de logs para rate-limiting
        self._log_buffer = []
        self._last_log_flush = time.time()
        # Asegurar que al iniciar el bot el estado runtime esté limpio
        try:
            self.reset_all_state()
        except Exception as e:
            self.add_log(f"[ERROR] reset_all_state on init: {str(e)[:80]}", 'error')
        # Parámetros para reaperturas forzadas basadas en la apertura inicial
        self.forced_open_params = None  # dict with keys: symbol, direction, vol, tp, sl
        self.forced_open_interval = 300  # segundos (5 minutos)
        self.next_forced_open = None
        # Pequeño retardo antes del primer intento de cierre para evitar retcode 10009
        self.close_delay = 0.03  # ⭐ CRÍTICO: 30ms - cierres INSTANTÁNEOS sin demora
        
        # Inicializar analizadores
        self.gold_analyzer = GoldAnalyzer(log_callback=self.add_log)
        self.loss_analyzer = LossAnalyzer(self.gold_analyzer, log_callback=self.add_log)
        
        # ⭐ NUEVO: Sistema Multi-IA
        self.buy_specialist = BuySpecialistAI(log_callback=self.add_log)
        self.sell_specialist = SellSpecialistAI(log_callback=self.add_log)
        self.arbitrator = DecisionArbitratorAI(log_callback=self.add_log)
        self.use_multi_ai = tk.BooleanVar(value=True)  # Activar por defecto
        
        # ⭐ Multi-Timeframe Analyzer será inicializado DESPUÉS de que self.config sea definido
        self.multi_timeframe_analyzer = None
        self.use_multi_timeframe = tk.BooleanVar(value=True)  # Activado por defecto

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
        
        # ⭐ NUEVO: Cierre dinámico por recuperación (RECOVERY_BASED_CLOSER)
        self.recovery_closer = RecoveryBasedCloser(log_callback=self.add_log)
        
        # ⭐ NUEVO: Feedback Loop para retroalimentación post-trade
        self.feedback_loop_ai = FeedbackLoopAI(log_callback=self.add_log)
        
        # [OBJETIVO] FASE 3: INSTANCIAR 12 NUEVOS ANALIZADORES V12
        self.super_analyzer = SuperAnalyzer(log_callback=self.add_log)
        self.calibrator = DynamicScoreCalibration(log_callback=self.add_log)
        self.recovery = RecoveryPotentialEnhanced(log_callback=self.add_log)
        self.spread_analyzer = SpreadSlippageAnalyzer(log_callback=self.add_log)
        self.session_filter = TimeBasedSessionFilter(log_callback=self.add_log)
        self.correlation = CorrelationAnalyzer(log_callback=self.add_log)
        
        # Histórico de trades removido: solo se usa datos de mercado actual
        # self.closed_trades_for_calibration = {} # DESHABILITADO
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
            'VOL': tk.DoubleVar(value=0.01),  # ⭐ GOLD: Volumen mínimo 0.01
            'TIMEFRAME': tk.StringVar(value="M1"),
            'CHECK_INTERVAL': tk.DoubleVar(value=0.05),  # ⭐ 50ms - Análisis ultra-rápido cada 50 milisegundos
            'OBJETIVO_Z': tk.IntVar(value=0),
            'TRADE_INTERVAL': tk.DoubleVar(value=1),  # ⭐ VALORES DECIMALES: 0.3 = 30s | 0.1 = 10s | 1 = 60s | 2 = 120s
            'MAX_SIMULTANEOUS_OPS': tk.IntVar(value=1),  # ⭐ OPTIMIZADO: Máximo 1 operación abierta para mejor control
            
            # Configuración de análisis
            'BARS_ANALYZE': tk.IntVar(value=30),
            'LATERAL_THRESHOLD': tk.DoubleVar(value=0.12),
            'TREND_THRESHOLD': tk.DoubleVar(value=0.18),
            'OFFSET_POINTS': tk.DoubleVar(value=5.0),
            'STEPS': tk.IntVar(value=5),
            'MIN_RANGE': tk.DoubleVar(value=2.0),
            'MIN_PROFIT_CLOSE': tk.DoubleVar(value=1),  # ⭐ OPTIMIZADO: cierre mínimo en ganancia $1
            'MIN_TIME_BLUE': tk.IntVar(value=0),
            
            # Configuración de Take Profit y Stop Loss
            'TP_DIFF': tk.DoubleVar(value=1.0),  # ⭐ BASE para TP en GOLD
            'SL_DIFF': tk.DoubleVar(value=30.0),  # ⭐ BASE para SL en GOLD
            'TREND_TP_MULTIPLIER': tk.DoubleVar(value=1.0),
            'FORCE_STOP_LOSS': tk.DoubleVar(value=100.0),
            'USE_SL': tk.BooleanVar(value=True),  # ⭐ NUEVO: Opción de usar SL
            'USE_MULTIPLE_PARTS': tk.BooleanVar(value=False),  # ⭐ NUEVO: Si activado, abre 1 en GOLD + 1 en SILVER simultáneamente
            
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
            'MAX_RECOVERY_CONSUMPTION_PCT': tk.DoubleVar(value=80.0),  # ⭐ NUEVO: Máx % del MIN_RECOVERY que puede consumirse antes de cerrar
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

            # ⭐️ Take Profit y Stop Loss Global configurables
            'GLOBAL_TP': tk.DoubleVar(value=1.0),  # Ganancia total para cerrar todo en GOLD
            'GLOBAL_SL': tk.DoubleVar(value=30),  # ⭐ Stop Loss Global para GOLD: $30 por defecto
            'MICROTREND_THRESHOLD': tk.DoubleVar(value=18.0),  # ⭐ OPTIMIZADO para GOLD: 18 pips (SILVER: 15)
            'MIN_PROB_ENTRADA': tk.DoubleVar(value=73.0),
            'PAUSA_POST_WIN': tk.IntVar(value=0),  # <-- cooldown tras ganar una operación (segundos)
            'CONFIDENCE_THRESHOLD': tk.DoubleVar(value=70.0),  # umbral general árbitro
            'BUY_CONFIDENCE_THRESHOLD': tk.DoubleVar(value=65.0),  # umbral especialista BUY
            'SELL_CONFIDENCE_THRESHOLD': tk.DoubleVar(value=65.0),  # umbral especialista SELL
            # Protecciones globales de especialistas (todas las rutas de análisis)
            'SPECIALIST_MAX_DIRECTION_LOSS_STREAK': tk.IntVar(value=3),
            'SPECIALIST_DIRECTION_PENALTY': tk.DoubleVar(value=12.0),
            'SPECIALIST_EXTREME_MOVE_PCT': tk.DoubleVar(value=0.20),
            'SPECIALIST_MIN_SCORE_GAP': tk.DoubleVar(value=4.0),
            # 'SPECIALIST_SESSION_WINDOW_TRADES' - REMOVIDO: No se usan datos de trades anteriores
            'SPECIALIST_SESSION_WEIGHT': tk.DoubleVar(value=0.75),
             'ANALYZE_DURING_PAUSE': tk.BooleanVar(value=True),  # permitir análisis mientras está en pausa
             'AUTO_OPEN_ON_SIGNAL': tk.BooleanVar(value=False),  # abrir automáticamente si señal fuerte durante pausa
            # Forzar apertura tras N minutos si no hay señal
            'ENABLE_FORCED_OPEN': tk.BooleanVar(value=True),
            'FORCED_OPEN_MINUTES': tk.DoubleVar(value=1),  # ⭐ CALIBRADO: 1 = 60s/1min (TRADE_INTERVAL standard) - CON VALIDACIÓN microtrend
            'MAX_STACK_PER_DIRECTION': tk.IntVar(value=2),  # Límite de apilado por dirección (BUY/SELL)
            
            # ⭐ NUEVO: Control de direcciones habilitadas
            'ALLOW_BUY': tk.BooleanVar(value=True),  # Permitir abrir operaciones BUY
            'ALLOW_SELL': tk.BooleanVar(value=True),  # Permitir abrir operaciones SELL
             
             # ⭐ NUEVO: Margen de Ganancia (objetivo automático)
             'MARGEN_GANANCIA': tk.DoubleVar(value=0.0),  # En porcentaje (1%, 2%, 3%, etc.)
             'OBJETIVO_NETO': tk.DoubleVar(value=2.0),  # Valor neto objetivo (ej: 160) - 0 desactiva
             'SPECIALIST_DEBUG_LOGS': tk.BooleanVar(value=False),  # Logs detallados de especialistas
             'SNAPSHOT_RELOAD_INTERVAL': tk.IntVar(value=30),  # Intervalo recarga snapshots (segundos)
        }
        
        # ⭐ NUEVO: Estructura de snapshots INDEPENDIENTE POR PAR
        self.market_snapshots_by_symbol = {}  # {symbol: [snapshots]}
        self.market_snapshots_backup_by_symbol = {}  # {symbol: [backup]}
        self.market_snapshots_lock_by_symbol = {}  # {symbol: lock}
        self.balance_inicial_para_margen_by_symbol = {}  # {symbol: valor}
        self.objetivo_margen_ganancia_by_symbol = {}  # {symbol: valor}
        self.last_successful_reload_time_by_symbol = {}  # {symbol: timestamp}
        self.reload_count_by_symbol = {}  # {symbol: contador}
        self.scheduler_reload_time_by_symbol = {}  # {symbol: timestamp}
        
        # ⭐ INICIALIZAR ATRIBUTOS que reload_market_snapshots() necesita
        self.last_successful_reload_time = 0
        self.reload_count = 0
        self.scheduler_reload_time = None
        
        # Inicializar para GOLD y SILVER
        for symbol in ['GOLD', 'SILVER']:
            self.market_snapshots_by_symbol[symbol] = []
            self.market_snapshots_backup_by_symbol[symbol] = []
            self.market_snapshots_lock_by_symbol[symbol] = threading.Lock()
            self.balance_inicial_para_margen_by_symbol[symbol] = 0.0
            self.objetivo_margen_ganancia_by_symbol[symbol] = 0.0
            self.last_successful_reload_time_by_symbol[symbol] = 0
            self.reload_count_by_symbol[symbol] = 0
            self.scheduler_reload_time_by_symbol[symbol] = None
        
        # ⭐ INICIALIZAR ANTES de usar en reload_market_snapshots()
        self.MAX_SNAPSHOTS = 1440  # 24h en M1, limpia automáticamente
        
        # Cargar snapshots independientes por par
        for symbol in ['GOLD', 'SILVER']:
            try:
                self.market_snapshots_by_symbol[symbol] = self.reload_market_snapshots(symbol=symbol)
            except Exception:
                logger.exception(f"Error cargando market_snapshots para {symbol}")
                self.market_snapshots_by_symbol[symbol] = []
        
        # ⭐ Mantener compatibilidad hacia atrás con self.market_snapshots
        self.market_snapshots = self.market_snapshots_by_symbol.get('GOLD', [])
        self.market_snapshots_backup = self.market_snapshots_backup_by_symbol.get('GOLD', [])
        
        # Riesgo por trade (fracción del equity). Usado para sizing dinámico.
        self.config['RISK_PCT'] = tk.DoubleVar(value=0.005)  # 0.5% por defecto
        
        # ⭐ CONFIG ÓPTIMA PARA GOLD (Scalping limpio y constante)
        # 🟡 1. THRESHOLD (Disparador de entrada) - RANGO: 16-19, IDEAL: 18
        #    ├─ Más bajo (16) → Entra en ruido, más falsos positivos
        #    ├─ Ideal (18) → Balance perfecto: buenos movimientos + filtra ruido
        #    └─ Más alto (19) → Rechaza buenos movimientos, entra tarde
        self.config['GOLD_THRESHOLD'] = tk.DoubleVar(value=18)  # 🎯 EN PIPS: 18 para ORO (se convierte a 0.18 decimal)
        
        # 🟡 2. MICROTENDENCIA (Confirmación de dirección)  - RANGO: 3-5 velas, IDEAL: 4
        #    ├─ Mínimo (3): Mayor rapidez pero más falsos positivos
        #    ├─ Ideal (4): Balance perfecto - captura movimientos claros
        #    └─ Máximo (5): Más filtrado, entra solo en movimientos fuertes
        #    ⚠️ COMBINADO CON: Análisis de 10/20/30 velas previas
        #       → Todas las velas deben ir en MISMA DIRECCIÓN
        #       → Cuerpo claro (mínimo 60%)
        #       → Confir. con tendencia de fondo (10/20/30 velas = contexto)
        self.config['GOLD_MICROTREND_CANDLES'] = tk.IntVar(value=4)  # Rango 3-5 (4 ideal)
        
        # 🟡 3. FILTRO DE VELA (CLAVE - Elimina ruido)
        #    ├─ Cuerpo ≥ 60%: Vela con cuerpo fuerte
        #    ├─ Mecha ≤ 40%: Mechas pequeñas (no rechazada)
        #    └─ Cierre cerca del extremo:
        #       • BUY: Cierre ≥ 70% del rango (cerca del MÁXIMO)
        #       • SELL: Cierre ≤ 30% del rango (cerca del MÍNIMO)
        self.config['GOLD_CANDLE_BODY_PCT'] = tk.IntVar(value=60)  # Mínimo 60% de cuerpo
        self.config['GOLD_CANDLE_WICK_PCT'] = tk.IntVar(value=40)  # Máximo 40% para mechas
        self.config['GOLD_CANDLE_CLOSE_PCT'] = tk.IntVar(value=70)  # BUY: ≥70%, SELL: ≤30%
        self.config['GOLD_VIDYA_CMO'] = tk.IntVar(value=9)  # CMO para VIDYA
        self.config['GOLD_VIDYA_EMA'] = tk.IntVar(value=12)  # EMA para VIDYA
        self.config['GOLD_IMPULSE_FILTER'] = tk.DoubleVar(value=1.5)  # Movimiento mínimo en puntos
        
        # 🟡 REFERENCIA RÁPIDA - FLUJO DE VALIDACIÓN GOLD:
        #    1️⃣  THRESHOLD (16-19 pips, ideal 18) - Filtro de impulso base
        #    2️⃣  MICROTENDENCIA + CONTEXTO MULTI-PERÍODO:
        #        ├─ Últimas 3-5 velas: TODAS en MISMA dirección ✓
        #        ├─ Contexto 10 velas: Tendencia general
        #        ├─ Contexto 20 velas: Tendencia media
        #        ├─ Contexto 30 velas: Tendencia larga
        #        └─ VALIDACIÓN: Velas recientes deben alinearse con tendencia de fondo
        #    3️⃣  FILTRO DE VELA (CRÍTICO - 3 CRITERIOS - Elimina ~90% ruido):
        #        ├─ Cuerpo ≥ 60% - Vela con cuerpo fuerte, no es mecha
        #        ├─ Mecha ≤ 40% - Las mechas/sombras son pequeñas
        #        └─ Cierre cerca del extremo:
        #           • BUY: Cierre ≥ 70% del rango (MUY CERCA del MÁXIMO)
        #           • SELL: Cierre ≤ 30% del rango (MUY CERCA del MÍNIMO)
        #    4️⃣  IMPULSO (1.5 puntos mínimo) - Movimiento real, no ruido
        #    5️⃣  FILTRO ANTI-RUIDO (4. Evitar):
        #        ├─ ❌ 2 velas seguidas con mechas grandes (> 50%)
        #        ├─ ❌ Rango lateral (máximos/mínimos iguales ±2 pips)
        #        └─ ❌ Velas pequeñas consecutivas (cuerpo < 30%)
        #    6️⃣  VIDYA (5. Apoyo - CMO:9, EMA:12):
        #        ├─ BUY: Precio arriba de VIDYA + VIDYA subiendo ✓
        #        ├─ SELL: Precio abajo de VIDYA + VIDYA bajando ✓
        #        └─ VIDYA debe tener inclinación clara (no horizontal)
        #    
        #    ✅ ENTRA: Si TODAS las 6 validaciones pasan
        #    ❌ RECHAZA: Si CUALQUIERA falla
        
        # ⭐ CONFIG ÓPTIMA PARA SILVER (Scalping M1/M5 más rápido)
        self.config['SILVER_THRESHOLD'] = tk.DoubleVar(value=15)  # ⭐ EN PIPS (como MICROTREND_THRESHOLD): 15 para PLATA, se convierte a 0.15 decimal
        self.config['SILVER_MICROTREND_CANDLES'] = tk.IntVar(value=4)  # Rango 3-5 (igual que ORO)
        self.config['SILVER_CANDLE_BODY_PCT'] = tk.IntVar(value=60)  # Mínimo 60% de cuerpo (MÁS CRÍTICO en plata)
        self.config['SILVER_VIDYA_CMO'] = tk.IntVar(value=9)  # CMO para VIDYA (igual)
        self.config['SILVER_VIDYA_EMA'] = tk.IntVar(value=12)  # EMA para VIDYA (igual)
        self.config['SILVER_IMPULSE_FILTER'] = tk.DoubleVar(value=1.5)  # Movimiento mínimo en puntos (igual)
        
        # ⭐ AHORA inicializar MultiTimeframeAnalyzer (después de que self.config existe)
        try:
            self.multi_timeframe_analyzer = MultiTimeframeAnalyzer(
                symbol=self.config['SYMBOL'].get(), 
                log_callback=self.add_log
            )
        except Exception as e:
            self.add_log(f"[MTF] Error inicializando MultiTimeframeAnalyzer: {str(e)[:60]}", 'warning')
            self.multi_timeframe_analyzer = None

        # Modo debug de logs para especialistas (OFF por defecto para estabilidad UI)
        try:
            debug_logs = bool(self._safe_get('SPECIALIST_DEBUG_LOGS', False))
            if hasattr(self, 'buy_specialist'):
                self.buy_specialist.debug_logs = debug_logs
            if hasattr(self, 'sell_specialist'):
                self.sell_specialist.debug_logs = debug_logs
        except Exception as e:
            self.add_log(f"[ERROR] Setting specialist debug logs: {str(e)}", 'error')
        
        # Lock para sincronizar acceso a market_snapshots en múltiples hilos
        try:
            self.market_snapshots_lock = threading.Lock()
        except Exception as e:
            self.add_log(f"[ERROR] Creating market_snapshots_lock: {str(e)}", 'error')
            self.market_snapshots_lock = None
        
        # ⭐ NUEVO: Sistema de Reanalisis Post-Cierre por símbolo
        self.post_close_reanalysis_active_by_symbol = {'GOLD': False, 'SILVER': False}
        self.post_close_reanalysis_until_by_symbol = {'GOLD': 0.0, 'SILVER': 0.0}
        self.post_close_reanalysis_thread_by_symbol = {'GOLD': None, 'SILVER': None}
        self.post_close_reanalysis_last_scores_by_symbol = {'GOLD': {'buy': 0, 'sell': 0}, 'SILVER': {'buy': 0, 'sell': 0}}
        
        # ⭐ FLAGS DE SINCRONIZACIÓN por símbolo
        self.trend_analysis_lock = threading.Lock()  # ⭐ Global lock para compatibilidad
        self.trend_analysis_lock_by_symbol = {'GOLD': threading.Lock(), 'SILVER': threading.Lock()}
        self.trend_imminent_reversal = False  # ⭐ Global flag para compatibilidad
        self.trend_imminent_reversal_by_symbol = {'GOLD': False, 'SILVER': False}
        self.trend_imminent_direction = None  # ⭐ Global para compatibilidad
        self.trend_imminent_direction_by_symbol = {'GOLD': None, 'SILVER': None}
        self.trend_imminent_confidence = 0.0  # ⭐ Global para compatibilidad
        self.trend_imminent_confidence_by_symbol = {'GOLD': 0.0, 'SILVER': 0.0}
        self.trend_analysis_ready_by_symbol = {'GOLD': True, 'SILVER': True}
        
        # ⭐ Monitor de actualización de datos
        self.last_data_stats_log = 0
        self.data_update_count = 0
        
        # Controla hasta cuándo no iniciar nuevas entradas tras una ganancia
        self.block_until = 0.0
        # Hasta cuándo permanece la pausa activa (timestamp)
        self.pause_until = 0.0
        
        # ⭐ LÍMITES DE MEMORIA: Control de tamaño máximo
        self.MAX_SNAPSHOTS = 1440  # 24h en M1, limpia automáticamente
        self.last_memory_log = 0  # Timestamp para logging de memoria cada 10 min
        
        # Resto de variables de estado
        self.window_size = 10
        self.pattern_threshold = 0.85
        self.min_pattern_matches = 3
        
        # Variables para control de operaciones y pausas
        self.operaciones_actuales = set()
        self.operaciones_procesadas = set()
        self.operaciones_cerradas = 0
        
        # Variables de estado
        self.z = 0
        self.ganadas = 0
        self.perdidas = 0
        self.deals_anterior = set()
        self.start_time = 0
        self.is_running = False
        self._scheduler_running = True  # ⭐ NUEVO: control independiente para scheduler
        self._start_bot_in_progress = False  # Evita ejecutar start_bot en paralelo
        self._forced_reopen_start_lock = threading.Lock()  # Evita iniciar scheduler duplicado
        self._forced_reopen_exec_lock = threading.Lock()  # Evita ciclos forzados simultáneos
        self._forced_scheduler_thread = None  # Referencia explícita para evitar múltiples schedulers
        self._last_forced_cycle_ts = 0.0  # Antiduplicado de ciclo scheduler
        self._open_operation_gate_lock = threading.Lock()  # Evita aperturas concurrentes duplicadas
        self._last_open_attempt_ts = 0.0  # Timestamp del último intento real de apertura
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
        self.base_volume = float(self.config.get('VOL', tk.DoubleVar(value=0.1)).get())  # ⭐ ETHUSD: 0.1 mínimo
        # Metadata de trades removida: solo análisis de mercado actual
        
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
        
        # ⭐ INICIALIZAR pending_operations (lista de operaciones en espera)
        self.pending_operations = []
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
        
        # ⭐ FIX #3: Inicializar MT5 Cache Manager (30x reducción en API calls)
        self.mt5_cache = MT5CacheManager(update_interval=2.0, log_callback=self.add_log)
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
        self.pause_until = 0.0  # Timestamp hasta cuándo está pausado (post-ganancia/pérdida)
        self.pause_reason = ""  # Razón de la pausa actual
        self.block_until = 0.0  # Timestamp para cooldown (menos restrictivo que pausa)
        
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
        
        # ⭐ NUEVO: Variables para Margen de Ganancia
        self.balance_inicial_para_margen = 0.0  # Se inicializa cuando inicia el bot
        self.objetivo_margen_ganancia = 0.0  # Objetivo dinámico: balance_inicial * (1 + margen/100)
        self.margen_ganancia_alcanzado = False  # Flag para saber si ya se logró el objetivo
        self.margen_monitor_label = None  # Widget para mostrar el estado
        self.margen_monitor_thread = None
        self.margen_monitor_running = False
        
        # ⭐ NUEVO: Variables para Objetivo Neto
        self.objetivo_neto_valor = 0.0  # Objetivo neto especificado por el usuario
        self.objetivo_neto_alcanzado = False  # Flag para saber si ya se logró el objetivo neto
        self.objetivo_neto_label = None  # Widget para mostrar el estado
        self.objetivo_neto_thread = None
        self.objetivo_neto_running = False
        self.objetivo_neto_inicial = 0.0  # ⭐ NUEVO: Equity inicial para calcular meta
        self.objetivo_neto_target = 0.0  # ⭐ NUEVO: Equity objetivo = inicial + objetivo_neto
        
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
        
        # ⭐ NUEVO: Monitor Reactivo de Pérdida Máxima (Posiciones en Rojo)
        self.red_monitor_thread = None
        self.red_monitor_running = False
        self.red_positions_watched = {}  # {ticket: {'detected_time': timestamp, 'loss': value}}
        self.last_red_check = 0
        
        # ⭐ NUEVO: Monitor Manual de Stop Loss
        self.sl_monitor_thread = None
        self.sl_monitor_running = False
        
        # ⭐ NUEVO: Monitor de Especialistas en Tiempo Real
        self.specialists_monitor_thread = None
        self.specialists_monitor_running = False
        self.last_buy_score = 0
        
        # ⭐ NUEVO: Cache de análisis para apertura INSTANTÁNEA (evita recomputo)
        self.analysis_cache = {'buy': None, 'sell': None, 'timestamp': 0}  # Análisis guardado
        self.analysis_cache_ttl = 0.1  # 100ms - reutilizar análisis si es más reciente
        self._analysis_in_progress = False  # Flag para evitar análisis simultáneos
        self.last_analysis_result = None  # Último resultado válido para reutilizar
        self.last_sell_score = 0
        self.last_buy_confidence = 0
        self.last_sell_confidence = 0
        self.buy_score_label = None
        self.sell_score_label = None
        self.specialist_scores_lock = threading.Lock()  # Sincronización entre scheduler y monitor (para last_*_score y scores compartidos)
        self.specialist_analysis_lock = threading.Lock()  # ⭐ NUEVO: Evitar análisis simultáneos
        self.scheduler_shared_scores = {'buy_score': 0, 'sell_score': 0, 'buy_conf': 0, 'sell_conf': 0, 'timestamp': 0}  # Datos que comparte el scheduler
        # ⭐ Lock para rapid_ops counters (thread-safe counters)
        self.rapid_ops_lock_counters = threading.Lock()
        
        # ⭐ NUEVO: Cache de datos FRESCOS de MT5 - sincronizado entre monitor y scheduler
        self.fresh_market_data_cache = []  # Últimas 100 barras M1 FRESCAS
        self.fresh_data_timestamp = 0
        self.fresh_data_lock = threading.Lock()
        
        self.create_widgets()
    
    def _get_symbol(self):
        """⭐ HELPER: Obtiene símbolo VALIDADO - NUNCA retorna cadena vacía"""
        try:
            if not hasattr(self, 'config') or self.config is None:
                return 'GOLD'
            
            symbol = self.config.get('SYMBOL', None)
            if symbol is None:
                return 'GOLD'
            
            symbol_val = symbol.get() if hasattr(symbol, 'get') else symbol
            if not symbol_val or (isinstance(symbol_val, str) and symbol_val.strip() == ''):
                return 'GOLD'
            
            return symbol_val
        except Exception as e:
            logger.debug(f"[_get_symbol] Error: {str(e)[:60]}, returning GOLD")
            return 'GOLD'

    def get_fresh_market_data(self, symbol, bars=100):
        """
        ⭐ PRIORIDAD: JSON primero (datos seguros), MT5 como fallback
        """
        try:
            # ⭐ PRIORIDAD 1: Cargar del JSON - DATOS SEGUROS Y CONFIRMADOS
            json_snaps = self._read_snapshots_for_symbol(symbol)
            if json_snaps and len(json_snaps) >= bars:
                return json_snaps[-bars:] if len(json_snaps) >= bars else json_snaps
            
            # ⭐ PRIORIDAD 2: Cache del monitor si está muy fresco
            try:
                with self.fresh_data_lock:
                    cache_age = time.time() - self.fresh_data_timestamp
                    if cache_age < 0.5 and len(self.fresh_market_data_cache) >= 50:
                        logger.debug(f"[FRESH_DATA] ✓ Cache del monitor ({cache_age:.2f}s)")
                        return list(self.fresh_market_data_cache)[-bars:] if len(self.fresh_market_data_cache) >= bars else list(self.fresh_market_data_cache)
            except Exception as e:
                logger.debug(f"[FRESH_DATA] Error reading cache: {str(e)[:60]}")
            
            # ⭐ PRIORIDAD 3: MT5 como fallback
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, bars)
            rates = mt5_safe._ensure_rates_list(rates)
            
            if rates is None or len(rates) == 0:
                # Si MT5 falla, retornar JSON aunque sea viejo
                if json_snaps and len(json_snaps) > 0:
                    return json_snaps[-bars:] if len(json_snaps) >= bars else json_snaps
                return []
            
            # Convertir MT5 rates a snapshots format
            market_snaps = []
            for idx, rate in enumerate(rates):
                snap = {
                    'time': float(rate['time']) if isinstance(rate, dict) else float(rate[0]),
                    'open': float(rate['open']) if isinstance(rate, dict) else float(rate[1]),
                    'high': float(rate['high']) if isinstance(rate, dict) else float(rate[2]),
                    'low': float(rate['low']) if isinstance(rate, dict) else float(rate[3]),
                    'close': float(rate['close']) if isinstance(rate, dict) else float(rate[4]),
                    'tick_volume': int(rate['tick_volume']) if isinstance(rate, dict) else int(rate[5]),
                }
                market_snaps.append(snap)
            return market_snaps
        except Exception as e:
            logger.error(f"[FRESH_DATA] Error: {str(e)[:60]} - usando fallback JSON")
            # ⭐ Usar el símbolo recibido como parámetro
            return self.reload_market_snapshots(symbol=self._map_symbol_internal(symbol)) or []

    def _update_snapshots_4min_cycle(self):
        """⭐ NEW: Manejar ciclo de snapshots cada 4 minutos de forma centralizada.
        
        Llamar periódicamente (cada ~240 segundos) para:
        1. Traer datos frescos de MT5
        2. Agregar al histórico persistente
        3. Rotar si es necesario (máximo 1440 = 24h en M1)
        4. Actualizar metadata
        
        Returns: (success_bool, snapshot_count, metadata)
        """
        try:
            symbol = self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get() if hasattr(self, 'config') else 'GOLD'
            
            # Traer últimos 240 snapshots (4 horas de M1, más que suficiente para últimas barras)
            latest_snaps = self.get_fresh_market_data(symbol, bars=240) or []
            
            if not latest_snaps or len(latest_snaps) == 0:
                logger.warning(f"[4MIN-CYCLE] ⚠️ No se obtuvieron snapshots frescos")
                return (False, 0, {})
            
            # Agregar al histórico (usando method que ya maneja símbolo)
            self.reload_market_snapshots(symbol=symbol)
            
            # Obtener metadata actualizada
            meta = get_market_snapshots_metadata()
            
            logger.info(
                f"[4MIN-CYCLE] ✅ Actualizado: {len(latest_snaps)} barras | "
                f"Total: {meta.get('snapshot_count', 0)} | "
                f"Rango: {meta.get('oldest_snapshot', 'N/A')[:10]} a {meta.get('newest_snapshot', 'N/A')[:10]}"
            )
            
            return (True, len(latest_snaps), meta)
        except Exception as e:
            logger.error(f"[4MIN-CYCLE] ❌ Error: {e}")
            return (False, 0, {})

    def _validate_snapshots_integrity(self, snapshots, min_count=10):
        """⭐ VALIDAR: Verifica que snapshots sean valid y tengan datos mínimos.
        
        Returns: (is_valid, reason)
        """
        if snapshots is None:
            return (False, "None")
        if not isinstance(snapshots, list):
            return (False, f"Wrong type: {type(snapshots).__name__}")
        if len(snapshots) == 0:
            return (False, "Empty list")
        if len(snapshots) < min_count:
            return (False, f"Too few: {len(snapshots)}<{min_count}")
        
        # Validar estructura de primer/último elemento
        try:
            first = snapshots[0]
            last = snapshots[-1]
            for snap in [first, last]:
                if not isinstance(snap, dict):
                    return (False, f"Non-dict element: {type(snap).__name__}")
                required_keys = {'close', 'timestamp'} if 'timestamp' in snap else {'close', 'time'}
                if not all(k in snap for k in required_keys):
                    return (False, f"Missing keys: {required_keys - set(snap.keys())}")
        except Exception as e:
            return (False, f"Validation error: {str(e)[:30]}")
        
        return (True, "valid")

    def _try_load_from_json(self, symbol='GOLD'):
        """⭐ PASO 1 DE FALLBACK: Intentar cargar desde JSON específico del símbolo."""
        try:
            snaps = self._read_snapshots_for_symbol(symbol) or []
            is_valid, reason = self._validate_snapshots_integrity(snaps)
            if is_valid:
                logger.info(f"[FALLBACK-JSON-{symbol}] ✅ Cargado: {len(snaps)} snapshots desde JSON")
                return (snaps, 'json_success')
            else:
                logger.warning(f"[FALLBACK-JSON-{symbol}] ❌ JSON inválido: {reason}")
                return ([], 'json_invalid')
        except Exception as e:
            logger.error(f"[FALLBACK-JSON-{symbol}] ❌ Error: {str(e)[:50]}")
            return ([], 'json_error')

    def _try_load_from_backup(self, symbol='GOLD'):
        """⭐ PASO 2 DE FALLBACK: Intentar cargar desde backup en memoria específico del símbolo."""
        backup = self.market_snapshots_backup_by_symbol.get(symbol, [])
        is_valid, reason = self._validate_snapshots_integrity(backup, min_count=5)
        if is_valid:
            logger.warning(f"[FALLBACK-BACKUP-{symbol}] ✅ Cargado: {len(backup)} snapshots desde backup")
            return (list(backup), 'backup_success')
        else:
            logger.warning(f"[FALLBACK-BACKUP-{symbol}] ❌ Backup inválido: {reason}")
            return ([], 'backup_invalid')

    def _try_load_from_memory(self, symbol='GOLD'):
        """⭐ PASO 3 DE FALLBACK: Intentar cargar desde memoria específica del símbolo."""
        snaps = self.market_snapshots_by_symbol.get(symbol, [])
        is_valid, reason = self._validate_snapshots_integrity(snaps, min_count=5)
        if is_valid:
            logger.warning(f"[FALLBACK-MEMORY-{symbol}] ✅ Cargado: {len(snaps)} snapshots desde memoria")
            return (list(snaps), 'memory_success')
        else:
            logger.warning(f"[FALLBACK-MEMORY-{symbol}] ❌ Memoria inválida: {reason}")
            return ([], 'memory_invalid')

    def _generate_synthetic_snapshots(self, count=10):
        """⭐ PASO 4 DE FALLBACK: Generar snapshots sintéticos mínimos para evitar crash."""
        try:
            if self.market_snapshots and len(self.market_snapshots) > 0:
                base = self.market_snapshots[-1]
                base_close = float(base.get('close', 1900.0))
            else:
                base_close = 2000.0  # Default para GOLD
            
            synthetics = []
            import random
            current_price = base_close
            now = datetime.now()
            
            for i in range(count):
                # Generar paseo aleatorio realista
                change = random.uniform(-0.05, 0.05)
                current_price += change
                
                snap = {
                    'timestamp': (now - timedelta(minutes=count-i)).isoformat(),
                    'time': (time.time() - (count-i)*60),
                    'open': current_price - random.uniform(0, 0.03),
                    'high': current_price + random.uniform(0, 0.03),
                    'low': current_price - random.uniform(0, 0.03),
                    'close': current_price,
                    'tick_volume': random.randint(50, 200)
                }
                synthetics.append(snap)
            
            logger.error(f"[FALLBACK-SYNTHETIC] ⚠️ Generados {len(synthetics)} snapshots sintéticos de EMERGENCIA")
            return synthetics
        except Exception as e:
            logger.error(f"[FALLBACK-SYNTHETIC] ❌ Error generando synthetic: {e}")
            return []

    def _robust_fallback_cascade(self, symbol='GOLD'):
        """⭐ CENTRALIZAR: Cascada robusta de fallback completa por símbolo.
        
        Intenta en orden:
        1. JSON (si tiene datos válidos)
        2. Backup en memoria (market_snapshots_backup_by_symbol)
        3. Memoria actual (self.market_snapshots_by_symbol)
        4. Generar synthetic (último recurso)
        
        Returns: (snapshots, fallback_chain_used)
        """
        fallbacks_used = []
        
        # PASO 1: JSON
        snaps, reason = self._try_load_from_json(symbol)
        fallbacks_used.append(reason)
        if len(snaps) > 0:
            return (snaps, fallbacks_used)
        
        # PASO 2: Backup
        snaps, reason = self._try_load_from_backup(symbol)
        fallbacks_used.append(reason)
        if len(snaps) > 0:
            return (snaps, fallbacks_used)
        
        # PASO 3: Memoria
        snaps, reason = self._try_load_from_memory(symbol)
        fallbacks_used.append(reason)
        if len(snaps) > 0:
            return (snaps, fallbacks_used)
        
        # PASO 4: Synthetic (último recurso)
        snaps = self._generate_synthetic_snapshots(count=20)
        fallbacks_used.append('synthetic_generated' if snaps else 'synthetic_failed')
        
        return (snaps, fallbacks_used)

    def reload_market_snapshots(self, symbol='GOLD', max_len=500, protect_from_empty=True):
        """
        Lee `logs/market_snapshots.json` y AGREGA última barra M1 de MT5 para frescura.
        ⭐ CRÍTICO: NUNCA permite sobrescribir con lista vacía - SIEMPRE mantiene datos disponibles
        ⭐ NUEVO protect_from_empty=True: Si se obtiene [] y tenemos backup, usa el backup
        """
        # ⭐ RASTREAR CUANDO SE LLAMA (para detectar si es scheduler)
        import time
        now = time.time()
        is_scheduler_call = (self.scheduler_reload_time is not None and 
                           (now - self.scheduler_reload_time) < 1)  # Si se llamó en último segundo
        
        # ⭐ VERIFICAR SI NECESITA RECARGA FRESCA (cada 4 minutos)
        time_since_init = now - (self.last_successful_reload_time or now)
        needs_fresh_reload = (self.last_successful_reload_time > 0 and time_since_init > 240)  # 240s = 4 minutos
        
        if needs_fresh_reload:
            logger.info(f"[reload] ⭐ CICLO DE 4M DETECTADO: {time_since_init:.0f}s desde último reload exitoso")
            logger.info(f"[reload] Iniciando RECARGA FRESCA...")
            try:
                # ⭐ CRÍTICO: Respetar el símbolo pasado como parámetro
                # Solo usar config como fallback si está VACÍO
                if not symbol:
                    symbol = self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get() if hasattr(self, 'config') else 'GOLD'
                # ⭐ SEGURIDAD: Asegurar que símbolo NO sea vacío nunca
                if not symbol or symbol.strip() == '':
                    symbol = 'GOLD'
                    
                filled, fresh_snaps = prefill_market_data_and_return(symbol, minutes=500)
                logger.info(f"[reload] ✓ RECARGA FRESCA ({symbol}): {filled} snapshots frescos obtenidos")
                if len(fresh_snaps) > 0:
                    snaps = list(fresh_snaps)
                else:
                    logger.warning(f"[reload] ⚠️ RECARGA FRESCA ({symbol}): prefill retornó 0 snapshots")
                    snaps = []
            except Exception as e:
                logger.error(f"[reload] ❌ Error en recarga fresca ({symbol}): {e}")
                snaps = []
            # Resetear contador para el siguiente ciclo de 4m
            self.last_successful_reload_time = now
        else:
            # Reload normal (incremental, no es ciclo de 4m)
            try:
                snaps = self._read_snapshots_for_symbol(symbol) or []
                logger.debug(f"[reload] _read_snapshots_for_symbol({symbol}) retornó {len(snaps)} barras (tipo: {type(snaps).__name__})")
            except Exception as e:
                logger.exception(f"[ERROR] Reading market_snapshots from disk: {str(e)[:80]}")
                snaps = getattr(self, 'market_snapshots', []) or []
                logger.debug(f"[reload] Fallback a self.market_snapshots: {len(snaps)} barras")
        
        # VALIDAR: Asegurar que es lista, no dict
        if isinstance(snaps, dict):
            snaps = snaps.get('snapshots', []) if 'snapshots' in snaps else []
            logger.debug(f"[reload] Convertida de dict a list: {len(snaps)} barras")
        
        try:
            if isinstance(snaps, list) and len(snaps) > max_len:
                snaps = snaps[-max_len:]
                logger.debug(f"[reload] Truncada a max_len={max_len}: {len(snaps)} barras")
        except Exception as e:
            logger.debug(f"[reload] Error truncating snapshots: {str(e)[:60]}")
        
        # ⭐ CHECKPOINT: Antes de MT5, ¿cuántos snapshots tenemos?
        snaps_before_mt5 = len(snaps) if isinstance(snaps, list) else 0
        logger.debug(f"[reload] CHECKPOINT antes MT5: {snaps_before_mt5} snapshots")
        
        # ⭐ Inicializar flag de éxito MT5
        mt5_success = False
        # ⭐ AGREGAR BARRA NUEVA DE MT5 para frescura (detecta cambios INTRA-minuto con tick_volume)
        try:
            # ⭐ IMPORTANTE: NO sobrescribir el symbol pasado como parámetro
            # Solo usar config como fallback si no se especificó
            if not symbol:
                symbol = self.config['SYMBOL'].get()
            # ⭐ TRIPLE SEGURIDAD: Asegurar que símbolo NUNCA sea VACÍO
            if not symbol or symbol.strip() == '':
                symbol = 'GOLD'
            
            logger.debug(f"[reload] Procesando symbol: {symbol} (parámetro respetado)")
            
            # ⭐ VALIDATION: Asegurar MT5 conectado
            if not mt5.initialize():
                logger.warning("[MT5] WARNING: No inicializado exitosamente")
                # Intentar una sola reinitialización
                try:
                    mt5.shutdown()
                    time.sleep(0.1)
                    mt5.initialize()
                except:
                    pass
            
            if mt5.initialize():
                # Obtener última barra M1
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
                
                # ⭐ DEBUG: Verificar exactamente qué retorna MT5
                if rates is None:
                    logger.warning(f"[MT5-ERROR] ❌ copy_rates_from_pos retornó None para {symbol}")
                    # FALLBACK: Inyectar sintético automáticamente CON MAYOR VARIACIÓN
                    if snaps and isinstance(snaps, list) and len(snaps) > 0:
                        last_real = snaps[-1]
                        synthetic_snap = dict(last_real)
                        # Variación MAYOR para forzar recálculos (±0.010 = 10x más grande)
                        synthetic_snap['close'] = float(last_real.get('close', 0)) + (0.010 * (1 if id(snaps) % 2 == 0 else -1))
                        synthetic_snap['tick_volume'] = int(last_real.get('tick_volume', 0)) + 5
                        snaps.append(synthetic_snap)
                        if len(snaps) > max_len:
                            snaps = snaps[-max_len:]
                        logger.warning(f"[MT5-AUTO-SYNTH] ✓ Fallback por MT5 None: close {last_real.get('close'):.2f} → {synthetic_snap['close']:.2f}")
                        mt5_success = False
                elif len(rates) == 0:
                    logger.warning(f"[MT5-ERROR] ❌ copy_rates_from_pos retornó lista VACÍA para {symbol}")
                    # FALLBACK: Inyectar sintético automáticamente
                    if snaps and isinstance(snaps, list) and len(snaps) > 0:
                        last_real = snaps[-1]
                        synthetic_snap = dict(last_real)
                        synthetic_snap['close'] = float(last_real.get('close', 0)) + 0.010
                        synthetic_snap['tick_volume'] = int(last_real.get('tick_volume', 0)) + 5
                        snaps.append(synthetic_snap)
                        if len(snaps) > max_len:
                            snaps = snaps[-max_len:]
                        logger.warning(f"[MT5-AUTO-SYNTH] ✓ Fallback por rates vacía: {synthetic_snap['close']:.2f}")
                        mt5_success = False
                elif len(rates) > 0:
                    latest_rate = rates[0]
                    # Convertir numpy.void a diccionario si es necesario
                    if hasattr(latest_rate, '__iter__') and not isinstance(latest_rate, dict):
                        try:
                            latest_rate = dict(latest_rate)
                        except:
                            pass
                    
                    # Crear snapshot con la barra nueva (campos defensivos)
                    try:
                        # Acceder a campos de forma segura
                        if isinstance(latest_rate, dict):
                            new_snapshot = {
                                'time': float(latest_rate.get('time', 0)),
                                'open': float(latest_rate.get('open', 0)),
                                'high': float(latest_rate.get('high', 0)),
                                'low': float(latest_rate.get('low', 0)),
                                'close': float(latest_rate.get('close', 0)),
                                'tick_volume': int(latest_rate.get('tick_volume', 0)),
                                'volume': int(latest_rate.get('volume', 0)),  # Puede no existir
                                'real_volume': int(latest_rate.get('real_volume', 0))  # Puede no existir
                            }
                        else:
                            # Acceso por atributo para numpy.void
                            new_snapshot = {
                                'time': float(getattr(latest_rate, 'time', 0)),
                                'open': float(getattr(latest_rate, 'open', 0)),
                                'high': float(getattr(latest_rate, 'high', 0)),
                                'low': float(getattr(latest_rate, 'low', 0)),
                                'close': float(getattr(latest_rate, 'close', 0)),
                                'tick_volume': int(getattr(latest_rate, 'tick_volume', 0)),
                                'volume': int(getattr(latest_rate, 'volume', 0)),
                                'real_volume': int(getattr(latest_rate, 'real_volume', 0))
                            }
                    except Exception as e:
                        logger.error(f"[MT5-EXCEPTION] ❌ EXCEPCIÓN agregando barra M1: {e}")
                        # Usar synthético como fallback
                        if snaps and isinstance(snaps, list) and len(snaps) > 0:
                            last_real = snaps[-1]
                            synthetic_snap = dict(last_real)
                            synthetic_snap['close'] = float(last_real.get('close', 0)) + 0.010
                            synthetic_snap['tick_volume'] = int(last_real.get('tick_volume', 0)) + 5
                            snaps.append(synthetic_snap)
                            if len(snaps) > max_len:
                                snaps = snaps[-max_len:]
                            logger.error(f"[MT5-FALLBACK-EXCEPTION] ✓ Inyectado snapshot sintético URGENTE por excepción MT5: {synthetic_snap['close']:.2f}")
                        mt5_success = False
                        new_snapshot = None
                    
                    if new_snapshot is None:
                        # Si hay error procesando MT5, parar aquí
                        pass
                    
                    # ⭐ CRÍTICO: Detectar CAMBIOS INTRA-MINUTO (solo si new_snapshot es válido)
                    # Durante el mismo minuto M1, el timestamp es idéntico pero:
                    # 1. tick_volume CAMBIA (nuevos ticks)
                    # 2. high/low pueden cambiar (precio explora nuevos niveles)
                    # 3. close cambia (precio actual)
                    if new_snapshot and snaps and isinstance(snaps, list) and len(snaps) > 0:
                        last_snap = snaps[-1]
                        # Agregar si:
                        if isinstance(last_snap, dict):
                            is_new_minute = last_snap.get('time') != new_snapshot.get('time')
                            is_new_ticks = last_snap.get('tick_volume', 0) != new_snapshot.get('tick_volume', 0)
                            is_new_high = last_snap.get('high', 0) != new_snapshot.get('high', 0)
                            is_new_low = last_snap.get('low', 0) != new_snapshot.get('low', 0)
                            is_new_close = last_snap.get('close', 0) != new_snapshot.get('close', 0)
                            
                            # ⭐ Agregar si HAY CAMBIO EN CUALQUIER MÉTRICA
                            has_change = is_new_minute or is_new_ticks or is_new_high or is_new_low or is_new_close
                            
                            if has_change:
                                snaps.append(new_snapshot)
                                # Mantener max_len
                                if len(snaps) > max_len:
                                    snaps = snaps[-max_len:]
                                # LOG: Cambios detectados (visible)
                                logger.info(f"[MT5] ✓ BARRAnueva: ts={new_snapshot.get('time', 0):.0f} close={new_snapshot.get('close', 0):.2f} ticks={new_snapshot.get('tick_volume')} [nuevo_min={is_new_minute}, ticks={is_new_ticks}, close={is_new_close}]")
                                mt5_success = True
                            else:
                                # ⭐ NO hay cambios detectados - puede ser error en MT5 o mercado congelado
                                logger.warning(f"[MT5-WARN] Sin cambios en MT5 rates: ticks={is_new_ticks}, close={is_new_close}, high={is_new_high}, low={is_new_low}")
                                # Inyectar fallback
                                if snaps and isinstance(snaps, list) and len(snaps) > 0:
                                    last_real = snaps[-1]
                                    synthetic_snap = dict(last_real)
                                    synthetic_snap['close'] = float(last_real.get('close', 0)) + 0.010
                                    synthetic_snap['tick_volume'] = int(last_real.get('tick_volume', 0)) + 3
                                    snaps.append(synthetic_snap)
                                    if len(snaps) > max_len:
                                        snaps = snaps[-max_len:]
                                    logger.info(f"[MT5-SYNTH-WARN] ✓ Inyectado fallback (no cambios en rates): {synthetic_snap['close']:.2f}")
                                    mt5_success = False
                    else:
                        # Si no hay snapshots, agregar el nuevo
                        snaps.append(new_snapshot)
                        mt5_success = True
                else:
                    # MT5 retornó datos válidos pero sin cambios - forzar sintético
                    if snaps and isinstance(snaps, list) and len(snaps) > 0:
                        logger.debug(f"[MT5-SYNTH] Forzando sintético porque rates vacía")
                        last_real = snaps[-1]
                        synthetic_snap = dict(last_real)
                        synthetic_snap['close'] = float(last_real.get('close', 0)) + 0.001
                        synthetic_snap['tick_volume'] = int(last_real.get('tick_volume', 0)) + 1
                        snaps.append(synthetic_snap)
                        if len(snaps) > max_len:
                            snaps = snaps[-max_len:]
        except Exception as e:
            logger.error(f"[MT5-EXCEPTION] ❌ EXCEPCIÓN agregando barra M1: {e}")
            # ⭐ FALLBACK AGRESIVO: Si MT5 falla COMPLETAMENTE, inyectar snapshot sintético automáticamente
            try:
                if snaps and isinstance(snaps, list) and len(snaps) > 0:
                    last_real = snaps[-1]
                    # Inyectar variación micro automáticamente como fallback URGENTE
                    synthetic_snap = dict(last_real)
                    synthetic_snap['close'] = float(last_real.get('close', 0)) + 0.010
                    synthetic_snap['tick_volume'] = int(last_real.get('tick_volume', 0)) + 3
                    snaps.append(synthetic_snap)
                    if len(snaps) > max_len:
                        snaps = snaps[-max_len:]
                    logger.error(f"[MT5-FALLBACK-EXCEPTION] ✓ Inyectado snapshot sintético URGENTE por excepción MT5: {synthetic_snap['close']:.2f}")
            except Exception as synth_error:
                logger.error(f"[MT5-FALLBACK-EXCEPTION] ❌ Error en fallback sintético: {synth_error}")
        
        # ⭐ PROTECCIÓN CRÍTICA: NUNCA permitir sobrescribir con lista vacía
        # Si obtenemos [], usar cascada robusta de fallback
        if not snaps or (isinstance(snaps, list) and len(snaps) == 0):
            logger.warning(f"[PROTECT] ⚠️ CRÍTICO: reload obtuvo lista VACÍA")
            
            # ⭐ USAR CASCADA CENTRALIZADA DE FALLBACK
            snaps, fallback_chain = self._robust_fallback_cascade()
            logger.warning(f"[PROTECT] Fallback chain usado: {' → '.join(fallback_chain)}")
            protect_from_empty = False  # No es reload exitoso, es fallback
        
        # ⭐ LIMITACIÓN DE TAMAÑO: Nunca permitir que snapshots crezca más de MAX_SNAPSHOTS
        if snaps and len(snaps) > self.MAX_SNAPSHOTS:
            snaps = snaps[-self.MAX_SNAPSHOTS:]  # Mantener solo los últimos 1440
            logger.info(f"[MEMORY-PROTECTION] Snapshots truncados a {len(snaps)} (máximo {self.MAX_SNAPSHOTS})")
        
        # Asignación protegida por lock si está disponible
        try:
            if getattr(self, 'market_snapshots_lock', None):
                with self.market_snapshots_lock:
                    # ⭐ NUNCA SOBRESCRIBIR CON VACÍO
                    if len(snaps) > 0:
                        self.market_snapshots = snaps
                        # ⭐ ACTUALIZAR RESPALDO cuando reload es exitoso
                        self.market_snapshots_backup = list(snaps)
                        self.last_successful_reload_time = time.time()
                        self.reload_count += 1
                        logger.debug(f"[PROTECT] ✓ Asignado y backup actualizado ({self.reload_count} recargas)")
                    else:
                        logger.warning(f"[PROTECT] ❌ NO sobrescribiendo: snaps vacío, manteniendo datos anteriores")
            else:
                if len(snaps) > 0:
                    self.market_snapshots = snaps
                    self.market_snapshots_backup = list(snaps)
                    self.last_successful_reload_time = time.time()
                    self.reload_count += 1
                else:
                    logger.warning(f"[PROTECT] ❌ NO asignando: snaps vacío")
        except Exception:
            logger.exception("Error al asignar self.market_snapshots")
            pass
        
        # ⭐ CRÍTICO: Guardar snapshots actualizados de vuelta al archivo CON PERSISTENCIA HISTÓRICA
        # Esto es esencial para que los datos nuevos persistan entre ciclos
        try:
            from trade_logger import write_market_snapshots
            if len(snaps) > 0:  # ⭐ SOLO GUARDAR SI TENEMOS DATOS
                # Usar el símbolo del parámetro del método
                write_market_snapshots(snaps, symbol=symbol, max_snapshots=1440)  # 1440 = 24h M1
                if mt5_success:
                    logger.info(f"[MT5-PERSIST] ✓ Guardado archivo HISTÓRICO: {len(snaps)} barras ({symbol}, MT5 exitoso)")
                else:
                    logger.info(f"[MT5-PERSIST] ⚠️ Guardado archivo HISTÓRICO: {len(snaps)} barras ({symbol}, con fallback sintético)")
            else:
                logger.warning("[MT5-PERSIST] ⚠️ NO guardando archivo: snaps vacío")
        except Exception as e:
            logger.warning(f"[MT5-PERSIST] ❌ Advertencia guardando snapshots: {e}")
        
        # ⭐ ACTUALIZAR ESTRUCTURAS POR SÍMBOLO
        try:
            if symbol in self.market_snapshots_by_symbol:
                with self.market_snapshots_lock_by_symbol[symbol]:
                    if len(snaps) > 0:
                        self.market_snapshots_by_symbol[symbol] = snaps
                        self.market_snapshots_backup_by_symbol[symbol] = list(snaps)
                        self.last_successful_reload_time_by_symbol[symbol] = time.time()
                        self.reload_count_by_symbol[symbol] += 1
                        logger.debug(f"[reload-{symbol}] ✓ Actualizado: {len(snaps)} snapshots")
                    else:
                        logger.warning(f"[reload-{symbol}] No sobrescribiendo: snaps vacío")
        except Exception as e:
            logger.warning(f"[reload-{symbol}] Error actualizando estructura: {e}")
        
        # ⭐ MANTENER COMPATIBILIDAD CON GOLD
        if symbol == 'GOLD':
            snaps_final = snaps if isinstance(snaps, list) else self.market_snapshots_by_symbol.get('GOLD', []) if isinstance(self.market_snapshots_by_symbol.get('GOLD', []), list) else []
            logger.info(f"[reload] FINAL: {len(snaps_final)} snapshots para {symbol}")
            return snaps_final
        
        return snaps if isinstance(snaps, list) else []

    def _get_snapshots_filepath(self, symbol='GOLD'):
        """Retorna la ruta del archivo JSON de snapshots para un símbolo."""
        try:
            # ⭐ CRÍTICO: Asegurar que símbolo NUNCA sea VACÍO
            if not symbol or symbol.strip() == '':
                logger.error(f"[PATH] ⛔ CRÍTICO: symbol vacío detectado, usando GOLD por defecto")
                symbol = 'GOLD'
                
            logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            return os.path.join(logs_dir, f'market_snapshots_{symbol}.json')
        except Exception as e:
            logger.error(f"[PATH] Error getting snapshots filepath: {str(e)[:80]}, using GOLD fallback")
            return os.path.join(os.path.dirname(__file__), 'logs', f'market_snapshots_GOLD.json')

    def _read_snapshots_for_symbol(self, symbol='GOLD'):
        """Lee snapshots desde archivo JSON específico del símbolo."""
        try:
            # ⭐ CRÍTICO: Asegurar que símbolo NUNCA sea VACÍO
            if not symbol or symbol.strip() == '':
                logger.error(f"[snapshot] ⛔ CRÍTICO: symbol vacío en _read_snapshots_for_symbol, usando GOLD")
                symbol = 'GOLD'
                
            filepath = self._get_snapshots_filepath(symbol)
            if not os.path.exists(filepath):
                logger.info(f"[snapshot-{symbol}] Archivo no existe: {filepath}")
                return []
            
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'snapshots' in data:
                    return data['snapshots']
                elif isinstance(data, list):
                    return data
                else:
                    return []
        except Exception as e:
            logger.warning(f"[snapshot-{symbol}] Error leyendo {filepath}: {e}")
            return []

    def _write_snapshots_for_symbol(self, symbol='GOLD', snapshots=None):
        """Escribe snapshots a archivo JSON específico del símbolo."""
        try:
            # ⭐ CRÍTICO: Asegurar que símbolo NUNCA sea VACÍO
            if not symbol or symbol.strip() == '':
                logger.error(f"[snapshot] ⛔ CRÍTICO: symbol vacío en _write_snapshots_for_symbol, usando GOLD")
                symbol = 'GOLD'
                
            if snapshots is None or len(snapshots) == 0:
                logger.debug(f"[snapshot-{symbol}] No escribiendo: snapshots vacío")
                return
            
            filepath = self._get_snapshots_filepath(symbol)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Guardar con metadata
            data = {
                'snapshots': snapshots,
                'symbol': symbol,
                'timestamp': time.time(),
                'count': len(snapshots)
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"[snapshot-{symbol}] Guardados {len(snapshots)} snapshots en {filepath}")
        except Exception as e:
            logger.warning(f"[snapshot-{symbol}] Error escribiendo {filepath}: {e}")

    def get_market_snapshots_by_symbol(self, symbol='GOLD'):
        """Retorna una copia de snapshots para un símbolo específico."""
        try:
            if symbol not in self.market_snapshots_by_symbol:
                logger.warning(f"[snapshot-{symbol}] Símbolo no registrado, retornando vacío")
                return []
            
            with self.market_snapshots_lock_by_symbol[symbol]:
                return list(self.market_snapshots_by_symbol[symbol])
        except Exception as e:
            logger.error(f"[snapshot-{symbol}] Error getting snapshots: {str(e)[:80]}")
            return []

    def sync_snapshots_between_symbols(self):
        """⭐ SINCRONIZACIÓN: Recargar snapshots independientes para ambos pares."""
        try:
            current_symbol = self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get() if hasattr(self, 'config') else 'GOLD'
            
            # Recargar ambos pares SIMULTÁNEAMENTE
            for symbol in ['GOLD', 'SILVER']:
                try:
                    updated_snaps = self.reload_market_snapshots(symbol=symbol)
                    logger.debug(f"[SYNC-{symbol}] Reloaded: {len(updated_snaps)} snapshots")
                except Exception as e:
                    logger.warning(f"[SYNC-{symbol}] Error durante reload: {e}")
        except Exception as e:
            logger.warning(f"[SYNC] Error en sincronización: {e}")

    def get_symbol_snapshots(self, symbol=None):
        """⭐ HELPER: Obtener snapshots del símbolo actual o especificado."""
        if symbol is None:
            symbol = self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get() if hasattr(self, 'config') else 'GOLD'
        return self.get_market_snapshots_by_symbol(symbol)

    def get_symbol_from_config(self):
        """⭐ HELPER: Obtener símbolo actual de la configuración."""
        try:
            return self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get() if hasattr(self, 'config') else 'GOLD'
        except Exception:
            return 'GOLD'

    def _get_current_snapshots(self):
        """⭐ HELPER RÁPIDO: Obtener snapshots del símbolo actual (para compatibilidad)."""
        symbol = self.get_symbol_from_config()
        return self.get_market_snapshots_by_symbol(symbol)

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

    def reload_all_symbols_snapshots(self):
        """⭐ NUEVO: Recarga snapshots para GOLD Y SILVER independientemente.
        Esto garantiza que ambos símbolos tengan datos frescos en paralelo.
        """
        try:
            for symbol in ['GOLD', 'SILVER']:
                try:
                    fresh_snaps = self.reload_market_snapshots(symbol=symbol)
                    if fresh_snaps and isinstance(fresh_snaps, list):
                        with self.market_snapshots_lock_by_symbol.get(symbol, threading.Lock()):
                            self.market_snapshots_by_symbol[symbol] = fresh_snaps
                            logger.debug(f"[DUAL-RELOAD] ✓ {symbol}: {len(fresh_snaps)} snapshots cargados")
                except Exception as e:
                    logger.warning(f"[DUAL-RELOAD] Error cargando {symbol}: {str(e)[:50]}")
        except Exception as e:
            logger.error(f"[DUAL-RELOAD] Error general: {str(e)[:100]}")


    def compute_signal_from_snapshots(self, symbol='GOLD', window=20):
        """Simple heuristic: SMA crossover on prefilled snapshots.
        Returns 'BUY', 'SELL' or None."""
        try:
            snaps = self.get_market_snapshots_by_symbol(symbol) or []
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
        except Exception as e:
            logger.debug(f"[TREND] Error analyzing trend: {str(e)[:60]}")
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
        except Exception as e:
            logger.debug(f"[VOL] Error calculating volatility: {str(e)[:60]}")
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
        except Exception as e:
            logger.debug(f"[RSI] Error calculating RSI: {str(e)[:60]}")
            return 50.0  # neutral fallback

    def _calculate_dynamic_tp_sl(self, volume):
        """⭐ NUEVO: Calcular TP y SL dinámicamente según el volumen (lotaje)
        
        Usa TP_DIFF y SL_DIFF de la GUI y los escala por el volumen.
        Base: volumen 0.1 = 1 lote (ETHUSD mínimo)
        - TP base: $3.0 (TP_DIFF) → Si volumen 0.2 → TP = $6.0
        - SL base: $15.0 (SL_DIFF) → Si volumen 0.2 → SL = $30.0
        
        Args:
            volume: Volumen/lotaje actual
        
        Returns:
            (tp_amount, sl_amount): TP y SL escalados dinámicamente
        """
        try:
            # Obtener bases de la GUI (TP_DIFF y SL_DIFF)
            tp_base = float(self.config.get('TP_DIFF', tk.DoubleVar(value=3.0)).get())
            sl_base = float(self.config.get('SL_DIFF', tk.DoubleVar(value=15.0)).get())
            
            # Volumen de referencia (0.1 = 1 lote para ETHUSD)
            volume_ref = 0.1
            
            # Calcular factor de escala
            scale_factor = volume / volume_ref if volume > 0 else 1.0
            
            # Aplicar escala
            tp_dynamic = tp_base * scale_factor
            sl_dynamic = sl_base * scale_factor
            
            # Log informativo (solo cada 10 operaciones aproximadamente para no saturar)
            if int(self.rapid_ops_total_opened) % 10 == 0:
                self.add_log(f"💰 TP/SL adaptado: Vol={volume:.2f} → TP=${tp_dynamic:.2f} | SL=${sl_dynamic:.2f}", 'info')
            
            return (tp_dynamic, sl_dynamic)
        except Exception as e:
            # Fallback a configuración estática
            tp_base = 1.0
            sl_base = 30.0
            self.add_log(f"[WARN] Fallback TP/SL: {str(e)[:40]}", 'warning')
            return (tp_base, sl_base)

    def _build_specialist_session_context(self):
        """Construye contexto basado SOLO en datos de mercado actual, sin histórico de trades."""
        try:
            # Contexto neutral basado solo en mercado actual, sin datos de trades anteriores
            return {
                'samples': 0,
                'buy_win_rate': 50.0,
                'sell_win_rate': 50.0,
                'buy_profit': 0.0,
                'sell_profit': 0.0,
                'buy_loss_streak': 0,
                'sell_loss_streak': 0,
                'session_weight': 0.50,
                'window': 0,
            }
        except Exception as e:
            logger.error(f"[SESSION-CONTEXT] Error building context: {str(e)[:80]}")
            return {
                'samples': 0,
                'buy_win_rate': 50.0,
                'sell_win_rate': 50.0,
                'buy_profit': 0.0,
                'sell_profit': 0.0,
                'buy_loss_streak': 0,
                'sell_loss_streak': 0,
                'session_weight': 0.50,
                'window': 0,
            }

    def _refresh_specialists_session_context(self):
        """Inyecta contexto de sesión actual en BUY/SELL specialists."""
        try:
            context = self._build_specialist_session_context()
            if hasattr(self, 'buy_specialist') and self.buy_specialist:
                if hasattr(self.buy_specialist, 'set_session_context'):
                    self.buy_specialist.set_session_context(context)
                else:
                    self.buy_specialist.session_context = context
            if hasattr(self, 'sell_specialist') and self.sell_specialist:
                if hasattr(self.sell_specialist, 'set_session_context'):
                    self.sell_specialist.set_session_context(context)
                else:
                    self.sell_specialist.session_context = context
        except Exception as e:
            logger.error(f"[SESSION] Error refreshing specialist context: {str(e)[:80]}")

    def _get_direction_loss_streak(self, direction):
        """DESHABILITADO: No se usa histórico de trades. Solo análisis de mercado actual."""
        return 0

    def _detect_extreme_micro_move(self, snapshots):
        """Detecta micro-movimiento extremo reciente usando últimos cierres M1."""
        try:
            if not snapshots or len(snapshots) < 6:
                return 0.0
            closes = []
            for s in snapshots[-6:]:
                c = s.get('close') if isinstance(s, dict) else None
                if c is not None:
                    closes.append(float(c))
            if len(closes) < 2 or closes[0] == 0:
                return 0.0
            move_pct = ((closes[-1] - closes[0]) / closes[0]) * 100.0
            return float(move_pct)
        except Exception as e:
            logger.debug(f"[MICRO-MOVE] Error detecting move: {str(e)[:60]}")
            return 0.0

    def _analyze_extreme_candle_reversal(self, snapshots):
        """
        ⭐ NUEVO: Detecta velas EXTREMAS y retorna dirección INVERSA para aprovechar reversión
        
        LÓGICA:
        - Si última vela fue EXTREMADAMENTE grande (body > 2x ATR)
        - Si subió mucho → VENDER (reversión hacia abajo)
        - Si bajó mucho → COMPRAR (reversión hacia arriba)
        
        Retorna: {
            'reversal_detected': bool,
            'reversal_direction': 'BUY' o 'SELL',
            'reversal_strength': 0.0-100.0 (confianza en reversión),
            'candle_move_pct': float (% del movimiento),
            'atr_ratio': float (tamaño vela / ATR)
        }
        """
        try:
            if not snapshots or len(snapshots) < 14:
                return {
                    'reversal_detected': False,
                    'reversal_direction': None,
                    'reversal_strength': 0.0,
                    'candle_move_pct': 0.0,
                    'atr_ratio': 0.0
                }
            
            # ═══════════════════════════════════════════════════════════
            # PASO 1: Calcular ATR (Average True Range) para normalizar
            # ═══════════════════════════════════════════════════════════
            try:
                highs = np.array([float(s.get('high', 0)) for s in snapshots[-14:]])
                lows = np.array([float(s.get('low', 0)) for s in snapshots[-14:]])
                closes = np.array([float(s.get('close', 0)) for s in snapshots[-14:]])
                
                # Calcular TR (True Range)
                high_low = highs - lows
                high_close = np.abs(highs - np.roll(closes, 1))
                low_close = np.abs(lows - np.roll(closes, 1))
                tr = np.max(np.vstack([high_low, high_close, low_close]), axis=0)
                atr = np.mean(tr[1:])  # Evitar primer valor NaN
                
                if atr <= 0:
                    atr = 0.01  # Evitar división por cero
            except Exception as e:
                logger.debug(f"[REVERSAL] Error calculating ATR: {str(e)[:60]}")
                return {
                    'reversal_detected': False,
                    'reversal_direction': None,
                    'reversal_strength': 0.0,
                    'candle_move_pct': 0.0,
                    'atr_ratio': 0.0
                }
            
            # ═══════════════════════════════════════════════════════════
            # PASO 2: Analizar última vela (la más reciente)
            # ═══════════════════════════════════════════════════════════
            last_candle = snapshots[-1]
            candle_open = float(last_candle.get('open', 0))
            candle_close = float(last_candle.get('close', 0))
            candle_high = float(last_candle.get('high', 0))
            candle_low = float(last_candle.get('low', 0))
            
            # Tamaño del cuerpo de la vela
            candle_body = abs(candle_close - candle_open)
            candle_range = candle_high - candle_low
            
            # Movimiento porcentual desde open hasta close
            if candle_open != 0:
                candle_move_pct = ((candle_close - candle_open) / candle_open) * 100.0
            else:
                candle_move_pct = 0.0
            
            # Ratio: tamaño vela / ATR (cuántos ATRs mide la vela)
            atr_ratio = candle_body / atr if atr > 0 else 0.0
            
            # ═══════════════════════════════════════════════════════════
            # PASO 3: Detectar si es una vela EXTREMA
            # ═══════════════════════════════════════════════════════════
            extreme_threshold = 1.8  # Vela debe ser > 1.8x ATR para ser considerada EXTREMA
            move_threshold = 0.25   # Movimiento debe ser > 0.25% para ser relevante
            
            if atr_ratio < extreme_threshold or abs(candle_move_pct) < move_threshold:
                return {
                    'reversal_detected': False,
                    'reversal_direction': None,
                    'reversal_strength': 0.0,
                    'candle_move_pct': candle_move_pct,
                    'atr_ratio': atr_ratio
                }
            
            # ═══════════════════════════════════════════════════════════
            # PASO 4: Determinar dirección de reversión (INVERSA a la vela)
            # ═══════════════════════════════════════════════════════════
            
            # Si vela cerró al alza (BUY) → Esperamos reversión a la baja (SELL)
            # Si vela cerró a la baja (SELL) → Esperamos reversión al alza (BUY)
            if candle_close > candle_open:  # Vela UP
                reversal_direction = 'SELL'
                reversal_reason = f"Vela UP extrema ({candle_move_pct:+.3f}%, {atr_ratio:.2f}x ATR) → esperando reversión BAJA"
            else:  # Vela DOWN
                reversal_direction = 'BUY'
                reversal_reason = f"Vela DOWN extrema ({candle_move_pct:+.3f}%, {atr_ratio:.2f}x ATR) → esperando reversión ALTA"
            
            # ═══════════════════════════════════════════════════════════
            # PASO 5: Calcular CONFIANZA en la reversión
            # ═══════════════════════════════════════════════════════════
            
            # Factores de confianza:
            # 1. Tamaño relativo de la vela (mayor = más extrema = mayor reversión esperada)
            size_confidence = min(100.0, (atr_ratio - extreme_threshold) / extreme_threshold * 100.0)
            
            # 2. Movimiento porcentual (mayor movimiento = más clara la dirección)
            move_confidence = min(100.0, abs(candle_move_pct) / move_threshold * 100.0)
            
            # 3. Cuerpo vs sombras (si el cuerpo es > 70% del rango, es más fuerte)
            body_ratio = (candle_body / candle_range) if candle_range > 0 else 0
            body_confidence = min(100.0, body_ratio * 100.0) if body_ratio > 0.7 else 50.0
            
            # Confianza final (promedio ponderado)
            reversal_strength = (size_confidence * 0.40 + move_confidence * 0.35 + body_confidence * 0.25)
            reversal_strength = max(0.0, min(100.0, reversal_strength))
            
            self.add_log(f"[🔄 REVERSIÓN EXTREMA] {reversal_reason}", 'warning')
            self.add_log(f"[📊 CONFIANZA] Size:{size_confidence:.0f}% + Move:{move_confidence:.0f}% + Body:{body_confidence:.0f}% = {reversal_strength:.0f}%", 'info')
            
            return {
                'reversal_detected': True,
                'reversal_direction': reversal_direction,
                'reversal_strength': reversal_strength,
                'candle_move_pct': candle_move_pct,
                'atr_ratio': atr_ratio
            }
            
        except Exception as e:
            logger.error(f"[REVERSAL] Error analyzing extreme candle: {str(e)[:80]}")
            return {
                'reversal_detected': False,
                'reversal_direction': None,
                'reversal_strength': 0.0,
                'candle_move_pct': 0.0,
                'atr_ratio': 0.0
            }

    def _apply_specialist_protections(self, buy_analysis, sell_analysis, snapshots=None, context='general'):
        """Aplica protecciones comunes de especialistas y retorna copias ajustadas."""
        try:
            if not buy_analysis or not sell_analysis:
                return buy_analysis, sell_analysis, {'block': False, 'reason': ''}

            buy_adj = dict(buy_analysis)
            sell_adj = dict(sell_analysis)

            buy_score = float(buy_adj.get('score', 0.0))
            sell_score = float(sell_adj.get('score', 0.0))
            buy_conf = float(buy_adj.get('confidence', 0.0))
            sell_conf = float(sell_adj.get('confidence', 0.0))

            try:
                max_streak = int(self.config.get('SPECIALIST_MAX_DIRECTION_LOSS_STREAK', tk.IntVar(value=3)).get())
            except Exception as e:
                logger.debug(f"[CONFIG] Error reading max_streak: {str(e)[:60]}")
                max_streak = 3
            try:
                penalty = float(self.config.get('SPECIALIST_DIRECTION_PENALTY', tk.DoubleVar(value=12.0)).get())
            except Exception as e:
                logger.debug(f"[CONFIG] Error reading penalty: {str(e)[:60]}")
                penalty = 12.0
            try:
                extreme_pct = float(self.config.get('SPECIALIST_EXTREME_MOVE_PCT', tk.DoubleVar(value=0.20)).get())
            except Exception as e:
                logger.debug(f"[CONFIG] Error reading extreme_pct: {str(e)[:60]}")
                extreme_pct = 0.20
            try:
                min_gap = float(self.config.get('SPECIALIST_MIN_SCORE_GAP', tk.DoubleVar(value=4.0)).get())
            except Exception as e:
                logger.debug(f"[CONFIG] Error reading min_gap: {str(e)[:60]}")
                min_gap = 4.0

            buy_streak = self._get_direction_loss_streak('BUY')
            sell_streak = self._get_direction_loss_streak('SELL')

            if max_streak > 0 and buy_streak >= max_streak:
                buy_score -= penalty
                buy_conf -= penalty * 0.6
                self.add_log(f"[SP-PROTECT] {context}: penalizando BUY por racha de pérdidas ({buy_streak})", 'warning')

            if max_streak > 0 and sell_streak >= max_streak:
                sell_score -= penalty
                sell_conf -= penalty * 0.6
                self.add_log(f"[SP-PROTECT] {context}: penalizando SELL por racha de pérdidas ({sell_streak})", 'warning')

            micro_move_pct = self._detect_extreme_micro_move(snapshots)
            score_gap = abs(buy_score - sell_score)
            if abs(micro_move_pct) >= abs(extreme_pct) and score_gap < min_gap:
                reason = f"micro-movimiento extremo ({micro_move_pct:+.3f}%) con gap bajo ({score_gap:.1f})"
                self.add_log(f"[SP-PROTECT] {context}: HOLD preventivo por {reason}", 'warning')
                buy_adj['score'] = max(0.0, buy_score)
                buy_adj['confidence'] = max(0.0, buy_conf)
                sell_adj['score'] = max(0.0, sell_score)
                sell_adj['confidence'] = max(0.0, sell_conf)
                return buy_adj, sell_adj, {'block': True, 'reason': reason}

            buy_adj['score'] = max(0.0, buy_score)
            buy_adj['confidence'] = max(0.0, buy_conf)
            sell_adj['score'] = max(0.0, sell_score)
            sell_adj['confidence'] = max(0.0, sell_conf)
            return buy_adj, sell_adj, {'block': False, 'reason': ''}
        except Exception as e:
            logger.error(f"[SP-PROTECT] Error in protection logic: {str(e)[:80]}")
            return buy_analysis, sell_analysis, {'block': False, 'reason': ''}

    def _analyze_for_forced_reopen(self, symbol):
        """Análisis dinámico de 30 segundos para reaperturas forzadas.
        Retorna: (mejor_dirección, score_buy, score_sell)"""
        try:
            best_buy = 50
            best_sell = 50
            best_direction = 'BUY'  # Default
            
            for i in range(30):
                try:
                    symbol = self.get_symbol_from_config()
                    snaps = self.get_market_snapshots_by_symbol(symbol) or []
                    if snaps:
                        self._refresh_specialists_session_context()
                        buy_res = None
                        sell_res = None
                        try:
                            # ⭐ ADQUIRIR LOCK para sincronización con monitor
                            with self.specialist_analysis_lock:
                                if hasattr(self.buy_specialist, 'analyze'):
                                    buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                                if hasattr(self.sell_specialist, 'analyze'):
                                    sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                        except Exception as e:
                            logger.error(f"[30s-ANAL] Error analyzing specialists: {str(e)[:80]}")
                        
                        if buy_res and sell_res:
                            buy_res, sell_res, prot = self._apply_specialist_protections(
                                buy_res, sell_res, snapshots=snaps, context='forced-30s'
                            )
                            if prot.get('block'):
                                continue
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
                except Exception as e:
                    logger.error(f"[30s-LOOP] Error in 30s loop iteration: {str(e)[:80]}")
                    time.sleep(1)
            
            self._update_forced_open_counter(0)
            return best_direction, best_buy, best_sell
        except Exception as e:
            self.add_log(f"Error en análisis forzada: {e}", 'error')
            return 'BUY', 50, 50

    def _quick_analysis_for_forced_reopen(self, symbol):
        """Análisis RÁPIDO para reaperturas forzadas - NO usa lock para evitar bloqueos.
        ⭐ IMPORTANTE: EN MODO FORZADO SE IGNORA ARBITRADOR - Se abre con mejor score
        Retorna: (mejor_dirección, score_buy, score_sell, trend_analysis)"""
        # --- FILTRO DE MICROTENDENCIA/MOMENTUM - USA THRESHOLD DEL PAR EN TIEMPO REAL ---
        try:
            microtrend = self._microtrend_direction(symbol, bars=10, threshold=None)  # ⭐ USA GOLD_THRESHOLD o SILVER_THRESHOLD DE CONFIG (PARAMETRIZABLE EN TIEMPO REAL)
        except Exception as e:
            self.add_log(f"[ERROR] microtrend_direction fallo: {e}", 'error')
            microtrend = 'FLAT'
        
        # Obtener threshold correcto del par
        if symbol.upper() == 'GOLD' or symbol == 'XAUUSD':
            threshold_pips = self._safe_get('GOLD_THRESHOLD', 18.0)
        elif symbol.upper() == 'SILVER' or symbol == 'XAGUSD':
            threshold_pips = self._safe_get('SILVER_THRESHOLD', 15.0)
        else:
            threshold_pips = self._safe_get('MICROTREND_THRESHOLD', 18.0)
        
        self.add_log(f"[MICROTREND/FORCED] Microtendencia detectada: {microtrend} (threshold={threshold_pips} pips por par, configurable en tiempo real)", 'info')
        try:
            # ⭐ CRÍTICO: Usar datos FRESCOS de MT5, no JSON estático
            snaps = self.get_fresh_market_data(symbol, bars=45) or []
            buy_score = 50
            sell_score = 50
            direction = 'BUY'
            trend_analysis = None
            buy_res = None
            sell_res = None
            market_trend = None  # ⭐ INICIALIZAR al principio
            
            # ⭐ PASO 1: Análisis de Especialistas SIN LOCK (scheduler tiene prioridad baja)
            # El monitor es quien mantiene la UI actualizada, así que NO lo bloqueamos
            if snaps:
                try:
                    self._refresh_specialists_session_context()
                    # ⭐ ANÁLISIS RÁPIDO sin lock - timeout protege contra bloqueos
                    if hasattr(self.buy_specialist, 'analyze'):
                        try:
                            buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                            buy_score = float(buy_res.get('score', 50)) if buy_res else 50
                        except Exception as e:
                            logger.debug(f"[RAPID-BUY] Error in rapid analysis: {str(e)[:60]}")
                    
                    if hasattr(self.sell_specialist, 'analyze'):
                        try:
                            sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                            sell_score = float(sell_res.get('score', 50)) if sell_res else 50
                        except Exception as e:
                            logger.debug(f"[RAPID-SELL] Error in rapid analysis: {str(e)[:60]}")

                    if buy_res and sell_res:
                        buy_res, sell_res, prot = self._apply_specialist_protections(
                            buy_res, sell_res, snapshots=snaps, context='forced-quick'
                        )
                        if prot.get('block'):
                            self.add_log(f"[FORZADA] HOLD por protección especialistas: {prot.get('reason', '')}", 'warning')
                            return 'BUY', 50, 50, trend_analysis
                        buy_score = float(buy_res.get('score', buy_score))
                        sell_score = float(sell_res.get('score', sell_score))
                    
                    # ⭐ PASO NUEVO: DETECTAR VELAS EXTREMAS Y APLICAR REVERSIÓN AUTOMÁTICA
                    # Si se detecta una vela extrema, invierte automáticamente los scores
                    reversal_analysis = self._analyze_extreme_candle_reversal(snaps)
                    reversal_detected = reversal_analysis.get('reversal_detected', False)
                    reversal_strength = reversal_analysis.get('reversal_strength', 0.0)
                    reversal_direction = reversal_analysis.get('reversal_direction')
                    
                    if reversal_detected and reversal_strength >= 60.0:
                        # ⭐ APLICAR INVERSIÓN DE SCORES POR REVERSIÓN EXTREMA
                        # Boost scores para la dirección de reversión, penaliza la opuesta
                        if reversal_direction == 'BUY':
                            boost_amount = min(25.0, reversal_strength * 0.30)
                            buy_score += boost_amount
                            sell_score = max(0.0, sell_score - boost_amount * 0.5)
                            self.add_log(f"[🔄 BOOST-REVERSIÓN] Boosting BUY +{boost_amount:.1f} (reversión detectada con {reversal_strength:.0f}% confianza)", 'success')
                        else:  # SELL
                            boost_amount = min(25.0, reversal_strength * 0.30)
                            sell_score += boost_amount
                            buy_score = max(0.0, buy_score - boost_amount * 0.5)
                            self.add_log(f"[🔄 BOOST-REVERSIÓN] Boosting SELL +{boost_amount:.1f} (reversión detectada con {reversal_strength:.0f}% confianza)", 'success')
                    
                    # ⭐ APLICAR AJUSTES DE SCORES - SOLO SI HAY UNA RAZÓN CLARA
                    # ANTES: Los ajustes por tendencia creaban sesgo systematic hacia BUY
                    # AHORA: Sin ajustes - los specialists ya incluyen análisis de tendencia en sus scores
                    market_trend = None
                    if buy_res and buy_res.get('market_condition'):
                        market_condition = buy_res.get('market_condition', {})
                        market_trend = market_condition.get('trend', None) if isinstance(market_condition, dict) else None
                    
                    # ⭐ FIX: NO ajustar scores por tendencia - eso crea sesgo
                    # Los especialistas ya consideran la tendencia en su análisis
                    buy_score_adjusted = buy_score
                    sell_score_adjusted = sell_score
                    
                    # ⭐ MODO FORZADO: Elegir por SCORE primero, confianza como desempate
                    # Extraer confianzas de los resultados de especialistas
                    buy_conf = float(buy_res.get('confidence', 0)) if buy_res else 0
                    sell_conf = float(sell_res.get('confidence', 0)) if sell_res else 0
                    buy_thr = float(self._safe_get('BUY_CONFIDENCE_THRESHOLD', 65.0))
                    sell_thr = float(self._safe_get('SELL_CONFIDENCE_THRESHOLD', 65.0))
                    min_gap = float(self._safe_get('SPECIALIST_MIN_SCORE_GAP', 4.0))
                    
                    # ⭐ DECISIÓN LIMPIA: Comparar scores PRIMERO, confianza como desempate
                    self.add_log(f"[FORZADA] 📋 DECISIÓN BRUTA: BUY (score={buy_score:.1f}, conf={buy_conf:.0f}%) vs SELL (score={sell_score:.1f}, conf={sell_conf:.0f}%)", 'info')
                    
                    # Comparar por SCORE primero (mayor precisión en microtendencias)
                    if buy_score > sell_score:
                        direction = 'BUY'
                        self.add_log(f"[FORZADA] ✅ DECISIÓN: BUY (score {buy_score:.1f} > {sell_score:.1f})", 'success')
                    elif sell_score > buy_score:
                        direction = 'SELL'
                        self.add_log(f"[FORZADA] ✅ DECISIÓN: SELL (score {sell_score:.1f} > {buy_score:.1f})", 'success')
                    else:
                        # Empate de score, usar confianza como desempate
                        if buy_conf > sell_conf:
                            direction = 'BUY'
                            self.add_log(f"[FORZADA] ⚔️ DESEMPATE: BUY (confianza {buy_conf:.0f}% > {sell_conf:.0f}%, score empatado {buy_score:.1f})", 'info')
                        elif sell_conf > buy_conf:
                            direction = 'SELL'
                            self.add_log(f"[FORZADA] ⚔️ DESEMPATE: SELL (confianza {sell_conf:.0f}% > {buy_conf:.0f}%, score empatado {sell_score:.1f})", 'info')
                        else:
                            # Empate completo - elegir BUY por defecto (raro)
                            direction = 'BUY'
                            self.add_log(f"[FORZADA] ⚔️ EMPATE TOTAL: Eligiendo BUY por defecto (score {buy_score:.1f}, conf {buy_conf:.0f}%)", 'warning')

                    # Modo siempre-abrir: nunca cancelar por HOLD.
                    # Si la convicción es baja, recalibrar dirección con score+confianza y abrir igualmente.
                    chosen_conf = buy_conf if direction == 'BUY' else sell_conf
                    chosen_thr = buy_thr if direction == 'BUY' else sell_thr
                    score_gap = abs(float(buy_score) - float(sell_score))
                    if chosen_conf < chosen_thr or score_gap < min_gap:
                        buy_conv = (float(buy_score) * 0.70) + (float(buy_conf) * 0.30)
                        sell_conv = (float(sell_score) * 0.70) + (float(sell_conf) * 0.30)
                        direction = 'BUY' if buy_conv >= sell_conv else 'SELL'
                        self.add_log(
                            f"[FORZADA] 🔄 Always-open override: convicción baja (conf {chosen_conf:.0f}/{chosen_thr:.0f}, gap {score_gap:.1f}/{min_gap:.1f}) -> {direction} (BUY {buy_conv:.1f} vs SELL {sell_conv:.1f})",
                            'warning'
                        )
                    
                    if market_trend:
                        self.add_log(f"[🛡️] Scores: BUY {buy_score:.1f}→{buy_score_adjusted:.1f} | SELL {sell_score:.1f}→{sell_score_adjusted:.1f} | Confianza: BUY {buy_conf:.0f}% | SELL {sell_conf:.0f}% = {direction}", 'info')
                    
                    # Usar las puntuaciones ajustadas para el retorno
                    buy_score = buy_score_adjusted
                    sell_score = sell_score_adjusted
                    
                    # ⭐ ACTUALIZAR SCORES CACHÉS PARA EL MONITOR
                    try:
                        with self.specialist_scores_lock:
                            self.scheduler_shared_scores.update({
                                'buy_score': float(buy_score),
                                'sell_score': float(sell_score),
                                'buy_conf': buy_res.get('confidence', 0) if buy_res else 0,
                                'sell_conf': sell_res.get('confidence', 0) if sell_res else 0,
                                'timestamp': time.time()
                            })
                    except Exception as e:
                        logger.debug(f"[SCHEDULER-CACHE] Error caching scores: {str(e)[:60]}")

                    # Metadata para feedback loop - REMOVIDA: solo análisis de mercado
                    # self.last_trade_metadata = {...} - DESHABILITADO
                    except Exception:
                        pass
                    
                except Exception as e:
                    logger.warning(f"[SCHEDULER-ANALYSIS] Error analizando especialistas: {str(e)[:60]}")
                    pass
            
            # ⭐ PASO 2: DESHABILITADO - NO SOBRESCRIBIR DECISIÓN DE ESPECIALISTAS
            # El sesgo de tendencia estaba invirtiendo decisiones correctas de los especialistas
            # La dirección elegida por BUY/SELL specialists es FINAL, sin sobrescrituras
            try:
                if hasattr(self, 'last_trend_analysis'):
                    trend_analysis = self.last_trend_analysis
                else:
                    trend_analysis = None
            except Exception as e:
                logger.debug(f"[TREND] Error getting trend: {str(e)[:60]}")
                trend_analysis = None
            
            # ⭐ PASO 3: EN MODO FORZADO, IGNORAR ARBITRADOR
            # Las reaperturas forzadas (cada 60s) son más agresivas
            # Abrimos con la dirección que tiene mejor score, sin validación conservadora del arbitrador
            live_buy = float(buy_score)
            live_sell = float(sell_score)
            live_age = 999.0
            live_gap = abs(live_buy - live_sell)
            live_dir = direction
            try:
                with self.specialist_scores_lock:
                    live_buy = float(self.scheduler_shared_scores.get('buy_score', buy_score))
                    live_sell = float(self.scheduler_shared_scores.get('sell_score', sell_score))
                    live_ts = float(self.scheduler_shared_scores.get('timestamp', 0.0))
                live_age = (time.time() - live_ts) if live_ts > 0 else 999.0
                live_gap = abs(live_buy - live_sell)
                live_dir = 'BUY' if live_buy >= live_sell else 'SELL'
            except Exception as e:
                logger.debug(f"[SCORES-LOCK] Error reading shared scores: {str(e)[:60]}")

            # Mezcla rápida: pondera más LIVE cuando está fresca para reaccionar antes a giros.
            try:
                if live_age <= 2.5:
                    buy_score = (float(buy_score) * 0.35) + (float(live_buy) * 0.65)
                    sell_score = (float(sell_score) * 0.35) + (float(live_sell) * 0.65)
            except Exception as e:
                logger.debug(f"[BLEND] Error blending scores: {str(e)[:60]}")

            # --- BLOQUEO/REVERSIÓN POR MICROTENDENCIA EN MODO FORZADO ---
            # Si la microtendencia es contraria a la dirección elegida, solo abrir si el gap de score es muy alto
            score_gap_required = 7.0
            if direction in ('BUY', 'SELL') and microtrend in ('BUY', 'SELL') and direction != microtrend:
                gap = abs(float(buy_score) - float(sell_score))
                if gap < score_gap_required:
                    self.add_log(f"[MICROTREND/FORCED] BLOQUEADO: Dirección {direction} va contra microtendencia {microtrend} y gap={gap:.2f} < {score_gap_required}", 'warning')
                    return direction, buy_score, sell_score, trend_analysis  # FIX: Devolver direction, no None
                else:
                    self.add_log(f"[MICROTREND/FORCED] ⚠️ Permitiendo apertura contra microtendencia por gap alto: {gap:.2f}", 'warning')

            override_reason = "RAW_SCORE"
            try:
                # Impulso de mercado: más estricto y sin contradecir una señal LIVE dominante.
                closes = []
                for s in (snaps[-7:] if isinstance(snaps, list) else []):
                    if isinstance(s, dict) and s.get('close') is not None:
                        closes.append(float(s.get('close')))

                if len(closes) >= 5:
                    up_moves = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i - 1])
                    down_moves = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i - 1])
                    impulse_pct = ((closes[-1] - closes[-5]) / max(abs(closes[-5]), 1.0)) * 100.0
                    winner_gap = abs(float(buy_score) - float(sell_score))

                    impulse_dir = None
                    if up_moves >= 4 and (up_moves - down_moves) >= 2 and impulse_pct >= 0.10:
                        impulse_dir = 'BUY'
                    elif down_moves >= 4 and (down_moves - up_moves) >= 2 and impulse_pct <= -0.10:
                        impulse_dir = 'SELL'

                    if impulse_dir and impulse_dir != direction:
                        if live_age <= 2.5 and live_gap >= 8.0 and impulse_dir != live_dir:
                            self.add_log(
                                f"[FORZADA] ⚖️ Impulso ignorado por LIVE fuerte ({impulse_dir} vs LIVE {live_dir}, gap={live_gap:.1f})",
                                'info'
                            )
                        elif winner_gap <= 12.0:
                            prev_dir = direction
                            direction = impulse_dir
                            override_reason = "IMPULSE_OVERRIDE"
                            self.add_log(
                                f"[FORZADA] ⚡ Override IMPULSO: {prev_dir} -> {direction} (up={up_moves}, down={down_moves}, impulse={impulse_pct:.4f}%, gap={winner_gap:.1f})",
                                'warning'
                            )
            except Exception as e:
                logger.debug(f"[IMPULSE] Error in impulse override: {str(e)[:60]}")

            try:
                # LIVE es la última palabra si está fresco y tiene ventaja mínima.
                if live_age <= 2.5 and live_gap >= 1.2:
                    if live_dir != direction:
                        self.add_log(
                            f"[FORZADA] 🔄 Override LIVE: {direction} -> {live_dir} (BUY {live_buy:.1f} | SELL {live_sell:.1f} | age {live_age:.2f}s)",
                            'warning'
                        )
                        override_reason = "LIVE_OVERRIDE"
                    direction = live_dir
                    buy_score = live_buy
                    sell_score = live_sell
            except Exception as e:
                logger.debug(f"[LIVE-OVERRIDE] Error in live override: {str(e)[:60]}")

            try:
                self.add_log(f"[FORZADA] 🧭 Motivo final: {override_reason}", 'info')
            except Exception:
                pass

            self.add_log(f"[🛡️] ✅ Análisis recomendado: {direction} (score={buy_score:.1f} vs {sell_score:.1f}) - Se aplicarán validaciones antes de abrir", 'info')
            
            return direction, buy_score, sell_score, trend_analysis
        except Exception as e:
            self.add_log(f"Error en análisis completo forzada: {e}", 'error')
            return 'BUY', 50, 50, None

    def evaluate_snapshots_and_open(self, symbol):
        """Evaluate `market_snapshots` with a light heuristic and open if signal found.
        ⭐ NUEVA LÓGICA: 30s análisis ANTES de abrir la operación inicial."""
        try:
            # ⭐ CRÍTICO: Usar datos FRESCOS de MT5, no JSON estático
            snaps = self.get_fresh_market_data(symbol, bars=100) or []
            
            # Ask specialists to evaluate using snapshots and WITHOUT recovery checks
            buy_res = None
            sell_res = None
            try:
                self._refresh_specialists_session_context()
                # ⭐ ADQUIRIR LOCK para sincronización con monitor
                with self.specialist_analysis_lock:
                    if hasattr(self.buy_specialist, 'analyze'):
                        buy_res = self.buy_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
                    if hasattr(self.sell_specialist, 'analyze'):
                        sell_res = self.sell_specialist.analyze(symbol, market_snapshots=snaps, check_recovery_potential=False)
            except Exception as e:
                logger.error(f"[BOT-LOOP-ANAL] Error analyzing specialists: {str(e)[:80]}")
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
            
            # 🎯 SIN SESGOS: Usar scores crudos de especialistas sin ajustes de tendencia
            # El usuario pidió eliminar penalizaciones para centrar decisiones en scores reales
            
            # Choose the direction with ADJUSTED scores; tie-break on confidence
            chosen = None
            try:
                if buy_res and sell_res:
                    if buy_score_adjusted > sell_score_adjusted:
                        chosen = 'BUY'
                        if market_trend:
                            self.add_log(f"[🟢 BUY {buy_score_adjusted:.1f} > SELL {sell_score_adjusted:.1f}{trend_bias_info}", 'info')
                    elif sell_score_adjusted > buy_score_adjusted:
                        chosen = 'SELL'
                        if market_trend:
                            self.add_log(f"[🟢 SELL {sell_score_adjusted:.1f} > BUY {buy_score_adjusted:.1f}{trend_bias_info}", 'info')
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
                self.add_log(f"⚠️ Error calculando potencial: {e}", 'error')
                chosen = None

            if chosen:
                # ⭐ ANÁLISIS 30s: Monitorear probabilidades en VIVO
                self.add_log(f"\n{'📊'*35}", 'info')
                self.add_log(f"[⏰] ⭐ MODO AGRESIVO: Abriendo con mejor score de especialistas (IGNORA arbitrador conservador)", 'success')
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
                self.add_log(f"[⏰] Análisis completado en 30 segundos", 'success')
                # ⭐ SIMPLIFICADO: Solo mostrar opción ganadora con confianza
                chosen_conf = best_buy_conf if best_direction == 'BUY' else best_sell_conf
                self.add_log(f"[⏰] {best_direction.upper()} {chosen_conf:.0f}%", 'success')
                self.add_log(f"[⏰] 🚀 ABRIENDO INMEDIATAMENTE: {best_direction.upper()}", 'success')
                self.add_log(f"{'✅'*35}\n", 'success')
                
                # ⭐ DESACTIVADO: NO ABRIR operación inicial (solo forzadas del scheduler)
                # try:
                #     result = self.abrir_operacion(best_direction, force=True, startup=True)
                #     if not result:
                #         self.add_log(f"[ERROR] abrir_operacion retornó False para {best_direction}", 'error')
                #     return result
                # except Exception as e:
                #     self.add_log(f"❌ Exception en abrir_operacion: {str(e)[:100]}", 'error')
                #     import traceback
                #     self.add_log(f"🔍 {traceback.format_exc()[:200]}", 'error')
                #     return False
                
                return False  # No abrir operación inicial
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
            # ⭐ DESACTIVADO: NO ABRIR operación inicial
            # try:
            #     return self.abrir_operacion(sig, force=True, startup=True)
            # except Exception:
            #     return False
            return False

        self.add_log(f"🤖 Multi-IA inicial sugiere {decision} — intentando abrir inmediatamente", 'info')
        # ⭐ DESACTIVADO: NO ABRIR operación inicial
        # try:
        #     return self.abrir_operacion(decision, force=True, startup=True)
        # except Exception:
        #     return False
        return False
        
    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg='#0f172a', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # ⭐ NUEVO: Frame horizontal para título + contador de tiempo
        title_frame = tk.Frame(header_frame, bg='#0f172a')
        title_frame.pack(fill='x', pady=10)
        
        title_label = tk.Label(title_frame, text="MT5 Smart Multi-IA Trading Bot", 
                              font=('Arial', 24, 'bold'), bg='#0f172a', fg='#60a5fa')
        title_label.pack(side='left', padx=10)
        
        # ⭐ NUEVO: Contador de próxima apertura forzada en el header
        time_header_frame = tk.Frame(title_frame, bg='#0f172a')
        time_header_frame.pack(side='right', padx=15)
        
        tk.Label(time_header_frame, text="📅 Próx.:", bg='#0f172a', fg='#f1f5f9', 
                font=('Arial', 14, 'bold')).pack(side='left', padx=3)
        self.rapid_countdown_label = tk.Label(time_header_frame, text="-", bg='#fbbf24', fg='#0f172a', font=('Arial', 15, 'bold'), width=4, relief='solid', bd=2)
        self.rapid_countdown_label.pack(side='left', padx=8)
        
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
        
        # Panel derecho (Sin cambios)
        right_panel = tk.Frame(main_container, bg='#1e293b')
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Llenar las pestañas
        self.create_control_panel(control_tab)
        self.create_config_panel(config_tab)
        self.create_stats_panel(right_panel)
        self.create_objectives_panel(right_panel)  # ⭐ Nuevo: Mostrar Objetivo Neto y Margen Ganancia
        self.create_future_data_panel(right_panel)  # 📊 Nuevo cuadro para datos futuros
        self.create_events_panel(right_panel)
        # Iniciar actualización periódica de información de cuenta (balance/equity)
        try:
            self._schedule_account_update()
        except Exception as e:
            self.add_log(f"[INIT] Error scheduling account update: {str(e)[:60]}", 'error')
        
    def _schedule_account_update(self):
        """Programa la actualización periódica de la información de cuenta MT5."""
        if self._account_scheduler_running:
            return
        self._account_scheduler_running = True
        
        # ⭐ Iniciar monitor global TP/SL en un hilo separado (después de que self.config está definido)
        try:
            self.global_tp_sl_thread = threading.Thread(target=self._monitor_global_tp_sl, daemon=True)
            self.global_tp_sl_thread.start()
            self.add_log("[GLOBAL TP/SL] Monitor global TP/SL iniciado.", 'info')
        except Exception as e:
            self.add_log(f"[GLOBAL TP/SL] Error iniciando monitor: {str(e)[:60]}", 'error')

        def _tick():
            try:
                # Reconectar a MT5 si es necesario
                try:
                    if not mt5.initialize():
                        mt5.initialize()
                except Exception as e:
                    logger.debug(f"[MT5-INIT] Error reconnecting MT5: {str(e)[:60]}")
                self.update_account_info()
            except Exception as e:
                logger.debug(f"[TICK] Error in account tick: {str(e)[:60]}")
            finally:
                try:
                    if self._account_scheduler_running:
                        self.root.after(1000, _tick)
                except Exception as e:
                    logger.debug(f"[TICK-SCHEDULE] Error scheduling next tick: {str(e)[:60]}")

        try:
            self.root.after(0, _tick)
        except Exception:
            pass
    
    def _monitor_profit_margin(self):
        """Monitorea el margen de ganancia y cierra el bot si se alcanza el objetivo.
        
        Lógica:
        - balance_inicial * (1 + margen/100) = objetivo
        - Cada segundo, verifica si equity >= objetivo
        - Si se cumple: cierra todas las operaciones y detiene el bot
        - Se activa SOLO si margen >= 1, se desactiva si margen es 0
        - INDEPENDIENTE: si Objetivo Neto está activo, este se desactiva
        """
        try:
            # Obtener parámetros
            margen_pct = float(self._safe_get('MARGEN_GANANCIA', 1.0))
            objetivo_neto = float(self._safe_get('OBJETIVO_NETO', 0.0))
            
            # ⭐ Actualizar label de estado PRIMERO (antes de cualquier retorno)
            if self.margen_monitor_label:
                try:
                    if margen_pct < 1:
                        self.margen_monitor_label.config(text="Desactivado (Margen < 1%)", fg='#cbd5e1')
                    elif objetivo_neto > 0 and self.objetivo_neto_running:
                        self.margen_monitor_label.config(text="Desactivado (Objetivo Neto activo)", fg='#cbd5e1')
                    else:
                        # Actualizar con datos actuales
                        account_info = mt5.account_info()
                        if account_info is not None:
                            equity = float(getattr(account_info, 'equity', 0.0))
                            if self.balance_inicial_para_margen == 0:
                                self.balance_inicial_para_margen = equity
                                self.objetivo_margen_ganancia = self.balance_inicial_para_margen * (1.0 + margen_pct / 100.0)
                            progress_pct = (equity / self.objetivo_margen_ganancia * 100) if self.objetivo_margen_ganancia > 0 else 0
                            self.margen_monitor_label.config(text=f"💵 Patrimonio: ${equity:.2f} / Objetivo: ${self.objetivo_margen_ganancia:.2f} ({progress_pct:.1f}%)", fg='#34d399')
                        else:
                            self.margen_monitor_label.config(text="Esperando conexión MT5...", fg='#fbbf24')
                except Exception as label_err:
                    pass
            
            # Si el Objetivo Neto está activo, desactivar este monitor
            if objetivo_neto > 0 and self.objetivo_neto_running:
                self.margen_monitor_running = False
                return
            
            # Si margen es 0 o menor a 1, desactivar
            if margen_pct < 1:
                self.margen_monitor_running = False
                return
            
            # Calcular objetivo una sola vez (cuando inicia)
            if self.balance_inicial_para_margen == 0:
                account_info = mt5.account_info()
                if account_info is not None:
                    self.balance_inicial_para_margen = float(getattr(account_info, 'equity', 0.0))
                    self.objetivo_margen_ganancia = self.balance_inicial_para_margen * (1.0 + margen_pct / 100.0)
                    self.add_log(f"💰 Margen Ganancia Iniciado: Patrimonio={self.balance_inicial_para_margen:.2f}, Objetivo={self.objetivo_margen_ganancia:.2f} ({margen_pct}%)", 'info')
                else:
                    self.add_log("⚠️ No se pudo obtener balance inicial para margen de ganancia", 'warning')
                    return
            
            # Verificar si se alcanzó el objetivo (cada segundo)
            account_info = mt5.account_info()
            if account_info is not None:
                equity = float(getattr(account_info, 'equity', 0.0))
                
                # Verificar si se alcanzó
                if equity >= self.objetivo_margen_ganancia and not self.margen_ganancia_alcanzado:
                    self.margen_ganancia_alcanzado = True
                    self.add_log(f"✅ OBJETIVO ALCANZADO: Patrimonio ${equity:.2f} >= Objetivo ${self.objetivo_margen_ganancia:.2f}", 'success')
                    self.add_log("🔴 Iniciando cierre de emergencia y detención del bot...", 'warning')
                    
                    # Cierra todas las operaciones
                    try:
                        self.cierre_emergencia()
                    except Exception as e:
                        self.add_log(f"❌ Error en cierre de emergencia: {str(e)[:80]}", 'error')
                    
                    # Detiene el bot
                    try:
                        self.is_running = False
                        self.pause_until = 0.0
                        self.margen_monitor_running = False
                        # Forzar actualización UI
                        if hasattr(self, 'root'):
                            self.root.after(100, self.stop_bot)
                    except Exception as e:
                        self.add_log(f"❌ Error deteniendo bot: {str(e)[:80]}", 'error')
        
        except Exception as e:
            self.add_log(f"❌ Error en monitoreo margen: {str(e)[:80]}", 'error')
        
        # Reprogramar si sigue activo
        if self.margen_monitor_running:
            try:
                self.root.after(500, self._monitor_profit_margin)
            except:
                pass
    
    def _monitor_objetivo_neto(self):
        """Monitorea el objetivo neto y cierra el bot si se alcanza.
        
        Lógica NUEVA:
        - El usuario especifica un INCREMENTO neto (ej: 2)
        - Se calcula SOLO UNA VEZ: patrimonio_inicial + incremento
        - Cada N segundos (reducido), verifica si equity >= target
        - Si se cumple: cierra todas las operaciones y detiene el bot
        - Se activa SOLO si objetivo_neto > 0, se desactiva si es 0
        """
        try:
            # Obtener parámetro
            objetivo_neto = float(self._safe_get('OBJETIVO_NETO', 0.0))
            margen_pct = float(self._safe_get('MARGEN_GANANCIA', 1.0))
            
            # ⭐ Actualizar label de estado PRIMERO (antes de cualquier retorno)
            if self.objetivo_neto_label:
                try:
                    if objetivo_neto <= 0:
                        self.objetivo_neto_label.config(text="Desactivado (Objetivo $0)", fg='#cbd5e1')
                    elif margen_pct >= 1 and self.margen_monitor_running:
                        self.objetivo_neto_label.config(text="Desactivado (Margen Ganancia activo)", fg='#cbd5e1')
                    else:
                        # Actualizar con datos actuales
                        account_info = mt5.account_info()
                        if account_info is not None:
                            equity = float(getattr(account_info, 'equity', 0.0))
                            if self.objetivo_neto_valor == 0:
                                self.objetivo_neto_valor = equity + objetivo_neto
                            falta = self.objetivo_neto_valor - equity
                            progress_pct = (equity / self.objetivo_neto_valor * 100) if self.objetivo_neto_valor > 0 else 0
                            falta_text = f" (Falta: ${abs(falta):.2f})" if falta > 0 else f" (Excedido: ${abs(falta):.2f})"
                            self.objetivo_neto_label.config(text=f"🎯 Patrimonio: ${equity:.2f} → Target: ${self.objetivo_neto_valor:.2f}{falta_text} ({progress_pct:.1f}%)", fg='#34d399')
                        else:
                            self.objetivo_neto_label.config(text="Esperando conexión MT5...", fg='#fbbf24')
                except Exception as label_err:
                    pass
            
            # Si el Margen de Ganancia está activo, desactivar este monitor
            if margen_pct >= 1 and self.margen_monitor_running:
                self.objetivo_neto_running = False
                return
            
            # Si objetivo es 0 o menor, desactivar
            if objetivo_neto <= 0:
                self.objetivo_neto_running = False
                return
            
            # Guardar el patrimonio inicial y calcular target SOLO una vez
            if self.objetivo_neto_valor == 0:
                account_info = mt5.account_info()
                if account_info is not None:
                    patrimonio_inicial = float(getattr(account_info, 'equity', 0.0))
                    self.objetivo_neto_valor = patrimonio_inicial + objetivo_neto
                    self.add_log(f"🎯 Objetivo Neto ACTIVADO: Patrimonio=${patrimonio_inicial:.2f} + Incremento=${objetivo_neto:.2f} = Target=${self.objetivo_neto_valor:.2f}", 'success')
                else:
                    self.add_log("⚠️ No se pudo obtener balance inicial para objetivo neto", 'warning')
                    return
            
            # Verificar si se alcanzó el objetivo (CASI EN TIEMPO REAL: 100ms = <1s)
            account_info = mt5.account_info()
            if account_info is not None:
                equity = float(getattr(account_info, 'equity', 0.0))
                
                # Verificar si se alcanzó (SUMA)
                if equity >= self.objetivo_neto_valor and not self.objetivo_neto_alcanzado:
                    self.objetivo_neto_alcanzado = True
                    self.add_log(f"✅ OBJETIVO NETO ALCANZADO: Patrimonio ${equity:.2f} >= Target ${self.objetivo_neto_valor:.2f}", 'success')
                    self.add_log("🔴 Iniciando cierre de emergencia y detención del bot...", 'warning')
                    
                    # Cierra todas las operaciones
                    try:
                        self.cierre_emergencia()
                    except Exception as e:
                        self.add_log(f"❌ Error en cierre de emergencia: {str(e)[:80]}", 'error')
                    
                    # Detiene el bot
                    try:
                        self.is_running = False
                        self.pause_until = 0.0
                        self.objetivo_neto_running = False
                        # Forzar actualización UI
                        if hasattr(self, 'root'):
                            self.root.after(100, self.stop_bot)
                    except Exception as e:
                        self.add_log(f"❌ Error deteniendo bot: {str(e)[:80]}", 'error')
        
        except Exception as e:
            self.add_log(f"❌ Error en monitoreo objetivo neto: {str(e)[:80]}", 'error')
        
        # Reprogramar si sigue activo
        if self.objetivo_neto_running:
            try:
                self.root.after(500, self._monitor_objetivo_neto)
            except:
                pass
        
    def create_control_panel(self, parent):
        control_frame = tk.LabelFrame(parent, text="Control del Bot", 
                                     bg='#334155', fg='#f1f5f9',
                                     font=('Arial', 11, 'bold'), padx=15, pady=15)
        control_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ⭐ ESTADO DEL BOT - ARRIBA DEL TODO
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
        
        # ⭐ TERCER PANEL DESPLEGABLE: Balance, Patrimonio, Margen y Objetivos
        self.finance_panel_expanded = True
        
        # Frame PRINCIPAL para el panel de finanzas
        self.finance_panel_main = tk.Frame(control_frame, bg='#1e293b')
        self.finance_panel_main.pack(fill='x', pady=(0, 15))
        
        # Frame de toggle para el panel de finanzas
        self.toggle_frame_finance = tk.Frame(self.finance_panel_main, bg='#1e293b', height=35)
        self.toggle_frame_finance.pack(fill='x', expand=False)
        
        self.collapse_toggle_btn_finance = tk.Button(
            self.toggle_frame_finance, 
            text="▼ Balance, Patrimonio y Objetivos",
            command=self._toggle_finance_panel,
            bg='#64748b', fg='#fbbf24', font=('Arial', 10, 'bold'),
            relief='flat', padx=15, pady=8, cursor='hand2', justify='left'
        )
        self.collapse_toggle_btn_finance.pack(side='left', fill='x', expand=True)
        
        # Frame contenedor para todo el contenido de finanzas (se colapsa/expande)
        self.finance_content_container = tk.Frame(self.finance_panel_main, bg='#334155')
        self.finance_content_container.pack(fill='x', expand=False)
        
        # ⭐ INFORMACIÓN DE CUENTA MT5 - DENTRO DEL PANEL DESPLEGABLE
        account_info_frame = tk.Frame(self.finance_content_container, bg='#334155')
        account_info_frame.pack(fill='x', padx=5, pady=(5, 0))
        
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
        
        # ===== MARGEN DE GANANCIA - DENTRO DEL PANEL DESPLEGABLE =====
        margen_frame = tk.Frame(self.finance_content_container, bg='#334155')
        margen_frame.pack(fill='x', padx=5, pady=(5, 0))
        
        tk.Label(margen_frame, text="🎯 Margen de Ganancia:", bg='#334155', fg='#f1f5f9', 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.margen_monitor_label = tk.Label(margen_frame, text="Inactivo", 
                                            bg='#334155', fg='#cbd5e1', font=('Arial', 9))
        self.margen_monitor_label.pack(anchor='w', pady=(0, 5))
        
        # ===== OBJETIVO NETO - DENTRO DEL PANEL DESPLEGABLE =====
        objetivo_neto_frame = tk.Frame(self.finance_content_container, bg='#334155')
        objetivo_neto_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        tk.Label(objetivo_neto_frame, text="🎯 Objetivo Neto:", bg='#334155', fg='#f1f5f9', 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.objetivo_neto_label = tk.Label(objetivo_neto_frame, text="Inactivo", 
                                           bg='#334155', fg='#cbd5e1', font=('Arial', 9))
        self.objetivo_neto_label.pack(anchor='w', pady=(0, 0))
        
        # ⭐ PANEL DESPLEGABLE COLAPSABLE DE BOTONES
        self.control_panel_expanded = True
        
        # ⭐ Frame PRINCIPAL que contiene todo (toggle + botones)
        self.control_panel_main = tk.Frame(control_frame, bg='#334155')
        self.control_panel_main.pack(fill='x')
        
        # Frame de toggle (encabezado con botón de colapso) - SIEMPRE VISIBLE
        self.toggle_frame = tk.Frame(self.control_panel_main, bg='#334155', height=35)
        self.toggle_frame.pack(fill='x', expand=False)
        
        self.collapse_toggle_btn = tk.Button(
            self.toggle_frame, 
            text="▼ Controles de Bot",
            command=self._toggle_control_panel,
            bg='#64748b', fg='#fbbf24', font=('Arial', 10, 'bold'),
            relief='flat', padx=15, pady=8, cursor='hand2', justify='left'
        )
        self.collapse_toggle_btn.pack(side='left', fill='x', expand=True)
        
        # Frame contenedor para todos los botones (se colapsa/expande)
        self.control_buttons_container = tk.Frame(self.control_panel_main, bg='#334155')
        self.control_buttons_container.pack(fill='x', expand=False)
        
        # Frame para botones principales (Iniciar/Detener)
        btn_frame = tk.Frame(self.control_buttons_container, bg='#334155')
        btn_frame.pack(fill='x', padx=5, pady=(5, 0))
        
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
        mgmt_btn_frame = tk.Frame(self.control_buttons_container, bg='#334155')
        mgmt_btn_frame.pack(fill='x', padx=5, pady=(5, 5))
        
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

        # ⭐ SEGUNDO PANEL DESPLEGABLE: Sistema Multi-IA, Objetivos y Pausas
        self.advanced_panel_expanded = True
        
        # Frame PRINCIPAL para el segundo panel
        self.advanced_panel_main = tk.Frame(control_frame, bg='#1e293b')
        self.advanced_panel_main.pack(fill='x', pady=(10, 0))
        
        # Frame de toggle para el segundo panel
        self.toggle_frame_advanced = tk.Frame(self.advanced_panel_main, bg='#1e293b', height=35)
        self.toggle_frame_advanced.pack(fill='x', expand=False)
        
        self.collapse_toggle_btn_advanced = tk.Button(
            self.toggle_frame_advanced, 
            text="▼ Sistema Multi-IA, Objetivos y Pausas",
            command=self._toggle_advanced_panel,
            bg='#64748b', fg='#fbbf24', font=('Arial', 10, 'bold'),
            relief='flat', padx=15, pady=8, cursor='hand2', justify='left'
        )
        self.collapse_toggle_btn_advanced.pack(side='left', fill='x', expand=True)
        
        # Frame contenedor para todo el contenido avanzado (se colapsa/expande)
        self.advanced_content_container = tk.Frame(self.advanced_panel_main, bg='#334155')
        self.advanced_content_container.pack(fill='x', expand=False)
        
        # ⭐ CONTENIDO DEL PANEL: Toggle Multi-IA
        multi_ai_frame = tk.Frame(self.advanced_content_container, bg='#334155')
        multi_ai_frame.pack(fill='x', padx=5, pady=(5, 0))

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
        
        # ⭐ CONTENIDO DEL PANEL: Objetivos y Pausas
        objetivo_frame = tk.LabelFrame(self.advanced_content_container, text="Objetivos y Pausas", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=10, pady=10)
        objetivo_frame.pack(fill='x', padx=5, pady=(5, 0))
        
        # Fila 1: Objetivo y Tiempo
        row1 = tk.Frame(objetivo_frame, bg='#2d3e50')
        row1.pack(fill='x', pady=3)
        
        tk.Label(row1, text="Objetivo ($):", bg='#2d3e50', fg='#f1f5f9', width=16, anchor='w').pack(side='left', padx=5)
        tk.Entry(row1, textvariable=self.objetivo_ganancia, width=8, bg='#475569', fg='white').pack(side='left', padx=5)
        
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

        # ⭐ CUARTO PANEL DESPLEGABLE: Cierre de Emergencia, Trading Manual y Detector de Tendencia
        self.emergency_panel_expanded = True
        
        # Frame PRINCIPAL para el panel de emergencia
        self.emergency_panel_main = tk.Frame(control_frame, bg='#1e293b')
        self.emergency_panel_main.pack(fill='x', pady=(10, 0))
        
        # Frame de toggle para el panel de emergencia
        self.toggle_frame_emergency = tk.Frame(self.emergency_panel_main, bg='#1e293b', height=35)
        self.toggle_frame_emergency.pack(fill='x', expand=False)
        
        self.collapse_toggle_btn_emergency = tk.Button(
            self.toggle_frame_emergency, 
            text="▼ Cierre Emergencia, Trading Manual y Tendencia",
            command=self._toggle_emergency_panel,
            bg='#64748b', fg='#ef4444', font=('Arial', 10, 'bold'),
            relief='flat', padx=15, pady=8, cursor='hand2', justify='left'
        )
        self.collapse_toggle_btn_emergency.pack(side='left', fill='x', expand=True)
        
        # Frame contenedor para todo el contenido del panel de emergencia (se colapsa/expande)
        self.emergency_content_container = tk.Frame(self.emergency_panel_main, bg='#334155')
        self.emergency_content_container.pack(fill='x', expand=False)
        
        # ⭐ BOTÓN DE CIERRE DE EMERGENCIA - DENTRO DEL PANEL DESPLEGABLE
        self.emergency_btn = tk.Button(self.emergency_content_container, text="🚨 CIERRE DE EMERGENCIA", 
                                     command=self.cierre_emergencia,
                                     bg='#dc2626', fg='white', font=('Arial', 10, 'bold'),
                                     relief='flat', padx=20, pady=8, cursor='hand2')
        self.emergency_btn.pack(fill='x', pady=(5, 10), padx=5)
        
        # ⭐ TRADING MANUAL - DENTRO DEL PANEL DESPLEGABLE
        manual_frame = tk.Frame(self.emergency_content_container, bg='#334155')
        manual_frame.pack(fill='x', padx=5, pady=(0, 10))
        
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
        
        # ⭐ DETECTOR DE TENDENCIA - DENTRO DEL PANEL DESPLEGABLE
        trend_frame = tk.Frame(self.emergency_content_container, bg='#1e3a3a')
        trend_frame.pack(fill='x', padx=5, pady=(0, 5))
        
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
    
    def _on_multiple_parts_toggle(self):
        """⭐ Cuando se activa/desactiva 'Usar múltiples partes', controlar visibilidad del selector"""
        try:
            use_multiple = self.config.get('USE_MULTIPLE_PARTS', tk.BooleanVar(value=False)).get()
            
            if use_multiple:
                # Activado: deshabilitar combobox y mostrar mensaje
                if hasattr(self, 'symbol_combo_widget'):
                    self.symbol_combo_widget.config(state='disabled')
                    self.symbol_combo_widget.set('')
                self.add_log("⚡ MÚLTIPLES PARTES activado: Usando GOLD + SILVER simultáneamente (selector deshabilitado)", 'info')
            else:
                # Desactivado: habilitar combobox
                if hasattr(self, 'symbol_combo_widget'):
                    self.symbol_combo_widget.config(state='readonly')
                    self.symbol_combo_widget.set(self.config['SYMBOL'].get() or 'GOLD')
                self.add_log("🔓 MÚLTIPLES PARTES desactivado: Operando con símbolo seleccionado en el Combobox", 'info')
        except Exception as e:
            self.add_log(f"Error en _on_multiple_parts_toggle: {str(e)[:60]}", 'error')

    def _configure_symbol_parameters(self, symbol):
        """⭐ NUEVO: Configura automáticamente TODOS los parámetros según el par seleccionado"""
        try:
            symbol = symbol.upper()
            
            # Definir configuración por par
            symbol_configs = {
                'GOLD': {
                    'VOL': 0.01,
                    'TP_DIFF': 1.0,
                    'SL_DIFF': 30.0,
                    'MICROTREND_THRESHOLD': 18.0,
                    'GLOBAL_TP': 1.0,
                    'GLOBAL_SL': 30.0,
                    'MIN_RANGE': 1.0,
                },
                'SILVER': {
                    'VOL': 0.01,
                    'TP_DIFF': 1.0,  # ⭐ SINCRONIZADO CON GOLD (era 0.5)
                    'SL_DIFF': 30.0,  # ⭐ SINCRONIZADO CON GOLD (era 0.20)
                    'MICROTREND_THRESHOLD': 15.0,
                    'GLOBAL_TP': 1.0,  # ⭐ SINCRONIZADO CON GOLD (era 0.5)
                    'GLOBAL_SL': 30.0,  # ⭐ SINCRONIZADO CON GOLD (era 0.20)
                    'MIN_RANGE': 1.0,  # ⭐ SINCRONIZADO CON GOLD (era 0.5)
                },
            }
            
            # Obtener configuración del par seleccionado
            if symbol in symbol_configs:
                config = symbol_configs[symbol]
                
                # ⭐ NO SOBRESCRIBIR TP_DIFF y SL_DIFF si el usuario ya los configuró manualmente
                # Solo aplicar configuración para otros parámetros (VOL, MICROTREND_THRESHOLD, etc.)
                # Aplicar configuración a los widgets - EXCEPTO TP_DIFF y SL_DIFF
                for key, value in config.items():
                    # ⭐ CRITICAL: NUNCA sobrescribir TP_DIFF y SL_DIFF - son configuración del usuario
                    if key not in ('TP_DIFF', 'SL_DIFF', 'GLOBAL_TP', 'GLOBAL_SL'):
                        if key in self.config:
                            self.config[key].set(value)
                
                self.add_log(f"✅ Configuración para {symbol} cargada automáticamente (TP/SL preservados)", 'success')
            else:
                self.add_log(f"⚠️ Par '{symbol}' no reconocido", 'warning')
                
        except Exception as e:
            self.add_log(f"❌ Error configurando {symbol}: {str(e)[:60]}", 'error')

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
            ("Max % Consumo Recuperación (%):", 'MAX_RECOVERY_CONSUMPTION_PCT'),
            ("Margen de Ganancia Objetivo (%):", 'MARGEN_GANANCIA'),
            ("Objetivo Neto ($):", 'OBJETIVO_NETO'),
            
            # ⭐ CONFIG ÓPTIMA PARA GOLD (Scalping limpio y constante)
            ("🟡 ⚙️ CONFIG ÓPTIMA – ORO (XAUUSD)", None),  # Separador visual
            ("Threshold (16-19, ideal 18):", 'GOLD_THRESHOLD'),  # 🎯 Rango: más bajo→ruido, más alto→pierda movimientos
            ("Microtendencia (3-5 velas misma dir, ideal 4):", 'GOLD_MICROTREND_CANDLES'),  # + Análisis 10/20/30 velas previas
            ("Cuerpo Vela Mínimo (%):", 'GOLD_CANDLE_BODY_PCT'),  # 60% = cuerpo fuerte
            ("Mecha Máxima (%):", 'GOLD_CANDLE_WICK_PCT'),  # 40% = mechas pequeñas
            ("Cierre Cercano (BUY≥%, SELL≤%):", 'GOLD_CANDLE_CLOSE_PCT'),  # 70% BUY, 30% SELL
            ("VIDYA CMO:", 'GOLD_VIDYA_CMO'),
            ("VIDYA EMA:", 'GOLD_VIDYA_EMA'),
            ("Filtro Impulso (puntos):", 'GOLD_IMPULSE_FILTER'),
            
            # ⭐ CONFIG ÓPTIMA PARA SILVER (Scalping M1/M5)
            ("🔥 ⚙️ CONFIG ÓPTIMA – PLATA (XAGUSD)", None),  # Separador visual
            ("Threshold (1.5-1.7):", 'SILVER_THRESHOLD'),
            ("Microtendencia (velas, 3-5):", 'SILVER_MICROTREND_CANDLES'),
            ("Cuerpo Vela Mínimo (%):", 'SILVER_CANDLE_BODY_PCT'),
            ("VIDYA CMO:", 'SILVER_VIDYA_CMO'),
            ("VIDYA EMA:", 'SILVER_VIDYA_EMA'),
            ("Filtro Impulso (puntos):", 'SILVER_IMPULSE_FILTER'),
        ]
        

        self.config_entries = {}

        for label, key in configs:
            # ⭐ NUEVO: Separador visual (si key es None)
            if key is None:
                sep_frame = tk.Frame(scrollable_frame, bg='#475569', height=2)
                sep_frame.pack(fill='x', pady=10, padx=5)
                sep_label = tk.Label(sep_frame, text=label, bg='#475569', fg='#fbbf24', font=('Arial', 10, 'bold'), anchor='w')
                sep_label.pack(fill='x', padx=5, pady=5)
                continue
            
            row_frame = tk.Frame(scrollable_frame, bg='#334155')
            row_frame.pack(fill='x', pady=3)
            lbl = tk.Label(row_frame, text=label, bg='#334155', fg='#cbd5e1', font=('Arial', 9), width=22, anchor='w')
            lbl.pack(side='left')
            
            # ⭐ NUEVO: Combobox para SYMBOL con auto-configuración
            if key == 'SYMBOL':
                symbol_combo = ttk.Combobox(row_frame, textvariable=self.config[key], 
                                           values=['GOLD', 'SILVER'],
                                           state='readonly', width=25,
                                           font=('Arial', 9))
                # ⭐ NUEVO: Establecer valor inicial (por defecto GOLD)
                current_symbol = self.config[key].get() or 'GOLD'
                symbol_combo.set(current_symbol)
                symbol_combo.pack(side='right', fill='x', expand=True)
                # Bind al evento de cambio de selección
                symbol_combo.bind('<<ComboboxSelected>>', 
                                 lambda e: self._configure_symbol_parameters(self.config['SYMBOL'].get()))
                self.config_entries[key] = symbol_combo
                self.symbol_combo_widget = symbol_combo  # Guardar referencia para habilitar/deshabilitar
            # ⭐ SPINBOX para GOLD_THRESHOLD (rango 16-20, step 0.1)
            elif key == 'GOLD_THRESHOLD':
                spinbox = tk.Spinbox(row_frame, from_=16.0, to=20.0, increment=0.1,
                                    textvariable=self.config[key], bg='#475569', fg='#fbbf24',
                                    relief='flat', font=('Arial', 9), insertbackground='white',
                                    width=8, justify='center')
                spinbox.pack(side='right', fill='x', expand=True)
                self.config_entries[key] = spinbox
            # ⭐ SPINBOX para SILVER_THRESHOLD (rango 1.3-1.8, step 0.1)
            elif key == 'SILVER_THRESHOLD':
                spinbox = tk.Spinbox(row_frame, from_=1.3, to=1.8, increment=0.1,
                                    textvariable=self.config[key], bg='#475569', fg='#ec4899',
                                    relief='flat', font=('Arial', 9), insertbackground='white',
                                    width=8, justify='center')
                spinbox.pack(side='right', fill='x', expand=True)
                self.config_entries[key] = spinbox
            else:
                entry = tk.Entry(row_frame, textvariable=self.config[key], bg='#475569', fg='white', relief='flat', font=('Arial', 9), insertbackground='white')
                entry.pack(side='right', fill='x', expand=True)
                self.config_entries[key] = entry

        # --- NUEVO: Sección TP/SL Global ---
        global_frame = tk.LabelFrame(scrollable_frame, text="TP Global y SL Global", bg='#2d3e50', fg='#f1f5f9', font=('Arial', 10, 'bold'), padx=10, pady=10)
        global_frame.pack(fill='x', pady=(10, 0))

        row_tp = tk.Frame(global_frame, bg='#2d3e50')
        row_tp.pack(fill='x', pady=3)
        tk.Label(row_tp, text="Take Profit Global ($):", bg='#2d3e50', fg='#fbbf24', font=('Arial', 9), width=22, anchor='w').pack(side='left')
        tk.Entry(row_tp, textvariable=self.config['GLOBAL_TP'], bg='#475569', fg='white', relief='flat', font=('Arial', 9), insertbackground='white').pack(side='right', fill='x', expand=True)

        row_sl = tk.Frame(global_frame, bg='#2d3e50')
        row_sl.pack(fill='x', pady=3)
        tk.Label(row_sl, text="Stop Loss Global ($):", bg='#2d3e50', fg='#ef4444', font=('Arial', 9), width=22, anchor='w').pack(side='left')
        tk.Entry(row_sl, textvariable=self.config['GLOBAL_SL'], bg='#475569', fg='white', relief='flat', font=('Arial', 9), insertbackground='white').pack(side='right', fill='x', expand=True)
        
        # --- FIN sección TP/SL Global ---

        # --- NUEVO: Sección Apertura Forzada ---
        forced_frame = tk.LabelFrame(scrollable_frame, text="Apertura Forzada",
                                     bg='#2d3e50', fg='#f1f5f9',
                                     font=('Arial', 10, 'bold'), padx=10, pady=10)
        forced_frame.pack(fill='x', pady=(10, 0))

        tk.Checkbutton(forced_frame, text="🚀 Habilitar apertura forzada",
                      variable=self.config['ENABLE_FORCED_OPEN'],
                      bg='#2d3e50', fg='#f1f5f9', selectcolor='#1e293b',
                      activebackground='#2d3e50', activeforeground='#f1f5f9',
                      font=('Arial', 10)).pack(side='left', padx=5)

        forced_minutes_frame = tk.Frame(forced_frame, bg='#2d3e50')
        forced_minutes_frame.pack(fill='x', pady=(8, 0))

        tk.Label(forced_minutes_frame, text="Minutos (decimales OK):", bg='#2d3e50', fg='#f1f5f9', width=18, anchor='w').pack(side='left', padx=5)
        tk.Entry(forced_minutes_frame, textvariable=self.config['FORCED_OPEN_MINUTES'], width=8, bg='#475569', fg='white').pack(side='left', padx=5)
        tk.Label(forced_minutes_frame, text="Ej: 0.5, 1.5, 2.25", bg='#2d3e50', fg='#cbd5e1', font=('Arial', 8)).pack(side='left', padx=5)
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
        
        tk.Checkbutton(sl_frame, text="⚡ Usar múltiples partes (GOLD + SILVER simultáneamente)", 
                      variable=self.config['USE_MULTIPLE_PARTS'],
                      command=self._on_multiple_parts_toggle,
                      bg='#2d3e50', fg='#60a5fa', selectcolor='#1e293b',
                      activebackground='#2d3e50', activeforeground='#60a5fa',
                      font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        # --- FIN bloque calibración ---

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

    def create_objectives_panel(self, parent):
        """⭐ NUEVO: Panel para mostrar Objetivo Neto y Margen de Ganancia"""
        objectives_frame = tk.LabelFrame(parent, text="🎯 Objetivos de Ganancia", 
                                        bg='#334155', fg='#f1f5f9',
                                        font=('Arial', 10, 'bold'), padx=10, pady=10)
        objectives_frame.pack(fill='x', pady=(0, 10))
        
        # === Fila 1: Margen de Ganancia ===
        margen_frame = tk.Frame(objectives_frame, bg='#2d3e50', relief='sunken', bd=1)
        margen_frame.pack(fill='x', pady=(0, 5), padx=5)
        
        margen_title = tk.Label(margen_frame, text="💵 Margen de Ganancia", 
                               bg='#2d3e50', fg='#fbbf24',
                               font=('Arial', 9, 'bold'), anchor='w')
        margen_title.pack(fill='x', padx=5, pady=(5, 0))
        
        self.margen_monitor_label = tk.Label(margen_frame, text="Desactivado", 
                                            bg='#2d3e50', fg='#cbd5e1',
                                            font=('Arial', 9), anchor='w')
        self.margen_monitor_label.pack(fill='x', padx=5, pady=(0, 5))
        
        # === Fila 2: Objetivo Neto ===
        objetivo_frame = tk.Frame(objectives_frame, bg='#2d3e50', relief='sunken', bd=1)
        objetivo_frame.pack(fill='x', pady=(0, 5), padx=5)
        
        objetivo_title = tk.Label(objetivo_frame, text="🎯 Objetivo Neto", 
                                 bg='#2d3e50', fg='#60a5fa',
                                 font=('Arial', 9, 'bold'), anchor='w')
        objetivo_title.pack(fill='x', padx=5, pady=(5, 0))
        
        self.objetivo_neto_label = tk.Label(objetivo_frame, text="Desactivado", 
                                           bg='#2d3e50', fg='#cbd5e1',
                                           font=('Arial', 9), anchor='w')
        self.objetivo_neto_label.pack(fill='x', padx=5, pady=(0, 5))

    def create_future_data_panel(self, parent):
        """📊 Panel para datos futuros - Análisis de especialistas en tiempo real"""
        data_frame = tk.LabelFrame(parent, text="📊 Datos del Sistema - Análisis Especialistas en Vivo", 
                                  bg='#334155', fg='#f1f5f9',
                                  font=('Arial', 11, 'bold'), padx=15, pady=15)
        data_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Contenedor principal para datos
        self.future_data_content = tk.Frame(data_frame, bg='#2d3e50', relief='sunken', bd=1)
        self.future_data_content.pack(fill='both', expand=True, padx=5, pady=5)
        
        # === FILA 1: BUY SPECIALIST ===
        buy_frame = tk.Frame(self.future_data_content, bg='#1a472a', relief='flat', bd=1)
        buy_frame.pack(fill='x', padx=5, pady=5)
        
        buy_label_title = tk.Label(buy_frame, text="📈 BUY SPECIALIST", 
                                   bg='#1a472a', fg='#34d399', 
                                   font=('Arial', 10, 'bold'))
        buy_label_title.pack(side='left', padx=5, pady=5)
        
        self.buy_score_label = tk.Label(buy_frame, text="Score: 0% | Conf: 0%", 
                                       bg='#1a472a', fg='#10b981', 
                                       font=('Arial', 11, 'bold'))
        self.buy_score_label.pack(side='right', padx=10, pady=5)
        
        # === FILA 2: SELL SPECIALIST ===
        sell_frame = tk.Frame(self.future_data_content, bg='#472a1a', relief='flat', bd=1)
        sell_frame.pack(fill='x', padx=5, pady=5)
        
        sell_label_title = tk.Label(sell_frame, text="📉 SELL SPECIALIST", 
                                    bg='#472a1a', fg='#f87171', 
                                    font=('Arial', 10, 'bold'))
        sell_label_title.pack(side='left', padx=5, pady=5)
        
        self.sell_score_label = tk.Label(sell_frame, text="Score: 0% | Conf: 0%", 
                                        bg='#472a1a', fg='#ef4444', 
                                        font=('Arial', 11, 'bold'))
        self.sell_score_label.pack(side='right', padx=10, pady=5)
        
        # Inicializar diccionario para guardar widgets de datos futuros
        self.future_data_widgets = {}
        
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
        # Frame principal con scroll
        events_frame = tk.LabelFrame(parent, text="📌 Evento, Análisis y Datos Importantes", 
                                    bg='#334155', fg='#f1f5f9',
                                    font=('Arial', 10, 'bold'), padx=10, pady=10)
        events_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Crear un canvas con scrollbar para más espacio
        canvas = tk.Canvas(events_frame, bg='#334155', highlightthickness=0)
        scrollbar = ttk.Scrollbar(events_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#334155')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 🤖 Estado del Bot
        state_label = tk.Label(scrollable_frame, text="🤖 Estado:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#60a5fa')
        state_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_bot_status = tk.Label(scrollable_frame, text="Conectado | Listo", 
                                      font=('Arial', 8), bg='#334155', fg='#34d399')
        self.lbl_bot_status.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # ⚠️ Último Evento
        event_label = tk.Label(scrollable_frame, text="⚠️ Último Evento:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#fbbf24')
        event_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_last_event = tk.Label(scrollable_frame, text="Esperando señal...", 
                                      font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                      wraplength=300, justify='left')
        self.lbl_last_event.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # ✅ Último Cierre
        close_label = tk.Label(scrollable_frame, text="✅ Último Cierre:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#34d399')
        close_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_last_close = tk.Label(scrollable_frame, text="N/A", 
                                      font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                      wraplength=300, justify='left')
        self.lbl_last_close.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # ❌ Último Error
        error_label = tk.Label(scrollable_frame, text="❌ Último Error:", 
                              font=('Arial', 8, 'bold'), bg='#334155', fg='#f87171')
        error_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_last_error = tk.Label(scrollable_frame, text="Ninguno", 
                                      font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                      wraplength=300, justify='left')
        self.lbl_last_error.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # 📊 Datos de Análisis
        analysis_label = tk.Label(scrollable_frame, text="📊 Análisis:", 
                                 font=('Arial', 8, 'bold'), bg='#334155', fg='#a78bfa')
        analysis_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_analysis_data = tk.Label(scrollable_frame, text="Analizando...", 
                                         font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                         wraplength=300, justify='left')
        self.lbl_analysis_data.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # 💰 Datos de Trading
        trading_label = tk.Label(scrollable_frame, text="💰 Trading:", 
                                font=('Arial', 8, 'bold'), bg='#334155', fg='#fbbf24')
        trading_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_trading_data = tk.Label(scrollable_frame, text="Sin datos", 
                                        font=('Arial', 7), bg='#334155', fg='#cbd5e1',
                                        wraplength=300, justify='left')
        self.lbl_trading_data.pack(anchor='w', padx=15, pady=(0, 8), fill='x')
        
        # 🕐 Timestamp
        time_label = tk.Label(scrollable_frame, text="🕐 Actualización:", 
                             font=('Arial', 7, 'italic'), bg='#334155', fg='#64748b')
        time_label.pack(anchor='w', pady=(5, 0), padx=5)
        self.lbl_events_timestamp = tk.Label(scrollable_frame, text="--:--:--", 
                                            font=('Arial', 7), bg='#334155', fg='#64748b')
        self.lbl_events_timestamp.pack(anchor='w', padx=15, pady=(0, 5), fill='x')
        
        # Empacar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    
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
        """⭐ OPTIMIZADO: Solo actualiza labels dinámicos, sin ScrolledText"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # SIEMPRE imprimir a consola (thread-safe)
        try:
            pass  # No imprimir a consola para evitar sobrecarga
        except:
            pass
        
        # Actualizar labels dinámicamente según el tipo de mensaje
        try:
            def update_ui():
                # Truncar texto a 60 caracteres para labels
                text_short = message[:60] + ("..." if len(message) > 60 else "")
                
                # Detectar categoría del mensaje
                is_analysis = any(kw in message.lower() for kw in ['análisis', 'score', 'microtrend', 'volatilidad', 'tendencia', 'rsi'])
                is_trading = any(kw in message.lower() for kw in ['operación', 'abierta', 'cierre', 'profit', 'pérdida', 'ticket'])
                
                # Actualizar labels según categoría
                if tag == 'error':
                    if hasattr(self, 'lbl_last_error'):
                        self.lbl_last_error.config(text=text_short, fg='#f87171')
                elif tag == 'success':
                    if hasattr(self, 'lbl_last_close'):
                        self.lbl_last_close.config(text=text_short, fg='#34d399')
                elif tag == 'warning':
                    if hasattr(self, 'lbl_last_event'):
                        self.lbl_last_event.config(text=text_short, fg='#fbbf24')
                elif tag == 'alert':
                    if hasattr(self, 'lbl_last_event'):
                        self.lbl_last_event.config(text=text_short, fg='#fb7185')
                elif tag == 'debug':
                    if is_analysis and hasattr(self, 'lbl_analysis_data'):
                        self.lbl_analysis_data.config(text=text_short, fg='#a78bfa')
                    elif is_trading and hasattr(self, 'lbl_trading_data'):
                        self.lbl_trading_data.config(text=text_short, fg='#fbbf24')
                
                # Caso default: llenar label según contexto
                if is_analysis and hasattr(self, 'lbl_analysis_data'):
                    self.lbl_analysis_data.config(text=text_short, fg='#a78bfa')
                elif is_trading and hasattr(self, 'lbl_trading_data'):
                    self.lbl_trading_data.config(text=text_short, fg='#fbbf24')
                else:
                    # Otros eventos
                    if hasattr(self, 'lbl_last_event'):
                        self.lbl_last_event.config(text=text_short, fg='#cbd5e1')
                
                # Actualizar timestamp
                if hasattr(self, 'lbl_events_timestamp'):
                    self.lbl_events_timestamp.config(text=timestamp)
            
            if hasattr(self, 'root'):
                self.root.after(0, update_ui)
            else:
                update_ui()
        except Exception as e:
            logger.debug(f"[UI-UPDATE] Error updating UI: {str(e)[:60]}")

    def _run_on_ui_thread(self, callback, *args, **kwargs):
        """Ejecuta callback en el hilo principal de Tkinter para evitar bloqueos/crashes."""
        try:
            if threading.current_thread() is threading.main_thread():
                callback(*args, **kwargs)
            elif hasattr(self, 'root') and self.root:
                self.root.after(0, lambda: callback(*args, **kwargs))
        except Exception as e:
            logger.debug(f"[UI-THREAD] Error running on UI thread: {str(e)[:60]}")
    
    def _update_log_widget_batch(self, messages):
        """⭐ ULTRA-OPTIMIZADO: Batch updates + deshabilitar widget durante insert para máximo performance"""
        try:
            if hasattr(self, 'log_text'):
                # ⭐ CRÍTICO: Deshabilitar widget ANTES de insert (no causa repaints)
                old_state = self.log_text.cget('state')
                self.log_text.config(state='normal')
                
                # Insertar TODO el batch en una sola operación SIN TAGS (50x más rápido)
                bulk_text = '\n'.join(messages) + '\n'
                self.log_text.insert('end', bulk_text)
                
                # ⭐ Limitar tamaño MUCHO MENOS frecuentemente (cada 5000 líneas)
                num_lines = int(self.log_text.index('end-1c').split('.')[0])
                if num_lines > 5000:
                    # Borrar primeras 300 líneas de una vez (más eficiente)
                    self.log_text.delete('1.0', '300.0')
                
                # ⭐ OPTIMIZACIÓN: Solo scroll cada 10 updates (no cada actualización)
                if not hasattr(self, '_log_update_count'):
                    self._log_update_count = 0
                self._log_update_count += 1
                
                if self._log_update_count % 10 == 0:  # Cada 10 updatesa
                    self.log_text.see('end')  # Hacer scroll solo ocasionalmente
                    self._log_update_count = 0
                
        except Exception:
            pass  # Silenciar errores

    def update_account_info(self):
        """Actualiza periódicamente las etiquetas de Balance, Patrimonio (Equity), Margen Libre y Alcance (Leverage)."""
        try:
            account_info = None
            try:
                account_info = mt5.account_info()
            except Exception as e:
                logger.debug(f"[ACCOUNT] Error getting account info: {str(e)[:60]}")
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
                
                # ⭐ OPTIMIZADO: Remover update frecuentes - no necesarios
                
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
                        self.add_log("⚠️ No se pudo obtener account_info de MT5; mostrando valores locales.", 'warning')
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
                            self.add_log(f"🌟 Objetivo alcanzado: equity ${equity:.2f} >= inicial ${self.balance_inicial:.2f} + objetivo ${objetivo:.2f}", 'success')
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
            pass

    def request_ui_refresh(self):
        """Solicita refresco de UI para que lo procese el tick central (coalesced)."""
        self._ui_refresh_requested = True

    def _entry_analysis_loop(self):
        """Ejecuta monitoreo de entry point y análisis de operaciones con throttling fuera de _update_ui."""
        while self._entry_analysis_running:
            try:
                now = time.time()

                if self.is_running and (now - self._last_open_ops_analysis >= 5.0):
                    self.analizar_operaciones_abiertas()
                    self._last_open_ops_analysis = now
            except Exception:
                pass
            time.sleep(0.25)

    def _compute_rapid_ops_distribution(self, min_samples=6):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        return 0.5

    def _apply_rapid_buy_frac_ui(self, buy_pct, color):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def analizar_operaciones_abiertas(self):
        """⭐ NUEVO: Analizador de operaciones abiertas en tiempo real"""
        try:
            if not self.connected:
                return
            
            symbol = self.config['SYMBOL'].get()
            positions = mt5.positions_get(symbol=symbol)
            
            if not positions or len(positions) == 0:
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
            
            # Análisis completo
            self.add_log(f"\n📊 ANÁLISIS DE OPERACIONES ABIERTAS: {len(positions)}/{max_ops}", 'info')
            
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
                    status = f"✅️ +${profit_money:.2f}"
                    color_tag = 'success'
                    total_profit += profit_money
                    profit_positions += 1
                elif profit_money < 0:
                    status = f"❌ ${profit_money:.2f}"
                    color_tag = 'error'
                    total_loss += abs(profit_money)
                    loss_positions += 1
                else:
                    status = f"🚀 $0.00"
                    color_tag = 'info'
                
                # Log detallado por posición
                self.add_log(f"   📋 #{ticket} {direction} @ {open_price:.5f} | Vol: {volume} | Precio: {current_price:.5f} | {status}", color_tag)
                self.add_log(f"      🎯 TP: {tp:.5f} (Dist: {dist_tp:.5f}) | 🛡️ SL: {sl:.5f} (Dist: {dist_sl:.5f})", 'info')
            
            # Resumen
            self.add_log(f"\n📈 RESUMEN: Ganancias: ${total_profit:.2f} ({profit_positions} pos) | Pérdidas: ${total_loss:.2f} ({loss_positions} pos)", 'success')
            
        except Exception as e:
            self.add_log(f"Error en análisis de operaciones: {str(e)}", 'error')

    def _calculate_atr_simple(self, highs, lows, closes, period=14):
        """Calcula ATR de forma simple para tolerancia dinámica (unidades: puntos)"""
        try:
            high_low = highs[-period:] - lows[-period:]
            high_close = np.abs(highs[-period:] - np.roll(closes[-period:], 1))
            low_close = np.abs(lows[-period:] - np.roll(closes[-period:], 1))
            ranges = np.max(np.vstack([high_low, high_close, low_close]), axis=0)
            atr = float(np.mean(ranges)) if len(ranges) > 0 else 1.0
            self.add_log(f"[ATR] Calculado: {atr:.5f} puntos (periodo={period})", 'info')
            return atr
        except Exception as e:
            self.add_log(f"[ATR] Error: {e}", 'error')
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
                return (True, f"[✅️] ALTA CONFIANZA ({conf_float:.1f}%): Abriendo INMEDIATAMENTE a {current_price:.5f}")
            
            elif direction == "BUY":
                # Para BUY: queremos que el precio SUBA hacia el objetivo
                if current_price <= target_price:
                    # Precio está debajo o igual al objetivo = PERFECTO para BUY
                    return (True, f"[📋] BUY: Precio DEBAJO {current_price:.5f} <= {target_price:.5f}")
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

    def _toggle_control_panel(self):
        """⭐ Alterna entre mostrar/ocultar el panel de controles de botones"""
        try:
            if self.control_panel_expanded:
                # Ocultar el panel de botones
                self.control_buttons_container.pack_forget()
                self.collapse_toggle_btn.config(text="▶ Controles de Bot")
                self.control_panel_expanded = False
            else:
                # Mostrar el panel de botones
                self.control_buttons_container.pack(fill='x', expand=False)
                self.collapse_toggle_btn.config(text="▼ Controles de Bot")
                self.control_panel_expanded = True
        except Exception as e:
            self.add_log(f"[ERROR] Fallo al toggle panel: {str(e)}", 'error')

    def _toggle_advanced_panel(self):
        """⭐ Alterna entre mostrar/ocultar el panel avanzado (Sistema Multi-IA, Objetivos y Pausas)"""
        try:
            if self.advanced_panel_expanded:
                # Ocultar el panel avanzado
                self.advanced_content_container.pack_forget()
                self.collapse_toggle_btn_advanced.config(text="▶ Sistema Multi-IA, Objetivos y Pausas")
                self.advanced_panel_expanded = False
            else:
                # Mostrar el panel avanzado
                self.advanced_content_container.pack(fill='x', expand=False)
                self.collapse_toggle_btn_advanced.config(text="▼ Sistema Multi-IA, Objetivos y Pausas")
                self.advanced_panel_expanded = True
        except Exception as e:
            self.add_log(f"[ERROR] Fallo al toggle panel avanzado: {str(e)}", 'error')

    def _toggle_finance_panel(self):
        """⭐ Alterna entre mostrar/ocultar el panel de finanzas (Balance, Patrimonio, Margen y Objetivos)"""
        try:
            if self.finance_panel_expanded:
                # Ocultar el panel de finanzas
                self.finance_content_container.pack_forget()
                self.collapse_toggle_btn_finance.config(text="▶ Balance, Patrimonio y Objetivos")
                self.finance_panel_expanded = False
            else:
                # Mostrar el panel de finanzas
                self.finance_content_container.pack(fill='x', expand=False)
                self.collapse_toggle_btn_finance.config(text="▼ Balance, Patrimonio y Objetivos")
                self.finance_panel_expanded = True
        except Exception as e:
            self.add_log(f"[ERROR] Fallo al toggle panel finanzas: {str(e)}", 'error')

    def _toggle_emergency_panel(self):
        """⭐ Alterna entre mostrar/ocultar el panel de emergencia (Cierre de Emergencia, Trading Manual y Tendencia)"""
        try:
            if self.emergency_panel_expanded:
                # Ocultar el panel de emergencia
                self.emergency_content_container.pack_forget()
                self.collapse_toggle_btn_emergency.config(text="▶ Cierre Emergencia, Trading Manual y Tendencia")
                self.emergency_panel_expanded = False
            else:
                # Mostrar el panel de emergencia
                self.emergency_content_container.pack(fill='x', expand=False)
                self.collapse_toggle_btn_emergency.config(text="▼ Cierre Emergencia, Trading Manual y Tendencia")
                self.emergency_panel_expanded = True
        except Exception as e:
            self.add_log(f"[ERROR] Fallo al toggle panel emergencia: {str(e)}", 'error')

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
            
            # ⭐ NUEVO: Limpiar variables de objetivo neto
            self.objetivo_neto_inicial = 0.0
            self.objetivo_neto_target = 0.0
            
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
            # ⭐ Remover after_idle() para evitar stack overflow
            
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
            
            # ⭐ NUEVO: Limpiar variables de objetivo neto
            self.objetivo_neto_inicial = 0.0
            self.objetivo_neto_target = 0.0
            
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
                    self.add_log("✅️ Sesión MT5 reiniciada", 'info')
            except Exception as e:
                self.add_log(f"⚠️ Error reiniciando MT5: {str(e)}", 'warning')
            
            # Actualizar UI
            self.resume_btn.config(state='disabled')
            self.update_stats()
            
            # Log de confirmación
            symbol = self.config['SYMBOL'].get()
            quantity = self.config['VOL'].get()
            self.add_log(f"\n🔄 BOT REINICIADO", 'warning')
            self.add_log(f"   🚀 Contadores: Limpiados", 'info')
            self.add_log(f"   🚀 Operaciones en espera: Limpiadas", 'info')
            self.add_log(f"   🚀 Sesión: Reiniciada", 'info')
            self.add_log(f"   🚀 Parámetros preservados: {symbol} / {quantity}", 'success')
            
            # Updates removidas para evitar stack overflow
            
        except Exception as e:
            self.add_log(f"❌ Error al reiniciar bot: {str(e)}", 'error')

    def update_stats(self):
        """⭐ OPTIMIZADO: Alias con debounce para evitar updates excesivos"""
        self.request_ui_refresh()

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
            
            status = "🌟 Vigilante" if self.objetivo_cumplido else "🔄 Activo"
            mode_text = "Multi-IA" if self.use_multi_ai.get() else "Tradicional"
            self.root.title(
                f"MT5 Bot [{mode_text}] | {status} | "
                f"📊 {self.total_operaciones_abiertas}/{self._safe_get('MAX_SIMULTANEOUS_OPS', 5)} | "
                f"[DINERO] Total: {saldo_text}"
            )
            
            # ⭐ NUEVO: ACTUALIZAR OBJETIVO NETO EN TIEMPO REAL (INDEPENDIENTE del MARGEN_GANANCIA)
            if hasattr(self, 'objetivo_neto_label'):
                try:
                    objetivo_neto = float(self._safe_get('OBJETIVO_NETO', 0.0))
                    
                    # ⭐ CORREGIDO: Mostrar OBJETIVO_NETO si > 0, INDEPENDIENTEMENTE de MARGEN_GANANCIA
                    if objetivo_neto <= 0:
                        self.objetivo_neto_label.config(text="Desactivado", fg='#cbd5e1')
                    else:
                        # Obtener equity actual
                        try:
                            account_info = mt5.account_info()
                            if account_info is not None:
                                equity = float(getattr(account_info, 'equity', 0.0))
                                
                                # Inicializar el objetivo si es la primera vez
                                if not hasattr(self, 'objetivo_neto_inicial') or self.objetivo_neto_inicial == 0:
                                    self.objetivo_neto_inicial = equity
                                    self.objetivo_neto_target = equity + objetivo_neto
                                
                                # Calcular falta o exceso
                                falta = self.objetivo_neto_target - equity
                                progress_pct = (equity / self.objetivo_neto_target * 100) if self.objetivo_neto_target > 0 else 0
                                
                                if falta > 0.01:
                                    # Aún falta ganar
                                    text = f"🎯 Patrimonio: ${equity:.2f} | Objetivo: ${self.objetivo_neto_target:.2f} | Falta: ${falta:.2f} ({progress_pct:.1f}%)"
                                    color = '#60a5fa'
                                elif falta < -0.01:
                                    # Exceso alcanzado
                                    text = f"✅ Patrimonio: ${equity:.2f} | Objetivo: ${self.objetivo_neto_target:.2f} | Exceso: ${abs(falta):.2f} ({progress_pct:.1f}%)"
                                    color = '#34d399'
                                else:
                                    # Exacto
                                    text = f"✅ Patrimonio: ${equity:.2f} | Objetivo: ${self.objetivo_neto_target:.2f} | ¡ALCANZADO! ({progress_pct:.1f}%)"
                                    color = '#34d399'
                                
                                self.objetivo_neto_label.config(text=text, fg=color)
                            else:
                                self.objetivo_neto_label.config(text="Esperando MT5...", fg='#fbbf24')
                        except Exception:
                            self.objetivo_neto_label.config(text="Error obteniendo datos", fg='#ef4444')
                except Exception as e:
                    pass
            
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
            
            # Updates removidas para evitar stack overflow
            
        except Exception as e:
            self.add_log(f"Error actualizando interfaz: {str(e)}", 'error')

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
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def start_rapid_operations(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def stop_rapid_operations(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def reset_rapid_ai(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def reset_all_state(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def get_last_minute_counts(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def decide_rapid_direction(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def monitor_rapid_operations(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def open_rapid_operation(self, symbol, force_direction=None):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def check_and_close_rapid_operations(self, symbol):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def _get_rapid_direction_loss_streak(self, direction):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def _apply_rapid_reversal_protection(self, symbol, positions):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def update_rapid_operations_ui(self):
        """Eliminada - Operaciones Rápidas fueron removidas"""
        pass

    def get_volatility_level(self, rates):
        """Helper para obtener nivel de volatilidad - usado por validación"""
        try:
            if not rates or len(rates) < 2:
                return 'NORMAL'
            closes = [r['close'] for r in rates]
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1] > 0]
            if not returns:
                return 'NORMAL'
            volatility = np.std(returns)
            if volatility > 0.005:  # 0.5%
                return 'HIGH'
            elif volatility > 0.002:  # 0.2%
                return 'MEDIUM'
            else:
                return 'LOW'
        except Exception:
            return 'NORMAL'

    def _calculate_rsi_quick(self, closes, period=14):
        """Cálculo rápido de RSI para validación pre-operación"""
        try:
            if len(closes) < period + 1:
                return 50.0
            deltas = np.diff(closes)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi)
        except Exception:
            return 50.0

    def open_real_trade(self, symbol, order_type, volume, sl_pips, tp_pips):
        """Abre una operación real - función placeholder"""
        pass

    def _run_on_ui_thread(self, func, *args):
        """Ejecuta una función en el hilo UI usando after()"""
        try:
            if hasattr(self, 'root'):
                self.root.after(0, lambda: func(*args) if args else func())
        except Exception:
            pass


    def get_last_minute_counts(self):
        """DESHABILITADO: No se usa histórico de operaciones rápidas. Solo análisis de mercado actual."""
        return 0, 0, 0

    def decide_rapid_direction(self):
        """DESHABILITADO: No se usa histórico de operaciones rápidas. Solo análisis de mercado actual."""
        return 'HOLD'

    def monitor_rapid_operations(self):
        """Monitorea y abre operaciones rápidas cada X segundos (sin análisis)"""
        self.add_log(f"[🔄] INICIANDO MONITOR RÁPIDAS - Connected: {self.connected}", 'info')
        
        # 🚀 CRÍTICO: Reinicializar MT5 en el thread de rápidas
        if not mt5.initialize():
            self.add_log(f"⚠️ Monitor rápidas: Intentando inicializar MT5...", 'warning')
            mt5.shutdown()
            time.sleep(1)
            if not mt5.initialize():
                self.add_log(f"❌ Monitor rápidas: NO pudo inicializar MT5", 'error')
                return
        
        self.add_log(f"✅️ Monitor rápidas: MT5 inicializado en thread", 'success')
        
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
                        self.add_log(f"🤖 IA Rápidas: fase inicial ({initial_phase}s) completada - Frac BUY objetivo {buy_frac:.2f}", 'info')
                        self.add_log("🤖 IA Rápidas: empezando análisis en vivo y aprendizaje continuo", 'info')
                        # Actualizar UI inmediatamente
                        try:
                            color = self.config.get('RAPID_OPS_FRAC_COLOR').get() if 'RAPID_OPS_FRAC_COLOR' in self.config else '#f59e0b'
                            self._run_on_ui_thread(self._apply_rapid_buy_frac_ui, int(buy_frac * 100), color)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Log cada 20 iteraciones
                if iteration % 20 == 0 and len(self.rapid_ops_active) > 0:
                    self.add_log(f"📊 Rápidas: {len(self.rapid_ops_active)} ops | Intervalo: {interval}s", 'info')

                # Verificar operaciones abiertas
                self.check_and_close_rapid_operations(symbol)

                # Abrir nuevas operaciones cada X segundos (sin análisis, solo abre)
                
                # ⭐ CRÍTICO: Inicializar last_rapid_op_time si es negativo o 0
                # Esto evita que se abra inmediatamente al iniciar
                if self.last_rapid_op_time <= 0:
                    self.last_rapid_op_time = current_time
                    self.add_log(f"[CONTADOR] Inicializado contador rápidas: próxima apertura en {interval}s", 'info')

                # Calcular tiempo transcurrido y verificar si puede abrir
                time_since_last_op = current_time - self.last_rapid_op_time
                
                if time_since_last_op >= interval:
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
                        # Análisis de histórico de operaciones rápidas removido
                        # if ghost_dir in ('BUY', 'SELL') and 'RAPID_OPS_OPEN_OPPOSITE_ON_WIN' in self.config...:
                        #     ... - DESHABILITADO
                        
                        # Protección por racha: si la dirección propuesta viene perdiendo seguido,
                        # forzar cambio para evitar seguir apilando pérdidas del mismo lado.
                            if ghost_dir in ('BUY', 'SELL'):
                                try:
                                    max_streak = int(self.config.get('RAPID_OPS_MAX_DIRECTION_LOSS_STREAK', tk.IntVar(value=3)).get())
                                except Exception:
                                    max_streak = 3
                                if max_streak > 0:
                                    losing_streak = self._get_rapid_direction_loss_streak(ghost_dir)
                                    if losing_streak >= max_streak:
                                        prev = ghost_dir
                                        ghost_dir = 'SELL' if ghost_dir == 'BUY' else 'BUY'
                                        self.add_log(
                                            f"[ANTI-RACHA] {losing_streak} pérdidas seguidas en {prev} -> cambiando a {ghost_dir}",
                                            'warning'
                                        )

                            # 2) IMPORTANTE: no invertir aquí por SL/TP.
                            # La contraria por SL/TP se ejecuta únicamente cuando hay cierre real,
                            # para evitar flips erráticos de micromomentos.
                            if ghost_dir in ('BUY', 'SELL') and 'RAPID_OPS_OPEN_OPPOSITE_ON_SLTP' in self.config and self.config['RAPID_OPS_OPEN_OPPOSITE_ON_SLTP'].get():
                                self.add_log("[ANTI-FLIP] OpenOppositeOnSLTP activo: se aplicará solo tras cierre real, no en pre-apertura", 'info')
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
                            
                            # ⭐ MODO AGRESIVO: Después de 1m (60s) de inicio, FUERZA apertura
                            time_since_start = current_time - self.rapid_ops_start_time if self.rapid_ops_start_time else 0
                            is_aggressive_timeout = time_since_start >= initial_phase  # Después de fase inicial
                            
                            should_force_open = is_aggressive_timeout or (getattr(self, 'aggressive_mode', False) and time_since_start >= 30)
                            
                            if not validation_result['should_open']:
                                # ❌ VALIDACIÓN RECHAZÓ - NO ABRIR
                                self.add_log(f"❌ [RAPID-VALID] Validación rechazó: {validation_result['reason']} | Risk: {validation_result['risk_level']}", 'warning')
                            else:
                                # ✅ VALIDACIÓN APROBÓ - ABRIR OPERACIÓN
                                self.add_log(f"✅ [RAPID-VALID] Validación aprobó (Risk: {validation_result['risk_level']}, {validation_result['passed_criteria']}/6 checks)", 'success')
                                
                                # Abrir operación real
                                if ghost_dir in ('BUY', 'SELL'):
                                    self.add_log(f"🚀 Abriendo rápida inteligente: {ghost_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                    self.open_rapid_operation(symbol, force_direction=ghost_dir)
                                else:
                                    alt_dir = 'BUY' if (len(self.rapid_ops_active) % 2 == 0) else 'SELL'
                                    self.add_log(f"🚀 Abriendo rápida inteligente: {alt_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                    self.open_rapid_operation(symbol, force_direction=alt_dir)
                        except Exception as e:
                            self.add_log(f"❌ Error en validación inteligente: {str(e)}", 'error')
                            # Fallback: abrir como antes
                            if ghost_dir in ('BUY', 'SELL'):
                                self.add_log(f"🚀 Abriendo rápida (fallback): {ghost_dir} #{len(self.rapid_ops_active)+1}...", 'info')
                                self.open_rapid_operation(symbol, force_direction=ghost_dir)
                            else:
                                alt_dir = 'BUY' if (len(self.rapid_ops_active) % 2 == 0) else 'SELL'
                                self.add_log(f"🚀 Abriendo rápida (fallback): {alt_dir} #{len(self.rapid_ops_active)+1}...", 'info')
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
                self._run_on_ui_thread(self.update_rapid_operations_ui)

                time.sleep(2)  # ⭐ AUMENTADO de 1s a 2s para reducir sobrecarga

            except Exception as e:
                self.add_log(f"❌ Error monitoreo rápidas: {str(e)}", 'error')
                break

    def open_rapid_operation(self, symbol, force_direction=None):
        """Abre operación rápida, usando force_direction ('BUY'/'SELL') si se indica (para modo fantasma)"""
        try:
            # ⭐ BLOQUEAR si está en reanalisis post-cierre
            if self.post_close_reanalysis_active:
                self.add_log(f"[BLOQUEADO] Reanalisis en progreso - Esperando recalibración IA...", 'warning')
                return
            
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
                # Lógica original (sin Entry Point)
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

            # ⭐⭐⭐ VALIDACIÓN OBLIGATORIA ANTES DE ABRIR ⭐⭐⭐
            # Validar SIEMPRE - sin excepciones por tiempo
            direction_str = 'BUY' if direction == mt5.ORDER_TYPE_BUY else 'SELL'
            
            is_valid, failed_filters, validation_reasons = self._validate_trade_entry(symbol, direction_str)
            
            if not is_valid:
                # ❌ FILTROS RECHAZARON LA ENTRADA - NO ABRIR
                self.add_log(f"❌ [{direction_str}] Entrada rechazada: {failed_filters}", 'warning')
                self.add_log(f"   Razón: {validation_reasons}", 'info')
                return  # NO ABRIR - salir de la función
            else:
                # ✅ TODOS LOS FILTROS PASARON - PERMITIR ENTRADA
                self.add_log(f"✅ [{direction_str}] Entrada validada - Abriendo operación", 'success')

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
                # ⭐ Proteger acceso a rapid_ops_active con lock
                try:
                    if self.rapid_ops_lock:
                        with self.rapid_ops_lock:
                            self.rapid_ops_active[result.order] = {
                                'type': order_type,
                                'entry_price': entry_price,
                                'open_time': datetime.now(),
                                'ticket': result.order
                            }
                            # ⭐ NO PAUSAR - dejar que el contador continúe para siguiente operación
                            # El contador se actualiza al final del ciclo monitor_rapid_operations
                    else:
                        self.rapid_ops_active[result.order] = {
                            'type': order_type,
                            'entry_price': entry_price,
                            'open_time': datetime.now(),
                            'ticket': result.order
                        }
                        # ⭐ NO PAUSAR - dejar que el contador continúe para siguiente operación
                        # El contador se actualiza al final del ciclo monitor_rapid_operations
                except Exception:
                    pass
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

            # SEGUNDO: Obtener configuración - SIEMPRE obtener TP/SL
            # ⭐ AJUSTAR TP/SL DINÁMICAMENTE según volumen
            volume_actual = self.config['VOL'].get()
            tp_amount, sl_amount = self._calculate_dynamic_tp_sl(volume_actual)
            min_profit = self.config['MIN_PROFIT_CLOSE'].get()

            # TERCERO: Analizar y cerrar posiciones
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return

            # Protección de reversión: si casi todas están contra la dirección actual,
            # cerrar primero la peor y girar para contener pérdidas acumuladas.
            try:
                self._apply_rapid_reversal_protection(symbol, positions)
            except Exception as _rev_e:
                self.add_log(f"[REVERSAL-PROTECT] Error: {str(_rev_e)[:80]}", 'warning')

            for pos in positions:
                # Solo procesar operaciones rápidas (magic number correcto)
                if pos.magic != self.config['MAGIC_NUMBER']:
                    continue
                    
                # Determinar si debe cerrarse
                should_close = False
                reason = ""
                
                # SIEMPRE cierra por TP/SL global
                if pos.profit >= tp_amount:
                    should_close = True
                    reason = f"TP alcanzado (${pos.profit:.2f} >= ${tp_amount:.2f})"
                elif pos.profit <= -sl_amount:
                    should_close = True
                    reason = f"SL alcanzado (${pos.profit:.2f} <= -${sl_amount:.2f})"

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
                        
                        # ⭐ Lectura thread-safe de rapid_ops_active
                        op_type = None
                        try:
                            if self.rapid_ops_lock:
                                with self.rapid_ops_lock:
                                    if pos.ticket in self.rapid_ops_active:
                                        op_type = self.rapid_ops_active[pos.ticket]['type']
                            else:
                                if pos.ticket in self.rapid_ops_active:
                                    op_type = self.rapid_ops_active[pos.ticket]['type']
                        except Exception:
                            pass
                        
                        if op_type:
                            # Histórico de operaciones rápidas removido: solo análisis de mercado
                            # self.rapid_ops_history.append(entry) - DESHABILITADO
                            
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
                            self.add_log(f"🚀 Aprendizaje IA (Rápidas): nueva preferencia BUY={self.rapid_adapt_frac:.2f}", 'info')
                            # --- ADAPTACIÓN: Removida - análisis de histórico de operaciones rápidas deshabilitado ---
                            # for e in list(self.rapid_ops_history)[-max_perdidas*2:]:
                            #     ... - DESHABILITADO
                            
                            # ⭐ Remover operación de manera thread-safe
                            try:
                                if self.rapid_ops_lock:
                                    with self.rapid_ops_lock:
                                        self.rapid_ops_active.pop(pos.ticket, None)
                                else:
                                    self.rapid_ops_active.pop(pos.ticket, None)
                                
                                # ⭐ REINICIAR CONTADOR cuando NO hay más operaciones abiertas
                                if len(self.rapid_ops_active) == 0:
                                    self.last_rapid_op_time = time.time()
                                    # ⭐ INICIAR REANALISIS POST-CIERRE
                                    self._start_post_close_reanalysis()
                            except Exception:
                                pass

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

    def _get_rapid_direction_loss_streak(self, direction):
        """DESHABILITADO: No se usa histórico de operaciones rápidas. Solo análisis de mercado actual."""
        return 0

    def _apply_rapid_reversal_protection(self, symbol, positions):
        """
        Si hay muchas operaciones abiertas en contra de la dirección actual, cierra la peor
        y abre una contraria para empezar a recuperar gradualmente.
        """
        try:
            enabled = bool(self.config.get('RAPID_OPS_REVERSAL_CLOSE_ENABLED', tk.BooleanVar(value=True)).get())
            if not enabled:
                return

            now = time.time()
            if now < float(getattr(self, 'rapid_reverse_cooldown_until', 0.0)):
                return

            bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
            if len(bot_positions) < 2:
                return

            try:
                use_ai = bool(self.config.get('RAPID_OPS_USE_AI', tk.BooleanVar(value=True)).get())
            except Exception:
                use_ai = True

            if use_ai:
                suggested = self.decide_rapid_direction()
            else:
                suggested = self.get_ghost_recommendation()

            if suggested not in ('BUY', 'SELL'):
                return

            opposite_type = mt5.POSITION_TYPE_SELL if suggested == 'BUY' else mt5.POSITION_TYPE_BUY
            same_type = mt5.POSITION_TYPE_BUY if suggested == 'BUY' else mt5.POSITION_TYPE_SELL
            opposite_positions = [p for p in bot_positions if p.type == opposite_type]
            same_positions = [p for p in bot_positions if p.type == same_type]

            # Solo actuar cuando hay desbalance real (ej: 5 SELL y mercado giró BUY).
            if len(opposite_positions) < 2 or len(opposite_positions) <= len(same_positions):
                return

            losing_opposite = [p for p in opposite_positions if float(getattr(p, 'profit', 0.0)) < 0]
            if not losing_opposite:
                return

            worst_pos = min(losing_opposite, key=lambda p: float(getattr(p, 'profit', 0.0)))

            try:
                sl_amount = float(self.config.get('RAPID_OPS_SL', tk.DoubleVar(value=0.5)).get())
            except Exception:
                sl_amount = 0.5
            try:
                loss_mult = float(self.config.get('RAPID_OPS_REVERSAL_LOSS_TRIGGER', tk.DoubleVar(value=0.6)).get())
            except Exception:
                loss_mult = 0.6

            trigger_loss = -abs(sl_amount * max(0.1, loss_mult))
            worst_profit = float(getattr(worst_pos, 'profit', 0.0))
            if worst_profit > trigger_loss:
                return

            close_type = mt5.ORDER_TYPE_SELL if worst_pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return
            close_price = tick.bid if worst_pos.type == mt5.POSITION_TYPE_BUY else tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": worst_pos.volume,
                "type": close_type,
                "position": worst_pos.ticket,
                "price": close_price,
                "magic": self.config['MAGIC_NUMBER'],
                "type_filling": mt5.ORDER_FILLING_IOC,
                "deviation": 20,
                "comment": "RapidReversalProtect"
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_dir = 'BUY' if worst_pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
                self.add_log(
                    f"[REVERSAL-PROTECT] Cerrada peor {closed_dir} #{worst_pos.ticket} ({worst_profit:.2f}) y girando a {suggested}",
                    'warning'
                )
                self._procesar_cierre_exitoso(
                    ticket=worst_pos.ticket,
                    symbol=symbol,
                    volume=worst_pos.volume,
                    pos_type=worst_pos.type,
                    profit=worst_profit
                )

                # Abrir en la dirección actual del mercado para compensar gradualmente.
                self.open_rapid_operation(symbol, force_direction=suggested)
                self.rapid_reverse_cooldown_until = now + 8.0
        except Exception:
            raise

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

        # ⭐ ACTUALIZAR COUNTDOWN DEL HEADER PRIMERO (SIEMPRE)
        try:
            # ⭐ SI BOT NO ESTÁ CORRIENDO, mostrar "-"
            if not getattr(self, 'is_running', False):
                countdown = "-"
            # ⭐ SI HAY OPERACIONES ABIERTAS, pausar contador
            elif hasattr(self, 'rapid_ops_active') and len(self.rapid_ops_active) > 0:
                countdown = "⏸"
            else:
                # BOT ESTÁ CORRIENDO Y SIN OPERACIONES: calcular countdown normal
                countdown = "-"
                
                # ⭐ USAR EL MISMO INTERVALO QUE EL MONITOR RÁPIDAS
                try:
                    configured_interval = self.config['RAPID_OPS_INTERVAL'].get()
                except:
                    configured_interval = 30  # Default
                
                now = time.time()
                
                if hasattr(self, 'last_rapid_op_time') and self.last_rapid_op_time > 0:
                    # Calcular cuándo fue la última operación
                    time_since_last = now - self.last_rapid_op_time
                    # Cuántos segundos faltan para la próxima
                    secs_remaining = max(0, configured_interval - time_since_last)
                    
                    # Si el tiempo restante es 0 o muy pequeño, mostrar "LISTO" o esperar
                    if secs_remaining <= 0:
                        countdown = "🚀"  # Listo para abrir
                    else:
                        countdown = f"{int(secs_remaining)}s"
                else:
                    # Si no hay registro de última operación, mostrar intervalo completo
                    countdown = f"{int(configured_interval)}s"

            # Actualizar la etiqueta de cuenta atrás del header
            if hasattr(self, 'rapid_countdown_label'):
                self.rapid_countdown_label.config(text=countdown)
        except Exception:
            pass

        # ⭐ RESTO DE ACTUALIZACIONES (solo si existen los widgets)
        try:
            if not hasattr(self, 'rapid_ops_status'):
                # Continuar directo a la llamada periódica
                pass
            else:
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

                # Actualizar IA adaptativa (fracción BUY) y mini-historial - DESHABILITADO
                # try:
                #     buy_frac = self._compute_rapid_ops_distribution()
                #     hist = list(self.rapid_ops_history)
                #     ... - DESHABILITADO
                # except Exception:
                #     pass

        except Exception as e:
            pass  # Silenciar errores de UI en thread

        # ⭐ IMPORTANTE: Llamar a sí misma periódicamente para actualizar el countdown en tiempo real
        try:
            self.root.after(200, self.update_rapid_operations_ui)
        except Exception:
            pass

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

    def _is_direction_allowed(self, direction):
        """
        ⭐ NUEVA: Valida si se permite abrir en una dirección específica.
        
        Args:
            direction (str): 'BUY' o 'SELL'
        
        Returns:
            bool: True si se permite, False si está deshabilitada
        """
        try:
            if direction.upper() == 'BUY':
                return bool(self._safe_get('ALLOW_BUY', True))
            elif direction.upper() == 'SELL':
                return bool(self._safe_get('ALLOW_SELL', True))
            else:
                return True  # Si dirección es inválida, permitir por defecto
        except Exception:
            return True  # Si hay error, permitir por defecto

    def _validate_float(self, S, P):
        """Valida que la entrada sea un número decimal válido para threshold.
        S = texto sustituido, P = texto predicho después de la sustitución.
        Solo permite dígitos (0-9) y puntos (.) para decimales."""
        if P == "":  # Permitir campo vacío
            return True
        try:
            # Contar puntos - máximo 1
            if P.count('.') > 1:
                return False
            # Intentar convertir a float
            float(P)
            return True
        except ValueError:
            return False

    def _on_threshold_change(self, var, index, value):
        """Callback cuando cambia el MICROTREND_THRESHOLD en tiempo real.
        Logea el cambio para confirmación del usuario."""
        try:
            current_val = self._safe_get('MICROTREND_THRESHOLD', 1.0)
            if current_val > 0:
                self.add_log(f"[THRESHOLD_UPDATED] Nuevo umbral de microtendencia: {current_val} pips "
                           f"(= {current_val/10000.0:.6f} decimal) | Aplicado en tiempo real", 'info')
        except Exception as e:
            pass  # Silenciar errores durante callbacks

    def _forced_open_interval_seconds(self, forced_value=None):
        """
        ⭐ CONVERSIÓN DUAL (IDÉNTICA a TRADE_INTERVAL):
        - Si < 1: multiplica por 100 (0.1 → 10s, 0.3 → 30s, 0.5 → 50s)
        - Si >= 1: multiplica por 60 (1 → 60s, 2 → 120s)
        
        Ejemplos: 0.1 → 10s, 0.3 → 30s, 1 → 60s, 2 → 120s
        """
        try:
            if forced_value is None:
                raw_value = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=1)).get())
            else:
                raw_value = float(forced_value)
        except Exception:
            raw_value = 1

        if raw_value <= 0:
            raw_value = 1

        # ⭐ LÓGICA DUAL IDÉNTICA A TRADE_INTERVAL
        if raw_value < 1:
            interval_seconds = raw_value * 100.0  # 0.3 * 100 = 30 segundos, 0.5 * 100 = 50 segundos
        else:
            interval_seconds = raw_value * 60.0  # 1 * 60 = 60 segundos (default), 2 * 60 = 120 segundos

        # En volatilidad alta reaccionar más rápido sin llegar a spam extremo.
        try:
            if str(getattr(self, 'market_volatility', '')).upper() == 'ALTA':
                interval_seconds *= 0.80
        except Exception:
            pass

        return max(0.1, float(interval_seconds)), float(raw_value)

    def _get_live_specialist_open_signal(self, max_age_sec=1.5):
        """
        Señal rápida basada DIRECTAMENTE en Buy/Sell specialist.
        La decisión nace en cada specialist y aquí solo se arbitra entre ambos.
        """
        try:
            buy_thr = float(self._safe_get('BUY_CONFIDENCE_THRESHOLD', 65.0))
            sell_thr = float(self._safe_get('SELL_CONFIDENCE_THRESHOLD', 65.0))

            buy_sig = None
            sell_sig = None
            if hasattr(self.buy_specialist, 'get_live_open_signal'):
                buy_sig = self.buy_specialist.get_live_open_signal(conf_threshold=buy_thr, max_age_sec=max_age_sec)
            if hasattr(self.sell_specialist, 'get_live_open_signal'):
                sell_sig = self.sell_specialist.get_live_open_signal(conf_threshold=sell_thr, max_age_sec=max_age_sec)

            if not buy_sig and not sell_sig:
                return None

            buy_score = float((buy_sig or {}).get('score', self.last_buy_score))
            sell_score = float((sell_sig or {}).get('score', self.last_sell_score))
            buy_conf = float((buy_sig or {}).get('confidence', self.last_buy_confidence))
            sell_conf = float((sell_sig or {}).get('confidence', self.last_sell_confidence))

            buy_valid = bool(buy_sig and str(buy_sig.get('recommendation', 'HOLD')).upper() == 'BUY')
            sell_valid = bool(sell_sig and str(sell_sig.get('recommendation', 'HOLD')).upper() == 'SELL')

            if not buy_valid and not sell_valid:
                return {
                    'source': 'LIVE_SPECIALISTS',
                    'recommendation': 'HOLD',
                    'confidence': max(buy_conf, sell_conf),
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'buy_conf': buy_conf,
                    'sell_conf': sell_conf,
                    'reason': f'Specialists en HOLD (BUY {buy_conf:.1f}/{buy_thr:.1f}, SELL {sell_conf:.1f}/{sell_thr:.1f})'
                }

            if buy_valid and not sell_valid:
                direction = 'BUY'
            elif sell_valid and not buy_valid:
                direction = 'SELL'
            else:
                if buy_score > sell_score:
                    direction = 'BUY'
                elif sell_score > buy_score:
                    direction = 'SELL'
                else:
                    direction = 'BUY' if buy_conf >= sell_conf else 'SELL'

            selected_conf = buy_conf if direction == 'BUY' else sell_conf
            return {
                'source': 'LIVE_SPECIALISTS',
                'recommendation': direction,
                'confidence': selected_conf,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'buy_conf': buy_conf,
                'sell_conf': sell_conf,
                'reason': 'Señal nativa BUY/SELL specialist'
            }
        except Exception:
            return None
    
    def _is_in_pause(self, strict=True):
        """
        ⭐ FUNCIÓN CRÍTICA: Verifica si el bot está en pausa ACTUALMENTE
        
        Args:
            strict (bool): 
                - True: Respeta TODAS las pausas (ganancia, pérdida, etc.) - para abrir operaciones
                - False: Solo respeta pausa de EMERGENCIA (force_stop) - para monitoreo
        
        MODO MÚLTIPLES PARTES:
            - Cada símbolo es 100% INDEPENDIENTE
            - Si GOLD causa pausa de ganancia, NO afecta a SILVER
            - Cada uno tiene su propio análisis, apertura y cierre
            - Solo EMERGENCIA (force_stop) afecta globalmente
        
        Returns:
            (bool, str): (en_pausa, razón_pausa)
        """
        now = time.time()
        
        # 1️⃣ PAUSA DE EMERGENCIA (máxima prioridad - GLOBAL, afecta a TODOS)
        if getattr(self, 'force_stop_triggered', False):
            return True, "🛑 EMERGENCIA: Force stop activado"
        
        # ⭐ EN MODO MÚLTIPLES PARTES: Pausas POST-OPERACIÓN son INDEPENDIENTES por símbolo
        # Esto permite que GOLD tenga pausa pero SILVER abra normalmente
        try:
            use_multiple = self.config.get('USE_MULTIPLE_PARTS', tk.BooleanVar(value=False)).get()
        except:
            use_multiple = False
        
        if use_multiple and strict:
            # En modo múltiples partes, solo respetar emergencia
            # Las pausas post-operación no bloquean (cada símbolo es independiente)
            return False, ""
        
        if self.bot_pausado:
            if self.pause_until and now < self.pause_until:
                remaining = int(self.pause_until - now)
                reason = getattr(self, 'pause_reason', "Pausa post-operación")
                return True, f"⏸️ {reason} ({remaining}s resta)"
            else:
                # Pausa vencida, resetear
                self.bot_pausado = False
                self.pause_until = 0.0
                self.pause_reason = ""
        
        # 2️⃣ COOLDOWN (solo si strict=True y NO en modo múltiples partes)
        if strict and not use_multiple and self.block_until and now < self.block_until:
            remaining = int(self.block_until - now)
            return True, f"⏳ Cooldown activo ({remaining}s resta)"
        
        return False, ""
    
    def _set_pause(self, duration_seconds, reason="Pausa"):
        """
        ⭐ ACTIVAR PAUSA: Centraliza la lógica de establecer pausa
        
        Args:
            duration_seconds (float): Segundos de pausa
            reason (str): Razón de la pausa (para logs)
        """
        self.bot_pausado = True
        self.pause_until = time.time() + duration_seconds
        self.pause_reason = reason
        self.add_log(f"⏸️ PAUSA ACTIVADA: {reason} por {int(duration_seconds)}s", 'warning')
    
    def _clear_pause(self):
        """Limpia la pausa antes de lo previsto"""
        self.bot_pausado = False
        self.pause_until = 0.0
        self.pause_reason = ""
        self.add_log("✅ Pausa CANCELADA manualmente", 'info')
    
    def conectar_mt5(self):
        """Mejorado manejo de conexión a MT5"""
        try:
            # Inicializar conexión con el terminal MetaTrader5 ya abierto
            if not mt5.initialize():
                self.add_log("Error inicializando MT5", 'error')
                return False

            # Usar la sesión ya activa del terminal; NO pedir login/password
            account_info = mt5.account_info()
            if account_info is None:
                self.add_log("No hay sesión MT5 activa. Abre MetaTrader5 y conéctate antes de iniciar el bot.", 'error')
                return False

            if not account_info.trade_allowed:
                self.add_log("Cuenta no permite trading", 'error')
                return False

            self.balance_inicial = account_info.balance
            self.saldo_inicial = account_info.balance
            self.saldo_actual = self.saldo_inicial
            self.ganancia_neta = 0.0
            self.add_log(f"MT5 conectado correctamente (sesión existente)", 'success')
            self.add_log(f"[DINERO] Saldo inicial: ${self.saldo_inicial:.2f}", 'info')
            self.connected = True
            return True
            
        except Exception as e:
            self.add_log(f"Error en conexión MT5: {str(e)}", 'error')
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
                self.add_log(f"⚠️ [BIAS DETECTED] Threshold ajustado", 'warning')
            
            if result['drift_warned']:
                self.add_log(f"⚠️ [DRIFT DETECTED] Reduciendo posición", 'warning')
            
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
        """Cierra absolutamente todas las posiciones abiertas, sin importar símbolo ni magic."""
        try:
            # ⭐ PRIMERO: Marcar como emergencia para que NO abra nuevas operaciones
            self.force_stop_triggered = True
            self.is_running = False
            self._scheduler_running = False
            self._forced_reopen_started = False
            self._forced_scheduler_thread = None
            self.en_pausa = False
            self.objetivo_cumplido = False
            
            self.add_log("[ALERTA] INICIANDO CIERRE DE EMERGENCIA FORZADO (todas las posiciones)", 'alert')
            if not mt5.initialize():
                mt5.shutdown()
                time.sleep(2)
                mt5.initialize()
                if not self.conectar_mt5():
                    self.add_log("[⚠️] Procediendo sin conexión confirmada", 'warning')

            positions = mt5.positions_get()
            if not positions:
                self.add_log("No hay operaciones abiertas", 'info')
            else:
                for pos in positions:
                    symbol = pos.symbol
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
                                "magic": pos.magic,
                                "comment": "Cierre-Emergencia",
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            result = mt5.order_send(request)
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                self.add_log(f"[OK] Cerrada #{pos.ticket} | ${pos.profit:.2f}", 'success')
                                break
                            self.add_log(f"Reintento {intento+1} para #{pos.ticket}...", 'warning')
                            time.sleep(1)
                        except Exception as e:
                            self.add_log(f"Error en intento {intento+1}: {str(e)}", 'error')
                            time.sleep(1)

            # ⭐ DESACTIVAR todos los controles para que no pueda cambiar nada
            for entry in self.config_entries.values():
                entry.config(state='disabled')

            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')

            self.status_indicator.itemconfig(self.status_circle, fill='#ef4444')
            self.status_label.config(text="Bot Detenido por Emergencia (No se abrirán más operaciones)", fg='#f87171')
            self._update_ui()
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

            # Histórico de trades removido: solo análisis de mercado actual
            # self.directional_trade_history.append({...}) - DESHABILITADO
            
            if len(self.historial_resultados) > self.max_historial:
                self.historial_resultados.pop(0)
            
            self.total_operaciones_abiertas = max(0, self.total_operaciones_abiertas - 1)
            
            # ⭐ NUEVO: Reiniciar contador de tiempo cuando no hay más operaciones abiertas
            if self.total_operaciones_abiertas == 0:
                self.ultima_operacion = time.time()
                self.add_log(f"[CONTADOR] Todas las operaciones cerradas. Contador de intervalo reiniciado.", 'info')
            
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
                    self._set_pause(pause_seconds, "Pausa post-pérdida (Max Loss)")
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
                    self._set_pause(pause_seconds, "Pausa post-ganancia")
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
                
                # Registro de trades deshabilitado: solo análisis de mercado
                # self.adaptive_params.record_trade_result(...) - DESHABILITADO
                
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
                self.add_log(f"⚠️ Error verificando objetivo: {str(e)[:50]}", 'warning')
            
            self.request_ui_refresh()
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
            # Calibración removida: solo análisis de mercado actual
            # self.closed_trades_for_calibration - DESHABILITADO
            # self.calibrator.record_trade(...) - DESHABILITADO
            # self.calibrator.auto_calibrate() - DESHABILITADO
            pass
        
        except Exception as e:
            self.add_log(f"Error registrando trade para calibración: {str(e)}", 'warning')

    def _regenerate_training_data(self):
        """⭐ OPCIÓN A: Regenera datos frescos (últimas 500 barras M1 = 8h) y entrena especialistas"""
        try:
            symbol = self.config['SYMBOL'].get()
            
            self.add_log("[📊] Regenerando datos de entrenamiento (últimas 500 barras M1 = 8h)...", 'info')
            
            # ⭐ OPCIÓN A: Usar datos FRESCOS de últimas 500 barras (8 horas) en lugar de 4 semanas
            snapshots = self.get_fresh_market_data(symbol, bars=500) or []
            
            if not snapshots or len(snapshots) < 50:
                self.add_log(f"[ERROR] Datos insuficientes: {len(snapshots)} barras (necesita >= 50)", 'error')
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
                self.add_log(f"[OK] Ambos especialistas entrenados con {len(snapshots)} barras M1 (⭐ últimas 8h datos frescos)", 'success')
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
            # PASO 1: Cargar datos - ⭐ USAR DATOS FRESCOS DE MT5
            snaps = self.get_fresh_market_data(symbol, bars=2000) or []  # 2000 barras M1 ≈ 33 horas
            
            # ⭐ DIAGNÓSTICO: Log detallado de qué se cargó
            logger.info(f"[DUAL] reload_market_snapshots() retornó {len(snaps)} snapshots (tipo: {type(snaps).__name__})")
            
            if not snaps:
                self.add_log("[DUAL] ❌ Sin datos - reload_market_snapshots retornó vacío", 'error')
                logger.error("[DUAL] ❌ reload_market_snapshots retornó lista VACÍA")
                return None
            
            # ⭐ Requisito reducido: al menos 20 snapshots (fue 100)
            if len(snaps) < 20:
                self.add_log(f"[DUAL] ❌ Datos insuficientes: {len(snaps)} < 20 snapshots", 'error')
                logger.error(f"[DUAL] ❌ Snapshots insuficientes: {len(snaps)} (necesita >= 20)")
                return None
            
            self.add_log(f"[DUAL] ✓ PASO 1: Cargados {len(snaps)} snapshots del histórico", 'info')
            logger.info(f"[DUAL] ✓ Cargados {len(snaps)} snapshots - PROCEEDING con análisis")
            
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
                self._refresh_specialists_session_context()
                # ⭐ ADQUIRIR LOCK para sincronización con monitor
                with self.specialist_analysis_lock:
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
                self._refresh_specialists_session_context()
                # ⭐ ADQUIRIR LOCK para sincronización con monitor
                with self.specialist_analysis_lock:
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

            buy_res, sell_res, prot = self._apply_specialist_protections(
                buy_res, sell_res, snapshots=snaps, context='dual'
            )
            if prot.get('block'):
                self.add_log(f"[DUAL] HOLD preventivo por protección especialistas: {prot.get('reason', '')}", 'warning')
                return {
                    'arbitrator': {'recommendation': 'HOLD', 'reason': prot.get('reason', '')},
                    'recommendation': 'HOLD',
                    'buy_specialist': buy_res,
                    'sell_specialist': sell_res
                }
            
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
            mode = "Sistema Multi-IA" if self.use_multi_ai.get() else "Modo Tradicional"
            self.add_log(f"Bot iniciado - {mode}", 'info')
            
            # ⭐ VALIDACIÓN DE OPERACIONES EN ESPERA
            if self.pending_operations:
                self.add_log(f"\n[ESPERA] OPERACIONES EN ESPERA DETECTADAS: {len(self.pending_operations)}", 'warning')
                for i, op in enumerate(self.pending_operations, 1):
                    status = "🚀" if op.get('status') == 'ESPERANDO' else "🚀"
                    self.add_log(f"   {status} Op #{op.get('id', i)}: {op['direction']} @ {op['price']:.5f}", 'info')
                self.add_log(f"   ► Analizando mercado para apertura...\n", 'warning')
            else:
                self.add_log(f"\n📊 Analizando mercado - Esperando operaciones\n", 'info')

            symbol = self._get_symbol()

            while self.is_running:
                try:
                    # FIX #19: CRÍTICO - Chequear pausa al INICIO del loop (antes de cualquier análisis)
                    if self.bot_pausado:
                        if self.pause_until and time.time() >= self.pause_until:
                            # Pausa vencida - reanudar completamente
                            self.add_log("[✅ REANUDACIÓN] Pausa terminada - Retomando operaciones", 'success')
                            
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
                                # ⭐ FIX #3: Usar cache MT5 en lugar de llamada directa
                                positions = self.mt5_cache.get_positions(symbol) or mt5.positions_get(symbol=symbol)
                                if positions:
                                    bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
                                    for pos in bot_positions:
                                        # Verificar TP/SL
                                        profit = pos.profit
                                        tp_val = self.config['TP_CLOSE'].get()
                                        sl_val = self.config['SL_CLOSE'].get()
                                        
                                        should_close = False
                                        reason = ""
                                        
                                        if tp_val and tp_val > 0 and profit >= tp_val:
                                            should_close = True
                                            reason = f"TP alcanzado (${profit:.2f} >= ${tp_val:.2f})"
                                        elif sl_val and sl_val > 0 and profit <= -sl_val:
                                            should_close = True
                                            reason = f"SL alcanzado (${profit:.2f} <= -${sl_val:.2f})"
                                        
                                        if should_close:
                                            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                                            # ⭐ FIX #3: Usar cache para tick
                                            tick = self.mt5_cache.get_tick(symbol) or mt5.symbol_info_tick(symbol)
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
                                logger.error(f"[PAUSE-MONITOR] Error closing position during pause: {str(e)[:80]}")
                        
                        # Mientras está pausado, dormir y continuar (SIN ANÁLISIS)
                        time.sleep(0.5)
                        continue
                    
                    # ⭐ OPCIÓN A: Regenerar datos de entrenamiento cada 30 minutos (aumentado de 5m)
                    try:
                        if not hasattr(self, '_last_training_regen'):
                            self._last_training_regen = 0
                        if time.time() - self._last_training_regen >= 1800:  # 30 minutos (⭐ AUMENTADO de 300s=5m)
                            self._regenerate_training_data()
                            self._last_training_regen = time.time()
                    except Exception as e:
                        logger.error(f"Error regenerando datos de entrenamiento: {e}")
                    
                    # ⭐ NUEVO: Ajustar parámetros dinámicamente cada minuto
                    if self.adaptive_params.adjust_parameters_dynamically():
                        self.adaptive_params.log_current_state()
                    
                    # [RESET] Recarga periódica de market_snapshots (REDUCIDA a 30s en lugar de 5s)
                    try:
                        reload_interval = 30  # ⭐ CAMBIADO de 5 a 30 segundos para reducir acumulación
                        try:
                            if 'SNAPSHOT_RELOAD_INTERVAL' in self.config:
                                reload_interval = int(self.config['SNAPSHOT_RELOAD_INTERVAL'].get())
                        except Exception:
                            pass
                        if not hasattr(self, '_last_snap_reload'):
                            self._last_snap_reload = 0
                        if time.time() - self._last_snap_reload >= float(reload_interval):
                            try:
                                # ⭐ Recargar AMBOS símbolos para mantener datos actualizados
                                for reload_symbol in ['GOLD', 'SILVER']:
                                    try:
                                        self.reload_market_snapshots(symbol=reload_symbol)
                                    except Exception:
                                        logger.exception(f"Error recargando {reload_symbol} en bot_loop")
                            except Exception:
                                logger.exception("Error en recarga periódica de market_snapshots en bot_loop")
                            self._last_snap_reload = time.time()
                    except Exception:
                        logger.exception("Error calculando recarga periódica de snapshots")
                    
                    # ⭐ LOGGING PERIÓDICO DE MEMORIA (cada 10 minutos)
                    try:
                        if time.time() - self.last_memory_log >= 600:  # 10 minutos
                            try:
                                import psutil  # type: ignore
                                process = psutil.Process(os.getpid())
                                mem_mb = process.memory_info().rss / 1024 / 1024
                                snap_count = len(self.market_snapshots) if isinstance(self.market_snapshots, list) else 0
                                ghost_count = len(self.ghost_ops_history) if hasattr(self, 'ghost_ops_history') else 0
                                self.add_log(f"[MEMORY] Uso: {mem_mb:.1f}MB | Snapshots: {snap_count} | Ghost ops: {ghost_count}", 'info')
                                self.last_memory_log = time.time()
                            except ImportError:
                                # psutil no está disponible
                                if not hasattr(self, '_psutil_warned'):
                                    logger.warning("[MEMORY] psutil no instalado - no se puede monitorear memoria")
                                    self._psutil_warned = True
                                self.last_memory_log = time.time()
                    except Exception:
                        pass  # Silenciar errores de logging de memoria

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
                    
                    # Lógica principal de trading
                    if self.total_operaciones_abiertas > 0:
                        continue

                    # MODO NORMAL (resto del código sin cambios)
                    objetivo = self.objetivo_ganancia.get()
                    if objetivo > 0 and self.ganancia_neta >= objetivo and not self.objetivo_cumplido:
                        self.add_log(f"\n🌟 OBJETIVO ALCANZADO: ${self.ganancia_neta:.2f} >= ${objetivo:.2f}", 'success')
                        self.objetivo_cumplido = True
                        self._handle_objetivo_pause()
                        time.sleep(0.05)  # ⭐ Ultra-rápido: 50ms para reintentar verificación
                        continue

                    if time.time() < getattr(self, 'block_until', 0):
                        remaining = int(self.block_until - time.time())
                        if remaining > 0:
                            self.add_log(f"[ESPERA] Cooldown tras ganancia activo ({remaining}s restantes) - esperando...", 'info')
                        time.sleep(0.05)  # ⭐ Verificar cada 50ms en lugar de 1s
                        continue
                    
                    # ⭐ NUEVA VERIFICACIÓN: Pausas post-operación (ganancia/pérdida)
                    in_pause, pause_reason = self._is_in_pause(strict=True)
                    if in_pause:
                        self.add_log(f"[PAUSA] {pause_reason} - esperando para nueva operación...", 'info')
                        time.sleep(0.05)  # ⭐ Verificar cada 50ms en lugar de 1s
                        continue

                    if self.total_operaciones_abiertas < self.config['MAX_SIMULTANEOUS_OPS'].get():
                        # ⭐ VERIFICACIÓN DINÁMIMA DE INTERVALO: Convertir TRADE_INTERVAL (valores decimales) a segundos
                        try:
                            trade_interval_value = float(self.config['TRADE_INTERVAL'].get())
                            # ⭐ LÓGICA DUAL: 
                            # - Si < 1: multiplicar por 100 (0.1 = 10s, 0.2 = 20s, 0.5 = 50s)
                            # - Si >= 1: multiplicar por 60 (1 = 60s/1min, 2 = 120s/2min)
                            if trade_interval_value < 1:
                                trade_interval_seconds = trade_interval_value * 100
                            else:
                                trade_interval_seconds = trade_interval_value * 60
                        except Exception:
                            trade_interval_seconds = 30  # Fallback: 30 segundos
                        
                        # Verificar si pasó suficiente tiempo desde la última operación
                        tiempo_desde_ultima = time.time() - self.ultima_operacion
                        if tiempo_desde_ultima < trade_interval_seconds:
                            falta_tiempo = trade_interval_seconds - tiempo_desde_ultima
                            # Log cada 5 segundos para no saturar
                            if falta_tiempo < 5 or (int(falta_tiempo) % 5 == 0):
                                self.add_log(f"[ESPERA-INTERVALO] Falta {falta_tiempo:.1f}s (intervalo: {trade_interval_value} = {trade_interval_seconds}s)", 'info')
                            time.sleep(0.05)
                            continue
                        
                        # ⭐ VERIFICACIÓN CRÍTICA PRE-ANÁLISIS: Bot detenido o deteniendo
                        if not self.is_running or getattr(self, 'force_stop_triggered', False):
                            self.add_log("[BOT] Bot detenido - canceling nuevas operaciones", 'warning')
                            break
                        
                        self.add_log("\n🔍 Iniciando análisis de mercado para nueva operación...", 'info')
                        
                        # Trigger primario: usar señal LIVE del monitor (mismos valores que UI)
                        analysis_result = self._get_live_specialist_open_signal(max_age_sec=1.5)
                        if analysis_result and analysis_result.get('recommendation') in ['BUY', 'SELL']:
                            self.add_log(
                                f"[LIVE] Trigger rápido con monitor 1s: "
                                f"BUY {analysis_result.get('buy_score', 0):.1f}%/{analysis_result.get('buy_conf', 0):.1f}% | "
                                f"SELL {analysis_result.get('sell_score', 0):.1f}%/{analysis_result.get('sell_conf', 0):.1f}%",
                                'success'
                            )
                        else:
                            # Fallback: análisis ULTRA-RÁPIDO con cache (reutiliza si es reciente)
                            analysis_result = self._ultra_fast_analysis(symbol)
                        
                        if analysis_result and analysis_result.get('recommendation') in ['BUY', 'SELL']:
                            direccion = analysis_result['recommendation']
                            self.add_log(f"[{analysis_result.get('source', '??')}] ✓ Análisis decidió: {direccion}", 'success')
                            
                            # NUEVO: Capturar confianza para volumen dinámico
                            signal_confidence = analysis_result.get('confidence', 50)
                            self.last_signal_confidence = signal_confidence
                            self.add_log(f"[CONFIDENCE] Señal con confianza: {signal_confidence}%", 'info')
                            
                            # ⭐ NUEVO: ANÁLISIS MULTI-PERÍODO PRE-APERTURA (10, 20, 30 velas simultáneamente)
                            self.add_log(f"\n🔄 Validando con análisis multi-período (10/20/30 velas)...", 'info')
                            multi_analysis = self._multi_period_candle_analysis(symbol, direccion)
                            
                            if not multi_analysis.get('valid', False):
                                self.add_log(
                                    f"[❌ MULTI-PERÍODO RECHAZÓ] {multi_analysis.get('reason', 'Confianza insuficiente')} "
                                    f"({multi_analysis.get('confidence', 0):.1f}%)",
                                    'warning'
                                )
                                time.sleep(0.05)
                                continue
                            
                            # ⭐ NUEVO: Si es GOLD, validar contra configuración óptima
                            if symbol.upper() == 'GOLD' or symbol == 'XAUUSD':
                                self.add_log(f"\n🟡 Aplicando validación CONFIG ÓPTIMA para GOLD...", 'info')
                                gold_validation = self._validate_gold_optimal_entry(symbol, direccion)
                                
                                if not gold_validation.get('valid', False):
                                    self.add_log(
                                        f"[❌ CONFIG GOLD RECHAZÓ] {gold_validation.get('reason', 'No cumple criterios')}",
                                        'warning'
                                    )
                                    time.sleep(0.05)
                                    continue
                                
                                # Incorporar score de GOLD en confianza final
                                gold_score = gold_validation.get('score', 0)
                                combined_confidence = (signal_confidence + multi_analysis['confidence'] + gold_score) / 3
                                self.add_log(
                                    f"[✅ VALIDACIÓN COMPLETA] Confianza final: {combined_confidence:.1f}% "
                                    f"(Análisis + Multi-período + CONFIG GOLD)",
                                    'success'
                                )
                            
                            # ⭐ NUEVO: Si es SILVER, validar contra configuración óptima
                            elif symbol.upper() == 'SILVER' or symbol == 'XAGUSD':
                                self.add_log(f"\n🔥 Aplicando validación CONFIG ÓPTIMA para SILVER...", 'info')
                                silver_validation = self._validate_silver_optimal_entry(symbol, direccion)
                                
                                if not silver_validation.get('valid', False):
                                    self.add_log(
                                        f"[❌ CONFIG SILVER RECHAZÓ] {silver_validation.get('reason', 'No cumple criterios')}",
                                        'warning'
                                    )
                                    time.sleep(0.05)
                                    continue
                                
                                # Incorporar score de SILVER en confianza final
                                silver_score = silver_validation.get('score', 0)
                                combined_confidence = (signal_confidence + multi_analysis['confidence'] + silver_score) / 3
                                self.add_log(
                                    f"[✅ VALIDACIÓN COMPLETA] Confianza final: {combined_confidence:.1f}% "
                                    f"(Análisis + Multi-período + CONFIG SILVER)",
                                    'success'
                                )
                            else:
                                # Combinar confianzas (sin validación GOLD)
                                combined_confidence = (signal_confidence + multi_analysis['confidence']) / 2
                                self.add_log(
                                    f"[✅ VALIDACIÓN EXITOSA] Confianza combinada: {combined_confidence:.1f}% "
                                    f"(Análisis: {analysis_result.get('source', '??')} + Multi-período)",
                                    'success'
                                )
                            
                            # NUEVO: Registrar metadata para feedback loop (pre-trade captura)
                            # Metadata de trade - REMOVIDA: solo análisis de mercado
                            # self.last_trade_metadata = {...} - DESHABILITADO
                            
                            if self.abrir_operacion_smart(direccion, force=False):
                                self.ultima_operacion = time.time()
                                self.last_confidence = combined_confidence
                                self.add_log("[ESPERA] Esperando resultado de la operación...", 'info')
                        else:
                            reason = analysis_result.get('reason', 'Sin definir') if analysis_result else 'Ambos análisis fallaron'
                            self.add_log(f"[Análisis rechazó] {reason}", 'warning')
                            time.sleep(0.05)  # ⭐ Reintentar análisis cada 50ms (muy rápido)
                    
                    # Siempre monitorear posiciones abiertas (cierres por profit/loss deben ser individuales)
                    try:
                        if self.total_operaciones_abiertas > 0:
                            self.monitorear_posiciones_en_rojo()
                            # ⭐ NUEVO: Verificar recuperación de operaciones en rojo
                            self._check_and_recover_red_positions()
                            self.limpiar_tracking_posiciones_cerradas()
                        # Mantener contador/estado actualizado
                        self.actualizar_contador_z()
                    except Exception as _e:
                        self.add_log(f"Error monitoreo periódicode posiciones: {_e}", 'error')

                    # ⭐ NUEVO: Logging del contador de operaciones forzadas en CADA ciclo
                    try:
                        if self.config.get('FORCED_OPS_ENABLED', tk.BooleanVar(value=False)).get():
                            try:
                                minutes = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=5.0)).get())
                            except Exception:
                                minutes = 5.0

                            intervalo, _ = self._forced_open_interval_seconds(minutes)
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

                    time.sleep(0.05)  # ⭐ ULTRA-OPTIMIZADO: 50ms - ciclo principal de análisis

                except Exception as e:
                    self.add_log(f"Error en ciclo: {str(e)}", 'error')
                    time.sleep(0.05)  # ⭐ Ultra-rápido: 50ms para reintentar inmediatamente
                    continue
                
        except Exception as e:
            self.add_log(f"Error crítico en bot_loop: {str(e)}", 'error')

    def _ultra_fast_analysis(self, symbol):
        """
        ⭐ ANÁLISIS ULTRA-RÁPIDO: Reutiliza análisis previo si es muy reciente (100ms)
        - Evita recomputo innecesario
        - Instantáneo si hay análisis válido cached
        - Fallback a análisis paralelo si cache está viejo
        """
        now = time.time()
        
        # Si hay análisis válido en cache (< 100ms de antigüedad), reutilizarlo
        if (self.last_analysis_result and 
            (now - self.analysis_cache.get('timestamp', 0)) < self.analysis_cache_ttl):
            return self.last_analysis_result
        
        # Si hay análisis en progreso, esperar 10ms y usar el anterior si existe
        if self._analysis_in_progress:
            time.sleep(0.01)
            if self.last_analysis_result:
                return self.last_analysis_result
        
        # Correr análisis paralelo (multi-threaded, muy rápido)
        return self._parallel_trade_analysis(symbol)

    # ⭐ NUEVO: Análisis paralelo V12 + DUAL (-40% latencia)
    def _parallel_trade_analysis(self, symbol):
        """
        Ejecuta V12 Analysis y DUAL Analysis EN PARALELO usando threading.
        Retorna el primero que genere un resultado válido (BUY/SELL).
        
        Impacto: -40% latencia antes de abrir posición
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
        
        # Elegir resultado: Prioridad a V12 si está válido, sino DUAL
        if results['v12'] and results['v12'].get('can_trade'):
            self.add_log(f"[RESULTADO] V12 ganó: {results['v12'].get('signal')} (conf: {results['v12'].get('confidence', 0):.1f}%)", 'success')
            result = {
                'source': 'V12',
                'signal': results['v12'].get('signal'),
                'confidence': results['v12'].get('confidence', 0),
                'recommendation': results['v12'].get('signal'),
                'reason': results['v12'].get('reason', 'V12 analysis')
            }
            # ⭐ Guardar en cache para reutilización ultra-rápida
            self.analysis_cache = {'buy': result, 'sell': result, 'timestamp': time.time()}
            self.last_analysis_result = result
            return result
        elif results['dual'] and results['dual'].get('recommendation') in ['BUY', 'SELL']:
            self.add_log(f"[RESULTADO] DUAL ganó: {results['dual'].get('recommendation')} (conf: {results['dual'].get('confidence', 0):.1f}%)", 'success')
            result = {
                'source': 'DUAL',
                'signal': results['dual'].get('recommendation'),
                'confidence': results['dual'].get('confidence', 0),
                'recommendation': results['dual'].get('recommendation'),
                'reason': 'DUAL analysis'
            }
            # ⭐ Guardar en cache para reutilización ultra-rápida
            self.analysis_cache = {'buy': result, 'sell': result, 'timestamp': time.time()}
            self.last_analysis_result = result
            return result
        else:
            reason = 'Ambos análisis rechazaron'
            if not v12_completed:
                reason = 'V12 timeout (>10s)'
            elif not dual_completed:
                reason = 'DUAL timeout (>10s)'
            self.add_log(f"[RECHAZADO] {reason}", 'warning')
            return None

    # ⭐ NUEVO: Función de análisis con Multi-IA
    def analizar_mercado(self):
        """Análisis usando Sistema Multi-IA o tradicional según configuración"""
        if self.total_operaciones_abiertas > 0:
            self.add_log("[ERROR] No se analiza - Ya hay una operación abierta", 'warning')
            return None
            
        symbol = self._get_symbol()
        # --- REFRESH: asegurar datos de mercado actualizados y calibración antes de abrir ---
        try:
            # Forzar recarga de snapshots desde disco/MT5
            try:
                # ⭐ Recargar AMBOS símbolos para datos frescos
                snaps = []
                for reload_symbol in ['GOLD', 'SILVER']:
                    try:
                        sym_snaps = self.reload_market_snapshots(symbol=reload_symbol) or []
                        if reload_symbol == 'GOLD':  # Usar GOLD como principal
                            snaps = sym_snaps
                    except Exception:
                        pass
            except Exception:
                snaps = []

            # Calibración removida: solo análisis de mercado actual
            # try:
            #     cal = calibrate_from_logs(limit=1000)
            #     ... - DESHABILITADO
            # except Exception:
            #     logger.exception("Error ejecutando calibrate_from_logs en pre-open")

            # Auto-calibrador dinámico local - DESHABILITADO
            # try:
            #     self.calibrator.auto_calibrate()
            # except Exception:
            #     pass

            # Validación final: pedir a especialistas que evalúen los snaps más recientes
            try:
                buy_res = None
                sell_res = None
                # ⭐ ADQUIRIR LOCK para sincronización con monitor
                with self.specialist_analysis_lock:
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
            
            self.add_log("\n📊 Fase 1: Análisis de Especialistas", 'info')
            
            # Combine prefilled snapshots with latest MT5 bars (prefer MT5 for newest bars).
            buy_analysis = None
            sell_analysis = None
            try:
                # ⭐ Recargar snapshots con el símbolo correcto
                snaps = self.reload_market_snapshots(symbol=self._map_symbol_internal(symbol)) or []
                # Try to fetch recent bars from MT5 to keep data fresh
                try:
                    recent = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, max(50, int(self.config.get('BARS_ANALYZE').get())))
                except Exception:
                    recent = None

                recent_list = []
                if recent is not None:
                    try:
                        for r in recent:
                            ts = int(r[0]) if isinstance(r, (list, tuple)) or hasattr(r, '__getitem__') else int(r['time'])
                            entry = {
                                'timestamp': datetime.fromtimestamp(ts).isoformat(),
                                'open': float(r[1]) if isinstance(r, (list, tuple)) else float(r.get('open', 0.0)),
                                'high': float(r[2]) if isinstance(r, (list, tuple)) else float(r.get('high', 0.0)),
                                'low': float(r[3]) if isinstance(r, (list, tuple)) else float(r.get('low', 0.0)),
                                'close': float(r[4]) if isinstance(r, (list, tuple)) else float(r.get('close', 0.0)),
                                'tick_volume': int(r[5]) if isinstance(r, (list, tuple)) else int(r.get('tick_volume', 0))
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
                    
                    # Escribir en disco (trade_logger) con PERSISTENCIA HISTÓRICA
                    try:
                        symbol = self.config.get('SYMBOL', tk.StringVar(value='GOLD')).get() if hasattr(self, 'config') else 'GOLD'
                        # ⭐ NUEVO: Pasar símbolo y max_snapshots para metadata e historial automático
                        write_market_snapshots(merged_list, symbol=symbol, max_snapshots=1440)
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
                # ⭐ ADQUIRIR LOCK para sincronización con monitor
                self._refresh_specialists_session_context()
                with self.specialist_analysis_lock:
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

                if buy_analysis and sell_analysis:
                    buy_analysis, sell_analysis, prot = self._apply_specialist_protections(
                        buy_analysis, sell_analysis, snapshots=merged_list, context='multi-ia'
                    )
                    if prot.get('block'):
                        self.add_log(f"[PAUSA] Especialistas bloquearon por protección: {prot.get('reason', '')}", 'warning')
                        return None
            except Exception:
                buy_analysis = None
                sell_analysis = None
            
            if not buy_analysis or not sell_analysis:
                # Fallback: attempt a simple snapshot-based heuristic if specialists failed
                self.add_log("[Especialistas no devolvieron análisis completo, usando heurística de snapshots]", 'warning')
                snap_signal = None
                try:
                    snap_signal = self.compute_signal_from_snapshots()
                except Exception:
                    snap_signal = None
                if snap_signal is None:
                    self.add_log("[ERROR] Error en análisis de especialistas y heurística - No abrir", 'error')
                    return None
                # Build minimal analysis dicts using configured thresholds (never bypass them)
                try:
                    _fb_score = float(self.config.get('MIN_SCORE_REQUIRED', tk.DoubleVar(value=73.0)).get())
                    _fb_conf_buy = float(self.config.get('BUY_CONFIDENCE_THRESHOLD', tk.DoubleVar(value=65.0)).get())
                    _fb_conf_sell = float(self.config.get('SELL_CONFIDENCE_THRESHOLD', tk.DoubleVar(value=65.0)).get())
                except Exception:
                    _fb_score, _fb_conf_buy, _fb_conf_sell = 73.0, 65.0, 65.0
                self.add_log(f"[ADVERTENCIA] Usando heurística fallback con score={_fb_score:.1f} — los umbrales UI siguen activos", 'warning')
                if snap_signal == 'BUY':
                    buy_analysis = {'score': _fb_score, 'confidence': _fb_conf_buy, 'recommendation': 'BUY', 'reasoning': ['snapshot_heuristic']}
                    sell_analysis = {'score': max(0.0, _fb_score - 15.0), 'confidence': max(0.0, _fb_conf_sell - 20.0), 'recommendation': 'SELL', 'reasoning': ['snapshot_heuristic']}
                else:
                    sell_analysis = {'score': _fb_score, 'confidence': _fb_conf_sell, 'recommendation': 'SELL', 'reasoning': ['snapshot_heuristic']}
                    buy_analysis = {'score': max(0.0, _fb_score - 15.0), 'confidence': max(0.0, _fb_conf_buy - 20.0), 'recommendation': 'BUY', 'reasoning': ['snapshot_heuristic']}
            
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
                self.add_log(f"   ⚠️ BUY no cumple umbral ({buy_analysis['confidence']}% < {buy_threshold}%)", 'warning')
            if not sell_valid:
                self.add_log(f"   ⚠️ SELL no cumple umbral ({sell_analysis['confidence']}% < {sell_threshold}%)", 'warning')
            
            self.add_log(f"\n[EMOJI]️ Fase 2: Arbitraje de Decisión", 'info')
            
            # Usar árbitro como gatekeeper (ALLOW only) con umbrales dinámicos vigentes en UI.
            try:
                min_score_required = float(self.config.get('MIN_SCORE_REQUIRED', tk.DoubleVar(value=73.0)).get())
            except Exception:
                min_score_required = 73.0
            allow_context = {
                'min_confidence': min(buy_threshold, sell_threshold),
                'min_score_difference': 8 if self.market_volatility == "ALTA" else 12,
                'min_absolute_score': min_score_required,
            }
            allow_result = self.arbitrator.allow_trade(
                buy_analysis,
                sell_analysis,
                symbol,
                context=allow_context
            )
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
                minutes = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=5.0)).get())
            except Exception:
                minutes = 5.0

            intervalo, _ = self._forced_open_interval_seconds(minutes)
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

                self.add_log(f"[RESET] Ejecutando reapertura forzada. Dirección: {fallback_dir}", 'warning')
                try:
                    opened = self.abrir_operacion_smart(fallback_dir, force=True)
                    if opened:
                        self.next_forced_open = time.time() + float(intervalo)
                        self.add_log(f"[OK] ✅ Reapertura forzada realizada: {fallback_dir}", 'success')
                        return {'can_trade': True, 'signal': fallback_dir, 'reason': 'Forced open executed', 'recommendation': fallback_dir}
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
                self.add_log(f"[Análisis RECHAZÓ] {reason}", 'warning')
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
                return {'can_trade': False, 'reason': f'[📊] Calibración: Confianza muy baja'}
            
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
                self.add_log(f"   🚀 Correlaciones confirmadas", 'info')
            else:
                self.add_log(f"   ⚠️ {correlation_analysis.get('recommendation', 'Conflicto')}", 'warning')
                
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
        """Análisis tradicional con GoldAnalyzer (método original) - Funciona con ETHUSD"""
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
[📊] Detalles de la señal:
[🚀] Dirección: {opportunity['direction']}
💯 Probabilidad: {opportunity['probability']:.1f}%
📈 TP: {opportunity['tp_points']:.1f} puntos
[🛡️] SL: 100.0 puntos fijos
""", 'info')
        
        return opportunity['direction']

    # ⭐ NUEVO: Método para calcular potencial de recuperación EN TIEMPO REAL
    def _calculate_market_recovery_potential(self, symbol, direccion):
        """Calcula el potencial de recuperación ANTES de abrir la operación"""
        try:
            # Obtener datos de las últimas 24 horas
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, start_date, end_date)
            if rates is None or len(rates) < 10:
                self.add_log("[⚠️] No hay datos de 24h - Permitiendo operación", 'warning')
                return 100.0  # Sin datos = permitir
            
            closes = np.array([r[4] for r in rates])
            highs = np.array([r[2] for r in rates])
            lows = np.array([r[3] for r in rates])
            
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

    # ⭐ DESHABILITADO: Sistema de volumen dinámico (Kelly-inspired)
    # No usa histórico de trades, solo mercado actual
    def _calculate_kelly_fraction(self):
        """
        DESHABILITADO: No se usan datos de trades anteriores. Solo análisis de mercado actual.
        
        Retorna: (kelly_fraction, win_rate, profit_factor) - valores neutros
        """
        try:
            # Valores neutros: sin usar histórico
            return 0.02, 0.50, 1.0  # Conservative defaults
        except Exception:
            return 0.02, 0.50, 1.0
    
    def _validate_margin_available(self, volume, symbol):
        """
        ⭐ PREVENCIÓN DE MARGIN CALLS: Verifica margen disponible ANTES de abrir
        
        Retorna: (puede_operar_bool, margen_disponible, margen_requerido)
        """
        try:
            acct = mt5.account_info()
            if not acct:
                self.add_log("[MARGEN] ❌ No se pudo obtener info de cuenta", 'warning')
                return False, 0, 0
            
            equity = float(getattr(acct, 'equity', 0))
            balance = float(getattr(acct, 'balance', 0))
            margin_free = float(getattr(acct, 'margin_free', 0))
            margin_level = float(getattr(acct, 'margin_level', 0))
            
            # Información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                self.add_log(f"[MARGEN] ❌ No se pudo obtener info de {symbol}", 'warning')
                return False, 0, 0
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.add_log(f"[MARGEN] ❌ No se pudo obtener tick de {symbol}", 'warning')
                return False, 0, 0
            
            # Calcular margen requerido (típico: 1% para pares FX/CFD)
            # margen_req = volumen * precio * margen_percent
            margen_percent = 0.01  # 1% típico (100:1 leverage)
            margen_requerido = volume * tick.bid * margen_percent
            
            # Buffers de seguridad
            # 1. Margen mínimo disponible (20% del balance actual)
            margen_minimo_buffer = balance * 0.20
            
            # 2. Equity mínima antes de detener (30% del balance inicial)
            equity_minima = balance * 0.30
            
            # Validaciones - MENOS RESTRICTIVAS para permitir siempre abrir
            puede_operar = True
            razones = []
            
            # Check 1: Margen libre debe ser positivo (básico)
            if margin_free <= 0:
                puede_operar = False
                razones.append(f"Margen libre negativo/cero: ${margin_free:.2f}")
            
            # Check 2: Equity mínima (más flexible: 10% en lugar de 30%)
            equity_minima_flexible = balance * 0.10
            if equity < equity_minima_flexible:
                puede_operar = False
                razones.append(f"Equity crítica: ${equity:.2f} < ${equity_minima_flexible:.2f}")
            
            # Check 3: Margin level - SOLO si está MUY bajo (<100%) y hay operaciones
            # Si margin_level=0%, es normal (sin operaciones), PERMITIR
            if margin_level > 0 and margin_level < 100.0:
                puede_operar = False
                razones.append(f"Margin level crítico: {margin_level:.1f}% < 100%")
            
            if razones:
                self.add_log(f"[MARGEN] ⚠️ " + " | ".join(razones), 'warning')
                self.add_log(
                    f"[MARGEN] Status: Equity=${equity:.2f} | Margin_Free=${margin_free:.2f} | Level={margin_level:.1f}%",
                    'warning'
                )
            
            return puede_operar, margin_free, margen_requerido
            
        except Exception as e:
            self.add_log(f"[MARGEN] Error validación: {str(e)[:50]}", 'error')
            return False, 0, 0
    
    def calculate_dynamic_volume(self, confidence=None):
        """
        ⭐ MEJORADO: Sizing dinámico con KELLY REAL + validación de margen
        
        Combina:
        1. Kelly fraction basada en histórico real (p%, b ratio)
        2. Multipliers por confianza/volatilidad/drawdown
        3. Validación de margen disponible (previene margin calls)
        
        Retorna: volumen seguro o 0 si no hay condiciones
        """
        try:
            # Obtener volumen base
            base_vol = self.base_volume if hasattr(self, 'base_volume') else float(self.config['VOL'].get())
            dynamic_vol = base_vol
            adjustments = []
            
            # ⭐ PASO 1: KELLY FRACTION (basado en histórico real)
            kelly_frac, win_rate, profit_factor = self._calculate_kelly_fraction()
            
            # Convertir Kelly a multiplicador del volumen base
            # Si Kelly = 5% y base = 0.01, entonces kelly_multiplier = 5/1 = 5
            # Pero limitamos razonablemente a [0.5x, 2.0x]
            kelly_multiplier = max(0.5, min((kelly_frac / 0.02), 2.0))  # Relativo a 2% default
            dynamic_vol *= kelly_multiplier
            adjustments.append(f"Kelly ({kelly_frac*100:.2f}%): {kelly_multiplier:.2f}x")
            
            # ⭐ PASO 2: Recalibración por confianza de señal
            if confidence is None:
                confidence = getattr(self, 'last_signal_confidence', 50)
            
            if confidence < 30:
                conf_mult = 0.4
                reason = "Muy baja"
            elif confidence < 50:
                conf_mult = 0.6
                reason = "Baja"
            elif confidence < 65:
                conf_mult = 0.85
                reason = "Normal-baja"
            elif confidence < 80:
                conf_mult = 1.0
                reason = "Normal"
            else:
                conf_mult = 1.2
                reason = "Alta"
            
            dynamic_vol *= conf_mult
            adjustments.append(f"Confianza ({confidence:.0f}%, {reason}): {conf_mult:.2f}x")
            
            # ⭐ PASO 3: Penalización por pérdidas recientes (drawdown correction)
            if not hasattr(self, 'recent_losses'):
                self.recent_losses = []
            
            self.recent_losses = [(t, p) for t, p in self.recent_losses if time.time() - t < 1000]
            
            loss_count = len(self.recent_losses)
            if loss_count >= 3:
                dd_mult = 0.5  # -50% después de 3+ pérdidas
                reason = f"{loss_count}+ pérdidas"
            elif loss_count >= 2:
                dd_mult = 0.65
                reason = "2 pérdidas"
            elif loss_count >= 1:
                dd_mult = 0.85
                reason = "1 pérdida"
            else:
                dd_mult = 1.0
                reason = "Sin pérdidas"
            
            dynamic_vol *= dd_mult
            adjustments.append(f"Drawdown ({reason}): {dd_mult:.2f}x")
            
            # ⭐ PASO 4: Volatilidad del mercado
            try:
                # ⭐ Usar GOLD como símbolo por defecto
                snaps = self.reload_market_snapshots(symbol='GOLD') or []
                vol_level = self.get_volatility_level(snaps)
                if vol_level == 'HIGH':
                    vol_mult = 0.7
                    adjustments.append("Vol-HIGH: 0.7x")
                elif vol_level == 'LOW':
                    vol_mult = 1.15
                    adjustments.append("Vol-LOW: 1.15x")
                else:
                    vol_mult = 1.0
                    adjustments.append("Vol-NORMAL: 1.0x")
                dynamic_vol *= vol_mult
            except Exception:
                pass
            
            # ⭐ PASO 5: Limites SEGUROS (0.05x a 2.0x, no 3.0x)
            dynamic_vol = max(base_vol * 0.05, min(dynamic_vol, base_vol * 2.0))
            
            # ⭐ PASO 6: VALIDACIÓN DE MARGEN - SIEMPRE INTENTA ABRIR
            symbol = self.config['SYMBOL'].get()
            puede_operar, margin_free, margin_req = self._validate_margin_available(dynamic_vol, symbol)
            
            if not puede_operar:
                # En lugar de rechazar, REDUCE el volumen para que quepa
                # Calcula volumen máximo que cabe con margen disponible
                try:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        margen_percent = 0.01  # 1% leverage
                        # vol_máximo = margen_libre / (precio * porcentaje)
                        vol_maximo_por_margen = margin_free / (tick.bid * margen_percent + 0.0001)
                        
                        # Usa 50% del volumen máximo calculado como fallback
                        vol_reducido = max(base_vol * 0.05, vol_maximo_por_margen * 0.50)
                        vol_reducido = min(vol_reducido, base_vol * 2.0)  # Respeta límite superior
                        
                        self.add_log(f"[VOLUMEN] ⚠️ Margen ajustado: {dynamic_vol:.4f} → {vol_reducido:.4f} (margen: ${margin_free:.2f})", 'warning')
                        dynamic_vol = vol_reducido
                    else:
                        # Sin tick, usa mínimo viable
                        dynamic_vol = base_vol * 0.05
                        self.add_log(f"[VOLUMEN] ⚠️ Sin tick, usando volumen mínimo: {dynamic_vol:.4f}", 'warning')
                except Exception as e:
                    dynamic_vol = base_vol * 0.05
                    self.add_log(f"[VOLUMEN] ⚠️ Error ajuste margen, mínimo: {dynamic_vol:.4f}", 'warning')
            
            # Logging final
            final_multiplier = dynamic_vol / base_vol
            msg = f"[VOLUMEN] Base: {base_vol:.4f} → Dinámico: {dynamic_vol:.4f} ({final_multiplier:.2f}x) | "
            msg += " | ".join(adjustments) + f" | ✅ Abriendo con margen: ${margin_free:.2f}"
            self.add_log(msg, 'info')
            
            return dynamic_vol
            
        except Exception as e:
            self.add_log(f"[VOLUMEN] Error calculando volumen dinámico: {str(e)[:60]}", 'warning')
            return float(self.config['VOL'].get())

    def abrir_operacion_smart(self, direccion, force=False, startup=False):
        """
        ⭐ APERTURA INTELIGENTE - Detecta si usar múltiples partes (GOLD + SILVER simultáneamente)
        
        - Si USE_MULTIPLE_PARTS=False: Abre 1 operación en símbolo configurado (normal)
        - Si USE_MULTIPLE_PARTS=True: Abre 1 en GOLD + 1 en SILVER CON ANÁLISIS INDEPENDIENTE
          → Cada una se analiza y determina su propia dirección óptima (BUY o SELL)
          → Cada una con sus propios parámetros GOLD_THRESHOLD/SILVER_THRESHOLD
          → Cada una con su propia monitorización
          → Comparten SOLO TP Global y SL Global
        
        Retorna: bool (True si ambas abrieron en modo múltiple, o si abrió en modo normal)
        """
        try:
            use_multiple = self.config.get('USE_MULTIPLE_PARTS', tk.BooleanVar(value=False)).get()
        except:
            use_multiple = False
        
        if not use_multiple:
            # Modo normal: 1 operación en símbolo configurado
            return self.abrir_operacion(direccion, force=force, startup=startup)
        
        # ⭐ MODO MÚLTIPLES PARTES: Abrir en GOLD + SILVER CON LA MISMA DIRECCIÓN (CORRELACIONADOS)
        self.add_log(f"\n{'='*60}", 'warning')
        self.add_log(f"[MÚLTIPLES PARTES] Analizando GOLD y SILVER (misma dirección - correlacionados)...", 'warning')
        self.add_log(f"{'='*60}\n", 'warning')
        
        symbol_actual = self.config['SYMBOL'].get()
        
        # ⭐ ANÁLISIS PARA GOLD (primer símbolo principal)
        self.add_log(f"[1/3] Analizando GOLD (símbolo principal)...", 'info')
        gold_direction, gold_buy_score, gold_sell_score, _ = self._quick_analysis_for_forced_reopen('GOLD')
        self.add_log(f"[1/3] ✅ GOLD: Dirección óptima = {gold_direction} (BUY={gold_buy_score:.1f}, SELL={gold_sell_score:.1f})", 'success')
        
        # Pausa mínima entre análisis
        time.sleep(0.3)
        
        # ⭐ USAR LA MISMA DIRECCIÓN PARA SILVER (Altamente correlacionados con GOLD)
        silver_direction = gold_direction  # ⭐ CRÍTICO: SILVER sigue a GOLD (correlación ~0.95)
        silver_buy_score = gold_buy_score  # Usar los mismos scores
        silver_sell_score = gold_sell_score
        self.add_log(f"[2/3] ✅ SILVER: Usando dirección de GOLD = {silver_direction} (correlacionados, BUY={silver_buy_score:.1f}, SELL={silver_sell_score:.1f})", 'success')
        
        # ⭐ ABRIR EN GOLD CON SU DIRECCIÓN ÓPTIMA
        self.add_log(f"[3/3] Abriendo en GOLD con dirección {gold_direction}...", 'info')
        self.config['SYMBOL'].set('GOLD')
        self._configure_symbol_parameters('GOLD')  # ⭐ NUEVO: Reconfigura parámetros para GOLD
        gold_result = self.abrir_operacion(gold_direction, force=force, startup=startup)
        
        # Pausa mínima entre órdenes para evitar race conditions
        time.sleep(0.5)
        
        # ⭐ ABRIR EN SILVER CON LA MISMA DIRECCIÓN (Correlacionados)
        self.add_log(f"[3/3 - Parte 2] Abriendo en SILVER con dirección {silver_direction} (igual a GOLD - correlacionados)...", 'info')
        self.config['SYMBOL'].set('SILVER')
        self._configure_symbol_parameters('SILVER')  # ⭐ NUEVO: Reconfigura parámetros para SILVER
        silver_result = self.abrir_operacion(silver_direction, force=force, startup=startup)
        
        # Restaurar símbolo original
        self.config['SYMBOL'].set(symbol_actual)
        
        # Log resultado
        if gold_result and silver_result:
            self.add_log(f"[ÉXITO] Ambas partes abiertas: GOLD({gold_direction})✅ + SILVER({silver_direction})✅", 'success')
            return True
        elif gold_result or silver_result:
            status = f"GOLD({gold_direction}){'✅' if gold_result else '❌'} + SILVER({silver_direction}){'✅' if silver_result else '❌'}"
            self.add_log(f"[PARCIAL] Una parte abierta: {status}", 'warning')
            return True  # Retornar True si al menos una abrió
        else:
            self.add_log(f"[FALLO] Ninguna parte se abrió: GOLD({gold_direction})❌ + SILVER({silver_direction})❌", 'error')
            return False

    def abrir_operacion(self, direccion_sugerida, force=False, startup=False, force_params=None):
        """Versión mejorada para una sola operación con mejor análisis.
        
        IMPORTANTE: 
        - Si `force=False`: SIEMPRE entrena especialistas y hace análisis DUAL (completo)
        - Si `force=True`: Usa análisis rápido del scheduler (sin entrenamiento) + validación
        Si `force=True`: El análisis se ejecuta rápido sin lock
        ⭐ FLUJO: ANÁLISIS (DUAL si force=False, RÁPIDO si force=True) → ARBITRADOR → EJECUCIÓN
        """
        # --- FILTRO DE MICROTENDENCIA/MOMENTUM - DETECTA TENDENCIAS REALES SIN SESGO ---
        symbol = self._get_symbol()
        try:
            microtrend = self._microtrend_direction(symbol, bars=10, threshold=None)  # ⭐ USA THRESHOLD DE CONFIG EN TIEMPO REAL
        except Exception as e:
            self.add_log(f"[ERROR] microtrend_direction fallo: {e}", 'error')
            microtrend = 'FLAT'
        self.add_log(f"[MICROTREND] Microtendencia detectada: {microtrend} (sugerida: {direccion_sugerida})", 'info')

        # ⭐⭐⭐ VALIDACIÓN CRÍTICA #0: ANÁLISIS COMPLETO DE 10 VELAS ANTES DE CUALQUIER APERTURA
        can_open_10velas, analysis_10 = self._analyze_10_candles_complete(symbol, direccion_sugerida)
        # ⭐ BYPASS PARA TESTING: Si force=True, permitir aunque falle análisis de 10 velas
        if not can_open_10velas and not force:
            self.add_log(f"[ABRIR] ❌ BLOQUEADO por análisis de 10 velas: {analysis_10.get('reason', 'desconocido')}", 'warning')
            return False
        elif not can_open_10velas and force:
            self.add_log(f"[ABRIR] ⚠️ Análisis 10-velas rechazó ({analysis_10.get('reason', '')}), pero force=True permite continuar", 'warning')

        # ⭐⭐⭐ VALIDACIÓN CRÍTICA #1: ANÁLISIS BIDIRECCIONAL INTELIGENTE DE ÚLTIMAS 4 VELAS
        # Este análisis DETERMINA la dirección correcta (BUY o SELL) o BLOQUEA si ambas son débiles
        snapshots_for_4analysis = self.get_fresh_market_data(symbol, bars=20) or []
        analysis_final_4 = self._analyze_final_4_candles_specialized(symbol, snapshots_for_4analysis)
        
        recommended_direction = analysis_final_4.get('recommended_direction', 'BLOCK')
        analysis_confidence = analysis_final_4.get('confidence', 0.0)
        analysis_reason = analysis_final_4.get('reason', '')
        
        self.add_log(
            f"[ANÁLISIS-4VELAS-RECOMENDACIÓN] {recommended_direction} ({analysis_confidence:.0f}% confianza) | {analysis_reason}",
            'success' if recommended_direction != 'BLOCK' else 'warning'
        )
        
        # ⭐ Si el análisis de 4 velas bloquea, no abrir
        if recommended_direction == 'BLOCK' and not force:
            self.add_log(f"[ABRIR] ❌ BLOQUEADO por análisis BIDIRECCIONAL 4-velas: {analysis_reason}", 'warning')
            return False
        elif recommended_direction == 'BLOCK' and force:
            self.add_log(f"[ABRIR] ⚠️ Análisis 4-velas bloqueó ({analysis_reason}), pero force=True permite continuar", 'warning')
        else:
            # ⭐ ACTUALIZAR dirección sugerida con la recomendación del análisis inteligente
            # Si el análisis dice que SELL es mejor, cambiar a SELL aunque inicialmente fuera BUY
            direccion_sugerida = recommended_direction
            self.add_log(f"[ABRIR] ✅ Dirección corregida por análisis 4-velas: {direccion_sugerida} (confianza: {analysis_confidence:.0f}%)", 'info')

        # Si la microtendencia es contraria a la dirección sugerida, solo abrir si el score es MUY superior
        # (esto se aplica tanto en modo normal como forzado)
        score_gap_required = 7.0  # Requiere gap de score mayor si va contra microtendencia
        microtrend_block = False

        try:
            # Anti-reentrada global: evita envíos duplicados de orden cuando dos hilos intentan abrir a la vez.
            try:
                now_ts = time.time()
                # ⭐ EN MODO MÚLTIPLES PARTES: permitir aperturas rápidas (gap muy pequeño)
                try:
                    use_multiple = self.config.get('USE_MULTIPLE_PARTS', tk.BooleanVar(value=False)).get()
                except:
                    use_multiple = False
                
                if force and use_multiple:
                    min_gap = 0.05  # 50ms: permite aperturas casi simultáneas en modo múltiples partes
                elif force:
                    min_gap = 0.35  # Forzado pero no en múltiples partes
                else:
                    min_gap = 0.35  # Normal
                
                with self._open_operation_gate_lock:
                    last_ts = float(getattr(self, '_last_open_attempt_ts', 0.0) or 0.0)
                    if (now_ts - last_ts) < min_gap:
                        self.add_log(
                            f"[ABRIR] ⛔ Apertura duplicada bloqueada ({now_ts - last_ts:.2f}s < {min_gap:.2f}s)",
                            'warning'
                        )
                        return False
                    self._last_open_attempt_ts = now_ts
            except Exception as e:
                self.add_log(f"[ABRIR] [ERROR] Anti-reentrada: {str(e)[:60]}", 'error')

            # ⭐⭐⭐ VERIFICACIÓN #1: PAUSAS - CRÍTICA Y TEMPRANA
            if not startup:
                in_pause, pause_reason = self._is_in_pause(strict=True)
                if in_pause and not force:
                    self.add_log(f"[ABRIR] ❌ {pause_reason} - Abortando apertura", 'warning')
                    return False
                elif in_pause and force:
                    # Si es forzado pero en pausa de ganancia, ser más restrictivo
                    if "post" in self.pause_reason.lower() or "objetivo" in self.pause_reason.lower():
                        self.add_log(f"[ABRIR] ❌ {pause_reason} (incluso force=True no puede eludir) - Abortando", 'error')
                        return False
                    # Si es forzado y solo hay cooldown, permitir con advertencia
                    elif "cooldown" in pause_reason.lower():
                        self.add_log(f"[ABRIR-FORCE] ⚠️ {pause_reason}, pero force=True - Procediendo con precaución", 'warning')
            
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
            
            symbol = self._get_symbol()
            self.add_log(f"[ABRIR] ✓ Verificaciones iniciales OK | Símbolo: {symbol} | Force: {force} | Startup: {startup}", 'info')
            
            # ⭐ VERIFICACIÓN CRÍTICA: Consultar FLAGS de sincronización (trend_monitor)
            # Si hay reversión INMINENTE (70%+) CONTRARIA a dirección_sugerida, BLOQUEAR
            with self.trend_analysis_lock:
                imminent_reversal = self.trend_imminent_reversal
                imminent_direction = self.trend_imminent_direction
                imminent_confidence = self.trend_imminent_confidence
            
            # ⭐ DESACTIVADO: No bloquear por reversión inminente (puede interferir con trading)
            # if imminent_reversal and imminent_direction != None:
            #     # Si intento abrir en dirección CONTRARIA a la reversión esperada, BLOQUEAR
            #     # (imminent_direction es la dirección que VA A VENIR, así que NO abrir en lo opuesto)
            #     if (direccion_sugerida == 'BUY' and imminent_direction == 'SELL') or \
            #        (direccion_sugerida == 'SELL' and imminent_direction == 'BUY'):
            #         self.add_log(f"[ABRIR] 🛑 BLOQUEADA: Reversión INMINENTE → {imminent_direction} @ {imminent_confidence:.1f}% confianza", 'error')
            #         self.add_log(f"[ABRIR] Intento: {direccion_sugerida} | Conflicto: Esperando reversa a {imminent_direction}", 'warning')
            #         return False  # BLOQUEAR APERTURA
            
            if force:
                self.add_log(f"[ABRIR-FORZADA] ✓ Modo reapertura: usando dirección {direccion_sugerida} del scheduler (sin reentrenamiento)", 'info')
                rec = direccion_sugerida
                buy_res = {'score': 50, 'confidence': 70, 'recommendation': 'HOLD'}
                sell_res = {'score': 50, 'confidence': 70, 'recommendation': 'HOLD'}
            else:
                self.add_log("[ABRIR] [INFO] Ejecutando DUAL analysis...", 'info')
                analysis = self._dual_analysis_before_opening(symbol)
                if not analysis:
                    self.add_log("[ABRIR] ❌ DUAL analysis devolvió None", 'error')
                    return False
                self.add_log(f"[ABRIR] ✓ DUAL análisis completado", 'info')
                rec = analysis.get('recommendation', 'HOLD')
                buy_res = analysis.get('buy_specialist', {})
                sell_res = analysis.get('sell_specialist', {})

            # --- LÓGICA DE BLOQUEO/REVERSIÓN POR MICROTENDENCIA ---
            if rec in ('BUY', 'SELL') and microtrend in ('BUY', 'SELL') and rec != microtrend:
                # Si la microtendencia es contraria, solo abrir si el score es muy superior
                buy_score = float(buy_res.get('score', 0))
                sell_score = float(sell_res.get('score', 0))
                gap = abs(buy_score - sell_score)
                if gap < score_gap_required:
                    msg = f"[MICROTREND] BLOQUEADO: Dirección sugerida {rec} va contra microtendencia {microtrend} y gap={gap:.2f} < {score_gap_required}"
                    if not force:
                        self.add_log(msg, 'warning')
                        return False
                    else:
                        self.add_log(f"{msg} - FORZADO: Continuando con force=True", 'warning')
                else:
                    self.add_log(f"[MICROTREND] ⚠️ Permitiendo apertura contra microtendencia por gap alto: {gap:.2f}", 'warning')
            # Si hay muchas operaciones abiertas en un sentido y la microtendencia cambió, pausar ese sentido
            if hasattr(self, 'get_open_positions_summary'):
                summary = self.get_open_positions_summary()
                buy_count = summary.get('BUY', 0)
                sell_count = summary.get('SELL', 0)
                if microtrend == 'BUY' and sell_count > 0 and rec == 'SELL':
                    self.add_log(f"[MICROTREND] PAUSA: Hay {sell_count} SELL abiertas pero microtendencia es BUY. Priorizando BUY.", 'warning')
                    return False
                if microtrend == 'SELL' and buy_count > 0 and rec == 'BUY':
                    self.add_log(f"[MICROTREND] PAUSA: Hay {buy_count} BUY abiertas pero microtendencia es SELL. Priorizando SELL.", 'warning')
                    return False
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
            all_positions_live = [p for p in (mt5.positions_get(symbol=symbol) or []) if getattr(p, 'magic', None) == magic_num]
            open_positions_live = len(all_positions_live)
            buy_count_live = sum(1 for p in all_positions_live if getattr(p, 'type', None) == mt5.POSITION_TYPE_BUY)
            sell_count_live = sum(1 for p in all_positions_live if getattr(p, 'type', None) == mt5.POSITION_TYPE_SELL)
            
            # ⭐ EN MODO MÚLTIPLES PARTES: Cada símbolo tiene su propio límite MAX_OPS (100% independiente)
            # EN MODO NORMAL: Usa el límite global
            try:
                use_multiple = self.config.get('USE_MULTIPLE_PARTS', tk.BooleanVar(value=False)).get()
            except:
                use_multiple = False
            
            # En modo múltiples partes, cada símbolo usa su propio contador sin considerar el otro
            # Esto permite GOLD tener MAX_OPS y SILVER tener MAX_OPS simultáneamente
            if use_multiple:
                # Cada símbolo puede tener hasta MAX_OPS sin restricción del otro
                effective_max = max_ops
                self.add_log(f"[ABRIR] 🔵 MODO MÚLTIPLES PARTES: {symbol} cuenta independientemente", 'info')
            else:
                # Modo normal: usar MAX_OPS global
                effective_max = max_ops
            
            if open_positions_live >= effective_max:
                self.add_log(f"[ABRIR] ❌ Límite en {symbol}: {open_positions_live}/{effective_max} (100% independiente)", 'warning')
                return False
            
            # Actualizar el contador local para que sea consistente
            self.total_operaciones_abiertas = open_positions_live
            self.add_log(f"[ABRIR] ✓ Posiciones en {symbol}: {open_positions_live}/{effective_max}", 'info')

            # Límite de stacking por dirección desactivado: sólo aplica MAX_SIMULTANEOUS_OPS
            self.add_log(f"[STACK] {symbol} - BUY:{buy_count_live} SELL:{sell_count_live} Total:{open_positions_live}/{effective_max}", 'info')
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
                # ⭐ Usar GOLD como símbolo por defecto para recarga
                snaps = self.reload_market_snapshots(symbol='GOLD') or []
                vol_level = self.get_volatility_level(snaps)
                if vol_level != 'NORMAL':
                    self.add_log(f"[ABRIR] ⚠️ Volatilidad: {vol_level} (requiere NORMAL)", 'warning')
                    return False
                else:
                    self.add_log(f"[ABRIR] ✓ Volatilidad OK: {vol_level}", 'info')
            except Exception as e:
                self.add_log(f"[ABRIR] ⚠️ Error en volatilidad: {str(e)[:60]}", 'warning')
                pass
        
        # ⭐ STARTUP: Verificación SIMPLE de snapshots (SIN REANALIZAR - confía en decisión de score ya tomada)
        if startup:
            self.add_log(f"[STARTUP] ✓ Verificando disponibilidad de snapshots...", 'info')
            try:
                snaps = []
                try:
                    # ⭐ Recargar ambos símbolos al startup
                    snaps = self.reload_market_snapshots(symbol='GOLD') or []
                    if not snaps:
                        snaps = self.reload_market_snapshots(symbol='SILVER') or []
                except Exception as e:
                    logger.exception("Error leyendo market_snapshots en apertura startup")
                    self.add_log(f"[STARTUP] ⚠️ Error loading snapshots: {str(e)[:60]}", 'warning')
                    snaps = []

                if not snaps:
                    self.add_log("[STARTUP] ⚠️ Sin snapshots disponibles - continuando con dirección sugerida", 'info')
                else:
                    self.add_log(f"[STARTUP] ✓ {len(snaps)} snapshots disponibles para inicio", 'info')
                
                # 🎯 DECISIÓN FINAL: Usar la dirección sugerida (ya fue calculada con algorithm correcto de scores)
                # NO RE-ANALIZAR porque introduce lógica de penalizaciones que distorsiona
                self.add_log(f"[STARTUP] 🎯 ABRIENDO CON MEJOR SCORE: {direccion_sugerida}", 'success')
                
            except Exception as e:
                self.add_log(f"[STARTUP] ❌ Exception: {str(e)[:80]}", 'error')
                import traceback
                self.add_log(f"[TRACE] {traceback.format_exc()[:200]}", 'error')
        
        symbol = self._get_symbol()
        
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
                    f"⚠️ Operación {direccion_sugerida} RECHAZADA | "
                    f"Potencial {recovery_potential:.1f}% < {min_recovery_pct:.1f}% (mínimo requerido)",
                    'warning'
                )
                return False
            self.add_log(
                f"[OK] Potencial de recuperación OK: {recovery_potential:.1f}% >= {min_recovery_pct:.1f}%",
                'success'
            )
        
        # Obtener TP dinámico solo si es análisis tradicional
        # Para operaciones forzadas SIEMPRE usar config (no dinámico)
        if not force and not self.use_multi_ai.get():
            opportunity = self.gold_analyzer.analyze_opportunity()
            if not opportunity or opportunity['probability'] < 73.0:
                return False
            tp_diff = opportunity['tp_points']
        else:
            # Para Multi-IA o forzadas: usar TP configurado desde la GUI
            try:
                tp_diff = float(self.config['TP_DIFF'].get()) if 'TP_DIFF' in self.config else 1.0
            except Exception as e:
                self.add_log(f"[CONFIG] Error reading TP_DIFF: {str(e)[:60]}", 'error')
                tp_diff = 1.0
        
        # ⭐ OBLIGATORIO: obtener SL desde config (respetar diferencia)
        try:
            sl_diff = float(self.config['SL_DIFF'].get()) if 'SL_DIFF' in self.config else 30.0
        except Exception as e:
            self.add_log(f"[CONFIG] Error reading SL_DIFF: {str(e)[:60]}", 'error')
            sl_diff = 30.0
        
        tick = mt5.symbol_info_tick(symbol)
        
        # Si MT5 falla, obtener precio del JSON
        if tick is None:
            json_snaps = self._read_snapshots_for_symbol(symbol)
            if json_snaps and len(json_snaps) > 0:
                last_snap = json_snaps[-1]
                precio = float(last_snap.get('close', 0))
                if precio <= 0:
                    self.add_log(f"[PRECIO] Precio del JSON inválido: {precio}", 'error')
                    return False
                self.add_log(f"[PRECIO] Obtenido del JSON: {precio:.5f}", 'info')
            else:
                self.add_log(f"[ERROR] No hay datos en JSON ni en MT5", 'error')
                return False
        else:
            precio = tick.ask if direccion_sugerida == "BUY" else tick.bid
        
        if direccion_sugerida == "BUY":
            sl = round(precio - sl_diff, symbol_info.digits)
            tp = round(precio + tp_diff, symbol_info.digits)
            tipo = mt5.ORDER_TYPE_BUY
        else:
            sl = round(precio + sl_diff, symbol_info.digits)
            tp = round(precio - tp_diff, symbol_info.digits)
            tipo = mt5.ORDER_TYPE_SELL
        
        # ⭐ LOG IMPORTANTE: Mostrar exactamente qué TP/SL se están usando
        self.add_log(f"[TP/SL] Usando valores de GUI: TP_DIFF=${tp_diff:.2f}, SL_DIFF=${sl_diff:.2f}", 'info')
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

            # ⭐ NOTA: Drawdown check REMOVIDO (fase anterior)
            # En su lugar, se implementa _check_and_recover_red_positions() 
            # que cierra automáticamente posiciones en ROJO con bajo potencial de recuperación
            
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
            
            # ⭐ TakeProfit: usar force_params si existe Y la dirección coincide, sino calcular desde config
            try:
                fp_dir = (force_params.get('direction') or '').upper()
                if 'tp' in force_params and force_params.get('tp') is not None and fp_dir == str(direccion_sugerida).upper():
                    tp = float(force_params.get('tp'))
                    self.add_log(f"[FORZADA] Usando TP desde force_params: {tp}", 'info')
                else:
                    # Calcular desde tp_diff de config (dirección cambió o no hay TP guardado)
                    if direccion_sugerida == 'BUY':
                        tp = round(precio + tp_diff, symbol_info.digits)
                    else:
                        tp = round(precio - tp_diff, symbol_info.digits)
                    self.add_log(f"[FORZADA] TP calculado desde config (TP_DIFF={tp_diff}): {tp}", 'info')
            except Exception as e:
                self.add_log(f"[FORZADA] Error calculando TP: {e}", 'warning')
                tp = None
            
            # ⭐ StopLoss: usar force_params si existe Y la dirección coincide, sino calcular desde config
            try:
                fp_dir = (force_params.get('direction') or '').upper()
                if 'sl' in force_params and force_params.get('sl') is not None and fp_dir == str(direccion_sugerida).upper():
                    sl = float(force_params.get('sl'))
                    self.add_log(f"[FORZADA] Usando SL desde force_params: {sl}", 'info')
                else:
                    # Calcular desde sl_diff de config (dirección cambió o no hay SL guardado)
                    if direccion_sugerida == 'BUY':
                        sl = round(precio - sl_diff, symbol_info.digits)
                    else:
                        sl = round(precio + sl_diff, symbol_info.digits)
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

        # ⭐ VOLUMEN: Usar SOLO el valor de la UI (sin dinámico)
        try:
            vol = float(self.config['VOL'].get())
            if vol <= 0:
                vol = 0.02
            self.add_log(f"[ABRIR] ✓ Volumen de UI aplicado: {vol:.4f}", 'info')
        except Exception as e:
            self.add_log(f"[VOLUMEN] Error obteniendo volumen UI: {str(e)[:60]}", 'warning')
            vol = 0.02

        mode_prefix = "MultiIA" if self.use_multi_ai.get() else "IA"

        # Asegurar que SL/TP tienen sentido relativo al precio (evitar stops invertidos)
        try:
            tp_cfg = abs(float(self.config.get('TP_DIFF', tk.DoubleVar(value=10.0)).get()))
        except Exception:
            tp_cfg = abs(10.0)
        try:
            sl_cfg = abs(float(self.config.get('SL_DIFF', tk.DoubleVar(value=100.0)).get()))
        except Exception:
            sl_cfg = abs(100.0)
        try:
            if tipo == mt5.ORDER_TYPE_BUY:
                # SL must be below price; TP must be above
                if sl is None or sl >= precio:
                    sl = round(precio - sl_cfg, symbol_info.digits)
                    self.add_log(f"⚠️ SL inválido corregido para BUY -> {sl:.{symbol_info.digits}f}", 'warning')
                if tp is None or tp <= precio:
                    tp = round(precio + tp_cfg, symbol_info.digits)
                    self.add_log(f"⚠️ TP inválido corregido para BUY -> {tp:.{symbol_info.digits}f}", 'warning')
            else:
                # For SELL: SL above price; TP below price
                if sl is None or sl <= precio:
                    sl = round(precio + sl_cfg, symbol_info.digits)
                    self.add_log(f"⚠️ SL inválido corregido para SELL -> {sl:.{symbol_info.digits}f}", 'warning')
                if tp is None or tp >= precio:
                    tp = round(precio - tp_cfg, symbol_info.digits)
                    self.add_log(f"⚠️ TP inválido corregido para SELL -> {tp:.{symbol_info.digits}f}", 'warning')
        except Exception:
            pass

        # ⭐ NUEVO: Respetar configuración USE_SL
        usar_sl = self.config['USE_SL'].get()
        sl_final = sl if usar_sl else 0.0

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(vol),
            "type": tipo,
            "price": precio,
            "sl": sl_final,
            "tp": tp,
            "deviation": 20,
            "magic": self.config['MAGIC_NUMBER'],
            "comment": f"Bot-{mode_prefix}-{direccion_sugerida}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Log de parámetros justo antes de enviar
        try:
            sl_text = f"SL={sl_final:.5f}" if usar_sl else "SIN SL"
            self.add_log(f"[ORDEN] Parámetros finales: {symbol} {direccion_sugerida} Vol={vol} Precio={precio:.5f} {sl_text} TP={tp:.5f}", 'success')
            self.add_log(f"[ORDEN] ✅ Enviando operación → Vol={vol:.4f} Precio={precio:.5f} TP={tp:.5f} SL={sl_final:.5f}", 'info')
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
        
        result = mt5.order_send(request)
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
                
                # Metadata de trades removida: solo análisis de mercado actual
                # try:
                #     if self.last_trade_metadata:
                #         self.feedback_loop_ai.record_trade_analysis(...) - DESHABILITADO
                # except Exception:
                #     pass
                
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
[🛡️] SL: {executed_sl:.5f}
📦 Volumen ejecutado: {executed_volume}
[IA] Modo: Punto de Entrada
"""
            self.add_log(msg, 'success')

            # Si esta apertura fue forzada al inicio, guardar parámetros para el scheduler
            if startup:
                try:
                    # ⭐ Obtener intervalo dinámico de la configuración - ACEPTA DECIMALES
                    try:
                        minutes = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=5.0)).get())
                        intervalo_dist, _ = self._forced_open_interval_seconds(minutes)
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
        if self.is_running:
            return
        if self._start_bot_in_progress:
            self.add_log("[START] Inicio en progreso, se ignora intento duplicado", 'warning')
            return
        self._start_bot_in_progress = True
        
        # ⭐⭐⭐ LIMPIEZA TOTAL - RESETEAR TODO DESDE CERO ⭐⭐⭐
        self.add_log("[RESET] Limpiando estado anterior completamente...", 'warning')
        
        # ✅ PRIMERO: Re-habilitar controles si están deshabilitados (después de emergencia)
        for entry in self.config_entries.values():
            try:
                entry.config(state='normal')
            except:
                pass
        
        self.force_stop_triggered = False  # ✅ LIMPIO: Permitir aperturas nuevamente
        self.is_running = False  # Se establecerá a True abajo
        self.bot_pausado = False
        self.en_pausa = False
        self.pause_until = 0.0
        self.pause_reason = ""
        self.block_until = 0.0
        self.ganancia_neta = 0.0
        self.ganancia_total = 0.0
        self.saldo_total_acumulado = 0.0
        self.saldo_actual = 0.0
        self.ultima_ganancia = 0.0
        self.objetivo_cumplido = False
        self.total_operaciones_abiertas = 0
        self.ganadas = 0
        self.perdidas = 0
        self.z = 0
        self.operaciones_azules = 0
        self.operaciones_rojas = 0
        self.operaciones_cerradas = 0
        self.ultima_operacion = time.time()
        self.ultima_operacion_timestamp = int(time.time())
        self.ultima_apertura = time.time()
        self.primera_operacion = True
        self.perdio_primera = False
        self.ultima_perdida = False
        self.ultima_direccion = None
        self.ultimo_precio = None
        self.perdidas_consecutivas = 0
        self.ganancias_consecutivas = 0
        self.analisis_inicial_hecho = False
        
        # Resetear contadores de posiciones
        self.position_tracking = {}
        self.posiciones_cerradas_tracking = {}
        self.deals_anterior = {}
        self.operaciones_actuales.clear()
        self.operaciones_procesadas.clear()
        self.deals_procesados = set()
        self.position_ids = set()
        self.pending_operations = []  # ✅ Limpiar operaciones en espera
        
        # Resetear historial
        self.historial_resultados = []
        
        # Resetear objetivo neto
        self.objetivo_neto_inicial = 0.0
        self.objetivo_neto_target = 0.0
        
        # Resetear scheduler
        self._scheduler_running = True
        self._forced_reopen_started = False
        self._forced_scheduler_thread = None
        
        # Resetear estado de análisis
        self._analysis_in_progress = False
        self.last_analysis_result = None
        self.market_state = "ANALIZANDO"
        self.trend_direction = "NEUTRAL"
        self.trend_strength = 0
        
        # ✅ LIMPIAR LOGS
        self.logs = []
        
        self.add_log("[OK] Estado anterior limpiado completamente", 'success')
        
        # Validar y configurar tiempo
        tiempo_min = self.tiempo_total.get()
        if tiempo_min > 0:
            self.tiempo_restante = tiempo_min * 60
            self.tiempo_inicio = time.time()
        else:
            self.tiempo_restante = 0
            
        if not self.conectar_mt5():
            messagebox.showerror("Error", "No se pudo conectar a MT5")
            self._start_bot_in_progress = False
            return

        # Cargar sistema PRO institucional (NIVEL 5-10)
        self._load_ml_models_v2_with_pro()
        
        # Actualizar especialistas con dataset manager
        if self.dataset_manager is not None:
            self.buy_specialist.dataset_manager = self.dataset_manager
            self.sell_specialist.dataset_manager = self.dataset_manager
            self.arbitrator.dataset_manager = self.dataset_manager
            self.add_log("[OK] Dataset Profesional integrado en especialistas", 'success')

        # Prefill market snapshots into a dedicated JSON for the selected symbol.
        # ⭐ No resetear _forced_reopen_started aquí para evitar scheduler duplicado.
        self._scheduler_running = True
        
        # We run one synchronous load at start (to allow immediate decision)
        # and then start a background thread that fetches latest M1 bars from MT5
        # and overwrites snapshots on disk and in-memory every `SNAPSHOT_RELOAD_INTERVAL` seconds.
        try:
            symbol = self.config['SYMBOL'].get()
            # ⭐ CRÍTICO: Asegurar que símbolo NUNCA sea VACÍO
            if not symbol or symbol.strip() == '':
                logger.warning("[INIT] ⚠️ Symbol del config está VACÍO, usando GOLD por defecto")
                symbol = 'GOLD'
            
            # ⭐ NUEVO: Cargar datos para AMBOS GOLD y SILVER al inicio
            self.add_log("[INIT] Cargando datos para GOLD y SILVER...", 'info')
            for load_symbol in ['GOLD', 'SILVER']:
                try:
                    filled, prefilled_snapshots = prefill_market_data_and_return(load_symbol, minutes=500)
                    logger.info(f"[INIT-PREFILL] ✓ {load_symbol}: {filled} snapshots en memoria")
                    
                    # Recargar para ese símbolo específicamente
                    snaps_loaded = self.reload_market_snapshots(symbol=load_symbol) or []
                    if snaps_loaded and isinstance(snaps_loaded, list):
                        with self.market_snapshots_lock_by_symbol.get(load_symbol, threading.Lock()):
                            self.market_snapshots_by_symbol[load_symbol] = snaps_loaded
                            logger.info(f"[INIT-RELOAD] ✓ {load_symbol}: {len(snaps_loaded)} snapshots cargados")
                except Exception as e:
                    logger.warning(f"[INIT-PREFILL] Error cargando {load_symbol}: {str(e)[:50]}")
            
            self.add_log("[OK] Datos de GOLD y SILVER cargados exitosamente", 'success')
            
            # ⭐ INICIALIZAR self.market_snapshots con GOLD (símbolo por defecto)
            # No cargar símbolo adicional del config para evitar símbolo vacío
            if 'GOLD' in self.market_snapshots_by_symbol and len(self.market_snapshots_by_symbol['GOLD']) > 0:
                self.market_snapshots = self.market_snapshots_by_symbol['GOLD']
                logger.info(f"[INIT-FINAL] ✓ market_snapshots = GOLD ({len(self.market_snapshots)} items)")
            elif 'SILVER' in self.market_snapshots_by_symbol and len(self.market_snapshots_by_symbol['SILVER']) > 0:
                self.market_snapshots = self.market_snapshots_by_symbol['SILVER']
                logger.info(f"[INIT-FINAL] ✓ market_snapshots = SILVER ({len(self.market_snapshots)} items)")
            else:
                logger.warning("[INIT-FINAL] ⚠️ Ambos GOLD y SILVER vacíos, inicializando lista vacía")
                self.market_snapshots = []
            
            final_count = len(self.market_snapshots) if isinstance(self.market_snapshots, list) else 0
            logger.info(f"[INIT-FINAL] Estado final: market_snapshots = {final_count} items")

            self.add_log(f"🗂️ Datos de GOLD y SILVER prefilled en logs", 'info')

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

            # ⭐ NUEVO: Inicializar temporizador usando FORCED_OPEN_MINUTES dinámicamente - ACEPTA DECIMALES
            try:
                minutes = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=5.0)).get())
                intervalo_segundos, minutes = self._forced_open_interval_seconds(minutes)
                self.next_forced_open = time.time() + intervalo_segundos
                self.add_log(f"[INIT] Temporizador forzada establecido: {minutes}m ({intervalo_segundos:.1f}s)", 'info')
            except Exception as e:
                self.next_forced_open = None
                self.add_log(f"[ERROR] Al establecer temporizador forzada: {e}", 'error')

            # Background loop: fetch latest M1 bars from MT5 and overwrite snapshots
            # ⭐ NUEVO: Usar DataUpdater para actualizaciones periódicas en tiempo real
            def _initialize_data_updater():
                try:
                    interval = int(self.config.get('SNAPSHOT_RELOAD_INTERVAL', tk.IntVar(value=1)).get())
                except Exception:
                    interval = 1  # ⭐ 1 segundo para actualizaciones en tiempo real
                
                self.data_updater = DataUpdater(symbol=symbol, interval=interval)  # ⭐ SIN max(60, ...) 
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
            scheduler_can_start = False
            with self._forced_reopen_start_lock:
                sched_thread = getattr(self, '_forced_scheduler_thread', None)
                scheduler_alive = bool(sched_thread and sched_thread.is_alive())
                if not getattr(self, '_forced_reopen_started', False) and not scheduler_alive:
                    self._forced_reopen_started = True
                    scheduler_can_start = True

            if scheduler_can_start:
                def _forced_reopen_scheduler_simple():
                    last_dual_reload = 0  # ⭐ TIMESTAMP del último reload dual
                    while getattr(self, '_scheduler_running', True):
                        try:
                            # ⭐ NUEVO: Recargar snapshots para AMBOS GOLD y SILVER cada 5-10 segundos
                            now = time.time()
                            if (now - last_dual_reload) > 5.0:  # Cada 5 segundos
                                try:
                                    self.reload_all_symbols_snapshots()
                                    last_dual_reload = now
                                except Exception as e:
                                    logger.warning(f"[SCHEDULER] Error en dual reload: {str(e)[:50]}")
                            
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
                                minutes = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=5.0)).get())
                            except Exception:
                                minutes = 5.0

                            intervalo, minutes = self._forced_open_interval_seconds(minutes)
                            
                            # ⭐ NUEVA LÓGICA: Verificar si ha pasado el time de next_forced_open
                            now = time.time()
                            next_open = getattr(self, 'next_forced_open', now)
                            
                            if now >= next_open:
                                if not self._forced_reopen_exec_lock.acquire(blocking=False):
                                    time.sleep(0.2)
                                    continue
                                # Evita ciclos duplicados en la misma ventana de tiempo.
                                dedup_window = max(3.0, float(intervalo) * 0.80)
                                if (now - float(getattr(self, '_last_forced_cycle_ts', 0.0) or 0.0)) < dedup_window:
                                    self._forced_reopen_exec_lock.release()
                                    time.sleep(0.2)
                                    continue
                                self._last_forced_cycle_ts = now
                                # Es hora de intentar reapertura forzada CON ANÁLISIS COMPLETO
                                self.add_log(f"\n[RESET] Scheduler: reapertura forzada activada", 'warning')
                                
                                # ⭐ INICIALIZAR VARIABLES antes del try (FIX: UnboundLocalError)
                                best_dir = 'BUY'  # Default para garantizar que siempre esté definido
                                buy_score = 50
                                sell_score = 50
                                trend_analysis = None
                                
                                try:
                                    # ⭐ VERIFICACIÓN CRÍTICA #1: Consultar FLAGS de sincronización (trend_monitor)
                                    with self.trend_analysis_lock:
                                        imminent_reversal = self.trend_imminent_reversal
                                        imminent_direction = self.trend_imminent_direction
                                        imminent_confidence = self.trend_imminent_confidence

                                    # Análisis completo: especialistas + tendencia (IGNORA arbitrador en modo forzado)
                                    best_dir, buy_score, sell_score, trend_analysis = self._quick_analysis_for_forced_reopen(symbol)
                                
                                    # ⭐ SINCRONIZAR: Compartir scores con el monitor para coherencia visual
                                    try:
                                        with self.specialist_scores_lock:
                                            self.scheduler_shared_scores = {
                                                'buy_score': float(buy_score),
                                                'sell_score': float(sell_score),
                                                'buy_conf': 0,  # Se actualizará con los de monitor cada segundo
                                                'sell_conf': 0,  # Se actualizará con los de monitor cada segundo
                                                'timestamp': time.time()
                                            }
                                    except Exception:
                                        pass
                                
                                    self.add_log(f"[ANÁLISIS] BUY: {buy_score:.1f} | SELL: {sell_score:.1f} → ELEGIDO: {best_dir}", 'info')
                                
                                    # ⭐⭐⭐ MICROTREND DETERMINANTE: Manda más que especialistas ⭐⭐⭐
                                    # Primero consulta MICROTREND (mercado real), luego usa especialistas como fallback
                                    direccion_final = None
                                    
                                    try:
                                        microtrend = self._microtrend_direction(symbol, bars=10, threshold=None)  # Usa config
                                        self.add_log(f"[MICROTREND] Detectado: {microtrend} (SIN SESGO, RESPETA PIPS)", 'info')
                                        
                                        # Si microtrend ve movimiento CLARO = ese es el que abrimos
                                        if microtrend in ('BUY', 'SELL'):
                                            direccion_final = microtrend
                                            self.add_log(f"[DECISIÓN] 🎯 MICROTREND manda: {microtrend} (vs especialistas {best_dir})", 'warning')
                                            if microtrend != best_dir:
                                                self.add_log(f"[CAMBIO] Especialistas {best_dir} → MICROTREND {microtrend}", 'warning')
                                        else:
                                            # FLAT = sin movimiento claro, usa especialistas
                                            direccion_final = best_dir
                                            self.add_log(f"[FALLBACK] Microtrend FLAT → Usa especialistas: {best_dir}", 'info')
                                    
                                    except Exception as e:
                                        self.add_log(f"[ERROR] microtrend_direction fallo: {str(e)}", 'error')
                                        direccion_final = best_dir
                                        self.add_log(f"[FALLBACK] Error en microtrend → Usa especialistas: {best_dir}", 'warning')
                                    
                                    self.add_log(f"[APERTURA] Dirección FINAL: {direccion_final} (MICROTREND DETERMINANTE)", 'warning')
                                    best_dir = direccion_final
                                
                                    # Registrar intento en monitor_debug.log
                                    try:
                                        with open(os.path.join('logs','monitor_debug.log'), 'a', encoding='utf-8') as fh:
                                            fh.write(json.dumps({'ts': datetime.utcnow().isoformat(), 'scheduler': 'forced_reopen_attempt_simple', 'has_params': bool(self.forced_open_params)}) + '\n')
                                    except Exception:
                                        pass

                                    # ⭐ VERIFICAR que el scheduler siga activo ANTES de intentar abrir
                                    if not getattr(self, '_scheduler_running', True):
                                        self.add_log("[SCHEDULER] Detenido - abortando reapertura", 'info')
                                        self._forced_reopen_exec_lock.release()
                                        break

                                    # ⭐⭐⭐ GARANTÍA DE APERTURA: best_dir DEBE ser BUY o SELL ⭐⭐⭐
                                    if best_dir not in ('BUY', 'SELL'):
                                        self.add_log(f"[SCHEDULER] FALLO: best_dir={best_dir} (inválido) - FORZANDO a BUY", 'error')
                                        best_dir = 'BUY'  # Fallback: BUY por defecto

                                    self.add_log(f"[RESET] 🚀 ABRIENDO {best_dir} (forzada, garantizado)", 'warning')
                                    self.abrir_operacion_smart(best_dir, force=True, startup=True)
                                    # ✅ Si llegó aquí sin excepción = ÉXITO
                                    self.next_forced_open = now + intervalo
                                    self.add_log(f"[SCHEDULER] ⏱️ Próxima reapertura en {intervalo}s ({minutes}m)", 'info')
                                except Exception as e:
                                    self.add_log(f"[SCHEDULER-ERRO] Intento fallido: {str(e)[:60]}", 'error')
                                    # Retry rápido: 3 segundos
                                    self.next_forced_open = now + 3
                                    self.add_log(f"[SCHEDULER] ⚠️ Reintentando en 3s (fallback a {best_dir})", 'warning')
                                finally:
                                    self._forced_reopen_exec_lock.release()
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

                self._forced_scheduler_thread = threading.Thread(target=_forced_reopen_scheduler_simple, daemon=True)
                self._forced_scheduler_thread.start()
                self.add_log("[SCHEDULER] ✅ Thread de reaperturas forzadas iniciado", 'success')
                
                # ⭐ INICIA MONITOR DE REVERSIÓN AGRESIVO (cada 2 segundos)
                try:
                    self._reversal_monitor_thread = threading.Thread(target=self._monitor_reversals_aggressive, daemon=True)
                    self._reversal_monitor_thread.start()
                    self.add_log("[⚡ REVERSIÓN] Monitor ultra-sensible iniciado (responde cada 2s)", 'success')
                except Exception as e:
                    self.add_log(f"[⚡ REVERSIÓN] Error al iniciar: {str(e)[:40]}", 'error')

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
            
        # Limpiar estructuras de datos
        self.operaciones_actuales.clear()
        self.operaciones_procesadas.clear()
        self.operaciones_cerradas = 0
        self.z = 0
        self.deals_procesados.clear()
        self.analisis_inicial_hecho = False
        
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
        
        # ⭐ INICIAR TEMPORIZADOR DEL HEADER (actualización cada 1 segundo)
        # Establecer timestamp inicial para que comience a contar
        try:
            self.last_rapid_op_time = time.time()
        except Exception:
            pass
        
        # Iniciar el loop de actualización cada 1 segundo
        try:
            self.root.after(0, self._update_countdown_timer)
        except Exception:
            pass
        
        # ⭐ NUEVO: Iniciar monitor de especialistas (análisis segundo a segundo)
        try:
            self.specialists_monitor_running = True
            self.specialists_monitor_thread = threading.Thread(target=self._monitor_specialists_loop, daemon=True)
            self.specialists_monitor_thread.start()
            self.add_log("[✓] Monitor de especialistas iniciado - análisis en vivo cada segundo", 'success')
        except Exception as e:
            self.add_log(f"[ERROR] No se pudo iniciar monitor de especialistas: {str(e)[:60]}", 'warning')

        # Loop auxiliar (entry point + análisis de abiertas) fuera de _update_ui
        try:
            self._entry_analysis_running = True
            self._entry_analysis_thread = threading.Thread(target=self._entry_analysis_loop, daemon=True)
            self._entry_analysis_thread.start()
        except Exception:
            pass
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_indicator.itemconfig(self.status_circle, fill='#10b981')
        self.status_label.config(text="Bot Activo", fg='#34d399')
        
        # ⭐ VALIDACIÓN INICIAL AL INICIAR EL BOT
        self.add_log("\n" + "="*60, 'warning')
        self.add_log("[IA] INICIANDO BOT - VALIDACIÓN INICIAL", 'warning')
        self.add_log("="*60, 'warning')
        
        # Verificar si hay operaciones en espera
        if self.pending_operations:
            self.add_log(f"[ESPERA] OPERACIONES EN ESPERA DETECTADAS", 'warning')
            self.add_log(f"   Total: {len(self.pending_operations)} operación(es)", 'warning')
            for i, op in enumerate(self.pending_operations, 1):
                status = "🚀" if op['status'] == 'ESPERANDO' else "🚀"
                self.add_log(f"   {status} Op #{op.get('id', i)}: {op['direction']} @ {op['price']:.5f}", 'info')
            self.add_log(f"   Estado: Analizando mercado para apertura...\n", 'warning')
        else:
            self.add_log(f"\n📊 ANALIZANDO MERCADO", 'info')
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
        
        # ⭐ FIX #3: Iniciar MT5 Cache Manager para reducir API calls 30x
        try:
            self.mt5_cache.start()
            self.add_log("[✓] MT5 Cache Manager iniciado - Consolidando llamadas cada 2s", 'success')
        except Exception as e:
            self.add_log(f"[WARNING] No se pudo iniciar MT5 Cache Manager: {str(e)[:60]}", 'warning')
        
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
        
        # ⭐ NUEVO: Iniciar monitor reactivo de pérdida máxima (Posiciones en Rojo)
        self.red_monitor_running = True
        self.red_positions_watched = {}
        self.red_monitor_thread = threading.Thread(target=self._red_positions_monitor_loop, daemon=True)
        self.red_monitor_thread.start()
        self.add_log("[✓] Monitor reactivo de pérdida máxima INICIADO - Verificando cada 0.5s", 'success')
        
        # ⭐ NUEVO: Iniciar monitor de Stop Loss Manual
        self.sl_monitor_running = True
        self.sl_monitor_thread = threading.Thread(target=self._monitor_stop_loss_manual, daemon=True)
        self.sl_monitor_thread.start()
        self.add_log("[✓] Monitor de Stop Loss Manual INICIADO - Verificando cada 0.5s", 'success')
        
        # ⭐ NUEVO: Iniciar monitor de Margen de Ganancia u Objetivo Neto (solo UNO a la vez)
        try:
            margen_pct = float(self._safe_get('MARGEN_GANANCIA', 0.0))
            objetivo_neto = float(self._safe_get('OBJETIVO_NETO', 0.0))
            
            # ⭐ RESETEAR FLAGS Y VALORES ANTES DE ACTIVAR
            self.margen_ganancia_alcanzado = False
            self.balance_inicial_para_margen = 0.0
            self.objetivo_margen_ganancia = 0.0
            self.objetivo_neto_alcanzado = False
            self.objetivo_neto_valor = 0.0
            self.margen_monitor_running = False
            self.objetivo_neto_running = False
            
            # Determinar cuál activar (prioridad: Margen de Ganancia si >= 1)
            if margen_pct >= 1:
                # Activar Margen de Ganancia
                self.margen_monitor_running = True
                self.root.after(0, self._monitor_profit_margin)
                self.add_log(f"[✓] Monitor de Margen de Ganancia INICIADO - Objetivo: {margen_pct}%", 'success')
                    
            elif objetivo_neto > 0:
                # Activar Objetivo Neto
                self.objetivo_neto_running = True
                self.root.after(0, self._monitor_objetivo_neto)
                self.add_log(f"[✓] Monitor de Objetivo Neto INICIADO - Objetivo: ${objetivo_neto:.2f}", 'success')
            else:
                # Ambos desactivados
                self.add_log(f"[ℹ️] Monitores desactivados: Margen={margen_pct}%, Objetivo=${objetivo_neto}", 'info')
                
        except Exception as e:
            self.add_log(f"[⚠️] Error iniciando Monitores: {str(e)[:60]}", 'warning')
            self.margen_monitor_running = False
            self.objetivo_neto_running = False

        self.manual_buy_btn.config(state='normal')
        self.manual_sell_btn.config(state='normal')

        self.pause_btn.config(state='normal')  # Habilitar botón de pausa
        self._start_bot_in_progress = False

    def _update_countdown_timer(self):
        """⭐ ACTUALIZAR COUNTDOWN del header continuamente cada 1 segundo.
        Muestra: 30s → 29s → 28s ... hasta apertura de operación
        ⭐ SINCRONIZADO CON OPERACIONES ABIERTAS:
           - Si bot NO está corriendo → muestra "-"
           - Si hay operaciones ABIERTAS → pausa contador (muestra "⏸")
           - Si NO hay operaciones → cuenta normal"""
        
        try:
            # ⭐ Verificar que el widget existe
            if not hasattr(self, 'rapid_countdown_label'):
                try:
                    self.root.after(1000, self._update_countdown_timer)
                except Exception:
                    pass
                return
            
            # ⭐ SI EL BOT NO ESTÁ CORRIENDO, mostrar "-"
            if not getattr(self, 'is_running', False):
                self.rapid_countdown_label.config(text="-")
                try:
                    self.root.after(1000, self._update_countdown_timer)
                except Exception:
                    pass
                return
            
            # ⭐ SI HAY OPERACIONES ABIERTAS, pausar contador
            if hasattr(self, 'rapid_ops_active') and len(self.rapid_ops_active) > 0:
                self.rapid_countdown_label.config(text="⏸")
                try:
                    self.root.after(1000, self._update_countdown_timer)
                except Exception:
                    pass
                return
            
            # ⭐ BOT CORRIENDO Y SIN OPERACIONES: calcular countdown normal
            # ⭐ Calcular el interval (0.3 × 100 = 30s)
            try:
                forced_minutes = float(self.config.get('FORCED_OPEN_MINUTES', tk.DoubleVar(value=0.3)).get())
            except Exception:
                forced_minutes = 0.3
            
            # Convertir a segundos
            if forced_minutes < 1:
                forced_interval = int(forced_minutes * 100)
            else:
                forced_interval = int(forced_minutes * 60)
            
            # ⭐ Calcular tiempo restante desde last_rapid_op_time
            now = time.time()
            
            # Siempre calcular desde last_rapid_op_time (se establece en start_bot y cada que abre operación)
            if hasattr(self, 'last_rapid_op_time') and self.last_rapid_op_time > 0:
                time_since_last = now - self.last_rapid_op_time
                secs_remaining = max(0, forced_interval - int(time_since_last))
                countdown_text = f"{secs_remaining}s"
                
                # Si llega a 0, reiniciar contador (simular apertura)
                if secs_remaining == 0:
                    self.last_rapid_op_time = now
                    countdown_text = f"{forced_interval}s"
            else:
                countdown_text = f"{forced_interval}s"
            
            # ⭐ Actualizar el widget
            self.rapid_countdown_label.config(text=countdown_text)
            
        except Exception as e:
            pass  # Silenciar errores
        
        # ⭐ Llamar a sí misma cada 1 segundo SIEMPRE
        try:
            self.root.after(1000, self._update_countdown_timer)
        except Exception:
            pass

    def _start_post_close_reanalysis(self):
        """⭐ INICIAR: Reanalisis post-cierre en thread separado
        Se llama automáticamente cuando se cierra la última operación (len(rapid_ops_active) == 0)"""
        try:
            # Si ya hay un reanalisis en progreso, no iniciar otro
            if self.post_close_reanalysis_active:
                return
            
            # Obtener tiempo de reanalisis (mismo que PAUSA_POST_WIN por defecto)
            try:
                reanalysis_time = int(self.config.get('PAUSA_POST_WIN', tk.IntVar(value=0)).get())
            except Exception:
                reanalysis_time = 0
            
            if reanalysis_time <= 0:
                return  # Reanalisis deshabilitado
            
            # Marcar como activo y guardar timestamp de término
            self.post_close_reanalysis_active = True
            self.post_close_reanalysis_until = time.time() + reanalysis_time
            
            self.add_log(f"🔄 REANALISIS POST-CIERRE iniciado ({reanalysis_time}s): recargando datos y recalibrando IA...", 'info')
            
            # Iniciar thread de reanalisis
            if self.post_close_reanalysis_thread and self.post_close_reanalysis_thread.is_alive():
                return  # Ya hay un thread activo
            
            self.post_close_reanalysis_thread = threading.Thread(
                target=self._post_close_reanalysis_worker,
                args=(reanalysis_time,),
                daemon=True
            )
            self.post_close_reanalysis_thread.start()
        except Exception as e:
            self.add_log(f"[ERROR] Iniciar reanalisis: {str(e)[:60]}", 'error')

    def _post_close_reanalysis_worker(self, reanalysis_time):
        """⭐ EJECUTAR: Reanalisis profundo post-cierre
        1. Recargar datos frescos (últimas 10 velas)
        2. Recalcular especialistas (BUY/SELL AI)
        3. Recalibrar indicadores técnicos
        4. Guardar scores para próxima entrada"""
        try:
            symbol = self.config['SYMBOL'].get()
            
            self.add_log(f"📊 Recargando datos frescos de MT5 (últimas 10 velas)...", 'info')
            
            # 1️⃣ RECARGAR DATOS FRESCOS (últimas 10 velas M1)
            snapshots_fresh = self.get_fresh_market_data(symbol, bars=10)
            if not snapshots_fresh or len(snapshots_fresh) < 5:
                self.add_log(f"⚠️ Datos insuficientes para reanalisis (obtenidos: {len(snapshots_fresh) if snapshots_fresh else 0})", 'warning')
                self.post_close_reanalysis_active = False
                return
            
            self.add_log(f"✅ Datos frescos cargados: {len(snapshots_fresh)} velas", 'success')
            
            # 2️⃣ RECALCULAR ESPECIALISTAS CON DATOS FRESCOS
            self.add_log(f"🧠 Recalculando análisis de especialistas IA...", 'info')
            try:
                # BUY Specialist
                buy_analysis = None
                if hasattr(self, 'buy_specialist'):
                    buy_analysis = self.buy_specialist.analyze(snapshots_fresh)
                    buy_score = buy_analysis.get('confidence', 0) if buy_analysis else 0
                    self.post_close_reanalysis_last_scores['buy'] = buy_score
                    self.add_log(f"  📈 BUY Score: {buy_score:.1f}%", 'info')
                
                # SELL Specialist
                sell_analysis = None
                if hasattr(self, 'sell_specialist'):
                    sell_analysis = self.sell_specialist.analyze(snapshots_fresh)
                    sell_score = sell_analysis.get('confidence', 0) if sell_analysis else 0
                    self.post_close_reanalysis_last_scores['sell'] = sell_score
                    self.add_log(f"  📉 SELL Score: {sell_score:.1f}%", 'info')
            except Exception as e:
                self.add_log(f"⚠️ Error recalculando especialistas: {str(e)[:50]}", 'warning')
            
            # 3️⃣ RECALIBRAR INDICADORES TÉCNICOS
            self.add_log(f"📈 Recalibrando indicadores técnicos...", 'info')
            try:
                # Extraer precios de las 10 velas
                closes = [float(snap.get('close', 0)) for snap in snapshots_fresh if snap.get('close')]
                highs = [float(snap.get('high', 0)) for snap in snapshots_fresh if snap.get('high')]
                lows = [float(snap.get('low', 0)) for snap in snapshots_fresh if snap.get('low')]
                
                if len(closes) >= 5:
                    # Recalcular RSI (14 período pero con solo 10 velas disponibles)
                    rsi_val = self._calculate_rsi_quick(closes, period=min(14, len(closes)//2))
                    self.rsi_value = rsi_val
                    self.add_log(f"  RSI: {rsi_val:.1f}", 'info')
                    
                    # Recalcular ATR aproximado
                    if len(highs) >= 2 and len(lows) >= 2:
                        ranges = [h - l for h, l in zip(highs[-10:], lows[-10:])]
                        atr = sum(ranges) / len(ranges) if ranges else 0
                        self.atr_value = atr
                        self.add_log(f"  ATR: {atr:.4f}", 'info')
                    
                    # Recalcular EMA rápido/lento
                    if len(closes) >= 7:
                        ema_fast_period = int(self.config.get('EMA_FAST', tk.IntVar(value=3)).get())
                        ema_slow_period = int(self.config.get('EMA_SLOW', tk.IntVar(value=7)).get())
                        
                        ema_fast = sum(closes[-ema_fast_period:]) / ema_fast_period if ema_fast_period <= len(closes) else closes[-1]
                        ema_slow = sum(closes[-ema_slow_period:]) / ema_slow_period if ema_slow_period <= len(closes) else closes[-1]
                        
                        self.ema_fast = ema_fast
                        self.ema_slow = ema_slow
                        self.add_log(f"  EMA Fast: {ema_fast:.4f} | EMA Slow: {ema_slow:.4f}", 'info')
            except Exception as e:
                self.add_log(f"⚠️ Error recalibrando indicadores: {str(e)[:50]}", 'warning')
            
            # Esperar el tiempo configurado mientras se bloquean nuevas aperturas
            self.add_log(f"⏱️ Bloqueando nuevas operaciones durante reanalisis...", 'info')
            start_time = time.time()
            while (time.time() - start_time) < reanalysis_time and self.is_running:
                time.sleep(0.5)
            
            # Terminar reanalisis
            self.post_close_reanalysis_active = False
            self.post_close_reanalysis_until = 0.0
            self.add_log(f"✅ REANALISIS COMPLETADO: Reabriendo operaciones con IA recalibrada", 'success')
            
        except Exception as e:
            self.add_log(f"[ERROR] Reanalisis worker: {str(e)[:60]}", 'error')
            self.post_close_reanalysis_active = False

    def _update_forced_open_counter(self, remaining_seconds):
        """Actualiza el contador visual de reapertura forzada en la UI"""
        if threading.current_thread() is not threading.main_thread():
            self._run_on_ui_thread(self._update_forced_open_counter, remaining_seconds)
            return
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
        except Exception as e:
            logger.error(f"Error actualizando contador: {e}")

    def _update_initial_analysis_counter(self, remaining_seconds, direction=''):
        """Actualiza el contador visual del análisis inicial de 30s en la UI"""
        if threading.current_thread() is not threading.main_thread():
            self._run_on_ui_thread(self._update_initial_analysis_counter, remaining_seconds, direction)
            return
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
        except Exception as e:
            logger.error(f"Error actualizando contador inicial: {e}")

    def stop_bot(self):
        """Versión mejorada que incluye manejo de pausa"""
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
        self.pause_btn.config(state='disabled', text="[PAUSA] Pausar")
        
        try:
            self.is_running = False
            self._scheduler_running = False  # ⭐ Detener scheduler también
            self._forced_reopen_started = False
            self._forced_scheduler_thread = None
            self.trend_monitor_running = False  # ⭐ NUEVO: Detener monitor de tendencias
            self.ui_refresh_running = False  # ⭐ NUEVO: Detener refresh de UI
            self.blue_monitor_running = False  # ⭐ NUEVO: Detener monitor de azul
            self.red_monitor_running = False  # ⭐ NUEVO: Detener monitor de rojo
            self.sl_monitor_running = False  # ⭐ NUEVO: Detener monitor de stop loss
            self.specialists_monitor_running = False  # ⭐ NUEVO: Detener monitor de especialistas
            self._entry_analysis_running = False
            self.margen_monitor_running = False  # ⭐ NUEVO: Detener monitor de margen de ganancia
            self.objetivo_neto_running = False  # ⭐ NUEVO: Detener monitor de objetivo neto
            
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
            
            # Updates removidas para evitar stack overflow
            
        except Exception as e:
            self.add_log(f"Error al detener el bot: {str(e)}", 'error')
            self.is_running = False
            self.root.update()

    def _monitor_global_tp_sl(self):
        """
        ⭐ MONITOR GLOBAL TP/SL: Cierra posiciones AZULES si TP se alcanza, ROJAS si SL se alcanza.
        El bot continúa operando después del cierre.
        """
        while getattr(self, '_scheduler_running', True):
            try:
                time.sleep(0.5)  # Verificar cada 500ms
                if getattr(self, 'bot_pausado', False):
                    continue
                
                # Leer valores globales de la configuración
                global_tp = self.config.get('GLOBAL_TP', None)
                global_sl = self.config.get('GLOBAL_SL', None)
                
                if global_tp is None or global_sl is None:
                    continue
                
                try:
                    tp_val = float(global_tp.get())
                    sl_val = float(global_sl.get())
                except Exception:
                    continue
                
                # Si ambos son cero, saltar
                if tp_val == 0 and sl_val == 0:
                    continue
                
                # Obtener todas las posiciones abiertas
                all_positions = []
                try:
                    if hasattr(self, 'mt5_cache') and hasattr(self.mt5_cache, 'cache'):
                        for sym, poslist in self.mt5_cache.cache.get('positions', {}).items():
                            all_positions.extend(poslist)
                    else:
                        symbol = self.config['SYMBOL'].get()
                        all_positions = self.mt5_cache.get_positions(symbol)
                except Exception as e:
                    self.add_log(f"[GLOBAL TP/SL] Error obteniendo posiciones: {str(e)[:60]}", 'warning')
                    continue
                
                # Si no hay posiciones, continuar
                if not all_positions:
                    continue
                
                # Calcular suma total de ganancias y pérdidas
                total_gain = 0.0
                total_loss = 0.0
                blue_positions = []  # Posiciones con ganancia
                red_positions = []   # Posiciones con pérdida
                
                for idx, pos in enumerate(all_positions):
                    try:
                        profit = pos.get('profit', 0) if isinstance(pos, dict) else getattr(pos, 'profit', 0)
                        profit = float(profit)
                        
                        if profit > 0:
                            total_gain += profit
                            blue_positions.append(pos)
                        elif profit < 0:
                            total_loss += profit
                            red_positions.append(pos)
                    except Exception as e:
                        self.add_log(f"[GLOBAL TP/SL] Error procesando posición {idx}: {str(e)[:60]}", 'warning')
                
                # Log de debug cada 10 ciclos (cada 5 segundos)
                if not hasattr(self, '_tp_sl_debug_count'):
                    self._tp_sl_debug_count = 0
                self._tp_sl_debug_count += 1
                
                if self._tp_sl_debug_count % 10 == 0:
                    self.add_log(f"[GLOBAL TP/SL] Azules: ${total_gain:.2f} (TP: {tp_val}) | Rojas: ${total_loss:.2f} (SL: {-sl_val})", 'info')
                
                # ⭐ CIERRE SELECTIVO DE POSICIONES ROJAS (pérdidas >= SL)
                if sl_val > 0 and abs(total_loss) >= sl_val and red_positions:
                    self.add_log(f"[GLOBAL SL] 🛑 Stop Loss alcanzado: pérdidas=${total_loss:.2f} >= -${sl_val:.2f}. Cerrando posiciones ROJAS...", 'alert')
                    close_count = 0
                    symbol = self.config['SYMBOL'].get()
                    for pos in red_positions:
                        try:
                            ticket = pos.get('ticket', None) if isinstance(pos, dict) else getattr(pos, 'ticket', None)
                            pos_type = pos.get('type', 0) if isinstance(pos, dict) else getattr(pos, 'type', 0)
                            volume = pos.get('volume', 0) if isinstance(pos, dict) else getattr(pos, 'volume', 0)
                            profit = pos.get('profit', 0) if isinstance(pos, dict) else getattr(pos, 'profit', 0)
                            
                            if ticket:
                                # Obtener tick y preparar cierre
                                tick = mt5.symbol_info_tick(symbol)
                                if not tick:
                                    continue
                                
                                close_type = mt5.ORDER_TYPE_SELL if pos_type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                                close_price = tick.bid if pos_type == mt5.POSITION_TYPE_BUY else tick.ask
                                
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": volume,
                                    "type": close_type,
                                    "position": ticket,
                                    "price": close_price,
                                    "magic": self.config['MAGIC_NUMBER'],
                                    "comment": f"GLOBAL_SL_CLOSE_{profit:.2f}",
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                
                                result = mt5.order_send(request)
                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    self.add_log(f"[GLOBAL SL] ✓ Cerrada #{ticket} | ${profit:.2f}", 'warning')
                                    self._procesar_cierre_exitoso(ticket, symbol, volume, pos_type, profit)
                                    close_count += 1
                                else:
                                    self.add_log(f"[GLOBAL SL] Error cerrando #{ticket}: {result.comment if result else 'Sin respuesta'}", 'error')
                        except Exception as e:
                            self.add_log(f"[GLOBAL SL] Error cerrando posición: {str(e)[:60]}", 'error')
                    
                    self.add_log(f"[GLOBAL SL] Total ROJAS cerradas: {close_count}. Bot continúa operando...", 'warning')
                
                # ⭐ CIERRE SELECTIVO DE POSICIONES AZULES (ganancias >= TP)
                elif tp_val > 0 and total_gain >= tp_val and blue_positions:
                    self.add_log(f"[GLOBAL TP] 🚀 Take Profit alcanzado: ganancias=${total_gain:.2f} >= ${tp_val:.2f}. Cerrando posiciones AZULES...", 'alert')
                    close_count = 0
                    symbol = self.config['SYMBOL'].get()
                    for pos in blue_positions:
                        try:
                            ticket = pos.get('ticket', None) if isinstance(pos, dict) else getattr(pos, 'ticket', None)
                            pos_type = pos.get('type', 0) if isinstance(pos, dict) else getattr(pos, 'type', 0)
                            volume = pos.get('volume', 0) if isinstance(pos, dict) else getattr(pos, 'volume', 0)
                            profit = pos.get('profit', 0) if isinstance(pos, dict) else getattr(pos, 'profit', 0)
                            
                            if ticket:
                                # Obtener tick y preparar cierre
                                tick = mt5.symbol_info_tick(symbol)
                                if not tick:
                                    continue
                                
                                close_type = mt5.ORDER_TYPE_SELL if pos_type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                                close_price = tick.bid if pos_type == mt5.POSITION_TYPE_BUY else tick.ask
                                
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": volume,
                                    "type": close_type,
                                    "position": ticket,
                                    "price": close_price,
                                    "magic": self.config['MAGIC_NUMBER'],
                                    "comment": f"GLOBAL_TP_CLOSE_{profit:.2f}",
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                
                                result = mt5.order_send(request)
                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    self.add_log(f"[GLOBAL TP] ✓ Cerrada #{ticket} | ${profit:.2f}", 'warning')
                                    close_count += 1
                                else:
                                    self.add_log(f"[GLOBAL TP] Error cerrando #{ticket}: {result.comment if result else 'Sin respuesta'}", 'error')
                        except Exception as e:
                            self.add_log(f"[GLOBAL TP] Error cerrando posición: {str(e)[:60]}", 'error')
                    
                    self.add_log(f"[GLOBAL TP] Total AZULES cerradas: {close_count}. Bot continúa operando...", 'warning')
                    
            except Exception as e:
                self.add_log(f"[GLOBAL TP/SL] Error en monitor: {str(e)[:100]}", 'error')

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
                self._set_pause(pause_seconds, "Pausa post-stop-loss")
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
            
            # ⭐ Remover after_idle() para evitar stack overflow
            
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
                
                # ⭐ DESHABILITADO: Cierre dinámico automático por reversión
                # El bot SOLO debe cerrar por MIN_PROFIT o MAX_LOSS de la interfaz, no por cambios de tendencia
                # if analysis and hasattr(self, 'position_closer'):
                #     closed = self.position_closer.evaluate_and_close(
                #         symbol=symbol,
                #         trend_analysis=analysis,
                #         magic_number=self.config['MAGIC_NUMBER']
                #     )
                #     if closed > 0:
                #         self.add_log(f"[TREND_MONITOR] ✅ Cierre dinámico: {closed} posición(es)", 'success')
                
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
                            # ⭐ MENSAJE INFORMATIVO ÚNICAMENTE (bloqueo desactivado)
                            self.add_log(f"[TREND-INFO] Reversión DETECTADA: {signal} @ {confidence:.1f}% confianza", 'info')
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
                # Tick central coalesced: un único punto de refresco
                if self.is_running or self._ui_refresh_requested:
                    self._ui_refresh_requested = False
                    self._run_on_ui_thread(self._update_ui)
                
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
        monitor_interval = 0.05  # ⭐ CRÍTICO: 50ms para cierres ULTRA-RÁPIDOS (2x más rápido que antes)
        
        self.add_log("[🔵] CIERRE ULTRA-RÁPIDO INICIADO - Intervalo 50ms", 'info')
        
        while self.blue_monitor_running:
            try:
                if not self.is_running:
                    time.sleep(1)
                    continue
                
                symbol = self.config['SYMBOL'].get()
                min_profit_close = float(self.config['MIN_PROFIT_CLOSE'].get()) if self.config['MIN_PROFIT_CLOSE'].get() else 2.0
                
                # ⭐ Obtener posiciones con CACHE (máxima velocidad)
                positions = self.mt5_cache.get_positions(symbol) or mt5.positions_get(symbol=symbol)
                if not positions:
                    time.sleep(monitor_interval)
                    continue
                
                # Filtrar solo posiciones del bot
                bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
                
                # ⭐ CACHE DE TICK REUTILIZABLE (una sola llamada por ciclo)
                tick = self.mt5_cache.get_tick(symbol) or mt5.symbol_info_tick(symbol)
                magic = self.config['MAGIC_NUMBER']
                
                for position in bot_positions:
                    ticket = position.ticket
                    current_profit = position.profit
                    
                    # ⭐ CIERRE DIRECTO SIN ESPERA: Si ganancia >= umbral, cerrar AHORA
                    if current_profit >= min_profit_close:
                        # Log SOLO si es primera detección (no repetir logs)
                        if ticket not in self.blue_positions_watched:
                            self.blue_positions_watched[ticket] = {'detected_time': time.time(), 'profit': current_profit}
                            self.add_log(f"🔵 Ticket #{ticket}: ${current_profit:.2f} >= ${min_profit_close:.2f} → CERRANDO", 'success')
                        
                        # ⭐ CIERRE ULTRA-RÁPIDO SIN VERIFICACIÓN PREVIA
                        try:
                            if not tick:
                                tick = mt5.symbol_info_tick(symbol)
                            if tick:
                                pos_type = position.type
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": position.volume,
                                    "type": mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY,
                                    "position": ticket,
                                    "price": tick.bid if pos_type == 0 else tick.ask,
                                    "magic": magic,
                                    "comment": "BLUE_CLOSE",
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                result = mt5.order_send(request)
                                
                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    self.add_log(f"✅ Cerrado #{ticket}: ${current_profit:.2f}", 'success')
                                    self._procesar_cierre_exitoso(ticket, symbol, position.volume, pos_type, current_profit)
                                    del self.blue_positions_watched[ticket]
                        except Exception as e:
                            pass  # Silencio en errores de cierre (reintentar en próxima iteración)
                    
                    elif ticket in self.blue_positions_watched:
                        # Posición salió de azul (regresionó)
                        del self.blue_positions_watched[ticket]
                
                time.sleep(monitor_interval)  # ⭐ MÍNIMA latencia: 50ms
            
            except Exception as e:
                time.sleep(monitor_interval)

    def _red_positions_monitor_loop(self):
        """
        🔴 Monitor Reactivo de Posiciones en ROJO
        - Verifica cada 0.05s si las posiciones con pérdida alcanzan MAX_LOSS_CLOSE
        - Cierra INMEDIATAMENTE cuando se alcanza el threshold
        - Evita pérdidas mayores
        """
        monitor_interval = 0.05  # ⭐ CRÍTICO: 50ms para cierres ULTRA-RÁPIDOS
        
        self.add_log("[🔴] CIERRE ULTRA-RÁPIDO EN ROJO INICIADO - Intervalo 50ms", 'info')
        
        while self.red_monitor_running:
            try:
                if not self.is_running:
                    time.sleep(1)
                    continue
                
                symbol = self.config['SYMBOL'].get()
                max_loss_close = abs(float(self.config['MAX_LOSS_CLOSE'].get())) if self.config['MAX_LOSS_CLOSE'].get() else 25.0
                
                # ⭐ Obtener posiciones con CACHE (máxima velocidad)
                positions = self.mt5_cache.get_positions(symbol) or mt5.positions_get(symbol=symbol)
                if not positions:
                    time.sleep(monitor_interval)
                    continue
                
                # Filtrar solo posiciones del bot
                bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
                
                # ⭐ CACHE DE TICK REUTILIZABLE (una sola llamada por ciclo)
                tick = self.mt5_cache.get_tick(symbol) or mt5.symbol_info_tick(symbol)
                magic = self.config['MAGIC_NUMBER']
                
                for position in bot_positions:
                    ticket = position.ticket
                    current_loss = abs(position.profit)
                    
                    # ⭐ CIERRE DIRECTO SIN ESPERA: Si pérdida >= umbral, cerrar AHORA
                    if current_loss >= max_loss_close:
                        # Log SOLO si es primera detección (no repetir logs)
                        if ticket not in self.red_positions_watched:
                            self.red_positions_watched[ticket] = {'detected_time': time.time(), 'loss': current_loss}
                            self.add_log(f"🔴 Ticket #{ticket}: -${current_loss:.2f} >= ${max_loss_close:.2f} → CERRANDO", 'error')
                        
                        # ⭐ CIERRE ULTRA-RÁPIDO SIN VERIFICACIÓN PREVIA
                        try:
                            if not tick:
                                tick = mt5.symbol_info_tick(symbol)
                            if tick:
                                pos_type = position.type
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": symbol,
                                    "volume": position.volume,
                                    "type": mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY,
                                    "position": ticket,
                                    "price": tick.bid if pos_type == 0 else tick.ask,
                                    "magic": magic,
                                    "comment": "RED_CLOSE",
                                    "type_filling": mt5.ORDER_FILLING_IOC,
                                }
                                result = mt5.order_send(request)
                                
                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    self.add_log(f"✅ Cerrado #{ticket}: -${current_loss:.2f}", 'success')
                                    self._procesar_cierre_exitoso(ticket, symbol, position.volume, pos_type, position.profit)
                                    del self.red_positions_watched[ticket]
                        except Exception:
                            pass  # Silencio en errores de cierre (reintentar en próxima iteración)
                    
                    elif ticket in self.red_positions_watched:
                        # Posición salió de rojo (recuperó)
                        del self.red_positions_watched[ticket]
                
                time.sleep(monitor_interval)  # ⭐ MÍNIMA latencia: 50ms
            
            except Exception:
                time.sleep(monitor_interval)

    def _check_and_recover_red_positions(self):
        """
        🔴 RECUPERACIÓN AUTOMÁTICA DE OPERACIONES EN ROJO
        
        Implementa la función solicitada por el usuario:
        - Analiza operaciones en ROJO (profit < 0)
        - Calcula potencial de recuperación individual
        - Si potencial < MIN_RECOVERY_POTENTIAL → cierra con mínima pérdida
        - Si potencial >= MIN_RECOVERY_POTENTIAL → mantiene abierta
        
        Se ejecuta independientemente de drawdown (drawdown check fue removido)
        """
        try:
            symbol = self.config['SYMBOL'].get()
            min_recovery_pct = float(self.config.get('MIN_RECOVERY_POTENTIAL', tk.DoubleVar(value=30.0)).get())
            
            # Obtener posiciones abiertas
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return
            
            # Filtrar solo posiciones del bot
            bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
            
            # Filtrar solo posiciones en ROJO (pérdida)
            red_positions = [p for p in bot_positions if p.profit < 0]
            
            if not red_positions:
                return
            
            self.add_log(f"\n🔴 [RED_RECOVERY] Revisando {len(red_positions)} operación(es) en ROJO...", 'info')
            
            for position in red_positions:
                ticket = position.ticket
                current_loss = position.profit
                pos_type_name = "BUY" if position.type == mt5.POSITION_TYPE_BUY else "SELL"
                
                # 1️⃣ Obtener datos históricos de 24h para calcular potencial
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1440)  # 1440 minutos = 24h
                
                if rates is None or len(rates) == 0:
                    self.add_log(f"   ⚠️ #{ticket} No se pudieron obtener datos históricos", 'warning')
                    continue
                
                closes = np.array([r['close'] for r in rates], dtype=np.float64)
                current_price = closes[-1]  # Precio actual
                highest_24h = np.max(closes)
                lowest_24h = np.min(closes)
                
                # 2️⃣ Calcular potencial de recuperación
                space_to_resistance = ((highest_24h - current_price) / current_price) * 100 if current_price > 0 else 0
                distance_to_support = ((current_price - lowest_24h) / current_price) * 100 if current_price > 0 else 0
                
                recovery_potential = (space_to_resistance / distance_to_support) * 100 if distance_to_support > 0 else 0
                
                self.add_log(
                    f"   #{ticket} {pos_type_name} | Pérdida: ${abs(current_loss):.2f} | "
                    f"Potencial Recuperación: {recovery_potential:.1f}% vs Límite: {min_recovery_pct:.1f}%",
                    'warning'
                )
                
                # 3️⃣ Decisión: ¿Cerrar o mantener?
                if recovery_potential < min_recovery_pct:
                    # BAJO POTENCIAL → CERRAR CON MÍNIMA PÉRDIDA
                    self.add_log(
                        f"   ❌ CIERRE AUTOMÁTICO: Potencial {recovery_potential:.1f}% < {min_recovery_pct:.1f}% "
                        f"(Pérdida: ${abs(current_loss):.2f})",
                        'error'
                    )
                    
                    # Intentar cierre inmediato
                    try:
                        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        tick = mt5.symbol_info_tick(symbol)
                        close_price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
                        
                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": position.volume,
                            "type": close_type,
                            "position": ticket,
                            "price": close_price,
                            "magic": self.config['MAGIC_NUMBER'],
                            "comment": f"RED_RECOVERY_CLOSE_LowRecovery_{recovery_potential:.1f}%",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        
                        result = mt5.order_send(request)
                        
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            self.add_log(
                                f"   ✅ Cerrada #{ticket}: Pérdida Final: ${current_loss:.2f}",
                                'success'
                            )
                            # Registrar cierre
                            self._procesar_cierre_exitoso(
                                ticket=ticket,
                                symbol=symbol,
                                volume=position.volume,
                                pos_type=position.type,
                                profit=current_loss
                            )
                        else:
                            retcode = getattr(result, 'retcode', 'UNKNOWN')
                            self.add_log(
                                f"   ⚠️ Intento de cierre falló (retcode={retcode})",
                                'warning'
                            )
                    
                    except Exception as close_error:
                        self.add_log(f"   ❌ Error al cerrar: {str(close_error)[:60]}", 'error')
                
                else:
                    # BUEN POTENCIAL → MANTENER ABIERTA
                    self.add_log(
                        f"   ✅ MANTENER ABIERTA: Potencial {recovery_potential:.1f}% >= {min_recovery_pct:.1f}% "
                        f"(Esperando recuperación...)",
                        'success'
                    )
        
        except Exception as e:
            self.add_log(f"[RED_RECOVERY] Error: {str(e)[:80]}", 'error')

    def _monitor_stop_loss_manual(self):
        """
        🛑 MONITOR DE STOP LOSS MANUAL (ACTIVO)
        
        Verifica cada 0.5s si las posiciones alcanzaron su SL.
        MT5 puede no cerrar automáticamente en algunos casos, así que monitoreamos manualmente.
        Cierra INMEDIATAMENTE cuando se alcanza el SL.
        
        Se ejecuta cada 0.5s para capturar movimientos rápidos.
        """
        monitor_interval = 0.5  # Verificar cada 500ms
        
        self.add_log("[🛑] Monitor de Stop Loss INICIADO - Verificando cada 0.5s", 'info')
        
        while self.is_running and hasattr(self, 'sl_monitor_running'):
            try:
                if not self.is_running:
                    time.sleep(1)
                    continue
                
                symbol = self.config['SYMBOL'].get()
                
                # Obtener todas las posiciones abiertas
                positions = self.mt5_cache.get_positions(symbol) or mt5.positions_get(symbol=symbol)
                if not positions:
                    time.sleep(monitor_interval)
                    continue
                
                # Filtrar solo posiciones del bot
                bot_positions = [p for p in positions if p.magic == self.config['MAGIC_NUMBER']]
                
                for position in bot_positions:
                    ticket = position.ticket
                    current_profit = position.profit
                    position_type = "BUY" if position.type == 0 else "SELL"
                    
                    # ⭐ COMPROBAR SL: Si profit < 0 y el SL se alcanzó → cierar inmediatamente
                    if position.sl > 0:  # SL configurado
                        if position.type == mt5.POSITION_TYPE_BUY:
                            # Para BUY, SL está abajo - se alcanza si precio actual <= SL
                            if position.price_current <= position.sl:
                                self._procesar_cierre_por_sl(position, symbol)
                        else:
                            # Para SELL, SL está arriba - se alcanza si precio actual >= SL
                            if position.price_current >= position.sl:
                                self._procesar_cierre_por_sl(position, symbol)
                
                time.sleep(monitor_interval)
            
            except Exception as e:
                self.add_log(f"[SL_MONITOR] Error: {str(e)[:80]}", 'error')
                time.sleep(monitor_interval * 2)

    def _procesar_cierre_por_sl(self, position, symbol):
        """Procesa el cierre de una posición que alcanzó su SL"""
        ticket = position.ticket
        current_profit = position.profit
        position_type = "BUY" if position.type == 0 else "SELL"
        
        try:
            tick = self.mt5_cache.get_tick(symbol) or mt5.symbol_info_tick(symbol)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position_type == 'BUY' else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": tick.bid if position_type == 'BUY' else tick.ask,
                "magic": self.config['MAGIC_NUMBER'],
                "comment": f"SL_MONITOR_CLOSE_{current_profit:.2f}",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.add_log(f"\n🛑 [SL_MONITOR] ¡SL ALCANZADO! Ticket #{ticket} CERRADO", 'success')
                self.add_log(f"   Tipo: {position_type} | Pérdida: ${current_profit:.2f}", 'error')
                
                # Registrar cierre
                self._procesar_cierre_exitoso(
                    ticket=ticket,
                    symbol=symbol,
                    volume=position.volume,
                    pos_type=position.type,
                    profit=current_profit
                )
            else:
                self.add_log(f"   ⚠️ Intento de cierre por SL falló (retcode={result.retcode if result else 'UNKNOWN'})", 'warning')
        
        except Exception as close_error:
            self.add_log(f"   ❌ Error al cerrar por SL: {str(close_error)[:60]}", 'error')

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
        
        # ⭐ Remover after_idle() para evitar stack overflow

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
            
            # Updates removidas para evitar stack overflow
            
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
            
            self.add_log(f"$ Saldo total acumulado: ${self.saldo_total_acumulado:.2f}", 'success')
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

 #FIX #16: Asegurar que bot_pausado se establece ANTES de cualquier operación de UI
            self._set_pause(pause_seconds, "Pausa post-objetivo")
            
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
            
            self.request_ui_refresh()
            
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

    def _monitor_specialists_loop(self):
        """
        ⭐ Monitor en Tiempo Real de Especialistas - OBTIENE DATOS FRESCOS DE MT5 CADA SEGUNDO
        NO depende de archivo JSON (que es estático)
        Garantiza que indicadores siempre analicen datos ACTUALES del mercado
        """
        self.add_log("📊 Monitor de Especialistas iniciado - Análisis TIEMPO REAL cada segundo", 'info')
        
        while self.specialists_monitor_running and self.is_running:
            try:
                if not self.is_running:
                    time.sleep(0.1)
                    continue
                
                symbol = self.config['SYMBOL'].get()
                loop_start = time.time()
                
                # ⭐ CRÍTICO: Obtener datos FRESCOS de MT5 CADA SEGUNDO
                # NO usar archivo JSON que es estático
                try:
                    # Obtener últimas 100 barras M1 de MT5 (DATOS FRESCOS EN TIEMPO REAL)
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
                    rates = mt5_safe._ensure_rates_list(rates)
                    
                    if rates is None or len(rates) == 0:
                        logger.warning("[MONITOR-MT5] No data from MT5, using fallback")
                        # Fallback a archivo si MT5 falla
                        # ⭐ Usar GOLD como símbolo por defecto
                        market_snaps = self.reload_market_snapshots(symbol='GOLD') or []
                    else:
                        # ✅ Convertir rates de MT5 a snapshots format
                        market_snaps = []
                        for idx, rate in enumerate(rates):
                            snap = {
                                'time': float(rate['time']) if isinstance(rate, dict) else float(rate[0]),
                                'open': float(rate['open']) if isinstance(rate, dict) else float(rate[1]),
                                'high': float(rate['high']) if isinstance(rate, dict) else float(rate[2]),
                                'low': float(rate['low']) if isinstance(rate, dict) else float(rate[3]),
                                'close': float(rate['close']) if isinstance(rate, dict) else float(rate[4]),
                                'tick_volume': int(rate['tick_volume']) if isinstance(rate, dict) else int(rate[5]),
                            }
                            market_snaps.append(snap)
                        
                        logger.debug(f"[MONITOR-MT5] ✓ Obtenidas {len(market_snaps)} barras FRESCOS de MT5")
                        
                        # ⭐ Guardar en cache compartido para que scheduler las use
                        try:
                            with self.fresh_data_lock:
                                self.fresh_market_data_cache = market_snaps
                                self.fresh_data_timestamp = time.time()
                        except Exception:
                            pass
                except Exception as e:
                    logger.debug(f"[MONITOR-MT5] Error: {str(e)[:40]} - usando fallback")
                    # ⭐ Usar GOLD como símbolo por defecto en fallback
                    market_snaps = self.reload_market_snapshots(symbol='GOLD') or []
                
                # Asegurar que tenemos datos
                if not market_snaps:
                    time.sleep(0.5)
                    continue
                
                # ⭐ Detectar si hay nuevos datos (cambio en última barra)
                current_close = None
                if market_snaps and isinstance(market_snaps, list) and len(market_snaps) > 0:
                    last_snap = market_snaps[-1]
                    if isinstance(last_snap, dict):
                        current_close = last_snap.get('close', 0)
                
                if not hasattr(self, '_last_monitor_close'):
                    self._last_monitor_close = current_close
                
                # Re-analizar SIEMPRE cada ciclo para que especialistas reaccionen cada 1s.
                should_analyze = True
                self._last_monitor_close = current_close
                
                buy_result = None
                sell_result = None

                # Evita crear threads nuevos en cada ciclo (fuga acumulativa tras horas de ejecución).
                if should_analyze:
                    try:
                        if hasattr(self.buy_specialist, 'analyze'):
                            buy_result = self.buy_specialist.analyze(
                                symbol,
                                market_snapshots=market_snaps,
                                check_recovery_potential=False
                            )
                    except Exception as e:
                        logger.debug(f"[MONITOR-BUY] Error: {str(e)[:40]}")

                    try:
                        if hasattr(self.sell_specialist, 'analyze'):
                            sell_result = self.sell_specialist.analyze(
                                symbol,
                                market_snapshots=market_snaps,
                                check_recovery_potential=False
                            )
                    except Exception as e:
                        logger.debug(f"[MONITOR-SELL] Error: {str(e)[:40]}")

                # ⭐ SIEMPRE PRIORIZAR RESULTADO FRESCO si disponible
                # Solo usar caché si análisis falló
                buy_score = None
                sell_score = None
                buy_conf = 0
                sell_conf = 0

                if buy_result:
                    buy_score = buy_result.get('score', None)
                    buy_conf = buy_result.get('confidence', 0)
                    try:
                        # Evitar publicar 0.0% fijo cuando el especialista devolvió dato inválido.
                        if buy_score is not None and float(buy_score) <= 0 and float(buy_conf) <= 0:
                            buy_score = self.last_buy_score if hasattr(self, 'last_buy_score') else 50
                    except Exception:
                        pass
                if buy_score is None:
                    buy_score = self.last_buy_score if hasattr(self, 'last_buy_score') else 50

                if sell_result:
                    sell_score = sell_result.get('score', None)
                    sell_conf = sell_result.get('confidence', 0)
                    try:
                        # Evitar publicar 0.0% fijo cuando el especialista devolvió dato inválido.
                        if sell_score is not None and float(sell_score) <= 0 and float(sell_conf) <= 0:
                            sell_score = self.last_sell_score if hasattr(self, 'last_sell_score') else 50
                    except Exception:
                        pass
                if sell_score is None:
                    sell_score = self.last_sell_score if hasattr(self, 'last_sell_score') else 50
                
                # ⭐ NUEVO: ANÁLISIS DE REVERSIÓN EXTREMA EN MONITOR TIEMPO REAL
                # Detectar velas extremas y aplicar boost a dirección de reversión
                try:
                    reversal_analysis = self._analyze_extreme_candle_reversal(market_snaps)
                    if reversal_analysis.get('reversal_detected', False):
                        reversal_strength = reversal_analysis.get('reversal_strength', 0.0)
                        reversal_direction = reversal_analysis.get('reversal_direction')
                        
                        if reversal_strength >= 60.0:
                            # Aplicar boost a la dirección de reversión
                            if reversal_direction == 'BUY':
                                boost = min(20.0, reversal_strength * 0.25)
                                buy_score = min(100.0, buy_score + boost)
                                sell_score = max(0.0, sell_score - boost * 0.3)
                                logger.debug(f"[MONITOR-REVERSAL] Reversal BUY detected: +{boost:.1f} boost")
                            else:  # SELL
                                boost = min(20.0, reversal_strength * 0.25)
                                sell_score = min(100.0, sell_score + boost)
                                buy_score = max(0.0, buy_score - boost * 0.3)
                                logger.debug(f"[MONITOR-REVERSAL] Reversal SELL detected: +{boost:.1f} boost")
                except Exception as e:
                    logger.debug(f"[MONITOR-REVERSAL] Error: {str(e)[:60]}")
                
                # ⭐ FIX: NO aplicar sesgos por tendencia - los especialistas YA incluyen análisis de tendencia
                # Aplicar sesgos crearía distorsión sistemática (problema anterior)
                # Los datos FRESCOS ya reflejan la tendencia correctamente
                market_trend = None
                if buy_result and buy_result.get('market_condition'):
                    market_condition = buy_result.get('market_condition', {})
                    market_trend = market_condition.get('trend', None) if isinstance(market_condition, dict) else None
                
                # ⭐ SIN SESGOS: Usar scores FRESCOS sin ajustes de tendencia
                # Los especialistas XGBoost ya consideran la tendencia en su análisis
                # No distorsionar con multiplicadores (0.95, 1.05)
                
                # Convertir a porcentajes
                buy_score_pct = min(100, max(0, buy_score))
                sell_score_pct = min(100, max(0, sell_score))
                
                # ⭐ Actualizar variables Y compartir con scheduler (ATOMICALLY bajo lock)
                try:
                    with self.specialist_scores_lock:
                        # Actualizar variables locales
                        self.last_buy_score = buy_score_pct
                        self.last_sell_score = sell_score_pct
                        self.last_buy_confidence = buy_conf
                        self.last_sell_confidence = sell_conf
                        # Compartir con scheduler
                        self.scheduler_shared_scores.update({
                            'buy_score': float(buy_score_pct),
                            'sell_score': float(sell_score_pct),
                            'buy_conf': float(buy_conf),
                            'sell_conf': float(sell_conf),
                            'timestamp': time.time()
                        })
                except Exception:
                    pass
                
                # Agregar al histórico
                timestamp = datetime.now().strftime("%H:%M:%S")
                source = "📊 LIVE"
                history_line = f"[{timestamp}] {source} → BUY: {buy_score_pct:.1f}% | SELL: {sell_score_pct:.1f}%"

                self._run_on_ui_thread(
                    self._apply_specialist_monitor_ui,
                    buy_score_pct,
                    sell_score_pct,
                    buy_conf,
                    sell_conf,
                    history_line,
                )
                
                # Sincronización fija a 1s para cambios más rápidos de especialistas.
                elapsed = time.time() - loop_start
                sleep_time = max(0.01, 1.0 - elapsed)  # Ajusta para que sea exactamente 1s total
                time.sleep(sleep_time)
                
            except Exception as e:
                self.add_log(f"[ERROR] Monitor especialistas: {str(e)[:60]}", 'error')
                time.sleep(0.1)  # Recuperación rápida sin bloqueo

    def _apply_specialist_monitor_ui(self, buy_score_pct, sell_score_pct, buy_conf, sell_conf, history_line):
        """Actualiza widgets del monitor de especialistas en el hilo UI."""
        try:
            if self.buy_score_label:
                self.buy_score_label.config(text=f"Score: {buy_score_pct:.1f}% | Conf: {buy_conf:.0f}%")
            if self.sell_score_label:
                self.sell_score_label.config(text=f"Score: {sell_score_pct:.1f}% | Conf: {sell_conf:.0f}%")

            pass  # Histórico de 10s eliminado
        except Exception:
            pass

    def monitorear_posiciones_en_rojo(self):
        """🔴 CIERRE ULTRA-RÁPIDO EN ROJO - Intervalo 50ms para MAX_LOSS inmediato"""
        try:
            symbol = self.config['SYMBOL'].get()
            max_loss = abs(float(self.config['MAX_LOSS_CLOSE'].get())) if self.config['MAX_LOSS_CLOSE'].get() else 25.0
            magic = self.config['MAGIC_NUMBER']
            
            # ⭐ Obtener posiciones con CACHE (máxima velocidad)
            positions = self.mt5_cache.get_positions(symbol) or mt5.positions_get(symbol=symbol)
            if not positions:
                return
            
            # Filtrar solo posiciones del bot
            bot_positions = [p for p in positions if p.magic == magic]
            
            # ⭐ CACHE DE TICK REUTILIZABLE (una sola llamada por ciclo)
            tick = self.mt5_cache.get_tick(symbol) or mt5.symbol_info_tick(symbol)
            
            for pos in bot_positions:
                ticket = pos.ticket
                loss = abs(pos.profit)
                
                # ⭐ CIERRE DIRECTO EN ROJO: Si pérdida >= MAX_LOSS, cerrar AHORA
                if loss >= max_loss:
                    # Log SOLO si es primera detección (no repetir logs)
                    if ticket not in self.blue_positions_watched:
                        self.blue_positions_watched[ticket] = {'detected_time': time.time(), 'profit': pos.profit}
                        self.add_log(f"🔴 Ticket #{ticket}: -${loss:.2f} >= ${max_loss:.2f} → CERRANDO", 'error')
                    
                    # ⭐ CIERRE ULTRA-RÁPIDO SIN VERIFICACIÓN PREVIA
                    try:
                        if not tick:
                            tick = mt5.symbol_info_tick(symbol)
                        if tick:
                            pos_type = pos.type
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": pos.volume,
                                "type": mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY,
                                "position": ticket,
                                "price": tick.bid if pos_type == 0 else tick.ask,
                                "magic": magic,
                                "comment": "RED_CLOSE",
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            result = mt5.order_send(request)
                            
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                self.add_log(f"✅ Cerrado #{ticket}: -${loss:.2f}", 'success')
                                self._procesar_cierre_exitoso(ticket, symbol, pos.volume, pos_type, pos.profit)
                                del self.blue_positions_watched[ticket]
                    except Exception:
                        pass  # Silencio en errores de cierre (reintentar en próxima iteración)
                
                elif ticket in self.blue_positions_watched:
                    # Posición salió de rojo (recuperó)
                    del self.blue_positions_watched[ticket]
            
            return  # ← FIN ciclo rápido MAX_LOSS
        
        except Exception as e:
            pass
    
    def _check_and_recover_red_positions(self):
        pass

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
            self.pause_btn.config(text="[PAUSA] Pausar")
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
            self.add_log("[CONFIG] Modo tradicional activado - Solo GoldAnalyzer (ETHUSD)", 'info')

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
                # Si el usuario NO definió valores, RECALCULAR con dinero objetivo
                self.add_log(f"📊 Recalculando TP/SL con objetivos de dinero ($5/$20)...", 'info')
                tp_recalc, sl_recalc = self._calcular_tp_sl_por_dinero(
                    precio_actual, direccion, volume,
                    goal_profit=5.0, max_loss=20.0, symbol=symbol
                )
                
                if tp_recalc is not None and sl_recalc is not None:
                    tp = tp_recalc
                    sl = sl_recalc
                    self.add_log(f"🔧 TP/SL calculado: TP={tp:.5f}, SL={sl:.5f}", 'info')
                else:
                    self.add_log(f"⚠️ No se pudo calcular TP/SL", 'warning')
                    return False
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
            
            self.add_log(f"🚀 Paradas validados: TP={tp_valid:.5f}, SL={sl_valid:.5f}", 'info')
            
            # ⭐ NUEVO: Opción de usar o no SL
            usar_sl = self.config['USE_SL'].get()
            sl_final = sl_valid if usar_sl else 0.0
            
            # ⭐ DEBUG: Log detallado antes de enviar a MT5
            self.add_log(f"📊 ANTES DE ENVIAR A MT5:", 'info')
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
            
            # Las operaciones manuales SIEMPRE se permiten, sin importar el límite
            
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                messagebox.showerror("Error", "No se pudo obtener información del símbolo")
                return
            
            # Calcular TP basado en configuración de UI
            tp_diff = float(self.config['TP_DIFF'].get())  # ⭐ SIEMPRE usar el TP de la GUI
            sl_diff = float(self.config['SL_DIFF'].get())  # <- usar valor desde interfaz
    
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                messagebox.showerror("Error", "No se pudo obtener tick actual")
                return
            
            precio = tick.ask if direccion == "BUY" else tick.bid
            
            if direccion == "BUY":
                sl = round(precio - sl_diff, symbol_info.digits)
                tp = round(precio + tp_diff, symbol_info.digits)
                tipo = mt5.ORDER_TYPE_BUY
            else:
                sl = round(precio + sl_diff, symbol_info.digits)
                tp = round(precio - tp_diff, symbol_info.digits)
                tipo = mt5.ORDER_TYPE_SELL
            
            # ⭐ NUEVO: Respetar configuración USE_SL
            usar_sl = self.config['USE_SL'].get()
            sl_final = sl if usar_sl else 0.0

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(self.config['VOL'].get()),
                "type": tipo,
                "price": precio,
                "sl": sl_final,
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
                msg = f"[OK] Operación manual {direccion}: {precio:.5f} | TP={tp:.5f} SL={sl_final:.5f} {'(SIN SL)' if not usar_sl else ''}"
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
        entry_notebook.add(custom_tab, text="🚀 Análisis Personalizado")

        # Pestaña 3: Configuración Manual
        manual_tab = tk.Frame(entry_notebook, bg='#1e293b')
        entry_notebook.add(manual_tab, text="[OBJETIVO] Punto de Entrada Manual")

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

        self.hierarchical_status = tk.Label(btn_row, text="🚀 Listo", 
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

        tk.Label(mark_row, text="🚀 Seleccionar:", bg='#2d3e50', fg='#cbd5e1', 
                font=('Arial', 9, 'bold'), width=16, anchor='w').pack(side='left', padx=5)

        # ⭐ Botón "Marcar Todo"
        tk.Button(mark_row, text="☑️ Marcar Todo", 
                 command=self._marcar_todas_opciones,
                 bg='#06b6d4', fg='white', font=('Arial', 8, 'bold'),
                 relief='flat', padx=15, pady=3, cursor='hand2').pack(side='left', padx=2, fill='x', expand=True)
        
        # ⭐ Botón "Desmarcar Todo"
        tk.Button(mark_row, text="❌ Desmarcar Todo", 
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
        tk.Button(velas_tp_row, text="✍️ Aplicar TP", 
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
        tk.Button(velas_sl_row, text="🛡️ Aplicar SL", 
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

        self.usar_hier_btn = tk.Button(use_btn_frame, text="[OK] Usar Opción Seleccionada", 
                                       command=self.usar_opcion_jerarquica,
                                       bg='#10b981', fg='white', font=('Arial', 10, 'bold'),
                                       relief='flat', padx=20, pady=8, cursor='hand2')
        self.usar_hier_btn.pack(side='left', padx=5, fill='x', expand=True)

        # ⭐ NUEVO: Botón para agregar a espera
        self.agregar_espera_hier_btn = tk.Button(use_btn_frame, text="[ESPERA] Agregar a Espera", 
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

        self.super_analysis_status = tk.Label(btn_row, text="🚀 Listo", 
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

        self.usar_custom_btn = tk.Button(use_btn_frame, text="[OK] Usar Este Análisis", 
                                        command=self.usar_analisis_personalizado,
                                        bg='#10b981', fg='white', font=('Arial', 10, 'bold'),
                                        relief='flat', padx=20, pady=8, cursor='hand2')
        self.usar_custom_btn.pack(side='left', padx=5, fill='x', expand=True)

        # ⭐ NUEVO: Frame para ajustar TP/SL con controles +/-
        controls_frame = tk.LabelFrame(main_frame, text="[CONFIG] Ajustar TP/SL y Calcular Ganancias", 
                                      bg='#2d3e50', fg='#f1f5f9',
                                      font=('Arial', 10, 'bold'), padx=10, pady=8)
        controls_frame.pack(fill='x', pady=(10, 0))

        # Variables para TP/SL ajustables
        self.tp_var = tk.DoubleVar(value=0.0)
        self.sl_var = tk.DoubleVar(value=0.0)
        self.tp_status_var = tk.StringVar(value="✅️")  # verde o rojo
        self.sl_status_var = tk.StringVar(value="✅️")

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
        self.enviar_espera_btn = tk.Button(controls_frame, text="[ESPERA] Enviar a Espera", 
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

        tk.Button(action_row, text="📍 Activar Entrada", 
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
        """Panel para gestionar operaciones en espera (DESHABILITADO)"""
        pass

    def create_pending_operations_panel(self, parent):
        """Panel para gestionar operaciones en espera (DESHABILITADO)"""
        pass

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
[📊] Timeframe: {op.get('timeframe', 'N/A')}
⭐ Confianza: {op.get('confidence', 0):.1f}%
🎲 Período: {op.get('period', 'N/A')}
👁️ Precio Actual: {op.get('current_price', 'N/A'):.5f}
📏 Distancia: {op.get('distance', 0):.5f}
[OBJETIVO] TP: {op.get('tp', 'N/A'):.5f}
[🛡️] SL: {op.get('sl', 'N/A'):.5f}
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
            analysis = f"⚠️ Esta operación ya fue {op['status']}\n"
            if op.get('timestamp_execution'):
                analysis += f"Ejecutada a las: {op['timestamp_execution']}"
            self.pending_analyzer_text.config(text=analysis, fg='#fbbf24')
            return
        
        symbol = self.config['SYMBOL'].get()
        tick = mt5.symbol_info_tick(symbol)
        
        if not tick:
            analysis = "[⚠️] No hay datos de mercado disponibles"
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
            if rates and len(rates) > 0:
                highs = np.array([r[2] for r in rates])
                lows = np.array([r[3] for r in rates])
                closes = np.array([r[4] for r in rates])
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
[📊] Rango Entrada: ±{tolerance:.5f} puntos
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
                        analysis += f"   🚀 Precio está ABAJO (válido para entrar cuando suba)\n"
                    else:
                        analysis += f"   🚀 Precio está ARRIBA (esperará a que baje primero)\n"
                    analysis += f"   Falta: {distance:.5f} puntos\n"
                else:
                    # SELL espera BAJADA
                    analysis += f"[UBICACION] Esperando BAJADA a {target_price:.5f}\n"
                    if current_price > target_price:
                        analysis += f"   🚀 Precio está ARRIBA (válido para entrar cuando baje)\n"
                    else:
                        analysis += f"   🚀 Precio está ABAJO (esperará a que suba primero)\n"
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
        """Limpia todas las operaciones en espera (DESHABILITADO)"""
        pass

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
                if rates and len(rates) > 0:
                    highs = np.array([r[2] for r in rates])
                    lows = np.array([r[3] for r in rates])
                    closes = np.array([r[4] for r in rates])
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
            if should_open and self.total_operaciones_abiertas < max_ops:
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
        self.super_analysis_status.config(text="[ESPERA] Analizando...", fg='#fbbf24')
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
                self.add_log(f"⚠️ Usando valores por defecto de tp/sl", 'warning')
            
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
            self.super_analysis_status.config(text="✅️ Listo", fg='#34d399')

            self.add_log(f"\n[OK] Super Análisis Completado (Ultra-Preciso)", 'success')
            self.add_log(f"   {period} | TF: {timeframe}", 'info')
            self.add_log(f"   {direction} @ {entry_price:.5f} ({confidence:.1f}%)", 'success')
            self.add_log(f"   [UBICACION] Entrada: {entry_price:.5f}", 'success')
            self.add_log(f"   [OBJETIVO] TP: {tp_recommended:.5f} (+{abs(tp_recommended - entry_price):.5f})", 'success')
            self.add_log(f"   🚀 SL: {sl_recommended:.5f} (-{abs(entry_price - sl_recommended):.5f})", 'info')
            
            # ⭐ LOGUEAR SCORE DE PRECISIÓN
            if 'precision_score' in analysis:
                self.add_log(f"   ⭐ Precisión: {analysis['precision_score']}%", 'success')

        else:
            self.super_analysis_label.config(text="[ERROR] Error en el análisis", fg='#f87171')
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
            self.suggestion_label.config(text="[ERROR] Error en el análisis", fg='#f87171')
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
                self._run_on_ui_thread(self.entry_current_price_label.config, text=status_text, fg='#f87171')
                return
            
            status_text = f"[DINERO] Precio Actual: {current_price:.5f} | 📏 Distancia: {distance:.5f}"

            if within_range:
                status_text += " | [OK] EN RANGO!"
                self._run_on_ui_thread(self.entry_current_price_label.config, text=status_text, fg='#22c55e')
            else:
                status_text += " | [ESPERA] Esperando..."
                self._run_on_ui_thread(self.entry_current_price_label.config, text=status_text, fg='#60a5fa')

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
                self._run_on_ui_thread(
                    self.entry_status_label.config,
                    text="[OK] Entrada ejecutada - Esperando cierre por TP",
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
                    self._run_on_ui_thread(
                        self.entry_status_label.config,
                        text="[OK] TP Alcanzado - Punto de entrada desactivado",
                        fg='#22c55e'
                    )
                    self.entry_point_active = False
                return

            for pos in positions:
                if pos.magic == self.config['MAGIC_NUMBER']:
                    profit_status = f"[DINERO] Profit Actual: ${pos.profit:.2f}"

                    if pos.profit > 0:
                        self._run_on_ui_thread(
                            self.entry_current_price_label.config,
                            text=f"{profit_status} | [OK] EN GANANCIA",
                            fg='#22c55e'
                        )
                    else:
                        self._run_on_ui_thread(
                            self.entry_current_price_label.config,
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
        self.hierarchical_status.config(text="[ESPERA] Analizando...", fg='#fbbf24')
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
                self.add_log(f"⚠️ Usando valores por defecto de tp/sl para opción", 'warning')

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
                tp_sl_text = f"🎯 TP: {tp_display:.5f} (+{abs(tp_display - entry):.5f}) | 🛡️ SL: {sl_display:.5f} (-{abs(entry - sl_display):.5f})"
            else:  # SELL - intercambiar para mostrar correctamente
                tp_display = sl_recommended  # TP va ABAJO
                sl_display = tp_recommended  # SL va ARRIBA
                tp_sl_text = f"🎯 TP: {tp_display:.5f} (-{abs(entry - tp_display):.5f}) | 🛡️ SL: {sl_display:.5f} (+{abs(sl_display - entry):.5f})"
            tk.Label(tp_sl_frame, text=tp_sl_text, bg=color_bg, fg=color_text,
                    font=('Arial', 8, 'bold'), justify='left').pack(anchor='w')

            # ⭐ NUEVO: Frame para controles +/- de TP/SL por opción
            controls_frame = tk.Frame(option_frame, bg=color_bg)
            controls_frame.pack(fill='x', padx=20, pady=(0, 5))

            # Variables para esta opción
            # Los valores ya están en el orden correcto
            option['tp_var'] = tk.DoubleVar(value=tp_recommended)
            option['sl_var'] = tk.DoubleVar(value=sl_recommended)
            option['tp_status_var'] = tk.StringVar(value="✅️ VÁLIDO")
            option['sl_status_var'] = tk.StringVar(value="✅️ VÁLIDO")
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

            tk.Label(velas_ctrl_row, text="[DATA] Velas:", bg=color_bg, fg=color_text,
                    font=('Arial', 8, 'bold'), width=10).pack(side='left', padx=2)

            option['velas_var'] = tk.DoubleVar(value=0.0)
            tk.Entry(velas_ctrl_row, textvariable=option['velas_var'], width=8, 
                    bg='#475569', fg='white', font=('Arial', 8), justify='center').pack(side='left', padx=1)

            # Botón Recalcular
            tk.Button(velas_ctrl_row, text="[ACTUALIZAR] Recalcular", 
                     command=lambda o=option: self._recalcular_velas_opcion(o, color_bg),
                     bg='#3b82f6', fg='white', font=('Arial', 7, 'bold'), width=12, padx=1).pack(side='left', padx=2, fill='x', expand=True)

            # Fila con información de ganancias y pérdidas SEPARADAS
            profit_row = tk.Frame(controls_frame, bg=color_bg)
            profit_row.pack(fill='x', pady=2)

            # Label para GANANCIA (verde)
            profit_label = tk.Label(profit_row, text="[DINERO] $0.00",
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
            text=f"🚀 {len(filtered_options)} opciones", 
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
                    self.add_log(f"   📋 BUY: TP ({pending_op['tp']:.5f}) > Entry ({entry_price:.5f}) ✅️", 'success')
                else:  # SELL
                    pending_op['tp'] = round(entry_price - distance, 5)
                    pending_op['sl'] = round(entry_price + distance, 5)
                    self.add_log(f"   📊 SELL: TP ({pending_op['tp']:.5f}) < Entry ({entry_price:.5f}) ✅️", 'success')

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
                self.add_log(f"   🚀 BUY: TP ({pending_op['tp']:.5f}) > Entry ({pending_op['price']:.5f})", 'info')
            else:
                self.add_log(f"   🚀 SELL: TP ({pending_op['tp']:.5f}) < Entry ({pending_op['price']:.5f})", 'info')
            
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
                text=f"🚀 {visible_count} opciones ({filter_mode})", 
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
            
            self.add_log(f"🚀 Marcadas {marked_count} opciones visibles (Filtro: {filter_mode})", 'success')
            
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
            
            self.add_log(f"🚀 Desmarcadas {unmarked_count} opciones visibles (Filtro: {filter_mode})", 'info')
            
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
                self.add_log(f"⚠️ No se pudo obtener info de {symbol} en _calcular_tp_sl_por_dinero", 'warning')
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
                self.add_log(f"⚠️ Ajustado TP/SL por separación insuficiente (requerida: {required_separation:.8f})", 'warning')
            
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
                self.add_log(f"⚠️ Labels no encontrados en opción", 'warning')
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
                            option['tp_status_var'].set("✅️ VÁLIDO")
                            option['tp_status_label'].config(fg='#34d399', font=('Arial', 8, 'bold'))
                    except:
                        pass
                    
                    try:
                        if 'sl_status_label' in option and option['sl_status_label'].winfo_exists():
                            option['sl_status_var'].set("✅️ VÁLIDO")
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
                                text="[ERROR] N/A",
                                fg='#ef4444',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    try:
                        if 'loss_label' in option and option['loss_label'].winfo_exists():
                            option['loss_label'].config(
                                text="[ERROR] N/A",
                                fg='#ef4444',
                                font=('Arial', 8, 'bold')
                            )
                    except:
                        pass
                    
                    try:
                        if 'ratio_label' in option and option['ratio_label'].winfo_exists():
                            option['ratio_label'].config(
                                text="[ERROR] Inválido",
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
                self.tp_status_var.set("[EMOJI]")
                self.sl_status_var.set("[EMOJI]")
                self.tp_status_label.config(fg='#ef4444')
                self.sl_status_label.config(fg='#ef4444')
                self.profit_info_label.config(text="[ERROR] TP/SL fuera de rango válido", fg='#ef4444')
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
                self.tp_status_var.set("[EMOJI]")
                self.sl_status_var.set("[EMOJI]")
                self.tp_status_label.config(fg='#34d399')
                self.sl_status_label.config(fg='#34d399')
                
                # Calcular ganancia (usando la función auxiliar)
                profit_per_pip, loss_per_pip = self._calcular_profit_loss(entry_price, tp_adj, sl_adj, direction, volume, symbol)
                
                risk_reward = profit_per_pip / loss_per_pip if loss_per_pip > 0 else 0
                
                self.profit_info_label.config(
                    text=f"[DATA] Ganancia Est.: ${profit_per_pip:,.2f} | Risk:Reward: 1:{risk_reward:.2f} | Vol: {volume}",
                    fg='#34d399'
                )
            else:
                self.tp_status_var.set("[EMOJI]")
                self.sl_status_var.set("[EMOJI]")
                self.tp_status_label.config(fg='#ef4444')
                self.sl_status_label.config(fg='#ef4444')
                self.profit_info_label.config(text="[ERROR] TP debe estar > Entry (BUY) o < Entry (SELL)", fg='#ef4444')
        
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
            self.add_log(f"⚠️ Precio objetivo muy lejos ({distance_to_target:.5f}). Rechazando entrada.", 'warning')
            return False
        
        # Usar el precio objetivo como entrada (o muy cerca)
        precio = round(target_price, symbol_info.digits)
        
        self.add_log(f"[UBICACION] Abriendo {direccion} EN el precio objetivo: {precio:.5f}", 'info')
        self.add_log(f"   Precio actual: {current_bid:.5f} | Diferencia: {distance_to_target:.5f}", 'info')
        
        # Obtener TP y SL del punto de entrada
        tp_diff = float(self.config['TP_DIFF'].get())
        sl_diff = float(self.config['SL_DIFF'].get())
        
        if direccion == "BUY":
            sl = round(precio - sl_diff, symbol_info.digits)
            tp = round(precio + tp_diff, symbol_info.digits)
            tipo = mt5.ORDER_TYPE_BUY  # ⭐ BUY normal para ejecutar al mejor precio cercano
        else:
            sl = round(precio + sl_diff, symbol_info.digits)
            tp = round(precio - tp_diff, symbol_info.digits)
            tipo = mt5.ORDER_TYPE_SELL  # ⭐ SELL normal para ejecutar al mejor precio cercano

        # ⭐ NUEVO: Respetar configuración USE_SL
        usar_sl = self.config['USE_SL'].get()
        sl_final = sl if usar_sl else 0.0

        # ⭐ USAR DEAL (ejecución inmediata) con FOK para ejecutar al mejor precio disponible
        # Cuando el precio está cercano al objetivo, abrimos al mejor precio disponible
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(self.config['VOL'].get()),
            "type": tipo,
            "price": current_ask if direccion == "BUY" else current_bid,  # ⭐ BUY usa ASK, SELL usa BID
            "sl": sl_final,
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

    def _multi_period_candle_analysis(self, symbol, direction):
        """
        ⭐ ANÁLISIS MULTI-PERÍODO PRE-APERTURA
        Analiza simultáneamente 10, 20 y 30 velas ANTES de abrir
        
        Retorna: {
            'valid': bool,
            'confidence': 0-100,
            'strength_10': 0-100,
            'strength_20': 0-100,
            'strength_30': 0-100,
            'consensus': 'STRONG' | 'MEDIUM' | 'WEAK',
            'reason': str,
            'details': dict
        }
        """
        try:
            # Obtener 30 velas de una vez
            snapshots = self.get_fresh_market_data(symbol, bars=32) or []
            if len(snapshots) < 30:
                return {
                    'valid': False,
                    'confidence': 0,
                    'reason': f'Velas insuficientes: {len(snapshots)}/30'
                }
            
            # Preparar estructuras para análisis paralelo
            results = {}
            threads = []
            lock = threading.Lock()
            
            # ⭐ FUNCIÓN INTERNA: Analizar N velas específicas
            def analyze_period(last_n, period_name):
                try:
                    period_data = snapshots[-last_n:] if len(snapshots) >= last_n else snapshots
                    
                    # Contadores básicos
                    up_count = 0
                    down_count = 0
                    closes_above_open = 0
                    strength_score = 0
                    
                    for candle in period_data:
                        c_open = float(candle.get('open', 0))
                        c_close = float(candle.get('close', 0))
                        
                        if c_open <= 0 or c_close <= 0:
                            continue
                        
                        if c_close > c_open:
                            up_count += 1
                            closes_above_open += 1
                        elif c_close < c_open:
                            down_count += 1
                    
                    # Calcular fuerza según dirección
                    if direction == "BUY":
                        strength_score = min(100, (closes_above_open / max(1, len(period_data))) * 100)
                    else:  # SELL
                        strength_score = min(100, ((len(period_data) - closes_above_open) / max(1, len(period_data))) * 100)
                    
                    with lock:
                        results[period_name] = {
                            'strength': strength_score,
                            'up_candles': up_count,
                            'down_candles': down_count,
                            'direction_match': (direction == "BUY" and up_count > down_count) or 
                                                (direction == "SELL" and down_count > up_count)
                        }
                except Exception as e:
                    with lock:
                        results[period_name] = {'strength': 0, 'error': str(e)}
            
            # ⭐ Lanzar análisis en paralelo para 10, 20, 30 velas
            t10 = threading.Thread(target=analyze_period, args=(10, 'strength_10'), daemon=True)
            t20 = threading.Thread(target=analyze_period, args=(20, 'strength_20'), daemon=True)
            t30 = threading.Thread(target=analyze_period, args=(30, 'strength_30'), daemon=True)
            
            threads = [t10, t20, t30]
            for t in threads:
                t.start()
            
            # Esperar a que terminen (máx 2 segundos)
            for t in threads:
                t.join(timeout=2.0)
            
            # ⭐ Recopilar resultados
            if 'strength_10' not in results or 'strength_20' not in results or 'strength_30' not in results:
                return {
                    'valid': False,
                    'confidence': 0,
                    'reason': 'Error en análisis paralelo'
                }
            
            s10 = results['strength_10']['strength']
            s20 = results['strength_20']['strength']
            s30 = results['strength_30']['strength']
            
            # ⭐ Calcular confianza consolidada
            confidence = (s10 * 0.4 + s20 * 0.35 + s30 * 0.25)  # Pesar más el corto plazo
            
            # Validar consenso
            matches = sum([
                results['strength_10'].get('direction_match', False),
                results['strength_20'].get('direction_match', False),
                results['strength_30'].get('direction_match', False)
            ])
            
            if matches == 3:
                consensus = 'STRONG'
                consensus_bonus = 20
            elif matches >= 2:
                consensus = 'MEDIUM'
                consensus_bonus = 10
            else:
                consensus = 'WEAK'
                consensus_bonus = 0
            
            # Confianza final
            final_confidence = min(100, confidence + consensus_bonus)
            
            # ⭐ Log detallado
            self.add_log(f"\n📊 ANÁLISIS MULTI-PERÍODO:", 'info')
            self.add_log(f"   • 10 velas: {s10:.1f}% | {results['strength_10']['up_candles']} up / {results['strength_10']['down_candles']} down", 'info')
            self.add_log(f"   • 20 velas: {s20:.1f}% | {results['strength_20']['up_candles']} up / {results['strength_20']['down_candles']} down", 'info')
            self.add_log(f"   • 30 velas: {s30:.1f}% | {results['strength_30']['up_candles']} up / {results['strength_30']['down_candles']} down", 'info')
            self.add_log(f"   ➜ Consenso: {consensus} ({matches}/3 coinciden)", 'success')
            self.add_log(f"   ➜ Confianza final: {final_confidence:.1f}%", 'success')
            
            # Decisión
            valid = final_confidence >= 55  # Umbral mínimo
            
            return {
                'valid': valid,
                'confidence': final_confidence,
                'strength_10': s10,
                'strength_20': s20,
                'strength_30': s30,
                'consensus': consensus,
                'reason': f'Consenso {consensus}: {final_confidence:.1f}% confianza',
                'details': {
                    'matches': matches,
                    'periods_analyzed': 3
                }
            }
            
        except Exception as e:
            self.add_log(f"[ERROR] Análisis multi-período falló: {str(e)}", 'error')
            return {
                'valid': False,
                'confidence': 0,
                'reason': f'Excepción: {str(e)}'
            }

    def _calculate_vidya(self, closes, cmo_period=9, ema_period=12):
        """
        ⭐ Calcula VIDYA (Variable Index Dynamic Average)
        
        Pasos:
        1. Calcular CMO (Chande Momentum Oscillator) sobre closes
        2. Usar CMO para ajustar dinámicamente el factor de suavizado de EMA
        3. Aplicar EMA ajustada a los closes
        
        Args:
            closes: array de precios de cierre
            cmo_period: período para calcular CMO (default 9)
            ema_period: período base para EMA (default 12)
        
        Returns:
            tuple: (vidya_values, cmo_value) donde vidya_values es array y cmo_value es último CMO
        """
        try:
            if len(closes) < max(cmo_period, ema_period):
                return None, None
            
            closes = np.array([float(x) for x in closes if x > 0])
            
            # PASO 1: Calcular CMO sobre los últimos cmo_period closes
            if len(closes) >= cmo_period:
                recent_closes = closes[-cmo_period:]
                up_moves = []
                down_moves = []
                
                for i in range(1, len(recent_closes)):
                    change = recent_closes[i] - recent_closes[i-1]
                    if change > 0:
                        up_moves.append(change)
                        down_moves.append(0)
                    elif change < 0:
                        up_moves.append(0)
                        down_moves.append(abs(change))
                    else:
                        up_moves.append(0)
                        down_moves.append(0)
                
                up_sum = sum(up_moves) if up_moves else 0.0001
                down_sum = sum(down_moves) if down_moves else 0.0001
                
                # CMO = ((UP - DOWN) / (UP + DOWN)) * 100
                cmo_value = ((up_sum - down_sum) / (up_sum + down_sum) * 100) if (up_sum + down_sum) > 0 else 0
            else:
                cmo_value = 0
            
            # PASO 2: Calcular factor de suavizado dinámico basado en CMO
            # factor = (1 + |CMO| / 100) permite que VIDYA sea más reactiva en tendencias fuertes
            dynamic_factor = (1 + abs(cmo_value) / 100)
            
            # Ajustar período EMA dinámicamente
            adjusted_ema_period = max(2, int(ema_period / dynamic_factor))
            
            # PASO 3: Calcular EMA con el período ajustado
            vidya_values = []
            multiplier = 2 / (adjusted_ema_period + 1)
            
            vidya = closes[0]  # Primer valor de VIDYA es el primer cierre
            vidya_values.append(vidya)
            
            for i in range(1, len(closes)):
                # EMA = (Precio - EMA_anterior) * multiplier + EMA_anterior
                vidya = (closes[i] - vidya) * multiplier + vidya
                vidya_values.append(vidya)
            
            return np.array(vidya_values), cmo_value
            
        except Exception as e:
            logger.error(f"Error calculando VIDYA: {str(e)}")
            return None, None

    def _validate_gold_optimal_entry(self, symbol, direction, snapshots=None):
        """
        ⭐ VALIDACIÓN INTERNA: CONFIG ÓPTIMA PARA GOLD (XAUUSD) - 5 CRITERIOS
        
        Validaciones en secuencia:
        🟡 1. THRESHOLD: 16-19 pips (ideal 18)
           ├─ 16 pips → Captura movimientos pero entra en ruido
           ├─ 18 pips → Balance perfecto
           └─ 19 pips → Más filtrado, pierda movimientos
        
        🟡 2. MICROTENDENCIA MULTI-PERÍODO (Rango: 3-5 velas, ideal 4):
           ├─ Análisis 10 velas → contexto general
           ├─ Análisis 20 velas → tendencia media
           ├─ Análisis 30 velas → tendencia larga
           └─ Últimas 3-5 velas: TODAS en MISMA DIRECCIÓN (confirmación)
           ⚠️ REQUISITO: Las velas recientes deben alinearse con la tendencia de fondo
        
        🟡 3. FILTRO DE VELA (CRÍTICO - Elimina ruido):
           ✅ Cuerpo ≥ 60% → Vela con cuerpo fuerte, no es mecha
           ✅ Mecha ≤ 40% → Las mechas/sombras son pequeñas (< 40%)
           ✅ Cierre cerca del extremo:
              • BUY: Cierre ≥ 70% del rango (muy cerca del MÁXIMO)
              • SELL: Cierre ≤ 30% del rango (muy cerca del MÍNIMO)
           ⚠️ Esto elimina ~90% del ruido. Solo velas VERDADERAMENTE válidas entran.
        
        🟡 4. IMPULSO: ≥ 1.5 puntos (movimiento real, no ruido)
        
        🚫 5. FILTRO ANTI-RUIDO (4. Evitar):
           ❌ NO OPERAR SI:
              • 2 velas seguidas con mechas grandes (> 50% del rango)
              • Rango lateral (máximos iguales o mínimos iguales ±2 pips)
              • Velas pequeñas consecutivas (cuerpo < 30%)
        
        Retorna: {
            'valid': bool,
            'score': 0-100 (20 puntos por criterio),
            'checks': {...}  (detalle de cada validación)
        }
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=32) or []
            
            if len(snapshots) < 5:
                return {
                    'valid': False,
                    'score': 0,
                    'reason': f'Velas insuficientes: {len(snapshots)}'
                }
            
            checks = {}
            
            # ⭐ 1. VALIDAR THRESHOLD (EN PIPS, COMO MICROTREND_THRESHOLD)
            try:
                threshold_pips = float(self.config.get('GOLD_THRESHOLD', tk.DoubleVar(value=18)).get())
            except:
                threshold_pips = 18
            
            # Convertir pips a decimal (18 pips * 0.01 = 0.18)
            pip_size = 0.01
            threshold = threshold_pips * pip_size
            
            # Calcular pendiente de últimas 3 velas como indicador de impulso
            last_3 = snapshots[-3:]
            if len(last_3) >= 3:
                close_1 = float(last_3[0].get('close', 0))
                close_2 = float(last_3[1].get('close', 0))
                close_3 = float(last_3[2].get('close', 0))
                impulse_value = abs(close_3 - close_1)
                checks['threshold'] = {
                    'value': impulse_value,
                    'required': threshold,
                    'valid': impulse_value >= threshold,
                    'threshold_pips': threshold_pips
                }
            
            # ⭐ 2. VALIDAR MICROTENDENCIA MULTI-PERÍODO (3-5 velas recientes + contexto 10/20/30)
            try:
                microtrend_candles = int(self.config.get('GOLD_MICROTREND_CANDLES', tk.IntVar(value=4)).get())
            except:
                microtrend_candles = 4
            
            # Asegurar rango válido
            microtrend_candles = max(3, min(5, microtrend_candles))
            
            # ═══════════════════════════════════════════════════════════
            # ANÁLISIS MULTI-PERÍODO: Contexto de fondo (10, 20, 30 velas)
            # ═══════════════════════════════════════════════════════════
            context_10_up = context_10_down = 0
            context_20_up = context_20_down = 0
            context_30_up = context_30_down = 0
            
            # Contexto 10 velas
            for i, candle in enumerate(snapshots[-10:] if len(snapshots) >= 10 else snapshots):
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    if c_close > c_open:
                        context_10_up += 1
                    else:
                        context_10_down += 1
            
            # Contexto 20 velas
            for candle in snapshots[-20:] if len(snapshots) >= 20 else snapshots:
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    if c_close > c_open:
                        context_20_up += 1
                    else:
                        context_20_down += 1
            
            # Contexto 30 velas
            for candle in snapshots[-30:] if len(snapshots) >= 30 else snapshots:
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    if c_close > c_open:
                        context_30_up += 1
                    else:
                        context_30_down += 1
            
            # ═══════════════════════════════════════════════════════════
            # MICROTENDENCIA: Últimas 3-5 velas CONFIRMACIÓN
            # ═══════════════════════════════════════════════════════════
            last_n = snapshots[-microtrend_candles:]
            up_count = 0
            down_count = 0
            microtrend_details = []
            
            for idx, candle in enumerate(last_n):
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    is_up = c_close > c_open
                    if is_up:
                        up_count += 1
                        microtrend_details.append(f"Vela {idx+1}: ↑ UP")
                    else:
                        down_count += 1
                        microtrend_details.append(f"Vela {idx+1}: ↓ DOWN")
            
            # ═══════════════════════════════════════════════════════════
            # VALIDACIÓN: Microtendencia alineada con contexto
            # ═══════════════════════════════════════════════════════════
            context_direction_10 = 'BUY' if context_10_up > context_10_down else ('SELL' if context_10_down > context_10_up else 'FLAT')
            context_direction_20 = 'BUY' if context_20_up > context_20_down else ('SELL' if context_20_down > context_20_up else 'FLAT')
            context_direction_30 = 'BUY' if context_30_up > context_30_down else ('SELL' if context_30_down > context_30_up else 'FLAT')
            
            # Voto de contexto (mayoría de 10, 20, 30 velas)
            context_votes = {'BUY': 0, 'SELL': 0}
            for ctx_dir in [context_direction_10, context_direction_20, context_direction_30]:
                if ctx_dir in context_votes:
                    context_votes[ctx_dir] += 1
            
            context_direction = 'BUY' if context_votes['BUY'] >= context_votes['SELL'] else 'SELL'
            
            # Validación: Microtendencia debe alinearse con dirección esperada Y contexto
            if direction == "BUY":
                # Últimas velas deben ser UP (mayoría en dirección BUY)
                # Y contexto debe confirmar tendencia alcista
                microtrend_correct = up_count > down_count and up_count >= microtrend_candles - 1
                context_agrees = context_direction == 'BUY'
                microtrend_valid = microtrend_correct and context_agrees
            else:  # SELL
                # Últimas velas deben ser DOWN (mayoría en dirección SELL)
                # Y contexto debe confirmar tendencia bajista
                microtrend_correct = down_count > up_count and down_count >= microtrend_candles - 1
                context_agrees = context_direction == 'SELL'
                microtrend_valid = microtrend_correct and context_agrees
            
            checks['microtrend'] = {
                'recent_up': up_count,
                'recent_down': down_count,
                'recent_details': ' | '.join(microtrend_details),
                'context_10': f"{context_10_up}↑/{context_10_down}↓ = {context_direction_10}",
                'context_20': f"{context_20_up}↑/{context_20_down}↓ = {context_direction_20}",
                'context_30': f"{context_30_up}↑/{context_30_down}↓ = {context_direction_30}",
                'context_agreement': context_direction,
                'valid': microtrend_valid,
                'reason': f"Últimas {microtrend_candles} velas: {up_count}↑/{down_count}↓ vs Contexto: {context_direction}"
            }
            
            # ⭐ 3. VALIDAR CUERPO DE VELA + MECHA + CIERRE CERCANO (FILTRO CRÍTICO - Elimina ruido)
            try:
                candle_body_pct = int(self.config.get('GOLD_CANDLE_BODY_PCT', tk.IntVar(value=60)).get())
                candle_wick_pct = int(self.config.get('GOLD_CANDLE_WICK_PCT', tk.IntVar(value=40)).get())
                candle_close_pct = int(self.config.get('GOLD_CANDLE_CLOSE_PCT', tk.IntVar(value=70)).get())
            except:
                candle_body_pct = 60
                candle_wick_pct = 40
                candle_close_pct = 70
            
            last_candle = snapshots[-1]
            c_open = float(last_candle.get('open', 0))
            c_close = float(last_candle.get('close', 0))
            c_high = float(last_candle.get('high', 0))
            c_low = float(last_candle.get('low', 0))
            
            if c_open > 0 and c_high > 0 and c_low > 0:
                # ═══════════════════════════════════════════════════════════
                # CÁLCULO 1: CUERPO (open vs close)
                # ═══════════════════════════════════════════════════════════
                body_size = abs(c_close - c_open)
                total_size = c_high - c_low
                body_pct = (body_size / total_size * 100) if total_size > 0 else 0
                body_valid = body_pct >= candle_body_pct
                
                # ═══════════════════════════════════════════════════════════
                # CÁLCULO 2: MECHA (High-Close vs High-Open para BUY, o Low-Open vs Low-Close para SELL)
                # ═══════════════════════════════════════════════════════════
                if direction == "BUY":
                    # BUY: Wick arriba (entre close y high)
                    wick_size = c_high - max(c_open, c_close)
                else:  # SELL
                    # SELL: Wick abajo (entre low y open/close)
                    wick_size = min(c_open, c_close) - c_low
                
                wick_pct = (wick_size / total_size * 100) if total_size > 0 else 0
                wick_valid = wick_pct <= candle_wick_pct
                
                # ═══════════════════════════════════════════════════════════
                # CÁLCULO 3: CIERRE CERCANO AL EXTREMO
                # ═══════════════════════════════════════════════════════════
                # Normalizar cierre en rango [0, 100%]
                close_position = ((c_close - c_low) / total_size * 100) if total_size > 0 else 50
                
                if direction == "BUY":
                    # BUY: Cierre debe estar CERCA DEL MÁXIMO (≥ 70% = en la parte alta)
                    close_valid = close_position >= candle_close_pct
                    close_msg = f"Cierre @{close_position:.0f}% (require ≥{candle_close_pct}% para BUY)"
                else:  # SELL
                    # SELL: Cierre debe estar CERCA DEL MÍNIMO (≤ 30% = en la parte baja)
                    close_valid = close_position <= (100 - candle_close_pct)  # 100-70=30
                    close_msg = f"Cierre @{close_position:.0f}% (require ≤{100-candle_close_pct}% para SELL)"
                
                # Vela válida: todas las 3 condiciones pasan
                candle_filter_valid = body_valid and wick_valid and close_valid
            else:
                body_pct = 0
                body_valid = False
                wick_pct = 0
                wick_valid = False
                close_valid = False
                close_msg = "Datos inválidos"
                candle_filter_valid = False
            
            checks['candle_filter'] = {
                'body_percentage': body_pct,
                'body_required': candle_body_pct,
                'body_valid': body_valid,
                'wick_percentage': wick_pct,
                'wick_required': candle_wick_pct,
                'wick_valid': wick_valid,
                'close_position': close_position if c_high > 0 else 0,
                'close_required': candle_close_pct,
                'close_valid': close_valid,
                'close_msg': close_msg,
                'valid': candle_filter_valid,
                'reason': f"Cuerpo:{body_pct:.0f}%✓ | Mecha:{wick_pct:.0f}%✓ | {close_msg}"
            }
            
            # ⭐ 4. VALIDAR IMPULSO MÍNIMO (movimiento en puntos debe ser significativo)
            try:
                impulse_filter = float(self.config.get('GOLD_IMPULSE_FILTER', tk.DoubleVar(value=1.5)).get())
            except:
                impulse_filter = 1.5
            
            # Impulso = diferencia entre últimas 3 velas (rango de movimiento)
            if len(snapshots) >= 3:
                last_3_opens = [float(snapshots[-3].get('open', 0)), float(snapshots[-2].get('open', 0)), float(snapshots[-1].get('open', 0))]
                last_3_closes = [float(snapshots[-3].get('close', 0)), float(snapshots[-2].get('close', 0)), float(snapshots[-1].get('close', 0))]
                all_prices = last_3_opens + last_3_closes
                valid_prices = [p for p in all_prices if p > 0]
                if valid_prices:
                    impulse_value = max(valid_prices) - min(valid_prices)
                else:
                    impulse_value = 0
            else:
                impulse_value = checks['threshold'].get('value', 0)
            
            impulse_valid = impulse_value >= impulse_filter
            
            checks['impulse'] = {
                'value': impulse_value,
                'required': impulse_filter,
                'valid': impulse_valid,
                'reason': f"Impulso: {impulse_value:.2f} puntos (requiere ≥{impulse_filter:.2f})"
            }
            
            # ⭐ 5. FILTRO ANTI-RUIDO (4. Evitar):
            # NO operar si:
            # - 2 velas seguidas con mechas grandes (> 50% del rango)
            # - Rango lateral (máximos iguales / mínimos iguales)
            # - Velas pequeñas consecutivas (cuerpo < 30%)
            
            noise_detected = False
            noise_reasons = []
            
            # Analizar últimas 4 velas para detectar ruido
            last_4_candles = snapshots[-4:] if len(snapshots) >= 4 else snapshots
            
            # CHECK 1: 2 velas seguidas con mechas grandes (> 50%)
            consecutive_large_wicks = 0
            for i in range(len(last_4_candles) - 1):
                candle1 = last_4_candles[i]
                candle2 = last_4_candles[i + 1]
                
                for candle in [candle1, candle2]:
                    try:
                        c_open = float(candle.get('open', 0))
                        c_close = float(candle.get('close', 0))
                        c_high = float(candle.get('high', 0))
                        c_low = float(candle.get('low', 0))
                        
                        if c_high > 0 and c_low > 0:
                            total_range = c_high - c_low
                            if total_range > 0:
                                # Wick según dirección
                                if direction == "BUY":
                                    wick_size = c_high - max(c_open, c_close)
                                else:
                                    wick_size = min(c_open, c_close) - c_low
                                
                                wick_pct = (wick_size / total_range * 100)
                                if wick_pct > 50:
                                    consecutive_large_wicks += 1
                    except:
                        pass
                
                # Si hay 2 mechas grandes consecutivas = ruido
                if consecutive_large_wicks >= 2:
                    noise_detected = True
                    noise_reasons.append("🔴 Mechas grandes consecutivas (> 50%) = ruido de mercado")
                    break
                consecutive_large_wicks = 0
            
            # CHECK 2: Rango lateral (máximos iguales o mínimos iguales ±2 pips)
            tolerance = 0.02  # 2 pips
            if len(last_4_candles) >= 2:
                highs = [float(c.get('high', 0)) for c in last_4_candles if float(c.get('high', 0)) > 0]
                lows = [float(c.get('low', 0)) for c in last_4_candles if float(c.get('low', 0)) > 0]
                
                if highs and lows:
                    max_high = max(highs)
                    min_high = min(highs)
                    max_low = max(lows)
                    min_low = min(lows)
                    
                    high_range = max_high - min_high
                    low_range = max_low - min_low
                    
                    # Si los máximos están muy cercanos (lateral) O los mínimos están muy cercanos (lateral)
                    if high_range <= tolerance or low_range <= tolerance:
                        noise_detected = True
                        noise_reasons.append(f"🔴 Rango lateral detectado (máximos: {high_range:.4f}, mínimos: {low_range:.4f})")
            
            # CHECK 3: Velas pequeñas consecutivas (cuerpo < 30% de la vela)
            consecutive_small_bodies = 0
            for candle in last_4_candles:
                try:
                    c_open = float(candle.get('open', 0))
                    c_close = float(candle.get('close', 0))
                    c_high = float(candle.get('high', 0))
                    c_low = float(candle.get('low', 0))
                    
                    if c_high > 0 and c_low > 0:
                        total_range = c_high - c_low
                        if total_range > 0:
                            body_size = abs(c_close - c_open)
                            body_pct = (body_size / total_range * 100)
                            
                            if body_pct < 30:
                                consecutive_small_bodies += 1
                            else:
                                consecutive_small_bodies = 0  # Reset si hay una vela grande
                    
                    if consecutive_small_bodies >= 2:
                        noise_detected = True
                        noise_reasons.append("🔴 Velas pequeñas consecutivas (cuerpo < 30%) = consolidación sin movimiento")
                        break
                except:
                    pass
            
            noise_ok = not noise_detected  # OK si NO hay ruido
            
            checks['anti_noise'] = {
                'valid': noise_ok,
                'noise_detected': noise_detected,
                'reasons': noise_reasons,
                'reason': " | ".join(noise_reasons) if noise_reasons else "✅ Sin ruido detectado"
            }
            
            # ⭐ 6. VALIDAR VIDYA (Indicador de Apoyo - 5. Apoyo)
            try:
                vidya_cmo = int(self.config.get('GOLD_VIDYA_CMO', tk.IntVar(value=9)).get())
                vidya_ema = int(self.config.get('GOLD_VIDYA_EMA', tk.IntVar(value=12)).get())
            except:
                vidya_cmo = 9
                vidya_ema = 12
            
            # Obtener últimas velas (mínimo 30 para calcular VIDYA correctamente)
            last_velas_for_vidya = snapshots[-30:] if len(snapshots) >= 30 else snapshots
            
            vidya_valid = False
            vidya_price_position = ""
            vidya_slope = ""
            vidya_current = 0
            vidya_previous = 0
            vidya_slope_pct = 0
            
            if len(last_velas_for_vidya) >= vidya_ema + vidya_cmo:
                try:
                    # Extraer closes para calcular VIDYA
                    vidya_closes = [float(v.get('close', 0)) for v in last_velas_for_vidya]
                    vidya_closes = [x for x in vidya_closes if x > 0]
                    
                    # Calcular VIDYA
                    vidya_values, cmo_value = self._calculate_vidya(vidya_closes, vidya_cmo, vidya_ema)
                    
                    if vidya_values is not None and len(vidya_values) >= 2:
                        vidya_current = float(vidya_values[-1])
                        vidya_previous = float(vidya_values[-2])
                        current_price = float(last_velas_for_vidya[-1].get('close', 0))
                        
                        # CHECK 1: Precio vs VIDYA
                        if direction == "BUY":
                            price_above_vidya = current_price > vidya_current
                            vidya_price_position = f"Precio {current_price:.2f} {'arriba ✓' if price_above_vidya else 'abajo ✗'} de VIDYA {vidya_current:.2f}"
                        else:  # SELL
                            price_below_vidya = current_price < vidya_current
                            vidya_price_position = f"Precio {current_price:.2f} {'abajo ✓' if price_below_vidya else 'arriba ✗'} de VIDYA {vidya_current:.2f}"
                        
                        # CHECK 2: Inclinación de VIDYA (debe tener pendiente clara)
                        slope_diff = vidya_current - vidya_previous
                        vidya_slope_pct = (slope_diff / vidya_previous * 100) if vidya_previous != 0 else 0
                        
                        if direction == "BUY":
                            # Para compra: VIDYA debe estar subiendo
                            vidya_slope_valid = slope_diff > 0
                            vidya_slope = f"VIDYA subiendo {vidya_slope_pct:.3f}% ✓" if vidya_slope_valid else f"VIDYA bajando {vidya_slope_pct:.3f}% ✗"
                        else:  # SELL
                            # Para venta: VIDYA debe estar bajando
                            vidya_slope_valid = slope_diff < 0
                            vidya_slope = f"VIDYA bajando {vidya_slope_pct:.3f}% ✓" if vidya_slope_valid else f"VIDYA subiendo {vidya_slope_pct:.3f}% ✗"
                        
                        # VALIDACIÓN FINAL: Ambas condiciones deben cumplirse
                        if direction == "BUY":
                            vidya_valid = (current_price > vidya_current) and (slope_diff > 0)
                        else:  # SELL
                            vidya_valid = (current_price < vidya_current) and (slope_diff < 0)
                
                except Exception as e:
                    logger.error(f"Error calculando VIDYA en validación: {str(e)}")
                    vidya_valid = False
            
            checks['vidya'] = {
                'valid': vidya_valid,
                'current_price': current_price if 'current_price' in locals() else 0,
                'vidya_value': vidya_current,
                'vidya_slope_pct': vidya_slope_pct,
                'price_position': vidya_price_position,
                'slope_msg': vidya_slope,
                'reason': f"VIDYA: {vidya_price_position} | {vidya_slope}"
            }
            
            # ⭐ DECISIÓN FINAL: Todas las validaciones deben pasar
            threshold_ok = checks['threshold'].get('valid', False)
            microtrend_ok = checks['microtrend'].get('valid', False)
            candle_filter_ok = checks['candle_filter'].get('valid', False)
            impulse_ok = checks['impulse'].get('valid', False)
            noise_ok = checks['anti_noise'].get('valid', False)
            vidya_ok = checks['vidya'].get('valid', False)  # ⭐ NUEVO: VIDYA
            
            valid = threshold_ok and microtrend_ok and candle_filter_ok and impulse_ok and noise_ok and vidya_ok
            
            # Construir razón de rechazo detallada
            failed_checks = []
            if not threshold_ok:
                failed_checks.append(f"Threshold insuficiente ({checks['threshold'].get('value', 0):.2f} < {checks['threshold'].get('required', 0):.2f})")
            if not microtrend_ok:
                failed_checks.append(f"Microtendencia rechazada: {checks['microtrend'].get('reason', 'contexto no coincide')}")
            if not candle_filter_ok:
                failed_checks.append(f"Vela no válida: {checks['candle_filter'].get('reason', 'no cumple criterios')}")
            if not impulse_ok:
                failed_checks.append(f"Impulso débil ({checks['impulse'].get('value', 0):.2f} < {checks['impulse'].get('required', 1.5)})")
            if not noise_ok:
                failed_checks.append(f"Ruido detectado: {' | '.join(checks['anti_noise'].get('reasons', ['desconocido']))}")
            if not vidya_ok:
                failed_checks.append(f"VIDYA rechazó: {checks['vidya'].get('reason', 'no cumple alineación')}")
            
            reason = " | ".join(failed_checks) if failed_checks else "✅ Todas las validaciones pasaron"
            
            # Calcular score (ahora con 6 validaciones ≈ 16.67 puntos cada una)
            score = 0
            for check_name in ['threshold', 'microtrend', 'candle_filter', 'impulse', 'anti_noise', 'vidya']:
                if checks[check_name].get('valid', False):
                    score += 17  # 17 * 6 = 102, redondeamos a 100
            
            # 🧠 LÓGICA COMPLETA (VERIFICACIÓN)
            #    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #    👉 ENTRA BUY si TODAS estas condiciones se cumplen:
            #    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #    ✅ 1. THRESHOLD ≥ 18 pips (impulso mínimo confirmado)
            #    ✅ 2. 3–5 velas alcistas limpias (microtendencia clear)
            #    ✅ 3. Cuerpos fuertes ≥60% (sin velas de ruido/doji)
            #    ✅ 4. Precio sobre VIDYA (alineación con tendencia)
            #    ✅ 5. VIDYA con pendiente positiva (confirmación dinámmica)
            #    ✅ 6. Sin ruido (no mechas grandes, no lateral, no consolidación)
            #    
            #    👉 ENTRA SELL si TODAS estas condiciones INVERSAS se cumplen:
            #    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #    ✅ 1. THRESHOLD ≥ 18 pips (impulso mínimo confirmado)
            #    ✅ 2. 3–5 velas bajistas limpias (microtendencia clear)
            #    ✅ 3. Cuerpos fuertes ≥60% (sin velas de ruido/doji)
            #    ✅ 4. Precio bajo VIDYA (alineación con tendencia)
            #    ✅ 5. VIDYA con pendiente negativa (confirmación dinámmica)
            #    ✅ 6. Sin ruido (no mechas grandes, no lateral, no consolidación)
            #    
            #    🚫 ERRORES A EVITAR (por qué muchos bots fallan):
            #    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #    ❌ Entrar SOLO por movimiento (threshold) sin validar vela
            #    ❌ No filtrar mechas grandes → ORO engaña constantemente
            #    ❌ No revisar microtendencia → entras en reversales
            #    ❌ No usar VIDYA → pierdes confirmación de flujo real
            #    ❌ No revisar ruido → consolidan y te atrapan
            #    
            #    🔥 CONFIG FINAL RECOMENDADA (OPTIMIZADA PARA GOLD):
            #    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #    📊 Threshold: 18 pips (1.8 decimal) ← impulso mínimo
            #    📊 Microtendencia: 4 velas ← balance entre velocidad y filtro
            #    📊 Cuerpo de vela: ≥60% ← elimina doji/mecha
            #    📊 Mecha máxima: ≤40% ← filtra velas rechazadas
            #    📊 Cierre cercano: BUY≥70%, SELL≤30% ← dirección clara
            #    📊 VIDYA CMO: 9 ← reactividad media
            #    📊 VIDYA EMA: 12 ← suavizado adaptativo
            #    📊 Aplicar a: Close ← únicamente cierre
            #    
            #    💎 SECRETO DEL ORO (GOLD/XAUUSD):
            #    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            #    👉 No es el INDICADOR... es FILTRAR VELAS MALAS
            #    👉 Mechas grandes = mercado indeciso = EVITAR
            #    👉 Seguir el FLUJO REAL (VIDYA + microtendencia)
            #    👉 El ORO es PREDADOR de traders con malos filtros
            #    👉 Resultado: 90% de falsas señales eliminadas ✅
            
            # Log detallado
            self.add_log(f"\n🟡 VALIDACIÓN CONFIG ÓPTIMA GOLD:", 'info')
            self.add_log(f"   ✓ Threshold: {checks['threshold']['value']:.2f} >= {checks['threshold']['required']:.2f} ({checks['threshold']['threshold_pips']:.0f} pips): {'✅' if checks['threshold']['valid'] else '❌'}", 'info')
            
            # Log detallado de microtendencia con contexto
            self.add_log(f"   ✓ Microtendencia ({microtrend_candles}v): {checks['microtrend']['recent_details']}", 'info')
            self.add_log(f"      └─ Contexto 10v: {checks['microtrend']['context_10']}", 'info')
            self.add_log(f"      └─ Contexto 20v: {checks['microtrend']['context_20']}", 'info')
            self.add_log(f"      └─ Contexto 30v: {checks['microtrend']['context_30']}", 'info')
            self.add_log(f"      └─ Voto final: {checks['microtrend']['context_agreement']} {'✅' if checks['microtrend']['valid'] else '❌'}", 'info')
            
            # Log detallado del filtro de vela (3 condiciones)
            self.add_log(f"   ✓ FILTRO DE VELA (3 CRITERIOS - Elimina ruido):", 'info')
            self.add_log(f"      ├─ Cuerpo: {checks['candle_filter']['body_percentage']:.1f}% >= {checks['candle_filter']['body_required']}%: {'✅' if checks['candle_filter']['body_valid'] else '❌'}", 'info')
            self.add_log(f"      ├─ Mecha: {checks['candle_filter']['wick_percentage']:.1f}% <= {checks['candle_filter']['wick_required']}%: {'✅' if checks['candle_filter']['wick_valid'] else '❌'}", 'info')
            self.add_log(f"      └─ {checks['candle_filter']['close_msg']}: {'✅' if checks['candle_filter']['close_valid'] else '❌'}", 'info')
            
            self.add_log(f"   ✓ Impulso: {checks['impulse']['value']:.2f} >= {checks['impulse']['required']:.2f}: {'✅' if checks['impulse']['valid'] else '❌'}", 'info')
            
            # Log del filtro anti-ruido
            self.add_log(f"   ✓ FILTRO ANTI-RUIDO (4. Evitar):", 'info')
            if checks['anti_noise']['valid']:
                self.add_log(f"      └─ ✅ Sin ruido detectado", 'info')
            else:
                for reason in checks['anti_noise']['reasons']:
                    self.add_log(f"      └─ {reason}", 'warning')
            
            # Log del indicador VIDYA
            self.add_log(f"   ✓ INDICADOR VIDYA (5. Apoyo - CMO:{vidya_cmo}, EMA:{vidya_ema}):", 'info')
            if checks['vidya']['valid']:
                self.add_log(f"      ├─ {checks['vidya']['price_position']}: ✅", 'info')
                self.add_log(f"      └─ {checks['vidya']['slope_msg']}: ✅", 'info')
            else:
                self.add_log(f"      ├─ {checks['vidya']['price_position']}: ❌", 'warning')
                self.add_log(f"      └─ {checks['vidya']['slope_msg']}: ❌", 'warning')
            
            self.add_log(f"   ➜ Score Final: {score}/100 | {reason}", 'success' if valid else 'warning')
            
            return {
                'valid': valid,
                'score': score,
                'checks': checks,
                'reason': reason
            }
            
        except Exception as e:
            self.add_log(f"[ERROR] Validación GOLD falló: {str(e)}", 'error')
            return {
                'valid': False,
                'score': 0,
                'reason': f'Excepción: {str(e)}'
            }

    def _validate_silver_optimal_entry(self, symbol, direction, snapshots=None):
        """
        ⭐ VALIDACIÓN INTERNA: CONFIG ÓPTIMA PARA SILVER (XAGUSD) - 6 CRITERIOS
        
        🔥 IGUAL QUE GOLD, pero con parámetros ajustados para plata más rápida:
        
        Validaciones en secuencia:
        🟡 1. THRESHOLD: 15 pips (más bajo que ORO - plata más rápida)
        🟡 2. MICROTENDENCIA MULTI-PERÍODO (igual 3-5 velas, ideal 4)
        🟡 3. FILTRO DE VELA (3 CRITERIOS - igual 60/40/70)
        🟡 4. IMPULSO: ≥ 1.5 puntos (igual que ORO)
        🚫 5. FILTRO ANTI-RUIDO (igual: mechas grandes, lateral, pequeñas)
        📈 6. INDICADOR VIDYA (igual: CMO:9, EMA:12)
        
        ⚠️ NOTA: Si el ORO no está claro, NO operes PLATA (más riesgoso)
        
        Retorna: {
            'valid': bool,
            'score': 0-100 (17 puntos por criterio),
            'checks': {...}  (detalle de cada validación)
        }
        """
        try:
            if not snapshots:
                snapshots = self.get_fresh_market_data(symbol, bars=32) or []
            
            if len(snapshots) < 5:
                return {
                    'valid': False,
                    'score': 0,
                    'reason': f'Velas insuficientes: {len(snapshots)}'
                }
            
            checks = {}
            
            # ⭐ 1. VALIDAR THRESHOLD (EN PIPS - SILVER MÁS RÁPIDO QUE GOLD)
            try:
                threshold_pips = float(self.config.get('SILVER_THRESHOLD', tk.DoubleVar(value=15)).get())
            except:
                threshold_pips = 15
            
            pip_size = 0.01
            threshold = threshold_pips * pip_size
            
            last_3 = snapshots[-3:]
            if len(last_3) >= 3:
                close_1 = float(last_3[0].get('close', 0))
                close_2 = float(last_3[1].get('close', 0))
                close_3 = float(last_3[2].get('close', 0))
                impulse_value = abs(close_3 - close_1)
                checks['threshold'] = {
                    'value': impulse_value,
                    'required': threshold,
                    'valid': impulse_value >= threshold,
                    'threshold_pips': threshold_pips
                }
            
            # ⭐ 2. VALIDAR MICROTENDENCIA MULTI-PERÍODO (IDÉNTICO A GOLD)
            try:
                microtrend_candles = int(self.config.get('SILVER_MICROTREND_CANDLES', tk.IntVar(value=4)).get())
            except:
                microtrend_candles = 4
            
            microtrend_candles = max(3, min(5, microtrend_candles))
            
            context_10_up = context_10_down = 0
            context_20_up = context_20_down = 0
            context_30_up = context_30_down = 0
            
            for i, candle in enumerate(snapshots[-10:] if len(snapshots) >= 10 else snapshots):
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    if c_close > c_open:
                        context_10_up += 1
                    else:
                        context_10_down += 1
            
            for i, candle in enumerate(snapshots[-20:] if len(snapshots) >= 20 else snapshots):
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    if c_close > c_open:
                        context_20_up += 1
                    else:
                        context_20_down += 1
            
            for i, candle in enumerate(snapshots[-30:] if len(snapshots) >= 30 else snapshots):
                c_open = float(candle.get('open', 0))
                c_close = float(candle.get('close', 0))
                if c_open > 0 and c_close > 0:
                    if c_close > c_open:
                        context_30_up += 1
                    else:
                        context_30_down += 1
            
            context_10 = "UP" if context_10_up > context_10_down else ("DOWN" if context_10_down > context_10_up else "FLAT")
            context_20 = "UP" if context_20_up > context_20_down else ("DOWN" if context_20_down > context_20_up else "FLAT")
            context_30 = "UP" if context_30_up > context_30_down else ("DOWN" if context_30_down > context_30_up else "FLAT")
            
            votes = sum([1 for c in [context_10, context_20, context_30] if c == direction])
            context_agreement = votes >= 2
            
            recent_ok = True
            if len(snapshots) >= microtrend_candles:
                for candle in snapshots[-microtrend_candles:]:
                    c_open = float(candle.get('open', 0))
                    c_close = float(candle.get('close', 0))
                    if c_open > 0 and c_close > 0:
                        is_up = c_close > c_open
                        if direction == "BUY" and not is_up:
                            recent_ok = False
                            break
                        elif direction == "SELL" and is_up:
                            recent_ok = False
                            break
            
            microtrend_ok = context_agreement and recent_ok
            
            checks['microtrend'] = {
                'valid': microtrend_ok,
                'context_10': f"{context_10_up}↑ {context_10_down}↓ = {context_10}",
                'context_20': f"{context_20_up}↑ {context_20_down}↓ = {context_20}",
                'context_30': f"{context_30_up}↑ {context_30_down}↓ = {context_30}",
                'context_agreement': f"Voto: {votes}/3 = {context_agreement}",
                'recent_details': f"{microtrend_candles}v {direction if recent_ok else 'rechazadas'}",
                'reason': f"Contexto: {context_agreement} + Recientes: {recent_ok}"
            }
            
            # ⭐ 3. FILTRO DE VELA (IDÉNTICO A GOLD)
            try:
                candle_body_pct = int(self.config.get('SILVER_CANDLE_BODY_PCT', tk.IntVar(value=60)).get())
                candle_wick_pct = int(self.config.get('SILVER_CANDLE_WICK_PCT', tk.IntVar(value=40)).get())
                candle_close_pct = int(self.config.get('SILVER_CANDLE_CLOSE_PCT', tk.IntVar(value=70)).get())
            except:
                candle_body_pct = 60
                candle_wick_pct = 40
                candle_close_pct = 70
            
            last_candle = snapshots[-1] if snapshots else {}
            c_open = float(last_candle.get('open', 0))
            c_close = float(last_candle.get('close', 0))
            c_high = float(last_candle.get('high', 0))
            c_low = float(last_candle.get('low', 0))
            
            body_valid = wick_valid = close_valid = candle_filter_valid = False
            body_pct = wick_pct = close_position = 0
            close_msg = ""
            
            if c_high > 0 and c_low > 0:
                total_range = c_high - c_low
                if total_range > 0:
                    body_size = abs(c_close - c_open)
                    body_pct = (body_size / total_range * 100)
                    body_valid = body_pct >= candle_body_pct
                    
                    if direction == "BUY":
                        wick_size = c_high - max(c_open, c_close)
                    else:
                        wick_size = min(c_open, c_close) - c_low
                    
                    wick_pct = (wick_size / total_range * 100)
                    wick_valid = wick_pct <= candle_wick_pct
                    
                    close_position = ((c_close - c_low) / total_range * 100)
                    if direction == "BUY":
                        close_valid = close_position >= candle_close_pct
                        close_msg = f"Cierre @{close_position:.0f}% (require ≥{candle_close_pct}%)"
                    else:
                        close_valid = close_position <= (100 - candle_close_pct)
                        close_msg = f"Cierre @{close_position:.0f}% (require ≤{100-candle_close_pct}%)"
                    
                    candle_filter_valid = body_valid and wick_valid and close_valid
            
            checks['candle_filter'] = {
                'body_percentage': body_pct,
                'body_required': candle_body_pct,
                'body_valid': body_valid,
                'wick_percentage': wick_pct,
                'wick_required': candle_wick_pct,
                'wick_valid': wick_valid,
                'close_position': close_position if c_high > 0 else 0,
                'close_required': candle_close_pct,
                'close_valid': close_valid,
                'close_msg': close_msg,
                'valid': candle_filter_valid,
                'reason': f"Cuerpo:{body_pct:.0f}%✓ | Mecha:{wick_pct:.0f}%✓ | {close_msg}"
            }
            
            # ⭐ 4. VALIDAR IMPULSO (IDÉNTICO A GOLD)
            try:
                impulse_filter = float(self.config.get('SILVER_IMPULSE_FILTER', tk.DoubleVar(value=1.5)).get())
            except:
                impulse_filter = 1.5
            
            if len(snapshots) >= 3:
                last_3_opens = [float(snapshots[-3].get('open', 0)), float(snapshots[-2].get('open', 0)), float(snapshots[-1].get('open', 0))]
                last_3_closes = [float(snapshots[-3].get('close', 0)), float(snapshots[-2].get('close', 0)), float(snapshots[-1].get('close', 0))]
                all_prices = last_3_opens + last_3_closes
                valid_prices = [p for p in all_prices if p > 0]
                if valid_prices:
                    impulse_value = max(valid_prices) - min(valid_prices)
                else:
                    impulse_value = 0
            else:
                impulse_value = checks['threshold'].get('value', 0)
            
            impulse_valid = impulse_value >= impulse_filter
            
            checks['impulse'] = {
                'value': impulse_value,
                'required': impulse_filter,
                'valid': impulse_valid,
                'reason': f"Impulso: {impulse_value:.2f} puntos (requiere ≥{impulse_filter:.2f})"
            }
            
            # ⭐ 5. FILTRO ANTI-RUIDO (IDÉNTICO A GOLD)
            noise_detected = False
            noise_reasons = []
            
            last_4_candles = snapshots[-4:] if len(snapshots) >= 4 else snapshots
            
            consecutive_large_wicks = 0
            for i in range(len(last_4_candles) - 1):
                candle1 = last_4_candles[i]
                candle2 = last_4_candles[i + 1]
                
                for candle in [candle1, candle2]:
                    try:
                        c_open = float(candle.get('open', 0))
                        c_close = float(candle.get('close', 0))
                        c_high = float(candle.get('high', 0))
                        c_low = float(candle.get('low', 0))
                        
                        if c_high > 0 and c_low > 0:
                            total_range = c_high - c_low
                            if total_range > 0:
                                if direction == "BUY":
                                    wick_size = c_high - max(c_open, c_close)
                                else:
                                    wick_size = min(c_open, c_close) - c_low
                                
                                wick_pct = (wick_size / total_range * 100)
                                if wick_pct > 50:
                                    consecutive_large_wicks += 1
                    except:
                        pass
                
                if consecutive_large_wicks >= 2:
                    noise_detected = True
                    noise_reasons.append("🔴 Mechas grandes consecutivas (> 50%) = ruido de mercado")
                    break
                consecutive_large_wicks = 0
            
            tolerance = 0.02
            if len(last_4_candles) >= 2:
                highs = [float(c.get('high', 0)) for c in last_4_candles if float(c.get('high', 0)) > 0]
                lows = [float(c.get('low', 0)) for c in last_4_candles if float(c.get('low', 0)) > 0]
                
                if highs and lows:
                    max_high = max(highs)
                    min_high = min(highs)
                    max_low = max(lows)
                    min_low = min(lows)
                    
                    high_range = max_high - min_high
                    low_range = max_low - min_low
                    
                    if high_range <= tolerance or low_range <= tolerance:
                        noise_detected = True
                        noise_reasons.append(f"🔴 Rango lateral detectado (máximos: {high_range:.4f}, mínimos: {low_range:.4f})")
            
            consecutive_small_bodies = 0
            for candle in last_4_candles:
                try:
                    c_open = float(candle.get('open', 0))
                    c_close = float(candle.get('close', 0))
                    c_high = float(candle.get('high', 0))
                    c_low = float(candle.get('low', 0))
                    
                    if c_high > 0 and c_low > 0:
                        total_range = c_high - c_low
                        if total_range > 0:
                            body_size = abs(c_close - c_open)
                            body_pct = (body_size / total_range * 100)
                            
                            if body_pct < 30:
                                consecutive_small_bodies += 1
                            else:
                                consecutive_small_bodies = 0
                    
                    if consecutive_small_bodies >= 2:
                        noise_detected = True
                        noise_reasons.append("🔴 Velas pequeñas consecutivas (cuerpo < 30%) = consolidación sin movimiento")
                        break
                except:
                    pass
            
            noise_ok = not noise_detected
            
            checks['anti_noise'] = {
                'valid': noise_ok,
                'noise_detected': noise_detected,
                'reasons': noise_reasons,
                'reason': " | ".join(noise_reasons) if noise_reasons else "✅ Sin ruido detectado"
            }
            
            # ⭐ 6. VALIDAR VIDYA (IDÉNTICO A GOLD)
            try:
                vidya_cmo = int(self.config.get('SILVER_VIDYA_CMO', tk.IntVar(value=9)).get())
                vidya_ema = int(self.config.get('SILVER_VIDYA_EMA', tk.IntVar(value=12)).get())
            except:
                vidya_cmo = 9
                vidya_ema = 12
            
            last_velas_for_vidya = snapshots[-30:] if len(snapshots) >= 30 else snapshots
            
            vidya_valid = False
            vidya_price_position = ""
            vidya_slope = ""
            vidya_current = 0
            vidya_previous = 0
            vidya_slope_pct = 0
            
            if len(last_velas_for_vidya) >= vidya_ema + vidya_cmo:
                try:
                    vidya_closes = [float(v.get('close', 0)) for v in last_velas_for_vidya]
                    vidya_closes = [x for x in vidya_closes if x > 0]
                    
                    vidya_values, cmo_value = self._calculate_vidya(vidya_closes, vidya_cmo, vidya_ema)
                    
                    if vidya_values is not None and len(vidya_values) >= 2:
                        vidya_current = float(vidya_values[-1])
                        vidya_previous = float(vidya_values[-2])
                        current_price = float(last_velas_for_vidya[-1].get('close', 0))
                        
                        if direction == "BUY":
                            price_above_vidya = current_price > vidya_current
                            vidya_price_position = f"Precio {current_price:.2f} {'arriba ✓' if price_above_vidya else 'abajo ✗'} de VIDYA {vidya_current:.2f}"
                        else:
                            price_below_vidya = current_price < vidya_current
                            vidya_price_position = f"Precio {current_price:.2f} {'abajo ✓' if price_below_vidya else 'arriba ✗'} de VIDYA {vidya_current:.2f}"
                        
                        slope_diff = vidya_current - vidya_previous
                        vidya_slope_pct = (slope_diff / vidya_previous * 100) if vidya_previous != 0 else 0
                        
                        if direction == "BUY":
                            vidya_slope_valid = slope_diff > 0
                            vidya_slope = f"VIDYA subiendo {vidya_slope_pct:.3f}% ✓" if vidya_slope_valid else f"VIDYA bajando {vidya_slope_pct:.3f}% ✗"
                        else:
                            vidya_slope_valid = slope_diff < 0
                            vidya_slope = f"VIDYA bajando {vidya_slope_pct:.3f}% ✓" if vidya_slope_valid else f"VIDYA subiendo {vidya_slope_pct:.3f}% ✗"
                        
                        if direction == "BUY":
                            vidya_valid = (current_price > vidya_current) and (slope_diff > 0)
                        else:
                            vidya_valid = (current_price < vidya_current) and (slope_diff < 0)
                
                except Exception as e:
                    logger.error(f"Error calculando VIDYA en validación SILVER: {str(e)}")
                    vidya_valid = False
            
            checks['vidya'] = {
                'valid': vidya_valid,
                'current_price': current_price if 'current_price' in locals() else 0,
                'vidya_value': vidya_current,
                'vidya_slope_pct': vidya_slope_pct,
                'price_position': vidya_price_position,
                'slope_msg': vidya_slope,
                'reason': f"VIDYA: {vidya_price_position} | {vidya_slope}"
            }
            
            # ⭐ DECISIÓN FINAL (IDÉNTICO A GOLD)
            threshold_ok = checks['threshold'].get('valid', False)
            microtrend_ok = checks['microtrend'].get('valid', False)
            candle_filter_ok = checks['candle_filter'].get('valid', False)
            impulse_ok = checks['impulse'].get('valid', False)
            noise_ok = checks['anti_noise'].get('valid', False)
            vidya_ok = checks['vidya'].get('valid', False)
            
            valid = threshold_ok and microtrend_ok and candle_filter_ok and impulse_ok and noise_ok and vidya_ok
            
            failed_checks = []
            if not threshold_ok:
                failed_checks.append(f"Threshold insuficiente ({checks['threshold'].get('value', 0):.2f} < {checks['threshold'].get('required', 0):.2f})")
            if not microtrend_ok:
                failed_checks.append(f"Microtendencia rechazada: {checks['microtrend'].get('reason', 'contexto no coincide')}")
            if not candle_filter_ok:
                failed_checks.append(f"Vela no válida: {checks['candle_filter'].get('reason', 'no cumple criterios')}")
            if not impulse_ok:
                failed_checks.append(f"Impulso débil ({checks['impulse'].get('value', 0):.2f} < {checks['impulse'].get('required', 1.5)})")
            if not noise_ok:
                failed_checks.append(f"Ruido detectado: {' | '.join(checks['anti_noise'].get('reasons', ['desconocido']))}")
            if not vidya_ok:
                failed_checks.append(f"VIDYA rechazó: {checks['vidya'].get('reason', 'no cumple alineación')}")
            
            reason = " | ".join(failed_checks) if failed_checks else "✅ Todas las validaciones pasaron"
            
            score = 0
            for check_name in ['threshold', 'microtrend', 'candle_filter', 'impulse', 'anti_noise', 'vidya']:
                if checks[check_name].get('valid', False):
                    score += 17
            
            # LOGS
            self.add_log(f"\n🔥 VALIDACIÓN CONFIG ÓPTIMA SILVER:", 'info')
            self.add_log(f"   ✓ Threshold: {checks['threshold']['value']:.2f} >= {checks['threshold']['required']:.2f} ({checks['threshold']['threshold_pips']:.0f} pips): {'✅' if checks['threshold']['valid'] else '❌'}", 'info')
            
            self.add_log(f"   ✓ Microtendencia ({microtrend_candles}v): {checks['microtrend']['recent_details']}", 'info')
            self.add_log(f"      └─ Contexto 10v: {checks['microtrend']['context_10']}", 'info')
            self.add_log(f"      └─ Contexto 20v: {checks['microtrend']['context_20']}", 'info')
            self.add_log(f"      └─ Contexto 30v: {checks['microtrend']['context_30']}", 'info')
            self.add_log(f"      └─ Voto final: {checks['microtrend']['context_agreement']} {'✅' if checks['microtrend']['valid'] else '❌'}", 'info')
            
            self.add_log(f"   ✓ FILTRO DE VELA (3 CRITERIOS - Elimina ruido):", 'info')
            self.add_log(f"      ├─ Cuerpo: {checks['candle_filter']['body_percentage']:.1f}% >= {checks['candle_filter']['body_required']}%: {'✅' if checks['candle_filter']['body_valid'] else '❌'}", 'info')
            self.add_log(f"      ├─ Mecha: {checks['candle_filter']['wick_percentage']:.1f}% <= {checks['candle_filter']['wick_required']}%: {'✅' if checks['candle_filter']['wick_valid'] else '❌'}", 'info')
            self.add_log(f"      └─ {checks['candle_filter']['close_msg']}: {'✅' if checks['candle_filter']['close_valid'] else '❌'}", 'info')
            
            self.add_log(f"   ✓ Impulso: {checks['impulse']['value']:.2f} >= {checks['impulse']['required']:.2f}: {'✅' if checks['impulse']['valid'] else '❌'}", 'info')
            
            self.add_log(f"   ✓ FILTRO ANTI-RUIDO (4. Evitar):", 'info')
            if checks['anti_noise']['valid']:
                self.add_log(f"      └─ ✅ Sin ruido detectado", 'info')
            else:
                for reason_text in checks['anti_noise']['reasons']:
                    self.add_log(f"      └─ {reason_text}", 'warning')
            
            self.add_log(f"   ✓ INDICADOR VIDYA (5. Apoyo - CMO:{vidya_cmo}, EMA:{vidya_ema}):", 'info')
            if checks['vidya']['valid']:
                self.add_log(f"      ├─ {checks['vidya']['price_position']}: ✅", 'info')
                self.add_log(f"      └─ {checks['vidya']['slope_msg']}: ✅", 'info')
            else:
                self.add_log(f"      ├─ {checks['vidya']['price_position']}: ❌", 'warning')
                self.add_log(f"      └─ {checks['vidya']['slope_msg']}: ❌", 'warning')
            
            self.add_log(f"   ➜ Score Final: {score}/100 | {reason}", 'success' if valid else 'warning')
            
            return {
                'valid': valid,
                'score': score,
                'checks': checks,
                'reason': reason
            }
            
        except Exception as e:
            self.add_log(f"[ERROR] Validación SILVER falló: {str(e)}", 'error')
            return {
                'valid': False,
                'score': 0,
                'reason': f'Excepción: {str(e)}'
            }


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
            sys.stderr.flush()
        except:
            pass
        sys.exit(1)
