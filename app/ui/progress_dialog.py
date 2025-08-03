# app/ui/progress_dialog.py - VERSIÓN CORREGIDA
import tkinter as tk
from tkinter import ttk
import threading
import time


class ProgressDialog:
    """
    Diálogo de progreso para mostrar el avance de la optimización.
    """
    
    def __init__(self, parent, title: str = "Procesando..."):
        self.parent = parent
        self.title = title
        self.dialog = None
        self.is_visible = False
        self.is_closed = False  # Nueva bandera para evitar reaperturas
        self.update_job = None  # Para cancelar actualizaciones programadas
        
    def show(self):
        """Muestra el diálogo de progreso."""
        if self.is_visible or self.is_closed:
            return
        
        self.is_closed = False  # Reset de la bandera
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        
        # Centrar en la ventana padre
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # IMPORTANTE: Configurar protocolo de cierre
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        
        # Centrar diálogo
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"400x200+{x}+{y}")
        
        # Contenido del diálogo
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Icono y título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(title_frame, text="🧬", font=("Segoe UI", 24)).pack()
        ttk.Label(title_frame, text=self.title, 
                 font=("Segoe UI", 12, "bold")).pack(pady=(10, 0))
        
        # Barra de progreso indeterminada
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            mode='indeterminate',
            length=300
        )
        self.progress_bar.pack(pady=(0, 20))
        
        # Etiqueta de estado
        self.status_label = ttk.Label(
            main_frame,
            text="Inicializando algoritmo genético...",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        self.status_label.pack()
        
        # Frame para información adicional
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(20, 0))
        
        info_text = """El algoritmo genético está optimizando simultáneamente:
• Margen de ganancia • Tiempo de preparación
• Balance nutricional • Variedad gastronómica  
• Eficiencia de ingredientes • Distribución de carga
• Satisfacción del cliente

Esto puede tomar unos momentos..."""
        
        ttk.Label(info_frame, text=info_text, 
                 font=("Segoe UI", 8), 
                 justify="center",
                 foreground="dark gray").pack()
        
        # Iniciar animación
        self.progress_bar.start(10)
        self.is_visible = True
        
        # Iniciar actualización de mensajes
        self._start_status_updates()
    
    def _start_status_updates(self):
        """Inicia la actualización automática de mensajes de estado."""
        self.status_messages = [
            "Inicializando algoritmo genético...",
            "Creando población inicial...",
            "Evaluando fitness de individuos...",
            "Ejecutando selección y cruzamiento...",
            "Aplicando operadores de mutación...",
            "Evolucionando hacia soluciones óptimas...",
            "Analizando convergencia...",
            "Refinando mejores soluciones...",
            "Finalizando optimización..."
        ]
        
        self.current_message_index = 0
        self._update_status_message()
    
    def _update_status_message(self):
        """Actualiza el mensaje de estado cíclicamente."""
        # CORRECCIÓN CRÍTICA: Verificar si el diálogo fue cerrado
        if self.is_closed or not self.is_visible:
            return
            
        if self.dialog and self._dialog_exists():
            try:
                message = self.status_messages[self.current_message_index]
                self.status_label.config(text=message)
                
                self.current_message_index = (self.current_message_index + 1) % len(self.status_messages)
                
                # Programar siguiente actualización SOLO si no está cerrado
                if not self.is_closed and self.is_visible:
                    self.update_job = self.dialog.after(2000, self._update_status_message)
                    
            except tk.TclError:
                # El diálogo fue cerrado inesperadamente
                self._cleanup()
    
    def _dialog_exists(self):
        """Verifica si el diálogo todavía existe."""
        try:
            return self.dialog and self.dialog.winfo_exists()
        except tk.TclError:
            return False
    
    def update_status(self, message: str):
        """Actualiza manualmente el mensaje de estado."""
        if not self.is_closed and self.is_visible and self._dialog_exists():
            try:
                self.status_label.config(text=message)
                self.dialog.update_idletasks()
            except tk.TclError:
                self._cleanup()
    
    def close(self):
        """Cierra el diálogo de progreso."""
        print("DEBUG: Cerrando diálogo de progreso...")
        self._cleanup()
    
    def _cleanup(self):
        """Limpia todos los recursos del diálogo."""
        self.is_closed = True
        self.is_visible = False
        
        # Cancelar cualquier actualización programada
        if self.update_job and self.dialog:
            try:
                self.dialog.after_cancel(self.update_job)
                self.update_job = None
            except tk.TclError:
                pass
        
        # Detener barra de progreso
        if hasattr(self, 'progress_bar') and self.progress_bar:
            try:
                self.progress_bar.stop()
            except tk.TclError:
                pass
        
        # Destruir diálogo
        if self.dialog and self._dialog_exists():
            try:
                self.dialog.destroy()
            except tk.TclError:
                pass
        
        self.dialog = None
        print("DEBUG: Diálogo de progreso cerrado correctamente")