#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para el Panel de Análisis en Vivo
Simula operaciones abiertas para verificar que el panel se actualiza correctamente
"""

import tkinter as tk
from dynamic_dashboard import DynamicOperationsPanel
import random
from datetime import datetime

class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Test - Panel de Análisis en Vivo")
        self.root.geometry("1000x800")
        self.root.configure(bg='#1e293b')
        
        # Crear el panel
        self.panel = DynamicOperationsPanel(root)
        
        # Botones de prueba
        btn_frame = tk.Frame(root, bg='#1e293b')
        btn_frame.pack(fill='x', padx=10, pady=10, side='bottom')
        
        tk.Button(btn_frame, text="✅ Simular 2 Operaciones", command=self.add_positions,
                 bg='#34d399', fg='#1e293b', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🔄 Actualizar Datos", command=self.update_random,
                 bg='#60a5fa', fg='#1e293b', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🧹 Limpiar", command=self.clear_positions,
                 bg='#f87171', fg='#1e293b', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        self.positions = []
        print("✅ App iniciada. Haz clic en los botones para probar.")
    
    def add_positions(self):
        """Agrega 2 posiciones de prueba"""
        self.positions = [
            {
                'ticket': 789139378,
                'direction': 'BUY',
                'open_price': 4708.72,
                'current_price': 4708.36,
                'volume': 0.02,
                'tp': 4711.63,
                'sl': 4656.63,
                'profit': -0.72,
                'dist_tp': 3.27,
                'dist_sl': 51.73
            },
            {
                'ticket': 789139392,
                'direction': 'SELL',
                'open_price': 4707.56,
                'current_price': 4708.36,
                'volume': 0.02,
                'tp': 4702.56,
                'sl': 4757.56,
                'profit': -3.84,
                'dist_tp': 5.80,
                'dist_sl': 49.20
            }
        ]
        
        self.panel.update_summary(
            open_count=len(self.positions),
            max_positions=5,
            total_profit=0.0,
            total_loss=4.56,
            positions_data=self.positions
        )
        
        self.panel.update_operations(self.positions)
        self.panel.update_metrics('ALTA', 'NEUTRAL', 45.5, 4708.36)
        
        print(f"✅ {len(self.positions)} operaciones agregadas")
    
    def update_random(self):
        """Actualiza los datos de forma aleatoria"""
        if not self.positions:
            print("⚠️ Primero agrega posiciones con 'Simular 2 Operaciones'")
            return
        
        # Modificar precios aleatoriamente
        for pos in self.positions:
            pos['current_price'] += random.uniform(-0.05, 0.05)
            pos['profit'] += random.uniform(-1, 1)
        
        # Actualizar totales
        total_profit = sum(p['profit'] for p in self.positions if p['profit'] > 0)
        total_loss = sum(abs(p['profit']) for p in self.positions if p['profit'] < 0)
        
        # Actualizar panel
        volatility = random.choice(['BAJA', 'NORMAL', 'ALTA'])
        trend = random.choice(['ALCISTA', 'NEUTRAL', 'BAJISTA'])
        winrate = random.uniform(30, 70)
        
        self.panel.update_summary(
            open_count=len(self.positions),
            max_positions=5,
            total_profit=total_profit,
            total_loss=total_loss
        )
        
        self.panel.update_operations(self.positions)
        self.panel.update_metrics(volatility, trend, winrate, self.positions[0]['current_price'])
        
        print(f"✅ Datos actualizados | Profit: ${total_profit:.2f} | Loss: ${total_loss:.2f}")
    
    def clear_positions(self):
        """Limpia todas las posiciones"""
        self.positions = []
        
        self.panel.update_summary(
            open_count=0,
            max_positions=5,
            total_profit=0.0,
            total_loss=0.0
        )
        
        self.panel.update_operations([])
        self.panel.update_metrics('NORMAL', 'NEUTRAL', 0.0, 0.0)
        
        print("✅ Posiciones limpidas")

if __name__ == '__main__':
    root = tk.Tk()
    app = TestApp(root)
    
    print("""
    ╔════════════════════════════════════════════════╗
    ║     Test del Panel de Análisis en Vivo        ║
    ║                                                ║
    ║  Botones:                                      ║
    ║  ✅ Simular 2 Operaciones - Carga datos demo   ║
    ║  🔄 Actualizar Datos - Modifica valores       ║
    ║  🧹 Limpiar - Remueve todas las operaciones   ║
    ║                                                ║
    ║  Si el panel se muestra correctamente,        ║
    ║  el bot está listo para usar.                 ║
    ╚════════════════════════════════════════════════╝
    """)
    
    root.mainloop()
