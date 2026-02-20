# Documentación de Scripts SQL

## Script de Inicialización Unificado

**Archivo:** `sql/schema_initialization.sql`

Este script contiene todo lo necesario para inicializar la estructura de la base de datos de GeoApp Cartografía desde cero.

### Contenido

1. **Extensiones:** Habilita `postgis` y `pgrouting`.
2. **Tipos:** Crea el tipo ENUM `estadoregistro`.
3. **Tablas:** Crea las tablas:
    * `camaras`
    * `centrales`
    * `empalmes`
    * `reservas`
    * `reportes_mal_estado`
    * `cable_corporativo`
    * `red` (topología)
4. **Índices:** Crea índices espaciales (GIST) para todas las columnas de geometría.
5. **Triggers:** Configura la actualización automática de `updated_at`.
6. **Funciones:**
    * `get_nearest_cable`
    * `get_cables_cercanos`
    * `fn_linea_en_ruta_red`
    * `fn_nodos_alcanzables_en_ruta_red`

### Cómo Ejecutar

Se puede ejecutar este script utilizando cualquier cliente de PostgreSQL (pgAdmin, DBeaver, psql).

**Ejemplo con psql:**

```bash
psql -h <host> -U <usuario> -d <base_de_datos> -f sql/schema_initialization.sql
```

**Nota:**
El script está diseñado para ser seguro de ejecutar (idempotente para tablas existentes con `IF NOT EXISTS`), **EXCEPTO** para la tabla `red`, que se elimina y recrea (`DROP TABLE IF EXISTS red`) para asegurar que la topología de ruteo esté siempre sincronizada con `cable_corporativo`.

## Archivos Legados (`sql/legacy`)

Los archivos en esta carpeta son **OBSOLETOS** y se conservan solo como referencia histórica. Su funcionalidad ha sido incorporada en `schema_initialization.sql`.

| Archivo | Descripción |
| :--- | :--- |
| `create_table_reportes_mal_estado.sql` | Creación inicial de la tabla. |
| `fix_reportes_mal_estado_schema.sql` | Script de corrección (ya aplicado). |
| `create_trigger_updated_at.sql` | Trigger para `updated_at`. |
| `get_cables_cercanos.sql` | Funciones de búsqueda. |
| ... | Otros scripts individuales. |

**NO EJECUTAR ESTOS ARCHIVOS INDIVIDUALMENTE SI SE USA `schema_initialization.sql`.**
