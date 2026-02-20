-- Migración completa: Alinear tabla reportes_mal_estado con BaseFeaturesTable
-- Fecha: 2026-02-20
-- Razón: La tabla fue creada sin todas las columnas del modelo base
-- 0. Crear tipo enum estadoregistro si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM pg_type
    WHERE typname = 'estadoregistro'
) THEN CREATE TYPE estadoregistro AS ENUM ('inicial', 'pendiente', 'aprobado', 'rechazado');
RAISE NOTICE 'Tipo estadoregistro creado exitosamente';
ELSE RAISE NOTICE 'El tipo estadoregistro ya existe';
END IF;
END $$;
-- 1. Agregar columna 'created_at' si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'created_at'
) THEN
ALTER TABLE reportes_mal_estado
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
RAISE NOTICE 'Columna created_at agregada exitosamente';
ELSE RAISE NOTICE 'La columna created_at ya existe';
END IF;
-- Asegurar que sea TIMESTAMP WITH TIME ZONE
ALTER TABLE reportes_mal_estado
ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';
END $$;
-- 2. Agregar columna 'updated_at' si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'updated_at'
) THEN
ALTER TABLE reportes_mal_estado
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
RAISE NOTICE 'Columna updated_at agregada exitosamente';
ELSE RAISE NOTICE 'La columna updated_at ya existe';
END IF;
END $$;
-- 3. Agregar columna 'estado' si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'estado'
) THEN
ALTER TABLE reportes_mal_estado
ADD COLUMN estado estadoregistro DEFAULT 'pendiente';
RAISE NOTICE 'Columna estado agregada exitosamente';
ELSE RAISE NOTICE 'La columna estado ya existe';
END IF;
END $$;
-- 4. Agregar columna 'updated_by' si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'updated_by'
) THEN
ALTER TABLE reportes_mal_estado
ADD COLUMN updated_by VARCHAR(255);
RAISE NOTICE 'Columna updated_by agregada exitosamente';
ELSE RAISE NOTICE 'La columna updated_by ya existe';
END IF;
END $$;
-- 5. Agregar columna 'created_by' si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'created_by'
) THEN
ALTER TABLE reportes_mal_estado
ADD COLUMN created_by VARCHAR(255);
-- Actualizar registros existentes con valor por defecto
UPDATE reportes_mal_estado
SET created_by = 'sistema'
WHERE created_by IS NULL;
RAISE NOTICE 'Columna created_by agregada exitosamente';
ELSE RAISE NOTICE 'La columna created_by ya existe';
END IF;
END $$;
-- 6. Agregar columna 'is_initial_load' si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'is_initial_load'
) THEN
ALTER TABLE reportes_mal_estado
ADD COLUMN is_initial_load BOOLEAN DEFAULT false;
RAISE NOTICE 'Columna is_initial_load agregada exitosamente';
ELSE RAISE NOTICE 'La columna is_initial_load ya existe';
END IF;
END $$;
-- 7. Crear índice GIST para consultas espaciales si no existe
CREATE INDEX IF NOT EXISTS idx_reportes_mal_estado_geom_geography ON reportes_mal_estado USING GIST ((geom::geography));
-- 7.5. Crear función update_updated_at_column si no existe
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ language 'plpgsql';
-- 8. Agregar trigger para updated_at si no existe
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM pg_trigger
    WHERE tgname = 'update_reportes_mal_estado_updated_at'
) THEN CREATE TRIGGER update_reportes_mal_estado_updated_at BEFORE
UPDATE ON reportes_mal_estado FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
RAISE NOTICE 'Trigger para updated_at creado exitosamente';
ELSE RAISE NOTICE 'El trigger para updated_at ya existe';
END IF;
END $$;
-- Comentarios descriptivos
COMMENT ON COLUMN reportes_mal_estado.created_at IS 'Fecha y hora de creación del registro';
COMMENT ON COLUMN reportes_mal_estado.updated_at IS 'Fecha y hora de la última actualización del registro';
COMMENT ON COLUMN reportes_mal_estado.estado IS 'Estado del registro: inicial, pendiente, aprobado, rechazado';
COMMENT ON COLUMN reportes_mal_estado.updated_by IS 'Usuario que actualizó el registro por última vez';
COMMENT ON COLUMN reportes_mal_estado.created_by IS 'Usuario que creó el registro';
COMMENT ON COLUMN reportes_mal_estado.is_initial_load IS 'Indica si el registro proviene de carga masiva inicial';
-- Verificación final
SELECT 'Estructura de reportes_mal_estado:' as info;
SELECT column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'reportes_mal_estado'
ORDER BY ordinal_position;