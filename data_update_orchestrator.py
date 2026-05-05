"""
🔥 CAPA 4: RISK ENGINE - Actualizador de Datos cada 5 Minutos
Coordinador central que actualiza todo el bot con nuevos datos
"""

import threading
import time
from datetime import datetime, timedelta
from professional_dataset_manager import ProfessionalDatasetManager
from dataset_learning_engine import DatasetLearningEngine
from market_snapshot_generator import MarketSnapshotGenerator


class DataUpdateOrchestrator:
    """
    🚀 Coordinador centralizado que:
    1. Genera nuevos snapshots cada 5 minutos
    2. Actualiza el dataset
    3. Recalcula features para IA
    4. Notifica a especialistas
    5. Reentrena modelos si es necesario
    """
    
    def __init__(self, bot_instance, update_interval=300, log_callback=None, symbol="GOLD"):
        """
        bot_instance: Instancia del bot principal (botver16)
        update_interval: Segundos entre actualizaciones (300 = 5 minutos)
        symbol: Par a usar (GOLD, XAUUSD, etc)
        """
        self.bot = bot_instance
        self.update_interval = update_interval
        self.log_callback = log_callback
        self.symbol = symbol  # 🟢 Símbolo dinámico
        
        # Inicializar componentes
        self.dataset_manager = ProfessionalDatasetManager(log_callback=self.log, symbol=symbol)
        self.learning_engine = DatasetLearningEngine(self.dataset_manager, log_callback=self.log)
        self.generator = MarketSnapshotGenerator(symbol=symbol)
        
        # Estado
        self.is_running = False
        self.update_thread = None
        self.last_update_time = None
        self.update_count = 0
        self.current_insights = None
        
        self.log("✅ DataUpdateOrchestrator inicializado", 'info')
    
    def log(self, message, level='info'):
        """Callback centralizado de logs"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    
    def start_update_loop(self):
        """Inicia el loop de actualización cada 5 minutos"""
        if self.is_running:
            self.log("⚠️ Update loop ya está corriendo", 'warning')
            return
        
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.log(f"🟢 Update loop iniciado (intervalo: {self.update_interval}s)", 'info')
    
    def stop_update_loop(self):
        """Detiene el loop de actualización"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        self.log("🔴 Update loop detenido", 'info')
    
    def _update_loop(self):
        """Loop principal de actualización"""
        while self.is_running:
            try:
                self._perform_update()
                time.sleep(self.update_interval)
            except Exception as e:
                self.log(f"❌ Error en update loop: {e}", 'error')
                time.sleep(10)  # Reintentar después de 10 segundos
    
    def _perform_update(self):
        """
        🟢 Realiza actualización completa:
        1. Genera snapshot
        2. Actualiza dataset
        3. Recalcula features
        4. Reanaliza patrones
        5. Notifica especialistas
        """
        try:
            # 1️⃣ Generar snapshot profesional
            current_time = datetime.utcnow()
            snapshot = self.generator.generate_professional_snapshot(current_time)
            
            # 2️⃣ Agregar al dataset profesi
            self.dataset_manager.add_snapshot(snapshot)
            self.update_count += 1
            
            # 3️⃣ Recalcular features
            features = self.dataset_manager.calculate_all_features(snapshot)
            
            # 4️⃣ Reanalizar patrones cada 20 actualizaciones (100 minutos)
            if self.update_count % 20 == 0:
                patterns = self.learning_engine.analyze_dataset_patterns()
                self.current_insights = self.learning_engine.get_learning_insights()
                
                self.log(
                    f"🧠 Patrones reanalizado (actualización #{self.update_count})",
                    'info'
                )
            
            # 5️⃣ Guardar dataset
            self.dataset_manager.save_dataset()
            
            # 6️⃣ Notificar a especialistas
            self._notify_specialists(snapshot, features)
            
            self.last_update_time = current_time
            
            self.log(
                f"✅ Actualización #{self.update_count} completada "
                f"| Snapshots en dataset: {len(self.dataset_manager.snapshots)}",
                'info'
            )
            
        except Exception as e:
            self.log(f"❌ Error en actualización: {e}", 'error')
    
    def _notify_specialists(self, snapshot, features):
        """
        📢 Notifica a especialistas con:
        - Snapshot actual
        - Features calculadas
        - Insights de aprendizaje
        - Patrones históricos
        """
        
        # Datos que reciben los especialistas
        data_packet = {
            'snapshot': snapshot,
            'features': features,
            'insights': self.current_insights,
            'dataset_stats': self.dataset_manager.get_summary_stats(),
            'total_snapshots': len(self.dataset_manager.snapshots),
            'update_count': self.update_count,
        }
        
        # Guardar en logs para auditoría
        self.log(
            f"📊 Notificando especialistas: "
            f"{len(self.dataset_manager.snapshots)} snapshots | "
            f"Features: {len(features) if features else 0}",
            'info'
        )
        
        # Si el bot tiene un callback para especialistas, llamarlo
        if hasattr(self.bot, 'on_dataset_update'):
            try:
                self.bot.on_dataset_update(data_packet)
            except Exception as e:
                self.log(f"⚠️ Error notificando bot: {e}", 'warning')
    
    def get_dataset_status(self):
        """Obtiene estado actual del dataset"""
        stats = self.dataset_manager.get_summary_stats()
        
        return {
            'total_snapshots': len(self.dataset_manager.snapshots),
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'update_count': self.update_count,
            'is_running': self.is_running,
            'statistics': stats,
            'current_insights': self.current_insights,
        }
    
    def export_training_dataset(self, output_path="logs/training_dataset.csv"):
        """🧠 Exporta dataset para training de modelos ML"""
        df = self.dataset_manager.get_dataframe()
        if df is not None:
            df.to_csv(output_path, index=False)
            self.log(f"✅ Dataset de training exportado: {output_path}", 'info')
            return output_path
        return None
    
    def force_update_now(self):
        """Fuerza una actualización inmediata (útil para testing)"""
        self.log("🔄 Forzando actualización inmediata...", 'info')
        self._perform_update()
    
    def initialize_dataset_from_generator(self, num_snapshots=1000):
        """
        🚀 Inicializa dataset con snapshots generados
        Útil para primeras corridas
        """
        self.log(f"🔄 Generando {num_snapshots} snapshots iniciales para {self.symbol}...", 'info')
        
        # Usar el generador para crear snapshots
        snapshots = self.generator.generate_1000_snapshots(num_snapshots=num_snapshots)
        
        # Agregar al dataset
        for snap in snapshots:
            self.dataset_manager.add_snapshot(snap)
        
        # Guardar
        self.dataset_manager.save_dataset()
        
        # Analizar patrones iniciales
        patterns = self.learning_engine.analyze_dataset_patterns()
        self.current_insights = self.learning_engine.get_learning_insights()
        
        self.log(f"✅ Dataset inicializado con {len(self.dataset_manager.snapshots)} snapshots", 'info')


class SpecialistDataAdapter:
    """
    🔗 Adaptador que proporciona datos a especialistas
    Compatibilidad con buy_specialist_ai, sell_specialist_ai
    """
    
    def __init__(self, dataset_manager):
        self.dataset_manager = dataset_manager
    
    def get_market_context(self):
        """Obtiene contexto de mercado actual"""
        snapshot = self.dataset_manager.get_latest_snapshot()
        if not snapshot:
            return None
        
        return {
            'current_price': snapshot['price']['close'],
            'bid': snapshot['price']['bid'],
            'ask': snapshot['price']['ask'],
            'spread': snapshot['price']['spread'],
            'rsi': snapshot['indicators']['rsi_14'],
            'ema_9': snapshot['indicators']['ema_9'],
            'ema_21': snapshot['indicators']['ema_21'],
            'ema_50': snapshot['indicators']['ema_50'],
            'atr': snapshot['volatility']['atr_14'],
            'session': snapshot['context']['session'],
            'trend_m5': snapshot['context']['trend_m5'],
            'trend_m15': snapshot['context']['trend_m15'],
        }
    
    def get_price_history(self, count=50):
        """Obtiene historial de precios para cálculos técnicos"""
        return self.dataset_manager.get_price_history(count)
    
    def get_market_snapshots(self, count=50):
        """Obtiene snapshots recientes para análisis"""
        return self.dataset_manager.get_snapshots_window(count)


if __name__ == "__main__":
    # 🚀 Demo de inicialización
    print("Demo DataUpdateOrchestrator")
    print("=" * 50)
    
    # Inicializar dataset
    manager = ProfessionalDatasetManager()
    orchestrator = DataUpdateOrchestrator(bot_instance=None, update_interval=300)
    
    # Generar dataset inicial
    orchestrator.initialize_dataset_from_generator(1000)
    
    # Ver estado
    status = orchestrator.get_dataset_status()
    print(f"\\n📊 Estado del Dataset:")
    print(f"  Total snapshots: {status['total_snapshots']}")
    print(f"  Actualizaciones: {status['update_count']}")
    
    # Exportar para ML
    orchestrator.export_training_dataset()
