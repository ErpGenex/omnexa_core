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
WORLD_CLASS_SCORE = 5.0
WORLD_CLASS_EFFICIENCY = 100

# Apps certified via portfolio certificate (33 vertical apps).
# Phase 0 apps without *_gap_register.py use benchmark whitelists below.
_BENCHMARK_FALLBACK: dict[str, str] = {
	"omnexa_education": "omnexa_education.education_global_benchmark.get_global_sis_score",
	"omnexa_healthcare": "omnexa_healthcare.healthcare_global_leader.get_global_leader_score",
	"omnexa_construction": "omnexa_construction.world_class_compliance.get_live_compliance_score"
	}


def _certified_app_keys() -> list[str]:
	from omnexa_core.omnexa_core.global_certificates_sync import load_certificate_data

	data = load_certificate_data()
	return [c["app_key"] for c in data.get("issued_certificates", [])]


def get_portfolio_certificate_summary() -> dict[str, Any]:
	from omnexa_core.omnexa_core.global_certificates_sync import load_certificate_data

	data = load_certificate_data()
	summary = dict(data.get("portfolio_summary") or {})
	certs = data.get("issued_certificates") or []
	if not summary.get("efficiency_score") and certs:
		scores = [int(c.get("efficiency_score") or round(float(c.get("overall_score", 0)) * 20)) for c in certs]
		summary["efficiency_score"] = min(scores) if scores else 0
	summary.setdefault("efficiency_display", f"{summary.get('efficiency_score', 0)}/100")
	summary.setdefault("certificates_total", len(certs))
	return summary


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
		return {"app": app, "status": "not_installed", "global_leader_gate": False
	}

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
				"global_leader_gate": bool(status.get("global_leader_gate"))
	}
		except Exception as exc:
			return {"app": app, "status": "error", "error": str(exc), "global_leader_gate": False
	}

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
				"score": score
	}
		except Exception as exc:
			return {"app": app, "status": "error", "error": str(exc), "global_leader_gate": False
	}

	return {"app": app, "status": "no_verifier", "global_leader_gate": False
	}


@frappe.whitelist()
def verify_portfolio_global_gate() -> dict[str, Any]:
	"""Verify all portfolio-certified vertical apps pass global leader gate."""
	installed = set(frappe.get_installed_apps() or [])
	apps = [app for app in _certified_app_keys() if app in installed]
	skipped = [app for app in _certified_app_keys() if app not in installed]
	results = [_verify_vertical_app(app) for app in apps]
	passed = [r for r in results if r.get("global_leader_gate")]
	failed = [r for r in results if not r.get("global_leader_gate")]
	return {
		"apps_total": len(apps),
		"apps_passed": len(passed),
		"apps_failed": len(failed),
		"apps_skipped_not_installed": len(skipped),
		"portfolio_global_gate": len(failed) == 0 and len(apps) > 0,
		"global_leader_target": GLOBAL_LEADER_TARGET,
		"passed": passed,
		"failed": failed,
		"skipped": skipped
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
	cert_summary = get_portfolio_certificate_summary()
	cert_eff = int(cert_summary.get("efficiency_score") or 0)
	if portfolio["portfolio_global_gate"] and ws_ratio >= 1.0 and cert_eff >= WORLD_CLASS_EFFICIENCY:
		weighted = WORLD_CLASS_SCORE
	elif portfolio["portfolio_global_gate"] and ws_ratio >= 0.95:
		weighted = max(weighted, 4.95)
	return {
		"platform_app": "omnexa_core",
		"weighted_score": weighted,
		"efficiency_score": cert_eff,
		"efficiency_display": cert_summary.get("efficiency_display") or f"{cert_eff
	}/100",
		"global_leader_gate": portfolio["portfolio_global_gate"] and ws_ratio >= 0.9 and cert_eff >= WORLD_CLASS_EFFICIENCY,
		"portfolio": {
			"apps_total": portfolio["apps_total"],
			"apps_passed": portfolio["apps_passed"],
			"gate": portfolio["portfolio_global_gate"]
	},
		"workspace_audit": summary,
		"standards": ["ISO/IEC 25010:2011", "ERPGenex Control Tower"]}


PLATFORM_BENCHMARK_APPS = [
	"omnexa_backup",
	"omnexa_customer_core",
	"omnexa_experience",
	"omnexa_setup_intelligence",
	"omnexa_intelligence_core",
	"omnexa_reporting_compliance",
	"omnexa_theme_manager",
	"omnexa_user_academy",
	"omnexa_n8n_bridge",
	"omnexa_eng_document_control",
	"omnexa_eng_platform_integrations",
	"omnexa_eng_workflow_engine",
	"erpgenex_theme_0426",
]


@frappe.whitelist()
def import_platform_benchmark_pages() -> dict[str, Any]:
	"""Import Page JSON fixtures for platform global benchmark apps."""
	import os

	from frappe.modules.import_file import import_file_by_path
	from frappe.utils import get_app_path

	imported: list[str] = []
	for app in PLATFORM_BENCHMARK_APPS:
		page_root = os.path.join(get_app_path(app), app, "page")
		if not os.path.isdir(page_root):
			continue
		for folder in sorted(os.listdir(page_root)):
			json_path = os.path.join(page_root, folder, f"{folder}.json")
			if not os.path.isfile(json_path):
				continue
			import_file_by_path(json_path, force=True)
			imported.append(f"{app}:{folder}")
	frappe.db.commit()
	return {"imported": imported, "count": len(imported)
	}


@frappe.whitelist()
def verify_platform_apps_global_gate() -> dict[str, Any]:
	"""Verify platform / infra apps with gap registers pass global leader gate."""
	results = [_verify_vertical_app(app) for app in PLATFORM_BENCHMARK_APPS]
	passed = [r for r in results if r.get("global_leader_gate")]
	failed = [r for r in results if not r.get("global_leader_gate")]
	return {
		"apps_total": len(PLATFORM_BENCHMARK_APPS),
		"apps_passed": len(passed),
		"apps_failed": len(failed),
		"platform_global_gate": len(failed) == 0 and len(passed) > 0,
		"passed": passed,
		"failed": failed
	}
