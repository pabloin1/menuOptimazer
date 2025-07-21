CREATE DATABASE IF NOT EXISTS menu_optimizer_db;
USE menu_optimizer_db;

-- Tablas Maestras
CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100)
);

CREATE TABLE stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE allergens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE techniques (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Tabla de Ingredientes
CREATE TABLE ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    cost_per_kg DECIMAL(10, 2) NOT NULL,
    calories_per_kg INT,
    proteins_per_kg INT,
    carbs_per_kg INT,
    season ENUM('Todo el año', 'Primavera', 'Verano', 'Otoño', 'Invierno') NOT NULL,
    source ENUM('Local', 'Nacional', 'Importado') DEFAULT 'Nacional',
    availability ENUM('Alta', 'Media', 'Baja') DEFAULT 'Alta',
    shelf_life_days INT,
    supplier_id INT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- Tabla de Platos
CREATE TABLE dishes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    popularity INT,
    complexity INT,
    diet_type VARCHAR(50),
    tags VARCHAR(255)
);

-- Tablas de Enlace (Relaciones)
CREATE TABLE recipe_items (
    dish_id INT,
    ingredient_id INT,
    quantity_grams INT NOT NULL,
    PRIMARY KEY (dish_id, ingredient_id),
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE recipe_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dish_id INT,
    step_order INT NOT NULL,
    description TEXT,
    time_required_min INT NOT NULL,
    station_id INT,
    technique_id INT,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id),
    FOREIGN KEY (technique_id) REFERENCES techniques(id),
    UNIQUE (dish_id, step_order)
);

CREATE TABLE ingredient_allergens (
    ingredient_id INT,
    allergen_id INT,
    PRIMARY KEY (ingredient_id, allergen_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
    FOREIGN KEY (allergen_id) REFERENCES allergens(id)
);