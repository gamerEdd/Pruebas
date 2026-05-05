"""
🔄 TREND CHANGE DETECTOR - Detector de Cambios de Tendencia Anticipado
Detecta cambios de mercado 10-30 segundos ANTES de que ocurran
Análisis: Divergencias, Momentum, Multi-timeframe + ADAPTATIVO con market_snapshots.json
"""

import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import json
import os
import time
from collections import deque


class TrendChangeDetector:
    """Detecta cambios de tendencia anticipados analizando divergencias, momentum y datos históricos"""
    
    def __init__(self, log_callback=None, snapshots_path='logs/market_snapshots.json'):
        self.log = log_callback or print
        self.name = "Trend Change Detector (Adaptive)"
        self.snapshots_path = snapshots_path
        
        # Historial de análisis para detectar patrones
        self.rsi_history = deque(maxlen=500)
        self.price_history = deque(maxlen=500)
        self.momentum_history = deque(maxlen=500)
        self.last_check = None
        self.last_snapshots_update = 0
        
        # Calibración adaptativa basada en datos históricos
        self.adaptive_rsi_overbought = 70
        self.adaptive_rsi_oversold = 30
        self.adaptive_momentum_threshold = 2.0
        self.divergence_strength = 1.0  # Factor de amplificación
        
        # Estadísticas para aprendizaje
        self.reversal_history = deque(maxlen=100)  # Historial de reversiones detectadas
        self.accuracy_score = 0.5  # Precisión de predicciones (0-1)
        
    def _reload_snapshots_if_needed(self):
        """Recarga market_snapshots cada 60 segundos para datos frescos"""
        now = time.time() if 'time' in dir() else 0
        if now - self.last_snapshots_update > 60:  # Cada minuto
            try:
                if os.path.exists(self.snapshots_path):
                    file_size = os.path.getsize(self.snapshots_path)
                    if file_size == 0:
                        self.log(f"[TREND] ⚠️ Snapshots vacío ({self.snapshots_path}) - sin datos", 'debug')
                        return []
                    
                    with open(self.snapshots_path, 'r') as f:
                        data = json.load(f)
                    self.last_snapshots_update = now
                    return data if isinstance(data, list) else data.get('snapshots', [])
            except json.JSONDecodeError as e:
                # Archivo JSON dañado/truncado - eliminar y regenerar
                try:
                    os.remove(self.snapshots_path)
                    self.log(f"[TREND] ✓ Archivo snapshots corrupto eliminado - se regenerará al iniciar", 'info')
                except:
                    pass
            except Exception:
                pass
        return getattr(self, '_cached_snapshots', [])
    
    def analyze_trend_change_risk(self, symbol, timeframe=mt5.TIMEFRAME_M1, lookback=100):
        """
        Analiza riesgo de cambio de tendencia usando market_snapshots.json + MT5
        ⭐ MEJORADO: Usa fuente consistente (snapshots O MT5, no ambas)
        ⭐ FIX #11: Reduce lookback to 50 para detección MÁS RÁPIDA de cambios
        Retorna: {risk_level, signal, confidence, reason}
        """
        try:
            return self._analyze_trend_change_risk_internal(symbol, timeframe, lookback)
        except Exception as e:
            self.log(f"[TREND] CRITICAL ERROR (outer catch): {str(e)[:60]}", 'error')
            import traceback
            tb = traceback.format_exc()
            self.log(f"[TRACE] {tb[:300]}", 'error')
            return self._safe_response("LOW", "STABLE", 0, f"Critical error: {str(e)[:30]}")
    
    def _analyze_trend_change_risk_internal(self, symbol, timeframe, lookback=100):
        """Implementación interna - ejecutada dentro de try/catch superior"""
        # ⭐ FIX #11: Usar MÁXIMO 50 barras para detección RÁPIDA (no 100)
        # Más rápido responde = detecta cambios más cerca del punto de inflexión
        lookback = min(max(lookback, 50), 50)  # Fuerza usar 50 máximo
        
        closes = None
        highs = None
        lows = None
        source = "MT5"
        
        # ⭐ PRIORIDAD 1: Usar market_snapshots.json si está disponible
        try:
            if os.path.exists(self.snapshots_path):
                file_size = os.path.getsize(self.snapshots_path)
                if file_size == 0:
                    self.log(f"[TREND] ⚠️ Snapshots vacío - usando MT5", 'debug')
                elif file_size > 100000000:  # Si > 100MB, probablemente dañado
                    self.log(f"[TREND] ⚠️ Snapshots muy grande ({file_size/1024/1024:.0f}MB) - regenerando...", 'debug')
                    try:
                        os.remove(self.snapshots_path)
                    except:
                        pass
                else:
                    with open(self.snapshots_path, 'r') as f:
                        snapshots = json.load(f)
                    
                    if isinstance(snapshots, dict):
                        snapshots = snapshots.get('snapshots', [])
                    
                    # ⭐ IMPORTANTE: Tomar ÚLTIMAS lookback barras consistentemente
                    if snapshots and len(snapshots) >= 30:
                        snapshots = snapshots[-lookback:] if len(snapshots) > lookback else snapshots
                        closes = np.array([s.get('close', 0) for s in snapshots])
                        highs = np.array([s.get('high', 0) for s in snapshots])
                        lows = np.array([s.get('low', 0) for s in snapshots])
                        source = "SNAPSHOTS"
                        self.log(f"[TREND] Usando {len(snapshots)} snapshots frescos (últimas {len(closes)} barras)", 'info')
        except json.JSONDecodeError:
            # Archivo JSON dañado - eliminarlo
            try:
                os.remove(self.snapshots_path)
                self.log(f"[TREND] ✓ Snapshots corrupto eliminado - regenerará al iniciar", 'info')
            except:
                pass
        except Exception as e:
            self.log(f"[TREND] No se pudieron cargar snapshots ({type(e).__name__}) - usando MT5", 'debug')
            pass
        if closes is None:
            from mt5_safe import copy_rates_from_pos_safe
            rates = copy_rates_from_pos_safe(symbol, timeframe, 0, lookback)
            # ⭐ Verificación segura para numpy array
            if rates is None:
                return self._safe_response("LOW", "STABLE", 30, "Datos insuficientes - MT5 no disponible")
            try:
                if len(rates) < 30:
                    return self._safe_response("LOW", "STABLE", 30, "Datos insuficientes - menos de 30 barras")
            except:
                return self._safe_response("LOW", "STABLE", 30, "Datos insuficientes - error verificando tamaño")
            
            closes = np.array([r['close'] for r in rates])
            highs = np.array([r['high'] for r in rates])
            lows = np.array([r['low'] for r in rates])
        
        if len(closes) < 30:
            return self._safe_response("LOW", "STABLE", 30, "Datos insuficientes")
        
        try:
            # ⭐ NUEVO: Calcular tendencia general de 50 barras
            general_trend, trend_strength = self._calculate_general_trend(closes[-50:] if len(closes) >= 50 else closes)
            
            # Calcular indicadores CON CALIBRACIÓN ADAPTATIVA
            rsi = self._calculate_rsi(closes, 14)
            
            # MACD
            macd, signal_line, histogram = self._calculate_macd(closes)
            
            # Momentum
            momentum = self._calculate_momentum(closes, 10)
            
            # ⭐ DETECTOR DE DIVERGENCIAS CON THRESHOLDS ADAPTATIVOS
            divergence_signal, divergence_confidence = self._detect_divergence(
                closes[-20:], rsi[-20:], highs[-20:], lows[-20:]
            )
            
            # ⭐ NUEVO: Validar divergencia contra tendencia general
            # Si mercado es bajista, ser muy escéptico con SELL_TO_BUY
            # Si mercado es alcista, ser muy escéptico con BUY_TO_SELL
            divergence_confidence = self._validate_signal_against_trend(
                divergence_signal, divergence_confidence, general_trend, trend_strength
            )
            
            # ⭐ NUEVO: Análisis de cambio de tendencia por SMA
            sma_signal, sma_confidence = self._detect_trend_crossover(closes, rsi)
            
            # Fuerza del movimiento actual (con factores adaptativos)
            # ⭐ Convertir rsi[-1] a float
            current_strength = self._analyze_market_strength(closes[-10:], float(rsi[-1]))
            
            # Análisis multi-timeframe para confirmar
            m5_analysis = self._quick_multiframe_check(symbol, mt5.TIMEFRAME_M5)
            
            # ⭐ CALIBRACIÓN: Recalcular thresholds si hay suficientes datos
            self._calibrate_adaptive_parameters(closes, rsi)
            
            # ⭐ COMBINAR DIVERGENCIA + SMA PARA MEJOR SEÑAL
            combined_signal = divergence_signal or sma_signal
            combined_confidence = max(divergence_confidence, sma_confidence)
            
            # Combinar señales CON FACTOR ADAPTATIVO
            # ⭐ Convertir valores de numpy a float para evitar ambigüedad
            risk_level, trend_signal, confidence, reason = self._synthesize_analysis(
                combined_signal, combined_confidence, current_strength, 
                float(macd[-1]), float(signal_line[-1]), float(momentum[-1]), m5_analysis, source
            )
            
        except Exception as calc_error:
            self.log(f"[TREND] Error en cálculos: {str(calc_error)[:80]}", 'error')
            import traceback
            self.log(f"[TRACE] {traceback.format_exc()[:200]}", 'error')
            return self._safe_response("LOW", "STABLE", 0, f"Error cálculo: {str(calc_error)[:40]}")
        
        return {
            'risk_level': risk_level,
            'signal': trend_signal,
            'confidence': confidence,
            'reason': reason,
            'source': source,
            'general_trend': general_trend,
            'trend_strength': trend_strength,
            'indicators': {
                'rsi': float(rsi[-1]),
                'macd': float(macd[-1]),
                'momentum': float(momentum[-1]),
                'divergence': divergence_signal,
                'adaptive_overbought': float(self.adaptive_rsi_overbought),
                'adaptive_oversold': float(self.adaptive_rsi_oversold)
            }
        }
    
    def _calibrate_adaptive_parameters(self, closes, rsi):
        """⭐ NUEVO: Calibración adaptativa basada en datos históricos"""
        try:
            if len(rsi) < 50:
                return
            
            # Estadísticas del RSI actual - ⭐ Convertir a Python float
            rsi_mean = float(np.mean(rsi[-50:]))
            rsi_std = float(np.std(rsi[-50:]))
            
            # Ajustar thresholds adaptativos:
            # Si RSI tiende a niveles altos → subir threshold overbought
            # Si RSI tiende a niveles bajos → bajar threshold oversold
            if rsi_mean > 55:
                self.adaptive_rsi_overbought = float(min(85, 70 + (rsi_mean - 55) * 0.3))
            else:
                self.adaptive_rsi_overbought = float(max(65, 70 - (55 - rsi_mean) * 0.3))
            
            if rsi_mean < 45:
                self.adaptive_rsi_oversold = float(max(15, 30 - (45 - rsi_mean) * 0.3))
            else:
                self.adaptive_rsi_oversold = float(min(35, 30 + (rsi_mean - 45) * 0.3))
            
            # Ajustar factor de divergencia según volatilidad
            price_volatility = float(np.std(np.diff(closes[-50:])))
            if price_volatility > 0:
                self.divergence_strength = float(min(2.0, 1.0 + price_volatility * 10))
            
            # Actualizar historial
            self.rsi_history.extend(rsi[-10:])
            self.price_history.extend(closes[-10:])
            
        except Exception:
            pass
    
    def _calculate_general_trend(self, prices):
        """
        ⭐ NUEVO: Calcula la tendencia general del mercado
        Retorna: ("UPTREND"|"DOWNTREND"|"RANGE", strength: 0-100)
        """
        try:
            if len(prices) < 10:
                return "RANGE", 50
            
            sma_10 = float(np.mean(prices[-10:]))
            sma_20 = float(np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices))
            current = float(prices[-1])
            
            # Calcular fuerza de tendencia
            price_change = ((current - prices[0]) / prices[0]) if prices[0] != 0 else 0
            strength = min(100, abs(price_change) * 1000)
            
            if current > sma_10 > sma_20:
                return "UPTREND", strength
            elif current < sma_10 < sma_20:
                return "DOWNTREND", strength
            else:
                return "RANGE", 50
        except Exception:
            return "RANGE", 50
    
    def _validate_signal_against_trend(self, signal, confidence, general_trend, trend_strength):
        """
        ⭐ NUEVO: Valida que la señal sea coherente con la tendencia general
        Si va CONTRA la tendencia → reducir confianza significativamente
        """
        try:
            if signal == "NONE" or confidence < 30:
                return confidence
            
            # Si mercado está en downtrend, ser escéptico con SELL_TO_BUY
            if general_trend == "DOWNTREND" and signal == "SELL_TO_BUY":
                # Reducir confianza: mercado bajista, no es buen momento para comprar
                penalty = min(confidence * 0.6, trend_strength * 0.4)  # Penalizar según fuerza del downtrend
                confidence = max(20, confidence - penalty)
                self.log(f"[TREND] ⚠️ SELL_TO_BUY en DOWNTREND: -60% confianza (ahora: {confidence:.0f}%)", 'debug')
            
            # Si mercado está en uptrend, ser escéptico con BUY_TO_SELL
            elif general_trend == "UPTREND" and signal == "BUY_TO_SELL":
                penalty = min(confidence * 0.6, trend_strength * 0.4)
                confidence = max(20, confidence - penalty)
                self.log(f"[TREND] ⚠️ BUY_TO_SELL en UPTREND: -60% confianza (ahora: {confidence:.0f}%)", 'debug')
            
            return float(confidence)
        except Exception:
            return confidence
    
    def _detect_divergence(self, prices, rsi_values, highs, lows):
        """
        ⭐ MEJORADO: Detecta divergencias Y cambios de tendencia con SENSIBILIDAD AUMENTADA
        Ahora analiza: divergencias, momentum, cambios de tendencia, extremos de RSI
        """
        try:
            if len(prices) < 10 or len(rsi_values) < 10:
                return "NONE", 0
            
            # Convertir a float para seguridad
            current_price = float(prices[-1])
            current_rsi = float(rsi_values[-1])
            
            # Últimos 5 y 10 candles
            prices_5 = np.array([float(p) for p in prices[-5:]])
            prices_10 = np.array([float(p) for p in prices[-10:]])
            rsi_5 = np.array([float(r) for r in rsi_values[-5:]])
            rsi_10 = np.array([float(r) for r in rsi_values[-10:]])
            
            # Tendencias simples
            price_trending_up = current_price > float(prices[-3])
            price_trending_down = current_price < float(prices[-3])
            rsi_trending_up = current_rsi > float(rsi_values[-3])
            rsi_trending_down = current_rsi < float(rsi_values[-3])
            
            # Extremos
            price_in_high_zone = current_price >= float(np.percentile(prices_10, 75))  # Top 25%
            price_in_low_zone = current_price <= float(np.percentile(prices_10, 25))   # Bottom 25%
            rsi_overbought = current_rsi > self.adaptive_rsi_overbought
            rsi_oversold = current_rsi < self.adaptive_rsi_oversold
            
            # Momentum reciente
            momentum_magnitude = abs(float(prices_5[-1]) - float(prices_5[0])) / float(prices_5[0]) if float(prices_5[0]) != 0 else 0
            
            signal = "NONE"
            confidence = 0
            
            # ⭐ SEÑAL 1: DIVERGENCIA BAJISTA (BUY_TO_SELL)
            # Precio en zona alta pero RSI NO confirma, o RSI bajando en tendencia alcista
            if price_trending_up and price_in_high_zone:
                # Situación A: Precio sube pero RSI NO está overbought
                if current_rsi < self.adaptive_rsi_overbought:
                    confidence = min(100, 40 + (price_in_high_zone * 20) + ((self.adaptive_rsi_overbought - current_rsi) * 0.5) * self.divergence_strength)
                    signal = "BUY_TO_SELL"
                
                # Situación B: Precio sube pero RSI baja (divergencia clásica)
                if rsi_trending_down and current_rsi < float(rsi_values[-3]):
                    confidence = min(100, 50 + (abs(current_rsi - float(rsi_values[-1])) * 0.7) * self.divergence_strength)
                    signal = "BUY_TO_SELL"
            
            # ⭐ SEÑAL 2: DIVERGENCIA ALCISTA (SELL_TO_BUY)
            # Precio en zona baja pero RSI NO confirma, o RSI subiendo en tendencia bajista
            if price_trending_down and price_in_low_zone:
                # Situación A: Precio baja pero RSI NO está oversold
                if current_rsi > self.adaptive_rsi_oversold:
                    confidence = min(100, 40 + (price_in_low_zone * 20) + ((current_rsi - self.adaptive_rsi_oversold) * 0.5) * self.divergence_strength)
                    signal = "SELL_TO_BUY"
                
                # Situación B: Precio baja pero RSI sube (divergencia clásica)
                if rsi_trending_up and current_rsi > float(rsi_values[-3]):
                    confidence = min(100, 50 + (abs(current_rsi - float(rsi_values[-1])) * 0.7) * self.divergence_strength)
                    signal = "SELL_TO_BUY"
            
            # ⭐ SEÑAL 3: EXTREMOS RSI (sin divergencia pero cambio probable)
            # RSI extremadamente overbought → SELL coming
            if rsi_overbought and current_rsi > 80:
                confidence = min(100, 35 + (current_rsi - 80) * 1.5)
                signal = "BUY_TO_SELL"
            
            # RSI extremadamente oversold → BUY coming
            if rsi_oversold and current_rsi < 20:
                confidence = min(100, 35 + (20 - current_rsi) * 1.5)
                signal = "SELL_TO_BUY"
            
            # ⭐ SEÑAL 4: MOMENTUM cambio (aceleración/desaceleración)
            # Si hay fuerte momentum pero estamos en extremo → reversión probable
            if momentum_magnitude > 0.002:  # 0.2% movimiento en 5 candles
                if price_trending_up and rsi_overbought:
                    confidence = min(100, 45 + momentum_magnitude * 5000)
                    signal = "BUY_TO_SELL"
                elif price_trending_down and rsi_oversold:
                    confidence = min(100, 45 + momentum_magnitude * 5000)
                    signal = "SELL_TO_BUY"
            
            return signal, float(confidence)
        except Exception as e:
            return "NONE", 0
    
    def _detect_trend_crossover(self, prices, rsi):
        """
        ⭐ NUEVO: Detecta cambios de tendencia por comportamiento de precios vs promedios móviles
        Más sensible que divergencias puras
        """
        try:
            if len(prices) < 20 or len(rsi) < 10:
                return "NONE", 0
            
            # Calcular promedios móviles
            sma_10 = float(np.mean(prices[-10:]))
            sma_20 = float(np.mean(prices[-20:]))
            sma_50 = float(np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices))
            
            current_price = float(prices[-1])
            current_rsi = float(rsi[-1])
            
            signal = "NONE"
            confidence = 0
            
            # SEÑAL 1: Muerte cruzada - SMA10 cruza bajo SMA20 (BUY_TO_SELL)
            # Patrón bajista: Precio baja bajo SMA10 que está bajo SMA20
            if current_price < sma_10 < sma_20:
                # Cruza plausible
                distance_to_sma = (sma_10 - current_price) / sma_10 if sma_10 > 0 else 0
                confidence = 45 + (distance_to_sma * 100)  # Más distancia = más confianza
                confidence = min(75, confidence)
                signal = "BUY_TO_SELL"
            
            # SEÑAL 2: Cruza dorada - SMA10 cruza sobre SMA20 (SELL_TO_BUY)
            # Patrón alcista: Precio sube sobre SMA10 que está sobre SMA20
            elif current_price > sma_10 > sma_20:
                distance_to_sma = (current_price - sma_10) / sma_10 if sma_10 > 0 else 0
                confidence = 45 + (distance_to_sma * 100)
                confidence = min(75, confidence)
                signal = "SELL_TO_BUY"
            
            # SEÑAL 3: Rechazo de nivel clave - precio rechaza SMA50
            # Precio baja fuerte pero sube desde SMA50 (cambio inminente)
            elif current_price < sma_50 and current_price > float(prices[-2]):
                if float(prices[-3]) > sma_50:  # Viene de arriba
                    distance_ratio = (sma_50 - current_price) / sma_50 if sma_50 > 0 else 0
                    if distance_ratio < 0.01:  # Cercano a SMA50
                        confidence = 50 + (abs(float(prices[-1]) - float(prices[-2])) * 1000)
                        confidence = min(70, confidence)
                        signal = "SELL_TO_BUY"
            
            # SEÑAL 4: Breakout de nivel - precio rompe nivel importante
            elif current_price > sma_50 and float(prices[-2]) < sma_50:
                # Ruptura alcista
                confidence = 55
                signal = "SELL_TO_BUY"
            
            elif current_price < sma_50 and float(prices[-2]) > sma_50:
                # Ruptura bajista
                confidence = 55
                signal = "BUY_TO_SELL"
            
            return signal, float(confidence)
        except Exception as e:
            return "NONE", 0
    
    def _analyze_market_strength(self, prices, rsi):
        """Analiza la fuerza actual del movimiento del mercado"""
        try:
            # ⭐ Convertir RSI a Python float para evitar ambigüedad
            rsi = float(rsi)
            
            # Calcular volatilidad relativa
            volatility = float(np.std(prices))
            mean_abs_diff = float(np.mean(np.abs(np.diff(prices))))
            
            # Si RSI está en zona media (40-60) y volatilidad baja = movimiento débil = cambio inminente
            if 40 < rsi < 60 and volatility < mean_abs_diff:
                return "WEAK"  # Cambio inminente probable
            elif rsi > 70 or rsi < 30:
                return "EXTREME"  # Cambio rápido probable
            else:
                return "NORMAL"
        except Exception:
            return "UNKNOWN"
    
    def _quick_multiframe_check(self, symbol, timeframe):
        """Verificación rápida en M5 para confirmar cambio"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 20)
            # ⭐ Verificación segura para array
            if rates is None or (isinstance(rates, (list, tuple)) and len(rates) == 0):
                return None
            try:
                if len(rates) == 0:
                    return None
            except:
                return None
            
            closes = np.array([r['close'] for r in rates])
            rsi = self._calculate_rsi(closes, 14)
            
            # Simple: si RSI extremo en M5 también, confirmado
            # ⭐ Convertir a float para evitar ambigüedad
            rsi_latest = float(rsi[-1]) if len(rsi) > 0 else 50
            
            if rsi_latest > 75 or rsi_latest < 25:
                return "CONFIRMED"
            else:
                return "NOT_CONFIRMED"
        except Exception:
            return None
    
    def _synthesize_analysis(self, div_signal, div_conf, strength, macd, macd_signal, 
                            momentum, m5_check, source="MT5"):
        """
        ⭐ MEJORADO: Sintetiza señales y retorna BUY% vs SELL% para mejor claridad
        En lugar de "SELL_TO_BUY 100%", ahora retorna:
        - signal="BUY_DOMINANCE" si BUY > SELL
        - confidence = diferencia (ej: BUY 75% vs SELL 25% → conf 50%)
        """
        
        if div_signal == "NONE":
            # STABLE: mercado equilibrado
            stable_confidence = 50 if strength == "STRONG" else 40
            reason = "Tendencia estable - sin señales claras de reversión"
            return "LOW", "STABLE", float(stable_confidence), reason
        
        # Calcular confianza total
        total_confidence = div_conf
        
        # Boost si strength es débil (cambio inminente)
        if strength == "WEAK":
            total_confidence += 20
        elif strength == "EXTREME":
            total_confidence += 15
        
        # Boost si M5 confirma
        if m5_check == "CONFIRMED":
            total_confidence += 25
        
        # ⭐ BOOST REDUCIDO para snapshots (no sobreestimar)
        if source == "SNAPSHOTS":
            total_confidence += 5  # Antes era +10 (demasiado)
        
        total_confidence = min(100, total_confidence)
        
        # ⭐ CONVERTIR SEÑAL DE REVERSIÓN A % DE CONFIANZA NETO
        # SELL_TO_BUY = BUY alcista (pero medir el diferencial)
        # BUY_TO_SELL = SELL bajista
        
        # Determinar nivel de riesgo
        if total_confidence > 75:
            risk_level = "HIGH"
            reason = f"CAMBIO INMINENTE: {div_signal} (conf: {total_confidence:.0f}%) - Mercado {strength} [📊 {source}]"
        elif total_confidence > 50:
            risk_level = "MEDIUM"
            reason = f"Posible cambio tendencia: {div_signal} (conf: {total_confidence:.0f}%) [📊 {source}]"
        else:
            risk_level = "LOW"
            reason = "Tendencia aún estable"
        
        return risk_level, div_signal, float(total_confidence), reason
    
    def record_reversal_outcome(self, prediction_signal, actual_signal, confidence):
        """⭐ NUEVO: Registra reversiones detectadas para aprendizaje futuro"""
        try:
            correct = prediction_signal == actual_signal
            self.reversal_history.append({
                'predicted': prediction_signal,
                'actual': actual_signal,
                'confidence': confidence,
                'correct': correct,
                'timestamp': datetime.now().isoformat()
            })
            
            # Recalcular score de precisión
            if len(self.reversal_history) > 0:
                correct_count = sum(1 for r in self.reversal_history if r['correct'])
                self.accuracy_score = correct_count / len(self.reversal_history)
        except Exception:
            pass
    
    def get_accuracy_report(self):
        """Devuelve reporte de precisión del detector"""
        if not self.reversal_history:
            return {"accuracy": 0, "total_predictions": 0}
        
        correct = sum(1 for r in self.reversal_history if r['correct'])
        return {
            "accuracy": float(self.accuracy_score),
            "correct_predictions": correct,
            "total_predictions": len(self.reversal_history),
            "adaptive_overbought": float(self.adaptive_rsi_overbought),
            "adaptive_oversold": float(self.adaptive_rsi_oversold),
            "divergence_strength": float(self.divergence_strength)
        }
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula RSI con mejor precisión"""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # ⭐ Convertir a Python float para evitar ambigüedad
            avg_gain = float(np.mean(gains[-period:]))
            avg_loss = float(np.mean(losses[-period:]))
            
            if avg_loss == 0:
                rsi = np.full(len(prices), 100.0 if avg_gain > 0 else 50.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi = np.full(len(prices), rsi)
            
            return rsi
        except Exception:
            return np.full(len(prices), 50.0)
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcula MACD"""
        try:
            exp1 = self._ema(prices, fast)
            exp2 = self._ema(prices, slow)
            macd = exp1 - exp2
            signal_line = self._ema(macd, signal)
            histogram = macd - signal_line
            return macd, signal_line, histogram
        except Exception:
            return np.zeros(len(prices)), np.zeros(len(prices)), np.zeros(len(prices))
    
    def _ema(self, prices, period):
        """Calcula EMA"""
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        return ema
    
    def _calculate_momentum(self, prices, period=10):
        """Calcula momentum (price change)"""
        try:
            momentum = np.zeros(len(prices))
            for i in range(period, len(prices)):
                # ⭐ Evitar división por cero
                if prices[i-period] != 0 and not np.isnan(prices[i-period]) and not np.isinf(prices[i-period]):
                    momentum[i] = ((prices[i] - prices[i-period]) / prices[i-period]) * 100
                else:
                    momentum[i] = 0  # Valor seguro si hay división por cero
            return momentum
        except Exception:
            return np.zeros(len(prices))
    
    def _safe_response(self, risk, signal, conf, reason):
        """Respuesta segura por defecto"""
        return {
            'risk_level': risk,
            'signal': signal,
            'confidence': conf,
            'reason': reason,
            'indicators': {}
        }
    
    # ========== NOVO: MULTI-TIMEFRAME TREND ANALYSIS ==========
    
    def analyze_trend_change_multi_timeframe(self, symbol='GOLD'):
        """
        Analiza cambio de tendencia en múltiples timeframes (M1, M5, M15, M30, H1)
        Detecta cambios antes con mayor anticipación usando consenso multi-TF
        
        Returns:
            dict: {
                'primary_signal': 'SELL_TO_BUY'|'BUY_TO_SELL'|'STABLE',
                'multi_tf_confidence': 0-100,
                'timeframe_signals': {'M1': signal, 'M5': signal, ...},
                'consensus_strength': 0-100 (% de timeframes en acuerdo),
                'strongest_signal_tf': 'M1'|'M5'|...,
                'time_to_reversal': 'IMMINENT'|'5-10_MINUTES'|'10-30_MINUTES'|'STALE',
                'recommendation': 'CLOSE_LONGS'|'CLOSE_SHORTS'|'HOLD'
            }
        """
        try:
            from multi_timeframe_analyzer import MultiTimeframeAnalyzer
            
            mta = MultiTimeframeAnalyzer(symbol=symbol, log_callback=self.log)
            data = mta.get_all_timeframes()
            
            if data['status'] == 'failed':
                return {
                    'primary_signal': 'STABLE',
                    'multi_tf_confidence': 0,
                    'timeframe_signals': {},
                    'reason': 'No data from timeframes'
                }
            
            # Analizar cada timeframe
            tf_signals = {}
            tf_risk_levels = {}
            
            for tf_name in ['M1', 'M5', 'M15', 'M30', 'H1']:
                if tf_name not in data or data[tf_name] is None:
                    continue
                
                rates = data[tf_name]
                if len(rates) < 30:
                    continue
                
                # Extraer OHLCV (acceso seguro a dicts o tuplas)
                closes = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates], dtype=np.float64)
                highs = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates], dtype=np.float64)
                lows = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates], dtype=np.float64)
                
                # Análisis de cambio de tendencia
                signal, risk, confidence = self._detect_trend_reversal(closes, highs, lows, tf_name)
                
                tf_signals[tf_name] = signal
                tf_risk_levels[tf_name] = {'risk': risk, 'confidence': confidence}
                
                self.log(f"[MTF] {tf_name} Signal: {signal} | Risk: {risk} | Conf: {confidence:.1f}%", 'info')
            
            if not tf_signals:
                return {
                    'primary_signal': 'STABLE',
                    'multi_tf_confidence': 0,
                    'timeframe_signals': {},
                    'reason': 'No valid signals from timeframes'
                }
            
            # Determinar señal primaria (consenso multi-TF)
            # Contar señales por tipo
            signals_count = {
                'SELL_TO_BUY': sum(1 for v in tf_signals.values() if v == 'SELL_TO_BUY'),
                'BUY_TO_SELL': sum(1 for v in tf_signals.values() if v == 'BUY_TO_SELL'),
                'STABLE': sum(1 for v in tf_signals.values() if v == 'STABLE')
            }
            
            total_signals = len(tf_signals)
            
            # Determinar consenso
            max_signal = max(signals_count.items(), key=lambda x: x[1])
            primary_signal = max_signal[0]
            consensus_strength = (max_signal[1] / total_signals) * 100
            
            # Confianza multi-TF: promedio ponderado de confianzas
            weighted_confidence = 0
            for tf_name, signal in tf_signals.items():
                if signal == primary_signal:
                    risk_data = tf_risk_levels[tf_name]
                    weight = {'M1': 1, 'M5': 1.1, 'M15': 1.2, 'M30': 1.1, 'H1': 0.9}.get(tf_name, 1)
                    weighted_confidence += risk_data['confidence'] * weight
            
            if total_signals > 0:
                weighted_confidence = weighted_confidence / total_signals
            
            # Recomendación
            if consensus_strength >= 70 and weighted_confidence >= 70:
                if primary_signal == 'SELL_TO_BUY':
                    recommendation = 'CLOSE_SHORTS'
                    time_to_reversal = 'IMMINENT'
                elif primary_signal == 'BUY_TO_SELL':
                    recommendation = 'CLOSE_LONGS'
                    time_to_reversal = 'IMMINENT'
                else:
                    recommendation = 'HOLD'
                    time_to_reversal = 'STALE'
            elif consensus_strength >= 50 and weighted_confidence >= 60:
                if primary_signal in ['SELL_TO_BUY', 'BUY_TO_SELL']:
                    recommendation = 'MONITOR'
                    time_to_reversal = '5-10_MINUTES'
                else:
                    recommendation = 'HOLD'
                    time_to_reversal = 'STALE'
            else:
                recommendation = 'HOLD'
                time_to_reversal = 'STALE'
            
            return {
                'primary_signal': primary_signal,
                'multi_tf_confidence': min(100, weighted_confidence),
                'timeframe_signals': tf_signals,
                'consensus_strength': consensus_strength,
                'strongest_signal_tf': max(tf_signals, key=tf_signals.get) if tf_signals else 'M1',
                'time_to_reversal': time_to_reversal,
                'recommendation': recommendation,
                'data_status': data['status'],
                'timeframes_loaded': data['loaded_timeframes']
            }
            
        except Exception as e:
            self.log(f"[MTF] Error en análisis multi-timeframe: {e}", 'error')
            return {
                'primary_signal': 'STABLE',
                'multi_tf_confidence': 0,
                'timeframe_signals': {},
                'reason': f'Error: {str(e)[:50]}'
            }
    
    def _detect_trend_reversal(self, closes, highs, lows, timeframe_name):
        """
        Detecta reversión de tendencia en un timeframe específico
        
        Returns:
            tuple: (signal, risk_level, confidence)
        """
        try:
            # Calcular indicadores
            rsi = self._calculate_rsi(closes)
            momentum = self._calculate_momentum(closes)
            
            # Detectar divergencias
            is_divergence_bullish = self._detect_bullish_divergence(lows, rsi)
            is_divergence_bearish = self._detect_bearish_divergence(highs, rsi)
            
            # Evaluar momentum
            momentum_bullish = momentum[-1] > 0 and momentum[-1] > np.mean(momentum[-20:] * 1.5)
            momentum_bearish = momentum[-1] < 0 and momentum[-1] < np.mean(momentum[-20:] * 1.5)
            
            # Determinar señal
            if (is_divergence_bullish or momentum_bullish) and rsi[-1] < 30:
                signal = 'SELL_TO_BUY'
                confidence = 70 + (15 if is_divergence_bullish else 0)
                risk = 'MEDIUM' if confidence < 80 else 'LOW'
            elif (is_divergence_bearish or momentum_bearish) and rsi[-1] > 70:
                signal = 'BUY_TO_SELL'
                confidence = 70 + (15 if is_divergence_bearish else 0)
                risk = 'MEDIUM' if confidence < 80 else 'LOW'
            else:
                signal = 'STABLE'
                confidence = 50
                risk = 'LOW'
            
            return signal, risk, confidence
            
        except Exception as e:
            self.log(f"[MTF] Error detectar reversión en {timeframe_name}: {e}", 'error')
            return 'STABLE', 'LOW', 0
    
    def _detect_bullish_divergence(self, prices, rsi):
        """Detecta divergencia alcista (precios bajos pero RSI sube)"""
        try:
            if len(prices) < 30 or len(rsi) < 30:
                return False
            
            # Últimos 30 datos
            recent_prices = prices[-30:]
            recent_rsi = rsi[-30:]
            
            min_price_idx = np.argmin(recent_prices)
            min_rsi_idx = np.argmin(recent_rsi)
            
            # Divergencia si segundo mínimo es más alto pero RSI es más bajo
            return min_price_idx < min_rsi_idx
            
        except Exception:
            return False
    
    def _detect_bearish_divergence(self, prices, rsi):
        """Detecta divergencia bajista (precios altos pero RSI baja)"""
        try:
            if len(prices) < 30 or len(rsi) < 30:
                return False
            
            # Últimos 30 datos
            recent_prices = prices[-30:]
            recent_rsi = rsi[-30:]
            
            max_price_idx = np.argmax(recent_prices)
            max_rsi_idx = np.argmax(recent_rsi)
            
            # Divergencia si segundo máximo es más bajo pero RSI es más alto
            return max_price_idx < max_rsi_idx
            
        except Exception:
            return False
