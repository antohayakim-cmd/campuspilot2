from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Lesson:
    lesson_id: str | None
    date: datetime
    start: datetime
    end: datetime
    subject: str
    building: str | None = None
    room: str | None = None
    teacher: str | None = None
    lesson_type: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Point:
    lat: float
    lon: float
    label: str | None = None


@dataclass(slots=True)
class RouteCandidate:
    departure: datetime
    arrival: datetime
    duration_seconds: int
    walk_distance_m: int | None
    transfers: int
    route_number: str | None
    boarding_stop: str | None
    alighting_stop: str | None
    raw: dict[str, Any]
