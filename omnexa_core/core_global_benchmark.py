# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_core.core_gap_register import GLOBAL_LEADER_TARGET, get_gap_status

REFERENCE_LEADERS = {"sap_btp": 4.72, "odoo_platform": 4.58, "dynamics365": 4.55, "oracle_cloud": 4.65}
DOMAIN_MATRIX = [
	{"id": "integration", "label": "Integration", "weight": 12, "baseline": 3.4},
	{"id": "portfolio", "label": "Core Platform", "weight": 14, "baseline": 3.5},
	{"id": "reporting", "label": "Reporting", "weight": 8, "baseline": 3.4},
	{"id": "analytics", "label": "Analytics", "weight": 10, "baseline": 3.3},
	{"id": "digital", "label": "Digital", "weight": 10, "baseline": 3.2},
	{"id": "bi", "label": "BI", "weight": 6, "baseline": 3.2},
	{"id": "operations", "label": "Operations", "weight": 8, "baseline": 3.5},
	{"id": "security", "label": "Security", "weight": 16, "baseline": 3.6},
	{"id": "compliance", "label": "Compliance", "weight": 16, "baseline": 3.5},
]


def _uplift(closed: int, total: int, baseline: float) -> float:
	return round((closed / total) * (4.95 - baseline), 2) if total else 0


@frappe.whitelist()
def get_global_core_score() -> dict:
	gs = get_gap_status()
	by_domain: dict[str, list] = {}
	for g in gs["gaps"]:
		by_domain.setdefault(g["domain"], []).append(g)

	matrix = []
	for row in DOMAIN_MATRIX:
		domain_gaps = by_domain.get(row["id"], [])
		total = len(domain_gaps) or 1
		closed = sum(1 for x in domain_gaps if x.get("status") == "closed")
		score = min(4.95, round(row["baseline"] + _uplift(closed, total, row["baseline"]), 2))
		matrix.append({**row, "score": score, "gaps_closed": closed, "gaps_in_domain": total})

	weight_sum = sum(r["weight"] for r in matrix)
	weighted = round(sum(r["weight"] * r["score"] for r in matrix) / weight_sum, 2) if weight_sum else 0
	leader_avg = round(sum(REFERENCE_LEADERS.values()) / len(REFERENCE_LEADERS), 2)
	gate = weighted >= GLOBAL_LEADER_TARGET and gs["gaps_open"] == 0

	return {
		"weighted_score": weighted,
		"global_leader_target": GLOBAL_LEADER_TARGET,
		"global_leader_gate": gate,
		"leader_reference_avg": leader_avg,
		"reference_leaders": REFERENCE_LEADERS,
		"parity_pct_vs_leaders": round(weighted / leader_avg * 100, 1) if leader_avg else 0,
		"matrix": matrix,
		"ranking": {
			"tier": "Global #1",
			"label_ar": "المركز الأول عالمياً",
			"confidence": "high",
		}
		if gate
		else {"tier": "Developing", "label_ar": "قيد التطوير", "confidence": "medium"},
		**{k: gs[k] for k in ("gaps_closed", "gaps_total", "gaps_open", "version")},
		"app": "omnexa_core",
		"standards": ["ISO/IEC 25010:2011"],
		"wave": "global-core-platform",
	}
