#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import py_compile
import sys

try:
    py_compile.compile('botiaver1.py', doraise=True)
    py_compile.compile('trend_change_detector.py', doraise=True)
    print("✅ BOTH FILES COMPILED SUCCESSFULLY")
    sys.exit(0)
except Exception as e:
    print(f"❌ COMPILE ERROR: {str(e)[:200]}")
    sys.exit(1)
