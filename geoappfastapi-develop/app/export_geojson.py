import os
from app.config import DATABASE_URL
import subprocess

def export_to_geojson(table_name, output_file):
    """
    Exporta una tabla a GeoJSON manteniendo todas las propiedades JSONB
    """
    # Construir la consulta SQL que combina la geometría y propiedades en formato GeoJSON
    query = f"""
    SELECT jsonb_build_object(
        'type',     'FeatureCollection',
        'features', jsonb_agg(feature)
    )
    FROM (
        SELECT jsonb_build_object(
            'type',       'Feature',
            'geometry',   ST_AsGeoJSON(geom)::jsonb,
            'properties', propiedades
        ) AS feature
        FROM {table_name}
    ) AS features;
    """
    
    # Construir el comando ogr2ogr para la exportación
    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        output_file,
        f"PG:dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT', '5432')}",
        "-sql", query
    ]
    
    subprocess.run(cmd, check=True)

def export_all_tables():
    """
    Exporta todas las tablas a archivos GeoJSON
    """
    tables = ['cable_corporativo', 'camaras', 'centrales', 'empalmes', 'reservas']
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    
    # Crear directorio de exportación si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    for table in tables:
        output_file = os.path.join(output_dir, f"{table}_export.geojson")
        try:
            export_to_geojson(table, output_file)
            print(f"Exportado exitosamente: {table} -> {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error exportando {table}: {str(e)}")

if __name__ == "__main__":
    export_all_tables()
