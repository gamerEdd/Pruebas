"""
Drift Detector - Detecta cambios de distribución usando PSI
Population Stability Index: si PSI > 0.2 hay drift
"""

import numpy as np
from collections import deque


class DriftDetector:
    """Detecta drift de distribución en features"""
    
    def __init__(self, window_size=100):
        self.window_size = window_size
        
        # Historial de features
        self.feature_history = {
            'rsi': deque(maxlen=window_size),
            'macd': deque(maxlen=window_size),
            'atr': deque(maxlen=window_size),
            'bb_pos': deque(maxlen=window_size),
            'price_return': deque(maxlen=window_size),
            'adx': deque(maxlen=window_size)
        }
        
        # Baseline (primeras 50 muestras)
        self.baseline_established = False
        self.baseline = {}
        
    def add_features(self, rsi, macd, atr, bb_pos, price_return, adx):
        """Agrega features al historial"""
        self.feature_history['rsi'].append(rsi)
        self.feature_history['macd'].append(macd)
        self.feature_history['atr'].append(atr)
        self.feature_history['bb_pos'].append(bb_pos)
        self.feature_history['price_return'].append(price_return)
        self.feature_history['adx'].append(adx)
        
        # Establecer baseline después de 50 muestras
        if not self.baseline_established and len(self.feature_history['rsi']) >= 50:
            self._establish_baseline()
    
    def _establish_baseline(self):
        """Calcula estadísticas de baseline"""
        for key in self.feature_history.keys():
            if len(self.feature_history[key]) >= 50:
                values = list(self.feature_history[key])[:50]
                self.baseline[key] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'percentiles': np.percentile(values, [10, 25, 50, 75, 90])
                }
        
        self.baseline_established = True
    
    def calculate_psi(self, feature_name='rsi', bins=10):
        """
        Calcula PSI (Population Stability Index)
        
        PSI = Σ (actual% - expected%) × ln(actual% / expected%)
        
        PSI > 0.2: hay drift
        PSI > 0.3: drift fuerte
        """
        if not self.baseline_established or feature_name not in self.feature_history:
            return 0.0
        
        history = list(self.feature_history[feature_name])
        
        if len(history) < 50:
            return 0.0
        
        # Split: primeras 50 vs últimas 50
        baseline_data = history[:50]
        current_data = history[-50:] if len(history) >= 100 else history[50:]
        
        # Crear bins
        all_data = np.concatenate([baseline_data, current_data])
        bin_edges = np.percentile(all_data, np.linspace(0, 100, bins + 1))
        bin_edges[0] = -np.inf  # Para capturar mínimos
        bin_edges[-1] = np.inf  # Para capturar máximos
        
        # Contar en cada bin
        baseline_counts = np.histogram(baseline_data, bins=bin_edges)[0]
        current_counts = np.histogram(current_data, bins=bin_edges)[0]
        
        # Normalizar
        baseline_pct = baseline_counts / np.sum(baseline_counts)
        current_pct = current_counts / np.sum(current_counts)
        
        # Evitar log(0)
        baseline_pct = np.where(baseline_pct == 0, 0.0001, baseline_pct)
        current_pct = np.where(current_pct == 0, 0.0001, current_pct)
        
        # Calcular PSI
        psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
        
        return psi
    
    def detect_drift(self):
        """
        Detecta drift en features principales
        
        Retorna:
        - (has_drift, drift_severity, drift_features)
        - has_drift: booleano si PSI > 0.2
        - drift_severity: máximo PSI detectado
        - drift_features: dict con PSI de cada feature
        """
        if not self.baseline_established:
            return False, 0.0, {}
        
        drift_features = {}
        max_psi = 0.0
        
        for feature in ['rsi', 'macd', 'atr', 'bb_pos', 'price_return', 'adx']:
            psi = self.calculate_psi(feature)
            drift_features[feature] = psi
            max_psi = max(max_psi, psi)
        
        # PSI > 0.2 es drift moderado
        # PSI > 0.3 es drift fuerte
        has_drift = max_psi > 0.2
        
        return has_drift, max_psi, drift_features
    
    def get_risk_adjustment(self):
        """
        Retorna factor de ajuste de riesgo basado en drift
        
        - Sin drift: 1.0 (sin ajuste)
        - Drift moderado (PSI 0.2-0.3): 0.8 (reducir 20%)
        - Drift fuerte (PSI > 0.3): 0.5 (reducir 50%)
        """
        has_drift, max_psi, _ = self.detect_drift()
        
        if not has_drift:
            return 1.0
        elif max_psi > 0.3:
            return 0.5
        else:
            return 0.8
    
    def reset(self):
        """Resetea el detector"""
        for key in self.feature_history.keys():
            self.feature_history[key].clear()
        self.baseline_established = False
        self.baseline = {}
