#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para comentar logs diagnósticos"""

import re
import sys

# Patrones de logs a comentar/deshabilitar
PATTERNS_TO_COMMENT = [
    r'self\.add_log\(f?".*\[VOLATILITY\]',
    r'self\.add_log\(f?".*\[TREND\].*snapshots',
    r'self\.add_log\(f?".*\[ESPERA-INTERVALO\]',
    r'self\.add_log\(f?".*\[GLOBAL TP/SL\].*Azules',
    r'self\.add_log\(f?".*\[GLOBAL TP/SL\].*Rojas',
    r'self\.add_log\(f?".*\[MONITOR-MT5\]',
    r'logger\.info\(f?".*\[VOLATILITY\]',
    r'logger\.info\(f?".*\[TREND\]',
    r'logger\.info\(f?".*\[reload\].*FINAL',
    r'logger\.info\(f?".*\[MTF\].*Signal',
    r'logger\.info\(f?".*\[MT5\].*BARRAnueva',
    r'logger\.info\(f?".*\[DATA\].*24h',
]

def comment_line(line):
    """Comenta una línea de código"""
    indent = len(line) - len(line.lstrip())
    return ' ' * indent + '# ' + line.strip() + '\n'

def process_file(filename):
    """Procesa el archivo comentando logs"""
    try:
        with open(filename, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        commented_count = 0
        for i, line in enumerate(lines):
            for pattern in PATTERNS_TO_COMMENT:
                if re.search(pattern, line, re.IGNORECASE):
                    if not line.lstrip().startswith('#'):  # No comentar si ya está comentado
                        lines[i] = comment_line(line)
                        commented_count += 1
                        print(f"Línea {i+1}: Comentada")
                        break
        
        # Escribir archivo modificado
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"\n✓ Total líneas comentadas: {commented_count}")
        return commented_count
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == '__main__':
    count = process_file('boteddver1.py')
    sys.exit(0 if count > 0 else 1)
