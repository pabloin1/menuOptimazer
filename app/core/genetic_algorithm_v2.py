# app/core/genetic_algorithm_v2.py
import random
import numpy as np
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Tuple, Set
import logging

from app.core.models import Dish
from app.core.fitness_evaluator import FitnessEvaluator
from app.core.genetic_operators import GeneticOperators


class MenuGeneticAlgorithm:
    """
    Algoritmo Genético para optimización de menús gastronómicos.
    Implementa las 7 variables de optimización especificadas en la propuesta.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa el algoritmo genético con configuración personalizada.
        
        Args:
            config: Diccionario con parámetros de configuración del algoritmo
        """
        # Parámetros del algoritmo genético
        self.population_size = config.get('population_size', 120)
        self.generations = config.get('generations', 200)
        self.mutation_rate = config.get('mutation_rate', 0.15)
        self.elite_size = config.get('elite_size', 10)
        self.tournament_size = config.get('tournament_size', 5)
        
        # Parámetros del problema
        self.num_dishes = config.get('num_dishes', 6)
        self.catalog = config.get('catalog', [])
        self.constraints = config.get('constraints', {})
        self.optimization_weights = config.get('optimization_weights', {})
        
        # Inicializar evaluadores y operadores
        self.fitness_evaluator = FitnessEvaluator(
            constraints=self.constraints,
            weights=self.optimization_weights
        )
        self.genetic_operators = GeneticOperators(
            catalog=self.catalog,
            mutation_rate=self.mutation_rate
        )
        
        # Estadísticas de la evolución
        self.evolution_stats = {
            'best_fitness_per_generation': [],
            'avg_fitness_per_generation': [],
            'diversity_per_generation': []
        }
    
    def create_initial_population(self) -> List[List[Dish]]:
        """
        Crea la población inicial de menús usando diferentes estrategias.
        
        Returns:
            Lista de individuos (menús) para la población inicial
        """
        population = []
        
        # Estrategia 1: Completamente aleatoria (40%)
        for _ in range(int(self.population_size * 0.4)):
            individual = self._create_random_individual()
            if individual:
                population.append(individual)
        
        # Estrategia 2: Basada en popularidad (30%)
        for _ in range(int(self.population_size * 0.3)):
            individual = self._create_popularity_based_individual()
            if individual:
                population.append(individual)
        
        # Estrategia 3: Basada en rentabilidad (30%)
        for _ in range(int(self.population_size * 0.3)):
            individual = self._create_profit_based_individual()
            if individual:
                population.append(individual)
        
        # Completar población si es necesario
        while len(population) < self.population_size:
            individual = self._create_random_individual()
            if individual:
                population.append(individual)
        
        logging.info(f"Población inicial creada: {len(population)} individuos")
        return population[:self.population_size]
    
    def _create_random_individual(self) -> List[Dish]:
        """Crea un individuo completamente aleatorio."""
        if len(self.catalog) >= self.num_dishes:
            return random.sample(self.catalog, self.num_dishes)
        return []
    
    def _create_popularity_based_individual(self) -> List[Dish]:
        """Crea un individuo priorizando platos populares."""
        if not self.catalog:
            return []
        
        # Ordenar por popularidad
        sorted_dishes = sorted(self.catalog, 
                             key=lambda d: getattr(d, 'popularity', 0), 
                             reverse=True)
        
        # Seleccionar top 50% con alguna aleatoriedad
        top_half = sorted_dishes[:len(sorted_dishes)//2]
        if len(top_half) >= self.num_dishes:
            return random.sample(top_half, self.num_dishes)
        return self._create_random_individual()
    
    def _create_profit_based_individual(self) -> List[Dish]:
        """Crea un individuo priorizando rentabilidad."""
        if not self.catalog:
            return []
        
        price_factor = self.constraints.get('price_factor', 1.5)
        
        # Calcular rentabilidad estimada para cada plato
        profit_dishes = []
        for dish in self.catalog:
            cost = getattr(dish, '_calculated_cost', 0) or self._estimate_dish_cost(dish)
            profit = (cost * price_factor) - cost
            profit_dishes.append((dish, profit))
        
        # Ordenar por rentabilidad
        profit_dishes.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar top platos rentables
        top_profitable = [dish for dish, _ in profit_dishes[:len(profit_dishes)//2]]
        if len(top_profitable) >= self.num_dishes:
            return random.sample(top_profitable, self.num_dishes)
        return self._create_random_individual()
    
    def _estimate_dish_cost(self, dish: Dish) -> float:
        """Estima el costo de un plato si no está precalculado."""
        if hasattr(dish, 'recipe') and dish.recipe:
            total_cost = 0.0
            for ingredient, quantity in dish.recipe.items():
                if hasattr(ingredient, 'cost_per_kg'):
                    cost_per_kg = float(ingredient.cost_per_kg)
                    qty_kg = float(quantity) / 1000.0
                    total_cost += cost_per_kg * qty_kg
            return total_cost
        return 10.0  # Costo por defecto
    
    def evolve(self) -> Tuple[List[Dish], float, Dict]:
        """
        Ejecuta el algoritmo genético completo.
        
        Returns:
            Tupla con (mejor_menu, mejor_fitness, estadisticas)
        """
        logging.info("Iniciando evolución del algoritmo genético")
        
        # Crear población inicial
        population = self.create_initial_population()
        
        best_individual = None
        best_fitness = -float('inf')
        
        for generation in range(self.generations):
            # Evaluar fitness de toda la población
            fitness_scores = []
            for individual in population:
                fitness = self.fitness_evaluator.evaluate_menu(individual)
                fitness_scores.append(fitness)
                
                # Actualizar mejor individuo
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()
            
            # Registrar estadísticas
            avg_fitness = np.mean(fitness_scores)
            diversity = self._calculate_diversity(population)
            
            self.evolution_stats['best_fitness_per_generation'].append(best_fitness)
            self.evolution_stats['avg_fitness_per_generation'].append(avg_fitness)
            self.evolution_stats['diversity_per_generation'].append(diversity)
            
            # Log progreso cada 25 generaciones
            if generation % 25 == 0:
                logging.info(f"Generación {generation}: "
                           f"Mejor fitness={best_fitness:.4f}, "
                           f"Promedio={avg_fitness:.4f}, "
                           f"Diversidad={diversity:.4f}")
            
            # Crear nueva generación
            if generation < self.generations - 1:
                population = self._create_new_generation(population, fitness_scores)
        
        logging.info(f"Evolución completada. Mejor fitness: {best_fitness:.4f}")
        
        return best_individual, best_fitness, self.evolution_stats
    
    def _create_new_generation(self, population: List[List[Dish]], 
                              fitness_scores: List[float]) -> List[List[Dish]]:
        """
        Crea una nueva generación usando elitismo y operadores genéticos.
        """
        new_population = []
        
        # Elitismo: mantener los mejores individuos
        elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
        for idx in elite_indices:
            new_population.append(population[idx].copy())
        
        # Generar resto de la población
        while len(new_population) < self.population_size:
            # Selección por torneo
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)
            
            # Cruzamiento
            offspring1, offspring2 = self.genetic_operators.crossover(parent1, parent2)
            
            # Mutación
            offspring1 = self.genetic_operators.mutate(offspring1)
            offspring2 = self.genetic_operators.mutate(offspring2)
            
            # Agregar descendencia válida
            if offspring1 and len(offspring1) == self.num_dishes:
                new_population.append(offspring1)
            if offspring2 and len(offspring2) == self.num_dishes and len(new_population) < self.population_size:
                new_population.append(offspring2)
        
        return new_population[:self.population_size]
    
    def _tournament_selection(self, population: List[List[Dish]], 
                             fitness_scores: List[float]) -> List[Dish]:
        """
        Selección por torneo para elegir padres.
        """
        tournament_indices = random.sample(range(len(population)), 
                                         min(self.tournament_size, len(population)))
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_idx].copy()
    
    def _calculate_diversity(self, population: List[List[Dish]]) -> float:
        """
        Calcula la diversidad de la población basada en platos únicos.
        """
        all_dishes = set()
        total_dishes = 0
        
        for individual in population:
            for dish in individual:
                all_dishes.add(dish.id)
                total_dishes += 1
        
        if total_dishes == 0:
            return 0.0
        
        return len(all_dishes) / total_dishes
    
    def get_multiple_solutions(self, num_solutions: int = 3) -> List[Tuple[List[Dish], float]]:
        """
        Ejecuta múltiples evoluciones para obtener diferentes soluciones óptimas.
        
        Args:
            num_solutions: Número de soluciones diferentes a generar
            
        Returns:
            Lista de tuplas (menu, fitness) con las mejores soluciones únicas
        """
        solutions = []
        seen_menus = set()
        
        for run in range(num_solutions * 2):  # Ejecutar más veces para encontrar soluciones únicas
            logging.info(f"Ejecutando búsqueda de solución {run + 1}")
            
            # Reiniciar estadísticas para cada ejecución
            self.evolution_stats = {
                'best_fitness_per_generation': [],
                'avg_fitness_per_generation': [],
                'diversity_per_generation': []
            }
            
            # Evolucionar
            best_menu, best_fitness, _ = self.evolve()
            
            if best_menu:
                # Crear signature del menú para verificar unicidad
                menu_signature = tuple(sorted([dish.id for dish in best_menu]))
                
                if menu_signature not in seen_menus:
                    solutions.append((best_menu, best_fitness))
                    seen_menus.add(menu_signature)
                    logging.info(f"Solución única {len(solutions)} encontrada con fitness: {best_fitness:.4f}")
                    
                    if len(solutions) >= num_solutions:
                        break
        
        # Ordenar por fitness descendente
        solutions.sort(key=lambda x: x[1], reverse=True)
        
        logging.info(f"Generadas {len(solutions)} soluciones únicas")
        return solutions[:num_solutions]