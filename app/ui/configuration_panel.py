# app/ui/configuration_panel.py - CÓDIGO COMPLETO CON CORRECCIÓN PARA CAMPOS VACÍOS
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict, Set
import logging


class ConfigurationPanel(ttk.Frame):
    """
    Panel de configuración para los parámetros del restaurante y optimización.
    """
    
    def __init__(self, parent, catalog: List, all_techniques: List[str], 
                 on_optimize_callback: Callable):
        super().__init__(parent, padding="15")
        
        self.catalog = catalog
        self.all_techniques = all_techniques
        self.on_optimize_callback = on_optimize_callback
        self.all_stations = []
        
        # Variables de configuración
        self.vars = {}  # Para restricciones del restaurante
        self.config_vars = {}  # Para parámetros de optimización
        self.technique_vars = {}
        self.station_vars = {}
        
        # NUEVO: Flags para rastrear si el usuario ha interactuado con los campos
        self.field_touched = {}
        
        # Presets de optimización por tipo de establecimiento
        self.establishment_presets = {
            'casual': {
                'description': '🍔 Restaurante Casual - Enfoque en popularidad, rapidez y precios accesibles',
                'target_margin': 30,
                'max_cost': 200
            },
            'elegante': {
                'description': '🍷 Restaurante Elegante - Enfoque en calidad, presentación y márgenes altos',
                'target_margin': 50,
                'max_cost': 350
            },
            'comida_rapida': {
                'description': '⚡ Comida Rápida - Máxima eficiencia operativa y tiempos mínimos',
                'target_margin': 40,
                'max_cost': 150
            }
        }
        
        self._create_interface()
        self._set_default_values()
    
    def _create_interface(self):
        """Crea la interfaz del panel de configuración."""
        # Crear columnas principales
        left_column = ttk.Frame(self)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_column = ttk.Frame(self)
        right_column.pack(side="left", fill="both", expand=True)
        
        # Secciones del panel izquierdo
        self._create_restaurant_constraints_section(left_column)
        self._create_stations_section(left_column)
        
        # Secciones del panel derecho
        self._create_optimization_section(right_column)
        self._create_techniques_section(right_column)
        
        # Botón de optimización
        self._create_optimize_button()
    
    def _create_restaurant_constraints_section(self, parent):
        """Crear sección de restricciones del restaurante."""
        frame = ttk.LabelFrame(parent, text="📊 Restricciones del Restaurante", padding=15)
        frame.pack(fill="x", pady=(0, 10))
        
        grid_row = 0
        
        # Número de opciones en el menú
        ttk.Label(frame, text="Número deseado de opciones en el menú:", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.vars["num_dishes"] = tk.StringVar(value="")  # VACÍO por defecto
        self.field_touched["num_dishes"] = False
        num_dishes_entry = ttk.Entry(frame, textvariable=self.vars["num_dishes"], 
                                   width=15, font=("Segoe UI", 10))
        num_dishes_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Agregar placeholder y eventos
        self._add_placeholder(num_dishes_entry, "Ej: 20")
        num_dishes_entry.bind('<FocusIn>', lambda e: self._on_field_focus_in(e, 'num_dishes'))
        num_dishes_entry.bind('<KeyPress>', lambda e: self._on_field_edit(e, 'num_dishes'))
        
        # Validación para números enteros positivos
        num_dishes_vcmd = (self.register(self._validate_positive_integer), '%P', '%V')
        num_dishes_entry.config(validate='key', validatecommand=num_dishes_vcmd)
        num_dishes_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'num_dishes', 1, 50, 20))
        
        grid_row += 1
        
        # Presupuesto máximo por plato
        ttk.Label(frame, text="Presupuesto máximo de costo por plato (MXN):", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.vars["max_cost_per_dish"] = tk.StringVar(value="")  # VACÍO por defecto
        self.field_touched["max_cost_per_dish"] = False
        cost_entry = ttk.Entry(frame, textvariable=self.vars["max_cost_per_dish"], 
                             width=15, font=("Segoe UI", 10))
        cost_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Agregar placeholder y eventos
        self._add_placeholder(cost_entry, "Ej: 200")
        cost_entry.bind('<FocusIn>', lambda e: self._on_field_focus_in(e, 'max_cost_per_dish'))
        cost_entry.bind('<KeyPress>', lambda e: self._on_field_edit(e, 'max_cost_per_dish'))
        
        # Validación para números decimales positivos
        cost_vcmd = (self.register(self._validate_positive_decimal), '%P', '%V')
        cost_entry.config(validate='key', validatecommand=cost_vcmd)
        cost_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'max_cost_per_dish', 10.0, 1000.0, 200.0))
        
        grid_row += 1
        
        # Personal disponible
        ttk.Label(frame, text="Personal disponible (cocineros):", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.vars["num_chefs"] = tk.StringVar(value="")  # VACÍO por defecto
        self.field_touched["num_chefs"] = False
        chefs_entry = ttk.Entry(frame, textvariable=self.vars["num_chefs"], 
                              width=15, font=("Segoe UI", 10))
        chefs_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Agregar placeholder y eventos
        self._add_placeholder(chefs_entry, "Ej: 8")
        chefs_entry.bind('<FocusIn>', lambda e: self._on_field_focus_in(e, 'num_chefs'))
        chefs_entry.bind('<KeyPress>', lambda e: self._on_field_edit(e, 'num_chefs'))
        
        # Validación para números enteros positivos
        chefs_vcmd = (self.register(self._validate_positive_integer), '%P', '%V')
        chefs_entry.config(validate='key', validatecommand=chefs_vcmd)
        chefs_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'num_chefs', 1, 50, 8))
    
    def _create_stations_section(self, parent):
        """Crea la sección de estaciones de trabajo."""
        frame = ttk.LabelFrame(parent, text="🏭 Estaciones de Trabajo Disponibles", padding=15)
        frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Botones de selección rápida
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(button_frame, text="Seleccionar Todas", 
                  command=self._select_all_stations).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Deseleccionar Todas", 
                  command=self._deselect_all_stations).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Configuración Básica", 
                  command=self._select_basic_stations).pack(side="left")
        
        # Canvas con scrollbar para las estaciones
        canvas = tk.Canvas(frame, height=120)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Contenedor para checkboxes (se llenará cuando se establezcan las estaciones)
        self.stations_container = scrollable_frame
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mensaje de ayuda
        ttk.Label(frame, text="💡 Seleccione las estaciones operativas",
                 font=("Segoe UI", 8, "italic"), foreground="#666666").pack(pady=(5, 0))
    
    def _create_optimization_section(self, parent):
        """Crea la sección de parámetros de optimización."""
        frame = ttk.LabelFrame(parent, text="🎯 Parámetros de Optimización", padding=15)
        frame.pack(fill="x", pady=(0, 10))
        
        grid_row = 0
        
        # Porcentaje mínimo de margen
        ttk.Label(frame, text="Porcentaje mínimo de margen de ganancia (%):", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.config_vars["min_profit_margin"] = tk.StringVar(value="")  # VACÍO por defecto
        self.field_touched["min_profit_margin"] = False
        margin_entry = ttk.Entry(frame, textvariable=self.config_vars["min_profit_margin"], 
                               width=15, font=("Segoe UI", 10))
        margin_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Agregar placeholder y eventos
        self._add_placeholder(margin_entry, "Ej: 30")
        margin_entry.bind('<FocusIn>', lambda e: self._on_field_focus_in(e, 'min_profit_margin'))
        margin_entry.bind('<KeyPress>', lambda e: self._on_field_edit(e, 'min_profit_margin'))
        
        # Validación para porcentajes (0-100)
        margin_vcmd = (self.register(self._validate_positive_decimal), '%P', '%V')
        margin_entry.config(validate='key', validatecommand=margin_vcmd)
        margin_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'min_profit_margin', 0.0, 100.0, 30.0))
        
        grid_row += 1
        
        # Temporada del año
        ttk.Label(frame, text="Temporada del año:", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.config_vars["season"] = tk.StringVar(value="Todo el año")
        season_combo = ttk.Combobox(frame, textvariable=self.config_vars["season"],
                                  values=['Todo el año', 'Primavera', 'Verano', 'Otoño', 'Invierno'],
                                  state="readonly", width=18, font=("Segoe UI", 10))
        season_combo.grid(row=grid_row, column=1, sticky="w")
        grid_row += 1
        
        # Tipo de establecimiento
        ttk.Label(frame, text="Tipo de establecimiento:", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.config_vars["establishment_type"] = tk.StringVar(value="casual")
        establishment_combo = ttk.Combobox(frame, textvariable=self.config_vars["establishment_type"],
                                         values=['casual', 'elegante', 'comida_rapida'],
                                         state="readonly", width=18, font=("Segoe UI", 10))
        establishment_combo.grid(row=grid_row, column=1, sticky="w")
        establishment_combo.bind('<<ComboboxSelected>>', self._on_establishment_change)
        grid_row += 1
        
        # Descripción del tipo de establecimiento
        self.establishment_description = ttk.Label(frame, text="", 
                                                 font=("Segoe UI", 9, "italic"),
                                                 foreground="#2c5282",
                                                 wraplength=400)
        self.establishment_description.grid(row=grid_row, column=0, columnspan=2, 
                                          sticky="w", pady=(10, 0))
        
        # Información sobre algoritmo genético
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Información del Algoritmo", padding=10)
        info_frame.pack(fill="x", pady=(10, 0))
        
        info_text = """🧬 ALGORITMO GENÉTICO MULTI-OBJETIVO

🎯 Optimiza simultáneamente 7 variables:
• Margen de ganancia total del menú
• Tiempo promedio de preparación por pedido
• Balance nutricional y tipos de dieta
• Variedad gastronómica y cultural
• Eficiencia de ingredientes (minimizar desperdicio)
• Distribución equilibrada de carga de trabajo
• Satisfacción proyectada del cliente

⚙️ Configuración del Algoritmo:
• Población: 150 individuos por generación
• Evolución: 250 generaciones con elitismo
• Estrategias múltiples de cruzamiento y mutación
• Búsqueda de soluciones únicas y diversas"""
        
        ttk.Label(info_frame, text=info_text, font=("Segoe UI", 8), 
                 justify="left", wraplength=400).pack(anchor="w")
    
    def _create_techniques_section(self, parent):
        """Crea la sección de técnicas culinarias."""
        frame = ttk.LabelFrame(parent, text="🔧 Técnicas Culinarias Disponibles", padding=15)
        frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Botones de selección rápida
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(button_frame, text="Seleccionar Todas", 
                  command=self._select_all_techniques).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Deseleccionar Todas", 
                  command=self._deselect_all_techniques).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Técnicas Básicas", 
                  command=self._select_basic_techniques).pack(side="left")
        
        # Canvas con scrollbar para las técnicas
        canvas = tk.Canvas(frame, height=120)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Crear checkboxes para técnicas
        techniques_per_column = 6
        col = 0
        row = 0
        
        for i, technique in enumerate(sorted(self.all_techniques)):
            if i > 0 and i % techniques_per_column == 0:
                col += 1
                row = 0
            
            self.technique_vars[technique] = tk.BooleanVar(value=False)
            ttk.Checkbutton(scrollable_frame, text=technique, 
                          variable=self.technique_vars[technique],
                          style="TCheckbutton").grid(
                row=row, column=col, sticky="w", padx=15, pady=2)
            row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mensaje de ayuda
        ttk.Label(frame, text="💡 Seleccione las técnicas disponibles",
                 font=("Segoe UI", 8, "italic"), foreground="#666666").pack(pady=(5, 0))
    
    def _create_optimize_button(self):
        """Crea el botón de optimización."""
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom", fill="x", pady=15)
        
        optimize_button = ttk.Button(
            button_frame, 
            text="🚀 OPTIMIZAR MENÚ DEL RESTAURANTE",
            command=self._run_optimization,
            style="Accent.TButton"
        )
        optimize_button.pack(pady=10, ipady=15, fill="x")
        
        # Información adicional del botón
        ttk.Label(
            button_frame,
            text="⏱️ La optimización puede tomar 1-2 minutos dependiendo de la complejidad",
            font=("Segoe UI", 8, "italic"),
            foreground="#666666"
        ).pack(pady=(0, 5))
        
        # Agregar tooltip con información
        self._create_tooltip(optimize_button, 
                           "Ejecuta el algoritmo genético para encontrar las mejores "
                           "configuraciones de menú según los parámetros establecidos.")
    
    def _add_placeholder(self, entry_widget, placeholder_text):
        """Agrega texto de placeholder a un Entry widget."""
        entry_widget.placeholder_text = placeholder_text
        entry_widget.insert(0, placeholder_text)
        entry_widget.configure(foreground='gray')
        
        def on_focus_in(event):
            if entry_widget.get() == placeholder_text:
                entry_widget.delete(0, tk.END)
                entry_widget.configure(foreground='black')
        
        def on_focus_out(event):
            if not entry_widget.get():
                entry_widget.insert(0, placeholder_text)
                entry_widget.configure(foreground='gray')
        
        entry_widget.bind('<FocusIn>', on_focus_in)
        entry_widget.bind('<FocusOut>', on_focus_out)
    
    def _on_field_focus_in(self, event, field_name):
        """Maneja cuando un campo recibe el foco."""
        print(f"DEBUG: Campo '{field_name}' recibió foco")
    
    def _on_field_edit(self, event, field_name):
        """Maneja cuando el usuario edita un campo."""
        self.field_touched[field_name] = True
        print(f"DEBUG: Campo '{field_name}' editado por usuario")
    
    def _set_default_values(self):
        """Establece valores por defecto. VERSIÓN CORREGIDA."""
        print("DEBUG: _set_default_values iniciado")
        
        # Configurar establishment change
        self._on_establishment_change()
        
        # Configurar técnicas básicas por defecto - PERO SIN MARCAR COMO TOCADO
        self._select_basic_techniques()
        
        # NO llamar _select_basic_stations aquí porque las estaciones aún no existen
        # Se llamará desde set_available_stations() con delay
        print("DEBUG: _set_default_values completado")
    
    def set_available_stations(self, stations: List[str]):
        """Establece las estaciones disponibles y crea los checkboxes. VERSIÓN CORREGIDA."""
        print(f"DEBUG: set_available_stations llamado con {len(stations)} estaciones")
        self.all_stations = stations
        
        # Limpiar contenedor existente
        for widget in self.stations_container.winfo_children():
            widget.destroy()
        
        # IMPORTANTE: Limpiar variables anteriores
        self.station_vars.clear()
        
        # Crear checkboxes para estaciones
        stations_per_column = 5
        col = 0
        row = 0
        
        for i, station in enumerate(sorted(self.all_stations)):
            if i > 0 and i % stations_per_column == 0:
                col += 1
                row = 0
            
            # Crear nueva variable
            self.station_vars[station] = tk.BooleanVar(value=False)
            
            # Crear checkbox
            checkbox = ttk.Checkbutton(self.stations_container, text=station,
                          variable=self.station_vars[station],
                          style="TCheckbutton")
            checkbox.grid(row=row, column=col, sticky="w", padx=15, pady=2)
            
            print(f"DEBUG: Estación '{station}' creada con variable {self.station_vars[station]}")
            row += 1
        
        # DESPUÉS de crear las estaciones, aplicar configuración básica
        self.after(100, self._select_basic_stations_delayed)  # Delay para asegurar que se crean primero
    
    def _select_basic_stations_delayed(self):
        """Selecciona estaciones básicas con delay para asegurar que existan."""
        print("DEBUG: Aplicando selección básica de estaciones (delayed)")
        self._select_basic_stations()
    
    def _on_establishment_change(self, event=None):
        """Maneja el cambio de tipo de establecimiento."""
        establishment_type = self.config_vars["establishment_type"].get()
        preset = self.establishment_presets.get(establishment_type, {})
        
        # Actualizar descripción
        description = preset.get('description', '')
        self.establishment_description.config(text=description)
        
        # SOLO actualizar valores si el usuario NO ha tocado los campos
        if 'target_margin' in preset and not self.field_touched.get('min_profit_margin', False):
            self.config_vars["min_profit_margin"].set(str(preset['target_margin']))
        if 'max_cost' in preset and not self.field_touched.get('max_cost_per_dish', False):
            self.vars["max_cost_per_dish"].set(str(preset['max_cost']))
    
    def _select_all_techniques(self):
        """Selecciona todas las técnicas."""
        for var in self.technique_vars.values():
            var.set(True)
    
    def _deselect_all_techniques(self):
        """Deselecciona todas las técnicas."""
        for var in self.technique_vars.values():
            var.set(False)
    
    def _select_basic_techniques(self):
        """Selecciona solo técnicas básicas."""
        basic_techniques = {'Plancha', 'Hervido', 'Salteado', 'Horneado', 'Freír', 'Guisar'}
        
        for technique, var in self.technique_vars.items():
            var.set(technique in basic_techniques)
    
    def _select_all_stations(self):
        """Selecciona todas las estaciones. VERSIÓN CON DEBUG."""
        print("DEBUG: Seleccionando todas las estaciones")
        count = 0
        for station, var in self.station_vars.items():
            var.set(True)
            count += 1
        print(f"DEBUG: {count} estaciones seleccionadas")
    
    def _deselect_all_stations(self):
        """Deselecciona todas las estaciones. VERSIÓN CON DEBUG."""
        print("DEBUG: Deseleccionando todas las estaciones")
        for var in self.station_vars.values():
            var.set(False)
    
    def _select_basic_stations(self):
        """Selecciona solo estaciones básicas. VERSIÓN CORREGIDA."""
        basic_stations = {
            'Mise en Place', 'Plancha y Parrilla', 'Horno y Rostizado',
            'Estofados y Salsas', 'Fritura', 'Ensamblaje y Emplatado'
        }
        
        print(f"DEBUG: _select_basic_stations - Estaciones disponibles: {list(self.station_vars.keys())}")
        
        selected_count = 0
        for station, var in self.station_vars.items():
            if station in basic_stations:
                var.set(True)
                selected_count += 1
                print(f"DEBUG: Estación '{station}' seleccionada como básica")
            else:
                var.set(False)
        
        print(f"DEBUG: {selected_count} estaciones básicas seleccionadas")
    
    def _run_optimization(self):
        """Recopila la configuración y ejecuta la optimización con validación completa."""
        try:
            config = self._gather_configuration()
            
            # Si la configuración es None, hubo errores de validación
            if config is None:
                return
            
            # Ejecutar callback de optimización
            self.on_optimize_callback(config)
            
        except Exception as e:
            messagebox.showerror("Error de Configuración", 
                               f"Error inesperado al recopilar configuración:\n{str(e)}")
    
    def _gather_configuration(self) -> Dict:
        """Recopila toda la configuración del panel con validación completa. VERSIÓN MEJORADA."""
        try:
            print("DEBUG: Iniciando _gather_configuration")
            
            # NUEVA VALIDACIÓN: Verificar que el usuario haya ingresado valores
            if not self._user_has_provided_input():
                messagebox.showwarning("Configuración Incompleta", 
                                     "Por favor complete todos los campos obligatorios antes de optimizar.\n\n"
                                     "Campos requeridos:\n"
                                     "• Número deseado de opciones en el menú\n"
                                     "• Presupuesto máximo de costo por plato\n"
                                     "• Personal disponible (cocineros)\n"
                                     "• Porcentaje mínimo de margen de ganancia")
                return None
            
            # Validar campos obligatorios
            validation_errors = self._validate_all_fields()
            if validation_errors:
                error_message = "Por favor corrija los siguientes errores:\n\n" + "\n".join(validation_errors)
                messagebox.showerror("Errores de Validación", error_message)
                return None
            
            # Técnicas seleccionadas
            selected_techniques = {tech for tech, var in self.technique_vars.items() 
                                 if var.get()}
            
            # Estaciones seleccionadas - CON DEBUGGING DETALLADO
            selected_stations = set()
            print(f"DEBUG: Revisando {len(self.station_vars)} variables de estación:")
            
            for station, var in self.station_vars.items():
                is_selected = var.get()
                print(f"DEBUG: Estación '{station}': {is_selected} (variable: {var})")
                if is_selected:
                    selected_stations.add(station)
            
            print(f"DEBUG: Técnicas seleccionadas: {len(selected_techniques)}")
            print(f"DEBUG: Lista de técnicas: {selected_techniques}")
            print(f"DEBUG: Estaciones seleccionadas: {len(selected_stations)}")  
            print(f"DEBUG: Lista de estaciones: {selected_stations}")
            
            # Validaciones con mensajes mejorados
            if not selected_techniques:
                messagebox.showerror("Error de Configuración", 
                                   "Debe seleccionar al menos una técnica culinaria disponible.")
                return None
            
            if not selected_stations:
                # Mensaje más detallado para debugging
                station_status = []
                for station, var in self.station_vars.items():
                    station_status.append(f"  • {station}: {'✓' if var.get() else '✗'}")
                
                detail_msg = f"Estado de las estaciones:\n" + "\n".join(station_status[:10])  # Mostrar primeras 10
                if len(station_status) > 10:
                    detail_msg += f"\n  ... y {len(station_status) - 10} más"
                
                print(f"DEBUG: Error - No hay estaciones seleccionadas")
                print(detail_msg)
                
                messagebox.showerror("Error de Configuración", 
                                   f"Debe seleccionar al menos una estación de trabajo disponible.\n\n{detail_msg}")
                return None