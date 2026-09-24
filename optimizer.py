from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .models import Point, RouteCandidate
from .two_gis import public_transport_route, summarize_route


async def find_latest_departure(
    *,
    api_key: str,
    home: Point,
    target: Point,
    latest_arrival: datetime,
    step_minutes: int,
    max_back_minutes: int,
    transports: list[str],
) -> RouteCandidate | None:
    """Search backward in time for the latest departure that still arrives on time."""
    departure = latest_arrival - timedelta(minutes=1)
    earliest = latest_arrival - timedelta(minutes=max_back_minutes)
    best: RouteCandidate | None = None

    while departure >= earliest:
        routes = await public_transport_route(
            api_key,
            home.lat,
            home.lon,
            target.lat,
            target.lon,
            departure,
            transports,
        )
        for raw in routes:
            candidate_data: dict[str, Any] = summarize_route(raw, departure)
            candidate = RouteCandidate(**candidate_data)
            if candidate.arrival <= latest_arrival:
                # For equal departure times prefer fewer transfers, then shorter duration.
                if best is None:
                    best = candidate
                else:
                    if (
                        candidate.departure > best.departure
                        or (
                            candidate.departure == best.departure
                            and (candidate.transfers, candidate.duration_seconds)
                            < (best.transfers, best.duration_seconds)
                        )
                    ):
                        best = candidate
        if best is not None and best.departure == departure:
            return best
        departure -= timedelta(minutes=step_minutes)

    return best
