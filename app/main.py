# app/main.py dsadasdasd
import tkinter as tk
from tkinter import messagebox
import logging
from app.data.database_manager import load_knowledge_base
from app.ui.app_gui import MenuOptimizerApp

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log", mode='w'),
                        logging.StreamHandler() # También muestra los logs en la consola
                    ])

if __name__ == "__main__":
    try:
        # Cargar toda la base de conocimiento desde la base de datos
        dish_catalog, all_techniques = load_knowledge_base()

        if not dish_catalog:
             logging.critical("La base de conocimiento de platos está vacía. La aplicación no puede iniciar.")
             messagebox.showerror("Error Crítico", "No se pudieron cargar datos de platos desde la base de datos. La aplicación no puede iniciar.")
        else:
            # Iniciar la aplicación de la GUI
            app = MenuOptimizerApp(dish_catalog, all_techniques)
            app.mainloop()

    except Exception as e:
        logging.critical(f"Fallo al iniciar la aplicación: {e}", exc_info=True)
        messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos MySQL o cargar los datos.\n\nAsegúrate de que el servidor MySQL esté corriendo y la configuración en 'config/db_config.ini' sea correcta.\n\nConsulta 'app.log' para más detalles.\n\nError: {e}")