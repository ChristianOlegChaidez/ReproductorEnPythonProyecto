from pygame import mixer
import customtkinter as ctk
import sqlite3
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
import tkinter as tk
import time

# ── INIT ─────────────────────────────
mixer.init()
mixer.music.set_volume(0.7)

conn = sqlite3.connect("musica.db")
cursor = conn.cursor()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── STATE ─────────────────────────────
canciones = []
canciones_filtradas = []
pausado = False
duracion_total = 0
tiempo_inicio = 0
tiempo_pausa = 0
indice_actual = None

# ── WINDOW ───────────────────────────
root = ctk.CTk()
root.title("Reproductor PRO")
root.geometry("850x820")

# ═════════════════════════════════════
# DB
# ═════════════════════════════════════

def cargar_canciones():
    cursor.execute("SELECT titulo, artista, duracion, ruta, etiqueta, genero, foto FROM canciones")
    return cursor.fetchall()

def obtener_etiquetas():
    """Obtiene todas las etiquetas únicas existentes en la base de datos."""
    cursor.execute("SELECT DISTINCT etiqueta FROM canciones WHERE etiqueta IS NOT NULL AND etiqueta != ''")
    filas = cursor.fetchall()
    return [fila[0] for fila in filas]

def refrescar_lista(data):
    listbox.delete(0, tk.END)
    for c in data:
        listbox.insert(tk.END, f"{c[0]} — {c[1]}")

    # Actualiza el contador de resultados
    lbl_contador.configure(text=f"{len(data)} canción(es)")

# ═════════════════════════════════════
# FILTRADO COMBINADO (búsqueda + etiqueta)
# ═════════════════════════════════════

def aplicar_filtros(event=None):
    """Filtra canciones combinando el texto de búsqueda y la etiqueta seleccionada."""
    global canciones_filtradas

    texto = search_var.get().lower().strip()
    etiqueta_sel = etiqueta_var.get()

    # Parte desde todas las canciones
    resultado = canciones

    # 1) Filtrar por etiqueta (si no es "Todas")
    if etiqueta_sel and etiqueta_sel != "Todas":
        resultado = [c for c in resultado if c[4] == etiqueta_sel]

    # 2) Filtrar por texto de búsqueda dentro del resultado anterior
    if texto:
        resultado = [
            c for c in resultado
            if texto in c[0].lower()       # título
            or texto in c[1].lower()       # artista
            or texto in (c[4] or "").lower()  # etiqueta
            or texto in (c[5] or "").lower()  # género
        ]

    canciones_filtradas = resultado
    refrescar_lista(canciones_filtradas)

def limpiar_filtros():
    """Resetea búsqueda y etiqueta a valores vacíos."""
    search_var.set("")
    etiqueta_var.set("Todas")
    aplicar_filtros()

# ═════════════════════════════════════
# AGREGAR (refresca etiquetas al añadir)
# ═════════════════════════════════════

def agregar_cancion():
    ruta = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
    if not ruta:
        return

    titulo    = simpledialog.askstring("Título",   "Nombre:")
    artista   = simpledialog.askstring("Artista",  "Artista:")
    duracion  = simpledialog.askinteger("Duración", "Segundos:")
    etiqueta  = simpledialog.askstring("Etiqueta", "Playlist:")
    genero    = simpledialog.askstring("Género",   "Género:")
    portada   = filedialog.askopenfilename(filetypes=[("Imagen", "*.jpg *.png")])

    cursor.execute("""
        INSERT INTO canciones (titulo, artista, duracion, ruta, etiqueta, genero, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (titulo, artista, duracion, ruta, etiqueta, genero, portada))
    conn.commit()

    canciones.append((titulo, artista, duracion, ruta, etiqueta, genero, portada))

    # Refresca el menú de etiquetas por si se agregó una nueva
    _refrescar_menu_etiquetas()

    aplicar_filtros()

def _refrescar_menu_etiquetas():
    """Actualiza las opciones del menú de etiquetas."""
    etiquetas_actualizadas = ["Todas"] + obtener_etiquetas()
    menu_etiqueta.configure(values=etiquetas_actualizadas)

# ═════════════════════════════════════
# IMAGEN
# ═════════════════════════════════════

def mostrar_imagen(foto):
    try:
        if foto:
            img = Image.open(foto)
            img = img.resize((200, 200))
            img = ImageTk.PhotoImage(img)
            lbl_imagen.configure(image=img, text="")
            lbl_imagen.image = img
        else:
            lbl_imagen.configure(image=None, text="Sin imagen")
            lbl_imagen.image = None
    except Exception:
        lbl_imagen.configure(text="Sin imagen")

# ═════════════════════════════════════
# REPRODUCTOR
# ═════════════════════════════════════

def reproducir():
    global indice_actual, pausado, tiempo_inicio

    if not canciones_filtradas:
        return

    if indice_actual is None:
        sel = listbox.curselection()
        if not sel:
            return
        indice_actual = sel[0]

    titulo, artista, duracion, ruta, etiqueta, genero, foto = canciones_filtradas[indice_actual]

    mixer.music.load(ruta)
    mixer.music.play()

    pausado = False
    tiempo_inicio = time.time()

    barra.configure(to=duracion if duracion else 100)
    lbl_cancion.configure(text=f"{titulo} — {artista}")

    mostrar_imagen(foto)

# ═════════════════════════════════════
# SIGUIENTE / ANTERIOR
# ═════════════════════════════════════

def siguiente():
    global indice_actual
    if not canciones_filtradas:
        return
    indice_actual = (indice_actual + 1) % len(canciones_filtradas)
    reproducir()

def anterior():
    global indice_actual
    if not canciones_filtradas:
        return
    indice_actual = (indice_actual - 1) % len(canciones_filtradas)
    reproducir()

# ═════════════════════════════════════
# PROGRESO
# ═════════════════════════════════════

def actualizar_barra():
    if mixer.music.get_busy() and not pausado:
        seg = int(time.time() - tiempo_inicio)
        barra.set(seg)
        m, s = divmod(seg, 60)
        lbl_actual.configure(text=f"{m}:{s:02d}")
    root.after(500, actualizar_barra)

def saltar(valor):
    global tiempo_inicio
    mixer.music.play(start=float(valor))
    tiempo_inicio = time.time() - float(valor)

def cambiar_volumen(valor):
    mixer.music.set_volume(float(valor) / 100)
    lbl_vol.configure(text=f"{int(float(valor))}%")

# ═════════════════════════════════════
# SELECT
# ═════════════════════════════════════

def seleccionar(event):
    global indice_actual
    sel = listbox.curselection()
    if not sel:
        return
    indice_actual = sel[0]

# ═════════════════════════════════════
# UI
# ═════════════════════════════════════

canciones = cargar_canciones()
canciones_filtradas = canciones[:]

# ── BARRA DE BÚSQUEDA ────────────────
search_var = ctk.StringVar()

frame_busqueda = ctk.CTkFrame(root)
frame_busqueda.pack(fill="x", padx=20, pady=(10, 4))

search_entry = ctk.CTkEntry(
    frame_busqueda,
    textvariable=search_var,
    placeholder_text="🔎  Buscar por título, artista o género…"
)
search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
search_entry.bind("<KeyRelease>", aplicar_filtros)

ctk.CTkButton(frame_busqueda, text="✕ Limpiar", width=80, command=limpiar_filtros).pack(side="left")

# ── SELECTOR DE ETIQUETAS ────────────
frame_etiqueta = ctk.CTkFrame(root)
frame_etiqueta.pack(fill="x", padx=20, pady=(0, 8))

ctk.CTkLabel(frame_etiqueta, text="🏷  Playlist / Etiqueta:").pack(side="left", padx=(4, 8))

etiquetas_disponibles = ["Todas"] + obtener_etiquetas()
etiqueta_var = ctk.StringVar(value="Todas")

menu_etiqueta = ctk.CTkOptionMenu(
    frame_etiqueta,
    variable=etiqueta_var,
    values=etiquetas_disponibles,
    command=lambda _: aplicar_filtros(),   # Se llama al cambiar la selección
    width=200
)
menu_etiqueta.pack(side="left")

# Contador de resultados (derecha)
lbl_contador = ctk.CTkLabel(frame_etiqueta, text=f"{len(canciones)} canción(es)")
lbl_contador.pack(side="right", padx=8)

# ── LISTA ────────────────────────────
listbox = tk.Listbox(root, bg="#2b2b2b", fg="white")
listbox.pack(fill="both", expand=True, padx=20)
listbox.bind("<<ListboxSelect>>", seleccionar)

refrescar_lista(canciones)

# ── BOTÓN AGREGAR ─────────────────────
ctk.CTkButton(root, text="➕ Agregar canción", command=agregar_cancion).pack(pady=5)

# ── INFO CANCIÓN ──────────────────────
lbl_cancion = ctk.CTkLabel(root, text="Ninguna canción")
lbl_cancion.pack()

lbl_imagen = ctk.CTkLabel(root, text="Sin imagen")
lbl_imagen.pack(pady=6)

# ── BARRA DE PROGRESO ─────────────────
frame = ctk.CTkFrame(root)
frame.pack(fill="x", padx=20)

lbl_actual = ctk.CTkLabel(frame, text="0:00")
lbl_actual.pack(side="left")

barra = ctk.CTkSlider(frame, from_=0, to=100, command=saltar)
barra.pack(side="left", fill="x", expand=True)

# ── VOLUMEN ───────────────────────────
frame_vol = ctk.CTkFrame(root)
frame_vol.pack(pady=8)

ctk.CTkLabel(frame_vol, text="🔊").pack(side="left")

barra_vol = ctk.CTkSlider(frame_vol, from_=0, to=100, command=cambiar_volumen)
barra_vol.set(70)
barra_vol.pack(side="left")

lbl_vol = ctk.CTkLabel(frame_vol, text="70%")
lbl_vol.pack(side="left")

# ── CONTROLES ─────────────────────────
frame_btn = ctk.CTkFrame(root)
frame_btn.pack(pady=10)

ctk.CTkButton(frame_btn, text="⏮", command=anterior).pack(side="left", padx=5)
ctk.CTkButton(frame_btn, text="▶", command=reproducir).pack(side="left", padx=5)
ctk.CTkButton(frame_btn, text="⏸", command=lambda: mixer.music.pause()).pack(side="left", padx=5)
ctk.CTkButton(frame_btn, text="⏹", command=lambda: mixer.music.stop()).pack(side="left", padx=5)
ctk.CTkButton(frame_btn, text="⏭", command=siguiente).pack(side="left", padx=5)

actualizar_barra()
root.mainloop()