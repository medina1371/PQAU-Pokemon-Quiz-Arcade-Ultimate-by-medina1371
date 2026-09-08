import random
import requests
import streamlit as st
from PIL import Image
import io
import json
import os

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
                return pokedex, shinydex, racha_max, logros, aciertos, fallos, partidas_perdidas, shinies_vistos
        except:
            pass
    return {}, {}, 0, {}, 0, 0, 0, 0

def guardar_progreso():
    datos = {
        "pokedex": st.session_state["pokedex_capturados"],
        "shinydex": st.session_state["shinydex_capturados"],
        "racha_maxima": st.session_state["racha_maxima"],
        "logros": st.session_state["logros"],
        "aciertos_totales": st.session_state["aciertos_totales"],
        "fallos_totales": st.session_state["fallos_totales"],
        "partidas_perdidas": st.session_state["partidas_perdidas"],
        "shinies_vistos": st.session_state["shinies_vistos"]
    }
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except:
        pass

if "pokedex_capturados" not in st.session_state:
    p_ini, s_ini, rm_ini, l_ini, ac_ini, fa_ini, pp_ini, sv_ini = cargar_progreso()
    st.session_state["pokedex_capturados"] = p_ini
    st.session_state["shinydex_capturados"] = s_ini
    st.session_state["racha_maxima"] = rm_ini
    st.session_state["logros"] = l_ini
    st.session_state["aciertos_totales"] = ac_ini
    st.session_state["fallos_totales"] = fa_ini
    st.session_state["partidas_perdidas"] = pp_ini
    st.session_state["shinies_vistos"] = sv_ini

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

if "reto_activo" not in st.session_state: st.session_state["reto_activo"] = False
if "reto_region" not in st.session_state: st.session_state["reto_region"] = None
if "reto_adivinados" not in st.session_state: st.session_state["reto_adivinados"] = set()
if "siguiente_pokemon_cache" not in st.session_state: st.session_state["siguiente_pokemon_cache"] = None

def agregar_notificacion(texto, tipo="success"):
    st.session_state["ultima_notificacion"] = {"texto": texto, "tipo": tipo}

LOGROS_DEF = {
    "primer_paso": {"titulo": "🌱 Primeros Pasos", "desc": "Registra tu primer Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 1},
    "coleccionista_20": {"titulo": "📦 Entrenador Novato", "desc": "Registra 20 Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 20},
    "coleccionista_100": {"titulo": "📘 Experto Pokémon", "desc": "Registra 100 Pokémon.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 100},
    "suerte_shiny": {"titulo": "✨ ¡Suerte Variocolor!", "desc": "Encuentra y atrapa tu primer Shiny.", "condicion": lambda: len(st.session_state["shinydex_capturados"]) >= 1},
    "racha_5": {"titulo": "🔥 En Chamba", "desc": "Alcanza una racha de 5 aciertos.", "condicion": lambda: st.session_state["racha_maxima"] >= 5},
    "racha_15": {"titulo": "⚡ Maestro de Arcade", "desc": "Alcanza una racha de 15 aciertos.", "condicion": lambda: st.session_state["racha_maxima"] >= 15},
    "veterano_aciertos": {"titulo": "🎯 Tirador Experto", "desc": "Consigue 50 aciertos totales.", "condicion": lambda: st.session_state["aciertos_totales"] >= 50},
}

def comprobar_logros():
    for clave, datos in LOGROS_DEF.items():
        if not st.session_state["logros"].get(clave, False):
            try:
                if datos["condicion"]():
                    st.session_state["logros"][clave] = True
                    guardar_progreso()
                    agregar_notificacion(f"🏆 ¡LOGRO DESBLOQUEADO: {datos['titulo']}!", "warning")
            except:
                pass

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

TRADUCCION_TIPOS = {
    "normal": "Normal", "fire": "Fuego", "water": "Agua", "grass": "Planta",
    "electric": "Eléctrico", "ice": "Hielo", "fighting": "Lucha", "poison": "Veneno",
    "ground": "Tierra", "flying": "Volador", "psychic": "Psíquico", "bug": "Bicho",
    "rock": "Roca", "ghost": "Fantasma", "dragon": "Dragón", "dark": "Siniestro",
    "steel": "Acero", "fairy": "Hada"
}

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
        
        es_shiny = random.random() < 0.05
        img_url = res_poke["sprites"]["front_shiny"] if es_shiny else res_poke["sprites"]["front_default"]
        if not img_url:
            img_url = res_poke["sprites"]["front_default"]
            es_shiny = False
            
        if es_shiny:
            st.session_state["shinies_vistos"] += 1
            guardar_progreso()
            
        img_data = descargar_imagen_bytes(img_url)
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA") if img_data else None
        
        ids_erroneos = random.sample([i for i in range(min_id, max_id + 1) if i != poke_id], min(3, max_id - min_id))
        nombres_erroneos = [obtener_nombre_por_id(i) for i in ids_erroneos]
        opciones = nombres_erroneos + [nombre]
        random.shuffle(opciones)
        
        resultado = {
            "id": poke_id, "nombre": nombre, "gen": gen,
            "tipos": tipos, "shiny": es_shiny, "imagen": pil_img, "opciones": opciones
        }
        
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
                "tipos": tipos, "shiny": es_shiny, "imagen": pil_img, "opciones": opciones
            }
    except:
        pass

# --- MENÚ LATERAL ---
opcion_menu = st.sidebar.radio("🧭 Menú Principal", ["🎮 Jugar Partida", "🏆 Reto Regional (Name All)", "📖 Pokédex", "✨ ShinyDex", "📊 Estadísticas y Logros", "⚙️ Ajustes"], key="menu_principal_radio")

# --- SECCIÓN POKÉDEX ---
if opcion_menu == "📖 Pokédex":
    st.title("📖 Tu Pokédex Web")
    st.write(f"Pokémon registrados: **{len(st.session_state['pokedex_capturados'])} / 1025**")
    
    if st.session_state["pokedex_capturados"]:
        tipo_filtro = st.radio("Filtrar:", ["🌟 Ver todos", "🔢 Filtrar por ID", "🗺️ Filtrar por Región"], horizontal=True, key="filtro_pokedex")
        registros = st.session_state["pokedex_capturados"]
        
        if tipo_filtro == "🔢 Filtrar por ID":
            id_buscado = st.number_input("Número ID:", min_value=1, max_value=1025, value=1, key="num_id_pokedex")
            if id_buscado in registros:
                p = registros[id_buscado]
                st.success("✅ ¡Registrado!")
                c1, c2 = st.columns([1, 3])
                with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id_buscado}.png", width=110)
                with c2: st.markdown(f"### **#{id_buscado:03d} - {p['nombre']}**\n🌍 Gen {p['gen']}")
            else:
                st.warning(f"❌ Aún no tienes el Pokémon #{id_buscado:03d}.")
                
        elif tipo_filtro == "🗺️ Filtrar por Región":
            reg = st.selectbox("Región:", list(GENERACIONES.values()), format_func=lambda x: f"{x['emoji']} {x['nombre']}", key="sel_reg_pokedex")
            gen_target = [k for k, v in GENERACIONES.items() if v == reg][0]
            filtrados = [(pid, data) for pid, data in sorted(registros.items()) if data["gen"] == gen_target]
            
            st.subheader(f"📍 {reg['nombre']} ({len(filtrados)})")
            for pid, data in filtrados:
                c1, c2 = st.columns([1, 5])
                with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=65)
                with c2: st.write(f"**#{pid:03d}** - {data['nombre']}")
                st.divider()
        else:
            for pid, data in sorted(registros.items()):
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
        st.info("🍀 Todavía no te ha salido ningún Shiny (5% de probabilidad). ¡Sigue probando!")
    st.stop()

# --- RETO REGIONAL ---
elif opcion_menu == "🏆 Reto Regional (Name All)":
    st.title("🏆 El Reto Regional (Name All)")
    st.write("¡Escribe los nombres de todos los Pokémon de la región elegida! Se irán descubriendo en la cuadrícula.")
    st.divider()
    
    if not st.session_state["reto_activo"]:
        reg_elegida = st.selectbox("Selecciona la región para el reto:", list(GENERACIONES.keys()), format_func=lambda x: f"{GENERACIONES[x]['emoji']} {GENERACIONES[x]['nombre']} ({GENERACIONES[x]['rango'][0]} - {GENERACIONES[x]['rango'][1]})", key="sel_reto_reg")
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
        
        nombre_input = st.text_input("Escribe el nombre de un Pokémon:", key="input_reto_poke", placeholder="Ej: Pikachu, Charizard...").strip().title()
        
        if nombre_input:
            encontrado_id = None
            for pid in range(rango_reg[0], rango_reg[1] + 1):
                nombre_real = obtener_nombre_por_id(pid)
                if nombre_real.lower() == nombre_input.lower():
                    encontrado_id = pid
                    break
            
            if encontrado_id and encontrado_id not in st.session_state["reto_adivinados"]:
                st.session_state["reto_adivinados"].add(encontrado_id)
                st.session_state["pokedex_capturados"][encontrado_id] = {"nombre": obtener_nombre_por_id(encontrado_id), "gen": reg_id}
                guardar_progreso()
                st.success(f"🎉 ¡Correcto! Has descubierto a {obtener_nombre_por_id(encontrado_id)}")
                st.rerun()
            elif encontrado_id in st.session_state["reto_adivinados"]:
                st.warning("⚠️ ¡Ya habías adivinado ese Pokémon!")

        st.subheader("🎴 Cuadrícula de Descubrimientos:")
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

# --- SECCIÓN ESTADÍSTICAS Y LOGROS ---
elif opcion_menu == "📊 Estadísticas y Logros":
    st.title("📊 Panel de Rendimiento")
    comprobar_logros()
    
    p_stats, p_logros = st.tabs(["📊 Estadísticas", "🏅 Trofeos"])
    with p_stats:
        total_resp = st.session_state["aciertos_totales"] + st.session_state["fallos_totales"]
        pct = (st.session_state["aciertos_totales"] / total_resp * 100) if total_resp > 0 else 0.0
        
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

# --- SECCIÓN AJUSTES ---
elif opcion_menu == "⚙️ Ajustes":
    st.title("⚙️ Ajustes")
    if st.button("🗑️ Borrar Todo el Progreso", type="secondary", key="btn_borrar_progreso"):
        for k in ["pokedex_capturados", "shinydex_capturados", "logros", "vistos_partida"]:
            st.session_state[k].clear()
        for k in ["racha_maxima", "aciertos_totales", "fallos_totales", "partidas_perdidas", "shinies_vistos", "racha", "puntos"]:
            st.session_state[k] = 0
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
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Reintentar", type="primary", use_container_width=True, key="btn_reintentar_derrota"):
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
            st.rerun()
    st.stop()

# --- MENÚ INICIAL DE PARTIDA ---
if not st.session_state["en_partida"]:
    st.title("🎮 Pokémon Quiz Arcade Ultimate")
    st.write("✨ *¡Pon a prueba tus conocimientos Pokémon al máximo nivel!* ✨")
    st.divider()
    
    filtro_gen = st.radio("🌍 1. Selecciona el filtro de generaciones:", ["🌟 Todas (Gen 1-9)", "🔴 Clásicas (Gen 1 - 3)", "💎 Intermedias (Gen 4 - 6)", "⚔️ Recientes (Gen 7 - 9)"], key="filtro_gen_menu")
    modo_juego = st.radio("🎯 2. Elige el modo de juego:", ["🏷️ Adivina Nombre", "🌍 Adivina Generación"], key="modo_juego_menu")
    
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
    
    c1, c2 = st.columns(2)
    with c1: st.metric("⭐ Puntos", st.session_state["puntos"])
    with c2: st.metric("🔥 Racha Actual", st.session_state["racha"])
    st.divider()
    
    comprobar_logros()
    modo = st.session_state["modo_seleccionado"]
    rango = st.session_state["rango_seleccionado"]
    ronda_id = st.session_state["id_ronda"]
    
    # --- MODO 1: ADIVINA NOMBRE ---
    if modo == "🏷️ Adivina Nombre":
        poke = st.session_state.get("pokemon_actual")
        if not poke:
            poke = obtener_pokemon_por_rango(rango[0], rango[1])
            st.session_state["pokemon_actual"] = poke
            
        if poke:
            st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            if poke["shiny"]:
                st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
                agregar_notificacion("✨ ¡SORPRESA! ¡Apareció un Pokémon SHINY!", "warning")
            guardar_progreso()
                
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if poke["imagen"]:
                    st.image(poke["imagen"], width=260)
                
            st.subheader("¿Cuál de estos Pokémon es el correcto?")
            
            # RENDERIZADO SECUENCIAL SIN COLUMNAS CRUZADAS (EVITA DUPLICADOS EN OBS)
            for idx, opc_nombre in enumerate(poke["opciones"]):
                if st.button(f"{opc_nombre}", use_container_width=True, key=f"btn_nombre_{ronda_id}_{idx}"):
                    if opc_nombre == poke["nombre"]:
                        st.session_state["puntos"] += 1
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto! Era {poke['nombre']}", "success")
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
        poke = st.session_state.get("pokemon_actual")
        if not poke:
            poke = obtener_pokemon_por_rango(rango[0], rango[1])
            st.session_state["pokemon_actual"] = poke
            
        if poke:
            st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            if poke["shiny"]:
                st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
                agregar_notificacion("✨ ¡SORPRESA! ¡Apareció un Pokémon SHINY!", "warning")
            guardar_progreso()
                
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2: 
                if poke["imagen"]:
                    st.image(poke["imagen"], width=260)
                
            st.subheader("¿A qué generación pertenece este Pokémon?")
            gens_permitidas = st.session_state["generaciones_permitidas"]
            
            for idx, g_num in enumerate(gens_permitidas):
                g_info = GENERACIONES[g_num]
                if st.button(f"{g_info['emoji']} Gen {g_num} ({g_info['nombre']})", use_container_width=True, key=f"btn_gen_{ronda_id}_{idx}_{g_num}"):
                    if g_num == poke["gen"]:
                        st.session_state["puntos"] += 1
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto! Gen {poke['gen']}", "success")
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

    st.divider()
    if st.button("🏠 Volver al Menú Principal", use_container_width=True, key="btn_volver_menu_activo"):
        st.session_state["en_partida"] = False
        st.session_state["derrota"] = False
        st.rerun()
