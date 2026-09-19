from __future__ import annotations

import hashlib
import os
import random
import re
import secrets
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover
    Client = Any
    create_client = None

ROOT = Path(__file__).parent
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://pokemon-quiz-arcade.onrender.com").rstrip("/")
app = FastAPI(title="Pokémon Quiz Arcade", version="2.0.0", servers=[{"url": PUBLIC_BASE_URL}])
app.add_middleware(CORSMiddleware, allow_origins=[PUBLIC_BASE_URL, "http://127.0.0.1:8000", "http://localhost:8000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

STARTING_PLAYER = {"coins": 100, "correct": 0, "failures": 0, "streak": 0, "best_streak": 0, "shinies_seen": 0, "wins": 0, "losses": 0, "xp": 0, "level": 1, "achievements": {}, "favorites": [], "team": [], "cosmetics": ["classic"], "active_cosmetic": "classic", "missions_claimed": {}, "pokedex": {}, "shinydex": {}}
LOCAL_PLAYERS: dict[str, dict[str, Any]] = {}
DAILY_LIMIT = 10
BET_MIN, BET_MAX = 5, 500
PLAYER_RE = re.compile(r"^[A-Z0-9_]{3,24}$")
GENERATION_LABELS = {i: f"Generación {i}" for i in range(1, 10)}
GENERATION_RANGES = {1: (1, 151), 2: (152, 251), 3: (252, 386), 4: (387, 493), 5: (494, 649), 6: (650, 721), 7: (722, 809), 8: (810, 905), 9: (906, 1025)}
GENERATION_CACHE: dict[int, list[str]] = {}
GENERATION_SPECIES_CACHE: dict[int, list[dict[str, Any]]] = {}
QUESTION_SHINY: dict[str, bool] = {}


def db() -> Client | None:
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key or not create_client:
        return None
    return create_client(url, key)


SUPABASE = db()


def player_id(value: str) -> str:
    value = value.strip().upper()
    if not PLAYER_RE.fullmatch(value):
        raise HTTPException(400, "El código debe tener 3-24 caracteres: A-Z, 0-9 o _.")
    return value


def question_shiny(code: str, mode: str, pokemon_id: int) -> bool:
    flag = random.random() < 0.05
    QUESTION_SHINY[f"{code}:{mode}:{pokemon_id}"] = flag
    if flag:
        state = load_player(code)
        state["shinies_seen"] += 1
        save_player(code, state)
    return flag


def update_progress(state: dict[str, Any]) -> None:
    state["level"] = max(1, state["xp"] // 100 + 1)
    rules = {
        "primer_acierto": state["correct"] >= 1,
        "racha_10": state["best_streak"] >= 10,
        "cazador_shiny": len(state["shinydex"]) >= 1,
        "coleccionista": len(state["pokedex"]) >= 25,
        "name_all": state["correct"] >= 50,
    }
    state["achievements"].update({key: True for key, ok in rules.items() if ok})


def normalize(row: dict[str, Any] | None) -> dict[str, Any]:
    row = row or {}
    result = {
        **STARTING_PLAYER,
        "coins": row.get("coins", row.get("monedas", STARTING_PLAYER["coins"])),
        "correct": row.get("correct", row.get("aciertos_totales", 0)),
        "failures": row.get("failures", row.get("fallos_totales", 0)),
        "streak": row.get("streak", 0),
        "best_streak": row.get("best_streak", row.get("racha_maxima", 0)),
        "shinies_seen": row.get("shinies_seen", 0),
        "wins": row.get("wins", 0),
        "losses": row.get("losses", 0),
        "xp": row.get("xp", 0),
        "level": row.get("level", 1),
        "achievements": row.get("achievements", row.get("logros", {})) or {},
        "favorites": row.get("favorites", []) or [],
        "team": row.get("team", row.get("equipo", [])) or [],
        "cosmetics": row.get("cosmetics", []) or [],
        "active_cosmetic": row.get("active_cosmetic", "classic"),
        "missions_claimed": row.get("missions_claimed", {}) or {},
        "pokedex": row.get("pokedex", {}) or {},
        "shinydex": row.get("shinydex", {}) or {},
        "casino_played": row.get("casino_played", 0),
        "casino_date": row.get("casino_date", ""),
    }
    result["coins"] = max(0, int(result.get("coins", 100)))
    result["casino_played"] = int(result.get("casino_played", 0))
    result["casino_date"] = result.get("casino_date") or ""
    return result


def load_player(pid: str) -> dict[str, Any]:
    if SUPABASE:
        try:
            response = SUPABASE.table("usuarios").select("*").eq("device_id", pid).limit(1).execute()
            return normalize(response.data[0] if response.data else None)
        except Exception:
            pass
    return normalize(LOCAL_PLAYERS.get(pid))


def save_player(pid: str, state: dict[str, Any]) -> None:
    LOCAL_PLAYERS[pid] = normalize(state)
    if SUPABASE:
        payload = {
            "device_id": pid,
            "monedas": state["coins"],
            "aciertos_totales": state["correct"],
            "fallos_totales": state["failures"],
            "racha_maxima": state["best_streak"],
            "shinies_seen": state["shinies_seen"],
            "xp": state["xp"],
            "level": state["level"],
            "achievements": state["achievements"],
            "favorites": state["favorites"],
            "team": state["team"],
            "cosmetics": state["cosmetics"],
            "active_cosmetic": state["active_cosmetic"],
            "missions_claimed": state["missions_claimed"],
            "casino_played": state["casino_played"],
            "casino_date": state["casino_date"],
            "wins": state["wins"],
            "losses": state["losses"],
            "pokedex": state["pokedex"],
            "shinydex": state["shinydex"],
        }
        try:
            SUPABASE.table("usuarios").upsert(payload, on_conflict="device_id").execute()
        except Exception:
            legacy = {"device_id": pid, "monedas": state["coins"], "aciertos_totales": state["correct"], "fallos_totales": state["failures"], "racha_maxima": state["best_streak"], "pokedex": state["pokedex"], "shinydex": state["shinydex"], "logros": state["achievements"], "equipo": state["team"]}
            try:
                SUPABASE.table("usuarios").upsert(legacy, on_conflict="device_id").execute()
            except Exception:
                pass


def daily_seed(pid: str) -> int:
    digest = hashlib.sha256(f"{pid}:{date.today().isoformat()}".encode()).hexdigest()
    return int(digest[:12], 16)


class NewPlayer(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=24)


class QuizAnswer(BaseModel):
    pokemon_id: int = Field(ge=1, le=1025)
    answer: str = Field(min_length=1, max_length=40)
    mode: str = Field(default="classic", pattern="^(classic|type|generation|evolution|name_all)$")


class NameAllSubmit(BaseModel):
    generation: int = Field(ge=1, le=9)
    names: list[str] = Field(max_length=1025)


class FeatureUpdate(BaseModel):
    action: str = Field(pattern="^(favorite|team_add|team_remove|cosmetic_equip)$")
    pokemon_id: int | None = Field(default=None, ge=1, le=1025)
    cosmetic: str | None = None


class MissionClaim(BaseModel):
    mission: str = Field(pattern="^(daily_correct|daily_shiny|daily_casino)$")


class CasinoBet(BaseModel):
    game: str = Field(pattern="^(slots|roulette)$")
    bet: int = Field(ge=BET_MIN, le=BET_MAX)
    choice: int | None = Field(default=None, ge=0, le=36)


@app.get("/")
def home() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.post("/api/players")
def create_player(payload: NewPlayer) -> dict[str, Any]:
    pid = player_id(payload.code or secrets.token_hex(4).upper())
    state = load_player(pid)
    save_player(pid, state)
    return {"code": pid, "state": state}


@app.get("/api/players/{code}")
def get_player(code: str) -> dict[str, Any]:
    pid = player_id(code)
    return {"code": pid, "state": load_player(pid)}


@app.get("/api/quiz/question")
async def quiz_question(
    code: str = Query(...),
    generation: int = Query(1, ge=1, le=9),
    mode: str = Query("classic", pattern="^(classic|type|generation|evolution)$"),
) -> dict[str, Any]:
    pid = player_id(code)
    low, high = GENERATION_RANGES[generation]
    pokemon_id = random.randint(low, high)
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
        if response.status_code != 200:
            raise HTTPException(502, "PokéAPI no está disponible ahora mismo.")
        data = response.json()
        pokemon_name = data["name"].capitalize()
        image = data["sprites"]["front_default"]
        if mode == "evolution":
            species = await client.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}")
            if species.status_code != 200:
                raise HTTPException(502, "No se pudo cargar la evolución.")
            next_name = await next_evolution(client, species.json()["evolution_chain"]["url"], data["name"])
            answer = next_name.capitalize() if next_name else "No evoluciona"
            options = {answer}
            while len(options) < 4:
                distractor = (await client.get(f"https://pokeapi.co/api/v2/pokemon/{random.randint(low, high)}")).json().get("name", "Pokémon").capitalize()
                options.add(distractor)
            return {"mode": mode, "pokemon_id": pokemon_id, "image": image, "shiny": question_shiny(pid, mode, pokemon_id), "prompt": f"¿En qué evoluciona {pokemon_name}?", "options": sorted(options)}
        if mode == "generation":
            answer = next(label for gen, label in GENERATION_LABELS.items() if GENERATION_RANGES[gen][0] <= pokemon_id <= GENERATION_RANGES[gen][1])
            return {"mode": mode, "pokemon_id": pokemon_id, "image": image, "shiny": question_shiny(pid, mode, pokemon_id), "prompt": "¿A qué generación pertenece este Pokémon?", "options": list(GENERATION_LABELS.values())}
        if mode == "type":
            types = " / ".join(t["type"]["name"].capitalize() for t in data.get("types", []))
            names = {pokemon_name}
            while len(names) < 4:
                distractor_id = random.randint(low, high)
                distractor = await client.get(f"https://pokeapi.co/api/v2/pokemon/{distractor_id}")
                if distractor.status_code == 200:
                    names.add(distractor.json()["name"].capitalize())
            return {"mode": mode, "pokemon_id": pokemon_id, "image": image, "shiny": question_shiny(pid, mode, pokemon_id), "prompt": f"Tipo: {types}. ¿Qué Pokémon es?", "options": sorted(names)}
    names = [s["name"] for s in data.get("forms", [])]
    answer = names[0].capitalize() if names else data["name"].capitalize()
    options = {answer}
    while len(options) < 4:
        options.add((await _pokemon_name(client, random.randint(low, high))))
    return {"mode": "classic", "pokemon_id": pokemon_id, "image": data["sprites"]["front_default"], "shiny": question_shiny(pid, "classic", pokemon_id), "prompt": "¿Cómo se llama este Pokémon?", "options": sorted(options)}


async def next_evolution(client: httpx.AsyncClient, chain_url: str, current: str) -> str | None:
    response = await client.get(chain_url)
    if response.status_code != 200:
        return None
    def walk(node: dict[str, Any]) -> str | None:
        if node.get("species", {}).get("name") == current:
            children = node.get("evolves_to", [])
            return children[0]["species"]["name"] if children else None
        for child in node.get("evolves_to", []):
            found = walk(child)
            if found:
                return found
        return None
    return walk(response.json()["chain"])


def register_catch(state: dict[str, Any], pokemon_id: int, name: str, is_shiny: bool | None = None) -> bool:
    """Registra una captura nueva; solo las capturas nuevas pueden ser shiny."""
    key = str(pokemon_id)
    if key in state["pokedex"]:
        return False
    is_shiny = random.random() < 0.05 if is_shiny is None else is_shiny
    state["pokedex"][key] = {"id": pokemon_id, "nombre": name.capitalize(), "shiny": is_shiny}
    if is_shiny:
        state["shinydex"][key] = {"id": pokemon_id, "nombre": name.capitalize()}
    return is_shiny


async def _pokemon_name(client: httpx.AsyncClient, pokemon_id: int) -> str:
    response = await client.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    if response.status_code != 200:
        return f"Pokémon {pokemon_id}"
    return response.json()["name"].capitalize()


@app.post("/api/quiz/answer")
async def quiz_answer(payload: QuizAnswer, code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(f"https://pokeapi.co/api/v2/pokemon/{payload.pokemon_id}")
    if response.status_code != 200:
        raise HTTPException(502, "PokéAPI no está disponible ahora mismo.")
    data = response.json()
    expected = data["name"]
    if payload.mode == "generation":
        expected = next(label for gen, label in GENERATION_LABELS.items() if GENERATION_RANGES[gen][0] <= payload.pokemon_id <= GENERATION_RANGES[gen][1])
    elif payload.mode == "type":
        expected = data["name"]
    elif payload.mode == "evolution":
        async with httpx.AsyncClient(timeout=8) as client:
            species = await client.get(f"https://pokeapi.co/api/v2/pokemon-species/{payload.pokemon_id}")
            expected_next = await next_evolution(client, species.json()["evolution_chain"]["url"], data["name"]) if species.status_code == 200 else None
        expected = expected_next or "No evoluciona"
    correct = expected.lower() == payload.answer.strip().lower()
    state = load_player(pid)
    if correct:
        state["correct"] += 1
        state["streak"] += 1
        state["best_streak"] = max(state["best_streak"], state["streak"])
        state["coins"] += 1
        state["xp"] += 10
        shiny = register_catch(state, payload.pokemon_id, data["name"], QUESTION_SHINY.pop(f"{pid}:{payload.mode}:{payload.pokemon_id}", False))
    else:
        state["failures"] += 1
        state["streak"] = 0
        shiny = False
    update_progress(state)
    save_player(pid, state)
    return {"correct": correct, "answer": expected.capitalize(), "shiny": shiny, "reward": 1 if correct else 0, "state": state}


async def generation_names(generation: int) -> list[str]:
    if generation in GENERATION_CACHE:
        return GENERATION_CACHE[generation]
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(f"https://pokeapi.co/api/v2/generation/{generation}")
    if response.status_code != 200:
        raise HTTPException(502, "No se pudo cargar esa generación.")
    names = sorted({item["name"].capitalize() for item in response.json().get("pokemon_species", [])})
    GENERATION_CACHE[generation] = names
    return names


async def generation_species(generation: int) -> list[dict[str, Any]]:
    if generation in GENERATION_SPECIES_CACHE:
        return GENERATION_SPECIES_CACHE[generation]
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(f"https://pokeapi.co/api/v2/generation/{generation}")
    if response.status_code != 200:
        raise HTTPException(502, "No se pudo cargar esa generación.")
    entries = []
    for item in response.json().get("pokemon_species", []):
        match = re.search(r"/pokemon-species/(\d+)/?$", item["url"])
        if match:
            entries.append({"id": int(match.group(1)), "name": item["name"].capitalize()})
    entries.sort(key=lambda item: item["id"])
    GENERATION_SPECIES_CACHE[generation] = entries
    return entries


@app.get("/api/minigames/name-all")
async def name_all_info(generation: int = Query(1, ge=1, le=9)) -> dict[str, Any]:
    names = await generation_names(generation)
    return {"generation": generation, "total": len(names), "seconds": max(60, len(names) * 3)}


@app.get("/api/minigames/name-all/question")
async def name_all_question(code: str = Query(...), generation: int = Query(1, ge=1, le=9), index: int = Query(0, ge=0)) -> dict[str, Any]:
    pid = player_id(code)
    entries = await generation_species(generation)
    if index >= len(entries):
        raise HTTPException(400, "El Name All ya ha terminado.")
    target = entries[index]
    choices = {target["name"]}
    while len(choices) < 4:
        distractor = entries[random.randrange(len(entries))]
        choices.add(distractor["name"])
    return {"index": index, "total": len(entries), "pokemon_id": target["id"], "image": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{target['id']}.png", "shiny": question_shiny(code, "name_all", target["id"]), "options": random.sample(list(choices), len(choices)), "prompt": f"Pregunta {index + 1} de {len(entries)}: ¿qué Pokémon es?"}


@app.post("/api/minigames/name-all/submit")
async def name_all_submit(payload: NameAllSubmit, code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    expected = set(await generation_names(payload.generation))
    submitted = {name.strip().capitalize() for name in payload.names if name.strip()}
    found = expected & submitted
    state = load_player(pid)
    perfect = found == expected
    reward = len(found)
    state["coins"] += reward
    save_player(pid, state)
    return {"found": len(found), "total": len(expected), "missing": sorted(expected - found)[:20], "perfect": perfect, "reward": reward, "state": state}


@app.get("/api/missions")
def missions(code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    state = load_player(pid)
    today = date.today().isoformat()
    claimed = state["missions_claimed"] if state.get("missions_claimed", {}).get("date") == today else {}
    return {"date": today, "missions": [
        {"id": "daily_correct", "title": "Entrenamiento diario", "description": "Consigue 5 aciertos", "progress": min(state["correct"], 5), "goal": 5, "reward": 10, "claimed": bool(claimed.get("daily_correct"))},
        {"id": "daily_shiny", "title": "Ojos de cazador", "description": "Ve una pregunta shiny", "progress": min(state["shinies_seen"], 1), "goal": 1, "reward": 15, "claimed": bool(claimed.get("daily_shiny"))},
        {"id": "daily_casino", "title": "Noche de arcade", "description": "Gana una partida del casino", "progress": min(state["wins"], 1), "goal": 1, "reward": 20, "claimed": bool(claimed.get("daily_casino"))},
    ]}


@app.post("/api/missions/claim")
def claim_mission(payload: MissionClaim, code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    state = load_player(pid)
    today = date.today().isoformat()
    if state.get("missions_claimed", {}).get("date") != today:
        state["missions_claimed"] = {"date": today}
    if state["missions_claimed"].get(payload.mission):
        raise HTTPException(400, "Misión ya reclamada hoy.")
    requirements = {"daily_correct": state["correct"] >= 5, "daily_shiny": state["shinies_seen"] >= 1, "daily_casino": state["wins"] >= 1}
    rewards = {"daily_correct": 10, "daily_shiny": 15, "daily_casino": 20}
    if not requirements[payload.mission]:
        raise HTTPException(400, "Aún no has completado esta misión.")
    state["missions_claimed"][payload.mission] = True
    state["coins"] += rewards[payload.mission]
    save_player(pid, state)
    return {"reward": rewards[payload.mission], "state": state}


@app.post("/api/features")
def update_features(payload: FeatureUpdate, code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    state = load_player(pid)
    if payload.action in {"favorite", "team_add", "team_remove"} and payload.pokemon_id is None:
        raise HTTPException(400, "Falta el ID del Pokémon.")
    if payload.action == "favorite":
        values = set(state["favorites"])
        values.remove(payload.pokemon_id) if payload.pokemon_id in values else values.add(payload.pokemon_id)
        state["favorites"] = sorted(values)
    elif payload.action == "team_add":
        if str(payload.pokemon_id) not in state["pokedex"]:
            raise HTTPException(400, "Solo puedes añadir Pokémon de tu Pokédex.")
        if payload.pokemon_id not in state["team"] and len(state["team"]) < 6:
            state["team"].append(payload.pokemon_id)
    elif payload.action == "team_remove":
        state["team"] = [pid for pid in state["team"] if pid != payload.pokemon_id]
    elif payload.action == "cosmetic_equip":
        if payload.cosmetic not in state["cosmetics"]:
            raise HTTPException(400, "Cosmético no desbloqueado.")
        state["active_cosmetic"] = payload.cosmetic
    save_player(pid, state)
    return {"state": state}


@app.post("/api/shop/buy")
def buy_cosmetic(cosmetic: str = Query(..., pattern="^(neon|forest|galaxy)$"), code: str = Query(...)) -> dict[str, Any]:
    prices = {"neon": 50, "forest": 80, "galaxy": 150}
    pid = player_id(code)
    state = load_player(pid)
    if cosmetic in state["cosmetics"]:
        raise HTTPException(400, "Ya tienes este cosmético.")
    if state["coins"] < prices[cosmetic]:
        raise HTTPException(400, "No tienes suficientes PokéCoins.")
    state["coins"] -= prices[cosmetic]
    state["cosmetics"].append(cosmetic)
    state["active_cosmetic"] = cosmetic
    save_player(pid, state)
    return {"state": state, "cosmetic": cosmetic}


@app.get("/api/leaderboard")
def leaderboard() -> dict[str, Any]:
    if SUPABASE:
        try:
            response = SUPABASE.table("usuarios").select("apodo_publico,aciertos_totales,racha_maxima").order("aciertos_totales", desc=True).limit(10).execute()
            return {"rows": response.data or []}
        except Exception:
            pass
    rows = [{"apodo_publico": key, "aciertos_totales": value["correct"], "racha_maxima": value["best_streak"]} for key, value in LOCAL_PLAYERS.items()]
    return {"rows": sorted(rows, key=lambda row: row["aciertos_totales"], reverse=True)[:10]}


@app.post("/api/battle/training")
def training_battle(code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    state = load_player(pid)
    if not state["team"]:
        raise HTTPException(400, "Añade al menos un Pokémon a tu equipo.")
    power = len(state["team"]) * 20 + random.randint(0, 80)
    opponent = random.randint(20, 180)
    won = power >= opponent
    state["wins" if won else "losses"] += 1
    if won:
        state["coins"] += 5
        state["xp"] += 20
        update_progress(state)
    save_player(pid, state)
    return {"won": won, "power": power, "opponent": opponent, "reward": 5 if won else 0, "state": state}


@app.post("/api/casino/play")
def casino(payload: CasinoBet, code: str = Query(...)) -> dict[str, Any]:
    pid = player_id(code)
    state = load_player(pid)
    today = date.today().isoformat()
    if state.get("casino_date") != today:
        state["casino_date"], state["casino_played"] = today, 0
    if state["casino_played"] >= DAILY_LIMIT:
        raise HTTPException(429, f"Límite diario alcanzado ({DAILY_LIMIT} partidas).")
    if state["coins"] < payload.bet:
        raise HTTPException(400, "No tienes suficientes PokéCoins.")
    state["coins"] -= payload.bet
    state["casino_played"] += 1
    if payload.game == "slots":
        symbols = ["🍒", "⚡", "🔥", "💎", "⭐"]
        roll = [random.choice(symbols) for _ in range(3)]
        multiplier = 8 if len(set(roll)) == 1 else 3 if len(set(roll)) == 2 else 0
        payout = payload.bet * multiplier
        result = {"roll": roll, "multiplier": multiplier, "payout": payout}
    else:
        number = random.randint(0, 36)
        payout = payload.bet * 35 if payload.choice == number else 0
        result = {"number": number, "choice": payload.choice, "payout": payout}
    state["coins"] += result["payout"]
    if result["payout"]:
        state["wins"] += 1
    else:
        state["losses"] += 1
    save_player(pid, state)
    return {**result, "state": state, "plays_left": DAILY_LIMIT - state["casino_played"]}
