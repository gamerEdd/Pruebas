## GUÍA DE COMPILACIÓN - boteddver1.exe

### Compilación Rápida

**Opción 1: Windows (Script Batch)**
```batch
double-click BUILD_BOTEDDVER1.bat
```

**Opción 2: Terminal de Windows**
```powershell
python build_exe.py
```

---

## MÉTODOS DE COMPILACIÓN

### 1️⃣ Compilación Estándar (Recomendada)
Compila boteddver1.py a ejecutable incluendo todas las dependencias:

```bash
python build_exe.py
```

**Lo que hace:**
- ✓ Instala dependencias desde requirements.txt
- ✓ Verifica que boteddver1.py sea válido
- ✓ Incluye todos los módulos personalizados
- ✓ Copia archivos de datos (config/, mi_sesion.session, etc.)
- ✓ Genera dist/boteddver1.exe

**Tiempo:** 3-10 minutos según tu PC

---

### 2️⃣ Compilación con Consola (Para Debug)
Genera .exe que muestra ventana de consola (útil para ver errores):

```bash
python build_exe.py --console
```

---

### 3️⃣ Compilación con MetaTrader5 Integrado
Incluye archivos de MetaTrader5 en el bundle (archivo más grande):

```bash
python build_exe.py --include-mt5
```

---

### 4️⃣ Compilación sin Instalación (Si ya tienes todo instalado)
Omite la instalación de dependencias (más rápido):

```bash
python build_exe.py --no-install
```

---

### 5️⃣ Dry-Run (Solo mostrar comando, sin compilar)
Muestra el comando PyInstaller que se ejecutaría sin hacerlo:

```bash
python build_exe.py --dry-run
```

---

## OPCIONES AVANZADAS

### Instalar Wheels Locales

Si tienes un archivo .whl (p.ej. MetaTrader5) descargado localmente:

```bash
python build_exe.py --wheel C:\path\to\MetaTrader5.whl
```

Para instalar múltiples wheels:
```bash
python build_exe.py --wheel wheel1.whl --wheel wheel2.whl
```

Para instalar todos los .whl de una carpeta:
```bash
python build_exe.py --wheel-dir C:\my_wheels
```

---

### Combinaciones Útiles

**Debug + Consola:**
```bash
python build_exe.py --console --no-install
```

**MetaTrader5 + Console:**
```bash
python build_exe.py --console --include-mt5
```

**Wheels locales + MT5:**
```bash
python build_exe.py --wheel C:\MetaTrader5.whl --include-mt5
```

---

## REQUISITOS PREVIOS

### Python 3.8+
```bash
python --version
```

### Dependencias (instaladas automáticamente)

El script instala automáticamente desde `requirements.txt`:
- numpy
- pandas
- xgboost
- scipy
- scikit-learn
- PyInstaller
- MetaTrader5 (opcional - puede requerir instalación manual)
- Y todas las librerías personalizadas del bot

### MetaTrader5 (Especial)

**Si PyInstaller falla por MetaTrader5:**

1. Descarga la rueda (.whl) oficial desde:
   https://www.mql5.com/en/docs/integration/python_metatrader5

2. Instala manualmente:
```bash
python -m pip install C:\path\to\MetaTrader5.whl
```

3. O usa este script con la rueda:
```bash
python build_exe.py --wheel C:\path\to\MetaTrader5.whl
```

---

## ARCHIVO GENERADO

**Ubicación:** `dist/boteddver1.exe`

**Tamaño:** ~150-300 MB (depende de opciones)

**Contiene:**
- boteddver1.py compilado a bytecode
- Todas las dependencias Python
- Archivos de configuración (config/)
- Sesión guardada (mi_sesion.session)
- Modelos y datos si se incluyen

---

## CÓMO EJECUTAR

### Desde Explorador de Archivos
```
Doble-click en: dist/boteddver1.exe
```

### Desde Terminal
```bash
dist\boteddver1.exe
```

### Desde PowerShell
```powershell
./dist/boteddver1.exe
```

---

## SOLUCIÓN DE PROBLEMAS

### "PyInstaller not found"
```bash
python -m pip install pyinstaller
python build_exe.py
```

### "MetaTrader5 not found"
Opción A: Instalar rueda manualmente
```bash
python build_exe.py --wheel <ruta_wheel>
```

Opción B: Omitir MT5 (si no lo necesitas en el .exe):
```bash
python build_exe.py
```

### "ModuleNotFoundError: No module named 'X'"

Si faltan módulos personalizados (buy_specialist_ai, etc.):

1. Verifica que existan en el directorio actual
2. Compila con --console para ver el error específico:
```bash
python build_exe.py --console
```

3. O omite el install:
```bash
python build_exe.py --no-install --console
```

### "dist/boteddver1.exe no encontrado"

1. Revisa los errores de PyInstaller en la salida
2. Asegúrate que boteddver1.py tenga sintaxis válida:
```bash
python -m py_compile boteddver1.py
```

3. Intenta con --console para ver más detalles:
```bash
python build_exe.py --console
```

---

## VENTAJAS DEL build_exe.py MEJORADO

✅ **Automático**: Instala todo lo necesario automáticamente
✅ **Completo**: Incluye todos los módulos del bot
✅ **Robusto**: Manejo de errores mejorado
✅ **Flexible**: Múltiples opciones de compilación
✅ **Diagnostico**: Mensajes claros y solución de problemas
✅ **Modular**: Fácil de mantener y actualizar

---

## NOTAS IMPORTANTES

1. **Primera compilación**: Tarda más porque instala dependencias
2. **Compilaciones posteriores**: Son más rápidas (--no-install)
3. **Tamaño del .exe**: ~200 MB es normal para aplicaciones Python con muchas librerías
4. **Permisos**: Asegúrate de tener permisos de escritura en el directorio
5. **Antivirus**: Algunos antivirus pueden ralentizar la compilación

---

## VERIFICACIÓN RÁPIDA

Después de compilar, verifica que el .exe funcione:

```bash
dist\boteddver1.exe --help
```

Si muestra la ayuda del bot, todo está correcto ✓

---

**¿Preguntas?** Revisa los mensajes de error en la compilación o consulta:
- boteddver1.py: código principal del bot
- requirements.txt: dependencias
- build_exe.py: configuración de PyInstaller
