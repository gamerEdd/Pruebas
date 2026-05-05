"""
🚀 ML TRAINING ENGINE - NIVEL INSTITUCIONAL
Entrena modelos profesionales con Logistic Regression + XGBoost
Valida con Walk-Forward Optimization
"""

import numpy as np
import pandas as pd
import json
import warnings
from datetime import datetime
from pathlib import Path

# ML Libraries
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import xgboost as xgb
import pickle

warnings.filterwarnings('ignore')


class MLTrainingEngine:
    """🧠 Motor de entrenamiento ML institucional"""
    
    def __init__(self, dataset_path='logs/market_snapshots.json', log_callback=None):
        self.dataset_path = dataset_path
        self.log = log_callback or print
        self.snapshots = []
        self.scaler = StandardScaler()
        self.models = {
            'logistic_buy': None,
            'logistic_sell': None,
            'xgboost_buy': None,
            'xgboost_sell': None,
        }
        self.metrics = {}
        
    def load_dataset(self):
        """Carga 1000 snapshots desde JSON"""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
                self.snapshots = data.get('snapshots', [])
            
            if len(self.snapshots) < 100:
                self.log(f"⚠️ Dataset insuficiente: {len(self.snapshots)} snapshots", 'warning')
                return False
            
            self.log(f"✅ Dataset cargado: {len(self.snapshots)} snapshots profesionales", 'success')
            return True
        except Exception as e:
            self.log(f"❌ Error cargando dataset: {str(e)}", 'error')
            return False
    
    def _extract_features_targets(self):
        """🧬 Extrae features y targets del dataset"""
        X = []
        y_buy = []
        y_sell = []
        
        for i in range(len(self.snapshots) - 5):
            snap = self.snapshots[i]
            snap_future = self.snapshots[i + 5]
            
            try:
                features = [
                    snap['indicators']['rsi_14'],
                    snap['indicators']['macd'],
                    snap['indicators']['macd_signal'],
                    snap['indicators']['bollinger_width'],
                    snap['volatility']['atr_14'],
                    snap['volatility']['range'],
                    snap['price']['close'],
                    snap['volume']['buy_volume'] / max(1, snap['volume']['sell_volume']),
                    snap['microstructure']['orderbook_imbalance'],
                    snap['volume']['tick_volume'],
                ]
            except KeyError:
                continue
            
            retorno = (snap_future['price']['close'] - snap['price']['close']) / snap['price']['close']
            y_buy.append(1 if retorno > 0.0005 else 0)
            y_sell.append(1 if retorno < -0.0005 else 0)
            X.append(features)
        
        X = np.array(X)
        y_buy = np.array(y_buy)
        y_sell = np.array(y_sell)
        X = self.scaler.fit_transform(X)
        
        self.log(f"✅ Features extraídas: {X.shape[0]} muestras × {X.shape[1]} features", 'success')
        self.log(f"   BUY signals: {np.sum(y_buy)} ({100*np.mean(y_buy):.1f}%)", 'info')
        self.log(f"   SELL signals: {np.sum(y_sell)} ({100*np.mean(y_sell):.1f}%)", 'info')
        
        return X, y_buy, y_sell
    
    def _walk_forward_validation(self, X, y, window_size=200, step_size=50):
        """🔄 Walk-Forward Validation"""
        initial_train = window_size
        scores = []
        
        for i in range(initial_train, len(X) - step_size, step_size):
            X_train = X[:i]
            y_train = y[:i]
            X_test = X[i:i+step_size]
            y_test = y[i:i+step_size]
            
            model = LogisticRegression(max_iter=1000, random_state=42)
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            scores.append(score)
        
        avg_score = np.mean(scores) if scores else 0
        self.log(f"🔄 Walk-Forward: {avg_score:.4f} ∓ {np.std(scores) if scores else 0:.4f}", 'success')
        return avg_score, scores
    
    def train_logistic_regression(self, X, y_buy, y_sell):
        """📈 Regresión Logística"""
        self.log("\n═══ LOGISTIC REGRESSION ═══", 'info')
        
        X_train, X_test, y_buy_train, y_buy_test = train_test_split(X, y_buy, test_size=0.2, random_state=42)
        _, _, y_sell_train, y_sell_test = train_test_split(X, y_sell, test_size=0.2, random_state=42)
        
        self.models['logistic_buy'] = LogisticRegression(max_iter=1000, random_state=42, C=0.1)
        self.models['logistic_buy'].fit(X_train, y_buy_train)
        score_buy = self.models['logistic_buy'].score(X_test, y_buy_test)
        self.log(f"   ✅ BUY: {score_buy:.4f}", 'success')
        
        self.models['logistic_sell'] = LogisticRegression(max_iter=1000, random_state=42, C=0.1)
        self.models['logistic_sell'].fit(X_train, y_sell_train)
        score_sell = self.models['logistic_sell'].score(X_test, y_sell_test)
        self.log(f"   ✅ SELL: {score_sell:.4f}", 'success')
        
        return score_buy, score_sell
    
    def train_xgboost(self, X, y_buy, y_sell):
        """🚀 XGBoost - SOTA"""
        self.log("\n═══ XGBOOST ═══", 'info')
        
        X_train, X_test, y_buy_train, y_buy_test = train_test_split(X, y_buy, test_size=0.2, random_state=42)
        _, _, y_sell_train, y_sell_test = train_test_split(X, y_sell, test_size=0.2, random_state=42)
        
        params = {
            'max_depth': 4,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
        }
        
        self.models['xgboost_buy'] = xgb.XGBClassifier(**params)
        self.models['xgboost_buy'].fit(X_train, y_buy_train)
        score_buy = self.models['xgboost_buy'].score(X_test, y_buy_test)
        self.log(f"   ✅ BUY: {score_buy:.4f}  ← SOTA", 'success')
        
        self.models['xgboost_sell'] = xgb.XGBClassifier(**params)
        self.models['xgboost_sell'].fit(X_train, y_sell_train)
        score_sell = self.models['xgboost_sell'].score(X_test, y_sell_test)
        self.log(f"   ✅ SELL: {score_sell:.4f}  ← SOTA", 'success')
        
        return score_buy, score_sell
    
    def train_all_models(self):
        """🔥 Entrena TODOS los modelos"""
        if not self.load_dataset():
            return False
        
        X, y_buy, y_sell = self._extract_features_targets()
        
        self.log("\n═══ VALIDACIÓN - WALK-FORWARD ═══\n", 'info')
        wf_buy, _ = self._walk_forward_validation(X, y_buy)
        wf_sell, _ = self._walk_forward_validation(X, y_sell)
        self.metrics['walk_forward_buy'] = wf_buy
        self.metrics['walk_forward_sell'] = wf_sell
        
        self.log("\n════════════════════════════════════════", 'info')
        
        lr_buy, lr_sell = self.train_logistic_regression(X, y_buy, y_sell)
        self.metrics['logistic_buy'] = lr_buy
        self.metrics['logistic_sell'] = lr_sell
        
        xgb_buy, xgb_sell = self.train_xgboost(X, y_buy, y_sell)
        self.metrics['xgboost_buy'] = xgb_buy
        self.metrics['xgboost_sell'] = xgb_sell
        
        self._print_summary()
        self.save_models()
        
        return True
    
    def _print_summary(self):
        """📊 Resumen de métricas"""
        self.log("\n" + "="*60, 'info')
        self.log("🏆 RESUMEN - MODELOS ENTRENADOS", 'success')
        self.log("="*60, 'info')
        
        self.log("\n📈 BUY MODELS:", 'info')
        self.log(f"   Logistic: {self.metrics.get('logistic_buy', 0):.4f}", 'info')
        self.log(f"   XGBoost: {self.metrics.get('xgboost_buy', 0):.4f}  ← USAR", 'success')
        self.log(f"   W-F Val: {self.metrics.get('walk_forward_buy', 0):.4f}", 'info')
        
        self.log("\n📉 SELL MODELS:", 'info')
        self.log(f"   Logistic: {self.metrics.get('logistic_sell', 0):.4f}", 'info')
        self.log(f"   XGBoost: {self.metrics.get('xgboost_sell', 0):.4f}  ← USAR", 'success')
        self.log(f"   W-F Val: {self.metrics.get('walk_forward_sell', 0):.4f}", 'info')
        
        self.log("="*60 + "\n", 'info')
    
    def save_models(self):
        """💾 Guardar modelos"""
        try:
            model_dir = Path('logs/trained_models')
            model_dir.mkdir(parents=True, exist_ok=True)
            
            for name, model in self.models.items():
                if model is not None:
                    with open(f'{model_dir}/{name}_model.pkl', 'wb') as f:
                        pickle.dump(model, f)
            
            with open(f'{model_dir}/scaler.pkl', 'wb') as f:
                pickle.dump(self.scaler, f)
            
            with open(f'{model_dir}/metrics.json', 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            self.log(f"✅ Modelos: logs/trained_models/", 'success')
            return True
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", 'error')
            return False


if __name__ == "__main__":
    print("\n🚀 ML TRAINING ENGINE - NIVEL INSTITUCIONAL\n")
    engine = MLTrainingEngine()
    engine.train_all_models()
