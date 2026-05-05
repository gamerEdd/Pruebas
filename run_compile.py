import py_compile, traceback
try:
    py_compile.compile(r'c:\\Users\\eddgt\\Desktop\\newtradebots\\botiaver1.py', doraise=True)
    print('compiled ok')
except Exception:
    traceback.print_exc()
