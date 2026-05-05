# -*- coding: utf-8 -*-
"""
Panel de Dashboard Dinámico para Análisis de Operaciones en Tiempo Real
Actualiza labels sin saturar el log de actividad
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

class DynamicOperationsPanel:
    """Panel dinámico que muestra análisis de operaciones en tiempo real"""
    
    def __init__(self, parent):
        self.parent = parent
        self.parent.configure(bg='#1e293b')
        
        # Frame principal con scroll
        main_frame = tk.Frame(parent, bg='#1e293b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title = tk.Label(main_frame, text="📊 ANÁLISIS EN VIVO", 
                        font=('Arial', 14, 'bold'), bg='#1e293b', fg='#34d399')
        title.pack(fill='x', pady=(0, 10))
        
        # Panel resumen superior
        self.create_summary_section(main_frame)
        
        # Panel de operaciones abiertas
        self.create_operations_section(main_frame)
        
        # Panel de métricas
        self.create_metrics_section(main_frame)
        
    def create_summary_section(self, parent):
        """Crear sección de resumen"""
        summary_frame = tk.LabelFrame(parent, text="Resumen General", 
                                     bg='#334155', fg='#f1f5f9',
                                     font=('Arial', 10, 'bold'), padx=10, pady=10)
        summary_frame.pack(fill='x', pady=(0, 10))
        
        # Grid para el resumen
        grid_frame = tk.Frame(summary_frame, bg='#334155')
        grid_frame.pack(fill='x', expand=True)
        
        # Fila 1: Operaciones abiertas
        tk.Label(grid_frame, text="📋 Operaciones Abiertas:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.lbl_open_positions = tk.Label(grid_frame, text="0/5", 
                                          font=('Arial', 9, 'bold'), bg='#334155', fg='#60a5fa')
        self.lbl_open_positions.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Fila 2: Ganancias/Pérdidas
        tk.Label(grid_frame, text="💰 Ganancias:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.lbl_profits = tk.Label(grid_frame, text="$0.00", 
                                   font=('Arial', 9, 'bold'), bg='#334155', fg='#34d399')
        self.lbl_profits.grid(row=0, column=3, sticky='w', padx=5, pady=5)
        
        # Fila 3: Pérdidas
        tk.Label(grid_frame, text="📉 Pérdidas:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=0, column=4, sticky='w', padx=5, pady=5)
        self.lbl_losses = tk.Label(grid_frame, text="$0.00", 
                                  font=('Arial', 9, 'bold'), bg='#334155', fg='#f87171')
        self.lbl_losses.grid(row=0, column=5, sticky='w', padx=5, pady=5)
        
        # Fila 4: Balance neto
        tk.Label(grid_frame, text="📊 Neto:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.lbl_net = tk.Label(grid_frame, text="$0.00", 
                               font=('Arial', 9, 'bold'), bg='#334155', fg='#60a5fa')
        self.lbl_net.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Última actualización
        tk.Label(grid_frame, text="🕐 Última actualización:", 
                font=('Arial', 8), bg='#334155', fg='#94a3b8').grid(row=1, column=2, columnspan=4, sticky='w', padx=5, pady=5)
        self.lbl_timestamp = tk.Label(grid_frame, text="--:--:--", 
                                     font=('Arial', 8), bg='#334155', fg='#64748b')
        self.lbl_timestamp.grid(row=1, column=5, sticky='w', padx=5, pady=5)
        
    def create_operations_section(self, parent):
        """Crear sección de operaciones detalladas"""
        ops_frame = tk.LabelFrame(parent, text="Operaciones Abiertas Detalladas", 
                                 bg='#334155', fg='#f1f5f9',
                                 font=('Arial', 10, 'bold'), padx=10, pady=10)
        ops_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Frame con scroll
        canvas_frame = tk.Frame(ops_frame, bg='#334155')
        canvas_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(canvas_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.operations_canvas = tk.Canvas(canvas_frame, bg='#1e293b', 
                                          highlightthickness=0, yscrollcommand=scrollbar.set)
        self.operations_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.operations_canvas.yview)
        
        self.operations_frame = tk.Frame(self.operations_canvas, bg='#1e293b')
        self.operations_canvas.create_window((0, 0), window=self.operations_frame, anchor='nw')
        
        # Placeholder
        self.lbl_no_positions = tk.Label(self.operations_frame, 
                                        text="Sin operaciones abiertas", 
                                        font=('Arial', 10), bg='#1e293b', fg='#94a3b8')
        self.lbl_no_positions.pack(pady=20)
        
        self.operations_list = []
        
    def create_metrics_section(self, parent):
        """Crear sección de métricas del mercado"""
        metrics_frame = tk.LabelFrame(parent, text="Métricas del Mercado", 
                                     bg='#334155', fg='#f1f5f9',
                                     font=('Arial', 10, 'bold'), padx=10, pady=10)
        metrics_frame.pack(fill='x')
        
        # Grid para métricas
        metrics_grid = tk.Frame(metrics_frame, bg='#334155')
        metrics_grid.pack(fill='x', expand=True)
        
        # Volatilidad
        tk.Label(metrics_grid, text="⚡ Volatilidad:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.lbl_volatility = tk.Label(metrics_grid, text="NORMAL", 
                                      font=('Arial', 9, 'bold'), bg='#334155', fg='#fbbf24')
        self.lbl_volatility.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Tendencia
        tk.Label(metrics_grid, text="📈 Tendencia:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.lbl_trend = tk.Label(metrics_grid, text="NEUTRAL", 
                                 font=('Arial', 9, 'bold'), bg='#334155', fg='#a78bfa')
        self.lbl_trend.grid(row=0, column=3, sticky='w', padx=5, pady=5)
        
        # Win Rate
        tk.Label(metrics_grid, text="🎯 Win Rate:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.lbl_winrate = tk.Label(metrics_grid, text="0%", 
                                   font=('Arial', 9, 'bold'), bg='#334155', fg='#34d399')
        self.lbl_winrate.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Precio actual
        tk.Label(metrics_grid, text="💵 Precio Actual:", 
                font=('Arial', 9), bg='#334155', fg='#cbd5e1').grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.lbl_price = tk.Label(metrics_grid, text="0.00000", 
                                 font=('Arial', 9, 'bold'), bg='#334155', fg='#60a5fa')
        self.lbl_price.grid(row=1, column=3, sticky='w', padx=5, pady=5)
        
    def update_summary(self, open_count, max_positions, total_profit, total_loss, positions_data=None):
        """Actualiza el resumen general"""
        try:
            # Operaciones abiertas
            self.lbl_open_positions.config(text=f"{open_count}/{max_positions}")
            
            # Ganancias y pérdidas
            self.lbl_profits.config(text=f"${total_profit:.2f}")
            if total_profit > 0:
                self.lbl_profits.config(fg='#34d399')
            elif total_profit < 0:
                self.lbl_profits.config(fg='#fbbf24')
            
            self.lbl_losses.config(text=f"${total_loss:.2f}")
            
            # Neto
            net = total_profit - total_loss
            self.lbl_net.config(text=f"${net:.2f}")
            if net > 0:
                self.lbl_net.config(fg='#34d399')
            elif net < 0:
                self.lbl_net.config(fg='#f87171')
            else:
                self.lbl_net.config(fg='#60a5fa')
            
            # Timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.lbl_timestamp.config(text=timestamp)
            
        except Exception as e:
            print(f"Error actualizando resumen: {e}")
    
    def update_operations(self, positions_data):
        """Actualiza la lista de operaciones abiertas"""
        try:
            # Limpiar canvas anterior
            for widget in self.operations_frame.winfo_children():
                widget.destroy()
            self.operations_list = []
            
            if not positions_data or len(positions_data) == 0:
                self.lbl_no_positions = tk.Label(self.operations_frame, 
                                                text="Sin operaciones abiertas", 
                                                font=('Arial', 10), bg='#1e293b', fg='#94a3b8')
                self.lbl_no_positions.pack(pady=20)
                self.operations_canvas.configure(scrollregion=self.operations_canvas.bbox('all'))
                return
            
            # Crear widget para cada posición
            for pos in positions_data:
                pos_frame = tk.Frame(self.operations_frame, bg='#0f172a', relief='flat', borderwidth=1)
                pos_frame.pack(fill='x', pady=5, padx=0)
                
                # Encabezado: Ticket y dirección
                header_frame = tk.Frame(pos_frame, bg='#0f172a')
                header_frame.pack(fill='x', padx=10, pady=(5, 0))
                
                ticket_text = f"#{pos.get('ticket', 'N/A')} {pos.get('direction', 'N/A')}"
                price_text = f"@ {pos.get('open_price', 0):.5f}"
                profit_text = f"${pos.get('profit', 0):.2f}"
                
                profit_color = '#34d399' if pos.get('profit', 0) > 0 else ('#f87171' if pos.get('profit', 0) < 0 else '#60a5fa')
                
                tk.Label(header_frame, text=ticket_text, font=('Arial', 9, 'bold'), 
                        bg='#0f172a', fg='#f1f5f9').pack(side='left')
                tk.Label(header_frame, text=price_text, font=('Arial', 8), 
                        bg='#0f172a', fg='#cbd5e1').pack(side='left', padx=(10, 0))
                tk.Label(header_frame, text=profit_text, font=('Arial', 9, 'bold'), 
                        bg='#0f172a', fg=profit_color).pack(side='right')
                
                # Detalles
                details_frame = tk.Frame(pos_frame, bg='#0f172a')
                details_frame.pack(fill='x', padx=10, pady=(3, 5))
                
                details_text = f"Vol: {pos.get('volume', 0)} | TP: {pos.get('tp', 0):.5f} | SL: {pos.get('sl', 0):.5f}"
                tk.Label(details_frame, text=details_text, font=('Arial', 8), 
                        bg='#0f172a', fg='#94a3b8').pack(anchor='w')
                
                self.operations_list.append(pos_frame)
            
            # Actualizar región de scroll con delay para que Tk calcule bien
            self.operations_frame.update_idletasks()
            self.operations_canvas.configure(scrollregion=self.operations_canvas.bbox('all'))
            
        except Exception as e:
            print(f"Error actualizando operaciones: {e}")
    
    def update_metrics(self, volatility, trend, winrate, current_price):
        """Actualiza las métricas del mercado"""
        try:
            # Volatilidad
            self.lbl_volatility.config(text=volatility)
            vol_colors = {'BAJA': '#34d399', 'NORMAL': '#fbbf24', 'ALTA': '#f87171'}
            self.lbl_volatility.config(fg=vol_colors.get(volatility, '#fbbf24'))
            
            # Tendencia
            self.lbl_trend.config(text=trend)
            trend_colors = {'ALCISTA': '#34d399', 'NEUTRAL': '#a78bfa', 'BAJISTA': '#f87171'}
            self.lbl_trend.config(fg=trend_colors.get(trend, '#a78bfa'))
            
            # Win Rate
            self.lbl_winrate.config(text=f"{winrate:.1f}%")
            if winrate > 50:
                self.lbl_winrate.config(fg='#34d399')
            elif winrate < 50:
                self.lbl_winrate.config(fg='#f87171')
            else:
                self.lbl_winrate.config(fg='#fbbf24')
            
            # Precio
            self.lbl_price.config(text=f"{current_price:.5f}")
            
        except Exception as e:
            print(f"Error actualizando métricas: {e}")
