# GeoAPIs — Documentación

Documentación técnica completa del sistema de gestión de infraestructura geoespacial para redes de fibra óptica.

---

## 📚 Índice de Documentación

### Documentación Esencial

| Documento | Descripción | Audiencia |
| --------- | ----------- | --------- |
| [Guía de Pruebas QA](guia-pruebas-qa.md) | Guía completa para testing, formularios, validación y consultas SQL | **QA, Testing, DBAs** |
| [API Referencia](api-referencia.md) | Documentación completa de todos los endpoints de la API | **Desarrolladores** |
| [Database Schema](database-schema.md) | Esquema de base de datos, tablas, campos y tipos de datos | **Desarrolladores, DBAs** |

### Guías de Integración

| Documento | Descripción | Audiencia |
| --------- | ----------- | --------- |
| [Autenticación](autenticacion.md) | HTTP Basic Auth, middleware y configuración | **Desarrolladores** |
| [Formato GeoJSON](formato-geojson.md) | Estructura de respuestas GeoJSON y propiedades | **Desarrolladores, Frontend** |
| [Integración Postman](guia-postman.md) | Importar colección y configurar Postman | **QA, Desarrolladores** |

### Guías de Mantenimiento

| Documento | Descripción | Audiencia |
| --------- | ----------- | --------- |
| [Configuración](configuracion.md) | Variables de entorno y configuración del sistema | **DevOps, Administradores** |
| [Manejo de Secuencias](manejo-secuencias.md) | Reset de secuencias PostgreSQL tras migraciones | **DBAs, DevOps** |

---

## 🚀 Quick Start

### Para QA / Testing

1. **Iniciar**: Leer [Guía de Pruebas QA](guia-pruebas-qa.md)
2. **Herramientas**: Instalar [Postman](https://www.postman.com/) o [pgAdmin 4](https://www.pgadmin.org/)
3. **Credenciales**: Obtener usuario/contraseña de API del administrador
4. **Testing**: Seguir ejemplos en guía de pruebas para cada tipo de formulario

### Para Desarrolladores

1. **Arquitectura**: Leer [Database Schema](database-schema.md) para entender el modelo de datos
2. **API**: Consultar [API Referencia](api-referencia.md) para endpoints disponibles
3. **Autenticación**: Configurar [HTTP Basic Auth](autenticacion.md)
4. **GeoJSON**: Entender [formato de respuestas](formato-geojson.md)

### Para DBAs

1. **Esquema**: Revisar [Database Schema](database-schema.md)
2. **Queries**: Ver [Guía de Pruebas QA - Verificación SQL](guia-pruebas-qa.md#verificación-de-datos-con-sql) para consultas útiles
3. **Mantenimiento**: Leer [Manejo de Secuencias](manejo-secuencias.md)
4. **Herramientas**: Configurar [pgAdmin 4](guia-pruebas-qa.md#herramientas-de-testing-sql)

---

## 📖 Documentación por Caso de Uso

### Registrar un Elemento

**Documentos**:
- [Guía de Pruebas QA](guia-pruebas-qa.md) - Formularios y campos
- [API Referencia](api-referencia.md) - Endpoints POST
- [Integración Postman](guia-postman.md) - Testing con Postman

### Consultar Elementos Geoespaciales

**Documentos**:
- [API Referencia](api-referencia.md) - Endpoints GET con parámetros espaciales
- [Formato GeoJSON](formato-geojson.md) - Estructura de respuestas
- [Testing Guide](testing-guide.md) - Consultas SQL espaciales

### Verificar Datos en la Base de Datos

**Documentos**:
- [Guía de Pruebas QA - Verificación SQL](guia-pruebas-qa.md#verificación-de-datos-con-sql) - Herramientas y consultas SQL
- [Database Schema](database-schema.md) - Estructura de tablas
- Archivo: `sql/queries_test.sql` - Consultas de referencia

### Configurar el Sistema

**Documentos**:
- [Configuración](configuracion.md) - Variables de entorno
- [Autenticación](autenticacion.md) - Setup de auth y middleware
- [Manejo de Secuencias](manejo-secuencias.md) - Post-migración

---

## 🗂️ Estructura del Proyecto

```
geoappfastapi-develop/
├── app/
│   ├── routes/
│   │   ├── cache_routes.py      # Endpoints GET (lectura)
│   │   ├── logic_routes.py      # Endpoints de análisis espacial
│   │   ├── write_routes.py      # Endpoints POST (escritura)
│   │   └── api_models.py        # Modelos Pydantic
│   ├── auth.py                  # HTTP Basic Auth
│   ├── config.py                # Variables de entorno
│   ├── database.py              # Connection pool PostgreSQL
│   ├── db_access.py             # Queries y lógica de BD
│   ├── models.py                # Modelos SQLAlchemy
│   └── main.py                  # App FastAPI + middleware
├── docs/                        # 📚 Esta carpeta
├── sql/                         # Scripts SQL y funciones PostGIS
└── requirements.txt             # Dependencias Python
```

---

## 🔗 Enlaces Útiles

### Herramientas Recomendadas

- [pgAdmin 4](https://www.pgadmin.org/download/) - IDE PostgreSQL
- [Postman](https://www.postman.com/downloads/) - Testing de APIs
- [DBeaver](https://dbeaver.io/download/) - Cliente SQL universal
- [QGIS](https://qgis.org/) - Visualización de datos geoespaciales

### Documentación Externa

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GeoJSON Specification](https://geojson.org/)

### APIs en Vivo

| Ambiente | URL | Documentación Interactiva |
| -------- | --- | ------------------------ |
| Railway (QA/Prod) | `https://geoappfastapi-develop-production.up.railway.app` | No disponible (solo local) |
| Local | `http://localhost:8000` | [Swagger UI](http://localhost:8000/docs), [ReDoc](http://localhost:8000/redoc) |

---

## 🆘 Soporte

### Reportar Problemas

Para reportar bugs o issues:

1. Verificar que el problema no esté documentado en las guías existentes
2. Revisar [Errores Comunes](guia-pruebas-qa.md#errores-comunes)
3. Consultar [Testing Guide - Troubleshooting](testing-guide.md#troubleshooting)
4. Contactar al equipo de desarrollo con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs o mensajes de error
   - Ambiente (Railway/Local)

### Contribuir a la Documentación

Para sugerir mejoras o correcciones a la documentación, contactar al equipo de desarrollo.

---

## 📋 Convenciones de Documentación

### Formato de Código

- **SQL**: Usar UPPERCASE para palabras clave SQL
- **JSON**: Usar comillas dobles, formato indentado
- **Python**: Seguir PEP 8

### Nombres de Campos

- **API**: snake_case (ej: `nombre_esp`, `remedy_id`)
- **Base de Datos**: snake_case para columnas, JSONB usa strings
- **Geometría**: Siempre SRID 4326 (WGS84), formato `[longitud, latitud]`

### Versionamiento

- Las actualizaciones de documentación siguen el versionamiento del proyecto
- Versión actual: **1.0.0**
- Última actualización: 2026-02-20

---

## 📝 Changelog

### v1.0.0 (2026-02-20)

- ✨ Documentación inicial completa
- 📚 Database Schema con descripción de todas las tablas
- 🧪 Testing Guide con queries SQL de verificación
- 📋 Guía de Pruebas QA reorganizada por formulario
- 🔗 Integración de referencias cruzadas entre documentos
- 🎯 Validación completa de queries vs formularios
