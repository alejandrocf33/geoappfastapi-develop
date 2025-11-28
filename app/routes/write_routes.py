from fastapi import APIRouter, Depends, Query, Body, Path, HTTPException, status, Header, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, Union, List, Dict, Any
from ..auth import authenticate
from ..db_access import (insertar_camara_db, insertar_cable_corporativo_db, 
                         insertar_central_db, insertar_empalme_db, insertar_reserva_db)
from .api_models import (CamaraResponse, CableResponse, CentralResponse, 
                          EmpalmeResponse, ReservaResponse, PuntoGeografico)
from .error_models import responses, create_error_response, ErrorCode

router = APIRouter(tags=["Operaciones de Escritura"])

class Camara(BaseModel):
    # En una nueva versión de la API, se pueden agregar campos para recibir las fotos
    type: Optional[str] = Field(None, description="Tipo de cámara (ej. 'Subterránea', 'Aérea', 'Pedestal')")
    id_texto: Optional[str] = Field(None, description="Identificador textual de la cámara")
    ubicacion: Optional[str] = Field(None, description="Dirección o ubicación de la cámara")
    nombre_esp: Optional[str] = Field(None, description="Nombre especial de la cámara")
    apertura: Optional[str] = Field(None, description="Tipo de apertura de la cámara")
    propietari: Optional[str] = Field(None, description="Propietario de la cámara")
    constructi: Optional[str] = Field(None, description="Constructor de la cámara")
    estado_cam: Optional[str] = Field(None, description="Estado de la cámara (ej. 'Operativa', 'En Mantenimiento')")
    codigo_etb: Optional[str] = Field(None, description="Código ETB de la cámara")
    latitud: float = Field(..., description="Latitud en grados decimales (WGS84)")
    longitud: float = Field(..., description="Longitud en grados decimales (WGS84)")
    geometry: Optional[str] = Field(None, description="Geometría en formato WKT (Well-Known Text), si se proporciona, sobreescribe latitud/longitud")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "Subterránea",
                "id_texto": "CAM-001",
                "nombre_esp": "Cámara Principal",
                "ubicacion": "Calle 100 #15-20",
                "longitud": -74.0617,
                "latitud": 4.6737
            }
        }
        
    @validator('latitud')
    def validate_latitud(cls, v):
        if v < -90 or v > 90:
            raise ValueError('La latitud debe estar entre -90 y 90 grados')
        return v
        
    @validator('longitud')
    def validate_longitud(cls, v):
        if v < -180 or v > 180:
            raise ValueError('La longitud debe estar entre -180 y 180 grados')
        return v
        
    @validator('geometry')
    def validate_geometry(cls, v):
        if v is not None and not (v.lower().startswith('point') or v.lower().startswith('multipoint')):
            raise ValueError('La geometría debe ser de tipo POINT o MULTIPOINT en formato WKT')
        return v

class CableCorporativo(BaseModel):
    # En una nueva versión de la API, se pueden agregar campos para recibir las fotos
    id_texto: Optional[str] = Field(None, description="Identificador textual del cable")
    name: Optional[str] = Field(None, description="Nombre del cable")
    nombre_ant: Optional[str] = Field(None, description="Nombre anterior del cable")
    nombre_esp: Optional[str] = Field(None, description="Nombre especial del cable")
    colocacion: Optional[str] = Field(None, description="Tipo de colocación (ej. Troncal, Acceso)")
    constructi: Optional[str] = Field(None, description="Constructor del cable")
    perdida_db: Optional[float] = Field(None, description="Pérdida en decibelios")
    contratist: Optional[str] = Field(None, description="Contratista")
    segmento: Optional[str] = Field(None, description="Segmento al que pertenece el cable")
    pr: Optional[str] = Field(None, description="Propietario del cable")
    calculat1: Optional[float] = Field(None, description="Cálculo de la capacidad del cable")
    calculat2: Optional[float] = Field(None, description="Cálculo adicional de la capacidad del cable")
    calculated: Optional[float] = Field(None, description="Cálculo final de la capacidad del cable")
    id_especificacion: Optional[float] = Field(None, description="Identificador de especificación del cable")
    measured_l: Optional[float] = Field(None, description="Longitud medida del cable")
    # Para LineString se necesita una lista de puntos (al menos 2)
    puntos: List[PuntoGeografico] = Field([], description="Lista de puntos geográficos que conforman el cable")
    geometry: Optional[str] = Field(None, description="Geometría en formato WKT (LINESTRING), si se proporciona, sobreescribe la lista de puntos")
    
    class Config:
        schema_extra = {
            "example": {
                "id_texto": "CABLE-001",
                "name": "Cable Troncal Norte",
                "nombre_esp": "Cable de fibra óptica 48 hilos",
                "colocacion": "Troncal",
                "puntos": [
                    {"longitud": -74.0617, "latitud": 4.6737},
                    {"longitud": -74.0618, "latitud": 4.6738},
                    {"longitud": -74.0619, "latitud": 4.6739}
                ]
            }
        }
    
    @validator('puntos')
    def validate_puntos(cls, v, values):
        # Si se proporciona geometry, no validamos los puntos
        if values.get('geometry') is not None:
            return v
        
        # Si no hay geometry, debe haber al menos 2 puntos para formar una línea
        if len(v) < 2:
            raise ValueError('Se requieren al menos 2 puntos para formar un cable (LineString)')
        return v
    
    @validator('geometry')
    def validate_geometry(cls, v):
        if v is not None and not v.lower().startswith('linestring'):
            raise ValueError('La geometría debe ser de tipo LINESTRING en formato WKT')
        return v
    
    @validator('perdida_db')
    def validate_perdida_db(cls, v):
        if v is not None and v < 0:
            raise ValueError('La pérdida en decibelios no puede ser negativa')
        return v

class Central(BaseModel):
    # En una nueva versión de la API, se pueden agregar campos para recibir las fotos
    id_texto: Optional[str] = Field(None, description="Identificador textual de la central")
    nombre: Optional[str] = Field(None, description="Nombre de la central")
    codigo: Optional[str] = Field(None, description="Código único de la central")
    direccion: Optional[str] = Field(None, description="Dirección física de la central")
    tipo: Optional[str] = Field(None, description="Tipo de central")
    latitud: float = Field(..., description="Latitud en grados decimales (WGS84)")
    longitud: float = Field(..., description="Longitud en grados decimales (WGS84)")
    geometry: Optional[str] = Field(None, description="Geometría en formato WKT (Well-Known Text), si se proporciona, sobreescribe latitud/longitud")
    
    class Config:
        schema_extra = {
            "example": {
                "id_texto": "CTL-001",
                "nombre": "Central Norte",
                "codigo": "CN-001",
                "direccion": "Calle 165 #25-30",
                "tipo": "Conmutación",
                "longitud": -74.0616,
                "latitud": 4.7437
            }
        }

class Empalme(BaseModel):
    # En una nueva versión de la API, se pueden agregar campos para recibir las fotos
    id_texto: Optional[str] = Field(None, description="Identificador textual del empalme")
    name: Optional[str] = Field(None, description="Nombre del empalme")
    x: Optional[float] = Field(None, description="Nombre alternativo del empalme")
    y: Optional[float] = Field(None, description="Nombre alternativo del empalme")
    type: Optional[str] = Field(None, description="Tipo de empalme")
    sangria: Optional[float] = Field(None, description="Sangría del empalme (ej. 'Sangría 1')")
    segmento: Optional[str] = Field(None, description="Segmento al que pertenece el empalme")
    location_x: Optional[float] = Field(None, description="Ubicación del empalme en el eje X")
    location_y: Optional[float] = Field(None, description="Ubicación del empalme en el eje Y")
    propietario: Optional[str] = Field(None, description="Propietario del empalme")
    splice_type: Optional[str] = Field(None, description="Tipo de empalme (ej. 'Empalme de Fibra Óptica')")
    count_mayorista: Optional[float] = Field(None, description="Cantidad de hilos mayoristas en el empalme")
    mayorista_gather: Optional[str] = Field(None, description="Mayorista al que pertenece el empalme")
    symbol_annotation: Optional[str] = Field(None, description="Anotación del símbolo del empalme")
    symbol_location_x: Optional[float] = Field(None, description="Ubicación del símbolo en el eje X")
    symbol_location_y: Optional[float] = Field(None, description="Ubicación del símbolo en el eje Y")
    id_specification: Optional[str] = Field(None, description="Identificador de especificación del empalme")
    construction_status: Optional[str] = Field(None, description="Estado de construcción del empalme (ej. 'En Construcción', 'Operativo')")
    nombre_especificacion: Optional[str] = Field(None, description="Nombre de la especificación del empalme")
    ubicacion_empalmes_camara_x: Optional[float] = Field(None, description="Ubicación del empalme en la cámara en el eje X")
    ubicacion_empalmes_camara_y: Optional[float] = Field(None, description="Ubicación del empalme en la cámara en el eje Y")
    ubicacion_empalmes_postes_x: Optional[float] = Field(None, description="Ubicación del empalme en el poste en el eje X")
    ubicacion_empalmes_postes_y: Optional[float] = Field(None, description="Ubicación del empalme en el poste en el eje Y")
    ubicacion_empalmes_edificio_x: Optional[float] = Field(None, description="Ubicación del empalme en el edificio en el eje X")
    ubicacion_empalmes_edificio_y: Optional[float] = Field(None, description="Ubicación del empalme en el edificio en el eje Y")
    ubicacion_empalmes_punto_de_acceso_x: Optional[float] = Field(None, description="Ubicación del empalme en el punto de acceso en el eje X")
    ubicacion_empalmes_punto_de_acceso_y: Optional[float] = Field(None, description="Ubicación del empalme en el punto de acceso en el eje Y")
    latitud: float = Field(..., description="Latitud en grados decimales (WGS84)")
    longitud: float = Field(..., description="Longitud en grados decimales (WGS84)")
    geometry: Optional[str] = Field(None, description="Geometría en formato WKT (Well-Known Text), si se proporciona, sobreescribe latitud/longitud")
    
    class Config:
        schema_extra = {
            "example": {
                "id_texto": "EMP-001",
                "nombre": "Empalme Principal",
                "tipo": "Empalme de Fibra Óptica",
                "capacidad": "96 hilos",
                "ubicacion": "Calle 80 con 30",
                "longitud": -74.0917,
                "latitud": 4.6647
            }
        }

class Reserva(BaseModel):
    # En una nueva versión de la API, se pueden agregar campos para recibir las fotos
    id_texto: Optional[str] = Field(None, description="Identificador textual de la reserva")
    nombre: Optional[str] = Field(None, description="Nombre de la reserva")
    tipo: Optional[str] = Field(None, description="Tipo de reserva")
    capacidad: Optional[str] = Field(None, description="Capacidad de la reserva (ej. '48 hilos')")
    ubicacion: Optional[str] = Field(None, description="Descripción de la ubicación de la reserva")
    latitud: float = Field(..., description="Latitud en grados decimales (WGS84)")
    longitud: float = Field(..., description="Longitud en grados decimales (WGS84)")
    geometry: Optional[str] = Field(None, description="Geometría en formato WKT (Well-Known Text), si se proporciona, sobreescribe latitud/longitud")
    
    class Config:
        schema_extra = {
            "example": {
                "id_texto": "RES-001",
                "nombre": "Reserva Principal",
                "tipo": "Reserva de Fibra Óptica",
                "capacidad": "48 hilos",
                "ubicacion": "Calle 26 con Avenida Caracas",
                "longitud": -74.0816,
                "latitud": 4.6147
            }
        }



@router.post(
    "/camaras", 
    response_model=CamaraResponse,
    summary="Crear nueva cámara",
    description="Inserta una nueva cámara en la base de datos usando coordenadas geográficas o geometría WKT.",
    response_description="Objeto de confirmación con ID y ObjectID generados",
)
@router.post(
    "/camaras/", 
    response_model=CamaraResponse,
    summary="Crear nueva cámara",
    description="Inserta una nueva cámara en la base de datos usando coordenadas geográficas o geometría WKT.",
    response_description="Objeto de confirmación con ID y ObjectID generados",
    responses={
        status.HTTP_401_UNAUTHORIZED: responses[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_ENTITY: responses[status.HTTP_422_UNPROCESSABLE_ENTITY],
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": responses[status.HTTP_500_INTERNAL_SERVER_ERROR]["model"],
            "description": "Error al insertar la cámara en la base de datos",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": "database_error",
                        "message": "Error al insertar la cámara en la base de datos",
                        "details": {
                            "error": "Violación de restricción de unicidad"
                        }
                    }
                }
            }
        }
    }
)
def insertar_camara(
    camara: Camara = Body(..., description="Datos de la nueva cámara"),
    request: Request = None,
    auth_user: str = Depends(authenticate),
    user_header: Optional[str] = Header(None, description="Usuario para trazabilidad (opcional)")
):
    """
    Inserta una nueva cámara en la base de datos.
    
    Se puede proporcionar las coordenadas directamente usando los campos 'longitud' y 'latitud',
    o proporcionar la geometría WKT usando el campo 'geometry'.
    
    El campo 'objectid' se generará automáticamente con el mismo valor que la clave primaria (id).
    Los campos 'created_by' y 'updated_by' serán establecidos automáticamente con el nombre del usuario.
    El usuario puede ser especificado en el header 'user-header', o se utilizará el usuario autenticado.
    
    Posibles códigos de error:
    - 401: Credenciales de autenticación no válidas
    - 422: Datos de entrada inválidos (ej. coordenadas fuera de rango)
    - 500: Error interno al procesar la solicitud
    
    El estado inicial de la cámara será 'pendiente'.
    """
    # Usar el usuario del header si está disponible, de lo contrario usar el usuario autenticado
    username = user_header if user_header else auth_user
    return insertar_camara_db(camara, username=username)

@router.post(
    "/cable_corporativo", 
    response_model=CableResponse,
    summary="Crear nuevo cable corporativo",
)
@router.post(
    "/cable_corporativo/", 
    response_model=CableResponse,
    summary="Crear nuevo cable corporativo",
    description="Inserta un nuevo cable corporativo en la base de datos usando una lista de puntos o geometría WKT.",
    response_description="Objeto de confirmación con ID generado",
    responses={
        status.HTTP_401_UNAUTHORIZED: responses[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": responses[status.HTTP_422_UNPROCESSABLE_ENTITY]["model"],
            "description": "Datos de entrada inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": "validation_error",
                        "message": "Error de validación en los datos de entrada",
                        "details": {
                            "errors": [
                                {
                                    "loc": ["body", "puntos"],
                                    "msg": "La lista debe contener al menos 2 puntos para formar una línea",
                                    "type": "value_error.list.min_items"
                                }
                            ]
                        }
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: responses[status.HTTP_500_INTERNAL_SERVER_ERROR]
    }
)
def insertar_cable_corporativo(
    cable: CableCorporativo = Body(..., description="Datos del nuevo cable corporativo"),
    request: Request = None,
    auth_user: str = Depends(authenticate),
    user_header: Optional[str] = Header(None, description="Usuario para trazabilidad (opcional)")
):
    """
    Inserta un nuevo cable corporativo en la base de datos.
    
    Se puede proporcionar una lista de puntos (al menos 2) usando el campo 'puntos',
    o proporcionar la geometría WKT usando el campo 'geometry'.
    
    Los campos 'created_by' y 'updated_by' serán establecidos automáticamente 
    con el nombre del usuario especificado en el header 'user-header' o el autenticado.
    
    El estado inicial del cable será 'pendiente'.
    
    Posibles códigos de error:
    - 401: Credenciales de autenticación no válidas
    - 422: Datos de entrada inválidos (ej. número insuficiente de puntos)
    - 500: Error interno al procesar la solicitud
    """
    # Usar el usuario del header si está disponible, de lo contrario usar el usuario autenticado
    username = user_header if user_header else auth_user
    return insertar_cable_corporativo_db(cable, username=username)

@router.post(
    "/centrales", 
    response_model=CentralResponse,
    summary="Crear nueva central",
)
@router.post(
    "/centrales/", 
    response_model=CentralResponse,
    summary="Crear nueva central",
    description="Inserta una nueva central en la base de datos usando coordenadas geográficas o geometría WKT.",
    response_description="Objeto de confirmación con ID generado"
)
def insertar_central(
    central: Central = Body(..., description="Datos de la nueva central"),
    request: Request = None,
    auth_user: str = Depends(authenticate),
    user_header: Optional[str] = Header(None, description="Usuario para trazabilidad (opcional)")
):
    """
    Inserta una nueva central en la base de datos.
    
    Se puede proporcionar las coordenadas directamente usando los campos 'longitud' y 'latitud',
    o proporcionar la geometría WKT usando el campo 'geometry'.
    
    Los campos 'created_by' y 'updated_by' serán establecidos automáticamente 
    con el nombre del usuario especificado en el header 'user-header' o el autenticado.
    
    El estado inicial de la central será 'pendiente'.
    """
    # Usar el usuario del header si está disponible, de lo contrario usar el usuario autenticado
    username = user_header if user_header else auth_user
    return insertar_central_db(central, username=username)

@router.post(
    "/empalmes", 
    response_model=EmpalmeResponse,
    summary="Crear nuevo empalme",
)
@router.post(
    "/empalmes/", 
    response_model=EmpalmeResponse,
    summary="Crear nuevo empalme",
    description="Inserta un nuevo empalme en la base de datos usando coordenadas geográficas o geometría WKT.",
    response_description="Objeto de confirmación con ID generado"
)
def insertar_empalme(
    empalme: Empalme = Body(..., description="Datos del nuevo empalme"),
    request: Request = None,
    auth_user: str = Depends(authenticate),
    user_header: Optional[str] = Header(None, description="Usuario para trazabilidad (opcional)")
):
    """
    Inserta un nuevo empalme en la base de datos.
    
    Se puede proporcionar las coordenadas directamente usando los campos 'longitud' y 'latitud',
    o proporcionar la geometría WKT usando el campo 'geometry'.
    
    Los campos 'created_by' y 'updated_by' serán establecidos automáticamente 
    con el nombre del usuario especificado en el header 'user-header' o el autenticado.
    
    El estado inicial del empalme será 'pendiente'.
    """
    # Usar el usuario del header si está disponible, de lo contrario usar el usuario autenticado
    username = user_header if user_header else auth_user
    return insertar_empalme_db(empalme, username=username)

@router.post(
    "/reservas", 
    response_model=ReservaResponse,
    summary="Crear nueva reserva",
)
@router.post(
    "/reservas/", 
    response_model=ReservaResponse,
    summary="Crear nueva reserva",
    description="Inserta una nueva reserva en la base de datos usando coordenadas geográficas o geometría WKT.",
    response_description="Objeto de confirmación con ID generado"
)
def insertar_reserva(
    reserva: Reserva = Body(..., description="Datos de la nueva reserva"),
    request: Request = None,
    auth_user: str = Depends(authenticate),
    user_header: Optional[str] = Header(None, description="Usuario para trazabilidad (opcional)")
):
    """
    Inserta una nueva reserva en la base de datos.
    
    Se puede proporcionar las coordenadas directamente usando los campos 'longitud' y 'latitud',
    o proporcionar la geometría WKT usando el campo 'geometry'.
    
    Los campos 'created_by' y 'updated_by' serán establecidos automáticamente 
    con el nombre del usuario especificado en el header 'user-header' o el autenticado.
    
    El estado inicial de la reserva será 'pendiente'.
    """
    # Usar el usuario del header si está disponible, de lo contrario usar el usuario autenticado
    username = user_header if user_header else auth_user
    return insertar_reserva_db(reserva, username=username)
