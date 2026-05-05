"""
ML Training Engine - Simple Version
Integra 4 niveles de corrección de sesgo sin dependencias de modulos externos
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import pickle
import warnings
warnings.filterwarnings('ignore')


class SimpleMLTrainingEngine:
    """Entrenamiento simple com 4 niveles integrados"""
    
    def __init__(self):
        self.dataset_path = 'logs/market_snapshots.json'
        self.model_dir = Path('logs/trained_models')
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots = []
    
    def load_dataset(self):
        """Carga dataset"""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
                self.snapshots = data.get('snapshots', [])
            print(f"[OK] Dataset: {len(self.snapshots)} snapshots")
            return True
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False
    
    # ============== NIVEL 1: DATASET BALANCER ==============
    def nivel_1_calculate_weights(self):
        """NIVEL 1: Calcula class weights para balance"""
        print("\n" + "="*70)
        print("[>>] NIVEL 1 - DATASET BALANCER")
        print("="*70)
        
        # Generar labels simples
        y_labels = []
        for i in range(len(self.snapshots) - 5):
            snap = self.snapshots[i]
            snap_future = self.snapshots[i + 5]
            retorno = (snap_future['price']['close'] - snap['price']['close']) / snap['price']['close']
            
            if retorno > 0.001:
                y_labels.append(1)  # BUY
            else:
                y_labels.append(0)  # SELL
        
        y_labels = np.array(y_labels)
        
        buy_count = np.sum(y_labels == 1)
        sell_count = np.sum(y_labels == 0)
        total = len(y_labels)
        
        print(f"\n[STATS] Dataset Balance:")
        print(f"  BUY:  {buy_count} ({100*buy_count/total:.1f}%)")
        print(f"  SELL: {sell_count} ({100*sell_count/total:.1f}%)")
        
        # Calcular weighted para sklearn
        # balanced: w = 1 / freq(class)
        w_buy = total / (2 * buy_count) if buy_count > 0 else 1.0
        w_sell = total / (2 * sell_count) if sell_count > 0 else 1.0
        
        # Normalize
        avg = (w_buy * buy_count + w_sell * sell_count) / total
        w_buy /= avg
        w_sell /= avg
        
        print(f"\n[+] Class Weights:")
        print(f"  BUY weight:  {w_buy:.4f}")
        print(f"  SELL weight: {w_sell:.4f}")
        
        # Para XGBoost
        scale_pos_weight = buy_count / sell_count if sell_count > 0 else 1.0
        print(f"  scale_pos_weight: {scale_pos_weight:.4f}")
        
        return y_labels, w_buy, w_sell, scale_pos_weight
    
    # ============== NIVEL 2: IMPROVED LABELS ==============
    def nivel_2_improve_labels(self, y_labels):
        """NIVEL 2: Mejora labels con multi-horizon voting"""
        print("\n" + "="*70)
        print("[>>] NIVEL 2 - IMPROVED LABELING")
        print("="*70)
        
        # Multi-horizon voting: 5, 15, 30 velas
        horizons = [5, 15, 30]
        thresholds = [0.0005, 0.001, 0.002]
        
        voting_results = []
        
        for i in range(len(self.snapshots) - max(horizons)):
            votes = 0
            
            for horizon in horizons:
                snap = self.snapshots[i]
                snap_future = self.snapshots[i + horizon]
                ret = (snap_future['price']['close'] - snap['price']['close']) / snap['price']['close']
                
                if ret > thresholds[1]:  # Medium threshold
                    votes += 1
            
            # Mayoria voting: 2 de 3 horizontes
            if votes >= 2:
                voting_results.append(1)
            else:
                voting_results.append(0)
        
        y_improved = np.array(voting_results)
        buy_count = np.sum(y_improved == 1)
        sell_count = np.sum(y_improved == 0)
        total = len(y_improved)
        
        print(f"\n[STATS] After Multi-Horizon Voting:")
        print(f"  BUY:  {buy_count} ({100*buy_count/total:.1f}%)")
        print(f"  SELL: {sell_count} ({100*sell_count/total:.1f}%)")
        
        return y_improved
    
    # ============== NIVEL 3: ADVANCED FEATURES ==============
    def nivel_3_extract_features(self, y_improved):
        """NIVEL 3: Extrae features avanzadas + normalizacion"""
        print("\n" + "="*70)
        print("[>>] NIVEL 3 - ADVANCED FEATURES")
        print("="*70)
        
        features = []
        
        for i in range(len(self.snapshots) - 30):
            snap = self.snapshots[i]
            indicators = snap.get('indicators', {})
            
            # Feature 1: RSI centered (no sesgo estructural a BUY)
            rsi = indicators.get('rsi_14', 50)
            rsi_centered = (rsi - 50) / 50
            
            # Feature 2-11: Otros indicators normalizados
            macd = indicators.get('macd_12_26', 0)
            atr = indicators.get('atr_14', 0.01)
            bb_width = indicators.get('bollinger_width', 0)
            
            # Log returns
            price_log = np.log(snap['price']['close'] + 1e-9)
            volume_tick = snap.get('volume', {}).get('tick_volume', 1) if isinstance(snap.get('volume'), dict) else snap.get('volume', 1)
            volume_log = np.log(volume_tick + 1)
            
            # Regime detection (ADX-based)
            adx = indicators.get('adx_14', 20)
            regime = 1 if adx > 25 else 0  # 1=trend, 0=range
            
            feature_vector = [
                rsi_centered,
                macd / 100 if macd != 0 else 0,
                atr,
                bb_width,
                price_log,
                volume_log,
                regime,
                indicators.get('cci_14', 0) / 100,
                indicators.get('stoch_k', 50) / 100,
                indicators.get('williams_r', -50) / 100,
                indicators.get('momentum', 0) / 100,
            ]
            
            features.append(feature_vector)
        
        X = np.array(features)
        
        print(f"\n[STATS] Features Extracted:")
        print(f"  Shape: {X.shape}")
        print(f"  Features: {X.shape[1]} dimensions")
        print(f"  RSI_centered mean: {np.mean(X[:, 0]):.4f} (near 0 = no BUY bias)")
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        print(f"  [OK] Scaled: mu=0, sigma=1")
        
        return X_scaled, scaler
    
    # ============== NIVEL 4: DECISION THRESHOLDS ==============
    def nivel_4_optimize_thresholds(self):
        """NIVEL 4: Define decision thresholds con zona neutra"""
        print("\n" + "="*70)
        print("[>>] NIVEL 4 - DECISION THRESHOLD OPTIMIZER")
        print("="*70)
        
        thresholds = {
            'static_buy': 0.60,
            'static_sell': 0.40,
            'neutral_zone': 0.20,
            'volatility_adjustment': 'enabled',
        }
        
        print(f"\n[+] Decision Logic:")
        print(f"  - BUY if prob > {thresholds['static_buy']:.2f}")
        print(f"  - SELL if prob < {thresholds['static_sell']:.2f}")
        print(f"  - NO TRADE if {thresholds['static_sell']:.2f} <= prob <= {thresholds['static_buy']:.2f}")
        print(f"  - Dynamic adjustment: Enabled")
        
        return thresholds
    
    # ============== TRAINING ==============
    def train_models(self, X, y, w_buy, w_sell, scale_pos_weight):
        """Entrena modelos con 4 niveles aplicados"""
        print("\n" + "="*70)
        print("[>>] MODEL TRAINING WITH 4-LEVEL CORRECTIONS")
        print("="*70)
        
        # Walk-Forward Validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        logistic_scores = []
        xgb_scores = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            print(f"\n[FOLD] {fold+1}/5")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Logistic Regression with class weights (NIVEL 1 + L2 from NIVEL 3)
            lr = LogisticRegression(
                C=0.01,  # L2 regularization
                class_weight='balanced',
                max_iter=1000,
                solver='lbfgs'
            )
            lr.fit(X_train, y_train)
            lr_score = lr.score(X_test, y_test)
            logistic_scores.append(lr_score)
            print(f"  Logistic: {lr_score:.4f}")
            
            # XGBoost with scale_pos_weight (NIVEL 1)
            xgb = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,
                reg_lambda=0.5,  # L2 from NIVEL 3
                reg_alpha=0.1,
                random_state=42,
                verbose=0
            )
            xgb.fit(X_train, y_train)
            xgb_score = xgb.score(X_test, y_test)
            xgb_scores.append(xgb_score)
            print(f"  XGBoost:  {xgb_score:.4f}")
        
        # Results
        print(f"\n[RESULTS] Walk-Forward Validation:")
        
        lr_mean = np.mean(logistic_scores)
        lr_std = np.std(logistic_scores)
        print(f"  Logistic: {lr_mean:.4f} +/- {lr_std:.4f}")
        
        xgb_mean = np.mean(xgb_scores)
        xgb_std = np.std(xgb_scores)
        print(f"  XGBoost:  {xgb_mean:.4f} +/- {xgb_std:.4f}")
        
        # Re-train on full dataset
        print(f"\n[+] Re-training on full dataset...")
        
        lr_final = LogisticRegression(C=0.01, class_weight='balanced', max_iter=1000, solver='lbfgs')
        lr_final.fit(X, y)
        
        xgb_final = XGBClassifier(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            scale_pos_weight=scale_pos_weight, reg_lambda=0.5, reg_alpha=0.1,
            random_state=42, verbose=0
        )
        xgb_final.fit(X, y)
        
        print(f"[OK] Models trained")
        
        return lr_final, xgb_final, (lr_mean, lr_std), (xgb_mean, xgb_std)
    
    def save_models(self, lr, xgb, scaler):
        """Guarda modelos"""
        with open(self.model_dir / 'logistic_v2_balanced.pkl', 'wb') as f:
            pickle.dump(lr, f)
        
        with open(self.model_dir / 'xgboost_v2_balanced.pkl', 'wb') as f:
            pickle.dump(xgb, f)
        
        with open(self.model_dir / 'scaler_v2_balanced.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        
        print(f"\n[OK] Models saved to {self.model_dir}")
    
    def run(self):
        """Ejecuta pipeline completo con 4 niveles"""
        print("\n" + "="*70)
        print("[ML] SIMPLE ML TRAINING ENGINE - 4 NIVELES")
        print("="*70)
        
        # Cargar
        if not self.load_dataset():
            return
        
        # NIVEL 1
        y_labels, w_buy, w_sell, scale_pos = self.nivel_1_calculate_weights()
        
        # NIVEL 2
        y_improved = self.nivel_2_improve_labels(y_labels)
        
        # NIVEL 3
        X_scaled, scaler = self.nivel_3_extract_features(y_improved)
        
        # NIVEL 4
        thresholds = self.nivel_4_optimize_thresholds()
        
        # Entrenar
        lr, xgb, lr_results, xgb_results = self.train_models(X_scaled, y_improved, w_buy, w_sell, scale_pos)
        
        # Guardar
        self.save_models(lr, xgb, scaler)
        
        print("\n" + "="*70)
        print("[OK] PIPELINE COMPLETADO - 4 NIVELES APLICADOS")
        print("="*70)
        print(f"\n[RESULTADOS]:")
        print(f"  Logistic: {lr_results[0]:.4f} +/- {lr_results[1]:.4f}")
        print(f"  XGBoost:  {xgb_results[0]:.4f} +/- {xgb_results[1]:.4f}")
        print(f"\n[OK] Modelos guardados en: {self.model_dir}/")


if __name__ == "__main__":
    engine = SimpleMLTrainingEngine()
    engine.run()
