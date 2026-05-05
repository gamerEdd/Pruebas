"""
MultiTimeframeAnalyzer: Carga y analiza datos de múltiples timeframes
Soporta: M1, M5, M15, M30, H1 con análisis de 500 pips en cada uno
"""

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MultiTimeframeAnalyzer:
    """Gestor central de datos multi-timeframe para especialistas"""
    
    # Mapeo de nombres a constantes MT5
    TIMEFRAMES = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
    }
    
    # Mappeo de máximo número de barras por timeframe para ~500 pips (aprox 2-3 horas de data)
    BARS_PER_TIMEFRAME = {
        'M1': 500,      # 500 minutos ≈ 8.3 horas
        'M5': 300,      # 300 × 5min = 1500 min ≈ 25 horas
        'M15': 200,     # 200 × 15min = 3000 min ≈ 50 horas
        'M30': 100,     # 100 × 30min = 3000 min ≈ 50 horas
        'H1': 50,       # 50 × 1h = 50 horas ≈ 2 días
    }
    
    def __init__(self, symbol='GOLD', log_callback=None):
        self.symbol = symbol
        self.log_callback = log_callback
        self.data_cache = {}  # {timeframe: rates}
        self.last_load_time = 0
        self.cache_ttl = 60  # segundos
        
    def log(self, msg, level='info'):
        """Log con callback opcional"""
        if self.log_callback:
            self.log_callback(msg, level)
        logger.log(getattr(logging, level.upper()), msg)
    
    def get_all_timeframes(self, force_refresh=False):
        """
        Obtiene datos de TODOS los timeframes (M1, M5, M15, M30, H1)
        
        Args:
            force_refresh: Si True, ignora cache y recarga todo
            
        Returns:
            dict: {
                'M1': rates_array,
                'M5': rates_array,
                ...
                'status': 'success'|'partial'|'failed',
                'loaded_timeframes': list de TF exitosos
            }
        """
        import time
        
        # Check cache
        now = time.time()
        if not force_refresh and (now - self.last_load_time) < self.cache_ttl:
            return self.data_cache.copy()
        
        result = {'loaded_timeframes': []}
        loaded_count = 0
        
        # Cargar cada timeframe
        for tf_name, tf_const in self.TIMEFRAMES.items():
            try:
                num_bars = self.BARS_PER_TIMEFRAME.get(tf_name, 500)
                rates = mt5.copy_rates_from_pos(
                    self.symbol,
                    tf_const,
                    0,
                    num_bars
                )
                
                if rates is not None and len(rates) > 0:
                    result[tf_name] = rates
                    result['loaded_timeframes'].append(tf_name)
                    loaded_count += 1
                    self.log(f"[MTF] {tf_name}: {len(rates)} barras cargadas", 'info')
                else:
                    self.log(f"[MTF] {tf_name}: NO DATA", 'warning')
                    
            except Exception as e:
                self.log(f"[MTF] {tf_name} ERROR: {e}", 'error')
        
        # Determinar estado
        if loaded_count == len(self.TIMEFRAMES):
            result['status'] = 'success'
        elif loaded_count > 0:
            result['status'] = 'partial'
        else:
            result['status'] = 'failed'
        
        # Cache
        self.data_cache = result.copy()
        self.last_load_time = now
        
        return result
    
    def get_price_range_all_tf(self):
        """
        Calcula el rango de precios (HIGH-LOW) en todos los timeframes
        
        Returns:
            dict: {
                'M1': {'high': X, 'low': Y, 'range_pips': Z},
                ...
            }
        """
        data = self.get_all_timeframes()
        result = {}
        
        for tf_name in self.TIMEFRAMES.keys():
            if tf_name not in data or tf_name == 'status':
                continue
                
            rates = data[tf_name]
            if len(rates) == 0:
                continue
            
            highs = np.array([r[2] for r in rates])
            lows = np.array([r[3] for r in rates])
            
            tf_high = np.max(highs)
            tf_low = np.min(lows)
            range_pips = (tf_high - tf_low) * 100  # Asume 2 decimales para oro
            
            result[tf_name] = {
                'high': tf_high,
                'low': tf_low,
                'range': range_pips
            }
        
        return result
    
    def analyze_multiple_tf(self, indicator_func):
        """
        Aplica una función de análisis a todos los timeframes
        
        Args:
            indicator_func: función(rates, tf_name) -> float (score 0-100)
            
        Returns:
            dict: {
                'M1': 75.0,
                'M5': 68.0,
                ...
                'average': 70.5,
                'strongest_tf': 'M1'
            }
        """
        data = self.get_all_timeframes()
        scores = {}
        
        for tf_name in self.TIMEFRAMES.keys():
            if tf_name not in data or data[tf_name] is None:
                continue
            
            try:
                rates = data[tf_name]
                score = indicator_func(rates, tf_name)
                scores[tf_name] = min(100, max(0, score))  # Clamp 0-100
            except Exception as e:
                self.log(f"[MTF] Error analizando {tf_name}: {e}", 'error')
        
        # Estadísticas
        if scores:
            scores['average'] = np.mean(list(scores.values()))
            scores['strongest_tf'] = max(scores.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)[0]
        
        return scores
    
    def get_consensus_signal(self, scores_dict, threshold=70):
        """
        Determina si hay consenso entre timeframes
        
        Args:
            scores_dict: dict retornado por analyze_multiple_tf()
            threshold: Score mínimo para considerar "señal fuerte"
            
        Returns:
            dict: {
                'has_consensus': bool,
                'agreement_count': int,
                'disagreement_count': int,
                'consensus_strength': 0-100 (% de TF en acuerdo)
            }
        """
        strong_signals = {}
        for tf_name, score in scores_dict.items():
            if tf_name in self.TIMEFRAMES and isinstance(score, (int, float)):
                strong_signals[tf_name] = score >= threshold
        
        if not strong_signals:
            return {'has_consensus': False, 'agreement_count': 0, 'disagreement_count': 0, 'consensus_strength': 0}
        
        agreement_count = sum(strong_signals.values())
        total_count = len(strong_signals)
        consensus_strength = (agreement_count / total_count) * 100
        
        return {
            'has_consensus': agreement_count >= (total_count * 0.6),  # 60% consenso
            'agreement_count': agreement_count,
            'disagreement_count': total_count - agreement_count,
            'consensus_strength': consensus_strength
        }
    
    def extract_ohlcv(self, rates, timeframe='M1'):
        """
        Extrae OHLCV normalized de rates
        
        Returns:
            dict: {
                'opens': numpy array,
                'highs': numpy array,
                'lows': numpy array,
                'closes': numpy array,
                'volumes': numpy array
            }
        """
        if rates is None or len(rates) == 0:
            return {
                'opens': np.array([]),
                'highs': np.array([]),
                'lows': np.array([]),
                'closes': np.array([]),
                'volumes': np.array([])
            }
        
        return {
            'opens': np.array([r[1] for r in rates], dtype=np.float64),
            'highs': np.array([r[2] for r in rates], dtype=np.float64),
            'lows': np.array([r[3] for r in rates], dtype=np.float64),
            'closes': np.array([r[4] for r in rates], dtype=np.float64),
            'volumes': np.array([r[7] for r in rates], dtype=np.float64),
        }
    
    def calculate_rsi(self, rates, period=14):
        """RSI en timeframe específico"""
        ohlcv = self.extract_ohlcv(rates)
        closes = ohlcv['closes']
        
        if len(closes) < period + 1:
            return 50
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def calculate_macd(self, rates):
        """MACD en timeframe específico"""
        ohlcv = self.extract_ohlcv(rates)
        closes = ohlcv['closes']
        
        if len(closes) < 26:
            return 0
        
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        macd = ema12[-1] - ema26[-1]
        return float(macd)
    
    @staticmethod
    def _ema(values, period):
        """Exponential Moving Average"""
        if len(values) < period:
            return values
        
        ema = np.zeros(len(values))
        ema[:period] = np.mean(values[:period])
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(values)):
            ema[i] = (values[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def get_timeframe_agreement(self, signal_type='BUY'):
        """
        Obtiene qué timeframes están de acuerdo con la dirección
        
        Args:
            signal_type: 'BUY' o 'SELL'
            
        Returns:
            dict: {
                'M1': True/False,
                'M5': True/False,
                ...
                'agreement_percentage': 0-100
            }
        """
        # Placeholder - se puede implementar con lógica más sofisticada
        return {'agreement_percentage': 80}


# Ejemplo de uso:
if __name__ == "__main__":
    mta = MultiTimeframeAnalyzer(symbol='GOLD')
    
    # Obtener todos los timeframes
    data = mta.get_all_timeframes()
    print(f"Status: {data['status']}")
    print(f"Timeframes cargados: {data['loaded_timeframes']}")
    
    # Obtener rango de precios
    ranges = mta.get_price_range_all_tf()
    for tf_name, info in ranges.items():
        print(f"{tf_name}: {info['range']:.2f} pips")
