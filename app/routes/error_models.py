"""
Modelos de respuesta para errores comunes de la API.
Este módulo define los modelos y los responses estándar para manejar errores.
"""

from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union, Type
from enum import Enum

class ErrorCode(str, Enum):
    """Códigos de error estandarizados para la API."""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    NOT_FOUND = "not_found"
    DATABASE_ERROR = "database_error"
    DUPLICATE_ENTRY = "duplicate_entry"
    INTERNAL_ERROR = "internal_error"
    GEOMETRY_ERROR = "geometry_error"
    PERMISSION_DENIED = "permission_denied"

class ErrorResponseModel(BaseModel):
    """Modelo base para respuestas de error."""
    status: str = "error"
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None

class ValidationError(BaseModel):
    """Modelo para errores de validación específicos."""
    loc: List[Union[str, int]]
    msg: str
    type: str

# Respuestas de error comunes que pueden ser reutilizadas en la documentación
responses = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponseModel,
        "description": "Error de autenticación",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "code": "authentication_error",
                    "message": "Credenciales incorrectas o no proporcionadas"
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponseModel,
        "description": "Recurso no encontrado",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "code": "not_found",
                    "message": "El recurso solicitado no existe",
                    "details": {
                        "resource_type": "camara",
                        "resource_id": 123
                    }
                }
            }
        }
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "model": ErrorResponseModel,
        "description": "Error de validación de datos",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "code": "validation_error",
                    "message": "Error de validación en los datos de entrada",
                    "details": {
                        "errors": [
                            {
                                "loc": ["body", "latitud"],
                                "msg": "El valor debe estar entre -90 y 90",
                                "type": "value_error.number.not_gt"
                            }
                        ]
                    }
                }
            }
        }
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponseModel,
        "description": "Error interno del servidor",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "code": "internal_error",
                    "message": "Error interno del servidor"
                }
            }
        }
    }
}

# Función auxiliar para generar HTTPException con formato consistente
def create_error_response(
    status_code: int, 
    code: ErrorCode, 
    message: str, 
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Crea una respuesta de error HTTP con formato consistente.
    
    Args:
        status_code: Código HTTP del error
        code: Código de error específico de la aplicación
        message: Mensaje descriptivo del error
        details: Detalles adicionales opcionales
        
    Returns:
        HTTPException formateada
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "status": "error",
            "code": code,
            "message": message,
            "details": details
        }
    )
