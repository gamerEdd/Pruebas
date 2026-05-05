# -*- mode: python ; coding: utf-8 -*-
# Especificacion de PyInstaller para MT5 Trading Bot - ONEFILE

block_cipher = None

from PyInstaller.building.build_main import Analysis, PYZ, EXE

a = Analysis(
    ['boteddver1.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('logs', 'logs'),
    ],
    hiddenimports=[
        'boteddver1',
        # Core specialists
        'buy_specialist_ai',
        'sell_specialist_ai',
        'decision_arbitrator_ai',
        'gold_analyzer',
        'loss_analyzer',
        'loss_protection_ai',
        'recovery_based_closer',
        'feedback_loop_ai',
        'rapid_ops_validator',
        'entry_point_ai',
        'adaptive_parameters',
        # Data management
        'data_updater_module',
        'data_loader_trainer',
        # Pro system (Nivel 5-10)
        'regime_detector',
        'trend_model',
        'reversion_model',
        'bias_monitor',
        'drift_detector',
        'dynamic_weights',
        'meta_selector',
        'bot_integration_manager',
        # Advanced V12 modules
        'super_analyzer',
        'dynamic_score_calibration',
        'recovery_potential_enhanced',
        'spread_slippage_analyzer',
        'time_based_session_filter',
        'correlation_analyzer',
        'trade_logger',
        'auto_calibration',
        'dynamic_position_closer',
        'trend_change_detector',
        'multi_timeframe_analyzer',
        # P3 Phase utilities
        'indicator_base',
        'temporal_weighting',
        'outlier_filter',
        'candle_validator',
        'market_snapshot_generator',
        'safety_filters_manager',
        # External dependencies
        'MetaTrader5',
        'xgboost',
        'numpy',
        'pandas',
        'sklearn',
        'scipy',
        'psutil'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='MT5TradingBot_v16_Edd',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
