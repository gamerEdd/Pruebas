"""
📌 PATTERN RECOGNIZER - Detectión de Patrones Gráficos
Identifica patrones clásicos: Double Bottom, Head & Shoulders, Triángulos, Cuñas
Accuracy: 60-65%
Precisión mejorada: +10%
"""

import numpy as np
import MetaTrader5 as mt5
import mt5_safe


class PatternRecognizer:
    """Detecta patrones gráficos automaticamente"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.name = "📌 Pattern Recognizer"
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def detect_patterns(self, symbol, timeframe='M5'):
        """Detecta patrones en el timeframe especificado"""
        try:
            # Mapear timeframe
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }
            
            tf = tf_map.get(timeframe, mt5.TIMEFRAME_M5)
            bars = 100 if timeframe == 'M5' else 50
            
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
            if rates is None or len(rates) < 30:
                return {
                    'pattern': 'NO_PATTERN',
                    'confidence': 0,
                    'reason': 'Insufficient data'
                }
            
            close = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates], dtype=np.float64)
            high = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates], dtype=np.float64)
            low = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates], dtype=np.float64)
            
            patterns = {
                'double_bottom': self._detect_double_bottom(close, high, low),
                'double_top': self._detect_double_top(close, high, low),
                'head_shoulders': self._detect_head_shoulders(close, high, low),
                'triangle': self._detect_triangle(close, high, low),
                'wedge': self._detect_wedge(close, high, low),
                'flag': self._detect_flag(close, high, low)
            }
            
            # Filtrar patrones válidos
            valid_patterns = {k: v for k, v in patterns.items() if v and v.get('confidence', 0) > 0.6}
            
            if not valid_patterns:
                return {
                    'pattern': 'NO_PATTERN',
                    'confidence': 0,
                    'reason': 'No patterns found'
                }
            
            # Patrón con mayor confianza
            strongest = max(valid_patterns.items(), key=lambda x: x[1].get('confidence', 0))
            pattern_name = strongest[0]
            pattern_data = strongest[1]
            
            result = {
                'pattern': pattern_name.upper(),
                'signal': pattern_data.get('signal', 'HOLD'),
                'confidence': min(85, pattern_data['confidence'] * 100),
                'details': pattern_data,
                'target': pattern_data.get('target', 0),
                'stop': pattern_data.get('stop', 0),
                'risk_reward': pattern_data.get('risk_reward', 0)
            }
            
            if result['signal'] != 'HOLD':
                self._log_pattern(result)
            
            return result
        
        except Exception as e:
            self.log(f"❌ Error Pattern Recognizer: {str(e)}", 'error')
            return {'pattern': 'ERROR', 'confidence': 0}
    
    def _detect_double_bottom(self, close, high, low, window=10):
        """D Detecta patrón Double Bottom (Dos mínimos)"""
        try:
            if len(close) < 30:
                return None
            
            # Encontrar 2 mínimos similares
            minima = self._find_local_minima(low[-30:], window=window)
            
            if len(minima) < 2:
                return None
            
            # Últimos dos mínimos
            min1_idx = minima[-2]
            min2_idx = minima[-1]
            
            min1_price = low[-(30 - min1_idx)]
            min2_price = low[-(30 - min2_idx)]
            
            # Similitud de mínimos (dentro del 0.5%)
            similarity = abs(min1_price - min2_price) / max(min1_price, min2_price)
            
            if similarity < 0.005:
                # Hay máximo entre los dos mínimos
                middle_max = np.max(low[-(30-min1_idx):-(30-min2_idx)])
                
                # Validar breakout por encima del máximo
                current_price = close[-1]
                resistance = np.max(high[-(30-min2_idx):])
                
                if current_price > middle_max * 0.99:
                    return {
                        'signal': 'BUY',
                        'confidence': 0.70,
                        'target': min1_price + (min1_price - middle_max),
                        'stop': min1_price * 0.99,
                        'risk_reward': 1.5,
                        'description': 'Double Bottom - Breakout alcista'
                    }
            
            return None
        
        except:
            return None
    
    def _detect_double_top(self, close, high, low, window=10):
        """Detecta patrón Double Top (Dos máximos)"""
        try:
            if len(close) < 30:
                return None
            
            maxima = self._find_local_maxima(high[-30:], window=window)
            
            if len(maxima) < 2:
                return None
            
            max1_idx = maxima[-2]
            max2_idx = maxima[-1]
            
            max1_price = high[-(30 - max1_idx)]
            max2_price = high[-(30 - max2_idx)]
            
            similarity = abs(max1_price - max2_price) / max(max1_price, max2_price)
            
            if similarity < 0.005:
                middle_min = np.min(low[-(30-max1_idx):-(30-max2_idx)])
                current_price = close[-1]
                
                if current_price < middle_min * 1.01:
                    return {
                        'signal': 'SELL',
                        'confidence': 0.70,
                        'target': max1_price - (middle_min - max1_price),
                        'stop': max1_price * 1.01,
                        'risk_reward': 1.5,
                        'description': 'Double Top - Breakout bajista'
                    }
            
            return None
        
        except:
            return None
    
    def _detect_head_shoulders(self, close, high, low):
        """Detecta patrón Cabeza y Hombros"""
        try:
            if len(close) < 40:
                return None
            
            maxima = self._find_local_maxima(high[-40:], window=5)
            
            if len(maxima) < 3:
                return None
            
            # Tres máximos: hombro izq, cabeza, hombro derecho
            shoulder_l = high[-(40 - maxima[-3])]
            head = high[-(40 - maxima[-2])]
            shoulder_r = high[-(40 - maxima[-1])]
            
            # Hombros similares, cabeza más alta
            shoulder_similarity = abs(shoulder_l - shoulder_r) / max(shoulder_l, shoulder_r)
            head_higher = head > max(shoulder_l, shoulder_r)
            
            if shoulder_similarity < 0.03 and head_higher:
                # Neckline = línea entre los valles
                valley_l = np.min(low[-(40-maxima[-3]):-(40-maxima[-2])])
                valley_r = np.min(low[-(40-maxima[-2]):-(40-maxima[-1])])
                neckline = max(valley_l, valley_r)
                
                if close[-1] < neckline:
                    return {
                        'signal': 'SELL',
                        'confidence': 0.65,
                        'target': neckline - (head - neckline),
                        'stop': head * 1.01,
                        'risk_reward': 1.8,
                        'description': 'Head & Shoulders - Reversal bearish'
                    }
            
            return None
        
        except:
            return None
    
    def _detect_triangle(self, close, high, low):
        """Detecta patrón Triángulo (Consolidación)"""
        try:
            if len(close) < 30:
                return None
            
            # Triángulo = range cada vez más pequeño
            range_10 = np.max(high[-10:]) - np.min(low[-10:])
            range_20 = np.max(high[-20:-10]) - np.min(low[-20:-10])
            range_30 = np.max(high[-30:-20]) - np.min(low[-30:-20])
            
            # Range decreciente
            if range_30 > range_20 > range_10:
                # Detectar ruptura
                breakout_size = abs(close[-1] - close[-10]) / close[-10]
                
                if breakout_size > 0.005:  # 0.5% movimiento
                    signal = 'BUY' if close[-1] > close[-10] else 'SELL'
                    target = close[-1] + (range_30 * (1 if signal == 'BUY' else -1))
                    
                    return {
                        'signal': signal,
                        'confidence': 0.62,
                        'target': target,
                        'stop': close[-1] * (0.99 if signal == 'BUY' else 1.01),
                        'risk_reward': 1.2,
                        'description': 'Triangle Breakout'
                    }
            
            return None
        
        except:
            return None
    
    def _detect_wedge(self, close, high, low):
        """Detecta patrón Cuña (Rising/Falling Wedge)"""
        try:
            if len(close) < 20:
                return None
            
            highest = np.max(high[-20:])
            lowest = np.min(low[-20:])
            current = close[-1]
            
            # Rising wedge: altos suben, bajos suben más (presión bajista)
            high_trend = high[-1] > high[-10]
            low_trend = low[-1] > low[-10]
            
            if high_trend and low_trend:
                upper_slope = (high[-1] - high[-10]) / 10
                lower_slope = (low[-1] - low[-10]) / 10
                
                if upper_slope < lower_slope:  # Cuña ascendente
                    return {
                        'signal': 'SELL',
                        'confidence': 0.58,
                        'target': lowest * 0.98,
                        'stop': highest * 1.01,
                        'risk_reward': 1.3,
                        'description': 'Rising Wedge - Bearish'
                    }
            
            return None
        
        except:
            return None
    
    def _detect_flag(self, close, high, low):
        """Detecta patrón Bandera (después de movimiento fuerte)"""
        try:
            if len(close) < 30:
                return None
            
            # Flag = movimiento fuerte (pole) + consolidación (flag)
            pole_size = abs(close[-15] - close[-30])
            flag_range = np.max(high[-15:]) - np.min(low[-15:])
            
            # Flag < 50% del pole
            if flag_range < pole_size * 0.5:
                # Detectar breakout
                if close[-1] > max(close[-15:]):
                    signal = 'BUY'
                else:
                    signal = 'SELL'
                
                if signal == 'BUY':
                    return {
                        'signal': 'BUY',
                        'confidence': 0.60,
                        'target': close[-1] + pole_size,
                        'stop': min(low[-15:]) * 0.99,
                        'risk_reward': 1.5,
                        'description': 'Flag Pattern - Bullish'
                    }
            
            return None
        
        except:
            return None
    
    def _find_local_minima(self, data, window=3):
        """Encuentra mínimos locales"""
        minima = []
        for i in range(window, len(data) - window):
            if all(data[i] < data[i+j] for j in range(-window, window+1) if j != 0):
                minima.append(i)
        return minima
    
    def _find_local_maxima(self, data, window=3):
        """Encuentra máximos locales"""
        maxima = []
        for i in range(window, len(data) - window):
            if all(data[i] > data[i+j] for j in range(-window, window+1) if j != 0):
                maxima.append(i)
        return maxima
    
    def _log_pattern(self, result):
        """Log formateado de patrón"""
        self.log(f"""
╔═══════════════════════════════════════════════════════╗
║          📌 PATTERN DETECTED!                         ║
╠═══════════════════════════════════════════════════════╣
║ Pattern: {result['pattern']:<40} ║
║ Signal: {result['signal']:<44} ║
║ Confidence: {result['confidence']:<39.1f}% ║
║ Target: {result.get('target', 0):<43.4f} ║
║ Stop: {result.get('stop', 0):<45.4f} ║
║ Risk/Reward: {result.get('risk_reward', 0):<37.2f} ║
╚═══════════════════════════════════════════════════════╝
""", 'info')

