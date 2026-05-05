"""
Regime Detector - Identifica mercado TREND vs RANGE
"""

import numpy as np
from collections import deque


class RegimeDetector:
    """Detecta regimen de mercado"""
    
    def __init__(self, adx_period=14, ema_fast=50, ema_slow=200):
        self.adx_period = adx_period
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.regime_history = deque(maxlen=20)
        
    def calculate_adx(self, high, low, close):
        """Calcula ADX"""
        if len(close) < self.adx_period + 1:
            return 20
        
        tr = []
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr.append(max(tr1, tr2, tr3))
        
        atr = np.mean(tr[-self.adx_period:])
        
        di_plus = []
        di_minus = []
        
        for i in range(1, len(close)):
            dm_plus = high[i] - high[i-1] if (high[i] - high[i-1]) > 0 else 0
            dm_minus = low[i-1] - low[i] if (low[i-1] - low[i]) > 0 else 0
            
            di_p = (dm_plus / atr * 100) if atr != 0 else 0
            di_m = (dm_minus / atr * 100) if atr != 0 else 0
            
            di_plus.append(di_p)
            di_minus.append(di_m)
        
        di_plus_avg = np.mean(di_plus[-self.adx_period:])
        di_minus_avg = np.mean(di_minus[-self.adx_period:])
        
        di_sum = di_plus_avg + di_minus_avg
        di_diff = abs(di_plus_avg - di_minus_avg)
        
        adx = 100 * (di_diff / di_sum) if di_sum != 0 else 20
        
        return adx
    
    def calculate_ema(self, prices, period):
        """Calcula EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        ema = [np.mean(prices[:period])]
        k = 2 / (period + 1)
        
        for i in range(period, len(prices)):
            ema.append(prices[i] * k + ema[-1] * (1 - k))
        
        return ema[-1]
    
    def detect(self, rates_dict):
        """
        Detecta regime: TREND o RANGE
        Returns: regime_name, trend_strength (0-100), adx, ema_trend
        """
        try:
            if not rates_dict or 'close' not in rates_dict:
                return "NEUTRAL", 50, 20, 0
            
            closes = rates_dict.get('close', [])
            highs = rates_dict.get('high', closes)
            lows = rates_dict.get('low', closes)
            
            if len(closes) < 201:
                return "NEUTRAL", 50, 20, 0
            
            # Convertir a numpy arrays si son listas
            closes = np.array(closes)
            highs = np.array(highs)
            lows = np.array(lows)
            
            # Calcular ADX
            adx = self.calculate_adx(highs, lows, closes)
            
            # Calcular EMAs
            ema50 = self.calculate_ema(closes, 50)
            ema200 = self.calculate_ema(closes, 200)
            
            # Calificar EMA trend
            ema_trend = 1 if ema50 > ema200 else -1
            
            # Determinar regime
            if adx > 25:
                regime = "TREND"
                strength = min(adx, 100)
            elif adx < 20:
                regime = "RANGE"
                strength = 100 - adx
            else:
                regime = "NEUTRAL"
                strength = 50
            
            self.regime_history.append({
                'regime': regime,
                'adx': adx,
                'ema50': ema50,
                'ema200': ema200,
                'ema_trend': ema_trend,
                'strength': strength
            })
            
            return regime, strength, adx, ema_trend
            
        except:
            return "NEUTRAL", 50, 20, 0
    
    def get_regime_stats(self):
        """Retorna estadisticas del regimen"""
        if not self.regime_history:
            return {"TREND": 0, "RANGE": 0, "NEUTRAL": 0}
        
        regimes = {}
        for item in self.regime_history:
            regime = item['regime']
            regimes[regime] = regimes.get(regime, 0) + 1
        
        total = len(self.regime_history)
        return {k: (v/total*100) for k, v in regimes.items()}
