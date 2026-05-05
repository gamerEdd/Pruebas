import argparse
import time
import numpy as np
from ml_pipeline import DataExtractor, FeatureGenerator, LabelGenerator, ModelTrainer, save_scaler
import logging
from sklearn.utils.class_weight import compute_class_weight

logger = logging.getLogger('train_model')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='GOLD')
    parser.add_argument('--bars', type=int, default=2500)
    parser.add_argument('--step', type=int, default=10)
    parser.add_argument('--model-out', type=str, default='models/gru_model.h5')
    parser.add_argument('--scaler-out', type=str, default='models/scaler.pkl')
    parser.add_argument('--balance', type=str, choices=['none','class_weight','oversample'], default='none', help='Class balancing strategy')
    args = parser.parse_args()

    de = DataExtractor(args.symbol)
    fg = FeatureGenerator()

    rates = de.fetch_rates(n_bars=args.bars)
    # compute atr for full series
    closes = np.array([r[4] for r in rates])
    highs = np.array([r[2] for r in rates])
    lows = np.array([r[3] for r in rates])
    atr_all = fg._atr(highs, lows, closes, period=14)
    labels_all = LabelGenerator.label_sequence(rates, atr_all, lookahead=20)

    samples = []
    labels = []
    max_start = len(rates) - 20 - 500 + 1
    for i in range(0, max_start, args.step):
        try:
            window = rates[i:i+500]
            feat_df = fg.compute_raw_features(window)
            samples.append(feat_df.values.astype(float))
            labels.append(int(labels_all[i]))
        except Exception as e:
            logger.exception(f'Window {i} error: {e}')
            continue

    if not samples:
        logger.error('No training samples created')
        return

    X_raw = np.stack(samples, axis=0)  # shape (n_samples, 500, n_features)
    n_samples, T, n_features = X_raw.shape
    # fit global scaler on concatenated data
    X_concat = X_raw.reshape(-1, n_features)
    scaler = fg.scaler.fit(X_concat)
    X_scaled = scaler.transform(X_concat).reshape(n_samples, T, n_features)

    trainer = ModelTrainer(n_features)
    # handle balancing options
    labels_arr = np.array(labels)
    if args.balance == 'class_weight':
        classes = np.unique(labels_arr)
        weights = compute_class_weight('balanced', classes=classes, y=labels_arr)
        cw_partial = {int(c): float(w) for c, w in zip(classes, weights)}
        # ensure mapping covers all class indices 0..2
        cw = {i: float(cw_partial.get(i, 1.0)) for i in range(3)}
        trainer.class_weight = cw
        model, test_data = trainer.train(X_scaled, labels_arr, epochs=20, batch_size=32)
    elif args.balance == 'oversample':
        # simple oversampling to equalize class counts
        unique, counts = np.unique(labels_arr, return_counts=True)
        target = int(counts.max())
        idxs = {int(u): np.where(labels_arr == u)[0].tolist() for u in unique}
        new_idx = []
        for u in unique:
            cur = idxs[int(u)]
            if len(cur) == 0:
                continue
            reps = int(np.ceil(target / len(cur)))
            new_idx.extend((cur * reps)[:target])
        X_bal = X_scaled[new_idx]
        y_bal = labels_arr[new_idx]
        model, test_data = trainer.train(X_bal, y_bal, epochs=20, batch_size=32)
    else:
        model, test_data = trainer.train(X_scaled, labels_arr, epochs=20, batch_size=32)

    # save model and scaler
    import os
    model.save(args.model_out)
    # Also save in native Keras format (.keras) for faster future loading
    keras_out = os.path.splitext(args.model_out)[0] + '.keras'
    try:
        model.save(keras_out)
    except Exception:
        # if saving .keras fails for any reason, ignore and continue
        pass
    save_scaler(scaler, args.scaler_out)
    logger.info('Training finished and artifacts saved')


if __name__ == '__main__':
    main()
