#!/usr/bin/env python
# -*- coding: utf-8 -*-
import py_compile
import sys

try:
    py_compile.compile('botiaver1.py', doraise=True)
    print("✅ COMPILATION SUCCESS")
    sys.exit(0)
except Exception as e:
    print(f"❌ COMPILATION ERROR: {e}")
    sys.exit(1)
