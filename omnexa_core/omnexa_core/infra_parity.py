# Copyright (c) 2026, ErpGenEx
"""Wave G/H — engineering stubs + BTP/platform infra parity previews."""

from __future__ import annotations

from typing import Any

INFRA_VERTICALS = frozenset(
	{
		"eng_document_control",
		"eng_workflow_engine",
		"eng_platform_integrations",
		"n8n_bridge",
		"intelligence_core",
		"setup_intelligence",
		"backup",
		"user_academy",
		"theme_manager",
		"erpgenex_theme_0426",
	}
)


def preview_infra(vertical: str, scenario: str | None = None, **params: Any) -> dict[str, Any]:
	vertical = (vertical or "").strip().lower()
	scenario = (scenario or "default").strip().lower()
	if vertical not in INFRA_VERTICALS:
		return {"vertical": vertical, "error": "unknown_infra_vertical"}
	handler = _HANDLERS.get(vertical, _default)
	return {"vertical": vertical, "scenario": scenario, **handler(scenario, params)}


def _default(_s: str, _p: dict) -> dict:
	return {"kpi": {}, "sap_module": "BTP"}


def _eng_stub(_s: str, params: dict) -> dict:
	bridge = False
	try:
		import omnexa_engineering_consulting  # noqa: F401

		bridge = True
	except Exception:
		bridge = False
	return {
		"kpi": {
			"consulting_bridge_available": bridge,
			"local_doctypes": 0,
			"delegation": "omnexa_engineering_consulting",
		},
		"sap_module": "DMS/BPM/BTP-INT",
	}


def _n8n(_s: str, params: dict) -> dict:
	events = int(params.get("pending_events") or 0)
	failed = int(params.get("failed_deliveries") or 0)
	return {"kpi": {"pending_events": events, "failed_deliveries": failed}, "sap_module": "BTP-INT"}


def _intelligence(_s: str, params: dict) -> dict:
	signals = int(params.get("active_signals") or 0)
	confidence = float(params.get("avg_confidence") or 0)
	return {"kpi": {"active_signals": signals, "avg_confidence": confidence}, "sap_module": "BTP-AI"}


def _setup(_s: str, params: dict) -> dict:
	checks = int(params.get("checks_passed") or 0)
	total = max(1, int(params.get("checks_total") or 1))
	return {
		"kpi": {"health_ratio": round(checks / total, 4)},
		"sap_module": "SAP Activate",
	}


def _backup(_s: str, params: dict) -> dict:
	hours = float(params.get("hours_since_backup") or 0)
	sla = float(params.get("backup_sla_hours") or 24)
	return {
		"kpi": {"hours_since_backup": hours, "within_sla": hours <= sla},
		"sap_module": "BC-DR",
	}


def _academy(_s: str, params: dict) -> dict:
	guides = int(params.get("published_guides") or 0)
	return {"kpi": {"published_guides": guides}, "sap_module": "LSO"}


def _theme(_s: str, params: dict) -> dict:
	active = bool(params.get("theme_active", 1))
	return {"kpi": {"theme_active": active}, "sap_module": "Fiori"}


_HANDLERS = {
	"eng_document_control": _eng_stub,
	"eng_workflow_engine": _eng_stub,
	"eng_platform_integrations": _eng_stub,
	"n8n_bridge": _n8n,
	"intelligence_core": _intelligence,
	"setup_intelligence": _setup,
	"backup": _backup,
	"user_academy": _academy,
	"theme_manager": _theme,
	"erpgenex_theme_0426": _theme,
}
