-- Ejecuta esto completo desde la misma sesión:
DROP TABLE IF EXISTS red;

CREATE TABLE red AS
SELECT
    row_number() OVER () AS id,
    geom,
    ST_Length(geom::geography) AS cost,
    ST_Length(geom::geography) AS reverse_cost,
    propiedades ->> 'name' AS nombre_cable
FROM cable_corporativo
WHERE ST_NPoints(geom) >= 2;

ALTER TABLE red ADD COLUMN IF NOT EXISTS source integer;
ALTER TABLE red ADD COLUMN IF NOT EXISTS target integer;

-- No agregues source y target manualmente; los crea pgr_createTopology
SELECT pgr_createTopology('red', 0.0001, 'geom', 'id');
