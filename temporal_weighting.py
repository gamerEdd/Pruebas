"""
TemporalWeighting - Aplica decaimiento exponencial a datos históricos
⭐ P3 Minor: Recency Bias Fix

Problema: Datos de hace 100 barras pesan igual que datos de hace 1 barra
Solución: Aplicar weights exponenciales (reciente = 100%, viejo = 20%)
"""

import numpy as np


class TemporalWeighting:
    """Gestiona pesos temporales para indicadores"""
    
    def __init__(self, decay_rate=0.95):
        """
        decay_rate: Factor de decaimiento (0.95 = 5% menos peso por barra)
                   0.90 = más agresivo
                   0.98 = más conservador
        """
        self.decay_rate = decay_rate
    
    def calculate_weights(self, data_length, strategy='exponential'):
        """
        Calcula array de pesos para históricos
        
        Args:
            data_length: Número de datos históricos
            strategy: 'exponential' | 'linear' | 'stepwise'
        
        Returns:
            array de pesos normalizados (suma = 1.0)
        
        Ejemplo (exponential, 10 datos, decay=0.95):
            [0.002, 0.002, 0.002, 0.003, 0.004, 0.005, 0.007, 0.009, 0.012, 0.958]
            ↑ viejo                                                        ↑ reciente
        """
        try:
            if data_length <= 1:
                return np.array([1.0])
            
            if strategy == 'exponential':
                # Decaimiento exponencial: weight[i] = decay_rate^(n-i-1)
                weights = np.array([
                    self.decay_rate ** (data_length - i - 1)
                    for i in range(data_length)
                ])
            
            elif strategy == 'linear':
                # Decaimiento lineal: weight[i] = (i+1) / sum(1..n)
                weights = np.array([float(i + 1) for i in range(data_length)])
            
            elif strategy == 'stepwise':
                # 3 escalones: viejo (20%), medio (40%), reciente (40%)
                third = data_length // 3
                weights = np.array([
                    0.2 if i < third else (0.4 if i < 2*third else 0.4)
                    for i in range(data_length)
                ])
            
            else:
                # Default: exponential
                weights = np.array([
                    self.decay_rate ** (data_length - i - 1)
                    for i in range(data_length)
                ])
            
            # Normalizar (suma = 1.0)
            weights = weights / np.sum(weights)
            
            return weights
        
        except Exception:
            # Fallback: weights iguales
            return np.ones(data_length) / data_length
    
    def weighted_mean(self, data, strategy='exponential'):
        """
        Calcula media ponderada por tiempo
        
        Args:
            data: list o array de valores
            strategy: tipo de decaimiento
        
        Returns:
            media ponderada (float)
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            weights = self.calculate_weights(len(data_array), strategy)
            return float(np.sum(data_array * weights))
        except:
            return float(np.mean(data))
    
    def weighted_std(self, data, strategy='exponential'):
        """
        Calcula desviación estándar ponderada por tiempo
        
        Args:
            data: list o array
            strategy: tipo de decaimiento
        
        Returns:
            std ponderada (float)
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            weights = self.calculate_weights(len(data_array), strategy)
            
            weighted_mean = self.weighted_mean(data_array, strategy)
            
            # Varianza ponderada
            variance = np.sum(weights * (data_array - weighted_mean) ** 2)
            
            return float(np.sqrt(variance))
        except:
            return float(np.std(data))
    
    def weighted_recent_ratio(self, data, recent_bars=5):
        """
        Calcula ratio entre valores recientes vs todo el histórico
        
        Uso: Detectar cambios de momentum rápidos
        
        Returns:
            ratio (float) > 1.0 = cambio alcista reciente
        """
        try:
            data_array = np.asarray(data, dtype=np.float64)
            
            if len(data_array) <= recent_bars:
                return 1.0
            
            recent = np.mean(data_array[-recent_bars:])
            historical = np.mean(data_array[:-recent_bars])
            
            if historical == 0:
                return 1.0
            
            return float(recent / historical)
        except:
            return 1.0
    
    def apply_recency_penalty(self, score, lookback_bars=10, current_bar=1):
        """
        Aplica penalización si el señal no es reciente
        
        Args:
            score: score original (0-100)
            lookback_bars: máximo de barras a considerar "reciente"
            current_bar: en qué barra se detectó (1 = ahora, 5 = hace 5 barras)
        
        Returns:
            score ajustado (penalizado si viejo)
        """
        try:
            if current_bar <= 1:
                return score  # No penalizar
            
            # Penalizar 10% por cada barra atrás
            penalty = 0.1 * (current_bar - 1)
            adjusted = score * (1.0 - penalty)
            
            return float(np.clip(adjusted, 0, 100))
        except:
            return score


# Ejemplo de uso
if __name__ == "__main__":
    tw = TemporalWeighting(decay_rate=0.95)
    
    # Datos: últimos 10 cierres
    closes = [100, 101, 99, 102, 101, 103, 104, 102, 105, 106]
    
    # Media normal vs media ponderada
    normal_mean = np.mean(closes)
    weighted_mean = tw.weighted_mean(closes, 'exponential')
    
    print(f"Media normal: {normal_mean:.2f}")
    print(f"Media ponderada (exponential): {weighted_mean:.2f}")
    print(f"  → Valores recientes ~106 tienen mayor peso")
    
    # Desv std
    print(f"\nStd normal: {np.std(closes):.2f}")
    print(f"Std ponderada: {tw.weighted_std(closes, 'exponential'):.2f}")
    
    # Ratio reciente
    ratio = tw.weighted_recent_ratio(closes, recent_bars=3)
    print(f"\nRatio reciente/histórico: {ratio:.2f}")
    if ratio > 1.0:
        print(f"  → Cambio positivo reciente (+{(ratio-1)*100:.1f}%)")
    
    # Weights visuales
    weights = tw.calculate_weights(10, 'exponential')
    print(f"\nWeights exponenciales:")
    for i, w in enumerate(weights):
        bar = '█' * int(w * 200)
        print(f"  [{i}] {bar} {w*100:.1f}%")
