# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Read-only platform health snapshot for ops / certification."""

from __future__ import annotations

import frappe

from omnexa_core.core_gap_register import get_gap_status
from omnexa_core.core_global_benchmark import get_global_core_score
from omnexa_core.omnexa_core.omnexa_mfa_gate import get_mfa_compliance_status
from omnexa_core.omnexa_core.ops_weekly_health import collect_ops_health


@frappe.whitelist(methods=["GET", "POST"])
def get_platform_health() -> dict:
	if frappe.session.user == "Guest":
		frappe.throw("Login required.", frappe.PermissionError)

	score = get_global_core_score()
	gaps = get_gap_status()
	ops = collect_ops_health()
	mfa = {"ok": False, "skipped": True}
	if "System Manager" in (frappe.get_roles() or []):
		try:
			mfa = get_mfa_compliance_status()
		except Exception as exc:
			mfa = {"ok": False, "error": str(exc)}

	return {
		"ok": True,
		"app": "omnexa_core",
		"site": frappe.local.site,
		"benchmark": {
			"weighted_score": score.get("weighted_score"),
			"global_leader_gate": score.get("global_leader_gate"),
			"gaps_open": gaps.get("gaps_open"),
			"gaps_closed": gaps.get("gaps_closed"),
			"ranking": score.get("ranking"),
		},
		"operations": ops,
		"mfa": mfa,
	}
