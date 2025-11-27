-- 1. Encontrar el nodo más cercano al punto de origen (Bogotá, Colombia en este ejemplo)
WITH origen AS (
  SELECT id AS node_id
  FROM red_vertices_pgr
  ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(-74.126022, 4.57189), 4326)
  LIMIT 1
),

-- 2. Calcular todos los nodos alcanzables dentro de 5000 unidades (metros, por ejemplo)
alcance AS (
  SELECT 
    dd.node AS node_id,
    v.the_geom AS geom,
    dd.agg_cost AS distancia_acumulada
  FROM 
    pgr_drivingDistance(
      'SELECT id, source, target, cost, reverse_cost FROM red',
      (SELECT node_id FROM origen),
      (2632 + (2632*(1-0.999))),  -- Distancia máxima (ajusta según tus necesidades)
      false
    ) AS dd
  JOIN 
    red_vertices_pgr AS v ON dd.node = v.id
)

-- 3. Seleccionar los resultados finales
SELECT * FROM alcance
WHERE distancia_acumulada >= (2632*0.999)  -- Ajusta el margen de error según sea necesario
ORDER BY distancia_acumulada;