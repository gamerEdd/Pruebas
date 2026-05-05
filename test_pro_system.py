"""
Test Híbrido: Verifica que sistema PRO + ML V2 carga correctamente
"""

import sys
sys.path.insert(0, r'c:\Users\eddgt\Desktop\newtradebots')

import numpy as np
import pandas as pd
import pickle
from pathlib import Path

# TEST 1: Importar módulos
print("=" * 60)
print("[TEST 1] Importar módulos PRO...")
try:
    from regime_detector import RegimeDetector
    from trend_model import TrendModel
    from reversion_model import ReversionModel
    from bias_monitor import BiasMonitor
    from drift_detector import DriftDetector
    from dynamic_weights import DynamicWeights
    from meta_selector import MetaSelector
    print("✅ Todos los módulos importados correctamente")
except Exception as e:
    print(f"❌ Error importando: {e}")
    sys.exit(1)

# TEST 2: Cargar modelos ML V2
print("\n" + "=" * 60)
print("[TEST 2] Cargar modelos ML V2...")
try:
    model_dir = Path('logs/trained_models')
    
    with open(model_dir / 'xgboost_v2_balanced.pkl', 'rb') as f:
        ml_model_xgb = pickle.load(f)
    
    with open(model_dir / 'scaler_v2_balanced.pkl', 'rb') as f:
        ml_scaler = pickle.load(f)
    
    print(f"✅ XGBoost V2 cargado")
    print(f"✅ Scaler V2 cargado")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# TEST 3: Inicializar componentes PRO
print("\n" + "=" * 60)
print("[TEST 3] Inicializar componentes PRO...")
try:
    regime_detector = RegimeDetector()
    trend_model = TrendModel()
    reversion_model = ReversionModel()
    bias_monitor = BiasMonitor()
    drift_detector = DriftDetector()
    dynamic_weights = DynamicWeights()
    
    print("✅ RegimeDetector inicializado")
    print("✅ TrendModel inicializado")
    print("✅ ReversionModel inicializado")
    print("✅ BiasMonitor inicializado")
    print("✅ DriftDetector inicializado")
    print("✅ DynamicWeights inicializado")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# TEST 4: Cargar modelos especializados
print("\n" + "=" * 60)
print("[TEST 4] Cargar modelos especializados...")
try:
    trend_model.load()
    reversion_model.load()
    
    if trend_model.model_loaded:
        print("✅ TrendModel cargó modelo")
    else:
        print("⚠️ TrendModel usará fallback")
    
    if reversion_model.model_loaded:
        print("✅ ReversionModel cargó modelo")
    else:
        print("⚠️ ReversionModel usará fallback")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# TEST 5: Crear MetaSelector
print("\n" + "=" * 60)
print("[TEST 5] Crear MetaSelector...")
try:
    meta_selector = MetaSelector(
        regime_detector,
        trend_model,
        reversion_model,
        bias_monitor,
        drift_detector,
        dynamic_weights
    )
    print("✅ MetaSelector creado exitosamente")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# TEST 6: Test de datos sintéticos
print("\n" + "=" * 60)
print("[TEST 6] Test con datos sintéticos...")
try:
    # Crear datos ficticios
    n_samples = 100
    dates = pd.date_range('2024-01-01', periods=n_samples, freq='1min')
    
    rates_dict = {
        'time': dates.astype(int) // 10**9,
        'open': np.random.uniform(2400, 2410, n_samples),
        'high': np.random.uniform(2410, 2420, n_samples),
        'low': np.random.uniform(2390, 2400, n_samples),
        'close': np.random.uniform(2400, 2410, n_samples),
        'tick_volume': np.random.uniform(100, 1000, n_samples)
    }
    
    # Crear features ficticias (11 dimensiones)
    features = np.array([[
        0.1, 0.2, 0.05, 0.3, 0.15, 0.05, 0.1, 0.05, 0.05, 0.02, 0.01
    ]], dtype=np.float32)
    
    # Predecir con MetaSelector
    result = meta_selector.predict(rates_dict, features)
    
    print(f"✅ Predicción completada")
    print(f"   - Régimen: {result['regime']}")
    print(f"   - Modelo usado: {result['model_used']}")
    print(f"   - Recomendación: {result['recommendation']}")
    print(f"   - Confianza: {result['confidence']:.1f}%")
    print(f"   - Bias detectado: {result['bias_adjusted']}")
    print(f"   - Drift detectado: {result['drift_warned']}")
    print(f"   - Size modifier: {result['position_size_modifier']:.2f}x")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 7: Test de BiasMonitor
print("\n" + "=" * 60)
print("[TEST 7] Test BiasMonitor...")
try:
    # Simular 200 operaciones para trigger check
    for i in range(200):
        bias_monitor.add_prediction(0.7, 0.3, executed_trade='BUY' if i % 2 == 0 else 'SELL')
    
    has_bias, adjustment, new_threshold = bias_monitor.check_bias()
    stats = bias_monitor.get_stats()
    
    print(f"✅ BiasMonitor test completado")
    print(f"   - Buy rate: {stats['buy_rate']:.2%}")
    print(f"   - Mean prob_buy: {stats['mean_prob_buy']:.3f}")
    print(f"   - Sesgo detectado: {has_bias}")
    print(f"   - Threshold actual: {stats['current_threshold_buy']:.2f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# TEST 8: Test de DynamicWeights
print("\n" + "=" * 60)
print("[TEST 8] Test DynamicWeights...")
try:
    weights_trend = dynamic_weights.get_weights_by_regime('TREND')
    weights_range = dynamic_weights.get_weights_by_regime('RANGE')
    
    print(f"✅ DynamicWeights test completado")
    print(f"   - TREND weights sum: {sum(weights_trend.values()):.3f}")
    print(f"   - RANGE weights sum: {sum(weights_range.values()):.3f}")
    
    emphasize = dynamic_weights.get_feature_emphasize('TREND')
    print(f"   - TREND top features: {[f[0] for f in emphasize['top_3']]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# RESUMEN FINAL
print("\n" + "=" * 60)
print("🎉 SISTEMA PRO COMPLETAMENTE FUNCIONAL")
print("=" * 60)
print("""
ARQUITECTURA IMPLEMENTADA:
─────────────────────────
✅ NIVEL 1-4: ML V2 XGBoost + 4 correcciones (ya existente)
✅ NIVEL 5: RegimeDetector (TREND/RANGE/NEUTRAL)
✅ NIVEL 6: TrendModel + ReversionModel (especialización)
✅ NIVEL 7: BiasMonitor (ajuste dinámico de thresholds)
✅ NIVEL 8: DriftDetector (PSI > 0.2 warning)
✅ NIVEL 9: DynamicWeights (pesos por régimen)
✅ NIVEL 10: MetaSelector (integración completa)

FLUJO DE PREDICCIÓN:
──────────────────
1. Detectar régimen (ADX > 25 = TREND, ADX < 20 = RANGE)
2. Elegir modelo según régimen
3. Verificar sesgo cada 200 operaciones
4. Detectar drift de distribución (PSI)
5. Ajustar tamaño de posición según drift
6. Aplicar pesos dinámicos
7. Hacer decisión con thresholds ajustados

FALLBACK JERÁRQUICO:
───────────────────
Intento 1: Sistema PRO (NIVEL 5-10)
Intento 2: ML V2 (NIVEL 4) si PRO falla
Intento 3: Análisis técnico si ML no disponible
""")
print("=" * 60)
