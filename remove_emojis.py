#!/usr/bin/env python
"""Remove all emojis from Python files"""

import re
from pathlib import Path

# Mapa de reemplazos
emoji_map = {
    '🔄': '[ACTUALIZAR]',
    '✅': '[OK]',
    '⚠️': '[ADVERTENCIA]',
    '🔁': '[RESET]',
    '🤖': '[IA]', 
    '⚙️': '[CONFIG]',
    '📊': '[DATA]',
    '🎯': '[OBJETIVO]',
    '❌': '[ERROR]',
    '💰': '[DINERO]',
    '🛑': '[STOP]',
    '⏳': '[ESPERA]',
    '⏸️': '[PAUSA]',
    '🏁': '[FIN]',
    '📍': '[UBICACION]',
    '🟢': '[OK]',
    '🟡': '[INFO]',
    '🔵': '[SWING]',
    '🟣': '[IA]',
    '🔥': '[IMPORTANTE]',
    '1️⃣': '1',
    '2️⃣': '2',
    '3️⃣': '3',
    '4️⃣': '4',
    '5️⃣': '5',
    '💎': '[PREMIUM]',
    '🚨': '[ALERTA]',
}

def remove_emojis(text):
    """Reemplaza emojis con texto descriptivo"""
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    
    # Remover cualquier emoji restante con una regex simple
    # Patrón que detecta caracteres unicode fuera del rango ASCII normal
    text = re.sub(r'[\U0001F600-\U0001F9FF]+', '[EMOJI]', text, flags=re.UNICODE)
    text = re.sub(r'[\u2600-\u27BF]+', '[EMOJI]', text, flags=re.UNICODE)
    
    return text

def process_file(filepath):
    """Procesa un archivo y remueve emojis"""
    print(f"Procesando {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Contar emojis antes
        emojis_before = len(re.findall(r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]', content))
        
        # Reemplazar emojis
        new_content = remove_emojis(content)
        
        # Contar emojis después
        emojis_after = len(re.findall(r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]', new_content))
        
        # Guardar
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  → Emojis removidos: {emojis_before} → {emojis_after}")
        return True
        
    except Exception as e:
        print(f"  → ERROR: {e}")
        return False

if __name__ == "__main__":
    files_to_process = [
        'botiaver1.py',
        'buy_specialist_ai.py',
        'sell_specialist_ai.py',
        'decision_arbitrator_ai.py',
        'adaptive_parameters.py',
        'loss_protection_ai.py'
    ]
    
    print("="*60)
    print("REMOVIENDO EMOJIS DE ARCHIVOS PYTHON")
    print("="*60 + "\n")
    
    success_count = 0
    for filepath in files_to_process:
        if Path(filepath).exists():
            if process_file(filepath):
                success_count += 1
        else:
            print(f"Archivo no encontrado: {filepath}")
    
    print("\n" + "="*60)
    print(f"✓ {success_count}/{len(files_to_process)} archivos procesados")
    print("="*60)
