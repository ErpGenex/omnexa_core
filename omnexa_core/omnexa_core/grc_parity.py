# Copyright (c) 2026, ErpGenEx
"""Wave E — GRC / audit parity previews (SAP GRC)."""

from __future__ import annotations

from typing import Any

from frappe.utils import flt

GRC_VERTICALS = frozenset({"statutory_audit", "reporting_compliance", "operational_risk"})


def preview_grc(vertical: str, scenario: str | None = None, **params: Any) -> dict[str, Any]:
	vertical = (vertical or "").strip().lower()
	scenario = (scenario or "default").strip().lower()
	if vertical not in GRC_VERTICALS:
		return {"vertical": vertical, "error": "unknown_grc_vertical"}
	handler = _HANDLERS[vertical]
	return {"vertical": vertical, "scenario": scenario, **handler(scenario, params)}


def _statutory_audit(_scenario: str, params: dict) -> dict:
	open_findings = int(params.get("open_findings") or 0)
	critical = int(params.get("critical_findings") or 0)
	evidence_locked = int(params.get("evidence_locked") or 0)
	evidence_total = max(1, int(params.get("evidence_total") or 1))
	return {
		"kpi": {
			"open_findings": open_findings,
			"critical_findings": critical,
			"evidence_lock_ratio": round(evidence_locked / evidence_total, 4),
		},
		"sap_module": "GRC-Audit",
	}


def _reporting_compliance(_scenario: str, params: dict) -> dict:
	controls = int(params.get("controls_total") or 0)
	effective = int(params.get("controls_effective") or 0)
	open_remediation = int(params.get("open_remediation") or 0)
	coverage = round(effective / controls, 4) if controls else 0
	return {
		"kpi": {
			"control_coverage": coverage,
			"open_remediation": open_remediation,
		},
		"sap_module": "GRC",
	}


def _operational_risk(_scenario: str, params: dict) -> dict:
	loss = flt(params.get("loss_amount") or 0)
	severity = (params.get("severity") or "Medium").strip()
	incidents = int(params.get("open_incidents") or 0)
	weight = {"Low": 1, "Medium": 2, "High": 4, "Critical": 8}.get(severity, 2)
	risk_score = round(loss / 10000 * weight + incidents * 0.5, 2)
	return {
		"kpi": {
			"loss_amount": loss,
			"open_incidents": incidents,
			"risk_score_preview": risk_score,
		},
		"sap_module": "GRC-ORM",
	}


def preview_regulatory_pack(
	vertical: str,
	*,
	controls_total: int = 10,
	controls_effective: int = 9,
	submissions_due: int = 1,
) -> dict[str, Any]:
	"""Regulatory submission pack readiness (preview)."""
	vertical = (vertical or "").strip().lower()
	coverage = round(int(controls_effective) / max(1, int(controls_total)), 4)
	return {
		"vertical": vertical,
		"kpi": {
			"control_coverage": coverage,
			"submissions_due": int(submissions_due),
			"pack_ready": coverage >= 0.95 and submissions_due == 0,
		},
		"sap_module": "GRC-Regulatory",
	}


_HANDLERS = {
	"statutory_audit": _statutory_audit,
	"reporting_compliance": _reporting_compliance,
	"operational_risk": _operational_risk,
}
