# DIAGNÓSTICO Y CORRECCIÓN DEFINITIVA - configuration_panel.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict, Set
import logging


class ConfigurationPanel(ttk.Frame):
    """Panel de configuración CORREGIDO para capturar valores correctamente."""
    
    def __init__(self, parent, catalog: List, all_techniques: List[str], 
                 on_optimize_callback: Callable):
        super().__init__(parent, padding="15")
        
        self.catalog = catalog
        self.all_techniques = all_techniques
        self.on_optimize_callback = on_optimize_callback
        self.all_stations = []
        
        # Variables de configuración - CAMBIO CRÍTICO: usar StringVar correctamente
        self.vars = {}
        self.config_vars = {}
        self.technique_vars = {}
        self.station_vars = {}
        
        # Presets por tipo de establecimiento
        self.establishment_presets = {
            'casual': {'description': 'Restaurante Casual - Enfoque en rapidez y precios', 'target_margin': 30, 'max_cost': 200},
            'elegante': {'description': 'Restaurante Elegante - Enfoque en calidad', 'target_margin': 50, 'max_cost': 350},
            'comida_rapida': {'description': 'Comida Rápida - Máxima eficiencia', 'target_margin': 40, 'max_cost': 150}
        }
        
        self._create_interface()
        self._set_default_values()
    
    def _create_interface(self):
        """Crea la interfaz del panel de configuración."""
        left_column = ttk.Frame(self)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_column = ttk.Frame(self)
        right_column.pack(side="left", fill="both", expand=True)
        
        self._create_restaurant_constraints_section(left_column)
        self._create_stations_section(left_column)
        self._create_optimization_section(right_column)
        self._create_techniques_section(right_column)
        self._create_optimize_button()
    
    def _create_restaurant_constraints_section(self, parent):
        """Crear sección de restricciones del restaurante."""
        frame = ttk.LabelFrame(parent, text="Restricciones del Restaurante", padding=15)
        frame.pack(fill="x", pady=(0, 10))
        
        # NÚMERO DE PLATOS - CORRECCIÓN CRÍTICA
        ttk.Label(frame, text="Número deseado de opciones en el menú:", 
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        
        # IMPORTANTE: Inicializar con valor por defecto explícito
        self.vars["num_dishes"] = tk.StringVar()
        self.vars["num_dishes"].set("20")  # Valor por defecto
        
        entry_dishes = ttk.Entry(frame, textvariable=self.vars["num_dishes"], width=15)
        entry_dishes.grid(row=0, column=1, sticky="w")
        
        # PRESUPUESTO MÁXIMO - CORRECCIÓN CRÍTICA
        ttk.Label(frame, text="Presupuesto máximo de costo por plato (MXN):", 
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        
        self.vars["max_cost_per_dish"] = tk.StringVar()
        self.vars["max_cost_per_dish"].set("200")  # Valor por defecto
        
        entry_cost = ttk.Entry(frame, textvariable=self.vars["max_cost_per_dish"], width=15)
        entry_cost.grid(row=1, column=1, sticky="w")
        
        # PERSONAL DISPONIBLE - CORRECCIÓN CRÍTICA  
        ttk.Label(frame, text="Personal disponible (cocineros):", 
                 font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        
        self.vars["num_chefs"] = tk.StringVar()
        self.vars["num_chefs"].set("8")  # Valor por defecto
        
        entry_chefs = ttk.Entry(frame, textvariable=self.vars["num_chefs"], width=15)
        entry_chefs.grid(row=2, column=1, sticky="w")
    
    def _create_stations_section(self, parent):
        """Crea la sección de estaciones de trabajo."""
        frame = ttk.LabelFrame(parent, text="Estaciones de Trabajo Disponibles", padding=15)
        frame.pack(fill="both", expand=True, pady=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(button_frame, text="Seleccionar Todas", command=self._select_all_stations).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Deseleccionar Todas", command=self._deselect_all_stations).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Configuración Básica", command=self._select_basic_stations).pack(side="left")
        
        canvas = tk.Canvas(frame, height=120)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.stations_container = scrollable_frame
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_optimization_section(self, parent):
        """Crea la sección de parámetros de optimización."""
        frame = ttk.LabelFrame(parent, text="Parámetros de Optimización", padding=15)
        frame.pack(fill="x", pady=(0, 10))
        
        # MARGEN DE GANANCIA
        ttk.Label(frame, text="Porcentaje mínimo de margen de ganancia (%):", 
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        
        self.config_vars["min_profit_margin"] = tk.StringVar()
        self.config_vars["min_profit_margin"].set("30")  # Valor por defecto
        
        entry_margin = ttk.Entry(frame, textvariable=self.config_vars["min_profit_margin"], width=15)
        entry_margin.grid(row=0, column=1, sticky="w")
        
        # TEMPORADA
        ttk.Label(frame, text="Temporada del año:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        
        self.config_vars["season"] = tk.StringVar(value="Todo el año")
        season_combo = ttk.Combobox(frame, textvariable=self.config_vars["season"],
                                  values=['Todo el año', 'Primavera', 'Verano', 'Otoño', 'Invierno'],
                                  state="readonly", width=18)
        season_combo.grid(row=1, column=1, sticky="w")
        
        # TIPO DE ESTABLECIMIENTO
        ttk.Label(frame, text="Tipo de establecimiento:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        
        self.config_vars["establishment_type"] = tk.StringVar(value="casual")
        establishment_combo = ttk.Combobox(frame, textvariable=self.config_vars["establishment_type"],
                                         values=['casual', 'elegante', 'comida_rapida'],
                                         state="readonly", width=18)
        establishment_combo.grid(row=2, column=1, sticky="w")
        establishment_combo.bind('<<ComboboxSelected>>', self._on_establishment_change)
        
        # Descripción
        self.establishment_description = ttk.Label(frame, text="", font=("Segoe UI", 9, "italic"),
                                                 foreground="#2c5282", wraplength=400)
        self.establishment_description.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        
        # Información del algoritmo
        info_frame = ttk.LabelFrame(parent, text="Información del Algoritmo", padding=10)
        info_frame.pack(fill="x", pady=(10, 0))
        
        info_text = """ALGORITMO GENÉTICO MULTI-OBJETIVO

Optimiza simultáneamente 7 variables:
• Margen de ganancia total del menú
• Tiempo promedio de preparación por pedido  
• Balance nutricional y tipos de dieta
• Variedad gastronómica y cultural
• Eficiencia de ingredientes (minimizar desperdicio)
• Distribución equilibrada de carga de trabajo
• Satisfacción proyectada del cliente

Configuración del Algoritmo:
• Población: 150 individuos por generación
• Evolución: 250 generaciones con elitismo
• Estrategias múltiples de cruzamiento y mutación"""
        
        ttk.Label(info_frame, text=info_text, font=("Segoe UI", 8), justify="left", wraplength=400).pack(anchor="w")
    
    def _create_techniques_section(self, parent):
        """Crea la sección de técnicas culinarias."""
        frame = ttk.LabelFrame(parent, text="Técnicas Culinarias Disponibles", padding=15)
        frame.pack(fill="both", expand=True, pady=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(button_frame, text="Seleccionar Todas", command=self._select_all_techniques).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Deseleccionar Todas", command=self._deselect_all_techniques).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Técnicas Básicas", command=self._select_basic_techniques).pack(side="left")
        
        canvas = tk.Canvas(frame, height=120)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        techniques_per_column = 6
        col = 0
        row = 0
        
        for i, technique in enumerate(sorted(self.all_techniques)):
            if i > 0 and i % techniques_per_column == 0:
                col += 1
                row = 0
            
            self.technique_vars[technique] = tk.BooleanVar(value=False)
            ttk.Checkbutton(scrollable_frame, text=technique, 
                          variable=self.technique_vars[technique]).grid(
                row=row, column=col, sticky="w", padx=15, pady=2)
            row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_optimize_button(self):
        """Crea el botón de optimización."""
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom", fill="x", pady=15)
        
        optimize_button = ttk.Button(button_frame, text="OPTIMIZAR MENÚ DEL RESTAURANTE",
                                   command=self._run_optimization, style="Accent.TButton")
        optimize_button.pack(pady=10, ipady=15, fill="x")
        
        ttk.Label(button_frame, text="La optimización puede tomar 1-2 minutos",
                 font=("Segoe UI", 8, "italic"), foreground="#666666").pack()
    
    def _set_default_values(self):
        """Establece valores por defecto."""
        self._on_establishment_change()
        self._select_basic_techniques()
    
    def set_available_stations(self, stations: List[str]):
        """Establece las estaciones disponibles y crea los checkboxes."""
        self.all_stations = stations
        
        for widget in self.stations_container.winfo_children():
            widget.destroy()
        
        stations_per_column = 5
        col = 0
        row = 0
        
        for i, station in enumerate(sorted(self.all_stations)):
            if i > 0 and i % stations_per_column == 0:
                col += 1
                row = 0
            
            self.station_vars[station] = tk.BooleanVar(value=False)
            ttk.Checkbutton(self.stations_container, text=station,
                          variable=self.station_vars[station]).grid(
                row=row, column=col, sticky="w", padx=15, pady=2)
            row += 1
        
        self._select_basic_stations()
    
    def _on_establishment_change(self, event=None):
        """Maneja el cambio de tipo de establecimiento."""
        establishment_type = self.config_vars["establishment_type"].get()
        preset = self.establishment_presets.get(establishment_type, {})
        
        description = preset.get('description', '')
        self.establishment_description.config(text=description)
        
        if 'target_margin' in preset:
            self.config_vars["min_profit_margin"].set(str(preset['target_margin']))
        if 'max_cost' in preset:
            self.vars["max_cost_per_dish"].set(str(preset['max_cost']))
    
    def _select_all_techniques(self):
        for var in self.technique_vars.values():
            var.set(True)
    
    def _deselect_all_techniques(self):
        for var in self.technique_vars.values():
            var.set(False)
    
    def _select_basic_techniques(self):
        basic_techniques = {'Plancha', 'Hervido', 'Salteado', 'Horneado', 'Freír', 'Guisar', 'Amasar', 'Brasear', 'Caramelizado', 'Fermentado'}
        for technique, var in self.technique_vars.items():
            var.set(technique in basic_techniques)
    
    def _select_all_stations(self):
        for var in self.station_vars.values():
            var.set(True)
    
    def _deselect_all_stations(self):
        for var in self.station_vars.values():
            var.set(False)
    
    def _select_basic_stations(self):
        basic_stations = {'Ahumador', 'Bar de Jugos y Smoothies', 'Bebidas y Cócteles',
                         'Ensaladas y Fríos', 'Ensamblaje y Emplatado', 'Estación de Sushis',
                         'Estación de Wok y Cocina Asiática', 'Estofados y Salsas',
                         'Fritura', 'Horno y Rostizado'}
        
        for station, var in self.station_vars.items():
            var.set(station in basic_stations)
    
    def _run_optimization(self):
        """MÉTODO CRÍTICO: Recopila la configuración y ejecuta la optimización."""
        try:
            config = self._gather_configuration()
            # SIN EMOJIS para evitar errores Unicode en Windows
            logging.info("DEBUG - Configuración recopilada: {}".format(config))
            self.on_optimize_callback(config)
        except Exception as e:
            logging.error("Error al recopilar configuración: {}".format(str(e)))
            messagebox.showerror("Error de Configuración", 
                               "Error al recopilar configuración:\n{}".format(str(e)))
    
    def _gather_configuration(self) -> Dict:
        """
        MÉTODO CORREGIDO CRÍTICO: Recopila toda la configuración del panel.
        """
        logging.info("DEBUG - Iniciando recopilación de configuración...")
        
        # CONVERSIÓN SEGURA CON DEBUGGING DETALLADO
        
        # NÚMERO DE PLATOS
        try:
            num_dishes_raw = self.vars["num_dishes"].get()
            logging.info("DEBUG - Valor raw num_dishes: '{}'".format(repr(num_dishes_raw)))
            num_dishes_str = str(num_dishes_raw).strip()
            num_dishes = int(num_dishes_str) if num_dishes_str and num_dishes_str.isdigit() else 20
            logging.info("DEBUG - Número de platos convertido: {} -> {}".format(num_dishes_str, num_dishes))
        except Exception as e:
            logging.error("Error convirtiendo num_dishes: {}".format(e))
            num_dishes = 20
        
        # COSTO MÁXIMO
        try:
            cost_raw = self.vars["max_cost_per_dish"].get()
            logging.info("DEBUG - Valor raw max_cost: '{}'".format(repr(cost_raw)))
            cost_str = str(cost_raw).strip()
            max_cost_per_dish = float(cost_str) if cost_str else 200.0
            logging.info("DEBUG - Costo máximo convertido: {} -> {}".format(cost_str, max_cost_per_dish))
        except Exception as e:
            logging.error("Error convirtiendo max_cost_per_dish: {}".format(e))
            max_cost_per_dish = 200.0
        
        # NÚMERO DE COCINEROS  
        try:
            chefs_raw = self.vars["num_chefs"].get()
            logging.info("DEBUG - Valor raw num_chefs: '{}'".format(repr(chefs_raw)))
            chefs_str = str(chefs_raw).strip()
            num_chefs = int(chefs_str) if chefs_str and chefs_str.isdigit() else 8
            logging.info("DEBUG - Número de cocineros convertido: {} -> {}".format(chefs_str, num_chefs))
        except Exception as e:
            logging.error("Error convirtiendo num_chefs: {}".format(e))
            num_chefs = 8
        
        # MARGEN DE GANANCIA
        try:
            margin_raw = self.config_vars["min_profit_margin"].get()
            logging.info("DEBUG - Valor raw margin: '{}'".format(repr(margin_raw)))
            margin_str = str(margin_raw).strip()
            min_profit_margin = float(margin_str) if margin_str else 30.0
            logging.info("DEBUG - Margen convertido: {} -> {}".format(margin_str, min_profit_margin))
        except Exception as e:
            logging.error("Error convirtiendo min_profit_margin: {}".format(e))
            min_profit_margin = 30.0
        
        # OTROS VALORES
        season = self.config_vars["season"].get() or "Todo el año"
        establishment_type = self.config_vars["establishment_type"].get() or "casual"
        
        logging.info("DEBUG - Temporada: {}".format(season))
        logging.info("DEBUG - Tipo establecimiento: {}".format(establishment_type))
        
        # TÉCNICAS Y ESTACIONES
        selected_techniques = {tech for tech, var in self.technique_vars.items() if var.get()}
        selected_stations = {station for station, var in self.station_vars.items() if var.get()}
        
        logging.info("DEBUG - Técnicas seleccionadas: {} técnicas".format(len(selected_techniques)))
        logging.info("DEBUG - Estaciones seleccionadas: {} estaciones".format(len(selected_stations)))
        
        # VALIDACIÓN
        if not selected_stations:
            raise ValueError("Debe seleccionar al menos una estación de trabajo disponible")
        if not selected_techniques:
            raise ValueError("Debe seleccionar al menos una técnica culinaria")
        
        # CONFIGURACIÓN FINAL
        config = {
            'num_dishes': num_dishes,
            'max_cost_per_dish': max_cost_per_dish,
            'num_chefs': num_chefs,
            'min_profit_margin': min_profit_margin,
            'season': season,
            'establishment_type': establishment_type,
            'available_techniques': selected_techniques,
            'available_stations': selected_stations
        }
        
        logging.info("DEBUG - Configuración final exitosa")
        logging.info("DEBUG - RESUMEN FINAL: {} platos, {} cocineros, {} MXN max, {}% margen".format(
            num_dishes, num_chefs, max_cost_per_dish, min_profit_margin))
        
        return config
    
    def _create_tooltip(self, widget, text):
        """Crea un tooltip simple."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.geometry("+{}+{}".format(event.x_root+10, event.y_root+10))
            
            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief="solid", borderwidth=1, font=("Segoe UI", 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)