# app/core/cubic_data_structure.py
import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict
import logging
from dataclasses import dataclass

from app.core.models import Dish, RecipeStep


@dataclass
class Person:
    """Representa una persona (cocinero) en la cocina."""
    id: int
    name: str
    skill_level: int  # 1-10
    specializations: List[str]  # Técnicas especializadas
    max_concurrent_tasks: int = 2
    
    def __post_init__(self):
        if not self.specializations:
            self.specializations = []


@dataclass
class Position:
    """Representa un puesto/estación de trabajo."""
    id: int
    name: str
    station_type: str
    max_capacity: int  # Número máximo de personas simultáneas
    required_skills: List[str]
    
    def __post_init__(self):
        if not self.required_skills:
            self.required_skills = []


@dataclass
class FoodStage:
    """Representa una etapa específica de preparación de un alimento."""
    id: int
    dish_id: int
    step_order: int
    description: str
    estimated_time: float
    required_technique: str
    required_station: str
    complexity: int  # 1-10
    
    def __str__(self):
        return f"Stage_{self.id}({self.description})"


class CubicWorkflowStructure:
    """
    Estructura de datos cúbica para modelar flujos de trabajo en cocina.
    
    Dimensiones:
    - D1: Persona (cocinero)
    - D2: Puesto (estación de trabajo) 
    - D3: Precedencia (orden de ejecución)
    
    Valor: ID de la etapa de un alimento
    """
    
    def __init__(self, max_persons: int = 20, max_positions: int = 15, max_precedence: int = 50):
        """
        Inicializa la estructura cúbica.
        
        Args:
            max_persons: Número máximo de personas
            max_positions: Número máximo de puestos
            max_precedence: Número máximo de precedencias
        """
        self.max_persons = max_persons
        self.max_positions = max_positions
        self.max_precedence = max_precedence
        
        # Estructura cúbica principal: [persona][puesto][precedencia] = etapa_id
        self.cube = np.full((max_persons, max_positions, max_precedence), -1, dtype=int)
        
        # Metadatos
        self.persons: Dict[int, Person] = {}
        self.positions: Dict[int, Position] = {}
        self.food_stages: Dict[int, FoodStage] = {}
        
        # Mapeos para búsqueda rápida
        self.person_name_to_id: Dict[str, int] = {}
        self.position_name_to_id: Dict[str, int] = {}
        
        # Verificación de consistencia
        self.precedence_graph: Dict[int, Set[int]] = defaultdict(set)  # etapa -> etapas_dependientes
        self.inconsistencies: List[str] = []
        
        logging.info(f"Estructura cúbica inicializada: {max_persons}x{max_positions}x{max_precedence}")
    
    def add_person(self, person: Person) -> bool:
        """Agrega una persona a la estructura."""
        if person.id >= self.max_persons:
            logging.error(f"ID de persona {person.id} excede el máximo {self.max_persons}")
            return False
        
        if person.id in self.persons:
            logging.warning(f"Persona {person.id} ya existe, reemplazando")
        
        self.persons[person.id] = person
        self.person_name_to_id[person.name] = person.id
        
        logging.info(f"Persona agregada: {person.name} (ID: {person.id})")
        return True
    
    def add_position(self, position: Position) -> bool:
        """Agrega un puesto/estación a la estructura."""
        if position.id >= self.max_positions:
            logging.error(f"ID de posición {position.id} excede el máximo {self.max_positions}")
            return False
        
        if position.id in self.positions:
            logging.warning(f"Posición {position.id} ya existe, reemplazando")
        
        self.positions[position.id] = position
        self.position_name_to_id[position.name] = position.id
        
        logging.info(f"Posición agregada: {position.name} (ID: {position.id})")
        return True
    
    def add_food_stage(self, stage: FoodStage) -> bool:
        """Agrega una etapa de alimento a la estructura."""
        if stage.id in self.food_stages:
            logging.warning(f"Etapa {stage.id} ya existe, reemplazando")
        
        self.food_stages[stage.id] = stage
        logging.info(f"Etapa agregada: {stage.description} (ID: {stage.id})")
        return True
    
    def assign_stage(self, person_id: int, position_id: int, precedence: int, stage_id: int) -> bool:
        """
        Asigna una etapa a una posición específica en el cubo.
        
        Args:
            person_id: ID de la persona
            position_id: ID del puesto
            precedence: Orden de precedencia (0-based)
            stage_id: ID de la etapa a asignar
        """
        # Validaciones
        if not self._validate_assignment(person_id, position_id, precedence, stage_id):
            return False
        
        # Verificar si ya hay algo asignado
        current_stage = self.cube[person_id, position_id, precedence]
        if current_stage != -1:
            logging.warning(f"Reemplazando etapa {current_stage} con {stage_id} en "
                          f"persona={person_id}, puesto={position_id}, precedencia={precedence}")
        
        # Asignar
        self.cube[person_id, position_id, precedence] = stage_id
        
        logging.debug(f"Etapa {stage_id} asignada a persona={person_id}, puesto={position_id}, precedencia={precedence}")
        return True
    
    def _validate_assignment(self, person_id: int, position_id: int, precedence: int, stage_id: int) -> bool:
        """Valida una asignación antes de realizarla."""
        # Verificar límites
        if not (0 <= person_id < self.max_persons):
            logging.error(f"ID de persona {person_id} fuera de rango")
            return False
        
        if not (0 <= position_id < self.max_positions):
            logging.error(f"ID de posición {position_id} fuera de rango")
            return False
        
        if not (0 <= precedence < self.max_precedence):
            logging.error(f"Precedencia {precedence} fuera de rango")
            return False
        
        # Verificar existencia de entidades
        if person_id not in self.persons:
            logging.error(f"Persona {person_id} no existe")
            return False
        
        if position_id not in self.positions:
            logging.error(f"Posición {position_id} no existe")
            return False
        
        if stage_id not in self.food_stages:
            logging.error(f"Etapa {stage_id} no existe")
            return False
        
        # Verificar compatibilidad
        person = self.persons[person_id]
        position = self.positions[position_id]
        stage = self.food_stages[stage_id]
        
        # Verificar habilidades requeridas
        if position.required_skills:
            if not any(skill in person.specializations for skill in position.required_skills):
                logging.warning(f"Persona {person.name} no tiene habilidades requeridas para {position.name}")
                # No retornamos False, solo advertencia
        
        # Verificar técnica requerida
        if stage.required_technique and stage.required_technique not in person.specializations:
            logging.warning(f"Persona {person.name} no domina técnica {stage.required_technique}")
        
        return True
    
    def get_stage(self, person_id: int, position_id: int, precedence: int) -> Optional[int]:
        """Obtiene la etapa asignada en una posición específica."""
        if not (0 <= person_id < self.max_persons and 
                0 <= position_id < self.max_positions and 
                0 <= precedence < self.max_precedence):
            return None
        
        stage_id = self.cube[person_id, position_id, precedence]
        return stage_id if stage_id != -1 else None
    
    def get_person_workflow(self, person_id: int) -> Dict[int, List[Tuple[int, int]]]:
        """
        Obtiene el flujo de trabajo completo de una persona.
        
        Returns:
            Dict[puesto_id, List[(precedencia, etapa_id)]]
        """
        if person_id not in self.persons:
            return {}
        
        workflow = defaultdict(list)
        
        for position_id in range(self.max_positions):
            for precedence in range(self.max_precedence):
                stage_id = self.cube[person_id, position_id, precedence]
                if stage_id != -1:
                    workflow[position_id].append((precedence, stage_id))
        
        # Ordenar por precedencia
        for position_id in workflow:
            workflow[position_id].sort(key=lambda x: x[0])
        
        return dict(workflow)
    
    def get_position_schedule(self, position_id: int) -> Dict[int, List[Tuple[int, int]]]:
        """
        Obtiene el horario de una posición/estación.
        
        Returns:
            Dict[persona_id, List[(precedencia, etapa_id)]]
        """
        if position_id not in self.positions:
            return {}
        
        schedule = defaultdict(list)
        
        for person_id in range(self.max_persons):
            for precedence in range(self.max_precedence):
                stage_id = self.cube[person_id, position_id, precedence]
                if stage_id != -1:
                    schedule[person_id].append((precedence, stage_id))
        
        # Ordenar por precedencia
        for person_id in schedule:
            schedule[person_id].sort(key=lambda x: x[0])
        
        return dict(schedule)
    
    def add_precedence_constraint(self, stage_a_id: int, stage_b_id: int):
        """
        Agrega una restricción de precedencia: stage_a debe completarse antes que stage_b.
        """
        if stage_a_id not in self.food_stages or stage_b_id not in self.food_stages:
            logging.error(f"Etapas {stage_a_id} o {stage_b_id} no existen")
            return
        
        self.precedence_graph[stage_a_id].add(stage_b_id)
        logging.debug(f"Precedencia agregada: {stage_a_id} -> {stage_b_id}")
    
    def check_precedence_consistency(self) -> bool:
        """
        Verifica la consistencia de las precedencias en toda la estructura.
        Detecta ciclos y violaciones de orden.
        """
        self.inconsistencies = []
        
        # 1. Detectar ciclos en el grafo de precedencias
        if self._has_cycles():
            self.inconsistencies.append("Se detectaron ciclos en las dependencias de etapas")
        
        # 2. Verificar precedencias en asignaciones del cubo
        self._check_cube_precedences()
        
        # 3. Verificar capacidades de posiciones
        self._check_position_capacities()
        
        # 4. Verificar carga de trabajo de personas
        self._check_person_workloads()
        
        is_consistent = len(self.inconsistencies) == 0
        
        if not is_consistent:
            logging.warning(f"Se encontraron {len(self.inconsistencies)} inconsistencias:")
            for inconsistency in self.inconsistencies:
                logging.warning(f"  - {inconsistency}")
        else:
            logging.info("Estructura de precedencias es consistente")
        
        return is_consistent
    
    def _has_cycles(self) -> bool:
        """Detecta ciclos en el grafo de precedencias usando DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True  # Ciclo detectado
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.precedence_graph.get(node, []):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for stage_id in self.food_stages:
            if stage_id not in visited:
                if dfs(stage_id):
                    return True
        
        return False
    
    def _check_cube_precedences(self):
        """Verifica que las asignaciones del cubo respeten las precedencias."""
        for person_id in range(self.max_persons):
            for position_id in range(self.max_positions):
                # Obtener secuencia de etapas para esta persona-posición
                stages_sequence = []
                for precedence in range(self.max_precedence):
                    stage_id = self.cube[person_id, position_id, precedence]
                    if stage_id != -1:
                        stages_sequence.append((precedence, stage_id))
                
                # Verificar que las precedencias se respeten
                for i, (prec_a, stage_a) in enumerate(stages_sequence):
                    for j, (prec_b, stage_b) in enumerate(stages_sequence[i+1:], i+1):
                        # Si stage_b debe ir antes que stage_a según el grafo
                        if stage_a in self.precedence_graph.get(stage_b, set()):
                            person_name = self.persons.get(person_id, {}).name if person_id in self.persons else f"Persona_{person_id}"
                            position_name = self.positions.get(position_id, {}).name if position_id in self.positions else f"Posición_{position_id}"
                            self.inconsistencies.append(
                                f"Violación de precedencia en {person_name}@{position_name}: "
                                f"Etapa {stage_b} (prec={prec_b}) debe ir antes que Etapa {stage_a} (prec={prec_a})"
                            )
    
    def _check_position_capacities(self):
        """Verifica que no se exceda la capacidad de las posiciones."""
        for position_id, position in self.positions.items():
            # Contar cuántas personas están asignadas simultáneamente
            max_concurrent = 0
            
            for precedence in range(self.max_precedence):
                concurrent_count = 0
                for person_id in range(self.max_persons):
                    if self.cube[person_id, position_id, precedence] != -1:
                        concurrent_count += 1
                
                max_concurrent = max(max_concurrent, concurrent_count)
            
            if max_concurrent > position.max_capacity:
                self.inconsistencies.append(
                    f"Posición {position.name} excede capacidad: {max_concurrent} > {position.max_capacity}"
                )
    
    def _check_person_workloads(self):
        """Verifica que las personas no tengan sobrecarga de trabajo."""
        for person_id, person in self.persons.items():
            # Contar tareas simultáneas máximas
            max_concurrent_tasks = 0
            
            for precedence in range(self.max_precedence):
                concurrent_tasks = 0
                for position_id in range(self.max_positions):
                    if self.cube[person_id, position_id, precedence] != -1:
                        concurrent_tasks += 1
                
                max_concurrent_tasks = max(max_concurrent_tasks, concurrent_tasks)
            
            if max_concurrent_tasks > person.max_concurrent_tasks:
                self.inconsistencies.append(
                    f"Persona {person.name} excede capacidad: {max_concurrent_tasks} > {person.max_concurrent_tasks}"
                )
    
    def optimize_assignments(self) -> Dict[str, Any]:
        """
        Optimiza las asignaciones para minimizar inconsistencias.
        """
        logging.info("Iniciando optimización de asignaciones...")
        
        original_inconsistencies = len(self.inconsistencies)
        
        # 1. Reordenar precedencias para resolver violaciones
        self._fix_precedence_violations()
        
        # 2. Redistribuir carga si es necesario
        self._redistribute_workload()
        
        # 3. Verificar de nuevo
        self.check_precedence_consistency()
        
        final_inconsistencies = len(self.inconsistencies)
        improvement = original_inconsistencies - final_inconsistencies
        
        result = {
            'original_inconsistencies': original_inconsistencies,
            'final_inconsistencies': final_inconsistencies,
            'improvement': improvement,
            'remaining_issues': self.inconsistencies.copy()
        }
        
        logging.info(f"Optimización completada. Inconsistencias: {original_inconsistencies} -> {final_inconsistencies}")
        
        return result
    
    def _fix_precedence_violations(self):
        """Intenta corregir violaciones de precedencia reordenando."""
        for person_id in range(self.max_persons):
            for position_id in range(self.max_positions):
                # Obtener y ordenar etapas según dependencias
                stages_with_precedence = []
                for precedence in range(self.max_precedence):
                    stage_id = self.cube[person_id, position_id, precedence]
                    if stage_id != -1:
                        stages_with_precedence.append((precedence, stage_id))
                
                if len(stages_with_precedence) <= 1:
                    continue
                
                # Ordenamiento topológico simple
                sorted_stages = self._topological_sort_stages([s[1] for s in stages_with_precedence])
                
                # Reasignar con nuevo orden
                for new_precedence, stage_id in enumerate(sorted_stages):
                    # Limpiar asignación anterior
                    for old_prec in range(self.max_precedence):
                        if self.cube[person_id, position_id, old_prec] == stage_id:
                            self.cube[person_id, position_id, old_prec] = -1
                    
                    # Asignar en nueva posición
                    if new_precedence < self.max_precedence:
                        self.cube[person_id, position_id, new_precedence] = stage_id
    
    def _topological_sort_stages(self, stages: List[int]) -> List[int]:
        """Ordena las etapas topológicamente según sus dependencias."""
        # Implementación simple de ordenamiento topológico
        in_degree = {stage: 0 for stage in stages}
        
        # Calcular grados de entrada
        for stage in stages:
            for dependent in self.precedence_graph.get(stage, []):
                if dependent in in_degree:
                    in_degree[dependent] += 1
        
        # Ordenamiento topológico
        queue = [stage for stage in stages if in_degree[stage] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for dependent in self.precedence_graph.get(current, []):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        # Si no se pudieron ordenar todas (hay ciclos), mantener orden original
        if len(result) != len(stages):
            return stages
        
        return result
    
    def _redistribute_workload(self):
        """Redistribuye la carga de trabajo para balancear capacidades."""
        # TODO: Implementar redistribución inteligente de tareas
        # Por ahora, solo registramos que se intentó
        logging.debug("Redistribución de carga de trabajo - funcionalidad pendiente")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas resumidas de la estructura."""
        total_assignments = np.sum(self.cube != -1)
        utilization_rate = total_assignments / self.cube.size
        
        active_persons = len([p for p in range(self.max_persons) 
                            if np.any(self.cube[p] != -1)])
        
        active_positions = len([p for p in range(self.max_positions) 
                              if np.any(self.cube[:, p] != -1)])
        
        max_precedence_used = 0
        for prec in range(self.max_precedence - 1, -1, -1):
            if np.any(self.cube[:, :, prec] != -1):
                max_precedence_used = prec + 1
                break
        
        return {
            'total_assignments': total_assignments,
            'utilization_rate': utilization_rate,
            'active_persons': active_persons,
            'active_positions': active_positions,
            'max_precedence_used': max_precedence_used,
            'total_persons': len(self.persons),
            'total_positions': len(self.positions),
            'total_stages': len(self.food_stages),
            'precedence_constraints': sum(len(deps) for deps in self.precedence_graph.values()),
            'inconsistencies_count': len(self.inconsistencies)
        }
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Exporta toda la estructura a un diccionario para serialización."""
        return {
            'cube_shape': self.cube.shape,
            'cube_data': self.cube.tolist(),
            'persons': {pid: {
                'id': p.id, 'name': p.name, 'skill_level': p.skill_level,
                'specializations': p.specializations, 'max_concurrent_tasks': p.max_concurrent_tasks
            } for pid, p in self.persons.items()},
            'positions': {pid: {
                'id': p.id, 'name': p.name, 'station_type': p.station_type,
                'max_capacity': p.max_capacity, 'required_skills': p.required_skills
            } for pid, p in self.positions.items()},
            'food_stages': {sid: {
                'id': s.id, 'dish_id': s.dish_id, 'step_order': s.step_order,
                'description': s.description, 'estimated_time': s.estimated_time,
                'required_technique': s.required_technique, 'required_station': s.required_station,
                'complexity': s.complexity
            } for sid, s in self.food_stages.items()},
            'precedence_graph': {k: list(v) for k, v in self.precedence_graph.items()}
        }
    
    def __str__(self):
        stats = self.get_summary_stats()
        return (f"CubicWorkflowStructure({self.cube.shape}) - "
                f"Asignaciones: {stats['total_assignments']}, "
                f"Utilización: {stats['utilization_rate']:.2%}, "
                f"Inconsistencias: {stats['inconsistencies_count']}")


def create_cubic_structure_from_menu(menu: List[Dish], persons: List[Person], 
                                    positions: List[Position]) -> CubicWorkflowStructure:
    """
    Crea una estructura cúbica a partir de un menú optimizado.
    
    Args:
        menu: Lista de platos del menú
        persons: Lista de personas (cocineros)
        positions: Lista de posiciones (estaciones)
    
    Returns:
        Estructura cúbica configurada
    """
    # Calcular dimensiones necesarias
    max_persons = len(persons)
    max_positions = len(positions)
    total_steps = sum(len(dish.steps) for dish in menu if hasattr(dish, 'steps') and dish.steps)
    max_precedence = max(50, total_steps + 10)  # Buffer para flexibilidad
    
    # Crear estructura
    cubic_structure = CubicWorkflowStructure(max_persons, max_positions, max_precedence)
    
    # Agregar personas
    for person in persons:
        cubic_structure.add_person(person)
    
    # Agregar posiciones
    for position in positions:
        cubic_structure.add_position(position)
    
    # Convertir pasos de platos a etapas de alimentos
    stage_id_counter = 0
    
    for dish in menu:
        if not hasattr(dish, 'steps') or not dish.steps:
            continue
        
        dish_stages = []
        
        for step in dish.steps:
            stage = FoodStage(
                id=stage_id_counter,
                dish_id=dish.id,
                step_order=step.order,
                description=f"{dish.name}: {step.description}",
                estimated_time=float(getattr(step, 'time', 0)),
                required_technique=getattr(step, 'technique', ''),
                required_station=getattr(step, 'station', ''),
                complexity=getattr(dish, 'complexity', 5)
            )
            
            cubic_structure.add_food_stage(stage)
            dish_stages.append(stage)
            stage_id_counter += 1
        
        # Agregar dependencias secuenciales entre pasos del mismo plato
        for i in range(len(dish_stages) - 1):
            cubic_structure.add_precedence_constraint(dish_stages[i].id, dish_stages[i + 1].id)
    
    logging.info(f"Estructura cúbica creada: {stage_id_counter} etapas de {len(menu)} platos")
    
    return cubic_structure