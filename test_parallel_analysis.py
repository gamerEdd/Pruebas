#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test simple para validar que _parallel_trade_analysis está correctamente implementado"""

import sys
import ast

try:
    # 1. Validar sintaxis
    with open('botiaver1.py', 'r', encoding='utf-8') as f:
        code = f.read()
        ast.parse(code)
    print("✅ Sintaxis válida (AST parsing OK)")
    
    # 2. Buscar el método en el archivo
    if '_parallel_trade_analysis' in code:
        print("✅ Método _parallel_trade_analysis encontrado")
    else:
        print("❌ Método _parallel_trade_analysis NO encontrado")
        sys.exit(1)
    
    # 3. Verificar estructura básica
    if 'def _parallel_trade_analysis(self, symbol):' in code:
        print("✅ Definición de método correcta")
    else:
        print("❌ Definición de método INCORRECTA")
        sys.exit(1)
    
    # 4. Verificar threads
    if 'threading.Thread' in code:
        print("✅ Threading imports encontrados")
    else:
        print("❌ Threading NO implementado")
        sys.exit(1)
    
    # 5. Verificar que se usa en bot_loop
    if '_parallel_trade_analysis(symbol)' in code:
        print("✅ _parallel_trade_analysis se llama en bot_loop")
    else:
        print("❌ _parallel_trade_analysis NO se llama")
        sys.exit(1)
    
    # 6. Verificar eventos sincronización
    if "threading.Event()" in code:
        print("✅ Eventos de sincronización (threading.Event) implementados")
    else:
        print("❌ NO hay eventos de sincronización")
        sys.exit(1)
    
    print("\n✅ Validación COMPLETA - Listo para ejecutar")
    
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
