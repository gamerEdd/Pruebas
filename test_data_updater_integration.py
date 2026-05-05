"""
Test de Verificación - Sistema de Actualización Dinámica de Datos
"""

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test 1: Verificar importaciones"""
    print("\n" + "="*60)
    print("TEST 1: Importaciones del Módulo DataUpdater")
    print("="*60)
    
    try:
        from data_updater_module import DataUpdater, PreAnalysisDataRefresher
        print("✅ Importación exitosa: DataUpdater")
        print("✅ Importación exitosa: PreAnalysisDataRefresher")
        return True
    except Exception as e:
        print(f"❌ Error importando módulos: {e}")
        return False

def test_data_updater_creation():
    """Test 2: Crear instancia de DataUpdater"""
    print("\n" + "="*60)
    print("TEST 2: Creación de Instancia DataUpdater")
    print("="*60)
    
    try:
        from data_updater_module import DataUpdater
        
        updater = DataUpdater(symbol="XAUUSD", interval=60)
        print(f"✅ DataUpdater creado para {updater.symbol}")
        print(f"✅ Intervalo configurado: {updater.interval} segundos")
        
        # Verificar atributos
        assert hasattr(updater, 'market_snapshots'), "Falta atributo: market_snapshots"
        assert hasattr(updater, 'update_count'), "Falta atributo: update_count"
        assert hasattr(updater, 'running'), "Falta atributo: running"
        print("✅ Todos los atributos presentes")
        
        return True, updater
    except Exception as e:
        print(f"❌ Error creando DataUpdater: {e}")
        return False, None

def test_data_updater_methods():
    """Test 3: Verificar métodos del DataUpdater"""
    print("\n" + "="*60)
    print("TEST 3: Métodos del DataUpdater")
    print("="*60)
    
    try:
        from data_updater_module import DataUpdater
        
        updater = DataUpdater()
        
        # Verificar métodos
        methods = [
            'start_periodic_updater',
            'update_snapshots_from_mt5',
            'force_update_before_analysis',
            'add_latest_m1_bar',
            'get_fresh_snapshots',
            'get_last_bar',
            'get_data_freshness',
            'stop'
        ]
        
        for method in methods:
            assert hasattr(updater, method), f"Falta método: {method}"
            assert callable(getattr(updater, method)), f"{method} no es callable"
            print(f"  ✅ {method}()")
        
        return True
    except Exception as e:
        print(f"❌ Error verificando métodos: {e}")
        return False

def test_pre_analysis_refresher():
    """Test 4: Crear instancia de PreAnalysisDataRefresher"""
    print("\n" + "="*60)
    print("TEST 4: Creación de PreAnalysisDataRefresher")
    print("="*60)
    
    try:
        from data_updater_module import DataUpdater, PreAnalysisDataRefresher
        
        updater = DataUpdater(symbol="XAUUSD", interval=60)
        
        def mock_log(msg, level='info'):
            print(f"  [{level.upper()}] {msg}")
        
        refresher = PreAnalysisDataRefresher(updater, log_callback=mock_log)
        print(f"✅ PreAnalysisDataRefresher creado")
        
        # Verificar atributos
        assert hasattr(refresher, 'updater'), "Falta atributo: updater"
        assert hasattr(refresher, 'log_callback'), "Falta atributo: log_callback"
        print("✅ Todos los atributos presentes")
        
        # Verificar métodos
        assert hasattr(refresher, 'refresh_before_analysis'), "Falta método: refresh_before_analysis"
        print("✅ Método refresh_before_analysis() presente")
        
        return True
    except Exception as e:
        print(f"❌ Error creando PreAnalysisDataRefresher: {e}")
        return False

def test_botiaver1_integration():
    """Test 5: Verificar integración en botiaver1.py"""
    print("\n" + "="*60)
    print("TEST 5: Integración en botiaver1.py")
    print("="*60)
    
    try:
        # Leer botiaver1.py y verificar integración (con manejo de encoding)
        with open('botiaver1.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Verificar importaciones
        if 'from data_updater_module import DataUpdater, PreAnalysisDataRefresher' in content:
            print("✅ Importaciones de DataUpdater agregadas")
        else:
            print("❌ Importaciones de DataUpdater NO encontradas")
            return False
        
        # Verificar inicialización
        if 'self.data_updater = None' in content:
            print("✅ Variable self.data_updater inicializada")
        else:
            print("❌ Variable self.data_updater NO inicializada")
            return False
        
        if 'self.pre_analysis_refresher = None' in content:
            print("✅ Variable self.pre_analysis_refresher inicializada")
        else:
            print("❌ Variable self.pre_analysis_refresher NO inicializada")
            return False
        
        # Verificar inicialización en start_bot
        if 'self.data_updater = DataUpdater' in content:
            print("✅ DataUpdater instanciado en start_bot()")
        else:
            print("❌ DataUpdater NO instanciado en start_bot()")
            return False
        
        # Verificar uso en análisis
        if 'self.pre_analysis_refresher.refresh_before_analysis' in content:
            print("✅ Pre-analysis refresher llamado antes de análisis")
        else:
            print("❌ Pre-analysis refresher NO llamado")
            return False
        
        # Verificar limpieza en stop_bot
        if 'self.data_updater.stop()' in content:
            print("✅ Data Updater detenido en stop_bot()")
        else:
            print("❌ Data Updater NO detenido en stop_bot()")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error verificando integración: {e}")
        return False

def test_compilation():
    """Test 6: Compilación de botiaver1.py"""
    print("\n" + "="*60)
    print("TEST 6: Compilación de botiaver1.py")
    print("="*60)
    
    try:
        import py_compile
        py_compile.compile('botiaver1.py', doraise=True)
        print("✅ botiaver1.py compila sin errores")
        return True
    except Exception as e:
        print(f"❌ Error compilando botiaver1.py: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print("SUITE DE TESTS - SISTEMA DE ACTUALIZACIÓN DINÁMICO DE DATOS")
    print("="*70)
    
    results = []
    
    # Test 1
    results.append(("Importaciones", test_imports()))
    
    # Test 2
    test2_pass, updater = test_data_updater_creation()
    results.append(("Instancia DataUpdater", test2_pass))
    
    # Test 3
    results.append(("Métodos DataUpdater", test_data_updater_methods()))
    
    # Test 4
    results.append(("PreAnalysisDataRefresher", test_pre_analysis_refresher()))
    
    # Test 5
    results.append(("Integración botiaver1.py", test_botiaver1_integration()))
    
    # Test 6
    results.append(("Compilación", test_compilation()))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASADO" if result else "❌ FALLADO"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*70)
    print(f"Total: {passed}/{len(results)} tests pasados")
    
    if failed == 0:
        print("\n🟢 TODOS LOS TESTS PASARON - SISTEMA OPERATIVO ✅")
        return True
    else:
        print(f"\n🔴 {failed} tests fallaron - Revisar errores")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
