# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['botiaver1.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gold_analyzer.py', '.'),
        ('loss_analyzer.py', '.'),
        ('loss_protection_ai.py', '.'),
        ('stop_loss_analyzer.py', '.'),
        ('buy_specialist_ai.py', '.'),
        ('sell_specialist_ai.py', '.'),
        ('decision_arbitrator_ai.py', '.')
    ],
    hiddenimports=[
        'MetaTrader5',
        'numpy',
        'pandas',
        'tkinter',
        'threading',
        'datetime',
        'collections',
        'gold_analyzer',
        'loss_analyzer',
        'loss_protection_ai',
        'stop_loss_analyzer',
        'buy_specialist_ai',
        'sell_specialist_ai',
        'decision_arbitrator_ai',
        'sklearn.preprocessing',
        'sklearn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Bot-IA-Ver7.0MultiAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
