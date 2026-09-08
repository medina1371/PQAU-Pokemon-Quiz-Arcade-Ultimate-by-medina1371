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

# --- ESTILOS CSS PARA UNA INTERFAZ FLUIDA ---
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
        border-radius: 10px !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-bottom: 8px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
    }
    div.stButton > button:active {
        transform: translateY(0px);
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
                monedas = datos.get("monedas", 100)
                inventario = datos.get("inventario", {"revividores": 0, "cebos_activos": 0})
                entrenador_actual = datos.get("entrenador_actual", "Red")
                entrenadores_desbloqueados = datos.get("entrenadores_desbloqueados", ["Red"])
                insignias = datos.get("insignias", [])
                misiones_dia = datos.get("misiones_dia", {})
                ultimo_dia_mision = datos.get("ultimo_dia_mision", "")
                inscripciones_legendarias = datos.get("inscripciones_legendarias", [])
                return pokedex, shinydex, racha_max, logros, aciertos, fallos, partidas_perdidas, shinies_vistos, monedas, inventario, entrenador_actual, entrenadores_desbloqueados, insignias, misiones_dia, ultimo_dia_mision, inscripciones_legendarias
        except:
            pass
    return {}, {}, 0, {}, 0, 0, 0, 0, 100, {"revividores": 0, "cebos_activos": 0}, "Red", ["Red"], [], {}, "", []

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
        "inscripciones_legendarias": st.session_state["inscripciones_legendarias"]
    }
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except:
        pass

if "pokedex_capturados" not in st.session_state:
    p_ini, s_ini, rm_ini, l_ini, ac_ini, fa_ini, pp_ini, sv_ini, mon_ini, inv_ini, ent_ini, ents_ini, ins_ini, mis_ini, udm_ini, ileg_ini = cargar_progreso()
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

# Variables para Líderes de Gimnasio y Eventos
if "en_combate_gimnasio" not in st.session_state: st.session_state["en_combate_gimnasio"] = False
if "lider_actual" not in st.session_state: st.session_state["lider_actual"] = None
if "gimnasio_ronda" not in st.session_state: st.session_state["gimnasio_ronda"] = 1
if "gimnasio_preguntas_totales" not in st.session_state: st.session_state["gimnasio_preguntas_totales"] = 3
if "gimnasio_pokemon_actual" not in st.session_state: st.session_state["gimnasio_pokemon_actual"] = None

if "evento_legendario_activo" not in st.session_state: st.session_state["evento_legendario_activo"] = False
if "legendario_actual" not in st.session_state: st.session_state["legendario_actual"] = None

if "reto_activo" not in st.session_state: st.session_state["reto_activo"] = False
if "reto_region" not in st.session_state: st.session_state["reto_region"] = None
if "reto_adivinados" not in st.session_state: st.session_state["reto_adivinados"] = set()
if "siguiente_pokemon_cache" not in st.session_state: st.session_state["siguiente_pokemon_cache"] = None

# --- DEFINICIÓN DE ENTRENADORES Y TRAITS ---
ENTRENADORES = {
    "Red": {
        "nombre": "Red", "gen": 1, "icono": "🔴", "costo": 0,
        "descripcion": "El campeón silencioso de Kanto.",
        "trait": "+1 Poké-Coin extra por acierto",
        "efecto_monedas": 1
    },
    "Leaf": {
        "nombre": "Leaf", "gen": 1, "icono": "🍃", "costo": 250,
        "descripcion": "Entrenadora experta en recolección.",
        "trait": "+50% de probabilidad base de encontrar Pokémon Shiny",
        "efecto_shiny": 0.05
    },
    "Blue": {
        "nombre": "Blue", "gen": 1, "icono": "🔵", "costo": 400,
        "descripcion": "El rival definitivo y arrogante.",
        "trait": "Duplica los puntos de experiencia y racha",
        "efecto_puntos": 2
    },
    "Brock": {
        "nombre": "Brock", "gen": 1, "icono": "🪨", "costo": 300,
        "descripcion": "Líder de roca con férrea voluntad.",
        "trait": "Inicia cada partida con 1 Ficha de Reintento gratis",
        "efecto_revive": 1
    },
    "Misty": {
        "nombre": "Misty", "gen": 1, "icono": "💧", "costo": 350,
        "descripcion": "La sirena implacable de Ciudad Celeste.",
        "trait": "+2 Poké-Coins extra por acierto",
        "efecto_monedas": 2
    },
    "Brendan": {
        "nombre": "Brendan", "gen": 3, "icono": "🌴", "costo": 500,
        "descripcion": "Explorador de la calurosa región de Hoenn.",
        "trait": "+10% más de probabilidad Shiny y +2 monedas por acierto",
        "efecto_shiny": 0.10, "efecto_monedas": 2
    },
    "May": {
        "nombre": "May", "gen": 3, "icono": "👒", "costo": 500,
        "descripcion": "Coordinadora y entrenadora estrella de Hoenn.",
        "trait": "+2 Poké-Coins extra y Ficha de Reintento al iniciar",
        "efecto_monedas": 2, "efecto_revive": 1
    },
    "Cynthia": {
        "nombre": "Cynthia", "gen": 4, "icono": "👑", "costo": 1000,
        "descripcion": "La campeona legendaria de Sinnoh.",
        "trait": "Probabilidad de Shiny multiplicada x3 y +5 monedas por acierto",
        "efecto_shiny": 0.15, "efecto_monedas": 5
    },
    "Giovanni": {
        "nombre": "Giovanni", "gen": 1, "icono": "💼", "costo": 1200,
        "descripcion": "Líder del Team Rocket y magnate de la mafia.",
        "trait": "+10 Poké-Coins por acierto y 2 Fichas de Reintento iniciales",
        "efecto_monedas": 10, "efecto_revive": 2
    }
}

def agregar_notificacion(texto, tipo="success"):
    st.session_state["ultima_notificacion"] = {"texto": texto, "tipo": tipo}

def obtener_titulo_entrenador():
    pokedex_len = len(st.session_state["pokedex_capturados"])
    racha_max = st.session_state["racha_maxima"]
    if racha_max >= 20 or pokedex_len >= 500:
        return "👑 Campeón Indiscutible"
    elif pokedex_len >= 100 or racha_max >= 15:
        return "⚡ Maestro Pokémon"
    elif pokedex_len >= 50 or racha_max >= 10:
        return "📘 Coleccionista Experto"
    elif pokedex_len >= 20 or racha_max >= 5:
        return "🐛 Cazabichos / Joven Promesa"
    else:
        return "🌱 Novato de Pueblo Paleta"

LOGROS_DEF = {
    "primer_paso": {"titulo": "🌱 Primeros Pasos", "desc": "Registra tu primer Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 1},
    "coleccionista_20": {"titulo": "📦 Entrenador Novato", "desc": "Registra 20 Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 20},
    "coleccionista_100": {"titulo": "📘 Experto Pokémon", "desc": "Registra 100 Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 100},
    "suerte_shiny": {"titulo": "✨ ¡Suerte Variocolor!", "desc": "Encuentra y atrapa tu primer Shiny.", "condicion": lambda: len(st.session_state["shinydex_capturados"]) >= 1},
    "racha_5": {"titulo": "🔥 En Chamba", "desc": "Alcanza una racha de 5 aciertos.", "condicion": lambda: st.session_state["racha_maxima"] >= 5},
    "racha_15": {"titulo": "⚡ Maestro de Arcade", "desc": "Alcanza una racha de 15 aciertos.", "condicion": lambda: st.session_state["racha_maxima"] >= 15},
    "veterano_aciertos": {"titulo": "🎯 Tirador Experto", "desc": "Consigue 50 aciertos totales.", "condicion": lambda: st.session_state["aciertos_totales"] >= 50},
    "insomne": {"titulo": "🌙 Insomne", "desc": "Juega una partida de madrugada (00:00 a 05:00).", "condicion": lambda: 0 <= datetime.now().hour < 5},
    "suerte_extrema": {"titulo": "🍀 Maestro de la Suerte", "desc": "Encuentra dos Pokémon Shiny seguidos.", "condicion": lambda: False},
    "caza_legendaria": {"titulo": "🐉 Cazador de Leyendas", "desc": "Derrota y registra un Pokémon Legendario Errante.", "condicion": lambda: len(st.session_state["inscripciones_legendarias"]) >= 1}
}

def comprobar_logros():
    for clave, datos in LOGROS_DEF.items():
        if not st.session_state["logros"].get(clave, False):
            try:
                if datos["condicion"]():
                    st.session_state["logros"][clave] = True
                    st.session_state["monedas"] += 100
                    guardar_progreso()
                    agregar_notificacion(f"🏆 ¡LOGRO DESBLOQUEADO: {datos['titulo']}! (+100 Poké-Coins)", "warning")
            except:
                pass

# --- MISIONES DEL PROFESOR OAK ---
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

# --- LÍDERES DE GIMNASIO ---
LIDERES_GIMNASIO = [
    {"nombre": "Brock", "titulo": "Líder de Ciudad Plateada", "tipo": "Roca", "avatar": "🪨", "rango_ids": (1, 151)},
    {"nombre": "Misty", "titulo": "Líder de Ciudad Celeste", "tipo": "Agua", "avatar": "💧", "rango_ids": (1, 251)},
    {"nombre": "Lt. Surge", "titulo": "Líder de Ciudad Carmín", "tipo": "Eléctrico", "avatar": "⚡", "rango_ids": (1, 386)},
    {"nombre": "Erika", "titulo": "Líder de Ciudad Azuliza", "tipo": "Planta", "avatar": "🌿", "rango_ids": (1, 500)},
    {"nombre": "Sabrina", "titulo": "Líder de Ciudad Azafrán", "tipo": "Psíquico", "avatar": "🔮", "rango_ids": (1, 700)}
]

GENERACIONES = {
    1: {"nombre": "Kanto", "rango": (1, 151), "emoji": "🔴"},
    2: {"nombre": "Johto", "rango": (152, 251), "emoji": "🟡"},
    3: {"nombre": "Hoenn", "rango": (252, 386), "emoji": "🔵"},
    4: {"nombre": "Sinnoh", "rango": (387, 493), "emoji": "💎"},
    5: {"nombre": "Teselia / Unova", "rango": (494, 649), "emoji": "🏙️"},
    6: {"nombre": "Kalos", "rango": (650, 721), "emoji": "✨"},
    7: {"nombre": "Alola", "rango": (722, 809), "emoji": "🏝️"},
    8: {"nombre": "Galar", "rango": (810, 905), "emoji": "⚔️"},
    9: {"nombre": "Paldea", "rango": (906, 1025), "emoji": "🍇"}
}

IDS_LEGENDARIOS = [144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386]

def limpiar_nombre_pokemon(nombre_api: str) -> str:
    nombre = nombre_api.replace("-", " ").title()
    reemplazos = {
        "Iron ": "Ferro-", "Great Tusk": "Colmilargo", "Scream Tail": "Colagrito",
        "Brute Bonnet": "Furioseta", "Flutter Mane": "Melenaleteo", "Slither Wing": "Ondas-Paradójicas",
        "Sandy Shocks": "Pelarena", "Iron Treads": "Ferrodada", "Iron Bundle": "Ferrosaco",
        "Iron Hands": "Ferropalmas", "Iron Jugulis": "Ferrocuello", "Iron Moth": "Ferropolilla",
        "Iron Thorns": "Ferropuas", "Roaring Moon": "Bramaluna", "Iron Valiant": "Ferropaladín",
        "Walking Wake": "Ondas Agua", "Iron Leaves": "Ferrohoja", "Gouging Fire": "Ocaso Feroz",
        "Raging Bolt": "Electrofuria", "Iron Boulder": "Ferrololita", "Iron Crown": "Ferrotesta"
    }
    return reemplazos.get(nombre_api.replace("-", " ").title(), nombre)

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_especie(poke_id: int):
    try:
        return requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/", timeout=2).json()
    except:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_pokemon(poke_id: int):
    try:
        return requests.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}/", timeout=2).json()
    except:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def descargar_imagen_bytes(url: str):
    try:
        return requests.get(url, timeout=2).content
    except:
        return None

def obtener_nombre_por_id(poke_id: int):
    res = obtener_datos_especie(poke_id)
    if res:
        return limpiar_nombre_pokemon(res["name"])
    return f"Pokémon #{poke_id}"

def obtener_pokemon_por_rango(min_id: int, max_id: int):
    if not st.session_state["evento_legendario_activo"] and random.random() < 0.01:
        st.session_state["evento_legendario_activo"] = True
        leg_id = random.choice(IDS_LEGENDARIOS)
        st.session_state["legendario_actual"] = leg_id
        agregar_notificacion(f"🚨 ¡AVISO DE RADAR! ¡Un Pokémon Legendario salvaje ha aparecido!", "warning")

    if st.session_state["evento_legendario_activo"] and st.session_state["legendario_actual"]:
        poke_id = st.session_state["legendario_actual"]
    else:
        if st.session_state["siguiente_pokemon_cache"] is not None:
            poke_cache = st.session_state["siguiente_pokemon_cache"]
            st.session_state["siguiente_pokemon_cache"] = None
            precargar_siguiente_pokemon(min_id, max_id)
            return poke_cache

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
        
        # Calcular pasiva de entrenadores para shiny
        ent_info = ENTRENADORES.get(st.session_state["entrenador_actual"], {})
        base_shiny = 0.05 + ent_info.get("efecto_shiny", 0.0)
        prob_shiny = base_shiny + (0.10 if st.session_state["inventario"].get("cebos_activos", 0) > 0 else 0.0)
        es_shiny = random.random() < prob_shiny
        
        if st.session_state["inventario"].get("cebos_activos", 0) > 0:
            st.session_state["inventario"]["cebos_activos"] -= 1

        img_url = res_poke["sprites"]["front_shiny"] if es_shiny else res_poke["sprites"]["front_default"]
        if not img_url:
            img_url = res_poke["sprites"]["front_default"]
            es_shiny = False
            
        if es_shiny:
            if st.session_state["ultimo_shiny"]:
                st.session_state["logros"]["suerte_extrema"] = True
            st.session_state["ultimo_shiny"] = True
            st.session_state["shinies_vistos"] += 1
            guardar_progreso()
        else:
            st.session_state["ultimo_shiny"] = False
            
        img_data = descargar_imagen_bytes(img_url)
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA") if img_data else None
        
        ids_erroneos = random.sample([i for i in range(min_id, max_id + 1) if i != poke_id], min(3, max_id - min_id))
        nombres_erroneos = [obtener_nombre_por_id(i) for i in ids_erroneos]
        opciones = nombres_erroneos + [nombre]
        random.shuffle(opciones)
        
        resultado = {
            "id": poke_id, "nombre": nombre, "gen": gen,
            "tipos": tipos, "shiny": es_shiny, "imagen": pil_img, "opciones": opciones,
            "es_legendario": st.session_state["evento_legendario_activo"]
        }
        
        if st.session_state["evento_legendario_activo"]:
            st.session_state["evento_legendario_activo"] = False

        precargar_siguiente_pokemon(min_id, max_id)
        return resultado
    except Exception:
        return None

def precargar_siguiente_pokemon(min_id: int, max_id: int):
    try:
        disponibles = [i for i in range(min_id, max_id + 1) if i not in st.session_state["vistos_partida"]]
        if not disponibles:
            disponibles = list(range(min_id, max_id + 1))
        poke_id = random.choice(disponibles)
        
        res_species = obtener_datos_especie(poke_id)
        res_poke = obtener_datos_pokemon(poke_id)
        if res_species and res_poke:
            nombre = limpiar_nombre_pokemon(res_species["name"])
            gen = int(res_species["generation"]["url"].split("/")[-2])
            tipos = [t["type"]["name"] for t in res_poke["types"]]
            es_shiny = random.random() < 0.05
            img_url = res_poke["sprites"]["front_shiny"] if es_shiny else res_poke["sprites"]["front_default"]
            img_data = descargar_imagen_bytes(img_url) if img_url else None
            pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA") if img_data else None
            
            ids_erroneos = random.sample([i for i in range(min_id, max_id + 1) if i != poke_id], min(3, max_id - min_id))
            opciones = [obtener_nombre_por_id(i) for i in ids_erroneos] + [nombre]
            random.shuffle(opciones)
            
            st.session_state["siguiente_pokemon_cache"] = {
                "id": poke_id, "nombre": nombre, "gen": gen,
                "tipos": tipos, "shiny": es_shiny, "imagen": pil_img, "opciones": opciones,
                "es_legendario": False
            }
    except:
        pass

# --- MENÚ LATERAL ---
with st.sidebar:
    ent_actual = ENTRENADORES.get(st.session_state['entrenador_actual'], ENTRENADORES["Red"])
    st.markdown(f"### {ent_actual['icono']} {st.session_state['entrenador_actual']}")
    st.caption(f"**Título:** {obtener_titulo_entrenador()}")
    st.metric("🪙 Poké-Coins", st.session_state["monedas"])
    
    if st.session_state.get("inscripciones_legendarias"):
        st.success(f"🌟 Legendarios: {len(st.session_state['inscripciones_legendarias'])}")
        
    st.divider()

opcion_menu = st.sidebar.radio("🧭 Menú Principal", ["🎮 Jugar Partida", "👥 Selección de Entrenadores", "🏆 Reto Regional (Name All)", "🛒 Mercado / Bazar", "📜 Misiones Diarias", "📖 Pokédex", "✨ ShinyDex", "📊 Estadísticas y Logros", "⚙️ Ajustes"], key="menu_principal_radio")

# --- SECCIÓN SELECCIÓN DE ENTRENADORES ---
if opcion_menu == "👥 Selección de Entrenadores":
    st.title("👥 Gimnasio de Entrenadores Legales")
    st.write("¡Desbloquea y elige a leyendas del universo Pokémon para aprovechar sus **traits y pasivas únicas** en tus partidas!")
    st.divider()
    
    for key_ent, datos in ENTRENADORES.items3 if hasattr(ENTRENADORES, "items3") else ENTRENADORES.items():
        es_desbloqueado = key_ent in st.session_state["entrenadores_desbloqueados"]
        es_activo = st.session_state["entrenador_actual"] == key_ent
        
        c1, c2, c3 = st.columns([1, 3, 2])
        with c1:
            st.markdown(f"### {datos['icono']}")
        with c2:
            st.markdown(f"**{datos['nombre']}** (Gen {datos['gen']})\n\n*{datos['descripcion']}*\n\n💡 **Trait:** `{datos['trait']}`")
        with c3:
            if es_activo:
                st.success("✅ Activo")
            elif es_desbloqueado:
                if st.button(f"Seleccionar", key=f"sel_ent_{key_ent}", use_container_width=True):
                    st.session_state["entrenador_actual"] = key_ent
                    # Aplicar revividor inicial si el trait lo incluye
                    if datos.get("efecto_revive", 0) > 0:
                        st.session_state["inventario"]["revividores"] += datos.get("efecto_revive", 0)
                    guardar_progreso()
                    st.success(f"¡Ahora juegas como {key_ent}!")
                    st.rerun()
            else:
                if st.button(f"Desbloquear (🪙 {datos['costo']})", key=f"buy_ent_{key_ent}", use_container_width=True):
                    if st.session_state["monedas"] >= datos["costo"]:
                        st.session_state["monedas"] -= datos["costo"]
                        st.session_state["entrenadores_desbloqueados"].append(key_ent)
                        st.session_state["entrenador_actual"] = key_ent
                        if datos.get("efecto_revive", 0) > 0:
                            st.session_state["inventario"]["revividores"] += datos.get("efecto_revive", 0)
                        guardar_progreso()
                        st.success(f"🎉 ¡Has desbloqueado y seleccionado a {key_ent}!")
                        st.rerun()
                    else:
                        st.error("❌ No tienes suficientes Poké-Coins.")
        st.divider()
    st.stop()

# --- SECCIÓN MISIONES DIARIAS ---
elif opcion_menu == "📜 Misiones Diarias":
    st.title("📜 Misiones del Profesor Oak")
    st.write("¡Completa tareas diarias para conseguir Poké-Coins extra!")
    st.divider()
    verificar_reajustar_misiones()
    for k_mis, m_data in st.session_state["misiones_dia"].items():
        estado = "✅ ¡Completada!" if m_data["completada"] else f"⏳ Progreso: {m_data['actual']} / {m_data['meta']}"
        st.info(f"**{m_data['desc']}**\n\nRecompensa: 🪙 {m_data['recompensa']} Poké-Coins\n\n*{estado}*")
    st.stop()

# --- SECCIÓN MERCADO / BAZAR (Precios Más Caros) ---
elif opcion_menu == "🛒 Mercado / Bazar":
    st.title("🛒 Bazar de Objetos Pokémon (Edición de Lujo)")
    st.write("¡Invierte tus **Poké-Coins** en ventajas caras y poderosas para expertos!")
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1: st.metric("🪙 Tus Monedas", st.session_state["monedas"])
    with c2: st.metric("🎒 Fichas de Reintento", st.session_state["inventario"].get("revividores", 0))
    
    st.subheader("📦 Artículos Exclusivos:")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info("**🔄 Ficha de Reintento Élite**\n\nPermite revivir una vez tras caer derrotado y conservar tu racha.")
        if st.button("Comprar (🪙 150)", use_container_width=True, key="btn_comprar_revive_caro"):
            if st.session_state["monedas"] >= 150:
                st.session_state["monedas"] -= 150
                st.session_state["inventario"]["revividores"] += 1
                guardar_progreso()
                st.success("✅ ¡Has comprado una Ficha de Reintento!")
                st.rerun()
            else:
                st.error("❌ Necesitas 150 Poké-Coins.")
                
    with col_t2:
        st.info("**✨ Cebo Shiny Supremo (10 Rondas)**\n\nAumenta drásticamente la probabilidad de Shinies durante 10 rondas.")
        if st.button("Comprar (🪙 350)", use_container_width=True, key="btn_comprar_cebo_caro"):
            if st.session_state["monedas"] >= 350:
                st.session_state["monedas"] -= 350
                st.session_state["inventario"]["cebos_activos"] = st.session_state["inventario"].get("cebos_activos", 0) + 10
                guardar_progreso()
                st.success("✅ ¡Cebo Supremo activado para 10 rondas!")
                st.rerun()
            else:
                st.error("❌ Necesitas 350 Poké-Coins.")
    st.stop()

# --- SECCIÓN POKÉDEX ---
elif opcion_menu == "📖 Pokédex":
    st.title("📖 Tu Pokédex Web")
    st.write(f"Pokémon registrados: **{len(st.session_state['pokedex_capturados'])} / 1025**")
    if st.session_state["pokedex_capturados"]:
        for pid, data in sorted(st.session_state["pokedex_capturados"].items()):
            c1, c2 = st.columns([1, 5])
            with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=65)
            with c2: st.write(f"**#{pid:03d}** - {data['nombre']} (Gen {data['gen']})")
            st.divider()
    else:
        st.info("💡 ¡Juega para rellenar tu Pokédex!")
    st.stop()

# --- SECCIÓN SHINYDEV ---
elif opcion_menu == "✨ ShinyDex":
    st.title("✨ Tu ShinyDex")
    st.write(f"Shinies capturados: **{len(st.session_state['shinydex_capturados'])}**")
    if st.session_state["shinydex_capturados"]:
        for pid, data in sorted(st.session_state["shinydex_capturados"].items()):
            c1, c2 = st.columns([1, 5])
            with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pid}.png", width=75)
            with c2: st.write(f"**#{pid:03d}** - {data['nombre']} ✨")
            st.divider()
    else:
        st.info("🍀 Todavía no te ha salido ningún Shiny. ¡Sigue probando!")
    st.stop()

# --- RETO REGIONAL ---
elif opcion_menu == "🏆 Reto Regional (Name All)":
    st.title("🏆 El Reto Regional (Name All)")
    st.write("¡Escribe los nombres de todos los Pokémon de la región elegida!")
    st.divider()
    if not st.session_state["reto_activo"]:
        reg_elegida = st.selectbox("Selecciona la región:", list(GENERACIONES.keys()), format_func=lambda x: f"{GENERACIONES[x]['emoji']} {GENERACIONES[x]['nombre']} ({GENERACIONES[x]['rango'][0]} - {GENERACIONES[x]['rango'][1]})", key="sel_reto_reg")
        if st.button("🚀 ¡Comenzar Reto Regional!", type="primary", use_container_width=True, key="btn_comenzar_reto"):
            st.session_state["reto_activo"] = True
            st.session_state["reto_region"] = reg_elegida
            st.session_state["reto_adivinados"] = set()
            st.rerun()
    else:
        reg_id = st.session_state["reto_region"]
        rango_reg = GENERACIONES[reg_id]["rango"]
        total_reg = (rango_reg[1] - rango_reg[0]) + 1
        adivinados = len(st.session_state["reto_adivinados"])
        st.metric(label=f"📊 Progreso en {GENERACIONES[reg_id]['nombre']}", value=f"{adivinados} / {total_reg}")
        
        nombre_input = st.text_input("Escribe el nombre de un Pokémon:", key="input_reto_poke", placeholder="Ej: Pikachu...").strip().title()
        if nombre_input:
            encontrado_id = None
            for pid in range(rango_reg[0], rango_reg[1] + 1):
                if obtener_nombre_por_id(pid).lower() == nombre_input.lower():
                    encontrado_id = pid
                    break
            if encontrado_id and encontrado_id not in st.session_state["reto_adivinados"]:
                st.session_state["reto_adivinados"].add(encontrado_id)
                st.session_state["pokedex_capturados"][encontrado_id] = {"nombre": obtener_nombre_por_id(encontrado_id), "gen": reg_id}
                st.session_state["monedas"] += 5
                avanzar_progreso_mision("mision_2", 1)
                guardar_progreso()
                st.success(f"🎉 ¡Correcto! Descubierto {obtener_nombre_por_id(encontrado_id)} (+5 Poké-Coins)")
                st.rerun()
            elif encontrado_id in st.session_state["reto_adivinados"]:
                st.warning("⚠️ ¡Ya habías adivinado ese Pokémon!")

        cols_grilla = st.columns(5)
        for idx, pid in enumerate(range(rango_reg[0], rango_reg[1] + 1)):
            col = cols_grilla[idx % 5]
            with col:
                if pid in st.session_state["reto_adivinados"]:
                    st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=70)
                    st.caption(f"#{pid}\n{obtener_nombre_por_id(pid)}")
                else:
                    st.info(f"#{pid}\n❓")
        st.divider()
        if st.button("🚪 Abandonar Reto", use_container_width=True, key="btn_abandonar_reto"):
            st.session_state["reto_activo"] = False
            st.session_state["reto_adivinados"].clear()
            st.rerun()
    st.stop()

# --- ESTADÍSTICAS Y LOGROS ---
elif opcion_menu == "📊 Estadísticas y Logros":
    st.title("📊 Panel de Rendimiento")
    comprobar_logros()
    p_stats, p_logros = st.tabs(["📊 Estadísticas", "🏅 Trofeos"])
    with p_stats:
        total_resp = st.session_state["aciertos_totales"] + st.session_state["fallos_totales"]
        pct = (st.session_state["aciertos_totales"] / total_resp * 100) if total_resp > 0 else 0.0
        st.info(f"👑 **Título Actual:** {obtener_titulo_entrenador()} | 👥 **Entrenador:** {st.session_state['entrenador_actual']}")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🔥 Racha Máxima", st.session_state["racha_maxima"])
            st.metric("✅ Aciertos", st.session_state["aciertos_totales"])
            st.metric("💥 Partidas Perdidas", st.session_state["partidas_perdidas"])
        with c2:
            st.metric("📖 Pokédex", f"{len(st.session_state['pokedex_capturados'])} / 1025")
            st.metric("❌ Fallos", st.session_state["fallos_totales"])
            st.metric("✨ Shinies Vistos", st.session_state["shinies_vistos"])
        st.divider()
        st.metric("🎯 Precisión General", f"{pct:.1f}%")
    with p_logros:
        for clave, datos in LOGROS_DEF.items():
            if st.session_state["logros"].get(clave, False):
                st.success(f"**{datos['titulo']}** — {datos['desc']} (✅ Desbloqueado)")
            else:
                st.info(f"**{datos['titulo']}** — {datos['desc']} (🔒 Bloqueado)")
    st.stop()

# --- AJUSTES ---
elif opcion_menu == "⚙️ Ajustes":
    st.title("⚙️ Ajustes y Perfil")
    if st.button("🗑️ Borrar Todo el Progreso", type="secondary", key="btn_borrar_progreso"):
        for k in ["pokedex_capturados", "shinydex_capturados", "logros", "vistos_partida", "inscripciones_legendarias", "entrenadores_desbloqueados"]:
            if isinstance(st.session_state[k], set): st.session_state[k].clear()
            elif isinstance(st.session_state[k], list): st.session_state[k] = ["Red"] if k == "entrenadores_desbloqueados" else []
            else: st.session_state[k].clear()
        for k in ["racha_maxima", "aciertos_totales", "fallos_totales", "partidas_perdidas", "shinies_vistos", "racha", "puntos", "monedas"]:
            st.session_state[k] = 0
        st.session_state["monedas"] = 100
        st.session_state["inventario"] = {"revividores": 0, "cebos_activos": 0}
        st.session_state["entrenador_actual"] = "Red"
        st.session_state["ultima_notificacion"] = None
        if os.path.exists(ARCHIVO_GUARDADO): os.remove(ARCHIVO_GUARDADO)
        st.success("✅ ¡Progreso reiniciado con éxito!")
    st.stop()

# --- PANTALLA DE DERROTA ---
if st.session_state["derrota"]:
    st.title("💥 ¡Has Caído!")
    st.error("¡Te equivocaste de respuesta!")
    if st.session_state["ultimo_pokemon_fallado"]:
        pf = st.session_state["ultimo_pokemon_fallado"]
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(pf["imagen"], width=220)
            st.subheader(f"Era: #{pf['id']:03d} - {pf['nombre']}")
    st.divider()
    
    tiene_revive = st.session_state["inventario"].get("revividores", 0) > 0
    if tiene_revive:
        if st.button(f"✨ Usar Ficha de Reintento (Tienes {st.session_state['inventario']['revividores']})", type="primary", use_container_width=True, key="btn_revivir"):
            st.session_state["inventario"]["revividores"] -= 1
            st.session_state["derrota"] = False
            guardar_progreso()
            agregar_notificacion("✨ ¡Has revivido! Tu racha se mantiene.", "success")
            st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Reiniciar Partida", type="secondary" if tiene_revive else "primary", use_container_width=True, key="btn_reintentar_derrota"):
            st.session_state["derrota"] = False
            st.session_state["puntos"] = 0
            st.session_state["racha"] = 0
            st.session_state["vistos_partida"].clear()
            st.session_state["siguiente_pokemon_cache"] = None
            st.session_state["id_ronda"] += 1
            rango = st.session_state["rango_seleccionado"]
            st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
            st.rerun()
    with c2:
        if st.button("🏠 Menú Principal", use_container_width=True, key="btn_menu_derrota"):
            st.session_state["derrota"] = False
            st.session_state["en_partida"] = False
            st.session_state["en_combate_gimnasio"] = False
            st.rerun()
    st.stop()

# --- COMBATE DE GIMNASIO (RPG) ---
if st.session_state["en_combate_gimnasio"]:
    st.title(f"⚔️ COMBATE DE GIMNASIO: {st.session_state['lider_actual']['nombre']}")
    st.write(f"*{st.session_state['lider_actual']['titulo']}* — Pregunta {st.session_state['gimnasio_ronda']} de {st.session_state['gimnasio_preguntas_totales']}")
    st.divider()
    
    poke_g = st.session_state["gimnasio_pokemon_actual"]
    if poke_g:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(poke_g["imagen"], width=240)
            st.markdown(f"### {st.session_state['lider_actual']['avatar']} ¡El líder desafía tus conocimientos!")
            
        for idx, opc in enumerate(poke_g["opciones"]):
            if st.button(f"{opc}", use_container_width=True, key=f"btn_gym_{st.session_state['gimnasio_ronda']}_{idx}"):
                if opc == poke_g["nombre"]:
                    if st.session_state["gimnasio_ronda"] >= st.session_state["gimnasio_preguntas_totales"]:
                        st.session_state["en_combate_gimnasio"] = False
                        st.session_state["monedas"] += 300
                        agregar_notificacion("🏆 ¡Has derrotado al Líder de Gimnasio! (+300 Poké-Coins)", "success")
                        st.rerun()
                    else:
                        st.session_state["gimnasio_ronda"] += 1
                        r_min, r_max = st.session_state["lider_actual"]["rango_ids"]
                        st.session_state["gimnasio_pokemon_actual"] = obtener_pokemon_por_rango(r_min, r_max)
                        st.success("✅ ¡Acierto de gimnasio! Siguiente pregunta...")
                        st.rerun()
                else:
                    st.session_state["en_combate_gimnasio"] = False
                    st.session_state["derrota"] = True
                    st.session_state["ultimo_pokemon_fallado"] = poke_g
                    st.rerun()
    st.stop()

# --- MENÚ INICIAL DE PARTIDA ---
if not st.session_state["en_partida"]:
    ent_actual = ENTRENADORES.get(st.session_state['entrenador_actual'], ENTRENADORES["Red"])
    st.title("🎮 Pokémon Quiz Arcade Ultimate")
    st.write(f"✨ *Entrenador actual:* **{ent_actual['icono']} {st.session_state['entrenador_actual']}** (`{ent_actual['trait']}`) ✨")
    st.divider()
    
    filtro_gen = st.radio("🌍 1. Selecciona el filtro de generaciones:", ["🌟 Todas (Gen 1-9)", "🔴 Clásicas (Gen 1 - 3)", "💎 Intermedias (Gen 4 - 6)", "⚔️ Recientes (Gen 7 - 9)"], key="filtro_gen_menu")
    modo_juego = st.radio("🎯 2. Elige el modo de juego:", ["🏷️ Adivina Nombre", "🌍 Adivina Generación", "🧩 Cripta de Tipos", "🕵️ Silueta Misteriosa"], key="modo_juego_menu")
    
    if st.button("🚀 ¡Comenzar Partida Ya!", type="primary", use_container_width=True, key="btn_comenzar_partida"):
        st.session_state["en_partida"] = True
        st.session_state["puntos"] = 0
        st.session_state["racha"] = 0
        st.session_state["vistos_partida"].clear()
        st.session_state["siguiente_pokemon_cache"] = None
        st.session_state["modo_seleccionado"] = modo_juego
        st.session_state["id_ronda"] += 1
        
        if filtro_gen == "🔴 Clásicas (Gen 1 - 3)":
            st.session_state["rango_seleccionado"] = (1, 386)
            st.session_state["generaciones_permitidas"] = [1, 2, 3]
        elif filtro_gen == "💎 Intermedias (Gen 4 - 6)":
            st.session_state["rango_seleccionado"] = (387, 721)
            st.session_state["generaciones_permitidas"] = [4, 5, 6]
        elif filtro_gen == "⚔️ Recientes (Gen 7 - 9)":
            st.session_state["rango_seleccionado"] = (722, 1025)
            st.session_state["generaciones_permitidas"] = [7, 8, 9]
        else:
            st.session_state["rango_seleccionado"] = (1, 1025)
            st.session_state["generaciones_permitidas"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            
        rango = st.session_state["rango_seleccionado"]
        st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
        st.rerun()

else:
    # --- PARTIDA ACTIVA ---
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
    modo = st.session_state["modo_seleccionado"]
    rango = st.session_state["rango_seleccionado"]
    ronda_id = st.session_state["id_ronda"]
    
    poke = st.session_state.get("pokemon_actual")
    if not poke:
        poke = obtener_pokemon_por_rango(rango[0], rango[1])
        st.session_state["pokemon_actual"] = poke
        
    if poke:
        st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
        if poke["shiny"]:
            st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            agregar_notificacion("✨ ¡SORPRESA! ¡Apareció un Pokémon SHINY!", "warning")
            
        if poke.get("es_legendario"):
            if poke["id"] not in st.session_state["inscripciones_legendarias"]:
                st.session_state["inscripciones_legendarias"].append(poke["id"])
                agregar_notificacion(f"🌟 ¡Has registrado al Pokémon Legendario {poke['nombre']} en tus inscripciones!", "success")
                guardar_progreso()

        guardar_progreso()

        # Cálculo de recompensas según el Entrenador Activo
        ent_info = ENTRENADORES.get(st.session_state["entrenador_actual"], {})
        bonus_monedas = ent_info.get("efecto_monedas", 1)
        bonus_puntos = ent_info.get("efecto_puntos", 1)

        # --- MODO 1: ADIVINA NOMBRE ---
        if modo == "🏷️ Adivina Nombre":
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if poke["imagen"]: st.image(poke["imagen"], width=260)
                
            st.subheader("¿Cuál de estos Pokémon es el correcto?")
            for idx, opc_nombre in enumerate(poke["opciones"]):
                if st.button(f"{opc_nombre}", use_container_width=True, key=f"btn_nombre_{ronda_id}_{idx}"):
                    if opc_nombre == poke["nombre"]:
                        st.session_state["puntos"] += 1 * bonus_puntos
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        ganancia = (5 * bonus_puntos) + bonus_monedas
                        st.session_state["monedas"] += ganancia
                        avanzar_progreso_mision("mision_1", 1)
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        
                        if st.session_state["racha"] > 0 and st.session_state["racha"] % 5 == 0:
                            lider_elegido = random.choice(LIDERES_GIMNASIO)
                            st.session_state["en_combate_gimnasio"] = True
                            st.session_state["lider_actual"] = lider_elegido
                            st.session_state["gimnasio_ronda"] = 1
                            r_min, r_max = lider_elegido["rango_ids"]
                            st.session_state["gimnasio_pokemon_actual"] = obtener_pokemon_por_rango(r_min, r_max)
                            agregar_notificacion(f"⚔️ ¡Reto de Gimnasio activado contra {lider_elegido['nombre']}!", "warning")
                            st.rerun()

                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto! Era {poke['nombre']} (+{ganancia} Poké-Coins)", "success")
                        st.session_state["id_ronda"] += 1
                        st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
                        st.rerun()
                    else:
                        st.session_state["fallos_totales"] += 1
                        st.session_state["partidas_perdidas"] += 1
                        guardar_progreso()
                        agregar_notificacion("¡Fallaste! Fin de la partida.", "error")
                        st.session_state["ultimo_pokemon_fallado"] = poke
                        st.session_state["derrota"] = True
                        st.rerun()

        # --- MODO 2: ADIVINA GENERACIÓN ---
        elif modo == "🌍 Adivina Generación":
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2: 
                if poke["imagen"]: st.image(poke["imagen"], width=260)
                
            st.subheader("¿A qué generación pertenece este Pokémon?")
            gens_permitidas = st.session_state["generaciones_permitidas"]
            for idx, g_num in enumerate(gens_permitidas):
                g_info = GENERACIONES[g_num]
                if st.button(f"{g_info['emoji']} Gen {g_num} ({g_info['nombre']})", use_container_width=True, key=f"btn_gen_{ronda_id}_{idx}_{g_num}"):
                    if g_num == poke["gen"]:
                        st.session_state["puntos"] += 1 * bonus_puntos
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        ganancia = (5 * bonus_puntos) + bonus_monedas
                        st.session_state["monedas"] += ganancia
                        avanzar_progreso_mision("mision_1", 1)
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto! Gen {poke['gen']} (+{ganancia} Poké-Coins)", "success")
                        st.session_state["id_ronda"] += 1
                        st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
                        st.rerun()
                    else:
                        st.session_state["fallos_totales"] += 1
                        st.session_state["partidas_perdidas"] += 1
                        guardar_progreso()
                        agregar_notificacion("¡Fallaste!", "error")
                        st.session_state["ultimo_pokemon_fallado"] = poke
                        st.session_state["derrota"] = True
                        st.rerun()

        # --- MODO 3: CRIPTA DE TIPOS ---
        elif modo == "🧩 Cripta de Tipos":
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f"### 🛡️ Tipos Elementales:\n" + "".join([f"` {t.upper()} ` " for t in poke["tipos"]]))
                st.caption("*(Adivina el Pokémon basándote únicamente en sus tipos)*")
                
            for idx, opc_nombre in enumerate(poke["opciones"]):
                if st.button(f"{opc_nombre}", use_container_width=True, key=f"btn_cripta_{ronda_id}_{idx}"):
                    if opc_nombre == poke["nombre"]:
                        st.session_state["puntos"] += 2 * bonus_puntos
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        ganancia = (10 * bonus_puntos) + bonus_monedas
                        st.session_state["monedas"] += ganancia
                        avanzar_progreso_mision("mision_1", 1)
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto en Cripta! Era {poke['nombre']} (+{ganancia} Poké-Coins)", "success")
                        st.session_state["id_ronda"] += 1
                        st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
                        st.rerun()
                    else:
                        st.session_state["fallos_totales"] += 1
                        st.session_state["partidas_perdidas"] += 1
                        guardar_progreso()
                        agregar_notificacion("¡Fallaste en la cripta!", "error")
                        st.session_state["ultimo_pokemon_fallado"] = poke
                        st.session_state["derrota"] = True
                        st.rerun()

        # --- MODO 4: SILUETA MISTERIOSA ---
        elif modo == "🕵️ Silueta Misteriosa":
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if poke["imagen"]:
                    silueta = ImageOps.colorize(poke["imagen"].convert("L"), black="black", white="black")
                    st.image(silueta, width=260)
                
            st.subheader("¿Quién es este Pokémon oculto en la sombra?")
            for idx, opc_nombre in enumerate(poke["opciones"]):
                if st.button(f"{opc_nombre}", use_container_width=True, key=f"btn_silueta_{ronda_id}_{idx}"):
                    if opc_nombre == poke["nombre"]:
                        st.session_state["puntos"] += 2 * bonus_puntos
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        ganancia = (10 * bonus_puntos) + bonus_monedas
                        st.session_state["monedas"] += ganancia
                        avanzar_progreso_mision("mision_1", 1)
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        guardar_progreso()
                        agregar_notificacion(f"¡Acertaste la silueta! Era {poke['nombre']} (+{ganancia} Poké-Coins)", "success")
                        st.session_state["id_ronda"] += 1
                        st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
                        st.rerun()
                    else:
                        st.session_state["fallos_totales"] += 1
                        st.session_state["partidas_perdidas"] += 1
                        guardar_progreso()
                        agregar_notificacion("¡Fallaste la silueta!", "error")
                        st.session_state["ultimo_pokemon_fallado"] = poke
                        st.session_state["derrota"] = True
                        st.rerun()

    st.divider()
    if st.button("🏠 Volver al Menú Principal", use_container_width=True, key="btn_volver_menu_activo"):
        st.session_state["en_partida"] = False
        st.session_state["derrota"] = False
        st.session_state["en_combate_gimnasio"] = False
        st.rerun()
