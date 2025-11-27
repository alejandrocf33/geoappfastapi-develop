from fastapi import HTTPException
from .database import get_connection
import psycopg2
import geojson

RADIUS_ERROR_MESSAGE = "El radio interno no puede ser mayor al radio externo"

def get_camaras_from_db(lat=None, lon=None, radio_interno=None, radio_externo=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if lat is not None and lon is not None and radio_interno is not None and radio_externo is not None:
                # Validate that inner radius is not greater than outer radius
                if radio_interno > radio_externo:
                    raise HTTPException(status_code=400, detail=RADIUS_ERROR_MESSAGE)

                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                    FROM camaras
                    WHERE (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado')
                    AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                    AND ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) >= %s;
                """, (lon, lat, lon, lat, radio_externo, lon, lat, radio_interno))
            else:
                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                    FROM camaras
                    WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                            limit 100;
                """)
            
            features = []
            for row in cur.fetchall():
                geom = geojson.loads(row[2])
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                # Add distance if available
                if len(row) > 3:
                    props["distancia"] = row[3]
                
                feature = geojson.Feature(geometry=geom, properties=props)
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_all_camaras_from_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                FROM camaras
                WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
            """)
            features = []
            for row in cur.fetchall():
                geom = geojson.loads(row[2])
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                
                feature = geojson.Feature(geometry=geom, properties=props)
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_camaras_en_falla_db(lon, lat, distancia, desviacion, camaras_en_radio_ids):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                FROM camaras
                WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                AND (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado');
                """,
                (lon, lat, lon, lat, distancia)
            )
            camaras_en_radio = []
            for row in cur.fetchall():
                geom = geojson.loads(row[2])
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID and distance
                props["id"] = row[0]
                props["distancia"] = row[3]
                
                feature = geojson.Feature(geometry=geom, properties=props)
                camaras_en_radio.append(feature)
                camaras_en_radio_ids.add(row[0])

            camaras_cercanas = []
            if camaras_en_radio_ids:
                cur.execute(
                    """
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                    FROM camaras
                    WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s + %s)
                      AND id NOT IN %s
                      AND (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado');
                    """,
                    (lon, lat, lon, lat, distancia, desviacion, tuple(camaras_en_radio_ids))
                )
                for row in cur.fetchall():
                    geom = geojson.loads(row[2])
                    # Get properties from JSONB, if null use empty dict
                    props = row[1] if row[1] is not None else {}
                    # Add ID and distance
                    props["id"] = row[0]
                    props["distancia"] = row[3]
                    
                    feature = geojson.Feature(geometry=geom, properties=props)
                    camaras_cercanas.append(feature)
            else:
                cur.execute(
                    """
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                    FROM camaras
                    WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s + %s)
                    AND (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado');
                    """,
                    (lon, lat, lon, lat, distancia, desviacion)
                )
                for row in cur.fetchall():
                    geom = geojson.loads(row[2])
                    # Get properties from JSONB, if null use empty dict  
                    props = row[1] if row[1] is not None else {}
                    # Add ID and distance
                    props["id"] = row[0]
                    props["distancia"] = row[3]
                    
                    feature = geojson.Feature(geometry=geom, properties=props)
                    camaras_cercanas.append(feature)
            
    return camaras_en_radio, camaras_cercanas

def insertar_camara_db(camara, username="sistema"):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Convert properties to JSONB
                props = {
                    "type": camara.type,
                    "apertura": camara.apertura,
                    "id_texto": camara.id_texto,
                    "ubicacion": camara.ubicacion,
                    "constructi": camara.constructi,
                    "estado_cam": camara.estado_cam,
                    "nombre_esp": camara.nombre_esp, 
                    "propietari": camara.propietari,
                    "cÓdigo_etb": camara.codigo_etb
                }
                
                # Si se proporciona geometry directamente, usarlo
                # Si no, construir el punto a partir de longitud/latitud
                if camara.geometry:
                    wkt_geometry = camara.geometry
                else:
                    wkt_geometry = f"POINT({camara.longitud} {camara.latitud})"

                # Convertir el diccionario props a JSON string para evitar el error "can't adapt type 'dict'"
                import json
                props_json = json.dumps(props)

                # Verificar si ya existe alguna cámara con estas coordenadas o id_texto para evitar duplicados
                if camara.id_texto:
                    cur.execute(
                        "SELECT id FROM camaras WHERE propiedades->>'id_texto' = %s",
                        (camara.id_texto,)
                    )
                    existing = cur.fetchone()
                    if existing:
                        raise HTTPException(
                            status_code=409, 
                            detail=f"Ya existe una cámara con id_texto '{camara.id_texto}'"
                        )
                
                # Usamos la secuencia de la tabla para generar el ID automáticamente
                cur.execute(
                    """
                    INSERT INTO camaras (geom, propiedades, created_by, updated_by, estado, is_initial_load)
                    VALUES (ST_GeomFromText(%s, 4326), %s::jsonb, %s, %s, 'pendiente', false)
                    RETURNING id
                    """,
                    (wkt_geometry, props_json, username, username)
                )
                
                # Obtener el ID generado
                generated_id = cur.fetchone()[0]
                
                # Actualizar las propiedades con el objectid igual al id generado
                props["objectid"] = generated_id
                props_json = json.dumps(props)
                
                # Actualizar el registro con las propiedades actualizadas
                cur.execute(
                    """
                    UPDATE camaras 
                    SET propiedades = %s::jsonb 
                    WHERE id = %s
                    """,
                    (props_json, generated_id)
                )
                
                conn.commit()
                
        return {
            "message": "Cámara insertada correctamente", 
            "id": generated_id, 
            "objectid": generated_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def insertar_cable_corporativo_db(cable, username="sistema"):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Convert properties to JSONB
                props = {
                    "id_text": cable.id_texto,
                    "name": cable.name,
                    "nombre_ant": cable.nombre_ant,
                    "nombre_esp": cable.nombre_esp, 
                    "colocacion": cable.colocacion,
                    "constructi": cable.constructi,
                    "perdida_db": cable.perdida_db,
                    "contratist": cable.contratist,
                    "segmento": cable.segmento,
                    "pr": cable.pr,
                    "calculat1": cable.calculat1,
                    "calculat2": cable.calculat2,
                    "calculated": cable.calculated,
                    "id_especif": cable.id_especificacion,
                    "measured_l": cable.measured_l
                }
                
                # Si se proporciona geometry directamente, usarlo
                # Si no, construir el linestring a partir de los puntos
                if cable.geometry:
                    wkt_geometry = cable.geometry
                else:
                    if len(cable.puntos) < 2:
                        raise HTTPException(status_code=400, detail="Se requieren al menos 2 puntos para crear un cable (linestring)")
                    
                    # Construir el WKT para un LINESTRING
                    coords = []
                    for punto in cable.puntos:
                        coords.append(f"{punto.longitud} {punto.latitud}")
                    
                    wkt_geometry = f"LINESTRING({', '.join(coords)})"                # Convertir el diccionario props a JSON string
                import json
                props_json = json.dumps(props)

                cur.execute(
                    """
                    INSERT INTO cable_corporativo (geom, propiedades, created_by, updated_by, estado, distancia_metros, is_initial_load)
                    VALUES (
                        ST_GeomFromText(%s, 4326), 
                        %s::jsonb, 
                        %s, 
                        %s, 
                        'pendiente',
                        ST_Length(ST_Transform(ST_GeomFromText(%s, 4326), 3857))::float,
                        false
                    )
                    RETURNING id
                    """,
                    (wkt_geometry, props_json, username, username, wkt_geometry)
                )
                  # Obtener el ID generado
                generated_id = cur.fetchone()[0]
                
                # Consultar el valor de distancia_metros calculado
                cur.execute(
                    """
                    SELECT distancia_metros 
                    FROM cable_corporativo 
                    WHERE id = %s
                    """,
                    (generated_id,)
                )
                distancia_metros = cur.fetchone()[0]
                
                # Actualizar las propiedades con el objectid igual al id generado y shape_length
                props["objectid"] = generated_id
                props["shape_length"] = distancia_metros
                props_json = json.dumps(props)
                
                # Actualizar el registro con las propiedades actualizadas
                cur.execute(
                    """
                    UPDATE cable_corporativo 
                    SET propiedades = %s::jsonb 
                    WHERE id = %s
                    """,
                    (props_json, generated_id)
                )
                
                conn.commit()
                
        return {
            "message": "Cable corporativo insertado correctamente",
            "id": generated_id,
            "objectid": generated_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def insertar_central_db(central, username="sistema"):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Convert properties to JSONB
                props = {
                    "id_texto": central.id_texto,
                    "nombre": central.nombre,
                    "codigo": central.codigo,
                    "direccion": central.direccion,
                    "tipo": central.tipo
                }
                
                # Si se proporciona geometry directamente, usarlo
                # Si no, construir el punto a partir de longitud/latitud
                if central.geometry:
                    wkt_geometry = central.geometry
                else:
                    wkt_geometry = f"POINT({central.longitud} {central.latitud})"

                # Convertir el diccionario props a JSON string
                import json
                props_json = json.dumps(props)

                cur.execute(
                    """
                    INSERT INTO centrales (geom, propiedades, created_by, updated_by, estado, is_initial_load)
                    VALUES (ST_GeomFromText(%s, 4326), %s::jsonb, %s, %s, 'pendiente', false)
                    RETURNING id
                    """,
                    (wkt_geometry, props_json, username, username)
                )
                
                # Obtener el ID generado
                generated_id = cur.fetchone()[0]
                conn.commit()
                
        return {
            "message": "Central insertada correctamente",
            "id": generated_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def insertar_empalme_db(empalme, username="sistema"):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Convert properties to JSONB
                props = {
                    "id_texto": empalme.id_texto,
                    "name": empalme.name,
                    "type": empalme.type,
                    "x": empalme.x,
                    "y": empalme.y,
                    "sangria_": empalme.sangria,
                    "segmento": empalme.segmento,
                    "location_x": empalme.location_x,
                    "location_y": empalme.location_y,
                    "propietario": empalme.propietario,
                    "splice_type": empalme.splice_type,
                    "count_mayorista": empalme.count_mayorista,
                    "mayorista_gather": empalme.mayorista_gather,
                    "symbol_annotation": empalme.symbol_annotation,
                    "symbol_location_x": empalme.symbol_location_x,
                    "symbol_location_y": empalme.symbol_location_y,
                    "id_especificación": empalme.id_specification,
                    "construction_status": empalme.construction_status,
                    "nombre_especificación": empalme.nombre_especificacion,
                    "ubicación_empalmes_camara_x": empalme.ubicacion_empalmes_camara_x,
                    "ubicación_empalmes_camara_y": empalme.ubicacion_empalmes_camara_y,
                    "ubicación_empalmes_postes_x": empalme.ubicacion_empalmes_postes_x,
                    "ubicación_empalmes_postes_y": empalme.ubicacion_empalmes_postes_y,
                    "ubicación_empalmes_edificio_x": empalme.ubicacion_empalmes_edificio_x,
                    "ubicación_empalmes_edificio_y": empalme.ubicacion_empalmes_edificio_y,
                    "ubicación_empalmes_punto_de_acceso_x": empalme.ubicacion_empalmes_punto_de_acceso_x,
                    "ubicación_empalmes_punto_de_acceso_y": empalme.ubicacion_empalmes_punto_de_acceso_y
                }
                
                # Si se proporciona geometry directamente, usarlo
                # Si no, construir el punto a partir de longitud/latitud
                if empalme.geometry:
                    wkt_geometry = empalme.geometry
                else:
                    wkt_geometry = f"POINT({empalme.longitud} {empalme.latitud})"

                # Convertir el diccionario props a JSON string
                import json
                props_json = json.dumps(props)

                # Verificar si ya existe algun empalme con estas coordenadas o id_texto para evitar duplicados
                if empalme.id_texto:
                    cur.execute(
                        "SELECT id FROM empalmes WHERE propiedades->>'id_texto' = %s",
                        (empalme.id_texto,)
                    )
                    existing = cur.fetchone()
                    if existing:
                        raise HTTPException(
                            status_code=409, 
                            detail=f"Ya existe un empalme con id_texto '{empalme.id_texto}'"
                        )

                cur.execute(
                    """
                    INSERT INTO empalmes (geom, propiedades, created_by, updated_by, estado, is_initial_load)
                    VALUES (ST_GeomFromText(%s, 4326), %s::jsonb, %s, %s, 'pendiente', false)
                    RETURNING id
                    """,
                    (wkt_geometry, props_json, username, username)
                )
                
                # Obtener el ID generado
                generated_id = cur.fetchone()[0]
                
                # Actualizar las propiedades con el objectid igual al id generado
                props["objectid"] = generated_id
                props_json = json.dumps(props)
                
                # Actualizar el registro con las propiedades actualizadas
                cur.execute(
                    """
                    UPDATE empalmes 
                    SET propiedades = %s::jsonb 
                    WHERE id = %s
                    """,
                    (props_json, generated_id)
                )
                
                conn.commit()
        return {
            "message": "Empalme insertado correctamente",
            "id": generated_id,
            "objectid": generated_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def insertar_reserva_db(reserva, username="sistema"):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Convert properties to JSONB
                props = {
                    "id_texto": reserva.id_texto,
                    "nombre": reserva.nombre,
                    "tipo": reserva.tipo,
                    "capacidad": reserva.capacidad,
                    "ubicacion": reserva.ubicacion
                }
                
                # Si se proporciona geometry directamente, usarlo
                # Si no, construir el punto a partir de longitud/latitud
                if reserva.geometry:
                    wkt_geometry = reserva.geometry
                else:
                    wkt_geometry = f"POINT({reserva.longitud} {reserva.latitud})"

                # Convertir el diccionario props a JSON string
                import json
                props_json = json.dumps(props)

                cur.execute(
                    """
                    INSERT INTO reservas (geom, propiedades, created_by, updated_by, estado, is_initial_load)
                    VALUES (ST_GeomFromText(%s, 4326), %s::jsonb, %s, %s, 'pendiente', false)
                    RETURNING id
                    """,
                    (wkt_geometry, props_json, username, username)
                )
                
                # Obtener el ID generado
                generated_id = cur.fetchone()[0]
                conn.commit()
                
        return {
            "message": "Reserva insertada correctamente",
            "id": generated_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_cables_corporativos_from_db(lat=None, lon=None, radio_interno=None, radio_externo=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if lat is not None and lon is not None and radio_interno is not None and radio_externo is not None:
                # Validate that inner radius is not greater than outer radius
                if radio_interno > radio_externo:
                    raise HTTPException(status_code=400, detail=RADIUS_ERROR_MESSAGE)# Para LineStrings, necesitamos verificar si algún punto del cable está dentro de los radios
                cur.execute("""
                    WITH puntos_cable AS (
                        SELECT id, 
                               propiedades, 
                               geom,
                               (ST_DumpPoints(geom)).geom as punto,
                               distancia_metros
                        FROM cable_corporativo
                        WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                    )
                    SELECT DISTINCT ON (id) 
                           id, 
                           propiedades, 
                           ST_AsGeoJSON(geom) as geometry,
                           distancia_metros,
                           LEAST(
                               MIN(ST_Distance(punto::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)) 
                               OVER (PARTITION BY id)
                           ) as distancia_al_punto
                    FROM puntos_cable
                    WHERE EXISTS (
                        SELECT 1 
                        FROM puntos_cable pc2 
                        WHERE pc2.id = puntos_cable.id
                        AND ST_DWithin(pc2.punto::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                        AND ST_Distance(pc2.punto::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) >= %s
                    );
                """, (lon, lat, lon, lat, radio_externo, lon, lat, radio_interno))
            else:
                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry, distancia_metros
                    FROM cable_corporativo
                    WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                    LIMIT 100;
                """)
            
            features = []
            for row in cur.fetchall():
                geom = geojson.loads(row[2])
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID and distances
                props["id"] = row[0]
                props["distancia_metros"] = row[3]
                if len(row) > 4:
                    props["distancia_al_punto"] = row[4]
                
                feature = geojson.Feature(geometry=geom, properties=props)
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_all_cables_corporativos_from_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH props_grouped AS (
                    SELECT 
                        propiedades,
                        array_agg(id) as ids,
                        ST_AsGeoJSON(ST_Collect(geom)) as geometry,
                        SUM(distancia_metros) as distancia_total,
                        COUNT(*) as cantidad_tramos
                    FROM cable_corporativo
                    WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                    GROUP BY propiedades
                )
                SELECT 
                    propiedades,
                    geometry,
                    ids,
                    distancia_total,
                    cantidad_tramos
                FROM props_grouped;
            """)
            features = []
            for row in cur.fetchall():
                geom = geojson.loads(row[1])
                # Get properties from JSONB, if null use empty dict
                props = row[0] if row[0] is not None else {}
                # Add additional information
                props["ids"] = row[2]
                props["distancia_total"] = row[3]
                props["cantidad_tramos"] = row[4]
                
                feature = geojson.Feature(geometry=geom, properties=props)
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_centrales_from_db(lat=None, lon=None, radio_interno=None, radio_externo=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if lat is not None and lon is not None and radio_interno is not None and radio_externo is not None:
                # Validate that inner radius is not greater than outer radius
                if radio_interno > radio_externo:
                    raise HTTPException(status_code=400, detail=RADIUS_ERROR_MESSAGE)

                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                    FROM centrales
                    WHERE (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado')
                    AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                    AND ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) >= %s;
                """, (lon, lat, lon, lat, radio_externo, lon, lat, radio_interno))
            else:
                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                    FROM centrales
                    WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                    LIMIT 100;
                """)
            
            features = []
            for row in cur.fetchall():
                geom_json = row[2]
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                # Add distance if available
                if len(row) > 3:
                    props["distancia"] = row[3]
                
                feature = geojson.Feature(
                    geometry=geojson.loads(geom_json), 
                    properties=props
                )
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_all_centrales_from_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                FROM centrales
                WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
            """)
            features = []
            for row in cur.fetchall():
                geom_json = row[2]
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                
                feature = geojson.Feature(
                    geometry=geojson.loads(geom_json), 
                    properties=props
                )
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_empalmes_from_db(lat=None, lon=None, radio_interno=None, radio_externo=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if lat is not None and lon is not None and radio_interno is not None and radio_externo is not None:
                # Validate that inner radius is not greater than outer radius
                if radio_interno > radio_externo:
                    raise HTTPException(status_code=400, detail=RADIUS_ERROR_MESSAGE)

                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                    FROM empalmes
                    WHERE (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado')
                    AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                    AND ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) >= %s;
                """, (lon, lat, lon, lat, radio_externo, lon, lat, radio_interno))
            else:
                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                    FROM empalmes
                    WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                    LIMIT 100;
                """)
            
            features = []
            for row in cur.fetchall():
                geom_json = row[2]
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                # Add distance if available
                if len(row) > 3:
                    props["distancia"] = row[3]
                
                feature = geojson.Feature(
                    geometry=geojson.loads(geom_json), 
                    properties=props
                )
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_all_empalmes_from_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                FROM empalmes
                WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
            """)
            features = []
            for row in cur.fetchall():
                geom_json = row[2]
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                
                feature = geojson.Feature(
                    geometry=geojson.loads(geom_json), 
                    properties=props
                )
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_reservas_from_db(lat=None, lon=None, radio_interno=None, radio_externo=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if lat is not None and lon is not None and radio_interno is not None and radio_externo is not None:
                # Validate that inner radius is not greater than outer radius
                if radio_interno > radio_externo:
                    raise HTTPException(status_code=400, detail=RADIUS_ERROR_MESSAGE)

                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry,
                           ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distancia
                    FROM reservas
                    WHERE (estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado')
                    AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                    AND ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) >= %s;
                """, (lon, lat, lon, lat, radio_externo, lon, lat, radio_interno))
            else:
                cur.execute("""
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                    FROM reservas
                    WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
                    LIMIT 100;
                """)
            
            features = []
            for row in cur.fetchall():
                geom_json = row[2]
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                # Add distance if available
                if len(row) > 3:
                    props["distancia"] = row[3]
                
                feature = geojson.Feature(
                    geometry=geojson.loads(geom_json), 
                    properties=props
                )
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_all_reservas_from_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry
                FROM reservas
                WHERE estado != 'pendiente' OR estado IS NULL OR estado != 'rechazado'
            """)
            features = []
            for row in cur.fetchall():
                geom_json = row[2]
                # Get properties from JSONB, if null use empty dict
                props = row[1] if row[1] is not None else {}
                # Add ID from the table
                props["id"] = row[0]
                
                feature = geojson.Feature(
                    geometry=geojson.loads(geom_json), 
                    properties=props
                )
                features.append(feature)
            return geojson.FeatureCollection(features)

def get_cables_cercanos_from_db(lon=None, lat=None, distancia=None, limite=100, incluir_troncales=False, nombre_cable=None, busqueda_exacta=True):
    """
    Obtiene cables cercanos a un punto usando la función SQL get_cables_cercanos o get_cables_cercanos_simple,
    según si se filtra por nombre de cable o no.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if nombre_cable:
                cur.execute(
                    """
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry, distancia_metros_calculada
                    FROM get_cables_cercanos(%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        lon,
                        lat,
                        distancia,
                        limite,
                        incluir_troncales,
                        nombre_cable,
                        busqueda_exacta
                    )
                )
            else:
                cur.execute(
                    """
                    SELECT id, propiedades, ST_AsGeoJSON(geom) as geometry, distancia_metros_calculada
                    FROM get_cables_cercanos_simple(%s, %s, %s, %s, %s)
                    """,
                    (
                        lon,
                        lat,
                        distancia,
                        limite,
                        incluir_troncales
                    )
                )
            features = []
            for row in cur.fetchall():
                geom = geojson.loads(row[2])
                props = row[1] if row[1] is not None else {}
                props["id"] = row[0]
                if len(row) > 3:
                    props["distancia_metros"] = row[3]
                feature = geojson.Feature(geometry=geom, properties=props)
                features.append(feature)
            return geojson.FeatureCollection(features)