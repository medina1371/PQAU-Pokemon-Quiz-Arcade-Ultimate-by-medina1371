import random
import requests
import streamlit as st
from PIL import Image, ImageOps
import io
import json
import os
import uuid  # <-- Importante para evitar duplicados de botones en Streamlit
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Pokémon Quiz Arcade Ultimate ⚡",
    page_icon="🎮",
    layout="centered"
)

# --- ESTILOS CSS ---
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
</style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA (JSON LOCAL) ---
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
                monedas = datos.get("monedas", 150)
                entrenador_actual = datos.get("entrenador_actual", "Rojo")
                entrenadores_desbloqueados = datos.get("entrenadores_desbloqueados", ["Rojo"])
                huevos = datos.get("huevos", [])
                cartas_coleccion = datos.get("cartas_coleccion", [])
                companero_id = datos.get("companero_id", 25)
                companero_shiny = datos.get("companero_shiny", False)
                return pokedex, shinydex, racha_max, logros, aciertos, fallos, monedas, entrenador_actual, entrenadores_desbloqueados, huevos, cartas_coleccion, companero_id, companero_shiny
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return {}, {}, 0, {}, 0, 0, 150, "Rojo", ["Rojo"], [], [], 25, False

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
        "companero_shiny": st.session_state["companero_shiny"]
    }
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except (OSError, TypeError, ValueError):
        pass

if "pokedex_capturados" not in st.session_state:
    p_ini, s_ini, rm_ini, l_ini, ac_ini, fa_ini, mon_ini, ent_ini, ents_ini, hue_ini, car_ini, comp_id_ini, comp_sh_ini = cargar_progreso()
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

# Token dinámico para evitar conflictos en los botones
if "round_token" not in st.session_state:
    st.session_state["round_token"] = str(uuid.uuid4())

if "racha" not in st.session_state: st.session_state["racha"] = 0
if "puntos" not in st.session_state: st.session_state["puntos"] = 0
if "derrota" not in st.session_state: st.session_state["derrota"] = False
if "ultimo_pokemon_fallado" not in st.session_state: st.session_state["ultimo_pokemon_fallado"] = None
if "en_partida" not in st.session_state: st.session_state["en_partida"] = False
if "modo_juego" not in st.session_state: st.session_state["modo_juego"] = None
if "rango_gens" not in st.session_state: st.session_state["rango_gens"] = (1, 151)
if "vistos_partida" not in st.session_state: st.session_state["vistos_partida"] = set()
if "ultima_notificacion" not in st.session_state: st.session_state["ultima_notificacion"] = None
if "mostrar_consola_trucos" not in st.session_state: st.session_state["mostrar_consola_trucos"] = False

# --- DETECTOR DE TECLA "Q" ---
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

if st.button("TrigQ", key="hidden_trigger_btn"):
    st.session_state["mostrar_consola_trucos"] = not st.session_state["mostrar_consola_trucos"]
    st.rerun()

# --- FUNCIONES AUXILIARES DE API Y DATOS ---
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
    if not url: return None
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
    if not res_poke: return None
    sprites = res_poke.get("sprites", {})
    img_url = sprites.get("front_shiny") if es_shiny else sprites.get("front_default")
    if not img_url: img_url = sprites.get("front_default")
    img_data = descargar_imagen_bytes(img_url)
    if not img_data: return None
    try:
        return Image.open(io.BytesIO(img_data)).convert("RGBA")
    except (OSError, ValueError):
        return None

def _crear_opciones_tipo(min_id, max_id, poke_id, nombre_correcto, combinacion_correcta, cantidad=4):
    datos_correctos = obtener_datos_pokemon(poke_id)
    imagen_correcta = datos_correctos.get("sprites", {}).get("front_default") if datos_correctos else None
    if not imagen_correcta: return None

    opciones = [{"nombre": nombre_correcto, "id": poke_id, "es_correcto": True, "imagen_url": imagen_correcta}]
    ids_usados = {poke_id}
    nombres_usados = {nombre_correcto.casefold()}

    candidatos = list(range(min_id, max_id + 1))
    random.shuffle(candidatos)

    for rid in candidatos:
        if len(opciones) >= cantidad: break
        if rid in ids_usados: continue

        r_spec = obtener_datos_especie(rid)
        r_poke = obtener_datos_pokemon(rid)
        if not r_spec or not r_poke: continue

        tipos_err = tuple(sorted(t["type"]["name"] for t in r_poke.get("types", [])))
        if tipos_err == combinacion_correcta: continue

        nombre = limpiar_nombre_pokemon(r_spec["name"])
        if nombre.casefold() in nombres_usados: continue

        imagen_url = r_poke.get("sprites", {}).get("front_default")
        if not imagen_url: continue

        ids_usados.add(rid)
        nombres_usados.add(nombre.casefold())
        opciones.append({"nombre": nombre, "id": rid, "es_correcto": False, "imagen_url": imagen_url})

    if len(opciones) < cantidad: return None
    random.shuffle(opciones)
    return opciones

# --- EJEMPLO DE RENDERIZADO SEGURO PARA EL MODO TIPO ---
# Asegúrate de terminar esta sección en tu bucle principal de juego así:
if "pokemon_actual" in st.session_state and st.session_state["pokemon_actual"]:
    poke = st.session_state["pokemon_actual"]
    if st.session_state.get("modo_juego") == "tipo":
        st.markdown(f"""
        <div style="background: #1e1e2f; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #ffcc00; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #ffcc00;">¿Qué Pokémon tiene esta combinación de tipos?</h3>
            <h2 style="margin: 10px 0 0 0; color: white; letter-spacing: 2px;">⚡ {poke['texto_tipos']} ⚡</h2>
        </div>
        """, unsafe_allow_html=True)
        
        opciones_tipo_unicas = []
        claves_tipo = set()
        for opc in poke.get("opciones_tipo", []):
            clave = (opc.get("id"), opc.get("nombre", "").casefold())
            if clave in claves_tipo: continue
            claves_tipo.add(clave)
            opciones_tipo_unicas.append(opc)

        cols_opc = st.columns(2)
        for idx, opc in enumerate(opciones_tipo_unicas[:4]):
            col_target = cols_opc[idx % 2]
            with col_target:
                imagen_opcion = opc.get("imagen_url")
                if imagen_opcion:
                    st.image(imagen_opcion, width=100)
                
                # LLAVE ÚNICA CON EL TOKEN DE RONDA
                btn_key = f"btn_tipo_{st.session_state['round_token']}_{idx}_{opc['id']}"
                
                if st.button(opc["nombre"], key=btn_key, use_container_width=True):
                    if opc["es_correcto"]:
                        st.session_state["puntos"] += 1
                        st.session_state["racha"] += 1
                        st.success("¡Correcto! 🎉")
                    else:
                        st.session_state["derrota"] = True
                        st.session_state["ultimo_pokemon_fallado"] = poke
                    
                    # Refrescamos el token y reiniciamos el pokemon actual para la siguiente ronda
                    st.session_state["round_token"] = str(uuid.uuid4())
                    st.session_state["pokemon_actual"] = None
                    st.rerun()
