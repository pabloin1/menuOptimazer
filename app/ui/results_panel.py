# app/ui/results_panel.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

from app.core.models import Dish


class ResultsPanel(ttk.Frame):
    """
    Panel para mostrar los resultados de la optimización.
    Incluye las tres salidas especificadas en la propuesta.
    """
    
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        
        self.current_results = None
        self._create_interface()
    
    def _create_interface(self):
        """Crea la interfaz del panel de resultados."""
        # Crear notebook para las diferentes vistas de resultados
        self.results_notebook = ttk.Notebook(self)
        self.results_notebook.pack(fill="both", expand=True)
        
        # Mensaje inicial
        self.initial_message = ttk.Label(
            self, 
            text="🎯 Ejecute la optimización para ver los resultados aquí",
            font=("Segoe UI", 14),
            foreground="gray"
        )
        self.initial_message.pack(expand=True)
    
    def display_results(self, results: Dict):
        """
        Muestra los resultados de la optimización.
        
        Args:
            results: Diccionario con resultados de optimización
        """
        self.current_results = results
        
        # Ocultar mensaje inicial
        self.initial_message.pack_forget()
        
        # Limpiar notebook existente
        for i in reversed(range(self.results_notebook.index('end'))):
            self.results_notebook.forget(i)
        
        # Crear pestañas para cada solución
        solutions = results['solutions']
        config = results['config']
        
        for i, (menu, fitness) in enumerate(solutions):
            # Crear frame para esta solución
            solution_frame = ttk.Frame(self.results_notebook, padding="10")
            self.results_notebook.add(solution_frame, 
                                    text=f"🏆 Solución #{i+1} (Fitness: {fitness:.3f})")
            
            # Crear notebook interno para las tres salidas
            internal_notebook = ttk.Notebook(solution_frame)
            internal_notebook.pack(fill="both", expand=True, pady=5)
            
            # SALIDA 1: Tabla de menú optimizado
            menu_tab = ttk.Frame(internal_notebook, padding="10")
            internal_notebook.add(menu_tab, text="📋 Menú Optimizado")
            self._create_optimized_menu_table(menu_tab, menu, config)
            
            # SALIDA 2: Reporte de eficiencia operativa
            efficiency_tab = ttk.Frame(internal_notebook, padding="10")
            internal_notebook.add(efficiency_tab, text="⚡ Eficiencia Operativa")
            self._create_operational_efficiency_report(efficiency_tab, menu, config)
            
            # SALIDA 3: Análisis de inventario
            inventory_tab = ttk.Frame(internal_notebook, padding="10")
            internal_notebook.add(inventory_tab, text="📦 Análisis de Inventario")
            self._create_inventory_analysis_report(inventory_tab, menu)
        
        # Pestaña adicional con estadísticas del algoritmo
        stats_tab = ttk.Frame(self.results_notebook, padding="10")
        self.results_notebook.add(stats_tab, text="📊 Estadísticas del Algoritmo")
        self._create_algorithm_statistics(stats_tab, results.get('algorithm_stats', {}))
    
    def _create_optimized_menu_table(self, parent, menu: List[Dish], config: Dict):
        """SALIDA 1: Tabla de menú optimizado."""
        # Título y descripción
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(title_frame, text="📋 TABLA DE MENÚ OPTIMIZADO", 
                 font=("Segoe UI", 16, "bold")).pack()
        
        establishment_descriptions = {
            'casual': '🍔 Restaurante Casual - Enfoque en popularidad y rapidez',
            'elegante': '🍷 Restaurante Elegante - Enfoque en calidad y ganancia',
            'comida_rapida': '⚡ Comida Rápida - Máxima eficiencia operativa'
        }
        
        description = establishment_descriptions.get(config['establishment_type'], '')
        ttk.Label(title_frame, text=description, 
                 font=("Segoe UI", 11, "italic")).pack(pady=(5, 0))
        
        # Frame para la tabla con scrollbars
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)
        
        # Configurar Treeview
        columns = ("Plato", "Ingredientes Principales", "Costo Producción", 
                  "Precio Sugerido", "Margen Ganancia", "Tiempo Prep.")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # Configurar encabezados
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Plato", width=200, anchor="w")
        tree.column("Ingredientes Principales", width=250, anchor="w")
        tree.column("Costo Producción", width=120, anchor="center")
        tree.column("Precio Sugerido", width=120, anchor="center")
        tree.column("Margen Ganancia", width=120, anchor="center")
        tree.column("Tiempo Prep.", width=100, anchor="center")
        
        # Calcular factor de precio
        min_margin = config['min_profit_margin']
        price_factor = 1 / (1 - min_margin / 100) if min_margin < 100 else 1.5
        
        # Agregar datos del menú
        total_cost = 0
        total_revenue = 0
        total_time = 0
        
        for dish in menu:
            cost = self._get_dish_cost(dish)
            price = cost * price_factor
            margin = ((price - cost) / price) * 100 if price > 0 else 0
            prep_time = self._get_dish_prep_time(dish)
            
            # Obtener ingredientes principales
            main_ingredients = self._get_main_ingredients(dish, num_ingredients=3)
            ingredients_text = ", ".join(main_ingredients) if main_ingredients else "N/A"
            
            tree.insert("", "end", values=(
                dish.name[:30] + "..." if len(dish.name) > 30 else dish.name,
                ingredients_text[:40] + "..." if len(ingredients_text) > 40 else ingredients_text,
                f"${cost:.2f}",
                f"${price:.2f}",
                f"{margin:.1f}%",
                f"{prep_time:.0f}min"
            ))
            
            total_cost += cost
            total_revenue += price
            total_time += prep_time
        
        # Agregar fila de totales
        total_margin = ((total_revenue - total_cost) / total_revenue) * 100 if total_revenue > 0 else 0
        avg_time = total_time / len(menu) if menu else 0
        
        tree.insert("", "end", values=(
            "TOTALES:",
            f"{len(menu)} platos",
            f"${total_cost:.2f}",
            f"${total_revenue:.2f}",
            f"{total_margin:.1f}%",
            f"{avg_time:.0f}min prom."
        ), tags=("total",))
        
        # Configurar estilo para totales
        tree.tag_configure("total", background="#E3F2FD", font=("Segoe UI", 9, "bold"))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empacar elementos
        tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Resumen financiero
        summary_frame = ttk.LabelFrame(parent, text="💰 Resumen Financiero", padding=10)
        summary_frame.pack(fill="x", pady=(15, 0))
        
        summary_text = (f"💵 Inversión total en ingredientes: ${total_cost:.2f} MXN\n"
                       f"💰 Ingresos proyectados: ${total_revenue:.2f} MXN\n"
                       f"📈 Ganancia neta: ${total_revenue - total_cost:.2f} MXN\n"
                       f"📊 Margen de ganancia promedio: {total_margin:.1f}%\n"
                       f"⏱️ Tiempo promedio de preparación: {avg_time:.1f} minutos")
        
        ttk.Label(summary_frame, text=summary_text, font=("Segoe UI", 10), 
                 justify="left").pack(anchor="w")
    
    def _create_operational_efficiency_report(self, parent, menu: List[Dish], config: Dict):
        """SALIDA 2: Reporte de eficiencia operativa."""
        # Título
        ttk.Label(parent, text="⚡ REPORTE DE EFICIENCIA OPERATIVA", 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Frame principal con scroll
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True)
        
        # Crear notebook para subsecciones
        efficiency_notebook = ttk.Notebook(main_frame)
        efficiency_notebook.pack(fill="both", expand=True)
        
        # Subsección 1: Tiempos de preparación
        times_frame = ttk.Frame(efficiency_notebook, padding="10")
        efficiency_notebook.add(times_frame, text="🕒 Tiempos de Preparación")
        self._create_preparation_times_section(times_frame, menu)
        
        # Subsección 2: Distribución por estación
        stations_frame = ttk.Frame(efficiency_notebook, padding="10")
        efficiency_notebook.add(stations_frame, text="🏭 Distribución por Estación")
        self._create_station_distribution_section(stations_frame, menu)
        
        # Subsección 3: Capacidad operativa
        capacity_frame = ttk.Frame(efficiency_notebook, padding="10")
        efficiency_notebook.add(capacity_frame, text="📊 Capacidad Operativa")
        self._create_capacity_projection_section(capacity_frame, menu, config)
    
    def _create_preparation_times_section(self, parent, menu: List[Dish]):
        """Crea la sección de tiempos de preparación."""
        # Tabla de tiempos
        columns = ("Plato", "Tiempo (min)", "Complejidad", "Clasificación")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        total_time = 0
        time_classifications = []
        
        for dish in menu:
            prep_time = self._get_dish_prep_time(dish)
            complexity = getattr(dish, 'complexity', 3)
            
            # Clasificar velocidad
            if prep_time <= 15:
                classification = "⚡ Rápido"
                color_tag = "fast"
            elif prep_time <= 30:
                classification = "🟡 Medio"
                color_tag = "medium"
            else:
                classification = "🔴 Lento"
                color_tag = "slow"
            
            time_classifications.append(classification)
            
            tree.insert("", "end", values=(
                dish.name[:25] + "..." if len(dish.name) > 25 else dish.name,
                f"{prep_time:.0f}",
                f"{complexity}/10",
                classification
            ), tags=(color_tag,))
            
            total_time += prep_time
        
        # Configurar colores
        tree.tag_configure("fast", background="#d4edda")
        tree.tag_configure("medium", background="#fff3cd")
        tree.tag_configure("slow", background="#f8d7da")
        
        tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Resumen de tiempos
        avg_time = total_time / len(menu) if menu else 0
        fast_count = time_classifications.count("⚡ Rápido")
        medium_count = time_classifications.count("🟡 Medio")
        slow_count = time_classifications.count("🔴 Lento")
        
        summary_text = (f"📊 RESUMEN DE TIEMPOS:\n"
                       f"• Tiempo total estimado: {total_time:.0f} minutos\n"
                       f"• Tiempo promedio por plato: {avg_time:.1f} minutos\n"
                       f"• Distribución: {fast_count} rápidos, {medium_count} medios, {slow_count} lentos")
        
        ttk.Label(parent, text=summary_text, font=("Segoe UI", 10), 
                 justify="left").pack(anchor="w", pady=(10, 0))
    
    def _create_station_distribution_section(self, parent, menu: List[Dish]):
        """Crea la sección de distribución por estación."""
        # Calcular uso por estación
        station_usage = defaultdict(int)
        station_time = defaultdict(float)
        
        for dish in menu:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    if hasattr(step, 'station') and step.station:
                        station_usage[step.station] += 1
                        if hasattr(step, 'time'):
                            station_time[step.station] += float(getattr(step, 'time', 0))
        
        if not station_time:
            ttk.Label(parent, text="ℹ️ No hay información detallada de estaciones disponible.", 
                     font=("Segoe UI", 12)).pack(expand=True)
            return
        
        # Tabla de estaciones
        columns = ("Estación", "Tiempo Total (min)", "% Carga", "Estado")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        max_time = max(station_time.values()) if station_time else 1
        
        for station, time_used in sorted(station_time.items(), key=lambda x: x[1], reverse=True):
            percentage = (time_used / max_time) * 100
            
            if percentage > 80:
                status = "🔴 Sobrecargada"
                color_tag = "overloaded"
            elif percentage > 60:
                status = "🟡 Ocupada"
                color_tag = "busy"
            else:
                status = "🟢 Normal"
                color_tag = "normal"
            
            tree.insert("", "end", values=(
                station[:30] + "..." if len(station) > 30 else station,
                f"{time_used:.0f}",
                f"{percentage:.1f}%",
                status
            ), tags=(color_tag,))
        
        # Configurar colores
        tree.tag_configure("overloaded", background="#f8d7da")
        tree.tag_configure("busy", background="#fff3cd")
        tree.tag_configure("normal", background="#d4edda")
        
        tree.pack(fill="both", expand=True)
    
    def _create_capacity_projection_section(self, parent, menu: List[Dish], config: Dict):
        """Crea la sección de proyección de capacidad."""
        # Calcular métricas de capacidad
        total_prep_time = sum(self._get_dish_prep_time(dish) for dish in menu)
        avg_prep_time = total_prep_time / len(menu) if menu else 0
        num_chefs = config.get('num_chefs', 4)
        
        # Capacidades
        theoretical_capacity = (60 / avg_prep_time) * num_chefs if avg_prep_time > 0 else 0
        practical_capacity = theoretical_capacity * 0.75  # 75% eficiencia
        peak_capacity = theoretical_capacity * 0.60  # 60% en hora pico
        daily_capacity = practical_capacity * 8  # 8 horas de servicio
        
        # Tabla de capacidades
        columns = ("Métrica", "Valor", "Descripción")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=8)
        
        tree.heading("Métrica", text="Métrica")
        tree.heading("Valor", text="Valor")
        tree.heading("Descripción", text="Descripción")
        
        tree.column("Métrica", width=200, anchor="w")
        tree.column("Valor", width=150, anchor="center")
        tree.column("Descripción", width=300, anchor="w")
        
        capacity_data = [
            ("Cocineros disponibles", f"{num_chefs}", "Personal asignado en cocina"),
            ("Tiempo promedio prep.", f"{avg_prep_time:.1f} min", "Tiempo medio por plato"),
            ("Capacidad teórica", f"{theoretical_capacity:.0f} platos/h", "Máximo teórico sin interrupciones"),
            ("Capacidad práctica", f"{practical_capacity:.0f} platos/h", "Considerando eficiencia del 75%"),
            ("Capacidad en hora pico", f"{peak_capacity:.0f} platos/h", "Durante períodos de alta demanda"),
            ("Capacidad diaria (8h)", f"{daily_capacity:.0f} platos", "Proyección para jornada completa"),
            ("Eficiencia del menú", f"{(1/avg_prep_time)*60:.1f}", "Platos por hora por cocinero")
        ]
        
        for metric, value, description in capacity_data:
            tree.insert("", "end", values=(metric, value, description))
        
        tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Recomendaciones operativas
        recommendations_frame = ttk.LabelFrame(parent, text="💡 Recomendaciones Operativas", padding=10)
        recommendations_frame.pack(fill="x", pady=(10, 0))
        
        if avg_prep_time > 25:
            efficiency_status = "⚠️ ATENCIÓN: Tiempo promedio alto"
            recommendations = [
                "• Considere pre-preparar ingredientes comunes",
                "• Implemente mise en place más eficiente",
                "• Evalúe agregar personal en horas pico"
            ]
        elif avg_prep_time < 15:
            efficiency_status = "✅ EXCELENTE: Tiempos muy eficientes"
            recommendations = [
                "• Mantenga los estándares actuales",
                "• Considere aumentar la complejidad del menú",
                "• Evalúe expandir la capacidad de servicio"
            ]
        else:
            efficiency_status = "✅ BUENO: Tiempos balanceados"
            recommendations = [
                "• Monitoree tiempos durante servicio",
                "• Implemente mejora continua",
                "• Considere capacitación cruzada del personal"
            ]
        
        recommendations_text = efficiency_status + "\n\n" + "\n".join(recommendations)
        ttk.Label(recommendations_frame, text=recommendations_text, 
                 font=("Segoe UI", 9), justify="left").pack(anchor="w")
    
    def _create_inventory_analysis_report(self, parent, menu: List[Dish]):
        """SALIDA 3: Análisis de inventario."""
        # Título
        ttk.Label(parent, text="📦 ANÁLISIS DE INVENTARIO", 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Consolidar ingredientes
        ingredient_totals = defaultdict(float)
        ingredient_info = {}
        
        for dish in menu:
            if hasattr(dish, 'recipe') and dish.recipe:
                for ingredient, quantity in dish.recipe.items():
                    if hasattr(ingredient, 'name'):
                        qty = float(quantity) if quantity else 0
                        ingredient_totals[ingredient.name] += qty
                        
                        if ingredient.name not in ingredient_info:
                            ingredient_info[ingredient.name] = {
                                'supplier': getattr(getattr(ingredient, 'supplier', None), 'name', 'N/A'),
                                'cost_per_kg': float(getattr(ingredient, 'cost_per_kg', 0)),
                                'shelf_life': f"{getattr(ingredient, 'shelf_life_days', 'N/A')}d" 
                                             if hasattr(ingredient, 'shelf_life_days') else 'N/A',
                                'season': getattr(ingredient, 'season', 'N/A')
                            }
        
        # Crear notebook para subsecciones
        inventory_notebook = ttk.Notebook(parent)
        inventory_notebook.pack(fill="both", expand=True)
        
        # Subsección 1: Lista de ingredientes
        ingredients_frame = ttk.Frame(inventory_notebook, padding="10")
        inventory_notebook.add(ingredients_frame, text="📋 Lista de Ingredientes")
        self._create_ingredients_list(ingredients_frame, ingredient_totals, ingredient_info)
        
        # Subsección 2: Análisis de costos
        costs_frame = ttk.Frame(inventory_notebook, padding="10")
        inventory_notebook.add(costs_frame, text="💰 Análisis de Costos")
        self._create_costs_analysis(costs_frame, ingredient_totals, ingredient_info)
        
        # Subsección 3: Recomendaciones
        recommendations_frame = ttk.Frame(inventory_notebook, padding="10")
        inventory_notebook.add(recommendations_frame, text="💡 Recomendaciones")
        self._create_inventory_recommendations(recommendations_frame, ingredient_totals, ingredient_info)
    
    def _create_ingredients_list(self, parent, ingredient_totals: Dict, ingredient_info: Dict):
        """Crea la lista detallada de ingredientes."""
        # Tabla de ingredientes
        columns = ("Ingrediente", "Cantidad Total", "Proveedor", "Costo Total", "Vida Útil", "Temporada")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Ingrediente", width=180, anchor="w")
        tree.column("Cantidad Total", width=120, anchor="center")
        tree.column("Proveedor", width=150, anchor="w")
        tree.column("Costo Total", width=120, anchor="center")
        tree.column("Vida Útil", width=80, anchor="center")
        tree.column("Temporada", width=100, anchor="center")
        
        total_inventory_cost = 0
        
        for ingredient_name, total_qty in sorted(ingredient_totals.items()):
            info = ingredient_info.get(ingredient_name, {})
            cost_per_kg = info.get('cost_per_kg', 0)
            total_cost = (total_qty / 1000) * cost_per_kg
            total_inventory_cost += total_cost
            
            tree.insert("", "end", values=(
                ingredient_name[:25] + "..." if len(ingredient_name) > 25 else ingredient_name,
                f"{total_qty:.0f}g",
                info.get('supplier', 'N/A')[:20] + "..." if len(info.get('supplier', 'N/A')) > 20 else info.get('supplier', 'N/A'),
                f"${total_cost:.2f}",
                info.get('shelf_life', 'N/A'),
                info.get('season', 'N/A')
            ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Resumen
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill="x", pady=(10, 0))
        
        unique_ingredients = len(ingredient_totals)
        avg_cost_per_ingredient = total_inventory_cost / unique_ingredients if unique_ingredients > 0 else 0
        
        summary_text = (f"📊 RESUMEN:\n"
                       f"• Ingredientes únicos: {unique_ingredients}\n"
                       f"• Costo total del inventario: ${total_inventory_cost:.2f} MXN\n"
                       f"• Costo promedio por ingrediente: ${avg_cost_per_ingredient:.2f} MXN")
        
        ttk.Label(summary_frame, text=summary_text, font=("Segoe UI", 10), 
                 justify="left").pack(anchor="w")
    
    def _create_costs_analysis(self, parent, ingredient_totals: Dict, ingredient_info: Dict):
        """Crea el análisis de costos detallado."""
        # Calcular métricas de costo
        total_cost = sum((qty/1000) * ingredient_info.get(name, {}).get('cost_per_kg', 0) 
                        for name, qty in ingredient_totals.items())
        
        # Top 10 ingredientes más costosos
        ingredient_costs = []
        for name, qty in ingredient_totals.items():
            cost_per_kg = ingredient_info.get(name, {}).get('cost_per_kg', 0)
            total_ing_cost = (qty/1000) * cost_per_kg
            ingredient_costs.append((name, total_ing_cost, qty))
        
        top_ingredients = sorted(ingredient_costs, key=lambda x: x[1], reverse=True)[:10]
        
        # Tabla de top ingredientes
        columns = ("Ranking", "Ingrediente", "Costo Total", "Cantidad", "% del Total")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Ranking", width=80, anchor="center")
        tree.column("Ingrediente", width=200, anchor="w")
        tree.column("Costo Total", width=120, anchor="center")
        tree.column("Cantidad", width=120, anchor="center")
        tree.column("% del Total", width=100, anchor="center")
        
        for i, (name, cost, qty) in enumerate(top_ingredients, 1):
            percentage = (cost / total_cost) * 100 if total_cost > 0 else 0
            tree.insert("", "end", values=(
                f"#{i}",
                name[:25] + "..." if len(name) > 25 else name,
                f"${cost:.2f}",
                f"{qty:.0f}g",
                f"{percentage:.1f}%"
            ))
        
        tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Análisis de distribución de costos
        analysis_frame = ttk.LabelFrame(parent, text="📊 Distribución de Costos", padding=10)
        analysis_frame.pack(fill="x", pady=(10, 0))
        
        if len(top_ingredients) >= 5:
            top_5_cost = sum(cost for _, cost, _ in top_ingredients[:5])
            top_5_percentage = (top_5_cost / total_cost) * 100 if total_cost > 0 else 0
            
            analysis_text = (f"💡 ANÁLISIS DE PARETO:\n"
                           f"• Los 5 ingredientes más costosos representan {top_5_percentage:.1f}% del costo total\n"
                           f"• Costo de top 5: ${top_5_cost:.2f} de ${total_cost:.2f} total\n"
                           f"• Recomendación: Enfocarse en negociar mejores precios para estos ingredientes")
        else:
            analysis_text = (f"📊 DISTRIBUCIÓN EQUILIBRADA:\n"
                           f"• Los costos están bien distribuidos entre ingredientes\n"
                           f"• No hay ingredientes que dominen el presupuesto\n"
                           f"• Costo total del inventario: ${total_cost:.2f}")
        
        ttk.Label(analysis_frame, text=analysis_text, font=("Segoe UI", 9), 
                 justify="left").pack(anchor="w")
    
    def _create_inventory_recommendations(self, parent, ingredient_totals: Dict, ingredient_info: Dict):
        """Crea las recomendaciones de inventario."""
        # Analizar patrones de vida útil
        short_shelf_life = []
        seasonal_ingredients = []
        high_cost_ingredients = []
        
        for name, qty in ingredient_totals.items():
            info = ingredient_info.get(name, {})
            
            # Analizar vida útil
            shelf_life = info.get('shelf_life', 'N/A')
            if shelf_life != 'N/A' and 'd' in shelf_life:
                try:
                    days = int(shelf_life.replace('d', ''))
                    if days <= 7:
                        short_shelf_life.append((name, days, qty))
                except:
                    pass
            
            # Analizar estacionalidad
            season = info.get('season', 'Todo el año')
            if season != 'Todo el año':
                seasonal_ingredients.append((name, season, qty))
            
            # Analizar costo alto
            cost_per_kg = info.get('cost_per_kg', 0)
            if cost_per_kg > 200:  # Ingredientes costosos
                total_cost = (qty/1000) * cost_per_kg
                high_cost_ingredients.append((name, cost_per_kg, total_cost))
        
        # Crear secciones de recomendaciones
        # 1. Ingredientes perecederos
        if short_shelf_life:
            perishable_frame = ttk.LabelFrame(parent, text="⚠️ Ingredientes Perecederos", padding=10)
            perishable_frame.pack(fill="x", pady=(0, 10))
            
            perishable_text = "🔄 ROTACIÓN RÁPIDA REQUERIDA:\n"
            for name, days, qty in sorted(short_shelf_life, key=lambda x: x[1]):
                perishable_text += f"• {name}: {days} días de vida útil ({qty:.0f}g)\n"
            
            perishable_text += ("\n💡 Recomendaciones:\n"
                              "• Implementar sistema FIFO estricto\n"
                              "• Pedidos más frecuentes en menores cantidades\n"
                              "• Monitoreo diario de fechas de vencimiento")
            
            ttk.Label(perishable_frame, text=perishable_text, font=("Segoe UI", 9), 
                     justify="left").pack(anchor="w")
        
        # 2. Ingredientes estacionales
        if seasonal_ingredients:
            seasonal_frame = ttk.LabelFrame(parent, text="🌱 Ingredientes Estacionales", padding=10)
            seasonal_frame.pack(fill="x", pady=(0, 10))
            
            seasonal_text = "📅 DISPONIBILIDAD LIMITADA:\n"
            for name, season, qty in seasonal_ingredients:
                seasonal_text += f"• {name}: {season} ({qty:.0f}g)\n"
            
            seasonal_text += ("\n💡 Recomendaciones:\n"
                            "• Planificar compras según calendario estacional\n"
                            "• Considerar alternativas fuera de temporada\n"
                            "• Ajustar menú según disponibilidad estacional")
            
            ttk.Label(seasonal_frame, text=seasonal_text, font=("Segoe UI", 9), 
                     justify="left").pack(anchor="w")
        
        # 3. Ingredientes de alto costo
        if high_cost_ingredients:
            high_cost_frame = ttk.LabelFrame(parent, text="💎 Ingredientes Premium", padding=10)
            high_cost_frame.pack(fill="x", pady=(0, 10))
            
            high_cost_text = "💰 INGREDIENTES DE ALTO VALOR:\n"
            for name, cost_per_kg, total_cost in sorted(high_cost_ingredients, key=lambda x: x[2], reverse=True)[:5]:
                high_cost_text += f"• {name}: ${cost_per_kg:.2f}/kg (Total: ${total_cost:.2f})\n"
            
            high_cost_text += ("\n💡 Recomendaciones:\n"
                              "• Almacenamiento seguro y controlado\n"
                              "• Porciones precisas para evitar desperdicio\n"
                              "• Negociar contratos con proveedores especializados\n"
                              "• Considerar alternativas más económicas")
            
            ttk.Label(high_cost_frame, text=high_cost_text, font=("Segoe UI", 9), 
                     justify="left").pack(anchor="w")
        
        # 4. Estrategias generales
        general_frame = ttk.LabelFrame(parent, text="🎯 Estrategias Generales de Inventario", padding=10)
        general_frame.pack(fill="x", pady=(10, 0))
        
        total_unique = len(ingredient_totals)
        total_cost = sum((qty/1000) * ingredient_info.get(name, {}).get('cost_per_kg', 0) 
                        for name, qty in ingredient_totals.items())
        
        if total_unique > 50:
            complexity_advice = "• Simplificar menú para reducir complejidad de inventario"
        elif total_unique < 20:
            complexity_advice = "• Inventario optimizado con pocos ingredientes únicos"
        else:
            complexity_advice = "• Complejidad de inventario balanceada"
        
        general_text = (f"📊 RESUMEN EJECUTIVO:\n"
                       f"• Total de ingredientes únicos: {total_unique}\n"
                       f"• Inversión total en inventario: ${total_cost:.2f}\n"
                       f"{complexity_advice}\n\n"
                       f"🎯 ESTRATEGIAS RECOMENDADAS:\n"
                       f"• Implementar sistema de gestión de inventario digital\n"
                       f"• Establecer relaciones a largo plazo con proveedores clave\n"
                       f"• Realizar auditorías de inventario semanales\n"
                       f"• Optimizar ciclos de pedido según rotación de productos\n"
                       f"• Capacitar al personal en manejo adecuado de ingredientes")
        
        ttk.Label(general_frame, text=general_text, font=("Segoe UI", 9), 
                 justify="left").pack(anchor="w")
    
    def _create_algorithm_statistics(self, parent, algorithm_stats: Dict):
        """Crea las estadísticas del algoritmo genético."""
        # Título
        ttk.Label(parent, text="📊 ESTADÍSTICAS DEL ALGORITMO GENÉTICO", 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        if not algorithm_stats:
            ttk.Label(parent, text="ℹ️ No hay estadísticas del algoritmo disponibles.", 
                     font=("Segoe UI", 12)).pack(expand=True)
            return
        
        # Frame para gráficos
        charts_frame = ttk.Frame(parent)
        charts_frame.pack(fill="both", expand=True)
        
        # Configurar matplotlib para usar el backend de tkinter
        plt.style.use('default')
        
        # Crear figura con subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Evolución del Algoritmo Genético', fontsize=14, fontweight='bold')
        
        # Obtener datos
        best_fitness = algorithm_stats.get('best_fitness_per_generation', [])
        avg_fitness = algorithm_stats.get('avg_fitness_per_generation', [])
        diversity = algorithm_stats.get('diversity_per_generation', [])
        
        if best_fitness and avg_fitness:
            generations = list(range(len(best_fitness)))
            
            # Gráfico 1: Evolución del fitness
            ax1.plot(generations, best_fitness, 'b-', label='Mejor fitness', linewidth=2)
            ax1.plot(generations, avg_fitness, 'r--', label='Fitness promedio', linewidth=1.5)
            ax1.set_title('Evolución del Fitness')
            ax1.set_xlabel('Generación')
            ax1.set_ylabel('Fitness')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico 2: Diversidad de la población
            if diversity:
                ax2.plot(generations, diversity, 'g-', linewidth=2)
                ax2.set_title('Diversidad de la Población')
                ax2.set_xlabel('Generación')
                ax2.set_ylabel('Diversidad')
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'Sin datos de diversidad', 
                        ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Diversidad de la Población')
            
            # Gráfico 3: Mejora por generación
            if len(best_fitness) > 1:
                improvements = [best_fitness[i] - best_fitness[i-1] for i in range(1, len(best_fitness))]
                ax3.bar(generations[1:], improvements, alpha=0.7, color='orange')
                ax3.set_title('Mejora por Generación')
                ax3.set_xlabel('Generación')
                ax3.set_ylabel('Mejora en Fitness')
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(0.5, 0.5, 'Insuficientes datos', 
                        ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title('Mejora por Generación')
            
            # Gráfico 4: Convergencia
            if len(best_fitness) > 10:
                convergence = [abs(best_fitness[i] - avg_fitness[i]) for i in range(len(best_fitness))]
                ax4.plot(generations, convergence, 'purple', linewidth=2)
                ax4.set_title('Convergencia (Diferencia Mejor-Promedio)')
                ax4.set_xlabel('Generación')
                ax4.set_ylabel('Diferencia')
                ax4.grid(True, alpha=0.3)
            else:
                ax4.text(0.5, 0.5, 'Insuficientes datos', 
                        ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('Convergencia')
        else:
            # Sin datos disponibles
            for ax in [ax1, ax2, ax3, ax4]:
                ax.text(0.5, 0.5, 'Sin datos disponibles', 
                       ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
        
        # Integrar gráfico en tkinter
        canvas = FigureCanvasTkAgg(fig, charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Estadísticas numéricas
        stats_frame = ttk.LabelFrame(parent, text="📈 Métricas del Algoritmo", padding=10)
        stats_frame.pack(fill="x", pady=(15, 0))
        
        if best_fitness:
            initial_fitness = best_fitness[0] if best_fitness else 0
            final_fitness = best_fitness[-1] if best_fitness else 0
            max_fitness = max(best_fitness) if best_fitness else 0
            improvement = final_fitness - initial_fitness
            improvement_pct = (improvement / initial_fitness * 100) if initial_fitness > 0 else 0
            
            stats_text = (f"🎯 RENDIMIENTO DEL ALGORITMO:\n"
                         f"• Generaciones ejecutadas: {len(best_fitness)}\n"
                         f"• Fitness inicial: {initial_fitness:.4f}\n"
                         f"• Fitness final: {final_fitness:.4f}\n"
                         f"• Mejor fitness alcanzado: {max_fitness:.4f}\n"
                         f"• Mejora total: {improvement:.4f} ({improvement_pct:+.2f}%)\n"
                         f"• Convergencia: {'Buena' if len(best_fitness) > 50 and improvement > 0 else 'Limitada'}")
        else:
            stats_text = "ℹ️ No hay estadísticas disponibles del algoritmo genético."
        
        ttk.Label(stats_frame, text=stats_text, font=("Segoe UI", 10), 
                 justify="left").pack(anchor="w")
    
    # Métodos auxiliares
    def _get_dish_cost(self, dish: Dish) -> float:
        """Obtiene el costo de un plato."""
        if hasattr(dish, '_calculated_cost'):
            return float(dish._calculated_cost)
        elif hasattr(dish, 'cost'):
            return float(dish.cost)
        else:
            return self._estimate_dish_cost(dish)
    
    def _get_dish_prep_time(self, dish: Dish) -> float:
        """Obtiene el tiempo de preparación de un plato."""
        if hasattr(dish, '_calculated_prep_time'):
            return float(dish._calculated_prep_time)
        elif hasattr(dish, 'prep_time'):
            return float(dish.prep_time)
        else:
            return self._estimate_dish_prep_time(dish)
    
    def _estimate_dish_cost(self, dish: Dish) -> float:
        """Estima el costo de un plato."""
        if hasattr(dish, 'recipe') and dish.recipe:
            total_cost = 0.0
            for ingredient, quantity in dish.recipe.items():
                if hasattr(ingredient, 'cost_per_kg'):
                    cost_per_kg = float(ingredient.cost_per_kg)
                    qty_kg = float(quantity) / 1000.0
                    total_cost += cost_per_kg * qty_kg
            return total_cost
        return 10.0
    
    def _estimate_dish_prep_time(self, dish: Dish) -> float:
        """Estima el tiempo de preparación de un plato."""
        if hasattr(dish, 'steps') and dish.steps:
            return sum(float(getattr(step, 'time', 0)) for step in dish.steps)
        elif hasattr(dish, 'complexity'):
            return float(dish.complexity) * 8
        return 20.0
    
    def _get_main_ingredients(self, dish: Dish, num_ingredients: int = 3) -> List[str]:
        """Obtiene los ingredientes principales de un plato."""
        if not hasattr(dish, 'recipe') or not dish.recipe:
            return []
        
        try:
            ingredient_costs = []
            for ingredient, quantity in dish.recipe.items():
                if hasattr(ingredient, 'cost_per_kg') and hasattr(ingredient, 'name'):
                    cost_per_kg = float(ingredient.cost_per_kg)
                    qty_kg = float(quantity) / 1000.0
                    total_cost = cost_per_kg * qty_kg
                    ingredient_costs.append((ingredient.name, total_cost))
            
            # Ordenar por costo y tomar los principales
            ingredient_costs.sort(key=lambda x: x[1], reverse=True)
            return [name for name, _ in ingredient_costs[:num_ingredients]]
        
        except Exception as e:
            logging.warning(f"Error getting main ingredients for {dish.name}: {e}")
            return [ing.name for ing in list(dish.recipe.keys())[:num_ingredients] 
                   if hasattr(ing, 'name')]