"""
Stub minimal para `nltk` usado sólo para evitar ModuleNotFoundError
during packaging. No proporciona funcionalidad completa.

Instala el paquete real con `pip install nltk` para uso en runtime.
"""
class _Data:
    def __init__(self):
        self.path = []
    def find(self, resource_name):
        # Indicar que no existe recurso localmente
        raise LookupError(f"Resource not found: {resource_name}")

data = _Data()

def download(*args, **kwargs):
    # No-op stub
    return None

def tokenize(text):
    # Very small placeholder
    if text is None:
        return []
    return str(text).split()
