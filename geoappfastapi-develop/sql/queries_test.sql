-- Active: 1748536286729@@aws-0-us-east-2.pooler.supabase.com@5432@postgres
-- Active: 1748931841281@@54.234.163.140@5432@geodb
-- Esta función devuelve tanto la línea de la ruta como el punto a la distancia especificada
SELECT * FROM pg_available_extensions WHERE name ILIKE 'pgrouting';

select *
from red_vertices_pgr;

select *
from red;

select *
from red_vertices_pgr
order by id desc;

SELECT id AS node_id
        FROM red_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(-74.145085, 4.668443), 4326)
        LIMIT 1;
SELECT
  p.proname,
  p.oid,
  p.proargtypes,
  pg_catalog.pg_get_function_identity_arguments(p.oid) AS args
FROM pg_proc p
WHERE proname ILIKE 'pgr_drivingdistance';

SELECT id, source, target, cost, reverse_cost, nombre_cable FROM red;

SELECT n.nspname, p.proname, pg_get_function_arguments(p.oid)
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE proname = 'pgr_drivingdistance';

SELECT proname, pg_get_function_arguments(p.oid)
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE proname ILIKE 'pgr_drivingdistance';


SELECT * FROM pg_catalog.pg_tables LIMIT 5;
SELECT current_user, session_user;


SELECT linea, punto FROM fn_linea_en_ruta_red(-74.145085, 4.668443, 2000, false);
SELECT * FROM fn_nodos_alcanzables_en_ruta_red(-74.145085, 4.668443, 2650);

select * from get_cables_cercanos(-74.145085, 4.668443, 2000, 100, false, null, null);