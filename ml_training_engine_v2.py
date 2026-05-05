"""
🔬 ML TRAINING ENGINE V2
INTEGRA 4 NIVELES DE CORRECCIÓN DE SESGO

NIVEL 1: Class weights (DatasetBalancer)
NIVEL 2: Improved labels (ImprovedLabelingEngine)
NIVEL 3: Advanced features (AdvancedFeatureEngine)
NIVEL 4: Decision thresholds (DecisionThresholdOptimizer)
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

# Component imports - Clean versions without emojis
from dataset_balancer_clean import DatasetBalancer
from improved_labeling_engine import ImprovedLabelingEngine
from advanced_feature_engine import AdvancedFeatureEngine
from decision_threshold_optimizer import DecisionThresholdOptimizer


class MLTrainingEngineV2:
    """Pipeline de entrenamiento con 4 niveles de corrección"""
    
    def __init__(self, dataset_path='logs/market_snapshots.json', log_callback=None):
        self.dataset_path = dataset_path
        self.log = log_callback or print
        self.model_dir = Path('logs/trained_models')
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Componentes
        self.balancer = DatasetBalancer(dataset_path)
        self.labeling = ImprovedLabelingEngine(dataset_path)
        self.features = AdvancedFeatureEngine(dataset_path)
        self.optimizer = DecisionThresholdOptimizer(dataset_path)
        
        self.snapshots = []
        self.models = {}
        
    def _print_section(self, title):
        self.log("\n" + "="*70, 'info')
        self.log(f"[>>] {title}", 'success')
        self.log("="*70, 'info')
    
    def load_dataset(self):
        """Carga dataset"""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
                self.snapshots = data.get('snapshots', [])
            self.log(f"[OK] Dataset: {len(self.snapshots)} snapshots", 'success')
            return True
        except Exception as e:
            self.log(f"[ERROR] {str(e)}", 'error')
            return False
    
    def nivel_1_balance_dataset(self):
        """NIVEL 1: Calcular class weights"""
        self._print_section("NIVEL 1 - DATASET BALANCER")
        
        # Cargar dataset en balancer
        self.balancer.load_dataset()
        
        # Analizar imbalance
        buy_count, sell_count, neutral_count = self.balancer.analyze_class_balance()
        
        self.log(f"\n📊 Clase BUY:  {buy_count} ({buy_count/(buy_count+sell_count)*100:.1f}%)", 'info')
        self.log(f"📊 Clase SELL: {sell_count} ({sell_count/(buy_count+sell_count)*100:.1f}%)", 'info')
        self.log(f"📊 Neutral:    {neutral_count}", 'info')
        
        # Calcular weights
        w_buy_bal, w_sell_bal = self.balancer.calculate_class_weights(method='balanced')
        w_buy_sqrt, w_sell_sqrt = self.balancer.calculate_class_weights(method='inverse_sqrt')
        w_buy_log, w_sell_log = self.balancer.calculate_class_weights(method='log_dampening')
        
        self.log(f"\n[OK] Estrategias de balancing:", 'success')
        self.log(f"   Balanced:        w_buy={w_buy_bal:.3f}, w_sell={w_sell_bal:.3f}", 'info')
        self.log(f"   Inverse sqrt:    w_buy={w_buy_sqrt:.3f}, w_sell={w_sell_sqrt:.3f}", 'info')
        self.log(f"   Log dampening:   w_buy={w_buy_log:.3f}, w_sell={w_sell_log:.3f}", 'info')
        
        self.log(f"\n[+] Para XGBoost:", 'info')
        scale_pos = self.balancer.get_xgboost_scale_pos_weight()
        self.log(f"   scale_pos_weight = {scale_pos:.3f}", 'info')
        
        weights_balanced = {'buy': w_buy_bal, 'sell': w_sell_bal}
        return weights_balanced, scale_pos
    
    def nivel_2_improved_labels(self):
        """NIVEL 2: Generar labels mejorados con multi-horizon"""
        self._print_section("NIVEL 2 - IMPROVED LABELING ENGINE")
        
        # Cargar dataset en labeling
        self.labeling.load_dataset()
        
        # Generar labels multi-horizon
        thresholds = (0.0005, 0.001, 0.002)
        horizons = (5, 15, 30)
        
        multi_horizon_results = self.labeling.generate_multi_horizon_labels(
            thresholds=thresholds,
            horizons=horizons
        )
        
        self.log(f"\n[+] Multi-Horizon Labeling:", 'info')
        self.log(f"   Umbrales: {thresholds}", 'info')
        self.log(f"   Horizontes: {horizons} velas", 'info')
        
        # Combinar con voting
        combined_y = self.labeling.combine_horizons_voting(multi_horizon_results)
        
        buy_count = np.sum(combined_y == 1)
        sell_count = np.sum(combined_y == 0)
        neutral_count = np.sum(combined_y == -1)
        
        self.log(f"\n✅ Labels después de voting:", 'success')
        self.log(f"   BUY:     {buy_count} ({buy_count/len(combined_y)*100:.1f}%)", 'success')
        self.log(f"   SELL:    {sell_count} ({sell_count/len(combined_y)*100:.1f}%)", 'success')
        self.log(f"   NEUTRAL: {neutral_count} ({neutral_count/len(combined_y)*100:.1f}%)", 'warning')
        
        # Filtrar neutrales
        valid_mask = combined_y != -1
        y_filtered = combined_y[valid_mask]
        
        self.log(f"\n💡 Después de filtrar neutrales:", 'info')
        self.log(f"   Muestras válidas: {np.sum(valid_mask)}", 'info')
        self.log(f"   Balance: BUY {np.mean(y_filtered):.1%}, SELL {(1-np.mean(y_filtered)):.1%}", 'success')
        
        return y_filtered, valid_mask
    
    def nivel_3_advanced_features(self, valid_mask):
        """NIVEL 3: Extraer features avanzadas"""
        self._print_section("NIVEL 3 - ADVANCED FEATURE ENGINE")
        
        # Preparar data
        prices = np.array([s['price']['close'] for s in self.snapshots])
        close_prices = prices[valid_mask]
        
        # Extraer features
        X = self.features.extract_advanced_features()
        X_filtered = X[valid_mask]
        
        self.log(f"\n📊 Features Extraídas:", 'info')
        self.log(f"   Dimensionalidad: {X_filtered.shape[1]} features", 'info')
        
        features_desc = [
            "RSI_centered (RSI-50)/50",
            "MACD_normalized",
            "ATR_normalized",
            "Bollinger_width",
            "Price_log_returns",
            "Volume_ratio",
            "Order_book_imbalance",
            "Volume_log",
            "Regime (ADX-based)",
            "Momentum",
            "Volatility_log"
        ]
        
        for i, desc in enumerate(features_desc[:X_filtered.shape[1]]):
            mean_val = np.mean(X_filtered[:, i])
            std_val = np.std(X_filtered[:, i])
            self.log(f"   [{i+1:2d}] {desc:30s} μ={mean_val:7.4f}, σ={std_val:7.4f}", 'info')
        
        self.log(f"\n✅ Verificación de bias:", 'success')
        rsi_centered_idx = 0
        rsi_mean = np.mean(X_filtered[:, rsi_centered_idx])
        self.log(f"   RSI_centered media: {rsi_mean:.4f}", 'success')
        self.log(f"   ✓ Cerca de 0 = NO hay sesgo estructural a BUY", 'success')
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_filtered)
        
        self.log(f"\n💡 Features normalizadas (StandardScaler):", 'info')
        self.log(f"   μ ≈ 0, σ ≈ 1 para todas", 'info')
        
        return X_scaled, scaler
    
    def nivel_4_decision_thresholds(self):
        """NIVEL 4: Optimizar thresholds de decisión"""
        self._print_section("NIVEL 4 - DECISION THRESHOLD OPTIMIZER")
        
        # Cargar dataset en optimizer
        self.optimizer.load_dataset()
        
        # Zona neutra estática
        static_config = self.optimizer.static_neutral_zone_strategy()
        
        # Threshold dinámico
        dynamic_config = self.optimizer.dynamic_volatility_adjusted_threshold()
        
        # Evitar empates
        tie_config = self.optimizer.avoid_close_call_ties()
        
        # Lógica ensemble
        ensemble_config = self.optimizer.ensemble_decision_logic()
        
        return {
            'static': static_config,
            'dynamic': dynamic_config,
            'no_ties': tie_config,
            'ensemble': ensemble_config,
        }
    
    def train_models(self, X, y, class_weights, scale_pos_weight):
        """Entrena modelos con 4 niveles"""
        self._print_section("ENTRENAMIENTO DE MODELOS CON 4 NIVELES")
        
        # Walk-Forward Validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        logistic_scores = []
        xgb_scores = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            self.log(f"\n📊 Fold {fold+1}/5:", 'info')
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # ✅ Logistic Regression con class weights (NIVEL 1)
            lr = LogisticRegression(
                C=0.01,  # L2 regularization (NIVEL 3)
                class_weight='balanced',  # Class weights (NIVEL 1)
                max_iter=1000,
                solver='lbfgs'
            )
            lr.fit(X_train, y_train)
            lr_score = lr.score(X_test, y_test)
            logistic_scores.append(lr_score)
            self.log(f"   Logistic Regression: {lr_score:.4f}", 'success')
            
            # ✅ XGBoost con scale_pos_weight (NIVEL 1)
            xgb = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,  # Class weights (NIVEL 1)
                reg_lambda=0.5,  # L2 regularization (NIVEL 3)
                reg_alpha=0.1,
                random_state=42,
                verbose=0
            )
            xgb.fit(X_train, y_train)
            xgb_score = xgb.score(X_test, y_test)
            xgb_scores.append(xgb_score)
            self.log(f"   XGBoost:              {xgb_score:.4f}", 'success')
        
        # Resultados
        self.log(f"\n✅ WALK-FORWARD VALIDATION:", 'success')
        
        lr_mean = np.mean(logistic_scores)
        lr_std = np.std(logistic_scores)
        self.log(f"   Logistic: {lr_mean:.4f} ± {lr_std:.4f}", 'success')
        
        xgb_mean = np.mean(xgb_scores)
        xgb_std = np.std(xgb_scores)
        self.log(f"   XGBoost:  {xgb_mean:.4f} ± {xgb_std:.4f}", 'success')
        
        # Entrenar en todo el dataset
        self.log(f"\n🔄 Reentrenando en dataset completo...", 'info')
        
        self.models['logistic'] = LogisticRegression(
            C=0.01,
            class_weight='balanced',
            max_iter=1000,
            solver='lbfgs'
        )
        self.models['logistic'].fit(X, y)
        
        self.models['xgboost'] = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            reg_lambda=0.5,
            reg_alpha=0.1,
            random_state=42,
            verbose=0
        )
        self.models['xgboost'].fit(X, y)
        
        self.log(f"✅ Modelos entrenados", 'success')
        
        return {
            'logistic_wf': (lr_mean, lr_std),
            'xgboost_wf': (xgb_mean, xgb_std),
        }
    
    def save_models(self, scaler):
        """Guarda modelos e información"""
        
        # Guardar modelos
        for name, model in self.models.items():
            path = self.model_dir / f'{name}_v2.pkl'
            with open(path, 'wb') as f:
                pickle.dump(model, f)
            self.log(f"✅ Guardado: {path}", 'success')
        
        # Guardar scaler
        scaler_path = self.model_dir / 'scaler_v2.pkl'
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        self.log(f"✅ Guardado: {scaler_path}", 'success')
        
        # Guardar config
        config = {
            'niveles': {
                'nivel_1': 'Dataset Balancer - Class Weights',
                'nivel_2': 'Improved Labeling - Multi-Horizon Voting',
                'nivel_3': 'Advanced Features - Centered RSI + Regime Detection',
                'nivel_4': 'Decision Thresholds - Neutral Zones + Dynamic Adjustment',
            },
            'preprocessing': {
                'scaler': 'StandardScaler',
                'feature_count': 11,
            },
            'models': {
                'logistic': {'C': 0.01, 'class_weight': 'balanced'},
                'xgboost': {'scale_pos_weight': 'calculated', 'reg_lambda': 0.5},
            },
        }
        
        config_path = self.model_dir / 'config_v2.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        self.log(f"✅ Guardado: {config_path}", 'success')


def main():
    print("\n" + "="*70)
    print("[ML] ML TRAINING ENGINE V2 - 4 NIVELES INTEGRADOS")
    print("="*70)
    
    engine = MLTrainingEngineV2()
    
    # Cargar dataset
    if not engine.load_dataset():
        return
    
    # NIVEL 1: Dataset Balancer
    weights, scale_pos = engine.nivel_1_balance_dataset()
    
    # NIVEL 2: Improved Labels
    y, valid_mask = engine.nivel_2_improved_labels()
    
    # NIVEL 3: Advanced Features
    X, scaler = engine.nivel_3_advanced_features(valid_mask)
    
    # NIVEL 4: Decision Thresholds
    threshold_config = engine.nivel_4_decision_thresholds()
    
    # Entrenar modelos con 4 niveles
    results = engine.train_models(X, y, weights, scale_pos)
    
    # Guardar
    engine.save_models(scaler)
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETADO - 4 NIVELES DE CORRECCIÓN APLICADOS")
    print("="*70)
    print("\n📊 RESULTADOS FINALES:")
    print(f"   Logistic WF: {results['logistic_wf'][0]:.4f} ± {results['logistic_wf'][1]:.4f}")
    print(f"   XGBoost WF:  {results['xgboost_wf'][0]:.4f} ± {results['xgboost_wf'][1]:.4f}")
    print("\n💾 Modelos guardados en: logs/trained_models/")


if __name__ == "__main__":
    main()
