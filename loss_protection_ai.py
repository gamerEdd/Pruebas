import numpy as np
import MetaTrader5 as mt5
import mt5_safe
from datetime import datetime
import json
import os
from pathlib import Path

# ⭐ Hacer scikit-learn OPCIONAL (compatible con Python 3.8)
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    StandardScaler = None
    RandomForestClassifier = None

class LossProtectionAI:
    def __init__(self, log_callback=None):
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.log_callback = log_callback
        self.sklearn_available = SKLEARN_AVAILABLE
        
        # ⭐ NUEVO: Modelo ML para predicción de pérdidas
        if SKLEARN_AVAILABLE:
            self.loss_predictor = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
            self.model_trained = False
        else:
            self.loss_predictor = None
            self.model_trained = False
            if log_callback:
                log_callback("[LOSS] ⚠️ scikit-learn no disponible - usando protección sin ML", 'warning')
        self.trades_count = 0
        self.training_data = []
        self.training_labels = []
        
        # Histórico de trades para entrenamiento
        self.trades_history_file = Path('logs/loss_protection_history.json')
        self.load_trades_history()
        
        # Ajustar pesos para dar más importancia a tendencia y momentum
        self.feature_weights = {
            'rsi': 0.15,          # Reducido
            'momentum': 0.25,      # Aumentado
            'macd': 0.20,         # Aumentado
            'bollinger': 0.15,
            'volume': 0.05,       # Reducido
            'adx': 0.15,
            'volatility': 0.05    # Reducido
        }
        
        # Ajustar umbrales para dar más tiempo
        self.thresholds = {
            'critical_score': 85,      # Aumentado (antes 75)
            'warning_score': 75,       # Aumentado (antes 60)
            'safe_score': 35,          # Reducido (antes 40)
            'min_profit_hold': 0.2,
            'max_loss_quick': -5.0     # Aumentado (antes -2.0)
        }
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def load_trades_history(self):
        """Carga histórico de trades cerrados para reentrenamiento"""
        try:
            if self.trades_history_file.exists():
                with open(self.trades_history_file, 'r') as f:
                    trades = json.load(f)
                    self.log(f"[LOSS] Cargados {len(trades)} trades históricos para entrenamiento", 'info')
                    return trades
        except Exception as e:
            self.log(f"[LOSS] Error cargando histórico: {str(e)}", 'warning')
        return []
    
    def save_closed_trade(self, trade_data):
        """Guarda un trade cerrado para reentrenamiento posterior"""
        try:
            history = self.load_trades_history()
            history.append({
                'timestamp': datetime.now().isoformat(),
                'profit_loss': trade_data.get('profit', 0),
                'direction': trade_data.get('direction', 'UNKNOWN'),
                'entry_rsi': trade_data.get('entry_rsi', 50),
                'entry_momentum': trade_data.get('entry_momentum', 0),
                'entry_macd': trade_data.get('entry_macd', 0),
                'exit_reason': trade_data.get('exit_reason', 'UNKNOWN'),
                'time_in_market': trade_data.get('time_in_market', 0),
                'max_drawdown': trade_data.get('max_drawdown', 0)
            })
            
            # Guardar con límite de 1000 trades más recientes
            history = history[-1000:]
            os.makedirs(self.trades_history_file.parent, exist_ok=True)
            with open(self.trades_history_file, 'w') as f:
                json.dump(history, f)
            
            self.trades_count += 1
            
            # ⭐ Reentrenar cada 50 trades
            if self.trades_count % 50 == 0:
                self.retrain_loss_predictor(history)
                self.log(f"[LOSS] Reentrenamiento #{self.trades_count // 50} completado", 'success')
        
        except Exception as e:
            self.log(f"[LOSS] Error guardando trade: {str(e)}", 'warning')
    
    def retrain_loss_predictor(self, trades_history):
        """Reentena el modelo con histórico de trades reales"""
        try:
            # ⭐ Saltar si sklearn no está disponible
            if not SKLEARN_AVAILABLE or not self.loss_predictor:
                return
            
            if len(trades_history) < 20:  # Mínimo 20 trades
                self.log("[LOSS] Datos insuficientes para reentrenamiento", 'warning')
                return
            
            training_data = []
            training_labels = []
            
            for trade in trades_history[-500:]:  # Últimos 500 trades
                # Features: entrada RSI, momentum, MACD, drawdown, tiempo en mercado
                features = [
                    trade.get('entry_rsi', 50),
                    trade.get('entry_momentum', 0),
                    trade.get('entry_macd', 0),
                    trade.get('max_drawdown', 0),
                    trade.get('time_in_market', 0)
                ]
                
                # Label: ¿Se debería haber cerrado antes? (1=sí, 0=no)
                profit = trade.get('profit_loss', 0)
                label = 1 if profit < -3.0 else 0  # Si pérdida > $3, debería haber cerrado
                
                training_data.append(features)
                training_labels.append(label)
            
            if len(training_data) < 10:
                return
            
            # Entrenar modelo
            X = np.array(training_data)
            y = np.array(training_labels)
            
            try:
                self.loss_predictor.fit(X, y)
                self.model_trained = True
                accuracy = self.loss_predictor.score(X, y)
                self.log(f"[LOSS] Modelo entrenado con accuracy: {accuracy:.2%}", 'success')
            except Exception as e:
                self.log(f"[LOSS] Error en entrenamiento ML: {str(e)}", 'warning')
        
        except Exception as e:
            self.log(f"[LOSS] Error en reentrenamiento: {str(e)}", 'warning')

    def analyze_position(self, symbol, position, tracking_info):
        """Analiza una posición usando múltiples indicadores y ML"""
        try:
            # Obtener datos históricos
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
            if rates is None:
                return None

            # Convertir a numpy arrays (acceso seguro)
            close = np.array([float(rate['close']) if isinstance(rate, dict) else float(rate[4]) for rate in rates])
            high = np.array([float(rate['high']) if isinstance(rate, dict) else float(rate[2]) for rate in rates])
            low = np.array([float(rate['low']) if isinstance(rate, dict) else float(rate[3]) for rate in rates])
            volume = np.array([float(rate.get('tick_volume') if isinstance(rate, dict) else rate[5]) for rate in rates])

            # Calcular features
            features = {
                'rsi': self._calculate_rsi(close),
                'momentum': self._calculate_momentum(close),
                'macd': self._calculate_macd(close),
                'bollinger': self._calculate_bollinger(close),
                'volume_trend': self._calculate_volume_trend(volume),
                'adx': self._calculate_adx(high, low, close),
                'volatility': self._calculate_volatility(close)
            }

            # Normalizar features
            normalized_features = {}
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    normalized_features[key] = value
                elif isinstance(value, np.ndarray):
                    normalized_features[key] = value[-1]

            # Calcular score ponderado
            score = self._calculate_weighted_score(normalized_features)

            # Analizar tendencia actual
            trend = self._analyze_current_trend(close)
            
            # Analizar patrón de precio
            pattern = self._analyze_price_pattern(close)
            
            # ⭐ NUEVO: Predicción anticipada de pérdidas (ML)
            anticipate_loss = self._predict_loss_anticipation(features, position, tracking_info)

            # Decisión final
            decision = self._make_decision(
                score=score,
                trend=trend,
                pattern=pattern,
                position=position,
                tracking_info=tracking_info,
                anticipate_loss=anticipate_loss
            )

            return {
                'score': score,
                'trend': trend,
                'pattern': pattern,
                'decision': decision,
                'features': features,
                'anticipate_loss': anticipate_loss
            }

        except Exception as e:
            self.log(f"Error en análisis de IA: {str(e)}", 'error')
            return None
    
    def _predict_loss_anticipation(self, features, position, tracking_info):
        """Predice si se debería cerrar la posición ANTES de alcanzar SL"""
        try:
            # ⭐ Retornar False si sklearn no está disponible
            if not SKLEARN_AVAILABLE or not self.model_trained:
                return False
            
            # Preparar features para predicción
            entry_rsi = tracking_info.get('entry_rsi', 50)
            entry_momentum = tracking_info.get('entry_momentum', 0)
            entry_macd = tracking_info.get('entry_macd', 0)
            max_drawdown = abs(min(0, position.profit))
            time_in_market = datetime.now().timestamp() - tracking_info.get('open_time', datetime.now().timestamp())
            
            X_pred = np.array([[entry_rsi, entry_momentum, entry_macd, max_drawdown, time_in_market]])
            
            try:
                prediction = self.loss_predictor.predict(X_pred)[0]
                confidence = self.loss_predictor.predict_proba(X_pred)[0][1]
                
                # Si el modelo predice cierre con >65% confianza Y la posición ya está en rojo
                if prediction == 1 and confidence > 0.65 and position.profit < -1:
                    self.log(f"[LOSS] ⚠️ Predicción de pérdida: {confidence:.1%} confianza → cerrar anticipadamente", 'warning')
                    return True
            except Exception:
                pass
            
            return False
        
        except Exception as e:
            self.log(f"[LOSS] Error en predicción: {str(e)}", 'warning')
            return False

    def _calculate_rsi(self, prices, period=14):
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:] = 100. - 100./(1. + rs)
        return rsi[-1]

    def _calculate_momentum(self, prices, period=14):
        return ((prices[-1] - prices[-period]) / prices[-period]) * 100

    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcula MACD usando numpy en lugar de pandas"""
        # Función para calcular EMA
        def calculate_ema(data, period):
            multiplier = 2 / (period + 1)
            ema = [data[0]]  # Primer valor es igual al precio
            for price in data[1:]:
                ema.append((price - ema[-1]) * multiplier + ema[-1])
            return np.array(ema)
        
        # Calcular EMAs
        fast_ema = calculate_ema(prices, fast)
        slow_ema = calculate_ema(prices, slow)
        
        # Calcular MACD line
        macd_line = fast_ema - slow_ema
        
        # Calcular Signal line
        signal_line = calculate_ema(macd_line, signal)
        
        # Retornar diferencia entre MACD y Signal
        return macd_line[-1] - signal_line[-1]

    def _calculate_bollinger(self, prices, period=20):
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        current = prices[-1]
        
        # Retornar posición relativa entre bandas (-1 a 1)
        return (current - sma) / (upper - sma) if current > sma else (current - sma) / (sma - lower)

    def _calculate_volume_trend(self, volume, period=14):
        return ((volume[-1] / np.mean(volume[-period:])) - 1) * 100

    def _calculate_adx(self, high, low, close, period=14):
        tr1 = np.abs(high[1:] - low[1:])
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        return np.mean(tr[-period:]) / close[-1] * 100

    def _calculate_volatility(self, prices, period=20):
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * np.sqrt(period)

    def _calculate_weighted_score(self, features):
        """Mejorar el cálculo del score con más indicadores"""
        try:
            # Pesos ajustados para cada indicador
            weights = {
                'rsi': 0.20,        # RSI tiene más peso
                'momentum': 0.15,    # Momentum importante
                'macd': 0.15,       # MACD para tendencia
                'bollinger': 0.15,  # Bandas para volatilidad
                'volume': 0.10,     # Volumen menor peso
                'adx': 0.15,        # ADX para fuerza tendencia
                'volatility': 0.10  # Volatilidad menor peso
            }
            
            score = 0
            for feature, value in features.items():
                if feature in weights:
                    # Normalizar valores
                    if feature == 'rsi':
                        # RSI más sensible
                        norm_value = min(100, max(0, abs(50 - value) * 2))
                    elif feature == 'momentum':
                        # Momentum más sensible
                        norm_value = min(100, max(0, abs(value) * 2))
                    elif feature == 'volatility':
                        # Volatilidad inversa (menor es mejor)
                        norm_value = max(0, 100 - (value * 200))
                    else:
                        # Otros indicadores
                        norm_value = min(100, max(0, abs(value) * 100))
                    
                    score += norm_value * weights[feature]
            
            return min(100, max(0, score))
            
        except Exception as e:
            print(f"Error en cálculo de score: {str(e)}")
            return 50  # Valor neutral por defecto

    def _analyze_current_trend(self, prices, short_period=5, long_period=20):
        short_ma = np.mean(prices[-short_period:])
        long_ma = np.mean(prices[-long_period:])
        
        if short_ma > long_ma * 1.001:
            return 'UP'
        elif short_ma < long_ma * 0.999:
            return 'DOWN'
        return 'LATERAL'

    def _analyze_price_pattern(self, prices, period=20):
        recent_prices = prices[-period:]
        price_direction = recent_prices[-1] - recent_prices[0]
        volatility = np.std(recent_prices)
        
        if abs(price_direction) < volatility:
            return 'CONSOLIDATION'
        elif price_direction > volatility:
            return 'UPTREND'
        return 'DOWNTREND'

    def _make_decision(self, score, trend, pattern, position, tracking_info, anticipate_loss=False):
        """Mejorada la toma de decisiones para dar más tiempo de análisis"""
        try:
            # Obtener tiempo en mercado
            time_in_market = datetime.now().timestamp() - tracking_info.get('open_time', datetime.now().timestamp())
            min_time_analysis = 180  # Mínimo 3 minutos antes de considerar cierre
            
            # ⭐ NUEVO: Si ML predice pérdida anticipada, cerrar inmediatamente
            if anticipate_loss and position.profit < -1:
                self.log(f"[LOSS] 🛡️ Cerrando por predicción ML: anticipación de pérdida", 'warning')
                return 'CLOSE_ANTICIPATE'
            
            # Si lleva menos del tiempo mínimo, mantener
            if time_in_market < min_time_analysis:
                return 'HOLD'
            
            # 1. Score crítico + tiempo mínimo
            if score >= self.thresholds['critical_score'] and time_in_market > 300:  # 5 minutos
                return 'CLOSE'
            
            # 2. Score de advertencia + condiciones adicionales
            if score >= self.thresholds['warning_score']:
                # Solo cerrar si el patrón es muy desfavorable y llevamos tiempo
                if time_in_market > 600 and (  # 10 minutos
                    (position.type == 0 and pattern == 'DOWNTREND') or
                    (position.type == 1 and pattern == 'UPTREND')
                ):
                    return 'CLOSE'
            
            # 3. Condiciones favorables - mantener más tiempo
            if (position.type == 0 and trend == 'UP') or (position.type == 1 and trend == 'DOWN'):
                return 'HOLD'
            
            # 4. Pérdida muy grande - pero con más tolerancia
            if position.profit <= self.thresholds['max_loss_quick'] and time_in_market > 900:  # 15 minutos
                return 'CLOSE'
            
            # Por defecto, mantener posición
            return 'HOLD'
            
        except Exception as e:
            self.log(f"Error en decisión: {str(e)}", 'error')
            return 'HOLD'  # Por defecto mantener
