# GeoAPIs

API REST para gestion y consulta de infraestructura geoespacial de red. Construida con FastAPI y PostgreSQL/PostGIS.

---

## Inicio rapido

```bash
# 1. Clonar y entrar al directorio
git clone <repo-url>
cd geoappfastapi-develop

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv_geo
# Linux/Mac: source venv_geo/bin/activate
# Windows:   .\venv_geo\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales del entorno correspondiente

# 4. Iniciar el servidor
python run.py --open
```

El servidor queda disponible en `http://localhost:8000`.

| URL | Descripcion |
| --- | --- |
| `http://localhost:8000/docs` | Swagger UI interactivo (solo local) |
| `http://localhost:8000/redoc` | ReDoc (solo local) |

---

## Documentacion

| Documento | Descripcion |
| --- | --- |
| [Referencia de APIs](docs/api-referencia.md) | Endpoints completos: parametros, respuestas, ejemplos |
| [Configuracion](docs/configuracion.md) | Variables de entorno, middleware, comportamiento por entorno |
| [Autenticacion](docs/autenticacion.md) | HTTP Basic Auth: formato, ejemplos, errores |
| [Formato GeoJSON](docs/formato-geojson.md) | Estructura de respuestas GeoJSON, propiedades por entidad |
| [Guia Postman](docs/guia-postman.md) | Importar coleccion, configurar auth, ejemplos de uso |
| [Manejo de secuencias](docs/manejo-secuencias.md) | Reset de secuencias PostgreSQL tras migraciones |

---

## Requisitos

- Python 3.10+
- PostgreSQL con extension PostGIS
- Acceso a base de datos (Supabase o instancia propia)

---

## Arranque del servidor

```bash
python run.py              # Inicio estandar
python run.py --open       # Abrir navegador al iniciar
python run.py --postman    # Generar coleccion Postman al iniciar
python run.py --reset-sequences  # Resetear secuencias de BD antes de iniciar
```

Produccion (Railway / contenedor): `uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-5000}`

---

## Estructura del proyecto

```
geoappfastapi-develop/
├── app/
│   ├── routes/
│   │   ├── cache_routes.py      # Endpoints de lectura (GET)
│   │   ├── logic_routes.py      # Endpoints de analisis espacial (GET)
│   │   ├── write_routes.py      # Endpoints de escritura (POST)
│   │   ├── api_models.py        # Modelos de respuesta Pydantic
│   │   └── error_models.py      # Modelos de error estandarizados
│   ├── auth.py                  # Autenticacion HTTP Basic
│   ├── config.py                # Carga de variables de entorno
│   ├── database.py              # Conexion psycopg2 a PostgreSQL
│   ├── db_access.py             # Queries y logica de acceso a BD
│   ├── db_init.py               # Inicializacion y migracion de tablas
│   ├── models.py                # Modelos SQLAlchemy
│   ├── reset_sequences.py       # Reset de secuencias PostgreSQL
│   └── main.py                  # Aplicacion FastAPI + middleware
├── docs/                        # Documentacion del proyecto
├── front/                       # Frontend (plugin Oracle Cloud + mapa)
├── sql/                         # Scripts SQL (funciones PostGIS)
├── requirements.txt
├── Procfile                     # Despliegue Railway
├── .env.example                 # Plantilla de variables (versionado)
└── run.py                       # Script de arranque con opciones CLI
```

---

## Notas importantes

- **`fn_nodos_alcanzables_en_ruta_red.sql`** debe desplegarse manualmente en la BD; `setup.py` no lo ejecuta automaticamente.
- **Cables** usan la propiedad `id_text` en el JSONB. El resto de entidades usan `id_texto`.
- **Secuencias PostgreSQL**: usar `python run.py --reset-sequences` si hay conflictos de ID tras migraciones.
- **Postman**: la coleccion generada usa placeholders `admin`/`password`; reemplazarlos antes de usar.
