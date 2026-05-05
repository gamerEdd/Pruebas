import json

with open('logs/market_snapshots.json', 'r') as f:
    data = json.load(f)
    snap = data['snapshots'][0]
    print('ESTRUCTURA DEL SNAPSHOT:')
    for key in snap:
        if isinstance(snap[key], dict):
            print(f'  {key}:')
            for subkey in snap[key]:
                print(f'    - {subkey}: {snap[key][subkey]}')
        else:
            print(f'  {key}: {snap[key]}')
