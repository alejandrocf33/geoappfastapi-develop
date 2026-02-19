# Formato GeoJSON en GeoAPIs

Las APIs de consulta devuelven resultados en formato GeoJSON, un estandar abierto para representar entidades geograficas basado en JSON.

---

## Estructura basica

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
        "id_texto": "CAM-001",
        "type": "Subterranea"
      }
    }
  ]
}
```

---

## Tipos de geometria

| Tipo | Entidades | Formato coordinates |
|------|-----------|---------------------|
| `Point` | Camaras, centrales, empalmes, reservas | `[longitud, latitud]` |
| `LineString` | Cables | `[[lon1, lat1], [lon2, lat2], ...]` |

---

## Propiedades por entidad

Las propiedades especificas de cada entidad (campos incluidos en `properties`) se documentan en detalle en la [Referencia de APIs](api-referencia.md), dentro de cada endpoint.

Notas importantes sobre nombres de propiedades:

- **Camaras**: la propiedad de tipo se llama `"type"` (no `"tipo"`)
- **Cables**: usan `"id_text"` (no `"id_texto"`) en el JSONB

---

## Compatibilidad con librerias de mapas

El formato GeoJSON es compatible con:

- Leaflet
- Mapbox GL
- OpenLayers
- Google Maps (con conversion)

### Ejemplo con Leaflet

```javascript
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
    for (let key in feature.properties) {
      popupContent += `<b>${key}:</b> ${feature.properties[key]}<br>`;
    }
    layer.bindPopup(popupContent);
  }
}).addTo(map);
```
