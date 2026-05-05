"""
⭐ CIERRE DINÁMICO DE POSICIONES CONTRARIAS A REVERSIÓN DETECTADA
Monitorea cambios de tendencia en tiempo real y cierra posiciones que van
a contraposición del cambio inminente.
"""

import MetaTrader5 as mt5
import time
from datetime import datetime

class DynamicPositionCloser:
    """Cierra posiciones dinámicamente cuando se detecta reversión de tendencia"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
        self.last_signal = 'STABLE'
        self.last_conf = 0
        self.close_threshold_confidence = 70  # Cerrar si confianza > 70%
        self.positions_monitored = {}  # {ticket: {'direction': 'BUY'/'SELL', 'open_time': t, 'entry_price': p}}
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def evaluate_and_close(self, symbol, trend_analysis, magic_number):
        """
        Evalúa cambio de tendencia y cierra posiciones contrarias.
        
        trend_analysis debe contener:
        {
            'signal': 'BUY_TO_SELL' | 'SELL_TO_BUY' | 'STABLE',
            'confidence': 0-100,
            'risk_level': 'LOW' | 'MEDIUM' | 'HIGH',
            'reason': str
        }
        
        Devuelve: número de posiciones cerradas
        """
        try:
            if not trend_analysis:
                return 0
            
            signal = trend_analysis.get('signal', 'STABLE')
            confidence = float(trend_analysis.get('confidence', 0))
            
            # Solo actuar si confianza es suficiente
            if confidence < self.close_threshold_confidence:
                return 0
            
            # Actualizar señal
            self.last_signal = signal
            self.last_conf = confidence
            
            # Determinar qué posiciones cerrar
            positions_to_close = []
            
            if signal == 'BUY_TO_SELL':
                # La tendencia va a cambiar de BUY a SELL
                # Cerrar posiciones LONG (BUY) que son contrarias
                self.log(f"📉 REVERSIÓN BUY→SELL detectada ({confidence:.1f}%): Buscando LONG para cerrar...", 'warning')
                positions = mt5.positions_get(symbol=symbol)
                if positions:
                    for pos in positions:
                        if pos.magic == magic_number and pos.type == mt5.POSITION_TYPE_BUY:
                            positions_to_close.append(pos)
                            self.log(f"   🔴 Marcada para cierre: BUY #{pos.ticket} @ {pos.price_open:.5f}", 'error')
            
            elif signal == 'SELL_TO_BUY':
                # La tendencia va a cambiar de SELL a BUY
                # Cerrar posiciones SHORT (SELL) que son contrarias
                self.log(f"📈 REVERSIÓN SELL→BUY detectada ({confidence:.1f}%): Buscando SHORT para cerrar...", 'warning')
                positions = mt5.positions_get(symbol=symbol)
                if positions:
                    for pos in positions:
                        if pos.magic == magic_number and pos.type == mt5.POSITION_TYPE_SELL:
                            positions_to_close.append(pos)
                            self.log(f"   🔴 Marcada para cierre: SELL #{pos.ticket} @ {pos.price_open:.5f}", 'error')
            
            # Ejecutar cierres
            closed_count = 0
            for pos in positions_to_close:
                try:
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        continue
                    
                    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                    close_price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": pos.volume,
                        "type": close_type,
                        "position": pos.ticket,
                        "price": close_price,
                        "magic": magic_number,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                        "deviation": 20,
                        "comment": "DynamicClose_Reversal"
                    }
                    
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                        profit_str = f"+${pos.profit:.2f}" if pos.profit >= 0 else f"-${abs(pos.profit):.2f}"
                        self.log(
                            f"✅ Cierre dinámico: {direction} #{pos.ticket} | "
                            f"Profit: {profit_str} | "
                            f"Motivo: Reversión {signal}",
                            'success'
                        )
                        closed_count += 1
                    else:
                        self.log(
                            f"❌ Error cerrando dinámicamente: {getattr(result, 'comment', str(result.retcode))}",
                            'error'
                        )
                except Exception as e:
                    self.log(f"Error cerrando posición #{pos.ticket}: {str(e)}", 'error')
            
            if closed_count > 0:
                self.log(
                    f"🛡️ CIERRE DINÁMICO COMPLETADO: {closed_count} posición(es) cerrada(s) antes del SL",
                    'success'
                )
            
            return closed_count
        
        except Exception as e:
            self.log(f"Error en evaluate_and_close: {str(e)}", 'error')
            return 0
    
    def should_open_new_position(self, signal, confidence):
        """
        Determina si es seguro ABRIR nueva posición en función del cambio de tendencia.
        
        Si se detectó reversión reciente, NO abrir en dirección antigua.
        Devuelve: (está_ok_para_abrir, razón)
        """
        try:
            # Ventana de tiempo: no abrir en dirección antigua durante 20 segundos
            # después de detectar reversión clara
            
            if confidence < 75:  # Baja confianza = no hay reversión clara
                return (True, "Confianza insuficiente para bloquear apertura")
            
            # Si SELL_TO_BUY: no abrir SELL por 20s
            # Si BUY_TO_SELL: no abrir BUY por 20s
            
            if signal == 'BUY_TO_SELL':
                return (False, "Reversión BUY→SELL: Bloqueado abrir BUY. Espera SELL.")
            elif signal == 'SELL_TO_BUY':
                return (False, "Reversión SELL→BUY: Bloqueado abrir SELL. Espera BUY.")
            
            return (True, "Sin restricciones")
        
        except Exception as e:
            self.log(f"Error en should_open_new_position: {str(e)}", 'error')
            return (True, "Error en validación")
