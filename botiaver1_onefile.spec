# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# ⭐ FORZAR XGBoost DLL manualmente
xgboost_binaries = collect_dynamic_libs('xgboost')
try:
    import xgboost
    xgb_dll = os.path.join(os.path.dirname(xgboost.__file__), 'lib', 'xgboost.dll')
    if os.path.exists(xgb_dll):
        xgboost_binaries.append((xgb_dll, 'xgboost/lib'))
        print(f"[SPEC] XGBoost DLL: {xgb_dll}")
except Exception as e:
    print(f"[SPEC] XGBoost error: {e}")

# Datos a incluir
datas = [('logs', 'logs')]
datas += collect_data_files('xgboost')
if os.path.exists('mi_sesion.session'):
    datas.append(('mi_sesion.session', '.'))

# Agregar datos de librerías críticas
datas += collect_data_files('numpy')
datas += collect_data_files('pandas')
datas += collect_data_files('sklearn')
datas += collect_data_files('scipy')
try:
    datas += collect_data_files('tensorflow')
except Exception:
    pass

# Módulos principales
hiddenimports = [
    'MetaTrader5', 'buy_specialist_ai', 'sell_specialist_ai', 'decision_arbitrator_ai',
    'loss_protection_ai', 'feedback_loop_ai', 'rapid_ops_validator', 'entry_point_ai',
    'adaptive_parameters', 'gold_analyzer', 'loss_analyzer', 'data_updater_module',
    'data_loader_trainer', 'trade_logger', 'auto_calibration', 'regime_detector',
    'trend_model', 'reversion_model', 'bias_monitor', 'drift_detector', 'dynamic_weights',
    'meta_selector', 'bot_integration_manager', 'super_analyzer', 'dynamic_score_calibration',
    'recovery_potential_enhanced', 'spread_slippage_analyzer', 'time_based_session_filter',
    'correlation_analyzer', 'trend_change_detector', 'multi_timeframe_analyzer',
    'tick_flow_analyzer', 'safety_filters_manager', 'advanced_feature_engine',
    'ensemble_predictor_ai', 'pattern_recognizer', 'divergence_detector', 'mt5_safe',
]

hiddenimports += collect_submodules('numpy')
_pandas_subs = collect_submodules('pandas')
# Evitar que PyInstaller intente recolectar los tests de pandas (p. ej. pandas.tests.*)
# que requieren `pytest` y no son necesarios en el ejecutable final.
_pandas_subs = [m for m in _pandas_subs if not (m.startswith('pandas.tests') or '.tests.' in m)]
hiddenimports += _pandas_subs
hiddenimports += collect_submodules('sklearn')
hiddenimports += collect_submodules('scipy')
try:
    hiddenimports += collect_submodules('tensorflow')
    hiddenimports += ['tensorflow','tensorflow.keras','keras']
except Exception:
    pass

# Utilidades
hiddenimports += ['xgboost','xgboost.sklearn','joblib','pickle','json','logging','requests','dateutil','pytz']
# Incluir stubs/locales para hooks que a veces faltan en entornos restringidos
# (por ejemplo 'findlibs'). Si dispones de red, instala los paquetes
# reales con pip y elimina estos stubs.
hiddenimports += ['findlibs', 'nltk', 'traitlets', 'pygraphviz']

# Runtime hooks detectados
runtime_hooks = ['C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_cryptography_openssl.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_enchant.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_ffpyplayer.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_findlibs.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_nltk.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_osgeo.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_pygraphviz.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_pyproj.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_pyqtgraph_multiprocess.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_pythoncom.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_pywintypes.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_tensorflow.py', 'C:\\Users\\eddgt\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\_pyinstaller_hooks_contrib\\rthooks\\pyi_rth_traitlets.py']

a = Analysis([
    'boteddver1.py'], pathex=[], binaries=xgboost_binaries, datas=datas,
    hiddenimports=hiddenimports, hookspath=[], runtime_hooks=runtime_hooks,
    excludes=['tests','pytest','matplotlib','distutils','certbot','acme','pyopenssl','cryptography','setuptools','pkg_resources','jaraco','zipp','importlib_metadata','importlib_resources','wheel','pip','platformdirs','tomli','docutils','pygments','markdown','distlib','typing_extensions','lxml','openpyxl','xlrd','odfpy','urllib3.contrib.emscripten'],
    win_no_prefer_redirects=False, win_private_assemblies=False, cipher=block_cipher, noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name='MT5TradingBot_v16_Edd', debug=False, bootloader_ignore_signals=False, strip=False, upx=False, upx_exclude=[], runtime_tmpdir=None, console=True)
