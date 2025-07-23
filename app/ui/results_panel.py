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
# Imports adicionales para estructura cúbica
from app.core.cubic_integration import CubicWorkflowManager


class ResultsPanel(ttk.Frame):
    """
    Panel para mostrar los resultados de la optimización.
    Incluye las tres salidas especificadas en la propuesta más análisis cúbico.
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
    
    def display_results_with_cubic(self, results: Dict, cubic_manager: CubicWorkflowManager = None):
        """
        Muestra los resultados de la optimización incluyendo análisis cúbico.
        
        Args:
            results: Diccionario con resultados de optimización
            cubic_manager: Gestor de flujo de trabajo cúbico (opcional)
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
            
            # ===== NUEVA SALIDA 4: ANÁLISIS DE FLUJO DE TRABAJO CÚBICO =====
            if cubic_manager and i == 0:  # Solo para la mejor solución
                workflow_tab = ttk.Frame(internal_notebook, padding="10")
                internal_notebook.add(workflow_tab, text="🧊 Flujo de Trabajo")
                self._create_cubic_workflow_analysis(workflow_tab, cubic_manager, menu, config)
        
        # Pestaña adicional con estadísticas del algoritmo
        stats_tab = ttk.Frame(self.results_notebook, padding="10")
        self.results_notebook.add(stats_tab, text="📊 Estadísticas del Algoritmo")
        self._create_algorithm_statistics(stats_tab, results.get('algorithm_stats', {}))
    
    def display_results(self, results: Dict):
        """
        Método de compatibilidad que llama a la versión con análisis cúbico.
        """
        cubic_manager = results.get('cubic_workflow_manager')
        self.display_results_with_cubic(results, cubic_manager)
    
    def _create_cubic_workflow_analysis(self, parent, cubic_manager: CubicWorkflowManager, menu, config):
        """
        NUEVO MÉTODO: Crea el análisis de flujo de trabajo cúbico integrado.
        """
        # Título
        ttk.Label(parent, text="🧊 ANÁLISIS DE FLUJO DE TRABAJO CÚBICO", 
                 font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        ttk.Label(parent, text="Persona × Puesto × Precedencia → Etapa de Alimento", 
                 font=("Segoe UI", 11, "italic"), foreground="#666666").pack(pady=(0, 15))
        
        # Obtener datos del workflow
        if not cubic_manager or not cubic_manager.cubic_structure:
            ttk.Label(parent, text="❌ Error: No se pudo generar la estructura cúbica", 
                     font=("Segoe UI", 12), foreground="red").pack(expand=True)
            return
        
        workflow_data = cubic_manager.get_workflow_report()
        
        # Crear notebook para sub-análisis
        workflow_notebook = ttk.Notebook(parent)
        workflow_notebook.pack(fill="both", expand=True)
        
        # 1. Resumen General
        self._create_workflow_overview_tab(workflow_notebook, workflow_data)
        
        # 2. Análisis por Persona
        self._create_workflow_person_tab(workflow_notebook, workflow_data)
        
        # 3. Análisis por Posición
        self._create_workflow_position_tab(workflow_notebook, workflow_data)
        
        # 4. Validación de Consistencia
        self._create_workflow_validation_tab(workflow_notebook, cubic_manager)
    
    def _create_workflow_overview_tab(self, parent_notebook, workflow_data):
        """Crea la pestaña de resumen del workflow."""
        overview_frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(overview_frame, text="📊 Resumen")
        
        stats = workflow_data['general_stats']
        
        # Estadísticas principales
        stats_frame = ttk.LabelFrame(overview_frame, text="📈 Estadísticas de la Estructura", padding=15)
        stats_frame.pack(fill="x", pady=(0, 15))
        
        # Grid de estadísticas
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x")
        
        # Columna izquierda
        left_col = ttk.Frame(stats_grid)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        ttk.Label(left_col, text="🧊 Dimensiones del Cubo:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(left_col, text=f"• Personas activas: {stats['active_persons']}/{stats['total_persons']}", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=(10, 0))
        ttk.Label(left_col, text=f"• Posiciones activas: {stats['active_positions']}/{stats['total_positions']}", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=(10, 0))
        ttk.Label(left_col, text=f"• Precedencias usadas: {stats['max_precedence_used']}", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=(10, 0))
        
        # Columna derecha
        right_col = ttk.Frame(stats_grid)
        right_col.pack(side="left", fill="both", expand=True)
        
        ttk.Label(right_col, text="📊 Asignaciones:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(right_col, text=f"• Etapas totales: {stats['total_stages']}", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=(10, 0))
        ttk.Label(right_col, text=f"• Asignaciones realizadas: {stats['total_assignments']}", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=(10, 0))
        ttk.Label(right_col, text=f"• Utilización: {stats['utilization_rate']:.1%}", 
                 font=("Segoe UI", 9)).pack(anchor="w", padx=(10, 0))
        
        status_color = "green" if stats['inconsistencies_count'] == 0 else "red"
        status_text = "✅ Consistente" if stats['inconsistencies_count'] == 0 else f"❌ {stats['inconsistencies_count']} problemas"
        
        ttk.Label(right_col, text=f"• Estado: {status_text}", 
                 font=("Segoe UI", 9), foreground=status_color).pack(anchor="w", padx=(10, 0))
    
    def _create_workflow_person_tab(self, parent_notebook, workflow_data):
        """Crea la pestaña de análisis por persona."""
        person_frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(person_frame, text="👥 Por Persona")
        
        person_analysis = workflow_data['person_analysis']
        
        # Tabla de análisis
        table_frame = ttk.Frame(person_frame)
        table_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        columns = ("Persona", "Tareas", "Tiempo (min)", "Utilización", "Posiciones")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Persona", width=120, anchor="w")
        tree.column("Tareas", width=80, anchor="center")
        tree.column("Tiempo (min)", width=100, anchor="center")
        tree.column("Utilización", width=100, anchor="center")
        tree.column("Posiciones", width=100, anchor="center")
        
        # Llenar datos
        for person_name, analysis in person_analysis.items():
            utilization = analysis['utilization_rate']
            color_tag = "normal"
            if utilization > 0.9:
                color_tag = "overloaded"
            elif utilization < 0.5:
                color_tag = "underloaded"
            
            tree.insert("", "end", values=(
                person_name,
                analysis['total_tasks'],
                f"{analysis['estimated_time']:.1f}",
                f"{utilization:.1%}",
                analysis['workflow_positions']
            ), tags=(color_tag,))
        
        # Configurar colores
        tree.tag_configure("overloaded", background="#ffebee")
        tree.tag_configure("underloaded", background="#e8f5e8")
        tree.tag_configure("normal", background="white")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Análisis de carga
        analysis_frame = ttk.LabelFrame(person_frame, text="📊 Análisis de Carga", padding=10)
        analysis_frame.pack(fill="x")
        
        overloaded = [name for name, data in person_analysis.items() if data['utilization_rate'] > 0.9]
        underloaded = [name for name, data in person_analysis.items() if data['utilization_rate'] < 0.5]
        
        analysis_text = "💡 RECOMENDACIONES:\n"
        
        if overloaded:
            analysis_text += f"⚠️ Sobrecargados: {', '.join(overloaded)}\n"
            analysis_text += "   • Redistribuir tareas o agregar personal\n"
        
        if underloaded:
            analysis_text += f"📈 Subutilizados: {', '.join(underloaded)}\n"
            analysis_text += "   • Asignar tareas adicionales\n"
        
        if not overloaded and not underloaded:
            analysis_text += "✅ Distribución balanceada"
        
        ttk.Label(analysis_frame, text=analysis_text, font=("Segoe UI", 9), 
                 justify="left").pack(anchor="w")
    
    def _create_workflow_position_tab(self, parent_notebook, workflow_data):
        """Crea la pestaña de análisis por posición."""
        position_frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(position_frame, text="🏭 Por Posición")
        
        position_analysis = workflow_data['position_analysis']
        
        # Tabla de análisis
        table_frame = ttk.Frame(position_frame)
        table_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        columns = ("Posición", "Asignaciones", "Pico Concurrente", "Capacidad", "Personas")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Posición", width=180, anchor="w")
        tree.column("Asignaciones", width=100, anchor="center")
        tree.column("Pico Concurrente", width=120, anchor="center")
        tree.column("Capacidad", width=100, anchor="center")
        tree.column("Personas", width=100, anchor="center")
        
        # Llenar datos
        for position_name, analysis in position_analysis.items():
            capacity_util = analysis['capacity_utilization']
            color_tag = "normal"
            if capacity_util > 0.8:
                color_tag = "high_capacity"
            elif capacity_util == 0:
                color_tag = "unused"
            
            tree.insert("", "end", values=(
                position_name[:25] + "..." if len(position_name) > 25 else position_name,
                analysis['total_assignments'],
                analysis['concurrent_peak'],
                f"{capacity_util:.1%}",
                analysis['assigned_persons']
            ), tags=(color_tag,))
        
        # Configurar colores
        tree.tag_configure("high_capacity", background="#fff3cd")
        tree.tag_configure("unused", background="#f8d7da")
        tree.tag_configure("normal", background="white")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Análisis de capacidad
        capacity_frame = ttk.LabelFrame(position_frame, text="📊 Análisis de Capacidad", padding=10)
        capacity_frame.pack(fill="x")
        
        high_capacity = [name for name, data in position_analysis.items() if data['capacity_utilization'] > 0.8]
        unused = [name for name, data in position_analysis.items() if data['capacity_utilization'] == 0]
        
        capacity_text = "🔍 ANÁLISIS:\n"
        
        if high_capacity:
            capacity_text += f"⚠️ Alta utilización: {len(high_capacity)} posiciones\n"
            capacity_text += "   • Riesgo de cuello de botella\n"
        
        if unused:
            capacity_text += f"❌ Sin usar: {len(unused)} posiciones\n"
            capacity_text += "   • Evaluar necesidad o reasignar\n"
        
        active_positions = sum(1 for data in position_analysis.values() if data['total_assignments'] > 0)
        total_positions = len(position_analysis)
        capacity_text += f"📈 Eficiencia: {active_positions}/{total_positions} activas ({active_positions/total_positions:.1%})"
        
        ttk.Label(capacity_frame, text=capacity_text, font=("Segoe UI", 9), 
                 justify="left").pack(anchor="w")
    
    def _create_workflow_validation_tab(self, parent_notebook, cubic_manager):
        """Crea la pestaña de validación."""
        validation_frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(validation_frame, text="✓ Validación")
        
        # Ejecutar validación
        validation_results = cubic_manager.validate_workflow_integrity()
        
        # Estado general
        status_frame = ttk.LabelFrame(validation_frame, text="📊 Estado General", padding=15)
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_icon = "✅" if validation_results['valid'] else "❌"
        status_text = "Válido" if validation_results['valid'] else "Problemas Detectados"
        status_color = "green" if validation_results['valid'] else "red"
        
        ttk.Label(status_frame, text=f"{status_icon} Estado: {status_text}", 
                 font=("Segoe UI", 12, "bold"), foreground=status_color).pack(anchor="w")
        
        # Errores críticos
        if validation_results['errors']:
            errors_frame = ttk.LabelFrame(validation_frame, text="🚨 Errores", padding=10)
            errors_frame.pack(fill="x", pady=(0, 10))
            
            for error in validation_results['errors'][:5]:  # Máximo 5 errores
                ttk.Label(errors_frame, text=f"• {error}", font=("Segoe UI", 9), 
                         foreground="red").pack(anchor="w")
        
        # Advertencias
        if validation_results['warnings']:
            warnings_frame = ttk.LabelFrame(validation_frame, text="⚠️ Advertencias", padding=10)
            warnings_frame.pack(fill="x", pady=(0, 10))
            
            for warning in validation_results['warnings'][:3]:  # Máximo 3 advertencias
                ttk.Label(warnings_frame, text=f"• {warning}", font=("Segoe UI", 9), 
                         foreground="orange").pack(anchor="w")
        
        # Recomendaciones
        if validation_results['recommendations']:
            recommendations_frame = ttk.LabelFrame(validation_frame, text="💡 Recomendaciones", padding=10)
            recommendations_frame.pack(fill="x")
            
            for recommendation in validation_results['recommendations']:
                ttk.Label(recommendations_frame, text=f"• {recommendation}", font=("Segoe UI", 9), 
                         foreground="blue").pack(anchor="w")
    
    # ===== MÉTODOS EXISTENTES (sin cambios) =====
    
    def _create_optimized_menu_table(self, parent, menu: List[Dish], config: Dict):
        """SALIDA 1: Tabla de menú optimizado con las tres mejores configuraciones"""
        
        ttk.Label(parent, text="📋 TABLA DE MENÚ OPTIMIZADO", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))
        
        # Información del tipo de establecimiento
        establishment_info = {
            'casual': '🍔 Restaurante Casual - Enfoque en popularidad y rapidez',
            'elegante': '🍷 Restaurante Elegante - Enfoque en calidad y ganancia',
            'comida_rapida': '⚡ Comida Rápida - Máxima eficiencia operativa'
        }
        
        ttk.Label(parent, text=establishment_info.get(config.get('establishment_type', ''), ''), 
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
        
        # Calcular factor de precio
        min_margin = config.get('min_profit_margin', 40)
        price_factor = 1 / (1 - min_margin / 100) if min_margin < 100 else 1.5
        
        # Agregar datos del menú
        total_cost = 0
        total_revenue = 0
        
        for dish in menu:
            # Usar el costo calculado previamente
            cost = getattr(dish, '_calculated_cost', self._calculate_dish_cost(dish))
            price = cost * price_factor
            margin = ((price - cost) / price) * 100 if price > 0 else 0
            
            # Obtener ingredientes principales (los 3 más costosos)
            main_ingredients = []
            if hasattr(dish, 'recipe') and dish.recipe:
                try:
                    ingredient_costs = []
                    for ing, qty in dish.recipe.items():
                        if hasattr(ing, 'cost_per_kg') and hasattr(ing, 'name'):
                            ing_cost = self._safe_float_conversion(ing.cost_per_kg) * (self._safe_float_conversion(qty)/1000)
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

    def _create_operational_efficiency_report(self, parent, menu: List[Dish], config: Dict):
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
            prep_time = getattr(dish, '_calculated_prep_time', self._calculate_dish_prep_time(dish))
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
                            station_time[step.station] += self._safe_float_conversion(step.time, 0)
        
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
        num_chefs = config.get('num_chefs', 4)
        theoretical_capacity = (60 / avg_time) * num_chefs if avg_time > 0 else 0
        practical_capacity = theoretical_capacity * 0.75  # 75% de eficiencia
        peak_capacity = theoretical_capacity * 0.60  # 60% en hora pico
        daily_capacity = practical_capacity * 8  # 8 horas de servicio
        
        capacity_data = [
            ("Cocineros disponibles", num_chefs, "Personal asignado en cocina"),
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

    def _create_inventory_analysis_report(self, parent, menu: List[Dish]):
        """SALIDA 3: Análisis de inventario."""
        
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
                        qty = self._safe_float_conversion(quantity, 0)
                        ingredient_totals[ingredient.name] += qty
                        
                        if ingredient.name not in ingredient_info:
                            supplier_name = "N/A"
                            cost_per_kg = 0
                            shelf_life = "N/A"
                            
                            if hasattr(ingredient, 'supplier') and ingredient.supplier:
                                supplier_name = getattr(ingredient.supplier, 'name', 'N/A')
                            
                            if hasattr(ingredient, 'cost_per_kg'):
                                cost_per_kg = self._safe_float_conversion(ingredient.cost_per_kg, 0)
                            
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
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _calculate_dish_cost(self, dish: Dish) -> float:
        """Obtiene el costo de un plato."""
        if hasattr(dish, '_calculated_cost'):
            return float(dish._calculated_cost)
        elif hasattr(dish, 'cost'):
            return float(dish.cost)
        else:
            return self._estimate_dish_cost(dish)
    
    def _calculate_dish_prep_time(self, dish: Dish) -> float:
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
    
    def _safe_float_conversion(self, value, default=0.0):
        """Convierte de manera segura cualquier tipo numérico a float"""
        try:
            if value is None:
                return default
            if hasattr(value, '__float__'):
                return float(value)
            else:
                return float(str(value))
        except (ValueError, TypeError, AttributeError):
            logging.warning(f"Error convirtiendo valor {value} a float, usando {default}")
            return default