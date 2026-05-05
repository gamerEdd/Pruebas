"""
Reversion Model - Operar SOLO en rango (ADX < 20)
Mean Reversion: compra en soporte, vende en resistencia
"""

import numpy as np
import pickle
from pathlib import Path


class ReversionModel:
    """Modelo especializado en mean reversion"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_loaded = False
        
    def load(self, model_path='logs/trained_models/xgboost_reversion.pkl',
             scaler_path='logs/trained_models/scaler_reversion.pkl'):
        """Carga modelo de reversión"""
        try:
            model_file = Path(model_path)
            scaler_file = Path(scaler_path)
            
            if model_file.exists() and scaler_file.exists():
                with open(model_file, 'rb') as f:
                    self.model = pickle.load(f)
                with open(scaler_file, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.model_loaded = True
                return True
            else:
                # Si no existe, usar XGBoost V2 balanceado como base
                base_model_path = Path('logs/trained_models/xgboost_v2_balanced.pkl')
                base_scaler_path = Path('logs/trained_models/scaler_v2_balanced.pkl')
                
                if base_model_path.exists() and base_scaler_path.exists():
                    with open(base_model_path, 'rb') as f:
                        self.model = pickle.load(f)
                    with open(base_scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)
                    self.model_loaded = True
                    return True
        except:
            pass
        
        return False
    
    def predict(self, features):
        """
        Predice probabilidad para operacion de reversión
        
        Features esperados:
        - RSI extremos (30/70)
        - Precio en Bollinger band
        - Z-score de retorno
        - Volumen decreciente
        """
        if not self.model_loaded or self.model is None:
            return None, None
        
        try:
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            # Normalizar
            features_scaled = self.scaler.transform(features)
            
            # Predecir
            prob = self.model.predict_proba(features_scaled)[0]
            
            prob_buy = prob[1]
            prob_sell = prob[0]
            
            return prob_buy, prob_sell
        except:
            return None, None
    
    def should_activate(self, adx, rsi, price_near_band):
        """Verifica si el modelo debe estar activo"""
        # Activar si tenemos rango + condiciones extremas
        if adx < 20:
            # En RANGO, mirar RSI extremos O precio en banda de Bollinger
            if (rsi < 30 or rsi > 70) or price_near_band:
                return True
        return False
    
    def get_confidence_multiplier(self, rsi, price_near_band):
        """Multiplica confianza segun intensidad de reversi贸n"""
        confidence = 1.0
        
        # RSI extremo
        if rsi < 20 or rsi > 80:
            confidence *= 1.3
        elif rsi < 30 or rsi > 70:
            confidence *= 1.1
        
        # Precio en banda
        if price_near_band:
            confidence *= 1.2
        
        return confidence
