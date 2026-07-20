# Copyright (c) 2026, ErpGenEx
"""Wave C whitelist — sector KPI preview."""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.vertical_parity import VERTICALS, preview_for_vertical


@frappe.whitelist()
def preview_sector_kpi(vertical: str, scenario: str | None = None, params: str | None = None) -> dict:
	"""SAP parity preview for vertical apps (JSON params, read-only)."""
	if vertical not in VERTICALS:
		frappe.throw(f"Unknown vertical: {vertical}")
	kw: dict[str, Any] = {}
	if params:
		parsed = json.loads(params) if isinstance(params, str) else params
		if isinstance(parsed, dict):
			kw = parsed
	return preview_for_vertical(vertical, scenario=scenario, **kw)
