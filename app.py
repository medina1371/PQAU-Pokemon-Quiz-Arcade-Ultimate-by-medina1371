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

# --- ESTILOS CSS GLOBALES (DISEÑO MODERNO Y FLUIDO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .centered-title {
        text-align: center;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .centered-text {
        text-align: center;
        color: #555555;
        font-size: 1.05rem;
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .pokemon-card {
        background: #ffffff;
        border: 1px solid #eaeaea;
        padding: 15px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
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

# Estados para el Reto Regional
if "reto_activo" not in st.session_state: st.session_state["reto_activo"] = False
if "reto_region" not in st.session_state: st.session_state["reto_region"] = None
if "reto_adivinados" not in st.session_state: st.session_state["reto_adivinados"] = set()

def agregar_notificacion(texto, tipo="success"):
    st.session_state["ultima_notificacion"] = {"texto": texto, "tipo": tipo}

# --- SISTEMA DE LOGROS ---
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

def obtener_nombre_por_id(poke_id: int):
    res = obtener_datos_especie(poke_id)
    if res:
        return limpiar_nombre_pokemon(res["name"])
    return f"Pokémon #{poke_id}"

def obtener_pokemon_por_rango(min_id: int, max_id: int):
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
            
        img_data = requests.get(img_url, timeout=2).content
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        
        ids_erroneos = random.sample([i for i in range(min_id, max_id + 1) if i != poke_id], min(3, max_id - min_id))
        nombres_erroneos = [obtener_nombre_por_id(i) for i in ids_erroneos]
        opciones = nombres_erroneos + [nombre]
        random.shuffle(opciones)
        
        return {
            "id": poke_id, "nombre": nombre, "gen": gen,
            "tipos": tipos, "shiny": es_shiny, "imagen": pil_img, "opciones": opciones
        }
    except Exception:
        return None

def obtener_pregunta_tipos(min_id: int, max_id: int):
    intentos = 0
    while intentos < 10:
        intentos += 1
        poke_correcto = obtener_pokemon_por_rango(min_id, max_id)
        if not poke_correcto: continue
            
        tipos_correctos = poke_correcto["tipos"]
        candidatos_erroneos = []
        ids_usados = {poke_correcto["id"]}
        
        for _ in range(3):
            sub_intentos = 0
            while sub_intentos < 5:
                sub_intentos += 1
                rand_id = random.randint(min_id, max_id)
                if rand_id in ids_usados: continue
                res_p = obtener_datos_pokemon(rand_id)
                res_s = obtener_datos_especie(rand_id)
                if res_p and res_s:
                    t_cand = [t["type"]["name"] for t in res_p["types"]]
                    if t_cand != tipos_correctos:
                        ids_usados.add(rand_id)
                        candidatos_erroneos.append({
                            "id": rand_id,
                            "nombre": limpiar_nombre_pokemon(res_s["name"]),
                            "imagen": res_p["sprites"]["front_default"]
                        })
                        break
        
        if len(candidatos_erroneos) == 3:
            opciones_juego = candidatos_erroneos + [{
                "id": poke_correcto["id"], "nombre": poke_correcto["nombre"], "imagen": poke_correcto["imagen"]
            }]
            random.shuffle(opciones_juego)
            return {
                "tipos": tipos_correctos, "correcto": poke_correcto["nombre"], "opciones": opciones_juego
            }
    return None

# --- MENÚ LATERAL ---
st.sidebar.title("🧭 Menú Principal 🎒")
opcion_menu = st.sidebar.radio("Ir a:", ["🎮 Jugar Partida", "🏆 Reto Regional (Name All)", "📖 Pokédex", "✨ ShinyDex", "📊 Estadísticas y Logros", "⚙️ Ajustes"])

# --- SECCIÓN POKÉDEX ---
if opcion_menu == "📖 Pokédex":
    st.markdown("<h2 class='centered-title'>📖 Tu Pokédex Web 🌐</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='centered-text'>Pokémon registrados: <b>{len(st.session_state['pokedex_capturados'])} / 1025</b> 🎯</p>", unsafe_allow_html=True)
    
    if st.session_state["pokedex_capturados"]:
        tipo_filtro = st.radio("Filtrar:", ["🌟 Ver todos", "🔢 Filtrar por ID", "🗺️ Filtrar por Región"], horizontal=True)
        registros = st.session_state["pokedex_capturados"]
        
        if tipo_filtro == "🔢 Filtrar por ID":
            id_buscado = st.number_input("Número ID:", min_value=1, max_value=1025, value=1)
            if id_buscado in registros:
                p = registros[id_buscado]
                st.success("✅ ¡Registrado!")
                c1, c2 = st.columns([1, 3])
                with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id_buscado}.png", width=110)
                with c2: st.markdown(f"### **#{id_buscado:03d} - {p['nombre']}**\n🌍 Gen {p['gen']}")
            else:
                st.warning(f"❌ Aún no tienes el Pokémon #{id_buscado:03d}.")
                
        elif tipo_filtro == "🗺️ Filtrar por Región":
            reg = st.selectbox("Región:", list(GENERACIONES.values()), format_func=lambda x: f"{x['emoji']} {x['nombre']}")
            gen_target = [k for k, v in GENERACIONES.items() if v == reg][0]
            filtrados = [(pid, data) for pid, data in sorted(registros.items()) if data["gen"] == gen_target]
            
            st.markdown(f"### 📍 **{reg['nombre']}** ({len(filtrados)}):")
            for pid, data in filtrados:
                c1, c2 = st.columns([1, 5])
                with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=65)
                with c2: st.write(f"**#{pid:03d}** - {data['nombre']}")
                st.markdown("---")
        else:
            for pid, data in sorted(registros.items()):
                c1, c2 = st.columns([1, 5])
                with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=65)
                with c2: st.write(f"**#{pid:03d}** - {data['nombre']} (Gen {data['gen']})")
                st.markdown("---")
    else:
        st.info("💡 ¡Juega para rellenar tu Pokédex!")
    st.stop()

# --- SECCIÓN SHINYDEV ---
elif opcion_menu == "✨ ShinyDex":
    st.markdown("<h2 class='centered-title'>✨ Tu ShinyDex 🌟</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='centered-text'>Shinies capturados: <b>{len(st.session_state['shinydex_capturados'])}</b> 💎</p>", unsafe_allow_html=True)
    if st.session_state["shinydex_capturados"]:
        for pid, data in sorted(st.session_state["shinydex_capturados"].items()):
            c1, c2 = st.columns([1, 5])
            with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pid}.png", width=75)
            with c2: st.write(f"**#{pid:03d}** - {data['nombre']} ✨")
            st.markdown("---")
    else:
        st.info("🍀 Todavía no te ha salido ningún Shiny (5% de probabilidad). ¡Sigue probando!")
    st.stop()

# --- NUEVO MINIJUEGO: RETO REGIONAL (NAME ALL POKEMON) ---
elif opcion_menu == "🏆 Reto Regional (Name All)":
    st.markdown("<h2 class='centered-title'>🏆 El Reto Regional (Name All) ⏱️</h2>", unsafe_allow_html=True)
    st.markdown("<p class='centered-text'>¡Escribe los nombres de todos los Pokémon de la región elegida! Se irán descubriendo en la cuadrícula.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not st.session_state["reto_activo"]:
        reg_elegida = st.selectbox("Selecciona la región para el reto:", list(GENERACIONES.keys()), format_func=lambda x: f"{GENERACIONES[x]['emoji']} {GENERACIONES[x]['nombre']} ({GENERACIONES[x]['rango'][0]} - {GENERACIONES[x]['rango'][1]})")
        if st.button("🚀 ¡Comenzar Reto Regional!", type="primary", use_container_width=True):
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
        
        # Caja para escribir Pokémon
        nombre_input = st.text_input("Escribe el nombre de un Pokémon:", key="input_reto_poke", placeholder="Ej: Pikachu, Charizard...").strip().title()
        
        if nombre_input:
            # Buscar si coincide con alguno de la región
            encontrado_id = None
            for pid in range(rango_reg[0], rango_reg[1] + 1):
                nombre_real = obtener_nombre_por_id(pid)
                if nombre_real.lower() == nombre_input.lower():
                    encontrado_id = pid
                    break
            
            if encontrado_id and encontrado_id not in st.session_state["reto_adivinados"]:
                st.session_state["reto_adivinados"].add(encontrado_id)
                # También se añade a la Pokédex global
                st.session_state["pokedex_capturados"][encontrado_id] = {"nombre": obtener_nombre_por_id(encontrado_id), "gen": reg_id}
                guardar_progreso()
                st.success(f"🎉 ¡Correcto! Has descubierto a {obtener_nombre_por_id(encontrado_id)}")
                st.rerun()
            elif encontrado_id in st.session_state["reto_adivinados"]:
                st.warning("⚠️ ¡Ya habías adivinado ese Pokémon!")

        st.markdown("### 🎴 Cuadrícula de Descubrimientos:")
        # Mostrar grilla de la región
        cols_grilla = st.columns(5)
        for idx, pid in enumerate(range(rango_reg[0], rango_reg[1] + 1)):
            col = cols_grilla[idx % 5]
            with col:
                if pid in st.session_state["reto_adivinados"]:
                    st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=70)
                    st.caption(f"#{pid}\n{obtener_nombre_por_id(pid)}")
                else:
                    st.markdown(f"<div style='text-align:center; background:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:10px;'><b>#{pid}</b><br>❓</div>", unsafe_allow_html=True)
                    
        st.markdown("---")
        if st.button("🚪 Abandonar Reto", use_container_width=True):
            st.session_state["reto_activo"] = False
            st.session_state["reto_adivinados"].clear()
            st.rerun()
    st.stop()

# --- SECCIÓN ESTADÍSTICAS Y LOGROS ---
elif opcion_menu == "📊 Estadísticas y Logros":
    st.markdown("<h2 class='centered-title'>📊 Panel de Rendimiento 🏆</h2>", unsafe_allow_html=True)
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
        st.markdown("---")
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
    st.markdown("<h2 class='centered-title'>⚙️ Ajustes 🛠️</h2>", unsafe_allow_html=True)
    if st.button("🗑️ Borrar Todo el Progreso"):
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
    st.markdown("<h2 class='centered-title'>💥 ¡Has Caído! 💀</h2>", unsafe_allow_html=True)
    st.error("¡Te equivocaste de respuesta!")
    
    if st.session_state["ultimo_pokemon_fallado"]:
        pf = st.session_state["ultimo_pokemon_fallado"]
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(pf["imagen"], width=220)
            st.markdown(f"<h3 class='centered-title'>Era: #{pf['id']:03d} - {pf['nombre']}</h3>", unsafe_allow_html=True)
            
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Reintentar", type="primary", use_container_width=True):
            st.session_state["derrota"] = False
            st.session_state["puntos"] = 0
            st.session_state["racha"] = 0
            st.session_state["vistos_partida"].clear()
            rango = st.session_state["rango_seleccionado"]
            st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
            st.rerun()
    with c2:
        if st.button("🏠 Menú Principal", use_container_width=True):
            st.session_state["derrota"] = False
            st.session_state["en_partida"] = False
            st.rerun()
    st.stop()

# --- MENÚ INICIAL DE PARTIDA ---
if not st.session_state["en_partida"]:
    st.markdown("<h1 class='centered-title'>🎮 Pokémon Quiz Arcade Ultimate ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p class='centered-text'>✨ <em>¡Pon a prueba tus conocimientos Pokémon al máximo nivel!</em> ✨</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    filtro_gen = st.radio("🌍 1. Selecciona el filtro de generaciones:", ["🌟 Todas (Gen 1-9)", "🔴 Clásicas (Gen 1 - 3)", "💎 Intermedias (Gen 4 - 6)", "⚔️ Recientes (Gen 7 - 9)"])
    modo_juego = st.radio("🎯 2. Elige el modo de juego:", ["🏷️ Adivina Nombre", "🌍 Adivina Generación", "🧪 Adivina por Tipos"])
    
    if st.button("🚀 ¡Comenzar Partida Ya!", type="primary", use_container_width=True):
        st.session_state["en_partida"] = True
        st.session_state["puntos"] = 0
        st.session_state["racha"] = 0
        st.session_state["vistos_partida"].clear()
        st.session_state["modo_seleccionado"] = modo_juego
        
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
        if modo_juego == "🧪 Adivina por Tipos":
            st.session_state["pregunta_tipos"] = obtener_pregunta_tipos(rango[0], rango[1])
        else:
            st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
        st.rerun()

else:
    # --- PARTIDA ACTIVA ---
    st.markdown("<h2 class='centered-title'>🎯 Partida en Curso 🕹️</h2>", unsafe_allow_html=True)
    
    if st.session_state["ultima_notificacion"]:
        msg = st.session_state["ultima_notificacion"]
        if msg["tipo"] == "success": st.success(msg["texto"], icon="🎉")
        elif msg["tipo"] == "warning": st.warning(msg["texto"], icon="✨")
        else: st.error(msg["texto"], icon="💥")
    
    c1, c2 = st.columns(2)
    with c1: st.metric("⭐ Puntos", st.session_state["puntos"])
    with c2: st.metric("🔥 Racha Actual", st.session_state["racha"])
    st.markdown("---")
    
    comprobar_logros()
    modo = st.session_state["modo_seleccionado"]
    rango = st.session_state["rango_seleccionado"]
    
    # --- MODO 1: ADIVINA NOMBRE (ICONOS GRANDES Y VISIBLES) ---
    if modo == "🏷️ Adivina Nombre":
        poke = st.session_state.get("pokemon_actual")
        if poke:
            st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            if poke["shiny"]:
                st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
                agregar_notificacion("✨ ¡SORPRESA! ¡Apareció un Pokémon SHINY!", "warning")
            guardar_progreso()
                
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                # Icono optimizado y más grande
                st.image(poke["imagen"], width=260)
                
            st.markdown("<h4 class='centered-title'>¿Cuál de estos Pokémon es el correcto?</h4>", unsafe_allow_html=True)
            cols_opc1 = st.columns(2)
            cols_opc2 = st.columns(2)
            
            for idx, opc_nombre in enumerate(poke["opciones"]):
                col_actual = cols_opc1[0] if idx == 0 else (cols_opc1[1] if idx == 1 else (cols_opc2[0] if idx == 2 else cols_opc2[1]))
                with col_actual:
                    if st.button(f"🔸 {opc_nombre}", use_container_width=True, key=f"btn_opc_{idx}"):
                        if opc_nombre == poke["nombre"]:
                            st.session_state["puntos"] += 1
                            st.session_state["racha"] += 1
                            st.session_state["aciertos_totales"] += 1
                            if st.session_state["racha"] > st.session_state["racha_maxima"]:
                                st.session_state["racha_maxima"] = st.session_state["racha"]
                            guardar_progreso()
                            agregar_notificacion(f"¡Correcto! Era {poke['nombre']}", "success")
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
        if poke:
            st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            if poke["shiny"]:
                st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
                agregar_notificacion("✨ ¡SORPRESA! ¡Apareció un Pokémon SHINY!", "warning")
            guardar_progreso()
                
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2: st.image(poke["imagen"], width=260)
                
            st.markdown("<h4 class='centered-title'>¿A qué generación pertenece este Pokémon?</h4>", unsafe_allow_html=True)
            gens_permitidas = st.session_state["generaciones_permitidas"]
            filas_gens = [gens_permitidas[i:i + 3] for i in range(0, len(gens_permitidas), 3)]
            
            for fila in filas_gens:
                cols_fila = st.columns(len(fila))
                for idx, g_num in enumerate(fila):
                    g_info = GENERACIONES[g_num]
                    with cols_fila[idx]:
                        if st.button(f"{g_info['emoji']} Gen {g_num}\n{g_info['nombre']}", use_container_width=True, key=f"btn_gen_{g_num}"):
                            if g_num == poke["gen"]:
                                st.session_state["puntos"] += 1
                                st.session_state["racha"] += 1
                                st.session_state["aciertos_totales"] += 1
                                if st.session_state["racha"] > st.session_state["racha_maxima"]:
                                    st.session_state["racha_maxima"] = st.session_state["racha"]
                                guardar_progreso()
                                agregar_notificacion(f"¡Correcto! Gen {poke['gen']}", "success")
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

    # --- MODO 3: ADIVINA POR TIPOS ---
    elif modo == "🧪 Adivina por Tipos":
        pregunta = st.session_state.get("pregunta_tipos")
        if pregunta:
            tipos_espanol = [TRADUCCION_TIPOS.get(t, t.title()) for t in pregunta["tipos"]]
            texto_tipos = " / ".join(tipos_espanol)
            
            st.markdown(f"<h3 class='centered-title'>🧪 ¿Cuál tiene el tipo: <b>{texto_tipos}</b>?</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            cols_t1 = st.columns(2)
            cols_t2 = st.columns(2)
            
            for idx, opc in enumerate(pregunta["opciones"]):
                col_actual = cols_t1[0] if idx == 0 else (cols_t1[1] if idx == 1 else (cols_t2[0] if idx == 2 else cols_t2[1]))
                with col_actual:
                    img_mini = opc["imagen"] if isinstance(opc["imagen"], Image.Image) else Image.open(io.BytesIO(requests.get(opc["imagen"]).content))
                    st.image(img_mini, width=130)
                    if st.button(f"🔸 {opc['nombre']}", use_container_width=True, key=f"btn_tipo_{idx}"):
                        if opc["nombre"] == pregunta["correcto"]:
                            st.session_state["puntos"] += 1
                            st.session_state["racha"] += 1
                            st.session_state["aciertos_totales"] += 1
                            if st.session_state["racha"] > st.session_state["racha_maxima"]:
                                st.session_state["racha_maxima"] = st.session_state["racha"]
                            guardar_progreso()
                            agregar_notificacion(f"¡Correcto! {pregunta['correcto']}", "success")
                            st.session_state["pregunta_tipos"] = obtener_pregunta_tipos(rango[0], rango[1])
                            st.rerun()
                        else:
                            st.session_state["fallos_totales"] += 1
                            st.session_state["partidas_perdidas"] += 1
                            guardar_progreso()
                            res_fail = obtener_datos_pokemon(opc["id"])
                            pil_fail = Image.open(io.BytesIO(requests.get(res_fail["sprites"]["front_default"]).content)).convert("RGBA") if res_fail else None
                            st.session_state["ultimo_pokemon_fallado"] = {"id": opc["id"], "nombre": opc["nombre"], "imagen": pil_fail, "gen": 1}
                            agregar_notificacion("¡Fallaste!", "error")
                            st.session_state["derrota"] = True
                            st.rerun()

    st.markdown("---")
    if st.button("🏠 Volver al Menú Principal", use_container_width=True):
        st.session_state["en_partida"] = False
        st.session_state["derrota"] = False
        st.rerun()
