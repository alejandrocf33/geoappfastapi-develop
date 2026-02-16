# GeoAPIs

API REST para gestión y consulta de infraestructura geoespacial de red. Construida con FastAPI y PostgreSQL/PostGIS.

---

## Contenido

- [Inicio rápido](#inicio-rápido)
- [Requisitos](#requisitos)
- [Configuración por entorno](#configuración-por-entorno)
- [Variables de entorno](#variables-de-entorno)
- [Arranque del servidor](#arranque-del-servidor)
- [Endpoints](#endpoints)
- [Autenticación](#autenticación)
- [Comportamiento por entorno](#comportamiento-por-entorno)
- [Caché](#caché)
- [Estructura del proyecto](#estructura-del-proyecto)

---

## Inicio rápido

```bash
# 1. Clonar y entrar al directorio
git clone <repo-url>
cd geoappfastapi-develop

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv_geo
# Para Linux/Mac: source venv_geo/bin/activate
# Para Windows (PowerShell): .\venv_geo\Scripts\Activate.ps1

pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales del entorno correspondiente

# 4. Iniciar el servidor
python run.py --open
```

El servidor queda disponible en `http://localhost:8000`.

| URL | Descripción |
| --- | --- |
| `http://localhost:8000/docs` | Swagger UI interactivo (solo local) |
| `http://localhost:8000/redoc` | ReDoc (solo local) |
| `http://localhost:8000/openapi.json` | Esquema OpenAPI (solo local) |

> **Nota:** La documentación interactiva solo está disponible en entorno local (cuando `ALLOWED_LOCAL_ORIGIN` está configurado). En QA y producción estos endpoints devuelven 404.

---

## Requisitos

- Python 3.10+
- PostgreSQL con extensión PostGIS
- Acceso a base de datos (Supabase o instancia propia)

**Dependencias Python** (`requirements.txt`):

```text
fastapi[all]
uvicorn[standard]
psycopg2-binary
geojson
cachetools
python-dotenv
geoalchemy2
SQLAlchemy
python-multipart
```

---

## Configuración por entorno

El proyecto usa archivos `.env` ignorados por git (ver `.gitignore`). Copiar el archivo correspondiente:

| Entorno | Archivo fuente | Comando |
| --- | --- | --- |
| Local / Desarrollo | `.env.example` | `cp .env.example .env` |
| QA | `.env.qa` | `cp .env.qa .env` |
| Producción | `.env.prod` | `cp .env.prod .env` |

> **Nota:** `.env`, `.env.qa` y `.env.prod` están en `.gitignore` y nunca se versionan.
> Solo `.env.example` se versiona como plantilla de referencia sin credenciales.

---

## Variables de entorno

| Variable | Requerida | Descripción | Ejemplo |
| --- | :---: | --- | --- |
| `DB_HOST` | Sí | Host de la base de datos | `aws-1-sa-east-1.pooler.supabase.com` |
| `DB_PORT` | Sí | Puerto de la base de datos | `6543` |
| `DB_NAME` | Sí | Nombre de la base de datos | `postgres` |
| `DB_USER` | Sí | Usuario de la base de datos | `postgres.xxxxx` |
| `DB_PASSWORD` | Sí | Contraseña de la base de datos | |
| `API_USERNAME` | No | Usuario para HTTP Basic Auth | |
| `API_PASSWORD` | No | Contraseña para HTTP Basic Auth | |
| `APP_DEBUG` | No | Modo debug (`true`/`false`) | `false` en prod |
| `OFFICE_IP` | No | IP de oficina con acceso directo | `181.234.203.142` |
| `ORACLE_REFERER_PATTERN` | No | Regex del referer Oracle Cloud/ETA | ver `.env.example` |
| `ALLOWED_LOCAL_ORIGIN` | No | Origen local permitido (solo desarrollo) | `http://127.0.0.1:5500` |

---

## Arranque del servidor

```bash
# Inicio estándar
python run.py

# Abrir navegador automáticamente al iniciar
python run.py --open

# Generar colección Postman al iniciar
python run.py --postman

# Resetear secuencias de BD antes de iniciar
python run.py --reset-sequences

# Producción (Heroku / contenedor)
uvicorn app.main:app --host=0.0.0.0 --port=8000
```

El `Procfile` para Heroku usa: `uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-5000}`

---

## Endpoints

Todos los endpoints requieren **HTTP Basic Auth** y están bajo el prefijo `/api`.

### Lectura (GET)

| Endpoint | Parámetros principales | Descripción |
| --- | --- | --- |
| `GET /api/camaras` | `lat`, `lon`, `radio_interno`, `radio_externo` | Cámaras en radio. Sin params: primeras 100 |
| `GET /api/all_camaras` | — | Todas las cámaras (caché 6h) |
| `GET /api/cables` | `lat`, `lon`, `radio_externo` | Cables corporativos en radio |
| `GET /api/all_cables` | — | Todos los cables (caché 6h) |
| `GET /api/centrales` | `lat`, `lon`, `radio_externo` | Centrales en radio |
| `GET /api/all_centrales` | — | Todas las centrales (caché 6h) |
| `GET /api/empalmes` | `lat`, `lon`, `radio_interno`, `radio_externo` | Empalmes en radio |
| `GET /api/all_empalmes` | — | Todos los empalmes (caché 6h) |
| `GET /api/reservas` | `lat`, `lon`, `radio_interno`, `radio_externo` | Reservas en radio |
| `GET /api/all_reservas` | — | Todas las reservas (caché 6h) |

### Lógica / Análisis espacial (GET)

| Endpoint | Parámetros principales | Descripción |
| --- | --- | --- |
| `GET /api/camaras_en_falla` | `lat`, `lon`, `distancia`, `desviacion` | Detecta cámaras potencialmente en falla |
| `GET /api/cables_cercanos` | `lat`, `lon`, `distancia`, `limite`, `incluir_troncales`, `nombre_cable` | Cables cercanos a un punto con filtros |
| `GET /api/linea_en_ruta_red` | `lat`, `lon`, `distancia`, `incluir_linea` | Ruta navegada sobre la red de cables |
| `GET /api/nodos_alcanzables_en_ruta_red` | `lat`, `lon`, `distancia`, `margen_factor` (default: `0.9`) | Nodos alcanzables desde un punto a una distancia |

### Escritura (POST)

| Endpoint | Body | Descripción |
| --- | --- | --- |
| `POST /api/camaras` | `Camara` | Crear nueva cámara |
| `POST /api/cable_corporativo` | `CableCorporativo` | Crear nuevo cable corporativo |
| `POST /api/centrales` | `Central` | Crear nueva central |
| `POST /api/empalmes` | `Empalme` | Crear nuevo empalme |
| `POST /api/reservas` | `Reserva` | Crear nueva reserva |

Todos los endpoints de escritura aceptan **dos formatos de geometría**:

- Coordenadas directas: campos `latitud` y `longitud` (WGS84)
- WKT: campo `geometry` con texto Well-Known Text

El header opcional `user-header` permite especificar el usuario para trazabilidad en `created_by` / `updated_by`.

---

## Autenticación

La API usa **HTTP Basic Auth** en todos los endpoints.

```bash
# curl
curl -u "usuario:contraseña" https://api-host/api/camaras
```

```python
# Python requests
import requests
response = requests.get(
    "https://api-host/api/camaras",
    auth=("usuario", "contraseña")
)
```

Las credenciales se configuran con `API_USERNAME` y `API_PASSWORD` en el `.env`.

**Respuesta 401:**

```json
{"detail": "Credenciales incorrectas"}
```

---

## Comportamiento por entorno

Dos variables controlan todo el comportamiento de seguridad y documentación:

- **`APP_DEBUG`** — Controla el middleware y los errores detallados
- **`ALLOWED_LOCAL_ORIGIN`** — Controla la documentación interactiva

### Matriz de comportamiento

| Funcionalidad | Local | QA | Producción |
| --- | --- | --- | --- |
| `APP_DEBUG` | `true` | `true` | `false` |
| `ALLOWED_LOCAL_ORIGIN` | `http://127.0.0.1:5500` | vacío | vacío |
| `/docs`, `/redoc`, `/openapi.json` | ✅ Disponible | ❌ 404 | ❌ 404 |
| Middleware de acceso | Solo log (no bloquea) | Bloquea con 403 | Bloquea con 403 |
| Traceback en errores 500 | Visible en respuesta | Visible en respuesta | Oculto |

### Middleware de validación de acceso

En **QA y producción** (`APP_DEBUG=false`), el middleware valida el origen de cada petición. Se permite el acceso si se cumple **alguna** de estas condiciones:

| Condición | Variable de entorno | Descripción |
| --- | --- | --- |
| Referer coincide con patrón Oracle Cloud | `ORACLE_REFERER_PATTERN` | Integración con ETA / Oracle Spatial |
| `X-Forwarded-For` es la IP de oficina | `OFFICE_IP` | Acceso directo desde red interna |
| Origin/Referer coincide con origen local | `ALLOWED_LOCAL_ORIGIN` | Acceso desde origen permitido |

Las peticiones que no cumplen ninguna condición reciben `403 Acceso denegado`.

En **local** (`APP_DEBUG=true`), el middleware solo registra en consola el origen de cada petición sin bloquear ninguna. Esto permite usar Postman, curl, navegador u cualquier herramienta sin restricciones.

### Documentación interactiva

Swagger UI (`/docs`), ReDoc (`/redoc`) y el esquema OpenAPI (`/openapi.json`) solo están disponibles cuando `ALLOWED_LOCAL_ORIGIN` tiene un valor configurado. Esto asegura que la documentación de la API no quede expuesta en QA ni producción.

### Configuración recomendada por entorno

| Variable | Local | QA | Producción |
| --- | --- | --- | --- |
| `APP_DEBUG` | `true` | `true` | `false` |
| `ALLOWED_LOCAL_ORIGIN` | `http://127.0.0.1:5500` | vacío | vacío |
| `ORACLE_REFERER_PATTERN` | vacío o patrón | patrón completo | patrón completo |
| `OFFICE_IP` | vacío o IP real | IP real | IP real |

---

## Caché

Los endpoints `all_*` usan caché en memoria con TTL de **6 horas** (`cachetools.TTLCache`).

El caché se invalida al reiniciar el servidor. Para forzar datos frescos en desarrollo, reiniciar el proceso.

---

## Estructura del proyecto

```text
geoappfastapi-develop/
├── app/
│   ├── routes/
│   │   ├── cache_routes.py      # Endpoints de lectura (GET)
│   │   ├── logic_routes.py      # Endpoints de análisis espacial (GET)
│   │   ├── write_routes.py      # Endpoints de escritura (POST)
│   │   ├── api_models.py        # Modelos de respuesta Pydantic
│   │   └── error_models.py      # Modelos de error estandarizados
│   ├── auth.py                  # Autenticación HTTP Basic
│   ├── config.py                # Carga de variables de entorno
│   ├── database.py              # Conexión psycopg2 a PostgreSQL
│   ├── db_access.py             # Queries y lógica de acceso a BD
│   ├── db_init.py               # Inicialización y migración de tablas
│   ├── models.py                # Modelos SQLAlchemy
│   ├── reset_sequences.py       # Reset de secuencias PostgreSQL
│   └── main.py                  # Aplicación FastAPI + middleware
├── sql/                         # Scripts SQL (funciones PostGIS)
│   ├── create_table_red.sql
│   ├── create_fn_punto_en_ruta_red.sql
│   ├── create_get_nearest_cable.sql
│   ├── get_cables_cercanos.sql
│   └── fn_nodos_alcanzables_en_ruta_red.sql  # Despliegue manual requerido
├── run.py                       # Script de arranque con opciones CLI
├── setup.py                     # Configuración inicial del entorno
├── requirements.txt
├── Procfile                     # Despliegue Heroku
├── .env.example                 # Plantilla de variables (versionado en git)
├── .env.qa                      # Variables QA (ignorado por git)
├── .env.prod                    # Variables producción (ignorado por git)
└── .env                         # Variables activas (ignorado por git)
```

---

## Notas importantes

- **`fn_nodos_alcanzables_en_ruta_red.sql`** debe desplegarse manualmente en la BD; `setup.py` no lo ejecuta automáticamente.
- **Cables**: usan la propiedad `id_text` en el JSONB. El resto de entidades usan `id_texto`.
- **Secuencias PostgreSQL**: usar `python run.py --reset-sequences` si hay conflictos de ID tras migraciones o importaciones de datos.
- **Postman**: generar la colección con `python run.py --postman` o importar directamente desde `http://localhost:8000/openapi.json`.
- **Credenciales Postman**: la colección generada usa placeholders `admin`/`password`; reemplazarlos antes de usar.

---

## Notas técnicas: `/api/nodos_alcanzables_en_ruta_red`

### Comportamiento del parámetro `margen_factor`

El `margen_factor` define el umbral mínimo de distancia aceptable para retornar un nodo:

```text
umbral_minimo = distancia_solicitada × margen_factor
```

Solo se retornan nodos cuya `distancia_acumulada >= umbral_minimo`. El valor por defecto es `0.9` (tolerancia del ±10%).

**¿Por qué no usar `0.999`?**
Los cables de la red son segmentos largos (100–700m). La distancia exacta solicitada casi nunca coincide con un nodo del grafo — cae en medio de un segmento. Un `margen_factor=0.999` exige que el nodo esté a máximo 0.1% de la distancia exacta, lo que produce resultados vacíos en la mayoría de casos.

| `margen_factor` | Tolerancia | Comportamiento |
| --- | --- | --- |
| `0.999` | ±0.1% | Muy estricto — vacío en la mayoría de casos |
| `0.9` | ±10% | Recomendado — retorna nodos del segmento más cercano |
| `0.8` | ±20% | Amplio — retorna más nodos, menor precisión |

### Coordenadas de prueba validadas

Para verificar el funcionamiento del endpoint use estas coordenadas que garantizan resultados:

```text
lon:           -74.1260221427765
lat:             4.5718904292518
distancia:     140
margen_factor: 0.9  (o usar el default)
```

### Calidad de datos: self-loops en tabla `red`

La tabla `red` puede contener cables con `source = target` (self-loops). pgRouting no puede navegar a través de ellos, por lo que los nodos conectados exclusivamente a self-loops no serán alcanzables. Para verificar:

```sql
SELECT COUNT(*) FROM red WHERE source = target;
```
