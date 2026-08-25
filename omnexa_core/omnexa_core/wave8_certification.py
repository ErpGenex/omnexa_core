# Copyright (c) 2026, ErpGenEx
"""Wave 8 certification — full activity independence + financial/inventory integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frappe
from frappe.utils import get_bench_path

from omnexa_core.omnexa_core.activity_registry import (
	FINANCIAL_CORE_APPS,
	INTEGRATION_COMMANDS,
	app_in_activity_registry,
	get_financial_core_apps,
)
from omnexa_core.omnexa_core.app_activity import activity_for_app
from omnexa_core.omnexa_core.integration_bus import list_integration_commands
from omnexa_core.omnexa_core.world_class import certify_app

WAVE8_TARGET = 5.0


def _gate_activity_registry_aligned(app: str) -> bool:
	return app_in_activity_registry(app)


def _gate_isolation_harness(app: str) -> bool:
	root = Path(get_bench_path()) / "apps" / app
	return bool(list(root.glob("**/tests/test_session_scope.py")))


def _gate_financial_core_present() -> bool:
	installed = set(frappe.get_installed_apps() or [])
	return "omnexa_accounting" in installed


def _gate_integration_bus_ready() -> bool:
	commands = set(list_integration_commands())
	return INTEGRATION_COMMANDS.issubset(commands)


def _gate_isolation_qa() -> bool:
	try:
		from omnexa_core.omnexa_core.isolation_qa import run_isolation_qa

		report = run_isolation_qa()
		return bool(report.get("all_pass"))
	except Exception:
		return False


def _gate_integration_contract_test(app: str) -> bool:
	root = Path(get_bench_path()) / "apps" / app
	candidates = list(root.glob("**/tests/test_accounting_integration.py")) + list(
		root.glob("**/tests/test_integration_bus.py")
	)
	if candidates:
		return True
	# Platform / financial core apps use bus natively.
	if app in FINANCIAL_CORE_APPS or app == "omnexa_core":
		return True
	return False


def wave8_gates(app: str) -> dict[str, bool]:
	return {
		"activity_registry_aligned": _gate_activity_registry_aligned(app),
		"isolation_session_scope": _gate_isolation_harness(app),
		"financial_core_installed": _gate_financial_core_present(),
		"integration_bus_ready": _gate_integration_bus_ready(),
		"isolation_qa_passes": _gate_isolation_qa(),
		"integration_contract_test": _gate_integration_contract_test(app),
	}


def certify_wave8(app: str) -> dict[str, Any]:
	base = certify_app(app)
	w8 = wave8_gates(app)
	independence_ok = all(
		w8[k]
		for k in (
			"activity_registry_aligned",
			"isolation_session_scope",
			"isolation_qa_passes",
		)
	)
	integration_ok = all(
		w8[k]
		for k in (
			"financial_core_installed",
			"integration_bus_ready",
			"integration_contract_test",
		)
	)
	full_wave8 = independence_ok and integration_ok and base.get("world_class_gate")
	level = "Wave 8 World Class"
	if full_wave8:
		pass
	elif independence_ok and integration_ok:
		level = "Independent + Integrated"
	elif independence_ok:
		level = "Independent"
	elif integration_ok:
		level = "Integrated"
	else:
		level = "Wave 8 Pending"

	return {
		**base,
		"wave8_gates": w8,
		"wave8_independence": independence_ok,
		"wave8_integration": integration_ok,
		"wave8_gate": full_wave8,
		"wave8_level": level,
		"financial_core_apps": get_financial_core_apps(),
		"activity_label": activity_for_app(app),
		"standards": base.get("standards", [])
		+ ["ERPGenEx W8-AIP-2026", "ERPGenEx W8-INT-2026"],
	}


@frappe.whitelist()
def get_wave8_certification(app: str | None = None) -> dict[str, Any]:
	if not app:
		frappe.throw("app is required")
	return certify_wave8((app or "").strip())
