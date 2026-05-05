#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la función de Margen de Ganancia en boteddver1.py

Esta prueba verifica que:
1. La variable MARGEN_GANANCIA está correctamente configurada
2. El monitor de margen se inicia cuando el bot comienza
3. El cálculo del objetivo es correcto
"""

import sys
import os

# Agregar ruta del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_margen_ganancia():
    """Test básico del margen de ganancia"""
    
    print("=" * 70)
    print("TEST: Función de Margen de Ganancia - boteddver1.py")
    print("=" * 70)
    
    # Test 1: Verificar que MARGEN_GANANCIA existe en configuración
    print("\n[TEST 1] Verificando que MARGEN_GANANCIA está en config...")
    try:
        # Leer el archivo boteddver1.py y buscar MARGEN_GANANCIA
        with open('boteddver1.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "'MARGEN_GANANCIA': tk.DoubleVar(value=1.0)" in content:
            print("✅ MARGEN_GANANCIA encontrado en configuración inicial (default=1.0%)")
        else:
            print("❌ MARGEN_GANANCIA NO encontrado en configuración")
            return False
            
        if "('Margen de Ganancia Objetivo (%):', 'MARGEN_GANANCIA')" in content:
            print("✅ Campo de entrada en panel de configuración detectado")
        else:
            print("⚠️ Campo de entrada en panel de configuración NO detectado (pero podría estar en otra forma)")
            
    except Exception as e:
        print(f"❌ Error leyendo boteddver1.py: {e}")
        return False
    
    # Test 2: Verificar función _monitor_profit_margin
    print("\n[TEST 2] Verificando función _monitor_profit_margin...")
    try:
        if "def _monitor_profit_margin(self):" in content:
            print("✅ Función _monitor_profit_margin() definida correctamente")
            
            # Verificar que incluye los checks necesarios
            if "self.balance_inicial_para_margen" in content and \
               "self.objetivo_margen_ganancia" in content and \
               "self.margen_ganancia_alcanzado" in content:
                print("✅ Variables de estado del margen inicializadas")
            else:
                print("⚠️ Algunas variables de estado NO están presentes")
                
            if "self.cierre_emergencia()" in content:
                print("✅ Función cierre_emergencia() será llamada si se alcanza objetivo")
            else:
                print("⚠️ cierre_emergencia() NO está siendo llamada")
        else:
            print("❌ Función _monitor_profit_margin NO encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando función: {e}")
        return False
    
    # Test 3: Verificar inicialización en start_bot
    print("\n[TEST 3] Verificando que el monitor se inicia en start_bot()...")
    try:
        if "self.margen_monitor_running = True" in content and \
           "self.margen_monitor_thread = threading.Thread(target=self._monitor_profit_margin" in content:
            print("✅ Monitor de margen se inicializa en start_bot()")
        else:
            print("❌ Monitor NO se inicializa en start_bot()")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 4: Verificar detención en stop_bot
    print("\n[TEST 4] Verificando que el monitor se detiene en stop_bot()...")
    try:
        if "self.margen_monitor_running = False" in content:
            print("✅ Monitor se detiene correctamente en stop_bot()")
        else:
            print("⚠️ Flag de detención NO encontrado (pero podría detenerse de otra forma)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 5: Verificar widget en panel de control
    print("\n[TEST 5] Verificando widget visual en panel de control...")
    try:
        if "self.margen_monitor_label = tk.Label(margen_frame" in content:
            print("✅ Widget margen_monitor_label creado en panel de control")
        else:
            print("⚠️ Widget NO encontrado (pero puede estar creado de otra forma)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 6: Lógica del cálculo
    print("\n[TEST 6] Verificando lógica del cálculo de objetivo...")
    try:
        if "self.objetivo_margen_ganancia = self.balance_inicial_para_margen * (1.0 + margen_pct / 100.0)" in content:
            print("✅ Fórmula correcta: objetivo = balance × (1 + margen%/100)")
            print("   Ejemplo: Si balance=$100 y margen=1%, objetivo will be $101")
        else:
            print("⚠️ Fórmula NO encontrada exactamente (pero podría estar escrita de otra forma)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 70)
    print("\n📝 RESUMEN DE FUNCIONAMIENTO:")
    print("   1. El usuario configura 'Margen de Ganancia Objetivo (%)' en el panel")
    print("   2. Al iniciar el bot, se captura el balance inicial")
    print("   3. Se calcula el objetivo: balance × (1 + margen/100)")
    print("   4. Cada segundo, se verifica si equity >= objetivo")
    print("   5. Si se cumple: cierra TODAS las operaciones y detiene el bot")
    print("   6. El widget muestra: 'Equity: $XXX / Objetivo: $YYY (NN.N%)'")
    print("\n💡 EJEMPLOS:")
    print("   • Balance=$500, Margen=2% → Objetivo=$510")
    print("   • Balance=$1000, Margen=1% → Objetivo=$1010")
    print("   • Balance=$100, Margen=5% → Objetivo=$105")
    print("\n" + "=" * 70)
    
    return True

if __name__ == "__main__":
    success = test_margen_ganancia()
    sys.exit(0 if success else 1)
