import argparse
import numpy as np
import json
from ml_pipeline import DataExtractor, FeatureGenerator, LabelGenerator, ModelTrainer, load_scaler
try:
    from tensorflow.keras.models import load_model
except Exception:
    try:
        from keras.models import load_model
    except Exception:
        raise
from sklearn.metrics import confusion_matrix, classification_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--scaler', required=True)
    parser.add_argument('--symbol', default='GOLD')
    parser.add_argument('--bars', type=int, default=500)
    parser.add_argument('--step', type=int, default=10)
    parser.add_argument('--lookahead', type=int, default=20)
    args = parser.parse_args()

    de = DataExtractor(args.symbol)
    fg = FeatureGenerator()

    # fetch rates from MT5 (will raise if not available)
    rates = de.fetch_rates(n_bars=args.bars + 200)
    if rates is None or len(rates) < args.bars + 50:
        raise SystemExit('Not enough bars for evaluation')

    # compute atr and labels for full series
    closes = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates])
    highs = np.array([float(r['high']) if isinstance(r, dict) else float(r[2]) for r in rates])
    lows = np.array([float(r['low']) if isinstance(r, dict) else float(r[3]) for r in rates])
    atr_all = fg._atr(highs, lows, closes, period=14)
    labels_all = LabelGenerator.label_sequence(rates, atr_all, lookahead=args.lookahead)

    samples = []
    labels = []
    max_start = len(rates) - args.lookahead - 500 + 1
    for i in range(0, max_start, args.step):
        try:
            window = rates[i:i+500]
            feat_df = fg.compute_raw_features(window)
            samples.append(feat_df.values.astype(float))
            labels.append(int(labels_all[i]))
        except Exception as e:
            print(f'Window {i} error: {e}')
            continue

    if not samples:
        raise SystemExit('No samples created for evaluation')

    X = np.stack(samples, axis=0)
    n_samples, T, n_features = X.shape
    # load scaler and model
    scaler = load_scaler(args.scaler)
    X_concat = X.reshape(-1, n_features)
    X_scaled = scaler.transform(X_concat).reshape(n_samples, T, n_features)

    model = load_model(args.model)
    probs = model.predict(X_scaled, batch_size=32)
    preds = np.argmax(probs, axis=1)
    y_true = np.array(labels)

    print('Confusion matrix:')
    print(confusion_matrix(y_true, preds))
    print('\nClassification report:')
    print(classification_report(y_true, preds, digits=4))

    # Save results
    out = {'confusion_matrix': confusion_matrix(y_true, preds).tolist(), 'report': classification_report(y_true, preds, output_dict=True)}
    with open('models/eval_report.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('\nSaved models/eval_report.json')


if __name__ == '__main__':
    main()
