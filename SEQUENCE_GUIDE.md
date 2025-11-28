# filepath: d:\Proyecto\geoapis\SEQUENCE_GUIDE.md
# Guía para el Manejo de Secuencias en PostgreSQL

Este documento proporciona una guía detallada para solucionar y prevenir problemas relacionados con las secuencias de ID en la base de datos PostgreSQL de GeoAPIs.

## Problema Común: "duplicate key value violates unique constraint"

Este error ocurre cuando:
- Se intentan insertar datos con IDs que ya existen en la tabla.
- Las secuencias de PostgreSQL no están sincronizadas con los máximos valores de ID existentes.

## Solución 1: Restablecer las Secuencias de PostgreSQL

En GeoAPIs, hemos implementado una solución para actualizar automáticamente las secuencias:

```bash
# En Windows PowerShell
cd d:\ruta\a\geoapis
python -m app.reset_sequences

# En Linux/macOS
cd /ruta/a/geoapis
python -m app.reset_sequences
```

Este script:
1. Consulta el máximo ID existente en cada tabla 
2. Establece la secuencia de cada tabla para comenzar desde (máximo ID + 1)
3. Garantiza que las nuevas inserciones no causen conflictos de claves primarias

## ¿Cuándo Restablecer las Secuencias?

Se debe ejecutar el script `reset_sequences.py` después de:

1. Cargar datos iniciales con IDs explícitos
2. Realizar inserciones manuales en la base de datos
3. Migrar datos desde otra base de datos
4. Recibir errores de "duplicate key value violates unique constraint"

## Prevención en Operaciones ETL y Carga de Datos

Si tienes procesos ETL que cargan datos con IDs explícitos, considera:

1. Añadir el restablecimiento de secuencias como último paso del proceso ETL
2. Usar rangos de IDs no conflictivos (por ejemplo: IDs negativos para datos de prueba)
3. Implementar una verificación periódica de secuencias como parte del mantenimiento

## Scripts SQL para Verificación Manual

Si necesitas verificar manualmente las secuencias desde SQL:

```sql
-- Consultar el valor actual de una secuencia
SELECT last_value, is_called FROM nombre_tabla_id_seq;

-- Consultar el ID máximo de una tabla
SELECT MAX(id) FROM nombre_tabla;

-- Actualizar manualmente una secuencia
ALTER SEQUENCE nombre_tabla_id_seq RESTART WITH valor_deseado;
```

## Ejemplo de Restauración de Secuencias Tabla por Tabla

Si necesitas restaurar las secuencias manualmente:

```sql
-- Para tabla camaras
SELECT setval('camaras_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM camaras), true);

-- Para tabla cable_corporativo
SELECT setval('cable_corporativo_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM cable_corporativo), true);

-- Para tabla centrales
SELECT setval('centrales_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM centrales), true);

-- Para tabla empalmes
SELECT setval('empalmes_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM empalmes), true);

-- Para tabla reservas
SELECT setval('reservas_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM reservas), true);
```

## Nota sobre `setup.py`

Al ejecutar `setup.py`, las secuencias se restablecen automáticamente después de cargar los datos iniciales, asegurando que no haya conflictos de ID al agregar nuevos elementos.
