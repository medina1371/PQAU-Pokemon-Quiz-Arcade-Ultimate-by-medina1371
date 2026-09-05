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

# --- ESTILOS CSS GLOBALES PARA CENTRADO PERFECTO ---
st.markdown("""
    <style>
    .centered-title {
        text-align: center;
    }
    .centered-text {
        text-align: center;
        color: gray;
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE PERSISTENCIA (GUARDADO LOCAL EN JSON) ---
ARCHIVO_GUARDADO = "pokedex_save.json"

def cargar_progreso():
    if os.path.exists(ARCHIVO_GUARDADO):
        try:
            with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as f:
                datos = json.load(f)
                pokedex = {int(k): v for k, v in datos.get("pokedex", {}).items()}
                shinydex = {int(k): v for k, v in datos.get("shinydex", {}).items()}
                racha_max = datos.get("racha_maxima", 0)
                return pokedex, shinydex, racha_max
        except:
            pass
    return {}, {}, 0

def guardar_progreso():
    datos = {
        "pokedex": st.session_state["pokedex_capturados"],
        "shinydex": st.session_state["shinydex_capturados"],
        "racha_maxima": st.session_state["racha_maxima"]
    }
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except:
        pass

# Inicializar Base de Datos Local en la sesión cargando del archivo
if "pokedex_capturados" not in st.session_state:
    pokedex_ini, shinydex_ini, racha_max_ini = cargar_progreso()
    st.session_state["pokedex_capturados"] = pokedex_ini
    st.session_state["shinydex_capturados"] = shinydex_ini
    st.session_state["racha_maxima"] = racha_max_ini

if "racha" not in st.session_state:
    st.session_state["racha"] = 0
if "puntos" not in st.session_state:
    st.session_state["puntos"] = 0
if "derrota" not in st.session_state:
    st.session_state["derrota"] = False
if "ultimo_pokemon_fallado" not in st.session_state:
    st.session_state["ultimo_pokemon_fallado"] = None
if "en_partida" not in st.session_state:
    st.session_state["en_partida"] = False
if "modo_seleccionado" not in st.session_state:
    st.session_state["modo_seleccionado"] = "🏷️ Adivina Nombre"
if "rango_seleccionado" not in st.session_state:
    st.session_state["rango_seleccionado"] = (1, 1025)
if "generaciones_permitidas" not in st.session_state:
    st.session_state["generaciones_permitidas"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Notificación única en pantalla (máximo 1)
if "ultima_notificacion" not in st.session_state:
    st.session_state["ultima_notificacion"] = None

def agregar_notificacion(texto, tipo="success"):
    st.session_state["ultima_notificacion"] = {"texto": texto, "tipo": tipo}

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

@st.cache_data(ttl=3600)
def obtener_datos_especie(poke_id: int):
    try:
        return requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/", timeout=3).json()
    except:
        return None

@st.cache_data(ttl=3600)
def obtener_datos_pokemon(poke_id: int):
    try:
        return requests.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}/", timeout=3).json()
    except:
        return None

def obtener_nombre_por_id(poke_id: int):
    res = obtener_datos_especie(poke_id)
    if res:
        return limpiar_nombre_pokemon(res["name"])
    return f"Pokémon #{poke_id}"

def obtener_pokemon_por_rango(min_id: int, max_id: int):
    poke_id = random.randint(min_id, max_id)
    try:
        res_species = obtener_datos_especie(poke_id)
        res_poke = obtener_datos_pokemon(poke_id)
        
        if not res_species or not res_poke:
            return None
            
        nombre = limpiar_nombre_pokemon(res_species["name"])
        gen = int(res_species["generation"]["url"].split("/")[-2])
        tipos = [t["type"]["name"] for t in res_poke["types"]]
        
        es_shiny = random.random() < 0.05
        img_url = res_poke["sprites"]["front_shiny"] if es_shiny else res_poke["sprites"]["front_default"]
        if not img_url:
            img_url = res_poke["sprites"]["front_default"]
            es_shiny = False
            
        img_data = requests.get(img_url).content
        pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        
        ids_erroneos = random.sample([i for i in range(min_id, max_id + 1) if i != poke_id], min(3, max_id - min_id))
        nombres_erroneos = [obtener_nombre_por_id(i) for i in ids_erroneos]
        
        opciones = nombres_erroneos + [nombre]
        random.shuffle(opciones)
        
        return {
            "id": poke_id,
            "nombre": nombre,
            "gen": gen,
            "tipos": tipos,
            "shiny": es_shiny,
            "imagen": pil_img,
            "opciones": opciones
        }
    except Exception:
        return None

# --- MENÚ LATERAL ---
st.sidebar.title("🧭 Menú Principal 🎒")
opcion_menu = st.sidebar.radio("Ir a:", ["🎮 Jugar Partida", "📖 Pokédex", "✨ ShinyDex", "⚙️ Ajustes"])

# --- SECCIÓN POKÉDEX CON ICONOS Y FILTROS ---
if opcion_menu == "📖 Pokédex":
    st.markdown("<h2 class='centered-title'>📖 Tu Pokédex Web 🌐</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='centered-text'>Pokémon registrados en total: <b>{len(st.session_state['pokedex_capturados'])} / 1025</b> 🎯</p>", unsafe_allow_html=True)
    
    if st.session_state["pokedex_capturados"]:
        st.markdown("### 🔍 Filtrar Pokédex")
        
        tipo_filtro = st.radio(
            "¿Cómo quieres filtrar tu Pokédex?",
            ["🌟 Ver todos", "🔢 Filtrar por Número ID", "🗺️ Filtrar por Región"],
            horizontal=True
        )
        
        registros = st.session_state["pokedex_capturados"]
        
        if tipo_filtro == "🔢 Filtrar por Número ID":
            id_buscado = st.number_input("Introduce el número ID del Pokémon:", min_value=1, max_value=1025, value=1, step=1)
            if id_buscado in registros:
                p = registros[id_buscado]
                st.success(f"✅ ¡Capturado!")
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id_buscado}.png", width=90)
                with c2:
                    st.markdown(f"### **#{id_buscado:03d} - {p['nombre']}**")
                    st.write(f"🌍 Generación: {p['gen']}")
            else:
                st.warning(f"❌ Todavía no has registrado el Pokémon con ID #{id_buscado:03d}.")
                
        elif tipo_filtro == "🗺️ Filtrar por Región":
            region_elegida = st.selectbox(
                "Selecciona la región:",
                ["Kanto", "Johto", "Hoenn", "Sinnoh", "Teselia / Unova", "Kalos", "Alola", "Galar", "Paldea"]
            )
            
            gen_map = {"Kanto": 1, "Johto": 2, "Hoenn": 3, "Sinnoh": 4, "Teselia / Unova": 5, "Kalos": 6, "Alola": 7, "Galar": 8, "Paldea": 9}
            gen_target = gen_map[region_elegida]
            
            filtrados = [(pid, data) for pid, data in sorted(registros.items()) if data["gen"] == gen_target]
            
            st.markdown(f"### 📍 Pokémon de **{region_elegida}** registrados ({len(filtrados)}):")
            if filtrados:
                for pid, data in filtrados:
                    col_i1, col_i2 = st.columns([1, 5])
                    with col_i1:
                        st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=55)
                    with col_i2:
                        st.write(f"**#{pid:03d}** - {data['nombre']}")
                    st.markdown("---")
            else:
                st.info(f"Aún no tienes ningún Pokémon registrado de {region_elegida}.")
                
        else:
            st.markdown("### 📋 Lista completa de descubrimientos:")
            for pid, data in sorted(registros.items()):
                col_i1, col_i2 = st.columns([1, 5])
                with col_i1:
                    st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=55)
                with col_i2:
                    st.write(f"**#{pid:03d}** - {data['nombre']} (Gen {data['gen']})")
                st.markdown("---")
                
    else:
        st.info("💡 ¡Aún no has descubierto ningún Pokémon! Entra a jugar para rellenar tu Pokédex.")
    st.stop()

elif opcion_menu == "✨ ShinyDex":
    st.markdown("<h2 class='centered-title'>✨ Tu ShinyDex Web 🌟</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='centered-text'>Shinies capturados: <b>{len(st.session_state['shinydex_capturados'])}</b> 💎</p>", unsafe_allow_html=True)
    if st.session_state["shinydex_capturados"]:
        st.success("🎉 ¡Increíble! Has atrapado estos ejemplares variocolor:")
        for pid, data in sorted(st.session_state["shinydex_capturados"].items()):
            col_s1, col_s2 = st.columns([1, 5])
            with col_s1:
                st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pid}.png", width=65)
            with col_s2:
                st.write(f"**#{pid:03d}** - {data['nombre']} ✨")
            st.markdown("---")
    else:
        st.info("🍀 Todavía no te ha salido ningún Shiny (tienen un 5% de probabilidad al aparecer). ¡Sigue probando suerte!")
    st.stop()

elif opcion_menu == "⚙️ Ajustes":
    st.markdown("<h2 class='centered-title'>⚙️ Ajustes del Juego 🛠️</h2>", unsafe_allow_html=True)
    st.markdown("<p class='centered-text'>Personaliza o limpia los datos guardados en tu sesión.</p>", unsafe_allow_html=True)
    if st.button("🗑️ Borrar Progreso (Pokédex / ShinyDex)"):
        st.session_state["pokedex_capturados"].clear()
        st.session_state["shinydex_capturados"].clear()
        st.session_state["racha_maxima"] = 0
        st.session_state["ultima_notificacion"] = None
        if os.path.exists(ARCHIVO_GUARDADO):
            os.remove(ARCHIVO_GUARDADO)
        st.success("✅ ¡Progreso reiniciado con éxito y archivo local eliminado!")
    st.stop()

# --- PANTALLA DE DERROTA ---
if st.session_state["derrota"]:
    st.markdown("<h2 class='centered-title'>💥 ¡Has Caído en Combate! 💀</h2>", unsafe_allow_html=True)
    st.error("¡Te equivocaste de respuesta y la partida ha terminado!")
    
    if st.session_state["ultimo_pokemon_fallado"]:
        poke_fail = st.session_state["ultimo_pokemon_fallado"]
        
        col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
        with col_f2:
            st.image(poke_fail["imagen"], width=200)
            st.markdown(f"<h3 class='centered-title'>Era: #{poke_fail['id']:03d} - {poke_fail['nombre']} (Gen {poke_fail['gen']})</h3>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3 class='centered-title'>📊 Estadísticas finales de tu partida:</h3>", unsafe_allow_html=True)
    st.metric(label="⭐ Puntos Totales", value=st.session_state["puntos"])
    st.metric(label="🔥 Racha Máxima", value=st.session_state["racha_maxima"])
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🔄 Volver al Intentarlo", type="primary", use_container_width=True):
            st.session_state["derrota"] = False
            st.session_state["puntos"] = 0
            st.session_state["racha"] = 0
            st.session_state["ultima_notificacion"] = None
            rango = st.session_state["rango_seleccionado"]
            st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
            st.rerun()
    with col_d2:
        if st.button("🏠 Menú Principal", use_container_width=True):
            st.session_state["derrota"] = False
            st.session_state["en_partida"] = False
            st.session_state["ultima_notificacion"] = None
            st.rerun()
    st.stop()

# --- MENÚ INICIAL ---
if not st.session_state["en_partida"]:
    st.markdown("<h1 class='centered-title'>🎮 Pokémon Quiz Arcade Ultimate ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p class='centered-text'>✨ <em>¡Diviértete con tus amigos en el navegador sin descargar nada!</em> ✨</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    filtro_gen = st.radio(
        "🌍 1. Selecciona el filtro de generaciones:",
        ["🌟 Todas (Gen 1-9)", "🔴 Clásicas (Gen 1 - 3)", "💎 Intermedias (Gen 4 - 6)", "⚔️ Recientes (Gen 7 - 9)"]
    )
    
    modo_juego = st.radio(
        "🎯 2. Elige el modo de juego:",
        ["🏷️ Adivina Nombre", "🌍 Adivina Generación"]
    )
    
    if st.button("🚀 ¡Comenzar Partida Ya!", type="primary", use_container_width=True):
        st.session_state["en_partida"] = True
        st.session_state["puntos"] = 0
        st.session_state["racha"] = 0
        st.session_state["ultima_notificacion"] = None
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
        st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
        st.rerun()

else:
    # --- PARTIDA ACTIVA ---
    st.markdown("<h2 class='centered-title'>🎯 Partida en Curso 🕹️</h2>", unsafe_allow_html=True)
    
    # Mostrar única notificación activa (máximo 1 en pantalla, reemplazándose al instante)
    if st.session_state["ultima_notificacion"]:
        msg = st.session_state["ultima_notificacion"]
        if msg["tipo"] == "success":
            st.success(msg["texto"], icon="🎉")
        elif msg["tipo"] == "warning":
            st.warning(msg["texto"], icon="✨")
        else:
            st.error(msg["texto"], icon="💥")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="⭐ Puntos", value=st.session_state["puntos"])
    with col_m2:
        st.metric(label="🔥 Racha Actual", value=st.session_state["racha"])
    
    st.markdown("---")
    
    poke = st.session_state["pokemon_actual"]
    
    if poke:
        st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
        if poke["shiny"]:
            st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
            agregar_notificacion("✨ ¡SORPRESA! ¡Apareció un Pokémon SHINY!", "warning")
            
        guardar_progreso()
            
        col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
        with col_img2:
            st.image(poke["imagen"], width=240)
            
        modo = st.session_state["modo_seleccionado"]
        
        # --- MODO 1: ADIVINA NOMBRE ---
        if modo == "🏷️ Adivina Nombre":
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
                            if st.session_state["racha"] > st.session_state["racha_maxima"]:
                                st.session_state["racha_maxima"] = st.session_state["racha"]
                                guardar_progreso()
                            
                            agregar_notificacion(f"¡Correcto! Era {poke['nombre']}", "success")
                            rango = st.session_state["rango_seleccionado"]
                            st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
                            st.rerun()
                        else:
                            agregar_notificacion("¡Fallaste! Fin de la partida.", "error")
                            st.session_state["ultimo_pokemon_fallado"] = poke
                            st.session_state["derrota"] = True
                            st.rerun()

        # --- MODO 2: ADIVINA GENERACIÓN ---
        elif modo == "🌍 Adivina Generación":
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
                                if st.session_state["racha"] > st.session_state["racha_maxima"]:
                                    st.session_state["racha_maxima"] = st.session_state["racha"]
                                    guardar_progreso()
                                
                                agregar_notificacion(f"¡Correcto! Era de la Gen {poke['gen']}", "success")
                                rango = st.session_state["rango_seleccionado"]
                                st.session_state["pokemon_actual"] = obtener_pokemon_por_rango(rango[0], rango[1])
                                st.rerun()
                            else:
                                agregar_notificacion("¡Fallaste! Fin de la partida.", "error")
                                st.session_state["ultimo_pokemon_fallado"] = poke
                                st.session_state["derrota"] = True
                                st.rerun()

    st.markdown("---")
    if st.button("🏠 Volver al Menú Principal", use_container_width=True):
        st.session_state["en_partida"] = False
        st.session_state["derrota"] = False
        st.session_state["ultima_notificacion"] = None
        st.rerun()