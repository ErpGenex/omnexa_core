# Copyright (c) 2026, ErpGenEx
"""Unified SAP parity preview APIs (waves C/E/G/H)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.grc_parity import GRC_VERTICALS, preview_grc, preview_regulatory_pack
from omnexa_core.omnexa_core.sap_parity_registry import get_app_parity_status
from omnexa_core.omnexa_core.infra_parity import INFRA_VERTICALS, preview_infra
from omnexa_core.omnexa_core.vertical_parity import VERTICALS, preview_for_vertical


def _parse_params(params: str | None) -> dict[str, Any]:
	if not params:
		return {}
	parsed = json.loads(params) if isinstance(params, str) else params
	return parsed if isinstance(parsed, dict) else {}


@frappe.whitelist()
def preview_sector_kpi(vertical: str, scenario: str | None = None, params: str | None = None) -> dict:
	if vertical not in VERTICALS:
		frappe.throw(f"Unknown sector vertical: {vertical}")
	return preview_for_vertical(vertical, scenario=scenario, **_parse_params(params))


@frappe.whitelist()
def preview_grc_kpi(vertical: str, scenario: str | None = None, params: str | None = None) -> dict:
	if vertical not in GRC_VERTICALS:
		frappe.throw(f"Unknown GRC vertical: {vertical}")
	return preview_grc(vertical, scenario=scenario, **_parse_params(params))


@frappe.whitelist()
def preview_infra_kpi(vertical: str, scenario: str | None = None, params: str | None = None) -> dict:
	if vertical not in INFRA_VERTICALS:
		frappe.throw(f"Unknown infra vertical: {vertical}")
	return preview_infra(vertical, scenario=scenario, **_parse_params(params))


@frappe.whitelist()
def preview_regulatory_pack_kpi(
	vertical: str,
	controls_total: int = 10,
	controls_effective: int = 9,
	submissions_due: int = 0,
) -> dict:
	if vertical not in GRC_VERTICALS:
		frappe.throw(f"Unknown GRC vertical: {vertical}")
	return preview_regulatory_pack(
		vertical,
		controls_total=controls_total,
		controls_effective=controls_effective,
		submissions_due=submissions_due,
	)


@frappe.whitelist()
def get_app_sap_parity_status(app: str) -> dict:
	return get_app_parity_status(app)
