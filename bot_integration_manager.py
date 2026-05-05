"""
🔗 INTEGRADOR CENTRAL - Conecta Professional Dataset con Bot
Archivo para inicializar el bot con dataset professional completo
"""

import sys
from pathlib import Path

# Agregar ruta del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from professional_dataset_manager import ProfessionalDatasetManager
from dataset_learning_engine import DatasetLearningEngine
from data_update_orchestrator import DataUpdateOrchestrator
from buy_specialist_ai import BuySpecialistAI
from sell_specialist_ai import SellSpecialistAI
from decision_arbitrator_ai import DecisionArbitratorAI


class BotIntegrationManager:
    """
    🔗 Manager centralizado que integra todo el sistema:
    - Dataset profesional (1000 snapshots)
    - Especialistas de compra/venta
    - Árbitro de decisiones
    - Motor de actualizaciones
    """
    
    def __init__(self, log_callback=None, bot_instance=None, symbol="GOLD"):
        self.log_callback = log_callback
        self.bot = bot_instance
        self.symbol = symbol  # 🟢 Símbolo dinámico
        
        # Componentes principales
        self.dataset_manager = None
        self.learning_engine = None
        self.orchestrator = None
        self.buy_specialist = None
        self.sell_specialist = None
        self.decision_arbitrator = None
        
        self.log(f"🚀 Inicializando BotIntegrationManager para {symbol}", 'info')
    
    def log(self, message, level='info'):
        """Callback centralizado de logs"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    
    def initialize(self, generate_initial_data=True):
        """
        ⚙️ Inicializa todo el sistema
        """
        try:
            self.log(f"📊 Paso 1: Cargando Professional Dataset Manager para {self.symbol}", 'info')
            self.dataset_manager = ProfessionalDatasetManager(log_callback=self.log, symbol=self.symbol)
            
            # Generar datos iniciales si no existen
            if generate_initial_data:
                snapshots = self.dataset_manager.get_summary_stats()
                if snapshots is None or snapshots.get('total_snapshots', 0) == 0:
                    self.log(f"🔄 Generando 1000 snapshots iniciales para {self.symbol}...", 'info')
                    self._generate_initial_data()
            
            self.log("🧠 Paso 2: Inicializando Learning Engine", 'info')
            self.learning_engine = DatasetLearningEngine(
                self.dataset_manager,
                log_callback=self.log
            )
            
            # Analizar patrones iniciales
            patterns = self.learning_engine.analyze_dataset_patterns()
            if patterns:
                self.log(f"✅ {len(patterns.get('buy_conditions', {}))} condiciones de compra identificadas", 'info')
            
            self.log("🤖 Paso 3: Inicializando Especialistas con Dataset", 'info')
            self.buy_specialist = BuySpecialistAI(
                log_callback=self.log,
                dataset_manager=self.dataset_manager
            )
            
            self.sell_specialist = SellSpecialistAI(
                log_callback=self.log,
                dataset_manager=self.dataset_manager
            )
            
            self.log("⚖️ Paso 4: Inicializando Decision Arbitrator", 'info')
            self.decision_arbitrator = DecisionArbitratorAI(
                log_callback=self.log,
                dataset_manager=self.dataset_manager
            )
            
            self.log("🔄 Paso 5: Inicializando Data Update Orchestrator", 'info')
            self.orchestrator = DataUpdateOrchestrator(
                bot_instance=self.bot,
                update_interval=300,  # 5 minutos
                log_callback=self.log,
                symbol=self.symbol  # 🟢 Pasar símbolo
            )
            
            # Iniciar loop de actualización
            # self.orchestrator.start_update_loop()
            
            self.log("✅ ¡Sistema completamente inicializado!", 'success')
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error inicializando: {e}", 'error')
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_initial_data(self):
        """Genera 1000 snapshots iniciales"""
        from market_snapshot_generator import MarketSnapshotGenerator
        
        generator = MarketSnapshotGenerator(base_price=5377.50, symbol=self.symbol)
        snapshots = generator.generate_1000_snapshots(num_snapshots=1000)
        
        if snapshots:
            for snap in snapshots:
                self.dataset_manager.add_snapshot(snap)
            self.dataset_manager.save_dataset()
            self.log(f"✅ {len(snapshots)} snapshots generados y cargados", 'info')
    
    def get_status(self):
        """Obtiene estado completo del sistema"""
        status = {
            'initialized': all([
                self.dataset_manager is not None,
                self.learning_engine is not None,
                self.buy_specialist is not None,
                self.sell_specialist is not None,
                self.decision_arbitrator is not None,
            ]),
            'dataset_stats': self.dataset_manager.get_summary_stats() if self.dataset_manager else None,
            'orchestrator_running': self.orchestrator.is_running if self.orchestrator else False,
        }
        
        return status
    
    def analyze_market(self, symbol=None):
        """
        🧠 Análisis completo del mercado usando especialistas
        Retorna: buy_analysis, sell_analysis, final_decision
        """
        if symbol is None:
            symbol = self.symbol  # 🟢 Usar símbolo del instancia (GOLD, XAUUSD, etc)
        
        try:
            if not all([self.buy_specialist, self.sell_specialist, self.decision_arbitrator]):
                self.log("⚠️ Sistema no inicializado correctamente", 'warning')
                return None, None, None
            
            # Obtener datos del dataset
            market_snapshots = self.dataset_manager.get_snapshots_window(100)
            
            # Análisis de compra
            buy_analysis = self.buy_specialist.analyze(
                symbol,
                market_snapshots=market_snapshots
            )
            
            # Análisis de venta
            sell_analysis = self.sell_specialist.analyze(
                symbol,
                market_snapshots=market_snapshots
            )
            
            # Arbitraje final
            final_decision = self.decision_arbitrator.arbitrate(
                buy_analysis,
                sell_analysis,
                symbol
            )
            
            return buy_analysis, sell_analysis, final_decision
            
        except Exception as e:
            self.log(f"❌ Error en análisis: {e}", 'error')
            return None, None, None
    
    def start_updates(self):
        """Inicia el loop de actualización cada 5 minutos"""
        if self.orchestrator:
            self.orchestrator.start_update_loop()
            self.log("✅ Update loop iniciado", 'info')
    
    def stop_updates(self):
        """Detiene el loop de actualización"""
        if self.orchestrator:
            self.orchestrator.stop_update_loop()
            self.log("✅ Update loop detenido", 'info')
    
    def export_dataset(self, output_path="logs/current_dataset.csv"):
        """Exporta dataset para análisis o ML"""
        if self.dataset_manager:
            return self.dataset_manager.get_dataframe().to_csv(output_path, index=False)
        return None


if __name__ == "__main__":
    # 🚀 Demo de uso
    print("=" * 60)
    print("🚀 SISTEMA COMPLETO DE BOT CON DATASET PROFESIONAL")
    print("=" * 60)
    
    # Inicializar sistema
    manager = BotIntegrationManager(bot_instance=None)
    
    if manager.initialize(generate_initial_data=True):
        # Ver estado
        status = manager.get_status()
        print(f"\n✅ Estado del sistema:")
        print(f"  - Inicializado: {status['initialized']}")
        print(f"  - Total snapshots: {status['dataset_stats'].get('total_snapshots', 0) if status['dataset_stats'] else 0}")
        
        # Analizar mercado
        print(f"\n🧠 Análisis de mercado:")
        buy_analysis, sell_analysis, decision = manager.analyze_market()
        
        if decision:
            print(f"  - BUY Score: {buy_analysis.get('score', 0):.1f}")
            print(f"  - SELL Score: {sell_analysis.get('score', 0):.1f}")
            print(f"  - Decision: {decision.get('recommendation', 'HOLD')}")
            print(f"  - Probability: {decision.get('probability', 0):.1%}")
        
        # Exportar dataset
        print(f"\n💾 Exportando dataset...")
        manager.export_dataset()
        print(f"  ✅ Dataset exportado a logs/current_dataset.csv")
        
        print("\n✅ Demo completado correctamente!")
    else:
        print("\n❌ Error inicializando sistema")
