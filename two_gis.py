from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

GEOCODE_URL = "https://catalog.api.2gis.com/3.0/items/geocode"
ROUTE_URL = "https://routing.api.2gis.com/public_transport/2.0"


class TwoGisError(RuntimeError):
    pass


async def geocode(address: str, api_key: str) -> tuple[float, float]:
    params = {
        "q": address,
        "fields": "items.point,items.geometry.centroid",
        "key": api_key,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(GEOCODE_URL, params=params)
        response.raise_for_status()
        data = response.json()
    items = data.get("result", {}).get("items", [])
    if not items:
        raise TwoGisError(f"2GIS: address not found: {address}")
    point = items[0].get("point") or {}
    if "lat" not in point or "lon" not in point:
        raise TwoGisError(f"2GIS: no coordinates for: {address}")
    return float(point["lat"]), float(point["lon"])


async def public_transport_route(
    api_key: str,
    source_lat: float,
    source_lon: float,
    target_lat: float,
    target_lon: float,
    departure: datetime,
    transports: list[str],
) -> list[dict[str, Any]]:
    payload = {
        "source": {"point": {"lat": source_lat, "lon": source_lon}},
        "target": {"point": {"lat": target_lat, "lon": target_lon}},
        "transport": transports,
        "start_time": int(departure.timestamp()),
        "enable_schedule": True,
        "locale": "ru",
    }
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            ROUTE_URL,
            params={"key": api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    # Public Transport API returns a top-level list of route options.
    if isinstance(data, dict) and isinstance(data.get("result"), list):
        return data["result"]
    if isinstance(data, list):
        return data
    return []


def summarize_route(route: dict[str, Any], departure: datetime) -> dict[str, Any]:
    total_duration = int(route.get("total_duration", 0))
    arrival = datetime.fromtimestamp(departure.timestamp() + total_duration)
    movements = route.get("movements") or []

    route_number = None
    boarding_stop = None
    alighting_stop = None
    walkway_distance = None

    for movement in movements:
        if not isinstance(movement, dict):
            continue
        if movement.get("type") == "passage" and route_number is None:
            routes = movement.get("routes") or []
            if routes and isinstance(routes[0], dict):
                names = routes[0].get("names") or []
                if names:
                    route_number = ", ".join(str(x) for x in names)
            platforms = movement.get("platforms") or {}
            names = platforms.get("names") if isinstance(platforms, dict) else None
            if isinstance(names, list) and names:
                boarding_stop = str(names[0])
                if len(names) > 1:
                    alighting_stop = str(names[-1])
            break

    raw_walk = route.get("total_walkway_distance")
    if isinstance(raw_walk, (int, float)):
        walkway_distance = int(raw_walk)

    return {
        "departure": departure,
        "arrival": arrival,
        "duration_seconds": total_duration,
        "walk_distance_m": walkway_distance,
        "transfers": int(route.get("transfer_count", 0)),
        "route_number": route_number,
        "boarding_stop": boarding_stop,
        "alighting_stop": alighting_stop,
        "raw": route,
    }
