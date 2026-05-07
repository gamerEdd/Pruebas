# -*- mode: python ; coding: utf-8 -*-
"""
boteddver1.spec - Especificacion personalizada de PyInstaller
Optimizado para MT5 Trading Bot con console y logging
"""

a = Analysis(
    ['C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\boteddver1.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\mi_sesion.session', '.'),
        ('C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\config', 'config'),
        ('C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\models', 'models'),
    ],
    hiddenimports=[
        'MetaTrader5', 'numpy', 'pandas', 'sklearn', 'xgboost', 'scipy',
        'tkinter', 'threading', 'json', 'pickle',
        'mt5_safe', 'buy_specialist_ai', 'sell_specialist_ai', 'decision_arbitrator_ai',
        'gold_analyzer', 'loss_analyzer', 'loss_protection_ai', 'recovery_based_closer',
        'feedback_loop_ai', 'rapid_ops_validator', 'entry_point_ai', 'adaptive_parameters',
        'data_updater_module', 'data_loader_trainer', 'regime_detector', 'trend_model',
        'reversion_model', 'bias_monitor', 'drift_detector', 'dynamic_weights', 'meta_selector',
        'bot_integration_manager', 'super_analyzer', 'dynamic_score_calibration',
        'recovery_potential_enhanced', 'spread_slippage_analyzer', 'time_based_session_filter',
        'correlation_analyzer', 'trade_logger', 'auto_calibration', 'dynamic_position_closer',
        'trend_change_detector', 'multi_timeframe_analyzer', 'indicator_base', 'temporal_weighting',
        'outlier_filter', 'candle_validator', 'market_snapshot_generator', 'safety_filters_manager',
    ],
    excludes=['torch', 'transformers', 'torchaudio', 'huggingface_hub'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='boteddver1',
    debug=True,  # PERMITIR TRACEBACK Y LOGS
    bootloader_ignore_signals=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # SIEMPRE CON CONSOLA
    disable_windowed_traceback=False,  # PERMITIR TRACEBACK
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)