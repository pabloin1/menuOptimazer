# app/data/database_manager.py
import mysql.connector
import configparser
import logging
from app.core.models import Supplier, Ingredient, Dish, RecipeStep

def get_db_connection():
    config = configparser.ConfigParser()
    config.read('config/db_config.ini')
    logging.info(f"Intentando conectar a la base de datos '{config['mysql']['database']}' en host '{config['mysql']['host']}'...")
    return mysql.connector.connect(**config['mysql'])

def load_knowledge_base():
    conn = get_db_connection()
    logging.info("Conexión a la base de datos exitosa.")
    cursor = conn.cursor(dictionary=True)

    # 1. Cargar datos maestros
    cursor.execute("SELECT id, name, contact_person, phone FROM suppliers")
    suppliers = {row['id']: Supplier(**row) for row in cursor.fetchall()}

    cursor.execute("SELECT id, name FROM stations")
    stations = {row['id']: row['name'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, name FROM techniques")
    techniques = {row['id']: row['name'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, name FROM allergens")
    allergens_map = {row['id']: row['name'] for row in cursor.fetchall()}
    
    cursor.execute("SELECT ingredient_id, allergen_id FROM ingredient_allergens")
    ingredient_allergens_relations = cursor.fetchall()
    
    allergens_by_ingredient = {}
    for rel in ingredient_allergens_relations:
        ing_id = rel['ingredient_id']
        allergen_name = allergens_map.get(rel['allergen_id'])
        if ing_id not in allergens_by_ingredient:
            allergens_by_ingredient[ing_id] = []
        allergens_by_ingredient[ing_id].append(allergen_name)

    # 2. Cargar ingredientes
    cursor.execute("SELECT * FROM ingredients")
    ingredients_data = cursor.fetchall()
    ingredients = {}
    for i_data in ingredients_data:
        i_data['supplier'] = suppliers.get(i_data['supplier_id'])
        i_data['allergens'] = allergens_by_ingredient.get(i_data['id'], [])
        ingredients[i_data['id']] = Ingredient(**i_data)

    # 3. Cargar Platos y sus componentes
    cursor.execute("SELECT * FROM dishes")
    dishes_data = cursor.fetchall()
    
    dish_catalog = []
    for d_data in dishes_data:
        dish_id = d_data['id']
        
        # Cargar receta (ingredientes y cantidades)
        cursor.execute("SELECT ingredient_id, quantity_grams FROM recipe_items WHERE dish_id = %s", (dish_id,))
        recipe_items = {ingredients[row['ingredient_id']]: row['quantity_grams'] for row in cursor.fetchall()}
        
        # Cargar pasos
        cursor.execute("""
            SELECT rs.step_order, rs.description, rs.time_required_min, rs.station_id, rs.technique_id
            FROM recipe_steps rs WHERE rs.dish_id = %s ORDER BY rs.step_order
        """, (dish_id,))
        
        recipe_steps = [
            RecipeStep(
                order=row['step_order'],
                description=row['description'],
                time=row['time_required_min'],
                station=stations.get(row['station_id']),
                technique=techniques.get(row['technique_id'])
            ) for row in cursor.fetchall()
        ]
        
        d_data['recipe'] = recipe_items
        d_data['steps'] = recipe_steps
        dish_catalog.append(Dish(**d_data))
        
    cursor.close()
    conn.close()
    
    logging.info(f"Carga completa. Se cargaron {len(ingredients)} ingredientes y {len(dish_catalog)} platos.")
    
    # Devolver los datos en el formato que la app espera
    return dish_catalog, list(techniques.values())