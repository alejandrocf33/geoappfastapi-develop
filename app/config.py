from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Credenciales de autenticación para la API
API_USERNAME = os.getenv("API_USERNAME", "u7Qw9z!2pL4vXr6s")
API_PASSWORD = os.getenv("API_PASSWORD", "A3$k8z!mQ2@vXr7pL4w9Zb6sT1#nJ5eR")

# Origen local permitido para desarrollo (desactivar en producción dejando vacío)
ALLOWED_LOCAL_ORIGIN = os.getenv("ALLOWED_LOCAL_ORIGIN", "")

# Modo debug de la aplicación (True en desarrollo/QA, False en producción)
APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

# IP de la oficina permitida para acceso directo (X-Forwarded-For)
OFFICE_IP = os.getenv("OFFICE_IP", "")

# Patrón regex del referer de Oracle Cloud (interoperabilidad con ETA/Oracle)
ORACLE_REFERER_PATTERN = os.getenv(
    "ORACLE_REFERER_PATTERN",
    r"^https://plugins-[^/]+(\.[^/]+)*\.fs\.ocs\.oraclecloud\.com/"
)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"