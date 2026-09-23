# Pokémon Quiz Arcade 2.0

Migración inicial de Streamlit a FastAPI + HTML/CSS/JavaScript.

## Despliegue recomendado: Vercel

Esta versión está preparada para Vercel. Vercel detecta `app.py` como una aplicación FastAPI y ejecuta el backend como una función Python. El archivo `vercel.json` sirve `static/index.html` como contenido estático y envía únicamente las rutas `/api/*` al backend.

1. Sube el contenido de esta carpeta a un repositorio de GitHub. No subas `.venv`.
2. Entra en Vercel, pulsa **Add New → Project** e importa el repositorio.
3. Pulsa **Deploy** sin añadir Build Command ni Output Directory.
4. En **Settings → Environment Variables**, añade `SUPABASE_URL` y `SUPABASE_KEY` si vas a guardar los datos de los jugadores.
5. Si Vercel te asigna una URL personalizada, añade también `PUBLIC_BASE_URL` con esa URL y vuelve a desplegar.

La aplicación detecta automáticamente `VERCEL_URL`, configura CORS para los dominios `vercel.app` y conserva la configuración local con Uvicorn. Vercel limita las funciones del plan Hobby a proyectos personales y aplica límites de tiempo/uso; para este juego pequeño debería ser suficiente.

Guía oficial: [FastAPI en Vercel](https://vercel.com/docs/frameworks/backend/fastapi) · [Plan Hobby](https://vercel.com/docs/plans/hobby)

## Migración anterior: Render

El destino elegido es Render en el plan **Free**. El repositorio incluye `.python-version` con Python 3.13 para evitar que Render intente compilar `pydantic-core` con Python 3.14. El nombre de servicio propuesto es `pokemon-quiz-arcade`, por lo que Render intentará asignar `https://pokemon-quiz-arcade.onrender.com`. La disponibilidad exacta del subdominio se confirma al crear el servicio; si Render asigna otro, cambia `PUBLIC_BASE_URL` por la URL real.

1. Crea un repositorio en GitHub y sube el contenido de esta carpeta.
2. En Render elige **New → Web Service** y conecta ese repositorio.
3. Selecciona el plan **Free** —no `Starter`—, usa Build Command `pip install -r requirements.txt` y Start Command `uvicorn app:app --host 0.0.0.0 --port $PORT`.
4. Añade `SUPABASE_URL` y `SUPABASE_KEY` como variables secretas.
5. Añade `PUBLIC_BASE_URL` con la URL pública final.

Comprueba especialmente que `static/index.html` esté en GitHub. El repositorio debe contener `app.py` y la carpeta `static` en el mismo nivel. Si el código está dentro de una subcarpeta, configura esa subcarpeta como **Root Directory** en Render.

También puedes desplegarlo directamente con el [render.yaml](render.yaml). Render documenta este flujo para FastAPI y exige escuchar en `0.0.0.0` y en el puerto `$PORT`; además ofrece un subdominio `onrender.com` y permite añadir un dominio propio con HTTPS. [Guía oficial de FastAPI en Render](https://render.com/docs/deploy-fastapi) · [Dominios personalizados](https://render.com/docs/custom-domains).

El plan Free se duerme después de 15 minutos sin tráfico y el primer acceso posterior puede tardar aproximadamente un minuto. No uses este plan para pagos o datos críticos; tu progreso debe seguir guardándose en Supabase.

Si Render conserva la versión anterior, abre **Manual Deploy → Clear build cache & deploy**. Render permite fijar Python mediante `.python-version` o `PYTHON_VERSION`; aquí se ha usado la primera opción. [Documentación de versiones Python](https://render.com/docs/python-version).

La selección de minijuegos incluye:

- Adivina el Pokémon por sus tipos.
- Adivina la generación mostrando su imagen.
- Adivina la siguiente evolución, incluida la opción "No evoluciona".
- Name All: escribe los Pokémon únicos de una generación; los duplicados no cuentan y completar todos da una bonificación.
- Name All ahora funciona por preguntas tipo Kahoot: cuatro opciones de colores, selección visible, botón de respuesta y avance manual.
- Cada acierto intenta capturar el Pokémon; existe un 5% de probabilidad de shiny y se guarda en Pokédex/ShinyDex.
- Las preguntas indican visualmente si son normales o shiny y muestran la respuesta correcta después de responder.
- Todos los minijuegos normales y Name All entregan exactamente 1 Poké-Coin por acierto.
- El avance vuelve a ser manual con “Siguiente pregunta” y Pokédex/ShinyDex incluyen filtro por generación.

También incluye un MVP funcional de niveles/XP, logros, misiones diarias reclamables, ranking, tienda de cosméticos, favoritos, equipo de hasta seis Pokémon, combate de entrenamiento y sonidos de acierto/fallo. Si quieres persistir estos datos en Supabase, ejecuta el `supabase_migration.sql` actualizado.

## Ejecutar

```powershell
cd pokemon_arcade
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SUPABASE_URL = "https://tu-proyecto.supabase.co"
$env:SUPABASE_KEY = "tu-clave"
python -m uvicorn app:app --reload
```

Importante: en tu equipo hay Python 3.13 y 3.14. El error `No module named fastapi` apareció porque `pip` instaló FastAPI en 3.13, pero `uvicorn` se lanzó con 3.14. Dentro del entorno virtual, usa siempre `python -m pip` y `python -m uvicorn`.

Abre <http://127.0.0.1:8000>. Si no configuras Supabase, usa almacenamiento temporal en memoria para poder probar la interfaz.

## Supabase

La tabla `usuarios` existente debe conservar `device_id`, `monedas`, `aciertos_totales` y `racha_maxima`. Para el MVP se pueden añadir estas columnas:

```sql
alter table usuarios add column if not exists casino_played integer default 0;
alter table usuarios add column if not exists casino_date text default '';
alter table usuarios add column if not exists wins integer default 0;
alter table usuarios add column if not exists losses integer default 0;
```

El casino usa solo monedas virtuales, valida la apuesta en el servidor y limita a 10 partidas por día. Para producción conviene añadir autenticación real, rate limiting y registrar cada transacción en una tabla de movimientos.
