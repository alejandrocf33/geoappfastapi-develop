# Autenticación en GeoAPIs

GeoAPIs utiliza autenticación HTTP Basic para proteger todas las rutas. Este documento explica cómo autenticarse correctamente con el sistema.

## Método de Autenticación

El sistema utiliza autenticación HTTP Basic, que requiere incluir un encabezado `Authorization` en todas las solicitudes HTTP a las APIs.

### Formato del encabezado

```
Authorization: Basic <credenciales_codificadas_en_base64>
```

Donde `<credenciales_codificadas_en_base64>` es la cadena resultante de codificar en Base64 la cadena `username:password`.

## Ejemplos de Autenticación

### Usando cURL

```bash
# Suponiendo username=admin, password=secret
curl -X GET "http://localhost:8000/api/camaras" \
     -H "Authorization: Basic YWRtaW46c2VjcmV0" 
```

### Usando JavaScript (fetch)

```javascript
const username = 'admin';
const password = 'secret';
const headers = new Headers();
headers.append('Authorization', 'Basic ' + btoa(username + ':' + password));

fetch('http://localhost:8000/api/camaras', {
  method: 'GET',
  headers: headers
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Usando Python (requests)

```python
import requests
import base64

username = 'admin'
password = 'secret'
credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

headers = {'Authorization': f'Basic {credentials}'}
response = requests.get('http://localhost:8000/api/camaras', headers=headers)
data = response.json()
print(data)
```

## Errores de Autenticación

Si las credenciales proporcionadas son incorrectas o no se proporciona el encabezado de autenticación, el servidor responderá con un error 401 Unauthorized:

```json
{
  "status": "error",
  "code": "authentication_error",
  "message": "Credenciales incorrectas o no proporcionadas"
}
```

## Configuración de Credenciales

Las credenciales de acceso se configuran en el archivo `app/config.py` mediante las variables:

- `API_USERNAME`: Nombre de usuario para acceder a la API
- `API_PASSWORD`: Contraseña para acceder a la API

**Nota**: En entornos de producción, se recomienda utilizar variables de entorno para configurar estas credenciales en lugar de hardcodearlas en el código fuente.
