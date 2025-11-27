import psycopg2
from . import config

def get_connection():
    """Obtiene una conexión a la base de datos usando la configuración centralizada"""
    try:
        return psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
    except psycopg2.Error as e:
        raise Exception(f"Error al conectar a la base de datos: {str(e)}")

def execute_query(query, params=None):
    """Ejecuta una consulta SELECT que devuelve múltiples filas"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()

def execute_single_query(query, params=None):
    """Ejecuta una consulta SELECT que devuelve una sola fila"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()

def execute_write_query(query, params=None):
    """Ejecuta una consulta INSERT/UPDATE/DELETE"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()
            return True
