# app/ui/configuration_panel.py - CÓDIGO COMPLETO CORREGIDO
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
        
        # Flags para rastrear si el usuario ha interactuado con los campos
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
        
        self.vars["num_dishes"] = tk.StringVar(value="10")  # Valor por defecto directo
        self.field_touched["num_dishes"] = False
        num_dishes_entry = ttk.Entry(frame, textvariable=self.vars["num_dishes"], 
                                   width=15, font=("Segoe UI", 10))
        num_dishes_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Eventos simplificados
        num_dishes_entry.bind('<FocusIn>', lambda e: self._on_field_focus_in(e, 'num_dishes'))
        num_dishes_entry.bind('<KeyPress>', lambda e: self._on_field_edit(e, 'num_dishes'))
        
        # Validación para números enteros positivos
        num_dishes_vcmd = (self.register(self._validate_positive_integer), '%P', '%V')
        num_dishes_entry.config(validate='key', validatecommand=num_dishes_vcmd)
        num_dishes_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'num_dishes', 1, 50, 10))
        
        grid_row += 1
        
        # Presupuesto máximo por plato
        ttk.Label(frame, text="Presupuesto máximo de costo por plato (MXN):", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.vars["max_cost_per_dish"] = tk.StringVar(value="200")  # Valor por defecto directo
        self.field_touched["max_cost_per_dish"] = False
        cost_entry = ttk.Entry(frame, textvariable=self.vars["max_cost_per_dish"], 
                             width=15, font=("Segoe UI", 10))
        cost_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Eventos simplificados
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
        
        self.vars["num_chefs"] = tk.StringVar(value="5")  # Valor por defecto directo
        self.field_touched["num_chefs"] = False
        chefs_entry = ttk.Entry(frame, textvariable=self.vars["num_chefs"], 
                              width=15, font=("Segoe UI", 10))
        chefs_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Eventos simplificados
        chefs_entry.bind('<FocusIn>', lambda e: self._on_field_focus_in(e, 'num_chefs'))
        chefs_entry.bind('<KeyPress>', lambda e: self._on_field_edit(e, 'num_chefs'))
        
        # Validación para números enteros positivos
        chefs_vcmd = (self.register(self._validate_positive_integer), '%P', '%V')
        chefs_entry.config(validate='key', validatecommand=chefs_vcmd)
        chefs_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'num_chefs', 1, 50, 5))
    
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
        
        self.config_vars["min_profit_margin"] = tk.StringVar(value="30")  # Valor por defecto directo
        self.field_touched["min_profit_margin"] = False
        margin_entry = ttk.Entry(frame, textvariable=self.config_vars["min_profit_margin"], 
                               width=15, font=("Segoe UI", 10))
        margin_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Eventos simplificados
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
    
    def _on_field_focus_in(self, event, field_name):
        """Maneja cuando un campo recibe el foco."""
        print(f"DEBUG: Campo '{field_name}' recibió foco")
    
    def _on_field_edit(self, event, field_name):
        """Maneja cuando el usuario edita un campo."""
        self.field_touched[field_name] = True
        print(f"DEBUG: Campo '{field_name}' editado por usuario")
    
    def _set_default_values(self):
        """Establece valores por defecto."""
        print("DEBUG: _set_default_values iniciado")
        
        # Configurar establishment change
        self._on_establishment_change()
        
        # Configurar técnicas básicas por defecto
        self._select_basic_techniques()
        
        print("DEBUG: _set_default_values completado")
    
    def set_available_stations(self, stations: List[str]):
        """Establece las estaciones disponibles y crea los checkboxes."""
        print(f"DEBUG: set_available_stations llamado con {len(stations)} estaciones")
        self.all_stations = stations
        
        # Limpiar contenedor existente
        for widget in self.stations_container.winfo_children():
            widget.destroy()
        
        # Limpiar variables anteriores
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
        
        # Después de crear las estaciones, aplicar configuración básica
        self.after(100, self._select_basic_stations_delayed)
    
    def _select_basic_stations_delayed(self):
        """Selecciona estaciones básicas con delay para asegurar que existan."""
        print("DEBUG: Aplicando selección básica de estaciones (delayed)")
        self._select_basic_stations()
    
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
        """Selecciona todas las estaciones."""
        print("DEBUG: Seleccionando todas las estaciones")
        count = 0
        for station, var in self.station_vars.items():
            var.set(True)
            count += 1
        print(f"DEBUG: {count} estaciones seleccionadas")
    
    def _deselect_all_stations(self):
        """Deselecciona todas las estaciones."""
        print("DEBUG: Deseleccionando todas las estaciones")
        for var in self.station_vars.values():
            var.set(False)
    
    def _select_basic_stations(self):
        """Selecciona solo estaciones básicas."""
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
    
    def _create_tooltip(self, widget, text):
        """Crea un tooltip para un widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, justify=tk.LEFT,
                           background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                           font=("Segoe UI", 8))
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)
        
        widget.bind("<Enter>", show_tooltip)
    
    def _validate_positive_integer(self, value, action):
        """Valida que el valor sea un entero positivo."""
        if action != 'key':
            return True
        
        if not value:
            return True
        
        try:
            int_val = int(value)
            return int_val > 0
        except ValueError:
            return False
    
    def _validate_positive_decimal(self, value, action):
        """Valida que el valor sea un decimal positivo."""
        if action != 'key':
            return True
        
        if not value:
            return True
        
        try:
            float_val = float(value)
            return float_val >= 0
        except ValueError:
            return False
    
    def _validate_positive_integer(self, value, action):
        """Valida que el valor sea un entero positivo."""
        if action != 'key':
            return True
        
        if not value:
            return True
        
        try:
            int_val = int(value)
            return int_val > 0
        except ValueError:
            return False
    
    def _validate_positive_decimal(self, value, action):
        """Valida que el valor sea un decimal positivo."""
        if action != 'key':
            return True
        
        if not value:
            return True
        
        try:
            float_val = float(value)
            return float_val >= 0
        except ValueError:
            return False
    
    def _validate_range(self, event, field_name, min_val, max_val, default_val):
        """Valida que un valor esté en el rango especificado."""
        try:
            widget = event.widget
            
            # Si el widget no tiene valor real, no validar
            if not getattr(widget, 'has_real_value', False):
                return
            
            if field_name in self.vars:
                value_str = self.vars[field_name].get()
            else:
                value_str = self.config_vars[field_name].get()
            
            value_str = value_str.strip()
            if not value_str:
                return
            
            if isinstance(min_val, int):
                value = int(value_str)
            else:
                value = float(value_str)
            
            if value < min_val or value > max_val:
                messagebox.showwarning("Valor fuera de rango", 
                                     f"El valor debe estar entre {min_val} y {max_val}. "
                                     f"Se establecerá el valor por defecto: {default_val}")
                if field_name in self.vars:
                    self.vars[field_name].set(str(default_val))
                else:
                    self.config_vars[field_name].set(str(default_val))
                
                # Marcar que el widget ahora tiene valor real
                widget.has_real_value = True
                widget.configure(foreground='black')
                
        except ValueError:
            pass  # Ya se manejó en la validación anterior
    
    # Eliminar funciones de placeholder que ya no son necesarias
    def _on_establishment_change(self, event=None):
        """Maneja el cambio de tipo de establecimiento."""
        establishment_type = self.config_vars["establishment_type"].get()
        preset = self.establishment_presets.get(establishment_type, {})
        
        # Actualizar descripción
        description = preset.get('description', '')
        self.establishment_description.config(text=description)
        
        # Solo actualizar valores si el usuario NO ha tocado los campos
        if 'target_margin' in preset and not self.field_touched.get('min_profit_margin', False):
            self.config_vars["min_profit_margin"].set(str(preset['target_margin']))
        if 'max_cost' in preset and not self.field_touched.get('max_cost_per_dish', False):
            self.vars["max_cost_per_dish"].set(str(preset['max_cost']))
    
    def _user_has_provided_input(self) -> bool:
        """Verifica si el usuario ha proporcionado entrada válida - VERSIÓN SIMPLIFICADA SIN PLACEHOLDERS."""
        required_fields = [
            ('num_dishes', self.vars, 'Número de opciones en el menú'),
            ('max_cost_per_dish', self.vars, 'Presupuesto máximo por plato'),
            ('num_chefs', self.vars, 'Personal disponible'),
            ('min_profit_margin', self.config_vars, 'Porcentaje mínimo de margen')
        ]
        
        for field_name, var_dict, description in required_fields:
            value = var_dict[field_name].get().strip()
            
            print(f"DEBUG: Campo '{field_name}': valor='{value}'")
            
            # Verificar que no esté vacío
            if not value:
                print(f"DEBUG: Campo '{field_name}' está vacío")
                return False
            
            # Verificar que sea un número válido
            try:
                if field_name in ['num_dishes', 'num_chefs']:
                    int(value)
                else:
                    float(value)
            except ValueError:
                print(f"DEBUG: Campo '{field_name}' no es un número válido")
                return False
        
        print("DEBUG: Todos los campos tienen valores válidos")
        return True
    
    def _get_all_children(self, widget):
        """Recursivamente obtiene todos los widgets hijos."""
        children = [widget]  # Incluir el widget padre también
        for child in widget.winfo_children():
            children.extend(self._get_all_children(child))
        return children
    
    def _validate_all_fields(self) -> List[str]:
        """Valida todos los campos y retorna lista de errores - VERSIÓN SIMPLIFICADA."""
        errors = []
        
        try:
            # Validar num_dishes
            num_dishes_str = self.vars["num_dishes"].get().strip()
            if not num_dishes_str:
                errors.append("• Número de opciones en el menú es requerido")
            else:
                try:
                    num_dishes = int(num_dishes_str)
                    if num_dishes <= 0 or num_dishes > 50:
                        errors.append("• Número de opciones debe estar entre 1 y 50")
                except ValueError:
                    errors.append("• Número de opciones debe ser un número entero")
            
            # Validar max_cost_per_dish
            cost_str = self.vars["max_cost_per_dish"].get().strip()
            if not cost_str:
                errors.append("• Presupuesto máximo por plato es requerido")
            else:
                try:
                    cost = float(cost_str)
                    if cost <= 0 or cost > 1000:
                        errors.append("• Presupuesto máximo debe estar entre 10 y 1000 MXN")
                except ValueError:
                    errors.append("• Presupuesto máximo debe ser un número válido")
            
            # Validar num_chefs
            chefs_str = self.vars["num_chefs"].get().strip()
            if not chefs_str:
                errors.append("• Número de cocineros es requerido")
            else:
                try:
                    chefs = int(chefs_str)
                    if chefs <= 0 or chefs > 50:
                        errors.append("• Número de cocineros debe estar entre 1 y 50")
                except ValueError:
                    errors.append("• Número de cocineros debe ser un número entero")
            
            # Validar min_profit_margin
            margin_str = self.config_vars["min_profit_margin"].get().strip()
            if not margin_str:
                errors.append("• Porcentaje mínimo de margen es requerido")
            else:
                try:
                    margin = float(margin_str)
                    if margin < 0 or margin > 100:
                        errors.append("• Margen de ganancia debe estar entre 0% y 100%")
                except ValueError:
                    errors.append("• Margen de ganancia debe ser un número válido")
            
        except Exception as e:
            errors.append(f"• Error de validación: {str(e)}")
        
        return errors
    
    def _debug_field_states(self):
        """Método de debug para ver el estado de todos los campos."""
        print("=== DEBUG: Estado de campos ===")
        required_fields = [
            ('num_dishes', self.vars),
            ('max_cost_per_dish', self.vars),
            ('num_chefs', self.vars),
            ('min_profit_margin', self.config_vars)
        ]
        
        for field_name, var_dict in required_fields:
            value = var_dict[field_name].get()
            print(f"Campo '{field_name}': valor='{value}'")
            
            # Buscar widget
            for widget in self._get_all_children(self):
                if hasattr(widget, 'textvariable') and widget.textvariable == var_dict[field_name]:
                    has_real = getattr(widget, 'has_real_value', False)
                    placeholder = getattr(widget, 'placeholder_text', 'N/A')
                    print(f"  Widget encontrado: has_real_value={has_real}, placeholder='{placeholder}'")
                    break
            else:
                print(f"  Widget NO encontrado")
        print("=== FIN DEBUG ===")
    
    def _run_optimization(self):
        """Recopila la configuración y ejecuta la optimización con validación completa."""
        try:
            # Agregar debug antes de la validación
            self._debug_field_states()
            
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
        """Recopila toda la configuración del panel con validación completa."""
        try:
            print("DEBUG: Iniciando _gather_configuration")
            
            # Verificar que el usuario haya ingresado valores
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
            
            # Estaciones seleccionadas
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
                
                detail_msg = f"Estado de las estaciones:\n" + "\n".join(station_status[:10])
                if len(station_status) > 10:
                    detail_msg += f"\n  ... y {len(station_status) - 10} más"
                
                print(f"DEBUG: Error - No hay estaciones seleccionadas")
                print(detail_msg)
                
                messagebox.showerror("Error de Configuración", 
                                   f"Debe seleccionar al menos una estación de trabajo disponible.\n\n{detail_msg}")
                return None
            
            # Construir configuración final - VERSIÓN SIMPLIFICADA
            config = {
                'num_dishes': int(self.vars["num_dishes"].get().strip()),
                'max_cost_per_dish': float(self.vars["max_cost_per_dish"].get().strip()),
                'num_chefs': int(self.vars["num_chefs"].get().strip()),
                'min_profit_margin': float(self.config_vars["min_profit_margin"].get().strip()),
                'season': self.config_vars["season"].get(),
                'establishment_type': self.config_vars["establishment_type"].get(),
                'available_techniques': selected_techniques,
                'available_stations': selected_stations
            }
            
            print(f"DEBUG: Configuración recopilada exitosamente:")
            for key, value in config.items():
                print(f"  {key}: {value}")
            
            return config
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", 
                               f"Error en la validación de campos:\n{str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error inesperado en _gather_configuration: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", 
                               f"Error inesperado al procesar configuración:\n{str(e)}")
            return None