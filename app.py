import uuid
import random
import requests
import streamlit as st
from PIL import Image, ImageOps
import io
import json
import os
import datetime
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Pokémon Quiz Arcade Ultimate ⚡",
    page_icon="🎮",
    layout="centered"
)

# --- ESTILOS CSS OPTIMIZADOS ---
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
        font-size: 15px !important;
        padding: 10px 18px !important;
        width: 100% !important;
        margin-bottom: 8px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
    }
    .perfil-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2b32b2 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        margin-bottom: 25px;
        border: 2px solid #ffcc00;
    }
    .minigame-card {
        background: #1e1e2f;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 2px solid #4a4e69;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .minigame-card:hover {
        border-color: #ffcc00;
    }
    .shop-card {
        background: #1e1e2f;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        border: 2px solid #4a4e69;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .card-tcg {
        background: #1a1a2e;
        border-radius: 14px;
        padding: 15px;
        text-align: center;
        border: 2px solid #e94560;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE USUARIO ÚNICO ---
if "user_id" not in st.query_params:
    st.query_params["user_id"] = str(uuid.uuid4())[:8]

USER_ID = st.query_params["user_id"]
ARCHIVO_GUARDADO = f"pokedex_save_{USER_ID}.json"

# --- PERSISTENCIA (JSON LOCAL) ---
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
                monedas = datos.get("monedas", 10)  # Ajustado a 10 iniciales
                entrenador_actual = datos.get("entrenador_actual", "Rojo")
                entrenadores_desbloqueados = datos.get("entrenadores_desbloqueados", ["Rojo"])
                huevos = datos.get("huevos", [])
                cartas_coleccion = datos.get("cartas_coleccion", [])
                companero_id = datos.get("companero_id", 25)
                companero_shiny = datos.get("companero_shiny", False)
                titulo_elegido = datos.get("titulo_elegido", "")
                historia_progreso = datos.get("historia_progreso", 1)
                misiones_diarias = datos.get("misiones_diarias", {})
                ultima_fecha_misiones = datos.get("ultima_fecha_misiones", "")
                return pokedex, shinydex, racha_max, logros, aciertos, fallos, monedas, entrenador_actual, entrenadores_desbloqueados, huevos, cartas_coleccion, companero_id, companero_shiny, titulo_elegido, historia_progreso, misiones_diarias, ultima_fecha_misiones
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return {}, {}, 0, {}, 0, 0, 10, "Rojo", ["Rojo"], [], [], 25, False, "", 1, {}, ""

def guardar_progreso():
    datos = {
        "pokedex": st.session_state["pokedex_capturados"],
        "shinydex": st.session_state["shinydex_capturados"],
        "racha_maxima": st.session_state["racha_maxima"],
        "logros": st.session_state["logros"],
        "aciertos_totales": st.session_state["aciertos_totales"],
        "fallos_totales": st.session_state["fallos_totales"],
        "monedas": st.session_state["monedas"],
        "entrenador_actual": st.session_state["entrenador_actual"],
        "entrenadores_desbloqueados": st.session_state["entrenadores_desbloqueados"],
        "huevos": st.session_state["huevos"],
        "cartas_coleccion": st.session_state["cartas_coleccion"],
        "companero_id": st.session_state["companero_id"],
        "companero_shiny": st.session_state["companero_shiny"],
        "titulo_elegido": st.session_state["titulo_elegido"],
        "historia_progreso": st.session_state["historia_progreso"],
        "misiones_diarias": st.session_state["misiones_diarias"],
        "ultima_fecha_misiones": st.session_state["ultima_fecha_misiones"]
    }
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except (OSError, TypeError, ValueError):
        pass

if "pokedex_capturados" not in st.session_state:
    p_ini, s_ini, rm_ini, l_ini, ac_ini, fa_ini, mon_ini, ent_ini, ents_ini, hue_ini, car_ini, comp_id_ini, comp_sh_ini, tit_ini, hist_ini, mis_ini, f_mis_ini = cargar_progreso()
    st.session_state["pokedex_capturados"] = p_ini
    st.session_state["shinydex_capturados"] = s_ini
    st.session_state["racha_maxima"] = rm_ini
    st.session_state["logros"] = l_ini
    st.session_state["aciertos_totales"] = ac_ini
    st.session_state["fallos_totales"] = fa_ini
    st.session_state["monedas"] = mon_ini
    st.session_state["entrenador_actual"] = ent_ini
    st.session_state["entrenadores_desbloqueados"] = ents_ini
    st.session_state["huevos"] = hue_ini
    st.session_state["cartas_coleccion"] = car_ini
    st.session_state["companero_id"] = comp_id_ini
    st.session_state["companero_shiny"] = comp_sh_ini
    st.session_state["titulo_elegido"] = tit_ini
    st.session_state["historia_progreso"] = hist_ini
    st.session_state["misiones_diarias"] = mis_ini
    st.session_state["ultima_fecha_misiones"] = f_mis_ini

if "racha" not in st.session_state: st.session_state["racha"] = 0
if "puntos" not in st.session_state: st.session_state["puntos"] = 0
if "derrota" not in st.session_state: st.session_state["derrota"] = False
if "ultimo_pokemon_fallado" not in st.session_state: st.session_state["ultimo_pokemon_fallado"] = None
if "en_partida" not in st.session_state: st.session_state["en_partida"] = False
if "modo_juego" not in st.session_state: st.session_state["modo_juego"] = None
if "rango_gens" not in st.session_state: st.session_state["rango_gens"] = (1, 151)
if "vistos_partida" not in st.session_state: st.session_state["vistos_partida"] = set()
if "ultima_notificacion" not in st.session_state: st.session_state["ultima_notificacion"] = None
if "carta_recien_abierta" not in st.session_state: st.session_state["carta_recien_abierta"] = None
if "mostrar_consola_trucos" not in st.session_state: st.session_state["mostrar_consola_trucos"] = False
if "en_historia" not in st.session_state: st.session_state["en_historia"] = False
if "historia_vidas" not in st.session_state: st.session_state["historia_vidas"] = 3

# --- GESTIÓN DE MISIONES DIARIAS ---
hoy_str = str(datetime.date.today())
if st.session_state["ultima_fecha_misiones"] != hoy_str:
    st.session_state["ultima_fecha_misiones"] = hoy_str
    st.session_state["misiones_diarias"] = {
        "aciertos_5": {"desc": "Consigue 5 aciertos en cualquier modo", "meta": 5, "actual": 0, "completada": False, "recompensa": 50},
        "modo_sombra": {"desc": "Juega 1 partida de Silueta", "meta": 1, "actual": 0, "completada": False, "recompensa": 40}
    }
    guardar_progreso()

# --- DETECTOR DE TECLA "Q" INVISIBLE ---
components.html("""
<script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'q' || e.key === 'Q') {
            if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
            const btn = parent.document.getElementById('hidden_trigger_btn');
            if (btn) { btn.click(); }
        }
    });
</script>
""", height=0)

st.markdown("""
<style>
    div[data-testid="stHorizontalBlock"] > div:has(#hidden_trigger_btn) {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

if st.button("TrigQ", key="hidden_trigger_btn"):
    st.session_state["mostrar_consola_trucos"] = not st.session_state["mostrar_consola_trucos"]
    st.rerun()

# --- ENTRENADORES AMPLIADOS ---
ENTRENADORES = {
    "Rojo": {"nombre": "Rojo", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/red.png", "costo": 0, "descripcion": "El campeón silencioso de Kanto.", "trait": "Gratis - Ganancia estándar", "bonus_monedas": 0},
    "Brock": {"nombre": "Brock", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/brock.png", "costo": 80, "descripcion": "Líder de Ciudad Plateada.", "trait": "+1 Poké-Coin extra por acierto", "bonus_monedas": 1},
    "Misty": {"nombre": "Misty", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/misty.png", "costo": 120, "descripcion": "La sirena juguetona de Celeste.", "trait": "+2 Poké-Coins extra por acierto", "bonus_monedas": 2},
    "Lt. Surge": {"nombre": "Lt. Surge", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/ltsurge.png", "costo": 180, "descripcion": "El americano rayo.", "trait": "+2 Poké-Coins extra por acierto", "bonus_monedas": 2},
    "Erika": {"nombre": "Erika", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/erika.png", "costo": 220, "descripcion": "La princesa amante de las plantas.", "trait": "+3 Poké-Coins extra por acierto", "bonus_monedas": 3},
    "Azul": {"nombre": "Azul", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/blue.png", "costo": 300, "descripcion": "El rival definitivo.", "trait": "+3 Poké-Coins extra por acierto", "bonus_monedas": 3},
    "Cintia": {"nombre": "Cintia", "avatar_url": "https://play.pokemonshowdown.com/sprites/trainers/cynthia.png", "costo": 500, "descripcion": "La campeona legendaria de Sinnoh.", "trait": "+5 Poké-Coins extra por acierto", "bonus_monedas": 5}
}

RANGOS_GENERACIONES = {
    "Clásicas (Gen 1-3)": (1, 386),
    "Intermedias (Gen 4-6)": (387, 721),
    "Avanzadas (Gen 7-9)": (722, 1025),
    "Todas las Generaciones (1-9)": (1, 1025)
}

# --- GIMNASIOS DEL MODO HISTORIA ---
GIMNASIOS_HISTORIA = [
    {"id": 1, "nombre": "Gimnasio Ciudad Plateada", "lider": "Brock", "avatar": "https://play.pokemonshowdown.com/sprites/trainers/brock.png", "recompensa": 100},
    {"id": 2, "nombre": "Gimnasio Ciudad Celeste", "lider": "Misty", "avatar": "https://play.pokemonshowdown.com/sprites/trainers/misty.png", "recompensa": 150},
    {"id": 3, "nombre": "Gimnasio Ciudad Carmín", "lider": "Lt. Surge", "avatar": "https://play.pokemonshowdown.com/sprites/trainers/ltsurge.png", "recompensa": 200},
    {"id": 4, "nombre": "Gimnasio Ciudad Azuliza / Celestic", "lider": "Erika", "avatar": "https://play.pokemonshowdown.com/sprites/trainers/erika.png", "recompensa": 250},
    {"id": 5, "nombre": "Liga Pokémon - Campeón", "lider": "Cintia", "avatar": "https://play.pokemonshowdown.com/sprites/trainers/cynthia.png", "recompensa": 500}
]

def agregar_notificacion(texto, tipo="success"):
    st.session_state["ultima_notificacion"] = {"texto": texto, "tipo": tipo}

def obtener_titulo_entrenador():
    if st.session_state.get("titulo_elegido"):
        return st.session_state["titulo_elegido"]
    pokedex_len = len(st.session_state["pokedex_capturados"])
    racha_max = st.session_state["racha_maxima"]
    if racha_max >= 20 or pokedex_len >= 500: return "👑 Campeón Indiscutible"
    elif pokedex_len >= 100 or racha_max >= 15: return "⚡ Maestro Pokémon"
    elif pokedex_len >= 50 or racha_max >= 10: return "📘 Coleccionista Experto"
    else: return "🌱 Novato de Pueblo Paleta"

LOGROS_DEF = {
    "primer_paso": {"titulo": "🌱 Primeros Pasos", "desc": "Registra tu primer Pokémon en la Pokédex.", "condicion": lambda: len(st.session_state["pokedex_capturados"]) >= 1},
    "suerte_shiny": {"titulo": "✨ ¡Suerte Variocolor!", "desc": "Encuentra y atrapa tu primer Pokémon Shiny.", "condicion": lambda: len(st.session_state["shinydex_capturados"]) >= 1},
    "huevo_eclosionado": {"titulo": "🥚 Padre Pokémon", "desc": "Eclosiona tu primer Huevo Pokémon en la guardería.", "condicion": lambda: any(h.get("eclosionado") for h in st.session_state["huevos"])},
    "coleccionista_tcg": {"titulo": "🎴 Coleccionista de TCG", "desc": "Obtén al menos 3 cartas en tu álbum TCG.", "condicion": lambda: len(st.session_state["cartas_coleccion"]) >= 3}
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
            except (KeyError, TypeError, ValueError):
                pass

def avanzar_huevos():
    for h in st.session_state["huevos"]:
        if not h.get("eclosionado", False):
            h["pasos_actuales"] += 1
            if h["pasos_actuales"] >= h["pasos_necesarios"]:
                h["eclosionado"] = True
                poke_id = random.randint(1, 1025)
                h["pokemon_id"] = poke_id
                es_shiny = random.random() < h["prob_shiny"]
                h["es_shiny"] = es_shiny
                
                res_spec = obtener_datos_especie(poke_id)
                nombre_poke = limpiar_nombre_pokemon(res_spec["name"]) if res_spec else f"Pokémon #{poke_id}"
                gen_poke = int(res_spec["generation"]["url"].split("/")[-2]) if res_spec else 1
                h["nombre_poke"] = nombre_poke
                
                st.session_state["pokedex_capturados"][poke_id] = {"nombre": nombre_poke, "gen": gen_poke}
                if es_shiny:
                    st.session_state["shinydex_capturados"][poke_id] = {"nombre": nombre_poke, "gen": gen_poke}
                guardar_progreso()
                agregar_notificacion(f"🐣 ¡Un Huevo ha eclosionado y nació {nombre_poke}{' ✨SHINY✨' if es_shiny else ''}!", "success")

def limpiar_nombre_pokemon(nombre_api: str) -> str:
    return nombre_api.replace("-", " ").title()

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_especie(poke_id: int):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}/", timeout=4)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_pokemon(poke_id: int):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}/", timeout=4)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def descargar_imagen_bytes(url: str):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=4)
        r.raise_for_status()
        return r.content
    except requests.RequestException:
        return None

def obtener_nombre_por_id(poke_id: int):
    res = obtener_datos_especie(poke_id)
    return limpiar_nombre_pokemon(res["name"]) if res else f"Pokémon #{poke_id}"

def _obtener_imagen_pokemon(res_poke, es_shiny=False):
    if not res_poke:
        return None
    sprites = res_poke.get("sprites", {})
    img_url = sprites.get("front_shiny") if es_shiny else sprites.get("front_default")
    if not img_url:
        img_url = sprites.get("front_default")
    img_data = descargar_imagen_bytes(img_url)
    if not img_data:
        return None
    try:
        return Image.open(io.BytesIO(img_data)).convert("RGBA")
    except (OSError, ValueError):
        return None

def _crear_opciones_nombres(min_id, max_id, poke_id, nombre_correcto, cantidad=4):
    datos_correctos = obtener_datos_pokemon(poke_id)
    imagen_correcta = (
        datos_correctos.get("sprites", {}).get("front_default")
        if datos_correctos else None
    )
    if not imagen_correcta:
        return None

    opciones = [{
        "nombre": nombre_correcto,
        "id": poke_id,
        "es_correcto": True,
        "imagen_url": imagen_correcta
    }]
    ids_usados = {poke_id}
    nombres_usados = {nombre_correcto.casefold()}

    candidatos = list(range(min_id, max_id + 1))
    random.shuffle(candidatos)

    for rid in candidatos:
        if len(opciones) >= cantidad:
            break
        if rid in ids_usados:
            continue

        nombre = obtener_nombre_por_id(rid)
        clave_nombre = nombre.casefold()
        if clave_nombre in nombres_usados:
            continue

        ids_usados.add(rid)
        nombres_usados.add(clave_nombre)
        opciones.append({
            "nombre": nombre,
            "id": rid,
            "es_correcto": False
        })

    if len(opciones) < cantidad:
        return None

    random.shuffle(opciones)
    return opciones

def obtener_pokemon_by_rango(min_id: int, max_id: int, modo="clasico"):
    if min_id > max_id:
        return None

    disponibles = [
        i for i in range(min_id, max_id + 1)
        if i not in st.session_state["vistos_partida"]
    ]
    if not disponibles:
        st.session_state["vistos_partida"].clear()
        disponibles = list(range(min_id, max_id + 1))

    candidatos_objetivo = disponibles[:]
    random.shuffle(candidatos_objetivo)

    for poke_id in candidatos_objetivo:
        try:
            res_species = obtener_datos_especie(poke_id)
            res_poke = obtener_datos_pokemon(poke_id)
            if not res_species or not res_poke:
                continue

            tipos = [t["type"]["name"] for t in res_poke.get("types", [])]
            nombre = limpiar_nombre_pokemon(res_species["name"])
            gen = int(res_species["generation"]["url"].split("/")[-2])
            es_shiny = random.random() < 0.05
            pil_img = _obtener_imagen_pokemon(res_poke, es_shiny)

            if modo == "sombra" and pil_img:
                data = pil_img.getdata()
                new_data = []
                for item in data:
                    if item[3] > 0:
                        new_data.append((0, 0, 0, item[3]))
                    else:
                        new_data.append((255, 255, 255, 0))
                pil_img.putdata(new_data)

            opciones_data = _crear_opciones_nombres(min_id, max_id, poke_id, nombre)
            if opciones_data is None:
                continue
            respuesta_correcta = nombre

            st.session_state["vistos_partida"].add(poke_id)
            return {
                "id": poke_id,
                "nombre": nombre,
                "gen": gen,
                "tipos": [t.capitalize() for t in tipos],
                "shiny": es_shiny,
                "imagen": pil_img,
                "opciones": opciones_data,
                "respuesta_correcta": respuesta_correcta
            }
        except (KeyError, TypeError, ValueError, IndexError, requests.RequestException, OSError):
            continue

    return None

# --- CONSOLA SECRETA ACTIVADA CON TECLA Q ---
if st.session_state["mostrar_consola_trucos"]:
    st.markdown("""
    <div style="background: rgba(0,0,0,0.85); border: 2px solid #ffcc00; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <h3 style="color: #ffcc00; margin-top: 0;">💻 Terminal Oculta del Sistema</h3>
        <p style="color: #fff; font-size: 13px;">Introduce el comando de autorización secreto:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        codigo_ingresado = st.text_input("Comando:", type="password", key="input_consola_secreta", label_visibility="collapsed")
    with col_t2:
        if st.button("Enviar", use_container_width=True):
            if codigo_ingresado.strip().lower() == "popoi":
                st.session_state["monedas"] += 10000
                guardar_progreso()
                st.success("✔ Autorización concedida. Transferencia completada.")
                st.session_state["mostrar_consola_trucos"] = False
                st.rerun()
            else:
                st.error("✘ Código no válido.")

# --- PERFIL DE ENTRENADOR Y COMPAÑERO ---
ent_actual = ENTRENADORES.get(st.session_state['entrenador_actual'], ENTRENADORES["Rojo"])
comp_id = st.session_state["companero_id"]
comp_shiny = st.session_state["companero_shiny"]
comp_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{'shiny/' if comp_shiny else ''}{comp_id}.png"

st.markdown(f"""
<div class="perfil-card">
    <table style="width:100%; border:none;">
        <tr>
            <td style="width:75px; vertical-align:middle; border:none;">
                <img src="{ent_actual['avatar_url']}" width="70" style="border-radius:10px; background: rgba(255,255,255,0.1); padding: 4px;">
            </td>
            <td style="vertical-align:middle; border:none; padding-left:15px;">
                <h2 style="margin:0; color:white; font-size: 24px;">{st.session_state['entrenador_actual']}</h2>
                <p style="margin:3px 0 0 0; font-size:15px; color:#ffeb3b; font-weight: bold;">{obtener_titulo_entrenador()}</p>
            </td>
            <td style="text-align:center; vertical-align:middle; border:none; width:85px;">
                <img src="{comp_url}" width="65" style="background: rgba(0,0,0,0.2); border-radius:50%; border: 2px solid #ffcc00;">
                <p style="margin:2px 0 0 0; font-size:11px; color:#ffcc00;">Compañero</p>
            </td>
            <td style="text-align:right; vertical-align:middle; border:none;">
                <h3 style="margin:0; color:white; font-size: 20px;">🪙 Poké-Coins</h3>
                <p style="margin:3px 0 0 0; font-size:22px; color:#00e676; font-weight: bold;">{st.session_state['monedas']}</p>
            </td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

# --- PESTAÑAS PRINCIPALES (INCLUYENDO MODO HISTORIA Y MISIONES) ---
tab_jugar, tab_historia, tab_misiones, tab_guarderia, tab_tcg, tab_entrenadores, tab_mercado, tab_pokedex, tab_shinydex, tab_stats, tab_ajustes = st.tabs([
    "🎮 Jugar", "🗺️ Modo Historia", "🎯 Misiones", "🥚 Guardería", "🎴 Cartas TCG", "👥 Entrenadores", "🛒 Mercado", "📖 Pokédex", "✨ ShinyDex", "📊 Stats", "⚙️ Ajustes"
])

# --- 1. JUGAR ---
with tab_jugar:
    if st.session_state["derrota"]:
        st.title("💥 ¡Has Caído!")
        st.error("¡Te equivocaste de respuesta!")
        if st.session_state["ultimo_pokemon_fallado"]:
            pf = st.session_state["ultimo_pokemon_fallado"]
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                res_p = obtener_datos_pokemon(pf["id"])
                if res_p:
                    img_url = res_p["sprites"]["front_default"]
                    st.image(img_url, width=220)
                st.subheader(f"Era: #{pf['id']:03d} - {pf['nombre']}")
        st.divider()
        if st.button("🔄 Volver al Selector", type="primary", use_container_width=True):
            st.session_state["derrota"] = False
            st.session_state["en_partida"] = False
            st.session_state["puntos"] = 0
            st.session_state["racha"] = 0
            st.rerun()

    elif not st.session_state["en_partida"]:
        st.title("🕹️ Salón de Juegos Arcade")
        gen_seleccionada = st.selectbox("📂 Rango de Generaciones:", list(RANGOS_GENERACIONES.keys()))
        st.session_state["rango_gens"] = RANGOS_GENERACIONES[gen_seleccionada]
        
        st.divider()
        st.write("Elige tu minijuego favorito:")
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.markdown("""
            <div class="minigame-card">
                <h3>🎯 Modo Clásico</h3>
                <p style="color:#aaa; font-size:13px; min-height:40px;">Adivina el nombre del Pokémon visible.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Jugar Clásico", key="btn_m_clasico", use_container_width=True):
                st.session_state["en_partida"] = True
                st.session_state["modo_juego"] = "clasico"
                st.session_state["puntos"] = 0
                st.session_state["racha"] = 0
                st.session_state["vistos_partida"].clear()
                r_min, r_max = st.session_state["rango_gens"]
                st.session_state["pokemon_actual"] = obtener_pokemon_by_rango(r_min, r_max, "clasico")
                st.rerun()
                
        with col_m2:
            st.markdown("""
            <div class="minigame-card">
                <h3>🌑 ¿Quién es ese Pokémon?</h3>
                <p style="color:#aaa; font-size:13px; min-height:40px;">Reconoce al Pokémon por su silueta.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🌑 Jugar Silueta", key="btn_m_sombra", use_container_width=True):
                st.session_state["en_partida"] = True
                st.session_state["modo_juego"] = "sombra"
                st.session_state["puntos"] = 0
                st.session_state["racha"] = 0
                st.session_state["vistos_partida"].clear()
                r_min, r_max = st.session_state["rango_gens"]
                st.session_state["pokemon_actual"] = obtener_pokemon_by_rango(r_min, r_max, "sombra")
                # Actualizar misión diaria de sombra
                if "modo_sombra" in st.session_state["misiones_diarias"]:
                    st.session_state["misiones_diarias"]["modo_sombra"]["actual"] = 1
                    if st.session_state["misiones_diarias"]["modo_sombra"]["actual"] >= st.session_state["misiones_diarias"]["modo_sombra"]["meta"]:
                        st.session_state["misiones_diarias"]["modo_sombra"]["completada"] = True
                guardar_progreso()
                st.rerun()

    else:
        modo_actual = st.session_state.get("modo_juego", "clasico")
        st.title("🎯 Partida Arcade Activa")
        
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
        r_min, r_max = st.session_state["rango_gens"]
        
        if not poke:
            poke = obtener_pokemon_by_rango(r_min, r_max, modo_actual)
            st.session_state["pokemon_actual"] = poke
            
        if poke:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if poke["imagen"]: st.image(poke["imagen"], width=285)
                
            st.subheader("¿Cuál de estos Pokémon es el correcto?")
            
            opciones_unicas = []
            nombres_vistos = set()
            for opc_item in poke.get("opciones", []):
                opc_nombre = opc_item.get("nombre", "")
                clave_nombre = opc_nombre.casefold()
                if clave_nombre in nombres_vistos:
                    continue
                nombres_vistos.add(clave_nombre)
                opciones_unicas.append(opc_item)

            for idx, opc_item in enumerate(opciones_unicas[:4]):
                opc_nombre = opc_item["nombre"]
                if st.button(f"{opc_nombre}", use_container_width=True, key=f"btn_opc_{idx}"):
                    if opc_nombre == poke["respuesta_correcta"]:
                        st.session_state["puntos"] += 1
                        st.session_state["racha"] += 1
                        st.session_state["aciertos_totales"] += 1
                        st.session_state["pokedex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
                        if poke["shiny"]:
                            st.session_state["shinydex_capturados"][poke["id"]] = {"nombre": poke["nombre"], "gen": poke["gen"]}
                        
                        ganancia_monedas = 4 + ent_actual.get("bonus_monedas", 0)
                        st.session_state["monedas"] += ganancia_monedas
                        avanzar_huevos()
                        
                        # Actualizar misión de aciertos
                        if "aciertos_5" in st.session_state["misiones_diarias"] and not st.session_state["misiones_diarias"]["aciertos_5"]["completada"]:
                            st.session_state["misiones_diarias"]["aciertos_5"]["actual"] += 1
                            if st.session_state["misiones_diarias"]["aciertos_5"]["actual"] >= st.session_state["misiones_diarias"]["aciertos_5"]["meta"]:
                                st.session_state["misiones_diarias"]["aciertos_5"]["completada"] = True
                                st.session_state["monedas"] += st.session_state["misiones_diarias"]["aciertos_5"]["recompensa"]
                                agregar_notificacion("🎯 ¡Misión diaria completada! +50 Poké-Coins", "success")

                        if st.session_state["racha"] > st.session_state["racha_maxima"]:
                            st.session_state["racha_maxima"] = st.session_state["racha"]
                        
                        guardar_progreso()
                        agregar_notificacion(f"¡Correcto! (+{ganancia_monedas} Poké-Coins)", "success")
                        st.session_state["pokemon_actual"] = obtener_pokemon_by_rango(r_min, r_max, modo_actual)
                        st.rerun()
                    else:
                        st.session_state["fallos_totales"] += 1
                        guardar_progreso()
                        st.session_state["ultimo_pokemon_fallado"] = poke
                        st.session_state["derrota"] = True
                        st.rerun()

        st.divider()
        if st.button("🏠 Salir al Menú de Minijuegos", use_container_width=True):
            st.session_state["en_partida"] = False
            st.session_state["derrota"] = False
            st.rerun()

# --- 2. MODO HISTORIA ---
with tab_historia:
    st.title("🗺️ Modo Historia: Liga de Gimnasios")
    st.write("Derrota a los líderes de gimnasio en una serie de desafíos de trivia para ganar grandes premios y títulos legendarios.")
    st.divider()
    
    progreso_actual = st.session_state["historia_progreso"]
    
    for gym in GIMNASIOS_HISTORIA:
        gym_id = gym["id"]
        superado = gym_id < progreso_actual
        en_curso = gym_id == progreso_actual
        
        c1, c2, c3 = st.columns([1, 3, 2])
        with c1: st.image(gym["avatar"], width=70)
        with c2:
            st.markdown(f"### {gym['nombre']}\nLíder: **{gym['lider']}**\nPremio: 🪙 {gym['recompensa']}")
        with c3:
            if superado:
                st.success("✅ Superado")
            elif en_curso:
                if not st.session_state["en_historia"]:
                    if st.button(f"⚔️ Retar a {gym['lider']}", key=f"retar_gym_{gym_id}", use_container_width=True):
                        st.session_state["en_historia"] = True
                        st.session_state["historia_vidas"] = 3
                        st.session_state["gym_activo"] = gym
                        st.session_state["pokemon_historia"] = obtener_pokemon_by_rango(1, 386, "clasico")
                        st.rerun()
                else:
                    st.warning("⚠️ Batalla en curso...")
            else:
                st.info("🔒 Bloqueado")
        st.divider()

    if st.session_state["en_historia"]:
        gym_activo = st.session_state["gym_activo"]
        st.markdown(f"### ⚔️ Combate de Gimnasio contra {gym_activo['lider']}")
        st.metric("❤️ Vidas restantes", st.session_state["historia_vidas"])
        
        poke_h = st.session_state.get("pokemon_historia")
        if poke_h:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if poke_h["imagen"]: st.image(poke_h["imagen"], width=250)
            
            st.write("¿Quién es este Pokémon?")
            for idx, opc_item in enumerate(poke_h["opciones"][:4]):
                opc_nombre = opc_item["nombre"]
                if st.button(opc_nombre, key=f"hist_opc_{idx}", use_container_width=True):
                    if opc_nombre == poke_h["respuesta_correcta"]:
                        st.session_state["historia_progreso"] += 1
                        st.session_state["monedas"] += gym_activo["recompensa"]
                        st.session_state["en_historia"] = False
                        guardar_progreso()
                        st.success(f"🎉 ¡Has derrotado a {gym_activo['lider']}! Recompensa obtenida.")
                        st.rerun()
                    else:
                        st.session_state["historia_vidas"] -= 1
                        if st.session_state["historia_vidas"] <= 0:
                            st.session_state["en_historia"] = False
                            st.error("💥 ¡Te has quedado sin vidas y has perdido el combate de gimnasio!")
                            st.rerun()
                        else:
                            st.warning(f"❌ ¡Fallaste! Te quedan {st.session_state['historia_vidas']} vidas.")
                            st.session_state["pokemon_historia"] = obtener_pokemon_by_rango(1, 386, "clasico")
                            st.rerun()

# --- 3. MISIONES DIARIAS ---
with tab_misiones:
    st.title("🎯 Misiones Diarias")
    st.write("Completa objetivos diarios para conseguir Poké-Coins extra.")
    st.divider()
    
    for m_key, m_val in st.session_state["misiones_diarias"].items():
        st.markdown(f"### {m_val['desc']}")
        st.progress(min(1.0, m_val["actual"] / m_val["meta"]))
        st.write(f"Progreso: {m_val['actual']} / {m_val['meta']} | Recompensa: 🪙 {m_val['recompensa']}")
        if m_val["completada"]:
            st.success("✅ Misión completada")
        else:
            st.info("⏳ En progreso")
        st.divider()

# --- 4. GUARDERÍA ---
with tab_guarderia:
    st.title("🥚 Guardería Pokémon")
    st.write("¡Incuba tus huevos ganando aciertos en las partidas arcade!")
    st.divider()
    
    if not st.session_state["huevos"]:
        st.info("No tienes huevos en incubación. ¡Compra uno en el **Mercado**!")
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
            st.divider()

# --- 5. CARTAS TCG (CON INTERCAMBIO) ---
with tab_tcg:
    st.title("🎴 Álbum de Cartas TCG e Intercambio")
    st.write("Colecciona cartas o intercambia 2 cartas repetidas por una nueva.")
    st.divider()
    
    if st.session_state["carta_recien_abierta"]:
        c_rec = st.session_state["carta_recien_abierta"]
        st.balloons()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2b32b2 0%, #1f4068 100%); border-radius: 16px; padding: 20px; text-align: center; border: 3px solid #ffcc00; margin-bottom: 25px;">
            <h3 style="color: #ffcc00; margin-top: 0;">🎉 ¡NUEVA CARTA OBTENIDA! 🎉</h3>
            <img src="{c_rec['imagen']}" width="140" style="border-radius:10px; background: rgba(255,255,255,0.1); padding: 6px;">
            <h4 style="color:white; margin:10px 0 5px 0;">{c_rec['nombre']}</h4>
            <p style="color:#00e676; font-weight:bold; margin:0;">Rareza: {c_rec['rareza']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✨ Guardar en el Álbum"):
            st.session_state["cartas_coleccion"].append(c_rec)
            st.session_state["carta_recien_abierta"] = None
            guardar_progreso()
            st.rerun()
        st.divider()

    if len(st.session_state["cartas_coleccion"]) >= 2:
        if st.button("🔄 Intercambiar 2 Cartas por un sobre aleatorio"):
            st.session_state["cartas_coleccion"] = st.session_state["cartas_coleccion"][2:]
            poke_id = random.randint(1, 151)
            res_p = obtener_datos_pokemon(poke_id)
            res_s = obtener_datos_especie(poke_id)
            img = res_p.get("sprites", {}).get("front_default") if res_p else None
            if res_p and res_s and img:
                nombre = limpiar_nombre_pokemon(res_s["name"])
                rareza = "Holográfica"
                st.session_state["carta_recien_abierta"] = {"nombre": nombre, "rareza": rareza, "imagen": img}
                guardar_progreso()
                st.rerun()

    if not st.session_state["cartas_coleccion"]:
        st.info("📦 Tu álbum está vacío. ¡Adquiere sobres en el **Mercado**!")
    else:
        cols = st.columns(3)
        for idx, carta in enumerate(st.session_state["cartas_coleccion"]):
            col = cols[idx % 3]
            with col:
                st.markdown(f"""
                <div class="card-tcg">
                    <img src="{carta['imagen']}" width="100" style="border-radius:8px;">
                    <h4 style="margin:8px 0 4px 0; color:white; font-size:15px;">{carta['nombre']}</h4>
                    <p style="margin:0; color:#ffcc00; font-size:12px; font-weight:bold;">★ {carta['rareza']}</p>
                </div>
                """, unsafe_allow_html=True)

# --- 6. ENTRENADORES ---
with tab_entrenadores:
    st.title("👥 Entrenadores")
    st.write("Desbloquea entrenadores para obtener bonificaciones de Poké-Coins.")
    st.divider()
    
    for key_ent, datos in ENTRENADORES.items():
        desbloqueado = key_ent in st.session_state["entrenadores_desbloqueados"] or datos["costo"] == 0
        es_activo = st.session_state["entrenador_actual"] == key_ent
        
        c1, c2, c3 = st.columns([1, 3, 2])
        with c1: st.image(datos["avatar_url"], width=70)
        with c2: 
            st.markdown(f"### {datos['nombre']}\n*{datos['descripcion']}*\n💡 `{datos['trait']}`")
        with c3:
            if es_activo:
                st.success("✅ Activo")
            elif desbloqueado:
                if st.button("Seleccionar", key=f"sel_e_{key_ent}", use_container_width=True):
                    st.session_state["entrenador_actual"] = key_ent
                    guardar_progreso()
                    st.rerun()
            else:
                if st.button(f"Comprar (🪙 {datos['costo']})", key=f"compr_e_{key_ent}", use_container_width=True):
                    if st.session_state["monedas"] >= datos["costo"]:
                        st.session_state["monedas"] -= datos["costo"]
                        st.session_state["entrenadores_desbloqueados"].append(key_ent)
                        st.session_state["entrenador_actual"] = key_ent
                        guardar_progreso()
                        st.success(f"🎉 ¡Desbloqueado a {datos['nombre']}!")
                        st.rerun()
                    else:
                        st.error("❌ Monedas insuficientes")
        st.divider()

# --- 7. MERCADO ---
with tab_mercado:
    st.title("🛒 Bazar Arcade")
    st.write(f"🪙 Monedas Disponibles: **{st.session_state['monedas']}**")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="shop-card">
            <h3>🥚 Huevo Normal</h3>
            <p style="color:#aaa; font-size:13px;">Requiere 10 aciertos.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Comprar (🪙 75)", key="b_h_norm", use_container_width=True):
            if st.session_state["monedas"] >= 75:
                st.session_state["monedas"] -= 75
                st.session_state["huevos"].append({"tipo": "Huevo Normal", "pasos_actuales": 0, "pasos_necesarios": 10, "prob_shiny": 0.05, "eclosionado": False})
                guardar_progreso()
                st.success("✅ ¡Adquirido!")
                st.rerun()
            else: st.error("❌ Monedas insuficientes")
            
    with c2:
        st.markdown("""
        <div class="shop-card">
            <h3>✨ Huevo Shiny</h3>
            <p style="color:#aaa; font-size:13px;">Mayor probabilidad Shiny (5 aciertos).</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Comprar (🪙 200)", key="b_h_shiny", use_container_width=True):
            if st.session_state["monedas"] >= 200:
                st.session_state["monedas"] -= 200
                st.session_state["huevos"].append({"tipo": "Huevo Shiny", "pasos_actuales": 0, "pasos_necesarios": 5, "prob_shiny": 0.50, "eclosionado": False})
                guardar_progreso()
                st.success("✅ ¡Adquirido!")
                st.rerun()
            else: st.error("❌ Monedas insuficientes")

    with c3:
        st.markdown("""
        <div class="shop-card">
            <h3>🎴 Sobre TCG</h3>
            <p style="color:#aaa; font-size:13px;">Consigue una carta coleccionable.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Comprar (🪙 80)", key="b_sobre", use_container_width=True):
            if st.session_state["monedas"] >= 80:
                poke_id = random.randint(1, 151)
                res_p = obtener_datos_pokemon(poke_id)
                res_s = obtener_datos_especie(poke_id)
                img = res_p.get("sprites", {}).get("front_default") if res_p else None
                if res_p and res_s and img:
                    nombre = limpiar_nombre_pokemon(res_s["name"])
                    rareza = random.choices(["Común", "Rara", "Holográfica", "Ultra Rara"], weights=[60, 25, 12, 3])[0]
                    nueva_carta = {"nombre": nombre, "rareza": rareza, "imagen": img}
                    st.session_state["monedas"] -= 80
                    st.session_state["carta_recien_abierta"] = nueva_carta
                    guardar_progreso()
                    st.rerun()
                else:
                    st.error("⚠️ No se pudo abrir el sobre. Inténtalo de nuevo.")
            else:
                st.error("❌ Monedas insuficientes")

# --- 8. POKÉDEX ---
with tab_pokedex:
    st.title("📖 Pokédex Web")
    st.write(f"Pokémon registrados: **{len(st.session_state['pokedex_capturados'])} / 1025**")
    st.divider()
    for pid, data in sorted(st.session_state["pokedex_capturados"].items()):
        c1, c2 = st.columns([1, 5])
        with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png", width=70)
        with c2: st.write(f"### #{pid:03d} - {data['nombre']}")
        st.divider()

# --- 9. SHINYMEX ---
with tab_shinydex:
    st.title("✨ ShinyDex")
    st.write(f"Pokémon variocolor registrados: **{len(st.session_state['shinydex_capturados'])}**")
    st.divider()
    if not st.session_state["shinydex_capturados"]:
        st.info("Aún no has descubierto ningún Pokémon Shiny. ¡Sigue jugando!")
    else:
        for pid, data in sorted(st.session_state["shinydex_capturados"].items()):
            c1, c2 = st.columns([1, 5])
            with c1: st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pid}.png", width=80)
            with c2: st.write(f"### #{pid:03d} - {data['nombre']} ✨")
            st.divider()

# --- 10. ESTADÍSTICAS Y LOGROS ---
with tab_stats:
    st.title("📊 Estadísticas, Récords y Logros")
    comprobar_logros()
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1: st.metric("🔥 Récord Guinness de Racha", st.session_state["racha_maxima"])
    with col_s2: st.metric("✅ Aciertos Totales", st.session_state["aciertos_totales"])
    with col_s3: st.metric("❌ Fallos Totales", st.session_state["fallos_totales"])
    
    st.divider()
    st.subheader("🏆 Lista de Logros")
    for clave, datos in LOGROS_DEF.items():
        completado = st.session_state["logros"].get(clave, False)
        if completado:
            st.success(f"**{datos['titulo']}** (Completado) — {datos['desc']}")
        else:
            st.info(f"🔒 **{datos['titulo']}** (Pendiente) — {datos['desc']}")

# --- 11. AJUSTES (CON SELECCIÓN DE TÍTULO Y COMPAÑERO) ---
with tab_ajustes:
    st.title("⚙️ Ajustes y Configuración")
    st.write("Gestiona tu título personalizado, tu compañero y opciones de guardado.")
    st.divider()
    
    st.subheader("👑 Selección de Título de Entrenador")
    titulos_disponibles = ["", "🌱 Novato de Pueblo Paleta", "📘 Coleccionista Experto", "⚡ Maestro Pokémon", "👑 Campeón Indiscutible"]
    titulo_elegido_actual = st.selectbox("Elige tu título preferido:", titulos_disponibles, index=titulos_disponibles.index(st.session_state["titulo_elegido"]) if st.session_state["titulo_elegido"] in titulos_disponibles else 0)
    
    if st.button("Guardar Título"):
        st.session_state["titulo_elegido"] = titulo_elegido_actual
        guardar_progreso()
        st.success("✔ ¡Título actualizado con éxito!")
        st.rerun()

    st.divider()
    st.subheader("🐾 Selección de Compañero")
    if not st.session_state["pokedex_capturados"]:
        st.info("Aún no tienes Pokémon en tu Pokédex para elegir como compañero.")
    else:
        nombres_disponibles = {data["nombre"]: pid for pid, data in st.session_state["pokedex_capturados"].items()}
        lista_nombres = sorted(list(nombres_disponibles.keys()))
        
        nombre_actual_comp = obtener_nombre_por_id(st.session_state["companero_id"])
        idx_default = lista_nombres.index(nombre_actual_comp) if nombre_actual_comp in lista_nombres else 0
        
        col_set1, col_set2 = st.columns([2, 1])
        with col_set1:
            pokemon_elegido_str = st.selectbox("Selecciona compañero registrado:", lista_nombres, index=idx_default)
        with col_set2:
            id_tentativo = nombres_disponibles[pokemon_elegido_str]
            tiene_shiny = id_tentativo in st.session_state["shinydex_capturados"]
            
            if tiene_shiny:
                modo_shiny_comp = st.checkbox("Versión Shiny ✨", value=st.session_state["companero_shiny"] and st.session_state["companero_id"] == id_tentativo)
            else:
                st.checkbox("Versión Shiny ✨ (Bloqueado)", value=False, disabled=True)
                modo_shiny_comp = False
            
        if st.button("💾 Establecer como Compañero", use_container_width=True):
            st.session_state["companero_id"] = id_tentativo
            st.session_state["companero_shiny"] = modo_shiny_comp
            guardar_progreso()
            st.success(f"✔ ¡{pokemon_elegido_str} es ahora tu compañero oficial!")
            st.rerun()

    st.divider()
    st.subheader("🛠️ Gestión de Datos")
    if st.button("🗑️ Borrar Progreso de Partida", type="secondary", use_container_width=True):
        if os.path.exists(ARCHIVO_GUARDADO):
            try:
                os.remove(ARCHIVO_GUARDADO)
            except OSError:
                pass

        st.session_state["pokedex_capturados"] = {}
        st.session_state["shinydex_capturados"] = {}
        st.session_state["racha_maxima"] = 0
        st.session_state["logros"] = {}
        st.session_state["aciertos_totales"] = 0
        st.session_state["fallos_totales"] = 0
        st.session_state["monedas"] = 10
        st.session_state["entrenador_actual"] = "Rojo"
        st.session_state["entrenadores_desbloqueados"] = ["Rojo"]
        st.session_state["huevos"] = []
        st.session_state["cartas_coleccion"] = []
        st.session_state["companero_id"] = 25
        st.session_state["companero_shiny"] = False
        st.session_state["titulo_elegido"] = ""
        st.session_state["historia_progreso"] = 1
        
        st.success("✅ Se han restablecido los datos correctamente.")
        st.rerun()
