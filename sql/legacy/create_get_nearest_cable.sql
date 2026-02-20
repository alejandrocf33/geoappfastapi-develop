CREATE OR REPLACE FUNCTION public.get_nearest_cable(lat double precision, lon double precision, search_distance_meters double precision)
 RETURNS TABLE(id integer, distance_meters double precision, properties jsonb, geom geometry)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
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
$function$
