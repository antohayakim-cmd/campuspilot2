from __future__ import annotations

import asyncio
import json
from datetime import date

from .config import Settings
from .unn import current_week, fetch_week


async def main() -> None:
    settings = Settings()
    start, finish = current_week(date.today())
    print(f"Requesting UNN RUZ group {settings.unn_group_id}: {start} -> {finish}")
    lessons = await fetch_week(settings.unn_group_id, start, finish)
    print(json.dumps(lessons, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
