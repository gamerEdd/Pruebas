"""
[ACTUALIZAR] DATA UPDATER MODULE - Actualización dinámica de datos para análisis

Propósito: Asegurar que antes de cada análisis y apertura de operación,
se tengan datos frescos actualizados con el último bar M1.

Sistema de actualización de 3 niveles:
1. NIVEL 1 - Periodic (cada 60s): Background thread actualiza snapshots
2. NIVEL 2 - Pre-Analysis (on-demand): Fuerza actualización antes de analizar
3. NIVEL 3 - Fresh Data (en tiempo real): Agrega último bar M1 inmediatamente
"""

import MetaTrader5 as mt5
import mt5_safe
import time
import threading
import logging
import numpy as np
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataUpdater:
    """
    Gestor de actualización de datos con garantía de frescura
    """
    
    def __init__(self, symbol="XAUUSD", interval=60):
        """
        Args:
            symbol: Símbolo a monitorear (XAUUSD, BTCUSDT, etc)
            interval: Intervalo en segundos entre actualizaciones periódicas (default 60)
        """
        self.symbol = symbol
        self.interval = max(1, int(interval))  # ⭐ Mínimo 1 segundo para actualizaciones en tiempo real
        self.last_update = 0
        self.running = False
        self.lock = threading.Lock()
        self.market_snapshots = []
        self.last_m1_bar = None
        self.update_count = 0
        
    def start_periodic_updater(self, callback=None):
        """Inicia hilo de actualización periódica cada `interval` segundos"""
        self.running = True
        
        def _periodic_loop():
            logger.info(f"[ACTUALIZAR] Iniciando periodic updater cada {self.interval}s para {self.symbol}")
            while self.running:
                try:
                    self.update_snapshots_from_mt5()
                    if callback:
                        callback(self.update_count, len(self.market_snapshots))
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Error en periodic updater: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=_periodic_loop, daemon=True)
        thread.start()
        return thread
    
    def update_snapshots_from_mt5(self, max_bars=500):
        """
        Actualiza snapshots - intenta desde market_snapshots.json PRIMERO
        Si existe archivo, cargarlo. Si no, intentar desde MT5 (fallback).
        """
        try:
            # PRIMERO: Intentar cargar desde market_snapshots.json (que ya existe)
            market_snap_path = Path("logs/market_snapshots.json")
            if market_snap_path.exists():
                try:
                    import json
                    with open(market_snap_path, 'r') as f:
                        data = json.load(f)
                    
                    # Esperar dict con 'snapshots' o lista directa
                    if isinstance(data, dict) and 'snapshots' in data:
                        new_snapshots = data['snapshots'][-max_bars:]
                    elif isinstance(data, list):
                        new_snapshots = data[-max_bars:]
                    else:
                        new_snapshots = []
                    
                    if new_snapshots:
                        with self.lock:
                            self.market_snapshots = new_snapshots
                            if new_snapshots:
                                self.last_m1_bar = new_snapshots[-1]
                            self.last_update = time.time()
                            self.update_count += 1
                        
                        logger.info(f"[OK] Actualización #{self.update_count}: {len(new_snapshots)} snapshots desde market_snapshots.json para {self.symbol}")
                        return True
                except Exception as e:
                    logger.warning(f"Error cargando market_snapshots.json: {e}")
            
            # FALLBACK: Intentar desde MT5 (silenciosamente)
            logger.debug(f"[FALLBACK] Intentando cargar desde MT5 para {self.symbol}...")
            if not mt5.initialize():
                logger.debug(f"MT5 no disponible para actualizar {self.symbol}")
                return False
            
            # Obtener últimas N barras M1
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, max_bars)
            # Normalizar rates si vienen en formato dict/tuple
            rates = mt5_safe._ensure_rates_list(rates)
            
            if rates is None or len(rates) == 0:
                logger.debug(f"No hay datos M1 para {self.symbol} en MT5")
                return False
            
            # Convertir a snapshots
            new_snapshots = []
            for r in rates:
                try:
                    ts = int(r['time'] if isinstance(r, dict) else (r[0] if isinstance(r, (list, tuple)) else 0))
                    entry = {
                        'timestamp': datetime.fromtimestamp(ts).isoformat(),
                        'open': float(r['open'] if isinstance(r, dict) else r[1]),
                        'high': float(r['high'] if isinstance(r, dict) else r[2]),
                        'low': float(r['low'] if isinstance(r, dict) else r[3]),
                        'close': float(r['close'] if isinstance(r, dict) else r[4]),
                        'tick_volume': int(r.get('tick_volume', r[5] if isinstance(r, (list, tuple)) else 0) if isinstance(r, dict) else r[5])
                    }
                    new_snapshots.append(entry)
                except Exception as e:
                    logger.debug(f"Error procesando bar: {e}")
                    continue
            
            if new_snapshots:
                with self.lock:
                    self.market_snapshots = new_snapshots[-max_bars:]
                    self.last_m1_bar = new_snapshots[-1]
                    self.last_update = time.time()
                    self.update_count += 1
                
                logger.info(f"[OK] Actualización #{self.update_count} desde MT5: {len(new_snapshots)} snapshots para {self.symbol}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error en update_snapshots_from_mt5: {e}")
            return False
    
    def force_update_before_analysis(self):
        """
        Fuerza actualización antes de análisis - NIVEL 2 (On-Demand)
        Se ejecuta JUSTO ANTES de llamar a analizar_mercado()
        """
        logger.info("[ACTUALIZAR] FORCE UPDATE: Actualizando datos FRESCOs antes de análisis...")
        
        # Si última actualización fue hace menos de 5 segundos, usar caché
        time_since_update = time.time() - self.last_update
        if time_since_update < 5:
            logger.info(f"[OK] Datos suficientemente frescos ({time_since_update:.1f}s), usando caché")
            return True
        
        # Si no, forzar actualización inmediata
        logger.info("[ADVERTENCIA] Datos antiguos, forzando actualización inmediata...")
        return self.update_snapshots_from_mt5()
    
    def add_latest_m1_bar(self, snapshots_list=None):
        """
        Agrega el último bar M1 a los snapshots - NIVEL 3 (Tiempo Real)
        Ejecuta DESPUÉS de force_update_before_analysis()
        
        Args:
            snapshots_list: Lista de snapshots a actualizar (o None para usar interna)
        
        Returns:
            Lista actualizada con último bar
        """
        try:
            if not mt5.initialize():
                logger.warning("MT5 no disponible para agregar último bar")
                return snapshots_list or []
            
            # Obtener último bar
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 1)
            
            if rates is None or len(rates) == 0:
                logger.warning("No hay datos M1 disponibles")
                return snapshots_list or []
            
            # Convertir a snapshot
            r = rates[0]
            latest_bar = {
                'timestamp': datetime.fromtimestamp(int(r[0])).isoformat(),
                'open': float(r[1]),
                'high': float(r[2]),
                'low': float(r[3]),
                'close': float(r[4]),
                'tick_volume': int(r[5])
            }
            
            # Usar lista proporcionada o la interna
            current_list = snapshots_list or self.market_snapshots or []
            
            # Si la lista está vacía o el último bar es diferente, agregar
            if not current_list or current_list[-1].get('timestamp') != latest_bar['timestamp']:
                updated_list = current_list + [latest_bar]
                
                # Mantener máximo 500
                if len(updated_list) > 500:
                    updated_list = updated_list[-500:]
                
                logger.info(f"[OK] Agregado último bar M1 @ {latest_bar['close']:.5f} (total: {len(updated_list)})")
                return updated_list
            
            logger.info("[INFO] Último bar ya está en la lista")
            return current_list
            
        except Exception as e:
            logger.error(f"Error en add_latest_m1_bar: {e}")
            return snapshots_list or []
    
    def get_fresh_snapshots(self, force=False):
        """
        Obtiene snapshots frescos (NIVEL 1 + NIVEL 2 combinado)
        
        Args:
            force: Si True, fuerza actualización inmediata
        
        Returns:
            Lista de snapshots actualizados
        """
        if force:
            self.force_update_before_analysis()
        
        with self.lock:
            return list(self.market_snapshots) if self.market_snapshots else []
    
    def get_last_bar(self):
        """Obtiene el último bar M1 conocido"""
        with self.lock:
            return self.last_m1_bar.copy() if self.last_m1_bar else None
    
    def get_data_freshness(self):
        """
        Retorna información sobre frescura de datos
        Returns:
            {
                'seconds_since_update': float,
                'update_count': int,
                'snapshot_count': int,
                'fresh': bool (True si < 30 segundos)
            }
        """
        time_since = time.time() - self.last_update
        with self.lock:
            count = len(self.market_snapshots)
        
        return {
            'seconds_since_update': time_since,
            'update_count': self.update_count,
            'snapshot_count': count,
            'fresh': time_since < 30,
            'status': '[OK] FRESCO' if time_since < 30 else '[ANTIGUO] ANTIGUO'
        }
    
    def stop(self):
        """Detiene el actualizar periódico"""
        self.running = False
        logger.info(f"[DETENER] DataUpdater detenido después de {self.update_count} actualizaciones")


class PreAnalysisDataRefresher:
    """
    Utilidad para refrescar datos justo ANTES de análisis
    Asegura que se tenga el último bar M1 disponible
    """
    
    def __init__(self, updater, log_callback=None):
        self.updater = updater
        self.log_callback = log_callback
    
    def refresh_before_analysis(self, symbol):
        """
        Refresca datos para analisis - Flujo Completo:
        1. Force update desde MT5
        2. Agrega ultimo bar M1
        3. Retorna snapshots frescos
        """
        self._log("[LOG] === FLUJO DE ACTUALIZACION PRE-ANALISIS ===")
        
        # PASO 1: Force update
        self._log(f"[PASO] 1: Forzando actualizacion desde MT5...")
        if self.updater.force_update_before_analysis():
            self._log(f"[OK] MT5 actualizado correctamente")
        else:
            self._log(f"[ADVERTENCIA] No se pudo actualizar desde MT5")
        
        # PASO 2: Obtener snapshots actuales
        snapshots = self.updater.get_fresh_snapshots()
        self._log(f"[PASO] 2: Snapshots actuales: {len(snapshots)}")
        
        # PASO 3: Agregar ultimo bar M1
        self._log(f"[PASO] 3: Agregando ultimo bar M1...")
        updated_snapshots = self.updater.add_latest_m1_bar(snapshots)
        self._log(f"[OK] Snapshots frescos con ultimo bar: {len(updated_snapshots)}")
        
        # PASO 4: Verificar frescura
        freshness = self.updater.get_data_freshness()
        self._log(f"[PASO] 4: Frescura de datos: {freshness['status']} ({freshness['seconds_since_update']:.1f}s)")
        
        self._log(f"[LISTO] === LISTO PARA ANALISIS CON DATOS FRESCOS ===\n")
        
        return updated_snapshots
    
    def _log(self, msg):
        """Registra mensaje"""
        if self.log_callback:
            self.log_callback(msg, 'info')
        else:
            logger.info(msg)


# ======================== EJEMPLO DE USO ========================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear updater
    updater = DataUpdater(symbol="XAUUSD", interval=60)
    
    # Iniciar actualización periódica
    updater.start_periodic_updater(
        callback=lambda count, total: print(f"[OK] Update #{count}: {total} snapshots")
    )
    
    # Esperar a primera actualización
    time.sleep(2)
    
    # Simular pre-análisis
    print("\n" + "="*50)
    print("SIMULANDO PRE-ANÁLISIS")
    print("="*50)
    
    refresher = PreAnalysisDataRefresher(updater, log_callback=lambda m, _: print(m))
    snapshots = refresher.refresh_before_analysis("XAUUSD")
    
    print(f"\n[OK] Análisis puede proceder con {len(snapshots)} snapshots frescos")
    print(f"Último close: {snapshots[-1]['close']:.5f}" if snapshots else "Sin datos")
    
    # Detener
    time.sleep(2)
    updater.stop()
