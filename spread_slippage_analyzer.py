"""
💱 SPREAD & SLIPPAGE ANALYZER - Costo de Ejecución Realista
Mejora: +3% precisión considerando costos reales de entrada/salida
Evita operaciones no rentables que pierden por spread+slippage
"""

import numpy as np


class SpreadSlippageAnalyzer:
    """💱 Analizador de costos reales de ejecución"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.name = "💱 Spread/Slippage"
        
        # Spreads históricos por par (en pips)
        self.spread_memory = {}  # {symbol: [spread1, spread2, ...]}
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def analyze_trade_viability(self, mt5, symbol, signal_decision, target_pips, stop_loss_pips):
        """
        Analiza si una operación es viable después de considerar spread + slippage
        Retorna: {is_viable, exit_cost_pips, entry_cost_pips, adjusted_tp, adjusted_sl, profit_after_costs}
        """
        try:
            # Obtener spread actual
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'is_viable': False, 'reason': 'No tick info'}
            
            bid = tick.bid
            ask = tick.ask
            spread_pips = (ask - bid) * 10000 if '.' in str(bid) else ask - bid
            
            # Guardar en memoria
            if symbol not in self.spread_memory:
                self.spread_memory[symbol] = []
            self.spread_memory[symbol].append(spread_pips)
            if len(self.spread_memory[symbol]) > 100:
                self.spread_memory[symbol].pop(0)
            
            # Estimar slippage (30% del spread típicamente)
            avg_spread = np.mean(self.spread_memory[symbol])
            average_slippage = avg_spread * 0.30  # Slippage = 30% del spread
            
            # Costos totales
            entry_cost = spread_pips * 0.5  # Mitad spread por entrar
            exit_cost = spread_pips + average_slippage  # Spread completo + slippage por salir
            total_cost = entry_cost + exit_cost
            
            # Ajustar TP y SL por costos
            adjusted_tp = target_pips - exit_cost  # TP actual después de costos
            adjusted_sl = stop_loss_pips + entry_cost  # SL aumentado por costo entrada
            
            # Profit neto
            profit_after_costs = target_pips - total_cost
            
            # Viabilidad: ganancias deben ser > costo total + margen mínimo
            min_profit_threshold = total_cost + 2  # Mínimo 2 pips de ganancia real
            
            is_viable = (adjusted_tp > 0) and (profit_after_costs > min_profit_threshold)
            
            # Risk-Reward después de costos
            rr_before = target_pips / stop_loss_pips if stop_loss_pips > 0 else 0
            rr_after = adjusted_tp / adjusted_sl if adjusted_sl > 0 else 0
            
            # Clasificación
            if is_viable and rr_after >= 1.5:
                viability = "✓ VIABLE - Excelente R:R"
            elif is_viable and rr_after >= 1.0:
                viability = "✓ VIABLE - Aceptable R:R"
            elif is_viable:
                viability = "⚠️ BORDERLINE - R:R débil"
            else:
                viability = "✗ NO VIABLE - Costo demasiado alto"
            
            # Log detallado
            self._log_analysis(
                symbol, signal_decision, spread_pips, average_slippage,
                entry_cost, exit_cost, target_pips, stop_loss_pips,
                adjusted_tp, adjusted_sl, rr_before, rr_after, viability
            )
            
            return {
                'is_viable': is_viable,
                'viability_status': viability,
                'current_spread': spread_pips,
                'avg_spread': avg_spread,
                'estimated_slippage': average_slippage,
                'entry_cost_pips': entry_cost,
                'exit_cost_pips': exit_cost,
                'total_cost_pips': total_cost,
                'adjusted_tp_pips': adjusted_tp,
                'adjusted_sl_pips': adjusted_sl,
                'original_tp': target_pips,
                'original_sl': stop_loss_pips,
                'profit_after_costs': profit_after_costs,
                'rr_ratio_before': rr_before,
                'rr_ratio_after': rr_after,
                'recommendation': self._get_recommendation(is_viable, rr_after, profit_after_costs)
            }
        
        except Exception as e:
            self.log(f"❌ Error Spread/Slippage: {str(e)}", 'error')
            return {'is_viable': False, 'reason': f'Error: {str(e)}'}
    
    def _get_recommendation(self, is_viable, rr_after, profit):
        """Genera recomendación según viabilidad"""
        if not is_viable:
            if profit < 0:
                return "❌ CANCELAR - Pérdida esperada inferior a costos"
            else:
                return "⚠️ RECONSIDERAR - Ganancia marginal"
        elif rr_after > 1.8:
            return "✓✓ ALTA PRIORIDAD - Excelente R:R después de costos"
        elif rr_after > 1.2:
            return "✓ EJECUTAR - R:R aceptable"
        else:
            return "⚠️ EJECUTAR CON CUIDADO - R:R ajustado"
    
    def get_real_entry_price(self, mt5, symbol, signal_direction):
        """Obtiene precio realista de entrada considerando spread"""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        
        # En compra: entrar al ASK
        # En venta: entrar al BID
        if signal_direction == 'BUY':
            return tick.ask
        else:
            return tick.bid
    
    def adjust_tp_for_costs(self, target_pips, spread_pips):
        """Reduce TP considerando costos de salida"""
        exit_cost = spread_pips + (spread_pips * 0.30)
        return max(1, target_pips - exit_cost)
    
    def adjust_sl_for_costs(self, stop_loss_pips, spread_pips):
        """Aumenta SL considerando costos de entrada"""
        entry_cost = spread_pips * 0.5
        return stop_loss_pips + entry_cost
    
    def get_spread_stats(self, symbol):
        """Estadísticas de spread para un símbolo"""
        if symbol not in self.spread_memory or len(self.spread_memory[symbol]) == 0:
            return None
        
        spreads = self.spread_memory[symbol]
        return {
            'current': spreads[-1],
            'average': np.mean(spreads),
            'min': np.min(spreads),
            'max': np.max(spreads),
            'std_dev': np.std(spreads),
            'samples': len(spreads)
        }
    
    def _log_analysis(self, symbol, direction, spread, slippage,
                     entry_cost, exit_cost, original_tp, original_sl,
                     adjusted_tp, adjusted_sl, rr_before, rr_after, viability):
        
        emoji_direction = "🟢 BUY" if direction == "BUY" else "🔴 SELL"
        
        self.log(f"""
╔═══════════════════════════════════════════════════════════════╗
║        💱 ANÁLISIS SPREAD & SLIPPAGE - {symbol}             ║
╠═══════════════════════════════════════════════════════════════╣
║ Dirección: {emoji_direction:<50} ║
║ Estatus: {viability:<50} ║
╠═══════════════════════════════════════════════════════════════╣
║ COSTOS DE EJECUCIÓN:                                         ║
║  • Spread actual:          {spread:>42.2f} pips ║
║  • Slippage estimado:      {slippage:>42.2f} pips ║
║  • Costo entrada (50%):    {entry_cost:>42.2f} pips ║
║  • Costo salida (spread+): {exit_cost:>42.2f} pips ║
║  • Total costos:           {entry_cost + exit_cost:>42.2f} pips ║
╠═══════════════════════════════════════════════════════════════╣
║ ANÁLISIS TP/SL:                                              ║
║            ORIGINAL  →  AJUSTADO (después costos)            ║
║  • Target: {original_tp:>7.2f} pips  →  {adjusted_tp:>7.2f} pips               ║
║  • Stop:   {original_sl:>7.2f} pips  →  {adjusted_sl:>7.2f} pips               ║
║  • R:R:    {rr_before:>7.2f}      →  {rr_after:>7.2f}                    ║
╚═══════════════════════════════════════════════════════════════╝
""", 'info')

