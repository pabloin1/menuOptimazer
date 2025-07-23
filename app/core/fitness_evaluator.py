# app/core/fitness_evaluator.py
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Set, Tuple
from decimal import Decimal
import logging

from app.core.models import Dish


class FitnessEvaluator:
    """
    Evaluador de fitness que implementa las 7 variables de optimización:
    1. Margen de ganancia total del menú
    2. Tiempo promedio de preparación por pedido
    3. Balance nutricional del menú
    4. Variedad gastronómica
    5. Utilización eficiente de ingredientes
    6. Distribución de carga de trabajo entre estaciones
    7. Satisfacción proyectada del cliente
    """
    
    def __init__(self, constraints: Dict, weights: Dict):
        """
        Inicializa el evaluador con restricciones y pesos.
        
        Args:
            constraints: Restricciones del restaurante
            weights: Pesos para cada variable de optimización
        """
        self.constraints = constraints
        self.weights = weights
        
        # Valores de referencia para normalización
        self.reference_values = {
            'max_profit_margin': 80.0,  # 80% margen máximo esperado
            'optimal_prep_time': 20.0,  # 20 min tiempo óptimo
            'max_popularity': 10.0,     # Escala de popularidad 1-10
            'max_stations': 10.0,       # Número máximo de estaciones
            'max_ingredients': 50.0,    # Número máximo de ingredientes únicos
        }
    
    def evaluate_menu(self, menu: List[Dish]) -> float:
        """
        Evalúa un menú completo considerando las 7 variables de optimización.
        
        Args:
            menu: Lista de platos que conforman el menú
            
        Returns:
            Puntuación de fitness normalizada (0-1)
        """
        if not menu:
            return 0.0
        
        try:
            # Calcular cada componente del fitness
            profit_score = self._calculate_profit_score(menu)
            time_score = self._calculate_time_efficiency_score(menu)
            nutrition_score = self._calculate_nutrition_balance_score(menu)
            variety_score = self._calculate_variety_score(menu)
            ingredient_efficiency_score = self._calculate_ingredient_efficiency_score(menu)
            workload_distribution_score = self._calculate_workload_distribution_score(menu)
            satisfaction_score = self._calculate_customer_satisfaction_score(menu)
            
            # Combinar scores con pesos
            total_fitness = (
                profit_score * self.weights.get('ganancia', 0.25) +
                time_score * self.weights.get('tiempo', 0.15) +
                nutrition_score * self.weights.get('nutricion', 0.10) +
                variety_score * self.weights.get('variedad', 0.15) +
                ingredient_efficiency_score * self.weights.get('desperdicio', 0.15) +
                workload_distribution_score * self.weights.get('distribucion_carga', 0.10) +
                satisfaction_score * self.weights.get('popularidad', 0.10)
            )
            
            # Aplicar penalizaciones por violación de restricciones
            penalty = self._calculate_constraint_penalties(menu)
            
            final_fitness = max(0.0, total_fitness - penalty)
            
            logging.debug(f"Fitness components - Profit: {profit_score:.3f}, "
                         f"Time: {time_score:.3f}, Nutrition: {nutrition_score:.3f}, "
                         f"Variety: {variety_score:.3f}, Ingredients: {ingredient_efficiency_score:.3f}, "
                         f"Workload: {workload_distribution_score:.3f}, "
                         f"Satisfaction: {satisfaction_score:.3f}, Penalty: {penalty:.3f}")
            
            return final_fitness
            
        except Exception as e:
            logging.error(f"Error evaluating menu fitness: {e}")
            return 0.0
    
    def _calculate_profit_score(self, menu: List[Dish]) -> float:
        """
        1. Margen de ganancia total del menú considerando costos de ingredientes
        """
        price_factor = self.constraints.get('price_factor', 1.5)
        
        total_cost = 0.0
        total_revenue = 0.0
        
        for dish in menu:
            cost = self._get_dish_cost(dish)
            revenue = cost * price_factor
            
            total_cost += cost
            total_revenue += revenue
        
        if total_revenue == 0:
            return 0.0
        
        profit_margin = ((total_revenue - total_cost) / total_revenue) * 100
        
        # Normalizar (0-1) basado en margen objetivo
        target_margin = self.constraints.get('min_profit_margin', 40.0)
        if profit_margin >= target_margin:
            score = min(1.0, profit_margin / self.reference_values['max_profit_margin'])
        else:
            # Penalizar si no alcanza el margen mínimo
            score = profit_margin / target_margin * 0.5
        
        return score
    
    def _calculate_time_efficiency_score(self, menu: List[Dish]) -> float:
        """
        2. Tiempo promedio de preparación por pedido para optimizar flujo de cocina
        """
        total_time = 0.0
        
        for dish in menu:
            prep_time = self._get_dish_prep_time(dish)
            total_time += prep_time
        
        avg_prep_time = total_time / len(menu)
        optimal_time = self.reference_values['optimal_prep_time']
        
        # Score más alto para tiempos cercanos al óptimo
        if avg_prep_time <= optimal_time:
            score = 1.0
        else:
            # Penalización exponencial para tiempos muy largos
            score = max(0.0, 1.0 - ((avg_prep_time - optimal_time) / optimal_time) ** 2)
        
        return score
    
    def _calculate_nutrition_balance_score(self, menu: List[Dish]) -> float:
        """
        3. Balance nutricional del menú (proteínas, carbohidratos, vitaminas, calorías)
        """
        diet_types = []
        complexity_variance = []
        
        for dish in menu:
            # Recopilar tipos de dieta
            diet_type = getattr(dish, 'diet_type', 'Omnívoro')
            diet_types.append(diet_type)
            
            # Recopilar complejidad para varianza
            complexity = getattr(dish, 'complexity', 3)
            complexity_variance.append(complexity)
        
        # Score basado en diversidad de tipos de dieta
        diet_diversity = len(set(diet_types)) / len(diet_types) if diet_types else 0
        
        # Score basado en varianza de complejidad (evitar todos muy fáciles o muy difíciles)
        if len(complexity_variance) > 1:
            complexity_balance = 1.0 - (np.std(complexity_variance) / 3.0)  # Normalizar por max std posible
            complexity_balance = max(0.0, min(1.0, complexity_balance))
        else:
            complexity_balance = 0.5
        
        # Combinar métricas
        nutrition_score = (diet_diversity * 0.6) + (complexity_balance * 0.4)
        
        return nutrition_score
    
    def _calculate_variety_score(self, menu: List[Dish]) -> float:
        """
        4. Variedad gastronómica para satisfacer diferentes gustos y restricciones dietéticas
        """
        # Extraer tags de todos los platos
        all_tags = []
        cuisine_types = set()
        
        for dish in menu:
            if hasattr(dish, 'tags') and dish.tags:
                tags = dish.tags.split(',') if isinstance(dish.tags, str) else dish.tags
                all_tags.extend([tag.strip() for tag in tags])
                
                # Identificar tipos de cocina
                for tag in tags:
                    tag = tag.strip().lower()
                    if tag in ['mexicano', 'italiano', 'asiático', 'francés', 'español', 'árabe', 'indio', 'japonés']:
                        cuisine_types.add(tag)
        
        # Diversidad de tags
        unique_tags = len(set(all_tags))
        tag_diversity = min(1.0, unique_tags / 10.0)  # Normalizar a máximo 10 tags únicos
        
        # Diversidad de tipos de cocina
        cuisine_diversity = min(1.0, len(cuisine_types) / 3.0)  # Máximo 3 cocinas diferentes
        
        # Score combinado
        variety_score = (tag_diversity * 0.6) + (cuisine_diversity * 0.4)
        
        return variety_score
    
    def _calculate_ingredient_efficiency_score(self, menu: List[Dish]) -> float:
        """
        5. Utilización eficiente de ingredientes para minimizar desperdicio
        """
        ingredient_usage = defaultdict(int)
        total_ingredients = 0
        
        # Contar uso de ingredientes
        for dish in menu:
            if hasattr(dish, 'recipe') and dish.recipe:
                for ingredient in dish.recipe.keys():
                    ingredient_usage[ingredient.id] += 1
                    total_ingredients += 1
        
        if total_ingredients == 0:
            return 0.0
        
        # Calcular eficiencia de reutilización
        reused_ingredients = sum(1 for count in ingredient_usage.values() if count > 1)
        unique_ingredients = len(ingredient_usage)
        
        # Score más alto cuando hay más reutilización
        if unique_ingredients > 0:
            reuse_ratio = reused_ingredients / unique_ingredients
            # Bonus por usar menos ingredientes únicos totales
            efficiency_bonus = max(0.0, 1.0 - (unique_ingredients / self.reference_values['max_ingredients']))
            efficiency_score = (reuse_ratio * 0.7) + (efficiency_bonus * 0.3)
        else:
            efficiency_score = 0.0
        
        return min(1.0, efficiency_score)
    
    def _calculate_workload_distribution_score(self, menu: List[Dish]) -> float:
        """
        6. Distribución de carga de trabajo entre diferentes estaciones de cocina
        """
        station_workload = defaultdict(int)
        station_time = defaultdict(float)
        
        # Calcular carga por estación
        for dish in menu:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    if hasattr(step, 'station') and step.station:
                        station_workload[step.station] += 1
                        if hasattr(step, 'time'):
                            station_time[step.station] += float(getattr(step, 'time', 0))
        
        if not station_time:
            return 0.5  # Score neutral si no hay información de estaciones
        
        # Calcular varianza de tiempo por estación (menor varianza = mejor distribución)
        time_values = list(station_time.values())
        if len(time_values) > 1:
            time_variance = np.var(time_values)
            max_possible_variance = (max(time_values) ** 2) / 4  # Normalización aproximada
            
            # Score más alto para menor varianza (mejor distribución)
            distribution_score = max(0.0, 1.0 - (time_variance / max_possible_variance))
        else:
            distribution_score = 0.0  # Penalizar usar solo una estación
        
        # Bonus por usar múltiples estaciones
        station_diversity = min(1.0, len(station_workload) / self.reference_values['max_stations'])
        
        # Score combinado
        workload_score = (distribution_score * 0.7) + (station_diversity * 0.3)
        
        return workload_score
    
    def _calculate_customer_satisfaction_score(self, menu: List[Dish]) -> float:
        """
        7. Satisfacción proyectada del cliente basada en tendencias y preferencias históricas
        """
        total_popularity = 0.0
        popularity_variance = []
        
        for dish in menu:
            popularity = getattr(dish, 'popularity', 5)  # Default neutral
            total_popularity += popularity
            popularity_variance.append(popularity)
        
        # Score basado en popularidad promedio
        avg_popularity = total_popularity / len(menu)
        popularity_score = avg_popularity / self.reference_values['max_popularity']
        
        # Penalizar varianza extrema en popularidad
        if len(popularity_variance) > 1:
            variance_penalty = min(0.3, np.std(popularity_variance) / 5.0)
        else:
            variance_penalty = 0.0
        
        satisfaction_score = max(0.0, popularity_score - variance_penalty)
        
        return min(1.0, satisfaction_score)
    
    def _calculate_constraint_penalties(self, menu: List[Dish]) -> float:
        """
        Calcula penalizaciones por violación de restricciones duras.
        """
        penalty = 0.0
        
        # Penalización por exceder costo máximo por plato
        max_cost = self.constraints.get('max_cost_per_dish', float('inf'))
        for dish in menu:
            cost = self._get_dish_cost(dish)
            if cost > max_cost:
                penalty += (cost - max_cost) / max_cost * 0.5
        
        # Penalización por no cumplir margen mínimo
        price_factor = self.constraints.get('price_factor', 1.5)
        min_margin = self.constraints.get('min_profit_margin', 0.0)
        
        total_cost = sum(self._get_dish_cost(dish) for dish in menu)
        total_revenue = total_cost * price_factor
        
        if total_revenue > 0:
            actual_margin = ((total_revenue - total_cost) / total_revenue) * 100
            if actual_margin < min_margin:
                penalty += (min_margin - actual_margin) / min_margin * 0.3
        
        return penalty
    
    def _get_dish_cost(self, dish: Dish) -> float:
        """Obtiene el costo de un plato (precalculado o estimado)."""
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
            return float(dish.complexity) * 5  # 5 min por nivel de complejidad
        return 15.0  # Tiempo por defecto