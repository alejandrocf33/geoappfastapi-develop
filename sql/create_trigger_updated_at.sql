-- Trigger function para actualizar automáticamente updated_at en cualquier UPDATE.
-- Necesario porque las escrituras usan psycopg2 (SQL crudo) en lugar del ORM de SQLAlchemy,
-- por lo que el "onupdate=func.now()" definido en models.py no se ejecuta.

CREATE OR REPLACE FUNCTION fn_actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar el trigger a todas las tablas con updated_at
DO $$
DECLARE
    tabla TEXT;
    tablas TEXT[] := ARRAY['camaras', 'cable_corporativo', 'centrales', 'empalmes', 'reservas', 'reportes_mal_estado'];
BEGIN
    FOREACH tabla IN ARRAY tablas LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_updated_at ON %I', tabla
        );
        EXECUTE format(
            'CREATE TRIGGER trg_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW
             EXECUTE FUNCTION fn_actualizar_updated_at()',
            tabla
        );
        RAISE NOTICE 'Trigger trg_updated_at creado en tabla %', tabla;
    END LOOP;
END;
$$;
