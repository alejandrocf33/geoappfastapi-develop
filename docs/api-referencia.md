# Referencia de APIs del Backend — GeoAPIs

> **Sistema:** GeoAPIs v1.0.0 — Gestión de Infraestructura Geoespacial
> **Base URL:** `/api`
> **Autenticación:** HTTP Basic Auth requerida en todos los endpoints
> **Formato de respuesta:** GeoJSON (FeatureCollection) para consultas / JSON para escritura
> **Sistema de coordenadas:** WGS84 (EPSG:4326), grados decimales

---

## Arquitectura General

```
Cliente (App / Mapa)
        │
        ▼
  Middleware HTTP
  ├── Validación de origen (Referer Oracle / IP Oficina / ALLOWED_LOCAL_ORIGIN)
  ├── Bloqueo 403 si origen no autorizado (solo en producción)
  └── En desarrollo (APP_DEBUG=true): solo registra, nunca bloquea
        │
        ▼
  Autenticación HTTP Basic (authenticate)
        │
        ▼
  Router FastAPI
  ├── cache_routes  →  Operaciones de Lectura  (GET /api/*)
  ├── logic_routes  →  Operaciones Lógicas     (GET /api/cables_cercanos, /nodos_alcanzables…)
  └── write_routes  →  Operaciones de Escritura (POST /api/*)
        │
        ▼
  db_access.py  →  PostgreSQL / PostGIS (psycopg2)
```

### Caché de datos
Los endpoints de lectura masiva (`/all_*`) utilizan un caché en memoria con **TTL de 6 horas** (`cachetools.TTLCache`). Las consultas espaciales por radio no usan caché y siempre van a la base de datos.

### Formatos de geometría aceptados (entrada)
| Método | Campo(s) | Descripción |
|--------|----------|-------------|
| Coordenadas directas | `latitud`, `longitud` | Grados decimales WGS84 |
| WKT | `geometry` | Well-Known Text. Sobreescribe latitud/longitud si se proporciona |

---

## Códigos de Error Comunes

| HTTP | `code` | Situación |
|------|--------|-----------|
| 401 | `authentication_error` | Credenciales inválidas. Cuerpo: `{"detail": "Credenciales incorrectas"}` |
| 403 | — | Origen bloqueado por middleware (producción) |
| 404 | `not_found` | Sin resultados para los parámetros dados |
| 422 | `validation_error` | Datos de entrada inválidos (coordenadas fuera de rango, puntos insuficientes, etc.) |
| 500 | `database_error` / `internal_error` | Error interno o fallo de base de datos |

---

---

# OPERACIONES DE LECTURA

## GET `/api/all_centrales`

**Descripción:** Devuelve **todas** las centrales registradas en la base de datos. Es el endpoint de inicialización del mapa; el frontend lo consume al cargar para llenar el dropdown de selección de centrales.

**Parámetros:** Ninguno

**Autenticación:** HTTP Basic requerida

**Interoperabilidad:**
- Consumido por el frontend al iniciar la aplicación para poblar el selector de centrales.
- Usa caché de 6 horas (`all_centrales_cache`). No hace consulta a la BD si el caché es válido.

**Respuesta exitosa (`200`):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-74.0616, 4.7437] },
      "properties": {
        "id": 1,
        "id_texto": "CTL-001",
        "nombre": "Central Norte",
        "codigo": "CN-001",
        "direccion": "Calle 165 #25-30",
        "tipo": "Conmutación"
      }
    }
  ]
}
```

**Filtro de estado:** Excluye registros en estado `pendiente` o `rechazado`.

---

## GET `/api/cables_cercanos`

**Descripción:** Busca cables dentro de un radio desde un punto geográfico. Usado para identificar el cable más cercano al punto de actividad/falla reportada. Soporta filtros por nombre y tipo de cable.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | Sí | — | Latitud del punto central (WGS84) |
| `lon` | float | Sí | — | Longitud del punto central (WGS84) |
| `distancia` | float | Sí | — | Radio de búsqueda en metros |
| `limite` | int | No | `100` | Máximo de resultados a retornar |
| `incluir_troncales` | bool | No | `false` | Si `true`, incluye cables de tipo Troncal |
| `nombre_cable` | string | No | `null` | Filtra por nombre del cable |
| `busqueda_exacta` | bool | No | `true` | `true` = coincidencia exacta; `false` = búsqueda parcial (`LIKE %nombre%`) |

**Autenticación:** HTTP Basic requerida

**Interoperabilidad:**
- Consumido por el flujo de registro de actividad de campo: el técnico indica su ubicación y la app busca el cable más cercano para asociarlo al ticket.
- Los resultados incluyen la **distancia calculada en metros** desde el punto de consulta a cada cable.
- Implementado en `logic_routes.py` → `get_cables_cercanos_from_db()` en `db_access.py`.

**Respuesta exitosa (`200`):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[-74.0617, 4.6737], [-74.0619, 4.6739]]
      },
      "properties": {
        "id_text": "CABLE-001",
        "name": "Cable Troncal Norte",
        "colocacion": "Acceso",
        "distancia": 23.4
      }
    }
  ]
}
```

> **Nota:** Las propiedades de cables usan `id_text` (no `id_texto`) en el JSONB de la BD.

---

## GET `/api/nodos_alcanzables_en_ruta_red`

**Descripción:** Calcula todos los **nodos alcanzables** en la red de cables desde un punto inicial hasta una distancia dada, navegando por la topología de la red (no distancia euclidiana). Indica cuál(es) nodo(s) es(son) el más cercano a la distancia solicitada. Usado para análisis de fallas y cálculo del alcance de afectación.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | Sí | — | Latitud del punto de inicio (WGS84) |
| `lon` | float | Sí | — | Longitud del punto de inicio (WGS84) |
| `distancia` | float | Sí | — | Distancia a recorrer en metros por la red |
| `margen_factor` | float | No | `0.9` | Factor decimal de margen para determinar el nodo más cercano a la distancia |

**Autenticación:** HTTP Basic requerida

**Interoperabilidad:**
- Depende de la función PostgreSQL/PostGIS: `fn_nodos_alcanzables_en_ruta_red(lon, lat, distancia, margen_factor)`.
- Esta función SQL **no se despliega automáticamente** por `setup.py`; debe desplegarse manualmente desde `fn_nodos_alcanzables_en_ruta_red.sql`.
- Usado en el módulo de análisis de fallas del frontend para visualizar el área de impacto en el mapa.

**Respuesta exitosa (`200`):**
```json
{
  "status": "success",
  "distancia_solicitada": 500,
  "margen_factor": 0.9,
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-74.062, 4.674] },
      "properties": {
        "distancia_acumulada": 487.3,
        "es_mas_cercano": true,
        "nombre_cable": "Cable Acceso Sur"
      }
    }
  ]
}
```

**Error `404`:** No se encontraron nodos alcanzables para la distancia dada.
**Error `500`:** Fallo en la ejecución de la función SQL.

---

## GET `/api/camaras`

**Descripción:** Consulta cámaras de inspección filtradas por ubicación y radio anular (donut). Si se omiten parámetros, retorna las primeras 100 cámaras. Carga los marcadores de cámaras en el mapa interactivo.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | No* | — | Latitud del centro de búsqueda (WGS84) |
| `lon` | float | No* | — | Longitud del centro de búsqueda (WGS84) |
| `radio_interno` | float | No* | — | Radio mínimo en metros (excluye cámaras más cercanas) |
| `radio_externo` | float | No* | — | Radio máximo en metros |

> *Si se proveen todos los parámetros se ejecuta búsqueda espacial. Si falta alguno, se retornan las primeras 100 cámaras.

**Autenticación:** HTTP Basic requerida

**Interoperabilidad:**
- Consumido por la capa de visualización del mapa para renderizar íconos de cámaras.
- La búsqueda anular (`radio_interno` a `radio_externo`) permite excluir cámaras muy cercanas al punto de consulta.
- Retorna `400` si `radio_interno > radio_externo`.

**Respuesta exitosa (`200`):** GeoJSON `FeatureCollection` con geometrías `Point`.

Propiedades incluidas en cada Feature:
```json
{
  "id": 123,
  "id_texto": "CAM-001",
  "type": "Subterránea",
  "ubicacion": "Calle 100 #15-20",
  "nombre_esp": "Cámara Principal",
  "apertura": "...",
  "propietari": "...",
  "constructi": "...",
  "estado_cam": "Operativa",
  "codigo_etb": "...",
  "distancia": 45.2
}
```

> **Nota:** La propiedad de tipo de cámara se llama `"type"` (no `"tipo"`) en el JSONB.

---

## GET `/api/cables`

**Descripción:** Consulta cables corporativos (polylines) filtrados por radio desde un punto. Renderiza los cables como líneas en el mapa. El `radio_interno` está **fijo en 0** (no configurable desde este endpoint).

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | No* | — | Latitud del centro (WGS84) |
| `lon` | float | No* | — | Longitud del centro (WGS84) |
| `radio_externo` | float | No* | — | Radio máximo en metros |

> *Si se proveen todos, se realiza búsqueda espacial. Si no, retorna los primeros 100 cables.

**Autenticación:** HTTP Basic requerida

**Interoperabilidad:**
- Consumido por la capa de cables del mapa para dibujar polylines de fibra óptica.
- Internamente llama a `get_cables_corporativos_from_db(lat, lon, radio_interno=0, radio_externo)`.

**Respuesta exitosa (`200`):** GeoJSON `FeatureCollection` con geometrías `LineString`.

Propiedades incluidas en cada Feature:
```json
{
  "id": 5,
  "id_text": "CABLE-001",
  "name": "Cable Troncal Norte",
  "nombre_ant": "...",
  "nombre_esp": "...",
  "colocacion": "Troncal",
  "constructi": "...",
  "perdida_db": 0.5,
  "segmento": "...",
  "distancia": 120.5
}
```

> **Nota:** Los cables usan `id_text` (sin "o") en sus propiedades JSONB.

---

## GET `/api/centrales`

**Descripción:** Consulta centrales telefónicas/técnicas filtradas por radio. Carga los marcadores de centrales en el mapa. El `radio_interno` está fijo en 0.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | No* | — | Latitud del centro (WGS84) |
| `lon` | float | No* | — | Longitud del centro (WGS84) |
| `radio_externo` | float | No* | — | Radio máximo en metros |

**Autenticación:** HTTP Basic requerida

**Respuesta exitosa (`200`):** GeoJSON `FeatureCollection` con geometrías `Point`.

Propiedades en cada Feature:
```json
{
  "id": 10,
  "id_texto": "CTL-001",
  "nombre": "Central Norte",
  "codigo": "CN-001",
  "direccion": "...",
  "tipo": "Conmutación",
  "distancia": 200.0
}
```

---

## GET `/api/empalmes`

**Descripción:** Consulta empalmes de fibra óptica filtrados por radio anular. Carga los marcadores de empalmes en el mapa.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | No* | — | Latitud del centro (WGS84) |
| `lon` | float | No* | — | Longitud del centro (WGS84) |
| `radio_interno` | float | No* | — | Radio mínimo en metros |
| `radio_externo` | float | No* | — | Radio máximo en metros |

**Autenticación:** HTTP Basic requerida

**Respuesta exitosa (`200`):** GeoJSON `FeatureCollection` con geometrías `Point`.

Propiedades incluidas:
```json
{
  "id": 20,
  "id_texto": "EMP-001",
  "name": "Empalme Principal",
  "type": "Empalme de Fibra Óptica",
  "splice_type": "...",
  "segmento": "...",
  "construction_status": "Operativo",
  "count_mayorista": 48,
  "distancia": 78.3
}
```

---

## GET `/api/reservas`

**Descripción:** Consulta reservas de fibra óptica filtradas por radio anular. Carga los marcadores de reservas en el mapa.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | No* | — | Latitud del centro (WGS84) |
| `lon` | float | No* | — | Longitud del centro (WGS84) |
| `radio_interno` | float | No* | — | Radio mínimo en metros |
| `radio_externo` | float | No* | — | Radio máximo en metros |

**Autenticación:** HTTP Basic requerida

**Respuesta exitosa (`200`):** GeoJSON `FeatureCollection` con geometrías `Point`.

Propiedades incluidas:
```json
{
  "id": 30,
  "id_texto": "RES-001",
  "nombre": "Reserva Principal",
  "tipo": "Reserva de Fibra Óptica",
  "capacidad": "48 hilos",
  "ubicacion": "Calle 26 con Avenida Caracas",
  "distancia": 55.0
}
```

---

---

# OPERACIONES DE ESCRITURA (POST)

Todos los endpoints de escritura:
- Requieren autenticación HTTP Basic.
- Aceptan un header opcional `user-header` para trazabilidad (si se omite, se usa el usuario autenticado).
- El estado inicial de todo registro es `"pendiente"`.
- Los campos `created_by` y `updated_by` se asignan automáticamente con el nombre del usuario.
- El campo `objectid` se genera automáticamente igual al `id` generado.

---

## POST `/api/camaras`

**Descripción:** Registra una nueva cámara de inspección en la base de datos geoespacial.

**Headers:**

| Header | Requerido | Descripción |
|--------|-----------|-------------|
| `Authorization` | Sí | HTTP Basic Auth |
| `user-header` | No | Usuario para trazabilidad (sobreescribe el autenticado) |

**Cuerpo (JSON):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `latitud` | float | Sí* | Latitud en grados decimales (−90 a 90) |
| `longitud` | float | Sí* | Longitud en grados decimales (−180 a 180) |
| `geometry` | string | No | WKT tipo `POINT` o `MULTIPOINT`. Sobreescribe lat/lon |
| `type` | string | No | Tipo de cámara (`"Subterránea"`, `"Aérea"`, `"Pedestal"`) |
| `id_texto` | string | No | Identificador textual (ej. `"CAM-001"`) |
| `ubicacion` | string | No | Dirección o descripción de ubicación |
| `nombre_esp` | string | No | Nombre especial |
| `apertura` | string | No | Tipo de apertura |
| `propietari` | string | No | Propietario |
| `constructi` | string | No | Constructor |
| `estado_cam` | string | No | Estado físico de la cámara |
| `codigo_etb` | string | No | Código interno ETB |

*`latitud` y `longitud` son requeridos si no se provee `geometry`.

**Ejemplo de solicitud:**
```json
{
  "type": "Subterránea",
  "id_texto": "CAM-001",
  "nombre_esp": "Cámara Principal",
  "ubicacion": "Calle 100 #15-20",
  "longitud": -74.0617,
  "latitud": 4.6737
}
```

**Respuesta exitosa (`200`):**
```json
{
  "message": "Cámara insertada correctamente",
  "id": 123,
  "objectid": 123
}
```

**Interoperabilidad:**
- Usado por el módulo de registro de campo del frontend.
- El registro queda en estado `"pendiente"` hasta aprobación.

---

## POST `/api/empalmes`

**Descripción:** Registra un nuevo empalme de fibra óptica.

**Headers:** Igual que `/api/camaras`.

**Cuerpo (JSON):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `latitud` | float | Sí* | Latitud WGS84 |
| `longitud` | float | Sí* | Longitud WGS84 |
| `geometry` | string | No | WKT `POINT` o `MULTIPOINT` |
| `id_texto` | string | No | Identificador textual |
| `name` | string | No | Nombre del empalme |
| `type` | string | No | Tipo de empalme |
| `splice_type` | string | No | Tipo específico (ej. `"Empalme de Fibra Óptica"`) |
| `segmento` | string | No | Segmento al que pertenece |
| `construction_status` | string | No | Estado constructivo (`"Operativo"`, `"En Construcción"`) |
| `count_mayorista` | float | No | Cantidad de hilos mayoristas |
| `mayorista_gather` | string | No | Mayorista asociado |
| `id_specification` | string | No | ID de especificación técnica |
| `nombre_especificacion` | string | No | Nombre de especificación técnica |
| `propietario` | string | No | Propietario del empalme |
| `sangria` | float | No | Sangría del empalme |
| `symbol_annotation` | string | No | Anotación simbólica |
| `location_x`, `location_y` | float | No | Coordenadas de ubicación auxiliar |
| `symbol_location_x/y` | float | No | Posición del símbolo en plano |
| `ubicacion_empalmes_camara_x/y` | float | No | Posición en cámara |
| `ubicacion_empalmes_postes_x/y` | float | No | Posición en poste |
| `ubicacion_empalmes_edificio_x/y` | float | No | Posición en edificio |
| `ubicacion_empalmes_punto_de_acceso_x/y` | float | No | Posición en punto de acceso |

**Respuesta exitosa (`200`):**
```json
{
  "message": "Empalme insertado correctamente",
  "id": 20,
  "objectid": 20
}
```

---

## POST `/api/cable_corporativo`

**Descripción:** Registra un nuevo cable corporativo (trayecto lineal de fibra óptica). Requiere al menos **2 puntos** para conformar una `LineString`.

**Headers:** Igual que `/api/camaras`.

**Cuerpo (JSON):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `puntos` | array | Sí* | Lista de al menos 2 objetos `{"latitud": float, "longitud": float}` |
| `geometry` | string | No | WKT `LINESTRING`. Sobreescribe `puntos` si se provee |
| `id_texto` | string | No | Identificador textual del cable |
| `name` | string | No | Nombre del cable |
| `nombre_ant` | string | No | Nombre anterior |
| `nombre_esp` | string | No | Nombre especial |
| `colocacion` | string | No | Tipo de colocación (`"Troncal"`, `"Acceso"`) |
| `constructi` | string | No | Constructor |
| `perdida_db` | float | No | Pérdida en decibelios (≥ 0) |
| `contratist` | string | No | Contratista |
| `segmento` | string | No | Segmento de red |
| `pr` | string | No | Propietario |
| `calculat1` | float | No | Cálculo de capacidad 1 |
| `calculat2` | float | No | Cálculo de capacidad 2 |
| `calculated` | float | No | Cálculo final de capacidad |
| `id_especificacion` | float | No | ID de especificación técnica |
| `measured_l` | float | No | Longitud medida del cable |

*`puntos` es requerido si no se provee `geometry`. Mínimo 2 puntos.

**Ejemplo de solicitud:**
```json
{
  "id_texto": "CABLE-001",
  "name": "Cable Troncal Norte",
  "colocacion": "Troncal",
  "puntos": [
    {"longitud": -74.0617, "latitud": 4.6737},
    {"longitud": -74.0618, "latitud": 4.6738},
    {"longitud": -74.0619, "latitud": 4.6739}
  ]
}
```

**Respuesta exitosa (`200`):**
```json
{
  "message": "Cable insertado correctamente",
  "id": 5,
  "objectid": 5
}
```

**Error `422`:** Si se proveen menos de 2 puntos y no hay `geometry`.

---

---

# ENDPOINTS AUXILIARES (Operaciones Lógicas adicionales)

## GET `/api/camaras_en_falla`

**Descripción:** Analiza un área y detecta cámaras potencialmente en falla basándose en patrones de distribución espacial. Retorna dos colecciones: cámaras dentro del radio principal y cámaras en el radio extendido.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lat` | float | Sí | — | Latitud del punto central |
| `lon` | float | Sí | — | Longitud del punto central |
| `distancia` | float | Sí | — | Radio de búsqueda principal en metros |
| `desviacion` | float | No | `10` | Metros adicionales para radio extendido |

**Respuesta exitosa (`200`):**
```json
{
  "camaras_en_radio": {
    "type": "FeatureCollection",
    "features": [...]
  },
  "camaras_cercanas": {
    "type": "FeatureCollection",
    "features": [...]
  }
}
```

## GET `/api/linea_en_ruta_red`

**Descripción:** Calcula una ruta sobre la red de cables desde un punto de entrada hasta una distancia dada. Útil para planificación de tendido y análisis de cobertura.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Defecto | Descripción |
|-----------|------|-----------|---------|-------------|
| `lon` | float | Sí | — | Longitud del punto de inicio |
| `lat` | float | Sí | — | Latitud del punto de inicio |
| `distancia` | float | Sí | — | Distancia a recorrer en metros |
| `incluir_linea` | bool | No | `true` | Si `true`, incluye geometría LineString de la ruta |

**Depende de:** Función SQL `fn_linea_en_ruta_red(lon, lat, distancia, incluir_linea)`

**Respuesta exitosa (`200`):**
```json
{
  "status": "success",
  "linea": {
    "type": "Feature",
    "geometry": { "type": "LineString", "coordinates": [...] },
    "properties": { "distancia_metros": 500 }
  },
  "puntos": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-74.062, 4.674] },
      "properties": { "distancia_metros": 500 }
    }
  ]
}
```

---

---

# Tabla Resumen de Endpoints

| Método | Endpoint | Auth | Caché | Función BD | Descripción |
|--------|----------|------|-------|-----------|-------------|
| GET | `/api/all_centrales` | Basic | 6h | `get_all_centrales_from_db` | Todas las centrales (dropdown) |
| GET | `/api/cables_cercanos` | Basic | No | `get_cables_cercanos_from_db` | Cables por radio + filtros |
| GET | `/api/nodos_alcanzables_en_ruta_red` | Basic | No | `fn_nodos_alcanzables_en_ruta_red` (SQL) | Nodos en ruta de falla |
| GET | `/api/camaras` | Basic | No | `get_camaras_from_db` | Cámaras por radio anular |
| GET | `/api/cables` | Basic | No | `get_cables_corporativos_from_db` | Cables por radio |
| GET | `/api/centrales` | Basic | No | `get_centrales_from_db` | Centrales por radio |
| GET | `/api/empalmes` | Basic | No | `get_empalmes_from_db` | Empalmes por radio anular |
| GET | `/api/reservas` | Basic | No | `get_reservas_from_db` | Reservas por radio anular |
| GET | `/api/camaras_en_falla` | Basic | No | `get_camaras_en_falla_db` | Análisis de falla por cámaras |
| GET | `/api/linea_en_ruta_red` | Basic | No | `fn_linea_en_ruta_red` (SQL) | Ruta sobre red de cables |
| POST | `/api/camaras` | Basic | — | `insertar_camara_db` | Registrar nueva cámara |
| POST | `/api/empalmes` | Basic | — | `insertar_empalme_db` | Registrar nuevo empalme |
| POST | `/api/cable_corporativo` | Basic | — | `insertar_cable_corporativo_db` | Registrar nuevo cable |
| POST | `/api/centrales` | Basic | — | `insertar_central_db` | Registrar nueva central |
| POST | `/api/reservas` | Basic | — | `insertar_reserva_db` | Registrar nueva reserva |

---

*Documentación generada desde el código fuente. Versión del backend: GeoAPIs 1.0.0*
