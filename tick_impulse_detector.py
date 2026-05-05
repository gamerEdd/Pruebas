# -*- coding: utf-8 -*-
"""
DETECTOR DE IMPULSOS DE TICK - MEJORADO V2
============================================

Sistema que detecta impulsos reales de los ticks (cambios bruscos en bid/ask y volumen)
en lugar de confiar solo en la tendencia general.

MEJORAS V2:
✓ Window size configurable (no fijo a 20)
✓ Análisis de secuencias de ticks (detecta 3+ movimientos consecutivos)
✓ Cálculo de velocidad del precio
✓ Presión bid/ask mejorada con ratio
✓ Validación final con bonus por micro-rupturas

El "impulso" es cuando hay:
1. Cambio de dirección en el precio dentro de M1
2. Volumen significativo en esa dirección
3. Velocidad del cambio (ticks por segundo)
4. Secuencias detectadas (3+ movimientos consistentes)

OBJETIVO: Validar que los impulsos de ticks coincidan con las señales de especialistas
antes de abrir posición, detectando micro-rupturas.
"""

import numpy as np
from collections import deque
from datetime import datetime, timedelta
import threading

class TickImpulseDetector:
    """Detecta impulsos reales de cada tick para validar señales de especialistas - V3 MEJORADO"""
    
    def __init__(self, window_size=20, tick_history_limit=500, 
                 min_sequence_length=3, price_velocity_threshold=0.15,
                 pressure_threshold=55, micro_breakout_size=0.8,
                 momentum_window=40, imbalance_ratio=1.22, spread_filter=1.5,
                 velocity_threshold=0.35, confirmation_count=3, 
                 signal_expiration_ms=500, min_tick_movement=2, log_callback=None):
        """
        Args:
            window_size: Número de ticks para analizar (CONFIGURABLE - default 20)
            tick_history_limit: Mantener historial de últimos N ticks
            min_sequence_length: Mínimo de movimientos consecutivos para detectar secuencia (default 3)
            price_velocity_threshold: Umbral de velocidad para bonus (0.15 = 15%)
            pressure_threshold: Umbral mínimo de presión para validar (55%)
            log_callback: Función para logging opcional - function(message, level='info')

            micro_breakout_size: Tamaño mínimo de ruptura en pips (default 0.8)
            momentum_window: Ventana para análisis de momentum (default 40)
            imbalance_ratio: Ratio de desbalance bid/ask (default 1.22)
            spread_filter: Multiplicador para filtro de spread (default 1.5)
            velocity_threshold: Umbral de velocidad del movimiento (default 0.35)
            
            ⭐ NUEVOS PARÁMETROS V4:
            confirmation_count: Número de últimos ticks para confirmar dirección (default 3)
            signal_expiration_ms: Tiempo máximo para ejecutar orden tras detectar señal en ms (default 500ms)
            min_tick_movement: Movimiento mínimo de precio en ticks para validar impulso (default 2)
        """
        self.window_size = window_size
        self.tick_history_limit = tick_history_limit
        self.min_sequence_length = min_sequence_length
        self.price_velocity_threshold = price_velocity_threshold
        self.pressure_threshold = pressure_threshold
        
        # ⭐ NUEVO V3: Parámetros de optimización para micro-impulsos
        self.micro_breakout_size = micro_breakout_size
        self.momentum_window = min(momentum_window, window_size)
        self.imbalance_ratio = imbalance_ratio
        self.spread_filter = spread_filter
        self.velocity_threshold = velocity_threshold
        
        # ⭐ NUEVO V4: Parámetros de confirmación y expiración de señal
        self.confirmation_count = confirmation_count
        self.signal_expiration_ms = signal_expiration_ms
        self.min_tick_movement = min_tick_movement
        
        # ⭐ NUEVO: Callback para logging
        self.log_callback = log_callback
        
        # Historial de ticks recientes
        self.tick_history = deque(maxlen=tick_history_limit)
        
        # Lock para acceso sincronizado
        self.lock = threading.Lock()
        
        # Estado actual
        self.current_impulse = None
        self.impulse_strength = 0.0
        self.impulse_direction = None  # 'BUY', 'SELL', None
        self.impulse_confidence = 0.0
        
        # Estadísticas
        self.last_update_time = None
        self.impulses_detected_count = 0
        self.last_sequence_detected = None
        self.last_velocity = 0.0
        
        # ⭐ NUEVO: Stats para debugging
        self.last_micro_breakout_detected = False
        self.last_velocity_filter_applied = False
        self.last_sequence_valid = False
        
        # ⭐ NUEVO V4: Timestamp de la última señal detectada (para expiración)
        self.last_signal_timestamp = None
        self.last_signal_direction = None
        
    def set_window_size(self, size):
        """Configurar dinámicamente el tamaño de la ventana de ticks"""
        if 5 <= size <= 100:
            self.window_size = size
            return True
        return False
    
    def set_pressure_threshold(self, threshold):
        """Configurar dinámicamente el umbral de presión"""
        if 0 <= threshold <= 100:
            self.pressure_threshold = threshold
            return True
        return False
    
    def _log(self, message, level='info'):
        """Helper para logging - usa callback si existe"""
        try:
            if self.log_callback:
                self.log_callback(f"[IMPULSE] {message}", level)
        except Exception:
            pass
    
    def set_min_sequence_length(self, length):
        """Configurar dinámicamente mínimo de secuencia"""
        if 2 <= length <= 20:
            self.min_sequence_length = length
            return True
        return False
    
    def set_micro_breakout_size(self, size):
        """Configurar tamaño mínimo de micro ruptura en pips"""
        if 0.1 <= size <= 10.0:
            self.micro_breakout_size = size
            return True
        return False
    
    def set_momentum_window(self, window):
        """Configurar ventana de análisis de momentum"""
        if 5 <= window <= self.window_size:
            self.momentum_window = window
            return True
        return False
    
    def set_imbalance_ratio(self, ratio):
        """Configurar ratio de desbalance bid/ask"""
        if 1.0 <= ratio <= 3.0:
            self.imbalance_ratio = ratio
            return True
        return False
    
    def set_spread_filter(self, spread_mult):
        """Configurar multiplicador de filtro de spread"""
        if 1.0 <= spread_mult <= 3.0:
            self.spread_filter = spread_mult
            return True
        return False
    
    def set_velocity_threshold(self, threshold):
        """Configurar umbral de velocidad del movimiento"""
        if 0.1 <= threshold <= 1.0:
            self.velocity_threshold = threshold
            return True
        return False
    
    def set_confirmation_count(self, count):
        """Configurar número de ticks para confirmación de dirección"""
        if 1 <= count <= 20:
            self.confirmation_count = count
            return True
        return False
    
    def set_signal_expiration_ms(self, ms):
        """Configurar tiempo de expiración de señal en milisegundos"""
        if 100 <= ms <= 5000:
            self.signal_expiration_ms = ms
            return True
        return False
    
    def set_min_tick_movement(self, count):
        """Configurar movimiento mínimo en ticks para validar impulso"""
        if 1 <= count <= 50:
            self.min_tick_movement = count
            return True
        return False
        
    def add_tick(self, timestamp, bid, ask, bid_volume, ask_volume):
        """
        Agrega un tick nuevo y detecta impulsos
        
        Args:
            timestamp: Tiempo del tick (datetime o número)
            bid: Precio bid
            ask: Precio ask (spread = ask - bid)
            bid_volume: Volumen en bid
            ask_volume: Volumen en ask
        
        Returns:
            {
                'direction': 'BUY' | 'SELL' | None,
                'strength': 0-100,
                'confidence': 0-100,
                'reason': str,
                'timestamp': datetime,
                'data': {detailed tick data}
            }
        """
        try:
            with self.lock:
                tick_data = {
                    'timestamp': timestamp,
                    'bid': float(bid),
                    'ask': float(ask),
                    'bid_volume': int(bid_volume),
                    'ask_volume': int(ask_volume),
                    'spread': float(ask) - float(bid),
                    'mid': (float(bid) + float(ask)) / 2.0
                }
                
                self.tick_history.append(tick_data)
                self.last_update_time = datetime.now()
                
                # Detectar impulso basado en los últimos N ticks
                impulse_result = self._detect_impulse_from_history()
                
                return impulse_result
        except Exception as e:
            return {
                'direction': None,
                'strength': 0,
                'confidence': 0,
                'reason': f'Error detectando impulso: {str(e)}',
                'timestamp': timestamp,
                'data': {}
            }
    
    def _check_micro_breakout(self, ticks):
        """
        ⭐ FILTRO 1: Verifica si hay micro ruptura (breakout)
        
        Calcula: max_price - min_price en la ventana de ticks
        Si < micro_breakout_size → penalización -15 puntos
        
        Returns: (penalty, detected)
        """
        if len(ticks) < 2:
            return 0, False
        
        try:
            mids = np.array([t['mid'] for t in ticks])
            price_range = np.max(mids) - np.min(mids)
            
            detected = price_range >= self.micro_breakout_size
            penalty = 0 if detected else 15
            
            self.last_micro_breakout_detected = detected
            
            # ⭐ LOGGING
            if detected:
                self._log(f"✅ Micro-ruptura DETECTADA: {price_range:.4f} pips (umbral: {self.micro_breakout_size})", 'success')
            else:
                self._log(f"⚠️ Micro-ruptura DÉBIL: {price_range:.4f} pips < {self.micro_breakout_size} (-{penalty}pts)", 'warning')
            
            return penalty, detected
        except Exception as e:
            self._log(f"❌ ERROR en _check_micro_breakout: {str(e)}", 'error')
            return 15, False
    
    def _check_velocity_filter(self, ticks):
        """
        ⭐ FILTRO 2: Verifica velocidad del movimiento
        
        velocity = (precio_actual - precio_anterior) / cantidad_ticks
        Si velocity < velocity_threshold → penalización -10 puntos
        
        Returns: (penalty, velocity_valid)
        """
        if len(ticks) < 3:
            return 0, True
        
        try:
            mids = np.array([t['mid'] for t in ticks])
            price_change = abs(mids[-1] - mids[0])
            ticks_count = max(1, len(mids) - 1)
            
            velocity = price_change / ticks_count if ticks_count > 0 else 0
            velocity_valid = velocity >= self.velocity_threshold
            penalty = 0 if velocity_valid else 10
            
            self.last_velocity = velocity
            self.last_velocity_filter_applied = (penalty > 0)
            
            # ⭐ LOGGING
            if velocity_valid:
                self._log(f"✅ Velocidad VÁLIDA: {velocity:.6f} (umbral: {self.velocity_threshold})", 'success')
            else:
                self._log(f"⚠️ Velocidad LENTA: {velocity:.6f} < {self.velocity_threshold} (-{penalty}pts)", 'warning')
            
            return penalty, velocity_valid
        except Exception as e:
            self._log(f"❌ ERROR en _check_velocity_filter: {str(e)}", 'error')
            return 10, False
    
    def _check_sequence_validity(self, ticks):
        """
        ⭐ FILTRO 3: Verifica si hay secuencia válida de ticks
        
        Cuenta movimientos consecutivos en la misma dirección
        Si secuencia < min_sequence_length → penalización -10 puntos
        
        Returns: (penalty, sequence_valid)
        """
        if len(ticks) < self.min_sequence_length:
            self._log(f"⚠️ Secuencia INSUFICIENTE: {len(ticks)} < {self.min_sequence_length} (-10pts)", 'warning')
            return 10, False
        
        try:
            mids = np.array([t['mid'] for t in ticks])
            price_changes = np.diff(mids)
            
            # Contar movimientos consecutivos
            max_sequence = 0
            current_sequence = 1
            
            for change in price_changes:
                if change > 0 or change < 0:  # Mismo signo
                    if (change * price_changes[0]) > 0:  # Mismo signo que el primero
                        current_sequence += 1
                    else:
                        max_sequence = max(max_sequence, current_sequence)
                        current_sequence = 1
            
            max_sequence = max(max_sequence, current_sequence)
            sequence_valid = max_sequence >= self.min_sequence_length
            penalty = 0 if sequence_valid else 10
            
            self.last_sequence_valid = sequence_valid
            
            # ⭐ LOGGING
            if sequence_valid:
                self._log(f"✅ Secuencia VÁLIDA: {max_sequence} movimientos consecutivos (mín: {self.min_sequence_length})", 'success')
            else:
                self._log(f"⚠️ Secuencia DÉBIL: {max_sequence} < {self.min_sequence_length} (-{penalty}pts)", 'warning')
            
            return penalty, sequence_valid
        except Exception as e:
            self._log(f"❌ ERROR en _check_sequence_validity: {str(e)}", 'error')
            return 10, False
    
    def _check_spread_imbalance(self, ticks):
        """
        ⭐ FILTRO 4 OPCIONAL: Verifica desbalance de spread
        
        Calcula ratio bid_volume / ask_volume
        Si está muy desbalanceado → puede confirmar dirección
        
        Returns: (strength_bonus, imbalance_info)
        """
        if len(ticks) < 2:
            return 0, None
        
        try:
            bid_vols = np.array([t['bid_volume'] for t in ticks])
            ask_vols = np.array([t['ask_volume'] for t in ticks])
            
            avg_bid = np.mean(bid_vols)
            avg_ask = np.mean(ask_vols)
            
            ratio = avg_bid / (avg_ask + 1e-9)
            
            # Si ratio > imbalance_ratio es fuerte presión compradora
            # Si ratio < 1/imbalance_ratio es fuerte presión vendedora
            imbalance_strength = 0
            direction = None
            
            if ratio > self.imbalance_ratio:
                imbalance_strength = min(5, ratio - 1.0)  # Bonus +5 máximo
                direction = 'BUY'
                self._log(f"✅ Desbalance BUY FUERTE: ratio {ratio:.2f} > {self.imbalance_ratio} (+{imbalance_strength:.1f}pts)", 'success')
            elif ratio < (1.0 / self.imbalance_ratio):
                imbalance_strength = min(5, (1.0 / ratio) - 1.0)
                direction = 'SELL'
                self._log(f"✅ Desbalance SELL FUERTE: ratio {ratio:.2f} < {(1.0/self.imbalance_ratio):.2f} (+{imbalance_strength:.1f}pts)", 'success')
            else:
                self._log(f"ℹ️ Desbalance NEUTRAL: ratio {ratio:.2f} (umbral: {self.imbalance_ratio})", 'info')
            
            return imbalance_strength, {'ratio': ratio, 'direction': direction}
        except Exception as e:
            self._log(f"❌ ERROR en _check_spread_imbalance: {str(e)}", 'error')
            return 0, None

    def _detect_impulse_from_history(self):
        """
        Analiza el historial reciente de ticks para detectar impulsos
        
        Un impulso es válido si:
        1. Hay divergencia consistente bid/ask (buyer pressure o seller pressure)
        2. El volumen confirma la dirección (mejorado con ratio)
        3. La velocidad es significativa (cambio en últimos N ticks)
        4. Hay secuencia detectada (3+ movimientos consecutivos)
        
        Retorna: 
            {direction, strength, confidence, reason, timestamp, data}
        """
        if len(self.tick_history) < 2:
            return {
                'direction': None,
                'strength': 0,
                'confidence': 0,
                'reason': 'Insuficientes ticks',
                'timestamp': None,
                'data': {}
            }
        
        # Usar últimos N ticks para análisis (window_size CONFIGURABLE)
        recent_ticks = list(self.tick_history)[-self.window_size:]
        
        # Análisis de presión compradora (BUY impulse)
        buy_pressure = self._calculate_buy_pressure(recent_ticks)
        
        # Análisis de presión vendedora (SELL impulse)
        sell_pressure = self._calculate_sell_pressure(recent_ticks)
        
        # ⭐ DEBUG VI: Log de PRESIONES ACTUALES
        self._log(f"[PRESSURE] buy_pressure={buy_pressure:.2f} | sell_pressure={sell_pressure:.2f} | diff={abs(buy_pressure-sell_pressure):.2f}", 'info')
        
        # Análisis de velocidad/momentum del precio
        momentum = self._calculate_momentum(recent_ticks)
        
        # ⭐ NUEVO: Detección de secuencias de ticks (micro-rupturas)
        sequence_info = self._detect_tick_sequence(recent_ticks)
        
        # ⭐ NUEVO: Cálculo de velocidad del precio
        price_velocity = self._calculate_price_velocity(recent_ticks)
        
        # ⭐ NUEVO V3: APLICAR 4 FILTROS DE OPTIMIZACIÓN
        # Filtro 1: Micro ruptura
        penalty_breakout, breakout_detected = self._check_micro_breakout(recent_ticks)
        
        # Filtro 2: Velocidad
        penalty_velocity, velocity_valid = self._check_velocity_filter(recent_ticks)
        
        # Filtro 3: Secuencia válida
        penalty_sequence, sequence_valid = self._check_sequence_validity(recent_ticks)
        
        # Filtro 4 (OPCIONAL): Desbalance de spread
        bonus_imbalance, imbalance_info = self._check_spread_imbalance(recent_ticks)
        
        # Calcular penalización total
        total_penalty = penalty_breakout + penalty_velocity + penalty_sequence
        
        # ⭐ LOGGING: Resumen de los 4 filtros aplicados
        if total_penalty > 0 or bonus_imbalance > 0:
            penalties_summary = []
            if penalty_breakout > 0:
                penalties_summary.append(f"Ruptura: -{penalty_breakout}pts")
            if penalty_velocity > 0:
                penalties_summary.append(f"Velocidad: -{penalty_velocity}pts")
            if penalty_sequence > 0:
                penalties_summary.append(f"Secuencia: -{penalty_sequence}pts")
            if bonus_imbalance > 0:
                penalties_summary.append(f"Desbalance: +{bonus_imbalance:.1f}pts")
            
            penalties_str = " | ".join(penalties_summary)
            self._log(f"📊 RESUMEN FILTROS V3: {penalties_str}", 'info')
        
        # Determinar impulso dominante
        if buy_pressure > sell_pressure:
            strength = min(100, buy_pressure)
            
            # ⭐ ORIGINAL: Bonus si hay secuencia + presión alta
            bonus = 0
            if sequence_info['direction'] == 'BUY' and buy_pressure >= self.pressure_threshold:
                bonus = min(10, sequence_info['consecutive_count'] * 2)  # +10 máximo
                strength = min(100, strength + bonus)
            
            # ⭐ NUEVO V3: Aplicar penalizaciones de filtros
            strength = max(0, strength - total_penalty)
            
            # ⭐ NUEVO V3: Añadir bonus de desbalance si va en dirección correcta
            if imbalance_info and imbalance_info.get('direction') == 'BUY':
                strength = min(100, strength + bonus_imbalance)
            
            confidence = min(100, buy_pressure * 0.8 + momentum * 0.2)
            direction = 'BUY'
            reason = f'Presión compradora {buy_pressure:.1f} + momentum {momentum:.1f}' + \
                    (f' + SECUENCIA BUY x{sequence_info["consecutive_count"]} (+{bonus}pts)' if bonus > 0 else '') + \
                    (f' (-{total_penalty}pts filtros)' if total_penalty > 0 else '')
            
            # ⭐ DEBUG LOGGING
            self._log(f"[IMPULSE-CHOICE] 🟢 BUY ELEGIDO: buy_pressure={buy_pressure:.2f} > sell_pressure={sell_pressure:.2f}", 'success')
            
        elif sell_pressure > buy_pressure:
            strength = min(100, sell_pressure)
            
            # ⭐ ORIGINAL: Bonus si hay secuencia + presión alta
            bonus = 0
            if sequence_info['direction'] == 'SELL' and sell_pressure >= self.pressure_threshold:
                bonus = min(10, sequence_info['consecutive_count'] * 2)  # +10 máximo
                strength = min(100, strength + bonus)
            
            # ⭐ NUEVO V3: Aplicar penalizaciones de filtros
            strength = max(0, strength - total_penalty)
            
            # ⭐ NUEVO V3: Añadir bonus de desbalance si va en dirección correcta
            if imbalance_info and imbalance_info.get('direction') == 'SELL':
                strength = min(100, strength + bonus_imbalance)
            
            confidence = min(100, sell_pressure * 0.8 + (100 - momentum) * 0.2)
            direction = 'SELL'
            reason = f'Presión vendedora {sell_pressure:.1f} + momentum opuesto {100-momentum:.1f}' + \
                    (f' + SECUENCIA SELL x{sequence_info["consecutive_count"]} (+{bonus}pts)' if bonus > 0 else '') + \
                    (f' (-{total_penalty}pts filtros)' if total_penalty > 0 else '')
            
            # ⭐ DEBUG LOGGING
            self._log(f"[IMPULSE-CHOICE] 🔴 SELL ELEGIDO: sell_pressure={sell_pressure:.2f} > buy_pressure={buy_pressure:.2f}", 'warning')
            
        else:
            direction = None
            strength = 0
            confidence = 0
            reason = 'Sin impulso claro (fuerzas equilibradas)'
            total_penalty = 0
            
            # ⭐ DEBUG LOGGING
            self._log(f"[IMPULSE-CHOICE] ⚪ NINGUNO: buy_pressure={buy_pressure:.2f} == sell_pressure={sell_pressure:.2f}", 'info')
        
        # Filtro: impulso debe tener confianza mínima
        MIN_CONFIDENCE_THRESHOLD = 55  # 55% como mínimo
        if confidence < MIN_CONFIDENCE_THRESHOLD and direction is not None:
            # Log pero no rechazar completamente - puede ser CAUTION
            pass
        
        result = {
            'direction': direction,
            'strength': strength,
            'confidence': confidence,
            'reason': reason,
            'timestamp': self.last_update_time,
            'data': {
                'buy_pressure': buy_pressure,
                'sell_pressure': sell_pressure,
                'momentum': momentum,
                'price_velocity': price_velocity,
                'velocity_bonus_applied': price_velocity > self.price_velocity_threshold,
                'ticks_analyzed': len(recent_ticks),
                'sequence_detected': sequence_info['detected'],
                'sequence_direction': sequence_info['direction'],
                'sequence_length': sequence_info['consecutive_count'],
                'latest_bid_volume': recent_ticks[-1]['bid_volume'],
                'latest_ask_volume': recent_ticks[-1]['ask_volume'],
                'spread': recent_ticks[-1]['spread'],
                # ⭐ NUEVO V3: Información de los 4 filtros
                'micro_breakout_detected': self.last_micro_breakout_detected,
                'micro_breakout_size': self.micro_breakout_size,
                'velocity_filter_applied': self.last_velocity_filter_applied,
                'velocity_threshold': self.velocity_threshold,
                'sequence_valid': self.last_sequence_valid,
                'min_sequence_required': self.min_sequence_length,
                'total_penalty_applied': total_penalty,
                'imbalance_info': imbalance_info
            }
        }
        
        # ⭐ NUEVO V4: VALIDACIONES ADICIONALES DE CONFIRMACIÓN Y EXPIRACIÓN
        
        # Validación 1: Confirmar últimos N ticks siguen la dirección del impulso
        if direction in ['BUY', 'SELL']:
            confirmation_valid, confirmation_reason = self._validate_recent_ticks_confirmation(
                recent_ticks, direction, self.confirmation_count
            )
            result['data']['confirmation_valid'] = confirmation_valid
            result['data']['confirmation_reason'] = confirmation_reason
            
            if not confirmation_valid:
                # Si confirmación falla, penalizar strength pero no rechazar completamente
                penalty_confirmation = 15
                result['strength'] = max(0, result['strength'] - penalty_confirmation)
                result['reason'] += f" | ⚠️ Confirmación débil (-{penalty_confirmation}pts)"
                self._log(f"⚠️ Confirmación FALLA: {confirmation_reason} (-{penalty_confirmation}pts)", 'warning')
            else:
                self._log(f"✅ Confirmación OK: {confirmation_reason}", 'success')
        
        # Validación 2: Verificar expiración de señal
        if direction in ['BUY', 'SELL']:
            signal_expired = self._check_signal_expiration(direction)
            result['data']['signal_expired'] = signal_expired
            
            if signal_expired:
                result['direction'] = None
                result['strength'] = 0
                result['confidence'] = 0
                result['reason'] = f"SE LA SEÑAL EXPIRÓ (> {self.signal_expiration_ms}ms)"
                self._log(f"❌ Señal EXPIRADA: {self.signal_expiration_ms}ms", 'error')
        
        # Validación 3: Verificar movimiento mínimo de precio
        if direction in ['BUY', 'SELL'] and result['direction'] is not None:  # Solo si no fue rechazada
            movement_valid, movement_reason = self._validate_price_movement(
                recent_ticks, self.min_tick_movement
            )
            result['data']['price_movement_valid'] = movement_valid
            result['data']['price_movement_reason'] = movement_reason
            
            if not movement_valid:
                penalty_movement = 20
                result['strength'] = max(0, result['strength'] - penalty_movement)
                result['reason'] += f" | ⚠️ Movimiento insuficiente (-{penalty_movement}pts)"
                self._log(f"⚠️ Movimiento INSUFICIENTE: {movement_reason} (-{penalty_movement}pts)", 'warning')
            else:
                self._log(f"✅ Movimiento OK: {movement_reason}", 'success')
        
        # Validación 4: Filtro de spread dinámico mejorado
        if direction in ['BUY', 'SELL'] and result['direction'] is not None:
            spread_valid, spread_reason = self._validate_dynamic_spread(recent_ticks)
            result['data']['spread_valid'] = spread_valid
            result['data']['spread_reason'] = spread_reason
            
            if not spread_valid:
                penalty_spread = 10
                result['strength'] = max(0, result['strength'] - penalty_spread)
                result['reason'] += f" | ⚠️ Spread alto (-{penalty_spread}pts)"
                self._log(f"⚠️ Spread TOO HIGH: {spread_reason} (-{penalty_spread}pts)", 'warning')
            else:
                self._log(f"✅ Spread OK: {spread_reason}", 'success')
        
        # Guardar para referencia
        self.current_impulse = result
        self.last_sequence_detected = sequence_info
        self.last_velocity = price_velocity
        
        # ⭐ NUEVO V4: Guardar timestamp y dirección de la última señal válida
        if direction in ['BUY', 'SELL'] and result['direction'] is not None:
            self.last_signal_timestamp = datetime.now()
            self.last_signal_direction = direction
        
        return result
    
    def _calculate_buy_pressure(self, ticks):
        """
        Calcula presión compradora mejorada:
        ✓ Ratio volumen bid/ask mejorado
        ✓ Cambios de precio hacia arriba
        ✓ Consistencia de dirección
        """
        if len(ticks) < 2:
            return 0
        
        try:
            # ⭐ NUEVO: Factor 1 mejorado - Ratio pressure_ratio = bid_vol / (bid_vol + ask_vol)
            bid_volumes = np.array([t['bid_volume'] for t in ticks])
            ask_volumes = np.array([t['ask_volume'] for t in ticks])
            
            total_volume = bid_volumes + ask_volumes
            pressure_ratio = np.mean(bid_volumes) / (np.mean(total_volume) + 1e-9)
            
            # Si pressure_ratio > 0.5, hay más presión compradora
            # 0.5 = neutral, 1.0 = 100% bid, 0.0 = 100% ask
            volume_factor = max(0, (pressure_ratio - 0.5) * 2)  # Escala 0 a 1
            volume_factor = volume_factor * 50  # 0-50
            
            # Factor 2: Cambios de precio hacia arriba
            mids = np.array([t['mid'] for t in ticks])
            price_changes = np.diff(mids)
            up_moves = np.sum(price_changes > 0) / len(price_changes)
            price_factor = up_moves * 30  # 0-30
            
            # Factor 3: Consistencia (últimos ticks vs primeros)
            recent_mid = np.mean(mids[-5:]) if len(mids) >= 5 else mids[-1]
            early_mid = np.mean(mids[:5]) if len(mids) >= 5 else mids[0]
            
            if early_mid > 0:
                price_improvement = ((recent_mid / early_mid) - 1.0) * 100
                consistency_factor = np.clip(price_improvement * 10, 0, 20)  # 0-20
            else:
                consistency_factor = 0
            
            buy_pressure = volume_factor + price_factor + consistency_factor
            
            # ⭐ DEBUG V1: Log del cálculo de BUY_PRESSURE
            self._log(f"[BUY-CALC] ratio={pressure_ratio:.3f} vol_factor={volume_factor:.1f} + price={price_factor:.1f} (up_moves={up_moves:.2f}) + consist={consistency_factor:.1f} = TOTAL={buy_pressure:.1f}", 'info')
            
            return np.clip(buy_pressure, 0, 100)
            
        except Exception as e:
            return 0
    
    def _calculate_sell_pressure(self, ticks):
        """
        Calcula presión vendedora mejorada:
        ✓ Ratio volumen ask/bid mejorado
        ✓ Cambios de precio hacia abajo
        ✓ Consistencia de dirección
        """
        if len(ticks) < 2:
            return 0
        
        try:
            # ⭐ NUEVO: Factor 1 mejorado - Ratio (1 - pressure_ratio)
            bid_volumes = np.array([t['bid_volume'] for t in ticks])
            ask_volumes = np.array([t['ask_volume'] for t in ticks])
            
            total_volume = bid_volumes + ask_volumes
            pressure_ratio = np.mean(bid_volumes) / (np.mean(total_volume) + 1e-9)
            
            # Si pressure_ratio < 0.5, hay más presión vendedora
            volume_factor = max(0, (0.5 - pressure_ratio) * 2)  # Escala 0 a 1
            volume_factor = volume_factor * 50  # 0-50
            
            # Factor 2: Cambios de precio hacia abajo
            mids = np.array([t['mid'] for t in ticks])
            price_changes = np.diff(mids)
            down_moves = np.sum(price_changes < 0) / len(price_changes)
            price_factor = down_moves * 30  # 0-30
            
            # Factor 3: Consistencia (últimos ticks vs primeros)
            recent_mid = np.mean(mids[-5:]) if len(mids) >= 5 else mids[-1]
            early_mid = np.mean(mids[:5]) if len(mids) >= 5 else mids[0]
            
            if early_mid > 0:
                price_degradation = (1.0 - (recent_mid / early_mid)) * 100
                consistency_factor = np.clip(price_degradation * 10, 0, 20)  # 0-20
            else:
                consistency_factor = 0
            
            sell_pressure = volume_factor + price_factor + consistency_factor
            
            # ⭐ DEBUG V2: Log del cálculo de SELL_PRESSURE
            self._log(f"[SELL-CALC] ratio={pressure_ratio:.3f} vol_factor={volume_factor:.1f} + price={price_factor:.1f} (down_moves={down_moves:.2f}) + consist={consistency_factor:.1f} = TOTAL={sell_pressure:.1f}", 'warning')
            
            return np.clip(sell_pressure, 0, 100)
            
        except Exception as e:
            return 0
    
    def _calculate_momentum(self, ticks):
        """
        Calcula momentum de los ticks (velocidad del cambio):
        Valores altos = movimiento fuerte en dirección del precio
        """
        if len(ticks) < 2:
            return 50  # Neutro
        
        try:
            mids = np.array([t['mid'] for t in ticks])
            
            # Cambio total desde inicio a fin
            total_change = mids[-1] - mids[0]
            max_change = np.max(np.abs(np.diff(mids)))
            
            if max_change > 0:
                # Ratio de cambio consistente vs cambio máximo
                consistency = abs(total_change) / max_change
                momentum = 50 + (consistency * 25)  # 50-75 para movimientos consistentes
            else:
                momentum = 50
            
            return np.clip(momentum, 0, 100)
            
        except Exception as e:
            return 50
    
    def _detect_tick_sequence(self, ticks):
        """
        ⭐ NUEVO: Detecta secuencias de ticks (micro-rupturas)
        
        Busca 3+ movimientos consecutivos en la misma dirección:
        UP UP UP → BUY sequence detected
        DOWN DOWN DOWN → SELL sequence detected
        
        Returns:
            {
                'detected': bool,
                'direction': 'BUY' | 'SELL' | None,
                'consecutive_count': int
            }
        """
        if len(ticks) < self.min_sequence_length:
            return {'detected': False, 'direction': None, 'consecutive_count': 0}
        
        try:
            mids = np.array([t['mid'] for t in ticks])
            price_changes = np.diff(mids)
            
            # Detectar secuencias de movimientos en la misma dirección
            max_up_sequence = 0
            max_down_sequence = 0
            current_up = 0
            current_down = 0
            
            for change in price_changes:
                if change > 0:  # UP
                    current_up += 1
                    current_down = 0
                    max_up_sequence = max(max_up_sequence, current_up)
                elif change < 0:  # DOWN
                    current_down += 1
                    current_up = 0
                    max_down_sequence = max(max_down_sequence, current_down)
                else:  # Sin cambio
                    current_up = 0
                    current_down = 0
            
            # Verificar si hay secuencia válida
            if max_up_sequence >= self.min_sequence_length:
                return {
                    'detected': True,
                    'direction': 'BUY',
                    'consecutive_count': max_up_sequence
                }
            elif max_down_sequence >= self.min_sequence_length:
                return {
                    'detected': True,
                    'direction': 'SELL',
                    'consecutive_count': max_down_sequence
                }
            else:
                return {'detected': False, 'direction': None, 'consecutive_count': 0}
                
        except Exception as e:
            return {'detected': False, 'direction': None, 'consecutive_count': 0}
    
    def _calculate_price_velocity(self, ticks):
        """
        ⭐ NUEVO: Calcula velocidad del precio
        
        price_velocity = abs(last_price - first_price) / tick_count
        
        Si velocidad supera umbral configurado, se aplica bonus.
        Returns: velocity value (0-1+)
        """
        if len(ticks) < 2:
            return 0.0
        
        try:
            mids = np.array([t['mid'] for t in ticks])
            
            first_price = mids[0]
            last_price = mids[-1]
            tick_count = len(ticks)
            
            if first_price > 0:
                # Velocidad como porcentaje de cambio por tick
                total_change = abs(last_price - first_price)
                price_velocity = total_change / (first_price * tick_count)
            else:
                price_velocity = 0.0
            
            return price_velocity
            
        except Exception as e:
            return 0.0
    
    def get_current_impulse(self):
        """Retorna impulso actual sin actualizar"""
        with self.lock:
            if self.current_impulse:
                return self.current_impulse.copy()
            return {
                'direction': None,
                'strength': 0,
                'confidence': 0,
                'reason': 'Sin datos de impulso',
                'timestamp': None,
                'data': {}
            }
    
    def validate_signal_alignment(self, specialist_direction, specialist_confidence, 
                                   min_alignment_threshold=60):
        """
        VALIDACIÓN CRÍTICA: Verifica si hay alineación entre impulso de tick y señal de especialista
        
        Args:
            specialist_direction: 'BUY' o 'SELL' del especialista
            specialist_confidence: 0-100 confianza del especialista
            min_alignment_threshold: Umbral mínimo de alineación (0-100)
        
        Returns:
            {
                'aligned': True|False,
                'alignment_score': 0-100,
                'impulse_direction': 'BUY'|'SELL'|None,
                'impulse_strength': 0-100,
                'conflict': str|None,
                'recommendation': 'PROCEED' | 'CAUTION' | 'REJECT'
            }
        """
        current = self.get_current_impulse()
        
        # Si no hay impulso claro, usar CAUTION
        if current['direction'] is None:
            return {
                'aligned': False,
                'alignment_score': 0,
                'impulse_direction': None,
                'impulse_strength': 0,
                'conflict': 'No hay impulso de tick detectado',
                'recommendation': 'CAUTION'
            }
        
        # Verificar si impulso y especialista coinciden en dirección
        direction_match = (current['direction'] == specialist_direction)
        
        if not direction_match:
            conflict = f"CONFLICTO: Especialista dice {specialist_direction} pero impulso es {current['direction']}"
            alignment_score = 0
            recommendation = 'REJECT'
            
        else:
            # Direcciones coinciden - calcular score de alineación
            # Combinar confianza del especialista con fuerza del impulso
            alignment_score = (specialist_confidence * 0.6 + current['strength'] * 0.4)
            
            conflict = None
            
            # Determinar recomendación basada en alignment
            if alignment_score >= min_alignment_threshold:
                recommendation = 'PROCEED'  # Verde - abierto
            else:
                recommendation = 'CAUTION'  # Amarillo - cuidado
        
        return {
            'aligned': direction_match and alignment_score >= min_alignment_threshold,
            'alignment_score': alignment_score,
            'impulse_direction': current['direction'],
            'impulse_strength': current['strength'],
            'impulse_confidence': current['confidence'],
            'conflict': conflict,
            'recommendation': recommendation
        }
    
    def get_detector_stats(self):
        """Retorna estadísticas del detector para debugging"""
        with self.lock:
            return {
                'window_size': self.window_size,
                'tick_history_length': len(self.tick_history),
                'last_velocity': self.last_velocity,
                'last_sequence': self.last_sequence_detected,
                'pressure_threshold': self.pressure_threshold,
                'min_sequence_length': self.min_sequence_length
            }
    
    def clear_history(self):
        """Limpia historial de ticks"""
        with self.lock:
            self.tick_history.clear()
            self.current_impulse = None
    
    # ⭐ NUEVO V4: MÉTODOS DE VALIDACIÓN PARA LAS 4 NUEVAS MEJORAS
    
    def _validate_recent_ticks_confirmation(self, ticks, expected_direction, confirmation_count):
        """
        ⭐ VALIDACIÓN 1: Confirma que los últimos N ticks siguen la dirección del impulso
        
        Si especialista recomienda BUY y presión BUY ≥ umbral:
        - Revisar últimos TickConfirmationCount ticks
        - Si la mayoría son alcistas → confirmar señal
        - Si no → penalizar entrada
        
        Returns: (valid, reason)
        """
        if len(ticks) < confirmation_count:
            return True, "Insuficientes ticks para confirmar"
        
        try:
            recent_confirmed = ticks[-confirmation_count:]
            
            # Contar ticks que confirman la dirección
            confirmations = 0
            for i in range(1, len(recent_confirmed)):
                price_change = recent_confirmed[i]['mid'] - recent_confirmed[i-1]['mid']
                
                if expected_direction == 'BUY' and price_change > 0:
                    confirmations += 1
                elif expected_direction == 'SELL' and price_change < 0:
                    confirmations += 1
            
            # Requiere > 50% de confirmación
            confirmation_ratio = confirmations / max(1, len(recent_confirmed) - 1)
            is_valid = confirmation_ratio >= 0.5
            
            reason = f"{expected_direction}: {confirmations}/{len(recent_confirmed)-1} ticks confirman ({confirmation_ratio*100:.0f}%)"
            
            return is_valid, reason
        except Exception as e:
            return True, f"Error en confirmación: {str(e)[:30]}"
    
    def _check_signal_expiration(self, direction):
        """
        ⭐ VALIDACIÓN 2: Verifica expiración de señal
        
        Si la señal fue detectada pero pasan más de signal_expiration_ms
        antes de ejecutar la orden → cancelar la señal y recalcular
        
        Returns: expired (bool)
        """
        if self.last_signal_timestamp is None:
            # Primera vez que se detecta esta dirección
            return False
        
        try:
            time_since_signal = (datetime.now() - self.last_signal_timestamp).total_seconds() * 1000
            expired = time_since_signal > self.signal_expiration_ms
            
            return expired
        except Exception:
            return False
    
    def _validate_price_movement(self, ticks, min_tick_movement):
        """
        ⭐ VALIDACIÓN 3: Movimiento mínimo de precio
        
        Evita operar en ruido del mercado.
        Verifica que el precio se haya movido al menos N ticks dentro de la ventana.
        
        Returns: (valid, reason)
        """
        if len(ticks) < min_tick_movement + 1:
            return True, "Insuficientes ticks para validar movimiento"
        
        try:
            # Contar cambios de precio significativos
            price_moves = 0
            for i in range(1, len(ticks)):
                if ticks[i]['mid'] != ticks[i-1]['mid']:
                    price_moves += 1
            
            is_valid = price_moves >= min_tick_movement
            reason = f"Movimientos: {price_moves}/{len(ticks)-1} (requerido: {min_tick_movement})"
            
            return is_valid, reason
        except Exception as e:
            return True, f"Error validando movimiento: {str(e)[:30]}"
    
    def _validate_dynamic_spread(self, ticks):
        """
        ⭐ VALIDACIÓN 4: Filtro de spread dinámico mejorado
        
        Evita operar cuando el spread es demasiado alto comparado con promedio.
        
        Parámetro: SpreadMultiplier (ej: 1.5)
        Lógica: Si spread actual > spread_promedio * SpreadMultiplier
        → Bloquear operación
        
        Returns: (valid, reason)
        """
        if len(ticks) < 5:
            return True, "Insuficientes ticks para estimar spread promedio"
        
        try:
            spreads = np.array([t['spread'] for t in ticks])
            avg_spread = np.mean(spreads)
            current_spread = spreads[-1]
            
            spread_ratio = current_spread / (avg_spread + 1e-9)
            is_valid = spread_ratio <= self.spread_filter
            
            reason = f"Spread actual: {current_spread:.5f} (promedio: {avg_spread:.5f}, ratio: {spread_ratio:.2f}x, límite: {self.spread_filter}x)"
            
            return is_valid, reason
        except Exception as e:
            return True, f"Error validando spread: {str(e)[:30]}"


# Para integración directa en botiaver1.py, aquí va un wrapper
class TickImpulseValidator:
    """Versión simplificada que trabaja con market_snapshots - MEJORADA V3"""
    
    def __init__(self, window_size=20, min_sequence_length=3, 
                 price_velocity_threshold=0.15, pressure_threshold=55,
                 micro_breakout_size=0.8, momentum_window=40,
                 imbalance_ratio=1.22, spread_filter=1.5, velocity_threshold=0.35,
                 confirmation_count=3, signal_expiration_ms=500, min_tick_movement=2,
                 log_callback=None):
        """
        Args:
            window_size: Tamaño de ventana configurable
            min_sequence_length: Mínimo de ticks consecutivos para secuencia
            price_velocity_threshold: Umbral de velocidad para bonus
            pressure_threshold: Umbral de presión mínimo
            micro_breakout_size: Tamaño mínimo de ruptura en pips
            momentum_window: Ventana para momentum
            imbalance_ratio: Ratio bid/ask desbalance
            spread_filter: Multiplicador de spread
            velocity_threshold: Umbral de velocidad del movimiento
            
            ⭐ NUEVOS V4:
            confirmation_count: Ticks para confirmar dirección (default 3)
            signal_expiration_ms: Expiración de señal en ms (default 500ms)
            min_tick_movement: Movimiento mínimo en ticks (default 2)
            
            log_callback: Función para logging opcional
        """
        self.log_callback = log_callback
        self.detector = TickImpulseDetector(
            window_size=window_size,
            min_sequence_length=min_sequence_length,
            price_velocity_threshold=price_velocity_threshold,
            pressure_threshold=pressure_threshold,
            micro_breakout_size=micro_breakout_size,
            momentum_window=momentum_window,
            imbalance_ratio=imbalance_ratio,
            spread_filter=spread_filter,
            velocity_threshold=velocity_threshold,
            confirmation_count=confirmation_count,
            signal_expiration_ms=signal_expiration_ms,
            min_tick_movement=min_tick_movement,
            log_callback=log_callback
        )
    
    def analyze_snapshots_for_impulse(self, snapshots, symbol=None):
        """
        Analiza market snapshots para detectar impulso
        Asume que snapshots tienen: timestamp, bid, ask, bid_volume?, ask_volume?
        
        Returns: impulse result dict
        """
        if not snapshots or len(snapshots) < 5:
            return {
                'direction': None,
                'strength': 0,
                'confidence': 0,
                'reason': 'Insuficientes snapshots',
                'data': {}
            }
        
        try:
            # Procesar últimos snapshots para impulso (según window_size)
            process_count = max(5, self.detector.window_size)
            for snap in snapshots[-process_count:]:
                try:
                    timestamp = snap.get('timestamp')
                    
                    # Mapear campos de precios (nested o flat)
                    if isinstance(snap.get('price'), dict):
                        bid = float(snap['price'].get('bid', 0))
                        ask = float(snap['price'].get('ask', 0))
                    else:
                        bid = float(snap.get('bid', 0))
                        ask = float(snap.get('ask', 0)) or (bid + 0.0005)
                    
                    # Mapear volúmenes - primero intentar buy_volume/sell_volume, después bid_volume/ask_volume
                    if isinstance(snap.get('volume'), dict):
                        bid_vol = int(snap['volume'].get('buy_volume', snap['volume'].get('bid_volume', 1)))
                        ask_vol = int(snap['volume'].get('sell_volume', snap['volume'].get('ask_volume', 1)))
                    else:
                        bid_vol = int(snap.get('buy_volume', snap.get('bid_volume', snap.get('tick_volume', 1))))
                        ask_vol = int(snap.get('sell_volume', snap.get('ask_volume', snap.get('tick_volume', 1))))
                    
                    result = self.detector.add_tick(timestamp, bid, ask, bid_vol, ask_vol)
                except Exception:
                    continue
            
            return self.detector.get_current_impulse()
            
        except Exception as e:
            return {
                'direction': None,
                'strength': 0,
                'confidence': 0,
                'reason': f'Error analizando snapshots: {str(e)}',
                'data': {}
            }
