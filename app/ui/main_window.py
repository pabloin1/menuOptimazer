import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict
from collections import defaultdict

from app.core.models import Dish
from app.core.genetic_algorithm_v2 import MenuGeneticAlgorithm
from app.ui.configuration_panel import ConfigurationPanel
from app.ui.results_panel import ResultsPanel
from app.ui.progress_dialog import ProgressDialog
# Imports adicionales para estructura cúbica
from app.core.cubic_integration import CubicWorkflowManager, integrate_cubic_workflow_with_menu_optimization


class MenuOptimizerMainWindow(tk.Tk):
    """
    Ventana principal del sistema MenuOptimizer.
    Coordina los paneles de configuración y resultados.
    """
    
    def __init__(self, catalog: List[Dish], all_techniques: List[str]):
        super().__init__()
        
        if not catalog:
            self.destroy()
            return
        
        self.catalog = catalog
        self.all_techniques = all_techniques
        
        # Configurar ventana principal
        self.title("MENUOPTIMIZER v10.0 - Sistema Inteligente de Optimización")
        self.geometry("1400x900")
        self.configure(bg='#f0f0f0')
        
        # Variables de estado
        self.current_results = None
        self.optimization_running = False
        self.cubic_workflow_manager = None  # NUEVA VARIABLE PARA ESTRUCTURA CÚBICA
        
        # Inicializar interfaz
        self._setup_ui()
        self._setup_menu_bar()
        
        # Obtener estaciones únicas de la base de datos
        self._extract_stations_from_catalog()
        
        logging.info("Ventana principal inicializada correctamente")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario principal."""
        # Crear notebook principal
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Panel de configuración
        self.config_panel = ConfigurationPanel(
            self.main_notebook, 
            catalog=self.catalog,
            all_techniques=self.all_techniques,
            on_optimize_callback=self._run_optimization
        )
        self.main_notebook.add(self.config_panel, text='⚙️ Configuración del Restaurante')
        
        # Panel de resultados
        self.results_panel = ResultsPanel(self.main_notebook)
        self.main_notebook.add(self.results_panel, text='🏆 Resultados de Optimización')
        
        # Statusbar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(side="bottom", fill="x", padx=5, pady=2)
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Listo - Configure los parámetros y ejecute la optimización",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left")
        
        self.progress_bar = ttk.Progressbar(
            self.status_frame, 
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(side="right", padx=(10, 0))
    
    def _setup_menu_bar(self):
        """Configura la barra de menú."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Exportar Resultados...", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Configuración Avanzada...", command=self._show_advanced_config)
        tools_menu.add_command(label="Estadísticas del Catálogo", command=self._show_catalog_stats)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Manual de Usuario", command=self._show_help)
        help_menu.add_command(label="Acerca de...", command=self._show_about)
    
    def _extract_stations_from_catalog(self):
        """Extrae todas las estaciones únicas del catálogo."""
        all_stations = set()
        for dish in self.catalog:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    if hasattr(step, 'station') and step.station:
                        all_stations.add(step.station)
        
        self.all_stations = sorted(list(all_stations))
        
        # Pasarlas al panel de configuración
        if hasattr(self.config_panel, 'set_available_stations'):
            self.config_panel.set_available_stations(self.all_stations)
    
    def _run_optimization(self, config: Dict):
        """
        Ejecuta el algoritmo de optimización con la configuración proporcionada.
        VERSIÓN MODIFICADA que incluye generación de estructura cúbica.
        
        Args:
            config: Diccionario con toda la configuración del usuario
        """
        if self.optimization_running:
            messagebox.showwarning("Optimización en Curso", 
                                 "Ya hay una optimización ejecutándose. Por favor espere.")
            return
        
        try:
            self.optimization_running = True
            self._update_status("Iniciando optimización...")
            self.progress_bar.start(10)
            
            # Validar configuración
            validation_result = self._validate_configuration(config)
            if not validation_result['valid']:
                messagebox.showerror("Configuración Inválida", validation_result['message'])
                self._cleanup_optimization()
                return
            
            # Filtrar catálogo según restricciones
            filtered_catalog = self._filter_catalog(config)
            
            if len(filtered_catalog) < config['num_dishes']:
                self._show_insufficient_dishes_dialog(len(filtered_catalog), config['num_dishes'])
                self._cleanup_optimization()
                return
            
            # Mostrar diálogo de progreso
            progress_dialog = ProgressDialog(self, "Optimizando Menú...")
            progress_dialog.show()
            
            # Configurar algoritmo genético
            genetic_config = self._build_genetic_config(config, filtered_catalog)
            genetic_algorithm = MenuGeneticAlgorithm(genetic_config)
            
            self._update_status("Ejecutando algoritmo genético...")
            
            # Ejecutar optimización (obtener múltiples soluciones)
            try:
                solutions = genetic_algorithm.get_multiple_solutions(num_solutions=3)
                
                if solutions:
                    # ===== NUEVA INTEGRACIÓN DE ESTRUCTURA CÚBICA =====
                    self._update_status("Generando estructura cúbica de flujo de trabajo...")
                    
                    # Actualizar mensaje del diálogo de progreso
                    if hasattr(progress_dialog, 'update_status'):
                        progress_dialog.update_status("Analizando flujo de trabajo en cocina...")
                    
                    # Tomar el mejor menú para generar la estructura cúbica
                    best_menu = solutions[0][0]  # Primer elemento es el menú, segundo es fitness
                    
                    # Crear estructura cúbica
                    self.cubic_workflow_manager = integrate_cubic_workflow_with_menu_optimization(
                        best_menu, config
                    )
                    
                    if self.cubic_workflow_manager:
                        logging.info("Estructura cúbica generada exitosamente")
                        
                        if hasattr(progress_dialog, 'update_status'):
                            progress_dialog.update_status("Verificando consistencia de precedencias...")
                        
                        validation_result = self.cubic_workflow_manager.validate_workflow_integrity()
                        if not validation_result['valid']:
                            logging.warning("Estructura cúbica inicial tiene inconsistencias. Optimizando...")
                            self.cubic_workflow_manager.optimize_workflow()
                    else:
                        logging.warning("No se pudo generar la estructura cúbica")
                    # ===== FIN DE INTEGRACIÓN CÚBICA =====
                    
                    self.current_results = {
                        'solutions': solutions,
                        'config': config,
                        'algorithm_stats': genetic_algorithm.evolution_stats,
                        'cubic_workflow_manager': self.cubic_workflow_manager
                    }
                    
                    # Mostrar resultados usando el método modificado
                    self.results_panel.display_results_with_cubic(self.current_results, self.cubic_workflow_manager)
                    self.main_notebook.select(1)
                    
                    self._update_status(f"Optimización completada - {len(solutions)} soluciones encontradas")
                    
                    cubic_status = "con análisis de flujo de trabajo" if self.cubic_workflow_manager else "sin análisis de flujo"
                    messagebox.showinfo("Optimización Completada", 
                                      f"Se encontraron {len(solutions)} configuraciones óptimas de menú {cubic_status}.")
                else:
                    messagebox.showwarning("Sin Resultados", 
                                         "No se pudieron generar menús óptimos con las restricciones actuales.")
                    self._update_status("Optimización completada sin resultados")
                    
            except Exception as e:
                logging.error(f"Error durante optimización: {e}", exc_info=True)
                messagebox.showerror("Error de Optimización", f"Error durante la optimización:\n{str(e)}")
                self._update_status("Error en optimización")
            
            finally:
                progress_dialog.close()
        
        except Exception as e:
            logging.error(f"Error en configuración de optimización: {e}", exc_info=True)
            messagebox.showerror("Error de Configuración", f"Error al configurar la optimización:\n{str(e)}")
            self._update_status("Error en configuración")
        
        finally:
            self._cleanup_optimization()

    def _cleanup_optimization(self):
        """Limpia el estado de la optimización."""
        self.optimization_running = False
        self.progress_bar.stop()
        self._update_status("Listo")

    def _validate_configuration(self, config: Dict) -> Dict:
        """Valida la configuración del usuario."""
        try:
            if config['num_dishes'] <= 0:
                return {'valid': False, 'message': 'El número de platos debe ser mayor a 0'}
            if config['max_cost_per_dish'] <= 0:
                return {'valid': False, 'message': 'El costo máximo por plato debe ser mayor a 0'}
            if not (0 <= config['min_profit_margin'] <= 100):
                return {'valid': False, 'message': 'El margen de ganancia debe estar entre 0% y 100%'}
            if config['num_chefs'] <= 0:
                return {'valid': False, 'message': 'El número de cocineros debe ser mayor a 0'}
            if not config['available_techniques']:
                return {'valid': False, 'message': 'Debe seleccionar al menos una técnica culinaria'}
            if not config['available_stations']:
                return {'valid': False, 'message': 'Debe seleccionar al menos una estación de trabajo'}
            
            return {'valid': True, 'message': 'Configuración válida'}
            
        except KeyError as e:
            return {'valid': False, 'message': f'Falta parámetro de configuración: {e}'}
        except Exception as e:
            return {'valid': False, 'message': f'Error de validación: {e}'}

    def _filter_catalog(self, config: Dict) -> List[Dish]:
        """Filtra el catálogo según las restricciones configuradas con logging detallado."""
        logging.info("=== INICIANDO FILTRADO DE CATÁLOGO ===")
        logging.info(f"Catálogo inicial: {len(self.catalog)} platos")
        
        filtered = []
        rejection_reasons = defaultdict(int)
        
        for dish in self.catalog:
            # Filtrar por costo
            dish_cost = self._calculate_dish_cost(dish)
            if dish_cost > config['max_cost_per_dish']:
                rejection_reasons['costo_excesivo'] += 1
                continue

            # Filtrar por temporada
            if config['season'] != 'Todo el año' and not self._dish_available_in_season(dish, config['season']):
                rejection_reasons['fuera_temporada'] += 1
                continue

            # Filtrar por técnicas disponibles
            required_techniques = {step.technique for step in dish.steps if hasattr(step, 'technique') and step.technique}
            if required_techniques and not required_techniques.issubset(config['available_techniques']):
                rejection_reasons['tecnicas_faltantes'] += 1
                continue

            # Filtrar por estaciones disponibles
            required_stations = {step.station for step in dish.steps if hasattr(step, 'station') and step.station}
            if required_stations and not required_stations.issubset(config['available_stations']):
                rejection_reasons['estaciones_faltantes'] += 1
                continue
            
            filtered.append(dish)

        logging.info("=== RESUMEN DE FILTRADO ===")
        logging.info(f"Platos aceptados: {len(filtered)}")
        logging.info(f"Platos rechazados: {sum(rejection_reasons.values())}")
        for reason, count in rejection_reasons.items():
            logging.info(f"  - {reason}: {count} platos")
        
        return filtered

    def _calculate_dish_cost(self, dish: Dish) -> float:
        """Calcula el costo de un plato."""
        if hasattr(dish, '_calculated_cost'):
            return float(dish._calculated_cost)
        if hasattr(dish, 'recipe') and dish.recipe:
            total_cost = 0.0
            for ingredient, quantity in dish.recipe.items():
                if hasattr(ingredient, 'cost_per_kg'):
                    cost_per_kg = float(getattr(ingredient, 'cost_per_kg', 0))
                    qty_kg = float(getattr(quantity, 'value', quantity)) / 1000.0
                    total_cost += cost_per_kg * qty_kg
            return total_cost
        return 10.0

    def _dish_available_in_season(self, dish: Dish, season: str) -> bool:
        """Verifica si un plato está disponible en la temporada especificada."""
        if not hasattr(dish, 'recipe') or not dish.recipe:
            return True
        for ingredient in dish.recipe.keys():
            if hasattr(ingredient, 'season') and ingredient.season not in ('Todo el año', season):
                return False
        return True

    def _calculate_dish_prep_time(self, dish: Dish) -> float:
        """Calcula el tiempo de preparación de un plato."""
        if hasattr(dish, '_calculated_prep_time'):
            return float(dish._calculated_prep_time)
        if hasattr(dish, 'steps') and dish.steps:
            return sum(float(getattr(step, 'time', 0)) for step in dish.steps)
        return float(getattr(dish, 'complexity', 3)) * 8

    def _build_genetic_config(self, config: Dict, filtered_catalog: List[Dish]) -> Dict:
        """Construye la configuración para el algoritmo genético."""
        min_margin = config['min_profit_margin']
        price_factor = 1 / (1 - min_margin / 100) if min_margin < 100 else 2.0

        establishment_weights = {
            'casual': {'ganancia': 0.20, 'tiempo': 0.25, 'nutricion': 0.10, 'variedad': 0.15, 'desperdicio': 0.10, 'distribucion_carga': 0.10, 'popularidad': 0.10},
            'elegante': {'ganancia': 0.30, 'tiempo': 0.10, 'nutricion': 0.15, 'variedad': 0.20, 'desperdicio': 0.15, 'distribucion_carga': 0.05, 'popularidad': 0.05},
            'comida_rapida': {'ganancia': 0.25, 'tiempo': 0.35, 'nutricion': 0.05, 'variedad': 0.10, 'desperdicio': 0.15, 'distribucion_carga': 0.10, 'popularidad': 0.00}
        }
        weights = establishment_weights.get(config['establishment_type'], establishment_weights['casual'])

        return {
            'population_size': 150, 'generations': 250, 'mutation_rate': 0.12,
            'elite_size': 15, 'tournament_size': 5, 'num_dishes': config['num_dishes'],
            'catalog': filtered_catalog,
            'constraints': {
                'max_cost_per_dish': config['max_cost_per_dish'],
                'min_profit_margin': config['min_profit_margin'],
                'price_factor': price_factor,
                'num_chefs': config['num_chefs'],
                'season': config['season']
            },
            'optimization_weights': weights
        }

    def _show_insufficient_dishes_dialog(self, available: int, needed: int):
        """Muestra diálogo cuando no hay suficientes platos."""
        message = (f"No se encontraron suficientes platos ({available}) para generar "
                   f"un menú de {needed} opciones.\n\nSugerencias:\n"
                   "• Reduzca el 'Número de opciones en el menú'\n"
                   "• Aumente el 'Presupuesto máximo por plato'\n"
                   "• Seleccione más 'Técnicas' y 'Estaciones'\n"
                   "• Cambie la 'Temporada' a 'Todo el año'")
        messagebox.showwarning("Restricciones Demasiado Estrictas", message)
    
    def _update_status(self, message: str):
        """Actualiza el mensaje de estado."""
        self.status_label.config(text=message)
        self.update_idletasks()
        logging.info(f"Status: {message}")
    
    def _export_results(self):
        """Exporta los resultados actuales."""
        if not self.current_results:
            messagebox.showinfo("Sin Resultados", "No hay resultados para exportar.")
            return
        messagebox.showinfo("Función no Implementada", "La exportación de resultados estará disponible en una futura versión.")
    
    def _show_advanced_config(self):
        """Muestra diálogo de configuración avanzada."""
        messagebox.showinfo("Función no Implementada", "La configuración avanzada estará disponible en una futura versión.")
    
    def _show_catalog_stats(self):
        """Muestra estadísticas del catálogo de platos."""
        total_dishes = len(self.catalog)
        avg_cost = sum(self._calculate_dish_cost(dish) for dish in self.catalog) / total_dishes
        avg_complexity = sum(getattr(dish, 'complexity', 0) for dish in self.catalog) / total_dishes
        diet_types = defaultdict(int)
        for dish in self.catalog:
            diet_types[getattr(dish, 'diet_type', 'N/D')] += 1
        
        diet_summary = '\n'.join([f"  • {diet}: {count}" for diet, count in diet_types.items()])

        workflow_info = ""
        if hasattr(self, 'cubic_workflow_manager') and self.cubic_workflow_manager and self.cubic_workflow_manager.cubic_structure:
            workflow_data = self.cubic_workflow_manager.get_workflow_report()
            stats = workflow_data['general_stats']
            workflow_info = f"""
🧊 FLUJO DE TRABAJO CÚBICO ACTUAL:
• Dimensiones: {stats['active_persons']}p × {stats['active_positions']}e × {stats['max_precedence_used']}pr
• Utilización: {stats['utilization_rate']:.1%}
• Estado: {'✅ Consistente' if stats['inconsistencies_count'] == 0 else f'⚠️ {stats["inconsistencies_count"]} problemas'}"""

        stats_message = (f"Estadísticas del Catálogo:\n\n"
                        f"Total de platos: {total_dishes}\n"
                        f"Costo promedio: ${avg_cost:.2f} MXN\n"
                        f"Complejidad promedio: {avg_complexity:.1f}/10\n\n"
                        f"Distribución por tipo de dieta:\n{diet_summary}"
                        f"{workflow_info}")
        
        messagebox.showinfo("Estadísticas del Catálogo", stats_message)
    
    def _show_help(self):
        """Muestra ayuda del usuario."""
        messagebox.showinfo("Ayuda", "Consulte la documentación para obtener instrucciones detalladas.")
    
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = "MENUOPTIMIZER v10.0\nSistema Inteligente de Optimización\n\nDesarrollado por: Pablo César Altuzar Grajales"
        messagebox.showinfo("Acerca de MenuOptimizer", about_text)