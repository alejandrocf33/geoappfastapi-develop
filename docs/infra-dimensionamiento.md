# Análisis de Infraestructura - GeoAPIs QA y Producción

> **Premisa fija:** Las dos bases de datos (QA y Producción) se despliegan en servidores on-premise PostgreSQL existentes en ETB. Este documento presenta dos alternativas exclusivamente para el backend.

---

## 1. Alternativa A — Backend en Servidor Linux Oracle On-Premise

### 1.1 Diagrama de Arquitectura

```
                   Internet / Red Corporativa
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│           SERVIDOR LINUX ORACLE (On-Prem)            │
│           4 vCPU / 4 GB RAM / 30 GB SSD              │
│                                                      │
│   ┌────────────────────────────────────────────┐     │
│   │  Nginx (443/SSL)                           │     │
│   │    ├── geoapi-qa.etb.local  → :8001        │     │
│   │    └── geoapi.etb.local     → :8000        │     │
│   └────────────────────────────────────────────┘     │
│                                                      │
│   ┌───────────────────┐  ┌───────────────────┐       │
│   │ Docker: geoapi    │  │ Docker: geoapi    │       │
│   │ PROD (:8000)      │  │ QA (:8001)        │       │
│   │ 2 vCPU / 2 GB     │  │ 2 vCPU / 2 GB     │       │
│   └─────────┬─────────┘  └─────────┬─────────┘       │
│             │                       │                 │
└─────────────┼───────────────────────┼─────────────────┘
              │      Red LAN          │
┌─────────────┼───────────────────────┼─────────────────┐
│             ▼                       ▼                 │
│   ┌───────────────────┐  ┌───────────────────┐       │
│   │  DB: geoapi_prod  │  │  DB: geoapi_qa    │       │
│   └───────────────────┘  └───────────────────┘       │
│          SERVIDOR POSTGRESQL ON-PREM                  │
│          6 vCPU / 12 GB RAM / 150 GB SSD              │
└───────────────────────────────────────────────────────┘
```

### 1.2 Servidor Backend — Hardware

| Recurso | QA | Producción | Total Servidor |
|---|---|---|---|
| **vCPU** | 1 | 2 | **4** (incluye OS + Nginx) |
| **RAM** | 1 GB | 2 GB | **4 GB** |
| **Disco** | 5 GB | 10 GB | **30 GB SSD** |
| **Red** | - | - | **1 Gbps** |

### 1.3 Servidor Backend — Desglose de RAM

| Componente | PROD | QA |
|---|---|---|
| FastAPI + Uvicorn (1 worker) | 50 MB | 50 MB |
| TTLCache lleno (5 endpoints get_all) | 120 MB | 80 MB |
| Pool psycopg2 (10 conexiones) | 20 MB | 20 MB |
| Picos procesamiento GeoJSON | 100 MB | 50 MB |
| **Subtotal por ambiente** | **~290 MB** | **~200 MB** |
| Docker engine (compartido) | 100 MB | - |
| Nginx (compartido) | 30 MB | - |
| Sistema operativo | 500 MB | - |
| **Total servidor** | **~1.1 GB activo** (asignar 4 GB) | |

### 1.4 Servidor Backend — Desglose de Disco

| Componente | Espacio |
|---|---|
| Oracle Linux base | 5 GB |
| Docker engine + imágenes | 3 GB |
| Imagen Docker GeoAPI × 2 ambientes | 800 MB |
| Logs rotativos 30 días (ambos ambientes) | 3 GB |
| Nginx + certificados SSL | 50 MB |
| Swap + temporal | 2 GB |
| **Total** | **~14 GB** (asignar 30 GB) |

### 1.5 Servidor Backend — Software Requerido

| Software | Versión | Propósito |
|---|---|---|
| Docker Engine | 20.10+ | Contenedores de la app |
| Docker Compose | 2.0+ | Orquestación QA + PROD |
| Nginx | 1.18+ | Reverse proxy, SSL, rate limiting |
| Certificado SSL | - | HTTPS (corporativo o Let's Encrypt) |
| Git | 2.30+ | Pull de código para builds |

### 1.6 Servidor Backend — Puertos

| Puerto | Protocolo | Dirección | Uso |
|---|---|---|---|
| 443 | HTTPS | Inbound | Nginx → clientes |
| 80 | HTTP | Inbound | Redirect a 443 |
| 8000 | HTTP | localhost | FastAPI PROD |
| 8001 | HTTP | localhost | FastAPI QA |
| 5432 | TCP | Outbound | → PostgreSQL on-prem |

### 1.7 Costos Alternativa A

| Concepto | Costo Mensual |
|---|---|
| Servidor Linux Oracle | **$0** (existente) |
| Licencias Docker CE | $0 (open source) |
| Licencias Nginx | $0 (open source) |
| SSL (Let's Encrypt) | $0 |
| **Total mensual** | **$0 USD** |

### 1.8 Pros y Contras — Alternativa A

| Pros | Contras |
|---|---|
| Cero costo adicional | Administración manual (updates, patches OS) |
| Latencia mínima backend↔DB (misma LAN) | Sin auto-scaling |
| Datos 100% dentro del perímetro corporativo | Sin alta disponibilidad nativa (requiere config manual) |
| Control total sobre configuración | Requiere equipo de infra para mantenimiento |
| Sin dependencia de servicios cloud | Deploy manual o scripts CI/CD propios |

---

## 2. Alternativa B — Backend en Azure Container Apps

### 2.1 Por qué Azure Container Apps (ACA)

| Servicio Azure | Descartado / Elegido | Razón |
|---|---|---|
| Azure Kubernetes Service (AKS) | Descartado | Sobredimensionado para 1 contenedor, requiere gestión de cluster |
| Azure Container Instances (ACI) | Descartado | Sin HTTPS nativo, sin auto-scaling, sin revisiones |
| Azure App Service | Descartado | Menos flexible que ACA para contenedores custom |
| **Azure Container Apps (ACA)** | **Elegido** | HTTPS built-in, auto-scaling (incluso a 0), revisiones blue/green, simple |

### 2.2 Diagrama de Arquitectura

```
                        Internet
                           │
                           ▼
              ┌────────────────────────┐
              │   Azure Front Door     │
              │   (opcional, CDN+WAF)  │
              └────────────┬───────────┘
                           │
         ┌─────────────────┼──────────────────┐
         │          Azure Cloud               │
         │                                    │
         │  ┌──────────────────────────────┐  │
         │  │  Azure Container Apps Env    │  │
         │  │                              │  │
         │  │  ┌────────────────────────┐  │  │
         │  │  │ geoapi-prod            │  │  │
         │  │  │ HTTPS auto (*.azurecon │  │  │
         │  │  │ tainerapps.io)         │  │  │
         │  │  │ 1 vCPU / 2 GB         │  │  │
         │  │  │ Min: 0, Max: 2 réplicas│  │  │
         │  │  └────────────┬───────────┘  │  │
         │  │               │              │  │
         │  │  ┌────────────────────────┐  │  │
         │  │  │ geoapi-qa             │  │  │
         │  │  │ HTTPS auto            │  │  │
         │  │  │ 0.5 vCPU / 1 GB       │  │  │
         │  │  │ Min: 0, Max: 1 réplica │  │  │
         │  │  └────────────┬───────────┘  │  │
         │  └───────────────┼──────────────┘  │
         │                  │                 │
         │  ┌───────────────────────────┐     │
         │  │  VPN Gateway / ExpressRoute│     │
         │  └───────────────┬───────────┘     │
         └──────────────────┼─────────────────┘
                            │  VPN Site-to-Site
              ┌─────────────┼─────────────────────┐
              │             ▼                     │
              │   ┌───────────────┐ ┌───────────┐ │
              │   │ geoapi_prod   │ │ geoapi_qa │ │
              │   └───────────────┘ └───────────┘ │
              │    SERVIDOR POSTGRESQL ON-PREM     │
              │    6 vCPU / 12 GB RAM / 150 GB     │
              └───────────────────────────────────┘
```

### 2.3 Recursos Azure — Producción

| Recurso Azure | SKU / Config | Especificación | Costo/mes USD |
|---|---|---|---|
| **Container App — PROD** | Consumption plan | 1 vCPU / 2 GB RAM | ~$36* |
| **Container App — QA** | Consumption plan | 0.5 vCPU / 1 GB RAM | ~$18* |
| **Container Apps Environment** | Consumption | Shared environment para ambos | Incluido |
| **Azure Container Registry** | Basic | Almacenar imágenes Docker | ~$5 |
| **VPN Gateway** | VpnGw1 (Gen1) | Conectividad Azure ↔ On-prem | ~$140 |
| **Log Analytics Workspace** | Free tier (5 GB/mes) | Logs y monitoring | $0 |
| **Total sin VPN** | | | **~$59 USD** |
| **Total con VPN** | | | **~$199 USD** |

> *Precios Consumption plan: $0.000012/vCPU-s + $0.000002/GiB-s. Estimado para uso 24/7 con 1 réplica activa. Si se configura scale-to-zero en QA, el costo baja ~30%.

### 2.4 Recursos Azure — Desglose por Container App

#### PROD

| Parámetro | Valor |
|---|---|
| CPU | 1 vCPU |
| Memoria | 2 GB |
| Min réplicas | 1 (siempre activo) |
| Max réplicas | 2 (auto-scale por CPU > 70%) |
| Ingress | HTTPS externo, puerto 8000 |
| Health probe | `/docs` (liveness), `/api/all_centrales` (readiness) |
| Imagen | `geoapi:prod-latest` desde ACR |

#### QA

| Parámetro | Valor |
|---|---|
| CPU | 0.5 vCPU |
| Memoria | 1 GB |
| Min réplicas | 0 (scale-to-zero cuando no hay tráfico) |
| Max réplicas | 1 |
| Ingress | HTTPS externo, puerto 8001 |
| Health probe | `/docs` |
| Imagen | `geoapi:qa-latest` desde ACR |

### 2.5 Conectividad Azure ↔ PostgreSQL On-Prem

| Opción | Costo/mes | Latencia | Seguridad |
|---|---|---|---|
| **VPN Gateway Site-to-Site** | ~$140 | 5-15ms | Alta (IPSec tunnel) |
| **ExpressRoute** | ~$200+ | 1-5ms | Muy alta (circuito dedicado) |
| **Exponer PG por IP pública + SSL** | $0 | Variable | Media (SSL + firewall rules) |

> **Recomendación:** VPN Gateway Site-to-Site es el balance correcto. ExpressRoute es para alto volumen de datos. Exponer PostgreSQL público es viable para QA si se restringe por IP + SSL, pero NO recomendado para producción.

### 2.6 Costos Alternativa B

| Concepto | Con VPN | Sin VPN (PG público+SSL) |
|---|---|---|
| Container App PROD | $36 | $36 |
| Container App QA | $18 | $18 |
| Container Registry (Basic) | $5 | $5 |
| VPN Gateway (VpnGw1) | $140 | $0 |
| Log Analytics | $0 | $0 |
| **Total mensual** | **~$199 USD** | **~$59 USD** |

### 2.7 Pros y Contras — Alternativa B

| Pros | Contras |
|---|---|
| HTTPS automático sin gestionar certificados | Costo mensual recurrente ($59-199 USD) |
| Auto-scaling (incluso a 0 réplicas en QA) | Requiere VPN Gateway para conectar a DB on-prem ($140/mes) |
| Deploy con `az containerapp update` o GitHub Actions | Latencia adicional Azure↔On-prem (5-15ms por VPN) |
| Revisiones blue/green para rollbacks | Dependencia de proveedor cloud |
| Monitoring nativo (Log Analytics) | La DB sigue on-prem, no se beneficia de managed DB |
| Sin gestionar servidor Linux ni Docker | Complejidad de red (VPN setup inicial) |
| SLA 99.95% en Container Apps | PostgreSQL on-prem sigue siendo el SPOF |

---

## 3. Comparativa Directa: Alternativa A vs B

| Criterio | A: Linux Oracle On-Prem | B: Azure Container Apps |
|---|---|---|
| **Costo mensual** | $0 | $59-199 USD |
| **Costo anual** | $0 | $708-2,388 USD |
| **Latencia backend↔DB** | <1ms (misma LAN) | 5-15ms (VPN) |
| **HTTPS/SSL** | Manual (Nginx + certbot) | Automático |
| **Auto-scaling** | No | Si (0 a N réplicas) |
| **Deploy** | docker-compose up (manual/script) | `az containerapp update` o CI/CD |
| **Monitoring** | Manual (health checks + logs) | Nativo (Log Analytics + métricas) |
| **Alta disponibilidad backend** | No nativa (requiere config) | Si (multi-réplica) |
| **Mantenimiento OS** | Equipo infra (patches, updates) | Ninguno (serverless) |
| **Complejidad setup inicial** | Media (Docker + Nginx + SSL) | Alta (VPN + ACR + ACA + networking) |
| **Complejidad operación diaria** | Media | Baja |
| **Cumplimiento datos en perímetro** | Si (todo on-prem) | Parcial (backend en cloud, DB on-prem) |
| **Dependencia cloud** | Ninguna | Azure |
| **Recovery Time (backend caído)** | ~5-15 min (restart manual) | ~30s (auto-restart réplicas) |

### Recomendación

| Si... | Entonces... |
|---|---|
| Prioridad es costo cero y datos on-prem | **Alternativa A** |
| Prioridad es operación simple y auto-scaling | **Alternativa B** |
| Ya hay VPN Azure↔On-prem configurada | **Alternativa B** (costo baja a $59/mes) |
| No hay VPN y no se planea crear una | **Alternativa A** |
| Se requiere SLA formal del backend | **Alternativa B** (SLA 99.95%) |

---

## 4. Base de Datos PostgreSQL On-Prem (común a ambas alternativas)

### 4.1 Servidor de Base de Datos — Hardware

> Este servidor es el **mismo** para ambas alternativas. Aloja las dos bases de datos (QA + PROD).

| Recurso | DB QA | DB PROD | Total Servidor |
|---|---|---|---|
| **vCPU** | 2 | 4 | **6** |
| **RAM** | 4 GB | 8 GB | **12 GB** |
| **Disco** | 50 GB | 100 GB | **150 GB SSD** |
| **IOPS** | 500+ | 1000+ | **1000+** |
| **Red** | - | - | **1 Gbps** |

### 4.2 Desglose de RAM — DB QA

| Componente | Consumo |
|---|---|
| PostgreSQL shared_buffers | 1 GB |
| work_mem × ~5 conexiones activas | 64 MB × 5 = 320 MB |
| maintenance_work_mem (VACUUM, reindex) | 256 MB (temporal, nocturno) |
| PostGIS GIST index cache (via OS page cache) | ~200-500 MB |
| pgRouting Dijkstra working memory | ~50 MB por query |
| pg_stat_statements | ~20 MB |
| **Total activo** | **~2.0 GB** (asignar 4 GB) |

### 4.3 Desglose de RAM — DB Producción

| Componente | Consumo |
|---|---|
| PostgreSQL shared_buffers | 2 GB |
| work_mem × ~10 conexiones activas | 128 MB × 10 = 1.3 GB |
| maintenance_work_mem (VACUUM, reindex) | 512 MB (temporal, nocturno) |
| PostGIS GIST index cache (via OS page cache) | ~500 MB - 1 GB |
| pgRouting Dijkstra working memory | ~100 MB por query |
| pg_stat_statements | ~50 MB |
| **Total activo pico** | **~4.5-5.0 GB** (asignar 8 GB) |

### 4.4 Desglose de Disco — DB QA

| Componente | Espacio |
|---|---|
| Tablas de datos (6 entidades, dataset reducido) | ~200-500 MB |
| Tabla `red` + `red_vertices_pgr` (topología) | ~100-200 MB |
| Índices GIST geography (×6 tablas) | ~150-300 MB |
| Índices GIST geometry (×7 tablas incl. `red`) | ~100-200 MB |
| Índices B-tree + PK (×7 tablas) | ~50-100 MB |
| WAL (Write-Ahead Log) | ~1 GB |
| pg_stat_statements + catálogos | ~100 MB |
| Backups locales pg_dump (7 días) | ~3-5 GB |
| Crecimiento 1 año | ~1-2 GB |
| **Total** | **~6-10 GB** (asignar 50 GB) |

### 4.5 Desglose de Disco — DB Producción

| Componente | Espacio |
|---|---|
| Tablas de datos (6 entidades, dataset completo) | ~1-2 GB |
| Tabla `red` + `red_vertices_pgr` (topología completa) | ~300-500 MB |
| Índices GIST geography (×6 tablas) | ~500 MB - 1 GB |
| Índices GIST geometry (×7 tablas incl. `red`) | ~300-500 MB |
| Índices B-tree + PK (×7 tablas) | ~100-300 MB |
| JSONB + TOAST storage | ~500 MB - 1 GB |
| WAL (Write-Ahead Log) | ~2 GB |
| pg_stat_statements + catálogos | ~200 MB |
| Backups locales pg_dump (7 días) | ~10-15 GB |
| Crecimiento 2 años (~20% anual) | ~3-5 GB |
| **Total** | **~19-29 GB** (asignar 100 GB) |

### 4.6 Configuración PostgreSQL — QA

```ini
shared_buffers = 1GB
work_mem = 64MB
maintenance_work_mem = 256MB
effective_cache_size = 2GB
max_connections = 30
statement_timeout = 15000
wal_buffers = 16MB
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100
log_min_duration_statement = 1000
shared_preload_libraries = 'pg_stat_statements'
```

### 4.7 Configuración PostgreSQL — Producción

```ini
shared_buffers = 2GB
work_mem = 128MB
maintenance_work_mem = 512MB
effective_cache_size = 5GB
max_connections = 50
statement_timeout = 15000
wal_buffers = 64MB
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 200
log_min_duration_statement = 500
shared_preload_libraries = 'pg_stat_statements'
checkpoint_completion_target = 0.9
max_wal_size = 2GB
min_wal_size = 512MB
```

---

## 5. Extensiones y Software Adicional en PostgreSQL

### 5.1 Extensiones OBLIGATORIAS

| Extensión | Versión | Propósito | Paquete Oracle Linux/RHEL |
|---|---|---|---|
| **postgis** | 3.4+ | Tipos geometry/geography, funciones ST_*, índices GIST | `postgresql15-postgis34` |
| **pgrouting** | 3.4+ | pgr_drivingDistance, pgr_createTopology (Dijkstra) | `pgrouting_15` |

**Dependencias del SO que se instalan con los paquetes:**

| Librería | Requerida por | Propósito |
|---|---|---|
| GEOS | PostGIS | Motor de operaciones geométricas |
| PROJ | PostGIS | Reproyección entre SRID 4326 ↔ 3857 |
| GDAL | PostGIS | Abstracción de datos geoespaciales |
| Boost C++ | pgRouting | Algoritmos de grafos (Dijkstra) |

**Comandos de instalación (Oracle Linux 8/9):**

```bash
# Repositorio PostgreSQL
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# PostGIS + pgRouting (ajustar número de versión PG)
sudo dnf install -y postgresql15-postgis34 postgresql15-postgis34-utils pgrouting_15

# Activar en cada base de datos
psql -U postgres -d geoapi_prod -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d geoapi_prod -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"
psql -U postgres -d geoapi_qa -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d geoapi_qa -c "CREATE EXTENSION IF NOT EXISTS pgrouting;"

# Verificar
psql -U postgres -d geoapi_prod -c "SELECT PostGIS_Version(), pgr_version();"
```

### 5.2 Funciones PostGIS usadas por la aplicación (auditoría completa)

| Función | Archivo fuente | Propósito |
|---|---|---|
| `ST_SetSRID()` | db_access.py, schema_initialization.sql | Asignar SRID 4326 |
| `ST_MakePoint()` | db_access.py, schema_initialization.sql | Crear puntos desde lon/lat |
| `ST_GeomFromText()` | db_access.py | Parsear WKT a geometry |
| `ST_AsGeoJSON()` | db_access.py, logic_routes.py | Geometry → GeoJSON |
| `ST_DWithin()` | db_access.py, schema_initialization.sql | Búsqueda por radio (metros) |
| `ST_Distance()` | db_access.py, schema_initialization.sql | Distancia entre geometrías |
| `ST_Transform()` | db_access.py, schema_initialization.sql | Reproyectar SRID 4326↔3857 |
| `ST_Length()` | db_access.py, schema_initialization.sql | Longitud de LINESTRING |
| `ST_Collect()` | db_access.py | Agrupar geometrías |
| `ST_LineMerge()` | schema_initialization.sql | MULTILINESTRING → LINESTRING |
| `ST_Union()` | schema_initialization.sql | Unión de geometrías |
| `ST_NPoints()` | schema_initialization.sql | Contar vértices |
| `ST_LineInterpolatePoint()` | schema_initialization.sql | Punto a fracción de línea |
| `ST_EndPoint()` | schema_initialization.sql | Último punto de línea |
| `ST_GeometryN()` | schema_initialization.sql | Extraer componente N |
| `GeometryType()` | schema_initialization.sql | Tipo de geometría |
| `::geography` cast | db_access.py, main.py | Cálculos en metros |
| `USING GIST` | main.py, schema_initialization.sql | Índices espaciales |

### 5.3 Funciones pgRouting usadas

| Función | Endpoint que la consume |
|---|---|
| `pgr_drivingDistance()` | `/api/linea_en_ruta_red`, `/api/nodos_alcanzables_en_ruta_red` |
| `pgr_createTopology()` | Inicialización de red (schema_initialization.sql) |

### 5.4 Extensiones RECOMENDADAS (la app funciona sin ellas)

| Extensión | Propósito | Prioridad |
|---|---|---|
| `pg_stat_statements` | Monitoreo de queries lentas (pgRouting puede llegar a 2s) | Alta |
| `pg_trgm` | Mejora `ILIKE '%cable%'` en `/api/cables_cercanos` | Media |

### 5.5 Extensiones que NO se necesitan

| Extensión | Razón |
|---|---|
| `postgis_topology` | No se usan topologías PostGIS (se usa pgRouting) |
| `postgis_raster` | Solo datos vector (POINT/LINESTRING) |
| `postgis_sfcgal` | No hay geometría 3D |
| `hstore` | Se usa JSONB |
| `pg_cron` | Cron jobs desde el SO |
| `timescaledb` | No hay series temporales |
| `pgvector` | No hay embeddings |

### 5.6 Versión de PostgreSQL requerida

| Requisito | Versión mínima |
|---|---|
| PostGIS 3.x | PostgreSQL 12+ |
| pgRouting 3.4+ | PostgreSQL 12+ |
| JSONB rendimiento óptimo | PostgreSQL 14+ |
| **Recomendada** | **PostgreSQL 14 o 15** |

---

## 6. Objetos de Base de Datos (inventario por DB)

> Estos objetos se crean en **cada** base de datos (QA y PROD) ejecutando `schema_initialization.sql`.

### 6.1 Tablas (8)

| Tabla | Geometría | Columnas propias | Índices |
|---|---|---|---|
| `camaras` | POINT 4326 | 9 base + JSONB (14 props) | PK, GIST(geom), GIST(geom::geography) |
| `cable_corporativo` | LINESTRING 4326 | 9 base + distancia_metros + JSONB (18 props) | PK, GIST(geom), GIST(geom::geography) |
| `centrales` | POINT 4326 | 9 base + JSONB (5 props) | PK, GIST(geom), GIST(geom::geography) |
| `empalmes` | POINT 4326 | 9 base + JSONB (28 props) | PK, GIST(geom), GIST(geom::geography) |
| `reservas` | POINT 4326 | 9 base + JSONB (5 props) | PK, GIST(geom), GIST(geom::geography) |
| `reportes_mal_estado` | POINT 4326 | 9 base + JSONB (6 props) | PK, GIST(geom), GIST(geom::geography) |
| `red` | LINESTRING 4326 | id, cost, reverse_cost, nombre_cable, source, target | PK, GIST(geom) |
| `red_vertices_pgr` | POINT | id, the_geom, cnt, chk | PK, GIST(the_geom) |

### 6.2 Funciones Almacenadas (6)

| Función | Complejidad | Recurso crítico |
|---|---|---|
| `fn_actualizar_updated_at()` | Baja | - |
| `get_nearest_cable(lat, lon, dist)` | Media | CPU (ST_Transform) |
| `get_cables_cercanos_simple(...)` | Media | CPU (ST_DWithin) |
| `get_cables_cercanos(...)` | Media | CPU (ILIKE pattern) |
| `fn_linea_en_ruta_red(...)` | **Alta** | CPU + RAM (Dijkstra + ST_LineMerge) |
| `fn_nodos_alcanzables_en_ruta_red(...)` | **Alta** | CPU + RAM (Dijkstra + CROSS JOIN) |

### 6.3 Triggers (6)

Un trigger `trg_updated_at` (BEFORE UPDATE → `fn_actualizar_updated_at()`) en cada tabla de entidad.

### 6.4 ENUM type

`estadoregistro`: `inicial`, `pendiente`, `aprobado`, `rechazado`

### 6.5 Total de Índices (~20)

- 6 × B-tree (PK automáticos)
- 7 × GIST(geom) — creados por schema_initialization.sql
- 6 × GIST(geom::geography) — creados por main.py en startup
- 1 × GIST(the_geom) en red_vertices_pgr — creado por pgr_createTopology

---

## 7. Configuración SSL para Conexión Backend → DB

El código en `database.py` usa `sslmode="require"`.

| Escenario | Configuración | Recomendado para |
|---|---|---|
| **Alternativa A** (misma LAN) | Puede cambiar a `sslmode="prefer"` o `"disable"` | QA y PROD si la red es aislada |
| **Alternativa A** (redes separadas) | Mantener `sslmode="require"`, configurar SSL en PostgreSQL | PROD |
| **Alternativa B** (Azure↔VPN) | Mantener `sslmode="require"`, el túnel VPN ya cifra | PROD (doble cifrado) |
| **Alternativa B** (PG público) | **Obligatorio** `sslmode="verify-full"` con certificado | Solo QA temporal |

---

## 8. Tabla Resumen Final

### 8.1 Recursos Backend

| Recurso | Alternativa A (Linux Oracle) | Alternativa B (Azure Container Apps) |
|---|---|---|
| **PROD vCPU** | 2 (compartido en servidor) | 1 (Container App) |
| **PROD RAM** | 2 GB | 2 GB |
| **QA vCPU** | 2 (compartido en servidor) | 0.5 (Container App) |
| **QA RAM** | 1 GB | 1 GB |
| **Disco** | 30 GB SSD (servidor) | N/A (serverless) |
| **Servidor Linux** | 4 vCPU / 4 GB / 30 GB total | No aplica |
| **Costo mensual** | **$0** | **$59-199 USD** |

### 8.2 Recursos Base de Datos (igual para ambas alternativas)

| Recurso | DB QA | DB PROD | Total Servidor PG |
|---|---|---|---|
| **vCPU** | 2 | 4 | **6** |
| **RAM** | 4 GB | 8 GB | **12 GB** |
| **Disco SSD** | 50 GB | 100 GB | **150 GB** |
| **IOPS** | 500+ | 1000+ | **1000+** |
| **Extensiones** | postgis + pgrouting | postgis + pgrouting | - |
| **Costo mensual** | **$0** | **$0** | **$0** |

### 8.3 Costo Total Anual

| | Alternativa A | Alternativa B (con VPN) | Alternativa B (sin VPN) |
|---|---|---|---|
| Backend | $0 | $2,388/año | $708/año |
| Base de datos | $0 | $0 | $0 |
| **Total anual** | **$0** | **$2,388 USD** | **$708 USD** |

---

## 9. Checklists de Implementación

### 9.1 Servidor PostgreSQL On-Prem (común)

```
[ ] Verificar versión PostgreSQL (requiere 14+)
[ ] Instalar PostGIS 3.x (paquete + dependencias GEOS, PROJ, GDAL)
[ ] Instalar pgRouting 3.4+ (paquete + dependencia Boost C++)
[ ] Activar pg_stat_statements en postgresql.conf
[ ] Crear base de datos: geoapi_prod
[ ] Crear base de datos: geoapi_qa
[ ] Crear usuario: geoapi_prod_user (GRANT ALL ON geoapi_prod)
[ ] Crear usuario: geoapi_qa_user (GRANT ALL ON geoapi_qa)
[ ] Ejecutar CREATE EXTENSION postgis en cada DB
[ ] Ejecutar CREATE EXTENSION pgrouting en cada DB
[ ] Ejecutar schema_initialization.sql en cada DB
[ ] Aplicar postgresql.conf según ambiente (sección 4.6 y 4.7)
[ ] Configurar pg_hba.conf para IP del backend
[ ] Configurar backups cron (pg_dump diario, retención 7 días)
[ ] Verificar: SELECT PostGIS_Version(), pgr_version();
```

### 9.2 Alternativa A — Servidor Linux Oracle

```
[ ] Instalar Docker Engine 20.10+
[ ] Instalar Docker Compose 2.0+
[ ] Instalar Nginx 1.18+
[ ] Instalar Git 2.30+
[ ] Crear Dockerfile para GeoAPI
[ ] Crear docker-compose.yml (servicios: geoapi-prod, geoapi-qa)
[ ] Crear .env.prod y .env.qa
[ ] Configurar Nginx (reverse proxy + SSL)
[ ] Obtener certificado SSL
[ ] Abrir firewall: 443 inbound, 5432 outbound
[ ] Deploy: docker-compose up -d
[ ] Configurar logrotate
[ ] Configurar health checks (cron)
```

### 9.3 Alternativa B — Azure Container Apps

```
[ ] Crear Resource Group: rg-geoapi
[ ] Crear Azure Container Registry (Basic): acrgeoapi
[ ] Build + push imagen Docker al ACR
[ ] Crear Container Apps Environment
[ ] Configurar VPN Gateway Site-to-Site (si aplica)
[ ] Crear Container App: geoapi-prod (1 vCPU, 2 GB, min=1)
[ ] Crear Container App: geoapi-qa (0.5 vCPU, 1 GB, min=0)
[ ] Configurar variables de entorno (DB_HOST, DB_PORT, etc.)
[ ] Configurar ingress HTTPS para cada app
[ ] Configurar custom domain (opcional)
[ ] Configurar Log Analytics Workspace
[ ] Configurar GitHub Actions para CI/CD (opcional)
[ ] Verificar conectividad Azure → PostgreSQL on-prem (port 5432)
```
