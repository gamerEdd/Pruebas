"""
📊 CAPA 2: FEATURE ENGINE - Gestor de Dataset Profesional
Lectura, actualización y cálculo de features para IA
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque


class ProfessionalDatasetManager:
    """
    Gestor centralizado de datos profesionales
    - Lee 1000+ snapshots
    - Calcula features para IA
    - Actualiza cada 5 minutos
    - Expone datos a especialistas
    """
    
    def __init__(self, dataset_path="logs/market_snapshots.json", max_snapshots=1000, log_callback=None, symbol="GOLD"):
        self.dataset_path = Path(dataset_path)
        self.max_snapshots = max_snapshots
        self.log_callback = log_callback
        self.symbol = symbol  # 🟢 Símbolo dinámico
        self.snapshots = deque(maxlen=max_snapshots)
        self.feature_cache = {}
        self.last_update = None
        
        self.load_dataset()
    
    def log(self, message, level='info'):
        """Callback para logs"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    
    def load_dataset(self):
        """Carga el dataset de snapshots desde archivo"""
        if not self.dataset_path.exists():
            self.log(f"⚠️ Dataset no encontrado: {self.dataset_path}", 'warning')
            return False
        
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
            
            # 🟢 Verificar que el símbolo coincida
            symbol_in_file = data.get('symbol', 'UNKNOWN')
            if symbol_in_file != self.symbol:
                self.log(
                    f"⚠️ Símbolo en archivo ({symbol_in_file}) != símbolo esperado ({self.symbol}). "
                    f"Actualizando a {self.symbol}",
                    'warning'
                )
                self.symbol = symbol_in_file  # Adaptar al archivo
            
            self.snapshots = deque(data.get('snapshots', []), maxlen=self.max_snapshots)
            self.log(f"✅ Dataset cargado: {len(self.snapshots)} snapshots para {self.symbol}", 'info')
            return True
        except Exception as e:
            self.log(f"❌ Error cargando dataset: {e}", 'error')
            return False
    
    def add_snapshot(self, snapshot):
        """Agrega un nuevo snapshot (para actualización en tiempo real)"""
        self.snapshots.append(snapshot)
        self.feature_cache.clear()  # Invalidar cache
    
    def get_latest_snapshot(self):
        """Obtiene el snapshot más reciente"""
        return self.snapshots[-1] if self.snapshots else None
    
    def get_snapshots_window(self, count=50):
        """Obtiene últimos N snapshots"""
        return list(self.snapshots)[-count:]
    
    def get_price_history(self, count=200):
        """Obtiene historial de precios para indicadores"""
        return [s['price']['close'] for s in list(self.snapshots)[-count:]]
    
    def calculate_feature(self, feature_name, snapshot=None, window_size=50):
        """
        🧠 Calcula features numéricas para IA
        """
        if snapshot is None:
            snapshot = self.get_latest_snapshot()
        
        if snapshot is None:
            return None
        
        price_history = self.get_price_history(window_size)
        if len(price_history) < 5:
            return None
        
        # Features de retorno
        if feature_name == 'return_1':
            return round((price_history[-1] - price_history[-2]) / price_history[-2], 6)
        
        elif feature_name == 'return_5':
            return round((price_history[-1] - price_history[-5]) / price_history[-5], 6)
        
        elif feature_name == 'volatility_5':
            returns = np.diff(price_history[-6:]) / price_history[-6:-1]
            return round(np.std(returns), 6)
        
        elif feature_name == 'volatility_20':
            returns = np.diff(price_history[-21:]) / price_history[-21:-1]
            return round(np.std(returns), 6)
        
        # Features de EMA
        elif feature_name == 'ema_ratio_9_21':
            ema_9 = snapshot['indicators'].get('ema_9', 0)
            ema_21 = snapshot['indicators'].get('ema_21', 0)
            return round(ema_9 / ema_21, 6) if ema_21 > 0 else 0
        
        elif feature_name == 'ema_ratio_21_50':
            ema_21 = snapshot['indicators'].get('ema_21', 0)
            ema_50 = snapshot['indicators'].get('ema_50', 0)
            return round(ema_21 / ema_50, 6) if ema_50 > 0 else 0
        
        # Features de RSI
        elif feature_name == 'rsi_14':
            return snapshot['indicators'].get('rsi_14', 50)
        
        # Features de ATR normalizado
        elif feature_name == 'atr_normalized':
            atr = snapshot['volatility'].get('atr_14', 0)
            close = snapshot['price'].get('close', 1)
            return round(atr / close, 6) if close > 0 else 0
        
        # Features de volumen
        elif feature_name == 'volume_zscore':
            volumes = [s['volume'].get('tick_volume', 100) for s in self.get_snapshots_window(50)]
            if len(volumes) > 1:
                mean_vol = np.mean(volumes)
                std_vol = np.std(volumes)
                current_vol = snapshot['volume'].get('tick_volume', 100)
                return round((current_vol - mean_vol) / std_vol if std_vol > 0 else 0, 6)
            return 0
        
        # Features de spread
        elif feature_name == 'spread_normalized':
            spread = snapshot['price'].get('spread', 0)
            close = snapshot['price'].get('close', 1)
            return round(spread / close, 6) if close > 0 else 0
        
        # Features de vela (candle patterns)
        elif feature_name == 'candle_body_ratio':
            high = snapshot['price']['high']
            low = snapshot['price']['low']
            body = snapshot['volatility']['body']
            range_px = high - low
            return round(body / range_px, 6) if range_px > 0 else 0
        
        elif feature_name == 'upper_wick_ratio':
            high = snapshot['price']['high']
            low = snapshot['price']['low']
            upper = snapshot['volatility']['upper_wick']
            range_px = high - low
            return round(upper / range_px, 6) if range_px > 0 else 0
        
        elif feature_name == 'lower_wick_ratio':
            high = snapshot['price']['high']
            low = snapshot['price']['low']
            lower = snapshot['volatility']['lower_wick']
            range_px = high - low
            return round(lower / range_px, 6) if range_px > 0 else 0
        
        # Features de microestructura
        elif feature_name == 'order_imbalance':
            return snapshot['microstructure'].get('orderbook_imbalance', 0.5)
        
        return None
    
    def calculate_all_features(self, snapshot=None):
        """
        🧠 Calcula TODAS las features para IA
        Output ideal para XGBoost, LSTM, etc.
        """
        if snapshot is None:
            snapshot = self.get_latest_snapshot()
        
        if snapshot is None:
            return None
        
        features = {
            'return_1': self.calculate_feature('return_1', snapshot),
            'return_5': self.calculate_feature('return_5', snapshot),
            'volatility_5': self.calculate_feature('volatility_5', snapshot),
            'volatility_20': self.calculate_feature('volatility_20', snapshot),
            'ema_ratio_9_21': self.calculate_feature('ema_ratio_9_21', snapshot),
            'ema_ratio_21_50': self.calculate_feature('ema_ratio_21_50', snapshot),
            'rsi_14': self.calculate_feature('rsi_14', snapshot),
            'atr_normalized': self.calculate_feature('atr_normalized', snapshot),
            'volume_zscore': self.calculate_feature('volume_zscore', snapshot),
            'spread_normalized': self.calculate_feature('spread_normalized', snapshot),
            'candle_body_ratio': self.calculate_feature('candle_body_ratio', snapshot),
            'upper_wick_ratio': self.calculate_feature('upper_wick_ratio', snapshot),
            'lower_wick_ratio': self.calculate_feature('lower_wick_ratio', snapshot),
            'order_imbalance': self.calculate_feature('order_imbalance', snapshot),
        }
        
        return features
    
    def get_dataframe(self, limit=None):
        """
        🧠 Exporta dataset como pandas DataFrame
        Ideal para análisis y ML training
        """
        if limit is None:
            limit = len(self.snapshots)
        
        snaps = list(self.snapshots)[-limit:]
        data = []
        
        for snap in snaps:
            features = self.calculate_all_features(snap)
            row = {
                'timestamp': snap['timestamp'],
                'timestamp_unix': snap['timestamp_unix'],
                'price_open': snap['price']['open'],
                'price_high': snap['price']['high'],
                'price_low': snap['price']['low'],
                'price_close': snap['price']['close'],
                'bid': snap['price']['bid'],
                'ask': snap['price']['ask'],
                'spread': snap['price']['spread'],
                'tick_volume': snap['volume']['tick_volume'],
                'buy_volume': snap['volume']['buy_volume'],
                'sell_volume': snap['volume']['sell_volume'],
                'session': snap['context']['session'],
                'trend_m5': snap['context']['trend_m5'],
                'trend_m15': snap['context']['trend_m15'],
            }
            
            if features:
                row.update(features)
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def save_dataset(self, output_path=None):
        """Guarda el dataset actualizado"""
        if output_path is None:
            output_path = self.dataset_path
        
        data = {
            "generated_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "total_snapshots": len(self.snapshots),
            "symbol": self.symbol,  # 🟢 Guarda símbolo correcto
            "timeframe": "M1",
            "snapshots": list(self.snapshots)
        }
        
        file_path = Path(output_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.log(f"✅ Dataset guardado: {output_path} ({self.symbol})")
    
    def get_summary_stats(self):
        """Obtiene estadísticas del dataset"""
        if not self.snapshots:
            return None
        
        prices = [s['price']['close'] for s in self.snapshots]
        volumes = [s['volume']['tick_volume'] for s in self.snapshots]
        rsis = [s['indicators']['rsi_14'] for s in self.snapshots]
        
        return {
            'total_snapshots': len(self.snapshots),
            'time_range': f"{self.snapshots[0]['timestamp']} to {self.snapshots[-1]['timestamp']}",
            'price_stats': {
                'min': min(prices),
                'max': max(prices),
                'mean': np.mean(prices),
                'std': np.std(prices),
            },
            'volume_stats': {
                'min': min(volumes),
                'max': max(volumes),
                'mean': np.mean(volumes),
            },
            'rsi_stats': {
                'min': min(rsis),
                'max': max(rsis),
                'mean': np.mean(rsis),
            }
        }


if __name__ == "__main__":
    # 🚀 Test: python professional_dataset_manager.py
    manager = ProfessionalDatasetManager()
    
    print(f"\n📊 Dataset Stats:")
    stats = manager.get_summary_stats()
    if stats:
        print(json.dumps(stats, indent=2))
    
    print(f"\n🧠 Latest Features:")
    features = manager.calculate_all_features()
    if features:
        print(json.dumps(features, indent=2))
