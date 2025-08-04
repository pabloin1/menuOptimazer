# app/ui/configuration_panel.py - VERSIÓN CORREGIDA PARA WINDOWS

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict, Set
import logging


class ConfigurationPanel(ttk.Frame):
    """Panel de configuración CORREGIDO para Windows y captura de valores."""
    
    def __init__(self, parent, catalog: List, all_techniques: List[str], 
                 on_optimize_callback: Callable):
        super().__init__(parent, padding="15")
        
        self.catalog = catalog
        self.all_techniques = all_techniques
        self.on_optimize_callback = on_optimize_callback
        self.all_stations = []
        
        # Variables de configuración
        self.vars = {}
        self.config_vars = {}
        self.technique_vars = {}
        self.station_vars = {}
        
        # Presets por tipo de establecimiento
        self.establishment_presets = {
            'casual': {'description': 'Restaurante Casual - Enfoque en rapidez y precios'},
            'elegante': {'description': 'Restaurante Elegante - Enfoque en calidad'},
            'comida_rapida': {'description': 'Comida Rápida - Máxima eficiencia'}
        }
        
        self._create_interface()
        self._initialize_with_defaults()  # CAMBIO: Método específico para defaults
    
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
        
        # NÚMERO DE PLATOS
        ttk.Label(frame, text="Número deseado de opciones en el menú:", 
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        
        self.vars["num_dishes"] = tk.StringVar()
        
        self.entry_dishes = ttk.Entry(frame, textvariable=self.vars["num_dishes"], width=15)
        self.entry_dishes.grid(row=0, column=1, sticky="w")
        
        # PRESUPUESTO MÁXIMO
        ttk.Label(frame, text="Presupuesto máximo de costo por plato (MXN):", 
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        
        self.vars["max_cost_per_dish"] = tk.StringVar()
        
        self.entry_cost = ttk.Entry(frame, textvariable=self.vars["max_cost_per_dish"], width=15)
        self.entry_cost.grid(row=1, column=1, sticky="w")
        
        # PERSONAL DISPONIBLE
        ttk.Label(frame, text="Personal disponible (cocineros):", 
                 font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        
        self.vars["num_chefs"] = tk.StringVar()
        
        self.entry_chefs = ttk.Entry(frame, textvariable=self.vars["num_chefs"], width=15)
        self.entry_chefs.grid(row=2, column=1, sticky="w")
    
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
        
        self.entry_margin = ttk.Entry(frame, textvariable=self.config_vars["min_profit_margin"], width=15)
        self.entry_margin.grid(row=0, column=1, sticky="w")
        
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
    
    def _initialize_with_defaults(self):
        """Inicializa con valores por defecto SOLO para conveniencia del usuario."""
        # ESTABLECER VALORES POR DEFECTO EN LOS WIDGETS DIRECTAMENTE
        self.entry_dishes.insert(0, "12")
        self.entry_cost.insert(0, "200")
        self.entry_chefs.insert(0, "8")
        self.entry_margin.insert(0, "30")
        
        # Actualizar descripción
        self._on_establishment_change()
    
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
        
        # Seleccionar estaciones básicas al inicio
        self._select_basic_stations()
        # Seleccionar técnicas básicas al inicio
        self._select_basic_techniques()
    
    def _on_establishment_change(self, event=None):
        """Maneja el cambio de tipo de establecimiento."""
        establishment_type = self.config_vars["establishment_type"].get()
        preset = self.establishment_presets.get(establishment_type, {})
        
        description = preset.get('description', '')
        self.establishment_description.config(text=description)
        
        logging.info(f"Tipo de establecimiento cambiado a: {establishment_type}")
    
    def _select_all_techniques(self):
        for var in self.technique_vars.values():
            var.set(True)
    
    def _deselect_all_techniques(self):
        for var in self.technique_vars.values():
            var.set(False)
    
    def _select_basic_techniques(self):
        basic_techniques = {'Plancha', 'Hervido', 'Salteado', 'Horneado', 'Freír', 'Guisar', 'Brasear', 'Caramelizado'}
        for technique, var in self.technique_vars.items():
            var.set(technique in basic_techniques)
    
    def _select_all_stations(self):
        for var in self.station_vars.values():
            var.set(True)
    
    def _deselect_all_stations(self):
        for var in self.station_vars.values():
            var.set(False)
    
    def _select_basic_stations(self):
        basic_stations = {'Ensaladas y Fríos', 'Ensamblaje y Emplatado', 'Estofados y Salsas',
                         'Fritura', 'Horno y Rostizado', 'Bebidas y Cócteles'}
        
        for station, var in self.station_vars.items():
            var.set(station in basic_stations)
    
    def _run_optimization(self):
        """Recopila la configuración y ejecuta la optimización."""
        try:
            config = self._gather_configuration()
            logging.info("CONFIGURACION CAPTURADA PARA OPTIMIZACION:")
            logging.info(f"  - Numero de platos: {config['num_dishes']}")
            logging.info(f"  - Costo maximo: ${config['max_cost_per_dish']}")
            logging.info(f"  - Cocineros: {config['num_chefs']}")
            logging.info(f"  - Margen minimo: {config['min_profit_margin']}%")
            logging.info(f"  - Tecnicas: {len(config['available_techniques'])}")
            logging.info(f"  - Estaciones: {len(config['available_stations'])}")
            
            self.on_optimize_callback(config)
        except Exception as e:
            logging.error(f"Error al recopilar configuracion: {e}")
            messagebox.showerror("Error de Configuración", 
                               f"Error al recopilar configuración:\n{str(e)}")
    
    def _gather_configuration(self) -> Dict:
        """
        MÉTODO COMPLETAMENTE CORREGIDO: Captura valores directamente de los widgets.
        """
        logging.info("RECOPILANDO CONFIGURACION DE LA INTERFAZ...")
        
        # CAPTURA DIRECTA DE LOS ENTRY WIDGETS - MÁS CONFIABLE
        num_dishes_raw = self.entry_dishes.get().strip()
        cost_raw = self.entry_cost.get().strip()
        chefs_raw = self.entry_chefs.get().strip()
        margin_raw = self.entry_margin.get().strip()
        
        # DEBUG: Mostrar valores capturados
        logging.info(f"VALORES CAPTURADOS DE LA INTERFAZ:")
        logging.info(f"  num_dishes_raw: '{num_dishes_raw}'")
        logging.info(f"  cost_raw: '{cost_raw}'")
        logging.info(f"  chefs_raw: '{chefs_raw}'")
        logging.info(f"  margin_raw: '{margin_raw}'")
        
        # VALIDACIONES CRÍTICAS
        if not num_dishes_raw:
            raise ValueError("Debe ingresar el número de opciones en el menú")
        if not cost_raw:
            raise ValueError("Debe ingresar el presupuesto máximo por plato")  
        if not chefs_raw:
            raise ValueError("Debe ingresar el número de cocineros disponibles")
        if not margin_raw:
            raise ValueError("Debe ingresar el margen mínimo de ganancia")
        
        # CONVERSIONES SEGURAS
        try:
            num_dishes = int(num_dishes_raw)
            if num_dishes <= 0:
                raise ValueError("El número de platos debe ser mayor a 0")
        except ValueError:
            raise ValueError(f"Número de platos inválido: '{num_dishes_raw}'. Debe ser un número entero.")
        
        try:
            max_cost_per_dish = float(cost_raw)
            if max_cost_per_dish <= 0:
                raise ValueError("El costo máximo debe ser mayor a 0")
        except ValueError:
            raise ValueError(f"Costo máximo inválido: '{cost_raw}'. Debe ser un número.")
        
        try:
            num_chefs = int(chefs_raw)
            if num_chefs <= 0:
                raise ValueError("El número de cocineros debe ser mayor a 0")
        except ValueError:
            raise ValueError(f"Número de cocineros inválido: '{chefs_raw}'. Debe ser un número entero.")
        
        try:
            min_profit_margin = float(margin_raw)
            if not (0 <= min_profit_margin <= 100):
                raise ValueError("El margen de ganancia debe estar entre 0% y 100%")
        except ValueError:
            raise ValueError(f"Margen de ganancia inválido: '{margin_raw}'. Debe ser un número entre 0 y 100.")
        
        # OBTENER OTROS VALORES
        season = self.config_vars["season"].get() or "Todo el año"
        establishment_type = self.config_vars["establishment_type"].get() or "casual"
        
        # OBTENER TÉCNICAS Y ESTACIONES SELECCIONADAS
        selected_techniques = {tech for tech, var in self.technique_vars.items() if var.get()}
        selected_stations = {station for station, var in self.station_vars.items() if var.get()}
        
        # VALIDACIONES FINALES
        if not selected_techniques:
            raise ValueError("Debe seleccionar al menos una técnica culinaria")
        if not selected_stations:
            raise ValueError("Debe seleccionar al menos una estación de trabajo")
        
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
        
        logging.info("CONFIGURACION FINAL VALIDADA:")
        logging.info(f"   Platos: {num_dishes}")
        logging.info(f"   Costo maximo: ${max_cost_per_dish}")
        logging.info(f"   Cocineros: {num_chefs}")
        logging.info(f"   Margen: {min_profit_margin}%")
        logging.info(f"   Temporada: {season}")
        logging.info(f"   Tipo: {establishment_type}")
        logging.info(f"   Tecnicas: {len(selected_techniques)}")
        logging.info(f"   Estaciones: {len(selected_stations)}")
        
        return config