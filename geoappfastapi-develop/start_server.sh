#!/bin/bash

# Instrucciones para iniciar el servidor GeoAPIs

# Iniciar normalmente
python run.py

# Iniciar y abrir el navegador automáticamente con la documentación Swagger
python run.py --open

# Iniciar y generar automáticamente la colección para Postman
python run.py --postman

# Iniciar con ambas opciones
python run.py --open --postman
