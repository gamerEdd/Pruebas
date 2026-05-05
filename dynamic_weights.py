"""
Dynamic Weights - Ajusta pesos de features según régimen de mercado
TREND: favor EMA + ATR
RANGE: favor RSI + Bollinger Bands
"""

import numpy as np


class DynamicWeights:
    """Ajusta pesos de features dinámicamente según régimen"""
    
    def __init__(self):
        # Pesos por régimen (deben sumar ~1.0)
        
        # TREND: favor tendencias (EMA, ATR, MACD)
        self.trend_weights = {
            'rsi_centered': 0.10,
            'macd_signal': 0.25,
            'atr_norm': 0.25,
            'bb_position': 0.10,
            'price_log_return': 0.15,
            'regime_indicator': 0.05,
            'cci': 0.05,
            'stochastic': 0.02,
            'williams_r': 0.02,
            'momentum': 0.01
        }
        
        # RANGE: favor reversión (RSI, Bollinger, Stochastic)
        self.range_weights = {
            'rsi_centered': 0.25,
            'macd_signal': 0.10,
            'atr_norm': 0.10,
            'bb_position': 0.25,
            'price_log_return': 0.10,
            'regime_indicator': 0.05,
            'cci': 0.08,
            'stochastic': 0.04,
            'williams_r': 0.02,
            'momentum': 0.01
        }
        
        # NEUTRAL: pesos balanceados
        self.neutral_weights = {
            'rsi_centered': 0.15,
            'macd_signal': 0.15,
            'atr_norm': 0.15,
            'bb_position': 0.15,
            'price_log_return': 0.15,
            'regime_indicator': 0.05,
            'cci': 0.07,
            'stochastic': 0.08,
            'williams_r': 0.04,
            'momentum': 0.01
        }
        
        self.current_weights = self.neutral_weights.copy()
    
    def get_weights_by_regime(self, regime):
        """
        Retorna pesos para régimen especificado
        
        regime: 'TREND', 'RANGE', o 'NEUTRAL'
        """
        if regime == 'TREND':
            self.current_weights = self.trend_weights.copy()
        elif regime == 'RANGE':
            self.current_weights = self.range_weights.copy()
        else:
            self.current_weights = self.neutral_weights.copy()
        
        return self.current_weights
    
    def apply_weights(self, features, regime='NEUTRAL'):
        """
        Aplica pesos ponderados a features
        
        features: numpy array o dict con valores de features
        regime: 'TREND', 'RANGE', o 'NEUTRAL'
        
        Retorna: weighted_score (0-100)
        """
        weights = self.get_weights_by_regime(regime)
        
        if isinstance(features, dict):
            # Si es dict, extraer valores en orden
            feature_names = list(weights.keys())
            feature_values = np.array([features.get(name, 0) for name in feature_names])
        else:
            # Si es array, asumir mismo orden que weights
            feature_values = features
        
        # Normalizar features a 0-100
        feature_values = np.clip(feature_values, 0, 100)
        
        # Aplicar pesos
        weight_values = np.array(list(weights.values()))
        weighted_score = np.sum(feature_values * weight_values)
        
        return weighted_score
    
    def get_feature_emphasize(self, regime):
        """
        Retorna qué features están enfatizados en este régimen
        
        Útil para logging/debugging
        """
        weights = self.get_weights_by_regime(regime)
        
        # Sort by weight descending
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        emphasize = {
            'top_3': sorted_weights[:3],
            'bottom_3': sorted_weights[-3:]
        }
        
        return emphasize
    
    def adjust_for_drift(self, drift_severity):
        """
        Reduce confianza en features durante drift
        
        drift_severity: PSI value (>0.2 = drift, >0.3 = strong)
        
        Retorna factor de ajuste (1.0 = normal, <1.0 = reducido)
        """
        if drift_severity < 0.2:
            return 1.0
        elif drift_severity < 0.3:
            return 0.85  # Reducir 15%
        else:
            return 0.70  # Reducir 30%
