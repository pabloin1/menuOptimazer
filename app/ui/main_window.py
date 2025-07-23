# app/ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict
from collections import defaultdict  # Agregar este import

from app.core.models import Dish
from app.ui.configuration_panel import ConfigurationPanel
from app.ui.results_panel import ResultsPanel
from app.ui.progress_dialog import ProgressDialog


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
        VERSIÓN CORREGIDA con mejor manejo de errores
        """
        if config is None:
            print("DEBUG: Configuración es None, cancelando optimización")
            return
            
        if self.optimization_running:
            messagebox.showwarning("Optimización en Curso", 
                                 "Ya hay una optimización ejecutándose. Por favor espere.")
            return
        
        # Variable para rastrear el diálogo de progreso
        progress_dialog = None
        
        try:
            self.optimization_running = True
            self._update_status("Iniciando optimización...")
            self.progress_bar.start(10)
            
            print(f"DEBUG: Iniciando optimización con config: {config.keys()}")
            
            # Validar configuración
            validation_result = self._validate_configuration(config)
            if not validation_result['valid']:
                messagebox.showerror("Configuración Inválida", validation_result['message'])
                return
            
            print("DEBUG: Configuración validada exitosamente")
            
            # Filtrar catálogo según restricciones
            filtered_catalog = self._filter_catalog(config)
            print(f"DEBUG: Catálogo filtrado: {len(filtered_catalog)} platos disponibles")
            
            if len(filtered_catalog) < config['num_dishes']:
                print(f"DEBUG: Insuficientes platos filtrados")
                self._show_insufficient_dishes_dialog(len(filtered_catalog), config['num_dishes'])
                return
            
            # Mostrar diálogo de progreso
            progress_dialog = ProgressDialog(self, "Optimizando Menú...")
            progress_dialog.show()
            print("DEBUG: Diálogo de progreso mostrado")
            
            # Configurar algoritmo genético
            genetic_config = self._build_genetic_config(config, filtered_catalog)
            
            # Importar aquí para evitar import circular
            from app.core.genetic_algorithm_v2 import MenuGeneticAlgorithm
            genetic_algorithm = MenuGeneticAlgorithm(genetic_config)
            
            self._update_status("Ejecutando algoritmo genético...")
            print("DEBUG: Iniciando algoritmo genético...")
            
            # Ejecutar optimización
            try:
                solutions = genetic_algorithm.get_multiple_solutions(num_solutions=3)
                print(f"DEBUG: Optimización completada. {len(solutions) if solutions else 0} soluciones encontradas")
                
                if solutions:
                    self.current_results = {
                        'solutions': solutions,
                        'config': config,
                        'algorithm_stats': genetic_algorithm.evolution_stats
                    }
                    
                    # Mostrar resultados
                    self.results_panel.display_results(self.current_results)
                    self.main_notebook.select(1)  # Cambiar a tab de resultados
                    
                    self._update_status(f"Optimización completada - {len(solutions)} soluciones encontradas")
                    messagebox.showinfo("Optimización Completada", 
                                      f"Se encontraron {len(solutions)} configuraciones óptimas de menú.")
                else:
                    messagebox.showwarning("Sin Resultados", 
                                         "No se pudieron generar menús óptimos con las restricciones actuales.")
                    self._update_status("Optimización completada sin resultados")
                    
            except Exception as e:
                logging.error(f"Error durante optimización: {e}", exc_info=True)
                print(f"DEBUG: Error en optimización: {e}")
                messagebox.showerror("Error de Optimización", 
                                   f"Error durante la optimización:\n{str(e)}")
                self._update_status("Error en optimización")
        
        except Exception as e:
            logging.error(f"Error en configuración de optimización: {e}", exc_info=True)
            print(f"DEBUG: Error en configuración: {e}")
            messagebox.showerror("Error de Configuración", 
                               f"Error al configurar la optimización:\n{str(e)}")
            self._update_status("Error en configuración")
        
        finally:
            print("DEBUG: Finalizando optimización, limpiando recursos...")
            self.optimization_running = False
            self.progress_bar.stop()
            
            # IMPORTANTE: Cerrar diálogo de progreso
            if progress_dialog:
                try:
                    progress_dialog.close()
                    print("DEBUG: Diálogo de progreso cerrado desde finally")
                except Exception as e:
                    print(f"DEBUG: Error cerrando diálogo: {e}")
    
    def _validate_configuration(self, config: Dict) -> Dict:
        """Valida la configuración del usuario."""
        try:
            # Validaciones básicas
            if config['num_dishes'] <= 0:
                return {'valid': False, 'message': 'El número de platos debe ser mayor a 0'}
            
            if config['max_cost_per_dish'] <= 0:
                return {'valid': False, 'message': 'El costo máximo por plato debe ser mayor a 0'}
            
            if config['min_profit_margin'] < 0 or config['min_profit_margin'] > 100:
                return {'valid': False, 'message': 'El margen de ganancia debe estar entre 0% y 100%'}
            
            if config['num_chefs'] <= 0:
                return {'valid': False, 'message': 'El número de cocineros debe ser mayor a 0'}
            
            # Validar que hay técnicas y estaciones seleccionadas
            if not config['available_techniques']:
                return {'valid': False, 'message': 'Debe seleccionar al menos una técnica culinaria disponible'}
            
            if not config['available_stations']:
                return {'valid': False, 'message': 'Debe seleccionar al menos una estación de trabajo disponible'}
            
            return {'valid': True, 'message': 'Configuración válida'}
            
        except KeyError as e:
            return {'valid': False, 'message': f'Falta parámetro de configuración: {e}'}
        except Exception as e:
            return {'valid': False, 'message': f'Error de validación: {e}'}
    
    def _filter_catalog(self, config: Dict) -> List[Dish]:
        """
        Filtra el catálogo con debugging mejorado
        """
        logging.info("=== INICIANDO FILTRADO DE CATÁLOGO ===")
        logging.info(f"Catálogo inicial: {len(self.catalog)} platos")
        print(f"DEBUG: Iniciando filtrado con {len(self.catalog)} platos")
        print(f"DEBUG: Estaciones disponibles: {config.get('available_stations', 'N/A')}")
        print(f"DEBUG: Técnicas disponibles: {config.get('available_techniques', 'N/A')}")
        
        filtered = []
        rejection_reasons = defaultdict(int)
        
        for dish in self.catalog:
            rejected = False
            
            # Calcular costo real del plato
            dish_cost = self._calculate_dish_cost(dish)
            dish._calculated_cost = dish_cost
            
            # Calcular tiempo real del plato
            real_prep_time = self._calculate_dish_prep_time(dish)
            dish._calculated_prep_time = real_prep_time
            
            # Filtrar por costo
            if dish_cost > config['max_cost_per_dish']:
                rejection_reasons['costo_excesivo'] += 1
                logging.debug(f"RECHAZADO '{dish.name}': Costo ${dish_cost:.2f} > Máximo ${config['max_cost_per_dish']}")
                continue
            
            # Filtrar por temporada
            if config['season'] != 'Todo el año':
                if not self._dish_available_in_season(dish, config['season']):
                    rejection_reasons['fuera_temporada'] += 1
                    logging.debug(f"RECHAZADO '{dish.name}': Fuera de temporada '{config['season']}'")
                    continue
            
            # Filtrar por técnicas disponibles
            required_techniques = set()
            if hasattr(dish, 'steps') and dish.steps:
                required_techniques = {step.technique for step in dish.steps if step.technique}
            
            if required_techniques and not required_techniques.issubset(config['available_techniques']):
                missing_techniques = required_techniques - config['available_techniques']
                rejection_reasons['tecnicas_faltantes'] += 1
                logging.debug(f"RECHAZADO '{dish.name}': Requiere técnicas no disponibles: {missing_techniques}")
                continue
            
            # Filtrar por estaciones disponibles
            required_stations = set()
            if hasattr(dish, 'steps') and dish.steps:
                required_stations = {step.station for step in dish.steps if step.station}
            
            if required_stations and not required_stations.issubset(config['available_stations']):
                missing_stations = required_stations - config['available_stations']
                rejection_reasons['estaciones_faltantes'] += 1
                logging.debug(f"RECHAZADO '{dish.name}': Requiere estaciones no disponibles: {missing_stations}")
                continue
            
            # Filtrar por tipo de establecimiento
            if not self._dish_suitable_for_establishment(dish, config['establishment_type']):
                rejection_reasons['inadecuado_establecimiento'] += 1
                logging.debug(f"RECHAZADO '{dish.name}': No adecuado para establecimiento '{config['establishment_type']}'")
                continue
            
            logging.debug(f"ACEPTADO '{dish.name}': Costo=${dish_cost:.2f}, Tiempo={real_prep_time:.0f}min")
            filtered.append(dish)
        
        # Log de resumen
        logging.info("=== RESUMEN DE FILTRADO ===")
        logging.info(f"Platos aceptados: {len(filtered)}")
        logging.info(f"Platos rechazados: {len(self.catalog) - len(filtered)}")
        
        print(f"DEBUG: Filtrado completado - {len(filtered)} platos aceptados de {len(self.catalog)}")
        for reason, count in rejection_reasons.items():
            logging.info(f"  - {reason}: {count} platos")
            print(f"DEBUG: {reason}: {count} platos")
        
        return filtered
    
    def _calculate_dish_cost(self, dish: Dish) -> float:
        """Calcula el costo de un plato."""
        if hasattr(dish, '_calculated_cost'):
            return float(dish._calculated_cost)
        
        if hasattr(dish, 'recipe') and dish.recipe:
            total_cost = 0.0
            for ingredient, quantity in dish.recipe.items():
                if hasattr(ingredient, 'cost_per_kg'):
                    cost_per_kg = float(ingredient.cost_per_kg)
                    qty_kg = float(quantity) / 1000.0
                    total_cost += cost_per_kg * qty_kg
            return total_cost
        
        return 10.0  # Costo por defecto
    
    def _dish_available_in_season(self, dish: Dish, season: str) -> bool:
        """Verifica si un plato está disponible en la temporada especificada."""
        if not hasattr(dish, 'recipe') or not dish.recipe:
            return True
        
        for ingredient in dish.recipe.keys():
            if hasattr(ingredient, 'season'):
                if ingredient.season not in ('Todo el año', season):
                    return False
        
        return True
    
    def _dish_suitable_for_establishment(self, dish: Dish, establishment_type: str) -> bool:
        """Verifica si un plato es adecuado para el tipo de establecimiento (criterios más permisivos)."""
        
        # Para tipo casual - solo rechazar los extremadamente complejos
        if establishment_type == 'casual':
            tags = getattr(dish, 'tags', '')
            if isinstance(tags, str) and ('molecular' in tags.lower() or 'vanguardista' in tags.lower()):
                return False
            
            complexity = getattr(dish, 'complexity', 0)
            # Más permisivo: rechazar solo si complejidad > 8 (muy alta)
            if complexity > 8:
                return False
            
            # Más permisivo: aceptar popularidad >= 4 (antes era >= 6)
            popularity = getattr(dish, 'popularity', 0)
            if popularity > 0 and popularity < 4:
                return False
        
        # Para comida rápida - solo rechazar los MUY lentos
        elif establishment_type == 'comida_rapida':
            prep_time = self._calculate_dish_prep_time(dish)
            # Más permisivo: rechazar solo si > 45 min (antes era > 30)
            if prep_time > 45:
                return False
        
        # Para elegante - aceptar todo (no rechazar nada)
        # elif establishment_type == 'elegante':
        #     pass  # Aceptar todos los platos para restaurantes elegantes
        
        return True
    
    def _calculate_dish_prep_time(self, dish: Dish) -> float:
        """Calcula el tiempo de preparación de un plato."""
        if hasattr(dish, '_calculated_prep_time'):
            return float(dish._calculated_prep_time)
        
        if hasattr(dish, 'steps') and dish.steps:
            return sum(float(getattr(step, 'time', 0)) for step in dish.steps)
        
        complexity = getattr(dish, 'complexity', 3)
        return complexity * 8  # 8 minutos por nivel de complejidad
    
    def _build_genetic_config(self, config: Dict, filtered_catalog: List[Dish]) -> Dict:
        """Construye la configuración para el algoritmo genético."""
        # Calcular factor de precio basado en margen mínimo
        min_margin = config['min_profit_margin']
        price_factor = 1 / (1 - min_margin / 100) if min_margin < 100 else 1.5
        
        # Obtener pesos según tipo de establecimiento
        establishment_weights = {
            'casual': {
                'ganancia': 0.20, 'tiempo': 0.25, 'nutricion': 0.10,
                'variedad': 0.15, 'desperdicio': 0.10, 
                'distribucion_carga': 0.10, 'popularidad': 0.10
            },
            'elegante': {
                'ganancia': 0.30, 'tiempo': 0.10, 'nutricion': 0.15,
                'variedad': 0.20, 'desperdicio': 0.15, 
                'distribucion_carga': 0.05, 'popularidad': 0.05
            },
            'comida_rapida': {
                'ganancia': 0.25, 'tiempo': 0.35, 'nutricion': 0.05,
                'variedad': 0.10, 'desperdicio': 0.15, 
                'distribucion_carga': 0.10, 'popularidad': 0.00
            }
        }
        
        weights = establishment_weights.get(config['establishment_type'], 
                                          establishment_weights['casual'])
        
        return {
            'population_size': 150,
            'generations': 250,
            'mutation_rate': 0.12,
            'elite_size': 15,
            'tournament_size': 5,
            'num_dishes': config['num_dishes'],
            'catalog': filtered_catalog,
            'constraints': {
                'max_cost_per_dish': config['max_cost_per_dish'],
                'min_profit_margin': config['min_profit_margin'],
                'price_factor': price_factor,
                'num_chefs': config['num_chefs'],
                'season': config['season'],
                'establishment_type': config['establishment_type']
            },
            'optimization_weights': weights
        }
    
    def _show_insufficient_dishes_dialog(self, available: int, needed: int):
        """Muestra diálogo cuando no hay suficientes platos."""
        message = (f"No se encontraron suficientes platos ({available}) para generar "
                  f"un menú de {needed} opciones.\n\n"
                  f"Sugerencias:\n"
                  f"• Reduzca el 'Número de opciones en el menú'\n"
                  f"• Aumente el 'Presupuesto máximo por plato'\n"
                  f"• Seleccione más 'Técnicas Culinarias Disponibles'\n"
                  f"• Seleccione más 'Estaciones de Trabajo Disponibles'\n"
                  f"• Cambie la 'Temporada' a 'Todo el año'\n"
                  f"• Considere cambiar el 'Tipo de establecimiento'")
        
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
        
        # TODO: Implementar exportación a Excel/PDF
        messagebox.showinfo("Función no Implementada", 
                          "La exportación de resultados estará disponible en una futura versión.")
    
    def _show_advanced_config(self):
        """Muestra diálogo de configuración avanzada."""
        # TODO: Implementar configuración avanzada del algoritmo genético
        messagebox.showinfo("Función no Implementada", 
                          "La configuración avanzada estará disponible en una futura versión.")
    
    def _show_catalog_stats(self):
        """Muestra estadísticas del catálogo de platos."""
        total_dishes = len(self.catalog)
        avg_cost = sum(self._calculate_dish_cost(dish) for dish in self.catalog) / total_dishes
        avg_complexity = sum(getattr(dish, 'complexity', 0) for dish in self.catalog) / total_dishes
        avg_popularity = sum(getattr(dish, 'popularity', 0) for dish in self.catalog) / total_dishes
        
        # Contar tipos de dieta
        diet_types = {}
        for dish in self.catalog:
            diet = getattr(dish, 'diet_type', 'No especificado')
            diet_types[diet] = diet_types.get(diet, 0) + 1
        
        diet_summary = '\n'.join([f"  {diet}: {count}" for diet, count in diet_types.items()])
        
        stats_message = (f"Estadísticas del Catálogo:\n\n"
                        f"Total de platos: {total_dishes}\n"
                        f"Costo promedio: ${avg_cost:.2f} MXN\n"
                        f"Complejidad promedio: {avg_complexity:.1f}/10\n"
                        f"Popularidad promedio: {avg_popularity:.1f}/10\n\n"
                        f"Distribución por tipo de dieta:\n{diet_summary}")
        
        messagebox.showinfo("Estadísticas del Catálogo", stats_message)
    
    def _show_help(self):
        """Muestra ayuda del usuario."""
        help_text = """MENUOPTIMIZER v10.0 - Manual de Usuario

CONFIGURACIÓN:
• Número de opciones: Cantidad de platos en el menú optimizado
• Presupuesto máximo: Costo máximo permitido por plato
• Personal disponible: Número de cocineros para calcular capacidad
• Temporada: Disponibilidad estacional de ingredientes
• Tipo de establecimiento: Afecta los pesos de optimización

TÉCNICAS Y ESTACIONES:
• Seleccione las técnicas culinarias disponibles en su cocina
• Marque las estaciones de trabajo operativas

OPTIMIZACIÓN:
• El sistema usa algoritmos genéticos para encontrar las mejores combinaciones
• Se optimizan 7 variables: ganancia, tiempo, nutrición, variedad, eficiencia de ingredientes, distribución de carga y satisfacción del cliente
• Se generan múltiples soluciones para comparar

RESULTADOS:
• Tabla de menú optimizado con costos y márgenes
• Reporte de eficiencia operativa
• Análisis de inventario y compras"""
        
        help_window = tk.Toplevel(self)
        help_window.title("Manual de Usuario")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(help_window, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
    
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = """MENUOPTIMIZER v10.0
Sistema Inteligente de Optimización de Menús Gastronómicos

Desarrollado por: Pablo César Altuzar Grajales
Matrícula: 223267
Grupo: 8B

Tecnologías utilizadas:
• Python 3.x
• Tkinter (Interfaz gráfica)
• MySQL (Base de datos)
• Algoritmos Genéticos (Optimización)
• NumPy (Cálculos numéricos)

Este sistema optimiza menús de restaurantes considerando:
✓ Margen de ganancia
✓ Tiempo de preparación
✓ Balance nutricional
✓ Variedad gastronómica
✓ Eficiencia de ingredientes
✓ Distribución de carga de trabajo
✓ Satisfacción del cliente

© 2024 - Todos los derechos reservados"""
        
        messagebox.showinfo("Acerca de MenuOptimizer", about_text)