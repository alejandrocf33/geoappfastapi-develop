#!/usr/bin/env python
"""
Script para ejecutar la migración de agregar columna updated_by a reportes_mal_estado
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_connection

def run_migration():
    """Ejecuta la migración SQL para agregar updated_by"""
    migration_file = Path(__file__).parent / 'sql' / 'alter_table_reportes_mal_estado_add_updated_by.sql'

    print(f"Leyendo migración desde: {migration_file}")

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    print("Ejecutando migración...")
    print("-" * 60)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Ejecutar el script SQL
                cur.execute(sql_script)
                conn.commit()

                # Verificar que la columna fue agregada
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'reportes_mal_estado'
                    AND column_name = 'updated_by'
                """)

                result = cur.fetchone()

                if result:
                    print(f"\n✅ Migración exitosa!")
                    print(f"   Columna: {result[0]}")
                    print(f"   Tipo: {result[1]}")
                    print("\nLa tabla reportes_mal_estado ahora tiene la columna 'updated_by'")
                else:
                    print("\n⚠️  La columna no fue encontrada después de la migración")

    except Exception as e:
        print(f"\n❌ Error durante la migración: {str(e)}")
        sys.exit(1)

    print("\n" + "-" * 60)
    print("Migración completada. El formulario de reportes ahora debería funcionar correctamente.")

if __name__ == "__main__":
    run_migration()
