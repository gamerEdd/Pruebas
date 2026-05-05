import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime
import time

class GoldAnalyzer:
    def __init__(self, log_callback=None):
        self.timeframes = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15
        }
        self.symbol = "GOLD"  # Cambiado a GOLD
        self.bars_to_analyze = 100
        
        # Agregar atributos que faltaban
        self.retry_attempts = 3  # Número de intentos de reconexión
        self.retry_delay = 1     # Segundos entre intentos
        
        # Parámetros más sensibles para Gold
        self.rsi_period = 14
        self.ema_fast = 3      # Más rápido (antes 5)
        self.ema_slow = 7      # Más rápido (antes 15)
        
        # Umbrales más sensibles
        self.rsi_thresholds = {
            'oversold': 45,     # Más sensible (antes 40)
            'overbought': 55,   # Más sensible (antes 60)
            'neutral_low': 47,  # Más preciso
            'neutral_high': 53  # Más preciso
        }
        
        # Ajustar probabilidad mínima a 75%
        self.min_probability = 75.0  # Cambiado de 80.0 a 75.0
        
        # Ajustar pesos para balance entre precisión y oportunidades
        self.weights = {
            "M1": 0.30,    # Reducido para dar más peso a M5
            "M5": 0.45,    # Aumentado para M5 que suele ser más estable
            "M15": 0.25    # Mantenido para validación
        }
        
        # Nuevos umbrales para confirmaciones
        self.score_thresholds = {
            "strong": 100.0,  # Score muy alto
            "medium": 70.0,   # Score medio
            "weak": 45.0      # Score bajo pero válido
        }
        
        # Agregar contadores que faltaban
        self.perdidas = 0
        self.operaciones_rojas = 0
        self.operaciones_azules = 0
        self.ganadas = 0
        self.ganancia_neta = 0.0
        self.total_operaciones_abiertas = 0
        self.position_ids = set()
        
        self.log_callback = log_callback or print  # Usar print si no hay callback

    def log(self, message, tag='info'):
        """Método para manejar logs usando callback si está disponible"""
        if self.log_callback and callable(self.log_callback):
            self.log_callback(message, tag)
        else:
            print(message)

    def analyze_opportunity(self):
        """Análisis más estricto con mejores filtros"""
        try:
            # Asegurar conexión MT5
            if not mt5.initialize():
                self.log("Reconectando a MT5...", 'warning')
                mt5.shutdown()
                time.sleep(1)
                if not mt5.initialize():
                    self.log("Error de conexión con MT5", 'error')
                    return None

            # Asegurar que el símbolo está seleccionado
            if not mt5.symbol_select(self.symbol, True):
                self.log(f"Error seleccionando {self.symbol}", 'error')
                return None

            analysis_results = {}
            total_score = 0
            final_direction = None
            confirmations = 0  # Nuevo: contador de confirmaciones
            
            self.log("\n🔄 Iniciando análisis multi-timeframe...", 'info')
            
            # Analizar cada timeframe
            for tf_name, tf in self.timeframes.items():
                self.log(f"\n📊 Analizando {tf_name}...", 'market')
                
                # Obtener datos con reintentos
                rates = None
                for attempt in range(self.retry_attempts):
                    rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, self.bars_to_analyze)
                    if rates is not None:
                        break
                    self.log(f"Reintento {attempt + 1} para {tf_name}...", 'warning')
                    time.sleep(self.retry_delay)
                
                if rates is None:
                    self.log(f"❌ No se pudieron obtener datos para {tf_name}", 'error')
                    continue
                    
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                # Calcular indicadores
                close = df['close'].values
                high = df['high'].values
                low = df['low'].values
                volume = df['tick_volume'].values
                
                # 1. Análisis técnico básico
                rsi = self._calculate_rsi(close)
                ema_fast = self._calculate_ema(close, self.ema_fast)
                ema_slow = self._calculate_ema(close, self.ema_slow)
                atr = self._calculate_atr(high, low, close)
                
                # 2. Análisis de volumen y volatilidad específico para Gold
                vol_sma = np.mean(volume[-20:])
                vol_ratio = volume[-1] / vol_sma if vol_sma > 0 else 1.0
                volatility = atr[-1] / close[-1] * 100  # Volatilidad en porcentaje
                
                # 3. Análisis de tendencia específico para Gold
                trend_direction = "FLAT"
                ema_diff = ema_fast[-1] - ema_slow[-1]
                ema_diff_pct = (ema_diff / close[-1]) * 100
                
                if abs(ema_diff_pct) > 0.05:  # Umbral de 0.05% para Gold
                    if ema_diff > 0:
                        trend_direction = "UP"
                    else:
                        trend_direction = "DOWN"
                
                # 4. Análisis de momentum para Gold
                momentum = self._calculate_momentum(close)
                
                # 5. Análisis de patrones de precio
                swing_high = self._is_swing_high(high, low, close)
                swing_low = self._is_swing_low(high, low, close)
                
                # Calcular score adaptado para Gold
                score = 0
                direction = None
                
                # RSI más sensible (0-50 puntos)
                current_rsi = rsi[-1]
                if current_rsi < self.rsi_thresholds['oversold']:
                    score += 50  # Aumentado de 40 a 50
                    direction = "BUY"
                elif current_rsi > self.rsi_thresholds['overbought']:
                    score += 50  # Aumentado de 40 a 50
                    direction = "SELL"
                elif current_rsi < self.rsi_thresholds['neutral_low']:
                    score += 30  # Aumentado de 25 a 30
                    direction = "BUY"
                elif current_rsi > self.rsi_thresholds['neutral_high']:
                    score += 30  # Aumentado de 25 a 30
                    direction = "SELL"
                
                # Tendencia más sensible (0-50 puntos)
                if abs(ema_diff_pct) > 0.01:  # Más sensible (antes 0.02)
                    if ema_diff > 0 and (direction is None or direction == "BUY"):
                        score += 50  # Aumentado de 40 a 50
                        direction = "BUY"
                    elif ema_diff < 0 and (direction is None or direction == "SELL"):
                        score += 50  # Aumentado de 40 a 50
                        direction = "SELL"
                
                # Momentum más sensible (0-30 puntos)
                if abs(momentum) > 0.02:  # Más sensible (antes 0.03)
                    if momentum > 0 and (direction is None or direction == "BUY"):
                        score += 30  # Aumentado de 20 a 30
                    elif momentum < 0 and (direction is None or direction == "SELL"):
                        score += 30  # Aumentado de 20 a 30
                        
                # Ajustes de volatilidad más sensibles
                volatility_multiplier = 1.0
                if volatility > 0.2:  # Más sensible (antes 0.3)
                    volatility_multiplier = 1.15
                elif volatility < 0.1:
                    volatility_multiplier = 0.95
                
                score *= volatility_multiplier
                
                # Ajustes de volumen más sensibles
                if vol_ratio > 1.1:  # Más sensible (antes 1.2)
                    score *= 1.15
                elif vol_ratio < 0.5:
                    score *= 0.95

                # Guardar resultados
                analysis_results[tf_name] = {
                    "score": score,
                    "direction": direction,
                    "rsi": current_rsi,
                    "trend": trend_direction,
                    "volume_ratio": vol_ratio,
                    "volatility": volatility,
                    "atr": atr[-1],
                    "momentum": momentum
                }
                
                # Acumular score ponderado
                weighted_score = score * self.weights[tf_name]
                total_score += weighted_score
                
                if weighted_score > 0:
                    final_direction = direction
                
                # Actualizar logs con resultados
                self.log(f"Score {tf_name}: {score:.1f} | Direction: {direction}", 'market')
                self.log(f"RSI: {current_rsi:.1f} | Trend: {trend_direction}", 'market')
                self.log(f"Volatility: {volatility:.2f}% | Vol Ratio: {vol_ratio:.2f}", 'market')
            
            # Al final del análisis de cada timeframe, si score > 65 contar como confirmación
            if score >= 65:  # Bajado de 70 a 65 para ser más permisivo
                confirmations += 1
                if final_direction is None:
                    final_direction = direction
                elif direction == final_direction:
                    confirmations += 1  # Doble confirmación si coincide dirección

            # Modificar la decisión final para usar el nuevo sistema
            directions = {"BUY": 0, "SELL": 0}
            strong_signals = 0
            confirmations = 0
            
            for tf_name, analysis in analysis_results.items():
                score = analysis["score"]
                direction = analysis["direction"]
                
                if direction:
                    directions[direction] += 1
                    
                    if score >= self.score_thresholds["strong"]:
                        strong_signals += 1
                        confirmations += 2  # Doble peso para señales fuertes
                    elif score >= self.score_thresholds["medium"]:
                        confirmations += 1
                    elif score >= self.score_thresholds["weak"]:
                        confirmations += 0.5  # Media confirmación para señales débiles
            
            # Determinar dirección final basada en mayoría
            final_direction = max(directions.items(), key=lambda x: x[1])[0] if any(directions.values()) else None
            
            # Nueva lógica de decisión más flexible
            should_trade = (
                total_score >= 73.0 and  # Cambiado de 69.0 a 73.0
                (
                    confirmations >= 1.5 or  # Al menos 1.5 confirmaciones
                    strong_signals >= 1 or   # O una señal muy fuerte
                    (directions[final_direction] >= 2 and total_score >= 75.0)  # O 2 timeframes en misma dirección con score alto
                )
            )
            
            # NUEVO: Análisis de spread
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                spread = (tick.ask - tick.bid) / tick.bid * 100
                if spread > 0.03:  # Spread mayor a 0.03%
                    self.log(f"⚠️ Spread muy alto: {spread:.4f}%", 'warning')
                    return None

            # NUEVO: Verificar volumen mínimo
            if rates is not None:
                volume = np.array([r[5] for r in rates])
                avg_volume = np.mean(volume[-20:])
                if volume[-1] < avg_volume * 0.8:
                    self.log("⚠️ Volumen insuficiente", 'warning')
                    return None

            # NUEVO: No operar si volatilidad es muy alta
            atr = self._calculate_atr(high, low, close)
            volatility = atr[-1] / close[-1] * 100
            if volatility > 0.3:  # Volatilidad mayor al 0.3%
                self.log(f"⚠️ Volatilidad muy alta: {volatility:.2f}%", 'warning')
                return None

            # NUEVO: Verificar tendencia clara
            ema20 = self._calculate_ema(close, 20)
            ema50 = self._calculate_ema(close, 50)
            ema100 = self._calculate_ema(close, 100)
            
            trend_aligned = (
                (ema20[-1] > ema50[-1] > ema100[-1]) or  # Tendencia alcista clara
                (ema20[-1] < ema50[-1] < ema100[-1])     # Tendencia bajista clara
            )
            
            if not trend_aligned:
                self.log("⚠️ Tendencia no clara - esperando mejor momento", 'warning')
                return None

            # NUEVO: Verificar momentum consistente
            momentum = self._calculate_momentum(close)
            if abs(momentum) < 0.05:  # Momentum muy débil
                self.log("⚠️ Momentum insuficiente", 'warning')
                return None

            # NUEVO: Requerir más confirmaciones
            if should_trade and final_direction:
                confirmations_needed = 2.5  # Aumentado de 1.5 a 2.5
                if confirmations < confirmations_needed:
                    self.log(f"⚠️ Confirmaciones insuficientes ({confirmations:.1f} < {confirmations_needed})", 'warning')
                    return None

                # NUEVO: Score mínimo más alto
                if total_score < 77.0:  # Aumentado de 73.0 a 77.0
                    self.log(f"⚠️ Score insuficiente ({total_score:.1f} < 77.0)", 'warning')
                    return None

            if should_trade and final_direction:
                current_atr = analysis_results["M1"]["atr"]
                volatility = analysis_results["M1"]["volatility"]
                
                # Ajustar SL/TP según la fuerza de la señal
                sl_points = max(100.0, current_atr * 2.5)
                tp_points = max(75.0, current_atr * 2.0)
                
                self.log(f"\n✅ SEÑAL ENCONTRADA:", 'success')
                self.log(f"Dirección: {final_direction}", 'success')
                self.log(f"Probabilidad: {total_score:.1f}%", 'success')
                self.log(f"Confirmaciones: {confirmations:.1f}", 'success')
                self.log(f"Señales fuertes: {strong_signals}", 'success')
                self.log(f"SL: {sl_points:.1f} | TP: {tp_points:.1f}", 'success')
                
                return {
                    "direction": final_direction,
                    "probability": total_score,
                    "trend_strength": abs(analysis_results["M1"]["momentum"]),
                    "volatility": current_atr,
                    "sl_points": sl_points,
                    "tp_points": tp_points,
                    "confirmations": confirmations
                }
            
            self.log(f"\n⚠️ No hay señal clara | Score Total: {total_score:.1f}% | Confirmaciones: {confirmations:.1f}", 'warning')
            return None
            
        except Exception as e:
            self.log(f"❌ Error en analyze_opportunity: {str(e)}", 'error')
            return None

    def _calculate_rsi(self, prices, period=14):
        """Calcula el RSI usando numpy"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        
        if down == 0:
            return np.zeros_like(prices) + 100
            
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            up = (up*(period-1) + upval)/period
            down = (down*(period-1) + downval)/period
            rs = up/down
            rsi[i] = 100. - 100./(1. + rs)
            
        return rsi

    def _calculate_ema(self, prices, period):
        """Calcula EMA usando numpy"""
        multiplier = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
            
        return ema

    def _calculate_atr(self, high, low, close, period=14):
        """Calcula ATR usando numpy"""
        high_low = high - low
        high_close = np.abs(high - np.roll(close, 1))
        low_close = np.abs(low - np.roll(close, 1))
        
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        tr[0] = tr[1]
        
        atr = np.zeros_like(close)
        atr[0] = tr[0]
        
        for i in range(1, len(close)):
            atr[i] = ((period - 1) * atr[i-1] + tr[i]) / period
            
        return atr

    def _calculate_momentum(self, prices, period=10):
        """Calcula el momentum"""
        return (prices[-1] - prices[-period]) / prices[-period] * 100

    def _is_swing_high(self, high, low, close, lookback=5):
        """Detecta swing highs"""
        last_high = high[-lookback:]
        return high[-lookback//2] == max(last_high)

    def _is_swing_low(self, high, low, close, lookback=5):
        """Detecta swing lows"""
        last_low = low[-lookback:]
        return low[-lookback//2] == min(last_low)

    def get_market_context(self):
        """Obtiene contexto actual del mercado"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return None
                
            return {
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "volume": tick.volume,
                "spread": tick.ask - tick.bid,
                "time": datetime.fromtimestamp(tick.time)
            }
        except:
            return None
