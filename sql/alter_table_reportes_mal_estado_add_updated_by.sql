-- Migración: Agregar columna updated_by a tabla reportes_mal_estado
-- Fecha: 2026-02-20
-- Razón: Alinear esquema de tabla con el modelo Python (BaseFeaturesTable)

-- Verificar si la columna ya existe antes de agregarla
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'reportes_mal_estado'
        AND column_name = 'updated_by'
    ) THEN
        ALTER TABLE reportes_mal_estado
        ADD COLUMN updated_by VARCHAR(255);

        RAISE NOTICE 'Columna updated_by agregada exitosamente a reportes_mal_estado';
    ELSE
        RAISE NOTICE 'La columna updated_by ya existe en reportes_mal_estado';
    END IF;
END $$;

-- Comentario descriptivo para la columna
COMMENT ON COLUMN reportes_mal_estado.updated_by IS 'Usuario que actualizó el registro por última vez';
