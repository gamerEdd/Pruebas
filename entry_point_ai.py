import MetaTrader5 as mt5
import numpy as np
from datetime import datetime, timedelta
import pandas as pd

class EntryPointAI:
    """IA especializada en análisis histórico con múltiples timeframes y períodos"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.last_analysis = None
        self.suggested_price = None
        self.suggested_direction = None
        
    def log(self, message, tag='info'):
        if self.log_callback:
            self.log_callback(message, tag)
    
    # ⭐ NUEVO: Análisis con período y timeframe seleccionables
    def analyze_custom_period(self, symbol, period, timeframe):
        """Analiza un período y timeframe específico"""
        try:
            # ⭐ MAPEO DE TIMEFRAMES
            timeframe_map = {
                "1m": mt5.TIMEFRAME_M1,
                "5m": mt5.TIMEFRAME_M5,
                "15m": mt5.TIMEFRAME_M15,
                "30m": mt5.TIMEFRAME_M30,
                "1h": mt5.TIMEFRAME_H1,
                "4h": mt5.TIMEFRAME_H4,
                "1d": mt5.TIMEFRAME_D1,
                "1w": mt5.TIMEFRAME_W1,
                "1mn": mt5.TIMEFRAME_MN1,
            }
            
            # ⭐ MAPEO DE PERÍODOS ACTUALIZADO
            period_map = {
                "1d": 1,
                "7d": 7,
                "14d": 14,
                "30d": 30,
                "60d": 60,      # ⭐ NUEVO: 2 meses
                "90d": 90,
                "120d": 120,
                "240d": 240,
                "365d": 365,
            }
            
            # ⭐ VALIDACIÓN MEJORADA
            if timeframe not in timeframe_map:
                self.log(f"❌ Período o Timeframe inválido", 'error')
                return None
            
            if period not in period_map:
                self.log(f"❌ Período o Timeframe inválido", 'error')
                return None
            
            mt5_timeframe = timeframe_map[timeframe]
            days = period_map[period]
            
            # ⭐ AJUSTE: Ampliar rango para timeframes 1w y 1mn
            if timeframe == "1w":
                days = max(90, days * 7)  # Mínimo 90 días para 1 semana
            elif timeframe == "1mn":
                days = max(365, days * 30)  # Mínimo 365 días para 1 mes
            
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obtener datos
            rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
            
            if rates is None or len(rates) < 10:
                self.log(f"⚠️ No hay suficientes datos para {period} en timeframe {timeframe}", 'warning')
                self.log(f"   💡 Intenta con un período más largo o timeframe más pequeño", 'info')
                return None
            
            self.log(f"\n{'='*80}", 'info')
            self.log(f"🔍 SUPER ANÁLISIS AVANZADO", 'info')
            self.log(f"   📊 Símbolo: {symbol}", 'info')
            self.log(f"   ⏱️ Período: {period}", 'info')
            self.log(f"   📈 Timeframe: {timeframe}", 'info')
            self.log(f"   📊 Velas analizadas: {len(rates)}", 'info')
            self.log(f"{'='*80}", 'info')
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Realizar análisis
            analysis = self._analyze_custom_period(df, symbol, period, timeframe)
            
            if analysis:
                self.last_analysis = analysis
                self.suggested_price = analysis['suggested_entry_price']
                self.suggested_direction = analysis['suggested_direction']
                
                self._log_custom_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            self.log(f"❌ Error en analyze_custom_period: {str(e)}", 'error')
            return None
    
    def _analyze_custom_period(self, df, symbol, period, timeframe):
        """Realiza el análisis técnico completo para el período/timeframe seleccionado"""
        try:
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            
            # ⭐ NUEVO: Obtener el precio ACTUAL en tiempo real desde MT5
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.log(f"❌ No se pudo obtener el precio actual", 'error')
                return None
            
            current_price = tick.bid  # Usar BID como precio actual de referencia
            
            # --- CÁLCULO DE INDICADORES ---
            rsi = self._calculate_rsi(closes, period=14)
            macd, signal, histogram = self._calculate_macd(closes)
            bb_upper, bb_middle, bb_lower, bb_width = self._calculate_bollinger_bands(closes)
            stoch_k, stoch_d = self._calculate_stochastic(highs, lows, closes)
            atr = self._calculate_atr(highs, lows, closes)
            adx, di_plus, di_minus = self._calculate_adx(highs, lows, closes)
            cci = self._calculate_cci(highs, lows, closes)
            
            # --- ANÁLISIS DE TENDENCIA ---
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else sma_20
            ema_12 = df['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            ema_26 = df['close'].ewm(span=26, adjust=False).mean().iloc[-1] if len(df) >= 26 else ema_12
            
            # --- NIVELES DE SOPORTE/RESISTENCIA ---
            week_high = np.max(highs)
            week_low = np.min(lows)
            support_levels = self._find_support_resistance(lows, current_price, is_support=True)
            resistance_levels = self._find_support_resistance(highs, current_price, is_support=False)
            
            # --- SCORING ---
            buy_score = 0
            sell_score = 0
            signals_list = []
            
            # RSI signals
            if rsi < 30:
                buy_score += 3
                signals_list.append(f"RSI Oversold ({rsi:.1f} < 30)")
            elif rsi > 70:
                sell_score += 3
                signals_list.append(f"RSI Overbought ({rsi:.1f} > 70)")
            elif rsi < 50:
                buy_score += 1
                signals_list.append(f"RSI Tendencia Bajista ({rsi:.1f})")
            else:
                sell_score += 1
                signals_list.append(f"RSI Tendencia Alcista ({rsi:.1f})")
            
            # MACD signals
            if macd > signal:
                buy_score += 2
                signals_list.append(f"MACD Bullish (Histogram: {histogram:.6f})")
            else:
                sell_score += 2
                signals_list.append(f"MACD Bearish (Histogram: {histogram:.6f})")
            
            # Bollinger Bands
            if current_price < bb_lower:
                buy_score += 2
                signals_list.append(f"Precio en Banda Inferior BB ({bb_lower:.5f})")
            elif current_price > bb_upper:
                sell_score += 2
                signals_list.append(f"Precio en Banda Superior BB ({bb_upper:.5f})")
            
            # Stochastic
            if stoch_k < 20:
                buy_score += 2
                signals_list.append(f"Stochastic Oversold ({stoch_k:.1f})")
            elif stoch_k > 80:
                sell_score += 2
                signals_list.append(f"Stochastic Overbought ({stoch_k:.1f})")
            
            # Medias móviles
            if sma_20 > sma_50:
                buy_score += 1
                signals_list.append(f"SMA20 ({sma_20:.5f}) > SMA50 ({sma_50:.5f})")
            else:
                sell_score += 1
                signals_list.append(f"SMA20 ({sma_20:.5f}) < SMA50 ({sma_50:.5f})")
            
            if ema_12 > ema_26:
                buy_score += 1
                signals_list.append(f"EMA12 > EMA26 (Momentum Alcista)")
            else:
                sell_score += 1
                signals_list.append(f"EMA12 < EMA26 (Momentum Bajista)")
            
            # ADX
            if adx > 25:
                if di_plus > di_minus:
                    buy_score += 2
                    signals_list.append(f"ADX Fuerte Alcista ({adx:.1f})")
                else:
                    sell_score += 2
                    signals_list.append(f"ADX Fuerte Bajista ({adx:.1f})")
            
            # CCI
            if cci > 100:
                sell_score += 1
                signals_list.append(f"CCI Sobrecompra ({cci:.1f})")
            elif cci < -100:
                buy_score += 1
                signals_list.append(f"CCI Sobreventa ({cci:.1f})")
            
            # Soporte/Resistencia
            if support_levels and any(abs(current_price - s) < atr * 0.3 for s in support_levels):
                buy_score += 1
                signals_list.append(f"Precio cerca de Soporte")
            if resistance_levels and any(abs(current_price - r) < atr * 0.3 for r in resistance_levels):
                sell_score += 1
                signals_list.append(f"Precio cerca de Resistencia")
            
            # --- GENERAR SUGERENCIA INTELIGENTE ---
            suggested_direction = "BUY" if buy_score > sell_score else "SELL"
            confidence = (max(buy_score, sell_score) / (buy_score + sell_score)) * 100 if (buy_score + sell_score) > 0 else 50
            
            # Calcular precio de entrada sugerido
            if suggested_direction == "BUY":
                # Buscar soporte cercano
                if support_levels:
                    suggested_entry = min(support_levels, key=lambda x: abs(x - current_price))
                else:
                    suggested_entry = current_price - (atr * 0.5)
            else:
                # Buscar resistencia cercana
                if resistance_levels:
                    suggested_entry = min(resistance_levels, key=lambda x: abs(x - current_price))
                else:
                    suggested_entry = current_price + (atr * 0.5)
            
            # Calcular potencial
            if suggested_direction == "BUY":
                resistance_target = max(resistance_levels) if resistance_levels else week_high
                potential_profit = resistance_target - suggested_entry
                distance_from_current = current_price - suggested_entry
            else:
                support_target = min(support_levels) if support_levels else week_low
                potential_profit = suggested_entry - support_target
                distance_from_current = suggested_entry - current_price
            
            return {
                'symbol': symbol,
                'period': period,
                'timeframe': timeframe,
                'current_price': round(current_price, 5),  # ⭐ Ahora es el precio REAL de MT5
                'suggested_direction': suggested_direction,
                'suggested_entry_price': round(suggested_entry, 5),
                'confidence': round(confidence, 1),
                'distance_from_current': round(distance_from_current, 5),
                'potential_profit': round(potential_profit, 5),
                'buy_score': buy_score,
                'sell_score': sell_score,
                'signals': signals_list,
                'indicators': {
                    'rsi': round(rsi, 1),
                    'macd': round(macd, 5),
                    'histogram': round(histogram, 5),
                    'bb_upper': round(bb_upper, 5),
                    'bb_middle': round(bb_middle, 5),
                    'bb_lower': round(bb_lower, 5),
                    'stoch_k': round(stoch_k, 1),
                    'atr': round(atr, 5),
                    'adx': round(adx, 1),
                    'cci': round(cci, 1),
                },
                'levels': {
                    'week_high': round(week_high, 5),
                    'week_low': round(week_low, 5),
                    'support': [round(s, 5) for s in support_levels[:2]],
                    'resistance': [round(r, 5) for r in resistance_levels[:2]],
                }
            }
            
        except Exception as e:
            self.log(f"Error analizando período personalizado: {str(e)}", 'error')
            return None
    
    def _log_custom_analysis(self, analysis):
        """Imprime el análisis de forma legible y profesional"""
        self.log(f"\n{'='*80}", 'success')
        self.log(f"📍 SUGERENCIA DE ENTRADA", 'success')
        self.log(f"{'='*80}", 'success')
        
        # Sugerencia principal
        direction = analysis['suggested_direction']
        entry_price = analysis['suggested_entry_price']
        current = analysis['current_price']
        distance = analysis['distance_from_current']
        
        if direction == "BUY":
            tag = 'success'
            if distance > 0:
                msg = f"🟢 {direction} en {entry_price} (${distance:.5f} debajo del precio actual {current})"
            else:
                msg = f"🟢 {direction} en {entry_price} (${abs(distance):.5f} arriba del precio actual {current})"
        else:
            tag = 'error'
            if distance > 0:
                msg = f"🔴 {direction} en {entry_price} (${distance:.5f} arriba del precio actual {current})"
            else:
                msg = f"🔴 {direction} en {entry_price} (${abs(distance):.5f} debajo del precio actual {current})"
        
        self.log(msg, tag)
        self.log(f"💯 Confianza: {analysis['confidence']:.1f}%", tag)
        self.log(f"📈 Potencial: {analysis['potential_profit']:.5f} puntos", tag)
        
        self.log(f"\n{'='*80}", 'info')
        self.log(f"📊 DATOS DEL ANÁLISIS", 'info')
        self.log(f"{'='*80}", 'info')
        
        indicators = analysis['indicators']
        self.log(f"\n🎯 Indicadores Técnicos:", 'market')
        self.log(f"   RSI: {indicators['rsi']:.1f}", 'info')
        self.log(f"   MACD: {indicators['macd']:.5f} (Signal: {indicators['histogram']:.5f})", 'info')
        self.log(f"   Stochastic K: {indicators['stoch_k']:.1f}", 'info')
        self.log(f"   ADX: {indicators['adx']:.1f}", 'info')
        self.log(f"   ATR: {indicators['atr']:.5f}", 'info')
        self.log(f"   CCI: {indicators['cci']:.1f}", 'info')
        
        self.log(f"\n📈 Bandas de Bollinger:", 'market')
        self.log(f"   Superior: {indicators['bb_upper']:.5f}", 'info')
        self.log(f"   Media: {indicators['bb_middle']:.5f}", 'info')
        self.log(f"   Inferior: {indicators['bb_lower']:.5f}", 'info')
        
        self.log(f"\n🔝 Niveles de Precios:", 'market')
        levels = analysis['levels']
        self.log(f"   Máximo (período): {levels['week_high']:.5f}", 'info')
        self.log(f"   Mínimo (período): {levels['week_low']:.5f}", 'info')
        
        if levels['support']:
            self.log(f"   Soportes: {', '.join([str(s) for s in levels['support']])}", 'info')
        if levels['resistance']:
            self.log(f"   Resistencias: {', '.join([str(r) for r in levels['resistance']])}", 'info')
        
        self.log(f"\n⚖️ Puntuación:", 'market')
        self.log(f"   BUY: {analysis['buy_score']} | SELL: {analysis['sell_score']}", 'info')
        
        self.log(f"\n🎯 Señales Detectadas:", 'market')
        for signal in analysis['signals']:
            self.log(f"   • {signal}", 'warning')
        
        self.log(f"\n{'='*80}\n", 'info')
    
    # --- INDICADORES TÉCNICOS ---
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula el RSI (Relative Strength Index)"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 1
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up / down if down != 0 else 1
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi[-1]
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcula MACD"""
        ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().values
        ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().values
        macd = ema_fast - ema_slow
        signal_line = pd.Series(macd).ewm(span=signal, adjust=False).mean().values
        histogram = macd - signal_line
        
        return macd[-1], signal_line[-1], histogram[-1]
    
    def _calculate_bollinger_bands(self, prices, period=20, num_std=2):
        """Calcula Bandas de Bollinger"""
        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        
        upper_band = sma[-1] + (std[-1] * num_std)
        middle_band = sma[-1]
        lower_band = sma[-1] - (std[-1] * num_std)
        width = upper_band - lower_band
        
        return upper_band, middle_band, lower_band, width
    
    def _calculate_stochastic(self, highs, lows, closes, period=14):
        """Calcula Stochastic"""
        lowest_low = pd.Series(lows).rolling(window=period).min().values[-1]
        highest_high = pd.Series(highs).rolling(window=period).max().values[-1]
        
        k = ((closes[-1] - lowest_low) / (highest_high - lowest_low) * 100) if highest_high != lowest_low else 50
        d = pd.Series([k]).rolling(window=3).mean().values[0]
        
        return k, d
    
    def _calculate_atr(self, highs, lows, closes, period=14):
        """Calcula ATR (Average True Range)"""
        high_low = highs - lows
        high_close = np.abs(highs - np.roll(closes, 1))
        low_close = np.abs(lows - np.roll(closes, 1))
        
        ranges = np.max(np.vstack([high_low, high_close, low_close]), axis=0)
        atr = pd.Series(ranges).rolling(period).mean().values[-1]
        
        return atr
    
    def _calculate_adx(self, highs, lows, closes, period=14):
        """Calcula ADX (Average Directional Index)"""
        high_diff = np.diff(highs)
        low_diff = -np.diff(lows)
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        atr_val = self._calculate_atr(highs, lows, closes, period)
        
        plus_di = 100 * pd.Series(plus_dm).rolling(period).mean().values[-1] / atr_val if atr_val != 0 else 0
        minus_di = 100 * pd.Series(minus_dm).rolling(period).mean().values[-1] / atr_val if atr_val != 0 else 0
        
        di_diff = abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        di_ratio = di_diff / di_sum if di_sum != 0 else 0
        
        adx = 100 * di_ratio
        
        return adx, plus_di, minus_di
    
    def _calculate_cci(self, highs, lows, closes, period=20):
        """Calcula CCI (Commodity Channel Index)"""
        typical_price = (highs + lows + closes) / 3
        sma_tp = pd.Series(typical_price).rolling(period).mean().values
        mad = pd.Series(typical_price).rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean()))).values
        
        cci = (typical_price[-1] - sma_tp[-1]) / (0.015 * mad[-1]) if mad[-1] != 0 else 0
        
        return cci
    
    def _find_support_resistance(self, prices, current_price, is_support=True):
        """Encuentra niveles de soporte o resistencia basados en pivotes"""
        levels = []
        
        for i in range(5, len(prices) - 5):
            if is_support:
                if all(prices[i] <= prices[i-j] for j in range(1, 6)) and \
                   all(prices[i] <= prices[i+j] for j in range(1, 6)):
                    levels.append(prices[i])
            else:
                if all(prices[i] >= prices[i-j] for j in range(1, 6)) and \
                   all(prices[i] >= prices[i+j] for j in range(1, 6)):
                    levels.append(prices[i])
        
        if not levels:
            return []
        
        levels = sorted(set(levels))
        grouped_levels = []
        current_group = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_group[-1]) < (current_price * 0.001):
                current_group.append(level)
            else:
                grouped_levels.append(np.mean(current_group))
                current_group = [level]
        
        if current_group:
            grouped_levels.append(np.mean(current_group))
        
        return grouped_levels
    
    def _log_complete_analysis(self, final_analysis, all_analysis):
        """Imprime el análisis completo de forma detallada"""
        self.log(f"\n{'='*80}", 'success')
        self.log("📍 PUNTO DE ENTRADA SUGERIDO:", 'success')
        self.log(f"   💰 Precio: {final_analysis['entry_price']}", 'success')
        self.log(f"   📊 Dirección: {final_analysis['direction']}", 'success')
        self.log(f"   ✅ Confianza: {final_analysis['confidence']:.1f}%", 'success')
        self.log(f"{'='*80}", 'success')
        
        self.log(f"\n📈 PRECIO ACTUAL: {final_analysis['current_price']}", 'info')
        distance = abs(final_analysis['entry_price'] - final_analysis['current_price'])
        self.log(f"   📏 Distancia: {distance:.5f} puntos", 'info')
        
        self.log(f"\n📊 RANGO SEMANAL:", 'info')
        self.log(f"   🔺 Máximo: {final_analysis['week_high']}", 'info')
        self.log(f"   🔻 Mínimo: {final_analysis['week_low']}", 'info')
        
        self.log(f"\n🎯 INDICADORES PROMEDIADOS (Multi-TF):", 'info')
        self.log(f"   RSI: {final_analysis['rsi']:.1f}", 'info')
        self.log(f"   ATR: {final_analysis['atr']:.5f}", 'info')
        self.log(f"   MACD Histogram: {final_analysis['macd_histogram']:.5f}", 'info')
        
        self.log(f"\n⚖️ SCORING CONSOLIDADO:", 'info')
        self.log(f"   🟢 BUY Score: {final_analysis['buy_score']}", 'info')
        self.log(f"   🔴 SELL Score: {final_analysis['sell_score']}", 'info')
        
        # Detalles por timeframe
        self.log(f"\n{'='*80}", 'info')
        self.log("📊 ANÁLISIS POR TIMEFRAME:", 'info')
        self.log(f"{'='*80}", 'info')
        
        for tf_key, tf_data in all_analysis.items():
            self.log(f"\n⏱️ {tf_data['timeframe']}:", 'market')
            self.log(f"   Precio: {tf_data['current_price']}", 'info')
            self.log(f"   BUY Score: {tf_data['buy_score']} | SELL Score: {tf_data['sell_score']}", 'info')
            
            indicators = tf_data['indicators']
            self.log(f"   RSI: {indicators['rsi']:.1f} | MACD: {indicators['histogram']:.5f}", 'info')
            self.log(f"   Stoch K: {indicators['stoch_k']:.1f} | ADX: {indicators['adx']:.1f}", 'info')
            self.log(f"   Bollinger: U:{indicators['bb_upper']:.5f} M:{indicators['bb_middle']:.5f} L:{indicators['bb_lower']:.5f}", 'info')
            self.log(f"   CCI: {indicators['cci']:.1f}", 'info')
            
            if tf_data['signals']:
                self.log(f"   Señales:", 'warning')
                for signal in tf_data['signals']:
                    self.log(f"      • {signal}", 'warning')
        
        self.log(f"\n{'='*80}\n", 'info')
    
    def check_entry_condition(self, symbol, target_price, tolerance=0.0005):
        """Verifica si el precio current_price está cerca del punto de entrada objetivo"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False, None
            
            current_price = tick.ask if self.suggested_direction == "BUY" else tick.bid
            
            # Calcular si está dentro del rango de tolerancia
            price_diff = abs(current_price - target_price)
            threshold = target_price * tolerance  # 0.05% por defecto
            
            within_range = price_diff <= threshold
            
            return within_range, current_price
            
        except Exception as e:
            self.log(f"Error verificando condición de entrada: {str(e)}", 'error')
            return False, None
    
    def get_last_suggestion(self):
        """Devuelve la última sugerencia de entrada"""
        return {
            'price': self.suggested_price,
            'direction': self.suggested_direction,
            'analysis': self.last_analysis
        }
    
    def analyze_7_days_history(self, symbol):
        """Analiza los últimos 7 días del par en múltiples timeframes"""
        try:
            self.log(f"\n{'='*80}", 'info')
            self.log("🔍 ANÁLISIS HISTÓRICO DE 7 DÍAS - PUNTO DE ENTRADA IA", 'info')
            self.log("📊 Analizando múltiples timeframes (1m, 15m, 1h, 1d)...", 'info')
            self.log(f"{'='*80}", 'info')
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Análisis por timeframe
            timeframes = {
                'M1': (mt5.TIMEFRAME_M1, "1 Minuto"),
                'M15': (mt5.TIMEFRAME_M15, "15 Minutos"),
                'H1': (mt5.TIMEFRAME_H1, "1 Hora"),
                'D1': (mt5.TIMEFRAME_D1, "1 Día")
            }
            
            all_analysis = {}
            scores = {'BUY': 0, 'SELL': 0}
            
            for tf_key, (tf_value, tf_name) in timeframes.items():
                self.log(f"\n📈 Analizando {tf_name}...", 'info')
                
                rates = mt5.copy_rates_range(symbol, tf_value, start_date, end_date)
                if rates is None or len(rates) < 50:
                    self.log(f"   ⚠️ Datos insuficientes para {tf_name}", 'warning')
                    continue
                
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                analysis = self._analyze_timeframe(df, tf_name, symbol)
                if analysis:
                    all_analysis[tf_key] = analysis
                    scores['BUY'] += analysis['buy_score']
                    scores['SELL'] += analysis['sell_score']
            
            # Análisis consolidado
            final_analysis = self._consolidate_analysis(all_analysis, scores, symbol)
            
            if final_analysis:
                self.last_analysis = final_analysis
                self.suggested_price = final_analysis['entry_price']
                self.suggested_direction = final_analysis['direction']
                
                self._log_complete_analysis(final_analysis, all_analysis)
                
            return final_analysis
            
        except Exception as e:
            self.log(f"❌ Error en análisis de 7 días: {str(e)}", 'error')
            return None
    
    def _analyze_timeframe(self, df, tf_name, symbol):
        """Analiza un timeframe específico con todos los indicadores"""
        try:
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            
            # --- 1. MEDIA MÓVIL SIMPLE Y EXPONENCIAL ---
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
            ema_12 = df['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            ema_26 = df['close'].ewm(span=26, adjust=False).mean().iloc[-1]
            
            # --- 2. RSI (Relative Strength Index) ---
            rsi = self._calculate_rsi(closes, period=14)
            
            # --- 3. MACD (Moving Average Convergence Divergence) ---
            macd, signal, histogram = self._calculate_macd(closes)
            
            # --- 4. Bandas de Bollinger ---
            bb_upper, bb_middle, bb_lower, bb_width = self._calculate_bollinger_bands(closes, period=20)
            
            # --- 5. Stochastic ---
            stoch_k, stoch_d = self._calculate_stochastic(highs, lows, closes, period=14)
            
            # --- 6. ATR (Average True Range) ---
            atr = self._calculate_atr(highs, lows, closes, period=14)
            
            # --- 7. ADX (Average Directional Index) ---
            adx, di_plus, di_minus = self._calculate_adx(highs, lows, closes, period=14)
            
            # --- 8. CCI (Commodity Channel Index) ---
            cci = self._calculate_cci(highs, lows, closes, period=20)
            
            # --- 9. Momentum ---
            momentum = closes[-1] - closes[-20] if len(closes) > 20 else 0
            
            # --- 10. Volume Profile (precio más frecuente) ---
            current_price = closes[-1]
            
            # Análisis de niveles
            week_high = np.max(highs)
            week_low = np.min(lows)
            support_levels = self._find_support_resistance(lows, current_price, is_support=True)
            resistance_levels = self._find_support_resistance(highs, current_price, is_support=False)
            
            # --- SCORING ---
            buy_score = 0
            sell_score = 0
            signals_list = []
            
            # RSI signals
            if rsi < 30:
                buy_score += 2
                signals_list.append("RSI Oversold (<30)")
            elif rsi > 70:
                sell_score += 2
                signals_list.append("RSI Overbought (>70)")
            
            # MACD signals
            if macd > signal:
                buy_score += 2
                signals_list.append("MACD Bullish (Arriba de Signal)")
            else:
                sell_score += 2
                signals_list.append("MACD Bearish (Abajo de Signal)")
            
            # Bollinger Bands signals
            if current_price < bb_lower:
                buy_score += 2
                signals_list.append("Precio en Banda Inferior de Bollinger")
            elif current_price > bb_upper:
                sell_score += 2
                signals_list.append("Precio en Banda Superior de Bollinger")
            
            # Stochastic signals
            if stoch_k < 20:
                buy_score += 1
                signals_list.append("Stochastic Oversold (<20)")
            elif stoch_k > 80:
                sell_score += 1
                signals_list.append("Stochastic Overbought (>80)")
            
            # SMA/EMA signals
            if sma_20 > sma_50:
                buy_score += 1
                signals_list.append("SMA20 > SMA50 (Tendencia Alcista)")
            else:
                sell_score += 1
                signals_list.append("SMA20 < SMA50 (Tendencia Bajista)")
            
            if ema_12 > ema_26:
                buy_score += 1
                signals_list.append("EMA12 > EMA26 (Momentum Positivo)")
            else:
                sell_score += 1
                signals_list.append("EMA12 < EMA26 (Momentum Negativo)")
            
            # ADX signals (fuerza de tendencia)
            if adx > 25:
                if di_plus > di_minus:
                    buy_score += 2
                    signals_list.append(f"ADX Fuerte Alcista ({adx:.1f})")
                else:
                    sell_score += 2
                    signals_list.append(f"ADX Fuerte Bajista ({adx:.1f})")
            
            # CCI signals
            if cci > 100:
                buy_score += 1
                signals_list.append("CCI Sobrecompra")
            elif cci < -100:
                sell_score += 1
                signals_list.append("CCI Sobreventa")
            
            # Momentum signals
            if momentum > 0:
                buy_score += 1
                signals_list.append("Momentum Positivo")
            else:
                sell_score += 1
                signals_list.append("Momentum Negativo")
            
            # Soporte/Resistencia signals
            if support_levels and any(abs(current_price - s) < atr * 0.3 for s in support_levels):
                buy_score += 1
                signals_list.append("Precio cerca de Soporte")
            if resistance_levels and any(abs(current_price - r) < atr * 0.3 for r in resistance_levels):
                sell_score += 1
                signals_list.append("Precio cerca de Resistencia")
            
            return {
                'timeframe': tf_name,
                'current_price': round(current_price, 5),
                'buy_score': buy_score,
                'sell_score': sell_score,
                'signals': signals_list,
                'indicators': {
                    'rsi': round(rsi, 1),
                    'macd': round(macd, 5),
                    'signal_line': round(signal, 5),
                    'histogram': round(histogram, 5),
                    'bb_upper': round(bb_upper, 5),
                    'bb_middle': round(bb_middle, 5),
                    'bb_lower': round(bb_lower, 5),
                    'bb_width': round(bb_width, 5),
                    'stoch_k': round(stoch_k, 1),
                    'stoch_d': round(stoch_d, 1),
                    'atr': round(atr, 5),
                    'adx': round(adx, 1),
                    'di_plus': round(di_plus, 1),
                    'di_minus': round(di_minus, 1),
                    'cci': round(cci, 1),
                    'sma_20': round(sma_20, 5),
                    'sma_50': round(sma_50, 5),
                    'ema_12': round(ema_12, 5),
                    'ema_26': round(ema_26, 5),
                    'momentum': round(momentum, 5),
                },
                'support_levels': [round(s, 5) for s in support_levels[:3]],
                'resistance_levels': [round(r, 5) for r in resistance_levels[:3]],
                'week_high': round(week_high, 5),
                'week_low': round(week_low, 5),
            }
            
        except Exception as e:
            self.log(f"   Error analizando {tf_name}: {str(e)}", 'error')
            return None
    
    def _consolidate_analysis(self, all_analysis, scores, symbol):
        """Consolida el análisis de múltiples timeframes"""
        try:
            if not all_analysis:
                return None
            
            # Promediar precios actuales
            prices = [tf['current_price'] for tf in all_analysis.values()]
            current_price = np.mean(prices)
            
            # Decisión basada en scoring total
            total_buy = scores['BUY']
            total_sell = scores['SELL']
            
            if total_buy > total_sell:
                direction = "BUY"
                confidence = (total_buy / (total_buy + total_sell)) * 100 if (total_buy + total_sell) > 0 else 50
                # Usar soporte para entrada
                support_levels = []
                for tf in all_analysis.values():
                    support_levels.extend(tf['support_levels'])
                
                if support_levels:
                    entry_price = min(support_levels, key=lambda x: abs(x - current_price))
                else:
                    # Un poco debajo del precio actual
                    atr_ref = all_analysis['M1']['indicators']['atr'] if 'M1' in all_analysis else 0.5
                    entry_price = current_price - (atr_ref * 0.5)
            else:
                direction = "SELL"
                confidence = (total_sell / (total_buy + total_sell)) * 100 if (total_buy + total_sell) > 0 else 50
                # Usar resistencia para entrada
                resistance_levels = []
                for tf in all_analysis.values():
                    resistance_levels.extend(tf['resistance_levels'])
                
                if resistance_levels:
                    entry_price = min(resistance_levels, key=lambda x: abs(x - current_price))
                else:
                    # Un poco arriba del precio actual
                    atr_ref = all_analysis['M1']['indicators']['atr'] if 'M1' in all_analysis else 0.5
                    entry_price = current_price + (atr_ref * 0.5)
            
            # Compilar información general
            week_high = max(tf['week_high'] for tf in all_analysis.values())
            week_low = min(tf['week_low'] for tf in all_analysis.values())
            
            # RSI promedio
            rsi_values = [tf['indicators']['rsi'] for tf in all_analysis.values()]
            avg_rsi = np.mean(rsi_values)
            
            # MACD promedio
            macd_values = [tf['indicators']['histogram'] for tf in all_analysis.values()]
            avg_macd_histogram = np.mean(macd_values)
            
            # ATR promedio
            atr_values = [tf['indicators']['atr'] for tf in all_analysis.values()]
            avg_atr = np.mean(atr_values)
            
            return {
                'entry_price': round(entry_price, 5),
                'direction': direction,
                'confidence': round(confidence, 1),
                'current_price': round(current_price, 5),
                'week_high': round(week_high, 5),
                'week_low': round(week_low, 5),
                'atr': round(avg_atr, 5),
                'rsi': round(avg_rsi, 1),
                'macd_histogram': round(avg_macd_histogram, 5),
                'buy_score': total_buy,
                'sell_score': total_sell,
                'timeframe_analysis': all_analysis,
                'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            self.log(f"Error consolidando análisis: {str(e)}", 'error')
            return None
    
    # --- INDICADORES TÉCNICOS ---
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula el RSI (Relative Strength Index)"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 1
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up / down if down != 0 else 1
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi[-1]
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcula MACD"""
        ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().values
        ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().values
        macd = ema_fast - ema_slow
        signal_line = pd.Series(macd).ewm(span=signal, adjust=False).mean().values
        histogram = macd - signal_line
        
        return macd[-1], signal_line[-1], histogram[-1]
    
    def _calculate_bollinger_bands(self, prices, period=20, num_std=2):
        """Calcula Bandas de Bollinger"""
        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        
        upper_band = sma[-1] + (std[-1] * num_std)
        middle_band = sma[-1]
        lower_band = sma[-1] - (std[-1] * num_std)
        width = upper_band - lower_band
        
        return upper_band, middle_band, lower_band, width
    
    def _calculate_stochastic(self, highs, lows, closes, period=14):
        """Calcula Stochastic"""
        lowest_low = pd.Series(lows).rolling(window=period).min().values[-1]
        highest_high = pd.Series(highs).rolling(window=period).max().values[-1]
        
        k = ((closes[-1] - lowest_low) / (highest_high - lowest_low) * 100) if highest_high != lowest_low else 50
        d = pd.Series([k]).rolling(window=3).mean().values[0]
        
        return k, d
    
    def _calculate_atr(self, highs, lows, closes, period=14):
        """Calcula ATR (Average True Range)"""
        high_low = highs - lows
        high_close = np.abs(highs - np.roll(closes, 1))
        low_close = np.abs(lows - np.roll(closes, 1))
        
        ranges = np.max(np.vstack([high_low, high_close, low_close]), axis=0)
        atr = pd.Series(ranges).rolling(period).mean().values[-1]
        
        return atr
    
    def _calculate_adx(self, highs, lows, closes, period=14):
        """Calcula ADX (Average Directional Index)"""
        high_diff = np.diff(highs)
        low_diff = -np.diff(lows)
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        atr_val = self._calculate_atr(highs, lows, closes, period)
        
        plus_di = 100 * pd.Series(plus_dm).rolling(period).mean().values[-1] / atr_val if atr_val != 0 else 0
        minus_di = 100 * pd.Series(minus_dm).rolling(period).mean().values[-1] / atr_val if atr_val != 0 else 0
        
        di_diff = abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        di_ratio = di_diff / di_sum if di_sum != 0 else 0
        
        adx = 100 * di_ratio
        
        return adx, plus_di, minus_di
    
    def _calculate_cci(self, highs, lows, closes, period=20):
        """Calcula CCI (Commodity Channel Index)"""
        typical_price = (highs + lows + closes) / 3
        sma_tp = pd.Series(typical_price).rolling(period).mean().values
        mad = pd.Series(typical_price).rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean()))).values
        
        cci = (typical_price[-1] - sma_tp[-1]) / (0.015 * mad[-1]) if mad[-1] != 0 else 0
        
        return cci
    
    def analyze_hierarchical_timeframes(self, symbol, base_period="1d"):
        """
        Análisis jerárquico: dado un período base, genera sugerencias en múltiples timeframes
        ordenadas por confianza (mayor primero).
        
        Base period → timeframes menores:
        - 1d → [1m, 5m, 15m, 30m, 1h, 4h, 1d]
        - 7d → [1m, 5m, 15m, 30m, 1h, 4h, 1d]
        - etc.
        
        Returns: {
            'period': '1d',
            'options': [
                {
                    'rank': 1,
                    'timeframe': '1h',
                    'confidence': 87.5,
                    'direction': 'BUY',
                    'entry_price': 2050.25,
                    'indicators': {...},
                    'reasoning': [...]
                },
                ...
            ],
            'best_option': {...}  # Option con confianza más alta
        }
        """
        try:
            # Mapeo período → timeframes a analizar
            period_to_timeframes = {
                '1d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                '7d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                '14d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                '30d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
                '60d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
                '90d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
                '120d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
                '240d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
                '365d': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
            }
            
            timeframes = period_to_timeframes.get(base_period, ['1m', '5m', '15m', '30m', '1h', '4h', '1d'])
            
            options = []
            
            # Analizar cada timeframe
            for tf in timeframes:
                analysis = self.analyze_custom_period(symbol, base_period, tf)
                
                if analysis:
                    option = {
                        'timeframe': tf,
                        'confidence': analysis['confidence'],
                        'direction': analysis['suggested_direction'],
                        'entry_price': analysis['suggested_entry_price'],
                        'current_price': analysis['current_price'],
                        'potential_profit': analysis['potential_profit'],
                        'indicators': analysis['indicators'],
                        'distance_from_current': analysis['distance_from_current']
                    }
                    options.append(option)
            
            # Ordenar por confianza (mayor primero)
            options.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Agregar ranking
            for rank, option in enumerate(options, 1):
                option['rank'] = rank
            
            result = {
                'period': base_period,
                'options': options,
                'best_option': options[0] if options else None,
                'total_options': len(options)
            }
            
            return result
            
        except Exception as e:
            self.log(f"Error en análisis jerárquico: {str(e)}", 'error')
            return None
    
    # ⭐ NUEVO: ANÁLISIS AVANZADO CON MÁXIMA PRECISIÓN
    def analyze_ultra_precise(self, symbol, period, timeframe):
        """Análisis ultra-preciso con parámetros avanzados para entrada óptima"""
        try:
            result = self.analyze_custom_period(symbol, period, timeframe)
            if not result:
                return None
            
            # Obtener datos OHLC para análisis adicional
            timeframe_map = {
                "1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
                "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1, "4h": mt5.TIMEFRAME_H4,
                "1d": mt5.TIMEFRAME_D1, "1w": mt5.TIMEFRAME_W1, "1mn": mt5.TIMEFRAME_MN1,
            }
            
            mt5_tf = timeframe_map[timeframe]
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            rates = mt5.copy_rates_range(symbol, mt5_tf, start_date, end_date)
            if rates is None or len(rates) < 50:
                return result
            
            df = pd.DataFrame(rates)
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            
            # ⭐ PARÁMETROS DE PRECISIÓN ADICIONALES
            precision_data = {
                'volatility_score': self._calculate_volatility_score(closes),
                'trend_strength': self._calculate_trend_strength(closes),
                'mean_reversion_probability': self._calculate_mean_reversion(closes),
                'support_resistance_strength': self._calculate_sr_strength(highs, lows, closes),
                'volume_confirmation': self._calculate_volume_score(df),
                'pattern_recognition': self._recognize_patterns(df),
                'optimal_entry': self._find_optimal_entry(result, closes, highs, lows),
                'price_level_score': self._calculate_price_level_precision(closes, result),
            }
            
            # Combinar con resultado anterior
            result['precision_analysis'] = precision_data
            result['precision_score'] = self._calculate_final_precision_score(precision_data)
            
            self._log_precision_analysis(result)
            
            return result
            
        except Exception as e:
            self.log(f"Error en análisis ultra-preciso: {str(e)}", 'error')
            return None
    
    def _calculate_volatility_score(self, closes):
        """Calcula score de volatilidad (0-100)"""
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * 100
        # Normalizar a 0-100: volatilidad alta = mayor score
        score = min(100, volatility * 1000)
        return round(score, 1)
    
    def _calculate_trend_strength(self, closes):
        """Calcula fuerza de tendencia con múltiples métodos"""
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        sma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else np.mean(closes)
        
        trend_bullish = (closes[-1] > sma_20) and (sma_20 > sma_50) and (sma_50 > sma_200)
        trend_bearish = (closes[-1] < sma_20) and (sma_20 < sma_50) and (sma_50 < sma_200)
        
        if trend_bullish:
            strength = 85 + (closes[-1] - sma_200) / sma_200 * 10
        elif trend_bearish:
            strength = -85 - (sma_200 - closes[-1]) / sma_200 * 10
        else:
            strength = 0
        
        return round(min(100, max(-100, strength)), 1)
    
    def _calculate_mean_reversion(self, closes):
        """Calcula probabilidad de reversión a la media"""
        sma = np.mean(closes[-50:])
        current_distance = (closes[-1] - sma) / sma * 100
        
        # Si está muy alejado, hay mayor probabilidad de reversión
        if abs(current_distance) > 3:
            probability = 80
        elif abs(current_distance) > 2:
            probability = 60
        elif abs(current_distance) > 1:
            probability = 40
        else:
            probability = 20
        
        return round(probability, 1)
    
    def _calculate_sr_strength(self, highs, lows, closes):
        """Calcula fuerza de niveles soporte/resistencia"""
        support_levels = self._find_support_resistance(lows, closes[-1], is_support=True)
        resistance_levels = self._find_support_resistance(highs, closes[-1], is_support=False)
        
        # Score basado en cercanía y número de niveles
        sr_score = (len(support_levels) + len(resistance_levels)) * 10
        sr_score = min(100, sr_score)
        
        return round(sr_score, 1)
    
    def _calculate_volume_score(self, df):
        """Calcula confirmación de volumen"""
        if 'tick_volume' in df.columns:
            recent_vol = df['tick_volume'].tail(20).mean()
            overall_vol = df['tick_volume'].mean()
            vol_ratio = recent_vol / overall_vol if overall_vol > 0 else 1
            score = (vol_ratio - 1) * 50 + 50  # Normalizar a 0-100
            return round(min(100, max(0, score)), 1)
        return 50.0
    
    def _recognize_patterns(self, df):
        """Reconoce patrones de precio"""
        patterns = []
        closes = df['close'].values
        
        # Patrón de fondo (V shape)
        if len(closes) >= 10:
            if closes[-1] > closes[-5] and closes[-5] < closes[-10]:
                patterns.append(("V-Bottom", 75))
            # Patrón de techo (Reverse V)
            if closes[-1] < closes[-5] and closes[-5] > closes[-10]:
                patterns.append(("V-Top", 75))
            # Triple bottom
            lows_3 = [closes[i] for i in [-10, -5, -1]]
            if len(set([round(l, 2) for l in lows_3])) == 1:
                patterns.append(("Triple-Bottom", 85))
        
        return patterns
    
    def _find_optimal_entry(self, analysis, closes, highs, lows):
        """Encuentra el punto de entrada más óptimo"""
        suggested_entry = analysis['suggested_entry_price']
        direction = analysis['suggested_direction']
        atr = analysis['indicators'].get('atr', 1.0)
        
        # Ajustar entrada basado en volatilidad
        if direction == "BUY":
            # Buscar soporte inmediato
            optimal = suggested_entry - (atr * 0.2)
            confirmation_price = suggested_entry + (atr * 0.1)
        else:
            # Buscar resistencia inmediata
            optimal = suggested_entry + (atr * 0.2)
            confirmation_price = suggested_entry - (atr * 0.1)
        
        return {
            'primary_entry': round(suggested_entry, 5),
            'optimal_entry': round(optimal, 5),
            'confirmation_price': round(confirmation_price, 5),
            'entry_zone_width': round(abs(optimal - suggested_entry) * 2, 5),
        }
    
    def _calculate_price_level_precision(self, closes, analysis):
        """Calcula precisión del nivel de precio sugerido"""
        # Analizar si el precio sugerido está en un nivel "redondo" o soporte
        suggested = analysis['suggested_entry_price']
        last_prices = closes[-100:]
        
        # Contar cuántas veces el precio ha rebotado en este nivel
        rebounds = sum(1 for p in last_prices if abs(p - suggested) < 0.001)
        
        # Score basado en rebotes (máximo 100)
        precision = min(100, rebounds * 10)
        
        return round(precision, 1)
    
    def _calculate_final_precision_score(self, precision_data):
        """Calcula el score final de precisión ponderado"""
        weights = {
            'volatility_score': 0.15,
            'trend_strength': 0.20,  # Mayor peso en la tendencia
            'mean_reversion_probability': 0.15,
            'support_resistance_strength': 0.15,
            'volume_confirmation': 0.10,
            'price_level_score': 0.15,  # Precisión del nivel
        }
        
        final_score = 0
        for metric, weight in weights.items():
            if metric in precision_data:
                value = precision_data[metric]
                # Normalizar a 0-100 si es necesario
                if isinstance(value, dict):
                    value = value.get('entry_zone_width', 50)
                if isinstance(value, list):
                    value = len(value) * 20
                
                value = min(100, max(0, abs(value)))
                final_score += value * weight
        
        return round(final_score, 1)
    
    def _log_precision_analysis(self, result):
        """Loguea el análisis de precisión de forma legible"""
        if 'precision_analysis' not in result:
            return
        
        precision = result['precision_analysis']
        
        self.log(f"\n{'='*80}", 'success')
        self.log(f"⭐ ANÁLISIS DE PRECISIÓN", 'success')
        self.log(f"{'='*80}", 'success')
        self.log(f"📊 Score de Volatilidad: {precision.get('volatility_score', 0)}%", 'info')
        self.log(f"📈 Fuerza de Tendencia: {precision.get('trend_strength', 0):+.1f}", 'info')
        self.log(f"🔄 Probabilidad Reversión: {precision.get('mean_reversion_probability', 0)}%", 'info')
        self.log(f"🎯 Fuerza S/R: {precision.get('support_resistance_strength', 0)}%", 'info')
        self.log(f"📦 Confirmación Volumen: {precision.get('volume_confirmation', 0)}%", 'info')
        
        optimal = precision.get('optimal_entry', {})
        if optimal:
            self.log(f"\n🔍 ENTRADA ÓPTIMA:", 'warning')
            self.log(f"   Principal: {optimal.get('primary_entry', 'N/A')}", 'info')
            self.log(f"   Óptima: {optimal.get('optimal_entry', 'N/A')}", 'success')
            self.log(f"   Confirmación: {optimal.get('confirmation_price', 'N/A')}", 'info')
            self.log(f"   Zona: ±{optimal.get('entry_zone_width', 'N/A')}", 'info')
        
        patterns = precision.get('pattern_recognition', [])
        if patterns:
            self.log(f"\n🎨 PATRONES DETECTADOS:", 'warning')
            for pattern_name, confidence in patterns:
                self.log(f"   • {pattern_name} ({confidence}% confianza)", 'success')
        
        precision_score = result.get('precision_score', 0)
        self.log(f"\n{'='*80}", 'success')
        self.log(f"✅ SCORE FINAL DE PRECISIÓN: {precision_score}%", 'success')
        self.log(f"{'='*80}", 'success')