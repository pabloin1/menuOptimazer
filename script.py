import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import random
from collections import defaultdict
import json

class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tooltip_window = widget, text, None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert"); x += self.widget.winfo_rootx() + 25; y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget); self.tooltip_window.wm_overrideredirect(True); self.tooltip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip_window, text=self.text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("tahoma", "8", "normal")).pack(ipadx=1)
    def hide_tip(self, event=None):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None

# --------------------------------------------------------------------------
# PARTE 1: BASE DE CONOCIMIENTO Y CLASES
# --------------------------------------------------------------------------
class Ingrediente:
    def __init__(self, **kwargs):
        self.alergenos = []
        self.__dict__.update(kwargs)
    def __repr__(self): return self.nombre

class Persona:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)
    def __repr__(self): return f"{self.nombre} ({self.rol})"

class Puesto:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)
    def __repr__(self): return self.nombre

class Etapa:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)
    def __repr__(self): return f"Etapa({self.id}: '{self.descripcion}')"

class Plato:
    def __init__(self, **kwargs):
        self.tags = []; self.ingredientes_principales = []
        self.__dict__.update(kwargs)
        self.costo_produccion = self._calcular_costo()
        self.info_nutricional = self._calcular_nutricion()

    def _calcular_costo(self):
        return sum((ing.costo_por_kg / 1000) * cant for ing, cant in self.receta.items())

    def _calcular_nutricion(self):
        nutri = {'calorias': 0, 'proteinas': 0, 'carbohidratos': 0}
        for ing, cant in self.receta.items():
            factor = cant / 1000
            nutri['calorias'] += getattr(ing, 'calorias_por_kg', 0) * factor
            nutri['proteinas'] += getattr(ing, 'proteinas_por_kg', 0) * factor
            nutri['carbohidratos'] += getattr(ing, 'carbohidratos_por_kg', 0) * factor
        return nutri

    def esta_en_temporada(self, t): return t == 'Todo el año' or all(ing.temporada in ('Todo el año', t) for ing in self.receta.keys())
    def get_alergenos(self): return sorted(list(set(a for i in self.receta.keys() for a in i.alergenos)))
    def __repr__(self): return self.nombre

class FlujoDeTrabajoPlato:
    def __init__(self, nombre_plato): self.nombre_plato, self.asignaciones = nombre_plato, defaultdict(lambda: defaultdict(dict))
    def asignar_etapa(self, p, pu, pr, e): self.asignaciones[p.nombre][pu.nombre][pr] = e
    def verificar_consistencia(self):
        if not self.asignaciones: return True, "Consistente: Flujo de trabajo vacío."
        pasos = {p for v in self.asignaciones.values() for v2 in v.values() for p in v2.keys()}
        if not pasos: return True, "Consistente: No hay pasos definidos."
        faltantes = set(range(1, max(pasos) + 1)) - pasos
        if faltantes: return False, f"Inconsistente. Faltan pasos: {sorted(list(faltantes))}"
        return True, f"Consistente (Pasos 1 a {max(pasos)})."

def cargar_base_de_conocimiento(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: data = json.load(f)
    except Exception as e: messagebox.showerror("Error Crítico", f"Error al cargar '{filepath}':\n{e}"); return None, None, None, None
    ingredientes = {i['nombre']: Ingrediente(**i) for i in data['ingredientes']}
    personal = {p['nombre']: Persona(**p) for p in data['personal']}
    puestos = {p['nombre']: Puesto(**p) for p in data['puestos']}
    etapas = {e['id']: Etapa(**e) for e in data.get('etapas_maestras', [])}
    catalogo = [Plato(**{**pd, 'receta': {ingredientes[r['ingrediente_nombre']]: r['cantidad_gr'] for r in pd['receta'] if r['ingrediente_nombre'] in ingredientes}}) for pd in data['platos']]
    for p, pd in zip(catalogo, data['platos']):
        p.flujo_trabajo = FlujoDeTrabajoPlato(p.nombre)
        for fi in pd.get('flujo_trabajo', []):
            try: p.flujo_trabajo.asignar_etapa(personal[fi['persona_nombre']], puestos[fi['puesto_nombre']], fi['precedencia'], etapas[fi['etapa_id']])
            except KeyError as e: print(f"Advertencia de datos: Clave no encontrada para el flujo de '{pd['nombre']}': {e}")
    return catalogo, {p.nombre: p for p in catalogo}, list(personal.values()), list(puestos.values())

# --------------------------------------------------------------------------
# PARTE 2: ALGORITMO GENÉTICO
# --------------------------------------------------------------------------
def crear_individuo(c, n): return random.sample(c, n) if len(c) >= n else []
def calcular_aptitud(menu, pesos, precio_sugerido_factor):
    if not menu: return 0
    np = len(menu); gt = sum((p.costo_produccion * precio_sugerido_factor) - p.costo_produccion for p in menu); tp = sum(p.tiempo_prep for p in menu) / np; pp = sum(p.popularidad for p in menu) / np
    an = {'calorias': sum(p.info_nutricional['calorias'] for p in menu) / np, 'proteinas': sum(p.info_nutricional['proteinas'] for p in menu) / np, 'carbohidratos': sum(p.info_nutricional['carbohidratos'] for p in menu) / np}
    on = {'calorias': 600, 'proteinas': 30, 'carbohidratos': 50}; ci = defaultdict(int); [ci.update({i.nombre: ci[i.nombre] + 1}) for p in menu for i in p.receta]
    sc = {'ganancia': min(gt / (100 * np), 1.0), 'tiempo': max(0, 1 - (tp / 30)), 'popularidad': pp / 10.0, 'variedad': (len({p.estacion_cocina for p in menu}) / 6 + len({p.tipo_dieta for p in menu}) / 4) / 2, 'nutricion': max(0, 1 - (sum(abs(an[k] - on[k]) / on[k] for k in on) / len(on))), 'desperdicio': (sum(1 for c in ci.values() if c > 1)) / np}
    return sum(sc.get(key, 0) * pesos.get(key, 0) for key in pesos)
def seleccionar_padres(p, a, k=3): return sorted(random.sample(list(zip(p, a)), k), key=lambda x: x[1], reverse=True)[0][0]
def cruzar(p1, p2, c):
    if not p1 or not p2: return []
    h = p1[:random.randint(1, len(p1) - 1)]; [h.append(pl) for pl in p2 if pl not in h and len(h) < len(p1)]
    while len(h) < len(p1):
        pl = random.choice(c)
        if pl not in h: h.append(pl)
    return h
def mutar(m, c, p=0.15):
    if not m or random.random() >= p or len(c) <= len(m): return m
    i, np = random.randint(0, len(m) - 1), random.choice(c)
    while np in m: np = random.choice(c)
    m[i] = np; return m

# --------------------------------------------------------------------------
# PARTE 3: INTERFAZ GRÁFICA
# --------------------------------------------------------------------------
class MenuOptimizerApp(tk.Tk):
    def __init__(self, cat, p_nom, per, pue):
        super().__init__()
        if not cat: self.destroy(); return
        self.cat, self.p_nom, self.per, self.pue = cat, p_nom, per, pue
        self.title("MENUOPTIMIZER v8.1 - Final Corregido"); self.geometry("1200x900")
        self.desc_font = font.Font(family="Segoe UI", size=8, slant="italic")
        self.notebook = ttk.Notebook(self); self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.crear_pestana_parametros(); self.crear_pestana_resultados()

    def crear_pestana_parametros(self):
        param_frame = ttk.Frame(self.notebook, padding="15"); self.notebook.add(param_frame, text='⚙️ 1. Configuración y Objetivos')
        col1 = ttk.Frame(param_frame); col1.pack(side="left", fill="y", padx=(0, 10)); col2 = ttk.Frame(param_frame); col2.pack(side="left", fill="both", expand=True)
        
        restric_frame = ttk.LabelFrame(col1, text="Restricciones", padding=10); restric_frame.pack(fill="x", pady=5)
        self.vars = {"platos": tk.StringVar(value="5"), "moneda": tk.StringVar(value="MXN$"), "costo_max": tk.StringVar(value="90.0"), "margen_min": tk.StringVar(value="150"), "temporada": tk.StringVar(value="Todo el año"), "tipo_est": tk.StringVar(value="Casual")}
        entries = {"Platos en Menú:": ("platos", "Define cuántos platillos distintos tendrá el menú."), "Símbolo Moneda:": ("moneda", "Símbolo monetario para los reportes."), "Costo Máx. Plato:": ("costo_max", "Filtra platos cuyo costo de producción es mayor."), "Margen Mín. (%):": ("margen_min", "Filtra platos que no alcancen esta rentabilidad.")}
        for i, (label, (key, tip)) in enumerate(entries.items()):
            ttk.Label(restric_frame, text=label).grid(row=i, column=0, padx=5, pady=8, sticky="w"); entry = ttk.Entry(restric_frame, textvariable=self.vars[key], width=12); entry.grid(row=i, column=1, padx=5, pady=8, sticky="w"); Tooltip(entry, tip)
        
        ttk.Label(restric_frame, text="Temporada:").grid(row=4, column=0, padx=5, pady=8, sticky="w"); ct = ttk.Combobox(restric_frame, textvariable=self.vars["temporada"], values=['Todo el año', 'Primavera', 'Verano', 'Otoño', 'Invierno'], state="readonly", width=10); ct.grid(row=4, column=1); Tooltip(ct, "Filtra platos por temporada.")
        
        def on_tipo_change(e=None): self.actualizar_pesos_por_preset()
        ttk.Label(restric_frame, text="Tipo Establecimiento:").grid(row=5, column=0, padx=5, pady=8, sticky="w"); ce = ttk.Combobox(restric_frame, textvariable=self.vars["tipo_est"], values=['Personalizado', 'Casual', 'Elegante', 'Comida Rápida'], state="readonly", width=10); ce.grid(row=5, column=1); ce.bind("<<ComboboxSelected>>", on_tipo_change); Tooltip(ce, "Ajusta las prioridades a un preset.")
        
        diet_frame = ttk.LabelFrame(col1, text="Filtros Dietéticos y Alérgenos", padding=10); diet_frame.pack(fill="x", pady=10)
        self.alergenos_vars = {a: tk.BooleanVar(value=False) for a in ['gluten', 'lacteos', 'pescado', 'crustaceos']}
        ttk.Label(diet_frame, text="Excluir platos que contengan:").pack(anchor="w"); [ttk.Checkbutton(diet_frame, text=a.capitalize(), variable=v).pack(anchor="w", padx=10) for a, v in self.alergenos_vars.items()]

        cap_frame = ttk.LabelFrame(col1, text="Capacidad y Equipo Disponible", padding=10); cap_frame.pack(fill="x", pady=10)
        self.personal_vars = {p.nombre: tk.BooleanVar(value=True) for p in self.per}; self.puestos_vars = {pu.nombre: tk.BooleanVar(value=True) for pu in self.pue}
        ttk.Label(cap_frame, text="Personal Activo:").pack(anchor="w"); [ttk.Checkbutton(cap_frame, text=p.nombre, variable=self.personal_vars[p.nombre]).pack(anchor="w", padx=10) for p in self.per]
        ttk.Label(cap_frame, text="Estaciones Activas:").pack(anchor="w", pady=(10, 0)); [ttk.Checkbutton(cap_frame, text=pu.nombre, variable=self.puestos_vars[pu.nombre]).pack(anchor="w", padx=10) for pu in self.pue]
        
        self.weights_frame = ttk.LabelFrame(col2, text="Prioridades (Objetivos)", padding=10); self.weights_frame.pack(fill="both", expand=True, pady=5)
        self.weights_frame.columnconfigure(1, weight=1); self.pesos = {}; self.sliders = {}
        obj = {"ganancia": "Maximizar Ganancia", "tiempo": "Minimizar Tiempo Prep.", "nutricion": "Balance Nutricional", "variedad": "Variedad Gastronómica", "popularidad": "Satisfacción Cliente", "desperdicio": "Eficiencia de Inventario"}
        tips = {"ganancia": "Prioriza menús con mayor margen.", "tiempo": "Prioriza menús rápidos de preparar.", "nutricion": "Busca menús balanceados.", "variedad": "Recompensa variedad de dietas y estaciones.", "popularidad": "Da preferencia a platos populares.", "desperdicio": "Recompensa menús que reutilizan ingredientes."}
        for i, (k, l) in enumerate(obj.items()):
            lb = ttk.Label(self.weights_frame, text=l); lb.grid(row=i, column=0, sticky="w", padx=5, pady=8); Tooltip(lb, tips[k]); self.pesos[k] = tk.DoubleVar(value=0.5); sl = ttk.Scale(self.weights_frame, from_=0.0, to=1.0, variable=self.pesos[k]); sl.grid(row=i, column=1, sticky="ew", padx=5); Tooltip(sl, f"Mover para dar MÁS importancia a '{l}'."); self.sliders[k] = sl
        
        ttk.Button(col2, text="🚀 Optimizar Menú", command=self.ejecutar_optimizacion, style="Accent.TButton").pack(pady=20, ipady=10, fill="x"); ttk.Style().configure("Accent.TButton", font=("Segoe UI", 12, "bold"))
        self.actualizar_pesos_por_preset()

    def actualizar_pesos_por_preset(self):
        t = self.vars["tipo_est"].get(); presets = {'Casual': {'ganancia': 0.6, 'tiempo': 0.6, 'nutricion': 0.4, 'variedad': 0.7, 'popularidad': 0.8, 'desperdicio': 0.5}, 'Elegante': {'ganancia': 0.9, 'tiempo': 0.2, 'nutricion': 0.6, 'variedad': 0.5, 'popularidad': 0.9, 'desperdicio': 0.3}, 'Comida Rápida': {'ganancia': 0.5, 'tiempo': 1.0, 'nutricion': 0.2, 'variedad': 0.3, 'popularidad': 0.7, 'desperdicio': 0.8}}
        state = "disabled" if t in presets else "normal"
        if t in presets:
            p = presets[t]
            for k, sl in self.sliders.items(): sl.set(p.get(k, 0.5))
        for sl in self.sliders.values(): sl.config(state=state)

    def crear_pestana_resultados(self): self.results_notebook = ttk.Notebook(self.notebook); self.notebook.add(self.results_notebook, text='🏆 2. Resultados de Optimización')

    def ejecutar_optimizacion(self):
        try:
            params = {k: v.get() for k, v in self.vars.items()}
            # --- CORRECCIÓN AQUÍ ---
            p_disp = [p for p, v in self.personal_vars.items() if v.get()]
            e_disp = [pu for pu, v in self.puestos_vars.items() if v.get()]
            # --- FIN DE LA CORRECCIÓN ---
            pesos = {k: v.get() for k, v in self.pesos.items()}; alergenos_excl = [a for a, v in self.alergenos_vars.items() if v.get()]
            num_platos = int(params["platos"]); costo_max = float(params["costo_max"]); margen_min = float(params["margen_min"])
        except ValueError: messagebox.showerror("Error", "Valores numéricos inválidos."); return
        
        [self.results_notebook.forget(i) for i in reversed(range(self.results_notebook.index('end')))]; self.notebook.select(1); self.update_idletasks()
        
        precio_factor = 1 + (margen_min / 100)
        cat_f = [p for p in self.cat if p.costo_produccion <= costo_max and (p.costo_produccion * precio_factor) > p.costo_produccion and p.esta_en_temporada(params["temporada"]) and p.estacion_cocina in e_disp and not any(a in p.get_alergenos() for a in alergenos_excl) and (params["tipo_est"] == 'Personalizado' or any(t in p.tags for t in params["tipo_est"].lower().replace(" ", "_").split()))]
        if len(cat_f) < num_platos: messagebox.showwarning("Insuficiente", f"No hay suficientes platos ({len(cat_f)}) que cumplan TODAS las restricciones."); return
        
        pob = [crear_individuo(cat_f, num_platos) for _ in range(150)]
        for _ in range(200):
            apt = [calcular_aptitud(m, pesos, precio_factor) for m in pob]
            pob = [mutar(cruzar(seleccionar_padres(pob, apt), seleccionar_padres(pob, apt), cat_f), cat_f) for _ in range(150)]
        
        final_apt = [calcular_aptitud(m, pesos, precio_factor) for m in pob]; pob_con_apt = sorted(zip(pob, final_apt), key=lambda x: x[1], reverse=True)
        mejores, vistos = [], set()
        for m, a in pob_con_apt:
            if m and tuple(sorted([p.nombre for p in m])) not in vistos: mejores.append((m, a)); vistos.add(tuple(sorted([p.nombre for p in m])))
            if len(mejores) == 3: break
        
        if not mejores: messagebox.showinfo("Sin Resultados", "No se pudo generar ningún menú. Intente de nuevo."); return
        for i, (m, a) in enumerate(mejores):
            mf = ttk.Frame(self.results_notebook, padding="10"); self.results_notebook.add(mf, text=f"Opción #{i+1} (Aptitud:{a:.3f})")
            mn = ttk.Notebook(mf); mn.pack(fill="both", expand=True)
            self.crear_reporte_menu(mn, m, params["moneda"], precio_factor)
            self.crear_reporte_eficiencia(mn, m, len(p_disp))
            self.crear_reporte_inventario(mn, m, params["moneda"])
    
    def crear_reporte_menu(self, parent, menu, moneda, precio_factor):
        f = ttk.Frame(parent, padding=10); parent.add(f, text='📋 Tabla de Menú')
        txt = scrolledtext.ScrolledText(f, wrap=tk.WORD, font=("Courier New", 9)); txt.pack(fill="both", expand=True)
        txt.insert(tk.INSERT, f"{'Plato':<35}|{'Ingredientes Principales':<30}|{'Alérgenos':<20}|{'Costo':<12}|{'Precio Sug.':<14}|{'Margen':<12}\n", ("bold",)); txt.insert(tk.INSERT, "-" * 130 + "\n")
        for p in menu:
            precio_sug = p.costo_produccion * precio_factor; margen = precio_sug - p.costo_produccion; alergenos = p.get_alergenos()
            txt.insert(tk.INSERT, f"{p.nombre:<35}|{', '.join(p.ingredientes_principales):<30}|{', '.join(alergenos) if alergenos else 'Ninguno':<20}|{moneda}{p.costo_produccion:<11.2f}|{moneda}{precio_sug:<13.2f}|{moneda}{margen:<11.2f}\n")
        txt.config(state="disabled"); txt.tag_config("bold", font=("Courier New", 9, "bold"))
    
    def crear_reporte_eficiencia(self, parent, menu, personal_disp):
        f = ttk.Frame(parent, padding=10); parent.add(f, text='📊 Eficiencia Operativa')
        txt = scrolledtext.ScrolledText(f, wrap=tk.WORD, font=("Segoe UI", 10)); txt.pack(fill="both", expand=True)
        tp = sum(p.tiempo_prep for p in menu) / len(menu); complejidad_total = sum(p.complejidad for p in menu)
        cap_hora = (personal_disp * 60) / (tp * (1 + complejidad_total * 0.01)) if tp > 0 else 0
        carga_est = {k: 0 for k, v in self.puestos_vars.items() if v.get()}; [carga_est.update({p.estacion_cocina: carga_est.get(p.estacion_cocina, 0) + 1}) for p in menu]
        txt.insert(tk.INSERT, "Proyección de Capacidad y Carga\n\n", ("h1",))
        txt.insert(tk.INSERT, f"▪ Tiempo Promedio Preparación: {tp:.1f} min\n▪ Complejidad Total del Menú: {complejidad_total} puntos\n▪ Personal Disponible: {personal_disp} cocineros\n")
        txt.insert(tk.INSERT, f"▪ Capacidad de Atención Estimada: {cap_hora:.1f} pedidos/hora\n\n", ("highlight",))
        txt.insert(tk.INSERT, "Distribución de Carga por Estación:\n", ("h2",))
        for e, c in sorted(carga_est.items()): txt.insert(tk.INSERT, f"  - {e:<25}: {c} plato(s)\n")
        txt.config(state="disabled"); txt.tag_config("h1", font=("Segoe UI", 14, "bold")); txt.tag_config("h2", font=("Segoe UI", 11, "bold", "underline")); txt.tag_config("highlight", font=("Segoe UI", 10, "bold"), foreground="#00529B", background="#BDE5F8")

    def crear_reporte_inventario(self, parent, menu, moneda):
        f = ttk.Frame(parent, padding=10); parent.add(f, text='🛒 Análisis de Inventario')
        txt = scrolledtext.ScrolledText(f, wrap=tk.WORD, font=("Segoe UI", 10)); txt.pack(fill="both", expand=True)
        inv = defaultdict(lambda: {'q': 0, 'c': 0}); cp = defaultdict(int)
        for p in menu:
            for i, c in p.receta.items(): inv[i.nombre]['q'] += c; inv[i.nombre]['c'] += (i.costo_por_kg / 1000) * c; cp[i.nombre] += 1
        txt.insert(tk.INSERT, "Lista de Ingredientes y Costos\n", ("h1",)); txt.insert(tk.INSERT, f"\n{'Ingrediente':<25}|{'Cantidad Necesaria':<20}|{'Costo Total':<15}\n", ("bold",)); txt.insert(tk.INSERT, "-" * 70 + "\n")
        ct = sum(d['c'] for d in inv.values()); [txt.insert(tk.INSERT, f"{n:<25}|{d['q']:.0f} gr{'':<15}|{moneda}{d['c']:<14.2f}\n") for n, d in sorted(inv.items())]
        txt.insert(tk.INSERT, "-" * 70 + "\n"); txt.insert(tk.INSERT, f"{'COSTO TOTAL INVENTARIO:':<48}{moneda}{ct:<15.2f}\n\n", ("bold",))
        re, porc = (sum(1 for v in cp.values() if v > 1), (sum(1 for v in cp.values() if v > 1) / len(cp)) * 100 if cp else 0)
        txt.insert(tk.INSERT, "Recomendaciones para Minimizar Desperdicio\n", ("h2",))
        txt.insert(tk.INSERT, f"  ▪ Este menú usa {len(cp)} ingredientes únicos.\n▪ {re} se usan en más de un plato ({porc:.1f}% de reutilización).\n")
        rec = "¡Excelente! Alta rotación de inventario." if porc > 50 else "Bueno. Considere reemplazar platos con ingredientes únicos." if porc > 25 else "Atención. Baja rotación podría aumentar desperdicio."
        txt.insert(tk.INSERT, f"  ▪ Recomendación: {rec}\n", ("highlight",))
        txt.config(state="disabled"); txt.tag_config("h1", font=("Segoe UI", 14, "bold")); txt.tag_config("h2", font=("Segoe UI", 11, "bold", "underline")); txt.tag_config("bold", font=("Segoe UI", 10, "bold")); txt.tag_config("highlight", background="#FFFFCC")

if __name__ == "__main__":
    cat, p_nom, per, pue = cargar_base_de_conocimiento("database.json")
    if cat:
        app = MenuOptimizerApp(cat, p_nom, per, pue)
        app.mainloop()