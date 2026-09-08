import random
import requests
import streamlit as st
from PIL import Image, ImageOps
import io
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Pokémon Quiz Arcade Ultimate ⚡",
    page_icon="🎮",
    layout="centered"
)

# --- ESTILOS CSS PARA UNA INTERFAZ AMPLIADA Y MODERNA ---
st.markdown("""
<style>
    .stApp {
        animation: fadeIn 0.2s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0.9; }
        to { opacity: 1; }
    }
    div.stButton > button {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0px 0px;
        font-weight: 700;
        font-size: 15px;
        padding: 8px 15px;
    }
    .perfil-card {
        background: linear-gradient(135deg, #2b32b2 0%, #1488cc 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        margin-bottom: 25px;
    }
    .card-tcg {
        background: #1e1e2f;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border: 2px solid #ffcc00;
        box-shadow: 0 4px 15px rgba(255, 204, 0, 0.3);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE PERSISTENCIA (JSON LOCAL) ---
ARCHIVO_GUARDADO = "pokedex_save.json"

def cargar_progreso():
    if os.path.exists(ARCHIVO_GUARDADO):
        try:
            with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as f:
                datos = json.load(f)
                pokedex = {int(k): v for k, v in datos.get("pokedex", {}).items()}
                shinydex = {int(k): v for k, v in datos.get("shinydex", {}).items()}
                racha_max = datos.get("racha_maxima", 0)
                logros = datos.get("logros", {})
                aciertos = datos.get("aciertos_totales", 0)
                fallos = datos.get("fallos_totales", 0)
                partidas_perdidas = datos.get("partidas_perdidas", 0)
                shinies_vistos = datos.get("shinies_vistos", 0)
                monedas = datos.get("monedas", 150)
                inventario = datos.get("inventario", {"revividores": 0, "cebos_activos": 0})
                entrenador_actual = datos.get("entrenador_actual", "Rojo")
                entrenadores_desbloqueados = datos.get("entrenadores_desbloqueados", ["Rojo"])
                insignias = datos.get("insignias", [])
                misiones_dia = datos.get("misiones_dia", {})
                ultimo_dia_mision = datos.get("ultimo_dia_mision", "")
                inscripciones_legendarias = datos.get("inscripciones_legendarias", [])
                huevos = datos.get("huevos", []) # Lista de huevos en incubación
                cartas_coleccion = datos.get("cartas_coleccion", []) # Cartas TCG obtenidas
                return pokedex, shinydex, racha_max, logros, aciertos, fallos, partidas_perdidas, shinies_vistos, monedas, inventario, entrenador_actual, entrenadores_desbloqueados, insignias, misiones_dia, ultimo_dia_mision, inscripciones_legendarias, huevos, cartas_coleccion
        except:
            pass
    return {}, {}, 0, {}, 0, 0, 0, 0, 150, {"revividores": 0, "cebos_activos": 0}, "Rojo", ["Rojo"], [], {}, "", [], [], []

def guardar_progreso():
    datos = {
        "pokedex": st.session_state["pokedex_capturados"],
        "shinydex": st.session_state["shinydex_capturados"],
        "racha_maxima": st.session_state["racha_maxima"],
        "logros": st.session_state["logros"],
        "aciertos_totales": st.session_state["aciertos_totales"],
        "fallos_totales": st.session_state["fallos_totales"],
        "partidas_perdidas": st.session_state["partidas_perdidas"],
        "shinies_vistos": st.session_state["shinies_vistos"],
        "monedas": st.session_state["monedas"],
        "inventario": st.session_state["inventario"],
        "entrenador_actual": st.session_state["entrenador_actual"],
        "entrenadores_desbloqueados": st.session_state["entrenadores_desbloqueados"],
        "insignias": st.session_state["insignias"],
        "misiones_dia": st.session_state["misiones_dia"],
        "ultimo_dia_mision": st.session_state["ultimo_dia_mision"],
        "inscripciones_legendarias": st.session_state["inscripciones_legendarias"],
        "huevos": st.session_state["huevos"],
        "cartas_coleccion": st.session_state["cartas_coleccion"]
    }
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except:
        pass

if "pokedex_capturados" not in st.session_state:
    p_ini, s_ini, rm_ini, l_ini, ac_ini, fa_ini, pp_ini, sv_ini, mon_ini, inv_ini, ent_ini, ents_ini, ins_ini, mis_ini, udm_ini, ileg_ini, hue_ini, car_ini = cargar_progreso()
    st.session_state["pokedex_capturados"] = p_ini
    st.session_state["shinydex_capturados"] = s_ini
    st.session_state["racha_maxima"] = rm_ini
    st.session_state["logros"] = l_ini
    st.session_state["aciertos_totales"] = ac_ini
    st.session_state["fallos_totales"] = fa_ini
    st.session_state["partidas_perdidas"] = pp_ini
    st.session_state["shinies_vistos"] = sv_ini
    st.session_state["monedas"] = mon_ini
    st.session_state["inventario"] = inv_ini
    st.session_state["entrenador_actual"] = ent_ini
    st.session_state["entrenadores_desbloqueados"] = ents_ini
    st.session_state["insignias"] = ins_ini
    st.session_state["misiones_dia"] = mis_ini
    st.session_state["ultimo_dia_mision"] = udm_ini
    st.session_state["inscripciones_legendarias"] = ileg_ini
    st.session_state["huevos"] = hue_ini
    st.session_state["cartas_coleccion"] = car_ini

if "racha" not in st.session_state: st.session_state["racha"] = 0
if "puntos" not in st.session_state: st.session_state["puntos"] = 0
if "derrota" not in st.session_state: st.session_state["derrota"] = False
if "ultimo_pokemon_fallado" not in st.session_state: st.session_state["ultimo_pokemon_fallado"] = None
if "en_partida" not in st.session_state: st.session_state["en_partida"] = False
if "modo_seleccionado" not in st.session_state: st.session_state["modo_seleccionado"] = "🏷️ Adivina Nombre"
if "rango_seleccionado" not in st.session_state: st.session_state["rango_seleccionado"] = (1, 1025)
if "generaciones_permitidas" not in st.session_state: st.session_state["generaciones_permitidas"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
if "vistos_partida" not in st.session_state: st.session_state["vistos_partida"] = set()
if "ultima_notificacion" not in st.session_state: st.session_state["ultima_notificacion"] = None
if "id_ronda" not in st.session_state: st.session_state["id_ronda"] = 0
if "ultimo_shiny" not in st.session_state: st.session_state["ultimo_shiny"] = False

if "en_combate_gimnasio" not in st.session_state: st.session_state["en_combate_gimnasio"] = False
if "lider_actual" not in st.session_state: st.session_state["lider_actual"] = None
if "gimnasio_ronda" not in st.session_state: st.session_state["gimnasio_ronda"] = 1
if "gimnasio_preguntas_totales" not in st.session_state: st.session_state["gimnasio_preguntas_totales"] = 3
if "gimnasio_pokemon_actual" not in st.session_state: st.session_state["gimnasio_pokemon_actual"] = None

if "evento_legendario_activo" not in st.session_state: st.session_state["evento_legendario_activo"] = False
if "legendario_actual" not in st.session_state: st.session_state["legendario_actual"] = None
if "siguiente_pokemon_cache" not in st.session_state: st.session_state["siguiente_pokemon_cache"] = None

# --- ENTRENADORES ---
ENTRENADORES = {
    "Rojo": {"nombre": "Rojo", "gen": 1, "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/red.png", "costo": 0, "descripcion": "El campeón silencioso de Kanto.", "trait": "+1 Poké-Coin extra por acierto", "efecto_monedas": 1},
    "Hojas": {"nombre": "Hojas", "gen": 1, "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/leaf.png", "costo": 250, "descripcion": "Entrenadora experta en recolección.", "trait": "+50% de probabilidad base de encontrar Pokémon Shiny", "efecto_shiny": 0.05},
    "Azul": {"nombre": "Azul", "gen": 1, "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/blue.png", "costo": 400, "descripcion": "El rival definitivo y arrogante.", "trait": "Duplica los puntos de experiencia y racha", "efecto_puntos": 2},
    "Cintia": {"nombre": "Cintia", "gen": 4, "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/cynthia.png", "costo": 1000, "descripcion": "La campeona legendaria de Sinnoh.", "trait": "Probabilidad de Shiny x3 y +5 monedas por acierto", "efecto_shiny": 0.15, "efecto_monedas": 5}
}

def agregar_notificacion(texto, tipo="success"):
    st.session_state["ultima_notificacion"] = {"texto": texto, "tipo": tipo}

def obtener_titulo_entrenador():
    pokedex_len = len(st.session_state["pokedex_capturados"])
    racha_max = st.session_state["racha_maxima"]
    if racha_max >= 20 or pokedex_len >= 500: return "👑 Campeón Indiscutible"
    elif pokedex_len >= 100 or racha_max >= 15: return "⚡ Maestro Pokémon"
    elif pokedex_len >= 50 or racha_max >= 10: return "📘 Coleccionista Experto"
    else: return "🌱 Novato de Pueblo Paleta"

LOGROS_DEF = {
    "primer_paso": {"titulo": "🌱 Primeros Pasos", "desc": "Registra tu primer Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 1},
    "suerte_shiny": {"titulo": "✨ ¡Suerte Variocolor!", "desc": "Encuentra y atrapa tu primer Shiny.", "condicion": lambda: len(st.session_state["shinydex_capturados"]) >= 1},
    "huevo_eclosionado": {"titulo": "🥚 Padre Pokémon", "desc": "Eclosiona tu primer Huevo Pokémon.", "condicion": lambda: any(h.get("eclosionado") for h in st.session_state["huevos"])}
}

def comprobar_logros():
    for clave, datos in LOGROS_DEF.items():
        if not st.session_state["logros"].get(clave, False):
            try:
                if datos["condicion"]():
                    st.session_state["logros"][clave] = True
                    st.session_state["monedas"] += 100
                    guardar_progreso()
                    agregar_notificacion(f"🏆 ¡LOGRO: {datos['titulo']}! (+100 Poké-Coins)", "warning")
            except: pass

def verificar_reajustar_misiones():
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    if st.session_state["ultimo_dia_mision"] != hoy_str:
        st.session_state["ultimo_dia_mision"] = hoy_str
        st.session_state["misiones_dia"] = {
            "mision_1": {"desc": "Consigue 5 aciertos hoy", "meta": 5, "actual": 0, "recompensa": 80, "completada": False},
            "mision_2": {"desc": "Registra 3 Pokémon en tu Pokédex", "meta": 3, "actual": 0, "recompensa": 60, "completada": False}
        }
        guardar_progreso()

verificar_reajustar_misiones()

def avanzar_progreso_mision(clave_mision, cantidad=1):
    if clave_mision in st.session_state["misiones_dia"]:
        m = st.session_state["misiones_dia"][clave_mision]
        if not m["completada"]:
            m["actual"] += cantidad
            if m["actual"] >= m["meta"]:
                m["actual"] = m["meta"]
                m["completada"] = True
                st.session_state["monedas"] += m["recompensa"]
                agregar_notificacion(f"📜 ¡Misión completada: {m['desc']}! (+{m['recompensa']} Poké-Coins)", "warning")
            guardar_progreso()

# Función para avanzar pasos en huevos activos
def avanzar_huevos():
    for h in st.session_state["huevos"]:
        if not h.get("eclosionado", False):
            h["pasos_actuales"] += 1
            if h["pasos_actuales"] >= h["pasos_necesarios"]:
                h["eclosionado"] = True
                # Generar Pokémon aleatorio del huevo
                poke_id = random.randint(1, 898)
                h["pokemon_id"] = poke_id
                # Probabilidad de shiny según tipo de huevo
                es_shiny = random.random() < h["prob_shiny"]
                h["es_shiny"] = es_shiny
                
                # Registrar en Pokédex
                res_spec = obtener_datos_especie(poke_id)
                nombre_poke = limpiar_nombre_pokemon(res_spec["name"]) if res_spec else f"Pokémon #{poke_id}"
                h["nombre_poke"] = nombre_poke
                
                st.session_state["pokedex_capturados"][poke_id] = {"nombre": nombre_poke, "gen": 1}
                if es_shiny:
                    st.session_state["shinydex_capturados"][poke_id] = {"nombre": nombre_poke, "gen": 1}
                guardar_progreso()
                agregar_notificacion(f"🐣 ¡Un Huevo ha eclosionado y ha nacido {nombre_poke}{' ✨SHINY✨' if es_shiny else ''}!", "success")

GENERACIONES = {
    1: {"nombre": "Kanto", "rango": (1, 151), "emoji": "🔴"},
    2: {"nombre": "Johto", "rango": (152, 251), "emoji": "🟡"},
    3: {"nombre": "Hoenn", "rango": (252, 386), "emoji": "🔵"},
    4: {"nombre": "Sinnoh", "rango": (387, 493), "emoji": "💎"},
    5: {"nombre": "Teselia", "rango": (494, 649), "emoji": "🏙️"},
    6: {"nombre": "Kalos", "rango": (650, 721), "emoji": "✨"},
    7: {"nombre": "Alola", "rango": (722, 809), "emoji": "🏝️"},
    8: {"nombre": "Galar", "rango": (810, 905), "emoji": "⚔️"},
    9: {"nombre": "Paldea", "rango": (906, 1025), "emoji": "🍇"}
}
IDS_LEGENDARIOS = [144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 377, 378, 379]

def limpiar_nombre_pokemon(nombre_api: str) -> str:
    return nombre_api.replace("-", " ").title()

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_especie(poke_id: int):
    try: return requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/", timeout=2).json()
    except: return None

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_pokemon(poke_id: int):
    try: return requests.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}/", timeout=2).json()
    except: return None

@st.cache_data(ttl=86400, show_spinner=False)
def descargar_imagen_bytes(url: str):
    try: return requests.get(url, timeout=2).content
    except: return None

def obtener_nombre_por_id(poke_id: int):
    res = obtener_datos_especie(poke_id)
    return limpiar_nombre_pokemon(res["name"]) if res else f"Pokémon #{poke_id}"

def obtener_pokemon_by_rango(min_id: int, max_id: int):
    disponibles = [i for i in range(min_id, max_id + 1) if i not in st.session_state["vistos_partida"]]
    if not disponibles:
        st.session_state["vistos_partida"].clear()
        disponibles = list(range(min_id, max_id + 1))
    poke_id = random.choice(disponibles)
    st.session_state["vistos_partida"].add(poke_id)
    
    try:
        res_species = obtener_datos_especie(poke_id)
        res_poke = obtener_datos_pokemon(poke_id)
        if not res_species or not res_poke: return None
            
        nombre = limpiar_nombre_pokemon(res_species["name"])
        gen = int(res_species["generation"]["url"].split("/")[-2])
        tipos = [t["type"]["name"] for t in res_poke["types"]]
        
        ent_info = ENTRENADORES.get(st.session_state["entrenador_actual"], ENTRENADORES["Rojo"])
        prob_shiny = 0.05 + ent_info.get("efecto_shiny", 0.0)
        es_shiny = random.random() < prob_shiny

        img_url = res_poke["sprites"]["front_shiny"] if es_shiny else res_poke["sprites"]["front_default"]
        if not img_url: img_url = res_poke["sprites"]["front_default"]
            
        img_data = descargar_imagen_bytes(img_url)
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA") if img_data else None
        
        ids_erroneos = random.sample([i for i in range(min_id, max_id + 1) if i != poke_id], min(3, max_id - min_id))
        opciones = [obtener_nombre_por_id(i) for i in ids_erroneos] + [nombre]
        random.shuffle(opciones)
        
        return {"id": poke_id, "nombre": nombre, "gen": gen, "tipos": tipos, "shiny": es_shiny, "imagen": pil_img, "opciones": opciones}
    except: return None

# --- ZONA PRINCIPAL: PERFIL DE ENTRENADOR AMPLIADO + MÚSICA RETRO ---
ent_actual = ENTRENADORES.get(st.session_state['entrenador_actual'], ENTRENADORES["Rojo"])

st.markdown(f"""
<div class="perfil-card">
    <table style="width:100%; border:none;">
        <tr>
            <td style="width:80px; vertical-align:middle; border:none;">
                <img src="{ent_actual['avatar_url']}" width="75" style="border-radius:10px; background: rgba(255,255,255,0.1); padding: 5px;">
            </td>
            <td style="vertical-align:middle; border:none; padding-left:15px;">
                <h2 style="margin:0; color:white; font-size: 26px;">{st.session_state['entrenador_actual']}</h2>
                <p style="margin:4px 0 0 0; font-size:16px; color:#ffeb3b; font-weight: bold;">{obtener_titulo_entrenador()}</p>
            </td>
            <td style="text-align:right; vertical-align:middle; border:none;">
                <h3 style="margin:0; color:white; font-size: 24px;">🪙 Poké-Coins</h3>
                <p style="margin:4px 0 0 0; font-size:22px; color:#00e676; font-weight: bold;">{st.session_state['monedas']}</p>
            </td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

# Reproductor de Música Chiptune Retro en Bebida Flotante
with st.expander("🎵 Reproductor de Música Arcade Chiptune (Retro 8-bit)", expanded=False):
    st.audio("https://vgmsite.com/soundtracks/pokemon-red-blue-yellow-gb/101-opening.mp3", format="audio/mp3", loop=True)
    st.caption("Disfruta de la atmósfera clásica mientras juegas y coleccionas cartas.")

# --- MENÚ DE PESTAÑAS (INCLUYENDO GUARDERÍA Y TCG) ---
tab_jugar, tab_guarderia, tab_tcg, tab_entrenadores, tab_mercado, tab_misiones, tab_pokedex, tab_shinydex, tab_stats, tab_ajustes = st.tabs([
    "🎮 Jugar", "🥚 Guardería", "1f0cf Cartas TCG", "👥 Entrenadores", "🛒 Mercado", "📜 Misiones", "📖 Pokédex", "✨ ShinyDex", "📊 Stats", "⚙️ Ajustes"
])

# --- 1. SECCIÓN JUGAR ---
with tab_jugar:
    if st.session_state["derrota"]:
        st.title("💥 ¡Has Caído!")
        st.error("¡Te equivocaste de respuesta!")
        if st.session_state["ultimo_pokemon_fallado"]:
            pf = st.session_state["ultimo_pokemon_fallado"]
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.image(pf["imagen"], width=240)
                st.subheader(f"Era: #{pf['id']:03d} - {pf['nombre']}")
        st.divider()
        if st.button("🔄 Reiniciar Partida", type="primary", use_container_width=True):
            st.session_state["derrota"] = False
            st.session_state["puntos"] = 0
            st.session_state["racha"] = 0
            st.session_state["vistos_partida"].clear()
            st.session_state["pokemon_actual"] = obtener_pokemon_by_rango(1, 1025)
            st.rerun()

    elif not st.session_state["en_partida"]:
        st.title("🎮 Pokémon Quiz Arcade Ultimate")
        st.write(f"✨ *Entrenador activo:* **{st.session_state['entrenador_actual']}** (`{ent_actual['trait']}`) ✨")
        st.divider()
        
        modo_juego = st.radio("🎯 Elige el modo de juego:", ["🏷️ Adivina Nombre", "🌍 Adivina Generación"], key="modo_juego_menu_tab")
        
        if st.button("🚀 ¡Comenzar Partida Ya!", type="primary", use_container_width=True):
            st.session_state["en_partida"] = True
            st.session_state["puntos"] = 0
            st.session_state["racha"] = 0
            st.session_state["vistos_partida"].clear()
            st.session_state["modo_seleccionado"] = modo_juego
            st.session_state["pokemon_actual"] = obtener_pokemon_by_rango(1, 1025)
            st.rerun()

    else:
        st.title("🎯 Partida en Curso")
        if st.session_state["ultima_notificacion"]:
            msg = st.session_state["ultima_notificacion"]
            if msg["tipo"] == "success": st.success(msg["texto"])
            elif msg["tipo"] == "warning": st.warning(msg["texto"])
            else: st.error(msg["texto"])
            st.session_state["ultima_notificacion"] = None
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("⭐ Puntos", st.session_state["puntos"])
        with c2: st.metric("🔥 Racha", st.session_state["racha"])
        with c3: st.metric("🪙 Monedas", st.session_state["monedas"])
        st.divider()
        
        comprobar_logros()
        poke = st.session_state.get("pokemon_actual")
        if not poke:
            poke = obtener_pokemon_by_rango(1, 1025)
            st.session_state["pokemon_actual"] = poke
            
        if poke:
            st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            if poke["shiny"]:
                st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            guardar_progreso()

            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if poke["imagen"]: st.image(poke["imagen"], width=280)
                
            st.subheader("¿Cuál de estos Pokémon es el correcto?")
            for idx, opc_nombre in enumerate(poke["opciones"]):
                if st.button(f"{opc_nombre}", use_container_width=True, key=f"btn_opc_{idx}"):
                    if opc_nombre == poke["nombre"]:
                        st.session_state["puntos"] += 1
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        st.session_state["monedas"] += 6
                        avanzar_progreso_mision("mision_1", 1)
                        avanzar_huevos() # ¡Suma pasos a los huevos activos!
                        
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        
                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto! Era {poke['nombre']} (+6 Poké-Coins, 🥚 +1 Paso a huevos)", "success")
                        st.session_state["pokemon_actual"] = obtener_pokemon_by_rango(1, 1025)
                        st.rerun()
                    else:
                        st.session_state["fallos_totales"] += 1
                        st.session_state["partidas_perdidas"] += 1
                        guardar_progreso()
                        st.session_state["ultimo_pokemon_fallado"] = poke
                        st.session_state["derrota"] = True
                        st.rerun()

        st.divider()
        if st.button("🏠 Volver al Menú", use_container_width=True):
            st.session_state["en_partida"] = False
            st.session_state["derrota"] = False
            st.rerun()

# --- 2. SECCIÓN GUARDERÍA (HUEVOS POKÉMON) ---
with tab_guarderia:
    st.title("🥚 Guardería Pokémon")
    st.write("¡Incuba tus huevos ganando aciertos en las partidas arcade y hazlos eclosionar!")
    st.divider()
    
    if not st.session_state["huevos"]:
        st.info("No tienes ningún huevo en incubación. ¡Compra uno en el **Mercado**!")
    else:
        for idx, h in enumerate(st.session_state["huevos"]):
            progreso = min(1.0, h["pasos_actuales"] / h["pasos_necesarios"])
            st.markdown(f"### 🥚 {h['tipo']} (Progreso: {h['pasos_actuales']} / {h['pasos_necesarios']} pasos)")
            st.progress(progreso)
            
            if h.get("eclosionado", False):
                st.success(f"🎉 ¡Eclosionado! Nació un **{h['nombre_poke']}** {'✨SHINY✨' if h['es_shiny'] else ''}")
                if st.button(f"Recoger al Pokémon (Huevo #{idx+1})", key=f"recoger_h_{idx}"):
                    st.session_state["huevos"].pop(idx)
                    guardar_progreso()
                    st.rerun()
            else:
                st.caption("💡 Juega partidas de Adivinanza para avanzar los pasos de este huevo.")
            st.divider()

# --- 3. SECCIÓN CARTAS TCG ---
with tab_tcg:
    st.title("🎴 Álbum de Cartas TCG")
    st.write("¡Colecciona cartas únicas comprando sobres en el mercado!")
    st.divider()
    
    if not st.session_state["cartas_coleccion"]:
        st.info("📦 Tu álbum está vacío. ¡Adquiere sobres de cartas en el **Mercado** para empezar a coleccionar!")
    else:
        cols = st.columns(3)
        for idx, carta in enumerate(st.session_state["cartas_coleccion"]):
            col = cols[idx % 3]
            with col:
                st.markdown(f"""
                <div class="card-tcg">
                    <img src="{carta['imagen']}" width="120" style="border-radius:8px;">
                    <h4 style="margin:8px 0 4px 0; color:white;">{carta['nombre']}</h4>
                    <p style="margin:0; color:#ffcc00; font-size:12px; font-weight:bold;">★ {carta['rareza']}</p>
                </div>
                """, unsafe_allow_html=True)

# --- 4. SECCIÓN ENTRENADORES ---
with tab_entrenadores:
    st.title("👥 Entrenadores")
    for key_ent, datos in ENTRENADORES.items():
        es_activo = st.session_state["entrenador_actual"] == key_ent
        c1, c2, c3 = st.columns([1, 3, 2])
        with c1: st.image(datos["avatar_url"], width=70)
        with c2: st.markdown(f"### {datos['nombre']}\n*{datos['descripcion']}*\n💡 `{datos['trait']}`")
        with c3:
            if es_activo: st.success("✅ Activo")
            else:
                if st.button("Seleccionar", key=f"sel_e_{key_ent}", use_container_width=True):
                    st.session_state["entrenador_actual"] = key_ent
                    guardar_progreso()
                    st.rerun()
        st.divider()

# --- 5. SECCIÓN MERCADO (HUEVOS Y SOBRES TCG) ---
with tab_mercado:
    st.title("🛒 Bazar de Objetos y TCG")
    st.write(f"🪙 Tus Monedas: **{st.session_state['monedas']}**")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🥚 Huevo Normal")
        st.write("Necesita 10 aciertos para eclosionar.")
        if st.button("Comprar (🪙 100)", key="b_h_norm", use_container_width=True):
            if st.session_state["monedas"] >= 100:
                st.session_state["monedas"] -= 100
                st.session_state["huevos"].append({"tipo": "Huevo Normal", "pasos_actuales": 0, "pasos_necesarios": 10, "prob_shiny": 0.05, "eclosionado": False})
                guardar_progreso()
                st.success("✅ ¡Huevo Normal añadido a la Guardería!")
                st.rerun()
            else: st.error("❌ Monedas insuficientes")
            
    with c2:
        st.markdown("### ✨ Huevo Shiny")
        st.write("Alta probabilidad de Shiny (5 aciertos).")
        if st.button("Comprar (🪙 300)", key="b_h_shiny", use_container_width=True):
            if st.session_state["monedas"] >= 300:
                st.session_state["monedas"] -= 300
                st.session_state["huevos"].append({"tipo": "Huevo Shiny", "pasos_actuales": 0, "pasos_necesarios": 5, "prob_shiny": 0.50, "eclosionado": False})
                guardar_progreso()
                st.success("✅ ¡Huevo Shiny añadido a la Guardería!")
                st.rerun()
            else: st.error("❌ Monedas insuficientes")

    with c3:
        st.markdown("### 🎴 Sobre TCG")
        st.write("Contiene 1 carta aleatoria coleccionable.")
        if st.button("Comprar (🪙 150)", key="b_sobre_tcg", use_container_width=True):
            if st.session_state["monedas"] >= 150:
                st.session_state["monedas"] -= 150
                poke_id = random.randint(1, 150)
                res_p = obtener_datos_pokemon(poke_id)
                res_s = obtener_datos_especie(poke_id)
                if res_p and res_s:
                    nombre = limpiar_nombre_pokemon(res_s["name"])
                    rareza = random.choice(["Común", "Común", "Rara", "Holográfica", "Ultra Rara"])
                    img = res_p["sprites"]["front_default"]
                    st.session_state["cartas_coleccion"].append({"nombre": nombre, "rareza": rareza, "imagen": img})
                    guardar_progreso()
                    st.success(f"🎴 ¡Abriste un sobre y obtuviste a **{nombre}** ({rareza})!")
                    st.rerun()
            else: st.error("❌ Monedas insuficientes")

# --- 6. SECCIÓN MISIONES ---
with tab_misiones:
    st.title("📜 Misiones del Profesor Oak")
    verificar_reajustar_misiones()
    for k_mis, m_data in st.session_state["misiones_dia"].items():
        estado = "✅ ¡Completada!" if m_data["completada"] else f"⏳ Progreso: {m_data['actual']} / {m_data['meta']}"
        st.info(f"**{m_data['desc']}**\nRecompensa: 🪙 {m_data['recompensa']}\n*{estado}*")

# --- 7. SECCIÓN POKÉDEX ---
with tab_pokedex:
    st.title("📖 Tu Pokédex Web")
    st.write(f"Pokémon registrados: **{len(st.session_state['pokedex_capturados'])} / 1025**")
    st.divider()
    for pid, data in sorted(st.session_state["pokedex_capturados"].items()):
        c1, c2 = st.columns([1, 5])
        with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=70)
        with c2: st.write(f"### #{pid:03d} - {data['nombre']}")
        st.divider()

# --- 8. SECCIÓN SHINYDEV ---
with tab_shinydex:
    st.title("✨ ShinyDex")
    for pid, data in sorted(st.session_state["shinydex_capturados"].items()):
        c1, c2 = st.columns([1, 5])
        with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pid}.png", width=80)
        with c2: st.write(f"### #{pid:03d} - {data['nombre']} ✨")
        st.divider()

# --- 9. SECCIÓN ESTADÍSTICAS ---
with tab_stats:
    st.title("📊 Estadísticas")
    comprobar_logros()
    st.metric("🔥 Racha Máxima", st.session_state["racha_maxima"])
    st.metric("✅ Aciertos Totales", st.session_state["aciertos_totales"])
    st.subheader("🏅 Logros Desbloqueados:")
    for clave, datos in LOGROS_DEF.items():
        if st.session_state["logros"].get(clave, False):
            st.success(f"**{datos['titulo']}** — {datos['desc']}")

# --- 10. SECCIÓN AJUSTES ---
with tab_ajustes:
    st.title("⚙️ Ajustes")
    if st.button("🗑️ Borrar Todo el Progreso", type="secondary"):
        if os.path.exists(ARCHIVO_GUARDADO): os.remove(ARCHIVO_GUARDADO)
        st.rerun()
