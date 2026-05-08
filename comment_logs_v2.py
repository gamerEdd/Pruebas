#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script agresivo para comentar logs diagnósticos"""

import re
import sys

# Patrones de logs a comentar (SIN el prefijo en_log o logger completo - más general)
PATTERNS_TO_COMMENT = [
    r'\[VOLATILITY\].*Factor',
    r'\[TREND\].*snapshots',
    r'\[ESPERA-INTERVALO\]',
    r'\[GLOBAL TP/SL\].*Azules',
    r'\[GLOBAL TP/SL\].*Rojas',
    r'\[MONITOR-MT5\]',
    r'\[MTF\].*Signal',
    r'\[MT5\].*BARRAnueva',
    r'\[DATA\].*24h',
    r'\[reload\].*FINAL',
    r'\[MT5-PERSIST\]',
    r'\[MT5-SYNTH-WARN\]',
    r'\[reload\]',  # Todos los reload que no sean debug
]

def should_comment(line):
    """Verifica si una línea debe ser comentada"""
    # No comentar si ya está comentado
    if line.lstrip().startswith('#'):
        return False
    
    # Verifica patrones
    for pattern in PATTERNS_TO_COMMENT:
        if re.search(pattern, line, re.IGNORECASE):
            # Verifica que sea un logger/add_log call
            if 'logger.info' in line or 'add_log' in line or 'logger.debug' in line or 'logger.warning' in line:
                return True
    
    return False

def comment_line(line):
    """Comenta una línea de código"""
    indent = len(line) - len(line.lstrip())
    return ' ' * indent + '# ' + line.lstrip()

def process_file(filename):
    """Procesa el archivo comentando logs"""
    try:
        with open(filename, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        commented_count = 0
        modified_lines = []
        
        for i, line in enumerate(lines):
            if should_comment(line):
                modified_lines.append(comment_line(line))
                commented_count += 1
                # Print primeros 20
                if commented_count <= 20:
                    print(f"Línea {i+1}: {line.strip()[:80]}")
            else:
                modified_lines.append(line)
        
        # Escribir archivo modificado
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        
        print(f"\n✓ Total líneas comentadas: {commented_count}")
        return commented_count
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    count = process_file('boteddver1.py')
    sys.exit(0 if count > 0 else 1)
