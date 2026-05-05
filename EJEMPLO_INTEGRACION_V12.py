"""
📚 EJEMPLO DE INTEGRACIÓN - Cómo usar los 12 módulos en botiaver1.py

Este archivo muestra el patrón de integración propuesto.
Copiar y adaptar según necesidad en el bot principal.
"""

# ============================================================================
# IMPORTS - Agregar al inicio de botiaver1.py
# ============================================================================

# from super_analyzer import SuperAnalyzer
# from dynamic_score_calibration import DynamicScoreCalibration
# from recovery_potential_enhanced import RecoveryPotentialEnhanced
# from spread_slippage_analyzer import SpreadSlippageAnalyzer
# from time_based_session_filter import TimeBasedSessionFilter
# from correlation_analyzer import CorrelationAnalyzer


# ============================================================================
# INITIALIZATION - En __init__ de MT5AdaptiveTradingBot
# ============================================================================

class MT5AdaptiveTradingBot:
    def __init__(self):
        # ... existing code ...
        
        # 🎯 INICIALIZAR LOS 12 NUEVOS ANALIZADORES
        self.super_analyzer = SuperAnalyzer(log_callback=self.log)
        self.calibrator = DynamicScoreCalibration(log_callback=self.log)
        self.recovery = RecoveryPotentialEnhanced(log_callback=self.log)
        self.spread_analyzer = SpreadSlippageAnalyzer(log_callback=self.log)
        self.session_filter = TimeBasedSessionFilter(log_callback=self.log)
        self.correlation = CorrelationAnalyzer(log_callback=self.log)
        
        # Historial para calibración dinámica
        self.closed_trades_for_calibration = []


# ============================================================================
# ANALYZE FUNCTION - Nueva función central de análisis
# ============================================================================

def analyze_trade_opportunity_v12(self, symbol, timeframe='H1'):
    """
    🎯 ANÁLISIS COMPLETO CON LOS 12 MEJORAS
    
    Flujo:
    1. SuperAnalyzer (6 motores) → decisión base
    2. DynamicScoreCalibration → valida confianza según histórico
    3. TimeBasedSessionFilter → verifica sesión óptima
    4. CorrelationAnalyzer → valida con activos correlacionados
    5. RecoveryPotentialEnhanced → evalúa potencial de bounce
    6. SpreadSlippageAnalyzer → asegura viabilidad económica
    
    Retorna: {can_trade, signal, confidence, entry_price, tp, sl, reason}
    """
    
    try:
        # ─────────────────────────────────────────────────────────
        # PASO 1: SuperAnalyzer - Análisis base (6 motores)
        # ─────────────────────────────────────────────────────────
        self.log("="*70, 'info')
        self.log(f"🔍 Iniciando análisis V12 para {symbol}", 'info')
        self.log("="*70, 'info')
        
        super_result = self.super_analyzer.analyze_super(symbol)
        
        if super_result['decision'] == 'HOLD':
            return {
                'can_trade': False,
                'reason': 'SuperAnalyzer: Sin señal (HOLD)'
            }
        
        base_signal = super_result['decision']
        base_confidence = super_result['confidence']
        
        # ─────────────────────────────────────────────────────────
        # PASO 2: Validar umbral dinámico
        # ─────────────────────────────────────────────────────────
        is_valid, validation_reason = self.calibrator.validate_signal(
            'BUY' if base_signal == 'BUY' else 'SELL',
            base_confidence
        )
        
        if not is_valid and base_confidence < 30:
            return {
                'can_trade': False,
                'reason': f'Calibración: {validation_reason}'
            }
        
        # ─────────────────────────────────────────────────────────
        # PASO 3: Filtro de sesión temporal
        # ─────────────────────────────────────────────────────────
        can_trade_session, session_confidence, session_reason = self.session_filter.filter_signal(
            symbol,
            base_signal,
            base_confidence,
            strict_mode=False  # Cambiar a True para solo peak hours
        )
        
        adjusted_confidence = session_confidence
        
        if not can_trade_session:
            self.log(f"⏰ Sesión no óptima: {session_reason}", 'warning')
            # Aquí decidir si continuar o cancelar
            # Por ahora continuamos pero con confianza reducida
        
        # ─────────────────────────────────────────────────────────
        # PASO 4: Validar Correlaciones Multi-Activo
        # ─────────────────────────────────────────────────────────
        correlation_analysis = self.correlation.analyze_correlation_signal(
            self.mt5,
            symbol,
            base_signal
        )
        
        if not correlation_analysis['signal_confirmed']:
            self.log(f"🔗 ALERTA Correlación: {correlation_analysis['recommendation']}", 'warning')
            
            # Reducir confianza si hay conflictos
            if correlation_analysis['correlation_risk'] == 'HIGH':
                return {
                    'can_trade': False,
                    'reason': f"Correlación: {correlation_analysis['recommendation']}"
                }
            elif correlation_analysis['correlation_risk'] == 'MEDIUM':
                adjusted_confidence *= 0.85  # Reducir 15%
        
        # ─────────────────────────────────────────────────────────
        # PASO 5: Evaluar Potencial de Recuperación
        # ─────────────────────────────────────────────────────────
        recovery_result = self.recovery.analyze_recovery_potential(
            self.mt5,
            symbol,
            'H1'
        )
        
        recovery_score = recovery_result.get('recovery_score', 0)
        
        # Si la señal es "REVERSAL" pero recovery_score bajo, cancelar
        if recovery_score < 30 and 'DIVERGENCE' in str(super_result):
            self.log("🚀 Recuperación baja para señal de divergencia", 'warning')
            adjusted_confidence *= 0.7
        
        # ─────────────────────────────────────────────────────────
        # PASO 6: Validar Viabilidad Económica (Spread/Slippage)
        # ─────────────────────────────────────────────────────────
        
        # Obtener stops del SuperAnalyzer
        if 'stops' not in super_result:
            return {'can_trade': False, 'reason': 'No stops calculados'}
        
        stops = super_result['stops']
        
        viability = self.spread_analyzer.analyze_trade_viability(
            self.mt5,
            symbol,
            base_signal,
            target_pips=stops.get('tp_points', 40),
            stop_loss_pips=stops.get('sl_points', 20)
        )
        
        if not viability['is_viable']:
            return {
                'can_trade': False,
                'reason': f"Costos: {viability['recommendation']}"
            }
        
        # Usar stops ajustados por slippage
        final_tp_pips = viability['adjusted_tp_pips']
        final_sl_pips = viability['adjusted_sl_pips']
        
        # ─────────────────────────────────────────────────────────
        # DECISIÓN FINAL
        # ─────────────────────────────────────────────────────────
        
        # Requerimientos mínimos
        MIN_CONFIDENCE = 35  # Después de todos los filtros
        
        if adjusted_confidence < MIN_CONFIDENCE:
            return {
                'can_trade': False,
                'reason': f'Confianza final {adjusted_confidence:.0f}% < {MIN_CONFIDENCE}%'
            }
        
        # TRADE CONFIRMADO
        entry_price = viability['entry_price'] if 'entry_price' in viability else None
        
        self.log(f"""
╔════════════════════════════════════════════╗
║    ✅ TRADE CONFIRMADO - PRONTO A OPERAR  ║
╠════════════════════════════════════════════╣
║ Señal: {base_signal}
║ Confianza: {adjusted_confidence:.0f}%
║ Votos SuperAnalyzer: BUY={super_result['buy_votes']}/5
║ Risk:Reward: {viability['rr_ratio_after']:.2f}:1
║ Spread: {viability['current_spread']:.2f}pips
╚════════════════════════════════════════════╝
""", 'warning')
        
        return {
            'can_trade': True,
            'signal': base_signal,
            'confidence': adjusted_confidence,
            'entry_price': entry_price,
            'tp_pips': final_tp_pips,
            'sl_pips': final_sl_pips,
            'reason': 'Todos los análisis confirmaron',
            'metadata': {
                'super_votes': super_result['buy_votes'],
                'correlation_aligned': len(correlation_analysis['aligned_assets']),
                'recovery_score': recovery_score,
                'spread_cost': viability['total_cost_pips']
            }
        }
    
    except Exception as e:
        self.log(f"❌ Error en análisis V12: {str(e)}", 'error')
        return {'can_trade': False, 'reason': f'Error: {str(e)}'}


# ============================================================================
# MODIFICAR BOT_LOOP - Para usar el nuevo análisis
# ============================================================================

def bot_loop(self):
    """Modificar el loop existente para usar V12"""
    
    while self.is_running:
        try:
            # ... código existente de conexión ...
            
            symbol = self.symbol_var.get()
            
            # ✅ USAR NUEVO ANÁLISIS V12
            trade_decision = self.analyze_trade_opportunity_v12(symbol)
            
            if trade_decision['can_trade']:
                # Abrir posición con los parámetros validados
                position = self.open_trade(
                    symbol=symbol,
                    direction=trade_decision['signal'],
                    volume=self.position_size,
                    tp_pips=trade_decision['tp_pips'],
                    sl_pips=trade_decision['sl_pips']
                )
                
                if position:
                    # 📊 Registrar para Dynamic Calibration
                    self.closed_trades_for_calibration.append({
                        'signal': trade_decision['signal'],
                        'confidence': trade_decision['confidence'],
                        'entry': position['entry'],
                        'timestamp': datetime.now()
                    })
            else:
                self.log(f"⏭️ {trade_decision['reason']}", 'info')
            
            # ... resto del loop ...
            
            # Cada 10 trades, calibrar dinámicamente
            if len(self.closed_trades_for_calibration) % 10 == 0:
                self.calibrator.auto_calibrate()
        
        except Exception as e:
            self.log(f"Error bot_loop: {str(e)}", 'error')


# ============================================================================
# ACTUALIZAR UI - Mostrar información de los 12 módulos
# ============================================================================

def update_ui_with_v12_data(self):
    """Mostrar datos de los 12 análisis en UI"""
    
    # Tab 1: SuperAnalyzer Votes
    # Mostrar tabla con votos de cada especialista
    
    # Tab 2: Session Status
    session_quality = self.session_filter.get_session_quality()
    # Mostrar liquidez, volatilidad, sesión actual
    
    # Tab 3: Correlation Status
    # Mostrar activos alineados/conflictivos
    
    # Tab 4: Spread & Slippage
    spread_stats = self.spread_analyzer.get_spread_stats(self.symbol_var.get())
    # Mostrar spread promedio, slippage estimado
    
    # Tab 5: Dynamic Calibration
    calib_stats = self.calibrator.get_statistics_summary()
    # Mostrar win_rate, umbrales dinámicos actuales


# ============================================================================
# REGISTRO DE OPERACIONES CERRADAS - Para Calibración
# ============================================================================

def on_trade_closed(self, entry_price, exit_price, direction, pnl_pips):
    """Llamar cuando se cierre una operación"""
    
    # Registrar en calibrador
    self.calibrator.record_trade(
        signal_type='BUY' if direction == 1 else 'SELL',
        confidence=self.last_confidence,  # Guardar confianza del trade
        entry_price=entry_price,
        exit_price=exit_price,
        pnl_pips=pnl_pips
    )
    
    # Cada 50 trades, auto-calibrar
    if self.calibrator.stats['total_trades'] % 50 == 0:
        self.calibrator.auto_calibrate()


# ============================================================================
# FIN - Estos son los 3 puntos principales de modificación
# ============================================================================

"""
RESUMEN DE CAMBIOS NECESARIOS:

1. IMPORTS: Agregar importaciones de 6 nuevos módulos

2. __init__: Instanciar 6 objetos analizadores con log_callback

3. NUEVO MÉTODO: analyze_trade_opportunity_v12()
   - Coordina los 6 análisis en secuencia
   - Retorna decisión final validada

4. MOD bot_loop(): 
   - Reemplazar análisis antiguo con analyze_trade_opportunity_v12()
   - Registrar operaciones cerradas para calibración

5. MOD on_trade_closed():
   - Agregar registro en DynamicScoreCalibration

6. OPCIONAL - UI:
   - Agregar tabs para mostrar estado de los 6 módulos
   - Mostrar Dynamic Calibration stats

CLASES NECESARIAS EN botiaver1.py:
- SuperAnalyzer ✓
- DynamicScoreCalibration ✓
- RecoveryPotentialEnhanced ✓
- SpreadSlippageAnalyzer ✓
- TimeBasedSessionFilter ✓
- CorrelationAnalyzer ✓
"""

