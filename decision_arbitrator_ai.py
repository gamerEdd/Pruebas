import numpy as np
import MetaTrader5 as mt5
import mt5_safe
from datetime import datetime
from safety_filters_manager import SafetyFiltersManager  # [EMOJI]️ Filtros institucionales
from micro_momentum_engine_v2 import MicroMomentumEngineV2  # ⭐ NUEVO: Micro momentum calibrado

class DecisionArbitratorAI:
    """IA Árbitro que analiza las señales de BUY y SELL specialists y toma la decisión final"""
    
    def __init__(self, log_callback=None, dataset_manager=None, symbol='GOLD', micro_profile='MICRO'):
        self.log_callback = log_callback
        self.dataset_manager = dataset_manager  # [OK] Professional Dataset Manager
        self.name = "Decision Arbitrator"
        self.symbol = symbol
        
        # ⭐ NUEVO: Micro Momentum Engine V2 - Calibrado para micromovimientos (5-10 pips)
        self.micro_momentum_engine = MicroMomentumEngineV2(
            log_callback=log_callback,
            symbol=symbol,
            profile=micro_profile  # 'ULTRA_MICRO' (5-7 pips), 'MICRO' (10-15 pips), 'NORMAL' (20+ pips)
        )
        
        # ⭐ NUEVO: Trend Detector (será inyectado desde botiaver1.py)
        self.trend_detector = None
        
        # [EMOJI]️ Inicializar filtros de seguridad institucionales
        self.safety_filters = SafetyFiltersManager(log_callback=log_callback)
        
        # Umbrales calibrados para más oportunidades
        self.thresholds = {
            'min_score_difference': 10,    # Reducido de 15 a 12
            'min_absolute_score': 30,      # Reducido de 50 a 35
            'min_confidence': 30,          # Reducido de 45 a 35
            'strong_signal_score': 50,     # Reducido de 69 a 55
            'strong_confidence': 45,       # Reducido de 65 a 50
            'max_conflict_threshold': 25   # Aumentado de 15 a 20
        }
        
        # Pesos rebalanceados
        self.decision_weights = {
            'score_difference': 0.40,      # Aumentado para dar más peso a diferencias claras
            'confidence_level': 0.25,      # Mantenido
            'market_context': 0.20,        # Reducido
            'signal_quality': 0.15         # Reducido
        }
        
        # Historial de decisiones para aprendizaje
        self.decision_history = []
        self.max_history = 50
        
        # [EMOJI] Insights del dataset profesional
        self.dataset_insights = None
        self.dataset_enabled = dataset_manager is not None
    
    def set_micro_profile(self, profile):
        """Cambiar perfil de micro momentum dinámicamente"""
        if hasattr(self, 'micro_momentum_engine'):
            self.micro_momentum_engine.set_profile(profile)
    
    def arbitrate(self, buy_analysis, sell_analysis, symbol):
        """Versión mejorada del arbitraje con más filtros"""
        try:
            # Validar análisis
            if not buy_analysis or not sell_analysis:
                self.log("[ADVERTENCIA] Análisis incompleto de especialistas", 'warning')
                return self._create_hold_decision("Análisis incompleto")
            
            # Extraer scores y confianzas
            buy_score = buy_analysis['score']
            buy_conf = buy_analysis['confidence']
            sell_score = sell_analysis['score']
            sell_conf = sell_analysis['confidence']

            # NUEVO: Verificar calidad mínima de señales
            if max(buy_score, sell_score) < self.thresholds['min_absolute_score']:
                return self._create_hold_decision("Señales débiles - No operar")

            # NUEVO: Verificar confianza mínima
            if max(buy_conf, sell_conf) < self.thresholds['min_confidence']:
                return self._create_hold_decision("Baja confianza - No operar")

            # [EMOJI]️ FILTROS DE SEGURIDAD INSTITUCIONALES
            try:
                is_market_safe, safety_checks = self.safety_filters.run_all_checks()
                # Protección: safety_checks debe ser dict, no string
                if isinstance(safety_checks, dict):
                    self.log(self.safety_filters.get_filter_summary(safety_checks), 'info')
                    if not is_market_safe:
                        failed_filters = [name for name, (safe, _) in safety_checks.items() if not safe]
                        reason = f"Filtros de seguridad: {', '.join(failed_filters)}"
                        self.log(f"[STOP] RECHAZADO POR FILTROS: {reason}", 'warning')
                        return self._create_hold_decision(reason)
                else:
                    self.log(f"[WARNING] safety_checks debe ser dict, es {type(safety_checks)}: {safety_checks}", 'warning')
                    if not is_market_safe:
                        self.log("[STOP] RECHAZADO POR FILTROS DE SEGURIDAD", 'warning')
                        return self._create_hold_decision("Filtros de seguridad fallaron")
            except Exception as e:
                self.log(f"[ERROR] Error en filtros de seguridad: {str(e)}", 'error')
                pass

            # NUEVO: Verificar condiciones de mercado
            market_context = self._analyze_market_context(symbol)
            if market_context.get('valid'):
                # No operar si volatilidad muy alta
                if market_context['volatility'] > 0.4:
                    return self._create_hold_decision("Volatilidad excesiva")
                    
                # No operar si spread alto
                if market_context.get('spread_ratio', 0) > 0.8:
                    return self._create_hold_decision("Spread muy alto")

            # NUEVO: Verificar alineación de timeframes
            timeframe_alignment = self._check_timeframe_alignment(symbol)
            if not timeframe_alignment['aligned']:
                return self._create_hold_decision("Timeframes no alineados")

            # Log de análisis recibidos
            self.log(f"""
╔══════════════════════════════════════════════╗
║        ANÁLISIS DE ESPECIALISTAS             ║
╠══════════════════════════════════════════════╣
║ [OK] BUY Specialist:                           ║
║    Score: {buy_score:.1f} | Confianza: {buy_conf}%         ║
║    Recomendación: {buy_analysis['recommendation']}       ║
║                                              ║
║ 🔴 SELL Specialist:                          ║
║    Score: {sell_score:.1f} | Confianza: {sell_conf}%         ║
║    Recomendación: {sell_analysis['recommendation']}      ║
╚══════════════════════════════════════════════╝
""", 'info')
            
            # 1. Detectar señales muy fuertes (obvias)
            strong_decision = self._check_strong_signals(buy_analysis, sell_analysis)
            if strong_decision:
                return strong_decision
            
            # 2. Detectar conflicto de señales
            if self._is_conflicted(buy_score, sell_score, buy_conf, sell_conf):
                return self._resolve_conflict(buy_analysis, sell_analysis, symbol)
            
            # 3. Análisis normal - calcular diferencias
            score_diff = abs(buy_score - sell_score)
            
            # 4. Verificar si hay diferencia significativa
            if score_diff < self.thresholds['min_score_difference']:
                return self._create_hold_decision(
                    f"Diferencia insuficiente ({score_diff:.1f} < {self.thresholds['min_score_difference']})"
                )
            
            # 5. Determinar dirección ganadora
            if buy_score > sell_score:
                winner = 'BUY'
                winner_analysis = buy_analysis
                loser_score = sell_score
            else:
                winner = 'SELL'
                winner_analysis = sell_analysis
                loser_score = buy_score
            
            # 6. Verificar umbrales mínimos
            if winner_analysis['score'] < self.thresholds['min_absolute_score']:
                return self._create_hold_decision(
                    f"Score insuficiente ({winner_analysis['score']:.1f} < {self.thresholds['min_absolute_score']})"
                )
            
            if winner_analysis['confidence'] < self.thresholds['min_confidence']:
                return self._create_hold_decision(
                    f"Confianza insuficiente ({winner_analysis['confidence']}% < {self.thresholds['min_confidence']}%)"
                )
            
            # NUEVO: Condiciones adicionales para señales fuertes
            if winner == 'BUY':
                if not self._validate_buy_conditions(winner_analysis, market_context):
                    return self._create_hold_decision("Condiciones BUY no óptimas")
            else:
                if not self._validate_sell_conditions(winner_analysis, market_context):
                    return self._create_hold_decision("Condiciones SELL no óptimas")

            # 7. Análisis de contexto del mercado
            market_context = self._analyze_market_context(symbol)
            
            # 8. Calcular score final de decisión
            final_score = self._calculate_final_decision_score(
                winner_analysis, loser_score, market_context
            )
            
            # 9. Generar razonamiento
            reasoning = self._generate_decision_reasoning(
                winner, winner_analysis, loser_score, score_diff, market_context
            )
            
            # 10. Crear decisión final
            decision = {
                'decision': winner,
                'confidence': final_score,
                'reasoning': reasoning,
                'details': {
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'score_difference': score_diff,
                    'market_context': market_context,
                    'winner_recommendation': winner_analysis['recommendation'],
                    'winner_features': winner_analysis['features']
                }
            }
            
            # ========== BLOQUE NUEVO: VALIDACIÓN MICRO MOMENTUM ==========
            # ⭐ Integración de MicroMomentumEngineV2 para detectar micromovimientos
            # Caso de uso: GOLD 5025→5019 (6 pips) debe detectarse como STRONG_SELL
            
            if winner and winner in ('BUY', 'SELL'):
                try:
                    micro_eval = self.micro_momentum_engine.evaluate(
                        symbol=symbol,
                        predicted_direction=winner
                    )
                    
                    if micro_eval['decision'] in ['STRONG_BUY', 'STRONG_SELL']:
                        # Micromomentum detectó un movimiento fuerte
                        movement_pips = micro_eval['tick_analytics'].get('movement_pips', 0)
                        confidence_bonus = min(15, int(movement_pips / 2))  # +1% por cada 2 pips
                        
                        decision['confidence'] = min(100, decision['confidence'] + confidence_bonus)
                        decision['micro_momentum'] = {
                            'decision': micro_eval['decision'],
                            'movement_pips': movement_pips,
                            'volatility_pips': micro_eval['tick_analytics'].get('volatility_pips', 0),
                            'confidence_bonus': confidence_bonus
                        }
                        
                        self.log(
                            f"✅ MICRO MOMENTUM VALIDA: {micro_eval['decision']} | "
                            f"{movement_pips:.1f} pips | "
                            f"Conf +{confidence_bonus}% → {decision['confidence']:.0f}%",
                            'success'
                        )
                    
                    elif micro_eval['decision'] == 'INVERT':
                        # Micromomentum invierte la decisión
                        self.log(
                            f"⚠️ MICRO MOMENTUM INVIERTE: {winner} → {micro_eval['final_direction']} | "
                            f"{micro_eval['tick_analytics'].get('movement_pips', 0):.1f} pips",
                            'warning'
                        )
                        # Opción: cambiar decisión o rechazar
                        # decision['final_direction'] = micro_eval['final_direction']
                        # Por defecto, rechazar si hay inversión fuerte
                        if micro_eval['tick_analytics'].get('volatility_pips', 0) > 5:
                            self.log(f"❌ Rechazo inversión micro: volatilidad alta", 'warning')
                            return self._create_hold_decision(
                                f"Micromomentum invierte a {micro_eval['final_direction']}"
                            )
                    
                    elif micro_eval['decision'] == 'CONFLICT':
                        # Conflicto detectado
                        self.log(
                            f"⚠️ MICRO MOMENTUM EN CONFLICTO: {micro_eval.get('reason', 'desconocido')}",
                            'warning'
                        )
                        decision['confidence'] = max(0, decision['confidence'] - 10)
                    
                    else:
                        # CONFIRM normal - sin cambios
                        self.log(
                            f"✓ Micro: Confirma dirección ({micro_eval['reason'][:60]}...)",
                            'info'
                        )
                
                except Exception as e:
                    self.log(f"[WARN] Error en validación micro: {str(e)[:50]}", 'warning')
                    pass
            
            # Registrar en historial
            self._add_to_history(decision)
            
            # Log de decisión final
            self.log(f"""
╔══════════════════════════════════════════════╗
║           DECISIÓN FINAL                     ║
╠══════════════════════════════════════════════╣
║ [EMOJI]️ Dirección: {winner}                          ║
║ 💯 Confianza: {decision['confidence']:.1f}%                     ║
║ [DATA] Diferencia: {score_diff:.1f} puntos              ║
║ [OBJETIVO] Recomendación: {winner_analysis['recommendation']}  ║
║ 🔬 Micro Profile: {self.micro_momentum_engine.profile_name}  ║
╚══════════════════════════════════════════════╝
""", 'success' if winner else 'info')
            
            for reason in reasoning:
                self.log(f"   • {reason}", 'info')
            
            return decision
            
        except Exception as e:
            self.log(f"[ERROR] Error en arbitraje: {str(e)}", 'error')
            return self._create_hold_decision(f"Error: {str(e)}")

    def allow_trade(self, buy_analysis, sell_analysis, symbol, context=None):
        """Gatekeeper API: devuelve solo allow (True/False), score y razones.
        Mantiene checks críticos del arbitraje pero NO decide dirección.
        """
        reasons = []
        try:
            if not buy_analysis or not sell_analysis:
                reasons.append("Análisis incompleto de especialistas")
                return {'allow': False, 'score': 0, 'reasons': reasons}

            buy_score = buy_analysis.get('score', 0)
            sell_score = sell_analysis.get('score', 0)
            buy_conf = buy_analysis.get('confidence', 0)
            sell_conf = sell_analysis.get('confidence', 0)

            ctx = context or {}
            min_absolute_score = float(ctx.get('min_absolute_score', self.thresholds['min_absolute_score']))
            min_confidence = float(ctx.get('min_confidence', self.thresholds['min_confidence']))
            min_score_difference = float(ctx.get('min_score_difference', self.thresholds['min_score_difference']))

            # Calidad mínima
            if max(buy_score, sell_score) < min_absolute_score:
                reasons.append('Señales débiles')
                return {'allow': False, 'score': max(buy_score, sell_score), 'reasons': reasons}

            if max(buy_conf, sell_conf) < min_confidence:
                reasons.append('Baja confianza')
                return {'allow': False, 'score': max(buy_conf, sell_conf), 'reasons': reasons}

            # Contexto de mercado
            market_context = self._analyze_market_context(symbol)
            if market_context.get('valid'):
                if market_context.get('volatility', 0) > 0.4:
                    reasons.append('Volatilidad excesiva')
                    return {'allow': False, 'score': 0, 'reasons': reasons}
                if market_context.get('spread_ratio', 0) > 0.8:
                    reasons.append('Spread muy alto')
                    return {'allow': False, 'score': 0, 'reasons': reasons}

            # Timeframe alignment
            tf = self._check_timeframe_alignment(symbol)
            if not tf.get('aligned', True):
                reasons.append('Timeframes no alineados')
                return {'allow': False, 'score': 0, 'reasons': reasons}

            # Conflicto
            if self._is_conflicted(buy_score, sell_score, buy_conf, sell_conf):
                reasons.append('Conflicto entre especialistas')
                return {'allow': False, 'score': 0, 'reasons': reasons}

            # Validar que la dirección ganadora sea coherente con el contexto de mercado
            winner = 'BUY' if buy_score >= sell_score else 'SELL'
            if market_context.get('valid'):
                if winner == 'BUY' and not self._validate_buy_conditions(buy_analysis, market_context):
                    reasons.append('Mercado bajista — dirección BUY bloqueada')
                    return {'allow': False, 'score': buy_score, 'reasons': reasons}
                if winner == 'SELL' and not self._validate_sell_conditions(sell_analysis, market_context):
                    reasons.append('Mercado alcista — dirección SELL bloqueada')
                    return {'allow': False, 'score': sell_score, 'reasons': reasons}

            # Diferencia mínima
            if abs(buy_score - sell_score) < min_score_difference:
                reasons.append('Diferencia insuficiente entre scores')
                return {'allow': False, 'score': abs(buy_score - sell_score), 'reasons': reasons}

            # Si pasamos todos los filtros, permitir
            final_score = max(buy_score, sell_score)
            reasons.append('Filtros duros OK')
            return {'allow': True, 'score': final_score, 'reasons': reasons}

        except Exception as e:
            self.log(f"[ERROR] Error allow_trade: {e}", 'error')
            return {'allow': False, 'score': 0, 'reasons': [str(e)]}
    
    def _check_strong_signals(self, buy_analysis, sell_analysis):
        """Detecta señales obviamente fuertes que no requieren más análisis"""
        buy_score = buy_analysis['score']
        buy_conf = buy_analysis['confidence']
        sell_score = sell_analysis['score']
        sell_conf = sell_analysis['confidence']
        
        # Señal BUY más permisiva
        if (buy_score >= 40 and          # Reducido de 69 
            buy_conf >= 45 and           # Reducido de 60
            buy_score - sell_score >= 10):  # Reducido de 15
            
            return {
                'decision': 'BUY',
                'confidence': min(90, (buy_score + buy_conf) / 2),
                'reasoning': [
                    "🌟 SEÑAL DE COMPRA detectada",
                    f"Score BUY ({buy_score:.1f}) supera a SELL ({sell_score:.1f})",
                    f"Confianza suficiente: {buy_conf}%",
                    "Indicadores alineados"
                ]
            }
        
        # Señal SELL más permisiva
        if (sell_score >= 40 and        # Reducido de 69
            sell_conf >= 45 and         # Reducido de 60
            sell_score - buy_score >= 10):  # Reducido de 15
            
            return {
                'decision': 'SELL',
                'confidence': min(90, (sell_score + sell_conf) / 2),
                'reasoning': [
                    "🌟 SEÑAL DE VENTA detectada", 
                    f"Score SELL ({sell_score:.1f}) supera a BUY ({buy_score:.1f})",
                    f"Confianza suficiente: {sell_conf}%",
                    "Indicadores alineados"
                ]
            }
        
        return None
    
    def _calculate_confidence(self, features, scores):
        """Calcula el nivel de confianza con criterios más permisivos"""
        # Contar señales fuertes y medias con umbrales más bajos
        strong_signals = sum(1 for s in scores.values() if s >= 70)  # Reducido de 85
        medium_signals = sum(1 for s in scores.values() if 50 <= s < 70)  # Rango más permisivo
        
        # Calcular confianza base más permisiva
        confidence = 0
        
        if strong_signals >= 3:
            confidence = 90
        elif strong_signals >= 2:
            confidence = 80
        elif strong_signals >= 1 and medium_signals >= 2:
            confidence = 70
        elif medium_signals >= 3:
            confidence = 65
        elif medium_signals >= 2:
            confidence = 60
        else:
            confidence = 50  # Base más alta (antes 45)
            
        return confidence
    
    def _is_conflicted(self, buy_score, sell_score, buy_conf, sell_conf):
        """Detecta si hay conflicto entre señales con criterios más permisivos"""
        # Scores similares con mayor tolerancia
        score_diff = abs(buy_score - sell_score)
        if score_diff <= self.thresholds['max_conflict_threshold']:
            return True
        
        # Ambos con scores moderados (antes altos)
        if buy_score >= 60 and sell_score >= 60:  # Reducido de 70
            return True
        
        # Ambos con confianza moderada
        if buy_conf >= 65 and sell_conf >= 65 and score_diff < 25:  # Reducido de 80/80/20
            return True
        
        return False
    
    def _resolve_conflict(self, buy_analysis, sell_analysis, symbol):
        """Resuelve conflictos entre señales usando análisis adicional"""
        self.log("[ADVERTENCIA] CONFLICTO detectado entre señales - Análisis profundo...", 'warning')
        
        # Análisis de desempate
        tiebreakers = []
        
        # 1. Tendencia de largo plazo
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
        if rates is not None:
            close = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
            long_trend = (close[-1] - close[0]) / close[0] * 100
            
            if long_trend > 0.3:
                tiebreakers.append(('BUY', 15, f"Tendencia largo plazo alcista ({long_trend:.2f}%)"))
            elif long_trend < -0.3:
                tiebreakers.append(('SELL', 15, f"Tendencia largo plazo bajista ({long_trend:.2f}%)"))
        
        # 2. Volatilidad reciente
        if rates is not None:
            volatility = np.std(close[-20:]) / np.mean(close[-20:]) * 100
            if volatility > 0.5:
                # Alta volatilidad = esperar
                return self._create_hold_decision(
                    f"Alta volatilidad durante conflicto ({volatility:.2f}%)"
                )
        
        # 3. Comparar razonamientos
        buy_reasons = len(buy_analysis.get('reasoning', []))
        sell_reasons = len(sell_analysis.get('reasoning', []))
        
        if buy_reasons > sell_reasons + 2:
            tiebreakers.append(('BUY', 10, f"Más indicadores BUY ({buy_reasons} vs {sell_reasons})"))
        elif sell_reasons > buy_reasons + 2:
            tiebreakers.append(('SELL', 10, f"Más indicadores SELL ({sell_reasons} vs {buy_reasons})"))
        
        # Decidir basado en tiebreakers
        if tiebreakers:
            buy_points = sum(pts for dir, pts, _ in tiebreakers if dir == 'BUY')
            sell_points = sum(pts for dir, pts, _ in tiebreakers if dir == 'SELL')
            
            if buy_points > sell_points:
                return {
                    'decision': 'BUY',
                    'confidence': 65,
                    'reasoning': [
                        "[EMOJI]️ Conflicto resuelto a favor de BUY",
                        *[reason for dir, _, reason in tiebreakers if dir == 'BUY']
                    ],
                    'details': {'conflict_resolved': True, 'tiebreakers': tiebreakers}
                }
            elif sell_points > buy_points:
                return {
                    'decision': 'SELL',
                    'confidence': 65,
                    'reasoning': [
                        "[EMOJI]️ Conflicto resuelto a favor de SELL",
                        *[reason for dir, _, reason in tiebreakers if dir == 'SELL']
                    ],
                    'details': {'conflict_resolved': True, 'tiebreakers': tiebreakers}
                }
        
        # Si no se puede resolver, HOLD
        return self._create_hold_decision("Conflicto irresoluble - Mercado indeciso")
    
    def _analyze_market_context(self, symbol):
        """Analiza el contexto general del mercado"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
            if rates is None:
                return {'valid': False}
            
            close = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
            volume = np.array([r[5] for r in rates])
            
            # Calcular SMA de volumen
            volume_sma = np.mean(volume[-20:])
            
            return {
                'valid': True,
                'volatility': np.std(close[-20:]) / np.mean(close[-20:]) * 100,
                'avg_volume': np.mean(volume[-20:]),
                'price_trend': (close[-1] - close[-50]) / close[-50] * 100,
                'recent_momentum': (close[-1] - close[-10]) / close[-10] * 100,
                'volume_sma': volume_sma,
                'spread_ratio': self._get_spread_ratio(symbol)  # Nuevo: relación de spread
            }
        except:
            return {'valid': False}
    
    def _get_spread_ratio(self, symbol):
        """Obtiene la relación del spread actual"""
        try:
            # Obtener precios de compra y venta
            bid = mt5.symbol_info_tick(symbol).bid
            ask = mt5.symbol_info_tick(symbol).ask
            
            # Calcular spread en puntos
            spread_points = ask - bid
            
            # Obtener el valor en puntos del spread mínimo
            min_spread_points = mt5.symbol_info(symbol).spread
            
            # Calcular y retornar la relación del spread
            return spread_points / min_spread_points if min_spread_points > 0 else 0
        except:
            return 0
    
    def _calculate_final_decision_score(self, winner_analysis, loser_score, market_context):
        """Calcula el score final de la decisión"""
        base_score = winner_analysis['score']
        confidence = winner_analysis['confidence']
        
        # Factor de diferencia
        diff_factor = min(20, (base_score - loser_score) * 0.5)
        
        # Factor de contexto
        context_factor = 0
        if market_context['valid']:
            # Reducir confianza si alta volatilidad
            if market_context['volatility'] > 0.5:
                context_factor -= 5
            # Aumentar si momentum alineado
            if winner_analysis['direction'] == 'BUY' and market_context['recent_momentum'] > 0.1:
                context_factor += 5
            elif winner_analysis['direction'] == 'SELL' and market_context['recent_momentum'] < -0.1:
                context_factor += 5
        
        # Score final
        final = (base_score * 0.5) + (confidence * 0.3) + diff_factor + context_factor
        return min(99, max(60, final))
    
    def _generate_decision_reasoning(self, direction, winner_analysis, loser_score, score_diff, market_context):
        """Genera el razonamiento detallado de la decisión"""
        reasons = [f"Dirección {direction} seleccionada"]
        
        # Agregar razones del especialista ganador
        reasons.extend(winner_analysis.get('reasoning', []))
        
        # Agregar diferencia de scores
        reasons.append(f"Ventaja de {score_diff:.1f} puntos sobre dirección contraria")
        
        # Agregar contexto de mercado
        if market_context['valid']:
            if abs(market_context['recent_momentum']) > 0.15:
                mom_dir = "alcista" if market_context['recent_momentum'] > 0 else "bajista"
                reasons.append(f"Momentum reciente {mom_dir} ({market_context['recent_momentum']:.2f}%)")
        
        return reasons
    
    def _create_hold_decision(self, reason):
        """Crea una decisión de HOLD con razón"""
        return {
            'decision': 'HOLD',
            'confidence': 0,
            'reasoning': [reason],
            'details': {}
        }
    
    def _add_to_history(self, decision):
        """Agrega decisión al historial"""
        self.decision_history.append({
            'timestamp': datetime.now(),
            'decision': decision
        })
        
        # Mantener solo últimas N decisiones
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)
    
    def get_decision_stats(self):
        """Obtiene estadísticas de decisiones tomadas"""
        if not self.decision_history:
            return None
        
        buy_count = sum(1 for d in self.decision_history if d['decision']['decision'] == 'BUY')
        sell_count = sum(1 for d in self.decision_history if d['decision']['decision'] == 'SELL')
        hold_count = sum(1 for d in self.decision_history if d['decision']['decision'] == 'HOLD')
        
        return {
            'total': len(self.decision_history),
            'buy': buy_count,
            'sell': sell_count,
            'hold': hold_count,
            'buy_rate': buy_count / len(self.decision_history) * 100,
            'sell_rate': sell_count / len(self.decision_history) * 100
        }
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def _validate_buy_conditions(self, analysis, market_context):
        """NUEVO: Validación específica para compras"""
        if not market_context.get('valid'):
            return True  # Si no hay contexto, permitir
            
        # Verificar tendencia
        if market_context['price_trend'] < -0.1:
            return False  # No comprar en tendencia bajista fuerte
            
        # Verificar momentum
        if market_context['recent_momentum'] < -0.05:
            return False  # No comprar con momentum negativo
            
        # Verificar volumen
        if market_context['avg_volume'] < market_context.get('volume_sma', 0):
            return False  # Volumen debe confirmar
            
        return True

    def _validate_sell_conditions(self, analysis, market_context):
        """NUEVO: Validación específica para ventas"""
        if not market_context.get('valid'):
            return True  # Si no hay contexto, permitir
            
        # Verificar tendencia
        if market_context['price_trend'] > 0.1:
            return False  # No vender en tendencia alcista fuerte
            
        # Verificar momentum
        if market_context['recent_momentum'] > 0.05:
            return False  # No vender con momentum positivo
            
        # Verificar volumen
        if market_context['avg_volume'] < market_context.get('volume_sma', 0):
            return False  # Volumen debe confirmar
            
        return True

    def _check_timeframe_alignment(self, symbol):
        """NUEVO: Verificar alineación de diferentes timeframes"""
        try:
            timeframes = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15]
            trends = []
            
            for tf in timeframes:
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, 50)
                if rates is not None:
                    close = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
                    sma20 = np.mean(close[-20:])
                    sma50 = np.mean(close[-50:])
                    trends.append(1 if sma20 > sma50 else -1)
            
            # Verificar si al menos 2 timeframes están alineados
            aligned = len(set(trends)) == 1  # Todos alineados
            partially_aligned = trends.count(trends[0]) >= 2  # Al menos 2 alineados
            
            return {
                'aligned': aligned or partially_aligned,
                'trend': 'UP' if sum(trends) > 0 else 'DOWN',
                'strength': abs(sum(trends)) / len(trends)
            }
            
        except Exception as e:
            self.log(f"Error en alineación de timeframes: {str(e)}", 'error')
            return {'aligned': True}  # Por defecto permitir