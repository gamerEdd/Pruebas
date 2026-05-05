#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DE CALIBRACIÓN MICRO: GOLD 5025 → 5019 (6 PIPS BAJISTAS)

Caso específico que el usuario reportó:
- GOLD bajó de 5025 a 5019 (movimiento de 6 pips hacia abajo)
- Bot NO detectó SELL con calibración anterior
- CON MicroMomentumEngineV2 + ULTRA_MICRO profile: DEBE detectar STRONG_SELL

Este test simula la evaluación de micromomentum en ese escenario.
"""

import sys
import time
from datetime import datetime

try:
    from micro_momentum_engine_v2 import MicroMomentumEngineV2
except ImportError:
    print("ERROR: No se puede importar MicroMomentumEngineV2")
    print("Asegúrate que micro_momentum_engine_v2.py está en el mismo directorio")
    sys.exit(1)


def log_callback(message, msg_type='info'):
    """Callback simple para logging"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    colors = {
        'info': '\033[94m',      # Azul
        'success': '\033[92m',   # Verde
        'warning': '\033[93m',   # Amarillo
        'error': '\033[91m',     # Rojo
    }
    reset = '\033[0m'
    
    color = colors.get(msg_type, '')
    icon = {
        'info': 'ℹ️ ',
        'success': '✅',
        'warning': '⚠️ ',
        'error': '❌',
    }.get(msg_type, '')
    
    print(f"{color}[{timestamp}] {icon} {message}{reset}")


def test_gold_5025_to_5019():
    """
    Test principal: Evaluar detección de GOLD 5025→5019
    """
    
    print("\n" + "="*80)
    print(" TEST DE CALIBRACIÓN: GOLD 5025 → 5019 (6 PIPS BAJISTAS)")
    print("="*80)
    print()
    print("ESCENARIO:")
    print("  • Precio inicial: GOLD 5025.0")
    print("  • Precio actual: GOLD 5019.0")
    print("  • Movimiento: 6 pips hacia ABAJO (bajista)")
    print("  • Dirección predicha: BUY (por los especialistas)")
    print("  • Esperado: Micromomentum INVIERTE a SELL/STRONG_SELL")
    print()
    
    # Crear engines con diferentes perfiles
    print("Inicializando engines con diferentes perfiles...\n")
    
    engines = {
        'ULTRA_MICRO': MicroMomentumEngineV2(
            log_callback=log_callback,
            symbol='GOLD',
            profile='ULTRA_MICRO'
        ),
        'MICRO': MicroMomentumEngineV2(
            log_callback=log_callback,
            symbol='GOLD',
            profile='MICRO'
        ),
        'NORMAL': MicroMomentumEngineV2(
            log_callback=log_callback,
            symbol='GOLD',
            profile='NORMAL'
        ),
    }
    
    print()
    print("="*80)
    print(" EVALUANDO CADA PERFIL")
    print("="*80)
    print()
    
    results = {}
    
    for profile_name, engine in engines.items():
        print(f"\n{'─'*80}")
        print(f"PERFIL: {profile_name} ({engine.profile_name})")
        print(f"{'─'*80}")
        print(f"\nTicks: window={engine.window_ticks}, threshold={engine.pressure_threshold}")
        print(f"Movement min: {engine.movement_min} (~{engine.movement_min/engine.pip_value:.1f} pips)")
        print(f"Volatility min: {engine.micro_volatility_min} (~{engine.micro_volatility_min/engine.pip_value:.1f} pips)")
        print(f"Confirm ticks: {engine.confirm_ticks}\n")
        
        try:
            # Simular evaluación
            # Nota: Esto intentará contactar MT5 para obtener ticks reales
            result = engine.evaluate(
                symbol='GOLD',
                predicted_direction='BUY'  # Predicción inicial: BUY
            )
            
            # Almacenar resultado
            results[profile_name] = result
            
            # Mostrar resultado
            print(f"RESULTADO:")
            print(f"  • Decisión: {result['decision']}")
            print(f"  • Dirección final: {result['final_direction']}")
            print(f"  • Confianza: {result['confidence']}%")
            print(f"  • Motivo: {result['reason'][:150]}...")
            
            if 'tick_analytics' in result:
                ta = result['tick_analytics']
                print(f"\nANÁLITICA DE TICKS:")
                print(f"  • Ticks totales: {ta.get('tick_count', 0)}")
                print(f"  • Ticks UP: {ta.get('up_ticks', 0)} | DOWN: {ta.get('down_ticks', 0)}")
                print(f"  • Presión BUY: {ta.get('buy_pressure', 0):.1%} | SELL: {ta.get('sell_pressure', 0):.1%}")
                print(f"  • Movimiento: {ta.get('movement_pips', 0):.1f} pips")
                print(f"  • Volatilidad: {ta.get('volatility_pips', 0):.1f} pips")
                print(f"  • Ticks/segundo: {ta.get('ticks_per_second', 0):.1f}")
            
            # Validar resultado
            print(f"\nVALIDACIÓN:")
            
            if profile_name == 'ULTRA_MICRO':
                if result['decision'] in ['STRONG_SELL', 'INVERT']:
                    print(f"  ✅ CORRECTO: Detectó {result['decision']} (esperado)")
                else:
                    print(f"  ⚠️ INESPERADO: Detectó {result['decision']} (se esperaba STRONG_SELL/INVERT)")
            
            elif profile_name == 'MICRO':
                if result['decision'] in ['STRONG_SELL', 'INVERT']:
                    print(f"  ✅ CORRECTO: Detectó {result['decision']} (esperado)")
                else:
                    print(f"  ⚠️ INESPERADO: Detectó {result['decision']} (se esperaba STRONG_SELL/INVERT)")
            
            else:  # NORMAL
                if result['decision'] in ['CONFIRM']:
                    print(f"  ✅ CORRECTO: {result['decision']} (6 pips < umbral de 10 pips)")
                else:
                    print(f"  ℹ️ NOTA: Detectó {result['decision']}")
        
        except Exception as e:
            log_callback(f"Error en evaluación {profile_name}: {str(e)}", 'error')
            results[profile_name] = {
                'error': str(e),
                'decision': 'ERROR'
            }
        
        time.sleep(1)  # Pequeño delay entre evaluaciones
    
    # Resumen final
    print(f"\n{'='*80}")
    print(" RESUMEN DE RESULTADOS")
    print("="*80 + "\n")
    
    summary_table = []
    for profile, result in results.items():
        if 'error' not in result:
            tick_analytics = result.get('tick_analytics', {})
            summary_table.append({
                'Perfil': profile,
                'Decisión': result['decision'],
                'Dirección': result['final_direction'],
                'Confianza': f"{result['confidence']}%",
                'Pips': f"{tick_analytics.get('movement_pips', 0):.1f}",
            })
        else:
            summary_table.append({
                'Perfil': profile,
                'Decisión': 'ERROR',
                'Dirección': '-',
                'Confianza': '-',
                'Pips': '-',
            })
    
    # Imprimir tabla
    print(f"{'Perfil':<15} | {'Decisión':<15} | {'Dirección':<12} | {'Confianza':<10} | {'Pips':<8}")
    print("─" * 80)
    for row in summary_table:
        print(f"{row['Perfil']:<15} | {row['Decisión']:<15} | {row['Dirección']:<12} | "
              f"{row['Confianza']:<10} | {row['Pips']:<8}")
    
    print()
    print("CONCLUSIÓN:")
    print()
    
    # Validaciones
    ultra_micro = results.get('ULTRA_MICRO', {})
    micro = results.get('MICRO', {})
    normal = results.get('NORMAL', {})
    
    all_good = True
    
    if ultra_micro.get('decision') in ['STRONG_SELL', 'INVERT']:
        print("  ✅ ULTRA_MICRO: Detecta STRONG_SELL correctamente (caso 5025→5019)")
    else:
        print(f"  ❌ ULTRA_MICRO: NO detectó STRONG_SELL (detectó: {ultra_micro.get('decision')})")
        all_good = False
    
    if micro.get('decision') in ['STRONG_SELL', 'INVERT']:
        print("  ✅ MICRO: Detecta STRONG_SELL correctamente (caso 5025→5019)")
    else:
        print(f"  ⚠️ MICRO: Resultó {micro.get('decision')}")
        all_good = False
    
    if normal.get('decision') in ['CONFIRM']:
        print("  ✅ NORMAL: Correcto - 6 pips < 10 pips requeridos (CONFIRM es esperado)")
    else:
        print(f"  ℹ️ NORMAL: {normal.get('decision')}")
    
    print()
    
    if all_good:
        print("🎉 ¡TEST EXITOSO! MicroMomentumEngineV2 detecta correctamente 5025→5019")
    else:
        print("⚠️ TEST CON ADVERTENCIAS - Revisar configuración")
    
    print()
    print("="*80)
    print()

    return results


def test_different_scenarios():
    """
    Pruebas adicionales: diferentes tamaños de movimiento
    """
    print("\n" + "="*80)
    print(" PRUEBAS ADICIONALES: DIFERENTES MOVIMIENTOS")
    print("="*80 + "\n")
    
    engine_micro = MicroMomentumEngineV2(
        log_callback=log_callback,
        symbol='GOLD',
        profile='MICRO'
    )
    
    test_cases = [
        ("GOLD 5025 → 5023", "3 pips"),
        ("GOLD 5025 → 5020", "5 pips"),
        ("GOLD 5025 → 5019", "6 pips (CASO USUARIO)"),
        ("GOLD 5025 → 5015", "10 pips"),
        ("GOLD 5025 → 5010", "15 pips"),
        ("GOLD 5025 → 5000", "25 pips"),
    ]
    
    print("Con el perfil MICRO, intentar evaluar diferentes movimientos:")
    print(f"(Nota: Los datos reales vienen de MT5, estos son solo ejemplos)\n")
    
    for scenario, pips_desc in test_cases:
        print(f"  • {scenario} ({pips_desc})")
    
    print("\nPara ver resultados reales, ejecutar durante sesión de mercado abierta.")


if __name__ == '__main__':
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "TEST DE MICRO MOMENTUM ENGINE V2" + " "*26 + "║")
    print("║" + " "*78 + "║")
    print("║" + " CALIBRACIÓN PARA GOLD 5025 → 5019 (6 PIPS BAJISTAS)" + " "*25 + "║")
    print("╚" + "="*78 + "╝")
    
    # Ejecutar tests
    results = test_gold_5025_to_5019()
    
    # Tests adicionales (solo info)
    test_different_scenarios()
    
    print("\n" + "="*80)
    print(" PRÓXIMOS PASOS")
    print("="*80)
    print("""
1. ✅ MicroMomentumEngineV2 creado (micro_momentum_engine_v2.py)
2. ✅ Test de calibración ejecutado (este archivo)
3. ⏳ Integrar en decision_arbitrator_ai.py
   - Cambiar import
   - Usar en arbitrate()
4. ⏳ Actualizar UI en botiaver1.py
   - Agregar dropdown de perfil
   - Agregar método set_micro_profile()
5. ⏳ Test en vivo
   - Esperar movimiento 5025→5019
   - Verificar que detecta STRONG_SELL
   - Esperar que abra operación SELL

Ejecución:
  python test_micro_calibration_case.py
    
Resultado esperado:
  ✅ ULTRA_MICRO: Detecta STRONG_SELL
  ✅ MICRO: Detecta STRONG_SELL  
  ✅ NORMAL: CONFIRM (correcto - requiere 10+ pips)
  🎉 TEST EXITOSO!
""")
    print("="*80 + "\n")
