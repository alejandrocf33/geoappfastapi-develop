# Guía de Pruebas QA — Registros de Entidades

Este documento describe cómo enviar correctamente solicitudes de registro para cada una de las 4 entidades geoespaciales. Incluye valores de ejemplo válidos y explica los errores más comunes.

---

## Requisitos comunes a todos los registros

### Autenticación
Todos los endpoints requieren **HTTP Basic Auth**.

```
Usuario: <valor de API_USERNAME en .env>
Contraseña: <valor de API_PASSWORD en .env>
```

En Postman: pestaña **Authorization** → tipo **Basic Auth**.

En curl:
```bash
curl -u usuario:contraseña -X POST ...
```

### URL base
- **Railway (producción/QA):** `https://geoappfastapi-develop-production.up.railway.app/api`
- **Local:** `http://localhost:8000/api`

### Cabecera opcional de trazabilidad
```
user-header: nombre-del-tecnico-qa
```

---

## 1. Cámara

**Endpoint:** `POST /api/camaras`

### Campos

| Campo | Tipo | Requerido | Descripción | Valores válidos de ejemplo |
|-------|------|-----------|-------------|---------------------------|
| `latitud` | float | **SÍ** | Latitud WGS84 | `-90` a `90`. Bogotá: `4.6097` |
| `longitud` | float | **SÍ** | Longitud WGS84 | `-180` a `180`. Bogotá: `-74.0817` |
| `type` | string | No | Tipo de cámara | `"Subterránea"`, `"Aérea"`, `"Pedestal"` |
| `id_texto` | string | No | Identificador textual **único** | `"CAM-001"` — si se envía, debe ser único en la BD. Dejar vacío si no se conoce |
| `ubicacion` | string | No | Dirección o descripción | `"Calle 100 # 15-20, Bogotá"` |
| `nombre_esp` | string | No | Nombre especial | `"Cámara Norte"` |
| `apertura` | string | No | Tipo de apertura | `"Manual"`, `"Hidráulica"` |
| `propietari` | string | No | Propietario | `"ETB"` |
| `constructi` | string | No | Constructor | `"Constructora ABC"` |
| `estado_cam` | string | No | Estado de la cámara | `"Operativa"`, `"En Mantenimiento"`, `"Fuera de Servicio"` |
| `estado_tapa` | string | No | Estado de la tapa | `"Buena"`, `"En daño"`, `"Sin seguridad"`, `"Sin tapa"` |
| `codigo_etb` | string | No | Código interno ETB | `"ETB-12345"` |
| `remedy_id` | string | No | ID de ticket Remedy | `"INC0001234"` |
| `tecnico` | string | No | Técnico responsable | `"Juan Pérez"` |
| `observaciones` | string | No | Texto libre | `"Cámara recién instalada"` |

> **IMPORTANTE sobre `id_texto`:** Este campo es un **identificador único** (no es Sí/No). Si se envía un valor que ya existe en la BD, la API retorna error **409 Conflict**. Usar siempre un valor nuevo (ej. `"CAM-QA-001"`) o dejarlo `null`.

### Ejemplo de body (mínimo válido)
```json
{
  "latitud": 4.6097,
  "longitud": -74.0817
}
```

### Ejemplo de body (completo para QA)
```json
{
  "type": "Subterránea",
  "id_texto": "CAM-QA-001",
  "ubicacion": "Calle 100 # 15-20, Bogotá",
  "nombre_esp": "Cámara QA Norte",
  "apertura": "Manual",
  "propietari": "ETB",
  "constructi": "Constructora QA",
  "estado_cam": "Operativa",
  "estado_tapa": "Buena",
  "codigo_etb": "ETB-QA-001",
  "remedy_id": "INC0000001",
  "tecnico": "Tecnico QA",
  "observaciones": "Registro de prueba QA",
  "latitud": 4.6097,
  "longitud": -74.0817
}
```

### Respuesta exitosa (201)
```json
{
  "message": "Cámara insertada correctamente",
  "id": 123,
  "objectid": 123
}
```

### Errores comunes

| Código | Causa | Solución |
|--------|-------|----------|
| 401 | Credenciales incorrectas | Verificar usuario/contraseña en Basic Auth |
| 409 | `id_texto` ya existe | Cambiar el valor de `id_texto` o dejarlo `null` |
| 422 | `latitud`/`longitud` fuera de rango | Usar coordenadas WGS84 válidas |
| 500 | Error interno BD | Revisar logs del servidor |

---

## 2. Cable Corporativo

**Endpoint:** `POST /api/cable_corporativo`

### Campos

| Campo | Tipo | Requerido | Descripción | Valores válidos de ejemplo |
|-------|------|-----------|-------------|---------------------------|
| `puntos` | array | **SÍ*** | Lista de al menos 2 puntos `{latitud, longitud}` | Ver ejemplo abajo |
| `id_texto` | string | No | Identificador textual | `"CABLE-QA-001"` |
| `name` | string | No | Nombre del cable | `"Cable Troncal Norte"` |
| `nombre_ant` | string | No | Nombre anterior | `"Cable Antiguo Norte"` |
| `nombre_esp` | string | No | Nombre especial | `"Fibra óptica 48H troncal"` |
| `colocacion` | string | No | Tipo de colocación | `"Troncal"`, `"Acceso"`, `"Distribución"` |
| `constructi` | string | No | Constructor | `"Constructora ABC"` |
| `perdida_db` | float | No | Pérdida en dB (≥ 0) | `2.5` |
| `contratist` | string | No | Contratista | `"Contratista XYZ"` |
| `segmento` | string | No | Segmento de red | `"Norte"`, `"Sur"` |
| `pr` | string | No | Propietario | `"ETB"` |
| `calculat1` | float | No | Cálculo capacidad 1 | `48.0` |
| `calculat2` | float | No | Cálculo capacidad 2 | `48.0` |
| `calculated` | float | No | Cálculo capacidad final | `48.0` |
| `id_especificacion` | float | No | ID de especificación | `1.0` |
| `measured_l` | float | No | Longitud medida (metros) | `250.5` |
| `remedy_id` | string | No | ID ticket Remedy | `"INC0001234"` |
| `tecnico` | string | No | Técnico responsable | `"Juan Pérez"` |
| `observaciones` | string | No | Texto libre | `"Cable nuevo QA"` |

> **\*`puntos` o `geometry`:** Se debe enviar `puntos` con al menos 2 coordenadas, O bien `geometry` en formato WKT LINESTRING. Si se envía `geometry`, el campo `puntos` puede omitirse.

### Estructura de cada punto en `puntos`
```json
{"latitud": 4.6097, "longitud": -74.0817}
```

### Ejemplo de body (mínimo válido)
```json
{
  "puntos": [
    {"latitud": 4.6097, "longitud": -74.0817},
    {"latitud": 4.6110, "longitud": -74.0830}
  ]
}
```

### Ejemplo de body (completo para QA)
```json
{
  "id_texto": "CABLE-QA-001",
  "name": "Cable QA Norte",
  "nombre_esp": "Fibra óptica 48H QA",
  "colocacion": "Troncal",
  "constructi": "Constructora QA",
  "perdida_db": 1.5,
  "segmento": "Norte",
  "pr": "ETB",
  "remedy_id": "INC0000002",
  "tecnico": "Tecnico QA",
  "observaciones": "Cable de prueba QA",
  "puntos": [
    {"latitud": 4.6097, "longitud": -74.0817},
    {"latitud": 4.6110, "longitud": -74.0830},
    {"latitud": 4.6125, "longitud": -74.0845}
  ]
}
```

### Alternativa con WKT
```json
{
  "name": "Cable QA WKT",
  "geometry": "LINESTRING(-74.0817 4.6097, -74.0830 4.6110, -74.0845 4.6125)"
}
```

> **Nota WKT:** El orden en WKT es `longitud latitud` (X Y), al contrario del JSON de `puntos`.

### Respuesta exitosa (201)
```json
{
  "message": "Cable corporativo insertado correctamente",
  "id": 456,
  "objectid": 456
}
```

### Errores comunes

| Código | Causa | Solución |
|--------|-------|----------|
| 401 | Credenciales incorrectas | Verificar Basic Auth |
| 422 | Menos de 2 puntos en `puntos` | Agregar al menos 2 puntos |
| 422 | `perdida_db` negativa | Usar valor ≥ 0 |
| 422 | `geometry` no es LINESTRING | Usar `LINESTRING(...)` |
| 500 | Error interno BD | Revisar logs |

---

## 3. Central

**Endpoint:** `POST /api/centrales`

### Campos

| Campo | Tipo | Requerido | Descripción | Valores válidos de ejemplo |
|-------|------|-----------|-------------|---------------------------|
| `latitud` | float | **SÍ** | Latitud WGS84 | `4.7437` |
| `longitud` | float | **SÍ** | Longitud WGS84 | `-74.0616` |
| `id_texto` | string | No | Identificador textual | `"CTL-QA-001"` |
| `nombre` | string | No | Nombre de la central | `"Central Norte"` |
| `codigo` | string | No | Código único interno | `"CN-001"` |
| `direccion` | string | No | Dirección física | `"Calle 165 # 25-30, Bogotá"` |
| `tipo` | string | No | Tipo de central | `"Conmutación"`, `"Transmisión"`, `"Datos"` |

### Ejemplo de body (mínimo válido)
```json
{
  "latitud": 4.7437,
  "longitud": -74.0616
}
```

### Ejemplo de body (completo para QA)
```json
{
  "id_texto": "CTL-QA-001",
  "nombre": "Central QA Norte",
  "codigo": "CQA-001",
  "direccion": "Calle 165 # 25-30, Bogotá",
  "tipo": "Conmutación",
  "latitud": 4.7437,
  "longitud": -74.0616
}
```

### Respuesta exitosa (201)
```json
{
  "message": "Central insertada correctamente",
  "id": 789
}
```

### Errores comunes

| Código | Causa | Solución |
|--------|-------|----------|
| 401 | Credenciales incorrectas | Verificar Basic Auth |
| 422 | `latitud`/`longitud` faltante o fuera de rango | Incluir coordenadas válidas |
| 500 | Error interno BD | Revisar logs |

---

## 4. Empalme

**Endpoint:** `POST /api/empalmes`

### Campos principales

| Campo | Tipo | Requerido | Descripción | Valores válidos de ejemplo |
|-------|------|-----------|-------------|---------------------------|
| `latitud` | float | **SÍ** | Latitud WGS84 | `4.6647` |
| `longitud` | float | **SÍ** | Longitud WGS84 | `-74.0917` |
| `id_texto` | string | No | Identificador textual **único** | `"EMP-QA-001"` |
| `tipo_empalme` | string | No | Tipo de empalme | `"T-T"`, `"T-A"`, `"A-A"` |
| `name` | string | No | Nombre | `"Empalme Principal"` |
| `type` | string | No | Tipo (clasificación) | `"Empalme de Fibra Óptica"` |
| `segmento` | string | No | Segmento de red | `"Norte"` |
| `propietario` | string | No | Propietario | `"ETB"` |
| `splice_type` | string | No | Tipo de empalme técnico | `"Fusión"`, `"Mecánico"` |
| `count_mayorista` | float | No | Hilos mayoristas | `12.0` |
| `mayorista_gather` | string | No | Nombre del mayorista | `"Telmex"` |
| `construction_status` | string | No | Estado de construcción | `"Operativo"`, `"En Construcción"` |
| `cable1` | string | No | Nombre cable asociado 1 | `"CABLE-001"` |
| `cable2` | string | No | Nombre cable asociado 2 | `"CABLE-002"` |
| `remedy_id` | string | No | ID ticket Remedy | `"INC0001234"` |
| `tecnico` | string | No | Técnico responsable | `"Juan Pérez"` |
| `observaciones` | string | No | Texto libre | `"Empalme nuevo QA"` |
| `sangria` | float | No | Sangría del empalme | `1.5` |
| `id_specification` | string | No | ID de especificación | `"ESP-001"` |
| `nombre_especificacion` | string | No | Nombre especificación | `"Especificación 48H"` |

> **IMPORTANTE sobre `id_texto`:** Al igual que en Cámara, es un **identificador único**. Si ya existe en la BD, la API retorna **409 Conflict**. Usar valor nuevo o dejarlo `null`.

### Ejemplo de body (mínimo válido)
```json
{
  "latitud": 4.6647,
  "longitud": -74.0917
}
```

### Ejemplo de body (completo para QA)
```json
{
  "id_texto": "EMP-QA-001",
  "tipo_empalme": "T-T",
  "name": "Empalme QA Principal",
  "type": "Empalme de Fibra Óptica",
  "segmento": "Norte",
  "propietario": "ETB",
  "splice_type": "Fusión",
  "count_mayorista": 12.0,
  "construction_status": "Operativo",
  "cable1": "CABLE-QA-001",
  "cable2": "CABLE-QA-002",
  "remedy_id": "INC0000003",
  "tecnico": "Tecnico QA",
  "observaciones": "Empalme de prueba QA",
  "latitud": 4.6647,
  "longitud": -74.0917
}
```

### Respuesta exitosa (201)
```json
{
  "message": "Empalme insertado correctamente",
  "id": 321,
  "objectid": 321
}
```

### Errores comunes

| Código | Causa | Solución |
|--------|-------|----------|
| 401 | Credenciales incorrectas | Verificar Basic Auth |
| 409 | `id_texto` ya existe | Cambiar el valor o dejarlo `null` |
| 422 | `latitud`/`longitud` faltante | Incluir coordenadas válidas |
| 500 | Error interno BD | Revisar logs |

---

## 5. Reserva

**Endpoint:** `POST /api/reservas`

### Campos

| Campo | Tipo | Requerido | Descripción | Valores válidos de ejemplo |
|-------|------|-----------|-------------|---------------------------|
| `latitud` | float | **SÍ** | Latitud WGS84 | `4.6147` |
| `longitud` | float | **SÍ** | Longitud WGS84 | `-74.0816` |
| `id_texto` | string | No | Identificador textual | `"RES-QA-001"` |
| `nombre` | string | No | Nombre de la reserva | `"Reserva QA Norte"` |
| `tipo` | string | No | Tipo de reserva | `"Reserva de Fibra Óptica"` |
| `capacidad` | string | No | Capacidad | `"48 hilos"`, `"96 hilos"` |
| `ubicacion` | string | No | Descripción de ubicación | `"Calle 26 con Av. Caracas"` |

### Ejemplo de body (mínimo válido)
```json
{
  "latitud": 4.6147,
  "longitud": -74.0816
}
```

### Ejemplo de body (completo para QA)
```json
{
  "id_texto": "RES-QA-001",
  "nombre": "Reserva QA Norte",
  "tipo": "Reserva de Fibra Óptica",
  "capacidad": "48 hilos",
  "ubicacion": "Calle 26 con Av. Caracas, Bogotá",
  "latitud": 4.6147,
  "longitud": -74.0816
}
```

### Respuesta exitosa (201)
```json
{
  "message": "Reserva insertada correctamente",
  "id": 654
}
```

### Errores comunes

| Código | Causa | Solución |
|--------|-------|----------|
| 401 | Credenciales incorrectas | Verificar Basic Auth |
| 422 | `latitud`/`longitud` faltante | Incluir coordenadas válidas |
| 500 | Error interno BD | Revisar logs |

---

## Coordenadas de referencia — Bogotá

Para pruebas en Bogotá, usar coordenadas dentro de estos rangos:

| Zona | Latitud | Longitud |
|------|---------|----------|
| Centro | `4.5981` | `-74.0761` |
| Norte | `4.7437` | `-74.0616` |
| Sur | `4.5000` | `-74.1200` |
| Occidente | `4.6500` | `-74.1500` |

---

## Tabla resumen de campos requeridos

| Entidad | Endpoint | Requerido obligatorio |
|---------|----------|----------------------|
| Cámara | `POST /api/camaras` | `latitud`, `longitud` |
| Cable Corporativo | `POST /api/cable_corporativo` | `puntos` (≥ 2) **o** `geometry` |
| Central | `POST /api/centrales` | `latitud`, `longitud` |
| Empalme | `POST /api/empalmes` | `latitud`, `longitud` |
| Reserva | `POST /api/reservas` | `latitud`, `longitud` |

---

## Verificación de registros

Después de un POST exitoso, verificar con GET:

```
GET /api/camaras          → lista cámaras (máx. 100)
GET /api/cables           → lista cables
GET /api/centrales        → lista centrales
GET /api/empalmes         → lista empalmes
GET /api/reservas         → lista reservas
```

Todos los GET también requieren Basic Auth y retornan GeoJSON FeatureCollection.
