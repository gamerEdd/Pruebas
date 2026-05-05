"""
🎯 SUPER ANALYZER - Integrador Central de 12 Mejoras
Combina todos los análisis: Ensemble, NN, MultiFrame, Volatility, Divergence, Patterns
Coordinador central que decide la señal FINAL
"""

import numpy as np
from ensemble_predictor_ai import EnsemblePredictorAI

# Import condicional - TensorFlow puede no estar disponible
try:
    from neural_network_predictor import NeuralNetworkPredictor
    NEURAL_NET_AVAILABLE = True
except (ImportError, Exception):
    NEURAL_NET_AVAILABLE = False
    NeuralNetworkPredictor = None

from multi_frame_analyzer import MultiFrameAnalyzer
from volatility_adjusted_entry import VolatilityAdjustedEntry
from divergence_detector import DivergenceDetector
from pattern_recognizer import PatternRecognizer


class SuperAnalyzer:
    """🎯 Centro de Inteligencia - Armoniza 12 mejoras de predicción"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.name = "🎯 Super Analyzer"
        
        # Inicializar 6 motores de análisis
        self.ensemble = EnsemblePredictorAI(log_callback)
        self.neural_net = NeuralNetworkPredictor(log_callback) if NEURAL_NET_AVAILABLE else None
        self.multiframe = MultiFrameAnalyzer(log_callback)
        self.volatility_adj = VolatilityAdjustedEntry(log_callback)
        self.divergence = DivergenceDetector(log_callback)
        self.pattern = PatternRecognizer(log_callback)
        
        # Pesos relativos de cada motor (suman 1.0)
        # Si NN no está disponible, sus pesos se redistribuyen a los otros
        if NEURAL_NET_AVAILABLE:
            self.weights = {
                'ensemble': 0.25,      # 25% - Base sólida
                'neural_net': 0.15,    # 15% - ML
                'multiframe': 0.20,    # 20% - Jerárquico
                'divergence': 0.18,    # 18% - Reversal  
                'pattern': 0.12,       # 12% - Patrón
                'volatility': 0.10     # 10% - Entrada dinámica (no vota, solo ajusta)
            }
        else:
            # Pesos sin NN: 15% redistribuidos a ensemble y multiframe
            self.weights = {
                'ensemble': 0.30,      # +5% - compensar sin NN
                'neural_net': 0.0,     # No disponible
                'multiframe': 0.25,    # +5% - compensar sin NN
                'divergence': 0.18,    # 18% - Reversal  
                'pattern': 0.12,       # 12% - Patrón
                'volatility': 0.15     # +5% - Entrada dinámica
            }
            # TensorFlow no disponible - usar configuración sin NN (silencioso)
        
        self.analysis_history = []
    
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    def analyze_super(self, symbol):
        """
        Super-análisis que combina 6 motores independientes
        Retorna decisión consensuada con detalles de cada motor
        """
        try:
            self.log("\n" + "="*70, 'info')
            motor_count = 6 if NEURAL_NET_AVAILABLE else 5
            self.log(f"🎯 INICIANDO SUPER-ANÁLISIS - {motor_count} MOTORES EN PARALELO", 'info')
            self.log("="*70, 'info')
            
            # Ejecutar todos los análisis EN PARALELO (mentalmente)
            results = {
                'ensemble': self.ensemble.predict(symbol),
                'neural_net': self.neural_net.predict(symbol) if NEURAL_NET_AVAILABLE else None,
                'multiframe': self.multiframe.analyze_synchronized(symbol),
                'divergence': self.divergence.detect_divergences(symbol, 'H1'),
                'pattern': self.pattern.detect_patterns(symbol, 'M5'),
                'volatility_state': self.volatility_adj.get_volatility_state(symbol)
            }
            
            # Sintetizar decisión final
            final_decision = self._synthesize_decision(symbol, results)
            
            # Calcular stops dinámicos
            if final_decision['decision'] in ['BUY', 'SELL']:
                stops = self.volatility_adj.calculate_dynamic_stops(
                    symbol, 
                    final_decision['decision'],
                    1.0  # Volume default
                )
                final_decision['stops'] = stops
            
            # Log final
            self._log_super_analysis(final_decision, results)
            
            # Guardar en historial
            self.analysis_history.append({'timestamp': None, 'decision': final_decision})
            
            return final_decision
        
        except Exception as e:
            self.log(f"❌ Error Super Analyzer: {str(e)}", 'error')
            return {
                'decision': 'HOLD',
                'confidence': 0,
                'reason': f'Error: {str(e)}'
            }
    
    def _synthesize_decision(self, symbol, results):
        """Sintetiza decisión de 6 motores con ponderación y override"""
        try:
            votes = {}
            confidences = {}
            
            # Extraer votos y confianzas  
            votes['ensemble'] = results['ensemble'].get('decision', 'HOLD')
            confidences['ensemble'] = results['ensemble'].get('ensemble_confidence', 0)
            
            # Neural Net solo si está disponible
            if results['neural_net'] is not None:
                votes['neural_net'] = results['neural_net'].get('decision', 'HOLD')
                confidences['neural_net'] = results['neural_net'].get('confidence', 0)
            else:
                votes['neural_net'] = 'HOLD'
                confidences['neural_net'] = 0
            
            votes['multiframe'] = results['multiframe'].get('decision', 'HOLD')
            confidences['multiframe'] = results['multiframe'].get('confidence', 0)
            
            votes['divergence'] = results['divergence'].get('signal', 'HOLD')
            confidences['divergence'] = results['divergence'].get('confidence', 0)
            
            votes['pattern'] = results['pattern'].get('signal', 'HOLD')
            confidences['pattern'] = results['pattern'].get('confidence', 0)
            
            # ⭐ OVERRIDE: Si MULTIFRAME tiene confidence > 75%, usar su decisión (optimizado: era 90%)
            if confidences['multiframe'] > 75 and votes['multiframe'] != 'HOLD':
                final_decision = votes['multiframe']
                avg_confidence = confidences['multiframe']
                consensus = 100
                self.log(f"[🎯 OVERRIDE] MULTIFRAME dominante (conf={avg_confidence:.1f}%) → {final_decision} [OPTIMIZADO 75%]", 'warning')
                
                return {
                    'decision': final_decision,
                    'confidence': min(95, avg_confidence),
                    'consensus': consensus,
                    'motor_votes': votes,
                    'motor_confidences': confidences,
                    'buy_votes': 1 if final_decision == 'BUY' else 0,
                    'sell_votes': 1 if final_decision == 'SELL' else 0,
                    'volatility_state': results['volatility_state'],
                    'divergence_detected': results['divergence'].get('type') != 'NO_DIVERGENCE',
                    'pattern_detected': results['pattern'].get('pattern') != 'NO_PATTERN',
                    'override_reason': 'MULTIFRAME_dominant'
                }
            
            # Contar votos ponderados (MULTIFRAME y ENSEMBLE tienen peso mayor)
            # Ajustar pesos si neural_net no está disponible
            if NEURAL_NET_AVAILABLE:
                weights_motors = {
                    'ensemble': 0.40,       # 40% - Base sólida
                    'multiframe': 0.40,     # 40% - Jerárquico
                    'neural_net': 0.10,     # 10% - ML
                    'divergence': 0.05,     # 5% - Reversal
                    'pattern': 0.05         # 5% - Patrón
                }
            else:
                # Sin neural_net, redistributribuir su 10% a ensemble y multiframe
                weights_motors = {
                    'ensemble': 0.45,       # +5% extra
                    'multiframe': 0.45,     # +5% extra
                    'neural_net': 0.0,      # 0% - No disponible
                    'divergence': 0.05,     # 5% - Reversal
                    'pattern': 0.05         # 5% - Patrón
                }
            
            # Calcular score ponderado
            buy_score = sum(
                (1 if votes[name] == 'BUY' else 0) * weight
                for name, weight in weights_motors.items()
                if weight > 0  # Solo considerar motores con peso > 0
            )
            sell_score = sum(
                (1 if votes[name] == 'SELL' else 0) * weight
                for name, weight in weights_motors.items()
                if weight > 0  # Solo considerar motores con peso > 0
            )
            
            # Decisión: aplicar umbral más bajo (3/5 = 0.6 → usar 0.50)
            if buy_score >= 0.50:
                final_decision = 'BUY'
                avg_confidence = np.mean([confidences[n] for n, v in votes.items() if v == 'BUY'])
                consensus = (buy_score / max(buy_score, sell_score)) * 100 if max(buy_score, sell_score) > 0 else 0
            elif sell_score >= 0.50:
                final_decision = 'SELL'
                avg_confidence = np.mean([confidences[n] for n, v in votes.items() if v == 'SELL'])
                consensus = (sell_score / max(buy_score, sell_score)) * 100 if max(buy_score, sell_score) > 0 else 0
            else:
                final_decision = 'HOLD'
                avg_confidence = np.mean(list(confidences.values()))
                consensus = max(buy_score, sell_score) * 100
            
            # ⭐ FILTRO: Si confidence < 40%, cambiar a HOLD
            if avg_confidence < 40:
                self.log(f"[⚠️  FILTRO] Confianza baja ({avg_confidence:.1f}% < 40%) → Forzando HOLD", 'warning')
                final_decision = 'HOLD'
                avg_confidence = 30  # Confianza mínima para HOLD
            
            # Volatility state (no vota)
            volatility_state = results['volatility_state']
            
            return {
                'decision': final_decision,
                'confidence': min(95, avg_confidence),
                'consensus': consensus,
                'motor_votes': votes,
                'motor_confidences': confidences,
                'buy_votes': sum(1 for v in votes.values() if v == 'BUY'),
                'sell_votes': sum(1 for v in votes.values() if v == 'SELL'),
                'buy_score_weighted': buy_score,
                'sell_score_weighted': sell_score,
                'volatility_state': volatility_state,
                'divergence_detected': results['divergence'].get('type') != 'NO_DIVERGENCE',
                'pattern_detected': results['pattern'].get('pattern') != 'NO_PATTERN'
            }
        
        except Exception as e:
            self.log(f"Error synthesizing: {str(e)}", 'error')
            return {'decision': 'HOLD', 'confidence': 0}
    
    def _log_super_analysis(self, final, motors):
        """Log formateado del super-análisis"""
        
        decision_emoji = '🟢' if final['decision'] == 'BUY' else '🔴' if final['decision'] == 'SELL' else '⚪'
        
        # Tabla de votos
        votes_str = " | ".join([
            f"{name.upper()[:7]}: {final['motor_votes'][name][0]}({final['motor_confidences'][name]:.0f}%)"
            for name in final['motor_votes'].keys()
        ])
        
        self.log(f"""
╔═══════════════════════════════════════════════════════════════╗
║           {decision_emoji} SUPER ANALYZER FINAL DECISION                  ║
╠═══════════════════════════════════════════════════════════════╣
║ Decision: {final['decision']:<50} ║
║ Confidence: {final['confidence']:<48.1f}% ║
║ Consensus: {final['consensus']:<48.1f}% ║
║ ─────────────────────────────────────────────────────────── ║
║ Votos: BUY={final['buy_votes']}/5  SELL={final['sell_votes']}/5  HOLD={5-final['buy_votes']-final['sell_votes']}/5       ║
║ ─────────────────────────────────────────────────────────── ║
║ {votes_str:<61} ║
║ Volatilidad: {final['volatility_state']:<45} ║
║ Divergencia: {'✓ Detectada' if final['divergence_detected'] else '✗ No':<42} ║
║ Patrón: {'✓ Detectado' if final['pattern_detected'] else '✗ No':<45} ║
╚═══════════════════════════════════════════════════════════════╝
""", 'info')

