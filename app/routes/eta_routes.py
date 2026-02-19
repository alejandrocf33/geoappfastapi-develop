import base64

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from app import config
from app.auth import authenticate

router = APIRouter(tags=["ETA / Oracle Field Service"])


def _eta_auth_header() -> dict:
    token = base64.b64encode(f"{config.ETA_USERNAME}:{config.ETA_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@router.get("/eta/ubicacion-tecnico")
async def get_ubicacion_tecnico(
    activity_id: str = Query(..., description="ID de la actividad OFS (campo 'aid' del plugin)"),
    resource_login: str = Query(None, description="Login del recurso/técnico en OFS. Si se provee, omite la consulta de actividad y va directo a lastKnownPositions."),
    _=Depends(authenticate),
):
    """
    Obtiene la ubicación actual del técnico asignado a una actividad OFS.

    Flujo sin resource_login:
    1. Consulta la actividad por activity_id → extrae resourceId (login del técnico)
    2. Consulta la última posición conocida del recurso
    3. Retorna lat/lng del técnico (o coordenadas de la actividad como fallback)

    Flujo con resource_login:
    1. Usa el login provisto directamente en lastKnownPositions
    2. Retorna lat/lng del técnico
    """
    if not config.ETA_BASE_URL or not config.ETA_USERNAME or not config.ETA_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Credenciales ETA no configuradas. Revise las variables de entorno ETA_BASE_URL, ETA_USERNAME y ETA_PASSWORD.",
        )

    headers = _eta_auth_header()
    raw_base = config.ETA_BASE_URL.rstrip("/")
    base = raw_base if raw_base.startswith("http") else f"https://{raw_base}"

    activity_lat = None
    activity_lng = None

    if resource_login:
        # Flujo directo: login del técnico provisto, sin consultar la actividad
        resource_id = resource_login
    else:
        # 1) Obtener actividad → extraer resourceId (login) y coordenadas de actividad
        async with httpx.AsyncClient(timeout=10) as client:
            r_act = await client.get(
                f"{base}/rest/ofscCore/v1/activities/{activity_id}",
                headers=headers,
                params={"fields": "resourceId,status,latitude,longitude"},
            )

        if r_act.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Actividad '{activity_id}' no encontrada en OFS.")
        if r_act.status_code == 401:
            raise HTTPException(status_code=502, detail="Credenciales OFS inválidas (401).")
        if r_act.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Error al consultar actividad OFS: HTTP {r_act.status_code}",
            )

        activity = r_act.json()
        resource_id = activity.get("resourceId")
        activity_lat = activity.get("latitude")
        activity_lng = activity.get("longitude")

        if not resource_id:
            raise HTTPException(status_code=404, detail="La actividad no tiene recurso/técnico asignado.")

    # 2) Obtener última posición conocida del recurso por su login
    async with httpx.AsyncClient(timeout=10) as client:
        r_pos = await client.get(
            f"{base}/rest/ofscCore/v1/resources/custom-actions/lastKnownPositions",
            headers=headers,
            params={"resources": resource_id},
        )

    # Extraer posición real (items puede contener entradas con errorMessage)
    pos = None
    if r_pos.status_code == 200:
        for item in r_pos.json().get("items", []):
            if "lat" in item and "lng" in item:
                pos = item
                break

    if pos:
        return {
            "resourceId": resource_id,
            "lat": pos["lat"],
            "lng": pos["lng"],
            "timestamp": pos.get("time"),
            "source": "last_known_position",
            "activity_coords": {"lat": activity_lat, "lng": activity_lng},
        }

    # Fallback: coordenadas de la actividad
    if activity_lat is not None and activity_lng is not None:
        return {
            "resourceId": resource_id,
            "lat": activity_lat,
            "lng": activity_lng,
            "timestamp": None,
            "source": "activity_coords",
            "activity_coords": {"lat": activity_lat, "lng": activity_lng},
        }

    raise HTTPException(
        status_code=404,
        detail="No se encontró posición reciente del técnico ni coordenadas de actividad.",
    )
