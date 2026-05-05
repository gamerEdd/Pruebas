# -*- coding: utf-8 -*-
"""
🔥 TICK FLOW ANALYZER - Análisis de Microestructura de Mercado
Confirma señales de IA analizando la presión real del mercado mediante flujo de ticks
"""

import MetaTrader5 as mt5
import numpy as np
from collections import deque
from datetime import datetime
from mt5_safe import get_ticks_safe


class TickFlowAnalyzer:
    """🔥 Analizador de flujo de ticks para confirmación de señales"""
    
    def __init__(self, symbol='XAUUSD', log_callback=None):
        """
        Inicializa el analizador de ticks
        
        Args:
            symbol: Símbolo a analizar
            log_callback: Función para logging
        """
        self.symbol = symbol
        self.log = log_callback or print
        
        # Configuración por defecto
        self.enabled = True
        self.ticks_window = 400  # Ventana de ticks a analizar
        self.momentum_window = 30  # Ventana para momentum
        self.imbalance_threshold = 20  # Umbral mínimo de imbalance
        self.spread_multiplier = 1.5  # Multiplicador de spread
        
        # Histórico de ticks en memoria (sin guardar a JSON)
        self.ticks_history = deque(maxlen=500)
        self.last_processed_time = None
        self.spread_baseline = 0
        self.spread_count = 0
        
    def update_config(self, config_dict):
        """Actualiza la configuración del analizador"""
        if 'enabled' in config_dict:
            self.enabled = config_dict['enabled']
        if 'ticks_window' in config_dict:
            self.ticks_window = config_dict['ticks_window']
        if 'momentum_window' in config_dict:
            self.momentum_window = config_dict['momentum_window']
        if 'imbalance_threshold' in config_dict:
            self.imbalance_threshold = config_dict['imbalance_threshold']
        if 'spread_multiplier' in config_dict:
            self.spread_multiplier = config_dict['spread_multiplier']
    
    def get_recent_ticks(self, limit=None):
        """
        Obtiene ticks recientes de MetaTrader5 con múltiples fallbacks
        
        ESTRATEGIAS (en orden):
        1. Subscribir al símbolo si es necesario
        2. copy_ticks_range() con rango reciente (PRIMARIA)
        3. copy_ticks_from() con datetime.now()
        4. copy_rates_range() como fallback (simular ticks desde bid-ask)
        5. Caché local en memoria
        
        IMPORTANTE: Para que funcione, XAUUSD debe:
        - Estar abierto un gráfico en MT5 (para mantener subscripción)
        - O tener datos históricos disponibles en MT5
        
        Args:
            limit: Cantidad máxima de ticks (default: ticks_window)
        
        Returns:
            List de ticks o None si hay error
        """
        if limit is None:
            limit = self.ticks_window
        
        # Asegurar que el símbolo está subscrito
        try:
            self.log(f"[TICK] Verificando subscripcion a {self.symbol}...", 'info')
            mt5.symbol_select(self.symbol, True)
            self.log(f"[TICK] OK: {self.symbol} subscrito", 'success')
        except Exception as e:
            self.log(f"[TICK] Error al subscribir: {str(e)[:60]}", 'warning')

        # Usar wrapper seguro que intenta copy_ticks_range -> copy_ticks_from -> rates
        try:
            ticks = get_ticks_safe(self.symbol, limit=limit, log=self.log)
            if ticks is not None and len(ticks) > 0:
                self.ticks_history.extend(ticks)
                self.log(f"[TICK] OK (safe): {len(ticks)} ticks obtenidos", 'success')
                return ticks
        except Exception as e:
            self.log(f"[TICK] get_ticks_safe error: {str(e)[:100]}", 'warning')

        # Cache fallback
        try:
            if len(self.ticks_history) > 10:
                cached_ticks = list(self.ticks_history)[-limit:]
                self.log(f"[TICK] OK ESTRAT 4 (CACHE): {len(cached_ticks)} ticks local", 'success')
                return cached_ticks
        except Exception as e:
            self.log(f"[TICK] ESTRAT 4 error: {str(e)[:60]}", 'warning')

        self.log(f"[TICK] ERROR TOTAL: Sin ticks para {self.symbol}", 'error')
        self.log(f"[TICK] SOLUCION: Abrir grafico de {self.symbol} en MT5 para subscribirse", 'warning')
        return None
    
    def calculate_tick_direction(self, ticks):
        """
        Calcula la dirección de cada tick usando VOLUMEN real (bid vs ask)
        ⭐ CORREGIDO: Usa ask_volume para presión ALCISTA, bid_volume para BAJISTA
        
        Lógica:
        - ask_volume > bid_volume → Presión de COMPRA (precio SUBE)
        - bid_volume > ask_volume → Presión de VENTA (precio BAJA)
        
        Args:
            ticks: Array de ticks de MT5
        
        Returns:
            Dict con conteos de buy/sell ticks
        """
        if ticks is None or len(ticks) < 2:
            return {'buy': 0, 'sell': 0, 'neutral': 0}
        
        buy_count = 0
        sell_count = 0
        neutral_count = 0
        
        for tick in ticks:
            # MT5 tick estructura: {'time', 'bid', 'ask', 'bid_volume', 'ask_volume', 'flags'}
            ask_vol = tick.get('ask_volume', 0)
            bid_vol = tick.get('bid_volume', 0)
            
            if ask_vol == 0 and bid_vol == 0:
                # Fallback: usar cambio de precio si no hay volumen
                # (raramente ocurre, pero para robustez)
                neutral_count += 1
                continue
            
            # ⭐ REGLA: Si ask_volume > bid_volume, presión ALCISTA
            # Esto es lo OPUESTO a la lógica anterior que estaba invertida
            if ask_vol > bid_vol:
                buy_count += 1  # Compradores agresivos al ASK (precio SUBE)
            elif bid_vol > ask_vol:
                sell_count += 1  # Vendedores agresivos al BID (precio BAJA)
            else:
                neutral_count += 1  # Volumen balanceado
        
        return {
            'buy': buy_count,
            'sell': sell_count,
            'neutral': neutral_count
        }
    
    def calculate_order_flow_imbalance(self, ticks):
        """
        Calcula el imbalance del flujo de órdenes
        
        Imbalance = buy_ticks - sell_ticks
        
        Positivo: Presión alcista
        Negativo: Presión bajista
        
        Args:
            ticks: Array de ticks
        
        Returns:
            Float con el imbalance
        """
        if ticks is None or len(ticks) < 2:
            return 0
        
        tick_counts = self.calculate_tick_direction(ticks)
        imbalance = tick_counts['buy'] - tick_counts['sell']
        
        # Diagnóstico detallado
        self.log(f"[TICK-IMBALANCE] Ticks procesados: {len(ticks)} | BUY: {tick_counts['buy']} | SELL: {tick_counts['sell']} | NEUTRAL: {tick_counts['neutral']}", 'info')
        self.log(f"[TICK-IMBALANCE] IMBALANCE RESULTADO: {imbalance:+.0f}", 'info')
        
        return imbalance
    
    def calculate_momentum(self, ticks):
        """
        Calcula el momentum usando ventana reciente
        
        Args:
            ticks: Array de ticks
        
        Returns:
            Float con el momentum normalizado (-100 a +100)
        """
        if len(ticks) < self.momentum_window:
            window = ticks
        else:
            window = ticks[-self.momentum_window:]
        
        tick_counts = self.calculate_tick_direction(window)
        total = tick_counts['buy'] + tick_counts['sell']
        
        if total == 0:
            return 0.0
        
        buy_ratio = (tick_counts['buy'] - tick_counts['sell']) / total
        momentum = buy_ratio * 100  # Normalizar a -100 a +100
        
        return momentum
    
    def calculate_spread_stats(self, ticks):
        """
        Calcula estadísticas del spread actual
        
        Args:
            ticks: Array de ticks
        
        Returns:
            Dict con spread actual, promedio, desv estándar
        """
        if ticks is None or len(ticks) == 0:
            return {
                'current_spread': 0,
                'average_spread': self.spread_baseline,
                'min_spread': 0,
                'max_spread': 0
            }
        
        spreads = []
        for tick in ticks:
            spread = tick['ask'] - tick['bid']
            spreads.append(spread)
        
        spreads = np.array(spreads)
        
        # Actualizar baseline si es necesario
        if self.spread_baseline == 0:
            self.spread_baseline = np.mean(spreads)
        
        current_spread = spreads[-1] if len(spreads) > 0 else 0
        
        return {
            'current_spread': float(current_spread),
            'average_spread': float(np.mean(spreads)),
            'min_spread': float(np.min(spreads)),
            'max_spread': float(np.max(spreads)),
            'std_spread': float(np.std(spreads))
        }
    
    def confirm_signal(self, signal_direction, ticks=None):
        """
        Confirma si hay soporte de flujo de ticks para la señal de IA
        
        IMPORTANTE: Este método devuelve si la SEÑAL es confirmada o rechazada
        por la microestructura del mercado (ticks reales)
        
        Args:
            signal_direction: 'BUY' o 'SELL'
            ticks: Array de ticks (si es None, los obtiene)
        
        Returns:
            Dict con análisis y confirmación
        """
        # Si el módulo no está habilitado, confirmar siempre
        if not self.enabled:
            self.log(f"[TICK-CONFIRM] {signal_direction} - Módulo DESHABILITADO, confirmando automáticamente", 'warning')
            return {
                'confirmed': True,
                'confirmation_type': 'disabled',
                'reason': 'Análisis de ticks deshabilitado',
                'data_status': 'disabled'
            }
        
        # Obtener ticks si no se proporcionan
        ticks_source = 'PROPORCIONADO'
        if ticks is None:
            self.log(f"[TICK-CONFIRM] {signal_direction} - Obteniendo ticks...", 'info')
            ticks = self.get_recent_ticks()
            ticks_source = 'MT5'
        
        if ticks is None:
            self.log(f"[TICK-CONFIRM] {signal_direction} - ❌ ERROR: get_recent_ticks() devolvió None", 'error')
            return {
                'confirmed': False,
                'confirmation_type': 'error_no_ticks',
                'reason': 'ERROR: No se obtuvieron ticks',
                'data_status': 'error'
            }
        
        if len(ticks) < 10:
            self.log(f"[TICK-CONFIRM] {signal_direction} - ⚠️ DATOS INSUFICIENTES: {len(ticks)} ticks (min 10) desde {ticks_source}", 'warning')
            return {
                'confirmed': False,
                'confirmation_type': 'insufficient_data',
                'reason': f'Datos de ticks insuficientes ({len(ticks)}/10)',
                'data_status': 'insufficient'
            }
        
        # ✅ TENEMOS DATOS REALES
        self.log(f"[TICK-CONFIRM] {signal_direction} - ✅ DATOS REALES: {len(ticks)} ticks desde {ticks_source}", 'success')
        
        # Calcular métricas
        imbalance = self.calculate_order_flow_imbalance(ticks)
        momentum = self.calculate_momentum(ticks)
        tick_counts = self.calculate_tick_direction(ticks)
        spread_stats = self.calculate_spread_stats(ticks)
        
        self.log(f"[TICK-CONFIRM] {signal_direction} - Ticks: BUY={tick_counts['buy']} | SELL={tick_counts['sell']} | NEUTRAL={tick_counts['neutral']}", 'info')
        
        # Filtro de spread
        spread_threshold = spread_stats['average_spread'] * self.spread_multiplier
        if spread_stats['current_spread'] > spread_threshold:
            self.log(f"[TICK-CONFIRM] {signal_direction} - ❌ RECHAZADA: Spread alto {spread_stats['current_spread']:.6f} > {spread_threshold:.6f}", 'warning')
            return {
                'confirmed': False,
                'confirmation_type': 'high_spread',
                'reason': f"Spread alto: {spread_stats['current_spread']:.2f} > {spread_threshold:.2f}",
                'metrics': {
                    'imbalance': imbalance,
                    'momentum': momentum,
                    'current_spread': spread_stats['current_spread'],
                    'threshold_spread': spread_threshold,
                    'tick_counts': tick_counts
                },
                'data_status': 'high_spread'
            }
        
        # Lógica de confirmación por dirección
        if signal_direction == 'BUY':
            confirmed = imbalance > self.imbalance_threshold
            reason = f"BUY: Imbalance={imbalance:+.0f} (umbral={self.imbalance_threshold})"
            status = "✅ CONFIRMADA" if confirmed else "❌ RECHAZADA"
            
        elif signal_direction == 'SELL':
            confirmed = imbalance < -self.imbalance_threshold
            reason = f"SELL: Imbalance={imbalance:+.0f} (umbral=-{self.imbalance_threshold})"
            status = "✅ CONFIRMADA" if confirmed else "❌ RECHAZADA"
        
        else:
            confirmed = False
            reason = f"Dirección inválida: {signal_direction}"
            status = "❌ ERROR"
        
        # Log de decisión final
        self.log(f"[TICK-CONFIRM] {signal_direction} {status}: Imbalance={imbalance:+.0f} vs Umbral={'±'+str(self.imbalance_threshold)}", 
                 'success' if confirmed else 'warning')
        
        confirmation_type = 'tick_flow_match' if confirmed else 'tick_flow_mismatch'
        
        return {
            'confirmed': confirmed,
            'confirmation_type': confirmation_type,
            'reason': reason,
            'metrics': {
                'imbalance': imbalance,
                'momentum': momentum,
                'current_spread': spread_stats['current_spread'],
                'average_spread': spread_stats['average_spread'],
                'min_spread': spread_stats['min_spread'],
                'max_spread': spread_stats['max_spread'],
                'tick_counts': tick_counts
            },
            'data_status': 'confirmed' if confirmed else 'rejected',
            'ticks_count': len(ticks),
            'ticks_source': ticks_source
        }
    
    def get_analysis_summary(self, ticks=None):
        """
        Obtiene un resumen completo del análisis actual
        
        Args:
            ticks: Array de ticks (si es None, los obtiene)
        
        Returns:
            Dict con análisis completo
        """
        if ticks is None:
            ticks = self.get_recent_ticks()
        
        if ticks is None or len(ticks) == 0:
            return {
                'status': 'no_data',
                'message': 'No hay datos de ticks disponibles'
            }
        
        imbalance = self.calculate_order_flow_imbalance(ticks)
        momentum = self.calculate_momentum(ticks)
        tick_counts = self.calculate_tick_direction(ticks)
        spread_stats = self.calculate_spread_stats(ticks)
        
        return {
            'status': 'ok',
            'tick_counts': tick_counts,
            'imbalance': imbalance,
            'momentum': momentum,
            'spread_stats': spread_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def resolve_final_direction(self, ia_direction, ticks=None):
        """
        🔥 MÉTODO CRÍTICO: Resuelve la dirección final respetando el flujo de ticks
        Si el IA dice SELL pero el flow dice BUY → retorna BUY
        Si el IA dice BUY pero el flow dice SELL → retorna SELL
        
        Args:
            ia_direction: Dirección del IA ('BUY' o 'SELL')
            ticks: Array de ticks (si es None, los obtiene)
        
        Returns:
            Dict con dirección final, análisis y logs
        """
        if not self.enabled:
            self.log(f"\n[FLOW] 🔐 Análisis DESHABILITADO - Usando dirección IA: {ia_direction}\n", 'info')
            return {
                'final_direction': ia_direction,
                'inverted': False,
                'reason': 'Análisis deshabilitado',
                'imbalance': 0,
                'momentum': 0,
                'status': 'disabled'
            }
        
        # Obtener ticks si no se proporcionan
        ticks_source = 'PROPORCIONADO'
        if ticks is None:
            self.log(f"[FLOW] 📊 Obteniendo ticks para análisis...", 'info')
            ticks = self.get_recent_ticks()
            ticks_source = 'MT5'
        
        # DIAGNÓSTICO CRÍTICO: Verificar que tenemos ticks reales
        if ticks is None:
            self.log(f"\n[FLOW] ❌ ERROR CRÍTICO: get_recent_ticks() devolvió None - NO HAY DATOS", 'error')
            return {
                'final_direction': ia_direction,
                'inverted': False,
                'reason': 'ERROR: Ticks None',
                'imbalance': 0,
                'momentum': 0,
                'status': 'error_no_ticks'
            }
        
        if len(ticks) < 10:
            self.log(f"\n[FLOW] ⚠️ DATOS INSUFICIENTES: Solo {len(ticks)} ticks (mínimo 10) - NO CONFIABLE", 'error')
            self.log(f"[FLOW] Ticks origen: {ticks_source} | Longitud: {len(ticks)}", 'warning')
            return {
                'final_direction': ia_direction,
                'inverted': False,
                'reason': f'Datos de ticks insuficientes ({len(ticks)}/10)',
                'imbalance': 0,
                'momentum': 0,
                'status': 'insufficient_data'
            }
        
        # ✅ DIAGNÓSTICO - CONFIRMAMOS QUE TENEMOS DATOS REALES
        self.log(f"\n[FLOW] ✅ DATOS OBTENIDOS: {len(ticks)} ticks DE {ticks_source}", 'success')
        self.log(f"[FLOW] Primer tick: {ticks[0]['time']} | Último tick: {ticks[-1]['time']}", 'info')
        
        # 🔥 DIAGNÓSTICO DE VOLÚMENES (primeros y últimos 3 ticks)
        try:
            self.log(f"[FLOW-VOL] 📊 PRIMEROS 3 TICKS:", 'info')
            for i, tick in enumerate(ticks[:3]):
                bid_v = tick.get('bid_volume', 0)
                ask_v = tick.get('ask_volume', 0)
                self.log(f"[FLOW-VOL]   Tick {i}: bid_vol={bid_v} | ask_vol={ask_v} | {bid_v} vs {ask_v} → {'BUY' if ask_v > bid_v else 'SELL' if bid_v > ask_v else 'NEUTRAL'}", 'info')
            
            self.log(f"[FLOW-VOL] 📊 ÚLTIMOS 3 TICKS:", 'info')
            for i, tick in enumerate(ticks[-3:]):
                bid_v = tick.get('bid_volume', 0)
                ask_v = tick.get('ask_volume', 0)
                idx = len(ticks) - 3 + i
                self.log(f"[FLOW-VOL]   Tick {idx}: bid_vol={bid_v} | ask_vol={ask_v} | {bid_v} vs {ask_v} → {'BUY' if ask_v > bid_v else 'SELL' if bid_v > ask_v else 'NEUTRAL'}", 'info')
        except Exception as e:
            self.log(f"[FLOW-VOL] ⚠️ Error en diagnóstico de volúmenes: {str(e)[:50]}", 'warning')
        
        # Calcular métricas clave
        imbalance = self.calculate_order_flow_imbalance(ticks)
        momentum = self.calculate_momentum(ticks)
        tick_counts = self.calculate_tick_direction(ticks)
        spread_stats = self.calculate_spread_stats(ticks)
        
        # Determinar presión de mercado basada en IMBALANCE FUERTE
        if abs(imbalance) > self.imbalance_threshold:
            # IMBALANCE FUERTE - DEFINIR DIRECCIÓN CLARA
            flow_direction = 'BUY' if imbalance > 0 else 'SELL'
            flow_strength = 'FUERTE'
            self.log(f"[FLOW] 💪 IMBALANCE FUERTE: |{imbalance:+.0f}| > {self.imbalance_threshold}", 'success')
        else:
            # IMBALANCE DÉBIL - USAR MOMENTUM COMO DESEMPATE
            flow_direction = 'BUY' if momentum > 0 else 'SELL'
            flow_strength = 'DÉBIL'
            self.log(f"[FLOW] ⚡ IMBALANCE DÉBIL: |{imbalance:+.0f}| ≤ {self.imbalance_threshold} (usando momentum)", 'warning')
        
        # 🔥 LÓGICA DE DECISIÓN FINAL
        final_direction = ia_direction
        inverted = False
        
        # Logs iniciales con separador
        self.log(f"\n[FLOW] ╔════════════════════════════════════════╗", 'info')
        self.log(f"[FLOW] ║   RESOLUCIÓN DE DIRECCIÓN FINAL       ║", 'info')
        self.log(f"[FLOW] ╚════════════════════════════════════════╝", 'info')
        self.log(f"[FLOW] 📌 IA SUGIERE: {ia_direction}", 'info')
        self.log(f"[FLOW] 📊 Imbalance: {imbalance:+.0f} (Umbral: ±{self.imbalance_threshold})", 'info')
        self.log(f"[FLOW] 📈 Momentum: {momentum:+.2f}%", 'info')
        self.log(f"[FLOW] 🟢 TICKS BUY: {tick_counts['buy']} | 🔴 TICKS SELL: {tick_counts['sell']} | ⚪ NEUTRAL: {tick_counts['neutral']}", 'info')
        self.log(f"[FLOW] 💪 Presión MERCADO: {flow_direction} ({flow_strength})", 'success' if flow_strength == 'FUERTE' else 'info')
        
        # EVALUAR CONFLICTO
        if ia_direction == flow_direction:
            # ✅ ALINEADOS
            self.log(f"[FLOW] ✅ POSICIÓN: IA y FLOW ALINEADOS", 'success')
            reason = f"IA={ia_direction} COINCIDE con FLOW={flow_direction} (Imb: {imbalance:+.0f})"
        else:
            # ⚠️ CONFLICTO - DECIDIR SI INVERTIR
            self.log(f"[FLOW] ⚠️ CONFLICTO: IA={ia_direction} vs FLOW={flow_direction}", 'warning')
            
            if flow_strength == 'FUERTE':
                # INVERTIR - El flow es demasiado fuerte
                final_direction = flow_direction
                inverted = True
                self.log(f"[FLOW] 🔄 ACCIÓN: INVERTIR dirección (flow FUERTE)", 'error')
                reason = f"FLOW FUERTE ({flow_direction}) ANULA IA ({ia_direction}) | Imbalance: {imbalance:+.0f}"
                self.log(f"[FLOW] 🎯 DIRECCIÓN FINAL: {final_direction} ← INVERTIDA!", 'error')
            else:
                # MANTENER - El flow es débil, confiamos más en IA
                self.log(f"[FLOW] ✏️ ACCIÓN: MANTENER IA (flow débil)", 'warning')
                reason = f"FLOW débil ({flow_direction}) NO anula IA ({ia_direction}) | Imbalance: {imbalance:+.0f}"
                self.log(f"[FLOW] 🎯 DIRECCIÓN FINAL: {final_direction} (IA respetada)", 'warning')
        
        # Log final
        self.log(f"[FLOW] 💾 Estado: {'INVERTIDA ✋' if inverted else 'CONFIRMADA ✓'}", 'error' if inverted else 'success')
        self.log(f"[FLOW] 📝 Razón: {reason}", 'warning' if inverted else 'info')
        self.log(f"[FLOW] ╚════════════════════════════════════════╝\n", 'info')
        
        return {
            'final_direction': final_direction,
            'inverted': inverted,
            'reason': reason,
            'imbalance': imbalance,
            'momentum': momentum,
            'flow_direction': flow_direction,
            'flow_strength': flow_strength,
            'tick_counts': tick_counts,
            'spread_stats': spread_stats,
            'status': 'resolved',
            'ticks_count': len(ticks),
            'ticks_source': ticks_source
        }

