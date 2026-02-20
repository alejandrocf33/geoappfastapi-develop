-- Función base: solo filtra por distancia y troncales
CREATE OR REPLACE FUNCTION get_cables_cercanos_simple(
    IN p_lon DOUBLE PRECISION,
    IN p_lat DOUBLE PRECISION,
    IN p_distancia_metros DOUBLE PRECISION,
    IN p_limit INTEGER DEFAULT 100,
    IN p_incluir_troncales BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
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
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cc.id,
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
    FROM 
        cable_corporativo cc
    WHERE
        (p_incluir_troncales OR cc.propiedades ->> 'colocacion' NOT LIKE 'Troncal%')
        AND ST_DWithin(
            cc.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
            p_distancia_metros
        )
    ORDER BY
        ST_Distance(
            cc.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
        ) ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Función extendida: filtra por nombre de cable y búsqueda exacta/parcial
CREATE OR REPLACE FUNCTION get_cables_cercanos(
    IN p_lon DOUBLE PRECISION,
    IN p_lat DOUBLE PRECISION,
    IN p_distancia_metros DOUBLE PRECISION,
    IN p_limit INTEGER DEFAULT 100,
    IN p_incluir_troncales BOOLEAN DEFAULT FALSE,
    IN p_nombre_cable TEXT DEFAULT NULL,
    IN p_busqueda_exacta BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
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
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cc.id,
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
    FROM 
        cable_corporativo cc
    WHERE
        (p_incluir_troncales OR cc.propiedades ->> 'colocacion' NOT LIKE 'Troncal%')
        AND ST_DWithin(
            cc.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
            p_distancia_metros
        )
        AND (
            p_nombre_cable IS NULL
            OR (p_busqueda_exacta = TRUE AND cc.propiedades ->> 'name' = p_nombre_cable)
            OR (p_busqueda_exacta = FALSE AND cc.propiedades ->> 'name' ILIKE '%' || p_nombre_cable || '%')
        )
    ORDER BY
        ST_Distance(
            cc.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
        ) ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
