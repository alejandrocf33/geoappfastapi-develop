from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# Modelos para respuestas de error
class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    NOT_FOUND = "not_found"
    DATABASE_ERROR = "database_error"
    DUPLICATE_ENTRY = "duplicate_entry"
    INTERNAL_ERROR = "internal_error"
    GEOMETRY_ERROR = "geometry_error"

class ErrorResponse(BaseModel):
    status: str = Field("error", description="Estado de la respuesta, siempre 'error' para errores")
    code: ErrorCode = Field(..., description="Código identificativo del error")
    message: str = Field(..., description="Mensaje descriptivo del error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "code": "not_found",
                "message": "El recurso solicitado no fue encontrado",
                "details": {
                    "resource_type": "camara",
                    "resource_id": 123
                }
            }
        }

# Modelos de respuesta para APIs de escritura
class CamaraResponse(BaseModel):
    message: str = Field(..., description="Mensaje de confirmación")
    id: int = Field(..., description="ID generado para la cámara")
    objectid: int = Field(..., description="ObjectID generado para la cámara (igual al ID)")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Cámara insertada correctamente",
                "id": 123,
                "objectid": 123
            }
        }

class CableResponse(BaseModel):
    message: str = Field(..., description="Mensaje de confirmación")
    id: int = Field(..., description="ID generado para el cable")
    objectid: int = Field(..., description="ObjectID generado para el cable (igual al ID)")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Cable insertado correctamente",
                "id": 123,
                "objectid": 123
            }
        }

class CentralResponse(BaseModel):
    message: str = Field(..., description="Mensaje de confirmación")
    id: int = Field(..., description="ID generado para la central")
    objectid: int = Field(..., description="ObjectID generado para la central (igual al ID)")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Central insertada correctamente",
                "id": 123,
                "objectid": 123
            }
        }

class EmpalmeResponse(BaseModel):
    message: str = Field(..., description="Mensaje de confirmación")
    id: int = Field(..., description="ID generado para el empalme")
    objectid: int = Field(..., description="ObjectID generado para el empalme (igual al ID)")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Empalme insertado correctamente",
                "id": 123,
                "objectid": 123
            }
        }

class ReservaResponse(BaseModel):
    message: str = Field(..., description="Mensaje de confirmación")
    id: int = Field(..., description="ID generado para la reserva")
    objectid: int = Field(..., description="ObjectID generado para la reserva (igual al ID)")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Reserva insertada correctamente",
                "id": 123,
                "objectid": 123
            }
        }

# Punto geográfico usado en varios modelos
class PuntoGeografico(BaseModel):
    longitud: float = Field(..., description="Longitud en grados decimales (WGS84)")
    latitud: float = Field(..., description="Latitud en grados decimales (WGS84)")

# Modelos para respuestas GeoJSON
class GeoJSONGeometry(BaseModel):
    type: str = Field(..., description="Tipo de geometría GeoJSON (Point, LineString, etc.)")
    coordinates: List[Union[float, List[float], List[List[float]]]] = Field(
        ..., description="Coordenadas de la geometría"
    )

class GeoJSONProperties(BaseModel):
    id: Optional[int] = Field(None, description="Identificador único del objeto")
    id_texto: Optional[str] = Field(None, description="Identificador textual del objeto")
    nombre: Optional[str] = Field(None, description="Nombre del objeto")
    tipo: Optional[str] = Field(None, description="Tipo del objeto")
    # Campos adicionales pueden variar según la entidad
    
    class Config:
        extra = "allow"  # Permitir campos adicionales específicos de cada entidad

class GeoJSONFeature(BaseModel):
    type: str = Field("Feature", description="Tipo de objeto GeoJSON, siempre 'Feature'")
    geometry: GeoJSONGeometry = Field(..., description="Geometría del objeto")
    properties: GeoJSONProperties = Field(..., description="Propiedades del objeto")
    id: Optional[int] = Field(None, description="Identificador opcional del Feature")

class GeoJSONFeatureCollection(BaseModel):
    type: str = Field("FeatureCollection", description="Tipo de objeto GeoJSON, siempre 'FeatureCollection'")
    features: List[GeoJSONFeature] = Field(..., description="Lista de Features GeoJSON")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-74.0617, 4.6737]
                        },
                        "properties": {
                            "id": 123,
                            "id_texto": "CAM-001",
                            "tipo": "Subterránea",
                            "ubicacion": "Calle 100 #15-20"
                        }
                    }
                ]
            }
        }

# Modelo para respuestas con paginación
class PaginatedResponse(BaseModel):
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Elementos por página")
    total_items: int = Field(..., description="Total de elementos disponibles")
    total_pages: int = Field(..., description="Total de páginas disponibles")
    data: Any = Field(..., description="Datos de la respuesta")
    
    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "data": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-74.0617, 4.6737]
                            },
                            "properties": {
                                "id": 123,
                                "nombre": "Cámara Principal"
                            }
                        }
                    ]
                }
            }
        }

# Modelos específicos para cada tipo de consulta
class CamarasConsultaResponse(GeoJSONFeatureCollection):
    pass

class CablesConsultaResponse(GeoJSONFeatureCollection):
    pass

class CentralesConsultaResponse(GeoJSONFeatureCollection):
    pass

class EmpalmeConsultaResponse(GeoJSONFeatureCollection):
    pass

class ReservaConsultaResponse(GeoJSONFeatureCollection):
    pass

# Versiones paginadas de los modelos de consulta
class CamarasConsultaPaginada(PaginatedResponse):
    data: GeoJSONFeatureCollection

class CablesConsultaPaginada(PaginatedResponse):
    data: GeoJSONFeatureCollection

class CentralesConsultaPaginada(PaginatedResponse):
    data: GeoJSONFeatureCollection

# Modelo para la respuesta de detección de cámaras en falla
class CamarasEnFallaResponse(BaseModel):
    camaras_cercanas: GeoJSONFeatureCollection = Field(..., description="Cámaras cercanas fuera del radio principal")
    camaras_en_radio: GeoJSONFeatureCollection = Field(..., description="Cámaras dentro del radio de búsqueda")
    
    class Config:
        schema_extra = {
            "example": {
                "camaras_cercanas": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-74.0620, 4.6740]
                            },
                            "properties": {
                                "id": 125,
                                "id_texto": "CAM-003",
                                "tipo": "Subterránea"
                            }
                        }
                    ]
                },
                "camaras_en_radio": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-74.0617, 4.6737]
                            },
                            "properties": {
                                "id": 123,
                                "id_texto": "CAM-001",
                                "tipo": "Subterránea"
                            }
                        }
                    ]
                }
            }
        }

# Modelo para la respuesta de cálculo de ruta en la red
class LineaEnRutaRedResponse(BaseModel):
    status: str = Field(..., description="Estado de la operación ('success' o 'error')")
    message: Optional[str] = Field(None, description="Mensaje informativo o de error")
    linea: Optional[Dict[str, Any]] = Field(None, description="GeoJSON de la línea que representa la ruta")
    punto_final: Optional[Dict[str, Any]] = Field(None, description="GeoJSON del punto final de la ruta")
    distancia_solicitada: Optional[float] = Field(None, description="Distancia solicitada en metros")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "linea": {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-74.0617, 4.6737],
                            [-74.0618, 4.6738],
                            [-74.0620, 4.6740]
                        ]
                    },
                    "properties": {
                        "distancia_metros": 150.25
                    }
                },
                "punto_final": {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-74.0620, 4.6740]
                    },
                    "properties": {}
                },
                "distancia_solicitada": 150
            }
        }
