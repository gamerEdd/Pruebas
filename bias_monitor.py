"""
Bias Monitor - Detección automática de sesgo BUY
Rastrea buy_rate y mean_prob_buy, ajusta thresholds dinámicamente
"""

from collections import deque
import numpy as np


class BiasMonitor:
    """Monitorea automáticamente el sesgo BUY del sistema"""
    
    def __init__(self, check_interval=200):
        self.check_interval = check_interval  # Revisar cada N operaciones
        self.trade_counter = 0
        self.buy_counter = 0
        self.prob_buy_history = deque(maxlen=200)
        
        # Thresholds adaptativos
        self.base_threshold_buy = 0.60
        self.base_threshold_sell = 0.40
        self.current_threshold_buy = 0.60
        self.current_threshold_sell = 0.40
        
        # Límites tolerables
        self.max_buy_rate = 0.58  # Si >58% de BUY, hay sesgo
        self.max_prob_buy = 0.53  # Si prob medio >0.53, hay sesgo
        
    def add_prediction(self, prob_buy, prob_sell, executed_trade=None):
        """
        Registra una predicción
        
        executed_trade: Opcional, si se ejecutó el trade ('BUY', 'SELL', 'HOLD' o None)
        """
        self.prob_buy_history.append(prob_buy)
        
        if executed_trade == 'BUY':
            self.buy_counter += 1
            self.trade_counter += 1
        elif executed_trade == 'SELL':
            self.trade_counter += 1
    
    def check_bias(self):
        """
        Verifica sesgo después de N operaciones
        
        Retorna:
        - (has_bias, adjustment_factor, new_threshold_buy)
        - has_bias: booleano si se detectó sesgo
        - adjustment_factor: multiplicador para confianza
        - new_threshold_buy: nuevo threshold dinámico
        """
        if self.trade_counter < self.check_interval:
            return False, 1.0, self.current_threshold_buy
        
        # Calcular métricas
        buy_rate = self.buy_counter / self.trade_counter if self.trade_counter > 0 else 0.5
        mean_prob_buy = np.mean(list(self.prob_buy_history)) if self.prob_buy_history else 0.5
        
        has_bias = False
        adjustment = 1.0
        
        # Detectar sesgo excesivo
        if buy_rate > self.max_buy_rate or mean_prob_buy > self.max_prob_buy:
            has_bias = True
            
            # NIVEL 5: Ajuste dinámico de threshold
            # Si hay sesgo BUY, subir el threshold
            sesgo_intensidad = (buy_rate - 0.5) / 0.08  # Normalizar
            
            # Nuevo threshold = base + sesgo
            new_threshold = self.base_threshold_buy + (sesgo_intensidad * 0.05)
            new_threshold = min(new_threshold, 0.75)  # Máximo 75%
            
            self.current_threshold_buy = new_threshold
            self.current_threshold_sell = 1.0 - new_threshold
            
            # Reducir confianza para ser más conservador
            adjustment = 0.85
        else:
            # Sin sesgo, resetear a base
            self.current_threshold_buy = self.base_threshold_buy
            self.current_threshold_sell = self.base_threshold_sell
            adjustment = 1.0
        
        return has_bias, adjustment, self.current_threshold_buy
    
    def reset_counters(self):
        """Resetea contadores después de hacer ajuste"""
        self.trade_counter = 0
        self.buy_counter = 0
    
    def get_stats(self):
        """Retorna estadísticas actuales"""
        buy_rate = self.buy_counter / self.trade_counter if self.trade_counter > 0 else 0.0
        mean_prob_buy = np.mean(list(self.prob_buy_history)) if self.prob_buy_history else 0.0
        
        return {
            'buy_rate': buy_rate,
            'mean_prob_buy': mean_prob_buy,
            'trade_counter': self.trade_counter,
            'buy_counter': self.buy_counter,
            'current_threshold_buy': self.current_threshold_buy,
            'current_threshold_sell': self.current_threshold_sell
        }
