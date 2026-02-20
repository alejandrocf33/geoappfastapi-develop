from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from .routes import cache_routes, logic_routes, write_routes
from .routes.api_models import ErrorResponse, ErrorCode
import traceback

from . import config as _config

app = FastAPI(
    title="GeoAPIs",
    description="""
    # API para gestión de infraestructura GEO

    ## Características

    * **Consultas geoespaciales** - Búsqueda de elementos por coordenadas y radio
    * **Operaciones de escritura** - Creación de elementos geoespaciales como cámaras, cables, centrales
    * **Análisis espacial** - Funciones avanzadas para análisis de infraestructura
    * **Autenticación básica** - Protección de endpoints mediante autenticación HTTP Basic

    ## Formatos de geometría

    Todos los endpoints soportan dos formatos para especificar geometrías:

    1. **Coordenadas directas** - Usando los campos `latitud` y `longitud`
    2. **Formato WKT** - Usando el campo `geometry` con geometría Well-Known Text

    ## Respuestas GeoJSON

    Las consultas devuelven resultados en formato GeoJSON compatible con librerías de mapas.
    """,
    version="1.0.0",
    # Documentación interactiva solo disponible en local (ALLOWED_LOCAL_ORIGIN configurado)
    docs_url="/docs" if _config.ALLOWED_LOCAL_ORIGIN else None,
    redoc_url="/redoc" if _config.ALLOWED_LOCAL_ORIGIN else None,
    openapi_url="/openapi.json" if _config.ALLOWED_LOCAL_ORIGIN else None,
    openapi_tags=[
        {
            "name": "Operaciones de Escritura",
            "description": "Endpoints para crear nuevos elementos geoespaciales en la base de datos como cámaras, cables, centrales, empalmes y reservas."
        },
        {
            "name": "Operaciones de Lectura",
            "description": "Endpoints para consultar elementos geoespaciales existentes, con opciones de filtrado por ubicación y distancia."
        },
        {
            "name": "Operaciones Lógicas",
            "description": "Endpoints para realizar operaciones analíticas y lógicas sobre datos geoespaciales, como detección de fallos y cálculo de rutas."
        }
    ],
    debug=_config.APP_DEBUG,
    contact={
        "name": "Equipo de Desarrollo GeoAPIs",
        "email": "geo-apis@example.com"
    },
    license_info={
        "name": "Propietario - Uso Interno",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware global para loguear origen de todas las peticiones
@app.middleware("http")
async def log_request_origin(request: Request, call_next):
    import re
    referer = request.headers.get("referer", "")
    origin = request.headers.get("origin", "")
    x_forwarded_for = request.headers.get("x-forwarded-for", "")
    host = request.headers.get("host", "")

    # En desarrollo (APP_DEBUG=true) el middleware solo registra, nunca bloquea
    if _config.APP_DEBUG:
        print(f"[API LOG] 🛠️  Desarrollo: Host={host} | Origin={origin} | Referer={referer} | X-Forwarded-For={x_forwarded_for}")
        response = await call_next(request)
        return response

    # En QA/Producción: validar origen estrictamente
    allowed_local_origin = _config.ALLOWED_LOCAL_ORIGIN
    local_ok = False
    if allowed_local_origin:
        local_ok = (origin.startswith(allowed_local_origin) if origin else False) or \
                   (referer.startswith(allowed_local_origin) if referer else False)
        if not local_ok and host:
            local_ok = host.startswith("localhost") or host.startswith("127.0.0.1")

    referer_ok = bool(re.match(_config.ORACLE_REFERER_PATTERN, referer)) if _config.ORACLE_REFERER_PATTERN else False
    ip_ok = bool(_config.OFFICE_IP) and x_forwarded_for.strip() == _config.OFFICE_IP

    if not (referer_ok or ip_ok or local_ok):
        print(f"[API LOG] ❌ Bloqueado: Host={host} | Origin={origin} | Referer={referer} | X-Forwarded-For={x_forwarded_for}")
        return JSONResponse(status_code=403, content={
            "status": "error",
            "message": "Acceso denegado",
            "host": host,
            "origin": origin,
            "referer": referer,
            "x_forwarded_for": x_forwarded_for
        })

    print(f"[API LOG] ✅ Producción: Referer={referer} | X-Forwarded-For={x_forwarded_for}")
    
    response = await call_next(request)
    return response

# Manejadores de errores
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador global para errores de validación de datos"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message="Error de validación en los datos de entrada",
            details={"errors": exc.errors()}
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador global para excepciones no controladas"""
    # En producción, podrías querer registrar el error pero no mostrar el traceback
    # al usuario por motivos de seguridad
    error_details = {"traceback": traceback.format_exception(type(exc), exc, exc.__traceback__)} if app.debug else None
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Error interno del servidor: {str(exc)}",
            details=error_details
        ).dict()
    )

@app.on_event("startup")
async def create_spatial_indexes():
    """Crea índices GIST sobre geography(geom) si no existen, para que ST_DWithin use índice."""
    from .database import get_connection
    tables = ["camaras", "cable_corporativo", "centrales", "empalmes", "reservas", "reportes_mal_estado"]
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for table in tables:
                    idx_name = f"idx_{table}_geom_geog"
                    cur.execute(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name}
                        ON {table} USING GIST ((geom::geography));
                    """)
                conn.commit()
        print("[STARTUP] Índices espaciales geography verificados/creados.")
    except Exception as e:
        print(f"[STARTUP] Advertencia al crear índices: {e}")

# Incluir las rutas modulares
app.include_router(cache_routes.router, prefix="/api")
app.include_router(logic_routes.router, prefix="/api")
app.include_router(write_routes.router, prefix="/api")
