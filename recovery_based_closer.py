"""
🔴 RECOVERY BASED CLOSER - Cierre Dinámico por Porcentaje de Recuperación
================================================
Cierra operaciones en ROJO cuando la pérdida consume más del X% del MIN_RECOVERY_POTENTIAL

LÓGICA:
-------
1. MIN_RECOVERY_POTENTIAL (%)  = Umbral mínimo de recuperación (ej: 30%)
2. MAX_RECOVERY_CONSUMPTION (%) = Máximo % del MIN que puede consumirse (ej: 80%)
3. Max pérdida permitida (%) = MIN * MAX_CONSUMPTION / 100
   Ejemplo: 30% * 80% = 24% máxima pérdida permitida

Si: |pérdida_actual %| >= max_pérdida_permitida %
    → CIERRE INMEDIATO (operación en rojo irrecuperable)
"""

import MetaTrader5 as mt5
import time


class RecoveryBasedCloser:
    """Cierra operaciones basadas en consumo de potencial de recuperación"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.name = "🔴 Recovery Closer"
        self.last_close_time = {}  # Prevenir cierres duplicados
        
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def check_and_close_by_recovery(self, 
                                    position,
                                    symbol,
                                    min_recovery_pct,
                                    max_recovery_consumption_pct,
                                    log_callback=None):
        """
        Verifica si la operación debe cerrarse por consumo de recuperación
        
        Args:
            position: Objeto de posición MT5
            symbol: Símbolo operando
            min_recovery_pct: MIN_RECOVERY_POTENTIAL (ej: 30.0)
            max_recovery_consumption_pct: Máximo % que puede consumirse (ej: 80.0)
            log_callback: Función para logging
            
        Returns:
            dict con resultado:
            {
                'should_close': bool,
                'reason': str,
                'loss_pct': float,
                'max_allowed_pct': float,
                'consumption_ratio': float  # % de MIN_RECOVERY consumido
            }
        """
        try:
            # ⭐ SOLO para operaciones en PÉRDIDA
            if position.profit >= 0:
                return {
                    'should_close': False,
                    'reason': 'Operación en AZUL (ganancia)',
                    'loss_pct': 0.0,
                    'max_allowed_pct': 0.0,
                    'consumption_ratio': 0.0
                }
            
            # Obtener info actual del símbolo
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {
                    'should_close': False,
                    'reason': 'No se pudo obtener tick de mercado',
                    'loss_pct': 0.0,
                    'max_allowed_pct': 0.0,
                    'consumption_ratio': 0.0
                }
            
            # Calcular punto de entrada (aproximado desde el profit)
            # profit = (precio_salida - precio_entrada) * volume * point_value
            # Para simplificar, usamos el profit directamente en %
            current_price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
            
            # Calcular % de pérdida en relación al punto de entrada
            if position.type == mt5.POSITION_TYPE_BUY:
                # Para BUY: precio actual < precio entrada = pérdida
                loss_pct = ((position.price_open - current_price) / position.price_open) * 100
            else:
                # Para SELL: precio atual > precio entrada = pérdida
                loss_pct = ((current_price - position.price_open) / position.price_open) * 100
            
            # Pérdida debe ser positivo para comparaciones
            loss_pct = abs(loss_pct)
            
            # ⭐ CÁLCULO: Máxima pérdida permitida en %
            max_allowed_loss_pct = (min_recovery_pct * max_recovery_consumption_pct) / 100
            
            # ⭐ RATIO DE CONSUMO: Qué % del MIN_RECOVERY_POTENTIAL se ha consumido
            if min_recovery_pct > 0:
                consumption_ratio = (loss_pct / min_recovery_pct) * 100
            else:
                consumption_ratio = 0.0
            
            # ⭐ DECISIÓN: ¿Cerrar?
            should_close = loss_pct >= max_allowed_loss_pct
            
            result = {
                'should_close': should_close,
                'reason': '',
                'loss_pct': round(loss_pct, 2),
                'max_allowed_pct': round(max_allowed_loss_pct, 2),
                'consumption_ratio': round(consumption_ratio, 2)
            }
            
            if should_close:
                result['reason'] = (
                    f"PÉRDIDA EXCESIVA: {loss_pct:.2f}% >= {max_allowed_loss_pct:.2f}% "
                    f"(consume {consumption_ratio:.1f}% del MIN_RECOVERY)"
                )
            else:
                # Mostrar estado de consumo
                if consumption_ratio >= 70:
                    result['reason'] = f"⚠️ ADVERTENCIA: {consumption_ratio:.1f}% consumo (crítico)"
                elif consumption_ratio >= 50:
                    result['reason'] = f"⚠️ ALERTA: {consumption_ratio:.1f}% consumo (alto)"
                else:
                    result['reason'] = f"✓ OK: {consumption_ratio:.1f}% consumo (dentro límite)"
            
            return result
            
        except Exception as e:
            return {
                'should_close': False,
                'reason': f'Error en check: {str(e)[:60]}',
                'loss_pct': 0.0,
                'max_allowed_pct': 0.0,
                'consumption_ratio': 0.0,
                'error': True
            }
    
    def calculate_max_allowed_loss_usd(self,
                                      position,
                                      min_recovery_pct,
                                      max_recovery_consumption_pct,
                                      symbol_info):
        """
        Calcula la máxima pérdida permitida en USD (moneda)
        
        Args:
            position: Objeto de posición MT5
            min_recovery_pct: MIN_RECOVERY_POTENTIAL (ej: 30.0)
            max_recovery_consumption_pct: Máximo % consumible (ej: 80.0)
            symbol_info: Info del símbolo de MT5
            
        Returns:
            dict con cálculo en USD
        """
        try:
            # Máxima pérdida permitida en %
            max_allowed_loss_pct = (min_recovery_pct * max_recovery_consumption_pct) / 100
            
            # Convertir a USD: entry_price * volume * contract_size * (loss_pct / 100)
            contract_size = symbol_info.trade_contract_size if symbol_info else 1.0
            max_loss_usd = (position.price_open * position.volume * contract_size * max_allowed_loss_pct) / 100
            
            # Pérdida actual en USD
            current_loss_usd = abs(position.profit)  # position.profit ya está en la moneda de cuenta
            
            return {
                'max_allowed_usd': round(max_loss_usd, 2),
                'current_loss_usd': round(current_loss_usd, 2),
                'threshold_exceeded': current_loss_usd >= max_loss_usd,
                'margin_remaining_usd': round(max_loss_usd - current_loss_usd, 2)
            }
            
        except Exception as e:
            return {
                'max_allowed_usd': 0.0,
                'current_loss_usd': 0.0,
                'threshold_exceeded': False,
                'error': str(e)
            }
    
    def close_position_by_recovery(self, position, symbol, log_callback=None):
        """
        EJECUTA el cierre de la posición
        
        Args:
            position: Objeto de posición a cerrar
            symbol: Símbolo
            log_callback: Función para logging
            
        Returns:
            dict con resultado del cierre
        """
        log_func = log_callback or self.log
        
        try:
            # Obtener tick actual
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                log_func(f"[RECOVERY_CLOSE] ❌ No se pudo obtener tick para {symbol}", 'error')
                return {'success': False, 'error': 'No tick available'}
            
            # Preparar orden de cierre
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
            
            # ⭐ Calcular pérdida % para el comentario
            if position.type == mt5.POSITION_TYPE_BUY:
                loss_pct = ((position.price_open - price) / position.price_open) * 100
            else:
                loss_pct = ((price - position.price_open) / position.price_open) * 100
            loss_pct = abs(loss_pct)
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": close_type,
                "price": price,
                "magic": position.magic,
                "comment": f"Recovery Close @ {loss_pct:.2f}% loss",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            # Ejecutar cierre
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                log_func(
                    f"[RECOVERY_CLOSE] ✅ Posición cerrada por recuperación "
                    f"[${position.profit:.2f} pérdida]",
                    'success'
                )
                return {
                    'success': True,
                    'order_id': result.order,
                    'deal_ticket': result.deal,
                    'profit': position.profit
                }
            else:
                log_func(
                    f"[RECOVERY_CLOSE] ❌ Error en cierre: {result.comment} "
                    f"(código {result.retcode})",
                    'error'
                )
                return {
                    'success': False,
                    'error': result.comment,
                    'retcode': result.retcode
                }
                
        except Exception as e:
            log_func(f"[RECOVERY_CLOSE] ❌ Exception: {str(e)[:80]}", 'error')
            return {
                'success': False,
                'error': str(e)
            }


# Función helper para integración simple
def should_close_by_recovery(position, 
                            symbol, 
                            min_recovery_pct, 
                            max_recovery_consumption_pct,
                            log_callback=None):
    """
    Función auxiliar para integración rápida
    
    Uso en boteddver1.py:
    -----
    from recovery_based_closer import should_close_by_recovery
    
    # En el loop de monitoreo:
    result = should_close_by_recovery(
        pos, 
        symbol,
        float(self.config['MIN_RECOVERY_POTENTIAL'].get()),
        float(self.config['MAX_RECOVERY_CONSUMPTION_PCT'].get()),
        self.add_log
    )
    
    if result['should_close']:
        # ejecutar cierre
    """
    closer = RecoveryBasedCloser(log_callback)
    return closer.check_and_close_by_recovery(
        position,
        symbol,
        min_recovery_pct,
        max_recovery_consumption_pct,
        log_callback
    )
