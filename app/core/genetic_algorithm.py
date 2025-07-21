# app/core/genetic_algorithm.py
import random
from collections import defaultdict
from decimal import Decimal # <-- AÑADIR ESTA LÍNEA

def create_individual(catalog, num_dishes):
    if len(catalog) >= num_dishes:
        return random.sample(catalog, num_dishes)
    return []

def calculate_fitness(menu, weights, price_factor):
    if not menu: return 0
    
   
    price_factor_decimal = Decimal(str(price_factor))
    
    num_dishes = len(menu)
   
    total_gain = sum((d.cost * price_factor_decimal) - d.cost for d in menu)
    
    avg_prep_time = sum(d.prep_time for d in menu) / num_dishes
    avg_popularity = sum(d.popularity for d in menu) / num_dishes
    
    # Calcular reutilización de ingredientes
    ingredient_usage = defaultdict(int)
    for dish in menu:
        for ing in dish.recipe.keys():
            ingredient_usage[ing.id] += 1
    
    reused_ingredients = sum(1 for count in ingredient_usage.values() if count > 1)
    
    # Normalizar scores (0 a 1)
    score_gain = min(float(total_gain) / (100 * num_dishes), 1.0)
    score_time = max(0, 1 - (avg_prep_time / 30)) # Objetivo: menos de 30 min
    score_popularity = avg_popularity / 10.0
    score_waste = reused_ingredients / len(ingredient_usage) if ingredient_usage else 0

    # Ponderar scores
    fitness = (
        score_gain * weights.get('ganancia', 0) +
        score_time * weights.get('tiempo', 0) +
        score_popularity * weights.get('popularidad', 0) +
        score_waste * weights.get('desperdicio', 0)
    )
    return fitness

def select_parents(population, fitnesses, k=3):
    sample = random.sample(list(zip(population, fitnesses)), k)
    return sorted(sample, key=lambda x: x[1], reverse=True)[0][0]

def crossover(parent1, parent2, catalog):
    if not parent1 or not parent2: return []
    
    point = random.randint(1, len(parent1) - 1)
    child = parent1[:point]
    
    for dish in parent2:
        if dish not in child and len(child) < len(parent1):
            child.append(dish)

    while len(child) < len(parent1):
        dish = random.choice(catalog)
        if dish not in child:
            child.append(dish)
            
    return child

def mutate(individual, catalog, prob=0.15):
    if not individual or random.random() >= prob or len(catalog) <= len(individual):
        return individual
        
    index_to_replace = random.randint(0, len(individual) - 1)
    new_dish = random.choice(catalog)
    
    while new_dish in individual:
        new_dish = random.choice(catalog)
        
    individual[index_to_replace] = new_dish
    return individual