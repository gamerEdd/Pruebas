import json
import time
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
import mt5_safe
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
# Keras import fallback: prefer tensorflow.keras, fall back to keras if needed
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import GRU, Dense, Dropout
    from tensorflow.keras.utils import to_categorical
    from tensorflow.keras.callbacks import EarlyStopping
except Exception:
    try:
        from keras.models import Sequential, load_model
        from keras.layers import GRU, Dense, Dropout
        from keras.utils import to_categorical
        from keras.callbacks import EarlyStopping
    except Exception:
        raise
import logging

logger = logging.getLogger('MLPipeline')


class DataExtractor:
    def __init__(self, symbol, tf_main=mt5.TIMEFRAME_M1, tf_ctx=mt5.TIMEFRAME_M5):
        self.symbol = symbol
        self.tf_main = tf_main
        self.tf_ctx = tf_ctx

    def fetch_rates(self, n_bars=500):
        # Try to ensure MT5 initialized and symbol selected, then fetch bars.
        try:
            if not mt5.initialize():
                mt5.initialize()
        except Exception:
            # ignore initialization error, we'll attempt copy_rates anyway
            pass
        try:
            mt5.symbol_select(self.symbol, True)
        except Exception:
            pass

        rates = mt5.copy_rates_from_pos(self.symbol, self.tf_main, 0, n_bars + 50)
        if rates is not None and len(rates) > 0:
            return list(rates)

        # Fallbacks: 1) CSV via env ML_RATES_CSV 2) local data/sample_rates.csv 3) synthetic data
        import os
        # Evitar dependencia de variables de entorno; usar ruta por defecto dentro del repo
        csv_path = os.path.join('data', 'sample_rates.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Expect columns similar to MT5: time, open, high, low, close, tick_volume, spread, real_volume
            if len(df) < n_bars:
                raise RuntimeError(f'Fallback CSV too short: {csv_path}')
            rec = df.tail(n_bars + 50)
            return [tuple(x) for x in rec.to_numpy()]

        # Synthetic generator (best-effort) to allow training/testing without MT5
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            base = float(getattr(tick, 'ask', getattr(tick, 'last', 100.0))) if tick is not None else 100.0
        except Exception:
            base = 100.0
        rng = np.random.default_rng(seed=42)
        size = n_bars + 50
        closes = base + np.cumsum(rng.normal(0, 0.05, size))
        opens = closes + rng.normal(0, 0.02, size)
        highs = np.maximum(opens, closes) + np.abs(rng.normal(0, 0.02, size))
        lows = np.minimum(opens, closes) - np.abs(rng.normal(0, 0.02, size))
        times = list(range(size))[::-1]
        vols = (rng.integers(1, 100, size)).tolist()
        spreads = (rng.random(size) * 0.0005).tolist()
        records = list(zip(times, opens.tolist(), highs.tolist(), lows.tolist(), closes.tolist(), vols, spreads, vols))
        return records

    def fetch_ctx(self):
        # fetch M5 context for EMA200, ADX. If MT5 not available return empty list.
        try:
            rates5 = mt5.copy_rates_from_pos(self.symbol, self.tf_ctx, 0, 400)
            return list(rates5) if rates5 is not None else []
        except Exception:
            return []


class FeatureGenerator:
    def __init__(self):
        self.scaler = StandardScaler()

    @staticmethod
    def _ema(series, period):
        return pd.Series(series).ewm(span=period, adjust=False).mean().values

    @staticmethod
    def _rsi(closes, period=14):
        series = pd.Series(closes)
        delta = series.diff()
        up = delta.clip(lower=0).rolling(window=period).mean()
        down = -delta.clip(upper=0).rolling(window=period).mean()
        rs = up / (down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi.values

    @staticmethod
    def _atr(highs, lows, closes, period=14):
        h = pd.Series(highs); l = pd.Series(lows); c = pd.Series(closes)
        tr1 = h - l
        tr2 = (h - c.shift()).abs()
        tr3 = (l - c.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.values

    def compute_raw_features(self, rates_m1, rates_m5=None):
        # return raw feature DataFrame (no scaling) for a 500-bar window
        df = pd.DataFrame(rates_m1)
        expected_cols = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        # ensure columns are named consistently; if not, coerce from positional tuples
        try:
            if df.shape[1] >= 5:
                df.columns = expected_cols[:df.shape[1]]
            else:
                # try to coerce records into rows of values
                df = pd.DataFrame([tuple(x) for x in rates_m1])
                if df.shape[1] >= 5:
                    df.columns = expected_cols[:df.shape[1]]
                else:
                    raise ValueError('Unexpected rates format: need at least 5 columns')
        except Exception:
            raise ValueError('Unexpected rates format: could not coerce columns')

        if len(df) < 500:
            raise ValueError('Need at least 500 bars')
        df = df.tail(500).reset_index(drop=True)
        closes = df['close'].astype(float).values
        opens = df['open'].astype(float).values
        highs = df['high'].astype(float).values
        lows = df['low'].astype(float).values
        features = {}
        features['price_log'] = np.log(closes + 1e-9)
        features['ret_log'] = np.concatenate([[0], np.diff(np.log(closes))])
        features['body_size'] = np.abs(closes - opens)
        features['range'] = highs - lows
        features['wick_up'] = highs - np.maximum(closes, opens)
        features['wick_down'] = np.minimum(closes, opens) - lows
        trend = []
        for i in range(len(closes)):
            window = closes[max(0, i-19):i+1]
            if len(window) < 2:
                trend.append(0.0)
            else:
                xs = np.arange(len(window))
                a = np.polyfit(xs, window, 1)[0]
                trend.append(a)
        features['trend'] = np.array(trend)
        ema50 = self._ema(closes, 50)
        ema200 = self._ema(closes, 200)
        features['dist_ema50'] = closes - ema50
        features['dist_ema200'] = closes - ema200
        features['ema50_slope'] = np.concatenate([[0], np.diff(ema50)])
        features['volatility'] = pd.Series(features['ret_log']).rolling(20).std().fillna(0).values
        atr = self._atr(highs, lows, closes, period=14)
        features['atr'] = atr
        atr50 = pd.Series(atr).rolling(50).mean().fillna(method='bfill').values
        features['atr_rel'] = np.divide(atr, atr50 + 1e-9)
        atrp20 = pd.Series(atr).rolling(50).apply(lambda x: np.percentile(x, 20) if len(x)>0 else 0).fillna(0).values
        features['compression'] = (atr <= atrp20).astype(float)
        atr_past = np.concatenate([[atr[0]]*5, atr[:-5]])
        features['expansion'] = np.divide(atr, atr_past + 1e-9)
        features['momentum'] = np.concatenate([[0]*1, np.diff(closes)])
        features['rsi'] = self._rsi(closes, 14)
        features['rsi_slope'] = np.concatenate([[0], np.diff(features['rsi'])])
        bullish_ratio = []
        for i in range(len(closes)):
            w = closes[max(0, i-19):i+1]
            o = opens[max(0, i-19):i+1]
            if len(w) == 0:
                bullish_ratio.append(0.0)
            else:
                bullish_ratio.append(np.mean((w - o) > 0))
        features['bull_ratio20'] = np.array(bullish_ratio)
        features['max50'] = pd.Series(closes).rolling(50).max().fillna(method='bfill').values
        features['min50'] = pd.Series(closes).rolling(50).min().fillna(method='bfill').values
        if rates_m5 is not None and len(rates_m5) > 50:
            closes5 = np.array([float(r['close']) if isinstance(r, dict) else float(r[4]) for r in rates_m5])
            ema200_m5 = self._ema(closes5, 200)[-1]
            features['ctx_ema200_m5'] = np.array([ema200_m5]*len(closes))
            features['ctx_adx_m5'] = np.array([0.0]*len(closes))
        else:
            features['ctx_ema200_m5'] = np.zeros(len(closes))
            features['ctx_adx_m5'] = np.zeros(len(closes))
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            spread = float(getattr(tick, 'ask', 0) - getattr(tick, 'bid', 0))
        except Exception:
            spread = 0.0
        features['spread'] = np.array([spread]*len(closes))
        hours = pd.to_datetime(df['time'], unit='s').dt.hour.values
        features['hour'] = hours / 23.0
        feat_df = pd.DataFrame(features)
        feat_df.fillna(0, inplace=True)
        return feat_df

    def generate_features(self, rates_m1, rates_m5=None):
        feat_df = self.compute_raw_features(rates_m1, rates_m5)
        X = feat_df.values.astype(float)
        Xn = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        return Xn, self.scaler


class LabelGenerator:
    @staticmethod
    def label_sequence(rates, atr_values, lookahead=20):
        # rates: list of tuples; atr_values aligned
        closes = np.array([r[4] for r in rates])
        n = len(closes)
        labels = []
        for i in range(n - lookahead):
            close = closes[i]
            atr = atr_values[i]
            tp = close + 1.8 * atr
            sl = close - 1.2 * atr
            outcome = 2  # NO_TRADE default (2)
            for j in range(i+1, i+1+lookahead):
                price = closes[j]
                if price >= tp:
                    outcome = 0  # BUY
                    break
                if price <= sl:
                    outcome = 1  # SELL
                    break
            labels.append(outcome)
        return np.array(labels)


class ModelTrainer:
    def __init__(self, n_features):
        self.n_features = n_features

    def build_model(self):
        model = Sequential()
        model.add(GRU(64, return_sequences=True, input_shape=(500, self.n_features)))
        model.add(Dropout(0.2))
        model.add(GRU(32))
        model.add(Dropout(0.2))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(3, activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
        return model

    def train(self, X, y, epochs=20, batch_size=32):
        model = self.build_model()
        y_cat = to_categorical(y, num_classes=3)
        X_train, X_tmp, y_train, y_tmp = train_test_split(X, y_cat, test_size=0.3, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.5, random_state=42)
        es = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        # Support passing class_weight dict via kwargs in future calls
        class_weight = None
        # if caller provided a class_weight mapping inside self (optional), use it
        if hasattr(self, 'class_weight') and isinstance(self.class_weight, dict):
            class_weight = self.class_weight
        model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=epochs, batch_size=batch_size, callbacks=[es], class_weight=class_weight)
        scores = model.evaluate(X_test, y_test, verbose=0)
        logger.info(f'Test loss/acc: {scores}')
        return model, (X_test, y_test)


class InferenceEngine:
    def __init__(self, model_path=None, scaler=None):
        self.model = load_model(model_path) if model_path else None
        self.scaler = scaler

    def predict_json(self, X_window):
        # X_window shape (500, n_features)
        xn = self.scaler.transform(X_window.reshape(-1, X_window.shape[-1])).reshape(X_window.shape)
        proba = self.model.predict(xn[np.newaxis, ...])[0]
        return json.dumps({
            'buy_probability': float(proba[0]),
            'sell_probability': float(proba[1]),
            'no_trade_probability': float(proba[2])
        })


class DecisionEngine:
    @staticmethod
    def decide(probs):
        buy, sell, no = probs
        if buy > 0.62 and buy > sell + 0.15:
            return 'BUY'
        if sell > 0.62 and sell > buy + 0.15:
            return 'SELL'
        return 'NO_TRADE'


class ExternalFilters:
    @staticmethod
    def block_by_spread(current_spread, avg_spread):
        return current_spread > avg_spread * 1.7

    @staticmethod
    def block_by_atr(atr, threshold=1e-6):
        return atr < threshold

    @staticmethod
    def block_by_streak(loss_streak, max_losses=3):
        return loss_streak >= max_losses


def save_scaler(scaler, path):
    import pickle
    with open(path, 'wb') as f:
        pickle.dump(scaler, f)

def load_scaler(path):
    import pickle
    with open(path, 'rb') as f:
        return pickle.load(f)
