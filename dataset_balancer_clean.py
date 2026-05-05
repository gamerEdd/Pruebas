"""
NIVEL 1 - DATASET BALANCER
Corrige el desbalance de clases usando Class Weights
Formula: Loss = -w_b * y*log(p) - w_s * (1-y)*log(1-p)
"""

import numpy as np
import json
from collections import Counter
from pathlib import Path


class DatasetBalancer:
    """Balancea clases automaticamente"""
    
    def __init__(self, dataset_path='logs/market_snapshots.json', log_callback=None):
        self.dataset_path = dataset_path
        self.log = log_callback or print
        self.snapshots = []
        self.class_weights = {'buy': 1.0, 'sell': 1.0}
        self.strategy = None
        
    def load_dataset(self):
        """Carga dataset"""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
                self.snapshots = data.get('snapshots', [])
            self.log(f"[OK] Dataset cargado: {len(self.snapshots)}", 'success')
            return True
        except Exception as e:
            self.log(f"[ERROR] Error: {str(e)}", 'error')
            return False
    
    def _generate_labels(self, threshold=0.0005):
        """Genera labels con threshold minimo"""
        y_buy = []
        y_sell = []
        
        for i in range(len(self.snapshots) - 5):
            snap = self.snapshots[i]
            snap_future = self.snapshots[i + 5]
            
            retorno = (snap_future['price']['close'] - snap['price']['close']) / snap['price']['close']
            
            # NIVEL 2: Threshold minimo para eliminar ruido
            if retorno > threshold:
                y_buy.append(1)
                y_sell.append(0)
            elif retorno < -threshold:
                y_buy.append(0)
                y_sell.append(1)
            else:
                y_buy.append(0)  # Zona neutra = no operar
                y_sell.append(0)
        
        return np.array(y_buy), np.array(y_sell)
    
    def analyze_class_balance(self):
        """Analiza balance de clases"""
        y_buy, y_sell = self._generate_labels()
        
        buy_count = int(np.sum(y_buy))
        sell_count = int(np.sum(y_sell))
        neutral_count = int(len(y_buy) - buy_count - sell_count)
        
        total = len(y_buy)
        
        self.log("\n" + "="*60, 'info')
        self.log("ANALISIS DE BALANCE - DATASET ORIGINAL", 'success')
        self.log("="*60, 'info')
        
        self.log(f"\n[B] BUY:     {buy_count:4d} ({100*buy_count/total:5.1f}%)", 'info')
        self.log(f"[S] SELL:    {sell_count:4d} ({100*sell_count/total:5.1f}%)", 'info')
        self.log(f"[N] NEUTRAL: {neutral_count:4d} ({100*neutral_count/total:5.1f}%)", 'info')
        
        ratio = buy_count / max(1, sell_count)
        self.log(f"\n[BALANCE] BUY/SELL Ratio: {ratio:.2f}x", 'warning' if ratio > 1.5 else 'info')
        
        return buy_count, sell_count, neutral_count
    
    def calculate_class_weights(self, method='balanced'):
        """
        Calcula pesos de clase para compensar desbalances
        
        Metodos:
        - 'balanced': w = 1 / freq(class)
        - 'inverse_sqrt': w = 1 / sqrt(freq(class))
        - 'log': w = 1 + log(total / freq(class))
        """
        y_buy, y_sell = self._generate_labels()
        
        buy_count = int(np.sum(y_buy))
        sell_count = int(np.sum(y_sell))
        total = len(y_buy)
        
        if method == 'balanced':
            # Formula: w = 1 / freq(class)
            w_buy = total / (2 * buy_count) if buy_count > 0 else 1.0
            w_sell = total / (2 * sell_count) if sell_count > 0 else 1.0
        
        elif method == 'inverse_sqrt':
            # Menos agresivo que balanced
            w_buy = 1 / np.sqrt(buy_count) if buy_count > 0 else 1.0
            w_sell = 1 / np.sqrt(sell_count) if sell_count > 0 else 1.0
        
        elif method == 'log':
            # Log dampening
            w_buy = 1 + np.log(total / buy_count) if buy_count > 0 else 1.0
            w_sell = 1 + np.log(total / sell_count) if sell_count > 0 else 1.0
        
        else:
            w_buy = w_sell = 1.0
        
        # Normalizar para que promedien 1.0
        avg_weight = (w_buy * buy_count + w_sell * sell_count) / total
        w_buy /= avg_weight
        w_sell /= avg_weight
        
        self.class_weights['buy'] = w_buy
        self.class_weights['sell'] = w_sell
        self.strategy = method
        
        self.log("\n" + "="*60, 'info')
        self.log(f"CLASS WEIGHTS ({method.upper()})", 'success')
        self.log("="*60, 'info')
        self.log(f"   BUY weight:  {w_buy:.4f}", 'info')
        self.log(f"   SELL weight: {w_sell:.4f}", 'info')
        self.log(f"   Ratio: {w_buy/w_sell:.2f}x", 'warning' if w_buy/w_sell > 1.2 else 'success')
        
        return w_buy, w_sell
    
    def get_sklearn_class_weight(self):
        """Retorna formato para sklearn"""
        return {0: self.class_weights['buy'], 1: self.class_weights['sell']}
    
    def get_xgboost_scale_pos_weight(self):
        """
        XGBoost usa scale_pos_weight= (neg_count / pos_count)
        Si SELL es clase positiva: neg_count=BUY, pos_count=SELL
        """
        y_buy, y_sell = self._generate_labels()
        buy_count = int(np.sum(y_buy))
        sell_count = int(np.sum(y_sell))
        
        if sell_count > 0:
            scale_pos_weight = buy_count / sell_count
        else:
            scale_pos_weight = 1.0
        
        self.log("\n" + "="*60, 'info')
        self.log(f"XGBoost scale_pos_weight: {scale_pos_weight:.4f}", 'success')
        self.log("="*60, 'info')
        
        return scale_pos_weight
    
    def export_metrics(self):
        """Exporta metricas de balance"""
        y_buy, y_sell = self._generate_labels()
        
        buy_count = int(np.sum(y_buy))
        sell_count = int(np.sum(y_sell))
        neutral_count = int(len(y_buy) - buy_count - sell_count)
        total = len(y_buy)
        
        return {
            'buy_count': buy_count,
            'buy_pct': 100 * buy_count / total,
            'sell_count': sell_count,
            'sell_pct': 100 * sell_count / total,
            'neutral_count': neutral_count,
            'neutral_pct': 100 * neutral_count / total,
            'class_weights': self.class_weights,
            'strategy': self.strategy,
        }


if __name__ == "__main__":
    print("\n[ML] NIVEL 1 - DATASET BALANCER\n")
    
    balancer = DatasetBalancer()
    balancer.load_dataset()
    balancer.analyze_class_balance()
    balancer.calculate_class_weights(method='balanced')
    balancer.get_xgboost_scale_pos_weight()
    
    print("\n[OK] Componente NIVEL 1 funcionando correctamente")
