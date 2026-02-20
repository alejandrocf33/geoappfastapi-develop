import psycopg2
from psycopg2 import pool
from . import config

# Pool de conexiones: mínimo 2, máximo 10 conexiones reutilizables
_connection_pool = None

def _get_pool():
    global _connection_pool
    if _connection_pool is None or _connection_pool.closed:
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            sslmode="require",
            options="-c statement_timeout=15000"  # 15s timeout por query
        )
    return _connection_pool

class PooledConnection:
    """Context manager que devuelve la conexión al pool al salir."""
    def __init__(self):
        self._conn = None

    def __enter__(self):
        self._conn = _get_pool().getconn()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            if exc_type:
                self._conn.rollback()
            _get_pool().putconn(self._conn)
        return False

def get_connection():
    """Obtiene una conexión del pool de conexiones."""
    return PooledConnection()

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
