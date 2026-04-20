# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Ensure Desk boot payloads use ERPGENEX as the product name (no ERPNext in UI)."""

from __future__ import annotations

from typing import Any


def _rebrand_str(value: str) -> str:
	if "ERPNext" not in value and "ErpNext" not in value:
		return value
	return value.replace("ERPNext", "ERPGENEX").replace("ErpNext", "ERPGENEX")


def _rebrand(value: Any) -> Any:
	if isinstance(value, str):
		return _rebrand_str(value)
	if isinstance(value, dict):
		return {k: _rebrand(v) for k, v in value.items()}
	if isinstance(value, list):
		return [_rebrand(v) for v in value]
	if isinstance(value, tuple):
		return tuple(_rebrand(v) for v in value)
	return value


def boot_session(bootinfo):
	"""Frappe hook: patch bootinfo in place for ERPGENEX branding."""
	for key in ("success_action", "notes"):
		if bootinfo.get(key):
			bootinfo[key] = _rebrand(bootinfo[key])
