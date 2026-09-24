from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

from .config import Settings
from .optimizer import find_latest_departure
from .telegram import send_message
from .two_gis import geocode
from .unn import current_week, fetch_week
from .models import Point


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


async def run_once() -> None:
    settings = Settings()
    today = date.today()
    week_start, week_end = current_week(today)

    lessons = await fetch_week(settings.unn_group_id, week_start, week_end)
    today_lessons = [x for x in lessons if x["date"] == today.isoformat()]
    today_lessons.sort(key=lambda x: x["start"])

    # Core "silent day" rule.
    if not today_lessons:
        print("No lessons today. Staying silent.")
        return

    first = today_lessons[0]
    if not first.get("building"):
        raise RuntimeError("The first lesson has no building in the RUZ response")

    buildings = settings.buildings
    building_key = first["building"]
    building_address = buildings.get(building_key) or buildings.get(str(building_key))
    if not building_address:
        raise RuntimeError(
            f"No address configured for building '{building_key}'. "
            "Add it to BUILDINGS_JSON."
        )

    home_lat, home_lon = await geocode(settings.home_address, settings.twogis_api_key)
    target_lat, target_lon = await geocode(building_address, settings.twogis_api_key)

    class_start = parse_iso_datetime(first["start"])
    latest_arrival = class_start.replace(tzinfo=None, microsecond=0)
    latest_arrival = latest_arrival - timedelta(minutes=settings.arrival_buffer_minutes)

    candidate = await find_latest_departure(
        api_key=settings.twogis_api_key,
        home=Point(home_lat, home_lon, settings.home_address),
        target=Point(target_lat, target_lon, building_address),
        latest_arrival=latest_arrival,
        step_minutes=settings.search_step_minutes,
        max_back_minutes=settings.max_search_back_minutes,
        transports=settings.transports,
    )

    if candidate is None:
        message = (
            "⚠️ Не удалось найти маршрут на сегодня.\n\n"
            f"Первая пара: {class_start:%H:%M}\n"
            f"Корпус: {first['building']}"
        )
    else:
        buffer = int((class_start - candidate.arrival).total_seconds() // 60)
        route_line = f"🚌 {candidate.route_number}" if candidate.route_number else "🚌 Общественный транспорт"
        stop_line = f"📍 Остановка: {candidate.boarding_stop}\n" if candidate.boarding_stop else ""
        message = (
            "☀️ Доброе утро\n\n"
            f"Первая пара: {class_start:%H:%M}\n"
            f"📚 {first['subject']}\n"
            f"🏢 {first['building']}" + (f", {first['room']}\n" if first.get("room") else "\n") +
            f"\n🚪 Выйти из дома: {candidate.departure:%H:%M}\n"
            f"{route_line}\n"
            + stop_line +
            f"🏫 Прибытие: {candidate.arrival:%H:%M}\n"
            f"⏱ Запас до пары: {buffer} мин"
        )

    await send_message(settings.telegram_bot_token, settings.telegram_chat_id, message)
    print(message)


if __name__ == "__main__":
    asyncio.run(run_once())
