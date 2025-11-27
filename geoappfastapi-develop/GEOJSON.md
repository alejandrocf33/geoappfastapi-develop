# Formato GeoJSON en GeoAPIs

Este documento explica el formato de respuesta GeoJSON utilizado en las APIs de consulta geoespacial.

## Formato GeoJSON

GeoJSON es un formato estándar abierto diseñado para representar entidades geográficas simples, junto con sus atributos no espaciales. 
Está basado en JSON (JavaScript Object Notation).

### Estructura básica

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-74.0617, 4.6737]
      },
      "properties": {
        "id": 123,
        "nombre": "Cámara Principal",
        "tipo": "Subterránea"
      }
    }
  ]
}
```

## Tipos de Geometrías en GeoAPIs

Las respuestas GeoJSON pueden contener diferentes tipos de geometrías según el tipo de objeto geoespacial:

### Point (Punto)

Utilizado para cámaras, centrales, empalmes y reservas.

```json
{
  "type": "Point",
  "coordinates": [longitud, latitud]
}
```

### LineString (Línea)

Utilizado para cables.

```json
{
  "type": "LineString",
  "coordinates": [
    [longitud1, latitud1],
    [longitud2, latitud2],
    [longitud3, latitud3]
  ]
}
```

## Propiedades por Tipo de Objeto

Cada tipo de objeto geoespacial tiene propiedades específicas que se incluyen en el campo `properties` de cada Feature.

### Cámaras

- `id`: Identificador único
- `id_texto`: Identificador textual
- `ubicacion`: Dirección o ubicación física
- `nombre_esp`: Nombre especial de la cámara
- `apertura`: Tipo de apertura
- `propietari`: Propietario
- `tipo`: Tipo de cámara

### Cables

- `id`: Identificador único
- `id_texto`: Identificador textual
- `name`: Nombre del cable
- `nombre_esp`: Nombre especial
- `colocacion`: Tipo de colocación (Troncal, Acceso, etc.)
- `perdida_db`: Pérdida en decibelios
- `segmento`: Segmento al que pertenece

### Centrales

- `id`: Identificador único
- `id_texto`: Identificador textual
- `nombre`: Nombre de la central
- `codigo`: Código único
- `direccion`: Dirección física
- `tipo`: Tipo de central

### Empalmes

- `id`: Identificador único
- `id_texto`: Identificador textual
- `nombre`: Nombre del empalme
- `tipo`: Tipo de empalme
- `capacidad`: Capacidad (ej. "96 hilos")
- `ubicacion`: Descripción de la ubicación

### Reservas

- `id`: Identificador único
- `id_texto`: Identificador textual
- `nombre`: Nombre de la reserva
- `tipo`: Tipo de reserva
- `capacidad`: Capacidad (ej. "48 hilos")
- `ubicacion`: Descripción de la ubicación

## Uso con Librerías de Mapas

El formato GeoJSON devuelto es compatible con librerías comunes de mapas como:

- Leaflet
- Mapbox GL
- OpenLayers
- Google Maps (con conversión)

### Ejemplo con Leaflet

```javascript
// Suponiendo que data contiene la respuesta GeoJSON
L.geoJSON(data, {
  pointToLayer: function (feature, latlng) {
    return L.circleMarker(latlng, {
      radius: 8,
      fillColor: "#ff7800",
      color: "#000",
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    });
  },
  onEachFeature: function (feature, layer) {
    let popupContent = `<h3>${feature.properties.nombre || feature.properties.id_texto || "ID: " + feature.properties.id}</h3>`;
    
    // Añadir todas las propiedades al popup
    for (let key in feature.properties) {
      popupContent += `<b>${key}:</b> ${feature.properties[key]}<br>`;
    }
    
    layer.bindPopup(popupContent);
  }
}).addTo(map);
```

## Filtrado y Consulta

Para filtrar los resultados por ubicación, se pueden utilizar los parámetros de consulta:

- `lat`: Latitud del punto central
- `lon`: Longitud del punto central
- `radio_interno`: Radio interno en metros (excluye elementos más cercanos que esta distancia)
- `radio_externo`: Radio externo en metros (límite máximo de búsqueda)

Ejemplo:
```
GET /api/camaras?lat=4.6737&lon=-74.0617&radio_interno=50&radio_externo=500
```
