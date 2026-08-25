# Copyright (c) 2026, ErpGenEx
"""Wave 9 certification — activity PQC + per-activity bench matrix + E2E harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frappe
from frappe.utils import get_bench_path

from omnexa_core.omnexa_core.wave8_certification import certify_wave8


def _gate_activity_pqc() -> bool:
	try:
		from omnexa_core.omnexa_core.activity_pqc import activity_pqc_self_test

		return bool(activity_pqc_self_test().get("all_pass"))
	except Exception:
		return False


def _gate_activity_e2e_harness() -> bool:
	root = Path(get_bench_path()) / "apps" / "omnexa_core"
	return bool(list(root.glob("**/tests/test_wave9_activity_e2e.py")))


def _gate_bench_matrix_script() -> bool:
	path = Path(get_bench_path()) / "Docs" / "2026-08-25" / "scripts" / "wave9_activity_bench_matrix.py"
	return path.is_file()


def wave9_gates(app: str) -> dict[str, bool]:
	return {
		"activity_pqc_ready": _gate_activity_pqc(),
		"activity_e2e_harness": _gate_activity_e2e_harness(),
		"per_activity_bench_matrix": _gate_bench_matrix_script(),
	}


def certify_wave9(app: str) -> dict[str, Any]:
	base = certify_wave8(app)
	w9 = wave9_gates(app)
	wave9_ok = all(w9.values())
	full = bool(base.get("wave8_gate")) and wave9_ok
	level = "Wave 9 Operational Excellence"
	if full:
		pass
	elif base.get("wave8_gate"):
		level = "Wave 8 World Class"
	else:
		level = base.get("wave8_level") or "Wave 9 Pending"

	return {
		**base,
		"wave9_gates": w9,
		"wave9_gate": full,
		"wave9_level": level,
		"standards": base.get("standards", []) + ["ERPGenEx W9-PQC-2026", "ERPGenEx W9-E2E-2026"],
	}


@frappe.whitelist()
def get_wave9_certification(app: str | None = None) -> dict[str, Any]:
	if not app:
		frappe.throw("app is required")
	return certify_wave9((app or "").strip())
