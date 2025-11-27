"""
Script para generar una colección Postman a partir del esquema OpenAPI de la API.
"""
import json
import os
import sys
from urllib.parse import urlparse

# Verificar si la biblioteca requests está instalada
try:
    import requests
except ImportError:
    print("\nError: La biblioteca 'requests' no está instalada.")
    print("\nPara instalar la dependencia, ejecuta:")
    print("pip install requests")
    print("\nLuego vuelve a ejecutar este script.")
    sys.exit(1)

def generate_postman_collection(openapi_url, output_file):
    """
    Genera una colección de Postman a partir del esquema OpenAPI.
    
    Args:
        openapi_url: URL del esquema OpenAPI (ej. http://localhost:8000/openapi.json)
        output_file: Ruta donde guardar el archivo de colección
    """
    try:
        print(f"Descargando esquema OpenAPI desde {openapi_url}...")
        response = requests.get(openapi_url)
        response.raise_for_status()
        openapi_spec = response.json()
        
        # Crear una colección de Postman básica
        postman_collection = {
            "info": {
                "name": openapi_spec.get("info", {}).get("title", "GeoAPIs Collection"),
                "description": openapi_spec.get("info", {}).get("description", "Colección generada automáticamente"),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "version": openapi_spec.get("info", {}).get("version", "1.0.0")
            },
            "item": [],
            "auth": {
                "type": "basic",
                "basic": [
                    {
                        "key": "username",
                        "value": "{{username}}",
                        "type": "string"
                    },
                    {
                        "key": "password",
                        "value": "{{password}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "baseUrl",
                    "value": f"{urlparse(openapi_url).scheme}://{urlparse(openapi_url).netloc}",
                    "type": "string"
                },
                {
                    "key": "username",
                    "value": "admin",
                    "type": "string"
                },
                {
                    "key": "password",
                    "value": "password",
                    "type": "string"
                }
            ]
        }
        
        # Organizar por tags
        tags = {}
        
        # Procesar cada endpoint
        for path, path_item in openapi_spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Convertir el path de OpenAPI a formato Postman (variables)
                    postman_path = path
                    for param in operation.get("parameters", []):
                        if param.get("in") == "path":
                            param_name = param.get("name")
                            postman_path = postman_path.replace(f"{{{param_name}}}", f":{param_name}")
                    
                    # Crear el ítem de Postman
                    item = {
                        "name": operation.get("summary", path),
                        "request": {
                            "method": method.upper(),
                            "url": {
                                "raw": f"{{{{baseUrl}}}}{postman_path}",
                                "host": ["{{baseUrl}}"],
                                "path": postman_path.strip("/").split("/"),
                                "query": []
                            },
                            "description": operation.get("description", ""),
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "auth": {
                                "type": "basic",
                                "basic": [
                                    {
                                        "key": "username",
                                        "value": "{{username}}",
                                        "type": "string"
                                    },
                                    {
                                        "key": "password",
                                        "value": "{{password}}",
                                        "type": "string"
                                    }
                                ]
                            }
                        },
                        "response": []
                    }
                    
                    # Añadir parámetros de consulta
                    for param in operation.get("parameters", []):
                        if param.get("in") == "query":
                            param_name = param.get("name")
                            item["request"]["url"]["query"].append({
                                "key": param_name,
                                "value": "",
                                "description": param.get("description", ""),
                                "disabled": not param.get("required", False)
                            })
                    
                    # Añadir cuerpo de la petición si es necesario
                    if method in ["post", "put", "patch"] and "requestBody" in operation:
                        content = operation["requestBody"].get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            if "example" in content["application/json"]:
                                example = content["application/json"]["example"]
                                item["request"]["body"] = {
                                    "mode": "raw",
                                    "raw": json.dumps(example, indent=2),
                                    "options": {
                                        "raw": {
                                            "language": "json"
                                        }
                                    }
                                }
                            elif "$ref" in schema:
                                # Buscar ejemplos en los componentes
                                ref_path = schema["$ref"].split("/")[1:]
                                ref_obj = openapi_spec
                                for path_part in ref_path:
                                    ref_obj = ref_obj.get(path_part, {})
                                
                                # Si hay un ejemplo, usarlo
                                if "example" in ref_obj:
                                    item["request"]["body"] = {
                                        "mode": "raw",
                                        "raw": json.dumps(ref_obj["example"], indent=2),
                                        "options": {
                                            "raw": {
                                                "language": "json"
                                            }
                                        }
                                    }
                    
                    # Organizar por tag
                    operation_tags = operation.get("tags", ["Sin categoría"])
                    for tag in operation_tags:
                        if tag not in tags:
                            tags[tag] = {
                                "name": tag,
                                "item": []
                            }
                        tags[tag]["item"].append(item)
        
        # Añadir todas las carpetas de tags a la colección
        postman_collection["item"] = list(tags.values())
        
        # Guardar la colección
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(postman_collection, f, indent=2)
        
        print(f"Colección de Postman generada en {output_file}")
        return True
    except Exception as e:
        print(f"Error al generar la colección de Postman: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_postman.py <openapi_url> [output_file]")
        sys.exit(1)
    
    openapi_url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "geoapis_postman_collection.json"
    
    generate_postman_collection(openapi_url, output_file)
