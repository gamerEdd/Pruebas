import numpy as np
import MetaTrader5 as mt5
import mt5_safe
import time
from datetime import datetime, timedelta
from indicator_base import IndicatorBase
from temporal_weighting import TemporalWeighting
from outlier_filter import OutlierFilter
from candle_validator import CandleValidator

class SellSpecialistAI(IndicatorBase):
    """IA especializada EXCLUSIVAMENTE en detectar oportunidades de VENTA"""
    
    def __init__(self, log_callback=None, dataset_manager=None, timeframe='M1'):
        super().__init__(timeframe=timeframe)
        self.log_callback = log_callback
        self.dataset_manager = dataset_manager  # [OK] Professional Dataset Manager
        self.name = "SELL Specialist"
        self.debug_logs = False
        
        # ⭐ NUEVO (P3 Minor): Utilidades de validación y filtrado
        self.temporal_weighting = TemporalWeighting(decay_rate=0.95)
        self.outlier_filter = OutlierFilter(method='iqr', window=5)
        self.candle_validator = CandleValidator(timeframe=timeframe)
        
        # ⭐ NUEVO: Trend Detector (será inyectado desde botiaver1.py)
        self.trend_detector = None
        
        # ⭐ PESOS REOPTIMIZADOS (P0 Phase 7)
        # Problema anterior: Osciladores subestimados, Volumen ignorado
        # Solución: ADX 0.07→0.16, CCI 0.08→0.12, Williams 0.07→0.12, Volumen 0.05→0.16
        # Pesos SIMÉTRICOS — idénticos a BUY specialist (mismo potencial máximo)
        self.weights = {
            'rsi_overbought': 0.17,
            'resistance_rejection': 0.15,
            'bearish_momentum': 0.10,
            'macd_bearish': 0.05,
            'volume_confirmation': 0.16,
            'bollinger_upper': 0.05,
            'stochastic_overbought': 0.06,
            'cci_bearish': 0.12,
            'williams_r_overbought': 0.12,
            'adx_trend_strength': 0.16,
        }
        
        # Umbrales más permisivos pero seguros
        self.thresholds = {
            'min_score': 30,
            'rsi_overbought': 50,
            'momentum_max': 0.25,
            'resistance_distance': 0.20,
            'confidence_high': 60,
            'confidence_medium': 45,
            'stochastic_overbought': 80,
            'cci_threshold': 100,
            'williams_r_overbought': 20,
            'adx_min_strength': 25,
        }
        
        # ⭐ NUEVO: Análisis histórico de 24 horas
        self.market_history_24h = None
        self.last_market_analysis_time = 0
        self.min_recovery_potential = 0.5
        
        # [EMOJI] Insights del aprendizaje del dataset
        self.dataset_insights = None
        self.dataset_enabled = dataset_manager is not None
        
        # [ENTRENAMIENTO] Baseline de indicadores aprendidos del dataset
        self.trained_baseline = {}
        self.is_trained = False
        
        # ⭐ NUEVO (P0 Phase 7): Volatilidad dinámica y TrendDetector
        self.dynamic_volatility_threshold = 1.0  # ATR normalizado
        self.volatility_factor = 1.0             # Multiplicador dinámico de umbrales
        
        # ⭐ NUEVO (P1 Phase 7): Histórico de indicadores para detectar cruces y divergencias
        self.previous_rsi = None
        self.previous_stochastic = None
        self.previous_cci = None
        self.previous_williams_r = None
        self.previous_adx = None
        self.previous_price_high = None
        self.previous_price_low = None
        self.previous_price_close = None
        
        # ⭐ NUEVO (P3 Phase - Historicidad): Mantener históricos de últimos 10 candles
        self.rsi_history = []                    # [rsi_1, rsi_2, ..., rsi_actual]
        self.stochastic_history = []            # Último 10 valores
        self.cci_history = []                   # Último 10 valores
        self.williams_r_history = []            # Último 10 valores
        self.overbought_condition_history = []  # [True/False, ...] de cuándo RSI > 70
        
        # ⭐ NUEVA (P2 Phase): Velocity Detector (SELL - Detectar cambios rápidos bajistas)
        self.last_analysis_time = time.time()
        self.last_rsi = 50
        self.last_volume_sum = 0
        self.direction_velocity_bonus = 0
        self.has_rapid_change = False
        self.session_context = {}
        self.last_live_signal = {
            'direction': 'SELL',
            'recommendation': 'HOLD',
            'confidence': 0.0,
            'score': 0.0,
            'timestamp': 0.0,
            'reason': 'No analysis yet'
        }

    def set_session_context(self, context):
        """Recibe contexto de sesión del bot para ponderar predicción actual."""
        try:
            self.session_context = context or {}
        except Exception:
            self.session_context = {}

    def _apply_session_context_bias(self, final_score, confidence):
        """Aplica sesgo de sesión actual manteniendo aprendizaje histórico como base."""
        try:
            ctx = self.session_context or {}
            samples = int(ctx.get('samples', 0) or 0)
            if samples < 6:
                return float(final_score), float(confidence), "session_bias=insufficient_samples"

            buy_wr = float(ctx.get('buy_win_rate', 50.0) or 50.0)
            sell_wr = float(ctx.get('sell_win_rate', 50.0) or 50.0)
            buy_p = float(ctx.get('buy_profit', 0.0) or 0.0)
            sell_p = float(ctx.get('sell_profit', 0.0) or 0.0)
            buy_ls = int(ctx.get('buy_loss_streak', 0) or 0)
            sell_ls = int(ctx.get('sell_loss_streak', 0) or 0)
            session_weight = float(ctx.get('session_weight', 0.75) or 0.75)
            session_weight = max(0.35, min(0.90, session_weight))

            wr_edge = (sell_wr - buy_wr) / 100.0
            profit_edge = np.tanh((sell_p - buy_p) / 10.0)
            streak_penalty = min(0.25, sell_ls * 0.08)
            opp_boost = min(0.12, buy_ls * 0.04)

            edge = (0.70 * wr_edge) + (0.30 * profit_edge) - streak_penalty + opp_boost
            session_delta = edge * (20.0 * session_weight)
            conf_delta = edge * (14.0 * session_weight)

            score_adj = float(np.clip(final_score + session_delta, 0.0, 100.0))
            conf_adj = float(np.clip(confidence + conf_delta, 0.0, 100.0))
            detail = f"session_bias={session_delta:+.1f} conf={conf_delta:+.1f} samples={samples}"
            return score_adj, conf_adj, detail
        except Exception:
            return float(final_score), float(confidence), "session_bias=error"

    def _update_live_signal_cache(self, recommendation, confidence, score):
        """Guarda la señal rápida del SELL specialist para trigger de apertura."""
        try:
            rec = str(recommendation).upper() if recommendation is not None else 'HOLD'
            conf = float(confidence or 0.0)
            scr = float(score or 0.0)
            self.last_live_signal = {
                'direction': 'SELL',
                'recommendation': rec,
                'confidence': conf,
                'score': scr,
                'timestamp': time.time(),
                'reason': f'SELL specialist rec={rec} conf={conf:.1f} score={scr:.1f}'
            }
        except Exception:
            pass

    def get_live_open_signal(self, conf_threshold=None, max_age_sec=1.5):
        """Retorna señal de apertura nacida en SELL specialist usando su último análisis."""
        try:
            sig = dict(self.last_live_signal or {})
            ts = float(sig.get('timestamp', 0.0) or 0.0)
            if ts <= 0:
                return None

            age = time.time() - ts
            if age > float(max_age_sec):
                return None

            thr = float(self.thresholds.get('confidence_high', 60)) if conf_threshold is None else float(conf_threshold)
            rec = str(sig.get('recommendation', 'HOLD')).upper()
            conf = float(sig.get('confidence', 0.0) or 0.0)

            if rec == 'SELL' and conf >= thr:
                sig['recommendation'] = 'SELL'
            else:
                sig['recommendation'] = 'HOLD'

            sig['age_sec'] = age
            sig['source'] = 'SELL_SPECIALIST'
            sig['threshold'] = thr
            return sig
        except Exception:
            return None
    
    def train(self, snapshots):
        """
        ENTRENA el especialista con dataset histórico (4 semanas).
        Calcula indicadores baseline que se usarán como referencia.
        
        Args:
            snapshots: Lista de 4 semanas de snapshots M1
        
        Returns:
            dict: Resumen de entrenamiento
        """
        try:
            if not snapshots or len(snapshots) < 100:
                self.log(f"[TRAIN] Datos insuficientes ({len(snapshots)}), saltando entrenamiento", 'warning')
                return {'status': 'insufficient_data'}
            
            # Normalizar snapshots
            snaps = self._normalize_snapshots(snapshots)
            
            # Extraer precios
            closes = np.array([s.get('close', 0) for s in snaps], dtype=np.float64)
            highs = np.array([s.get('high', 0) for s in snaps], dtype=np.float64)
            lows = np.array([s.get('low', 0) for s in snaps], dtype=np.float64)
            volumes = np.array([s.get('tick_volume', 0) for s in snaps], dtype=np.float64)
            
            if len(closes) < 50:
                return {'status': 'insufficient_data'}
            
            # Calcular baseline de indicadores
            self.trained_baseline = {
                # Precios
                'price_min': float(np.min(closes)),
                'price_max': float(np.max(closes)),
                'price_mean': float(np.mean(closes)),
                'price_current': float(closes[-1]),
                
                # Volatilidad
                'volatility': float(np.std(closes)),
                'atr': float(np.mean(np.abs(np.diff(closes)))),
                
                # RSI promedio del período
                'rsi_mean': float(self._calculate_rsi(closes)),
                
                # Momentum
                'momentum': float((closes[-1] - closes[0]) / closes[0] * 100),
                
                # Volumen
                'volume_mean': float(np.mean(volumes)),
                'volume_std': float(np.std(volumes)),
                
                # Bandas
                'bollinger_position': self._calculate_bollinger_position(closes),
            }
            
            self.is_trained = True
            
            self.log(
                f"[TRAIN] SELL Specialist entrenado con {len(snaps)} barras. "
                f"Baseline: RSI={self.trained_baseline['rsi_mean']:.1f}, "
                f"Volatilidad={self.trained_baseline['volatility']:.4f}",
                'success'
            )
            
            return {
                'status': 'success', 
                'trained_bars': len(snaps),
                'baseline': self.trained_baseline
            }
        except Exception as e:
            self.log(f"Error entrenando SELL Specialist: {e}", 'error')
            return {'status': 'error', 'error': str(e)}
    
    def _detect_crosses(self, features):
        """
        ⭐ P1 PHASE: Detecta NUEVOS cruces de osciladores (SELL version)
        
        Para SELL buscamos cruces BAJISTAS:
        - RSI cruza de abajo de 70 hacia arriba: BAJISTA ✅
        - Stochastic cruza de abajo de 80 hacia arriba: BAJISTA ✅
        - CCI cruza de abajo de 100 hacia arriba: BAJISTA ✅
        - Williams %R cruza de abajo de -20 hacia arriba: BAJISTA ✅
        
        Returns:
            dict con cross_strength (0-4) + flags de cruces individuales
        """
        try:
            crosses = {
                'rsi_cross': False,
                'stochastic_cross': False,
                'cci_cross': False,
                'williams_cross': False,
                'cross_strength': 0,
            }
            
            # Detectar cruce RSI (SELL: de 70- → >70)
            current_rsi = features.get('rsi', 50)
            if self.previous_rsi is not None:
                if self.previous_rsi <= 70 and current_rsi > 70:
                    crosses['rsi_cross'] = True
                    crosses['cross_strength'] += 1
            
            # Detectar cruce Stochastic (SELL: de 80- → >80)
            current_stoch = features.get('stochastic', 50)
            if self.previous_stochastic is not None:
                if self.previous_stochastic <= 80 and current_stoch > 80:
                    crosses['stochastic_cross'] = True
                    crosses['cross_strength'] += 1
            
            # Detectar cruce CCI (SELL: de 100- → >100)
            current_cci = features.get('cci', 0)
            if self.previous_cci is not None:
                if self.previous_cci <= 100 and current_cci > 100:
                    crosses['cci_cross'] = True
                    crosses['cross_strength'] += 1
            
            # Detectar cruce Williams %R (SELL: de -20- → >-20)
            current_williams = features.get('williams_r', -50)
            if self.previous_williams_r is not None:
                if self.previous_williams_r <= -20 and current_williams > -20:
                    crosses['williams_cross'] = True
                    crosses['cross_strength'] += 1
            
            if crosses['cross_strength'] > 0:
                self.log(f"[CROSS] {crosses['cross_strength']} osciladores cruzaron", 'success')
            
            return crosses
        
        except Exception as e:
            self.log(f"Error detectando cruces: {str(e)[:60]}", 'error')
            return {
                'rsi_cross': False,
                'stochastic_cross': False,
                'cci_cross': False,
                'williams_cross': False,
                'cross_strength': 0,
            }
    
    def _normalize_snapshots(self, snapshots):
        """Convierte estructura anidada (price['close']) a plana (snapshot['close'])"""
        try:
            normalized = []
            for snap in snapshots:
                if isinstance(snap, dict):
                    # Si ya está plano, usar tal cual
                    if 'close' in snap:
                        normalized.append(snap)
                    # Si está anidado en 'price', extraer y aplanar
                    elif 'price' in snap and isinstance(snap['price'], dict):
                        flat = {
                            'open': snap['price'].get('open', 0),
                            'close': snap['price'].get('close', 0),
                            'high': snap['price'].get('high', 0),
                            'low': snap['price'].get('low', 0),
                            'bid': snap['price'].get('bid', 0),
                            'ask': snap['price'].get('ask', 0),
                            'tick_volume': snap.get('volume', {}).get('tick_volume', 0) if 'volume' in snap else 0
                        }
                        # Copiar otros campos importantes
                        for key in ['symbol', 'timeframe', 'timestamp']:
                            if key in snap:
                                flat[key] = snap[key]
                        normalized.append(flat)
                    else:
                        # No se puede normalizar, usar tal cual
                        normalized.append(snap)
            return normalized
        except Exception as e:
            self.log(f"Error normalizando snapshots: {e}", 'error')
            return snapshots  # En caso de error, devolver originales
    
    def _update_dataset_insights(self):
        """[OK] Actualiza insights del dataset profesional para mejorar análisis"""
        if not self.dataset_enabled or not self.dataset_manager:
            return
        
        try:
            # Obtener insights de aprendizaje
            patterns = self.dataset_manager.learning_engine.analyze_dataset_patterns()
            insights = self.dataset_manager.learning_engine.get_learning_insights()
            
            if insights:
                self.dataset_insights = insights
                
                # Aplicar insights a thresholds
                sell_cond = insights.get('best_sell_conditions', {})
                if sell_cond.get('requires_rsi_overbought'):
                    self.thresholds['rsi_overbought'] = 65  # Más estricto
                
                self.log("[EMOJI] Insights del dataset aplicados a SELL Specialist", 'info')
        except Exception as e:
            self.log(f"[ADVERTENCIA] Error actualizando insights: {e}", 'warning')
    
    # ⭐ NUEVO (P2 Phase 7): Validación de confluencia requerida (firma de entrada)
    def _calculate_dynamic_volatility_factor(self, features):
        """
        Calcula factor de volatilidad dinámica para ajustar umbrales.
        
        - Volatilidad BAJA (ATR < 0.5) → umbrales MÁS PERMISIVOS (factor = 0.8)
        - Volatilidad NORMAL (ATR 0.5-2.0) → factor = 1.0 (normal)
        - Volatilidad ALTA (ATR > 2.0) → umbrales MÁS ESTRICTOS (factor = 1.3)
        
        Returns: float (multiplicador de umbrales)
        """
        try:
            # Usar ATR del market_history_24h si disponible
            if self.market_history_24h is None:
                return 1.0
            
            volatility = self.market_history_24h.get('volatility_24h', 1.0)
            
            if volatility < 0.5:
                # Volatilidad muy baja → más permisivos
                factor = 0.8
                condition = "BAJA"
            elif volatility > 2.0:
                # Volatilidad muy alta → más estrictos
                factor = 1.3
                condition = "ALTA"
            else:
                # Volatilidad normal
                factor = 1.0
                condition = "NORMAL"
            
            self.volatility_factor = factor
            
            self.log(
                f"[VOLATILITY] {condition} ({volatility:.2f}) → Factor: {factor}x",
                'market'
            )
            
            return factor
            
        except Exception as e:
            self.log(f"Error calculando volatilidad dinámica: {e}", 'error')
            return 1.0
    
    def _requires_confluent_entry(self, cross_strength, divergences):
        """
        ⭐ NUEVO (P4): Confluencia INFORMATIVA - NUNCA rechaza operaciones
        
        Solo loguea información sobre cruces y confluencia para debugging.
        Las operaciones SIEMPRE se abren (decisión tomada por specialists + arbitrador)
        
        Returns: (is_valid=True, reason, recommendation=None)
        """
        try:
            # ⭐ CAMBIO RADICAL: is_valid SIEMPRE TRUE, confluencia es INFORMATIVA
            is_valid = True  # ⭐ SIEMPRE True - las operaciones siempre se abren
            recommendation = None  # ⭐ NUNCA 'HOLD'
            
            bearish_div = divergences.get('bearish_divergence', False)
            
            # ⭐ Verificar confluencia TEMPORAL (solo para info)
            temporal_confluence = (
                len(self.rsi_history) <= 2 and
                len(self.stochastic_history) <= 2 and
                len(self.cci_history) <= 2 and
                len(self.williams_r_history) <= 2
            )
            
            temporal_status = "🎯 TEMPORAL_SINCRONIZADO" if temporal_confluence else "⚠️ TEMPORAL_DISPERSO"
            
            # ⭐ SOLO INFORMACIÓN - Nunca bloquea
            if cross_strength >= 3:
                if temporal_confluence:
                    reason = f"[INFO] {cross_strength}/4 cruces sincronizados ({temporal_status})"
                else:
                    reason = f"[INFO] {cross_strength}/4 cruces - {temporal_status}"
            elif cross_strength == 2 and bearish_div:
                reason = f"[INFO] 2/4 cruces + Divergencia Bajista ({temporal_status})"
            else:
                # ⭐ CAMBIO CRÍTICO: Informar pero NO rechazar
                reason = f"[INFO] Cruces débiles ({cross_strength}/4) pero abre de todas formas"
            
            # ⭐ Solo loguear información, NUNCA rechazo
            self.log(f"[CONFLUENCE-INFO] {reason}", 'info')
            
            return is_valid, reason, recommendation
            
        except Exception as e:
            self.log(f"Error en validación de confluencia: {e}", 'error')
            return False, f"ERROR: {e}", 'HOLD'
    

    # ⭐ NUEVO (P1 Phase 7): Análisis de divergencias
    def _calculate_divergences(self, current_features, current_price):
        """
        Detecta divergencias entre precio e indicadores.
        
        Divergencia BAJISTA (buena para SELL, continúa):
        - Precio sube (high anterior < high actual)
        - RSI baja (rsi anterior > rsi actual)
        - = Vendedores ganando fuerza
        
        Divergencia ALCISTA (mala para SELL, rechaza):
        - Precio baja (low anterior > low actual)
        - RSI sube (rsi anterior < rsi actual)
        - = Compradores ganando fuerza
        
        Divergencia OCULTA (continuación tendencia):
        - Precio sube (high anterior < high actual)
        - RSI sube (rsi anterior < rsi actual)
        - = Alcista continúa
        
        Returns: dict con análisis de divergencias
        """
        try:
            divergences = {
                'bearish_divergence': False,        # Bajista (buena para SELL)
                'bullish_divergence': False,        # Alcista (mala para SELL)
                'hidden_bullish_divergence': False, # Oculta alcista
                'divergence_strength': 0.0,         # Qué tan fuerte
                'penalty': 1.0,                     # Multiplicador a aplicar al score
            }
            
            if self.previous_price_low is None or self.previous_rsi is None:
                return divergences  # Sin datos históricos
            
            current_rsi = current_features.get('rsi', 50)
            
            # 📈 DIVERGENCIA ALCISTA (mala para SELL) 🚫
            # Precio baja pero RSI sube = compradores ganando
            if current_price < self.previous_price_low and current_rsi > self.previous_rsi:
                divergences['bullish_divergence'] = True
                strength = abs(current_rsi - self.previous_rsi) / self.previous_rsi * 100
                divergences['divergence_strength'] = strength
                divergences['penalty'] = 0.4  # Penalizar -60% por divergencia alcista
                self.log(
                    f"[DIVERGENCIA] ALCISTA DETECTADA: Precio ↓{current_price:.2f} vs RSI ↑{current_rsi:.1f} "
                    f"(fuerza: {strength:.1f}%) → Penalizar SELL",
                    'warning'
                )
            
            # 📉 DIVERGENCIA BAJISTA (buena para SELL) ✅
            # Precio sube pero RSI baja = vendedores ganando
            elif current_price > self.previous_price_high and current_rsi < self.previous_rsi:
                divergences['bearish_divergence'] = True
                strength = abs(current_rsi - self.previous_rsi) / self.previous_rsi * 100
                divergences['divergence_strength'] = strength
                divergences['penalty'] = 1.3  # Bonus +30% por divergencia bajista
                self.log(
                    f"[DIVERGENCIA] BAJISTA DETECTADA: Precio ↑{current_price:.2f} vs RSI ↓{current_rsi:.1f} "
                    f"(fuerza: {strength:.1f}%) → Bonus SELL",
                    'success'
                )
            
            # 📊 DIVERGENCIA OCULTA ALCISTA (continuación alcista)
            # Precio sube y RSI sube = alcista continúa
            elif current_price > self.previous_price_high and current_rsi > self.previous_rsi:
                divergences['hidden_bullish_divergence'] = True
                strength = abs(current_rsi - self.previous_rsi) / self.previous_rsi * 100
                divergences['divergence_strength'] = strength
                divergences['penalty'] = 0.7  # Penalizar -30% (menos que divergencia directa)
                self.log(
                    f"[DIVERGENCIA] OCULTA ALCISTA: Precio ↑ y RSI ↑ → Continuación alcista, evitar SELL",
                    'warning'
                )
            
            return divergences
            
        except Exception as e:
            self.log(f"Error calculando divergencias: {e}", 'error')
            return {'penalty': 1.0}
    
    # ⭐ NUEVO (P1 Phase 7): Validación integral de calidad de señal
    def _validate_signal_quality(self, final_score, crosses, divergences):
        """
        Valida la calidad INTEGRAL de la señal combinando:
        1. Cruces (señal nueva vs vieja)
        2. Divergencias (momentum sostenido)
        3. Confluencia temporal (múltiples osciladores simultáneamente)
        
        Returns: (adjusted_score, quality_rating)
        """
        try:
            adjusted_score = final_score
            quality_rating = "DESCONOCIDA"
            
            # Aplicar penalización de divergencias
            divergence_penalty = divergences.get('penalty', 1.0)
            adjusted_score = adjusted_score * divergence_penalty
            
            if divergence_penalty < 1.0:
                self.log(f"[QUALITY] Divergencia alcista penaliza score ({final_score:.1f} × {divergence_penalty} = {adjusted_score:.1f})", 'warning')
            elif divergence_penalty > 1.0:
                self.log(f"[QUALITY] Divergencia bajista bonus score ({final_score:.1f} × {divergence_penalty} = {adjusted_score:.1f})", 'success')
            
            # Evaluar calidad por cruces
            cross_strength = crosses.get('cross_strength', 0)
            
            if cross_strength >= 3:
                # Confluencia FUERTE: 3+ osciladores cruzaron
                adjusted_score = adjusted_score * 1.2  # Bonus +20%
                quality_rating = "EXCELENTE"
                self.log(f"[CONFLUENCE] 3+ Cruces simultáneos → +20% bonus → Score final: {adjusted_score:.1f}", 'success')
            elif cross_strength == 2:
                # Confluencia MEDIA: 2 osciladores cruzaron
                adjusted_score = adjusted_score * 1.1  # Bonus +10%
                quality_rating = "BUENA"
                self.log(f"[CONFLUENCE] 2 Cruces simultáneos → +10% bonus → Score final: {adjusted_score:.1f}", 'success')
            elif cross_strength == 1:
                # Confluencia DÉBIL: 1 oscilador cruzó
                quality_rating = "DÉBIL"
                self.log(f"[CONFLUENCE] 1 Cruce → Señal débil → Score final: {adjusted_score:.1f}", 'info')
            else:
                # Sin cruces: señal VIEJA
                adjusted_score = adjusted_score * 0.6  # Penalizar -40%
                quality_rating = "MUY DÉBIL (sin cruces)"
                self.log(f"[CONFLUENCE] Sin cruces nuevos → -40% penalización → Score final: {adjusted_score:.1f}", 'warning')
            
            # Cap score a 100
            adjusted_score = min(100, adjusted_score)
            
            return adjusted_score, quality_rating
            
        except Exception as e:
            self.log(f"Error validando calidad: {e}", 'error')
            return final_score, "ERROR"
    
    def _validate_and_weight_signal(self, score, features, close_data, current_time=None):
        """
        ⭐ P3 MINOR INTEGRATION: Aplica validaciones y ponderaciones finales
        
        Combina 3 utilidades:
        1. Candle State Validation (>95% cierre requerido)
        2. Temporal Decay Weighting (datos recientes pesan más)
        3. Outlier Detection (filtra spikes en precios)
        
        Returns:
            dict with: final_score, is_valid, details, multipliers
        """
        try:
            adjustments = {
                'candle_validation': 1.0,
                'temporal_decay': 1.0,
                'outlier_penalty': 1.0,
                'final_score': score,
                'is_valid': True,
                'details': []
            }
            
            current_time = current_time or datetime.now()
            
            # 1️⃣ Validar estado del candle
            candle_status = self.candle_validator.is_candle_closed(current_time, tolerance_pct=95)
            
            if not candle_status['is_closed']:
                # Penalizar si candle aún está abierto
                multiplier = self.candle_validator.get_signal_quality_by_candle_state(current_time)
                adjustments['candle_validation'] = multiplier
                
                progress = candle_status['progress_pct']
                if progress < 50:
                    adjustments['is_valid'] = False  # Demasiado temprano
                    adjustments['details'].append(f"⏳ Candle muy abierto ({progress:.0f}%)")
                else:
                    adjustments['details'].append(f"🟡 Candle {progress:.0f}% - Calidad {multiplier:.0%}")
            
            # 2️⃣ Aplicar weighting temporal
            if len(close_data) >= 5:
                recent_ratio = self.temporal_weighting.weighted_recent_ratio(close_data[-10:], recent_bars=3)
                
                if recent_ratio < 0.95:  # Datos recientes bajaron significativamente
                    penalty = max(0.9, recent_ratio)  # Máximo 10% penalización
                    adjustments['temporal_decay'] = penalty
                    adjustments['details'].append(f"📉 Datos recientes bajaron ({recent_ratio:.2f})")
            
            # 3️⃣ Detectar outliers en precios
            if len(close_data) >= 5:
                filtered_closes, outlier_mask = self.outlier_filter.filter_data(close_data[-20:], remove_outliers=True)
                
                outlier_count = np.sum(outlier_mask) if isinstance(outlier_mask, np.ndarray) else 0
                if outlier_count > 3:  # Demasiados outliers
                    penalty = 1.0 - (outlier_count * 0.05)  # 5% por outlier
                    adjustments['outlier_penalty'] = max(0.7, penalty)  # Mínimo -30%
                    adjustments['details'].append(f"🔊 {int(outlier_count)} outliers (-{(1-penalty)*100:.0f}%)")
            
            # Aplicar todos los ajustes
            final_multiplier = (
                adjustments['candle_validation'] *
                adjustments['temporal_decay'] *
                adjustments['outlier_penalty']
            )
            
            adjustments['final_score'] = int(score * final_multiplier)
            
            # Log si hay penalizaciones
            if final_multiplier < 1.0:
                self.log(
                    f"[VAL&WEIGHT] {score} × {final_multiplier:.2f} = {adjustments['final_score']} "
                    f"({', '.join(adjustments['details'])})",
                    'warning'
                )
            
            return adjustments
        
        except Exception as e:
            self.log(f"[ERROR] _validate_and_weight_signal: {str(e)[:60]}", 'error')
            return {
                'candle_validation': 1.0,
                'temporal_decay': 1.0,
                'outlier_penalty': 1.0,
                'final_score': score,
                'is_valid': True,
                'details': []
            }
    
    def analyze(self, symbol, market_snapshots=None, check_recovery_potential=True, min_recovery_pct=0.5):
        """
        Analiza el mercado SOLO para oportunidades de VENTA
        - Usa Professional Dataset si está disponible
        - Aprende de 1000+ snapshots históricos
        - Ajusta umbrales dinámicamente
        
        check_recovery_potential: Verificar potencial de recuperación
        min_recovery_pct: Porcentaje mínimo de potencial requerido
        """
        try:
            # [OK] Actualizar insights del dataset cada 100 análisis
            if hasattr(self, '_analysis_count'):
                self._analysis_count += 1
            else:
                self._analysis_count = 1
            
            if self._analysis_count % 100 == 0:
                self._update_dataset_insights()
            
            # ⭐ NUEVO: Actualizar análisis histórico cada 60 segundos
            current_time = datetime.now().timestamp()
            if current_time - self.last_market_analysis_time >= 60:
                self._analyze_24h_history(symbol)
                self.last_market_analysis_time = current_time
            
            # [OK] PRIORIDAD: Usar datos del Professional Dataset si están disponibles
            if self.dataset_enabled and self.dataset_manager:
                close, high, low, volume = self._get_data_from_professional_dataset()
                data_source = "Professional Dataset"
            # Preferir datos pasados via market_snapshots si se proporcionan
            elif market_snapshots and len(market_snapshots) >= 30:
                # CONVERTIR estructura anidada (price['close']) a plana (snapshot['close'])
                normalized_snaps = self._normalize_snapshots(market_snapshots)
                closes = [float(s.get('close', 0)) for s in normalized_snaps[-100:]]
                highs = [float(s.get('high', 0)) for s in normalized_snaps[-100:]]
                lows = [float(s.get('low', 0)) for s in normalized_snaps[-100:]]
                volumes = [int(s.get('tick_volume', 0)) for s in normalized_snaps[-100:]]
                close = np.array(closes)
                high = np.array(highs)
                low = np.array(lows)
                volume = np.array(volumes)
            else:
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
                rates = mt5_safe._ensure_rates_list(rates)
                if rates is None or len(rates) == 0:
                    return None
                close = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
                high = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates])
                low = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates])
                volume = np.array([float(r['tick_volume']) if isinstance(r, dict) else float(r[5]) for r in rates])
            
            # Calcular indicadores enfocados en VENTA (ampliados)
            features = {
                'rsi': self._calculate_rsi(close),
                'resistance_level': self._find_resistance(high, close[-1]),
                'momentum': self._calculate_momentum(close),
                'macd_signal': self._calculate_macd_bearish(close),
                'volume_trend': self._calculate_volume_trend(volume),
                'bollinger_position': self._calculate_bollinger_position(close),
                'trend_strength': self._calculate_trend_strength(close, 'bearish'),
                'stochastic': self._calculate_stochastic(high, low, close),
                'cci': self._calculate_cci(high, low, close),
                'williams_r': self._calculate_williams_r(high, low, close),
                'adx': self._calculate_adx(high, low, close),
            }
            
            # ⭐ NUEVO (P3 Phase - Historicidad): Actualizar históricos de indicadores
            max_history = 10
            self.rsi_history.append(features['rsi'])
            self.stochastic_history.append(features['stochastic'])
            self.cci_history.append(features['cci'])
            self.williams_r_history.append(features['williams_r'])
            
            # Mantener solo últimos 10 valores
            self.rsi_history = self.rsi_history[-max_history:]
            self.stochastic_history = self.stochastic_history[-max_history:]
            self.cci_history = self.cci_history[-max_history:]
            self.williams_r_history = self.williams_r_history[-max_history:]
            
            # Rastrear condición de sobrecompra (RSI > 70)
            rsi_overbought = features['rsi'] > 70
            self.overbought_condition_history.append(rsi_overbought)
            self.overbought_condition_history = self.overbought_condition_history[-max_history:]
            
            # ⭐ Calcular frescura de condición de sobrecompra
            rsi_freshness = self._calculate_signal_freshness(
                self.overbought_condition_history,
                lambda x: x == True,  # Condición: está en sobrecompra
                max_lookback=max_history
            )
            
            features['rsi_freshness'] = rsi_freshness['freshness_score']
            features['rsi_candles_overbought'] = rsi_freshness['candles_in_condition']
            
            # Log de frescura
            if rsi_freshness['candles_in_condition'] > 0:
                self.log(
                    f"[FRESHNESS] RSI en sobrecompra {rsi_freshness['candles_in_condition']} velas "
                    f"(frescura: {rsi_freshness['freshness_score']}/100, "
                    f"fresh={rsi_freshness['is_fresh']}, stale={rsi_freshness['is_stale']})",
                    'info' if rsi_freshness['is_fresh'] else 'warning'
                )
            
            # ⭐ NUEVO (P0 Phase 7): Calcular factores dinámicos ANTES de scores
            volatility_factor = self._calculate_dynamic_volatility_factor(features)
            
            # Calcular scores individuales para cada señal con volatilidad factorizada
            scores = self._calculate_sell_scores(features, volatility_factor)
            
            # Score final ponderado (sin penalización de tendencia del mercado)
            final_score = sum(scores[k] * self.weights[k] for k in self.weights.keys())
            
            # NUEVO: Bonuses para señales fuertes
            # Si RSI está muy alto (muy overbought) → agregar +30 puntos
            if features['rsi'] > 75:
                final_score += 30
                self.log(f"[BONUS] RSI muy alto ({features['rsi']:.1f}) → +30 puntos", 'success')
            
            # Si MACD está en cruza bajista → agregar +25 puntos
            macd_signal_val = features.get('macd_signal', 0)
            if isinstance(macd_signal_val, (int, float)) and macd_signal_val < 0:
                final_score += 25
                self.log(f"[BONUS] MACD cruza bajista ({macd_signal_val:.4f}) → +25 puntos", 'success')
            
            # Cap final_score a 100
            final_score = min(100, final_score)
            
            # ⭐ NUEVO (P1 Phase 7): Detectar cruces de osciladores (señales nuevas)
            crosses = self._detect_crosses(features)
            
            # ⭐ NUEVO (P1 Phase 7): Detectar divergencias (validar momentum)
            divergences = self._calculate_divergences(features, close[-1] if len(close) > 0 else 0)
            
            # ⭐ NUEVO (P1 Phase 7): Validar calidad integral de la señal
            final_score, quality_rating = self._validate_signal_quality(final_score, crosses, divergences)
            
            self.log(
                f"[SIGNAL_QUALITY] Calidad: {quality_rating} | "
                f"Cruces: {crosses['cross_strength']}/4 | "
                f"Divergencias: {'Bajista ✅' if divergences.get('bearish_divergence') else ('Alcista 🚫' if divergences.get('bullish_divergence') else 'Normal')}",
                'info'
            )
            
            # ⭐ CONFLUENCIA: Solo registro informativo, NO bloquea apertura
            confluent_valid, confluence_reason, confluence_override = self._requires_confluent_entry(
                crosses['cross_strength'],
                divergences
            )
            self.log(f"[CONFLUENCE-INFO] {confluence_reason}", 'info')  # ⭐ Solo loguea, no rechaza
            
            # ⭐ NUEVA (P2 Phase): Detectar velocidad de cambio direccional y obtener bonus
            current_volume_sum = float(np.sum(volume)) if len(volume) > 0 else 0
            velocity_bonus, has_rapid_change, rsi_velocity = self._detect_direction_velocity(
                features['rsi'],
                current_volume_sum
            )
            self.direction_velocity_bonus = velocity_bonus
            self.has_rapid_change = has_rapid_change

            # Reversión rápida bajista: evita rezago del SELL en giros fuertes a la baja.
            if rsi_velocity < -0.8 and features.get('momentum', 0) < 0:
                rebound_bonus = min(25.0, 8.0 + (abs(rsi_velocity) * 4.0))
                prev_score = final_score
                final_score = min(100.0, final_score + rebound_bonus)
                self.log(
                    f"[REBOUND_SELL] RSI vel {rsi_velocity:.2f}/s + momentum {features.get('momentum', 0):.2f} -> score {prev_score:.1f}->{final_score:.1f}",
                    'success'
                )
            
            # Calcular confianza base
            base_confidence = self._calculate_confidence(features, scores)
            
            # Aplicar velocity bonus a confianza (capped at 100%)
            confidence = min(100, base_confidence + velocity_bonus)
            
            # Log de confianza con y sin bonus
            if velocity_bonus > 0:
                self.log(
                    f"[CONFIDENCE] Base: {base_confidence}% + Velocity Bonus: {velocity_bonus} = Final: {confidence}%",
                    'success'
                )
            
            
            # ⭐ FIX: DESACTIVAR FRESHNESS_PENALTY
            # Razón: Velocity bonus ahora siempre es 0, haciendo penalty siempre activo
            # Además: Frescura de RSI NO correlaciona con calidad de entrada
            # Los especialistas ya consideran momentum en sus análisis
            # Aplicar penalty doble causa incongruencia BUY vs SELL
            if False:  # ⭐ Desactivado permanentemente
                pass
            
            # ⭐ Penalizadores por condiciones (ajustan score, no bloquean)
            adx = features.get('adx', 0)
            momentum = features.get('momentum', 0)
            resistance = features.get('resistance_level', 999)
            
            # Penalizar si ADX débil (sin tendencia clara)
            if adx < 20:
                final_score = final_score * 0.8  # -20% score
                self.log(f"[ADX_ANALYSIS] ADX débil ({adx:.1f}) → score -20%", 'info')
            
            # Penalizar si momentum positivo — proporcional a magnitud (espejo de BUY)
            if momentum > 0.5:
                final_score = final_score * 0.50  # -50%: subida muy intensa
                self.log(f"[MOMENTUM_ANALYSIS] Momentum fuerte positivo ({momentum:.2f}) → SELL score -50%", 'warning')
            elif momentum > 0.25:
                final_score = final_score * 0.65  # -35%: subida moderada
                self.log(f"[MOMENTUM_ANALYSIS] Momentum moderado positivo ({momentum:.2f}) → SELL score -35%", 'info')
            elif momentum > 0:
                final_score = final_score * 0.80  # -20%: subida leve
                self.log(f"[MOMENTUM_ANALYSIS] Momentum leve positivo ({momentum:.2f}) → SELL score -20%", 'info')
            
            # Penalizar si resistencia muy lejana
            if resistance > 0.15:
                final_score = final_score * 0.8  # -20% score
                self.log(f"[RESISTANCE_ANALYSIS] Resistencia lejana ({resistance:.2f}%) → score -20%", 'info')
            
            # ⭐ ANÁLISIS: Multi-indicator y Volatilidad AJUSTAN score, NO bloquean
            # Contar indicadores para penalización
            main_indicators_count = 0
            if scores.get('rsi_overbought', 0) >= 40:
                main_indicators_count += 1
            if scores.get('resistance_rejection', 0) >= 40:
                main_indicators_count += 1
            if scores.get('bearish_momentum', 0) >= 40:
                main_indicators_count += 1
            if scores.get('macd_bearish', 0) >= 40:
                main_indicators_count += 1
            if scores.get('volume_confirmation', 0) >= 40:
                main_indicators_count += 1
            
            # ⭐ Si menos de 4 indicadores, penalizar score
            if main_indicators_count < 4:
                final_score = final_score * 0.75  # Penalización: -25% score
                self.log(
                    f"[MULTI_INDICATOR_ANALYSIS] Solo {main_indicators_count}/5 indicadores → score -25%",
                    'info'
                )
            
            # ⭐ Volatilidad ajusta score pero NO bloquea
            volatility = features.get('volatility', 0)
            if volatility > 2.5:
                final_score = final_score * 0.7  # Penalización: -30% score
                self.log(
                    f"[VOLATILIDAD_ANALYSIS] Vol ALTA ({volatility:.2f} ATR) → score -30%",
                    'warning'
                )
            
            # ⭐ Cruces frescos ajustan confianza
            if crosses['cross_strength'] == 0:
                confidence = confidence * 0.85  # Penalización: -15% confianza
                self.log(
                    f"[CRUCE_ANALYSIS] Sin cruces frescos → confianza -15%",
                    'info'
                )

            # ⭐ AJUSTE POR VELAS CONSECUTIVAS (activo desde 2 velas, simétrico con BUY)
            if len(close) >= 2:
                _cn_dir = 1 if close[-1] >= close[-2] else -1
                _cn_count = 0
                for _ci in range(len(close)-1, max(0, len(close)-9), -1):
                    if (_cn_dir == 1 and close[_ci] >= close[_ci-1]) or (_cn_dir == -1 and close[_ci] < close[_ci-1]):
                        _cn_count += 1
                    else:
                        break
                # Velas CONTRA SELL (alcistas)
                if _cn_dir == 1 and _cn_count >= 6:
                    final_score = final_score * 0.35
                    confidence = max(0, confidence * 0.60)
                    self.log(f"[CANDLE_TREND] {_cn_count} velas alcistas → SELL -65%, conf -40%", 'warning')
                elif _cn_dir == 1 and _cn_count >= 4:
                    final_score = final_score * 0.55
                    confidence = max(0, confidence * 0.75)
                    self.log(f"[CANDLE_TREND] {_cn_count} velas alcistas → SELL -45%, conf -25%", 'warning')
                elif _cn_dir == 1 and _cn_count >= 2:
                    final_score = final_score * 0.75
                    confidence = max(0, confidence * 0.88)
                    self.log(f"[CANDLE_TREND] {_cn_count} velas alcistas → SELL -25%, conf -12%", 'warning')
                # Velas A FAVOR de SELL (bajistas)
                elif _cn_dir == -1 and _cn_count >= 6:
                    final_score = min(100, final_score * 1.35)
                    confidence = min(100, confidence + 15)
                    self.log(f"[CANDLE_TREND] {_cn_count} velas bajistas → SELL +35%, conf +15", 'success')
                elif _cn_dir == -1 and _cn_count >= 4:
                    final_score = min(100, final_score * 1.20)
                    confidence = min(100, confidence + 10)
                    self.log(f"[CANDLE_TREND] {_cn_count} velas bajistas → SELL +20%, conf +10", 'success')
                elif _cn_dir == -1 and _cn_count >= 2:
                    final_score = min(100, final_score * 1.10)
                    confidence = min(100, confidence + 5)
                    self.log(f"[CANDLE_TREND] {_cn_count} velas bajistas → SELL +10%, conf +5", 'success')

            # Penalización por riesgo de cambio de tendencia detectado externamente.
            trend_penalty = self._apply_trend_detector_penalty(symbol)
            if trend_penalty < 1.0:
                prev_score = final_score
                final_score = final_score * trend_penalty
                self.log(
                    f"[TREND_PENALTY] Score {prev_score:.1f} → {final_score:.1f} (x{trend_penalty:.2f})",
                    'warning'
                )
            
            # ⭐ Ahora: Siempre recomendar basado en score ajustado
            final_score, confidence, session_detail = self._apply_session_context_bias(final_score, confidence)
            self.log(f"[SESSION] SELL {session_detail}", 'info')
            recommendation = self._make_sell_recommendation(final_score, confidence, features)
            
            # ⭐ NUEVO: Verificar potencial de recuperación ANTES de recomendación final
            if check_recovery_potential:
                recovery_potential = self._calculate_recovery_potential(symbol, features)
                
                if recovery_potential < min_recovery_pct:
                    self.log(
                        f"[ADVERTENCIA] Potencial recuperación BAJO ({recovery_potential:.2f}% < {min_recovery_pct}%) "
                        f"→ RECHAZADA operación SELL",
                        'warning'
                    )
                    recommendation = 'HOLD'
                    final_score = final_score * 0.5
                    confidence = max(0, confidence - 20)
                else:
                    self.log(
                        f"[OK] Potencial recuperación OK ({recovery_potential:.2f}%)",
                        'success'
                    )
            
            # ⭐ NUEVO (P3 Minor): Validar y ponderar signal con utilidades (temporal, outlier, candle)
            if recommendation != 'HOLD':  # Solo validar si la recomendación es positiva
                validation = self._validate_and_weight_signal(
                    final_score,
                    features,
                    close if len(close) > 0 else np.array([]),
                    current_time=datetime.now()
                )
                
                if not validation['is_valid']:
                    # Si ciertas condiciones hacen inválida la señal, rechazarla
                    recommendation = 'HOLD'
                    self.log(f"[VAL&WEIGHT] Señal rechazada: {validation['details']}", 'warning')
                else:
                    # Aplicar ajuste de score
                    final_score = validation['final_score']
                    if validation['final_score'] < final_score:
                        self.log(f"[VAL&WEIGHT] Score ajustado a {final_score}", 'info')
            
            result = {
                'direction': 'SELL',
                'score': final_score,
                'confidence': confidence,
                'recommendation': recommendation,
                'features': features,
                'individual_scores': scores,
                'reasoning': self._generate_reasoning(features, scores),
                'recovery_potential': recovery_potential if check_recovery_potential else None,
                'market_condition': self._get_market_condition(),
                'cross_strength': crosses.get('cross_strength', 0),
                'divergence_type': 'bearish' if divergences.get('bearish_divergence') else ('bullish' if divergences.get('bullish_divergence') else 'none'),
                'signal_quality': quality_rating
                , 'session_context': self.session_context
            }
            
            # ⭐ NUEVO (P1 Phase 7): Guardar históricos para próxima iteración
            self.previous_rsi = features.get('rsi', 50)
            self.previous_stochastic = features.get('stochastic', 50)
            self.previous_cci = features.get('cci', 0)
            self.previous_williams_r = features.get('williams_r', -50)
            self.previous_adx = features.get('adx', 0)
            if len(close) > 0:
                self.previous_price_close = float(close[-1])
                if len(high) > 0:
                    self.previous_price_high = float(high[-1])
                if len(low) > 0:
                    self.previous_price_low = float(low[-1])
            
            self.log(
                f"🔴 {self.name} | Score: {final_score:.1f} | Conf: {confidence}% | "
                f"Recomendación: {recommendation}",
                'info'
            )

            self._update_live_signal_cache(recommendation, confidence, final_score)
            
            return result
            
        except Exception as e:
            self.log(f"[ERROR] Error en {self.name}: {str(e)}", 'error')
            self._update_live_signal_cache('HOLD', 0.0, 0.0)
            return None
    
    def _get_data_from_professional_dataset(self):
        """
        [OK] Extrae datos del Professional Dataset Manager
        Utiliza últimos 100 snapshots para análisis
        """
        try:
            if not self.dataset_manager:
                return None, None, None, None
            
            snapshots = self.dataset_manager.get_snapshots_window(100)
            if not snapshots:
                return None, None, None, None
            
            prices = [s['price']['close'] for s in snapshots]
            highs = [s['price']['high'] for s in snapshots]
            lows = [s['price']['low'] for s in snapshots]
            volumes = [s['volume']['tick_volume'] for s in snapshots]
            
            close = np.array(prices, dtype=np.float64)
            high = np.array(highs, dtype=np.float64)
            low = np.array(lows, dtype=np.float64)
            volume = np.array(volumes, dtype=np.float64)
            
            self.log(f"[OK] Datos cargados desde Professional Dataset: {len(snapshots)} snapshots", 'info')
            
            return close, high, low, volume
            
        except Exception as e:
            self.log(f"[ERROR] Error cargando datos del dataset: {e}", 'error')
            return None, None, None, None
    
    # ⭐ NUEVO: Analizar últimas 24 horas
    def _analyze_24h_history(self, symbol):
        """Analiza el comportamiento del mercado en las últimas 24 horas"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            rates = mt5_safe.copy_rates_range_safe(symbol, mt5.TIMEFRAME_H1, start_date, end_date)
            if rates is None or len(rates) < 10:
                self.log("[ADVERTENCIA] No hay suficientes datos de 24h para análisis", 'warning')
                return
            
            # ⭐ CREAR ARRAYS CON DTYPE EXPLÍCITO (acceso seguro: dicts o tuplas)
            close_24h = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates], dtype=np.float64)
            high_24h = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates], dtype=np.float64)
            low_24h = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates], dtype=np.float64)
            
            # ⭐ EXTRAER ESCALARES INMEDIATAMENTE Y CONVERTIR A PYTHON FLOAT
            max_high = float(np.max(high_24h))
            min_low = float(np.min(low_24h))
            current_close = float(close_24h[-1])
            first_close = float(close_24h[0])
            volatility_std = float(np.std(close_24h))
            
            # ⭐ COMPARACIÓN ENTRE ESCALARES PYTHON PURO (NO NUMPY)
            if current_close > first_close:
                trend = 'ALCISTA'
            else:
                trend = 'BAJISTA'
            
            self.market_history_24h = {
                'highest_24h': max_high,
                'lowest_24h': min_low,
                'current_price': current_close,
                'rsi_24h': float(self._calculate_rsi(close_24h)),
                'trend_24h': trend,
                'volatility_24h': volatility_std,
                'price_range_24h': max_high - min_low,
            }
            
            self.log(
                f"[DATA] Análisis 24h: Rango {min_low:.2f} - "
                f"{max_high:.2f} | Tendencia: {trend}",
                'market'
            )
            
        except Exception as e:
            self.log(f"Error analizando 24h: {str(e)}", 'error')
    
    # ⭐ NUEVO: Calcular potencial de recuperación para SELL
    def _calculate_recovery_potential(self, symbol, features):
        """
        SISTEMA SIMETRICO BUY/SELL: Calcula potencial de recuperación  
        SELL: Ganancia potencial vs Distancia recorrida HACIA ARRIBA
        Inverso al cálculo de BUY para congruencia
        """
        try:
            if self.market_history_24h is None:
                return 100.0
            
            current = float(self.market_history_24h['current_price'])
            highest = float(self.market_history_24h['highest_24h'])
            lowest = float(self.market_history_24h['lowest_24h'])
            
            # SELL: Ganancia potencial vs Distancia recorrida
            # Si precio está cerca del máx 24h → entrada buena para VENTA  
            # Si piso 24h está lejano → salida con ganancia posible
            distance_from_max = ((highest - current) / highest * 100) if highest > 0 else 0
            distance_to_min = ((current - lowest) / current * 100) if current > 0 else 0
            
            # Potencial = Ganancia posible / Distancia ya corrida
            # SELL alto cuando: precio alto (cerca máx) + piso lejano
            if distance_from_max <= 0.1:
                return 100.0  # Precio EN el máximo = entrada perfecta para VENTA
            
            recovery_potential = (distance_to_min / distance_from_max) * 100
            
            self.log(
                f"📉 Análisis Potencial SELL: Soporte -{distance_to_min:.2f}% | "
                f"Resistencia +{distance_from_max:.2f}% | Potencial: {recovery_potential:.2f}%",
                'info'
            )
            
            return float(recovery_potential)
            
        except Exception as e:
            self.log(f"Error calculando potencial: {str(e)}", 'error')
            return 50.0
    
    # ⭐ NUEVO: Obtener condición de mercado
    def _get_market_condition(self):
        """Retorna la condición del mercado basada en análisis de 24h"""
        if self.market_history_24h is None:
            return "DESCONOCIDA"
        
        volatility = float(self.market_history_24h['volatility_24h'])
        trend = self.market_history_24h['trend_24h']
        
        if volatility > 2.0:
            condition = f"{trend} - ALTA VOLATILIDAD"
        elif volatility > 1.0:
            condition = f"{trend} - VOLATILIDAD NORMAL"
        else:
            condition = f"{trend} - BAJA VOLATILIDAD"
        
        return condition
    
    def _calculate_sell_scores(self, features, volatility_factor=1.0):
        """
        Calcula scores individuales para cada indicador de VENTA
        
        ⭐ NUEVO (P0 Phase 7): Ajusta umbrales RSI dinámicamente según volatilidad
        - Volatilidad BAJA → RSI más permisivos (puede ser < 55)
        - Volatilidad ALTA → RSI más estrictos (debe ser > 75)
        """
        scores = {}
        
        # 1. RSI Overbought Score - RECALIBRADO CON VOLATILIDAD DINÁMICA
        rsi = float(features['rsi'])
        # ⭐ Ajustar umbral RSI según volatilidad
        dynamic_rsi_threshold = int(65 * volatility_factor)
        
        if rsi > 80:
            scores['rsi_overbought'] = 100
        elif rsi > 72:  # Cambió de 75 (más sensible)
            scores['rsi_overbought'] = 85
        elif rsi > 68:  # Cambió de 70 (más sensible)
            scores['rsi_overbought'] = 70
        elif rsi > dynamic_rsi_threshold:  # ⭐ Ahora dinámico
            scores['rsi_overbought'] = 50
            self.log(f"[RSI_DYNAMIC] RSI={rsi:.1f} vs threshold={dynamic_rsi_threshold} (factor={volatility_factor}x)", 'info')
        else:
            scores['rsi_overbought'] = max(0, rsi - 55)
        
        # 2. Resistance Rejection Score
        resistance_dist = float(features['resistance_level'])
        if resistance_dist < 0.03:
            scores['resistance_rejection'] = 100
        elif resistance_dist < 0.08:
            scores['resistance_rejection'] = 80
        elif resistance_dist < 0.12:
            scores['resistance_rejection'] = 60
        else:
            scores['resistance_rejection'] = max(0, 100 - (resistance_dist * 300))
        
        # 3. Bearish Momentum Score
        momentum = float(features['momentum'])
        if momentum < -0.5:
            scores['bearish_momentum'] = 100
        elif momentum < -0.25:
            scores['bearish_momentum'] = 80
        elif momentum < 0:
            scores['bearish_momentum'] = 60
        else:  # momentum >= 0 (⭐ FIX: NO dar puntos con momentum positivo)
            scores['bearish_momentum'] = 0
        
        # 4. MACD Bearish Score
        macd = float(features['macd_signal'])
        if macd < 0:
            scores['macd_bearish'] = min(100, abs(macd * 200))
        else:
            scores['macd_bearish'] = 0
        
        # 5. Volume Confirmation Score
        volume_trend = float(features['volume_trend'])
        if volume_trend > 30:
            scores['volume_confirmation'] = 100
        elif volume_trend > 20:
            scores['volume_confirmation'] = 80
        elif volume_trend > 10:
            scores['volume_confirmation'] = 60
        else:
            scores['volume_confirmation'] = 0
        
        # 6. Bollinger Upper Band Score
        bb_pos = float(features['bollinger_position'])
        if bb_pos > 0.9:
            scores['bollinger_upper'] = 100
        elif bb_pos > 0.7:
            scores['bollinger_upper'] = 80
        elif bb_pos > 0.5:
            scores['bollinger_upper'] = 60
        else:
            scores['bollinger_upper'] = max(0, 40 + (bb_pos * 50))  # espejo de BUY: neutro=40pts
        
        # 7. Stochastic Overbought Score
        stoch = float(features['stochastic'])
        if stoch > 80:
            scores['stochastic_overbought'] = 100
        elif stoch > 70:
            scores['stochastic_overbought'] = 80
        elif stoch > 60:
            scores['stochastic_overbought'] = 60
        elif stoch > 50:
            scores['stochastic_overbought'] = 30
        else:
            scores['stochastic_overbought'] = 0
        
        # 8. CCI Bearish Score
        cci = float(features['cci'])
        if cci > 100:
            scores['cci_bearish'] = 100
        elif cci > 50:
            scores['cci_bearish'] = 80
        elif cci > 0:
            scores['cci_bearish'] = 50
        elif cci > -100:
            scores['cci_bearish'] = 20
        else:
            scores['cci_bearish'] = 0
        
        # 9. Williams %R Overbought Score
        williams = float(features['williams_r'])
        if williams > -20:
            scores['williams_r_overbought'] = 100
        elif williams > -50:
            scores['williams_r_overbought'] = 80
        elif williams > -80:
            scores['williams_r_overbought'] = 50
        elif williams > -100:
            scores['williams_r_overbought'] = 20
        else:
            scores['williams_r_overbought'] = 0
        
        # 10. ADX Trend Strength Score
        adx = float(features['adx'])
        if adx >= 40:
            scores['adx_trend_strength'] = 100
        elif adx >= 30:
            scores['adx_trend_strength'] = 80
        elif adx >= 25:
            scores['adx_trend_strength'] = 60
        elif adx >= 20:
            scores['adx_trend_strength'] = 40
        else:
            scores['adx_trend_strength'] = 0
        
        # ⭐ NUEVO (P3 Phase - Penalización por Frescura): 
        # ⭐ MODIFICADO (P2 Phase - Velocity Aware): Solo penalizar si velocity < 0.5/s
        # La penalización se hará en analyze() DESPUÉS de calcular velocity_bonus
        # Aquí simplement NO aplicamos penalización automáticamente
        # (será manejada en analyze() condicionalmente)
        
        return scores

    def _calculate_confidence(self, features, scores):
        """Calcula el nivel de confianza — espejo exacto de BUY specialist (mismos niveles)"""
        strong_signals = sum(1 for s in scores.values() if s >= 60)
        medium_signals = sum(1 for s in scores.values() if 40 <= s < 60)
        adx = features.get('adx', 0)

        if strong_signals >= 5 and adx >= 25:
            confidence = 90
        elif strong_signals >= 4 and adx >= 20:
            confidence = 85
        elif strong_signals >= 3 and adx >= 20:
            confidence = 75
        elif strong_signals >= 2 and medium_signals >= 3 and adx >= 20:
            confidence = 70
        elif strong_signals >= 2 and adx >= 20:
            confidence = 65
        elif medium_signals >= 5 and adx >= 25:
            confidence = 65
        elif medium_signals >= 4 and adx >= 20:
            confidence = 62
        elif medium_signals >= 3 and adx >= 20:
            confidence = 60
        else:
            confidence = 50

        # Penalizar si momentum positivo — proporcional a magnitud (contra dirección SELL)
        momentum = features.get('momentum', 0)
        if momentum > 0.5:
            confidence = max(50, confidence * 0.70)  # -30% conf: subida muy intensa
        elif momentum > 0.25:
            confidence = max(50, confidence * 0.80)  # -20% conf: subida moderada
        elif momentum > 0:
            confidence = max(50, confidence * 0.90)  # -10% conf: subida leve

        return confidence
    
    def _detect_direction_velocity(self, current_rsi, current_volume_sum):
        """
        Detecta microaceleración de señal para entradas tempranas de SELL.
        Usa delta RSI + expansión de volumen como proxy robusto.
        
        Returns: (velocity_bonus, has_rapid_change, rsi_velocity)
        """
        try:
            now = time.time()
            dt = max(0.1, now - float(getattr(self, 'last_analysis_time', now)))

            prev_rsi = float(getattr(self, 'last_rsi', current_rsi))
            prev_vol = float(getattr(self, 'last_volume_sum', current_volume_sum))

            delta_rsi = float(current_rsi) - prev_rsi
            rsi_velocity = delta_rsi / dt
            vol_growth = ((float(current_volume_sum) - prev_vol) / max(1.0, prev_vol))

            velocity_bonus = 0
            has_rapid_change = False

            # SELL: premia aceleración bajista (RSI cayendo) con confirmación de volumen.
            if rsi_velocity < -1.8 and vol_growth > 0.10:
                has_rapid_change = True
                velocity_bonus = 12
            elif rsi_velocity < -1.2 and vol_growth > 0.05:
                has_rapid_change = True
                velocity_bonus = 6

            # Persistir estado para próxima iteración.
            self.last_analysis_time = now
            self.last_rsi = float(current_rsi)
            self.last_volume_sum = float(current_volume_sum)

            return int(velocity_bonus), bool(has_rapid_change), float(rsi_velocity)
            
        except Exception as e:
            self.log(f"[VELOCITY] Error: {e}", 'error')
            return 0, False, 0

    def _make_sell_recommendation(self, score, confidence, features):
        """Abre siempre según score de la microtendencia"""
        # Abre basado en score sin filtros restrictivos
        if score >= 85 and confidence >= 75:
            return 'STRONG_SELL'
        elif score >= 75 and confidence >= 70:
            return 'SELL'
        elif score >= 65 and confidence >= 65:
            return 'WEAK_SELL'
        elif score >= 50 and confidence >= 50:
            return 'WEAK_SELL'  # ⭐ Abre con score moderado según microtendencia
        
        return 'HOLD'

    def _calculate_macd_bearish(self, closes):
        """Calcula MACD enfocado en señales bajistas"""
        if len(closes) < 26:
            return 0.0
        
        ema_fast = self._ema(closes, 12)
        ema_slow = self._ema(closes, 26)
        
        # Asegurar que son escalares
        macd_line = float(ema_fast) - float(ema_slow)
        
        # Calcular signal line correctamente
        if len(closes) >= 9:
            macd_values = []
            for i in range(len(closes)):
                fast = self._ema(closes[:i+1], 12)
                slow = self._ema(closes[:i+1], 26)
                macd_values.append(float(fast) - float(slow))
            
            macd_array = np.array(macd_values)
            signal_line = float(self._ema(macd_array[-9:], 9))
        else:
            signal_line = macd_line
        
        # ⭐ RETORNAR ESCALAR (diferencia normalizada)
        result = float(macd_line - signal_line)
        return result if not np.isnan(result) else 0.0
    
    def _generate_reasoning(self, features, scores):
        """Genera explicación del análisis"""
        reasons = []
        
        if scores.get('rsi_overbought', 0) >= 80:
            reasons.append(f"RSI en sobrecompra ({features['rsi']:.1f})")
        
        if scores.get('resistance_rejection', 0) >= 80:
            reasons.append(f"Cerca de resistencia ({features['resistance_level']:.2f}%)")
        
        if scores.get('bearish_momentum', 0) >= 80:
            reasons.append(f"Momentum bajista fuerte ({features['momentum']:.2f}%)")
        
        if scores.get('macd_bearish', 0) >= 80:
            reasons.append("MACD cruce bajista")
        
        if scores.get('bollinger_upper', 0) >= 80:
            reasons.append("Precio en banda superior Bollinger")
        
        if scores.get('stochastic_overbought', 0) >= 80:
            reasons.append(f"Stochastic en sobrecompra ({features['stochastic']:.1f})")
        
        if scores.get('cci_bearish', 0) >= 80:
            reasons.append(f"CCI alcista extremo ({features['cci']:.0f})")
        
        if scores.get('williams_r_overbought', 0) >= 80:
            reasons.append(f"Williams %R en sobrecompra ({features['williams_r']:.1f})")
        
        if scores.get('adx_trend_strength', 0) >= 80:
            reasons.append(f"Tendencia bajista fuerte (ADX: {features['adx']:.1f})")
        
        return reasons if reasons else ["No hay señales fuertes de venta"]
    
    def log(self, message, tag='info'):
        if tag == 'error':
            if self.log_callback:
                self.log_callback(message, tag)
            return

        # En modo normal suprime ruido de especialistas para no saturar la UI.
        if not getattr(self, 'debug_logs', False):
            if tag in ('info', 'success'):
                return
            if tag == 'warning' and not str(message).startswith('[ERROR]'):
                return

        if self.log_callback:
            self.log_callback(message, tag)
    
    # ========== NOVO: MULTI-TIMEFRAME ANALYSIS ==========
    
    def analyze_multi_timeframe(self, symbol='GOLD'):
        """
        Análisis de SELL en múltiples timeframes (M1, M5, M15, M30, H1)
        Retorna score consolidado y consenso entre timeframes
        
        Returns:
            dict: {
                'multi_tf_score': 0-100,
                'timeframe_scores': {'M1': X, 'M5': Y, ...},
                'consensus': {'has_consensus': bool, 'agreement_count': int, ...},
                'strongest_tf': 'M1'|'M5'|...,
                'weighted_confidence': 0-100,
                'recommendation': 'STRONG_SELL'|'SELL'|'HOLD'|'WEAK_SELL'
            }
        """
        try:
            from multi_timeframe_analyzer import MultiTimeframeAnalyzer
            
            mta = MultiTimeframeAnalyzer(symbol=symbol, log_callback=self.log)
            data = mta.get_all_timeframes()
            
            if data['status'] == 'failed':
                self.log("[MTF] No data loaded from any timeframe", 'warning')
                return None
            
            # Analizar cada timeframe
            tf_scores = {}
            for tf_name in ['M1', 'M5', 'M15', 'M30', 'H1']:
                if tf_name not in data:
                    continue
                
                rates = data[tf_name]
                if rates is None or len(rates) == 0:
                    continue
                
                # Extraer OHLCV
                closes = np.array([r[4] for r in rates])
                highs = np.array([r[2] for r in rates])
                lows = np.array([r[3] for r in rates])
                volumes = np.array([r[5] for r in rates])
                
                # Calcular indicadores en este timeframe
                features = {
                    'rsi': self._calculate_rsi(closes),
                    'resistance_level': self._find_resistance(highs, closes[-1]),
                    'momentum': self._calculate_momentum(closes),
                    'macd_signal': self._calculate_macd_bearish(closes),
                    'volume_trend': self._calculate_volume_trend(volumes),
                    'bollinger_position': self._calculate_bollinger_position(closes),
                    'trend_strength': self._calculate_trend_strength(closes, 'bearish'),
                    'stochastic': self._calculate_stochastic(highs, lows, closes),
                    'cci': self._calculate_cci(highs, lows, closes),
                    'williams_r': self._calculate_williams_r(highs, lows, closes),
                    'adx': self._calculate_adx(highs, lows, closes),
                }
                
                scores = self._calculate_sell_scores(features)
                tf_score = sum(scores.get(k, 0) * self.weights.get(k, 0) for k in self.weights.keys())
                
                # Bonuses por timeframe
                if features['rsi'] > 75:
                    tf_score += 20  # Menos agresivo que en M1
                if features['momentum'] < -0.15:
                    tf_score += 15
                
                tf_score = min(100, tf_score)
                tf_scores[tf_name] = tf_score
                
                self.log(f"[MTF] {tf_name} SELL Score: {tf_score:.1f}", 'info')
            
            if not tf_scores:
                return None
            
            # Consenso entre timeframes
            consensus = mta.get_consensus_signal(tf_scores, threshold=60)
            
            # Score multi-timeframe: promedio ponderado (TF mayores tienen más peso)
            weights_mtf = {'M1': 1.0, 'M5': 1.2, 'M15': 1.3, 'M30': 1.2, 'H1': 1.0}
            weighted_sum = sum(
                tf_scores[tf] * weights_mtf.get(tf, 1.0) 
                for tf in tf_scores 
                if tf in weights_mtf
            )
            weight_total = sum(
                weights_mtf.get(tf, 1.0) 
                for tf in tf_scores 
                if tf in weights_mtf
            )
            multi_tf_score = weighted_sum / weight_total if weight_total > 0 else 0
            
            # Boost de confianza si hay consenso
            confidence_boost = 0
            if consensus['consensus_strength'] >= 80:
                confidence_boost = 25
            elif consensus['consensus_strength'] >= 60:
                confidence_boost = 15
            
            weighted_confidence = min(95, 50 + consensus['consensus_strength']/2 + confidence_boost)
            
            # Recomendación basada en multi-TF
            if multi_tf_score >= 75 and consensus['has_consensus']:
                recommendation = 'STRONG_SELL'
            elif multi_tf_score >= 65:
                recommendation = 'SELL'
            elif multi_tf_score >= 50:
                recommendation = 'WEAK_SELL'
            else:
                recommendation = 'HOLD'
            
            return {
                'multi_tf_score': min(100, multi_tf_score),
                'timeframe_scores': tf_scores,
                'consensus': consensus,
                'strongest_tf': max(tf_scores, key=tf_scores.get) if tf_scores else 'M1',
                'weighted_confidence': weighted_confidence,
                'recommendation': recommendation,
                'data_status': data['status'],
                'timeframes_loaded': data['loaded_timeframes']
            }
            
        except Exception as e:
            self.log(f"[MTF] Error en análisis multi-timeframe: {e}", 'error')
            return None