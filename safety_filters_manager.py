"""
🛡️ SAFETY FILTERS MANAGER - FILTROS INSTITUCIONALES
Spread, ATR, Economic Calendar, Market Hours, Volatility Regimes
"""

import json
import datetime
import numpy as np
from pathlib import Path


class SafetyFiltersManager:
    """🛡️ Gestor de filtros de seguridad profesionales"""
    
    def __init__(self, dataset_path='logs/market_snapshots.json', log_callback=None):
        self.dataset_path = dataset_path
        self.log = log_callback or print
        self.snapshots = []
        
        # ⭐ NUEVO: Flag para evitar repetir warnings al inicio
        self.warned_empty_dataset = False
        
        # Estadísticas calculadas
        self.mean_spread = 0
        self.std_spread = 0
        self.mean_atr = 0
        self.std_atr = 0
        self.mean_volume = 0
        
        self.load_dataset()
        self.calculate_statistics()
    
    def load_dataset(self):
        """Carga datos del dataset"""
        try:
            # Verificar si el archivo existe
            if not Path(self.dataset_path).exists():
                # ⭐ SILENCIOSO: No loguear si no existe (es normal al inicio)
                # self.log(f"ℹ️ Dataset no encontrado: {self.dataset_path} (se creará al operar)", 'info')
                self.snapshots = []
                return False
            
            # Intentar cargar el JSON
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # Si el archivo está vacío, inicializar con lista vacía
                if not content:
                    # ⭐ SILENCIOSO: No loguear si dataset está vacío (es normal al inicio)
                    # self.log(f"ℹ️ Dataset vacío en: {self.dataset_path}", 'info')
                    self.snapshots = []
                    return False
                
                # Intentar parsear JSON
                data = json.loads(content)
                self.snapshots = data.get('snapshots', []) if isinstance(data, dict) else []
            
            if len(self.snapshots) > 0:
                self.log(f"✅ Dataset cargado: {len(self.snapshots)} snapshots", 'success')
            # ⭐ SILENCIOSO: No loguear "Dataset vacío" (es normal al inicio)
            
            return len(self.snapshots) > 0
            
        except json.JSONDecodeError as e:
            self.log(f"⚠️ JSON corrupto en {self.dataset_path}: {str(e)[:50]}", 'warning')
            self.snapshots = []
            return False
        except Exception as e:
            self.log(f"⚠️ Error cargando dataset: {str(e)[:100]}", 'warning')
            self.snapshots = []
            return False
    
    def calculate_statistics(self):
        """📊 Calcula estadísticas del dataset para umbrales dinámicos"""
        if len(self.snapshots) < 10:
            # ⭐ SILENCIOSO: Solo loguear una sola vez al init
            if not self.warned_empty_dataset and len(self.snapshots) == 0:
                # DEBUG: Se salta este log al inicio para no contaminar
                # self.log("⚠️ Dataset insuficiente para cálculos", 'warning')
                self.warned_empty_dataset = True
            return
        
        # Spreads
        spreads = [s.get('volume', {}).get('spread', 0.00001) for s in self.snapshots]
        self.mean_spread = np.mean(spreads)
        self.std_spread = np.std(spreads)
        
        # ATR
        atrs = [s.get('indicators', {}).get('atr_14', 0.1) for s in self.snapshots]
        self.mean_atr = np.mean(atrs)
        self.std_atr = np.std(atrs)
        
        # Volumen
        volumes = [s.get('volume', {}).get('tick_volume', 100) for s in self.snapshots]
        self.mean_volume = np.mean(volumes)
        
        self.log(f"📊 Estadísticas calculadas:", 'info')
        self.log(f"   Spread promedio: {self.mean_spread:.6f} ± {self.std_spread:.6f}", 'info')
        self.log(f"   ATR promedio: {self.mean_atr:.6f} ± {self.std_atr:.6f}", 'info')
        self.log(f"   Volumen promedio: {self.mean_volume:.0f}", 'info')
    
    def check_spread_safe(self, current_spread, threshold_multiplier=1.5):
        """
        🔴 FILTRO 1: Spread seguro
        Si Spread > media_spread × 1.5 → NO OPERAR (spreads altos = slippage)
        """
        max_spread = self.mean_spread * threshold_multiplier
        is_safe = current_spread <= max_spread
        
        if not is_safe:
            reason = f"Spread {current_spread:.6f} > límite {max_spread:.6f}"
        else:
            reason = f"Spread {current_spread:.6f} OK (límite: {max_spread:.6f})"
        
        return is_safe, reason
    
    def check_atr_safe(self, current_atr, threshold_multiplier=0.5):
        """
        🔴 FILTRO 2: ATR mínimo
        Si ATR < media_atr × 0.5 → NO OPERAR (movimiento insuficiente)
        """
        min_atr = self.mean_atr * threshold_multiplier
        is_safe = current_atr >= min_atr
        
        if not is_safe:
            reason = f"ATR {current_atr:.6f} < mínimo {min_atr:.6f} (volatilidad baja)"
        else:
            reason = f"ATR {current_atr:.6f} OK (mínimo: {min_atr:.6f})"
        
        return is_safe, reason
    
    def check_market_hours_safe(self):
        """
        🕐 FILTRO 3: Horario de mercado
        ESPECIALMENTE para GOLD (XAUUSD):
        - MEJOR: London (08:00-17:00 UK time)
        - BUENO: NY (13:00-22:00 UK time)
        - EVITAR: Cierre de semana/Sydney (muy illíquidos)
        """
        now_utc = datetime.datetime.utcnow()
        hour_utc = now_utc.hour
        day_utc = now_utc.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
        
        # Determinar sesión
        sessions = {
            'sydney': (22, 7),      # 22:00-07:00 UTC
            'tokyo': (0, 9),        # 00:00-09:00 UTC
            'london': (8, 17),      # 08:00-17:00 UTC (MEJOR)
            'newyork': (13, 22),    # 13:00-22:00 UTC (BUENO)
        }
        
        current_session = self._get_current_session(hour_utc, sessions)
        
        # Reglas de seguridad
        is_trading_safe = True
        reason = ""
        
        # No operar en fin de semana
        if day_utc >= 5:
            is_trading_safe = False
            reason = "FIN DE SEMANA - Mercado cerrado"
        # Preferred: London + NY
        elif current_session in ['london', 'newyork']:
            reason = f"✅ Sesión óptima: {current_session.upper()} (líquida)"
        # OK but less liquid
        elif current_session == 'tokyo':
            reason = f"⚠️ Sesión TOKIO - Menos líquida pero operando"
        # Avoid: Sydney
        elif current_session == 'sydney':
            is_trading_safe = False
            reason = "❌ Sesión SYDNEY - Muy ilíquida, NO OPERAR"
        
        return is_trading_safe, reason
    
    def _get_current_session(self, hour_utc, sessions):
        """Determina sesión actual"""
        for session_name, (start, end) in sessions.items():
            if start <= end:  # No cruza medianoche
                if start <= hour_utc < end:
                    return session_name
            else:  # Cruza medianoche
                if hour_utc >= start or hour_utc < end:
                    return session_name
        return 'sydney'
    
    def check_economic_calendar_safe(self):
        """
        📍 FILTRO 4: Calendario económico
        Simula detección de eventos económicos importantes
        
        En prod: Integrar con económic calendar API (forexfactory, etc)
        Aquí: Detectar volatilidad anormal como proxy
        """
        if len(self.snapshots) < 2:
            return True, "Sin datos para evaluar"
        
        # Obtener volatilidad últimas 10 candles
        recent_volatility = [
            self.snapshots[-i].get('volatility', {}).get('volatility_20', 0)
            for i in range(1, min(11, len(self.snapshots)))
        ]
        
        mean_vol = np.mean(recent_volatility)
        current_vol = recent_volatility[0]
        
        # Si volatilidad > 3σ = probable evento económico
        vol_threshold = mean_vol * 3
        is_safe = current_vol <= vol_threshold
        
        if not is_safe:
            reason = f"⚠️ Volatilidad extrema: {current_vol:.6f} > {vol_threshold:.6f} (probable evento económico)"
        else:
            reason = f"✅ Volatilidad normal: {current_vol:.6f}"
        
        return is_safe, reason
    
    def check_volume_safe(self, current_volume, min_volume_ratio=0.7):
        """
        📊 FILTRO 5: Volumen mínimo
        Si volumen < media × 0.7 → Posible problema de liquidez
        """
        min_volume = self.mean_volume * min_volume_ratio
        is_safe = current_volume >= min_volume
        
        if not is_safe:
            reason = f"Volumen bajo: {current_volume:.0f} < mínimo {min_volume:.0f}"
        else:
            reason = f"Volumen OK: {current_volume:.0f} (mínimo: {min_volume:.0f})"
        
        return is_safe, reason
    
    def check_drawdown_protection(self, current_drawdown, max_drawdown_threshold=-0.02):
        """
        📉 FILTRO 6: Protección contra drawdown
        Si Max Drawdown > -2% → Reducir tamaño de posición o salirse
        """
        is_safe = current_drawdown >= max_drawdown_threshold
        
        if not is_safe:
            reason = f"Drawdown crítico: {current_drawdown:.2%} < {max_drawdown_threshold:.2%}"
        else:
            reason = f"Drawdown OK: {current_drawdown:.2%}"
        
        return is_safe, reason
    
    def run_all_checks(self, current_snapshot=None):
        """
        🛡️ EJECUTA TODOS LOS FILTROS DE SEGURIDAD
        Retorna: (es_seguro_operar, razones_detalladas)
        
        ⭐ MEJORA: Si no hay datos al INICIO, retorna True (permite operar)
                  mientras el bot genera snapshots automáticamente
        """
        if current_snapshot is None and len(self.snapshots) > 0:
            current_snapshot = self.snapshots[-1]
        
        if current_snapshot is None:
            # ⭐ AL INICIO DEL BOT: Permitir operar (True) para empezar a generar datos
            # El sistema generará snapshots mientras opera
            return True, {'starting_up': (True, "✅ Iniciando - generando datos de snapshots")}
        
        checks = {}
        all_safe = True
        
        # FILTRO 1: Spread
        spread = current_snapshot.get('volume', {}).get('spread', 0.00001)
        safe, reason = self.check_spread_safe(spread)
        checks['spread'] = (safe, reason)
        all_safe = all_safe and safe
        
        # FILTRO 2: ATR
        atr = current_snapshot.get('indicators', {}).get('atr_14', 0.1)
        safe, reason = self.check_atr_safe(atr)
        checks['atr'] = (safe, reason)
        all_safe = all_safe and safe
        
        # FILTRO 3: Horario
        safe, reason = self.check_market_hours_safe()
        checks['market_hours'] = (safe, reason)
        all_safe = all_safe and safe
        
        # FILTRO 4: Eventos Económicos
        safe, reason = self.check_economic_calendar_safe()
        checks['economic_events'] = (safe, reason)
        all_safe = all_safe and safe
        
        # FILTRO 5: Volumen
        volume = current_snapshot.get('volume', {}).get('tick_volume', 100)
        safe, reason = self.check_volume_safe(volume)
        checks['volume'] = (safe, reason)
        all_safe = all_safe and safe
        
        return all_safe, checks
    
    def get_filter_summary(self, checks):
        """📊 Imprime resumen de filtros"""
        summary = "\n🛡️ FILTROS DE SEGURIDAD:\n"
        for filter_name, (is_safe, reason) in checks.items():
            status = "✅ PASS" if is_safe else "❌ FAIL"
            summary += f"  {status} | {filter_name.upper():20s} | {reason}\n"
        return summary


if __name__ == "__main__":
    print("\n" + "🛡️ "*30)
    print("SAFETY FILTERS MANAGER - FILTROS INSTITUCIONALES")
    print("🛡️ "*30 + "\n")
    
    manager = SafetyFiltersManager()
    is_safe, checks = manager.run_all_checks()
    print(manager.get_filter_summary(checks))
    print(f"\n{'✅ SEGURO OPERAR' if is_safe else '❌ NOT SAFE'}\n")
