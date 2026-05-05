#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

# Leer build_bot_exe.py
with open('build_bot_exe.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar todos los caracteres especiales Unicode problemáticos
replacements = {
    '✓': '[OK]',
    '✗': '[FAIL]',
    '⭐': '[STAR]',
    '【': '[',
    '】': ']',
}

for old_char, new_char in replacements.items():
    content = content.replace(old_char, new_char)

# Escribir back
with open('build_bot_exe.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Caracteres especiales corregidos en build_bot_exe.py')
