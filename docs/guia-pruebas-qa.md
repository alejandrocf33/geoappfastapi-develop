# Guía de Pruebas QA — Registro de Elementos

Instructivo para el equipo QA sobre cómo completar correctamente cada formulario de registro y los valores válidos para cada campo. Aplica tanto para uso desde la interfaz web como desde Postman/curl.

---

## Menú de tipos de elemento

El selector "TIPO DE ELEMENTO" tiene las siguientes opciones:

| Opción en formulario | Endpoint API |
|----------------------|--------------|
| Cámara | `POST /api/camaras` |
| Empalme | `POST /api/empalmes` |
| Cable Corporativo | `POST /api/cable_corporativo` |
| Reporte Cierre Mal Estado | `POST /api/reporte_mal_estado` |

---

## Autenticación (requerida en todos los registros)

Todos los endpoints usan **HTTP Basic Auth**.

- En Postman: pestaña **Authorization** → tipo **Basic Auth** → ingresar usuario y contraseña de la API.
- En curl: `curl -u usuario:contraseña -X POST ...`

---

## 1. Cámara

**Endpoint:** `POST /api/camaras`

### Campos del formulario

| Etiqueta en formulario | Campo API | Tipo | Requerido | Valores válidos |
|------------------------|-----------|------|-----------|-----------------|
| Marquillado (SÍ/NO) | `marquillado` | string | No | `"SÍ"`, `"NO"` |
| Nombre (Esp) | `nombre_esp` | string | No | Texto libre. Ej: `"ETB-CENTRO-01"` |
| Apertura | `apertura` | string | No | Ver tabla abajo |
| Ubicación (Dirección) | `ubicacion` | string | No | Texto libre. Ej: `"Calle 100 # 15-20"` |
| Propietario | `propietari` | string | No | Ver tabla abajo |
| Estado Cámara | `estado_cam` | string | No | `"SIN NOVEDAD"`, `"CON GASES"` |
| Estado Tapa | `estado_tapa` | string | No | Ver tabla abajo |
| Observaciones | `observaciones` | string | No | Texto libre |
| ID Tarea REMEDY | `remedy_id` | string | No | Ej: `"INC000012345"` (se llena automáticamente) |
| Técnico | `tecnico` | string | No | Nombre del técnico (se llena automáticamente) |
| Código ETB | `codigo_etb` | string | No | Ej: `"ETB-12345"` |
| Longitud | `longitud` | float | **SÍ** | Se llena con botón "Ubicación" (GPS) |
| Latitud | `latitud` | float | **SÍ** | Se llena con botón "Ubicación" (GPS) |

> **Tipo** y **Constructi** están ocultos en el formulario y no son necesarios para el registro.

#### Valores válidos: Apertura

| Valor |
|-------|
| `ESTANDAR` |
| `MAGNETICA` |
| `ESTANDAR SOLDADA` |
| `LLAVE DE SEGURIDAD` |
| `CORCHO DIFERENCIAL` |
| `CORTINA - CANDADO` |
| `Llave de Seguridad - SOLDADA` |
| `CORCHO GRUA` |

#### Valores válidos: Propietario

| Valor |
|-------|
| `ETB` |
| `CODENSA` |
| `OTROS OPERADORES` |
| `SDM` |
| `SMV` |
| `EMSA` |

#### Valores válidos: Estado Tapa

| Valor |
|-------|
| `Buena` |
| `En daño` |
| `Sin seguridad` |
| `Sin tapa` |

### Ejemplo de body para Postman (QA)

```json
{
  "marquillado": "SÍ",
  "nombre_esp": "Camara QA Norte",
  "apertura": "ESTANDAR",
  "ubicacion": "Calle 100 # 15-20, Bogotá",
  "propietari": "ETB",
  "estado_cam": "SIN NOVEDAD",
  "estado_tapa": "Buena",
  "observaciones": "Registro de prueba QA",
  "remedy_id": "INC000012345",
  "tecnico": "Tecnico QA",
  "codigo_etb": "ETB-QA-001",
  "latitud": 4.6097,
  "longitud": -74.0817
}
```

### Respuesta exitosa

```json
{
  "message": "Cámara insertada correctamente",
  "id": 123,
  "objectid": 123
}
```

---

## 2. Empalme

**Endpoint:** `POST /api/empalmes`

### Campos del formulario

| Etiqueta en formulario | Campo API | Tipo | Requerido | Valores válidos |
|------------------------|-----------|------|-----------|-----------------|
| Etiqueta Cable (Marquilla) | `name` | string | No | Texto libre. Ej: `"EMP-001"` |
| Tipo | `type` | string | No | `"Mecánico"`, `"Fusión"` |
| Tipo Empalme | `tipo_empalme` | string | No | `"T-T"`, `"T-A"`, `"A-A"` |
| Cable 1 | `cable1` | string | No | Nombre del cable asociado. Ej: `"CABLE-001"` |
| Cable 2 | `cable2` | string | No | Nombre del cable asociado. Ej: `"CABLE-002"` |
| ID Tarea REMEDY | `remedy_id` | string | No | Ej: `"INC000012345"` |
| Técnico | `tecnico` | string | No | Nombre del técnico |
| Observaciones | `observaciones` | string | No | Texto libre |
| Longitud | `longitud` | float | **SÍ** | Se llena con botón "Ubicación" (GPS) |
| Latitud | `latitud` | float | **SÍ** | Se llena con botón "Ubicación" (GPS) |

> El campo **Ubicación** en el formulario es solo para geocodificación (autocompletar las coordenadas), no se envía a la API.

### Valores válidos: Tipo Empalme

| Valor | Descripción |
|-------|-------------|
| `T-T` | Tierra - Tierra |
| `T-A` | Tierra - Aéreo |
| `A-A` | Aéreo - Aéreo |

### Ejemplo de body para Postman (QA)

```json
{
  "name": "EMP-QA-001",
  "type": "Mecánico",
  "tipo_empalme": "T-T",
  "cable1": "CABLE-QA-001",
  "cable2": "CABLE-QA-002",
  "remedy_id": "INC000012345",
  "tecnico": "Tecnico QA",
  "observaciones": "Empalme de prueba QA",
  "latitud": 4.6647,
  "longitud": -74.0917
}
```

### Respuesta exitosa

```json
{
  "message": "Empalme insertado correctamente",
  "id": 321,
  "objectid": 321
}
```

---

## 3. Cable Corporativo

**Endpoint:** `POST /api/cable_corporativo`

### Campos del formulario

| Etiqueta en formulario | Campo API | Tipo | Requerido | Valores válidos |
|------------------------|-----------|------|-----------|-----------------|
| Colocación | `colocacion` | string | No | `"Troncal"`, `"Acceso"`, `"Troncal-Acceso"`, texto libre |
| Nombre ESP | `nombre_esp` | string | No | Texto libre. Ej: `"Ductado 24h senc"` |
| ID Tarea REMEDY | `remedy_id` | string | No | Ej: `"INC000012345"` |
| Técnico | `tecnico` | string | No | Nombre del técnico |
| Observaciones | `observaciones` | string | No | Texto libre |
| Longitud Inicial | primer punto en `puntos` | float | **SÍ** | Se llena con botón "Capturar Inicio" (GPS) |
| Latitud Inicial | primer punto en `puntos` | float | **SÍ** | Se llena con botón "Capturar Inicio" (GPS) |
| Longitud Final | segundo punto en `puntos` | float | **SÍ** | Se llena con botón "Capturar Fin" (GPS) |
| Latitud Final | segundo punto en `puntos` | float | **SÍ** | Se llena con botón "Capturar Fin" (GPS) |

> El formulario captura **2 puntos** (inicio y fin). La API los recibe como lista en el campo `puntos`.
> Los campos **Ubicación Inicial** y **Ubicación Final** son solo para geocodificación, no se envían a la API.

### Ejemplo de body para Postman (QA)

```json
{
  "colocacion": "Troncal",
  "nombre_esp": "Cable QA Ductado 24h",
  "remedy_id": "INC000012345",
  "tecnico": "Tecnico QA",
  "observaciones": "Cable de prueba QA",
  "puntos": [
    {"latitud": 4.6097, "longitud": -74.0817},
    {"latitud": 4.6125, "longitud": -74.0845}
  ]
}
```

### Respuesta exitosa

```json
{
  "message": "Cable corporativo insertado correctamente",
  "id": 456,
  "objectid": 456
}
```

### Error más común: menos de 2 puntos

```json
HTTP 422 Unprocessable Entity
"Se requieren al menos 2 puntos para formar un cable (LineString)"
```

Asegurarse de que tanto los campos de punto inicial como final estén diligenciados antes de enviar.

---

## 4. Reporte Cierre Mal Estado

**Endpoint:** `POST /api/reporte_mal_estado`

### Campos del formulario

| Etiqueta en formulario | Campo API | Tipo | Requerido | Valores válidos |
|------------------------|-----------|------|-----------|-----------------|
| Número de Cable | `numero_cable` | string | No | Texto libre. Ej: `"CABLE-001"` |
| Nivel de Daño | `nivel_dano` | string | No | `"Alto"`, `"Medio"`, `"Bajo"` |
| Dirección | `direccion` | string | No | Texto libre. Ej: `"Calle 80 # 30-40"` |
| Observaciones | `observaciones` | string | No | Texto libre |
| ID Tarea REMEDY | `remedy_id` | string | No | Ej: `"INC000012345"` |
| Técnico | `tecnico` | string | No | Nombre del técnico |
| Longitud | `longitud` | float | **SÍ** | Se llena con botón "Ubicación (Obligatorio)" |
| Latitud | `latitud` | float | **SÍ** | Se llena con botón "Ubicación (Obligatorio)" |

> La **Ubicación** es obligatoria en este formulario. El botón activa el GPS para llenar longitud y latitud. Sin coordenadas, el registro fallará.

### Ejemplo de body para Postman (QA)

```json
{
  "numero_cable": "CABLE-QA-001",
  "nivel_dano": "Medio",
  "direccion": "Calle 80 # 30-40, Bogotá",
  "observaciones": "Caja rota con cables expuestos",
  "remedy_id": "INC000012345",
  "tecnico": "Tecnico QA",
  "latitud": 4.6500,
  "longitud": -74.1200
}
```

### Respuesta exitosa

```json
{
  "message": "Reporte de mal estado registrado correctamente",
  "id": 789
}
```

---

## Errores comunes en todos los registros

| Código | Causa | Solución |
|--------|-------|----------|
| **401** | Credenciales incorrectas | Verificar usuario/contraseña en Basic Auth |
| **409** | `id_texto` duplicado en Empalme (si se envía desde Postman) | Usar un valor distinto o dejarlo vacío |
| **422** | Campo requerido vacío o inválido | Revisar que latitud/longitud estén diligenciados; para Cable, verificar que hay 2 puntos |
| **500** | Error interno de base de datos | Revisar los logs del servidor en Railway |

---

## Coordenadas de prueba — Bogotá

Para pruebas manuales desde Postman (sin GPS), usar coordenadas reales de Bogotá:

| Zona | Latitud | Longitud |
|------|---------|----------|
| Centro | `4.5981` | `-74.0761` |
| Norte | `4.7437` | `-74.0616` |
| Sur | `4.5000` | `-74.1200` |
| Occidente | `4.6500` | `-74.1500` |

---

## URL de la API

| Ambiente | URL base |
|----------|----------|
| Railway (QA/Prod) | `https://geoappfastapi-develop-production.up.railway.app/api` |
| Local | `http://localhost:8000/api` |
