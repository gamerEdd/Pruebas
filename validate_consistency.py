#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 SCRIPT DE VALIDACIÓN - Verificar consistencia del bot

Ejecutar: python validate_consistency.py
"""

import sys
import re

def check_file_for_patterns(filepath, patterns):
    """Verificar que los patrones existan en el archivo"""
    print(f"\n📄 Analizando: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {}
    for name, pattern in patterns.items():
        count = len(re.findall(pattern, content, re.IGNORECASE))
        exists = count > 0
        results[name] = {'exists': exists, 'count': count}
        
        status = "✅" if exists else "❌"
        print(f"  {status} {name}: {count} ocurrencias")
    
    return results

def main():
    print("=" * 60)
    print("🔍 VALIDACIÓN DE CONSISTENCIA DEL BOT")
    print("=" * 60)
    
    filepath = "botiaver1.py"
    
    patterns = {
        "Import TrendChangeDetector": r"from\s+trend_change_detector\s+import\s+TrendChangeDetector",
        "Instancia self.trend_detector": r"self\.trend_detector\s*=\s*TrendChangeDetector",
        "Función _analyze_trend_consistently": r"def\s+_analyze_trend_consistently",
        "Función _dual_analysis_before_opening": r"def\s+_dual_analysis_before_opening",
        "Método refactorizado check_forced_opening": r"def\s+check_forced_opening",
        "Método refactorizado startup_analysis_30s": r"def\s+startup_analysis_30s",
        "Parámetro force_mode en abrir_operacion": r"def\s+abrir_operacion\(self,\s*direccion_sugerida,\s*force_mode",
        "[DUAL] logs en _dual_analysis_before_opening": r"\[DUAL\]",
        "[FORZADA] logs en check_forced_opening": r"\[FORZADA\]",
        "[INICIAL] logs": r"\[INICIAL\]",
        "[TREND] logs": r"\[TREND\]",
        "Paso 1 - Cargar snapshots": r"PASO 1.*snapshots",
        "Paso 2 - Entrenar": r"PASO 2.*Entrenando",
        "Paso 3 - Analizar": r"PASO 3.*Analizando",
        "Paso 4 - Arbitrar": r"PASO 4.*Arbitrando",
        "Mode FORZADA en _dual_analysis": r"force_mode.*True.*Ignorando.*arbitrador",
        "Mode FORZADA en check_forced_opening": r"check_forced_opening.*force_mode.*True",
    }
    
    try:
        results = check_file_for_patterns(filepath, patterns)
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró {filepath}")
        return 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r['exists'])
    
    print(f"✅ Pasadas: {passed}/{total}")
    print(f"❌ Fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("   El bot está listo para testing")
        return 0
    else:
        print("\n⚠️  ALGUNAS VALIDACIONES FALLARON")
        print("   Revisar los cambios necesarios")
        return 1

if __name__ == '__main__':
    sys.exit(main())
