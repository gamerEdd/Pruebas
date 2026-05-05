"""
CandleValidator - Valida que señales ocurran en candles cerrados
⭐ P3 Minor: Closed Candle Validation

Problema: Señales sobre candles abiertos son menos confiables
Solución: Validar que el candle esté casi completamente cerrado (>95% del timeframe)
"""

from datetime import datetime, timedelta
import MetaTrader5 as mt5


class CandleValidator:
    """Valida estado y características de candles"""
    
    def __init__(self, timeframe='M1'):
        """
        timeframe: 'M1', 'M5', 'M15', 'M30', 'H1', 'D1'
        """
        self.timeframe = timeframe
        self.timeframe_minutes = self._get_timeframe_minutes(timeframe)
    
    def _get_timeframe_minutes(self, timeframe):
        """Convierte nombre de timeframe a minutos"""
        mapping = {
            'M1': 1,
            'M5': 5,
            'M15': 15,
            'M30': 30,
            'H1': 60,
            'H4': 240,
            'D1': 1440,
            'W1': 10080,
            'MN1': 43200
        }
        return mapping.get(timeframe, 1)
    
    def is_candle_closed(self, current_time, tolerance_pct=95):
        """
        Valida si el candle actual está cerrado o casi cerrado
        
        Args:
            current_time: datetime del momento actual
            tolerance_pct: porcentaje de candle transcurrido (default 95%)
        
        Returns:
            dict {
                'is_closed': bool,
                'progress_pct': % del candle completado,
                'time_remaining_sec': segundos hasta cierre,
                'recommendation': 'WAIT' | 'OK' | 'CLOSE_SOON'
            }
        """
        try:
            now = current_time if isinstance(current_time, datetime) else datetime.now()
            
            # Tiempo del candle que abrió
            minutes_since_hour = now.minute
            minutes_since_start = minutes_since_hour % self.timeframe_minutes
            
            # Progreso en porcentaje
            progress_pct = (minutes_since_start / self.timeframe_minutes) * 100
            
            # Tiempo restante
            time_remaining_sec = (self.timeframe_minutes - minutes_since_start) * 60
            time_remaining_sec -= now.second  # Restar segundos del minuto actual
            
            # Decisiones
            is_closed = progress_pct >= tolerance_pct
            
            if progress_pct < 80:
                recommendation = 'WAIT'  # Muy temprano
            elif progress_pct < tolerance_pct:
                recommendation = 'CLOSE_SOON'  # Casi cerrado
            else:
                recommendation = 'OK'  # Cerrado o casi cerrado
            
            return {
                'is_closed': is_closed,
                'progress_pct': round(progress_pct, 1),
                'time_remaining_sec': max(0, int(time_remaining_sec)),
                'recommendation': recommendation,
                'tolerance_pct': tolerance_pct
            }
        
        except Exception as e:
            return {
                'is_closed': True,
                'progress_pct': 0,
                'time_remaining_sec': 0,
                'recommendation': 'ERROR',
                'error': str(e)
            }
    
    def get_candle_boundaries(self, current_time):
        """
        Retorna hora de apertura y cierre del candle actual
        
        Returns:
            dict {
                'open_time': datetime,
                'close_time': datetime,
                'duration_minutes': int
            }
        """
        try:
            now = current_time if isinstance(current_time, datetime) else datetime.now()
            
            # Calcular inicio del candle
            minutes_since_start = now.minute % self.timeframe_minutes
            
            open_time = now.replace(
                minute=now.minute - minutes_since_start,
                second=0,
                microsecond=0
            )
            
            close_time = open_time + timedelta(minutes=self.timeframe_minutes)
            
            return {
                'open_time': open_time,
                'close_time': close_time,
                'duration_minutes': self.timeframe_minutes
            }
        except:
            return None
    
    def should_validate_signal(self, current_time, min_closed_pct=95):
        """
        Retorna True si es seguro ejecutar una señal en este momento
        
        Recomendación: Usar esto como filtro ANTES de enviar órdenes
        """
        validation = self.is_candle_closed(current_time, tolerance_pct=min_closed_pct)
        return validation['is_closed'] and validation['recommendation'] in ['OK', 'CLOSE_SOON']
    
    def get_signal_quality_by_candle_state(self, current_time):
        """
        Estima calidad de signal basada en estado del candle
        
        Returns:
            multiplicador de score (0.5 = muy temprano, 1.0 = candle cerrado)
        """
        validation = self.is_candle_closed(current_time)
        progress = validation['progress_pct']
        
        if progress < 30:
            return 0.5  # -50%
        elif progress < 60:
            return 0.7  # -30%
        elif progress < 80:
            return 0.85  # -15%
        elif progress < 95:
            return 0.95  # -5%
        else:
            return 1.0  # OK
    
    def log_candle_status(self, current_time):
        """
        Retorna string legible del estado del candle
        
        Útil para logs
        """
        validation = self.is_candle_closed(current_time)
        boundaries = self.get_candle_boundaries(current_time)
        
        progress = validation['progress_pct']
        remaining = validation['time_remaining_sec']
        
        status_icon = {
            'WAIT': '⏳',
            'CLOSE_SOON': '🟡',
            'OK': '✅',
            'ERROR': '❌'
        }.get(validation['recommendation'], '❓')
        
        return (
            f"{status_icon} [{self.timeframe}] "
            f"Progress: {progress:.0f}% | "
            f"Remaining: {remaining}s | "
            f"Closes: {boundaries['close_time'].strftime('%H:%M:%S') if boundaries else '?'}"
        )
    
    def validate_candle_integrity(self, high, low, close, open_price):
        """
        Valida que candle sea válido (sin valores imposibles)
        
        Returns:
            dict {
                'is_valid': bool,
                'issues': [list de problemas encontrados]
            }
        """
        try:
            issues = []
            
            # High debe ser >= close y open
            if high < close or high < open_price:
                issues.append("High < Close o Open")
            
            # Low debe ser <= close y open
            if low > close or low > open_price:
                issues.append("Low > Close o Open")
            
            # High >= Low siempre
            if high < low:
                issues.append("High < Low (inválido)")
            
            # OHLC ranges
            range_size = high - low
            if range_size < 0:
                issues.append("Negative range")
            
            is_valid = len(issues) == 0
            
            return {
                'is_valid': is_valid,
                'issues': issues,
                'range': range_size,
                'body': abs(close - open_price)
            }
        except Exception as e:
            return {
                'is_valid': False,
                'issues': [str(e)],
                'range': 0,
                'body': 0
            }


# Ejemplo de uso
if __name__ == "__main__":
    cv = CandleValidator(timeframe='M1')
    
    # Test en diferentes momentos
    test_times = [
        datetime.now().replace(minute=0, second=0),  # Inicio
        datetime.now().replace(minute=0, second=50),  # 50%
        datetime.now().replace(minute=0, second=55),  # 95%
    ]
    
    for test_time in test_times:
        print(f"\nTiempo: {test_time.strftime('%H:%M:%S')}")
        
        # Ajustar minuto a algo realista
        adjusted_time = test_time.replace(minute=(test_time.minute or 0))
        
        status = cv.log_candle_status(adjusted_time)
        print(f"  {status}")
        
        validation = cv.is_candle_closed(adjusted_time)
        print(f"  Recomendación: {validation['recommendation']}")
        print(f"  Quality multiplier: {cv.get_signal_quality_by_candle_state(adjusted_time):.2f}")
