from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "54.234.163.140")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "geodb")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "adminpostgres2025")

# Credenciales de autenticación para la API
API_USERNAME = os.getenv("API_USERNAME", "u7Qw9z!2pL4vXr6s")
API_PASSWORD = os.getenv("API_PASSWORD", "A3$k8z!mQ2@vXr7pL4w9Zb6sT1#nJ5eR")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"