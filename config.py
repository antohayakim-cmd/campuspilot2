from __future__ import annotations

import json
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: str
    telegram_chat_id: str
    twogis_api_key: str
    unn_group_id: int = 50793
    home_address: str
    arrival_buffer_minutes: int = 10
    search_step_minutes: int = 2
    max_search_back_minutes: int = 120
    transport_types: str = "bus,tram,trolleybus,metro,shuttle_bus"
    buildings_json: str = "{}"

    @property
    def transports(self) -> list[str]:
        return [x.strip() for x in self.transport_types.split(",") if x.strip()]

    @property
    def buildings(self) -> dict[str, Any]:
        try:
            value = json.loads(self.buildings_json)
        except json.JSONDecodeError as exc:
            raise ValueError("BUILDINGS_JSON contains invalid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("BUILDINGS_JSON must be an object")
        return value
