-- Active: 1748931841281@@54.234.163.140@5432@geodb
-- Alternativa a fn_linea_en_ruta_red: devuelve todos los nodos alcanzables a una distancia específica desde un punto de inicio
-- Recibe: lon, lat, distancia_m
-- Devuelve: node_id, geom (geometry del nodo), distancia_acumulada

DROP FUNCTION IF EXISTS fn_nodos_alcanzables_en_ruta_red(
    lon double precision,
    lat double precision,
    distancia_m double precision
);
CREATE OR REPLACE FUNCTION fn_nodos_alcanzables_en_ruta_red(
    lon double precision,
    lat double precision,
    distancia_m double precision,
    margen_factor double precision DEFAULT 0.999
)
RETURNS TABLE (
    geom geometry,
    distancia_acumulada double precision,
    es_mas_cercano integer,
    nombre_cable text
) AS
$$
BEGIN
    RETURN QUERY
    WITH origen AS (
        SELECT id AS node_id
        FROM red_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        LIMIT 1
    ),
    alcance AS (
        SELECT 
            dd.node AS node_id,
            v.the_geom AS geom,
            dd.agg_cost AS distancia_acumulada,
            r.nombre_cable
        FROM 
            pgr_drivingdistance(
                'SELECT id, source, target, cost, reverse_cost, nombre_cable FROM red'::text,
                CAST((SELECT node_id FROM origen) AS integer),
                distancia_m + (distancia_m * (1-margen_factor)),  -- margen de error parametrizable
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
    SELECT 
        alcance.geom, 
        alcance.distancia_acumulada,
        CASE WHEN ABS(alcance.distancia_acumulada - distancia_m) = min_dist.min_diff THEN 1 ELSE 0 END AS es_mas_cercano,
        alcance.nombre_cable
    FROM alcance
    CROSS JOIN min_dist
    WHERE alcance.distancia_acumulada >= (distancia_m * margen_factor)
    ORDER BY alcance.distancia_acumulada;
END;
$$ LANGUAGE plpgsql;
