#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build MT5 Trading Bot Executable
Genera el ejecutable del bot de trading MT5 con PyInstaller
"""

import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """
    Construye el ejecutable del bot usando PyInstaller
    """
    
    print("[INFO] ========================================")
    print("[INFO] MT5 TRADING BOT - PYINSTALLER BUILD")
    print("[INFO] ========================================")
    
    # Verificar que estamos en el directorio correcto
    workspace = Path.cwd()
    print(f"[INFO] Directorio: {workspace}")
    
    # Lista de modulos principales (38 módulos requeridos)
    bot_modules = [
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
    ]
    
    # Verificar que todos los archivos principales existen
    print("[INFO] Verificando módulos del bot...")
    missing_modules = []
    for module in bot_modules:
        module_file = workspace / f"{module}.py"
        if not module_file.exists():
            missing_modules.append(module)
            print(f"[ERROR] Falta: {module}.py")
        else:
            print(f"[OK] {module}.py")
    
    if missing_modules:
        print(f"\n[FATAL] Faltan {len(missing_modules)} módulos. Abortando.")
        return False
    
    print(f"\n[OK] Todos los {len(bot_modules)} módulos encontrados")
    
    # ⭐ VERIFICAR QUE LAS CARPETAS DE DATOS EXISTEN
    print("\n[INFO] Verificando carpetas de datos...")
    config_dir = workspace / 'config'
    logs_dir = workspace / 'logs'
    
    if not config_dir.exists():
        print(f"[WARNING] Carpeta config no existe, creando...")
        config_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Carpeta config disponible")
    
    if not logs_dir.exists():
        print(f"[WARNING] Carpeta logs no existe, creando...")
        logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Carpeta logs disponible")
    
    # Nombres de archivos de salida
    exe_name = "MT5TradingBot_v16_Edd"
    
    # Ejecutar PyInstaller directamente con TODOS los argumentos
    print("\n[INFO] Iniciando compilacion con PyInstaller (MODO: onefile)...")
    print("[INFO] ⭐ COMPILANDO CON TODAS LAS DEPENDENCIAS...")
    print("[INFO] Esto puede tomar varios minutos...")
    
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',                        # ⭐ Un solo exe
        '--console',                        # ⭐ Con consola para logs
        '--distpath', str(workspace / 'dist'),
        '--workpath', str(workspace / 'build'),
        '--specpath', str(workspace),
        '--add-data', f'{config_dir}:config',      # Incluir carpeta config
        '--add-data', f'{logs_dir}:logs',          # Incluir carpeta logs
        # ⭐ MÓDULOS PRINCIPALES DEL BOT
        '--hidden-import=boteddver1',
        '--hidden-import=buy_specialist_ai',
        '--hidden-import=sell_specialist_ai',
        '--hidden-import=decision_arbitrator_ai',
        '--hidden-import=gold_analyzer',
        '--hidden-import=loss_analyzer',
        '--hidden-import=loss_protection_ai',
        '--hidden-import=recovery_based_closer',
        '--hidden-import=feedback_loop_ai',
        '--hidden-import=rapid_ops_validator',
        '--hidden-import=entry_point_ai',
        '--hidden-import=adaptive_parameters',
        '--hidden-import=data_updater_module',
        '--hidden-import=data_loader_trainer',
        '--hidden-import=regime_detector',
        '--hidden-import=trend_model',
        '--hidden-import=reversion_model',
        '--hidden-import=bias_monitor',
        '--hidden-import=drift_detector',
        '--hidden-import=dynamic_weights',
        '--hidden-import=meta_selector',
        '--hidden-import=bot_integration_manager',
        '--hidden-import=super_analyzer',
        '--hidden-import=dynamic_score_calibration',
        '--hidden-import=recovery_potential_enhanced',
        '--hidden-import=spread_slippage_analyzer',
        '--hidden-import=time_based_session_filter',
        '--hidden-import=correlation_analyzer',
        '--hidden-import=trade_logger',
        '--hidden-import=auto_calibration',
        '--hidden-import=dynamic_position_closer',
        '--hidden-import=trend_change_detector',
        '--hidden-import=multi_timeframe_analyzer',
        '--hidden-import=indicator_base',
        '--hidden-import=temporal_weighting',
        '--hidden-import=outlier_filter',
        '--hidden-import=candle_validator',
        '--hidden-import=market_snapshot_generator',
        '--hidden-import=safety_filters_manager',
        # ⭐ DEPENDENCIAS EXTERNAS CRÍTICAS
        '--hidden-import=MetaTrader5',
        '--hidden-import=mt5',
        '--hidden-import=xgboost',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=sklearn',
        '--hidden-import=sklearn.ensemble',
        '--hidden-import=sklearn.preprocessing',
        '--hidden-import=scipy',
        '--hidden-import=scipy.stats',
        '--hidden-import=psutil',
        '--hidden-import=threading',
        '--hidden-import=logging',
        '--hidden-import=json',
        '--hidden-import=time',
        '--hidden-import=datetime',
        '--hidden-import=collections',
        '--hidden-import=deque',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=pickle',
        '--hidden-import=requests',
        # ⭐ TKINTER Y UI
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=tkinter.font',
        # ⭐ OPCIONES DE RENDIMIENTO
        '--noupx',                          # Sin compresión UPX
        '--onefile',
        'boteddver1.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n[OK] Compilacion completada exitosamente")
        print("[INFO] ========================================")
        print("[INFO] VERIFICANDO EJECUTABLE...")
        print("[INFO] ========================================")
        
        # Verificar que el ejecutable fue creado (ONEFILE)
        dist_dir = workspace / 'dist'
        
        # ⭐ LISTAR ARCHIVOS EN dist/ PARA DEBUG
        if dist_dir.exists():
            print(f"\n[DEBUG] Archivos en {dist_dir}:")
            for item in dist_dir.iterdir():
                print(f"  - {item.name}")
        
        # Búsqueda flexible del ejecutable
        exe_path = dist_dir / f'{exe_name}.exe'
        
        # Si no lo encuentra con .exe, buscar en subcarpeta o sin extensión
        if not exe_path.exists():
            # Buscar cualquier .exe en dist
            exe_files = list(dist_dir.glob('*.exe'))
            if exe_files:
                exe_path = exe_files[0]
                print(f"\n[INFO] Ejecutable encontrado: {exe_path.name}")
            else:
                # Buscar en subcarpetas
                exe_files = list(dist_dir.glob('**/*.exe'))
                if exe_files:
                    exe_path = exe_files[0]
                    print(f"\n[INFO] Ejecutable encontrado: {exe_path}")
        
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # Convertir a MB
            print(f"\n[OK] ✅ EJECUTABLE ONEFILE CREADO")
            print(f"[OK] Ubicación: {exe_path}")
            print(f"[OK] Tamaño: {file_size:.1f} MB")
            print(f"\n[INFO] ========================================")
            print(f"[OK] ✅ INCLUIDO EN EL EJECUTABLE:")
            print(f"[OK] ✅ 39 módulos del bot")
            print(f"[OK] ✅ Carpeta config/ (con configuraciones)")
            print(f"[OK] ✅ Carpeta logs/ (para registros)")
            print(f"[OK] ✅ MetaTrader5")
            print(f"[OK] ✅ XGBoost")
            print(f"[OK] ✅ NumPy, Pandas, SciPy, Sklearn")
            print(f"[OK] ✅ Tkinter (interfaz gráfica)")
            print(f"[OK] ✅ Todas las dependencias")
            print(f"[INFO] ========================================")
            print(f"[OK] El bot está listo para usar")
            print(f"[INFO] Ejecuta: {exe_path}")
            print(f"[INFO] ========================================\n")
            return True
        else:
            print(f"\n[ERROR] No se encontro el ejecutable")
            print(f"[ERROR] Ubicación buscada: {exe_path}")
            print(f"[ERROR] Verifica que dist/ contiene archivos")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] PyInstaller fallo con codigo {e.returncode}")
        print(f"[ERROR] Ver detalles arriba en la salida")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error durante la compilacion: {e}")
        return False

def main():
    """Punto de entrada principal"""
    try:
        success = build_executable()
        if success:
            print("\n[INFO] ========================================")
            print("[OK] COMPILACION EXITOSA")
            print("[INFO] ========================================")
            sys.exit(0)
        else:
            print("\n[INFO] ========================================")
            print("[ERROR] COMPILACION FALLIDA")
            print("[INFO] ========================================")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[ERROR] Compilacion interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
