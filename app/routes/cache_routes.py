from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from ..auth import authenticate
from ..db_access import (
    get_camaras_from_db,
    get_all_camaras_from_db,
    get_cables_corporativos_from_db,
    get_all_cables_corporativos_from_db,
    get_centrales_from_db,
    get_all_centrales_from_db,
    get_empalmes_from_db,
    get_all_empalmes_from_db,
    get_reservas_from_db,
    get_all_reservas_from_db
)
import cachetools
from cachetools import cached
from .api_models import (
    CamarasConsultaResponse,
    CablesConsultaResponse,
    CentralesConsultaResponse,
    EmpalmeConsultaResponse,
    ReservaConsultaResponse
)
from .error_models import responses, create_error_response, ErrorCode

router = APIRouter(tags=["Operaciones de Lectura"])

# Crear una caché global para almacenar datos
cache = cachetools.TTLCache(maxsize=100, ttl=21600)  # 6 horas de TTL

@cached(cache, key=lambda *args, **kwargs: "all_camaras_cache")
def cached_get_all_camaras_from_db():
    return get_all_camaras_from_db()

@cached(cache, key=lambda *args, **kwargs: "all_cables_corporativos_cache")
def cached_get_all_cables_corporativos_from_db():
    return get_all_cables_corporativos_from_db()

@cached(cache, key=lambda *args, **kwargs: "all_centrales_cache")
def cached_get_all_centrales_from_db():
    return get_all_centrales_from_db()

@cached(cache, key=lambda *args, **kwargs: "all_empalmes_cache")
def cached_get_all_empalmes_from_db():
    return get_all_empalmes_from_db()

@cached(cache, key=lambda *args, **kwargs: "all_reservas_cache")
def cached_get_all_reservas_from_db():
    return get_all_reservas_from_db()

@router.get(
    "/camaras",
    response_model=CamarasConsultaResponse,
    summary="Consultar cámaras",
    description="Obtiene las cámaras dentro de un radio especificado alrededor de un punto. Si no se especifican parámetros, retorna las primeras 100 cámaras.",
    response_description="GeoJSON FeatureCollection con las cámaras encontradas",
    responses={
        status.HTTP_401_UNAUTHORIZED: responses[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_404_NOT_FOUND: {
            "model": responses[status.HTTP_404_NOT_FOUND]["model"],
            "description": "No se encontraron cámaras con los criterios especificados",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": "not_found",
                        "message": "No se encontraron cámaras en el área especificada",
                        "details": {
                            "radio_externo": 500,
                            "lat": 4.6737,
                            "lon": -74.0617
                        }
                    }
                }
            }
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: responses[status.HTTP_422_UNPROCESSABLE_ENTITY]
    }
)
def get_camaras(
    lat: float | None = Query(None, description="Latitud del punto central de búsqueda (en grados decimales)"),
    lon: float | None = Query(None, description="Longitud del punto central de búsqueda (en grados decimales)"),
    radio_interno: float | None = Query(None, description="Radio interno en metros (excluye elementos más cercanos que esta distancia)"),
    radio_externo: float | None = Query(None, description="Radio externo en metros (límite máximo de búsqueda)"),
    user: str = Depends(authenticate)
):
    """
    Consulta cámaras en la base de datos, opcionalmente filtradas por ubicación.
    
    Parámetros:
    - **lat**: Latitud del punto central de búsqueda en grados decimales (WGS84)
    - **lon**: Longitud del punto central de búsqueda en grados decimales (WGS84)
    - **radio_interno**: Radio interno en metros (excluye elementos más cercanos que esta distancia)
    - **radio_externo**: Radio externo en metros (límite máximo de búsqueda)
    
    Si se proporcionan todos los parámetros, se realiza una búsqueda espacial.
    Si no, se devuelven las primeras 100 cámaras en la base de datos.
    
    La respuesta incluye un GeoJSON FeatureCollection con las cámaras encontradas.
    """
    return JSONResponse(content=get_camaras_from_db(lat, lon, radio_interno, radio_externo))

@router.get(
    "/all_camaras",
    response_model=CamarasConsultaResponse,
    summary="Consultar todas las cámaras",
    description="Obtiene todas las cámaras registradas en la base de datos. Utiliza una caché de 6 horas para mejorar el rendimiento.",
    response_description="GeoJSON FeatureCollection con todas las cámaras",
    responses={
        status.HTTP_401_UNAUTHORIZED: responses[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": responses[status.HTTP_500_INTERNAL_SERVER_ERROR]["model"],
            "description": "Error al consultar la base de datos",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": "database_error",
                        "message": "Error al consultar la base de datos",
                        "details": {
                            "error_type": "connection_error"
                        }
                    }
                }
            }
        }
    }
)
def get_all_camaras(user: str = Depends(authenticate)):
    """
    Devuelve todas las cámaras registradas en el sistema.
    
    La respuesta es un GeoJSON FeatureCollection que contiene todas las cámaras.
    
    Este endpoint utiliza una caché con un tiempo de vida (TTL) de 6 horas para mejorar el rendimiento.
    """
    return JSONResponse(content=cached_get_all_camaras_from_db())

@router.get(
    "/cables",
    response_model=CablesConsultaResponse,
    summary="Consultar cables corporativos",
    description="Obtiene los cables corporativos dentro de un radio especificado alrededor de un punto. Si no se especifican parámetros, retorna los primeros 100 cables.",
    response_description="GeoJSON FeatureCollection con los cables encontrados"
)
def get_cables_corporativos(
    lat: float | None = Query(None, description="Latitud del punto central de búsqueda (en grados decimales)"),
    lon: float | None = Query(None, description="Longitud del punto central de búsqueda (en grados decimales)"),
    radio_externo: float | None = Query(None, description="Radio externo en metros (límite máximo de búsqueda)"),
    user: str = Depends(authenticate)
):
    """
    Consulta cables corporativos en la base de datos, opcionalmente filtrados por ubicación.
    
    Parámetros:
    - **lat**: Latitud del punto central de búsqueda en grados decimales (WGS84)
    - **lon**: Longitud del punto central de búsqueda en grados decimales (WGS84)
    - **radio_externo**: Radio externo en metros (límite máximo de búsqueda)
    
    Si se proporcionan todos los parámetros, se realiza una búsqueda espacial.
    Si no, se devuelven los primeros 100 cables en la base de datos.
    """
    return JSONResponse(content=get_cables_corporativos_from_db(lat, lon, 0, radio_externo))

@router.get(
    "/all_cables",
    response_model=CablesConsultaResponse,
    summary="Consultar todos los cables",
    description="Obtiene todos los cables corporativos registrados en la base de datos. Utiliza una caché de 6 horas para mejorar el rendimiento.",
    response_description="GeoJSON FeatureCollection con todos los cables"
)
def get_all_cables_corporativos(user: str = Depends(authenticate)):
    """
    Devuelve todos los cables corporativos registrados en el sistema.
    
    La respuesta es un GeoJSON FeatureCollection que contiene todos los cables.
    
    Este endpoint utiliza una caché con un tiempo de vida (TTL) de 6 horas para mejorar el rendimiento.
    """
    return JSONResponse(content=cached_get_all_cables_corporativos_from_db())

@router.get(
    "/centrales",
    response_model=CentralesConsultaResponse,
    summary="Consultar centrales",
    description="Obtiene las centrales dentro de un radio especificado alrededor de un punto. Si no se especifican parámetros, retorna las primeras 100 centrales.",
    response_description="GeoJSON FeatureCollection con las centrales encontradas"
)
def get_centrales(
    lat: float | None = Query(None, description="Latitud del punto central de búsqueda (en grados decimales)"),
    lon: float | None = Query(None, description="Longitud del punto central de búsqueda (en grados decimales)"),
    radio_externo: float | None = Query(None, description="Radio externo en metros (límite máximo de búsqueda)"),
    user: str = Depends(authenticate)
):
    """
    Consulta centrales en la base de datos, opcionalmente filtradas por ubicación.
    
    Parámetros:
    - **lat**: Latitud del punto central de búsqueda en grados decimales (WGS84)
    - **lon**: Longitud del punto central de búsqueda en grados decimales (WGS84)
    - **radio_externo**: Radio externo en metros (límite máximo de búsqueda)
    
    Si se proporcionan todos los parámetros, se realiza una búsqueda espacial.
    Si no, se devuelven las primeras 100 centrales en la base de datos.
    """
    return JSONResponse(content=get_centrales_from_db(lat, lon, 0, radio_externo))

@router.get(
    "/all_centrales",
    response_model=CentralesConsultaResponse,
    summary="Consultar todas las centrales",
    description="Obtiene todas las centrales registradas en la base de datos. Utiliza una caché de 6 horas para mejorar el rendimiento.",
    response_description="GeoJSON FeatureCollection con todas las centrales"
)
def get_all_centrales(user: str = Depends(authenticate)):
    """
    Devuelve todas las centrales registradas en el sistema.
    
    La respuesta es un GeoJSON FeatureCollection que contiene todas las centrales.
    
    Este endpoint utiliza una caché con un tiempo de vida (TTL) de 6 horas para mejorar el rendimiento.
    """
    return JSONResponse(content=cached_get_all_centrales_from_db())

@router.get(
    "/empalmes",
    response_model=EmpalmeConsultaResponse,
    summary="Consultar empalmes",
    description="Obtiene los empalmes dentro de un radio especificado alrededor de un punto. Si no se especifican parámetros, retorna los primeros 100 empalmes.",
    response_description="GeoJSON FeatureCollection con los empalmes encontrados"
)
def get_empalmes(
    lat: float | None = Query(None, description="Latitud del punto central de búsqueda (en grados decimales)"),
    lon: float | None = Query(None, description="Longitud del punto central de búsqueda (en grados decimales)"),
    radio_interno: float | None = Query(None, description="Radio interno en metros (excluye elementos más cercanos que esta distancia)"),
    radio_externo: float | None = Query(None, description="Radio externo en metros (límite máximo de búsqueda)"),
    user: str = Depends(authenticate)
):
    """
    Consulta empalmes en la base de datos, opcionalmente filtrados por ubicación.
    
    Parámetros:
    - **lat**: Latitud del punto central de búsqueda en grados decimales (WGS84)
    - **lon**: Longitud del punto central de búsqueda en grados decimales (WGS84)
    - **radio_interno**: Radio interno en metros (excluye elementos más cercanos que esta distancia)
    - **radio_externo**: Radio externo en metros (límite máximo de búsqueda)
    
    Si se proporcionan todos los parámetros, se realiza una búsqueda espacial.
    Si no, se devuelven los primeros 100 empalmes en la base de datos.
    """
    return JSONResponse(content=get_empalmes_from_db(lat, lon, radio_interno, radio_externo))

@router.get(
    "/all_empalmes",
    response_model=EmpalmeConsultaResponse,
    summary="Consultar todos los empalmes",
    description="Obtiene todos los empalmes registrados en la base de datos. Utiliza una caché de 6 horas para mejorar el rendimiento.",
    response_description="GeoJSON FeatureCollection con todos los empalmes"
)
def get_all_empalmes(user: str = Depends(authenticate)):
    """
    Devuelve todos los empalmes registrados en el sistema.
    
    La respuesta es un GeoJSON FeatureCollection que contiene todos los empalmes.
    
    Este endpoint utiliza una caché con un tiempo de vida (TTL) de 6 horas para mejorar el rendimiento.
    """
    return JSONResponse(content=cached_get_all_empalmes_from_db())

@router.get(
    "/reservas",
    response_model=ReservaConsultaResponse,
    summary="Consultar reservas",
    description="Obtiene las reservas dentro de un radio especificado alrededor de un punto. Si no se especifican parámetros, retorna las primeras 100 reservas.",
    response_description="GeoJSON FeatureCollection con las reservas encontradas"
)
def get_reservas(
    lat: float | None = Query(None, description="Latitud del punto central de búsqueda (en grados decimales)"),
    lon: float | None = Query(None, description="Longitud del punto central de búsqueda (en grados decimales)"),
    radio_interno: float | None = Query(None, description="Radio interno en metros (excluye elementos más cercanos que esta distancia)"),
    radio_externo: float | None = Query(None, description="Radio externo en metros (límite máximo de búsqueda)"),
    user: str = Depends(authenticate)
):
    """
    Consulta reservas en la base de datos, opcionalmente filtradas por ubicación.
    
    Parámetros:
    - **lat**: Latitud del punto central de búsqueda en grados decimales (WGS84)
    - **lon**: Longitud del punto central de búsqueda en grados decimales (WGS84)
    - **radio_interno**: Radio interno en metros (excluye elementos más cercanos que esta distancia)
    - **radio_externo**: Radio externo en metros (límite máximo de búsqueda)
    
    Si se proporcionan todos los parámetros, se realiza una búsqueda espacial.
    Si no, se devuelven las primeras 100 reservas en la base de datos.
    """
    return JSONResponse(content=get_reservas_from_db(lat, lon, radio_interno, radio_externo))

@router.get(
    "/all_reservas",
    response_model=ReservaConsultaResponse,
    summary="Consultar todas las reservas",
    description="Obtiene todas las reservas registradas en la base de datos. Utiliza una caché de 6 horas para mejorar el rendimiento.",
    response_description="GeoJSON FeatureCollection con todas las reservas"
)
def get_all_reservas(user: str = Depends(authenticate)):
    """
    Devuelve todas las reservas registradas en el sistema.
    
    La respuesta es un GeoJSON FeatureCollection que contiene todas las reservas.
    
    Este endpoint utiliza una caché con un tiempo de vida (TTL) de 6 horas para mejorar el rendimiento.
    """
    return JSONResponse(content=cached_get_all_reservas_from_db())
