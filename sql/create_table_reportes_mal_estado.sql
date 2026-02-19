-- HU7: Tabla para reportes de cierre por mal estado
-- Ejecutar en la base de datos PostgreSQL/PostGIS antes de usar el endpoint POST /reporte_mal_estado

CREATE TABLE IF NOT EXISTS reportes_mal_estado (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Point, 4326),
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);

-- Indice espacial para consultas por ubicacion
CREATE INDEX IF NOT EXISTS idx_reportes_mal_estado_geom
ON reportes_mal_estado USING GIST (geom);
