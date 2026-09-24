from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import httpx

BASE = "https://portal.unn.ru/ruzapi/schedule/group/{group_id}"


def _first(obj: dict[str, Any], keys: list[str], default=None):
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return default


def _parse_dt(value: Any, fallback_date: date | None = None, time_only: bool = False) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M",
        "%H:%M",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt == "%H:%M":
                if fallback_date is None:
                    return None
                return datetime.combine(fallback_date, parsed.time())
            return parsed.replace(tzinfo=None)
        except ValueError:
            continue
    return None


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("result", "items", "lessons", "schedule", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                found = _extract_items(value)
                if found:
                    return found
    return []


def normalize_ruz(payload: Any) -> list[dict[str, Any]]:
    """Normalize the likely RUZ response shapes into a compact internal shape.

    We intentionally keep `raw` so the parser can be adjusted after the first
    live request without losing information.
    """
    result: list[dict[str, Any]] = []
    for item in _extract_items(payload):
        start_raw = _first(item, [
            "startdatetime", "startDateTime", "start", "beginLesson", "dateStart", "startTime"
        ])
        end_raw = _first(item, [
            "enddatetime", "endDateTime", "end", "endLesson", "dateEnd", "endTime"
        ])
        date_raw = _first(item, ["date", "day", "lessonDate"])
        fallback_date = None
        if date_raw:
            try:
                fallback_date = date.fromisoformat(str(date_raw)[:10])
            except ValueError:
                try:
                    fallback_date = datetime.strptime(str(date_raw)[:10], "%d.%m.%Y").date()
                except ValueError:
                    pass
        start = _parse_dt(start_raw, fallback_date)
        end = _parse_dt(end_raw, fallback_date)
        if not start or not end:
            continue
        result.append({
            "lesson_id": str(_first(item, ["id", "eventId", "lessonId"], "")) or None,
            "date": start.date().isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "subject": _first(item, ["discipline", "subject", "name", "disciplineName"], "Без названия"),
            "building": _first(item, ["building", "buildingName", "korpus", "korpusName"]),
            "room": _first(item, ["auditorium", "aud", "aud_name", "room", "roomName"]),
            "teacher": _first(item, ["lecturer", "teacher", "teacherName", "lector"]),
            "lesson_type": _first(item, ["kindOfWork", "type", "typework", "workType"]),
            "raw": item,
        })
    return result


async def fetch_week(group_id: int, start: date, finish: date) -> list[dict[str, Any]]:
    url = BASE.format(group_id=group_id)
    params = {
        "start": start.isoformat(),
        "finish": finish.isoformat(),
        "lng": 1,
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    return normalize_ruz(payload)


def current_week(today: date) -> tuple[date, date]:
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)
