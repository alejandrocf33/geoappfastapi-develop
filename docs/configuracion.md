# Configuracion del Entorno

## Variables de entorno

| Variable | Requerida | Descripcion | Ejemplo |
| --- | :---: | --- | --- |
| `DB_HOST` | Si | Host de la base de datos PostgreSQL | `aws-1-sa-east-1.pooler.supabase.com` |
| `DB_PORT` | Si | Puerto de la base de datos | `6543` |
| `DB_NAME` | Si | Nombre de la base de datos | `postgres` |
| `DB_USER` | Si | Usuario de la base de datos | `postgres.xxxxx` |
| `DB_PASSWORD` | Si | Contrasena de la base de datos | |
| `API_USERNAME` | No | Usuario para HTTP Basic Auth | |
| `API_PASSWORD` | No | Contrasena para HTTP Basic Auth | |
| `APP_DEBUG` | No | Modo debug (`true`/`false`) | `false` en prod |
| `OFFICE_IP` | No | IP de oficina con acceso directo | `181.234.203.142` |
| `ORACLE_REFERER_PATTERN` | No | Regex del referer permitido desde Oracle Cloud | ver `.env.example` |
| `ALLOWED_LOCAL_ORIGIN` | No | Origen local permitido (solo desarrollo) | `http://127.0.0.1:5500` |

---

## Configuracion por entorno

El proyecto usa archivos `.env` ignorados por git. Copiar el archivo correspondiente:

| Entorno | Archivo fuente | Comando |
| --- | --- | --- |
| Local / Desarrollo | `.env.example` | `cp .env.example .env` |
| QA | `.env.qa` | `cp .env.qa .env` |
| Produccion | `.env.prod` | `cp .env.prod .env` |

> **Nota:** `.env`, `.env.qa` y `.env.prod` estan en `.gitignore` y nunca se versionan.
> Solo `.env.example` se versiona como plantilla de referencia sin credenciales.

---

## Comportamiento por entorno

Dos variables controlan el comportamiento de seguridad y documentacion:

- **`APP_DEBUG`** — Controla el middleware y los errores detallados
- **`ALLOWED_LOCAL_ORIGIN`** — Controla la documentacion interactiva

### Matriz de comportamiento

| Funcionalidad | Local | QA | Produccion |
| --- | --- | --- | --- |
| `APP_DEBUG` | `true` | `true` | `false` |
| `ALLOWED_LOCAL_ORIGIN` | `http://127.0.0.1:5500` | vacio | vacio |
| `/docs`, `/redoc`, `/openapi.json` | Disponible | 404 | 404 |
| Middleware de acceso | Solo log (no bloquea) | Bloquea con 403 | Bloquea con 403 |
| Traceback en errores 500 | Visible en respuesta | Visible en respuesta | Oculto |

### Configuracion recomendada por entorno

| Variable | Local | QA | Produccion |
| --- | --- | --- | --- |
| `APP_DEBUG` | `true` | `true` | `false` |
| `ALLOWED_LOCAL_ORIGIN` | `http://127.0.0.1:5500` | vacio | vacio |
| `ORACLE_REFERER_PATTERN` | vacio o patron | patron completo | patron completo |
| `OFFICE_IP` | vacio o IP real | IP real | IP real |

---

## Middleware de validacion de acceso

En **QA y produccion** (`APP_DEBUG=false`), el middleware valida el origen de cada peticion. Se permite el acceso si se cumple **alguna** de estas condiciones:

| Condicion | Variable de entorno | Descripcion |
| --- | --- | --- |
| Referer coincide con patron Oracle Cloud | `ORACLE_REFERER_PATTERN` | Integracion con Oracle Cloud |
| `X-Forwarded-For` es la IP de oficina | `OFFICE_IP` | Acceso directo desde red interna |
| Origin/Referer coincide con origen local | `ALLOWED_LOCAL_ORIGIN` | Acceso desde origen permitido |

Las peticiones que no cumplen ninguna condicion reciben `403 Acceso denegado`.

En **local** (`APP_DEBUG=true`), el middleware solo registra en consola el origen de cada peticion sin bloquear ninguna. Esto permite usar Postman, curl, navegador o cualquier herramienta sin restricciones.

---

## Documentacion interactiva

Swagger UI (`/docs`), ReDoc (`/redoc`) y el esquema OpenAPI (`/openapi.json`) solo estan disponibles cuando `ALLOWED_LOCAL_ORIGIN` tiene un valor configurado. Esto asegura que la documentacion de la API no quede expuesta en QA ni produccion.

---

## Cache

Los endpoints `all_*` usan cache en memoria con TTL de **6 horas** (`cachetools.TTLCache`).

El cache se invalida al reiniciar el servidor. Para forzar datos frescos en desarrollo, reiniciar el proceso.
