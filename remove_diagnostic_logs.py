#!/usr/bin/env python3
"""Remove repetitive diagnostic logs"""
import re

# Read file
with open('boteddver1.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Patterns to comment out (case-insensitive)
patterns_to_remove = [
    r".*\[VOLATILITY\].*",
    r".*Usando \d+ snapshots frescos.*",
    r".*\[TREND\].*Usando.*",
    r".*\[DATA\].*Análisis 24h.*",
    r".*\[MTF\].*barras cargadas.*",
    r".*\[MTF\].*Signal:.*",
    r".*\[MICROTREND/FORCED\].*",
    r".*\[FORZADA\].*DECISIÓN BRUTA.*",
    r".*\[FORZADA\].*DECISIÓN:.*",
    r".*\[FORZADA\].*Always-open.*",
    r".*\[FORZADA\].*Motivo final.*",
    r".*\[ANÁLISIS-10-VELAS\].*",
    r".*\[ANÁLISIS-FINAL-BIDIRECCIONAL\].*",
    r".*\[ANÁLISIS-4VELAS.*",
    r".*add_log\(.*\[VOLATILITY\].*",
    r".*add_log\(.*\[TREND\].*snapshots.*",
]

new_lines = []
i = 0
commented = 0

while i < len(lines):
    line = lines[i]
    
    # Check if any pattern matches
    should_comment = False
    for pattern in patterns_to_remove:
        if re.search(pattern, line, re.IGNORECASE):
            should_comment = True
            break
    
    if should_comment and not line.strip().startswith('#'):
        # Comment it out
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + '# ' + line.lstrip())
        commented += 1
    else:
        new_lines.append(line)
    
    i += 1

# Write back
with open('boteddver1.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ Commented {commented} diagnostic log lines")
