import numpy as np
from datetime import datetime, timedelta
from collections import deque

class AdaptiveParameters:
    """Sistema de aprendizaje dinámico que ajusta TODOS los indicadores según el mercado"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        # ⭐ PARÁMETROS BASE QUE SE AJUSTAN DINÁMICAMENTE
        
        # Medias móviles
        self.ema_fast_period = 12
        self.ema_slow_period = 26
        self.sma_short_period = 20
        self.sma_long_period = 50
        
        # RSI
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
        # MACD
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # Bandas de Bollinger
        self.bb_period = 20
        self.bb_std_dev = 2.0
        
        # Stochastic
        self.stoch_period = 14
        self.stoch_smooth_k = 3
        self.stoch_smooth_d = 3
        
        # ATR (Average True Range)
        self.atr_period = 14
        
        # ADX (Average Directional Index)
        self.adx_period = 14
        
        # CCI (Commodity Channel Index)
        self.cci_period = 20
        
        # Williams %R
        self.williams_period = 14
        
        # Histórico de resultados para aprendizaje
        self.trade_history = deque(maxlen=50)
        self.market_conditions = deque(maxlen=100)
        self.parameter_performance = {}
        
        # Factores de volatilidad
        self.current_volatility = 1.0
        self.volatility_history = deque(maxlen=20)
        
        # Contador de aprendizaje
        self.learning_cycles = 0
        self.last_adjustment_time = 0
        
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def record_trade_result(self, direction, entry_price, exit_price, profit, confidence, market_volatility):
        """Registra resultado de operación para análisis"""
        try:
            self.trade_history.append({
                'direction': direction,
                'entry': entry_price,
                'exit': exit_price,
                'profit': profit,
                'profit_pct': (profit / entry_price) * 100 if entry_price > 0 else 0,
                'confidence': confidence,
                'volatility': market_volatility,
                'timestamp': datetime.now(),
                'parameters_hash': self._hash_parameters()
            })
            
            self.log(f"[DATA] Operación registrada para aprendizaje", 'info')
            
        except Exception as e:
            self.log(f"Error registrando operación: {str(e)}", 'error')
    
    def record_market_condition(self, volatility, trend, price_range, rsi, adx):
        """Registra condiciones del mercado"""
        try:
            # ⭐ CONVERSIÓN EXPLÍCITA A FLOAT INMEDIATA
            volatility = float(volatility)
            price_range = float(price_range)
            rsi = float(rsi)
            adx = float(adx)
            
            self.market_conditions.append({
                'volatility': volatility,
                'trend': trend,
                'price_range': price_range,
                'rsi': rsi,
                'adx': adx,
                'timestamp': datetime.now()
            })
            
            # ⭐ APPEND ESCALAR PYTHON PURO
            self.volatility_history.append(volatility)
            
            # ⭐ CONVERSIÓN CORRECTA: Convertir a list ANTES de np.mean(), luego a float
            if len(self.volatility_history) > 0:
                volatility_list = list(self.volatility_history)
                mean_result = np.mean(volatility_list)
                self.current_volatility = float(mean_result)
            else:
                self.current_volatility = 1.0
            
        except Exception as e:
            self.log(f"Error registrando condición de mercado: {str(e)}", 'error')
            # ⭐ FALLBACK SEGURO
            self.current_volatility = 1.0
    
    def adjust_parameters_dynamically(self):
        """Ajusta TODOS los parámetros dinámicamente basado en aprendizaje"""
        try:
            current_time = datetime.now().timestamp()
            
            # Ajustar cada minuto (60 segundos)
            if current_time - self.last_adjustment_time < 60:
                return False
            
            self.last_adjustment_time = current_time
            self.learning_cycles += 1
            
            if len(self.trade_history) < 5:
                # ⭐ SILENCIOSO: Sin mensaje "[ESPERA]" que congele visualmente
                # El monitor continúa actualizando cada segundo sin interrupciones
                return False
            
            self.log(f"\n{'='*80}", 'success')
            self.log(f"[IA] AJUSTE DINÁMICO DE PARÁMETROS (Ciclo #{self.learning_cycles})", 'success')
            self.log(f"{'='*80}", 'success')
            
            # Analizar rendimiento reciente
            self._analyze_performance()
            
            # Ajustar TODOS los indicadores
            self._adjust_ema_periods()
            self._adjust_sma_periods()
            self._adjust_rsi_parameters()
            self._adjust_macd_parameters()
            self._adjust_bollinger_parameters()
            self._adjust_stochastic_parameters()
            self._adjust_atr_period()
            self._adjust_adx_period()
            self._adjust_cci_period()
            self._adjust_williams_period()
            
            self.log(f"\n{'='*80}\n", 'success')
            return True
            
        except Exception as e:
            self.log(f"Error ajustando parámetros: {str(e)}", 'error')
            return False
    
    def _analyze_performance(self):
        """Analiza el rendimiento de las últimas operaciones"""
        try:
            if not self.trade_history:
                return
            
            recent_trades = list(self.trade_history)[-10:]
            
            # ⭐ CONVERSIÓN EXPLÍCITA A FLOAT ESCALAR
            profit_list = [float(t['profit']) for t in recent_trades]
            total_profit = float(sum(profit_list))
            
            win_count = 0
            loss_count = 0
            for t in recent_trades:
                profit_val = float(t['profit'])
                if profit_val > 0:
                    win_count += 1
                else:
                    loss_count += 1
            
            # ⭐ CONVERSIONES A FLOAT ANTES DE CUALQUIER OPERACIÓN
            total_trades = float(len(recent_trades))
            if total_trades > 0:
                win_rate = float(win_count) / total_trades * 100.0
            else:
                win_rate = 0.0
            
            profit_pcts = [float(t['profit_pct']) for t in recent_trades]
            if profit_pcts:
                avg_profit = float(sum(profit_pcts)) / float(len(profit_pcts))
            else:
                avg_profit = 0.0
            
            self.log(f"\n📈 ANÁLISIS DE RENDIMIENTO (últimas {int(total_trades)} operaciones):", 'info')
            self.log(f"   Total: ${total_profit:.2f} | Win Rate: {win_rate:.1f}%", 'info')
            self.log(f"   Ganadas: {win_count} | Perdidas: {loss_count}", 'info')
            self.log(f"   Profit promedio: {avg_profit:.2f}%", 'info')
            
            # Registrar métricas
            self.performance_metrics = {
                'total_profit': float(total_profit),
                'win_rate': float(win_rate),
                'avg_profit': float(avg_profit),
                'total_trades': int(total_trades)
            }
            
        except Exception as e:
            self.log(f"Error analizando rendimiento: {str(e)}", 'error')
    
    def _adjust_ema_periods(self):
        """Ajusta períodos EMA basado en volatilidad y rendimiento"""
        try:
            old_fast = self.ema_fast_period
            old_slow = self.ema_slow_period
            
            # ⭐ CONVERSIÓN EXPLÍCITA A FLOAT ESCALAR
            volatility_float = float(self.current_volatility)
            
            # ⭐ COMPARACIONES CON ESCALARES PYTHON PURO
            if volatility_float > 1.5:
                # Alta volatilidad: períodos más largos (suavizar más)
                self.ema_fast_period = max(10, min(16, int(12 * (volatility_float * 0.8))))
                self.ema_slow_period = max(20, min(35, int(26 * (volatility_float * 0.8))))
                self.log(f"   🔼 ALTA VOLATILIDAD: EMA períodos aumentados", 'warning')
            
            elif volatility_float < 0.8:
                # Baja volatilidad: períodos más cortos (responder más rápido)
                self.ema_fast_period = max(8, min(12, int(12 * (volatility_float / 0.8))))
                self.ema_slow_period = max(18, min(26, int(26 * (volatility_float / 0.8))))
                self.log(f"   🔽 BAJA VOLATILIDAD: EMA períodos reducidos", 'warning')
            
            else:
                # Volatilidad normal: mantener cerca de los valores base
                self.ema_fast_period = 12
                self.ema_slow_period = 26
            
            # Ajustar según win rate
            if hasattr(self, 'performance_metrics'):
                win_rate_val = float(self.performance_metrics['win_rate'])
                if win_rate_val < 40.0:
                    # Rendimiento bajo: aumentar períodos (ser más conservador)
                    self.ema_fast_period = min(self.ema_fast_period + 2, 16)
                    self.ema_slow_period = min(self.ema_slow_period + 2, 32)
                    self.log(f"   [ADVERTENCIA] RENDIMIENTO BAJO: EMA períodos conservadores", 'warning')
                
                elif win_rate_val > 70.0:
                    # Rendimiento alto: reducir períodos (ser más agresivo)
                    self.ema_fast_period = max(self.ema_fast_period - 1, 10)
                    self.ema_slow_period = max(self.ema_slow_period - 1, 20)
                    self.log(f"   [OK] RENDIMIENTO ALTO: EMA períodos agresivos", 'success')
            
            if old_fast != self.ema_fast_period or old_slow != self.ema_slow_period:
                self.log(
                    f"🔧 EMA: FAST {old_fast}→{self.ema_fast_period} | "
                    f"SLOW {old_slow}→{self.ema_slow_period}",
                    'warning'
                )
        
        except Exception as e:
            self.log(f"Error ajustando EMA: {str(e)}", 'error')
    
    def _adjust_sma_periods(self):
        """Ajusta períodos SMA basado en tendencia"""
        try:
            old_short = self.sma_short_period
            old_long = self.sma_long_period
            
            if len(self.market_conditions) < 5:
                return
            
            recent_trends = [m['trend'] for m in list(self.market_conditions)[-5:]]
            alcista_count = sum(1 for t in recent_trends if t == 'ALCISTA')
            
            if alcista_count >= 4:
                # Tendencia fuerte alcista: períodos más cortos
                self.sma_short_period = max(15, min(25, int(20 * 0.85)))
                self.sma_long_period = max(40, min(60, int(50 * 0.85)))
                self.log(f"   📈 Tendencia ALCISTA: SMA períodos más cortos", 'info')
            
            elif alcista_count <= 1:
                # Tendencia fuerte bajista: períodos más largos
                self.sma_short_period = max(20, min(30, int(20 * 1.15)))
                self.sma_long_period = max(55, min(70, int(50 * 1.15)))
                self.log(f"   📉 Tendencia BAJISTA: SMA períodos más largos", 'info')
            
            else:
                # Tendencia neutral
                self.sma_short_period = 20
                self.sma_long_period = 50
            
            if old_short != self.sma_short_period or old_long != self.sma_long_period:
                self.log(
                    f"🔧 SMA: SHORT {old_short}→{self.sma_short_period} | "
                    f"LONG {old_long}→{self.sma_long_period}",
                    'warning'
                )
        
        except Exception as e:
            self.log(f"Error ajustando SMA: {str(e)}", 'error')
    
    def _adjust_rsi_parameters(self):
        """Ajusta parámetros RSI según volatilidad"""
        try:
            old_period = self.rsi_period
            old_overbought = self.rsi_overbought
            old_oversold = self.rsi_oversold
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            # RSI: más sensible con volatilidad baja, menos con volatilidad alta
            if volatility_float > 1.5:
                self.rsi_period = max(16, min(21, int(14 * 1.3)))  # Más suave
                self.rsi_overbought = 75  # Umbral más alto
                self.rsi_oversold = 25   # Umbral más bajo
                self.log(f"   [DATA] Alta volatilidad: RSI período {old_period}→{self.rsi_period}", 'info')
            else:
                self.rsi_period = max(10, min(14, int(14 * 0.8)))  # Más sensible
                self.rsi_overbought = 70
                self.rsi_oversold = 30
                self.log(f"   [DATA] Baja volatilidad: RSI período {old_period}→{self.rsi_period}", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando RSI: {str(e)}", 'error')
    
    def _adjust_macd_parameters(self):
        """Ajusta parámetros MACD según momentum"""
        try:
            old_fast = self.macd_fast
            old_slow = self.macd_slow
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            # MACD: ajustar según volatilidad para captar cambios
            if volatility_float > 1.5:
                # Alta volatilidad: períodos más cortos para captar cambios rápidos
                self.macd_fast = max(10, min(14, int(12 * 0.9)))
                self.macd_slow = max(22, min(28, int(26 * 0.9)))
            else:
                # Baja volatilidad: períodos más largos para evitar falsas señales
                self.macd_fast = max(12, min(14, int(12 * 1.1)))
                self.macd_slow = max(26, min(30, int(26 * 1.1)))
            
            if old_fast != self.macd_fast or old_slow != self.macd_slow:
                self.log(f"   📈 MACD: FAST {old_fast}→{self.macd_fast} | SLOW {old_slow}→{self.macd_slow}", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando MACD: {str(e)}", 'error')
    
    def _adjust_bollinger_parameters(self):
        """Ajusta parámetros de Bandas de Bollinger"""
        try:
            old_period = self.bb_period
            old_std = self.bb_std_dev
            
            # ⭐ CONVERSIÓN EXPLÍCITA A FLOAT
            volatility_float = float(self.current_volatility)
            
            # ⭐ COMPARACIONES CON ESCALARES
            if volatility_float > 1.5:
                # Alta volatilidad: ampliar bandas
                self.bb_period = max(18, min(24, int(20 * 0.95)))
                self.bb_std_dev = max(2.0, min(2.5, 2.0 + (volatility_float * 0.2)))
                self.log(f"   [DATA] Bollinger: Bandas ampliadas para volatilidad alta", 'info')
            else:
                # Baja volatilidad: reducir bandas
                self.bb_period = max(16, min(22, int(20 * 1.05)))
                self.bb_std_dev = max(1.5, min(2.0, 2.0 - (volatility_float * 0.2)))
                self.log(f"   [DATA] Bollinger: Bandas reducidas para volatilidad baja", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando Bollinger: {str(e)}", 'error')
    
    def _adjust_stochastic_parameters(self):
        """Ajusta parámetros Stochastic"""
        try:
            old_period = self.stoch_period
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            # Stochastic: ajustar sensibilidad según volatilidad
            if volatility_float > 1.5:
                self.stoch_period = max(16, min(20, int(14 * 1.2)))
                self.stoch_smooth_k = 5
                self.stoch_smooth_d = 5
                self.log(f"   [DATA] Stochastic: Período {old_period}→{self.stoch_period} (menos sensible)", 'info')
            else:
                self.stoch_period = max(12, min(14, int(14 * 0.9)))
                self.stoch_smooth_k = 3
                self.stoch_smooth_d = 3
                self.log(f"   [DATA] Stochastic: Período {old_period}→{self.stoch_period} (más sensible)", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando Stochastic: {str(e)}", 'error')
    
    def _adjust_atr_period(self):
        """Ajusta período ATR según volatilidad"""
        try:
            old_period = self.atr_period
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            if volatility_float > 1.5:
                self.atr_period = max(16, min(20, int(14 * 1.2)))
            else:
                self.atr_period = max(12, min(14, int(14 * 0.9)))
            
            if old_period != self.atr_period:
                self.log(f"   [DATA] ATR: Período {old_period}→{self.atr_period}", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando ATR: {str(e)}", 'error')
    
    def _adjust_adx_period(self):
        """Ajusta período ADX"""
        try:
            old_period = self.adx_period
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            if volatility_float > 1.5:
                self.adx_period = max(14, min(18, int(14 * 1.15)))
            else:
                self.adx_period = max(12, min(14, int(14 * 0.9)))
            
            if old_period != self.adx_period:
                self.log(f"   [DATA] ADX: Período {old_period}→{self.adx_period}", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando ADX: {str(e)}", 'error')
    
    def _adjust_cci_period(self):
        """Ajusta período CCI"""
        try:
            old_period = self.cci_period
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            if volatility_float > 1.5:
                self.cci_period = max(20, min(28, int(20 * 1.2)))
            else:
                self.cci_period = max(16, min(22, int(20 * 0.9)))
            
            if old_period != self.cci_period:
                self.log(f"   [DATA] CCI: Período {old_period}→{self.cci_period}", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando CCI: {str(e)}", 'error')
    
    def _adjust_williams_period(self):
        """Ajusta período Williams %R"""
        try:
            old_period = self.williams_period
            
            # ⭐ CONVERSIÓN EXPLÍCITA
            volatility_float = float(self.current_volatility)
            
            if volatility_float > 1.5:
                self.williams_period = max(16, min(20, int(14 * 1.2)))
            else:
                self.williams_period = max(12, min(14, int(14 * 0.9)))
            
            if old_period != self.williams_period:
                self.log(f"   [DATA] Williams %R: Período {old_period}→{self.williams_period}", 'info')
        
        except Exception as e:
            self.log(f"Error ajustando Williams: {str(e)}", 'error')
    
    def _hash_parameters(self):
        """Crea un hash de los parámetros actuales"""
        return hash((
            self.ema_fast_period,
            self.ema_slow_period,
            self.sma_short_period,
            self.sma_long_period,
            self.rsi_period,
            self.macd_fast,
            self.macd_slow,
            self.bb_period,
            self.stoch_period,
            self.atr_period,
            self.adx_period,
            self.cci_period,
            self.williams_period,
        ))
    
    def get_current_parameters(self):
        """Devuelve TODOS los parámetros actuales ajustados"""
        return {
            'ema_fast': self.ema_fast_period,
            'ema_slow': self.ema_slow_period,
            'sma_short': self.sma_short_period,
            'sma_long': self.sma_long_period,
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow,
            'macd_signal': self.macd_signal,
            'bb_period': self.bb_period,
            'bb_std_dev': round(self.bb_std_dev, 2),
            'stoch_period': self.stoch_period,
            'atr_period': self.atr_period,
            'adx_period': self.adx_period,
            'cci_period': self.cci_period,
            'williams_period': self.williams_period,
            'current_volatility': round(self.current_volatility, 3),
            'learning_cycles': self.learning_cycles
        }
    
    def calculate_entry_tolerance(self, atr_value, current_price):
        """Calcula rango de tolerancia dinámico para entradas rápidas basado en ATR y volatilidad"""
        try:
            # ⭐ CONVERSIÓN EXPLÍCITA A FLOAT
            atr_float = float(atr_value)
            price_float = float(current_price)
            volatility_float = float(self.current_volatility)
            
            # Base: % del ATR (mayor ATR = mayor tolerancia)
            atr_percentage = atr_float / price_float * 100 if price_float > 0 else 0.1
            
            # Factor de volatilidad (inverso: baja volatilidad = rango corto = entrada rápida)
            # ⭐ REDUCIDO PARA ENTRAR MÁS CERCA DEL PRECIO OBJETIVO
            if volatility_float > 1.5:
                # Alta volatilidad: permitir rango mayor
                tolerance_pct = atr_percentage * 0.35  # REDUCIDO de 0.80 a 0.35
            elif volatility_float < 0.8:
                # Baja volatilidad: rango muy corto (entrada rápida)
                tolerance_pct = atr_percentage * 0.12  # REDUCIDO de 0.25 a 0.12
            else:
                # Volatilidad normal
                tolerance_pct = atr_percentage * 0.20  # REDUCIDO de 0.50 a 0.20
            
            # Convertir porcentaje a puntos
            tolerance_points = price_float * tolerance_pct / 100
            
            # Mínimo 0.3 puntos, máximo 2.5 puntos (REDUCIDO para máximo)
            tolerance_points = max(0.3, min(2.5, tolerance_points))
            
            return float(tolerance_points)
            
        except Exception as e:
            self.log(f"Error calculando tolerancia de entrada: {str(e)}", 'error')
            return 1.0  # Fallback: 1 punto
    
    # ⭐ NUEVO: CALIBRACIÓN ULTRA-PRECISA
    def calculate_ultra_precise_calibration(self, closes, highs, lows):
        """Calcula calibración ultra-precisa basada en análisis técnico avanzado"""
        try:
            if len(closes) < 100:
                return 50  # Score neutral por defecto
            
            # 1 ANÁLISIS DE RETORNO A LA MEDIA (Mean Reversion Index)
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])
            distance_from_mean = abs(closes[-1] - sma_20) / sma_20 * 100
            
            if distance_from_mean > 5:
                mean_reversion_score = 90  # Alta probabilidad de reversión
            elif distance_from_mean > 3:
                mean_reversion_score = 70
            else:
                mean_reversion_score = 40
            
            # 2 ANÁLISIS DE ESTRUCTURA DE PRECIOS
            recent_high = max(closes[-20:])
            recent_low = min(closes[-20:])
            current_position = (closes[-1] - recent_low) / (recent_high - recent_low)
            
            # Si está en extremo, hay menos precisión
            if current_position > 0.9 or current_position < 0.1:
                structure_score = 60
            elif current_position > 0.7 or current_position < 0.3:
                structure_score = 75
            else:
                structure_score = 90  # Centro = más equilibrio
            
            # 3 CONFIRMACIÓN DE VOLUMEN
            vol_20 = np.mean(closes[-20:])
            vol_momentum = (closes[-1] - vol_20) / vol_20 * 100
            
            if abs(vol_momentum) > 2:
                volume_score = 85  # Movimiento confirmado
            elif abs(vol_momentum) > 1:
                volume_score = 70
            else:
                volume_score = 50  # Indeciso
            
            # 4 TENDENCIA ALINEADA
            trend_up = (closes[-1] > sma_20 > sma_50)
            trend_down = (closes[-1] < sma_20 < sma_50)
            
            if trend_up or trend_down:
                trend_score = 85  # Fuerte tendencia
            else:
                trend_score = 55  # Sin tendencia clara
            
            # 5 PUNTOS DE CONTROL (Pivots y Extremos)
            pivots = self._calculate_pivots(closes[-50:])
            distance_to_pivot = min([abs(closes[-1] - p) for p in pivots]) if pivots else 0
            
            if distance_to_pivot < 0.5:
                pivot_score = 95  # Muy cerca de pivot
            elif distance_to_pivot < 2:
                pivot_score = 80  # Cerca de pivot
            else:
                pivot_score = 60
            
            # [OBJETIVO] SCORE FINAL PONDERADO
            calibration_score = (
                mean_reversion_score * 0.25 +
                structure_score * 0.20 +
                volume_score * 0.15 +
                trend_score * 0.25 +
                pivot_score * 0.15
            )
            
            return round(min(100, max(0, calibration_score)), 1)
            
        except Exception as e:
            self.log(f"Error en calibración ultra-precisa: {str(e)}", 'error')
            return 50
    
    def _calculate_pivots(self, prices):
        """Calcula puntos pivot de soporte/resistencia"""
        try:
            if len(prices) < 3:
                return []
            
            pivots = []
            for i in range(1, len(prices) - 1):
                # Local max (techo)
                if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                    pivots.append(prices[i])
                # Local min (fondo)
                elif prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                    pivots.append(prices[i])
            
            return pivots
        except:
            return []
    
    def calculate_entry_confidence_advanced(self, buy_score, sell_score, volatility, trend_strength):
        """Calcula confianza de entrada avanzada considerando múltiples factores"""
        try:
            # Diferencia entre compra y venta
            score_difference = abs(buy_score - sell_score)
            
            # Factor de divergencia
            if score_difference > 30:
                divergence_factor = 1.2  # Señal fuerte
            elif score_difference > 20:
                divergence_factor = 1.0  # Señal normal
            else:
                divergence_factor = 0.8  # Señal débil
            
            # Factor de volatilidad (bajo = mayor confianza)
            volatility_factor = 1 / (volatility / 100 + 0.5)
            volatility_factor = min(1.5, volatility_factor)
            
            # Factor de tendencia
            if abs(trend_strength) > 70:
                trend_factor = 1.2  # Tendencia muy fuerte
            elif abs(trend_strength) > 40:
                trend_factor = 1.0  # Tendencia normal
            else:
                trend_factor = 0.9  # Tendencia débil
            
            # Score final
            base_confidence = max(buy_score, sell_score)
            final_confidence = base_confidence * divergence_factor * volatility_factor * trend_factor
            
            return round(min(100, max(0, final_confidence)), 1)
            
        except Exception as e:
            self.log(f"Error calculando confianza avanzada: {str(e)}", 'error')
            return 50.0
    
    def log_current_state(self):
        """Loguea el estado actual de TODOS los parámetros"""
        try:
            params = self.get_current_parameters()
            
            self.log(f"\n[DATA] ESTADO DE PARÁMETROS ADAPTATIVOS:", 'market')
            self.log(f"   Ciclos de aprendizaje: {params['learning_cycles']}", 'info')
            self.log(f"   Volatilidad actual: {params['current_volatility']:.2f}x", 'info')
            
            self.log(f"\n📈 Medias Móviles:", 'market')
            self.log(f"   EMA: {params['ema_fast']}/{params['ema_slow']}", 'info')
            self.log(f"   SMA: {params['sma_short']}/{params['sma_long']}", 'info')
            
            self.log(f"\n[OBJETIVO] Osciladores:", 'market')
            self.log(f"   RSI({params['rsi_period']}): OB={params['rsi_overbought']} OS={params['rsi_oversold']}", 'info')
            self.log(f"   MACD: {params['macd_fast']}/{params['macd_slow']}/{params['macd_signal']}", 'info')
            self.log(f"   Stoch({params['stoch_period']})", 'info')
            
            self.log(f"\n[DATA] Bandas y Rango:", 'market')
            self.log(f"   Bollinger({params['bb_period']}, σ={params['bb_std_dev']})", 'info')
            self.log(f"   ATR({params['atr_period']})", 'info')
            
            self.log(f"\n[UBICACION] Tendencia y Canales:", 'market')
            self.log(f"   ADX({params['adx_period']})", 'info')
            self.log(f"   CCI({params['cci_period']})", 'info')
            self.log(f"   Williams %R({params['williams_period']})", 'info')
            
        except Exception as e:
            self.log(f"Error loguando estado: {str(e)}", 'error')
