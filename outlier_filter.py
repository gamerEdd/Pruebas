"""
OutlierFilter - Detecta y suaviza spikes anómalos
⭐ P3 Minor: Noise Filtering

Problema: Spikes puntuales (1 tick ATM) generan falsas señales
Solución: Usar filtros robustos (Kalman-like, median, IQR detection)
"""

import numpy as np
from typing import List, Tuple


class OutlierFilter:
    """Filtra outliers y ruido en datos de mercado"""
    
    def __init__(self, method='median_filter', window=5):
        """
        method: 'median_filter' | 'kalman' | 'iqr' | 'zscore'
        window: tamaño de ventana para filtrado
        """
        self.method = method
        self.window = window
        self.kalman_state = None
        self.kalman_covariance = 1.0
    
    def is_outlier_iqr(self, data, threshold=1.5):
        """
        Detecta outliers usando Interquartile Range
        
        Args:
            data: array de valores
            threshold: IQR multiplier (1.5 = standard, 1.0 = agresivo)
        
        Returns:
            array booleano (True = outlier)
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            q1 = np.percentile(data_array, 25)
            q3 = np.percentile(data_array, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            is_outlier = (data_array < lower_bound) | (data_array > upper_bound)
            
            return is_outlier
        except:
            return np.zeros(len(data), dtype=bool)
    
    def is_outlier_zscore(self, data, threshold=2.5):
        """
        Detecta outliers usando Z-Score
        
        threshold=2.5 → ~1.2% de probabilidad de falsos positivos
        threshold=3.0 → ~0.3% de probabilidad
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            mean = np.mean(data_array)
            std = np.std(data_array)
            
            if std == 0:
                return np.zeros(len(data), dtype=bool)
            
            z_scores = np.abs((data_array - mean) / std)
            is_outlier = z_scores > threshold
            
            return is_outlier
        except:
            return np.zeros(len(data), dtype=bool)
    
    def is_outlier_mad(self, data, threshold=3.0):
        """
        Detecta outliers usando Median Absolute Deviation
        Más robusto que z-score contra múltiples outliers
        
        threshold=2.5 es estándar, 3.0 es más conservador
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            median = np.median(data_array)
            mad = np.median(np.abs(data_array - median))
            
            if mad == 0:
                return np.zeros(len(data), dtype=bool)
            
            # Constant 0.6745 para escalar MAD a std
            standardized = 0.6745 * (data_array - median) / mad
            is_outlier = np.abs(standardized) > threshold
            
            return is_outlier
        except:
            return np.zeros(len(data), dtype=bool)
    
    def detect_spike(self, data, window=3, threshold_pct=5.0):
        """
        Detecta spikes (cambios abruptos)
        
        Usa: Detectar 1-candle spikes en volatilidad o precio
        
        Args:
            data: array de valores
            window: tamaño de la media móvil para comparación
            threshold_pct: porcentaje de desviación para considerar spike (default 5%)
        
        Returns:
            array booleano (True = spike detectado)
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            if len(data_array) < window + 1:
                return np.zeros(len(data_array), dtype=bool)
            
            # Media móvil de la ventana anterior
            sma = np.convolve(data_array, np.ones(window)/window, mode='same')
            
            # Diferencia porcentual
            pct_change = np.abs((data_array - sma) / sma) * 100
            
            is_spike = pct_change > threshold_pct
            
            return is_spike
        except:
            return np.zeros(len(data), dtype=bool)
    
    def filter_median(self, data):
        """
        Filtro de mediana (suaviza spikes extremos)
        Preserva características importantes mejor que media móvil
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            if len(data_array) < self.window:
                return data_array
            
            filtered = np.zeros_like(data_array)
            
            for i in range(len(data_array)):
                # Ventana centrada
                start = max(0, i - self.window // 2)
                end = min(len(data_array), i + self.window // 2 + 1)
                
                filtered[i] = np.median(data_array[start:end])
            
            return filtered
        except:
            return np.asarray(data)
    
    def filter_kalman_1d(self, data, process_noise=1e-5, measurement_noise=1e-2):
        """
        Filtro Kalman simple (1D)
        Suaviza datos mientras rastrean cambios
        
        process_noise: cuánto esperamos que el estado cambie (bajo = menos cambio)
        measurement_noise: cuán ruidosa es la medición (alto = confiar menos)
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            filtered = np.zeros_like(data_array)
            
            # Inicializar estado
            x = data_array[0]
            p = 1.0
            
            for i, z in enumerate(data_array):
                # Predict
                x_pred = x
                p_pred = p + process_noise
                
                # Update
                k = p_pred / (p_pred + measurement_noise)  # Kalman gain
                x = x_pred + k * (z - x_pred)
                p = (1 - k) * p_pred
                
                filtered[i] = x
            
            return filtered
        except:
            return np.asarray(data)
    
    def filter_data(self, data, remove_outliers=True, smooth=True):
        """
        Pipeline completo: detectar + remover/suavizar outliers
        
        Returns:
            - filtered_data: datos limpios
            - outlier_mask: dónde estaban los outliers
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            # Detectar outliers
            if self.method == 'iqr':
                outlier_mask = self.is_outlier_iqr(data_array)
            elif self.method == 'zscore':
                outlier_mask = self.is_outlier_zscore(data_array)
            elif self.method == 'mad':
                outlier_mask = self.is_outlier_mad(data_array)
            else:
                outlier_mask = np.zeros(len(data_array), dtype=bool)
            
            # Remover o remplazar outliers
            filtered_data = data_array.copy()
            
            if remove_outliers and np.any(outlier_mask):
                # Reemplazar con mediana de vecinos
                for i in np.where(outlier_mask)[0]:
                    start = max(0, i - 2)
                    end = min(len(data_array), i + 3)
                    valid_indices = np.where(~outlier_mask[start:end])[0] + start
                    
                    if len(valid_indices) > 0:
                        filtered_data[i] = np.median(filtered_data[valid_indices])
            
            # Suavizar
            if smooth:
                if self.method == 'kalman':
                    filtered_data = self.filter_kalman_1d(filtered_data)
                else:
                    filtered_data = self.filter_median(filtered_data)
            
            return filtered_data, outlier_mask
        except:
            return np.asarray(data), np.zeros(len(data), dtype=bool)
    
    def get_clean_value(self, data, use_median=True):
        """
        Retorna valor "limpio" del último dato
        Útil para obtener valor actual sin ruido
        
        Args:
            use_median: Si True, usa mediana de últimos 5 datos
                       Si False, usa último dato filtrado
        """
        try:
            filtered, _ = self.filter_data(data)
            
            if use_median and len(filtered) >= 5:
                return float(np.median(filtered[-5:]))
            else:
                return float(filtered[-1])
        except:
            return float(data[-1]) if len(data) > 0 else 0.0


# Ejemplo
if __name__ == "__main__":
    # Datos con spike
    closes = [100, 101, 99, 102, 150, 103, 104, 102, 105, 106]  # 150 es spike
    
    # Probar diferentes métodos
    for method in ['iqr', 'zscore', 'mad']:
        of = OutlierFilter(method=method, window=5)
        filtered, outliers = of.filter_data(closes)
        
        print(f"\n{method.upper()}:")
        print(f"  Original:  {closes}")
        print(f"  Filtered:  {[f'{x:.1f}' for x in filtered]}")
        print(f"  Outliers:  {outliers}")
        print(f"  Clean value: {of.get_clean_value(closes):.1f}")
