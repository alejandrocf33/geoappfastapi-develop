from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class EstadoRegistro(enum.Enum):
    INICIAL = "inicial"      # Carga inicial del sistema
    PENDIENTE = "pendiente"  # Insertado pero pendiente de aprobación
    APROBADO = "aprobado"   # Aprobado por un supervisor
    RECHAZADO = "rechazado" # Rechazado por un supervisor

class BaseFeaturesTable:
    id = Column(Integer, primary_key=True)
    propiedades = Column(JSONB)    # Campos de auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String)  # Usuario que creó el registro
    updated_by = Column(String)  # Usuario que actualizó por última vez
    estado = Column(Enum(EstadoRegistro), default=EstadoRegistro.PENDIENTE)
    is_initial_load = Column(Boolean, default=False)  # Indica si es parte de la carga inicial

class CableCorporativo(Base, BaseFeaturesTable):
    __tablename__ = 'cable_corporativo'
    geom = Column(Geometry('LINESTRING', srid=4326))
    distancia_metros = Column(Float)

class Camaras(Base, BaseFeaturesTable):
    __tablename__ = 'camaras'
    geom = Column(Geometry('POINT', srid=4326))

class Centrales(Base, BaseFeaturesTable):
    __tablename__ = 'centrales'
    geom = Column(Geometry('POINT', srid=4326))

class Empalmes(Base, BaseFeaturesTable):
    __tablename__ = 'empalmes'
    geom = Column(Geometry('POINT', srid=4326))

class Reservas(Base, BaseFeaturesTable):
    __tablename__ = 'reservas'
    geom = Column(Geometry('POINT', srid=4326))
