"""
Stub minimal para el paquete `findlibs`.
Permite evitar ModuleNotFoundError durante el proceso de empaquetado
cuando no es posible instalar el paquete real desde PyPI.

NOTA: esto es un stub temporal. Si tu aplicación necesita la funcionalidad
real de `findlibs` en tiempo de ejecución, instala el paquete real.
"""
def find_library(name):
    """Intentar localizar una librería; el stub siempre devuelve None."""
    return None

def find_libraries(*args, **kwargs):
    """Devolver lista vacía por compatibilidad con llamadas del hook."""
    return []
