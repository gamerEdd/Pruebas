from auto_calibration import prefill_market_data

if __name__ == '__main__':
    n = prefill_market_data('GOLD', minutes=500)
    print('filled', n)
