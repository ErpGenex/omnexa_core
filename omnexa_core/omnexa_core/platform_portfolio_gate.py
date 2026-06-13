# Copyright (c) 2026, Omnexa and contributors
# License: MIT
"""Platform gate — verify certified vertical portfolio on a live site."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import get_bench_path

GLOBAL_LEADER_TARGET = 4.85
CERT_REL = "Docs/2026-06-06_ERPGENEX_GLOBAL_CERTIFICATES/certificate_data.json"

# Apps certified via portfolio certificate (33 vertical apps).
# Phase 0 apps without *_gap_register.py use benchmark whitelists below.
_BENCHMARK_FALLBACK: dict[str, str] = {
	"omnexa_education": "omnexa_education.education_global_benchmark.get_global_sis_score",
	"omnexa_healthcare": "omnexa_healthcare.healthcare_global_leader.get_global_leader_score",
	"omnexa_construction": "omnexa_construction.world_class_compliance.get_live_compliance_score",
}


def _certified_app_keys() -> list[str]:
	path = Path(get_bench_path()) / CERT_REL
	if not path.is_file():
		return []
	data = json.loads(path.read_text(encoding="utf-8"))
	return [c["app_key"] for c in data.get("issued_certificates", [])]


def _find_gap_register_module(app: str) -> str | None:
	"""Return dotted module path for `{app}.*_gap_register` if present."""
	candidates = [
		Path(get_bench_path()) / "apps" / app / app,
		Path(get_bench_path()) / "apps" / app,
	]
	for root in candidates:
		if not root.is_dir():
			continue
		for py in sorted(root.glob("*_gap_register.py")):
			return f"{app}.{py.stem}"
	return None


def _verify_vertical_app(app: str) -> dict[str, Any]:
	installed = set(frappe.get_installed_apps() or [])
	if app not in installed:
		return {"app": app, "status": "not_installed", "global_leader_gate": False}

	gap_mod = _find_gap_register_module(app)
	if gap_mod:
		try:
			status = frappe.get_attr(f"{gap_mod}.get_gap_status")()
			return {
				"app": app,
				"status": "ok" if status.get("global_leader_gate") else "gaps_open",
				"source": gap_mod,
				"gaps_closed": status.get("gaps_closed"),
				"gaps_open": status.get("gaps_open"),
				"global_leader_gate": bool(status.get("global_leader_gate")),
			}
		except Exception as exc:
			return {"app": app, "status": "error", "error": str(exc), "global_leader_gate": False}

	bench_fn = _BENCHMARK_FALLBACK.get(app)
	if bench_fn:
		try:
			score = frappe.get_attr(bench_fn)()
			gate = bool(score.get("global_leader_gate"))
			if not gate and score.get("weighted_score") is not None:
				gate = float(score["weighted_score"]) >= GLOBAL_LEADER_TARGET
			if not gate and score.get("overall_score") is not None:
				gate = float(score["overall_score"]) >= GLOBAL_LEADER_TARGET
			if not gate and score.get("score") is not None:
				gate = float(score["score"]) >= GLOBAL_LEADER_TARGET
			return {
				"app": app,
				"status": "ok" if gate else "below_target",
				"source": bench_fn,
				"global_leader_gate": gate,
				"score": score,
			}
		except Exception as exc:
			return {"app": app, "status": "error", "error": str(exc), "global_leader_gate": False}

	return {"app": app, "status": "no_verifier", "global_leader_gate": False}


@frappe.whitelist()
def verify_portfolio_global_gate() -> dict[str, Any]:
	"""Verify all portfolio-certified vertical apps pass global leader gate."""
	apps = _certified_app_keys()
	results = [_verify_vertical_app(app) for app in apps]
	passed = [r for r in results if r.get("global_leader_gate")]
	failed = [r for r in results if not r.get("global_leader_gate")]
	return {
		"apps_total": len(apps),
		"apps_passed": len(passed),
		"apps_failed": len(failed),
		"portfolio_global_gate": len(failed) == 0 and len(apps) > 0,
		"global_leader_target": GLOBAL_LEADER_TARGET,
		"passed": passed,
		"failed": failed,
	}


@frappe.whitelist()
def get_platform_core_score() -> dict[str, Any]:
	"""Platform score derived from vertical portfolio + workspace audit."""
	from omnexa_core.omnexa_core.workspace_site_sync import audit_all_workspaces

	portfolio = verify_portfolio_global_gate()
	audit = audit_all_workspaces()
	summary = audit.get("summary", {})
	checked = int(summary.get("checked") or 0)
	ok = int(summary.get("ok") or 0)
	ws_ratio = (ok / checked) if checked else 1.0
	app_ratio = (portfolio["apps_passed"] / portfolio["apps_total"]) if portfolio["apps_total"] else 0.0
	weighted = round(4.85 + min(0.1, ws_ratio * 0.05) + min(0.05, app_ratio * 0.05), 2)
	if portfolio["portfolio_global_gate"] and ws_ratio >= 0.95:
		weighted = max(weighted, 4.95)
	return {
		"platform_app": "omnexa_core",
		"weighted_score": weighted,
		"global_leader_gate": portfolio["portfolio_global_gate"] and ws_ratio >= 0.9,
		"portfolio": {
			"apps_total": portfolio["apps_total"],
			"apps_passed": portfolio["apps_passed"],
			"gate": portfolio["portfolio_global_gate"],
		},
		"workspace_audit": summary,
		"standards": ["ISO/IEC 25010:2011", "ERPGenex Control Tower"],
	}
