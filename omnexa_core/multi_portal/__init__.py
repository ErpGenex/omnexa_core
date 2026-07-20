# Copyright (c) 2026, ErpGenEx
"""Multi-Portal Architecture — dynamic role portals for healthcare, education, commerce."""

from __future__ import annotations

APPLICATION_APP_MAP: dict[str, str] = {
	"healthcare": "omnexa_healthcare",
	"education": "omnexa_education",
	"commerce": "omnexa_trading"
	}

APPLICATION_ALIASES: dict[str, str] = {
	"trading": "commerce"
	}

VALID_APPLICATIONS: tuple[str, ...] = tuple(APPLICATION_APP_MAP.keys())

ALL_APPLICATION_KEYS: tuple[str, ...] = tuple(dict.fromkeys([*VALID_APPLICATIONS, *APPLICATION_ALIASES.keys()]))


def resolve_application(application_id: str) -> str:
	application_id = (application_id or "").strip().lower()
	return APPLICATION_ALIASES.get(application_id, application_id)
