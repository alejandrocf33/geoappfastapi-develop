CREATE OR REPLACE FUNCTION fn_linea_en_ruta_red(
    lon double precision,
    lat double precision,
    distancia_m double precision,
    incluir_linea boolean DEFAULT true
)
RETURNS TABLE (
    linea geometry,
    punto geometry
) AS
$$
DECLARE
    linea_resultado geometry;
    linea_final geometry;
    longitud_total double precision;
    n_puntos integer;
BEGIN
    -- Obtener la línea completa de la ruta
    WITH punto AS (
        SELECT ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geometry AS geom
    ),
    nodo_inicio AS (
        SELECT id
        FROM red_vertices_pgr
        ORDER BY the_geom <-> (SELECT geom FROM punto)
        LIMIT 1
    ),
    subred AS (
        SELECT *
        FROM pgr_drivingDistance(
            'SELECT id, source, target, cost, reverse_cost FROM red',
            (SELECT id FROM nodo_inicio),
            distancia_m,
            directed := false
        )
    )
    SELECT ST_LineMerge(ST_Union(r.geom)) AS geom
    INTO linea_resultado
    FROM subred s
    JOIN red r ON s.edge = r.id;
    
    -- Si no se encontró ninguna ruta, devolver NULL
    IF linea_resultado IS NULL THEN
        RETURN;
    END IF;

    -- Si sigue siendo MULTILINESTRING, extraer el primer componente y volver a hacer LineMerge
    IF GeometryType(linea_resultado) = 'MULTILINESTRING' THEN
        linea_final := ST_LineMerge(ST_GeometryN(linea_resultado, 1));
    ELSE
        linea_final := linea_resultado;
    END IF;

    -- Validar que sea un LINESTRING
    IF linea_final IS NULL OR GeometryType(linea_final) != 'LINESTRING' THEN
        RETURN;
    END IF;

    -- Calcular la longitud total de la línea
    longitud_total := ST_Length(ST_Transform(linea_final, 3857));
    IF longitud_total IS NULL OR longitud_total = 0 THEN
        RETURN;
    END IF;

    -- Calcular el número de puntos a devolver
    n_puntos := floor(longitud_total / distancia_m);
    IF n_puntos < 1 THEN
        n_puntos := 1;
    END IF;

    -- Devolver los puntos a intervalos de distancia_m sobre la línea
    FOR i IN 1..n_puntos LOOP
        RETURN QUERY SELECT 
            CASE WHEN incluir_linea THEN linea_final ELSE NULL END AS linea,
            ST_LineInterpolatePoint(linea_final, LEAST(1.0, (i * distancia_m) / longitud_total)) AS punto;
    END LOOP;

    -- Si la distancia no es múltiplo exacto, devolver el último punto de la línea
    IF (n_puntos * distancia_m) < longitud_total THEN
        RETURN QUERY SELECT 
            CASE WHEN incluir_linea THEN linea_final ELSE NULL END AS linea,
            ST_EndPoint(linea_final) AS punto;
    END IF;
END;
$$ LANGUAGE plpgsql;
