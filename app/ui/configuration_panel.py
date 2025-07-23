# app/ui/configuration_panel.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict, Set


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
        
        self.vars["num_dishes"] = tk.StringVar(value="20")
        num_dishes_entry = ttk.Entry(frame, textvariable=self.vars["num_dishes"], 
                                   width=15, font=("Segoe UI", 10))
        num_dishes_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Validación para números enteros positivos
        num_dishes_vcmd = (self.register(self._validate_positive_integer), '%P', '%V')
        num_dishes_entry.config(validate='key', validatecommand=num_dishes_vcmd)
        num_dishes_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'num_dishes', 1, 50, 20))
        
        grid_row += 1
        
        # Presupuesto máximo por plato
        ttk.Label(frame, text="Presupuesto máximo de costo por plato (MXN):", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.vars["max_cost_per_dish"] = tk.StringVar(value="200")
        cost_entry = ttk.Entry(frame, textvariable=self.vars["max_cost_per_dish"], 
                             width=15, font=("Segoe UI", 10))
        cost_entry.grid(row=grid_row, column=1, sticky="w")
        
        # Validación para números decimales positivos
        cost_vcmd = (self.register(self._validate_positive_decimal), '%P', '%V')
        cost_entry.config(validate='key', validatecommand=cost_vcmd)
        cost_entry.bind('<FocusOut>', lambda e: self._validate_range(e, 'max_cost_per_dish', 10.0, 1000.0, 200.0))
        
        grid_row += 1
        
        # Personal disponible
        ttk.Label(frame, text="Personal disponible (cocineros):", 
                 font=("Segoe UI", 9, "bold")).grid(
            row=grid_row, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.vars["num_chefs"] = tk.StringVar(value="8")
        chefs_entry = ttk.Entry(frame, textvariable=self.vars["num_chefs"], 
                              width=15, font=("Segoe UI", 10))
        chefs_entry.grid(row=grid_row, column=1, sticky="w")
        
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
        
        self.config_vars["min_profit_margin"] = tk.StringVar(value="30")
        margin_entry = ttk.Entry(frame, textvariable=self.config_vars["min_profit_margin"], 
                               width=15, font=("Segoe UI", 10))
        margin_entry.grid(row=grid_row, column=1, sticky="w")
        
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
    
    def _set_default_values(self):
        """Establece valores por defecto."""
        self._on_establishment_change()
        
        # Configurar técnicas básicas por defecto
        self._select_basic_techniques()
        # Configurar estaciones básicas por defecto
        self._select_basic_stations()
    
    def set_available_stations(self, stations: List[str]):
        """Establece las estaciones disponibles y crea los checkboxes."""
        self.all_stations = stations
        
        # Limpiar contenedor existente
        for widget in self.stations_container.winfo_children():
            widget.destroy()
        
        # Crear checkboxes para estaciones
        stations_per_column = 5
        col = 0
        row = 0
        
        for i, station in enumerate(sorted(self.all_stations)):
            if i > 0 and i % stations_per_column == 0:
                col += 1
                row = 0
            
            self.station_vars[station] = tk.BooleanVar(value=False)
            ttk.Checkbutton(self.stations_container, text=station,
                          variable=self.station_vars[station],
                          style="TCheckbutton").grid(
                row=row, column=col, sticky="w", padx=15, pady=2)
            row += 1
    
    def _on_establishment_change(self, event=None):
        """Maneja el cambio de tipo de establecimiento."""
        establishment_type = self.config_vars["establishment_type"].get()
        preset = self.establishment_presets.get(establishment_type, {})
        
        # Actualizar descripción
        description = preset.get('description', '')
        self.establishment_description.config(text=description)
        
        # Actualizar valores sugeridos
        if 'target_margin' in preset:
            self.config_vars["min_profit_margin"].set(str(preset['target_margin']))
        if 'max_cost' in preset:
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
        """Selecciona todas las estaciones."""
        for var in self.station_vars.values():
            var.set(True)
    
    def _deselect_all_stations(self):
        """Deselecciona todas las estaciones."""
        for var in self.station_vars.values():
            var.set(False)
    
    def _select_basic_stations(self):
        """Selecciona solo estaciones básicas."""
        basic_stations = {
            'Mise en Place', 'Plancha y Parrilla', 'Horno y Rostizado',
            'Estofados y Salsas', 'Fritura', 'Ensamblaje y Emplatado'
        }
        
        for station, var in self.station_vars.items():
            var.set(station in basic_stations)
    
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
        """Recopila toda la configuración del panel con validación completa."""
        try:
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
            selected_stations = {station for station, var in self.station_vars.items() 
                               if var.get()}
            
            # Validar selecciones
            if not selected_techniques:
                messagebox.showerror("Error de Configuración", 
                                   "Debe seleccionar al menos una técnica culinaria disponible.")
                return None
            
            if not selected_stations:
                messagebox.showerror("Error de Configuración", 
                                   "Debe seleccionar al menos una estación de trabajo disponible.")
                return None
            
            config = {
                'num_dishes': int(self.vars["num_dishes"].get()),
                'max_cost_per_dish': float(self.vars["max_cost_per_dish"].get()),
                'num_chefs': int(self.vars["num_chefs"].get()),
                'min_profit_margin': float(self.config_vars["min_profit_margin"].get()),
                'season': self.config_vars["season"].get(),
                'establishment_type': self.config_vars["establishment_type"].get(),
                'available_techniques': selected_techniques,
                'available_stations': selected_stations
            }
            
            return config
            
        except ValueError as e:
            messagebox.showerror("Error de Formato", 
                               f"Error en el formato de los datos:\n{str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("Error Inesperado", 
                               f"Error inesperado al recopilar configuración:\n{str(e)}")
            return None
    
    def _validate_all_fields(self) -> List[str]:
        """Valida todos los campos y retorna lista de errores."""
        errors = []
        
        # Validar número de platos
        try:
            num_dishes = int(self.vars["num_dishes"].get().strip())
            if num_dishes <= 0:
                errors.append("• El número de opciones en el menú debe ser mayor a 0")
            elif num_dishes > 50:
                errors.append("• El número de opciones en el menú no puede ser mayor a 50")
        except ValueError:
            errors.append("• El número de opciones en el menú debe ser un número entero válido")
        
        # Validar costo máximo
        try:
            max_cost = float(self.vars["max_cost_per_dish"].get().strip())
            if max_cost <= 0:
                errors.append("• El presupuesto máximo por plato debe ser mayor a 0")
            elif max_cost > 1000:
                errors.append("• El presupuesto máximo por plato no puede ser mayor a $1000")
        except ValueError:
            errors.append("• El presupuesto máximo por plato debe ser un número válido")
        
        # Validar número de cocineros
        try:
            num_chefs = int(self.vars["num_chefs"].get().strip())
            if num_chefs <= 0:
                errors.append("• El número de cocineros debe ser mayor a 0")
            elif num_chefs > 50:
                errors.append("• El número de cocineros no puede ser mayor a 50")
        except ValueError:
            errors.append("• El número de cocineros debe ser un número entero válido")
        
        # Validar margen de ganancia
        try:
            margin = float(self.config_vars["min_profit_margin"].get().strip())
            if margin < 0:
                errors.append("• El margen de ganancia no puede ser negativo")
            elif margin > 100:
                errors.append("• El margen de ganancia no puede ser mayor a 100%")
        except ValueError:
            errors.append("• El margen de ganancia debe ser un número válido")
        
        return errors
    
    def _validate_positive_integer(self, value, validation_type):
        """Valida que el valor sea un entero positivo o vacío."""
        if validation_type == 'focusout':
            return True
        
        if value == "":
            return True
        
        try:
            num = int(value)
            return num >= 0
        except ValueError:
            return False
    
    def _validate_positive_decimal(self, value, validation_type):
        """Valida que el valor sea un decimal positivo o vacío."""
        if validation_type == 'focusout':
            return True
        
        if value == "":
            return True
        
        # Permitir punto decimal
        if value.count('.') <= 1:
            try:
                if value.endswith('.'):
                    # Permitir número seguido de punto
                    return float(value[:-1]) >= 0 if value[:-1] else True
                else:
                    num = float(value)
                    return num >= 0
            except ValueError:
                return False
        return False
    
    def _validate_range(self, event, var_name, min_val, max_val, default_val):
        """Valida que el valor esté en el rango especificado."""
        try:
            widget = event.widget
            current_value = widget.get().strip()
            
            if not current_value:
                # Campo vacío, establecer valor por defecto
                if var_name in self.vars:
                    self.vars[var_name].set(str(default_val))
                else:
                    self.config_vars[var_name].set(str(default_val))
                widget.config(bg='#fff2cc')  # Color amarillo suave para indicar corrección
                self.after(1000, lambda: widget.config(bg='white'))
                return
            
            # Validar rango
            if isinstance(min_val, int):
                value = int(current_value)
            else:
                value = float(current_value)
            
            if value < min_val:
                messagebox.showwarning("Valor Fuera de Rango", 
                                     f"El valor mínimo permitido es {min_val}")
                if var_name in self.vars:
                    self.vars[var_name].set(str(min_val))
                else:
                    self.config_vars[var_name].set(str(min_val))
                widget.config(bg='#ffebee')  # Color rojo suave
                self.after(1000, lambda: widget.config(bg='white'))
                
            elif value > max_val:
                messagebox.showwarning("Valor Fuera de Rango", 
                                     f"El valor máximo permitido es {max_val}")
                if var_name in self.vars:
                    self.vars[var_name].set(str(max_val))
                else:
                    self.config_vars[var_name].set(str(max_val))
                widget.config(bg='#ffebee')  # Color rojo suave
                self.after(1000, lambda: widget.config(bg='white'))
            else:
                # Valor válido
                widget.config(bg='#e8f5e8')  # Color verde suave
                self.after(1000, lambda: widget.config(bg='white'))
                
        except ValueError:
            # Valor inválido, restablecer al valor por defecto
            messagebox.showerror("Valor Inválido", 
                               f"Por favor ingrese un número válido")
            if var_name in self.vars:
                self.vars[var_name].set(str(default_val))
            else:
                self.config_vars[var_name].set(str(default_val))
            widget.config(bg='#ffebee')
            self.after(1000, lambda: widget.config(bg='white'))
    
    def _create_tooltip(self, widget, text):
        """Crea un tooltip para el widget especificado."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
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