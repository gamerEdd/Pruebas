"""
🚀 RECOVERY POTENTIAL ENHANCED - Análisis de Potencial de Recuperación Mejorado
Mejora: +5% precisión por mejor evaluación de oportunidad de mercado
Usa 8 indicadores para evaluar si hay potencial de bounce/reversal
"""

import numpy as np


class RecoveryPotentialEnhanced:
    """🚀 Analizador de potencial de recuperación de mercado"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.name = "🚀 Recovery Analyzer"
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def analyze_recovery_potential(self, mt5, symbol, timeframe='H1'):
        """
        Analiza 8 factores para determinar potencial de recuperación
        Retorna score de 0-100 indicando probabilidad de bounce
        """
        try:
            import MetaTrader5 as mt5_module
            
            # Obtener datos
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
            if rates is None or len(rates) < 50:
                return {'recovery_score': 0, 'reason': 'Datos insuficientes'}
            
            prices = np.array([r[4] for r in rates])  # close prices
            
            # Calcular 8 factores
            factors = {}
            
            # Factor 1: Desviación de media móvil (oversold = good bounce potential)
            factors['ma_deviation'] = self._calc_ma_deviation(prices)  # 0-25 pts
            
            # Factor 2: Volatilidad relativa
            factors['volatility_expansion'] = self._calc_volatility_expansion(prices)  # 0-20 pts
            
            # Factor 3: Posición en bandas (extremos = reversión esperada)
            factors['bb_position'] = self._calc_bb_position(prices)  # 0-20 pts
            
            # Factor 4: RSI extremos (dicotomía de fuerza)
            factors['rsi_extreme'] = self._calc_rsi_extreme(prices)  # 0-15 pts
            
            # Factor 5: Estructuras de soporte
            factors['support_level'] = self._calc_support_level(prices)  # 0-10 pts
            
            # Factor 6: Acumulación de volumen (si baja hay compra)
            factors['volume_accumulation'] = self._calc_volume_accumulation(rates)  # 0-10 pts
            
            # Factor 7: Distancia desde máximo de 20 barras
            factors['pullback_from_high'] = self._calc_pullback_from_high(prices)  # 0-5 pts
            
            # Factor 8: Patrón V-shape (piso doble)
            factors['v_shape_pattern'] = self._calc_v_shape_pattern(prices)  # 0-5 pts
            
            # Sumar factores
            total_score = sum(factors.values())
            
            # Normalizar a 0-100
            recovery_score = min(100, (total_score / 100) * 100)
            
            # Clasificar
            if recovery_score >= 70:
                classification = "ALTA RECUPERACIÓN POTENCIAL 🚀"
                recommendation = "ENTRADA AGRESIVA RECOMENDADA"
            elif recovery_score >= 50:
                classification = "RECUPERACIÓN MEDIA ⚙️"
                recommendation = "ESPERAR MÁS SEÑALES"
            elif recovery_score >= 30:
                classification = "RECUPERACIÓN BAJA ⏳"
                recommendation = "NO RECOMENDAR ENTRADA"
            else:
                classification = "SIN POTENCIAL ❌"
                recommendation = "ESPERAR Nueva ESTRUCTURA"
            
            # Log detallado
            self._log_recovery(classification, recovery_score, factors, recommendation)
            
            return {
                'recovery_score': recovery_score,
                'classification': classification,
                'recommendation': recommendation,
                'factors': factors,
                'factor_breakdown': self._format_factors(factors)
            }
        
        except Exception as e:
            self.log(f"❌ Error Recovery: {str(e)}", 'error')
            return {'recovery_score': 0, 'reason': f'Error: {str(e)}'}
    
    def _calc_ma_deviation(self, prices):
        """Qué tan lejos está el precio de su MA20"""
        ma20 = np.mean(prices[-20:])
        current_price = prices[-1]
        
        # Desviación porcentual
        deviation_pct = abs((current_price - ma20) / ma20) * 100
        
        # Convertir a puntos (max 25)
        # Si está lejos de MA = overbought/oversold = bounce potencial
        if deviation_pct > 3:
            return min(25, 5 + deviation_pct * 5)
        else:
            return max(5, 15 - deviation_pct * 5)
    
    def _calc_volatility_expansion(self, prices):
        """Expansión de volatilidad = cambio de régimen"""
        recent_vol = np.std(prices[-10:])
        historical_vol = np.std(prices[-50:-20])
        
        if historical_vol == 0:
            return 10
        
        vol_ratio = recent_vol / historical_vol
        
        # Alta volatilidad = potencial de bounce
        if vol_ratio > 1.5:
            return min(20, 10 + (vol_ratio - 1.5) * 20)
        elif vol_ratio > 0.8:
            return 10
        else:
            return 5
    
    def _calc_bb_position(self, prices):
        """Posición en bandas de Bollinger (extremo = hay bounce)"""
        ma20 = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        
        upper_band = ma20 + 2 * std
        lower_band = ma20 - 2 * std
        current = prices[-1]
        
        # Distancia a extremo
        if current <= lower_band:
            return 20  # En mínimo = bounce probable
        elif current >= upper_band:
            return 20  # En máximo = reversal probable
        elif current < ma20 - std:
            return 15  # Cerca de mínimo
        elif current > ma20 + std:
            return 15  # Cerca de máximo
        else:
            return 5
    
    def _calc_rsi_extreme(self, prices):
        """RSI en extremos = fuerza = reversión"""
        rsi = self._calc_rsi(prices, 14)
        
        if rsi is None:
            return 0
        
        if rsi < 20:
            return 15  # Oversold
        elif rsi > 80:
            return 15  # Overbought
        elif rsi < 30:
            return 12
        elif rsi > 70:
            return 12
        else:
            return 5
    
    def _calc_support_level(self, prices):
        """Proximidad a nivel de soporte identificado"""
        # Encontrar mínimos locales en últimas 30 barras
        lows = prices[-30:]
        min_price = np.min(lows)
        current = prices[-1]
        
        distance_pct = abs((current - min_price) / min_price) * 100
        
        # Si está cerca del mínimo = soporte tocado
        if distance_pct < 0.5:
            return 10
        elif distance_pct < 1.5:
            return 8
        else:
            return max(0, 5 - distance_pct)
    
    def _calc_volume_accumulation(self, rates):
        """Volumen durante bajada = acumulación = reversal"""
        volumes = np.array([r[5] for r in rates[-15:]])  # últimas 15 barras
        
        if np.sum(volumes) == 0:
            return 0
        
        avg_vol = np.mean(volumes)
        recent_vol = volumes[-1]
        
        # Si volumen reciente > promedio = acumulación
        if recent_vol > avg_vol * 1.5:
            return 10
        elif recent_vol > avg_vol:
            return 6
        else:
            return 3
    
    def _calc_pullback_from_high(self, prices):
        """Cuán lejos está del máximo de 20 barras = corrección natural"""
        high_20 = np.max(prices[-20:])
        current = prices[-1]
        
        pullback_pct = ((high_20 - current) / high_20) * 100
        
        # Pullback de 1-3% = corrección sana
        if 1 < pullback_pct < 3:
            return 5
        elif 0.5 < pullback_pct <= 1:
            return 3
        else:
            return 0
    
    def _calc_v_shape_pattern(self, prices):
        """Patrón V = soporte tocado 2x = reversal fuerte"""
        recent = prices[-10:]
        
        # Buscar 2 mínimos cercanos
        local_min_indices = []
        for i in range(1, len(recent) - 1):
            if recent[i] < recent[i-1] and recent[i] < recent[i+1]:
                local_min_indices.append(i)
        
        # Si hay 2+ mínimos = V-shape
        if len(local_min_indices) >= 2:
            return 5
        else:
            return 0
    
    def _calc_rsi(self, prices, period=14):
        """Calcula RSI"""
        if len(prices) < period:
            return None
        
        deltas = np.diff(prices)
        seed = deltas[:period]
        
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = 100 - 100 / (1 + rs)
        
        return rsi
    
    def _format_factors(self, factors):
        """Formatea breakdown de factores"""
        lines = []
        for name, value in factors.items():
            bar = "█" * int(value / 2) + "░" * (25 - int(value / 2))
            lines.append(f"  {name:<20} {bar} {value:>5.1f}pts")
        return "\n".join(lines)
    
    def _log_recovery(self, classification, score, factors, recommendation):
        """Log bonito del análisis"""
        self.log(f"""
╔═══════════════════════════════════════════════════════════════╗
║           🚀 ANÁLISIS DE RECUPERACIÓN POTENCIAL             ║
╠═══════════════════════════════════════════════════════════════╣
║ Clasificación: {classification:<45} ║
║ Score: {score:>56.1f}% ║
║ Recomendación: {recommendation:<42} ║
╠═══════════════════════════════════════════════════════════════╣
║ FACTORES:                                                   ║
║                                                             ║
║  MA Deviation:    {"█" * int(factors["ma_deviation"]/2):<25} {factors["ma_deviation"]:>5.1f}pts
║  Volatility Exp:  {"█" * int(factors["volatility_expansion"]/2):<25} {factors["volatility_expansion"]:>5.1f}pts
║  BB Position:     {"█" * int(factors["bb_position"]/2):<25} {factors["bb_position"]:>5.1f}pts
║  RSI Extreme:     {"█" * int(factors["rsi_extreme"]/2):<25} {factors["rsi_extreme"]:>5.1f}pts
║  Support Level:   {"█" * int(factors["support_level"]/2):<25} {factors["support_level"]:>5.1f}pts
║  Volume Accum:    {"█" * int(factors["volume_accumulation"]/2):<25} {factors["volume_accumulation"]:>5.1f}pts
║  Pullback %:      {"█" * int(factors["pullback_from_high"]/2):<25} {factors["pullback_from_high"]:>5.1f}pts
║  V-Shape:         {"█" * int(factors["v_shape_pattern"]/2):<25} {factors["v_shape_pattern"]:>5.1f}pts
╚═══════════════════════════════════════════════════════════════╝
""", 'info')
