# Autenticacion en GeoAPIs

GeoAPIs utiliza autenticacion HTTP Basic para proteger todos los endpoints.

---

## Metodo de autenticacion

Todas las solicitudes HTTP requieren un encabezado `Authorization` con credenciales codificadas en Base64:

```
Authorization: Basic <credenciales_codificadas_en_base64>
```

Donde `<credenciales_codificadas_en_base64>` es el resultado de codificar `username:password` en Base64.

Las credenciales se configuran con las variables de entorno `API_USERNAME` y `API_PASSWORD` en el archivo `.env`.

---

## Ejemplos

### curl

```bash
curl -u "usuario:contrasena" https://api-host/api/camaras
```

### Python (requests)

```python
import requests

response = requests.get(
    "https://api-host/api/camaras",
    auth=("usuario", "contrasena")
)
data = response.json()
```

### JavaScript (fetch)

```javascript
const username = 'usuario';
const password = 'contrasena';
const headers = new Headers();
headers.append('Authorization', 'Basic ' + btoa(username + ':' + password));

fetch('https://api-host/api/camaras', {
  method: 'GET',
  headers: headers
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Respuesta 401

Si las credenciales son incorrectas o no se proporcionan, el servidor responde con:

```json
{"detail": "Credenciales incorrectas"}
```

> **Nota:** La respuesta 401 usa el formato estandar de FastAPI (`{"detail": "..."}`) y NO el formato `ErrorResponse` estructurado que se usa en otros codigos de error.
