# GeoAPIs - Guía para Postman

Esta guía explica cómo importar y utilizar la API GeoAPIs en Postman, una herramienta popular para probar y documentar APIs.

## Importar la API en Postman

Existen dos maneras de importar la API GeoAPIs en Postman:

### Método 1: Importar directamente desde la URL de OpenAPI

1. Inicia Postman
2. Haz clic en el botón "Import" en la esquina superior izquierda
3. Selecciona la pestaña "Link"
4. Ingresa la URL: `http://localhost:8000/openapi.json`
5. Haz clic en "Continue" y luego en "Import"

### Método 2: Usar el script generador de colección

Este método proporciona una importación más completa con ejemplos de solicitud y mejor organización.

1. Asegúrate de que el servidor GeoAPIs esté en ejecución
2. Abre una terminal y ejecuta:
   ```
   python generate_postman.py http://localhost:8000/openapi.json
   ```
3. Esto generará el archivo `geoapis_postman_collection.json`
4. En Postman, haz clic en "Import" y selecciona este archivo

Alternativamente, puedes iniciar el servidor con la opción `--postman`:
```
python run.py --postman
```
Esto generará automáticamente la colección después de iniciar el servidor.

## Configuración de Autenticación

La colección generada está preconfigurada con autenticación básica, pero necesitas ajustar las credenciales:

1. Haz clic en los tres puntos (...) junto al nombre de la colección
2. Selecciona "Edit"
3. Ve a la pestaña "Variables"
4. Actualiza las variables:
   - `username`: Nombre de usuario para la API (por defecto "admin")
   - `password`: Contraseña para la API (por defecto "password")

## Encabezados Personalizados

Para las operaciones de escritura (creación de elementos), puedes especificar un usuario personalizado para trazabilidad:

1. En cada petición POST, agrega un header personalizado:
   - Nombre: `user-header`
   - Valor: [nombre del usuario para trazabilidad]

Este header es opcional. Si no se proporciona, se utilizará el usuario de la autenticación básica.
Este valor se guardará en los campos `created_by` y `updated_by` en la base de datos.

## Estructura de la Colección

La colección está organizada por categorías que reflejan los tags de la API:

- **Operaciones de Escritura**: Endpoints para crear nuevos elementos
- **Operaciones de Lectura**: Endpoints para consultar datos existentes

## Notas importantes sobre los endpoints

A partir de la última versión, la API acepta URLs tanto con como sin barra final. Por ejemplo, ambas formas son válidas:
- POST `/api/camaras/` 
- POST `/api/camaras`

Si experimentas error "Method Not Allowed" al usar Postman, verifica que:
1. Estás usando el método HTTP correcto (GET, POST, etc.)
2. El endpoint está correctamente escrito, incluyendo el prefijo `/api/`
- **Operaciones Lógicas**: Endpoints para análisis y operaciones complejas

## Ejemplos de Uso

### Consultar Cámaras

1. Expande la carpeta "Operaciones de Lectura"
2. Selecciona "Consultar cámaras"
3. En la pestaña "Params", añade los parámetros deseados:
   - `lat`: Latitud (ej. 4.6737)
   - `lon`: Longitud (ej. -74.0617)
   - `radio_interno`: Radio interno en metros (ej. 0)
   - `radio_externo`: Radio externo en metros (ej. 500)
4. Haz clic en "Send"

### Crear una Nueva Cámara

1. Expande la carpeta "Operaciones de Escritura"
2. Selecciona "Crear nueva cámara"
3. En la pestaña "Body", ya encontrarás un ejemplo que puedes modificar
4. Haz clic en "Send"

## Manejo de Errores

Los códigos de estado HTTP indican el resultado de la operación:

- **2xx**: Éxito (200 OK, 201 Created, etc.)
- **4xx**: Error del cliente (400 Bad Request, 401 Unauthorized, 404 Not Found, 409 Conflict, etc.)
- **5xx**: Error del servidor (500 Internal Server Error, etc.)

## Nota sobre secuencias de ID

Cuando se crea un nuevo registro mediante los endpoints POST, el sistema automáticamente asigna un ID utilizando secuencias de PostgreSQL. Si experimentas errores de clave primaria duplicada después de cargar datos iniciales o hacer inserciones manuales con IDs específicos, puedes restablecer las secuencias ejecutando:

```bash
python -m app.reset_sequences
```

Este script actualiza todas las secuencias de ID para que comiencen desde el máximo ID existente + 1, evitando conflictos de clave primaria en futuras inserciones.

Los errores incluyen información detallada sobre el problema en el cuerpo de la respuesta.

## Personalización

Puedes guardar ejemplos de respuestas haciendo clic en "Save Response" y luego "Save as Example" después de realizar una solicitud satisfactoria.

## Pruebas Automatizadas

Postman permite crear pruebas automatizadas para verificar que la API funciona correctamente:

1. En cualquier solicitud, ve a la pestaña "Tests"
2. Añade código JavaScript para verificar la respuesta, por ejemplo:
   ```javascript
   pm.test("Respuesta exitosa", function () {
       pm.response.to.have.status(200);
   });
   
   pm.test("Datos en formato GeoJSON", function () {
       var jsonData = pm.response.json();
       pm.expect(jsonData.type).to.eql("FeatureCollection");
       pm.expect(jsonData.features).to.be.an("array");
   });
   ```
