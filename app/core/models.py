# app/core/models.py
from functools import cached_property

class Supplier:
    def __init__(self, id, name, **kwargs):
        self.id, self.name = id, name
        self.contact_person = kwargs.get('contact_person')
        self.phone = kwargs.get('phone')
    def __repr__(self): return self.name

class Ingredient:
    def __init__(self, id, name, cost_per_kg, **kwargs):
        self.id, self.name, self.cost_per_kg = id, name, cost_per_kg
        self.supplier = kwargs.get('supplier')
        self.allergens = kwargs.get('allergens', [])
        self.calories_per_kg = kwargs.get('calories_per_kg', 0)
        self.season = kwargs.get('season', 'Todo el año')
    def __repr__(self): return self.name

class RecipeStep:
    def __init__(self, order, description, time, station, technique):
        self.order, self.description, self.time = order, description, time
        self.station, self.technique = station, technique

class Dish:
    def __init__(self, id, name, popularity, complexity, **kwargs):
        self.id, self.name = id, name,
        self.popularity, self.complexity = popularity, complexity
        self.diet_type = kwargs.get('diet_type', 'N/D')
        self.tags = kwargs.get('tags', [])
        self.recipe = kwargs.get('recipe', {}) # {Ingredient_obj: quantity_gr}
        self.steps = kwargs.get('steps', [])   # [RecipeStep_obj]

    @cached_property
    def prep_time(self):
        """Calcula el tiempo total de preparación sumando los pasos."""
        return sum(step.time for step in self.steps)

    @cached_property
    def cost(self):
        """Calcula el costo total de producción del plato."""
        return sum((ing.cost_per_kg / 1000) * qty for ing, qty in self.recipe.items())

    def get_allergens(self):
        """Obtiene una lista única de alérgenos del plato."""
        return sorted(list(set(allergen for ing in self.recipe.keys() for allergen in ing.allergens)))
        
    def __repr__(self): return self.name