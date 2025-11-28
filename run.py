import uvicorn
import os
import sys
import webbrowser
import subprocess
from time import sleep
from threading import Thread
from app import config

def open_browser():
    """Abre el navegador con la documentación después de 2 segundos"""
    sleep(2)
    webbrowser.open("http://localhost:8000/docs")

def generate_postman_collection():
    """Genera una colección de Postman a partir del esquema OpenAPI"""
    try:
        print("\nGenerando colección de Postman...")
        
        # Verificar primero si está instalado requests
        try:
            import importlib
            importlib.import_module('requests')
        except ImportError:
            print("La biblioteca 'requests' no está instalada. Intentando instalar...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
                print("La biblioteca 'requests' se ha instalado correctamente.")
            except subprocess.SubprocessError:
                print("Error al instalar la biblioteca 'requests'.")
                print("Por favor, instálala manualmente ejecutando: pip install requests")
                return
        
        # Ejecutar el script para generar la colección
        result = subprocess.run([
            sys.executable, 
            "generate_postman.py", 
            "http://localhost:8000/openapi.json", 
            "geoapis_postman_collection.json"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("¡Colección generada con éxito!")
        else:
            print(f"Error al generar la colección de Postman:")
            print(result.stderr)
    except Exception as e:
        print(f"Error al generar la colección de Postman: {str(e)}")

def reset_database_sequences():
    """Restablece las secuencias de la base de datos para evitar conflictos de ID"""
    try:
        print("\nRestableciendo secuencias de la base de datos...")
        
        result = subprocess.run([
            sys.executable, 
            "-m", 
            "app.reset_sequences"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("¡Secuencias restablecidas con éxito!")
        else:
            print(f"Error al restablecer secuencias:")
            print(result.stderr)
    except Exception as e:
        print(f"Error al restablecer secuencias: {str(e)}")

if __name__ == "__main__":
    # Procesar argumentos
    open_browser_flag = "--open" in sys.argv
    generate_postman_flag = "--postman" in sys.argv
    reset_sequences_flag = "--reset-sequences" in sys.argv
    
    print("\n" + "="*80)
    print(" "*30 + "GeoAPIs Server" + " "*30)
    print("="*80)
    print("\nIniciando servidor GeoAPIs...")
    print("\nDocumentación disponible en:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - OpenAPI JSON: http://localhost:8000/openapi.json")
    print("\nBase de datos conectada:")
    print(f"  Host: {config.DB_HOST}")
    print(f"  Puerto: {config.DB_PORT}")
    print(f"  Nombre: {config.DB_NAME}")
    print(f"  Usuario: {config.DB_USER}")
    print("\nArchivos de documentación adicional:")
    print("  - README.md: Documentación general")
    print("  - AUTH.md: Instrucciones de autenticación")
    print("  - GEOJSON.md: Formato de respuestas GeoJSON")
    print("\nEjemplos de consultas en:")
    print("  - pruebas_completas_api.http")
    print("\nImportación a Postman:")
    print("  1. Opción A - Importar directamente desde la URL:")
    print("     - En Postman: Import > Link > http://localhost:8000/openapi.json")
    print("  2. Opción B - Generar y usar archivo de colección:")
    print("     - Ejecutar: python generate_postman.py http://localhost:8000/openapi.json")
    print("     - En Postman: Import > File > Seleccionar geoapis_postman_collection.json")
    
    print("\nArgumentos disponibles:")
    print("  --open: Abrir automáticamente el navegador al iniciar")
    print("  --postman: Generar automáticamente colección de Postman")
    print("  --reset-sequences: Restablecer secuencias de la base de datos")
      # Si se pasa el argumento --postman, generar la colección automáticamente
    if generate_postman_flag:
        # Esperar a que el servidor esté en marcha antes de generar la colección
        server_thread = Thread(target=lambda: sleep(5) and generate_postman_collection())
        server_thread.daemon = True
        server_thread.start()
    
    # Si se pasa el argumento --reset-sequences, restablecer las secuencias antes de iniciar
    if reset_sequences_flag:
        reset_database_sequences()
    
    # Si se pasa el argumento --open, abrir el navegador automáticamente
    if open_browser_flag:
        browser_thread = Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    print("\nPresiona CTRL+C para detener el servidor\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
