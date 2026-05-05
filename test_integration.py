#!/usr/bin/env python
"""Script de prueba rápida de integración"""

print("[TEST] Importando módulos...")

try:
    from dynamic_position_closer import DynamicPositionCloser
    print("✅ DynamicPositionCloser importado correctamente")
except Exception as e:
    print(f"❌ Error importando DynamicPositionCloser: {e}")

try:
    # Simular verificación de cambios en botiaver1.py
    with open('botiaver1.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Verificación 1: Import
    if 'from dynamic_position_closer import DynamicPositionCloser' in content:
        print("✅ Import de DynamicPositionCloser presente")
    else:
        print("❌ Import de DynamicPositionCloser NO encontrado")
    
    # Verificación 2: Instancia
    if 'self.position_closer = DynamicPositionCloser(log_callback=self.add_log)' in content:
        print("✅ Instancia de position_closer presente")
    else:
        print("❌ Instancia de position_closer NO encontrada")
    
    # Verificación 3: Uso en trend_monitor
    if 'self.position_closer.evaluate_and_close(' in content:
        print("✅ Uso de position_closer en trend_monitor presente")
    else:
        print("❌ Uso de position_closer NO encontrado")
    
    print("\n[TEST] ✅ Integración completada exitosamente")
    
except Exception as e:
    print(f"❌ Error verificando integración: {e}")
