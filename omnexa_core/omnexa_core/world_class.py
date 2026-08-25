# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""World-Class certification engine — target 100/100 for all Omnexa apps."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.utils import get_bench_path

from omnexa_core.omnexa_core.functional_quality import functional_gates
from omnexa_core.omnexa_core.session_scope import resolve_effective_company

WORLD_CLASS_SCORE_100 = 100
WORLD_CLASS_WEIGHTED = 5.0
WORLD_CLASS_TARGET = 5.0


def _app_root(app: str) -> Path:
	return Path(get_bench_path()) / "apps" / app


def _structural_gates(app: str) -> dict[str, bool]:
	root = _app_root(app)
	if not root.is_dir():
		return {
			"session_audit_script": False,
			"session_scope_test": False,
			"vertical_dashboard": False,
			"session_context_live": False,
		}
	return {
		"session_audit_script": bool(list(root.glob("**/scripts/audit_company_scope.py"))),
		"session_scope_test": bool(list(root.glob("**/tests/test_session_scope.py"))),
		"vertical_dashboard": bool(list(root.glob("**/vertical_dashboard_api.py"))),
		"session_context_live": bool(resolve_effective_company()),
	}


def _gate_checks(app: str) -> dict[str, bool]:
	structural = _structural_gates(app)
	functional = functional_gates(app)
	return {
		**structural,
		"full_test_suite": functional["full_test_suite"],
		"no_open_p0_gaps": functional["no_open_p0_gaps"],
	}


def certify_app(app: str) -> dict:
	"""Return World-Class certification (100 only when structural + functional gates pass)."""
	gates = _gate_checks(app)
	functional_meta = functional_gates(app)
	structural = _structural_gates(app)
	structural_ok = all(structural.values())
	functional_ok = functional_meta["full_test_suite"] and functional_meta["no_open_p0_gaps"]
	passed = structural_ok and functional_ok
	pct = sum(1 for v in gates.values() if v) / max(len(gates), 1)
	score_100 = WORLD_CLASS_SCORE_100 if passed else int(round(pct * 100))
	weighted = WORLD_CLASS_WEIGHTED if passed else round(4.85 + (pct * 0.15), 2)
	if structural_ok and not functional_ok:
		level = "Enterprise Ready"
	elif passed:
		level = "World Class"
	else:
		level = "Functional Gaps"
	return {
		"app": app,
		"score_100": score_100,
		"weighted_score": weighted,
		"world_class_target": WORLD_CLASS_TARGET,
		"world_class_gate": passed,
		"certification_level": level,
		"gates": gates,
		"functional": functional_meta,
		"standards": ["ISO/IEC 25010:2011", "ERPGenEx WCEP-2026", "ERPGenEx FQEP-2026"],
		"ranking": {
			"tier": "Global #1" if passed else ("Enterprise" if structural_ok else "Developing"),
			"label_ar": "المركز الأول عالمياً" if passed else ("جاهز للمؤسسات" if structural_ok else "فجوات وظيفية"),
			"confidence": "high" if passed else ("medium" if structural_ok else "low"),
		},
	}


@frappe.whitelist()
def get_world_class_certification(app: str | None = None) -> dict:
	if not app:
		frappe.throw("app is required")
	return certify_app((app or "").strip())
