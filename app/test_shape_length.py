#!/usr/bin/env python
"""
Test script para validar que el shape_length se esté agregando correctamente en las propiedades
de los registros insertados en la tabla cable_corporativo.
"""

import psycopg2
import os
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

# Obtener las credenciales de conexión del entorno
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "gis")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Función para obtener una conexión a la base de datos
def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

# Función para insertar un cable de prueba
def insertar_cable_prueba():
    """Inserta un cable de prueba para verificar el shape_length"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Crear un cable simple para pruebas
            wkt_geometry = "LINESTRING(-74.0620 4.6740, -74.0621 4.6741, -74.0622 4.6742)"
            props = {
                "id_text": "TEST-SHAPE-LENGTH",
                "name": "Cable de prueba shape_length",
                "colocacion": "Prueba"
            }
            props_json = json.dumps(props)
            
            # Insertar el cable
            cur.execute(
                """
                INSERT INTO cable_corporativo (geom, propiedades, created_by, updated_by, estado, distancia_metros)
                VALUES (
                    ST_GeomFromText(%s, 4326), 
                    %s::jsonb, 
                    %s, 
                    %s, 
                    'pendiente',
                    ST_Length(ST_Transform(ST_GeomFromText(%s, 4326), 3857))::float
                )
                RETURNING id
                """,
                (wkt_geometry, props_json, "test_script", "test_script", wkt_geometry)
            )
            
            # Obtener el ID generado
            generated_id = cur.fetchone()[0]
            
            # Consultar el valor de distancia_metros calculado
            cur.execute(
                """
                SELECT distancia_metros 
                FROM cable_corporativo 
                WHERE id = %s
                """,
                (generated_id,)
            )
            distancia_metros = cur.fetchone()[0]
            
            # Actualizar las propiedades con el objectid igual al id generado y shape_length
            props["objectid"] = generated_id
            props["shape_length"] = distancia_metros
            props_json = json.dumps(props)
            
            # Actualizar el registro con las propiedades actualizadas
            cur.execute(
                """
                UPDATE cable_corporativo 
                SET propiedades = %s::jsonb 
                WHERE id = %s
                """,
                (props_json, generated_id)
            )
            
            conn.commit()
            
            # Devolver el ID del cable insertado
            return generated_id
    except Exception as e:
        conn.rollback()
        print(f"Error al insertar cable de prueba: {e}")
        raise
    finally:
        conn.close()

# Función para verificar si el shape_length existe en las propiedades
def verificar_shape_length(cable_id):
    """Verifica si el cable tiene shape_length en sus propiedades"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT propiedades, distancia_metros
                FROM cable_corporativo
                WHERE id = %s
                """,
                (cable_id,)
            )
            result = cur.fetchone()
            if result:
                props = result[0]
                distancia_metros = result[1]
                if "shape_length" in props:
                    shape_length = props["shape_length"]
                    print(f"✅ shape_length encontrado en las propiedades: {shape_length}")
                    
                    # Verificar si el valor coincide con distancia_metros
                    if shape_length == distancia_metros:
                        print(f"✅ shape_length ({shape_length}) coincide con distancia_metros ({distancia_metros})")
                    else:
                        print(f"❌ shape_length ({shape_length}) NO coincide con distancia_metros ({distancia_metros})")
                else:
                    print("❌ No se encontró shape_length en las propiedades")
            else:
                print(f"❌ No se encontró el cable con ID {cable_id}")
    finally:
        conn.close()

# Función para limpiar el cable de prueba
def limpiar_cable_prueba(cable_id):
    """Elimina el cable de prueba"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM cable_corporativo
                WHERE id = %s
                """,
                (cable_id,)
            )
            conn.commit()
            print(f"🧹 Cable de prueba con ID {cable_id} eliminado")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar cable de prueba: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Ejecutando prueba de shape_length...")
    try:
        # Insertar un cable de prueba
        cable_id = insertar_cable_prueba()
        print(f"Cable de prueba insertado con ID: {cable_id}")
        
        # Verificar que el shape_length se haya agregado correctamente
        verificar_shape_length(cable_id)
        
        # Limpiar el entorno de prueba
        limpiar_cable_prueba(cable_id)
        
        print("Prueba completada.")
    except Exception as e:
        print(f"Error durante la prueba: {e}")
