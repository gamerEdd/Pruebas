# Control de Direcciones de Trading

## ⭐ Nueva Funcionalidad

Ahora puedes controlar qué direcciones están habilitadas para abrir operaciones:
- **ALLOW_BUY**: Habilitar/Deshabilitar aperturas BUY
- **ALLOW_SELL**: Habilitar/Deshabilitar aperturas SELL

## Configuración

### Variables de Configuración

```python
'ALLOW_BUY': tk.BooleanVar(value=True)    # True = BUY habilitado
'ALLOW_SELL': tk.BooleanVar(value=True)   # True = SELL habilitado
```

### Casos de Uso

| Caso | ALLOW_BUY | ALLOW_SELL | Resultado |
|------|-----------|-----------|-----------|
| Normal | True | True | ✅ Abrir BUY y SELL |
| Solo BUY | True | False | 📈 Solo BUY |
| Solo SELL | False | True | 📉 Solo SELL |
| Parado | False | False | 🛑 Sin aperturas |

## Función de Validación

### `_is_direction_allowed(direction)`

Valida si se permite abrir en una dirección específica.

**Parámetros:**
- `direction` (str): 'BUY' o 'SELL'

**Retorna:**
- `bool`: True si se permite, False si está deshabilitada

**Ejemplo:**

```python
# Antes de abrir una operación, validar:
if not self._is_direction_allowed('BUY'):
    self.add_log("🚫 BUY deshabilitado. Operación cancelada.", 'warning')
    return False

# O para SELL:
if self._is_direction_allowed('SELL'):
    # Abrir operación SELL
    ...
```

## Integración en Código Existente

### Patrón de Integración

Donde actualmente tienes lógica de apertura:

```python
# ANTES:
if direction == 'BUY':
    result = mt5.order_send(request)
    
# DESPUÉS:
if direction == 'BUY' and self._is_direction_allowed('BUY'):
    result = mt5.order_send(request)
elif direction == 'BUY':
    self.add_log(f"🚫 {direction} deshabilitado por configuración", 'info')
    return False
```

### Ejemplo Completo

```python
def abrir_operacion(self, symbol, direction, volume, tp, sl):
    """Abrir operación con validación de dirección."""
    
    # ⭐ Validar que la dirección está permitida
    if not self._is_direction_allowed(direction):
        self.add_log(f"🚫 {direction} está deshabilitado. Configuración: ALLOW_BUY={self._safe_get('ALLOW_BUY', True)}, ALLOW_SELL={self._safe_get('ALLOW_SELL', True)}", 'warning')
        return False
    
    # Continuar con la lógica de apertura...
    order_type = mt5.ORDER_TYPE_BUY if direction == 'BUY' else mt5.ORDER_TYPE_SELL
    
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': volume,
        'type': order_type,
        'price': mt5.symbol_info_tick(symbol).ask if direction == 'BUY' else mt5.symbol_info_tick(symbol).bid,
        'tp': tp,
        'sl': sl,
        'magic': 123456,
        'comment': f'Operación {direction} - Control Activo'
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        self.add_log(f"✅ {direction} abierto exitosamente", 'success')
        return True
    else:
        self.add_log(f"❌ Error abriendo {direction}: {result.comment}", 'error')
        return False
```

## Cómo Activar Desde la UI

Necesitas agregar checkboxes en la interfaz:

```python
# Dentro de create_widgets() o el frame de configuración:

frame_direcciones = tk.LabelFrame(frame_config, text="Control de Direcciones", bg=bg_color, fg=fg_color)
frame_direcciones.pack(fill='x', padx=5, pady=5)

# Checkbox ALLOW_BUY
tk.Checkbutton(
    frame_direcciones,
    text="✅ Permitir BUY",
    variable=self.config['ALLOW_BUY'],
    bg=bg_color,
    fg=fg_color,
    selectcolor='#059669'
).pack(anchor='w', padx=10, pady=5)

# Checkbox ALLOW_SELL
tk.Checkbutton(
    frame_direcciones,
    text="✅ Permitir SELL",
    variable=self.config['ALLOW_SELL'],
    bg=bg_color,
    fg=fg_color,
    selectcolor='#dc2626'
).pack(anchor='w', padx=10, pady=5)
```

## Notas Importantes

⚠️ **Recordar integrar la validación en TODOS los puntos donde se abren operaciones:**
- Operaciones normales (scheduler)
- Operaciones forzadas (forced_open)
- Operaciones rápidas (rapid_ops)
- Aperturas de reversión
- Cualquier otra lógica de apertura

✅ **Uso Recomendado:**
- Desactivar SELL si solo quieres trading alcista
- Desactivar BUY si solo quieres trading bajista
- Desactivar ambas para pausar sin afectar otras funciones
- Usar con TRADE_INTERVAL y FORCED_OPEN_MINUTES para máximo control

## Estado Actual

✅ **Variables de configuración:** Agregadas
✅ **Función de validación:** Implementada
✅ **Compilación:** EXITOSA

⏳ **Próximo paso:** Integrar validación en funciones de apertura (búsqueda manual requerida)
