import os
import sys
import subprocess
from pathlib import Path

def create_env_file():
    """Crear archivo .env si no existe"""
    env_path = Path('.env')
    if not env_path.exists():
        env_content = """DB_HOST=54.234.163.140
DB_PORT=5432
DB_NAME=geodb
DB_USER=admin
DB_PASSWORD=adminpostgres2025"""
        env_path.write_text(env_content, encoding='utf-8')
        print("Archivo .env creado\n")

def install_dependencies():
    """Instalar dependencias del proyecto"""
    print("Instalando dependencias...\n")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])

def init_database():
    """Inicializar la base de datos"""
    print("Inicializando la base de datos...")
    subprocess.check_call([sys.executable, "-m", "app.db_init"])

def ejecutar_scripts_sql():
    """Ejecutar scripts SQL en el orden especificado"""
    from dotenv import load_dotenv
    import psycopg2
    
    print("Ejecutando scripts SQL...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener credenciales de la base de datos
    db_host = os.environ.get('DB_HOST', '54.234.163.140')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'geodb')
    db_user = os.environ.get('DB_USER', 'admin')
    db_password = os.environ.get('DB_PASSWORD', 'adminpostgres2025')
    
    # Conectar a la base de datos
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = True
        
        # Lista de scripts SQL en el orden especificado
        sql_scripts = [
            'sql/create_table_red.sql',
            'sql/create_fn_punto_en_ruta_red.sql',
            'sql/create_get_nearest_cable.sql',
            'sql/get_cables_cercanos.sql'
        ]
        
        for script_path in sql_scripts:
            print(f"Ejecutando {script_path}...")
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_path)
            
            try:
                with open(full_path, 'r', encoding='utf-8') as file:
                    sql_script = file.read()
                    
                with conn.cursor() as cursor:
                    cursor.execute(sql_script)
                    
                print(f"Script {script_path} ejecutado correctamente.")
            except Exception as e:
                print(f"Error al ejecutar {script_path}: {str(e)}")
                print("Continuando con el siguiente script...")
        
        conn.close()
        print("Todos los scripts SQL han sido procesados.")
    except Exception as e:
        print(f"Error al conectar a la base de datos: {str(e)}")
        print("No se pudieron ejecutar los scripts SQL.")

def reset_sequences():
    """Ejecuta el script para restablecer las secuencias de la base de datos"""
    print("Actualizando secuencias de las tablas...")
    try:
        subprocess.check_call([sys.executable, "-m", "app.reset_sequences"])
        print("Secuencias actualizadas correctamente.")
    except Exception as e:
        print(f"Error al actualizar secuencias: {str(e)}")
        print("Se recomienda ejecutar 'python -m app.reset_sequences' manualmente.")

def main():
    try:
        create_env_file()
        install_dependencies()
        init_database()
        ejecutar_scripts_sql()
        reset_sequences()  # Aseguramos que las secuencias estén actualizadas
        print("¡Configuración completada exitosamente!")
    except Exception as e:
        print(f"Error durante la configuración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
