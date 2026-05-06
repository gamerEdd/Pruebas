# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\boteddver1.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\mi_sesion.session', '.'), ('C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\config', 'config'), ('C:\\Users\\eddgt\\Desktop\\new\\ejet\\Pruebas\\models', 'models')],
    hiddenimports=['MetaTrader5', 'numpy', 'pandas', 'sklearn', 'xgboost', 'scipy', 'tkinter', 'threading', 'json', 'pickle', 'mt5_safe', 'buy_specialist_ai', 'sell_specialist_ai', 'decision_arbitrator_ai', 'gold_analyzer', 'loss_analyzer', 'loss_protection_ai', 'recovery_based_closer', 'feedback_loop_ai', 'rapid_ops_validator', 'entry_point_ai', 'adaptive_parameters', 'data_updater_module', 'data_loader_trainer', 'regime_detector', 'trend_model', 'reversion_model', 'bias_monitor', 'drift_detector', 'dynamic_weights', 'meta_selector', 'bot_integration_manager', 'super_analyzer', 'dynamic_score_calibration', 'recovery_potential_enhanced', 'spread_slippage_analyzer', 'time_based_session_filter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    debug=False,
    bootloader_ignore_signals=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
