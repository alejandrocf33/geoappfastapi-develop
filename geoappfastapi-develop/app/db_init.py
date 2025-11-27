import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.models import Base, EstadoRegistro
import subprocess

def init_db():
    print("Conectando a la base de datos...\n")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            print("Limpiando tablas temporales anteriores...")
            # Eliminar tablas temporales si existen
            connection.execute(text("""
                DO $$ 
                DECLARE 
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE tablename LIKE '%_temp') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """))
            
            print("Configurando extensión PostGIS...")
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            connection.commit()
            
            print("Eliminando tablas y tipos existentes...\n")
            Base.metadata.drop_all(engine)
            connection.execute(text("DROP TYPE IF EXISTS estadoregistro CASCADE;"))
            connection.commit()
            
            print("Creando tipo enum para estados...")
            connection.execute(text("""
                CREATE TYPE estadoregistro AS ENUM ('inicial', 'pendiente', 'aprobado', 'rechazado');
            """))
            connection.commit()
            
            print("Creando tablas...")
            Base.metadata.create_all(engine)
            connection.commit()
            
            print("Base de datos inicializada correctamente.\n")
            
    except Exception as e:
        print(f"Error durante la inicialización de la base de datos: {str(e)}")
        raise
    
    return engine

def check_ogr2ogr():
    """Verifica si ogr2ogr está instalado y accesible"""
    try:
        subprocess.run(['ogr2ogr', '--version'], 
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.PIPE,
                              text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("""
ERROR: No se encuentra ogr2ogr. Por favor, sigue estos pasos para instalarlo:

1. Descarga OSGeo4W Network Installer (32 o 64 bits) desde:
   https://trac.osgeo.org/osgeo4w/

2. Ejecuta el instalador y selecciona:
   - Express Desktop Install
   - GDAL

3. Una vez instalado, agrega la ruta al PATH del sistema:
   - Busca "Variables de entorno" en Windows
   - En Variables del sistema, edita "Path"
   - Agrega: C:\\OSGeo4W64\\bin (o C:\\OSGeo4W\\bin para 32 bits)
   
4. Reinicia tu terminal/PowerShell

Después de completar estos pasos, ejecuta este script nuevamente.
""")
        return False

def load_geojson_to_postgres():
    print("\nIniciando carga de archivos GeoJSON...")
    if not check_ogr2ogr():
        print("Error: ogr2ogr no está instalado o no es accesible.")
        return

    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    file_table_mapping = {
        'cable_corporativo.geojson': 'cable_corporativo',
        'camaras.geojson': 'camaras',
        'centrales.geojson': 'centrales',
        'empalmes.geojson': 'empalmes',
        'reservas.geojson': 'reservas'
    }
    
    engine = create_engine(DATABASE_URL)
    temp_tables = []
    
    try:
        for geojson_file, table_name in file_table_mapping.items():
            file_path = os.path.join(data_dir, geojson_file)
            if not os.path.exists(file_path):
                print(f"Advertencia: No se encuentra el archivo {geojson_file}")
                continue
                
            print(f"\nProcesando {geojson_file}...")
            # Para cable_corporativo permitimos MULTILINESTRING en la tabla temporal
            geometry_type = 'MULTILINESTRING' if table_name == 'cable_corporativo' else 'POINT'
            temp_table = f"{table_name}_temp"
            temp_tables.append(temp_table)
            
            cmd = [
                'ogr2ogr',
                '-f', 'PostgreSQL',
                f'PG:dbname={os.getenv("DB_NAME")} user={os.getenv("DB_USER")} password={os.getenv("DB_PASSWORD")} host={os.getenv("DB_HOST")} port={os.getenv("DB_PORT", "5432")}',
                file_path,
                '-nln', temp_table,
                '-overwrite',
                '-lco', 'GEOMETRY_NAME=geom',
                '-lco', 'PRECISION=NO',
                '-nlt', geometry_type,
                '-t_srs', 'EPSG:4326'
            ]
            
            try:
                print("- Cargando datos en tabla temporal...")
                result = subprocess.run(cmd, 
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.PIPE,
                             text=True)
                if result.returncode != 0:
                    print(f"Error al ejecutar ogr2ogr: {result.stderr}")
                    continue
                print("- Datos cargados en tabla temporal.")
                
                with engine.connect() as connection:
                    print("- Analizando estructura de datos...")
                    json_columns_query = text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = :table_name 
                        AND column_name NOT IN ('id', 'geom', 'ogc_fid');
                    """)
                    
                    result = connection.execute(json_columns_query, {"table_name": temp_table}).fetchall()
                    columns = [row[0] for row in result]
                    
                    if not columns:
                        print("  Advertencia: No se encontraron columnas para las propiedades")
                        continue
                        
                    print(f"  Encontradas {len(columns)} columnas para propiedades")
                    json_build_object = ", ".join([f"'{col}', {col}" for col in columns])
                    
                    print("- Transfiriendo datos a tabla final...")
                    if table_name == 'cable_corporativo':
                        # Para cable_corporativo, extraemos cada línea del MULTILINESTRING
                        insert_query = text(f"""
                            WITH RECURSIVE geometry_parts AS (
                                SELECT 
                                    ogc_fid,
                                    (ST_Dump(geom)).path[1] as part_id,
                                    (ST_Dump(geom)).geom as single_geom,
                                    {', '.join(columns)}
                                FROM {temp_table}
                            )
                            INSERT INTO {table_name} (id, geom, propiedades, created_by, updated_by, estado, is_initial_load, distancia_metros)
                            SELECT 
                                (ogc_fid * 1000) + part_id as id,
                                single_geom as geom,
                                jsonb_build_object({json_build_object}) as propiedades,
                                'sistema' as created_by,
                                'sistema' as updated_by,
                                'inicial'::estadoregistro as estado,
                                true as is_initial_load,
                                ST_Length(ST_Transform(single_geom::geometry, 3857))::float as distancia_metros
                            FROM geometry_parts;
                        """)
                    else:
                        # Para otras tablas, inserción normal
                        insert_query = text(f"""
                            INSERT INTO {table_name} (id, geom, propiedades, created_by, updated_by, estado, is_initial_load)
                            SELECT 
                                ogc_fid as id,
                                geom,
                                jsonb_build_object({json_build_object}) as propiedades,
                                'sistema' as created_by,
                                'sistema' as updated_by,
                                'inicial'::estadoregistro as estado,
                                true as is_initial_load
                            FROM {temp_table};
                        """)
                    
                    connection.execute(insert_query)
                    connection.commit()
                    print(f"✓ {geojson_file} cargado exitosamente")
                    
            except subprocess.CalledProcessError as e:
                print(f"Error al ejecutar ogr2ogr para {geojson_file}: {str(e)}")
            except Exception as e:
                print(f"Error al procesar {geojson_file}: {str(e)}")
                if 'connection' in locals():
                    connection.rollback()
                
    finally:
        print("\nLimpiando tablas temporales...")
        with engine.connect() as connection:
            for temp_table in temp_tables:
                try:
                    connection.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))
                    connection.commit()
                    print(f"- Tabla temporal {temp_table} eliminada")
                except Exception as e:
                    print(f"Error al eliminar tabla temporal {temp_table}: {str(e)}")
            print("Limpieza de tablas temporales completada")

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

if __name__ == "__main__":
    try:
        init_db()
        load_geojson_to_postgres()
        reset_sequences()
        print("\n¡Proceso completado exitosamente!")
    except Exception as e:
        print(f"\nError durante la ejecución: {str(e)}")
        exit(1)
