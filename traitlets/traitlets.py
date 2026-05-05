"""
Submodule providing minimal traitlets API needed to satisfy imports during
PyInstaller analysis. Not a full implementation; install real `traitlets`
for production use.
"""
class HasTraits:
    def __init__(self, *args, **kwargs):
        pass

def observe(*args, **kwargs):
    def _decorator(f):
        return f
    return _decorator

class TraitError(Exception):
    pass
