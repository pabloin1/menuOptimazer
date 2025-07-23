# app/core/cubic_integration.py
from typing import List, Dict, Tuple, Any
import logging
from collections import defaultdict

from app.core.models import Dish
from app.core.cubic_data_structure import (
    CubicWorkflowStructure, Person, Position, FoodStage,
    create_cubic_structure_from_menu
)


class CubicWorkflowManager:
    """
    Gestor que integra la estructura cúbica con el sistema MenuOptimizer.
    Proporciona interfaz de alto nivel para manejo de flujos de trabajo.
    """
    
    def __init__(self):
        self.cubic_structure: CubicWorkflowStructure = None
        self.workflow_assignments: Dict[str, Any] = {}
        self.optimization_history: List[Dict] = []
    
    def initialize_from_menu_and_config(self, menu: List[Dish], config: Dict) -> bool:
        """
        Inicializa la estructura cúbica a partir de un menú optimizado y configuración.
        
        Args:
            menu: Menú optimizado por el algoritmo genético
            config: Configuración del restaurante
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            # Crear personas (cocineros) basándose en la configuración
            persons = self._create_persons_from_config(config)
            
            # Crear posiciones (estaciones) basándose en estaciones disponibles
            positions = self._create_positions_from_config(config)
            
            # Crear estructura cúbica
            self.cubic_structure = create_cubic_structure_from_menu(menu, persons, positions)
            
            # Realizar asignación inicial inteligente
            success = self._perform_initial_assignment(menu, config)
            
            if success:
                # Verificar consistencia
                is_consistent = self.cubic_structure.check_precedence_consistency()
                
                if not is_consistent:
                    logging.warning("Estructura inicial no es consistente, aplicando optimización...")
                    self.optimize_workflow()
                
                logging.info("Estructura cúbica inicializada exitosamente")
                return True
            else:
                logging.error("Falló la asignación inicial")
                return False
        
        except Exception as e:
            logging.error(f"Error inicializando estructura cúbica: {e}")
            return False
    
    def _create_persons_from_config(self, config: Dict) -> List[Person]:
        """Crea personas (cocineros) basándose en la configuración."""
        num_chefs = config.get('num_chefs', 4)
        available_techniques = config.get('available_techniques', set())
        
        persons = []
        
        # Distribuir técnicas entre cocineros
        techniques_list = list(available_techniques) if available_techniques else []
        
        for i in range(num_chefs):
            # Asignar especialidades de manera distribuida
            specializations = []
            
            if techniques_list:
                # Cada cocinero domina algunas técnicas
                techniques_per_chef = max(1, len(techniques_list) // num_chefs)
                start_idx = i * techniques_per_chef
                end_idx = min(start_idx + techniques_per_chef + 2, len(techniques_list))  # +2 para overlap
                specializations = techniques_list[start_idx:end_idx]
            
            # Nivel de habilidad basado en el tipo de establecimiento
            establishment_type = config.get('establishment_type', 'casual')
            if establishment_type == 'elegante':
                skill_level = 7 + (i % 3)  # 7-9
                max_concurrent = 2
            elif establishment_type == 'comida_rapida':
                skill_level = 5 + (i % 3)  # 5-7
                max_concurrent = 3
            else:  # casual
                skill_level = 6 + (i % 3)  # 6-8
                max_concurrent = 2
            
            person = Person(
                id=i,
                name=f"Chef_{i+1}",
                skill_level=skill_level,
                specializations=specializations,
                max_concurrent_tasks=max_concurrent
            )
            
            persons.append(person)
        
        logging.info(f"Creadas {len(persons)} personas con especialidades distribuidas")
        return persons
    
    def _create_positions_from_config(self, config: Dict) -> List[Position]:
        """Crea posiciones (estaciones) basándose en estaciones disponibles."""
        available_stations = config.get('available_stations', set())
        
        positions = []
        
        # Mapeo de estaciones a configuraciones
        station_configs = {
            'Mise en Place': {'max_capacity': 3, 'skills': ['Preparación', 'Organización']},
            'Plancha y Parrilla': {'max_capacity': 2, 'skills': ['Plancha', 'Parrilla']},
            'Horno y Rostizado': {'max_capacity': 2, 'skills': ['Horneado', 'Rostizado']},
            'Estofados y Salsas': {'max_capacity': 2, 'skills': ['Guisar', 'Salsas']},
            'Fritura': {'max_capacity': 1, 'skills': ['Freír']},
            'Ensamblaje y Emplatado': {'max_capacity': 3, 'skills': ['Emplatado', 'Presentación']},
            'Repostería y Postres': {'max_capacity': 2, 'skills': ['Repostería', 'Decoración']},
            'Ensaladas y Fríos': {'max_capacity': 2, 'skills': ['Ensaladas', 'Preparación en Frío']},
            'Pasta y Granos': {'max_capacity': 2, 'skills': ['Hervido', 'Pasta']},
            'Bebidas y Cócteles': {'max_capacity': 1, 'skills': ['Mezclas', 'Bebidas']},
            'Parrilla Exterior': {'max_capacity': 1, 'skills': ['Parrilla', 'Ahumado']},
            'Estación de Sushis': {'max_capacity': 1, 'skills': ['Sushi', 'Corte Japonés']},
            'Bar de Jugos y Smoothies': {'max_capacity': 1, 'skills': ['Licuados', 'Jugos']},
            'Estación de Wok y Cocina Asiática': {'max_capacity': 1, 'skills': ['Wok', 'Salteado']},
            'Ahumador': {'max_capacity': 1, 'skills': ['Ahumado']},
            'Tandoor y Horno de Barro': {'max_capacity': 1, 'skills': ['Tandoor', 'Horno de Barro']},
            'Molecular Gastronomy Lab': {'max_capacity': 1, 'skills': ['Molecular', 'Técnicas Avanzadas']}
        }
        
        position_id = 0
        for station_name in sorted(available_stations):
            config_data = station_configs.get(station_name, {
                'max_capacity': 2, 
                'skills': ['General']
            })
            
            position = Position(
                id=position_id,
                name=station_name,
                station_type=self._categorize_station(station_name),
                max_capacity=config_data['max_capacity'],
                required_skills=config_data['skills']
            )
            
            positions.append(position)
            position_id += 1
        
        logging.info(f"Creadas {len(positions)} posiciones de estaciones disponibles")
        return positions
    
    def _categorize_station(self, station_name: str) -> str:
        """Categoriza una estación por tipo."""
        hot_stations = ['Plancha', 'Horno', 'Fritura', 'Parrilla', 'Tandoor', 'Wok']
        cold_stations = ['Ensaladas', 'Sushis', 'Jugos', 'Emplatado']
        prep_stations = ['Mise en Place', 'Repostería']
        
        station_lower = station_name.lower()
        
        if any(hot in station_lower for hot in [s.lower() for s in hot_stations]):
            return 'caliente'
        elif any(cold in station_lower for cold in [s.lower() for s in cold_stations]):
            return 'frio'
        elif any(prep in station_lower for prep in [s.lower() for s in prep_stations]):
            return 'preparacion'
        else:
            return 'general'
    
    def _perform_initial_assignment(self, menu: List[Dish], config: Dict) -> bool:
        """Realiza la asignación inicial de etapas a personas y posiciones."""
        try:
            # Estrategia de asignación: Round Robin inteligente
            assignment_strategy = self._get_assignment_strategy(config)
            
            if assignment_strategy == 'skill_based':
                return self._assign_by_skills(menu)
            elif assignment_strategy == 'load_balanced':
                return self._assign_load_balanced(menu)
            else:
                return self._assign_round_robin(menu)
        
        except Exception as e:
            logging.error(f"Error en asignación inicial: {e}")
            return False
    
    def _get_assignment_strategy(self, config: Dict) -> str:
        """Determina la estrategia de asignación según el tipo de establecimiento."""
        establishment_type = config.get('establishment_type', 'casual')
        
        if establishment_type == 'elegante':
            return 'skill_based'  # Asignar por habilidades específicas
        elif establishment_type == 'comida_rapida':
            return 'load_balanced'  # Balancear carga para eficiencia
        else:
            return 'round_robin'  # Distribución simple
    
    def _assign_by_skills(self, menu: List[Dish]) -> bool:
        """Asignación basada en habilidades específicas."""
        precedence_counter = defaultdict(int)
        
        for dish in menu:
            if not hasattr(dish, 'steps') or not dish.steps:
                continue
            
            for step in dish.steps:
                # Encontrar la etapa correspondiente
                stage = self._find_stage_for_step(dish.id, step.order)
                if not stage:
                    continue
                
                # Encontrar posición apropiada
                position_id = self._find_position_by_station(step.station)
                if position_id is None:
                    continue
                
                # Encontrar persona con habilidades apropiadas
                person_id = self._find_skilled_person(step.technique, stage.complexity)
                if person_id is None:
                    continue
                
                # Asignar
                precedence = precedence_counter[(person_id, position_id)]
                success = self.cubic_structure.assign_stage(person_id, position_id, precedence, stage.id)
                
                if success:
                    precedence_counter[(person_id, position_id)] += 1
                else:
                    logging.warning(f"Falló asignación de etapa {stage.id}")
        
        return True
    
    def _assign_load_balanced(self, menu: List[Dish]) -> bool:
        """Asignación balanceada por carga de trabajo."""
        person_load = defaultdict(int)  # person_id -> carga total
        precedence_counter = defaultdict(int)
        
        # Calcular todas las etapas y sus tiempos
        all_stages = []
        for dish in menu:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    stage = self._find_stage_for_step(dish.id, step.order)
                    if stage:
                        all_stages.append((stage, step))
        
        # Ordenar por tiempo estimado (asignar primero las más largas)
        all_stages.sort(key=lambda x: x[0].estimated_time, reverse=True)
        
        for stage, step in all_stages:
            # Encontrar posición
            position_id = self._find_position_by_station(step.station)
            if position_id is None:
                continue
            
            # Encontrar persona con menor carga
            person_id = min(
                [p.id for p in self.cubic_structure.persons.values()],
                key=lambda pid: person_load[pid]
            )
            
            # Asignar
            precedence = precedence_counter[(person_id, position_id)]
            success = self.cubic_structure.assign_stage(person_id, position_id, precedence, stage.id)
            
            if success:
                precedence_counter[(person_id, position_id)] += 1
                person_load[person_id] += stage.estimated_time
        
        return True
    
    def _assign_round_robin(self, menu: List[Dish]) -> bool:
        """Asignación simple round robin."""
        person_counter = 0
        precedence_counter = defaultdict(int)
        
        for dish in menu:
            if not hasattr(dish, 'steps') or not dish.steps:
                continue
            
            for step in dish.steps:
                stage = self._find_stage_for_step(dish.id, step.order)
                if not stage:
                    continue
                
                position_id = self._find_position_by_station(step.station)
                if position_id is None:
                    continue
                
                # Rotar entre personas
                person_id = person_counter % len(self.cubic_structure.persons)
                person_counter += 1
                
                precedence = precedence_counter[(person_id, position_id)]
                success = self.cubic_structure.assign_stage(person_id, position_id, precedence, stage.id)
                
                if success:
                    precedence_counter[(person_id, position_id)] += 1
        
        return True
    
    def _find_stage_for_step(self, dish_id: int, step_order: int) -> FoodStage:
        """Encuentra la etapa correspondiente a un paso de plato."""
        for stage in self.cubic_structure.food_stages.values():
            if stage.dish_id == dish_id and stage.step_order == step_order:
                return stage
        return None
    
    def _find_position_by_station(self, station_name: str) -> int:
        """Encuentra el ID de posición por nombre de estación."""
        for pos_id, position in self.cubic_structure.positions.items():
            if position.name == station_name:
                return pos_id
        return None
    
    def _find_skilled_person(self, required_technique: str, complexity: int) -> int:
        """Encuentra la persona más adecuada para una técnica y complejidad."""
        best_person_id = None
        best_score = -1
        
        for person_id, person in self.cubic_structure.persons.items():
            score = 0
            
            # Puntuación por habilidad específica
            if required_technique in person.specializations:
                score += 10
            
            # Puntuación por nivel de habilidad vs complejidad
            skill_match = 10 - abs(person.skill_level - complexity)
            score += max(0, skill_match)
            
            if score > best_score:
                best_score = score
                best_person_id = person_id
        
        return best_person_id
    
    def optimize_workflow(self) -> Dict[str, Any]:
        """Optimiza el flujo de trabajo completo."""
        if not self.cubic_structure:
            return {'error': 'Estructura cúbica no inicializada'}
        
        logging.info("Iniciando optimización de flujo de trabajo...")
        
        # Optimizar asignaciones
        optimization_result = self.cubic_structure.optimize_assignments()
        
        # Registrar en historial
        self.optimization_history.append({
            'timestamp': logging.Formatter().formatTime(logging.LogRecord(
                '', 0, '', 0, '', (), None), '%Y-%m-%d %H:%M:%S'),
            'result': optimization_result
        })
        
        return optimization_result
    
    def get_workflow_report(self) -> Dict[str, Any]:
        """Genera un reporte completo del flujo de trabajo."""
        if not self.cubic_structure:
            return {'error': 'Estructura cúbica no inicializada'}
        
        # Estadísticas generales
        stats = self.cubic_structure.get_summary_stats()
        
        # Análisis por persona
        person_analysis = {}
        for person_id, person in self.cubic_structure.persons.items():
            workflow = self.cubic_structure.get_person_workflow(person_id)
            total_tasks = sum(len(tasks) for tasks in workflow.values())
            estimated_time = self._calculate_person_total_time(person_id)
            
            person_analysis[person.name] = {
                'total_tasks': total_tasks,
                'estimated_time': estimated_time,
                'utilization_rate': min(1.0, estimated_time / 480),  # Asumiendo jornada de 8h
                'workflow_positions': len(workflow)
            }
        
        # Análisis por posición
        position_analysis = {}
        for position_id, position in self.cubic_structure.positions.items():
            schedule = self.cubic_structure.get_position_schedule(position_id)
            total_assignments = sum(len(tasks) for tasks in schedule.values())
            concurrent_peak = self._calculate_position_peak_usage(position_id)
            
            position_analysis[position.name] = {
                'total_assignments': total_assignments,
                'concurrent_peak': concurrent_peak,
                'capacity_utilization': concurrent_peak / position.max_capacity if position.max_capacity > 0 else 0,
                'assigned_persons': len(schedule)
            }
        
        # Análisis de precedencias
        precedence_analysis = {
            'total_constraints': stats['precedence_constraints'],
            'consistency_status': 'Consistent' if stats['inconsistencies_count'] == 0 else 'Has Issues',
            'issues_count': stats['inconsistencies_count'],
            'issues_details': self.cubic_structure.inconsistencies if stats['inconsistencies_count'] > 0 else []
        }
        
        return {
            'general_stats': stats,
            'person_analysis': person_analysis,
            'position_analysis': position_analysis,
            'precedence_analysis': precedence_analysis,
            'optimization_history': self.optimization_history
        }
    
    def _calculate_person_total_time(self, person_id: int) -> float:
        """Calcula el tiempo total estimado para una persona."""
        total_time = 0.0
        workflow = self.cubic_structure.get_person_workflow(person_id)
        
        for position_tasks in workflow.values():
            for precedence, stage_id in position_tasks:
                stage = self.cubic_structure.food_stages.get(stage_id)
                if stage:
                    total_time += stage.estimated_time
        
        return total_time
    
    def _calculate_position_peak_usage(self, position_id: int) -> int:
        """Calcula el pico de uso concurrente de una posición."""
        max_concurrent = 0
        
        for precedence in range(self.cubic_structure.max_precedence):
            concurrent_count = 0
            for person_id in range(self.cubic_structure.max_persons):
                if self.cubic_structure.cube[person_id, position_id, precedence] != -1:
                    concurrent_count += 1
            
            max_concurrent = max(max_concurrent, concurrent_count)
        
        return max_concurrent
    
    def export_workflow_data(self) -> Dict[str, Any]:
        """Exporta todos los datos del flujo de trabajo."""
        if not self.cubic_structure:
            return {'error': 'Estructura cúbica no inicializada'}
        
        return {
            'cubic_structure': self.cubic_structure.export_to_dict(),
            'workflow_assignments': self.workflow_assignments,
            'optimization_history': self.optimization_history,
            'workflow_report': self.get_workflow_report()
        }
    
    def validate_workflow_integrity(self) -> Dict[str, Any]:
        """Valida la integridad completa del flujo de trabajo."""
        if not self.cubic_structure:
            return {'valid': False, 'error': 'Estructura cúbica no inicializada'}
        
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # Verificar consistencia de precedencias
        is_consistent = self.cubic_structure.check_precedence_consistency()
        
        if not is_consistent:
            validation_results['valid'] = False
            validation_results['errors'].extend(self.cubic_structure.inconsistencies)
        
        # Verificar balance de carga
        person_loads = {}
        for person_id, person in self.cubic_structure.persons.items():
            load_time = self._calculate_person_total_time(person_id)
            person_loads[person.name] = load_time
            
            if load_time > 600:  # Más de 10 horas
                validation_results['warnings'].append(
                    f"Persona {person.name} tiene sobrecarga: {load_time:.1f} minutos"
                )
            elif load_time < 240:  # Menos de 4 horas
                validation_results['warnings'].append(
                    f"Persona {person.name} tiene poca carga: {load_time:.1f} minutos"
                )
        
        # Verificar utilización de posiciones
        for position_id, position in self.cubic_structure.positions.items():
            schedule = self.cubic_structure.get_position_schedule(position_id)
            if not schedule:
                validation_results['warnings'].append(
                    f"Posición {position.name} no tiene asignaciones"
                )
        
        # Generar recomendaciones
        if validation_results['warnings'] or validation_results['errors']:
            validation_results['recommendations'].append(
                "Ejecutar optimización de flujo de trabajo"
            )
        
        if len([w for w in validation_results['warnings'] if 'sobrecarga' in w]) > 0:
            validation_results['recommendations'].append(
                "Considerar agregar más personal o redistribuir tareas"
            )
        
        return validation_results


# Función de utilidad para integración con el sistema principal
def integrate_cubic_workflow_with_menu_optimization(menu: List[Dish], config: Dict) -> CubicWorkflowManager:
    """
    Función principal para integrar la estructura cúbica con el resultado de optimización de menú.
    
    Args:
        menu: Menú optimizado por el algoritmo genético
        config: Configuración del restaurante
    
    Returns:
        Gestor de flujo de trabajo configurado
    """
    workflow_manager = CubicWorkflowManager()
    
    success = workflow_manager.initialize_from_menu_and_config(menu, config)
    
    if success:
        logging.info("Integración de estructura cúbica completada exitosamente")
        
        # Generar reporte inicial
        report = workflow_manager.get_workflow_report()
        logging.info(f"Reporte de flujo: {report['general_stats']['total_assignments']} asignaciones, "
                    f"{report['general_stats']['inconsistencies_count']} inconsistencias")
        
        return workflow_manager
    else:
        logging.error("Falló la integración de estructura cúbica")
        return None