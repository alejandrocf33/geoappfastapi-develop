# GeoAPIs - Documentación

GeoAPIs es una aplicación FastAPI para gestión de infraestructura geoespacial, ofreciendo endpoints para consultar, crear y analizar datos geográficos como cámaras, cables, centrales, empalmes y reservas.

## Requisitos

- PostgreSQL con PostGIS
- Python 3.8+
- Google Maps API Key (para visualizaciones)
- GDAL/OGR (para cargar datos GeoJSON)

## Características

- APIs RESTful para gestión de datos geoespaciales
- Autenticación de usuarios
- Soporte para geometrías WKT y coordenadas directas
- Operaciones espaciales avanzadas con PostGIS
- Documentación interactiva con Swagger y ReDoc
- Sistema de caché para mejorar el rendimiento de consultas frecuentes

## Documentación de la API

La documentación completa de la API está disponible en varios formatos:

### Documentación Interactiva

- **Swagger UI**: Disponible en `/docs` - Interfaz interactiva que permite probar endpoints directamente
- **ReDoc**: Disponible en `/redoc` - Documentación más limpia y detallada para consulta

### Documentos Adicionales

- [AUTH.md](AUTH.md): Guía detallada sobre el sistema de autenticación y ejemplos
- [GEOJSON.md](GEOJSON.md): Explicación del formato GeoJSON utilizado en las respuestas
- [POSTMAN.md](POSTMAN.md): Instrucciones para integrar la API con Postman
- [SEQUENCE_GUIDE.md](SEQUENCE_GUIDE.md): Guía para resolver problemas con secuencias de PostgreSQL

### Ejemplos de Uso

El archivo [pruebas_completas_api.http](pruebas_completas_api.http) contiene ejemplos completos de todas las operaciones disponibles en la API.

### Integración con Postman

La API puede ser fácilmente importada a Postman para pruebas y desarrollo:

1. **Importación directa**: Importa el esquema desde `http://localhost:8000/openapi.json`
2. **Colección generada**: Ejecuta `python generate_postman.py http://localhost:8000/openapi.json`

Para más detalles, consulta [POSTMAN.md](POSTMAN.md).

**URL:** [http://localhost:8000/docs](http://localhost:8000/docs) (cuando la aplicación está en ejecución)

### ReDoc

Una alternativa más limpia y organizada para leer la documentación:

**URL:** [http://localhost:8000/redoc](http://localhost:8000/redoc) (cuando la aplicación está en ejecución)

## Instalación e Inicio

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor con recarga automática
python run.py
```

También puedes iniciar el servidor directamente con uvicorn:
```bash
uvicorn app.main:app --reload
```

## Grupos de Endpoints

La API está organizada en los siguientes grupos:

### Operaciones de Escritura

Endpoints para la creación de nuevos elementos geoespaciales:
- `/api/camaras/` - Crear nuevas cámaras
- `/api/cable_corporativo/` - Crear nuevos cables
- `/api/centrales/` - Crear nuevas centrales
- `/api/empalmes/` - Crear nuevos empalmes
- `/api/reservas/` - Crear nuevas reservas

### Consultas con Caché

Endpoints de lectura que utilizan sistema de caché para mejorar el rendimiento:
- `/api/camaras` - Consultar cámaras por ubicación
- `/api/all_camaras` - Obtener todas las cámaras
- `/api/cables` - Consultar cables por ubicación
- `/api/all_cables` - Obtener todos los cables
- Endpoints similares para centrales, empalmes y reservas

### Consultas con Lógica

Endpoints que realizan operaciones espaciales o lógicas avanzadas:
- `/api/camaras_en_falla` - Detectar posibles cámaras en falla
- `/api/cables_cercanos` - Buscar cables próximos a un punto
- `/api/linea_en_ruta_red` - Calcular rutas en la red

## Autenticación

Todos los endpoints requieren autenticación mediante token JWT. Para obtener un token:

```
POST /token
Content-Type: application/x-www-form-urlencoded

username=usuario&password=contraseña
```

Luego, incluye el token en las solicitudes:

```
Authorization: Bearer {token}
```

## Mantenimiento de la Base de Datos

### Restablecer Secuencias de PostgreSQL

Si experimentas errores de clave duplicada al crear nuevos registros, puede deberse a que las secuencias de ID no están sincronizadas con los datos existentes. Esto suele ocurrir después de cargar datos con IDs explícitos o hacer inserciones manuales en la base de datos.

Para restablecer todas las secuencias:

```bash
python -m app.reset_sequences
```

## Uso de Coordenadas vs. WKT

Las APIs de creación aceptan tanto coordenadas directas como geometrías WKT:

### Ejemplo con coordenadas directas:
```json
{
  "id_texto": "CAM-001",
  "nombre_esp": "Cámara Principal",
  "ubicacion": "Calle 100 #15-20",
  "tipo": "Subterránea",
  "longitud": -74.0617,
  "latitud": 4.6737
}
```

### Ejemplo con geometría WKT:
```json
{
  "id_texto": "CAM-001",
  "nombre_esp": "Cámara Principal",
  "ubicacion": "Calle 100 #15-20",
  "tipo": "Subterránea",
  "geometry": "POINT(-74.0617 4.6737)"
}
```

Para LineStrings (cables), también se puede usar una lista de puntos:
```json
{
  "id_texto": "CABLE-001",
  "name": "Cable Troncal Norte",
  "puntos": [
    {"longitud": -74.0617, "latitud": 4.6737},
    {"longitud": -74.0618, "latitud": 4.6738},
    {"longitud": -74.0619, "latitud": 4.6739}
  ]
}
```
