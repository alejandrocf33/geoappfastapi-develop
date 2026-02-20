# Guía de Pruebas QA — Registro de Elementos

Guía completa para el equipo QA sobre cómo completar correctamente cada formulario de registro, valores válidos, y verificación de datos.

---

## Tabla de Contenidos

1. [Contexto del Sistema](#contexto-del-sistema)
2. [Autenticación](#autenticación)
3. [Coordenadas de Prueba](#coordenadas-de-prueba)
4. [Formularios de Registro](#formularios-de-registro)
   - [1. Cámara](#1-cámara)
   - [2. Empalme](#2-empalme)
   - [3. Cable Corporativo](#3-cable-corporativo)
   - [4. Reporte Cierre Mal Estado](#4-reporte-cierre-mal-estado)
5. [Errores Comunes](#errores-comunes)
6. [Verificación de Datos con SQL](#verificación-de-datos-con-sql)
7. [URLs de la API](#urls-de-la-api)

---

## Contexto del Sistema

GeoAPIs es un sistema de gestión de infraestructura geoespacial para la red de fibra óptica. Permite registrar, consultar y gestionar elementos físicos de la red con sus ubicaciones geográficas precisas.

### Documentación Relacionada

- 📖 [Database Schema](database-schema.md) - Esquema completo de base de datos
- 📮 [Postman Integration](integracion-postman.md) - Testing con Postman
- 🔐 [Autenticación](autenticacion.md) - Guía de autenticación HTTP Basic

### Tipos de Elementos

| Tipo de Elemento | Tabla BD | Geometría | Endpoint API |
| ---------------- | -------- | --------- | ------------ |
| Cámara | `camaras` | POINT | `POST /api/camaras` |
| Empalme | `empalmes` | POINT | `POST /api/empalmes` |
| Cable Corporativo | `cable_corporativo` | LINESTRING | `POST /api/cable_corporativo` |
| Reporte Mal Estado | `reportes_mal_estado` | POINT | `POST /api/reporte_mal_estado` |

### Estados de Registro

Todos los registros nuevos se crean con estado **`pendiente`** y deben ser aprobados por un supervisor.

| Estado | Descripción |
| ------ | ----------- |
| `pendiente` | Registro nuevo esperando aprobación (estado por defecto) |
| `aprobado` | Validado y aprobado por supervisor |
| `rechazado` | Rechazado, requiere corrección |
| `inicial` | Datos de carga inicial del sistema (históricos) |

---

## Autenticación

**Todos los endpoints requieren HTTP Basic Authentication.**

### En Postman
1. Ir a la pestaña **Authorization**
2. Seleccionar tipo **Basic Auth**
3. Ingresar usuario y contraseña de la API

### En curl
```bash
curl -u usuario:contraseña -X POST https://api-url/api/camaras \
  -H "Content-Type: application/json" \
  -d '{"latitud": 4.6097, "longitud": -74.0817, ...}'
```

### Respuesta de Error
```json
HTTP 401 Unauthorized
{
  "detail": "Credenciales incorrectas"
}
```

---

## Coordenadas de Prueba

Para pruebas manuales desde Postman (sin GPS), usar coordenadas reales de Bogotá:

| Zona | Latitud | Longitud | Descripción |
| ---- | -------- | -------- | ----------- |
| Centro | `4.5981` | `-74.0761` | Plaza de Bolívar |
| Norte | `4.7437` | `-74.0616` | Usaquén |
| Sur | `4.5000` | `-74.1200` | Soacha |
| Occidente | `4.6500` | `-74.1500` | Fontibón |
| Oriente | `4.6097` | `-74.0817` | Chapinero |

**Formato**: Grados decimales (WGS84)

---

## Formularios de Registro

### 1. Cámara

**Endpoint**: `POST /api/camaras`

**Descripción**: Cámaras de inspección subterráneas (manholes) que permiten el acceso a cables de fibra óptica.

#### Campos del Formulario

| Campo | Nombre API | Tipo | Requerido | Notas |
| ----- | ---------- | ---- | --------- | ----- |
| Marquillado (SÍ/NO) | `marquillado` | string | No | "SÍ" o "NO" |
| Nombre (ESP) | `nombre_esp` | string | No | Nombre descriptivo |
| Apertura | `apertura` | string | No | Ver valores válidos |
| Ubicación (Dirección) | `ubicacion` | string | No | Dirección física |
| Propietario | `propietari` | string | No | Ver valores válidos |
| Estado Cámara | `estado_cam` | string | No | "SIN NOVEDAD" o "CON GASES" |
| Estado Tapa | `estado_tapa` | string | No | Ver valores válidos |
| Observaciones | `observaciones` | string | No | Texto libre |
| ID Tarea REMEDY | `remedy_id` | string | No | Auto-llenado (ej: "INC000012345") |
| Técnico | `tecnico` | string | No | Auto-llenado |
| Código ETB | `codigo_etb` | string | No | Código único ETB |
| **Longitud** | `longitud` | float | **SÍ** | Auto-llenado con GPS |
| **Latitud** | `latitud` | float | **SÍ** | Auto-llenado con GPS |

#### Valores Válidos

**Apertura**:
- `ESTANDAR`
- `MAGNETICA`
- `ESTANDAR SOLDADA`
- `LLAVE DE SEGURIDAD`
- `CORCHO DIFERENCIAL`
- `CORTINA - CANDADO`
- `Llave de Seguridad - SOLDADA`
- `CORCHO GRUA`

**Propietario**:
- `ETB`
- `CODENSA`
- `OTROS OPERADORES`
- `SDM`
- `SMV`
- `EMSA`

**Estado Tapa**:
- `Buena`
- `En daño`
- `Sin seguridad`
- `Sin tapa`

#### Ejemplo JSON para Postman

```json
{
  "marquillado": "SÍ",
  "nombre_esp": "CAM-QA-NORTE-001",
  "apertura": "ESTANDAR",
  "ubicacion": "Calle 100 # 15-20, Bogotá",
  "propietari": "ETB",
  "estado_cam": "SIN NOVEDAD",
  "estado_tapa": "Buena",
  "observaciones": "Registro de prueba QA",
  "remedy_id": "TAS000000107501",
  "tecnico": "GRD_ASG_FIBRA",
  "codigo_etb": "2012T78",
  "latitud": 4.6097,
  "longitud": -74.0817
}
```

#### Respuesta Exitosa

```json
HTTP 200 OK
{
  "message": "Cámara insertada correctamente",
  "id": 123,
  "objectid": 123
}
```

---

### 2. Empalme

**Endpoint**: `POST /api/empalmes`

**Descripción**: Puntos de conexión/empalme entre cables de fibra óptica (mecánicos o por fusión).

#### Campos del Formulario

| Campo | Nombre API | Tipo | Requerido | Notas |
| ----- | ---------- | ---- | --------- | ----- |
| Etiqueta Cable (Marquilla) | `name` | string | No | Identificador del empalme |
| Tipo | `type` | string | No | "Mecánico" o "Fusión" |
| Tipo Empalme | `tipo_empalme` | string | No | Ver valores válidos |
| Cable 1 | `cable1` | string | No | Nombre del cable 1 |
| Cable 2 | `cable2` | string | No | Nombre del cable 2 |
| Observaciones | `observaciones` | string | No | Texto libre |
| ID Tarea REMEDY | `remedy_id` | string | No | Auto-llenado |
| Técnico | `tecnico` | string | No | Auto-llenado |
| **Longitud** | `longitud` | float | **SÍ** | Auto-llenado con GPS |
| **Latitud** | `latitud` | float | **SÍ** | Auto-llenado con GPS |

**Nota**: El campo "Ubicación" en el formulario es solo para geocodificación (no se envía a la API).

#### Valores Válidos

**Tipo Empalme**:
- `T-T` - Tierra-Tierra
- `T-A` - Tierra-Aéreo
- `A-A` - Aéreo-Aéreo

#### Ejemplo JSON para Postman

```json
{
  "name": "EMP-QA-001",
  "type": "Mecánico",
  "tipo_empalme": "T-T",
  "cable1": "CABLE-QA-001",
  "cable2": "CABLE-QA-002",
  "remedy_id": "TAS000000107501",
  "tecnico": "GRD_ASG_FIBRA",
  "observaciones": "Empalme de prueba QA",
  "latitud": 4.6647,
  "longitud": -74.0917
}
```

#### Respuesta Exitosa

```json
HTTP 200 OK
{
  "message": "Empalme insertado correctamente",
  "id": 321,
  "objectid": 321
}
```

---

### 3. Cable Corporativo

**Endpoint**: `POST /api/cable_corporativo`

**Descripción**: Cables de fibra óptica que forman la red troncal y de acceso. Requiere mínimo 2 puntos (inicio y fin).

#### Campos del Formulario

| Campo | Nombre API | Tipo | Requerido | Notas |
| ----- | ---------- | ---- | --------- | ----- |
| Colocación | `colocacion` | string | No | "Troncal", "Acceso", o "Troncal-Acceso" |
| Nombre ESP | `nombre_esp` | string | No | Nombre descriptivo |
| Observaciones | `observaciones` | string | No | Texto libre |
| ID Tarea REMEDY | `remedy_id` | string | No | Auto-llenado |
| Técnico | `tecnico` | string | No | Auto-llenado |
| **Puntos** | `puntos` | array | **SÍ** | Mínimo 2 puntos (inicio y fin) |

**Nota**: Los campos "Ubicación Inicial" y "Ubicación Final" son solo para geocodificación (no se envían a la API).

#### Estructura del Array de Puntos

Cada punto debe tener `latitud` y `longitud`:

```json
{
  "puntos": [
    {"latitud": 4.6097, "longitud": -74.0817},  // Punto inicial
    {"latitud": 4.6125, "longitud": -74.0845}   // Punto final
  ]
}
```

#### Ejemplo JSON para Postman

```json
{
  "colocacion": "Troncal-Acceso",
  "nombre_esp": "Ductado 24h senc",
  "remedy_id": "TAS000000107501",
  "tecnico": "GRD_ASG_FIBRA",
  "observaciones": "Cable de prueba QA",
  "puntos": [
    {"latitud": 4.6097, "longitud": -74.0817},
    {"latitud": 4.6125, "longitud": -74.0845}
  ]
}
```

#### Respuesta Exitosa

```json
HTTP 200 OK
{
  "message": "Cable corporativo insertado correctamente",
  "id": 456,
  "objectid": 456
}
```

#### Error Común: Menos de 2 Puntos

```json
HTTP 422 Unprocessable Entity
{
  "detail": "Se requieren al menos 2 puntos para formar un cable (LineString)"
}
```

**Solución**: Asegurarse de que tanto el punto inicial como final estén diligenciados.

---

### 4. Reporte Cierre Mal Estado

**Endpoint**: `POST /api/reporte_mal_estado`

**Descripción**: Registros de infraestructura en mal estado que requiere mantenimiento o reparación.

#### Campos del Formulario

| Campo | Nombre API | Tipo | Requerido | Notas |
| ----- | ---------- | ---- | --------- | ----- |
| Número de Cable | `numero_cable` | string | No | Cable afectado |
| Nivel de Daño | `nivel_dano` | string | No | Ver valores válidos |
| Dirección | `direccion` | string | No | Dirección del reporte |
| Observaciones | `observaciones` | string | No | Descripción del problema |
| ID Tarea REMEDY | `remedy_id` | string | No | Auto-llenado |
| Técnico | `tecnico` | string | No | Auto-llenado |
| **Longitud** | `longitud` | float | **SÍ** | Obligatorio |
| **Latitud** | `latitud` | float | **SÍ** | Obligatorio |

**Nota**: La ubicación es **obligatoria** en este formulario.

#### Valores Válidos

**Nivel de Daño**:
- `Alto` - Requiere atención inmediata
- `Medio` - Requiere planificación de reparación
- `Bajo` - Mantenimiento preventivo

#### Ejemplo JSON para Postman

```json
{
  "numero_cable": "CABLE-QA-001",
  "nivel_dano": "Medio",
  "direccion": "Calle 80 # 30-40, Bogotá",
  "observaciones": "Caja rota con cables expuestos",
  "remedy_id": "TAS000000107501",
  "tecnico": "GRD_ASG_FIBRA",
  "latitud": 4.6500,
  "longitud": -74.1200
}
```

#### Respuesta Exitosa

```json
HTTP 200 OK
{
  "message": "Reporte de mal estado registrado correctamente",
  "id": 789
}
```

---

## Errores Comunes

### Errores HTTP y Soluciones

| Código HTTP | Causa | Solución |
| ----------- | ----- | -------- |
| **401 Unauthorized** | Credenciales incorrectas | Verificar usuario/contraseña en Basic Auth |
| **403 Forbidden** | Origen no autorizado | Verificar que la petición viene de origen permitido |
| **409 Conflict** | `id_texto` duplicado (Empalme) | Usar un valor distinto o dejarlo vacío |
| **422 Unprocessable Entity** | Campo requerido vacío o inválido | Revisar que latitud/longitud estén presentes. Para cables, verificar mínimo 2 puntos |
| **500 Internal Server Error** | Error interno de base de datos | Revisar logs del servidor o contactar soporte |

### Validaciones Específicas

**Cámaras**:
- Coordenadas obligatorias
- Valores de apertura, propietario y estado_tapa deben coincidir con valores válidos

**Empalmes**:
- Coordenadas obligatorias
- `id_texto` debe ser único (si se proporciona)

**Cables**:
- Mínimo 2 puntos en el array `puntos`
- Cada punto debe tener `latitud` y `longitud`

**Reportes**:
- Coordenadas obligatorias (marcadas como "Ubicación (Obligatorio)" en formulario)
- `nivel_dano` debe ser "Alto", "Medio" o "Bajo"

---

## Verificación de Datos con SQL

Para verificar que los datos se guardaron correctamente, se recomienda usar herramientas SQL como **pgAdmin 4** para ejecutar consultas directamente en la base de datos.

> ⚠️ **ADVERTENCIA - Migración de Esquema Requerida**
>
> Si al ejecutar consultas en la tabla `reportes_mal_estado` obtienes errores como:
>
> - `ERROR: column "estado" does not exist`
> - `ERROR: column "updated_at" does not exist`
> - `ERROR: column "created_at" does not exist`
>
> Debes ejecutar primero la migración de esquema:
>
> ```sql
> -- Ejecutar el contenido completo del archivo:
> -- sql/fix_reportes_mal_estado_schema.sql
> ```
>
> Esta migración agrega las columnas faltantes de `BaseFeaturesTable` que son necesarias para el correcto funcionamiento del sistema. Ver [Database Schema](database-schema.md) para más detalles.

---

### Herramientas de Testing SQL

#### pgAdmin 4 (Recomendado)

**pgAdmin 4** es la herramienta IDE oficial de PostgreSQL para ejecutar consultas SQL directamente.

**Instalación**:
- Descargar desde: [https://www.pgadmin.org/download/](https://www.pgadmin.org/download/)
- Disponible para Windows, Mac y Linux

**Configuración de Conexión**:

1. Abrir pgAdmin 4
2. Click derecho en "Servers" → "Register" → "Server"
3. Configurar credenciales desde archivo `.env`:
   - **Name**: GeoAPIs (nombre descriptivo)
   - **Host**: valor de `DB_HOST`
   - **Port**: valor de `DB_PORT`
   - **Database**: valor de `DB_NAME`
   - **Username**: valor de `DB_USER`
   - **Password**: valor de `DB_PASSWORD`
   - **SSL Mode**: Require
4. Guardar y conectar

**Características Útiles**:
- Query Tool con autocompletado SQL
- Visualizador de geometrías PostGIS
- Exportación de resultados a CSV/Excel
- Historial de consultas
- Explicación de planes de ejecución

#### Herramientas Alternativas

| Herramienta | Descripción | Plataforma | Características Destacadas |
| ----------- | ----------- | ---------- | ------------------------- |
| **DBeaver** | Cliente universal SQL open-source | Windows, Mac, Linux | Soporte PostGIS, visualización de geometrías, ER diagrams |
| **DataGrip** | IDE de JetBrains (de pago) | Windows, Mac, Linux | Refactoring SQL, debugging, comparación de esquemas |
| **psql** | CLI oficial de PostgreSQL | Windows, Mac, Linux | Scripting, automatización, ligero |
| **QGIS** | GIS desktop con soporte PostGIS | Windows, Mac, Linux | Visualización avanzada de mapas y geometrías |

---

### Consultas de Verificación por Entidad

#### 1. Verificación de Cámaras

Muestra todos los campos del formulario de registro de cámaras:

```sql
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
```

**Uso**:
1. Abrir pgAdmin 4 y conectarse
2. Click derecho en la base de datos → "Query Tool"
3. Copiar y pegar la consulta
4. Ejecutar (F5 o botón ▶)
5. Verificar que los datos coincidan con el formulario

#### 2. Verificación de Empalmes

Muestra todos los campos del formulario de registro de empalmes:

```sql
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
```

#### 3. Verificación de Cables Corporativos

Muestra todos los campos del formulario incluyendo coordenadas de inicio/fin y longitud calculada:

```sql
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
```

#### 4. Verificación de Reportes de Mal Estado

Muestra todos los campos del formulario de reportes:

```sql
SELECT
    id,
    estado,
    created_at,
    updated_at,
    created_by,
    updated_by,
    -- Propiedades JSONB
    propiedades->>'numero_cable' as numero_cable,
    propiedades->>'nivel_dano' as nivel_dano,
    propiedades->>'direccion' as direccion,
    propiedades->>'observaciones' as observaciones,
    propiedades->>'remedy_id' as id_tarea_remedy,
    propiedades->>'tecnico' as tecnico,
    -- Coordenadas
    ST_X(geom::geometry) as longitud,
    ST_Y(geom::geometry) as latitud
FROM reportes_mal_estado
WHERE estado = 'pendiente'
ORDER BY id DESC
LIMIT 5;
```

---

### Consultas de Análisis y Estadísticas

#### Conteo de Registros por Estado

**Por tabla individual**:
```sql
-- Cámaras
SELECT estado, COUNT(*) as cantidad
FROM camaras
GROUP BY estado
ORDER BY cantidad DESC;

-- Empalmes
SELECT estado, COUNT(*) as cantidad
FROM empalmes
GROUP BY estado
ORDER BY cantidad DESC;

-- Cables
SELECT estado, COUNT(*) as cantidad
FROM cable_corporativo
GROUP BY estado
ORDER BY cantidad DESC;

-- Reportes
SELECT estado, COUNT(*) as cantidad
FROM reportes_mal_estado
GROUP BY estado
ORDER BY cantidad DESC;
```

**Resumen consolidado**:
```sql
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
```

#### Registros por Usuario

```sql
-- Registros creados por usuario específico
SELECT id, created_at, created_by, updated_by, estado,
       propiedades->>'nombre_esp' as nombre
FROM camaras
WHERE created_by = 'nombre_usuario'
ORDER BY created_at DESC;

-- Top 10 usuarios más activos
SELECT created_by, COUNT(*) as registros_creados
FROM (
    SELECT created_by FROM camaras
    UNION ALL
    SELECT created_by FROM empalmes
    UNION ALL
    SELECT created_by FROM cable_corporativo
    UNION ALL
    SELECT created_by FROM reportes_mal_estado
) as todos_registros
WHERE created_by IS NOT NULL
GROUP BY created_by
ORDER BY registros_creados DESC
LIMIT 10;
```

#### Últimos Registros Creados

```sql
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
```

---

### Consultas Espaciales

#### Búsqueda por Radio

Buscar elementos cerca de una ubicación específica:

```sql
-- Buscar cámaras en radio de 1000 metros
SELECT id,
       propiedades->>'nombre_esp' as nombre,
       propiedades->>'codigo_etb' as codigo,
       ST_Distance(
           geom::geography,
           ST_SetSRID(ST_MakePoint(-74.0817, 4.6097), 4326)::geography
       ) as distancia_metros,
       estado
FROM camaras
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(-74.0817, 4.6097), 4326)::geography,
    1000
)
ORDER BY distancia_metros
LIMIT 10;
```

**Parámetros**:
- `-74.0817, 4.6097` - Coordenadas del punto central (lon, lat)
- `1000` - Radio de búsqueda en metros

#### Cables con Longitud Calculada

```sql
SELECT id,
       propiedades->>'nombre_esp' as nombre,
       propiedades->>'colocacion' as colocacion,
       ST_Length(geom::geography) as longitud_metros,
       ROUND(ST_Length(geom::geography)::numeric, 2) as longitud_metros_redondeado,
       estado,
       created_at
FROM cable_corporativo
WHERE ST_Length(geom::geography) > 0
ORDER BY longitud_metros DESC
LIMIT 10;
```

#### Elementos sin Coordenadas Válidas

Detectar registros con geometrías nulas o inválidas:

```sql
-- Cámaras sin geometría válida
SELECT id, estado, created_at, created_by
FROM camaras
WHERE geom IS NULL
   OR NOT ST_IsValid(geom)
   OR ST_IsEmpty(geom);

-- Cables con menos de 2 puntos (inválidos)
SELECT id, estado, created_at, created_by,
       ST_NPoints(geom) as num_puntos
FROM cable_corporativo
WHERE ST_NPoints(geom) < 2;
```

---

### Validación de Datos

#### Duplicados por ID Texto

```sql
-- Empalmes con id_texto duplicado
SELECT propiedades->>'id_texto' as id_texto, COUNT(*) as cantidad
FROM empalmes
WHERE propiedades->>'id_texto' IS NOT NULL
GROUP BY propiedades->>'id_texto'
HAVING COUNT(*) > 1;
```

#### Registros con Campos Obligatorios Vacíos

```sql
-- Cámaras sin código ETB
SELECT id, estado, created_at, created_by
FROM camaras
WHERE propiedades->>'codigo_etb' IS NULL
   OR propiedades->>'codigo_etb' = ''
ORDER BY created_at DESC;

-- Reportes sin nivel de daño especificado
SELECT id, estado, created_at, created_by
FROM reportes_mal_estado
WHERE propiedades->>'nivel_dano' IS NULL
   OR propiedades->>'nivel_dano' = ''
ORDER BY created_at DESC;
```

#### Registros Fuera de Rango Geográfico

Colombia está aproximadamente entre:
- Latitud: -4° a 13°
- Longitud: -79° a -67°

```sql
-- Elementos fuera de Colombia
SELECT 'camara' as tipo, id,
       ST_X(geom::geometry) as lon,
       ST_Y(geom::geometry) as lat
FROM camaras
WHERE ST_Y(geom::geometry) NOT BETWEEN -4 AND 13
   OR ST_X(geom::geometry) NOT BETWEEN -79 AND -67
UNION ALL
SELECT 'empalme', id,
       ST_X(geom::geometry),
       ST_Y(geom::geometry)
FROM empalmes
WHERE ST_Y(geom::geometry) NOT BETWEEN -4 AND 13
   OR ST_X(geom::geometry) NOT BETWEEN -79 AND -67;
```

---

### Consultas de Mantenimiento

#### Cleanup de Registros de Prueba

```sql
-- Ver registros de prueba (antes de eliminar)
SELECT id, estado, created_at, created_by,
       propiedades->>'nombre_esp' as nombre,
       propiedades->>'observaciones' as observaciones
FROM camaras
WHERE propiedades->>'observaciones' ILIKE '%prueba%'
   OR propiedades->>'nombre_esp' ILIKE '%test%'
   OR propiedades->>'nombre_esp' ILIKE '%prueba%';

-- Eliminar solo si estás seguro
-- DELETE FROM camaras
-- WHERE id IN (SELECT id FROM camaras
--              WHERE propiedades->>'observaciones' ILIKE '%prueba%');
```

#### Reseteo de Secuencias

Ver [Manejo de Secuencias](manejo-secuencias.md) para guía completa.

```sql
-- Verificar estado de secuencias
SELECT 'camaras' as tabla,
       (SELECT MAX(id) FROM camaras) as max_id,
       (SELECT last_value FROM camaras_id_seq) as seq_value;

-- Resetear secuencia (después de carga masiva)
SELECT setval('camaras_id_seq', (SELECT MAX(id) FROM camaras));
```

---

### Testing de Performance

#### Tiempo de Ejecución de Consultas

```sql
-- Activar timing en psql
\timing on

-- O usar EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM camaras
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(-74.0817, 4.6097), 4326)::geography,
    1000
);
```

#### Verificar Uso de Índices

```sql
EXPLAIN (FORMAT JSON, ANALYZE)
SELECT * FROM camaras
WHERE estado = 'pendiente'
  AND ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_MakePoint(-74.0817, 4.6097), 4326)::geography,
    5000
);
```

Buscar en el resultado:
- `"Index Scan"` o `"Bitmap Index Scan"` ✅ Usando índice
- `"Seq Scan"` ❌ Sin índice (lento para tablas grandes)

---

### Archivo de Queries de Referencia

Todas las consultas de esta guía están disponibles en:

📄 **`sql/queries_test.sql`**

Este archivo contiene:
- Consultas de verificación para todas las entidades
- Queries de análisis y estadísticas
- Consultas espaciales de ejemplo
- Validaciones de datos
- Herramientas de mantenimiento

**Uso recomendado**:
1. Abrir `sql/queries_test.sql` en pgAdmin 4
2. Seleccionar la consulta deseada
3. Ejecutar con F5 o botón ▶
4. Modificar parámetros según necesidad (fechas, usuarios, coordenadas)

---

### Mejores Prácticas

#### ✅ DO

- Usar `LIMIT` en consultas de exploración
- Verificar datos antes de operaciones DELETE masivas
- Usar transacciones para cambios importantes: `BEGIN; ... COMMIT;`
- Exportar resultados importantes a CSV antes de cambios
- Usar `EXPLAIN ANALYZE` para optimizar queries lentas
- Aprovechar índices espaciales con geography cast

#### ❌ DON'T

- No ejecutar DELETE sin WHERE clause
- No modificar datos en producción sin backup
- No usar `SELECT *` en queries de producción
- No olvidar el cast a `::geography` en consultas espaciales
- No ejecutar queries sin LIMIT en tablas grandes
- No ignorar warnings de índices faltantes

---

### Troubleshooting

#### Timeout en Consultas

Si una consulta excede el timeout de 15 segundos:

1. Verificar uso de índices con `EXPLAIN ANALYZE`
2. Reducir el área de búsqueda espacial
3. Agregar filtros adicionales (estado, fechas)
4. Paginar resultados con LIMIT y OFFSET
5. Considerar crear índices adicionales

#### Geometrías Inválidas

```sql
-- Reparar geometrías inválidas
UPDATE camaras
SET geom = ST_MakeValid(geom)
WHERE NOT ST_IsValid(geom);
```

#### Consultas Espaciales Lentas

```sql
-- Verificar que existe índice GIST
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'camaras'
  AND indexdef LIKE '%GIST%';

-- Recrear índice si es necesario
DROP INDEX IF EXISTS idx_camaras_geom_geog;
CREATE INDEX idx_camaras_geom_geog
ON camaras USING GIST ((geom::geography));
```

---

## URLs de la API

| Ambiente | URL Base |
| -------- | -------- |
| **Railway (QA/Prod)** | `https://geoappfastapi-develop-production.up.railway.app/api` |
| **Local** | `http://localhost:8000/api` |

### Endpoints Disponibles

| Método | Endpoint | Descripción |
| ------ | -------- | ----------- |
| POST | `/api/camaras` | Crear cámara |
| POST | `/api/empalmes` | Crear empalme |
| POST | `/api/cable_corporativo` | Crear cable corporativo |
| POST | `/api/reporte_mal_estado` | Crear reporte de mal estado |
| GET | `/api/camaras?latitud=X&longitud=Y&radio=R` | Consultar cámaras por ubicación |
| GET | `/api/empalmes?latitud=X&longitud=Y&radio=R` | Consultar empalmes por ubicación |

Ver [API Referencia](api-referencia.md) para documentación completa de todos los endpoints.

---

## Checklist de Pruebas QA

### Antes de Iniciar Pruebas

- [ ] Credenciales de API configuradas en Postman
- [ ] Coordenadas de prueba identificadas
- [ ] Ambiente de pruebas identificado (Railway QA o Local)
- [ ] pgAdmin 4 instalado y configurado (opcional, para verificación SQL)

### Pruebas Funcionales por Formulario

**Cámara**:
- [ ] Crear cámara con datos mínimos (solo coordenadas)
- [ ] Crear cámara con todos los campos completos
- [ ] Verificar que apertura acepta valores válidos
- [ ] Verificar que propietario acepta valores válidos
- [ ] Verificar que estado_tapa acepta valores válidos
- [ ] Verificar que registro queda en estado "pendiente"
- [ ] Verificar datos en BD con query SQL

**Empalme**:
- [ ] Crear empalme con datos mínimos (solo coordenadas)
- [ ] Crear empalme con todos los campos completos
- [ ] Verificar que tipo_empalme acepta T-T, T-A, A-A
- [ ] Verificar que `id_texto` duplicado genera error 409
- [ ] Verificar datos en BD con query SQL

**Cable Corporativo**:
- [ ] Crear cable con 2 puntos (mínimo)
- [ ] Crear cable con más de 2 puntos
- [ ] Verificar error 422 con menos de 2 puntos
- [ ] Verificar cálculo automático de longitud en BD
- [ ] Verificar datos en BD con query SQL

**Reporte Mal Estado**:
- [ ] Crear reporte con nivel de daño "Alto"
- [ ] Crear reporte con nivel de daño "Medio"
- [ ] Crear reporte con nivel de daño "Bajo"
- [ ] Verificar que coordenadas son obligatorias
- [ ] Verificar datos en BD con query SQL

### Pruebas de Integración

- [ ] Crear registros desde frontend y verificar en BD
- [ ] Crear registros desde Postman y verificar en frontend
- [ ] Verificar que campos auto-llenados (remedy_id, tecnico) se guardan correctamente
- [ ] Verificar que timestamps (created_at, updated_at) se generan automáticamente

---

## Soporte y Escalación

### Documentación

- 📚 [Documentación completa en `/docs`](.)
- 🌐 [Swagger UI (solo local)](http://localhost:8000/docs)
- 📖 [ReDoc (solo local)](http://localhost:8000/redoc)

### Reportar Problemas

Si encuentras errores o comportamientos inesperados:

1. Verificar que los datos cumplen con las validaciones
2. Revisar mensajes de error HTTP
3. Consultar la sección [Troubleshooting](#troubleshooting) de esta guía
4. Revisar logs del servidor (en Railway o local)
5. Contactar al equipo de desarrollo con:
   - Endpoint utilizado
   - Body de la petición
   - Código HTTP y mensaje de error
   - Ambiente (Railway/Local)
