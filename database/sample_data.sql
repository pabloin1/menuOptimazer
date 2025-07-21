USE menu_optimizer_db;

-- Insertar datos maestros
INSERT INTO suppliers (id, name, contact_person, phone, email) VALUES
(1, 'Carnes del Norte S.A.', 'Juan Pérez', '55-1234-5678', 'ventas@carnesnorte.com'),
(2, 'Frutas y Verduras del Valle', 'María López', '55-8765-4321', 'pedidos@fvvalle.mx'),
(3, 'Mariscos Frescos del Golfo', 'Carlos Sánchez', '55-5555-1234', 'csanchez@mariscosgolfo.net');

INSERT INTO stations (id, name) VALUES
(1, 'Mise en Place'), (2, 'Plancha'), (3, 'Horno'), (4, 'Estofados y Salsas'), (5, 'Fritura'), (6, 'Ensamblaje y Emplatado');

INSERT INTO allergens (id, name) VALUES (1, 'pescado'), (2, 'crustaceos'), (3, 'gluten'), (4, 'lacteos');

INSERT INTO techniques (id, name) VALUES (1, 'Plancha'), (2, 'Hervido'), (3, 'Salteado'), (4, 'Horneado');

-- Insertar ingredientes
INSERT INTO ingredients (name, cost_per_kg, calories_per_kg, season, supplier_id, shelf_life_days) VALUES
('Pechuga de Pollo', 130.00, 1650, 'Todo el año', 1, 4),
('Arroz Blanco', 35.00, 1300, 'Todo el año', 2, 365),
('Salmón Fresco', 420.00, 2080, 'Invierno', 3, 3),
('Quinoa', 120.00, 3680, 'Todo el año', 2, 365);
INSERT INTO ingredient_allergens (ingredient_id, allergen_id) VALUES (3, 1);

-- Insertar platos
INSERT INTO dishes (name, popularity, complexity, diet_type, tags) VALUES
('Pechuga a la Plancha con Arroz', 8, 2, 'Omnívoro', 'casual,rápido'),
('Salmón Invernal', 9, 4, 'Sin Gluten', 'elegante');

-- Insertar recetas
INSERT INTO recipe_items (dish_id, ingredient_id, quantity_grams) VALUES
(1, 1, 220), (1, 2, 150),
(2, 3, 180), (2, 4, 120);

-- Insertar pasos de receta
INSERT INTO recipe_steps (dish_id, step_order, description, time_required_min, station_id, technique_id) VALUES
-- Pasos para Pechuga
(1, 1, 'Hervir arroz', 20, 4, 2),
(1, 2, 'Sazonar y cocinar pechuga a la plancha', 10, 2, 1),
(1, 3, 'Emplatar pechuga y arroz', 5, 6, NULL),
-- Pasos para Salmón
(2, 1, 'Hervir quinoa', 15, 4, 2),
(2, 2, 'Hornear el salmón con especias', 20, 3, 4),
(2, 3, 'Emplatar salmón sobre cama de quinoa', 5, 6, NULL);