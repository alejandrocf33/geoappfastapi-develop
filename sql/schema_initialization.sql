-- =========================================================================================
-- SCRIPT DE INICIALIZACIÓN DE BASE DE DATOS - GEOAPP
-- Fecha: 2026-02-20
-- Descripción: Este script construye el esquema completo de la base de datos desde cero.
--              Incluye extensiones, tipos, tablas, índices, triggers y funciones almacenadas.
-- =========================================================================================
-- 1. EXTENSIONES
-- =========================================================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
-- 2. TIPOS DE DATOS (ENUMS)
-- =========================================================================================
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM pg_type
    WHERE typname = 'estadoregistro'
) THEN CREATE TYPE estadoregistro AS ENUM ('inicial', 'pendiente', 'aprobado', 'rechazado');
END IF;
END $$;
-- 3. FUNCIONES DE UTILIDAD PARA TRIGGERS
-- =========================================================================================
CREATE OR REPLACE FUNCTION fn_actualizar_updated_at() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- 4. TABLAS PRINCIPALES
-- =========================================================================================
-- Tabla: camaras
CREATE TABLE IF NOT EXISTS camaras (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326),
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR,
    updated_by VARCHAR,
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_camaras_geom ON camaras USING GIST (geom);
-- Tabla: centrales
CREATE TABLE IF NOT EXISTS centrales (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326),
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR,
    updated_by VARCHAR,
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_centrales_geom ON centrales USING GIST (geom);
-- Tabla: empalmes
CREATE TABLE IF NOT EXISTS empalmes (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326),
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR,
    updated_by VARCHAR,
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_empalmes_geom ON empalmes USING GIST (geom);
-- Tabla: reservas
CREATE TABLE IF NOT EXISTS reservas (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326),
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR,
    updated_by VARCHAR,
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_reservas_geom ON reservas USING GIST (geom);
-- Tabla: reportes_mal_estado
CREATE TABLE IF NOT EXISTS reportes_mal_estado (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326),
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR,
    updated_by VARCHAR,
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_reportes_mal_estado_geom ON reportes_mal_estado USING GIST (geom);
-- Tabla: cable_corporativo
CREATE TABLE IF NOT EXISTS cable_corporativo (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(LINESTRING, 4326),
    distancia_metros FLOAT,
    propiedades JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR,
    updated_by VARCHAR,
    estado estadoregistro DEFAULT 'pendiente',
    is_initial_load BOOLEAN DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_cable_corporativo_geom ON cable_corporativo USING GIST (geom);
-- Tabla: red (Topología para pgRouting)
-- Nota: Esta tabla se reconstruye para asegurar consistencia con cable_corporativo
DROP TABLE IF EXISTS red;
CREATE TABLE red AS
SELECT row_number() OVER () AS id,
    geom,
    ST_Length(geom::geography) AS cost,
    ST_Length(geom::geography) AS reverse_cost,
    propiedades->>'name' AS nombre_cable
FROM cable_corporativo
WHERE ST_NPoints(geom) >= 2;
ALTER TABLE red
ADD COLUMN IF NOT EXISTS source integer;
ALTER TABLE red
ADD COLUMN IF NOT EXISTS target integer;
CREATE INDEX IF NOT EXISTS idx_red_geom ON red USING GIST (geom);
-- Construir topología de red
SELECT pgr_createTopology('red', 0.0001, 'geom', 'id');
-- 5. TRIGGERS
-- =========================================================================================
DO $$
DECLARE tabla TEXT;
tablas TEXT [] := ARRAY ['camaras', 'cable_corporativo', 'centrales', 'empalmes', 'reservas', 'reportes_mal_estado'];
BEGIN FOREACH tabla IN ARRAY tablas LOOP EXECUTE format(
    'DROP TRIGGER IF EXISTS trg_updated_at ON %I',
    tabla
);
EXECUTE format(
    '
            CREATE TRIGGER trg_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION fn_actualizar_updated_at()',
    tabla
);
END LOOP;
END $$;
-- 6. FUNCIONES ALMACENADAS
-- =========================================================================================
-- Función: get_nearest_cable
CREATE OR REPLACE FUNCTION public.get_nearest_cable(
        lat double precision,
        lon double precision,
        search_distance_meters double precision
    ) RETURNS TABLE(
        id integer,
        distance_meters double precision,
        properties jsonb,
        geom geometry
    ) LANGUAGE plpgsql AS $function$ BEGIN RETURN QUERY
SELECT c.id,
    ST_Distance(
        ST_Transform(c.geom, 3857),
        ST_Transform(ST_SetSRID(ST_MakePoint(lon, lat), 4326), 3857)
    ) as distance_meters,
    c.propiedades,
    c.geom
FROM cable_corporativo c
WHERE ST_DWithin(
        ST_Transform(c.geom, 3857),
        ST_Transform(ST_SetSRID(ST_MakePoint(lon, lat), 4326), 3857),
        search_distance_meters
    )
ORDER BY distance_meters ASC
LIMIT 1;
END;
$function$;
-- Función: get_cables_cercanos_simple
CREATE OR REPLACE FUNCTION get_cables_cercanos_simple(
        IN p_lon DOUBLE PRECISION,
        IN p_lat DOUBLE PRECISION,
        IN p_distancia_metros DOUBLE PRECISION,
        IN p_limit INTEGER DEFAULT 100,
        IN p_incluir_troncales BOOLEAN DEFAULT FALSE
    ) RETURNS TABLE (
        id INTEGER,
        geom GEOMETRY,
        distancia_metros DOUBLE PRECISION,
        propiedades JSONB,
        distancia_metros_calculada DOUBLE PRECISION,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ,
        created_by VARCHAR,
        updated_by VARCHAR,
        estado VARCHAR,
        is_initial_load BOOLEAN
    ) AS $$ BEGIN RETURN QUERY
SELECT cc.id,
    cc.geom,
    cc.distancia_metros,
    cc.propiedades,
    ST_Distance(
        cc.geom::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
    ) AS distancia_metros_calculada,
    cc.created_at,
    cc.updated_at,
    cc.created_by,
    cc.updated_by,
    cc.estado::VARCHAR,
    cc.is_initial_load
FROM cable_corporativo cc
WHERE (
        p_incluir_troncales
        OR cc.propiedades->>'colocacion' NOT LIKE 'Troncal%'
    )
    AND ST_DWithin(
        cc.geom::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
        p_distancia_metros
    )
ORDER BY ST_Distance(
        cc.geom::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
    ) ASC
LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
-- Función: get_cables_cercanos
CREATE OR REPLACE FUNCTION get_cables_cercanos(
        IN p_lon DOUBLE PRECISION,
        IN p_lat DOUBLE PRECISION,
        IN p_distancia_metros DOUBLE PRECISION,
        IN p_limit INTEGER DEFAULT 100,
        IN p_incluir_troncales BOOLEAN DEFAULT FALSE,
        IN p_nombre_cable TEXT DEFAULT NULL,
        IN p_busqueda_exacta BOOLEAN DEFAULT FALSE
    ) RETURNS TABLE (
        id INTEGER,
        geom GEOMETRY,
        distancia_metros DOUBLE PRECISION,
        propiedades JSONB,
        distancia_metros_calculada DOUBLE PRECISION,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ,
        created_by VARCHAR,
        updated_by VARCHAR,
        estado VARCHAR,
        is_initial_load BOOLEAN
    ) AS $$ BEGIN RETURN QUERY
SELECT cc.id,
    cc.geom,
    cc.distancia_metros,
    cc.propiedades,
    ST_Distance(
        cc.geom::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
    ) AS distancia_metros_calculada,
    cc.created_at,
    cc.updated_at,
    cc.created_by,
    cc.updated_by,
    cc.estado::VARCHAR,
    cc.is_initial_load
FROM cable_corporativo cc
WHERE (
        p_incluir_troncales
        OR cc.propiedades->>'colocacion' NOT LIKE 'Troncal%'
    )
    AND ST_DWithin(
        cc.geom::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
        p_distancia_metros
    )
    AND (
        p_nombre_cable IS NULL
        OR (
            p_busqueda_exacta = TRUE
            AND cc.propiedades->>'name' = p_nombre_cable
        )
        OR (
            p_busqueda_exacta = FALSE
            AND cc.propiedades->>'name' ILIKE '%' || p_nombre_cable || '%'
        )
    )
ORDER BY ST_Distance(
        cc.geom::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
    ) ASC
LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
-- Función: fn_linea_en_ruta_red
CREATE OR REPLACE FUNCTION fn_linea_en_ruta_red(
        lon double precision,
        lat double precision,
        distancia_m double precision,
        incluir_linea boolean DEFAULT true
    ) RETURNS TABLE (linea geometry, punto geometry) AS $$
DECLARE linea_resultado geometry;
linea_final geometry;
longitud_total double precision;
n_puntos integer;
BEGIN -- Obtener la línea completa de la ruta
WITH punto AS (
    SELECT ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geometry AS geom
),
nodo_inicio AS (
    SELECT id
    FROM red_vertices_pgr
    ORDER BY the_geom <->(
            SELECT geom
            FROM punto
        )
    LIMIT 1
), subred AS (
    SELECT *
    FROM pgr_drivingDistance(
            'SELECT id, source, target, cost, reverse_cost FROM red',
            (
                SELECT id
                FROM nodo_inicio
            ),
            distancia_m,
            directed := false
        )
)
SELECT ST_LineMerge(ST_Union(r.geom)) AS geom INTO linea_resultado
FROM subred s
    JOIN red r ON s.edge = r.id;
-- Si no se encontró ninguna ruta, devolver NULL
IF linea_resultado IS NULL THEN RETURN;
END IF;
-- Si sigue siendo MULTILINESTRING, extraer el primer componente y volver a hacer LineMerge
IF GeometryType(linea_resultado) = 'MULTILINESTRING' THEN linea_final := ST_LineMerge(ST_GeometryN(linea_resultado, 1));
ELSE linea_final := linea_resultado;
END IF;
-- Validar que sea un LINESTRING
IF linea_final IS NULL
OR GeometryType(linea_final) != 'LINESTRING' THEN RETURN;
END IF;
-- Calcular la longitud total de la línea
longitud_total := ST_Length(ST_Transform(linea_final, 3857));
IF longitud_total IS NULL
OR longitud_total = 0 THEN RETURN;
END IF;
-- Calcular el número de puntos a devolver
n_puntos := floor(longitud_total / distancia_m);
IF n_puntos < 1 THEN n_puntos := 1;
END IF;
-- Devolver los puntos a intervalos de distancia_m sobre la línea
FOR i IN 1..n_puntos LOOP RETURN QUERY
SELECT CASE
        WHEN incluir_linea THEN linea_final
        ELSE NULL
    END AS linea,
    ST_LineInterpolatePoint(
        linea_final,
        LEAST(1.0, (i * distancia_m) / longitud_total)
    ) AS punto;
END LOOP;
-- Si la distancia no es múltiplo exacto, devolver el último punto de la línea
IF (n_puntos * distancia_m) < longitud_total THEN RETURN QUERY
SELECT CASE
        WHEN incluir_linea THEN linea_final
        ELSE NULL
    END AS linea,
    ST_EndPoint(linea_final) AS punto;
END IF;
END;
$$ LANGUAGE plpgsql;
-- Función: fn_nodos_alcanzables_en_ruta_red
CREATE OR REPLACE FUNCTION fn_nodos_alcanzables_en_ruta_red(
        lon double precision,
        lat double precision,
        distancia_m double precision,
        margen_factor double precision DEFAULT 0.999
    ) RETURNS TABLE (
        geom geometry,
        distancia_acumulada double precision,
        es_mas_cercano integer,
        nombre_cable text
    ) AS $$ BEGIN RETURN QUERY WITH origen AS (
        SELECT id AS node_id
        FROM red_vertices_pgr
        ORDER BY the_geom <->ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        LIMIT 1
    ), alcance AS (
        SELECT dd.node AS node_id,
            v.the_geom AS geom,
            dd.agg_cost AS distancia_acumulada,
            r.nombre_cable
        FROM pgr_drivingdistance(
                'SELECT id, source, target, cost, reverse_cost, nombre_cable FROM red'::text,
                CAST(
                    (
                        SELECT node_id
                        FROM origen
                    ) AS integer
                ),
                distancia_m + (distancia_m * (1 - margen_factor)),
                -- margen de error parametrizable
                false
            ) AS dd
            JOIN red r ON dd.edge = r.id
            JOIN red_vertices_pgr AS v ON dd.node = v.id
    ),
    min_dist AS (
        SELECT MIN(ABS(alcance.distancia_acumulada - distancia_m)) AS min_diff
        FROM alcance
        WHERE alcance.distancia_acumulada >= (distancia_m * margen_factor)
    )
SELECT alcance.geom,
    alcance.distancia_acumulada,
    CASE
        WHEN ABS(alcance.distancia_acumulada - distancia_m) = min_dist.min_diff THEN 1
        ELSE 0
    END AS es_mas_cercano,
    alcance.nombre_cable
FROM alcance
    CROSS JOIN min_dist
WHERE alcance.distancia_acumulada >= (distancia_m * margen_factor)
ORDER BY alcance.distancia_acumulada;
END;
$$ LANGUAGE plpgsql;
-- =========================================================================================
-- FIN DEL SCRIPT
-- =========================================================================================