"""
Script para restablecer las secuencias de PostgreSQL después de insertar datos con IDs explícitos.
Esto asegura que las nuevas inserciones automáticas usen IDs que no entren en conflicto.
"""

import os
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

def reset_sequences():
    """Actualiza todas las secuencias de las tablas para que comiencen desde el máximo ID + 1"""
    print("\nActualizando secuencias de ID en las tablas...")
    engine = create_engine(DATABASE_URL)
    
    # Lista de tablas a actualizar
    tables = ['cable_corporativo', 'camaras', 'centrales', 'empalmes', 'reservas']
    
    try:
        with engine.connect() as connection:
            for table in tables:
                # Construir el nombre de la secuencia según la convención de PostgreSQL
                sequence_name = f"{table}_id_seq"
                
                # Consulta para obtener el máximo ID de la tabla
                max_id_query = text(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}")
                max_id = connection.execute(max_id_query).scalar()
                
                # Actualizar la secuencia para comenzar desde el máximo ID + 1
                reset_query = text(f"ALTER SEQUENCE {sequence_name} RESTART WITH {max_id}")
                connection.execute(reset_query)
                connection.commit()
                
                print(f"✓ Secuencia de {table} actualizada para comenzar desde {max_id}")
        
        print("Todas las secuencias han sido actualizadas correctamente")
    except Exception as e:
        print(f"Error al actualizar secuencias: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        reset_sequences()
        print("\n¡Secuencias actualizadas exitosamente!")
    except Exception as e:
        print(f"\nError durante la actualización de secuencias: {str(e)}")
        exit(1)
