# app/main.py - VERSIÓN CORREGIDA PARA WINDOWS
import tkinter as tk
from tkinter import messagebox, ttk
import logging
import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.database_manager import load_knowledge_base
from app.ui.main_window import MenuOptimizerMainWindow


def setup_logging():
    """Configura el sistema de logging CON SOPORTE COMPLETO PARA UNICODE."""
    # CONFIGURACIÓN CORREGIDA PARA WINDOWS - Soporte completo UTF-8
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            # ✅ CORRECCIÓN CRÍTICA: Agregar encoding='utf-8' para soporte de emojis
            logging.FileHandler("app.log", mode='w', encoding='utf-8'),
            
            # ✅ CORRECCIÓN CRÍTICA: Configurar StreamHandler para Windows
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar nivel específico para librerías verbose
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # ✅ NUEVO: Configurar encoding para stdout en Windows
    if sys.platform.startswith('win'):
        try:
            # Intentar configurar la consola de Windows para UTF-8
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        except Exception:
            # Si falla, usar logging sin emojis para evitar crashes
            logging.info("Configurando logging sin emojis para compatibilidad con Windows")


def setup_tkinter_styles():
    """Configura estilos personalizados para la aplicación."""
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana temporal
    
    # Configurar tema y estilos
    style = ttk.Style()
    
    # Usar tema moderno si está disponible
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')
    
    # Configurar colores personalizados
    style.configure('Accent.TButton', 
                   font=('Segoe UI', 10, 'bold'),
                   foreground='white',
                   background='#0078d4')
    
    style.map('Accent.TButton',
              background=[('active', '#106ebe'),
                         ('pressed', '#005a9e')])
    
    # Configurar estilo de notebook
    style.configure('TNotebook.Tab', 
                   font=('Segoe UI', 9))
    
    # Configurar labelframes
    style.configure('TLabelframe.Label', 
                   font=('Segoe UI', 9, 'bold'))
    
    root.destroy()


def check_dependencies():
    """Verifica que todas las dependencias estén disponibles."""
    missing_deps = []
    
    try:
        import mysql.connector
    except ImportError:
        missing_deps.append("mysql-connector-python")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    if missing_deps:
        deps_str = ", ".join(missing_deps)
        error_message = (f"Faltan dependencias requeridas: {deps_str}\n\n"
                        f"Por favor instálelas usando:\n"
                        f"pip install {' '.join(missing_deps)}")
        messagebox.showerror("Dependencias Faltantes", error_message)
        return False
    
    return True


def check_database_connection():
    """Verifica la conexión a la base de datos."""
    try:
        # Intentar cargar una pequeña muestra de datos
        from app.data.database_manager import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dishes LIMIT 1")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        logging.info(f"Conexión a base de datos exitosa. {count} platos disponibles.")
        return True
        
    except Exception as e:
        logging.error(f"Error de conexión a base de datos: {e}")
        error_message = (f"No se pudo conectar a la base de datos MySQL.\n\n"
                        f"Verifique que:\n"
                        f"• El servidor MySQL esté ejecutándose\n"
                        f"• Las credenciales en 'config/db_config.ini' sean correctas\n"
                        f"• La base de datos 'menu_optimizer_db' exista\n\n"
                        f"Error específico: {str(e)}")
        messagebox.showerror("Error de Base de Datos", error_message)
        return False


def show_startup_splash():
    """Muestra pantalla de inicio con información del sistema."""
    splash = tk.Toplevel()
    splash.title("MenuOptimizer v10.0")
    splash.geometry("500x300")
    splash.resizable(False, False)
    
    # Centrar splash
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (500 // 2)
    y = (splash.winfo_screenheight() // 2) - (300 // 2)
    splash.geometry(f"500x300+{x}+{y}")
    
    # Contenido del splash
    main_frame = tk.Frame(splash, bg='#f0f8ff')
    main_frame.pack(fill='both', expand=True)
    
    # Logo y título - SIN EMOJIS para evitar problemas de encoding
    tk.Label(main_frame, text="MENU", font=("Arial", 48), bg='#f0f8ff').pack(pady=(30, 10))
    tk.Label(main_frame, text="MENUOPTIMIZER v10.0", 
             font=("Segoe UI", 20, "bold"), bg='#f0f8ff', fg='#2c3e50').pack()
    tk.Label(main_frame, text="Sistema Inteligente de Optimización de Menús", 
             font=("Segoe UI", 11), bg='#f0f8ff', fg='#7f8c8d').pack(pady=(5, 20))
    
    # Información del sistema
    info_text = """Algoritmos Genéticos Avanzados
Optimización Multi-objetivo (7 variables)
Análisis Operativo Integral
Interfaz Intuitiva y Moderna
Estructura Cúbica de Flujo de Trabajo

Desarrollado por: Pablo César Altuzar Grajales
Matrícula: 223267 - Grupo: 8B"""
    
    tk.Label(main_frame, text=info_text, 
             font=("Segoe UI", 9), bg='#f0f8ff', fg='#34495e', 
             justify='center').pack(pady=(0, 20))
    
    # Barra de progreso
    progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
    progress.pack(pady=(0, 10))
    progress.start(10)
    
    status_label = tk.Label(main_frame, text="Inicializando sistema...", 
                           font=("Segoe UI", 9), bg='#f0f8ff', fg='#7f8c8d')
    status_label.pack()
    
    splash.update()
    return splash, progress, status_label


def main():
    """Función principal de la aplicación."""
    try:
        # 1. Configurar logging CON SOPORTE UNICODE
        setup_logging()
        logging.info("=== INICIANDO MENUOPTIMIZER v10.0 ===")
        
        # 2. Verificar dependencias
        if not check_dependencies():
            return
        
        # 3. Configurar estilos de tkinter
        setup_tkinter_styles()
        
        # 4. Mostrar splash screen
        splash, progress, status_label = show_startup_splash()
        
        # 5. Verificar conexión a base de datos
        status_label.config(text="Verificando conexión a base de datos...")
        splash.update()
        
        if not check_database_connection():
            splash.destroy()
            return
        
        # 6. Cargar base de conocimiento
        status_label.config(text="Cargando base de conocimiento...")
        splash.update()
        
        logging.info("Cargando catálogo de platos y técnicas culinarias...")
        dish_catalog, all_techniques = load_knowledge_base()
        
        if not dish_catalog:
            progress.stop()
            splash.destroy()
            messagebox.showerror("Error Crítico", 
                               "La base de conocimiento de platos está vacía. "
                               "Verifique que la base de datos contenga datos de muestra.")
            logging.critical("Base de conocimiento vacía")
            return
        
        logging.info(f"Base de conocimiento cargada: {len(dish_catalog)} platos, {len(all_techniques)} técnicas")
        
        # 7. Inicializar aplicación principal
        status_label.config(text="Iniciando interfaz principal...")
        splash.update()
        
        # Cerrar splash
        progress.stop()
        splash.destroy()
        
        # 8. Crear y mostrar ventana principal
        try:
            app = MenuOptimizerMainWindow(dish_catalog, all_techniques)
            
            # Configurar comportamiento de cierre
            def on_closing():
                logging.info("Cerrando aplicación...")
                app.destroy()
            
            app.protocol("WM_DELETE_WINDOW", on_closing)
            
            # Mostrar ventana maximizada pero redimensionable
            try:
                app.state('zoomed')  # Windows
            except tk.TclError:
                app.attributes('-zoomed', True)  # Linux
            except:
                app.geometry("1400x900")  # Fallback
            
            logging.info("Aplicación iniciada exitosamente")
            
            # Ejecutar loop principal
            app.mainloop()
            
        except Exception as e:
            logging.error(f"Error al crear ventana principal: {e}", exc_info=True)
            messagebox.showerror("Error de Interfaz", 
                               f"No se pudo inicializar la interfaz gráfica:\n{str(e)}")
    
    except KeyboardInterrupt:
        logging.info("Aplicación interrumpida por usuario")
    
    except Exception as e:
        logging.critical(f"Error crítico en aplicación: {e}", exc_info=True)
        messagebox.showerror("Error Crítico", 
                           f"Error inesperado en la aplicación:\n{str(e)}\n\n"
                           f"Consulte 'app.log' para más detalles.")
    
    finally:
        logging.info("=== FINALIZANDO MENUOPTIMIZER ===")


if __name__ == "__main__":
    main()