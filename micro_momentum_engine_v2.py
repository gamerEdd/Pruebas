#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MICRO MOMENTUM CALIBRATOR V2 - CALIBRACIÓN BASADA EN TICKS Y PIPS
Optimizado para detectar movimientos pequeños: 5-10 pips
Entrada: 5019 no fue detectado como SELL desde 5025 = 6 pips bajista
Solución: Umbral movement_min basado en PIPS, no en %
"""

import threading
from datetime import datetime
import MetaTrader5 as mt5
import numpy as np


class MicroMomentumEngineV2:
    """
    Motor de micro-momentum RECALIBRADO para capturar movimientos de 5-10 pips
    
    Estrategia:
    1. Detectar símbolo y precio actual
    2. Calcular PIPS (no %) - GOLD: 1 pip = 0.1, EUR/USD: 1 pip = 0.0001
    3. Usar PERFILES según tamaño de operación deseada
    4. Ajustar window_ticks, pressure_threshold y movement_min dinámicamente
    """

    def __init__(self, log_callback=None, symbol='GOLD', profile='MICRO'):
        """
        profile: 'ULTRA_MICRO' (5 pips), 'MICRO' (10 pips), 'NORMAL' (20+ pips)
        """
        self.log_callback = log_callback
        self._lock = threading.Lock()
        self.symbol = symbol
        self.profile = profile  # 'ULTRA_MICRO', 'MICRO', 'NORMAL'
        
        # Detectar divisa y pips
        self.pip_value = self._get_pip_value(symbol)
        self.symbol_multiplier = self._get_symbol_multiplier(symbol)
        
        # Estado
        self._last_reverse_direction = None
        self._reverse_streak = 0
        self.tick_history = []  # Histórico de ticks recientes
        self.last_evaluation_time = 0
        
        # Calibración por perfil
        self._apply_profile(profile)
        
        self.log(f"[MICRO] MicroMomentumEngineV2 inicializado", 'success')
        self.log(f"  Symbol: {symbol} (1 pip = {self.pip_value})", 'info')
        self.log(f"  Perfil: {profile}", 'info')
        self.log(f"  Umbrales: window={self.window_ticks}, "
                f"threshold={self.pressure_threshold}, "
                f"movement_min={self.movement_min} pips", 'info')

    def _get_pip_value(self, symbol):
        """Retorna el valor de 1 pip para el símbolo"""
        # GOLD, XAU/USD: 1 pip = 0.1 (4 decimales)
        # EUR/USD, GBP/USD: 1 pip = 0.0001 (4 decimales)
        # Mayoría de pares: 1 pip = 0.0001
        
        if symbol.upper() in ('GOLD', 'XAUUSD', 'XAU/USD', 'XAUUSD'):
            return 0.1  # GOLD
        else:
            return 0.0001  # Forex estándar

    def _get_symbol_multiplier(self, symbol):
        """Retorna el multiplicador para conversión pip→precio"""
        if symbol.upper() in ('GOLD', 'XAUUSD', 'XAU/USD'):
            return 10  # 1 pip GOLD = 10 ticks en MT5 normalmente
        else:
            return 10000  # Forex estándar

    def _apply_profile(self, profile):
        """Aplica calibración según perfil de operación"""
        
        if profile == 'ULTRA_MICRO':
            # Movimientos de 5 pips - velocidad máxima
            self.window_ticks = 15          # 15 ticks = ~0.5-1s (muy rápido)
            self.pressure_threshold = 0.52  # 52% - muy sensible
            self.movement_min = 0.002       # ~2 pips mínimo
            self.ticks_per_second_min = 3.0 # Bajo, permite mercado lento
            self.micro_volatility_min = 0.01  # 1 pip de volatilidad
            self.confirm_ticks = 1          # Confirmar INMEDIATAMENTE
            self.profile_name = "ULTRA_MICRO (5-7 pips)"
            
        elif profile == 'MICRO':
            # Movimientos de 10 pips - balance velocidad-confianza
            self.window_ticks = 20          # 20 ticks = ~1-2s (rápido)
            self.pressure_threshold = 0.55  # 55% presión
            self.movement_min = 0.003       # ~3 pips (permite 5-10 pips de ganancia)
            self.ticks_per_second_min = 4.0 # Moderado
            self.micro_volatility_min = 0.015  # 1.5 pips volatilidad
            self.confirm_ticks = 1          # Confirmar inmediatamente
            self.profile_name = "MICRO (10-15 pips)"
            
        else:  # 'NORMAL'
            # Movimientos normales 20+ pips
            self.window_ticks = 30          # 30 ticks = ~2-3s
            self.pressure_threshold = 0.60  # 60% presión
            self.movement_min = 0.01        # 10 pips mínimo
            self.ticks_per_second_min = 5.0 # Requiere actividad
            self.micro_volatility_min = 0.05  # 5 pips
            self.confirm_ticks = 2          # Dos confirmaciones
            self.profile_name = "NORMAL (20+ pips)"

    def log(self, message, msg_type="info"):
        if self.log_callback:
            try:
                self.log_callback(message, msg_type)
            except Exception:
                pass

    def set_profile(self, profile):
        """Cambiar perfil dinámicamente (útil para ajuste en vivo)"""
        with self._lock:
            old_profile = self.profile
            self._apply_profile(profile)
            self.log(f"[MICRO] Perfil cambiado: {old_profile} → {profile}", 'success')
            self.log(f"  Nuevos umbrales: window={self.window_ticks}, "
                    f"threshold={self.pressure_threshold}, "
                    f"movement_min={self.movement_min:.4f} ({self.movement_min*100:.2f}% = "
                    f"~{self.movement_min/self.pip_value:.1f} pips)", 'info')

    def update_params(self, **kwargs):
        """Actualizar parámetros manualmente"""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    self.log(f"[MICRO] {key} → {value}", 'info')

    def _extract_price(self, tick):
        """Extraer precio del tick"""
        try:
            # Intentar order: last > mid(bid,ask) > bid > ask
            if hasattr(tick, 'last'):
                last = float(tick.last)
                if last > 0:
                    return last
            
            # Fallback a promedio bid/ask
            if hasattr(tick, 'bid') and hasattr(tick, 'ask'):
                bid = float(tick.bid)
                ask = float(tick.ask)
                if bid > 0 and ask > 0:
                    return (bid + ask) / 2.0
                if bid > 0:
                    return bid
                if ask > 0:
                    return ask
            
            # Último recurso: acceso por índice (si es tuple)
            if isinstance(tick, (tuple, list)):
                return float(tick[1])  # bid
            
            return 0.0
        except:
            return 0.0

    def evaluate(self, symbol, predicted_direction):
        """
        NUEVA VERSIÓN: Evaluación micro-calibrada con análisis de TICKS y PIPS
        
        Retorna:
        {
            'decision': 'CONFIRM' | 'INVERT' | 'STRONG_BUY' | 'STRONG_SELL',
            'final_direction': 'BUY' | 'SELL',
            'confidence': 0-100 (% de confianza),
            'pips_moved': número de pips que se movió,
            'tick_analytics': {...}
        }
        """
        base_dir = (predicted_direction or "").upper()
        if base_dir not in ("BUY", "SELL"):
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": "Invalid base direction",
                "confidence": 0,
            }

        # ========== BLOQUE 1: OBTENER TICKS RECIENTES ==========
        
        with self._lock:
            window_ticks = self.window_ticks
            pressure_threshold = self.pressure_threshold
            movement_min = self.movement_min
            tps_min = self.ticks_per_second_min
            vol_min = self.micro_volatility_min
            confirm_ticks = self.confirm_ticks

        try:
            ticks = mt5.copy_ticks_from(
                symbol,
                datetime.now(),
                int(window_ticks * 1.5),  # 1.5x más para seguridad
                mt5.COPY_TICKS_ALL
            )
        except Exception as e:
            self.log(f"[ERROR] No se pudieron obtener ticks: {str(e)[:50]}", 'error')
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": f"Tick error: {str(e)[:30]}",
                "confidence": 0,
            }

        if ticks is None or len(ticks) < max(8, int(window_ticks * 0.5)):
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": f"Insufficient ticks ({len(ticks) if ticks else 0} < {int(window_ticks * 0.5)})",
                "confidence": 10,
                "tick_count": len(ticks) if ticks else 0,
            }

        # ========== BLOQUE 2: ANALIZAR TICKS Y CALCULAR PIPS ==========
        
        prices = []
        times_msc = []
        
        for t in ticks:
            p = self._extract_price(t)
            if p > 0:
                prices.append(p)
                times_msc.append(int(t.time_msc if hasattr(t, 'time_msc') else t[0]))

        if len(prices) < 8:
            return {
                "decision": "CONFIRM",
                "final_direction": base_dir,
                "reason": "Not enough priced ticks",
                "confidence": 15,
                "tick_count": len(prices),
            }

        # ========== BLOQUE 3: CALCULAR PRESIÓN Y MOVIMIENTO EN PIPS ==========
        
        # Contar ticks UP/DOWN
        up_ticks = 0
        down_ticks = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                up_ticks += 1
            elif prices[i] < prices[i - 1]:
                down_ticks += 1

        directional = up_ticks + down_ticks
        if directional > 0:
            buy_pressure = up_ticks / directional
            sell_pressure = down_ticks / directional
        else:
            buy_pressure = sell_pressure = 0.5

        # Movimiento en valor absoluto
        movement_abs = prices[-1] - prices[0]
        
        # Convertir a PIPS (para logging y debugging)
        movement_pips = abs(movement_abs) / self.pip_value
        
        # Volatilidad en PIPS
        micro_volatility = max(prices) - min(prices)
        volatility_pips = micro_volatility / self.pip_value

        # Velocidad de ticks
        dt_seconds = 1.0
        if len(times_msc) >= 2 and times_msc[-1] > times_msc[0]:
            dt_seconds = max(0.001, (times_msc[-1] - times_msc[0]) / 1000.0)
        ticks_per_second = len(prices) / dt_seconds if dt_seconds > 0 else 0

        # ========== BLOQUE 4: DETECTAR DIRECCIÓN DOMINANTE ==========
        
        # Criterios para dirección dominante:
        # 1. Presión suficiente (compra >55% O venta >55%)
        # 2. Movimiento mínimo (threshold_minmo)
        # 3. Volatilidad mínima (para confirmar actividad)
        
        market_active = ticks_per_second >= tps_min and micro_volatility >= vol_min
        
        dominant_direction = "NONE"
        confidence_score = 0
        
        if buy_pressure >= pressure_threshold and movement_abs >= movement_min:
            dominant_direction = "BUY"
            confidence_score = int(buy_pressure * 100)
        elif sell_pressure >= pressure_threshold and (-movement_abs) >= movement_min:
            dominant_direction = "SELL"
            confidence_score = int(sell_pressure * 100)

        # ========== BLOQUE 5: LÓGICA DE INVERSIÓN ==========
        
        # Si hay dirección dominante OPUESTA a base_dir y se confirma
        opposite_strong = (
            market_active and
            dominant_direction in ("BUY", "SELL") and
            dominant_direction != base_dir
        )

        if opposite_strong:
            if self._last_reverse_direction == dominant_direction:
                self._reverse_streak += 1
            else:
                self._last_reverse_direction = dominant_direction
                self._reverse_streak = 1
        else:
            self._last_reverse_direction = None
            self._reverse_streak = 0

        should_invert = opposite_strong and self._reverse_streak >= confirm_ticks
        
        # ========== BLOQUE 6: DETERMINAR DECISIÓN FINAL ==========
        
        # Si confirmación es inmediata (confirm_ticks=1) e invierte, decidir STRONG
        if should_invert:
            if confirm_ticks == 1:
                decision = f"STRONG_{dominant_direction}"
            else:
                decision = "INVERT"
            final_direction = dominant_direction
            final_confidence = confidence_score
        else:
            decision = "CONFIRM"
            final_direction = base_dir
            final_confidence = min(100, int(buy_pressure * 100 if base_dir == "BUY" else sell_pressure * 100))

        # ========== BLOQUE 7: BUILD RESPUESTA DETALLADA ==========
        
        result = {
            "decision": decision,
            "final_direction": final_direction,
            "base_direction": base_dir,
            "dominant_direction": dominant_direction,
            "confidence": final_confidence,
            "tick_analytics": {
                "tick_count": len(prices),
                "up_ticks": up_ticks,
                "down_ticks": down_ticks,
                "buy_pressure": round(buy_pressure, 3),
                "sell_pressure": round(sell_pressure, 3),
                "movement_abs": round(movement_abs, 6),
                "movement_pips": round(movement_pips, 1),
                "volatility": round(micro_volatility, 6),
                "volatility_pips": round(volatility_pips, 1),
                "ticks_per_second": round(ticks_per_second, 1),
                "market_active": market_active,
            },
            "profile": self.profile_name,
            "reason": (
                f"{decision} | dom={dominant_direction} "
                f"press(B/S)={buy_pressure:.2f}/{sell_pressure:.2f} "
                f"mov={movement_pips:.1f}pips vol={volatility_pips:.1f}pips "
                f"tps={ticks_per_second:.1f}t/s conf={final_confidence}%"
            ),
        }

        # ========== LOG DETALLADO PARA DEBUGGING ==========
        
        log_detail = (
            f"[TICK-ANALYSIS] {symbol} | {self.profile_name} | "
            f"Decision={decision} | Dom={dominant_direction} | "
            f"Presor(B/S)=({buy_pressure:.1%}/{sell_pressure:.1%}) | "
            f"Move={movement_pips:.1f}pips (req:{(movement_min/self.pip_value):.1f}) | "
            f"Vol={volatility_pips:.1f}pips (req:{(vol_min/self.pip_value):.1f}) | "
            f"Ticks={len(prices)}({up_ticks}↑/{down_ticks}↓) | TPS={ticks_per_second:.1f} | "
            f"Conf={final_confidence}%"
        )
        
        if decision in ["STRONG_BUY", "STRONG_SELL", "INVERT"]:
            self.log(log_detail, 'success')
        else:
            self.log(log_detail, 'info')

        return result


# ============================================================================
# FUNCIONES DE AYUDA PARA CALIBRACIÓN DINÁMICA
# ============================================================================

def create_calibrated_engine(symbol='GOLD', target_pips=10, log_callback=None):
    """
    Fábrica: Crea engine automáticamente calibrado según pips deseados
    
    target_pips: 5-7 → ULTRA_MICRO, 10-15 → MICRO, 20+ → NORMAL
    """
    if target_pips <= 7:
        profile = 'ULTRA_MICRO'
    elif target_pips <= 15:
        profile = 'MICRO'
    else:
        profile = 'NORMAL'
    
    engine = MicroMomentumEngineV2(
        log_callback=log_callback,
        symbol=symbol,
        profile=profile
    )
    
    if log_callback:
        log_callback(
            f"[CALIBRATION] Engine creado para {symbol} | "
            f"Target: {target_pips}pips → Perfil: {profile}",
            'success'
        )
    
    return engine


def get_pip_size_recommendation(profit_target_dollars=50, account_balance=10000, symbol='GOLD'):
    """
    Recomienda tamaño de pip según objetivo de ganancia y balance
    
    Ejemplo:
    - Balance: $10,000
    - Objetivo por trade: $50
    - GOLD: 1 pip = ~$10 por 0.1 lotes
    → Recomendación: 5 pips × $10 = $50
    """
    # Valores aproximados (varían según broker)
    if symbol.upper() in ('GOLD', 'XAUUSD'):
        dollars_per_pip_per_lot = 100  # GOLD: 1 pip ≈ $100 por 1 lote
    else:
        dollars_per_pip_per_lot = 10   # Forex: 1 pip ≈ $10 por 1 lote

    # Recomendar 0.1 lotes por defecto
    dollars_per_pip = dollars_per_pip_per_lot * 0.1
    
    recommended_pips = max(5, profit_target_dollars // dollars_per_pip)
    
    if recommended_pips <= 7:
        profile = 'ULTRA_MICRO'
    elif recommended_pips <= 15:
        profile = 'MICRO'
    else:
        profile = 'NORMAL'
    
    return {
        'recommended_pips': int(recommended_pips),
        'recommended_profile': profile,
        'expected_profit_per_trade': dollars_per_pip * recommended_pips,
        'risk_per_pip': dollars_per_pip,
    }
