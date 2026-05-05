"""
🧠 CAPA 1: DATA COLLECTOR - Generador de Snapshots Profesionales
Genera 1000+ datos realistas con microestructura de mercado (XAUUSD)
"""

import json
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path


class MarketSnapshotGenerator:
    """Genera snapshots profesionales de mercado con estructura realista"""
    
    def __init__(self, base_price=5377.50, symbol="GOLD"):
        self.base_price = base_price
        self.current_price = base_price
        self.symbol = symbol  # 🟢 Símbolo configurable: GOLD, XAUUSD, etc
        self.sessions = ["Sydney", "Tokyo", "London", "New York"]
        self.session_hours = {
            "Sydney": (22, 7),      # UTC
            "Tokyo": (0, 9),
            "London": (8, 17),
            "New York": (13, 22),
        }
        
    def _get_session(self, dt):
        """Obtiene la sesión de trading basada en la hora UTC"""
        hour = dt.hour
        for session, (start, end) in self.session_hours.items():
            if start <= hour < end or (start > end and (hour >= start or hour < end)):
                return session
        return "Off-Market"
    
    def _brownian_motion(self, current, volatility=0.0015, drift=0.00001):
        """Movimiento browniano realista de precios"""
        z = np.random.normal(0, 1)
        return current * (1 + drift + volatility * z)
    
    def _generate_candle(self, open_price, volatility=0.002):
        """Genera vela OHLC realista"""
        high = open_price * (1 + abs(np.random.normal(0, volatility)))
        low = open_price * (1 - abs(np.random.normal(0, volatility)))
        close = np.random.uniform(low, high)
        
        return {
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
        }
    
    def _calculate_indicator(self, prices, period, indicator_type='ema'):
        """Calcula indicadores técnicos básicos"""
        if len(prices) < period:
            return prices[-1] if prices else None
        
        if indicator_type == 'ema':
            k = 2.0 / (period + 1)
            ema = prices[0]
            for price in prices[1:]:
                ema = price * k + ema * (1 - k)
            return round(ema, 2)
        elif indicator_type == 'sma':
            return round(np.mean(prices[-period:]), 2)
        elif indicator_type == 'rsi':
            deltas = np.diff(prices[-period-1:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss == 0:
                return 100 if avg_gain > 0 else 50
            rs = avg_gain / avg_loss
            return round(100 - (100 / (1 + rs)), 2)
        elif indicator_type == 'atr':
            true_ranges = []
            for i in range(1, len(prices)):
                tr = max(
                    prices[i] - prices[i-1],
                    abs(prices[i] - prices[i-1])
                )
                true_ranges.append(tr)
            return round(np.mean(true_ranges[-period:]) if true_ranges else 0, 2)
    
    def generate_professional_snapshot(self, timestamp, previous_candle=None, close_price=None):
        """
        🟢 Dataset Optimizado para SCALPING (M1)
        Generador profesional de snapshots
        """
        
        # Generar vela
        if close_price:
            self.current_price = close_price
        candle = self._generate_candle(self.current_price)
        self.current_price = candle['close']
        
        # Bid/Ask spread realista (0.01-0.05 para XAUUSD)
        spread = round(np.random.uniform(0.01, 0.05), 2)
        bid = round(candle['close'] - spread/2, 2)
        ask = round(candle['close'] + spread/2, 2)
        
        # Volúmenes realistas
        tick_volume = np.random.randint(100, 300)
        real_volume = np.random.randint(0, 50)
        delta_volume = np.random.randint(-50, 100)
        buy_volume = max(0, tick_volume // 2 + delta_volume)
        sell_volume = tick_volume - buy_volume
        
        # Volatilidad
        range_px = candle['high'] - candle['low']
        body = abs(candle['close'] - candle['open'])
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        atr_14 = range_px * np.random.uniform(0.8, 1.2)
        
        # Historia de precios para indicadores (últimas 50)
        price_history = [self.current_price]
        prices = [candle['close']]
        
        # Indicadores técnicos simulados
        ema_9 = round(self.current_price * np.random.uniform(0.9995, 1.0005), 2)
        ema_21 = round(self.current_price * np.random.uniform(0.999, 1.001), 2)
        ema_50 = round(self.current_price * np.random.uniform(0.998, 1.002), 2)
        
        rsi_14 = round(np.random.uniform(35, 75), 2)  # RSI realista
        macd = round(np.random.uniform(-0.5, 0.5), 2)
        macd_signal = round(macd * np.random.uniform(0.8, 1.2), 2)
        bollinger_width = round(range_px * np.random.uniform(1, 2), 2)
        
        # Microestructura de mercado
        orderbook_imbalance = round(np.random.uniform(0.4, 0.8), 2)  # Buy/Sell ratio
        liquidity_above = round(ask + np.random.uniform(1, 3), 2)
        liquidity_below = round(bid - np.random.uniform(1, 3), 2)
        
        # Tendencias multi-timeframe (simuladas)
        trend_m5 = np.random.choice(["bullish", "bearish", "neutral"])
        trend_m15 = np.random.choice(["bullish", "bearish", "neutral"])
        
        # Sesión
        session = self._get_session(timestamp)
        
        # Construir snapshot profesional
        snapshot = {
            "symbol": self.symbol,  # 🟢 Usa símbolo configurable (GOLD, XAUUSD, etc)
            "timeframe": "M1",
            "timestamp": timestamp.isoformat(),
            "timestamp_unix": int(timestamp.timestamp()),
            
            # Precio
            "price": {
                "open": candle['open'],
                "high": candle['high'],
                "low": candle['low'],
                "close": candle['close'],
                "bid": bid,
                "ask": ask,
                "spread": spread
            },
            
            # Volumen
            "volume": {
                "tick_volume": tick_volume,
                "real_volume": real_volume,
                "delta_volume": delta_volume,
                "buy_volume": buy_volume,
                "sell_volume": sell_volume
            },
            
            # Volatilidad
            "volatility": {
                "range": round(range_px, 2),
                "body": round(body, 2),
                "upper_wick": round(upper_wick, 2),
                "lower_wick": round(lower_wick, 2),
                "atr_14": round(atr_14, 2)
            },
            
            # Indicadores técnicos
            "indicators": {
                "ema_9": ema_9,
                "ema_21": ema_21,
                "ema_50": ema_50,
                "rsi_14": rsi_14,
                "macd": macd,
                "macd_signal": macd_signal,
                "bollinger_width": bollinger_width
            },
            
            # Microestructura
            "microstructure": {
                "orderbook_imbalance": orderbook_imbalance,
                "liquidity_above": liquidity_above,
                "liquidity_below": liquidity_below
            },
            
            # Contexto
            "context": {
                "session": session,
                "trend_m5": trend_m5,
                "trend_m15": trend_m15
            }
        }
        
        return snapshot
    
    def generate_snapshots(self, start_timestamp=None, output_path="logs/market_snapshots.json", num_snapshots=None, weeks=4):
        """
        Genera snapshots de ultimas N semanas (default 4 semanas)
        Si num_snapshots es None, calcula basado en weeks
        Oro: mercado 24/5 = ~28,800 mins por semana (24*60*5)
        """
        if num_snapshots is None:
            # 4 semanas = ~115,200 minutos (24*60*5*4)
            # Pero para mantener manejable, usar ~20,160 (4 semanas con algo de sparsity)
            num_snapshots = weeks * 24 * 60 * 5
        
        if start_timestamp is None:
            start_timestamp = datetime.utcnow() - timedelta(minutes=num_snapshots)
        
        print(f"[GENERATOR] Generando {num_snapshots} snapshots ({weeks} semanas) para {self.symbol}...")
        
        snapshots = []
        current_timestamp = start_timestamp
        
        for i in range(num_snapshots):
            snapshot = self.generate_professional_snapshot(current_timestamp)
            snapshots.append(snapshot)
            
            self.current_price = snapshot['price']['close']
            current_timestamp += timedelta(minutes=1)
            
            if (i + 1) % max(1, num_snapshots // 10) == 0:
                print(f"  [{i + 1}/{num_snapshots}]")
        
        # Guardar
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_snapshots": len(snapshots),
            "symbol": self.symbol,
            "timeframe": "M1",
            "weeks": weeks,
            "snapshots": snapshots
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f)
        
        print(f"[OK] {len(snapshots)} snapshots guardados en {output_path}")
        return snapshots
    
    def generate_1000_snapshots(self, start_timestamp=None, output_path="logs/market_snapshots.json", num_snapshots=1000):
        """Compatibilidad backward - genera 1000 snapshots"""
        return self.generate_snapshots(start_timestamp, output_path, num_snapshots=num_snapshots)


if __name__ == "__main__":
    generator = MarketSnapshotGenerator(base_price=5377.50, symbol="GOLD")
    snapshots = generator.generate_snapshots(weeks=4)
