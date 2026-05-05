import argparse
import json
from ml_pipeline import DataExtractor, FeatureGenerator, InferenceEngine, load_scaler, DecisionEngine
import numpy as np
import logging

logger = logging.getLogger('infer_live')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='GOLD')
    parser.add_argument('--model', type=str, default='models/gru_test.keras',
                        help='Path to model (.keras preferred). If not found, will try .h5 and convert')
    parser.add_argument('--scaler', type=str, default='models/scaler_test.pkl')
    args = parser.parse_args()

    de = DataExtractor(args.symbol)
    fg = FeatureGenerator()
    rates = de.fetch_rates(n_bars=600)
    # prepare last 500 window
    window = rates[-500:]
    feat_df = fg.compute_raw_features(window)
    X_raw = feat_df.values.astype(float)
    scaler = load_scaler(args.scaler)
    # Ensure model exists: if .keras missing but .h5 present, convert it on the fly.
    import os
    try:
        from tensorflow.keras.models import load_model as _load_model
    except Exception:
        try:
            from keras.models import load_model as _load_model
        except Exception:
            raise

    model_path = args.model
    if not os.path.exists(model_path):
        # try .h5 fallback
        if model_path.endswith('.keras'):
            alt = model_path[:-6] + '.h5'
        else:
            alt = model_path + '.h5'
        if os.path.exists(alt):
            print(f'Converting {alt} -> {model_path}')
            m = _load_model(alt)
            m.save(model_path)
        else:
            raise SystemExit(f'Model not found: {model_path} (tried alt {alt})')

    ie = InferenceEngine(model_path=model_path, scaler=scaler)
    j = ie.predict_json(X_raw)
    print(j)
    probs = json.loads(j)
    decision = DecisionEngine.decide((probs['buy_probability'], probs['sell_probability'], probs['no_trade_probability']))
    print('Decision:', decision)

if __name__ == '__main__':
    main()
