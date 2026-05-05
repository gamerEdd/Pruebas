import MetaTrader5 as mt5
import numpy as np
import mt5_safe
from datetime import datetime

class StopLossAnalyzer:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
        self.thresholds = {
            'rsi_danger': 20,          # RSI extremo
            'momentum_danger': -0.5,    # Momentum negativo fuerte
            'volatility_max': 0.3,      # Volatilidad máxima permitida
            'trend_strength': 60,       # Fuerza mínima de tendencia
            'time_in_loss': 300,        # 5 minutos en pérdida
            'max_loss_percent': 0.5     # Máxima pérdida permitida %
        }
        
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def analyze_position(self, position, initial_price):
        """Analiza una posición en pérdida y decide si cerrarla"""
        try:
            symbol = position.symbol
            current_loss = position.profit
            loss_percent = abs(current_loss / initial_price) * 100
            
            # 1. Análisis técnico rápido
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None:
                return False
                
            close_prices = np.array([float(rate['close']) if isinstance(rate, dict) else float(rate[4]) for rate in rates])
            
            # Calcular indicadores
            rsi = self._calculate_rsi(close_prices)
            momentum = self._calculate_momentum(close_prices)
            volatility = self._calculate_volatility(close_prices)
            trend_strength = self._calculate_trend_strength(close_prices)
            
            # 2. Sistema de puntuación para cierre
            close_score = 0
            reasons = []
            
            # RSI en zona extrema
            if (position.type == 0 and rsi < self.thresholds['rsi_danger']) or \
               (position.type == 1 and rsi > (100 - self.thresholds['rsi_danger'])):
                close_score += 30
                reasons.append(f"RSI extremo: {rsi:.1f}")
            
            # Momentum contrario fuerte
            if (position.type == 0 and momentum < self.thresholds['momentum_danger']) or \
               (position.type == 1 and momentum > -self.thresholds['momentum_danger']):
                close_score += 25
                reasons.append(f"Momentum contrario: {momentum:.2f}")
            
            # Volatilidad alta
            if volatility > self.thresholds['volatility_max']:
                close_score += 20
                reasons.append(f"Volatilidad alta: {volatility:.2f}")
            
            # Tendencia fuerte en contra
            if trend_strength > self.thresholds['trend_strength']:
                if (position.type == 0 and close_prices[-1] < close_prices[-10]) or \
                   (position.type == 1 and close_prices[-1] > close_prices[-10]):
                    close_score += 25
                    reasons.append(f"Tendencia fuerte en contra: {trend_strength:.1f}")
            
            # Pérdida alcanza umbral crítico
            if loss_percent > self.thresholds['max_loss_percent']:
                close_score += 35
                reasons.append(f"Pérdida crítica: {loss_percent:.2f}%")
            
            # Decisión final
            should_close = close_score >= 50
            
            if should_close:
                self.log("\n🔴 Análisis de pérdida sugiere cerrar posición:", 'warning')
                for reason in reasons:
                    self.log(f"- {reason}", 'warning')
                self.log(f"Score total: {close_score}/100", 'warning')
            
            return should_close
            
        except Exception as e:
            self.log(f"Error en análisis de pérdida: {str(e)}", 'error')
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
    
    def _calculate_momentum(self, prices, period=10):
        return ((prices[-1] - prices[-period]) / prices[-period]) * 100
    
    def _calculate_volatility(self, prices, period=20):
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * np.sqrt(period)
    
    def _calculate_trend_strength(self, prices, period=20):
        ma_fast = np.mean(prices[-period:])
        ma_slow = np.mean(prices[-period*2:-period])
        return abs((ma_fast - ma_slow) / ma_slow * 100)
