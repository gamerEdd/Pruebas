#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FEEDBACK LOOP AI - Post-Trade Analysis & Dynamic Reweighting
Objetivo: Mejorar decisiones ajustando pesos de motores basado en resultados reales

Sistema "aprende" de cada trade:
- Trades ganadores con baja confianza → aumentar peso del motor
- Trades perdedores con alta confianza → disminuir peso del motor
- Acumula accuracy por motor → retroalimentación continua
"""

import json
import os
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta
import numpy as np


class FeedbackLoopAI:
    """Post-trade analysis y dynamic reweighting basado en historial"""
    
    def __init__(self, log_callback=None):
        """
        Args:
            log_callback: Función para logging (signature: log(message, type))
        """
        self.log_callback = log_callback or self._default_log
        
        # Persistencia
        self.feedback_history_file = Path('logs/feedback_history.json')
        self.motor_weights_file = Path('logs/motor_weights.json')
        self.motor_accuracy_file = Path('logs/motor_accuracy.json')
        
        # Crear directorio si no existe
        Path('logs').mkdir(exist_ok=True)
        
        # Cargar histórico
        self.feedback_history = self._load_feedback_history()
        self.motor_weights = self._load_motor_weights()
        self.motor_accuracy = self._load_motor_accuracy()

        # Compatibilidad hacia atrás: si no existe historial propio, importar legado de LOSS.
        if not self.feedback_history:
            imported = self._bootstrap_from_loss_history()
            if imported > 0:
                self.log(f"[FEEDBACK] Importados {imported} trades desde loss_protection_history.json", 'info')
        
        # Estado
        self.trades_processed = 0
        self.total_updates = 0
        
        self.log(f"[FEEDBACK] FeedbackLoopAI inicializado - {len(self.feedback_history)} trades históricos", 'info')

    def _bootstrap_from_loss_history(self):
        """Importa historial legado de LOSS cuando feedback_history está vacío."""
        try:
            legacy_file = Path('logs/loss_protection_history.json')
            if not legacy_file.exists():
                return 0

            with open(legacy_file, 'r') as f:
                legacy_trades = json.load(f)

            if not isinstance(legacy_trades, list) or not legacy_trades:
                return 0

            imported = 0
            for i, t in enumerate(legacy_trades[-1000:], 1):
                if not isinstance(t, dict):
                    continue

                ts = t.get('timestamp') or datetime.now().isoformat()
                profit = float(t.get('profit_loss', t.get('profit', 0.0)) or 0.0)
                direction = str(t.get('direction', 'UNKNOWN') or 'UNKNOWN').upper()

                # Entrada mínima para reportes/estadísticas históricas.
                entry = {
                    'ticket': int(t.get('ticket', -i)),
                    'analysis_source': 'LEGACY_LOSS_HISTORY',
                    'buy_score': float(t.get('buy_score', 50.0) or 50.0),
                    'sell_score': float(t.get('sell_score', 50.0) or 50.0),
                    'confidence': float(t.get('confidence', 50.0) or 50.0),
                    'direction': direction,
                    'recorded_at': ts,
                    'closed_at': ts,
                    'profit': profit,
                    'result': 'GANADA' if profit > 0 else 'PERDIDA' if profit < 0 else 'NEUTRAL'
                }
                self.feedback_history.append(entry)
                imported += 1

            if imported > 0:
                self.feedback_history = self.feedback_history[-1000:]
                self._save_feedback_history()

            return imported
        except Exception as e:
            self.log(f"[FEEDBACK] Error importando legado LOSS: {str(e)[:40]}", 'warning')
            return 0
    
    def _default_log(self, message, msg_type='info'):
        """Logging por defecto si no se proporciona callback"""
        print(f"[{msg_type.upper()}] {message}")
    
    def log(self, message, msg_type='info'):
        """Log wrapper"""
        if self.log_callback:
            self.log_callback(message, msg_type)
    
    def record_trade_analysis(self, trade_metadata):
        """
        Registra metadata de análisis para retroalimentación posterior
        
        Args:
            trade_metadata (dict):
                - ticket: ID de ticket
                - analysis_source: 'V12' o 'DUAL'
                - buy_score: Score BUY (0-100)
                - sell_score: Score SELL (0-100)
                - confidence: Confianza general (0-100)
                - direction: 'BUY' o 'SELL'
                - entry_rsi: RSI al entry
                - entry_volatility: Volatilidad al entry
                - motor_votes: {'multiframe': 'BUY', 'ensemble': 'HOLD', ...}
                - timestamp: cuando se abrió
        """
        try:
            # Validar estructura mínima
            required = ['ticket', 'analysis_source', 'buy_score', 'sell_score', 'confidence', 'direction']
            if not all(k in trade_metadata for k in required):
                self.log(f"[FEEDBACK] Metadata incompleta, faltando: {[k for k in required if k not in trade_metadata]}", 'warning')
                return False
            
            # Guardar en histórico volatile
            trade_metadata['recorded_at'] = datetime.now().isoformat()
            self.feedback_history.append(trade_metadata)
            
            # Limitar a últimas 1000
            if len(self.feedback_history) > 1000:
                self.feedback_history.pop(0)
            
            self._save_feedback_history()
            return True
        except Exception as e:
            self.log(f"[FEEDBACK] Error registrando análisis: {str(e)[:50]}", 'error')
            return False
    
    def analyze_closed_trade(self, trade_result):
        """
        Analiza un trade cerrado y retroalimenta al sistema
        
        Args:
            trade_result (dict):
                - ticket: ID de ticket
                - profit: Ganancia/pérdida en $ (positivo o negativo)
                - closed_at: timestamp cierre
        
        Returns:
            dict: {
                'feedback_applied': bool,
                'motor_adjustments': {'multiframe': 0.02, 'ensemble': -0.01, ...},
                'accuracy_updates': {'V12': {'wins': 1, 'losses': 0}, ...},
                'confidence_shift': 'up' | 'down' | 'neutral'
            }
        """
        try:
            ticket = trade_result.get('ticket')
            profit = trade_result.get('profit', 0)
            
            # Encontrar metadata del trade (debe haberse registrado en record_trade_analysis)
            trade_metadata = None
            for entry in reversed(self.feedback_history):
                if entry.get('ticket') == ticket and 'closed_at' not in entry:
                    trade_metadata = entry
                    break
            
            if not trade_metadata:
                self.log(f"[FEEDBACK] No metadata encontrada para ticket {ticket}", 'warning')
                return {'feedback_applied': False}
            
            # Marcar como cerrado
            trade_metadata['closed_at'] = datetime.now().isoformat()
            trade_metadata['profit'] = profit
            trade_metadata['result'] = 'GANADA' if profit > 0 else 'PERDIDA' if profit < 0 else 'NEUTRAL'
            
            # Realizar feedback analysis
            result = self._perform_feedback_analysis(trade_metadata)
            
            self._save_feedback_history()
            self.trades_processed += 1
            
            return result
            
        except Exception as e:
            self.log(f"[FEEDBACK] Error analizando trade: {str(e)[:50]}", 'error')
            return {'feedback_applied': False, 'error': str(e)[:50]}
    
    def _perform_feedback_analysis(self, trade_metadata):
        """
        Análisis central de retroalimentación
        
        Lógica:
        1. Determinar si trade fue "correcto" con su dirección
        2. Comparar confidence con resultado
        3. Ajustar pesos de motores que votaron
        4. Actualizar accuracy por análisis_source
        5. Recalcular umbral de confianza
        """
        adjustments = {}
        accuracy_updates = {}
        
        direction = trade_metadata.get('direction')  # BUY o SELL
        profit = trade_metadata.get('profit', 0)
        confidence = trade_metadata.get('confidence', 50)
        source = trade_metadata.get('analysis_source', 'UNKNOWN')
        motor_votes = trade_metadata.get('motor_votes', {})
        
        # [1] Determinar si fue correcto
        was_correct = (profit > 0)  # Ganancia = decisión acertada
        
        # [2] Comparar confidence vs resultado
        confidence_shift = 'neutral'
        if was_correct and confidence >= 70:
            # Ganancia con alta confianza = confianza bien calibrada ✓
            confidence_shift = 'stable'
        elif was_correct and confidence < 50:
            # Ganancia con baja confianza = subestimó seguridad
            confidence_shift = 'up'
        elif not was_correct and confidence >= 70:
            # Pérdida con alta confianza = sobresestimó confianza
            confidence_shift = 'down'
        elif not was_correct and confidence < 50:
            # Pérdida con baja confianza = confianza bien calibrada ✓
            confidence_shift = 'stable'
        
        # [3] Ajustar pesos de motores
        for motor_name, motor_vote in motor_votes.items():
            weight_key = f"{motor_name}_weight"
            current_weight = self.motor_weights.get(weight_key, 0.1)
            
            # Si motor votó por la dirección ganadora → +ajuste
            # Si motor votó contra → -ajuste
            voted_correctly = (motor_vote == direction)
            
            if was_correct and voted_correctly:
                # Acertó → aumentar peso (+2-3%)
                adjustment = 0.025 if confidence >= 70 else 0.015
                adjustments[motor_name] = adjustment
                self.motor_weights[weight_key] = min(0.40, current_weight + adjustment)  # Cap 40%
            elif not was_correct and not voted_correctly:
                # Se equivocó pero votó diferente → reconocer
                adjustment = 0.010
                adjustments[motor_name] = adjustment
                self.motor_weights[weight_key] = min(0.40, current_weight + adjustment)
            elif not was_correct and voted_correctly:
                # Perdió pero votó correctamente → el votante fue overridden
                # (-1-2% para compensar por rechazo)
                adjustment = -0.010
                adjustments[motor_name] = adjustment
                self.motor_weights[weight_key] = max(0.02, current_weight + adjustment)
            else:
                # Ganó pero votó diferente → penalizar (-1%)
                adjustment = -0.010
                adjustments[motor_name] = adjustment
                self.motor_weights[weight_key] = max(0.02, current_weight + adjustment)
        
        # [4] Actualizar accuracy por source
        if source not in accuracy_updates:
            accuracy_updates[source] = {'wins': 0, 'losses': 0, 'total': 0}
        
        if was_correct:
            accuracy_updates[source]['wins'] = self.motor_accuracy.get(f"{source}_wins", 0) + 1
        else:
            accuracy_updates[source]['losses'] = self.motor_accuracy.get(f"{source}_losses", 0) + 1
        accuracy_updates[source]['total'] = accuracy_updates[source]['wins'] + accuracy_updates[source]['losses']
        
        # Actualizar global
        self.motor_accuracy[f"{source}_wins"] = accuracy_updates[source]['wins']
        self.motor_accuracy[f"{source}_losses"] = accuracy_updates[source]['losses']
        
        # Calcular win rate
        if accuracy_updates[source]['total'] >= 5:  # Mínimo 5 trades para calcular
            win_rate = accuracy_updates[source]['wins'] / accuracy_updates[source]['total']
            self.motor_accuracy[f"{source}_win_rate"] = round(win_rate, 3)
        
        # [5] Recalcular umbral de confianza global
        # Si hay muchos falsos positivos → subir umbral
        # Si hay muchos falsos negativos → bajar umbral
        recent_trades = self._get_recent_trades(50)
        if len(recent_trades) >= 10:
            false_positives = sum(1 for t in recent_trades if t.get('profit', 0) < 0 and t.get('confidence', 0) >= 70)
            false_negatives = sum(1 for t in recent_trades if t.get('profit', 0) > 0 and t.get('confidence', 0) < 50)
            
            fp_rate = false_positives / len(recent_trades)
            fn_rate = false_negatives / len(recent_trades)
            
            # Logaritmo de ajustes
            if fp_rate > 0.30:
                # >30% false positives → subir umbral (ser más conservador)
                self.motor_accuracy['confidence_threshold'] = self.motor_accuracy.get('confidence_threshold', 50) + 2
            elif fn_rate > 0.20:
                # >20% false negatives → bajar umbral (ser más agresivo)
                self.motor_accuracy['confidence_threshold'] = max(30, self.motor_accuracy.get('confidence_threshold', 50) - 2)
        
        # Guardar cambios
        self._save_motor_weights()
        self._save_motor_accuracy()
        
        # Log
        result_str = "✓ GANADA" if was_correct else "✗ PÉRDIDA"
        self.log(f"[FEEDBACK] {result_str} | {direction} | Conf:{confidence}% | Ajustes: {len(adjustments)} motores", 'info')
        
        return {
            'feedback_applied': True,
            'trade_result': trade_metadata.get('result'),
            'confidence_shift': confidence_shift,
            'motor_adjustments': adjustments,
            'accuracy_updates': accuracy_updates,
            'trades_processed': self.trades_processed + 1
        }
    
    def get_current_weights(self):
        """Retorna pesos actuales ajustados por feedback"""
        return dict(self.motor_weights)
    
    def get_adjusted_threshold(self):
        """Retorna umbral de confianza ajustado dinámicamente"""
        return self.motor_accuracy.get('confidence_threshold', 50)
    
    def get_motor_accuracy_stats(self):
        """Estadísticas de accuracy por motor/source"""
        stats = {}
        for source in ['V12', 'DUAL']:
            wins = self.motor_accuracy.get(f"{source}_wins", 0)
            losses = self.motor_accuracy.get(f"{source}_losses", 0)
            total = wins + losses
            if total > 0:
                win_rate = round(100 * wins / total, 1)
                stats[source] = {
                    'wins': wins,
                    'losses': losses,
                    'total': total,
                    'win_rate': f"{win_rate}%"
                }
        return stats
    
    def _get_recent_trades(self, count=100):
        """Último N trades cerrados"""
        closed = [t for t in self.feedback_history if 'closed_at' in t]
        return closed[-count:] if len(closed) > count else closed
    
    def _load_feedback_history(self):
        """Cargar histórico de trades"""
        try:
            if self.feedback_history_file.exists():
                with open(self.feedback_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.log(f"[FEEDBACK] Error cargando histórico: {str(e)[:40]}", 'warning')
            return []
    
    def _save_feedback_history(self):
        """Guardar histórico de trades"""
        try:
            with open(self.feedback_history_file, 'w') as f:
                json.dump(self.feedback_history, f, indent=2)
        except Exception as e:
            self.log(f"[FEEDBACK] Error guardando histórico: {str(e)[:40]}", 'error')
    
    def _load_motor_weights(self):
        """Cargar pesos ajustados de motores"""
        try:
            if self.motor_weights_file.exists():
                with open(self.motor_weights_file, 'r') as f:
                    return json.load(f)
            # Inicializar con pesos por defecto (igual a super_analyzer.py)
            return {
                'ensemble_weight': 0.40,
                'multiframe_weight': 0.40,
                'neural_weight': 0.10,
                'divergence_weight': 0.05,
                'pattern_weight': 0.05
            }
        except Exception as e:
            self.log(f"[FEEDBACK] Error cargando pesos: {str(e)[:40]}", 'warning')
            return {}
    
    def _save_motor_weights(self):
        """Guardar pesos ajustados de motores"""
        try:
            with open(self.motor_weights_file, 'w') as f:
                json.dump(self.motor_weights, f, indent=2)
        except Exception as e:
            self.log(f"[FEEDBACK] Error guardando pesos: {str(e)[:40]}", 'error')
    
    def _load_motor_accuracy(self):
        """Cargar estadísticas de accuracy"""
        try:
            if self.motor_accuracy_file.exists():
                with open(self.motor_accuracy_file, 'r') as f:
                    return json.load(f)
            return {
                'V12_wins': 0,
                'V12_losses': 0,
                'DUAL_wins': 0,
                'DUAL_losses': 0,
                'confidence_threshold': 50
            }
        except Exception as e:
            self.log(f"[FEEDBACK] Error cargando accuracy: {str(e)[:40]}", 'warning')
            return {}
    
    def _save_motor_accuracy(self):
        """Guardar estadísticas de accuracy"""
        try:
            with open(self.motor_accuracy_file, 'w') as f:
                json.dump(self.motor_accuracy, f, indent=2)
        except Exception as e:
            self.log(f"[FEEDBACK] Error guardando accuracy: {str(e)[:40]}", 'error')
    
    def get_summary_report(self):
        """Reporte resumido del feedback loop"""
        recent = self._get_recent_trades(100)
        if not recent:
            return "Sin trades para reportar"
        
        wins = sum(1 for t in recent if t.get('profit', 0) > 0)
        losses = sum(1 for t in recent if t.get('profit', 0) < 0)
        total = len(recent)
        win_rate = 100 * wins / total if total > 0 else 0
        
        avg_confidence = np.mean([t.get('confidence', 50) for t in recent]) if recent else 0
        avg_profit = np.mean([t.get('profit', 0) for t in recent]) if recent else 0
        
        accuracy_stats = self.get_motor_accuracy_stats()
        
        report = f"""
FEEDBACK LOOP REPORT
{'=' * 50}
Últimos 100 trades:
  Victorias: {wins}/{total} ({win_rate:.1f}%)
  Pérdidas: {losses}/{total}
  Profit promedio: ${avg_profit:.2f}
  Confianza promedio: {avg_confidence:.1f}%

Accuracy por Source:
{json.dumps(accuracy_stats, indent=2)}

Umbral de confianza actual: {self.get_adjusted_threshold()}%
Pesos ajustados: {sum(1 for k, v in self.motor_weights.items() if v != 0.1)}+ motores modificados
{'=' * 50}
"""
        return report.strip()
