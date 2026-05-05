#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 Script de Verificación de Fixes
Valida que todos los cambios de memory leak se aplicaron correctamente
"""

import os
import sys

def check_fix(file_path, search_text, fix_name):
    """Verifica que un fix está presente en el archivo"""
    print(f"\n{'='*60}")
    print(f"🔍 Verificando: {fix_name}")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if search_text in content:
            print(f"✅ ENCONTRADO: {fix_name}")
            return True
        else:
            print(f"❌ NO ENCONTRADO: {fix_name}")
            return False
    except Exception as e:
        print(f"❌ ERROR al leer archivo: {e}")
        return False


def main():
    bot_file = r"c:\Users\eddgt\Desktop\newtradebots\boteddver1.py"
    
    if not os.path.exists(bot_file):
        print(f"❌ Error: Bot file no encontrado en {bot_file}")
        return False
    
    print("\n" + "="*60)
    print("🚀 AUDITORÍA DE MEMORY LEAK FIXES")
    print("="*60)
    
    fixes = [
        (
            "self.ghost_ops_history = deque(maxlen=100)",
            "Fix #1: ghost_ops_history limitado a 100"
        ),
        (
            "self.MAX_SNAPSHOTS = 1440",
            "Fix #2: MAX_SNAPSHOTS agregado"
        ),
        (
            "self.last_memory_log = 0  # Timestamp para logging",
            "Fix #3: last_memory_log agregado"
        ),
        (
            "reload_interval = 30  # ⭐ CAMBIADO de 5 a 30 segundos",
            "Fix #4: reload_interval cambiado a 30 segundos"
        ),
        (
            "if snaps and len(snaps) > self.MAX_SNAPSHOTS:",
            "Fix #5: Limitación de tamaño en reload_market_snapshots()"
        ),
        (
            "[MEMORY-PROTECTION] Snapshots truncados",
            "Fix #6: Log de protección de memoria"
        ),
        (
            "[MEMORY] Uso:",
            "Fix #7: Logging periódico de memoria"
        ),
        (
            "hist_size = min(hist_size, 200)",
            "Fix #8: Cap máximo para rapid_ops_history"
        ),
    ]
    
    results = []
    for search_text, fix_name in fixes:
        result = check_fix(bot_file, search_text, fix_name)
        results.append((fix_name, result))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for fix_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {fix_name}")
    
    print(f"\n{'='*60}")
    print(f"Fixes aplicados: {passed}/{total}")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS FIXES SE APLICARON CORRECTAMENTE!")
        print("\náximos pasos:")
        print("1. Instala psutil: pip install psutil")
        print("2. Ejecuta el bot: python boteddver1.py")
        print("3. Monitorea los logs [MEMORY] cada 10 minutos")
        print("4. Prueba cierre de emergencia después de 30 minutos")
        print("5. Verifica que la memoria se estabilice")
        return True
    else:
        print(f"\n⚠️  Solo {passed}/{total} fixes aplicados")
        print("Algunos cambios pueden haber fallado. Revisa manualmente.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

