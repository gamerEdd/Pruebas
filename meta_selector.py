"""
Meta Selector - Elige entre TrendModel y ReversionModel
Integra RegimeDetector, BiasMonitor, DriftDetector, DynamicWeights
"""

import numpy as np


class MetaSelector:
    """Meta-selector que integra todos los modelos especializados"""
    
    def __init__(self, regime_detector, trend_model, reversion_model, 
                 bias_monitor, drift_detector, dynamic_weights):
        self.regime_detector = regime_detector
        self.trend_model = trend_model
        self.reversion_model = reversion_model
        self.bias_monitor = bias_monitor
        self.drift_detector = drift_detector
        self.dynamic_weights = dynamic_weights
    
    def predict(self, rates_dict, features_array=None):
        """
        Predicción integrada usando régimen de mercado
        
        Retorna:
        - {
            'prob_buy': float (0-1),
            'prob_sell': float (0-1),
            'recommendation': 'BUY'|'SELL'|'HOLD',
            'confidence': float (0-100),
            'regime': str,
            'model_used': str,
            'bias_adjusted': bool,
            'drift_warned': bool,
            'position_size_modifier': float
          }
        """
        
        result = {
            'prob_buy': 0.5,
            'prob_sell': 0.5,
            'recommendation': 'HOLD',
            'confidence': 0,
            'regime': 'UNKNOWN',
            'model_used': 'NONE',
            'bias_adjusted': False,
            'drift_warned': False,
            'position_size_modifier': 1.0
        }
        
        # 1. Detectar régimen
        regime, strength, adx, ema_trend = self.regime_detector.detect(rates_dict)
        result['regime'] = regime
        
        # 2. Elegir modelo basado en régimen
        if regime == 'TREND':
            if self.trend_model.should_activate(adx, positive_trend=ema_trend > 0):
                prob_buy, prob_sell = self.trend_model.predict(features_array)
                result['model_used'] = 'TrendModel'
                confidence_mult = self.trend_model.get_confidence_multiplier(adx)
            else:
                prob_buy, prob_sell = self.reversion_model.predict(features_array)
                result['model_used'] = 'ReversionModel'
                confidence_mult = 1.0
        elif regime == 'RANGE':
            if self.reversion_model.should_activate(adx, rsi=0, price_near_band=False):
                prob_buy, prob_sell = self.reversion_model.predict(features_array)
                result['model_used'] = 'ReversionModel'
                confidence_mult = 1.0
            else:
                prob_buy, prob_sell = self.trend_model.predict(features_array)
                result['model_used'] = 'TrendModel'
                confidence_mult = 1.0
        else:
            # NEUTRAL: usar promedio
            prob_buy_t, prob_sell_t = self.trend_model.predict(features_array)
            prob_buy_r, prob_sell_r = self.reversion_model.predict(features_array)
            
            prob_buy = (prob_buy_t + prob_buy_r) / 2.0
            prob_sell = (prob_sell_t + prob_sell_r) / 2.0
            result['model_used'] = 'HybridAverage'
            confidence_mult = 0.95
        
        # Validar
        if prob_buy is None or prob_sell is None:
            prob_buy = prob_sell = 0.5
        
        result['prob_buy'] = prob_buy
        result['prob_sell'] = prob_sell
        
        # 3. Verificar sesgo (NIVEL 5)
        has_bias, bias_adjustment, new_threshold_buy = self.bias_monitor.check_bias()
        result['bias_adjusted'] = has_bias
        
        if has_bias:
            # Aumentar threshold en caso de sesgo BUY
            threshold_buy = new_threshold_buy
            confidence_mult *= bias_adjustment  # Reducir confianza
        else:
            threshold_buy = self.bias_monitor.current_threshold_buy
        
        threshold_sell = 1.0 - threshold_buy
        
        # 4. Detectar drift (NIVEL 6)
        has_drift, drift_severity, drift_features = self.drift_detector.detect_drift()
        result['drift_warned'] = has_drift
        
        if has_drift:
            # Reducir tamaño de posición
            risk_adj = self.drift_detector.get_risk_adjustment()
            result['position_size_modifier'] = risk_adj
            confidence_mult *= 0.9  # Reducir confianza en drift
        
        # 5. Aplicar pesos dinámicos
        weighted_score = self.dynamic_weights.apply_weights(
            {'prob_buy': prob_buy * 100, 'adx': adx},
            regime=regime
        )
        
        # 6. Hacer decisión con NIVEL 4 elegado
        confidence = min(abs(prob_buy - prob_sell) * 100, 100)
        confidence *= confidence_mult
        confidence = np.clip(confidence, 0, 100)
        
        if prob_buy > threshold_buy:
            result['recommendation'] = 'BUY'
            result['confidence'] = confidence
        elif prob_sell > (1.0 - threshold_buy):
            result['recommendation'] = 'SELL'
            result['confidence'] = confidence
        else:
            result['recommendation'] = 'HOLD'
            result['confidence'] = 0
        
        return result
    
    def record_trade(self, recommendation):
        """Registra trade ejecutado para BiasMonitor"""
        self.bias_monitor.add_prediction(
            prob_buy=0,  # Será actualizado
            prob_sell=0,
            executed_trade=recommendation
        )
    
    def get_system_status(self):
        """Retorna estado completo del sistema"""
        bias_stats = self.bias_monitor.get_stats()
        has_drift, drift_severity, drift_features = self.drift_detector.detect_drift()
        
        return {
            'bias_stats': bias_stats,
            'drift_detected': has_drift,
            'drift_severity': drift_severity,
            'drift_features': drift_features,
            'position_size_modifier': self.drift_detector.get_risk_adjustment()
        }
