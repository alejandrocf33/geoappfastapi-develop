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

-- ========================================
-- CONSULTAS DE VERIFICACIÓN DE DATOS
-- ========================================

-- Consulta completa de cámaras con todos los campos del formulario de registro
-- Muestra: campos base + propiedades JSONB + coordenadas extraídas
SELECT
    id,
    estado,
    created_at,
    updated_at,
    created_by,
    updated_by,
    -- Propiedades JSONB
    propiedades->>'type' as tipo,
    propiedades->>'nombre_esp' as nombre_esp,
    propiedades->>'apertura' as apertura,
    propiedades->>'ubicacion' as ubicacion,
    propiedades->>'propietari' as propietario,
    propiedades->>'estado_cam' as estado_camara,
    propiedades->>'estado_tapa' as estado_tapa,
    propiedades->>'observaciones' as observaciones,
    propiedades->>'remedy_id' as id_tarea_remedy,
    propiedades->>'tecnico' as tecnico,
    propiedades->>'codigo_etb' as codigo_etb,
    propiedades->>'marquillado' as marquillado,
    propiedades->>'id_texto' as id_texto,
    propiedades->>'constructi' as constructi,
    -- Coordenadas desde la geometría
    ST_X(geom::geometry) as longitud,
    ST_Y(geom::geometry) as latitud
FROM camaras
WHERE estado = 'pendiente'
ORDER BY id DESC
LIMIT 5;

-- Consulta completa de empalmes con todos los campos del formulario de registro
-- Muestra: campos base + propiedades JSONB + coordenadas extraídas
SELECT
    id,
    estado,
    created_at,
    updated_at,
    created_by,
    updated_by,
    -- Propiedades JSONB
    propiedades->>'name' as etiqueta_cable_marquilla,
    propiedades->>'type' as tipo,
    propiedades->>'tipo_empalme' as tipo_empalme,
    propiedades->>'cable1' as cable1,
    propiedades->>'cable2' as cable2,
    propiedades->>'observaciones' as observaciones,
    propiedades->>'remedy_id' as id_tarea_remedy,
    propiedades->>'tecnico' as tecnico,
    -- Coordenadas desde la geometría
    ST_X(geom::geometry) as longitud,
    ST_Y(geom::geometry) as latitud
FROM empalmes
WHERE estado = 'pendiente'
ORDER BY id DESC
LIMIT 5;

-- Consulta completa de cables corporativos con todos los campos del formulario de registro
-- Muestra: campos base + propiedades JSONB + geometría del cable
SELECT
    id,
    estado,
    created_at,
    updated_at,
    created_by,
    updated_by,
    -- Propiedades JSONB
    propiedades->>'colocacion' as colocacion,
    propiedades->>'nombre_esp' as nombre_esp,
    propiedades->>'observaciones' as observaciones,
    propiedades->>'remedy_id' as id_tarea_remedy,
    propiedades->>'tecnico' as tecnico,
    -- Geometría del cable
    ST_Length(geom::geography) as longitud_metros,
    -- Coordenadas de inicio y fin
    ST_X(ST_StartPoint(geom::geometry)) as longitud_inicial,
    ST_Y(ST_StartPoint(geom::geometry)) as latitud_inicial,
    ST_X(ST_EndPoint(geom::geometry)) as longitud_final,
    ST_Y(ST_EndPoint(geom::geometry)) as latitud_final
FROM cable_corporativo
WHERE estado = 'pendiente'
ORDER BY id DESC
LIMIT 5;

-- Consulta completa de reportes de mal estado con todos los campos del formulario
-- Muestra: campos base + propiedades JSONB + coordenadas extraídas
SELECT
    id,
    estado,
    created_at,
    updated_at,
    created_by,
    updated_by,
    -- Propiedades JSONB (del formulario)
    propiedades->>'numero_cable' as numero_cable,
    propiedades->>'nivel_dano' as nivel_dano,
    propiedades->>'direccion' as direccion,
    propiedades->>'observaciones' as observaciones,
    propiedades->>'remedy_id' as id_tarea_remedy,
    propiedades->>'tecnico' as tecnico,
    -- Coordenadas desde la geometría
    ST_X(geom::geometry) as longitud,
    ST_Y(geom::geometry) as latitud
FROM reportes_mal_estado
WHERE estado = 'pendiente'
ORDER BY id DESC
LIMIT 5;

-- ========================================
-- CONSULTAS ÚTILES ADICIONALES
-- ========================================

-- Contar registros por estado en cámaras
SELECT estado, COUNT(*) as cantidad
FROM camaras
GROUP BY estado;

-- Contar registros por estado en empalmes
SELECT estado, COUNT(*) as cantidad
FROM empalmes
GROUP BY estado;

-- Contar registros por estado en cables corporativos
SELECT estado, COUNT(*) as cantidad
FROM cable_corporativo
GROUP BY estado;

-- Contar registros por estado en reportes de mal estado
SELECT estado, COUNT(*) as cantidad
FROM reportes_mal_estado
GROUP BY estado;

-- Ver todos los registros pendientes de aprobación (resumen por tipo)
SELECT 'camaras' as tipo, COUNT(*) as pendientes
FROM camaras WHERE estado = 'pendiente'
UNION ALL
SELECT 'empalmes', COUNT(*)
FROM empalmes WHERE estado = 'pendiente'
UNION ALL
SELECT 'cables', COUNT(*)
FROM cable_corporativo WHERE estado = 'pendiente'
UNION ALL
SELECT 'reportes', COUNT(*)
FROM reportes_mal_estado WHERE estado = 'pendiente';

-- Verificar registros creados por un usuario específico en cámaras
-- (Reemplazar 'nombre_usuario' con el usuario a buscar)
SELECT id, created_at, created_by, updated_by, estado,
       propiedades->>'nombre_esp' as nombre
FROM camaras
WHERE created_by = 'nombre_usuario'
ORDER BY created_at DESC;

-- Ver últimos 10 registros creados en todas las tablas (con tipo de elemento)
SELECT 'camara' as tipo_elemento, id, created_at, created_by, estado,
       propiedades->>'nombre_esp' as nombre
FROM camaras
UNION ALL
SELECT 'empalme', id, created_at, created_by, estado,
       propiedades->>'name'
FROM empalmes
UNION ALL
SELECT 'cable', id, created_at, created_by, estado,
       propiedades->>'nombre_esp'
FROM cable_corporativo
UNION ALL
SELECT 'reporte', id, created_at, created_by, estado,
       propiedades->>'numero_cable'
FROM reportes_mal_estado
ORDER BY created_at DESC
LIMIT 10;

-- Ver cables con su longitud calculada en metros
SELECT id,
       propiedades->>'nombre_esp' as nombre,
       propiedades->>'colocacion' as colocacion,
       ST_Length(geom::geography) as longitud_metros,
       estado, created_at
FROM cable_corporativo
ORDER BY id DESC
LIMIT 10;

-- Buscar elementos cerca de una ubicación específica (radio en metros)
-- Ejemplo: buscar cámaras en radio de 1000 metros desde un punto
SELECT id,
       propiedades->>'nombre_esp' as nombre,
       propiedades->>'codigo_etb' as codigo,
       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(-74.0817, 4.6097), 4326)::geography) as distancia_metros,
       estado
FROM camaras
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(-74.0817, 4.6097), 4326)::geography,
    1000
)
ORDER BY distancia_metros
LIMIT 10;