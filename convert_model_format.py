import argparse
try:
    from tensorflow.keras.models import load_model
except Exception:
    try:
        from keras.models import load_model
    except Exception:
        raise
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--h5', required=True, help='Path to HDF5 model (.h5)')
    parser.add_argument('--out', required=False, help='Output .keras path (default: same name .keras)')
    args = parser.parse_args()

    h5 = args.h5
    if not os.path.exists(h5):
        raise SystemExit(f'HDF5 model not found: {h5}')
    out = args.out or (os.path.splitext(h5)[0] + '.keras')
    print(f'Loading {h5}...')
    model = load_model(h5)
    print(f'Saving to {out} (Keras native format)...')
    model.save(out)
    print('Done')

if __name__ == '__main__':
    main()
