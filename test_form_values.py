# test_form_values.py - Script para probar la captura de valores
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.database_manager import load_knowledge_base
from app.ui.configuration_panel import ConfigurationPanel


def test_configuration_panel():
    """Prueba específica para verificar que los valores se capturen correctamente."""
    
    def on_optimize_test(config):
        """Callback de prueba para ver los valores capturados."""
        print("\n" + "="*60)
        print("🧪 PRUEBA DE CAPTURA DE VALORES - RESULTADOS")
        print("="*60)
        
        if config is None:
            print("❌ ERROR: Configuración es None")
            return
        
        print("✅ Configuración capturada exitosamente:")
        print(f"📊 Número de opciones en el menú: {config.get('num_dishes', 'NO CAPTURADO')}")
        print(f"💰 Presupuesto máximo por plato: {config.get('max_cost_per_dish', 'NO CAPTURADO')} MXN")
        print(f"👨‍🍳 Personal disponible: {config.get('num_chefs', 'NO CAPTURADO')} cocineros")
        print(f"📈 Margen mínimo de ganancia: {config.get('min_profit_margin', 'NO CAPTURADO')}%")
        print(f"🌱 Temporada: {config.get('season', 'NO CAPTURADO')}")
        print(f"🏪 Tipo de establecimiento: {config.get('establishment_type', 'NO CAPTURADO')}")
        
        techniques = config.get('available_techniques', set())
        stations = config.get('available_stations', set())
        print(f"🔧 Técnicas seleccionadas: {len(techniques)} técnicas")
        print(f"🏭 Estaciones seleccionadas: {len(stations)} estaciones")
        
        print("\n🎯 VERIFICACIÓN DE VALORES ESPERADOS:")
        expected_values = {
            'num_dishes': 20,
            'max_cost_per_dish': 200.0,
            'num_chefs': 12,
            'min_profit_margin': 30.0
        }
        
        all_correct = True
        for key, expected in expected_values.items():
            actual = config.get(key)
            status = "✅" if actual == expected else "❌"
            print(f"{status} {key}: Esperado={expected}, Actual={actual}")
            if actual != expected:
                all_correct = False
        
        if all_correct:
            print("\n🎉 ¡TODOS LOS VALORES FUERON CAPTURADOS CORRECTAMENTE!")
            messagebox.showinfo("Prueba Exitosa", 
                               "✅ Todos los valores se capturaron correctamente.\n\n"
                               "Los datos ingresados en la UI coinciden con los valores esperados.")
        else:
            print("\n⚠️ ALGUNOS VALORES NO COINCIDEN CON LO ESPERADO")
            messagebox.showwarning("Prueba Parcial", 
                                  "⚠️ Algunos valores no coinciden.\n\n"
                                  "Revise la consola para ver los detalles.")
        
        print("="*60)
    
    try:
        # Cargar datos de prueba
        print("🔄 Cargando base de conocimiento...")
        catalog, techniques = load_knowledge_base()
        
        if not catalog:
            print("❌ Error: No se pudo cargar el catálogo")
            return
        
        print(f"✅ Catálogo cargado: {len(catalog)} platos, {len(techniques)} técnicas")
        
        # Crear ventana de prueba
        root = tk.Tk()
        root.title("🧪 PRUEBA DE CAPTURA DE VALORES - MenuOptimizer")
        root.geometry("1200x800")
        
        # Agregar instrucciones
        instructions_frame = ttk.Frame(root, padding="10")
        instructions_frame.pack(fill="x")
        
        instructions = """🧪 PRUEBA DE VALIDACIÓN DE CAPTURA DE VALORES

📋 INSTRUCCIONES:
1. Ingrese los siguientes valores en el formulario:
   • Número de opciones: 20
   • Presupuesto máximo: 200
   • Personal disponible: 12  
   • Margen de ganancia: 30

2. Seleccione algunas técnicas y estaciones de trabajo

3. Haga clic en "OPTIMIZAR MENÚ" para verificar la captura

🎯 El sistema verificará si los valores ingresados coinciden con los esperados."""
        
        ttk.Label(instructions_frame, text=instructions, 
                 font=("Segoe UI", 9), justify="left").pack(anchor="w")
        
        # Separador
        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=10)
        
        # Crear panel de configuración
        config_panel = ConfigurationPanel(
            root,
            catalog=catalog,
            all_techniques=techniques,
            on_optimize_callback=on_optimize_test
        )
        config_panel.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Establecer estaciones
        all_stations = set()
        for dish in catalog:
            if hasattr(dish, 'steps') and dish.steps:
                for step in dish.steps:
                    if hasattr(step, 'station') and step.station:
                        all_stations.add(step.station)
        
        config_panel.set_available_stations(sorted(list(all_stations)))
        
        # Configurar valores por defecto para la prueba
        def set_test_values():
            """Establece valores de prueba para facilitar la verificación."""
            try:
                config_panel.vars["num_dishes"].set("20")
                config_panel.vars["max_cost_per_dish"].set("200")
                config_panel.vars["num_chefs"].set("12")
                config_panel.config_vars["min_profit_margin"].set("30")
                print("✅ Valores de prueba establecidos")
            except Exception as e:
                print(f"⚠️ Error estableciendo valores de prueba: {e}")
        
        # Botón para establecer valores de prueba
        test_button_frame = ttk.Frame(root)
        test_button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(test_button_frame, 
                  text="🎯 Establecer Valores de Prueba Automáticamente",
                  command=set_test_values).pack(pady=5)
        
        # Esperar un poco antes de establecer valores
        root.after(1000, set_test_values)
        
        print("🎮 Interfaz de prueba iniciada. Siga las instrucciones en pantalla.")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 INICIANDO PRUEBA DE CAPTURA DE VALORES")
    print("="*60)
    test_configuration_panel()