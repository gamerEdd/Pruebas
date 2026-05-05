#!/usr/bin/env python3
# Fix script for pause_until replacements

import re

# Leer el archivo
with open('boteddver1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazo 1: Línea 7301-7302
content = content.replace(
    """                self.bot_pausado = True
                self.pause_until = time.time() + pause_seconds
                self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
                self.status_label.config(text=f"Bot Pausado por Stop Loss ({pause_seconds}s)", fg='#fbbf24')
                t = threading.Thread(target=self._loss_pause_worker, args=(pause_seconds,), daemon=True)""",
    """                self._set_pause(pause_seconds, "Pausa post-stop-loss")
                self.status_indicator.itemconfig(self.status_circle, fill='#fbbf24')
                self.status_label.config(text=f"Bot Pausado por Stop Loss ({pause_seconds}s)", fg='#fbbf24')
                t = threading.Thread(target=self._loss_pause_worker, args=(pause_seconds,), daemon=True)"""
)

# Reemplazo 2: Línea 7732-7733
content = content.replace(
    """            # FIX #16: Asegurar que bot_pausado se establece ANTES de cualquier operación de UI
            self.bot_pausado = True
            self.pause_until = time.time() + pause_seconds""",
    """ #FIX #16: Asegurar que bot_pausado se establece ANTES de cualquier operación de UI
            self._set_pause(pause_seconds, "Pausa post-objetivo")"""
)

# Escribir de vuelta
with open('boteddver1.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Reemplazos completados exitosamente")
