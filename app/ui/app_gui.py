# app/ui/app_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from collections import defaultdict
import logging
from app.core.genetic_algorithm import create_individual, calculate_fitness, select_parents, crossover, mutate

class MenuOptimizerApp(tk.Tk):
    def __init__(self, catalog, all_techniques):
        super().__init__()
        if not catalog: self.destroy(); return
        
        self.catalog = catalog
        self.all_techniques = all_techniques
        
        self.title("MENUOPTIMIZER v9.2 - Final Fix"); self.geometry("1200x900")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.create_parameters_tab()
        self.create_results_tab()

    def create_parameters_tab(self):
        param_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(param_frame, text='⚙️ 1. Configuración y Objetivos')
        
        col1 = ttk.Frame(param_frame); col1.pack(side="left", fill="y", padx=(0, 10))
        col2 = ttk.Frame(param_frame); col2.pack(side="left", fill="both", expand=True)

        # --- Restricciones ---
        restric_frame = ttk.LabelFrame(col1, text="Restricciones", padding=10)
        restric_frame.pack(fill="x", pady=5)
        self.vars = {
            "num_platos": tk.StringVar(value="5"),
            "costo_max_plato": tk.StringVar(value="150.0"),
            "margen_min_pct": tk.StringVar(value="50"),
            "num_cocineros": tk.StringVar(value="3"),
            "temporada": tk.StringVar(value="Todo el año")
        }
        ttk.Label(restric_frame, text="Platos en Menú:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(restric_frame, textvariable=self.vars["num_platos"], width=10).grid(row=0, column=1)
        ttk.Label(restric_frame, text="Costo Máx. Plato:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(restric_frame, textvariable=self.vars["costo_max_plato"], width=10).grid(row=1, column=1)
        ttk.Label(restric_frame, text="Margen Mínimo (%):").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(restric_frame, textvariable=self.vars["margen_min_pct"], width=10).grid(row=2, column=1)
        ttk.Label(restric_frame, text="Nº Cocineros:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(restric_frame, textvariable=self.vars["num_cocineros"], width=10).grid(row=3, column=1)
        ttk.Label(restric_frame, text="Temporada:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Combobox(restric_frame, textvariable=self.vars["temporada"], values=['Todo el año', 'Primavera', 'Verano', 'Otoño', 'Invierno'], state="readonly", width=12).grid(row=4, column=1)

        # --- Filtros de Técnicas ---
        tech_frame = ttk.LabelFrame(col1, text="Técnicas Culinarias Disponibles", padding=10)
        tech_frame.pack(fill="x", pady=10)
        self.tech_vars = {tech: tk.BooleanVar(value=True) for tech in self.all_techniques}
        for tech, var in self.tech_vars.items():
            ttk.Checkbutton(tech_frame, text=tech, variable=var).pack(anchor="w")

        # --- Prioridades (Objetivos) ---
        weights_frame = ttk.LabelFrame(col2, text="Prioridades (Objetivos)", padding=10)
        weights_frame.pack(fill="both", expand=True, pady=5)
        self.weights = {}
        obj = {"ganancia": "Maximizar Ganancia", "tiempo": "Minimizar Tiempo Prep.", "popularidad": "Maximizar Popularidad", "desperdicio": "Minimizar Desperdicio"}
        for i, (key, label) in enumerate(obj.items()):
            ttk.Label(weights_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=8)
            self.weights[key] = tk.DoubleVar(value=0.5)
            ttk.Scale(weights_frame, from_=0.0, to=1.0, variable=self.weights[key]).grid(row=i, column=1, sticky="ew", padx=5)
        
        ttk.Button(col2, text="🚀 Optimizar Menú", command=self.run_optimization).pack(pady=20, ipady=10, fill="x")

    def create_results_tab(self):
        self.results_notebook = ttk.Notebook(self)
        self.notebook.add(self.results_notebook, text='🏆 2. Resultados de Optimización')

    def run_optimization(self):
        # 1. Recoger y validar parámetros
        try:
            num_platos = int(self.vars["num_platos"].get())
            costo_max = float(self.vars["costo_max_plato"].get())
            margen_min = float(self.vars["margen_min_pct"].get())
            temporada = self.vars["temporada"].get()
            pesos = {k: v.get() for k, v in self.weights.items()}
            tecnicas_disponibles = {tech for tech, var in self.tech_vars.items() if var.get()}
        except ValueError:
            messagebox.showerror("Error", "Por favor, introduce valores numéricos válidos."); return
        
        logging.info("--- INICIANDO NUEVA OPTIMIZACIÓN ---")
        logging.info(f"Parámetros: Platos={num_platos}, Costo Máx={costo_max}, Margen={margen_min}%, Temporada={temporada}")
        logging.info(f"Técnicas disponibles: {tecnicas_disponibles}")

        # Limpiar resultados anteriores
        for i in reversed(range(self.results_notebook.index('end'))):
            self.results_notebook.forget(i)
        self.notebook.select(1)
        self.update_idletasks()

        # 2. Filtrar catálogo inicial
        logging.info(f"Iniciando filtrado de {len(self.catalog)} platos totales...")
        filtered_catalog = []
        for dish in self.catalog:
            # Chequeo de costo
            if dish.cost > costo_max:
                logging.warning(f"RECHAZADO '{dish.name}': Costo ({dish.cost:.2f}) > Máximo ({costo_max}).")
                continue
            
            # --- CORRECCIÓN 1: Lógica de la temporada ---
            if temporada != 'Todo el año':
                is_in_season = all(ing.season in ('Todo el año', temporada) for ing in dish.recipe.keys())
                if not is_in_season:
                    logging.warning(f"RECHAZADO '{dish.name}': Fuera de temporada ('{temporada}').")
                    continue
                
            # Chequeo de técnicas
            required_techs = {step.technique for step in dish.steps if step.technique}
            if not required_techs.issubset(tecnicas_disponibles):
                logging.warning(f"RECHAZADO '{dish.name}': Requiere técnicas no disponibles {required_techs - tecnicas_disponibles}.")
                continue
            
            logging.info(f"ACEPTADO '{dish.name}': Cumple todas las restricciones.")
            filtered_catalog.append(dish)

        logging.info(f"Filtrado finalizado. {len(filtered_catalog)} platos cumplen las restricciones.")

        if len(filtered_catalog) < num_platos:
            mensaje = (f"No se encontraron suficientes platos ({len(filtered_catalog)}) para generar un menú de {num_platos} opciones "
                       f"que cumplan TODAS las restricciones (costo, temporada, técnicas, etc.).\n\n"
                       f"Sugerencias:\n"
                       f"  - Reduzca el 'Número de Platos en Menú'.\n"
                       f"  - Aumente el 'Costo Máx. Plato'.\n"
                       f"  - Seleccione más 'Técnicas Culinarias Disponibles'.\n\n"
                       f"Consulte el archivo 'app.log' para ver en detalle por qué se rechazó cada plato.")
            messagebox.showwarning("Filtros Demasiado Estrictos", mensaje)
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

        # 4. Mostrar resultados
        if not best_menus:
            messagebox.showinfo("Sin Resultados", "El algoritmo no pudo generar ningún menú. Intente relajar las restricciones."); return
            
        for i, (menu, fitness) in enumerate(best_menus):
            menu_frame = ttk.Frame(self.results_notebook, padding="10")
            self.results_notebook.add(menu_frame, text=f"Opción #{i+1} (Aptitud: {fitness:.3f})")
            
            # Crear reporte de inventario
            self.create_inventory_report(menu_frame, menu, "MXN$")

    def create_inventory_report(self, parent, menu, currency):
        ttk.Label(parent, text="🛒 Análisis de Inventario", font=("Segoe UI", 12, "bold")).pack(pady=(0, 5), anchor="w")

        txt = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=("Courier New", 9))
        txt.pack(fill="both", expand=True)
        
        inventory = defaultdict(lambda: {'qty': 0, 'cost': 0, 'obj': None})
        for dish in menu:
            for ing_obj, qty in dish.recipe.items():
                inventory[ing_obj.name]['qty'] += qty
                # --- CORRECCIÓN 2: Usar el atributo correcto 'cost_per_kg' ---
                inventory[ing_obj.name]['cost'] += float(ing_obj.cost_per_kg) * (qty / 1000)
                inventory[ing_obj.name]['obj'] = ing_obj

        header = f"{'Ingrediente':<25}|{'Proveedor':<25}|{'Cantidad':<15}|{'Costo':<15}\n"
        txt.insert(tk.INSERT, header, ("bold",))
        txt.insert(tk.INSERT, "-" * len(header) + "\n")

        total_cost = 0
        for name, data in sorted(inventory.items()):
            ing_obj = data['obj']
            supplier_name = ing_obj.supplier.name if ing_obj.supplier else "N/A"
            line = f"{name:<25}|{supplier_name:<25}|{data['qty']:.0f} gr{'':<10}|{currency}{data['cost']:.2f}\n"
            txt.insert(tk.INSERT, line)
            total_cost += data['cost']
        
        txt.insert(tk.INSERT, "-" * len(header) + "\n")
        total_line = f"{'COSTO TOTAL INVENTARIO:':<67}{currency}{total_cost:.2f}\n"
        txt.insert(tk.INSERT, total_line, ("bold",))
        
        txt.config(state="disabled")
        txt.tag_config("bold", font=("Courier New", 9, "bold"))