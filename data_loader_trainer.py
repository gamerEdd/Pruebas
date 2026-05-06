"""
DATA LOADER & TRAINING ENGINE
Integración completa de datos para entrenar y usar en botiaver1

Funciona así:
1. Carga market_snapshots.json si existe
2. Si no existe, genera datos usando MarketSnapshotGenerator
3. Entrena los especialistas con los datos
4. Proporciona datos frescos para análisis en vivo
"""

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from market_snapshot_generator import MarketSnapshotGenerator

logger = logging.getLogger(__name__)


class DataLoaderTrainer:
    """Carga datos históricos, entrena especialistas y proporciona datos frescos"""
    
    def __init__(self, symbol="XAUUSD", snapshots_file="logs/market_snapshots.json"):
        self.symbol = symbol
        self.snapshots_file = Path(snapshots_file)
        self.market_snapshots = []
        self.training_data = []
        self.is_ready = False
        logger.info("[DATALOADER] Inicializando Data Loader & Trainer...")
        
    def load_or_generate_snapshots(self, num_snapshots=1000):
        """
        Carga snapshots de archivo o genera nuevos
        
        Returns:
            list: Lista de snapshots M1
        """
        try:
            # Intentar cargar archivo existente
            if self.snapshots_file.exists():
                logger.info(f"[DATALOADER] Cargando snapshots desde {self.snapshots_file}...")
                with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Manejar tanto dict (con 'snapshots' key) como lista directa
                if isinstance(data, dict) and 'snapshots' in data:
                    self.market_snapshots = data['snapshots']
                elif isinstance(data, list):
                    self.market_snapshots = data
                else:
                    logger.warning(f"[DATALOADER] Estructura inesperada, regenerando...")
                    self.market_snapshots = []
                    raise ValueError("Invalid snapshot structure")
                
                logger.info(f"[DATALOADER] [OK] Cargados {len(self.market_snapshots)} snapshots")
                self.is_ready = True
                return self.market_snapshots
        except Exception as e:
            logger.warning(f"[DATALOADER] No se pudo cargar archivo: {e}")
        
        # Generar nuevos snapshots
        logger.info(f"[DATALOADER] Generando {num_snapshots} snapshots nuevos...")
        try:
            generator = MarketSnapshotGenerator(base_price=5377.50, symbol=self.symbol)
            
            snapshots = []
            current_time = datetime.utcnow() - timedelta(minutes=num_snapshots)
            
            for i in range(num_snapshots):
                try:
                    snapshot = generator.generate_professional_snapshot(
                        timestamp=current_time,
                        close_price=None
                    )
                    snapshots.append(snapshot)
                    current_time += timedelta(minutes=1)
                except Exception as e:
                    logger.warning(f"[DATALOADER] Error generando snapshot {i}: {e}")
                    continue
            
            # Guardar snapshots
            self.snapshots_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.snapshots_file, 'w', encoding='utf-8') as f:
                json.dump(snapshots, f, indent=2, ensure_ascii=False)
            
            self.market_snapshots = snapshots
            logger.info(f"[DATALOADER] [OK] {len(snapshots)} snapshots generados y guardados")
            self.is_ready = True
            return snapshots
            
        except Exception as e:
            logger.error(f"[DATALOADER] Error generando snapshots: {e}")
            self.is_ready = False
            return []
    
    def get_training_features(self, window_size=100):
        """
        Prepara features para entrenar especialistas
        
        Args:
            window_size: Tamaño de ventana para indicadores (default 100)
        
        Returns:
            dict: Features agregadas para entrenar
        """
        if not self.market_snapshots or len(self.market_snapshots) < window_size:
            logger.warning("[DATALOADER] Datos insuficientes para extraer features")
            return {}
        
        logger.info(f"[DATALOADER] Extrayendo features de {len(self.market_snapshots)} snapshots...")
        
        try:
            # Extraer precios - manejar estructura flexible
            closes = []
            highs = []
            lows = []
            
            for snap in self.market_snapshots:
                # Proteger contra diferentes estructuras de snapshot
                if isinstance(snap, dict):
                    if 'price' in snap and isinstance(snap['price'], dict):
                        closes.append(snap['price'].get('close', 0))
                        highs.append(snap['price'].get('high', 0))
                        lows.append(snap['price'].get('low', 0))
                    elif 'close' in snap:
                        closes.append(snap.get('close', 0))
                        highs.append(snap.get('high', 0))
                        lows.append(snap.get('low', 0))
                    else:
                        closes.append(0)
                        highs.append(0)
                        lows.append(0)
                else:
                    closes.append(0)
                    highs.append(0)
                    lows.append(0)
            
            # Si no hay datos válidos
            if not closes or all(c == 0 for c in closes):
                logger.warning("[DATALOADER] No valid price data found in snapshots")
                return {}
            
            # Calcular indicadores
            ema_9 = self._calculate_ema(closes[-window_size:], 9)
            ema_21 = self._calculate_ema(closes[-window_size:], 21)
            ema_50 = self._calculate_ema(closes[-window_size:], 50)
            rsi_14 = self._calculate_rsi(closes[-window_size:], 14)
            atr_14 = self._calculate_atr(highs[-window_size:], lows[-window_size:], closes[-window_size:], 14)
            
            # Extraer volumen agregado - manejar estructura flexible
            volumes = []
            buy_volumes = []
            sell_volumes = []
            
            for snap in self.market_snapshots[-window_size:]:
                if isinstance(snap, dict):
                    if 'volume' in snap and isinstance(snap['volume'], dict):
                        volumes.append(snap['volume'].get('tick_volume', 0))
                        buy_volumes.append(snap['volume'].get('buy_volume', 0))
                        sell_volumes.append(snap['volume'].get('sell_volume', 0))
                    else:
                        volumes.append(0)
                        buy_volumes.append(0)
                        sell_volumes.append(0)
                else:
                    volumes.append(0)
                    buy_volumes.append(0)
                    sell_volumes.append(0)
            
            avg_volume = np.mean(volumes) if volumes else 0
            total_buying = sum(buy_volumes)
            total_selling = sum(sell_volumes)
            imbalance = total_buying / max(1, total_buying + total_selling)
            
            # Volatilidad - proteger contra división por cero
            price_diffs = np.diff(closes[-window_size:])
            price_base = np.array(closes[-window_size:-1])
            
            # Proteger contra valores cero o muy pequeños en el denominador
            price_base_safe = np.where(np.abs(price_base) < 1e-10, 1e-10, price_base)
            returns = price_diffs / price_base_safe
            
            # Reemplazar infinitos y NaN con 0
            returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)
            volatility = np.std(returns) if len(returns) > 0 else 0.01
            
            features = {
                'price_current': closes[-1],
                'ema_9': ema_9,
                'ema_21': ema_21,
                'ema_50': ema_50,
                'rsi_14': rsi_14,
                'atr_14': atr_14,
                'avg_volume': avg_volume,
                'buy_sell_imbalance': imbalance,
                'volatility': volatility,
                'trend': 'bullish' if closes[-1] > ema_50 else 'bearish',
                'snapshots_count': len(self.market_snapshots),
                'window_size': window_size
            }
            
            logger.info(f"[DATALOADER] [OK] Features extraídos: {list(features.keys())}")
            return features
            
        except Exception as e:
            logger.error(f"[DATALOADER] Error extrayendo features: {e}")
            return {}
    
    def get_latest_snapshots(self, num_bars=100):
        """
        Obtiene últimos N snapshots para análisis
        
        Args:
            num_bars: Número de barras a retornar
        
        Returns:
            list: Últimos snapshots
        """
        if not self.market_snapshots:
            logger.warning("[DATALOADER] Sin snapshots disponibles")
            return []
        
        return self.market_snapshots[-num_bars:] if len(self.market_snapshots) > num_bars else self.market_snapshots
    
    def get_snapshot_by_index(self, index=-1):
        """
        Obtiene un snapshot específico
        
        Args:
            index: Índice (-1 = último, -2 = penúltimo, etc)
        
        Returns:
            dict: Snapshot
        """
        if not self.market_snapshots:
            return None
        
        try:
            return self.market_snapshots[index]
        except IndexError:
            return None
    
    def _calculate_ema(self, prices, period):
        """Calcula EMA"""
        if len(prices) < 2:
            return prices[-1] if prices else 0
        
        k = 2.0 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * k + ema * (1 - k)
        return round(ema, 2)
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.mean([d for d in deltas if d > 0]) if any(d > 0 for d in deltas) else 0
        losses = -np.mean([d for d in deltas if d < 0]) if any(d < 0 for d in deltas) else 0
        
        if losses == 0:
            return 100.0 if gains > 0 else 50.0
        
        rs = gains / losses
        return round(100 - (100 / (1 + rs)), 2)
    
    def _calculate_atr(self, highs, lows, closes, period=14):
        """Calcula ATR"""
        if len(closes) < 2:
            return highs[0] - lows[0] if highs and lows else 1.0
        
        tr_values = []
        for i in range(1, min(len(closes), period + 1)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
        
        return round(np.mean(tr_values) if tr_values else 1.0, 2)
    
    def get_status(self):
        """Retorna estado de disponibilidad de datos"""
        return {
            'ready': self.is_ready,
            'snapshots_loaded': len(self.market_snapshots),
            'data_file': str(self.snapshots_file),
            'file_exists': self.snapshots_file.exists()
        }
    
    def get_data_status(self):
        """Retorna estado de datos con edad de datos en segundos"""
        status = self.get_status()
        
        # Calcular edad de datos basado en último snapshot
        data_age_seconds = 999
        if self.market_snapshots and len(self.market_snapshots) > 0:
            last_snap = self.market_snapshots[-1]
            if isinstance(last_snap, dict) and 'timestamp' in last_snap:
                try:
                    # Parsear timestamp
                    snap_time_str = last_snap.get('timestamp', '')
                    if snap_time_str:
                        snap_time = datetime.fromisoformat(snap_time_str.replace('Z', '+00:00'))
                        now = datetime.utcnow()
                        if snap_time.tzinfo:
                            now = datetime.now(snap_time.tzinfo)
                        age = (now - snap_time).total_seconds()
                        data_age_seconds = max(0, int(age))
                except:
                    pass
        
        status['data_age_seconds'] = data_age_seconds
        return status


# ======================== FUNCIÓN DE BOOTSTRAP ========================

def initialize_data_loader(symbol="XAUUSD", generate_if_missing=True, num_snapshots=1000):
    """
    Función auxiliar para inicializar DataLoaderTrainer
    
    Args:
        symbol: Símbolo a usar
        generate_if_missing: Generar datos si no existen
        num_snapshots: Número de snapshots a generar
    
    Returns:
        DataLoaderTrainer: Instancia lista para usar
    """
    loader = DataLoaderTrainer(symbol=symbol)
    
    if generate_if_missing:
        loader.load_or_generate_snapshots(num_snapshots=num_snapshots)
    else:
        loader.load_or_generate_snapshots(num_snapshots=0)
    
    status = loader.get_status()
    logger.info(f"[BOOTSTRAP] DataLoader status: {status}")
    
    return loader


if __name__ == "__main__":
    # Ejemplo de uso
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "="*70)
    print("DATA LOADER & TRAINING ENGINE - DEMO")
    print("="*70 + "\n")
    
    # Inicializar
    loader = initialize_data_loader(symbol="XAUUSD", generate_if_missing=True, num_snapshots=1000)
    
    # Mostrar status
    status = loader.get_status()
    print(f"Status: {status}\n")
    
    # Extraer features
    features = loader.get_training_features(window_size=100)
    print(f"Training Features: {features}\n")
    
    # Obtener últimos snapshots
    latest = loader.get_latest_snapshots(num_bars=5)
    print(f"Últimos 5 snapshots (mostrando close):")
    for i, snap in enumerate(latest):
        print(f"  Bar {i+1}: Close = {snap.get('price', {}).get('close', 'N/A')}")
    
    print("\n" + "="*70)
    print("Demo completado exitosamente")
    print("="*70 + "\n")
