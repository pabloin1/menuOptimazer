# app/ui/app_gui.py - CÓDIGO COMPLETO CORREGIDO
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from collections import defaultdict
from decimal import Decimal
import logging
from app.core.genetic_algorithm import create_individual, calculate_fitness, select_parents, crossover, mutate

class MenuOptimizerApp(tk.Tk):
    def __init__(self, catalog, all_techniques):
        super().__init__()
        if not catalog: self.destroy(); return
        
        self.catalog = catalog
        self.all_techniques = all_techniques
        
        # Obtener todas las estaciones únicas de la base de datos
        self.all_stations = set()
        for dish in catalog:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    if hasattr(step, 'station') and step.station:
                        self.all_stations.add(step.station)
        self.all_stations = sorted(list(self.all_stations))
        
        self.title("MENUOPTIMIZER v9.4 - Interfaz Simplificada"); self.geometry("1200x800")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Presets de objetivos por tipo de establecimiento (CORREGIDOS)
        self.establishment_presets = {
            'casual': {'ganancia': 0.5, 'tiempo': 0.9, 'popularidad': 1.0, 'desperdicio': 0.4},
            'elegante': {'ganancia': 1.0, 'tiempo': 0.3, 'popularidad': 0.7, 'desperdicio': 0.8},
            'comida_rapida': {'ganancia': 0.6, 'tiempo': 1.0, 'popularidad': 0.9, 'desperdicio': 0.8}
        }
        
        self.create_parameters_tab()
        self.create_results_tab()
    
    def safe_float_conversion(self, value, default=0.0):
        """Convierte de manera segura cualquier tipo numérico a float"""
        try:
            if value is None:
                return default
            if isinstance(value, Decimal):
                return float(value)
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                return float(str(value))
        except (ValueError, TypeError, AttributeError):
            logging.warning(f"Error convirtiendo valor {value} a float, usando {default}")
            return default

    def calculate_dish_cost(self, dish):
        """Calcula el costo real de un plato basado en sus ingredientes"""
        if not hasattr(dish, 'recipe') or not dish.recipe:
            logging.warning(f"Plato {dish.name} no tiene receta")
            return 10.0  # Costo por defecto
        
        total_cost = 0.0
        try:
            for ingredient, quantity in dish.recipe.items():
                if hasattr(ingredient, 'cost_per_kg'):
                    cost_per_kg = self.safe_float_conversion(ingredient.cost_per_kg, 0)
                    qty_kg = self.safe_float_conversion(quantity, 0) / 1000.0
                    ingredient_cost = cost_per_kg * qty_kg
                    total_cost += ingredient_cost
                    logging.debug(f"Ingrediente {ingredient.name}: {quantity}g * ${cost_per_kg}/kg = ${ingredient_cost:.2f}")
            
            logging.info(f"Costo calculado para {dish.name}: ${total_cost:.2f}")
            return max(total_cost, 1.0)  # Mínimo $1.00
        except Exception as e:
            logging.error(f"Error calculando costo de {dish.name}: {e}")
            return 10.0

    def calculate_dish_prep_time(self, dish):
        """Calcula el tiempo de preparación real de un plato"""
        # Primero intentar usar el atributo prep_time si existe
        if hasattr(dish, 'prep_time') and dish.prep_time:
            prep_time = self.safe_float_conversion(dish.prep_time, 0)
            if prep_time > 0:
                return prep_time
        
        # Si no, calcular desde los steps
        if hasattr(dish, 'steps') and dish.steps:
            total_time = 0
            try:
                for step in dish.steps:
                    if hasattr(step, 'time'):
                        step_time = self.safe_float_conversion(step.time, 0)
                        total_time += step_time
                
                if total_time > 0:
                    logging.info(f"Tiempo calculado desde steps para {dish.name}: {total_time} min")
                    return total_time
            except Exception as e:
                logging.error(f"Error calculando tiempo desde steps para {dish.name}: {e}")
        
        # Si no hay steps o tiempo, usar complejidad como base
        complexity = getattr(dish, 'complexity', 3)
        estimated_time = complexity * 8  # 8 minutos por nivel de complejidad
        logging.info(f"Tiempo estimado por complejidad para {dish.name}: {estimated_time} min (complejidad: {complexity})")
        return estimated_time

    def create_parameters_tab(self):
        param_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(param_frame, text='⚙️ Configuración del Restaurante')
        
        # Crear dos columnas principales
        col1 = ttk.Frame(param_frame)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        col2 = ttk.Frame(param_frame)
        col2.pack(side="left", fill="both", expand=True)

        # === COLUMNA 1: RESTRICCIONES ===
        self.create_restrictions_section(col1)
        self.create_stations_section(col1)
        
        # === COLUMNA 2: PARÁMETROS DE OPTIMIZACIÓN Y TÉCNICAS ===
        self.create_optimization_section(col2)
        self.create_techniques_section(col2)
        
        # Botón de optimización
        btn_frame = ttk.Frame(param_frame)
        btn_frame.pack(side="bottom", fill="x", pady=20)
        ttk.Button(btn_frame, text="🚀 Optimizar Menú del Restaurante", 
                  command=self.run_optimization, style="Accent.TButton").pack(pady=10, ipady=15, fill="x")

    def create_restrictions_section(self, parent):
        """Crear sección de restricciones del restaurante"""
        restric_frame = ttk.LabelFrame(parent, text="📊 Restricciones del Restaurante", padding=15)
        restric_frame.pack(fill="x", pady=(0, 10))
        
        self.vars = {}
        
        # Número deseado de opciones en el menú
        ttk.Label(restric_frame, text="Número deseado de opciones en el menú:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        self.vars["num_platos"] = tk.StringVar(value="6")
        ttk.Entry(restric_frame, textvariable=self.vars["num_platos"], width=15, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Presupuesto máximo de costo por plato
        ttk.Label(restric_frame, text="Presupuesto máximo de costo por plato (MXN):", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        self.vars["costo_max_plato"] = tk.StringVar(value="120.0")
        ttk.Entry(restric_frame, textvariable=self.vars["costo_max_plato"], width=15, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # Capacidad de la cocina y personal disponible
        ttk.Label(restric_frame, text="Personal disponible (cocineros):", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        self.vars["num_cocineros"] = tk.StringVar(value="4")
        ttk.Entry(restric_frame, textvariable=self.vars["num_cocineros"], width=15, font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(10, 0))

    def create_stations_section(self, parent):
        """Crear sección de estaciones de trabajo disponibles"""
        stations_frame = ttk.LabelFrame(parent, text="🏭 Estaciones de Trabajo Disponibles", padding=15)
        stations_frame.pack(fill="x", pady=(10, 0))
        
        # Crear canvas con scrollbar para las estaciones
        stations_canvas = tk.Canvas(stations_frame, height=120)
        stations_scrollbar = ttk.Scrollbar(stations_frame, orient="vertical", command=stations_canvas.yview)
        stations_scrollable_frame = ttk.Frame(stations_canvas)
        
        stations_scrollable_frame.bind(
            "<Configure>",
            lambda e: stations_canvas.configure(scrollregion=stations_canvas.bbox("all"))
        )
        
        stations_canvas.create_window((0, 0), window=stations_scrollable_frame, anchor="nw")
        stations_canvas.configure(yscrollcommand=stations_scrollbar.set)
        
        # Agregar estaciones con checkboxes
        self.station_vars = {}
        stations_per_column = 4
        col = 0
        row = 0
        
        for i, station in enumerate(self.all_stations):
            if i > 0 and i % stations_per_column == 0:
                col += 1
                row = 0
            
            self.station_vars[station] = tk.BooleanVar(value=True)
            ttk.Checkbutton(stations_scrollable_frame, text=station, variable=self.station_vars[station], 
                          style="TCheckbutton").grid(row=row, column=col, sticky="w", padx=15, pady=2)
            row += 1
        
        stations_canvas.pack(side="left", fill="both", expand=True)
        stations_scrollbar.pack(side="right", fill="y")

    def create_techniques_section(self, parent):
        """Crear sección de técnicas culinarias disponibles"""
        tech_frame = ttk.LabelFrame(parent, text="🔧 Técnicas Culinarias Disponibles", padding=15)
        tech_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Crear canvas con scrollbar para las técnicas
        canvas = tk.Canvas(tech_frame, height=120)
        scrollbar = ttk.Scrollbar(tech_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Agregar técnicas con checkboxes
        self.tech_vars = {}
        techniques_per_column = 4
        col = 0
        row = 0
        
        for i, tech in enumerate(sorted(self.all_techniques)):
            if i > 0 and i % techniques_per_column == 0:
                col += 1
                row = 0
            
            self.tech_vars[tech] = tk.BooleanVar(value=True)
            ttk.Checkbutton(scrollable_frame, text=tech, variable=self.tech_vars[tech], 
                          style="TCheckbutton").grid(row=row, column=col, sticky="w", padx=15, pady=2)
            row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_optimization_section(self, parent):
        """Crear sección de parámetros de optimización"""
        optim_frame = ttk.LabelFrame(parent, text="🎯 Parámetros de Optimización", padding=15)
        optim_frame.pack(fill="x", pady=(0, 10))
        
        # Porcentaje mínimo de margen de ganancia
        ttk.Label(optim_frame, text="Porcentaje mínimo de margen de ganancia (%):", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        self.vars["margen_min_pct"] = tk.StringVar(value="45")
        ttk.Entry(optim_frame, textvariable=self.vars["margen_min_pct"], width=15, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Temporada del año para disponibilidad de ingredientes
        ttk.Label(optim_frame, text="Temporada del año:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        self.vars["temporada"] = tk.StringVar(value="Todo el año")
        season_combo = ttk.Combobox(optim_frame, textvariable=self.vars["temporada"], 
                                   values=['Todo el año', 'Primavera', 'Verano', 'Otoño', 'Invierno'], 
                                   state="readonly", width=18, font=("Segoe UI", 10))
        season_combo.grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # Tipo de establecimiento
        ttk.Label(optim_frame, text="Tipo de establecimiento:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        self.vars["tipo_establecimiento"] = tk.StringVar(value="casual")
        establishment_combo = ttk.Combobox(optim_frame, textvariable=self.vars["tipo_establecimiento"], 
                                         values=['casual', 'elegante', 'comida_rapida'], 
                                         state="readonly", width=18, font=("Segoe UI", 10))
        establishment_combo.grid(row=2, column=1, sticky="w", padx=(10, 0))
        
        # Información sobre los presets
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Información de Presets", padding=10)
        info_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        info_text = """Los objetivos de optimización se configuran automáticamente según el tipo de establecimiento:

🍔 CASUAL: Prioriza popularidad y tiempo rápido de preparación
🍷 ELEGANTE: Enfoque en ganancia y calidad, tiempo secundario  
⚡ COMIDA RÁPIDA: Máxima velocidad y eficiencia operativa

Estos presets han sido calibrados para obtener los mejores resultados según el tipo de negocio."""
        
        ttk.Label(info_frame, text=info_text, font=("Segoe UI", 9), justify="left", wraplength=350).pack(anchor="w")

    def create_results_tab(self):
        self.results_notebook = ttk.Notebook(self)
        self.notebook.add(self.results_notebook, text='🏆 Resultados de Optimización')

    def run_optimization(self):
        # 1. Recoger y validar parámetros
        try:
            num_platos = int(self.vars["num_platos"].get())
            costo_max = float(self.vars["costo_max_plato"].get())
            margen_min = float(self.vars["margen_min_pct"].get())
            num_cocineros = int(self.vars["num_cocineros"].get())
            temporada = self.vars["temporada"].get()
            tipo_establecimiento = self.vars["tipo_establecimiento"].get()
            
            # Obtener pesos automáticamente según el tipo de establecimiento
            pesos = self.establishment_presets[tipo_establecimiento].copy()
            
            tecnicas_disponibles = {tech for tech, var in self.tech_vars.items() if var.get()}
            estaciones_disponibles = {station for station, var in self.station_vars.items() if var.get()}
        except ValueError:
            messagebox.showerror("Error", "Por favor, introduce valores numéricos válidos."); return
        
        logging.info("--- INICIANDO NUEVA OPTIMIZACIÓN ---")
        logging.info(f"Parámetros: Platos={num_platos}, Costo Máx={costo_max}, Margen={margen_min}%, Temporada={temporada}")
        logging.info(f"Tipo de establecimiento: {tipo_establecimiento}")
        logging.info(f"Objetivos automáticos: {pesos}")
        logging.info(f"Técnicas disponibles: {tecnicas_disponibles}")
        logging.info(f"Estaciones disponibles: {estaciones_disponibles}")

        # Limpiar resultados anteriores
        for i in reversed(range(self.results_notebook.index('end'))):
            self.results_notebook.forget(i)
        self.notebook.select(1)
        self.update_idletasks()

        # 2. Filtrar catálogo inicial y calcular costos reales
        logging.info(f"Iniciando filtrado de {len(self.catalog)} platos totales...")
        filtered_catalog = []
        
        for dish in self.catalog:
            # Calcular costo real del plato
            real_cost = self.calculate_dish_cost(dish)
            dish._calculated_cost = real_cost  # Guardar costo calculado
            
            # Calcular tiempo real del plato
            real_prep_time = self.calculate_dish_prep_time(dish)
            dish._calculated_prep_time = real_prep_time  # Guardar tiempo calculado
            
            # NUEVO: Filtro por tipo de establecimiento
            if tipo_establecimiento == 'casual':
                # Para casual: rechazar platos moleculares o muy complejos
                if (hasattr(dish, 'tags') and dish.tags and 
                    ('molecular' in dish.tags or 'vanguardista' in dish.tags)) or \
                   (hasattr(dish, 'complexity') and dish.complexity > 6):
                    logging.warning(f"RECHAZADO '{dish.name}': Demasiado complejo para restaurante casual.")
                    continue
                    
                # Para casual: priorizar platos populares y simples
                if hasattr(dish, 'popularity') and dish.popularity < 6:
                    logging.warning(f"RECHAZADO '{dish.name}': Popularidad muy baja para restaurante casual.")
                    continue
                    
            elif tipo_establecimiento == 'comida_rapida':
                # Para comida rápida: solo platos muy rápidos
                if real_prep_time > 30:
                    logging.warning(f"RECHAZADO '{dish.name}': Tiempo de preparación muy largo para comida rápida.")
                    continue
            
            # Chequeo de costo
            if real_cost > costo_max:
                logging.warning(f"RECHAZADO '{dish.name}': Costo ({real_cost:.2f}) > Máximo ({costo_max}).")
                continue
            
            # Chequeo de temporada
            if temporada != 'Todo el año':
                # Verificar si el plato tiene receta e ingredientes
                if hasattr(dish, 'recipe') and dish.recipe:
                    is_in_season = all(ing.season in ('Todo el año', temporada) for ing in dish.recipe.keys())
                    if not is_in_season:
                        logging.warning(f"RECHAZADO '{dish.name}': Fuera de temporada ('{temporada}').")
                        continue
                else:
                    # Si no tiene receta, asumir que está disponible todo el año
                    logging.warning(f"'{dish.name}': Sin receta definida, asumiendo disponibilidad todo el año.")
            
            # Chequeo de técnicas
            if hasattr(dish, 'steps') and dish.steps:
                required_techs = {step.technique for step in dish.steps if step.technique}
                if required_techs and not required_techs.issubset(tecnicas_disponibles):
                    logging.warning(f"RECHAZADO '{dish.name}': Requiere técnicas no disponibles {required_techs - tecnicas_disponibles}.")
                    continue
            
            # Chequeo de estaciones
            if hasattr(dish, 'steps') and dish.steps:
                required_stations = {step.station for step in dish.steps if step.station}
                if required_stations and not required_stations.issubset(estaciones_disponibles):
                    logging.warning(f"RECHAZADO '{dish.name}': Requiere estaciones no disponibles {required_stations - estaciones_disponibles}.")
                    continue
            
            logging.info(f"ACEPTADO '{dish.name}': Costo real=${real_cost:.2f}, Tiempo={real_prep_time}min")
            filtered_catalog.append(dish)

        logging.info(f"Filtrado finalizado. {len(filtered_catalog)} platos cumplen las restricciones.")

        if len(filtered_catalog) < num_platos:
            mensaje = (f"No se encontraron suficientes platos ({len(filtered_catalog)}) para generar un menú de {num_platos} opciones.\n\n"
                       f"Sugerencias:\n"
                       f"  - Reduzca el 'Número de opciones en el menú'\n"
                       f"  - Aumente el 'Presupuesto máximo por plato'\n"
                       f"  - Seleccione más 'Técnicas Culinarias Disponibles'\n"
                       f"  - Seleccione más 'Estaciones de Trabajo Disponibles'\n"
                       f"  - Cambie la 'Temporada' a 'Todo el año'\n\n"
                       f"Consulte el archivo 'app.log' para ver detalles.")
            messagebox.showwarning("Restricciones Demasiado Estrictas", mensaje)
            logging.error("Optimización cancelada: No hay suficientes platos en el catálogo filtrado.")
            return

        # 3. Ejecutar algoritmo genético
        logging.info("Iniciando algoritmo genético...")
        price_factor = 1 + (margen_min / 100)
        population = [create_individual(filtered_catalog, num_platos) for _ in range(100)]
        
        for _ in range(150):
            fitnesses = [calculate_fitness(ind, pesos, price_factor) for ind in population]
            new_population = []
            for _ in range(len(population)):
                p1 = select_parents(population, fitnesses)
                p2 = select_parents(population, fitnesses)
                child = crossover(p1, p2, filtered_catalog)
                child = mutate(child, filtered_catalog)
                new_population.append(child)
            population = new_population

        final_fitnesses = [calculate_fitness(ind, pesos, price_factor) for ind in population]
        sorted_population = sorted(zip(population, final_fitnesses), key=lambda x: x[1], reverse=True)
        
        best_menus = []
        seen_menus = set()
        for menu, fitness in sorted_population:
            if not menu: continue
            menu_signature = tuple(sorted([d.id for d in menu]))
            if menu_signature not in seen_menus:
                best_menus.append((menu, fitness))
                seen_menus.add(menu_signature)
            if len(best_menus) >= 3: break
        
        logging.info(f"Algoritmo finalizado. Se encontraron {len(best_menus)} menús únicos para mostrar.")

        # 4. Mostrar resultados según especificaciones
        if not best_menus:
            messagebox.showinfo("Sin Resultados", "El algoritmo no pudo generar ningún menú. Intente relajar las restricciones."); return
            
        for i, (menu, fitness) in enumerate(best_menus):
            menu_frame = ttk.Frame(self.results_notebook, padding="10")
            self.results_notebook.add(menu_frame, text=f"🏆 Configuración #{i+1} (Aptitud: {fitness:.3f})")
            
            # Crear el reporte completo según las especificaciones
            self.create_specified_report(menu_frame, menu, fitness, price_factor, margen_min, num_cocineros, tipo_establecimiento)

    def create_specified_report(self, parent, menu, fitness, price_factor, margen_min, num_cocineros, tipo_establecimiento):
        """Crea el reporte según las especificaciones exactas del usuario"""
        
        # Validaciones
        if not menu:
            ttk.Label(parent, text="❌ Error: Menú vacío", font=("Segoe UI", 14, "bold")).pack(pady=20)
            return
            
        if price_factor <= 0:
            price_factor = 1.45  # Valor por defecto seguro
            
        # Crear notebook para las tres salidas especificadas
        output_notebook = ttk.Notebook(parent)
        output_notebook.pack(fill="both", expand=True, pady=5)
        
        # === SALIDA 1: TABLA DE MENÚ OPTIMIZADO ===
        menu_tab = ttk.Frame(output_notebook, padding="10")
        output_notebook.add(menu_tab, text="📋 Tabla de Menú Optimizado")
        self.create_optimized_menu_table(menu_tab, menu, price_factor, tipo_establecimiento)
        
        # === SALIDA 2: REPORTE DE EFICIENCIA OPERATIVA ===
        efficiency_tab = ttk.Frame(output_notebook, padding="10")
        output_notebook.add(efficiency_tab, text="⚡ Reporte de Eficiencia Operativa")
        self.create_operational_efficiency_report(efficiency_tab, menu, num_cocineros)
        
        # === SALIDA 3: ANÁLISIS DE INVENTARIO ===
        inventory_tab = ttk.Frame(output_notebook, padding="10")
        output_notebook.add(inventory_tab, text="📦 Análisis de Inventario")
        self.create_inventory_analysis_report(inventory_tab, menu)

    def create_optimized_menu_table(self, parent, menu, price_factor, tipo_establecimiento):
        """SALIDA 1: Tabla de menú optimizado con las tres mejores configuraciones"""
        
        ttk.Label(parent, text="📋 TABLA DE MENÚ OPTIMIZADO", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Información del tipo de establecimiento
        establishment_info = {
            'casual': '🍔 Restaurante Casual - Enfoque en popularidad y rapidez',
            'elegante': '🍷 Restaurante Elegante - Enfoque en calidad y ganancia',
            'comida_rapida': '⚡ Comida Rápida - Máxima eficiencia operativa'
        }
        
        ttk.Label(parent, text=establishment_info.get(tipo_establecimiento, ''), 
                 font=("Segoe UI", 11, "italic")).pack(pady=(0, 10))
        
        # Crear tabla con información detallada
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)
        
        # Configurar Treeview
        columns = ("Plato", "Ingredientes Principales", "Costo Producción", "Precio Sugerido", "Margen Ganancia")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=len(menu) + 2)
        
        # Configurar encabezados y columnas
        tree.heading("Plato", text="Plato")
        tree.heading("Ingredientes Principales", text="Ingredientes Principales")
        tree.heading("Costo Producción", text="Costo Producción")
        tree.heading("Precio Sugerido", text="Precio Sugerido")
        tree.heading("Margen Ganancia", text="Margen Ganancia")
        
        tree.column("Plato", width=200, anchor="w")
        tree.column("Ingredientes Principales", width=300, anchor="w")
        tree.column("Costo Producción", width=120, anchor="center")
        tree.column("Precio Sugerido", width=120, anchor="center")
        tree.column("Margen Ganancia", width=120, anchor="center")
        
        # Agregar datos del menú
        total_cost = 0
        total_revenue = 0
        
        for dish in menu:
            # Usar el costo calculado previamente
            cost = getattr(dish, '_calculated_cost', self.calculate_dish_cost(dish))
            price = cost * price_factor
            margin = ((price - cost) / price) * 100 if price > 0 else 0
            
            # Obtener ingredientes principales (los 3 más costosos)
            main_ingredients = []
            if hasattr(dish, 'recipe') and dish.recipe:
                try:
                    ingredient_costs = []
                    for ing, qty in dish.recipe.items():
                        if hasattr(ing, 'cost_per_kg') and hasattr(ing, 'name'):
                            ing_cost = self.safe_float_conversion(ing.cost_per_kg) * (self.safe_float_conversion(qty)/1000)
                            ingredient_costs.append((ing.name, ing_cost))
                    
                    ingredient_costs.sort(key=lambda x: x[1], reverse=True)
                    main_ingredients = [ing[0] for ing in ingredient_costs[:3]]
                except Exception as e:
                    logging.error(f"Error procesando ingredientes de {dish.name}: {e}")
                    main_ingredients = ["Error al procesar"]
            else:
                main_ingredients = ["Sin receta definida"]
            
            ingredients_text = ", ".join(main_ingredients) if main_ingredients else "N/A"
            
            tree.insert("", "end", values=(
                dish.name[:25] + "..." if len(dish.name) > 25 else dish.name,
                ingredients_text[:35] + "..." if len(ingredients_text) > 35 else ingredients_text,
                f"MXN${cost:.2f}",
                f"MXN${price:.2f}",
                f"{margin:.1f}%"
            ))
            
            total_cost += cost
            total_revenue += price
        
        # Agregar fila de totales
        total_margin = ((total_revenue - total_cost) / total_revenue) * 100 if total_revenue > 0 else 0
        tree.insert("", "end", values=(
            "TOTALES:",
            "",
            f"MXN${total_cost:.2f}",
            f"MXN${total_revenue:.2f}",
            f"{total_margin:.1f}%"
        ), tags=("total",))
        
        # Configurar estilo para totales
        tree.tag_configure("total", background="#E3F2FD", font=("Segoe UI", 9, "bold"))
        
        # Agregar scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empacar elementos
        tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

    def create_operational_efficiency_report(self, parent, menu, num_cocineros):
        """SALIDA 2: Reporte de eficiencia operativa"""
        
        ttk.Label(parent, text="⚡ REPORTE DE EFICIENCIA OPERATIVA", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Crear frame principal con scroll
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True)
        
        # === SECCIÓN 1: TIEMPOS DE PREPARACIÓN ===
        prep_frame = ttk.LabelFrame(main_frame, text="🕒 Tiempos de Preparación Estimados", padding=10)
        prep_frame.pack(fill="x", pady=(0, 10))
        
        # Tabla de tiempos
        prep_columns = ("Plato", "Tiempo Prep. (min)", "Complejidad", "Clasificación")
        prep_tree = ttk.Treeview(prep_frame, columns=prep_columns, show="headings", height=6)
        
        for col in prep_columns:
            prep_tree.heading(col, text=col)
            prep_tree.column(col, width=150, anchor="center")
        
        total_time = 0
        for dish in menu:
            prep_time = getattr(dish, '_calculated_prep_time', self.calculate_dish_prep_time(dish))
            complexity = getattr(dish, 'complexity', 3)
            
            # Clasificar velocidad
            if prep_time <= 15:
                classification = "⚡ Rápido"
            elif prep_time <= 30:
                classification = "🟡 Medio"
            else:
                classification = "🔴 Lento"
            
            prep_tree.insert("", "end", values=(
                dish.name[:20] + "..." if len(dish.name) > 20 else dish.name,
                prep_time,
                f"{complexity}/6",
                classification
            ))
            total_time += prep_time
        
        prep_tree.pack(fill="x")
        
        # Resumen de tiempos
        avg_time = total_time / len(menu) if menu else 0
        ttk.Label(prep_frame, text=f"Tiempo total estimado: {total_time} min | Promedio por plato: {avg_time:.1f} min", 
                 font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
        
        # === SECCIÓN 2: DISTRIBUCIÓN POR ESTACIÓN ===
        station_frame = ttk.LabelFrame(main_frame, text="🏭 Distribución de Carga por Estación", padding=10)
        station_frame.pack(fill="x", pady=(0, 10))
        
        # Calcular uso por estación
        station_usage = defaultdict(int)
        station_time = defaultdict(int)
        
        for dish in menu:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    if hasattr(step, 'station') and step.station:
                        station_usage[step.station] += 1
                        if hasattr(step, 'time'):
                            station_time[step.station] += self.safe_float_conversion(step.time, 0)
        
        # Tabla de estaciones
        station_columns = ("Estación", "Tiempo Total (min)", "% Carga", "Estado")
        station_tree = ttk.Treeview(station_frame, columns=station_columns, show="headings", height=6)
        
        for col in station_columns:
            station_tree.heading(col, text=col)
            station_tree.column(col, width=150, anchor="center")
        
        max_time = max(station_time.values()) if station_time else 1
        
        for station, time_used in sorted(station_time.items(), key=lambda x: x[1], reverse=True):
            percentage = (time_used / max_time) * 100
            
            if percentage > 80:
                status = "🔴 Sobrecargada"
            elif percentage > 60:
                status = "🟡 Ocupada"
            else:
                status = "🟢 Normal"
            
            station_tree.insert("", "end", values=(
                station[:25] + "..." if len(station) > 25 else station,
                time_used,
                f"{percentage:.1f}%",
                status
            ))
        
        station_tree.pack(fill="x")
        
        # === SECCIÓN 3: PROYECCIÓN DE CAPACIDAD ===
        capacity_frame = ttk.LabelFrame(main_frame, text="📊 Proyección de Capacidad de Atención por Hora", padding=10)
        capacity_frame.pack(fill="x", pady=(0, 10))
        
        # Calcular capacidades
        theoretical_capacity = (60 / avg_time) * num_cocineros if avg_time > 0 else 0
        practical_capacity = theoretical_capacity * 0.75  # 75% de eficiencia
        peak_capacity = theoretical_capacity * 0.60  # 60% en hora pico
        daily_capacity = practical_capacity * 8  # 8 horas de servicio
        
        capacity_data = [
            ("Cocineros disponibles", num_cocineros, "Personal asignado en cocina"),
            ("Tiempo promedio prep.", f"{avg_time:.1f} min", "Tiempo medio por plato"),
            ("Capacidad teórica", f"{theoretical_capacity:.0f} platos/h", "Máximo teórico sin interrupciones"),
            ("Capacidad práctica", f"{practical_capacity:.0f} platos/h", "Considerando eficiencia del 75%"),
            ("Capacidad en hora pico", f"{peak_capacity:.0f} platos/h", "Durante períodos de alta demanda"),
            ("Capacidad diaria (8h)", f"{daily_capacity:.0f} platos", "Proyección para jornada completa")
        ]
        
        # Tabla de capacidades
        capacity_columns = ("Métrica", "Valor", "Descripción")
        capacity_tree = ttk.Treeview(capacity_frame, columns=capacity_columns, show="headings", height=6)
        
        capacity_tree.heading("Métrica", text="Métrica")
        capacity_tree.heading("Valor", text="Valor")
        capacity_tree.heading("Descripción", text="Descripción")
        
        capacity_tree.column("Métrica", width=150, anchor="w")
        capacity_tree.column("Valor", width=120, anchor="center")
        capacity_tree.column("Descripción", width=300, anchor="w")
        
        for metric, value, description in capacity_data:
            capacity_tree.insert("", "end", values=(metric, value, description))
        
        capacity_tree.pack(fill="x")

    def create_inventory_analysis_report(self, parent, menu):
        """SALIDA 3: Análisis de inventario"""
        
        ttk.Label(parent, text="📦 ANÁLISIS DE INVENTARIO", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # === SECCIÓN 1: LISTA DE INGREDIENTES ===
        ingredients_frame = ttk.LabelFrame(parent, text="📋 Lista de Ingredientes Necesarios", padding=10)
        ingredients_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Consolidar ingredientes
        ingredient_totals = defaultdict(float)
        ingredient_info = {}
        
        for dish in menu:
            if hasattr(dish, 'recipe') and dish.recipe:
                for ingredient, quantity in dish.recipe.items():
                    if hasattr(ingredient, 'name'):
                        qty = self.safe_float_conversion(quantity, 0)
                        ingredient_totals[ingredient.name] += qty
                        
                        if ingredient.name not in ingredient_info:
                            supplier_name = "N/A"
                            cost_per_kg = 0
                            shelf_life = "N/A"
                            
                            if hasattr(ingredient, 'supplier') and ingredient.supplier:
                                supplier_name = getattr(ingredient.supplier, 'name', 'N/A')
                            
                            if hasattr(ingredient, 'cost_per_kg'):
                                cost_per_kg = self.safe_float_conversion(ingredient.cost_per_kg, 0)
                            
                            if hasattr(ingredient, 'shelf_life_days'):
                                shelf_life = f"{ingredient.shelf_life_days}d"
                            
                            ingredient_info[ingredient.name] = {
                                'supplier': supplier_name,
                                'cost_per_kg': cost_per_kg,
                                'shelf_life': shelf_life
                            }
        
        # Tabla de ingredientes
        ing_columns = ("Ingrediente", "Cantidad Total", "Proveedor", "Costo Total", "Vida Útil")
        ing_tree = ttk.Treeview(ingredients_frame, columns=ing_columns, show="headings", height=8)
        
        for col in ing_columns:
            ing_tree.heading(col, text=col)
        
        ing_tree.column("Ingrediente", width=180, anchor="w")
        ing_tree.column("Cantidad Total", width=120, anchor="center")
        ing_tree.column("Proveedor", width=150, anchor="w")
        ing_tree.column("Costo Total", width=120, anchor="center")
        ing_tree.column("Vida Útil", width=80, anchor="center")
        
        total_inventory_cost = 0
        
        for ingredient_name, total_qty in sorted(ingredient_totals.items()):
            info = ingredient_info.get(ingredient_name, {})
            cost_per_kg = info.get('cost_per_kg', 0)
            total_cost = (total_qty / 1000) * cost_per_kg
            total_inventory_cost += total_cost
            
            ing_tree.insert("", "end", values=(
                ingredient_name[:25] + "..." if len(ingredient_name) > 25 else ingredient_name,
                f"{total_qty:.0f}g",
                info.get('supplier', 'N/A')[:20] + "..." if len(info.get('supplier', 'N/A')) > 20 else info.get('supplier', 'N/A'),
                f"MXN${total_cost:.2f}",
                info.get('shelf_life', 'N/A')
            ))
        
        # Agregar scrollbar
        ing_scrollbar = ttk.Scrollbar(ingredients_frame, orient="vertical", command=ing_tree.yview)
        ing_tree.configure(yscrollcommand=ing_scrollbar.set)
        ing_tree.pack(side="left", fill="both", expand=True)
        ing_scrollbar.pack(side="right", fill="y")
        
        # === SECCIÓN 2: COSTOS TOTALES ===
        costs_frame = ttk.LabelFrame(parent, text="💰 Costos Totales", padding=10)
        costs_frame.pack(fill="x", pady=(10, 10))
        
        # Cálculos de costos
        unique_ingredients = len(ingredient_totals)
        avg_cost_per_ingredient = total_inventory_cost / unique_ingredients if unique_ingredients > 0 else 0
        cost_per_portion = total_inventory_cost / len(menu) if menu else 0
        
        cost_text = f"""📊 RESUMEN DE COSTOS:
• Costo total del inventario: MXN${total_inventory_cost:.2f}
• Número de ingredientes únicos: {unique_ingredients}
• Costo promedio por ingrediente: MXN${avg_cost_per_ingredient:.2f}
• Costo por porción del menú: MXN${cost_per_portion:.2f}"""
        
        ttk.Label(costs_frame, text=cost_text, font=("Segoe UI", 10), justify="left").pack(anchor="w")
        
        # Top 5 ingredientes más costosos
        top_ingredients = sorted(
            [(name, (qty/1000) * ingredient_info.get(name, {}).get('cost_per_kg', 0)) 
             for name, qty in ingredient_totals.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        if top_ingredients:
            top_text = "\n🔝 TOP 5 INGREDIENTES MÁS COSTOSOS:\n"
            for i, (name, cost) in enumerate(top_ingredients, 1):
                top_text += f"{i}. {name}: MXN${cost:.2f}\n"
            
            ttk.Label(costs_frame, text=top_text, font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=(10, 0))
        
        # === SECCIÓN 3: RECOMENDACIONES ===
        recommendations_frame = ttk.LabelFrame(parent, text="💡 Recomendaciones para Minimizar Desperdicio", padding=10)
        recommendations_frame.pack(fill="x", pady=(10, 0))
        
        recommendations_text = """🔄 ESTRATEGIAS DE ROTACIÓN:
• Método FIFO (First In, First Out) para todos los ingredientes perecederos
• Etiquetado con fechas de recepción y vencimiento
• Revisión diaria del inventario y programación de menús según proximidad de vencimiento

📋 RECOMENDACIONES ESPECÍFICAS:
• Optimizar pedidos basados en vida útil y rotación
• Implementar sistema de alertas para ingredientes próximos a vencer
• Considerar preparaciones que utilicen múltiples ingredientes del menú
• Establecer políticas de descuento para platos con ingredientes próximos a vencer"""
        
        ttk.Label(recommendations_frame, text=recommendations_text, font=("Segoe UI", 9), justify="left", wraplength=700).pack(anchor="w")