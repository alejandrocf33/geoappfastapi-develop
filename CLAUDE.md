# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FastAPI application for geospatial infrastructure management using PostgreSQL/PostGIS. Provides REST APIs for querying and creating network infrastructure elements (cameras, cables, centrals, splices, reserves) with geospatial queries.

## Development Commands

### Server Management
```bash
# Standard startup with hot reload
python run.py

# Open browser automatically to /docs
python run.py --open

# Reset PostgreSQL sequences (after migrations/data imports)
python run.py --reset-sequences

# Generate Postman collection
python run.py --postman

# Production (Railway/container)
uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-5000}
```

### Database Initialization
```bash
# Full setup: creates .env, installs deps, initializes DB, runs SQL scripts
python setup.py

# Only initialize tables (uses SQLAlchemy models)
python -m app.db_init

# Only reset sequences
python -m app.reset_sequences
```

### Testing
```bash
# Interactive API testing
# 1. Start server: python run.py --open
# 2. Use Swagger UI at http://localhost:8000/docs
# 3. Or import examples from pruebas_completas_api.http
```

## Architecture

### Request Flow
```
Client → Middleware (CORS + Origin validation)
      → Routes (cache/logic/write)
      → Auth (HTTP Basic)
      → db_access.py (queries)
      → Database (psycopg2 pool)
      → PostGIS
```

### Key Components

**app/main.py** - FastAPI app, middleware, startup event handlers
- Middleware validates origin via 3 conditions: Oracle Referer pattern OR office IP OR ALLOWED_LOCAL_ORIGIN
- In development (APP_DEBUG=true), middleware only logs, never blocks
- On startup: creates GIST geography indexes on all entity tables

**app/routes/** - Modular route definitions
- `cache_routes.py` - GET endpoints with 6-hour TTLCache (all entities)
- `logic_routes.py` - Spatial analysis endpoints (fault detection, routing)
- `write_routes.py` - POST endpoints for creating entities
- `api_models.py` - Pydantic response models
- `error_models.py` - Standardized error responses

**app/database.py** - Connection pool management
- ThreadedConnectionPool (2-10 connections)
- 15s statement timeout per query
- Context manager auto-returns connections to pool with rollback

**app/db_access.py** - All SQL queries and business logic
- Builds GeoJSON FeatureCollection responses
- Handles WKT geometry or lat/lon coordinates
- Constructs JSONB properties from entity models

**app/models.py** - SQLAlchemy ORM models
- All entities inherit from BaseFeaturesTable: id, propiedades (JSONB), created_at, updated_at, created_by, updated_by, estado (enum), is_initial_load, geom
- EstadoRegistro enum: INICIAL, PENDIENTE, APROBADO, RECHAZADO

**app/auth.py** - HTTP Basic Authentication
- Uses API_USERNAME and API_PASSWORD from .env
- Returns 401 with `{"detail": "Credenciales incorrectas"}` on failure (NOT structured ErrorResponse)

### Cache Strategy
- TTLCache with 6-hour TTL on all GET endpoints
- Invalidation: cache clears automatically after TTL; no manual invalidation on writes
- Keys: simple strings like "all_camaras_cache", "all_cables_corporativos_cache"

## Critical Patterns

### JSONB Property Names
- **Cameras**: use `"type"` (not `"tipo"`) in propiedades JSONB
- **Cables**: use `"id_text"` (not `"id_texto"`) in propiedades JSONB
- **All other entities**: use `"id_texto"`

### Geometry Handling
All POST endpoints accept two formats:
1. Direct coordinates: `latitud` + `longitud` fields
2. WKT geometry: `geometry` field with Well-Known Text (e.g., "POINT(-74.0617 4.6737)")

Output is always GeoJSON with coordinates array: `[longitude, latitude]`

### Authentication
- Format: `Authorization: Basic base64(username:password)`
- 401 response: `{"detail": "Credenciales incorrectas"}` (plain FastAPI HTTPException, NOT ErrorResponse model)

### SQL Deployment
- `setup.py` auto-deploys SQL scripts in `sql/` directory
- **EXCEPTION**: `fn_nodos_alcanzables_en_ruta_red.sql` exists but is NOT auto-deployed
- To add SQL scripts: update `sql_scripts` list in `setup.py:56-62`
- Manual deployment required for route-finding function

### Sequence Management
- After data imports or migrations, sequences may be out of sync
- Symptom: "duplicate key value violates unique constraint" errors
- Fix: `python run.py --reset-sequences`
- Uses `ALTER SEQUENCE ... RESTART WITH` (NOT `setval()`)

## Environment Configuration

Required `.env` variables:
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - PostgreSQL connection
- API_USERNAME, API_PASSWORD - HTTP Basic auth credentials
- APP_DEBUG - Set to "true" for development (disables middleware blocking, enables /docs)
- ALLOWED_LOCAL_ORIGIN - Local dev origin (e.g., "http://localhost:3000")
- ORACLE_REFERER_PATTERN - Regex for Oracle Cloud referer validation
- OFFICE_IP - Allowed office IP for X-Forwarded-For check

## Common Tasks

### Adding a New Entity Type
1. Define SQLAlchemy model in `app/models.py` inheriting from `BaseFeaturesTable`
2. Add Pydantic request/response models in `app/routes/api_models.py`
3. Create CRUD functions in `app/db_access.py` (remember JSONB property names)
4. Add routes in appropriate file (`cache_routes.py` for GET, `write_routes.py` for POST)
5. Run `python -m app.db_init` to create table
6. Update table list in `main.py:149` for geography index creation

### Updating Spatial Queries
- Use `ST_DWithin(geom::geography, point::geography, distance)` for distance queries
- Geography casts enable meter-based queries (vs degrees)
- GIST indexes on `geom::geography` auto-created on startup
- Default timeout: 15s per query (set in database.py connection options)

### Testing Spatial Functions
- SQL test files: `sql/functions_test.sql`, `sql/queries_test.sql`
- Run directly in psql or pgAdmin
- Or use logic endpoints (e.g., `/api/detectar_fallo_en_punto`)

## Documentation Structure
- `docs/api-referencia.md` - Complete endpoint reference (params, models, responses)
- `docs/autenticacion.md` - Auth mechanics + middleware + local development
- `docs/formato-geojson.md` - GeoJSON format, properties per entity type
- `docs/integracion-postman.md` - Postman collection usage
- `docs/manejo-secuencias.md` - Sequence reset guide
- `docs/configuracion.md` - Environment variables

## Known Issues / Gotchas
- Postman collection generator uses placeholder credentials `admin`/`password` - must be updated
- `setup.py` has hardcoded Supabase credentials (security risk)
- Middleware checks 3 conditions - ensure at least one matches in production or requests will be blocked (403)
- In development mode (APP_DEBUG=true), middleware never blocks
