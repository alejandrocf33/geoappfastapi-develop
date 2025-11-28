import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.database import get_connection
from ..auth import authenticate
from ..db_access import get_camaras_en_falla_db, get_cables_cercanos_from_db
import geojson
from .api_models import (
    CamarasEnFallaResponse,
    CablesConsultaResponse,
    LineaEnRutaRedResponse
)
from .error_models import responses, create_error_response, ErrorCode

router = APIRouter(tags=["Operaciones Lógicas"])

@router.get(
    "/camaras_en_falla",
    response_model=CamarasEnFallaResponse,
    summary="Detectar cámaras potencialmente en falla",
    description="Analiza un área específica y detecta cámaras que podrían estar en falla según patrones de distribución.",
    response_description="Objeto con dos colecciones GeoJSON: cámaras en radio y cámaras cercanas",
    responses={
        status.HTTP_401_UNAUTHORIZED: responses[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_404_NOT_FOUND: {
            "model": responses[status.HTTP_404_NOT_FOUND]["model"],
            "description": "No se encontraron cámaras en el área especificada",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": "not_found",
                        "message": "No se encontraron cámaras en el área especificada para el análisis",
                        "details": {
                            "lat": 4.6737,
                            "lon": -74.0617,
                            "distancia": 100
                        }
                    }
                }
            }
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: responses[status.HTTP_422_UNPROCESSABLE_ENTITY]
    }
)
def get_camaras_en_falla(
    lat: float = Query(..., description="Latitud del punto central de análisis (en grados decimales)"),
    lon: float = Query(..., description="Longitud del punto central de análisis (en grados decimales)"),
    distancia: float = Query(..., description="Radio de búsqueda inicial en metros"),
    desviacion: float = Query(10, description="Distancia adicional para buscar cámaras cercanas fuera del radio inicial (en metros)"),
    user: str = Depends(authenticate)
):
    """
    Analiza un área específica para detectar potenciales cámaras en falla.
    
    Este endpoint utiliza un algoritmo de análisis espacial para identificar posibles cámaras con problemas,
    basado en patrones de distribución y cercanía.
    
    Parámetros:
    - **lat**: Latitud del punto central de análisis en grados decimales (WGS84)
    - **lon**: Longitud del punto central de análisis en grados decimales (WGS84)
    - **distancia**: Radio de búsqueda inicial en metros
    - **desviacion**: Distancia adicional para buscar cámaras cercanas fuera del radio inicial
    
    La respuesta incluye dos colecciones de cámaras:
    - **camaras_en_radio**: Cámaras encontradas dentro del radio de búsqueda principal
    - **camaras_cercanas**: Cámaras encontradas fuera del radio principal pero dentro del radio extendido
    """
    camaras_en_radio_ids = set()
    camaras_en_radio, camaras_cercanas = get_camaras_en_falla_db(
        lon, lat, distancia, desviacion, camaras_en_radio_ids
    )
    return JSONResponse(content={
        "camaras_cercanas": geojson.FeatureCollection(camaras_cercanas),
        "camaras_en_radio": geojson.FeatureCollection(camaras_en_radio)
    })

@router.get(
    "/cables_cercanos",
    response_model=CablesConsultaResponse,
    summary="Buscar cables cercanos",
    description="Obtiene cables que estén dentro de un radio específico desde un punto dado, con opciones para filtrar por tipo y nombre.",
    response_description="GeoJSON FeatureCollection con los cables encontrados"
)
def get_cables_cercanos(
    lat: float = Query(..., description="Latitud del punto central (en grados decimales)"),
    lon: float = Query(..., description="Longitud del punto central (en grados decimales)"), 
    distancia: float = Query(..., description="Radio de búsqueda en metros"),
    limite: int = Query(100, description="Cantidad máxima de resultados a retornar"),
    incluir_troncales: bool = Query(False, description="Incluir cables troncales en los resultados"),
    nombre_cable: str = Query(None, description="Nombre del cable para filtrar los resultados (opcional)"),
    busqueda_exacta: bool = Query(True, description="Si es True, busca coincidencia exacta del nombre; si es False, usa búsqueda parcial con LIKE"),
    user: str = Depends(authenticate)
):
    """
    Obtiene cables cercanos a un punto geográfico con opciones avanzadas de filtrado.
    
    Este endpoint permite buscar cables dentro de un radio específico desde un punto dado,
    con múltiples opciones de filtrado como tipo de cable, nombre y límite de resultados.
    
    Parámetros:
    - **lat**: Latitud del punto central en grados decimales (WGS84)
    - **lon**: Longitud del punto central en grados decimales (WGS84)
    - **distancia**: Radio de búsqueda en metros
    - **limite**: Cantidad máxima de resultados a retornar (por defecto: 100)
    - **incluir_troncales**: Si es True, incluye cables troncales en los resultados (por defecto: False)
    - **nombre_cable**: Opcional. Filtra cables por nombre
    - **busqueda_exacta**: Si es True (predeterminado), busca coincidencias exactas del nombre; si es False, 
      busca coincidencias parciales usando LIKE %nombre%
    
    Por defecto excluye los cables troncales, pero pueden incluirse mediante el parámetro correspondiente.
    Los resultados incluyen la distancia al punto especificado en metros.
    """
    resultado = get_cables_cercanos_from_db(
        lon=lon, 
        lat=lat, 
        distancia=distancia, 
        limite=limite, 
        incluir_troncales=incluir_troncales,
        nombre_cable=nombre_cable,
        busqueda_exacta=busqueda_exacta
    )
    return JSONResponse(content=resultado)

@router.get(
    "/linea_en_ruta_red",
    response_model=LineaEnRutaRedResponse,
    summary="Calcular ruta en la red",
    description="Calcula una ruta en la red de cables desde un punto de entrada hasta una distancia específica.",
    response_description="Objeto con los GeoJSON de la línea de la ruta y los puntos a la distancia especificada"
)
def get_linea_en_ruta_red_endpoint(
    lon: float = Query(..., description="Longitud del punto de entrada (en grados decimales)"),
    lat: float = Query(..., description="Latitud del punto de entrada (en grados decimales)"),
    distancia: float = Query(..., description="Distancia a recorrer en metros por la red"),
    incluir_linea: bool = Query(True, description="Si es True, devuelve la línea geometry junto con los puntos"),
    user: str = Depends(authenticate)
):
    """
    Calcula y obtiene una ruta en la red de cables.
    
    Este endpoint utiliza una función PostgreSQL/PostGIS especializada para:
    1. Encontrar el cable más cercano al punto de entrada
    2. Navegar por la red de cables hasta la distancia especificada
    3. Devolver tanto la ruta completa como los puntos a intervalos de la distancia
    
    Parámetros:
    - **lon**: Longitud del punto de entrada en grados decimales (WGS84)
    - **lat**: Latitud del punto de entrada en grados decimales (WGS84)
    - **distancia**: Distancia a recorrer en metros por la red
    - **incluir_linea**: Si es True (predeterminado), incluye la geometría de la línea en la respuesta
    
    La respuesta incluye:
    - **status**: Estado de la operación ('success' o 'error')
    - **linea**: GeoJSON de la línea que representa la ruta calculada (opcional)
    - **puntos**: Lista de GeoJSON de los puntos a intervalos de la distancia especificada
    - **distancia_solicitada**: La distancia en metros que se solicitó recorrer
    
    Es útil para planificación de tendido de cables y análisis de cobertura de red.
    """
    result = get_linea_en_ruta_red(lon, lat, distancia, incluir_linea)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return JSONResponse(content=result)


def get_linea_en_ruta_red(lon: float, lat: float, distancia_m: float, incluir_linea: bool = True):
    """
    Obtiene una línea que representa la ruta en la red de cables desde un punto 
    hasta una distancia específica, y los puntos a esa distancia.
    
    Args:
        lon: Longitud del punto de inicio
        lat: Latitud del punto de inicio
        distancia_m: Distancia en metros a recorrer por la red de cables
        incluir_linea: Si debe incluir la geometría de la línea en la respuesta
    
    Returns:
        Un diccionario con la línea de la ruta (opcional) y los puntos a la distancia especificada
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ST_AsGeoJSON(linea) as linea_geojson,
                        ST_AsGeoJSON(punto) as punto_geojson
                    FROM fn_linea_en_ruta_red(%s, %s, %s, %s)
                """, (lon, lat, distancia_m, incluir_linea))
                rows = cur.fetchall()
                if not rows or all(r[0] is None and r[1] is None for r in rows):
                    return {"status": "error", "message": "No se pudo calcular la ruta en la red de cables"}
                # Si hay varias filas, la línea será la misma en todas (si incluir_linea=True)
                linea_geojson = json.loads(rows[0][0]) if rows[0][0] else None
                puntos_geojson = [json.loads(r[1]) for r in rows if r[1]]
                return {
                    "status": "success",
                    "linea": {
                        "type": "Feature",
                        "geometry": linea_geojson,
                        "properties": {
                            "distancia_metros": distancia_m
                        }
                    } if linea_geojson else None,
                    "puntos": [
                        {
                            "type": "Feature",
                            "geometry": punto,
                            "properties": {
                                "distancia_metros": distancia_m
                            }
                        } for punto in puntos_geojson
                    ]
                }
    except Exception as e:
        return {"status": "error", "message": f"Error obteniendo la ruta en la red: {str(e)}"}

@router.get(
    "/nodos_alcanzables_en_ruta_red",
    summary="Nodos alcanzables en la red a una distancia dada",
    description="Devuelve todos los nodos alcanzables desde un punto inicial a una distancia específica sobre la red, e indica cuál(es) es(son) el(los) más cercano(s) a la distancia solicitada.",
    response_description="Lista de nodos alcanzables con su geometría, distancia acumulada, si es el más cercano a la distancia solicitada y el nombre del cable."
)
def get_nodos_alcanzables_en_ruta_red(
    lon: float = Query(..., description="Longitud del punto de inicio (en grados decimales)"),
    lat: float = Query(..., description="Latitud del punto de inicio (en grados decimales)"),
    distancia: float = Query(..., description="Distancia a recorrer en metros por la red"),
    margen_factor: float = Query(0.999, description="Margen de error como factor decimal (por defecto 0.999)"),
    user: str = Depends(authenticate)
):
    """
    Devuelve todos los nodos alcanzables desde un punto inicial a una distancia específica sobre la red,
    e indica cuál(es) es(son) el(los) más cercano(s) a la distancia solicitada y el nombre del cable.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT ST_AsGeoJSON(geom) as geom_geojson, distancia_acumulada, es_mas_cercano, nombre_cable
                    FROM fn_nodos_alcanzables_en_ruta_red(%s, %s, %s, %s)
                """, (lon, lat, distancia, margen_factor))
                rows = cur.fetchall()
                if not rows:
                    return JSONResponse(content={"status": "error", "message": "No se encontraron nodos alcanzables para la distancia dada"}, status_code=404)
                features = []
                for row in rows:
                    feature = {
                        "type": "Feature",
                        "geometry": json.loads(row[0]) if row[0] else None,
                        "properties": {
                            "distancia_acumulada": row[1],
                            "es_mas_cercano": row[2],
                            "nombre_cable": row[3]
                        }
                    }
                    features.append(feature)
                return JSONResponse(content={
                    "status": "success",
                    "features": features,
                    "distancia_solicitada": distancia,
                    "margen_factor": margen_factor
                })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error consultando nodos alcanzables: {str(e)}"}, status_code=500)