"""
Simple checker: lee `requirements.txt` y prueba importar cada paquete.
Uso: `python check_requirements.py` (ideal dentro del entorno virtual que usarás para el build)

No es 100% infalible (nombre de paquete != nombre de módulo), pero detecta dependencias faltantes comunes.
"""
import importlib
import sys
import re

def normalize_pkg_to_module(name):
    name = name.strip()
    # eliminar extras y versiones (e.g. pandas>=1.0 -> pandas)
    name = re.split('[<=>]', name)[0]
    # normalizar guiones a guion_bajo y pasar a minúsculas
    name = name.replace('-', '_').lower()

    # mapeos para paquetes cuyo nombre difiere del módulo importable
    mapping = {
        'python_binance': 'binance',
        'keras': 'keras',
    }

    if name.startswith('scikit'):
        return 'sklearn'

    return mapping.get(name, name)

def main():
    missing = []
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as fh:
            lines = [l.strip() for l in fh if l.strip() and not l.startswith('#')]
    except FileNotFoundError:
        print('No se encontró requirements.txt en el directorio actual.')
        sys.exit(2)

    for line in lines:
        pkg = normalize_pkg_to_module(line)
        try:
            importlib.import_module(pkg)
            print(f'OK: {pkg}')
        except Exception:
            print(f'MISSING: {pkg}  (original spec: "{line}")')
            missing.append((pkg, line))

    if missing:
        print('\nResumen: faltan paquetes/modulos:')
        for pkg, orig in missing:
            print(f'- {pkg}  (requirements: {orig})')
        print('\nRecomendación: activa tu entorno virtual y ejecuta `pip install -r requirements.txt`')
        sys.exit(1)
    else:
        print('\nTodas las importaciones básicas existen en el entorno actual.')

if __name__ == "__main__":
    main()
