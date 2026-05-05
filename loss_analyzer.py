import MetaTrader5 as mt5
import numpy as np
import mt5_safe
import time
from datetime import datetime
from loss_protection_ai import LossProtectionAI

class LossAnalyzer:
    def __init__(self, gold_analyzer, log_callback=None):
        self.gold_analyzer = gold_analyzer
        self.log_callback = log_callback
        self.perdidas = []  # Agregar esta línea
        self.tracking = {}
        self.ai_protection = LossProtectionAI()
        self.last_analysis_time = {}
        self.last_recovery_potential = {}
        self.analysis_interval = 1  # Analizar cada segundo
        self.min_analysis_time = 10  # Tiempo mínimo de análisis en segundos
        self.last_potential_log = {}  # Para trackear último potencial mostrado
        # Eliminar el valor fijo y usar el de configuración
        self.min_recovery_potential = 0.0  # Será actualizado desde la configuración del bot

        # Nuevos umbrales para análisis más preciso
        self.momentum_thresholds = {
            'strong_positive': 0.15,    # Momentum fuertemente positivo
            'moderate_positive': 0.05,  # Momentum moderadamente positivo
            'weak_positive': 0.02,      # Momentum débilmente positivo
            'strong_negative': -0.15,   # Momentum fuertemente negativo
            'moderate_negative': -0.05, # Momentum moderadamente negativo
            'weak_negative': -0.02      # Momentum débilmente negativo
        }
        self.volatility_thresholds = {
            'very_low': 0.1,    # Volatilidad muy baja
            'low': 0.2,         # Volatilidad baja
            'moderate': 0.3,    # Volatilidad moderada
            'high': 0.4         # Volatilidad alta
        }

    def analyze_red_position(self, position, tracking_info):
        """Analiza una posición en rojo. ⭐ DESACTIVADO: No cierra por potencial bajo."""
        try:
            tiempo_actual = time.time()
            tiempo_abierta = tiempo_actual - tracking_info.get('open_time', tiempo_actual)
            
            # Obtener datos para análisis (solo para logging)
            try:
                rates = mt5.copy_rates_from_pos(position.symbol, mt5.TIMEFRAME_M1, 0, 100)
                if rates is not None:
                    close = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
                    
                    # Calcular indicadores
                    momentum = self._calculate_momentum(close)
                    volatility = self._calculate_volatility(close)
                    
                    # Calcular potencial de recuperación
                    recovery_potential = self._analyze_recovery_potential(position, close, momentum, volatility)
                    
                    # NUEVO: Log SOLO del potencial (SIN CERRAR)
                    min_recovery = self.min_recovery_potential if hasattr(self, 'min_recovery_potential') else 30.0
                    
                    # ⭐ DESACTIVADO: Ya NO cierra por potencial bajo - permite que continúe abriendo
                    # Se loguea el potencial solo para información
                    if recovery_potential < min_recovery:
                        self.log(f"📊 Posición #{position.ticket}: Potencial {recovery_potential:.1f}% < {min_recovery:.1f}% (sin cerrar - permite seguir abriendo)", 'info')
                    
            except Exception as e:
                self.log(f"Error calculando potencial: {e}", 'error')
            
            # DESACTIVADO: Ya no cierra las posiciones en rojo
            # Permite que continuen abiertas y el bot siga abriendo operaciones
            return False

        except Exception as e:
            self.log(f"Error en análisis de pérdida: {str(e)}", 'error')
            return False

    def cerrar_operacion(self, position):
        """Método mejorado para cerrar operaciones y actualizar contadores"""
        for intento in range(3):
            try:
                symbol = position.symbol
                close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": position.volume,
                    "type": close_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": position.magic,
                    "comment": "IA-Cierre-Loss",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    # Actualizar contadores del gold_analyzer de forma segura
                    if hasattr(self.gold_analyzer, 'perdidas') and position.profit < 0:
                        self.gold_analyzer.perdidas += 1
                        self.gold_analyzer.operaciones_rojas += 1
                    elif hasattr(self.gold_analyzer, 'ganadas') and position.profit > 0:
                        self.gold_analyzer.ganadas += 1
                        self.gold_analyzer.operaciones_azules += 1
                    
                    # Actualizar ganancia neta de forma segura
                    if hasattr(self.gold_analyzer, 'ganancia_neta'):
                        self.gold_analyzer.ganancia_neta = round(self.gold_analyzer.ganancia_neta + position.profit, 2)
                    
                    # Actualizar total operaciones de forma segura
                    if hasattr(self.gold_analyzer, 'total_operaciones_abiertas'):
                        self.gold_analyzer.total_operaciones_abiertas = max(0, self.gold_analyzer.total_operaciones_abiertas - 1)
                    
                    # Eliminar de tracking si existe
                    if hasattr(self.gold_analyzer, 'position_ids') and position.ticket in self.gold_analyzer.position_ids:
                        self.gold_analyzer.position_ids.remove(position.ticket)
                    
                    # Log con detalles
                    if position.profit < 0:
                        msg = f"🔴 Operación cerrada con pérdida: #{position.ticket} | ${position.profit:.2f}"
                        tag = 'error'
                    else:
                        msg = f"✅ Operación cerrada con ganancia: #{position.ticket} | +${position.profit:.2f}"
                        tag = 'success'
                    
                    self.log(msg, tag)
                    if hasattr(self.gold_analyzer, 'ganadas'):
                        self.log(f"G/P: {self.gold_analyzer.ganadas}/{self.gold_analyzer.perdidas} | Total: ${self.gold_analyzer.ganancia_neta:.2f}", 'info')
                    
                    return True
                
                self.log(f"Intento {intento+1}: No se pudo cerrar, error {result.retcode if result else 'desconocido'}", 'warning')
                time.sleep(1)
                
            except Exception as e:
                self.log(f"Error en intento {intento+1}: {str(e)}", 'error')
                time.sleep(1)
        
        self.log("❌ No se pudo cerrar después de 3 intentos", 'error')
        return False

    def _calculate_momentum(self, prices, period=14):
        """Cálculo de momentum mejorado"""
        if len(prices) < period:
            return 0
        
        # Usar EMA para suavizar el momentum
        ema_fast = self._calculate_ema(prices[-period:], 5)
        ema_slow = self._calculate_ema(prices[-period:], period)
        
        # Calcular momentum como diferencia porcentual de EMAs
        momentum = ((ema_fast - ema_slow) / ema_slow) * 100
        return momentum

    def _calculate_ema(self, prices, period):
        """Cálculo de EMA para momentum"""
        if len(prices) < period:
            return prices[-1]
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema

    def _calculate_volatility(self, prices, period=20):
        """Cálculo de volatilidad mejorado"""
        if len(prices) < period:
            return 0
            
        # Usar True Range para mejor medida de volatilidad
        tr_sum = 0
        for i in range(1, len(prices)):
            high = max(prices[i], prices[i-1])
            low = min(prices[i], prices[i-1])
            tr = high - low
            tr_sum += tr
            
        atr = tr_sum / period
        return (atr / prices[-1]) * 100  # Retornar como porcentaje

    def _analyze_recovery_potential(self, position, prices, momentum, volatility):
        """Análisis de recuperación mejorado con más precisión"""
        try:
            recovery_score = 0
            
            # 1. Análisis de tendencia más detallado (30 puntos max)
            short_trend = (prices[-1] - prices[-10]) / prices[-10] * 100
            mid_trend = (prices[-1] - prices[-20]) / prices[-20] * 100
            long_trend = (prices[-1] - prices[-50]) / prices[-50] * 100  # Nuevo: tendencia larga
            
            if position.type == mt5.POSITION_TYPE_BUY:
                # Análisis de tendencia para compras
                if short_trend > 0.1: recovery_score += 10
                if mid_trend > 0.15: recovery_score += 10
                if long_trend > 0.2: recovery_score += 10
            else:
                # Análisis de tendencia para ventas
                if short_trend < -0.1: recovery_score += 10
                if mid_trend < -0.15: recovery_score += 10
                if long_trend < -0.2: recovery_score += 10
            
            # 2. Momentum más preciso (35 puntos max)
            if position.type == mt5.POSITION_TYPE_BUY:
                if momentum >= self.momentum_thresholds['strong_positive']:
                    recovery_score += 35
                elif momentum >= self.momentum_thresholds['moderate_positive']:
                    recovery_score += 25
                elif momentum >= self.momentum_thresholds['weak_positive']:
                    recovery_score += 15
            else:
                if momentum <= self.momentum_thresholds['strong_negative']:
                    recovery_score += 35
                elif momentum <= self.momentum_thresholds['moderate_negative']:
                    recovery_score += 25
                elif momentum <= self.momentum_thresholds['weak_negative']:
                    recovery_score += 15
            
            # 3. Volatilidad como factor (20 puntos max)
            if volatility < self.volatility_thresholds['very_low']:
                recovery_score += 20        # Volatilidad ideal
            elif volatility < self.volatility_thresholds['low']:
                recovery_score += 15        # Volatilidad buena
            elif volatility < self.volatility_thresholds['moderate']:
                recovery_score += 10        # Volatilidad aceptable
            elif volatility >= self.volatility_thresholds['high']:
                recovery_score -= 10        # Penalización por alta volatilidad
            
            # 4. Profundidad de pérdida (15 puntos max)
            loss_percent = abs(position.profit / position.price_open * 100)
            if loss_percent < 0.2:
                recovery_score += 15
            elif loss_percent < 0.4:
                recovery_score += 10
            elif loss_percent < 0.6:
                recovery_score += 5
            
            # Multiplicador por condiciones favorables
            if ((position.type == mt5.POSITION_TYPE_BUY and momentum > 0 and short_trend > 0) or
                (position.type == mt5.POSITION_TYPE_SELL and momentum < 0 and short_trend < 0)):
                recovery_score *= 1.1  # 10% extra por alineación favorable
            
            # Log detallado del análisis
            self.log(f"""
📊 Análisis detallado de recuperación:
➡️ Tendencias: Corta={short_trend:.2f}% | Media={mid_trend:.2f}% | Larga={long_trend:.2f}%
💫 Momentum: {momentum:.3f}
📈 Volatilidad: {volatility:.3f}
💰 Pérdida: {loss_percent:.2f}%
🎯 Score Final: {recovery_score:.1f}
""", 'info')
            
            return min(100, recovery_score)  # Asegurar máximo de 100
            
        except Exception as e:
            self.log(f"Error en análisis de recuperación: {str(e)}", 'error')
            return 0

    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
