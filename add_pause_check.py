#!/usr/bin/env python3
# Add pause check to bot_loop

with open('boteddver1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y agregar verificación de pausa en bot_loop
old_block = """                    if time.time() < getattr(self, 'block_until', 0):
                        remaining = int(self.block_until - time.time())
                        if remaining > 0:
                            self.add_log(f"[ESPERA] Cooldown tras ganancia activo ({remaining}s restantes) - esperando...", 'info')
                        time.sleep(1)
                        continue

                    if self.total_operaciones_abiertas < self.config['MAX_SIMULTANEOUS_OPS'].get():"""

new_block = """                    if time.time() < getattr(self, 'block_until', 0):
                        remaining = int(self.block_until - time.time())
                        if remaining > 0:
                            self.add_log(f"[ESPERA] Cooldown tras ganancia activo ({remaining}s restantes) - esperando...", 'info')
                        time.sleep(1)
                        continue
                    
                    # ⭐ NUEVA VERIFICACIÓN: Pausas post-operación (ganancia/pérdida)
                    in_pause, pause_reason = self._is_in_pause(strict=True)
                    if in_pause:
                        self.add_log(f"[PAUSA] {pause_reason} - esperando para nueva operación...", 'info')
                        time.sleep(1)
                        continue

                    if self.total_operaciones_abiertas < self.config['MAX_SIMULTANEOUS_OPS'].get():"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('boteddver1.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Verificación de pausa agregada a bot_loop")
else:
    print("❌ No se encontró el bloque de código en bot_loop")
