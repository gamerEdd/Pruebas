"""
IndicatorBase - Clase base con funciones de cálculo de indicadores comunes
Evita duplicación entre buy_specialist_ai.py y sell_specialist_ai.py
"""

import numpy as np
from abc import ABC


class IndicatorBase(ABC):
    """Clase base con funciones de indicadores técnicos comunes"""
    
    def __init__(self, timeframe='M1'):
        """
        Inicializa la base con timeframe especificado
        
        timeframe: 'M1', 'M5', 'M15', 'M30', 'H1', 'D1' (default: M1)
        """
        self.timeframe = timeframe
        self.periods = self._get_periods_for_timeframe(timeframe)
    
    def _get_periods_for_timeframe(self, timeframe):
        """
        Retorna períodos óptimos DINÁMICAMENTE según timeframe.
        
        ⭐ P3 FIX: Periodos fijos ignoraban contexto de timeframe
        Problema: RSI(14) en M1 = mala (14 min historia), ok en H1 (14 horas)
        Solución: Ajustar períodos dinámicamente
        """
        periods = {
            'M1': {
                'rsi': 7,           # ⭐ CAMBIADO: 14→7 (M1 necesita memoria más corta)
                'stochastic': 7,    # ⭐ CAMBIADO: 14→7
                'cci': 12,          # ⭐ CAMBIADO: 20→12
                'williams_r': 7,    # ⭐ CAMBIADO: 14→7
                'adx': 14,          # ADX puede mantener 14 incluso en M1
                'bollinger': 20,    # Bollinger más largo = ok (volatilidad)
                'atr': 14,          # ⭐ CAMBIADO: 100→14 (100 min es demasiado)
                'ema_fast': 12,
                'ema_slow': 26,
            },
            'M5': {
                'rsi': 9,
                'stochastic': 9,
                'cci': 14,
                'williams_r': 9,
                'adx': 14,
                'bollinger': 20,
                'atr': 14,
                'ema_fast': 12,
                'ema_slow': 26,
            },
            'M15': {
                'rsi': 10,
                'stochastic': 10,
                'cci': 15,
                'williams_r': 10,
                'adx': 14,
                'bollinger': 20,
                'atr': 14,
                'ema_fast': 12,
                'ema_slow': 26,
            },
            'M30': {
                'rsi': 12,
                'stochastic': 12,
                'cci': 18,
                'williams_r': 12,
                'adx': 14,
                'bollinger': 20,
                'atr': 14,
                'ema_fast': 12,
                'ema_slow': 26,
            },
            'H1': {
                'rsi': 14,
                'stochastic': 14,
                'cci': 20,
                'williams_r': 14,
                'adx': 14,
                'bollinger': 20,
                'atr': 14,
                'ema_fast': 12,
                'ema_slow': 26,
            },
            'D1': {
                'rsi': 14,
                'stochastic': 14,
                'cci': 20,
                'williams_r': 14,
                'adx': 14,
                'bollinger': 20,
                'atr': 20,
                'ema_fast': 12,
                'ema_slow': 26,
            }
        }
        
        return periods.get(timeframe, periods['M1'])  # Default a M1 si no existe
    
    
    def _ema(self, data, period):
        """Calcula EMA - RETORNA ESCALAR SIEMPRE"""
        try:
            if len(data) == 0:
                return 0.0
            
            # Convertir a array si no lo es
            data_array = np.asarray(data, dtype=np.float64)
            
            multiplier = 2.0 / float(period + 1)
            ema = float(data_array[0])
            
            for i in range(1, len(data_array)):
                price = float(data_array[i])
                ema = (price * multiplier) + (ema * (1.0 - multiplier))
            
            return float(ema)
        except Exception:
            return 0.0

    def _calculate_bollinger_position(self, prices, period=20):
        """Posición relativa en Bandas de Bollinger"""
        try:
            prices_array = np.asarray(prices[-period:], dtype=np.float64)
            
            if len(prices_array) < period:
                return 0.0
            
            sma = float(np.mean(prices_array))
            std = float(np.std(prices_array))
            
            if std == 0:
                return 0.0
            
            upper = sma + (std * 2.0)
            lower = sma - (std * 2.0)
            current = float(prices_array[-1])
            
            if current <= lower:
                return -1.0
            elif current >= upper:
                return 1.0
            else:
                result = float((current - sma) / std)
                return result if not np.isnan(result) else 0.0
        except Exception:
            return 0.0

    def _calculate_stochastic(self, high, low, close, period=None):
        """Calcula el Stochastic Oscillator (0-100) con período dinámico"""
        try:
            if period is None:
                period = self.periods.get('stochastic', 14)
            
            high_array = np.asarray(high[-period:], dtype=np.float64)
            low_array = np.asarray(low[-period:], dtype=np.float64)
            close_val = float(close[-1])
            
            lowest_low = float(np.min(low_array))
            highest_high = float(np.max(high_array))
            
            if highest_high == lowest_low:
                return 50.0
            
            k = ((close_val - lowest_low) / (highest_high - lowest_low)) * 100.0
            return float(np.clip(k, 0, 100))
        except Exception:
            return 50.0

    def _calculate_cci(self, high, low, close, period=None):
        """Calcula Commodity Channel Index con período dinámico"""
        try:
            if period is None:
                period = self.periods.get('cci', 20)
            
            typical_price = (np.asarray(high[-period:], dtype=np.float64) + 
                           np.asarray(low[-period:], dtype=np.float64) + 
                           np.asarray(close[-period:], dtype=np.float64)) / 3.0
            
            sma_tp = float(np.mean(typical_price))
            mad = float(np.mean(np.abs(typical_price - sma_tp)))
            
            if mad == 0:
                return 0.0
            
            cci = (float(typical_price[-1]) - sma_tp) / (0.015 * mad)
            return float(cci) if not np.isnan(cci) else 0.0
        except Exception:
            return 0.0

    def _calculate_williams_r(self, high, low, close, period=None):
        """Calcula Williams %R (-100 a 0) con período dinámico"""
        try:
            if period is None:
                period = self.periods.get('williams_r', 14)
            
            high_array = np.asarray(high[-period:], dtype=np.float64)
            low_array = np.asarray(low[-period:], dtype=np.float64)
            
            highest_high = float(np.max(high_array))
            lowest_low = float(np.min(low_array))
            close_val = float(close[-1])
            
            if highest_high == lowest_low:
                return -50.0
            
            williams_r = ((highest_high - close_val) / (highest_high - lowest_low)) * -100.0
            return float(williams_r)
        except Exception:
            return -50.0

    def _calculate_adx(self, high, low, close, period=None):
        """Calcula Average Directional Index (0-100) con período dinámico"""
        if period is None:
            period = self.periods.get('adx', 14)
        try:
            high_array = np.asarray(high, dtype=np.float64)
            low_array = np.asarray(low, dtype=np.float64)
            close_array = np.asarray(close, dtype=np.float64)
            
            if len(high_array) < period + 1:
                return 0.0
            
            plus_dm = np.zeros(len(high_array) - 1)
            minus_dm = np.zeros(len(high_array) - 1)
            tr = np.zeros(len(high_array) - 1)
            
            for i in range(len(high_array) - 1):
                h_diff = float(high_array[i+1]) - float(high_array[i])
                l_diff = float(low_array[i]) - float(low_array[i+1])
                
                if h_diff > 0 and h_diff > l_diff:
                    plus_dm[i] = h_diff
                if l_diff > 0 and l_diff > h_diff:
                    minus_dm[i] = l_diff
                
                tr1 = float(high_array[i+1]) - float(low_array[i+1])
                tr2 = abs(float(high_array[i+1]) - float(close_array[i]))
                tr3 = abs(float(low_array[i+1]) - float(close_array[i]))
                tr[i] = max(tr1, tr2, tr3)
            
            atr = float(np.mean(tr[-period:])) if len(tr) >= period else float(np.mean(tr))
            
            if atr <= 0:
                return 0.0
            
            plus_di = 100.0 * float(np.mean(plus_dm[-period:])) / atr if len(plus_dm) >= period else 0.0
            minus_di = 100.0 * float(np.mean(minus_dm[-period:])) / atr if len(minus_dm) >= period else 0.0
            
            di_diff = abs(plus_di - minus_di)
            di_sum = plus_di + minus_di
            
            if di_sum <= 0:
                return 0.0
            
            adx = 100.0 * di_diff / di_sum
            return float(np.clip(adx, 0, 100))
        except Exception:
            return 0.0

    def _calculate_rsi(self, prices, period=None):
        """
        Calcula RSI correctamente con período dinámico
        
        period: Si es None, usa self.periods['rsi'] (dinámico)
        """
        try:
            if period is None:
                period = self.periods.get('rsi', 14)
            
            prices_array = np.asarray(prices, dtype=np.float64)
            deltas = np.diff(prices_array)
            
            if len(deltas) < period:
                return 50.0
            
            seed = deltas[:period+1]
            up = float(np.sum(seed[seed >= 0])) / float(period)
            down = -float(np.sum(seed[seed < 0])) / float(period)
            
            rs = up / down if down != 0 else 1.0
            rsi = 100.0 - (100.0 / (1.0 + rs))
            
            return float(rsi) if not np.isnan(rsi) else 50.0
        except Exception:
            return 50.0

    def _find_support(self, lows, current_price):
        """Encuentra el nivel de soporte más cercano"""
        try:
            recent_lows = lows[-50:]
            support = float(np.min(recent_lows))
            distance = ((float(current_price) - support) / float(current_price)) * 100 if current_price > 0 else 0.0
            return float(distance)
        except Exception:
            return 0.0

    def _calculate_momentum(self, prices, period=10):
        """Calcula momentum"""
        try:
            return float(((prices[-1] - prices[-period]) / prices[-period]) * 100)
        except Exception:
            return 0.0

    def _calculate_volume_trend(self, volume, period=14):
        """Calcula tendencia de volumen"""
        try:
            mean_vol = float(np.mean(volume[-period:]))
            if mean_vol <= 0:
                return 0.0
            return float(((volume[-1] / mean_vol) - 1) * 100)
        except Exception:
            return 0.0

    def _calculate_trend_strength(self, prices, direction, period=20):
        """Calcula fuerza de tendencia en dirección específica"""
        try:
            ma_short = float(np.mean(prices[-10:]))
            ma_long = float(np.mean(prices[-period:]))
            
            if direction == 'bullish':
                return float(max(0, ((ma_short - ma_long) / ma_long) * 100))
            else:
                return float(max(0, ((ma_long - ma_short) / ma_long) * 100))
        except Exception:
            return 0.0
    
    def _find_resistance(self, highs, current_price):
        """
        Encuentra el nivel de resistencia más cercano (opuesto a soporte).
        Retorna la distancia porcentual desde el precio actual hasta la resistencia.
        """
        try:
            recent_highs = highs[-50:]
            resistance = float(np.max(recent_highs))
            distance = ((resistance - float(current_price)) / float(current_price)) * 100 if current_price > 0 else 0.0
            return float(distance)
        except Exception:
            return 0.0
    
    def _apply_trend_detector_penalty(self, symbol='GOLD'):
        """
        ⭐ P0 PHASE: Penalización por TrendDetector
        
        Si trend_detector está disponible y detecta cambio de tendencia,
        aplica penalización al score (multiplicador < 1.0).
        
        Returns:
            float: Multiplicador (1.0 = sin penalización, 0.55 = 45% penalización)
        """
        try:
            # Si no hay trend_detector inyectado, retornar sin penalización
            if not hasattr(self, 'trend_detector') or self.trend_detector is None:
                return 1.0
            
            # Analizar riesgo de cambio de tendencia
            analysis = self.trend_detector.analyze_trend_change_risk(symbol, timeframe=1, lookback=50)
            
            if not analysis:
                return 1.0
            
            risk_level = analysis.get('risk_level', 'LOW')
            confidence = analysis.get('confidence', 0)
            
            # Mapear risk_level a multiplicador
            if risk_level == 'HIGH':
                # Alto riesgo de cambio = penalización fuerte (45% descuento)
                penalty = 0.55
            elif risk_level == 'MEDIUM':
                # Riesgo medio = penalización moderada (25% descuento)
                penalty = 0.75
            else:  # LOW
                # Bajo riesgo = sin penalización
                penalty = 1.0
            
            # Ajustar por confianza (si confianza es baja, mitigar penalización)
            if confidence < 50:
                penalty = 1.0 - ((1.0 - penalty) * 0.5)  # Reduce penalización a la mitad
            
            return float(penalty)
        
        except Exception as e:
            # En caso de error, retornar sin penalización
            return 1.0
    
    # ⭐ NUEVO (P3 Phase - Historicidad de Señales)
    def _calculate_signal_freshness(self, history, condition_func, max_lookback=None):
        """
        Calcula cuántos candles lleva un indicador en una condición específica.
        
        ⭐ P3 FIX: Historicidad de Señales
        Problema: RSI=30 para 10 candles = señal débil, pero RSI acaba de cruzar 30 = señal fuerte
        No se contaba cuántos_candles_en_condición → No se validaba "novedad" de la señal
        
        Args:
            history: list de valores históricos (más reciente al FINAL) [precio_1, precio_2, ..., precio_actual]
            condition_func: función que retorna bool si se cumple la condición
                           Ej: lambda rsi: rsi < 30
            max_lookback: máximo número de candles a revisar (default: len(history))
        
        Returns:
            dict {
                'candles_in_condition': número de candles consecutivos en condición (desde el más reciente),
                'freshness_score': 0-100 (100 = acaba de entrar, 0 = lleva mucho tiempo),
                'is_fresh': bool (True si entró en últimos 2 candles),
                'is_stale': bool (True si lleva >5 candles en condición)
            }
        """
        try:
            if not history or len(history) == 0:
                return {
                    'candles_in_condition': 0,
                    'freshness_score': 0,
                    'is_fresh': False,
                    'is_stale': False
                }
            
            if max_lookback is None:
                max_lookback = len(history)
            
            # Contar cuántos candles consecutivos (más recientes) cumplen condición
            candles_in_condition = 0
            recent_history = history[-max_lookback:]  # Tomar últimos max_lookback
            
            # Iterar desde el MÁS RECIENTE hacia atrás
            for i in range(len(recent_history) - 1, -1, -1):
                try:
                    if condition_func(recent_history[i]):
                        candles_in_condition += 1
                    else:
                        break  # Romper al encontrar primer valor que NO cumple
                except:
                    break
            
            # Calcular score de "frescura" (100 = acaba de entrar, 0 = muy viejo)
            # Máximo 10 candles = parámetro de antigüedad
            if candles_in_condition == 0:
                freshness_score = 0
                is_fresh = False
                is_stale = False
            elif candles_in_condition == 1:
                freshness_score = 100  # Acaba de entrar
                is_fresh = True
                is_stale = False
            elif candles_in_condition == 2:
                freshness_score = 90   # Muy fresco aún (2do candle)
                is_fresh = True
                is_stale = False
            elif candles_in_condition <= 5:
                freshness_score = max(20, 100 - (candles_in_condition * 15))
                is_fresh = False
                is_stale = False
            else:
                freshness_score = 0
                is_fresh = False
                is_stale = True
            
            return {
                'candles_in_condition': int(candles_in_condition),
                'freshness_score': int(freshness_score),
                'is_fresh': is_fresh,
                'is_stale': is_stale
            }
        except Exception as e:
            return {
                'candles_in_condition': 0,
                'freshness_score': 0,
                'is_fresh': False,
                'is_stale': False
            }
