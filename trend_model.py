"""
Trend Model - Operar SOLO en tendencia (ADX > 25)
Activacion: ADX > 25 y EMA50 > EMA200
"""

import numpy as np
import pickle
from pathlib import Path


class TrendModel:
    """Modelo especializado en trading de tendencia"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_loaded = False
        
    def load(self, model_path='logs/trained_models/xgboost_trend.pkl',
             scaler_path='logs/trained_models/scaler_trend.pkl'):
        """Carga modelo de tendencia"""
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
        Predice probabilidad para operacion en tendencia
        
        Features esperados:
        - EMA ratio (50/200)
        - RSI > 50 indicator
        - Break of structure
        - ATR expansion
        - etc
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
    
    def should_activate(self, adx, ema50, ema200):
        """Verifica si el modelo debe estar activo"""
        # Activar si tenemos fuerte tendencia
        if adx > 25 and ema50 > ema200:
            return True
        return False
    
    def get_confidence_multiplier(self, adx):
        """Multiplica confianza segun fuerza de tendencia"""
        if adx > 40:
            return 1.3  # Muy fuerte
        elif adx > 30:
            return 1.1  # Fuerte
        else:
            return 1.0  # Normal
