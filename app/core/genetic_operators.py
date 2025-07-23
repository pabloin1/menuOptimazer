# app/core/genetic_operators.py
import random
from typing import List, Tuple
import logging
import numpy as np

from app.core.models import Dish


class GeneticOperators:
    """
    Operadores genéticos especializados para optimización de menús.
    Implementa múltiples estrategias de cruzamiento y mutación.
    """
    
    def __init__(self, catalog: List[Dish], mutation_rate: float = 0.15):
        """
        Inicializa los operadores genéticos.
        
        Args:
            catalog: Catálogo completo de platos disponibles
            mutation_rate: Tasa de mutación base
        """
        self.catalog = catalog
        self.mutation_rate = mutation_rate
        
        # Agrupar platos por características para operadores inteligentes
        self._group_dishes_by_characteristics()
    
    def _group_dishes_by_characteristics(self):
        """Agrupa platos por características para cruzamientos inteligentes."""
        self.dishes_by_type = {
            'appetizers': [],
            'main_courses': [],
            'desserts': [],
            'beverages': []
        }
        
        self.dishes_by_cuisine = {}
        self.dishes_by_diet = {}
        self.dishes_by_complexity = {i: [] for i in range(1, 11)}
        
        for dish in self.catalog:
            # Agrupar por tipo (basado en tags)
            tags = getattr(dish, 'tags', '')
            if isinstance(tags, str):
                tags = tags.lower()
                if any(word in tags for word in ['entrada', 'aperitivo', 'sopa']):
                    self.dishes_by_type['appetizers'].append(dish)
                elif any(word in tags for word in ['postre', 'dulce', 'helado']):
                    self.dishes_by_type['desserts'].append(dish)
                elif any(word in tags for word in ['bebida', 'agua', 'té', 'café']):
                    self.dishes_by_type['beverages'].append(dish)
                else:
                    self.dishes_by_type['main_courses'].append(dish)
                
                # Agrupar por cocina
                for cuisine in ['mexicano', 'italiano', 'asiático', 'francés', 'español', 'japonés', 'indio']:
                    if cuisine in tags:
                        if cuisine not in self.dishes_by_cuisine:
                            self.dishes_by_cuisine[cuisine] = []
                        self.dishes_by_cuisine[cuisine].append(dish)
            
            # Agrupar por tipo de dieta
            diet_type = getattr(dish, 'diet_type', 'Omnívoro')
            if diet_type not in self.dishes_by_diet:
                self.dishes_by_diet[diet_type] = []
            self.dishes_by_diet[diet_type].append(dish)
            
            # Agrupar por complejidad
            complexity = getattr(dish, 'complexity', 5)
            if 1 <= complexity <= 10:
                self.dishes_by_complexity[complexity].append(dish)
    
    def crossover(self, parent1: List[Dish], parent2: List[Dish]) -> Tuple[List[Dish], List[Dish]]:
        """
        Realiza cruzamiento entre dos menús padres.
        Usa múltiples estrategias de cruzamiento.
        
        Args:
            parent1, parent2: Menús padres
            
        Returns:
            Tupla con dos menús hijos
        """
        if not parent1 or not parent2:
            return parent1[:], parent2[:]
        
        # Seleccionar estrategia de cruzamiento aleatoriamente
        crossover_strategies = [
            self._uniform_crossover,
            self._single_point_crossover,
            self._cuisine_based_crossover,
            self._balanced_crossover
        ]
        
        strategy = random.choice(crossover_strategies)
        
        try:
            offspring1, offspring2 = strategy(parent1, parent2)
            
            # Validar y reparar descendencia
            offspring1 = self._repair_individual(offspring1, len(parent1))
            offspring2 = self._repair_individual(offspring2, len(parent2))
            
            return offspring1, offspring2
            
        except Exception as e:
            logging.warning(f"Error in crossover: {e}. Using fallback crossover.")
            return self._single_point_crossover(parent1, parent2)
    
    def _uniform_crossover(self, parent1: List[Dish], parent2: List[Dish]) -> Tuple[List[Dish], List[Dish]]:
        """Cruzamiento uniforme: cada gen se hereda aleatoriamente."""
        offspring1 = []
        offspring2 = []
        
        for i in range(min(len(parent1), len(parent2))):
            if random.random() < 0.5:
                offspring1.append(parent1[i])
                offspring2.append(parent2[i])
            else:
                offspring1.append(parent2[i])
                offspring2.append(parent1[i])
        
        return offspring1, offspring2
    
    def _single_point_crossover(self, parent1: List[Dish], parent2: List[Dish]) -> Tuple[List[Dish], List[Dish]]:
        """Cruzamiento de un punto: intercambiar segmentos."""
        min_length = min(len(parent1), len(parent2))
        if min_length <= 1:
            return parent1[:], parent2[:]
        
        crossover_point = random.randint(1, min_length - 1)
        
        offspring1 = parent1[:crossover_point] + parent2[crossover_point:]
        offspring2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return offspring1, offspring2
    
    def _cuisine_based_crossover(self, parent1: List[Dish], parent2: List[Dish]) -> Tuple[List[Dish], List[Dish]]:
        """Cruzamiento basado en tipos de cocina para mantener coherencia."""
        offspring1 = []
        offspring2 = []
        
        # Intentar mantener coherencia de cocina
        for dish1, dish2 in zip(parent1, parent2):
            cuisine1 = self._get_dish_cuisine(dish1)
            cuisine2 = self._get_dish_cuisine(dish2)
            
            # Si las cocinas son compatibles, intercambiar
            if cuisine1 == cuisine2 or random.random() < 0.3:
                if random.random() < 0.5:
                    offspring1.append(dish1)
                    offspring2.append(dish2)
                else:
                    offspring1.append(dish2)
                    offspring2.append(dish1)
            else:
                # Mantener cocinas separadas
                offspring1.append(dish1)
                offspring2.append(dish2)
        
        return offspring1, offspring2
    
    def _balanced_crossover(self, parent1: List[Dish], parent2: List[Dish]) -> Tuple[List[Dish], List[Dish]]:
        """Cruzamiento que intenta mantener balance en complejidad y tipos."""
        offspring1 = []
        offspring2 = []
        
        # Calcular métricas de balance para padres
        balance1 = self._calculate_menu_balance(parent1)
        balance2 = self._calculate_menu_balance(parent2)
        
        # Heredar de padre más balanceado con mayor probabilidad
        for i in range(min(len(parent1), len(parent2))):
            if balance1 > balance2:
                prob_parent1 = 0.7
            elif balance2 > balance1:
                prob_parent1 = 0.3
            else:
                prob_parent1 = 0.5
            
            if random.random() < prob_parent1:
                offspring1.append(parent1[i])
                offspring2.append(parent2[i])
            else:
                offspring1.append(parent2[i])
                offspring2.append(parent1[i])
        
        return offspring1, offspring2
    
    def mutate(self, individual: List[Dish]) -> List[Dish]:
        """
        Aplica mutación a un individuo usando múltiples estrategias.
        
        Args:
            individual: Menú a mutar
            
        Returns:
            Menú mutado
        """
        if not individual or random.random() >= self.mutation_rate:
            return individual[:]
        
        # Seleccionar estrategia de mutación
        mutation_strategies = [
            self._random_replacement_mutation,
            self._smart_replacement_mutation,
            self._swap_mutation,
            self._cuisine_consistent_mutation
        ]
        
        strategy = random.choice(mutation_strategies)
        
        try:
            mutated = strategy(individual[:])
            return self._repair_individual(mutated, len(individual))
        except Exception as e:
            logging.warning(f"Error in mutation: {e}. Using fallback mutation.")
            return self._random_replacement_mutation(individual[:])
    
    def _random_replacement_mutation(self, individual: List[Dish]) -> List[Dish]:
        """Mutación por reemplazo aleatorio."""
        if not self.catalog:
            return individual
        
        mutation_index = random.randint(0, len(individual) - 1)
        new_dish = random.choice(self.catalog)
        
        # Evitar duplicados
        attempts = 0
        while new_dish in individual and attempts < 10:
            new_dish = random.choice(self.catalog)
            attempts += 1
        
        if new_dish not in individual:
            individual[mutation_index] = new_dish
        
        return individual
    
    def _smart_replacement_mutation(self, individual: List[Dish]) -> List[Dish]:
        """Mutación inteligente basada en características del plato a reemplazar."""
        if not self.catalog:
            return individual
        
        mutation_index = random.randint(0, len(individual) - 1)
        old_dish = individual[mutation_index]
        
        # Buscar platos similares
        similar_dishes = self._find_similar_dishes(old_dish)
        
        if similar_dishes:
            candidates = [dish for dish in similar_dishes if dish not in individual]
            if candidates:
                individual[mutation_index] = random.choice(candidates)
            else:
                # Fallback a mutación aleatoria
                return self._random_replacement_mutation(individual)
        
        return individual
    
    def _swap_mutation(self, individual: List[Dish]) -> List[Dish]:
        """Mutación por intercambio de posiciones."""
        if len(individual) < 2:
            return individual
        
        idx1, idx2 = random.sample(range(len(individual)), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
        
        return individual
    
    def _cuisine_consistent_mutation(self, individual: List[Dish]) -> List[Dish]:
        """Mutación que mantiene consistencia de cocina."""
        if not individual:
            return individual
        
        mutation_index = random.randint(0, len(individual) - 1)
        old_dish = individual[mutation_index]
        old_cuisine = self._get_dish_cuisine(old_dish)
        
        # Buscar platos de la misma cocina
        if old_cuisine and old_cuisine in self.dishes_by_cuisine:
            candidates = [dish for dish in self.dishes_by_cuisine[old_cuisine] 
                         if dish not in individual]
            if candidates:
                individual[mutation_index] = random.choice(candidates)
                return individual
        
        # Fallback a mutación inteligente
        return self._smart_replacement_mutation(individual)
    
    def _repair_individual(self, individual: List[Dish], target_length: int) -> List[Dish]:
        """
        Repara un individuo eliminando duplicados y ajustando longitud.
        
        Args:
            individual: Individuo a reparar
            target_length: Longitud objetivo
            
        Returns:
            Individuo reparado
        """
        if not individual:
            return []
        
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_individual = []
        for dish in individual:
            if dish.id not in seen:
                unique_individual.append(dish)
                seen.add(dish.id)
        
        # Ajustar longitud
        while len(unique_individual) < target_length:
            # Agregar platos aleatorios que no estén ya incluidos
            available_dishes = [dish for dish in self.catalog if dish.id not in seen]
            if available_dishes:
                new_dish = random.choice(available_dishes)
                unique_individual.append(new_dish)
                seen.add(new_dish.id)
            else:
                break
        
        # Truncar si es necesario
        return unique_individual[:target_length]
    
    def _find_similar_dishes(self, dish: Dish) -> List[Dish]:
        """Encuentra platos similares basados en características."""
        similar_dishes = []
        
        # Buscar por cocina
        cuisine = self._get_dish_cuisine(dish)
        if cuisine and cuisine in self.dishes_by_cuisine:
            similar_dishes.extend(self.dishes_by_cuisine[cuisine])
        
        # Buscar por tipo de dieta
        diet_type = getattr(dish, 'diet_type', None)
        if diet_type and diet_type in self.dishes_by_diet:
            similar_dishes.extend(self.dishes_by_diet[diet_type])
        
        # Buscar por complejidad similar (±1 nivel)
        complexity = getattr(dish, 'complexity', 5)
        for level in range(max(1, complexity - 1), min(11, complexity + 2)):
            similar_dishes.extend(self.dishes_by_complexity[level])
        
        # Eliminar duplicados y el plato original
        unique_similar = []
        seen = {dish.id}
        for similar_dish in similar_dishes:
            if similar_dish.id not in seen:
                unique_similar.append(similar_dish)
                seen.add(similar_dish.id)
        
        return unique_similar
    
    def _get_dish_cuisine(self, dish: Dish) -> str:
        """Extrae el tipo de cocina de un plato."""
        tags = getattr(dish, 'tags', '')
        if isinstance(tags, str):
            tags = tags.lower()
            for cuisine in ['mexicano', 'italiano', 'asiático', 'francés', 'español', 'japonés', 'indio']:
                if cuisine in tags:
                    return cuisine
        return None
    
    def _calculate_menu_balance(self, menu: List[Dish]) -> float:
        """Calcula una métrica de balance para un menú."""
        if not menu:
            return 0.0
        
        # Balance de complejidad
        complexities = [getattr(dish, 'complexity', 5) for dish in menu]
        complexity_std = np.std(complexities) if len(complexities) > 1 else 0
        complexity_balance = max(0, 1 - complexity_std / 3)
        
        # Balance de popularidad
        popularities = [getattr(dish, 'popularity', 5) for dish in menu]
        popularity_avg = np.mean(popularities)
        popularity_balance = popularity_avg / 10.0
        
        # Diversidad de tipos
        diet_types = set(getattr(dish, 'diet_type', 'Omnívoro') for dish in menu)
        type_diversity = len(diet_types) / len(menu)
        
        return (complexity_balance + popularity_balance + type_diversity) / 3