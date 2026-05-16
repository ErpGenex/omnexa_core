# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Gap analysis vs international real-estate / asset-management practice.

Reference frameworks (non-exhaustive):
- IPMS / RICS (property measurement & development)
- IFRS 16 / IPSAS (lease accounting)
- ISO 55000 / ISO 14224 (asset management & maintenance taxonomy)
- CRM pipeline (lead → reservation → contract)
"""

from __future__ import annotations

from typing import Any

import frappe

MATURITY_TARGET_PERCENT = 90.0


def _doctype_inventory(module: str) -> list[str]:
	return frappe.get_all("DocType", filters={"module": module, "istable": 0}, pluck="name", order_by="name asc")


def audit_erpgenex_verticals() -> dict[str, Any]:
	"""Return structured coverage matrix for PMC / RE Dev / RE Sales / Maintenance."""
	modules = {
		"property_mgmt": {
			"module": "Erpgenex Property Mgmt",
			"frameworks": ["IPMS", "IFRS 16", "IPSAS", "RICS (owner reporting)"],
			"implemented": [
				"Portfolio registry (PMC Property / Unit)",
				"Lease contracts with term validation",
				"Overlapping active lease guard per unit",
				"CAM budget + billing runs",
				"Owner statements with collection/remittance balance check",
				"Company / branch coherence",
				"PMC Rent Roll script report with aging buckets",
				"PMC Occupancy Summary (IPMS-style leasable vs leased)",
				"Rental Escalation Rule with daily apply job",
				"PMC Lease Liability Schedule (IFRS 16 lessee bridge)",
				"Tenant portal API (leases, billing, maintenance)",
				"Lease document checklist + contract amendments",
				"Indexation method on lease",
				"Termination notice workflow",
				"PMC Management Fee Summary report",
				"E2E rental lifecycle integration test (QA-01)",
			],
			"gaps": [
				"Online payment gateway (Payment Request) integration",
			],
			"roadmap": [
				"IFRS 16 automatic journal entry posting",
				"Multi-currency FX revaluation engine",
			],
		},
		"re_development": {
			"module": "Erpgenex Realestate Dev",
			"frameworks": ["RICS development lifecycle", "BOQ / cost control", "Snagging / handover"],
			"implemented": [
				"Land parcel + development project",
				"BOQ + budget with project/BOQ linkage",
				"Unit inventory with status",
				"Handover package",
				"Company coherence on inventory/budget",
				"RICS / IPMS measurement fields (GIA, NIA) on RE Unit Inventory",
				"RE Project EV report (BAC vs earned value on budget lines)",
				"RE Handover Snag Item child table with critical-gate sign-off",
				"RE Subcontract Commitment register",
				"RE Permit Milestone with overdue scheduler",
				"Inventory vs booking status guard",
				"E2E development lifecycle integration test (QA-03)",
			],
			"gaps": [],
			"roadmap": [
				"S-curve chart / earned-value time-phasing",
				"Procurement PO integration for commitments",
			],
		},
		"re_sales": {
			"module": "Erpgenex Realestate Sales",
			"frameworks": ["CRM funnel", "Reservation / SPA practice", "Anti-double-sale controls"],
			"implemented": [
				"Sales lead with status funnel (New → Won/Lost)",
				"Unit reservation with active conflict check",
				"Reservation expiry validation",
				"Sales booking with inventory status sync",
				"Parallel pipeline booking prevention",
				"Registered booking immutability",
				"Lead ↔ development project / unit inventory links",
				"Campaign field on lead (ROI reporting foundation)",
				"Scheduled reservation expiry (daily via omnexa_core registry)",
				"Sales Commission Schedule on booking",
				"Sales Payment Plan (SPA installments) on booking",
				"Sales Booking → Sales Invoice on Registered",
				"Per-installment Sales Invoice helper",
				"Campaign ROI report",
				"Sales Commission Accrual report",
				"Signature status + amendments on booking",
				"E2E sales pipeline integration test (QA-02)",
			],
			"gaps": [],
			"roadmap": [
				"E-signature provider integration (DocuSign, etc.)",
			],
		},
		"maintenance_core": {
			"module": "ERPGenEx Maintenance Core",
			"frameworks": ["ISO 55000", "ISO 14224 taxonomy", "CMMS KPIs"],
			"implemented": [
				"Service request → work order flow",
				"SLA profiles",
				"PM schedules",
				"ISO 14224-style classification codes on work orders",
				"Labor/material actuals + downtime",
				"Reliability KPI script report",
				"PMC Property Unit / RE Unit Inventory links on CSR and Core WO",
				"Core Reliability by Classification (MTBF/MTTR rollup)",
				"Core Contractor Scorecard report",
				"Technician portal API for assigned work orders",
				"Batch material issue across work orders",
				"Contractor (Supplier) link on Core Work Order",
				"E2E maintenance CSR→WO integration test (QA-04)",
			],
			"gaps": [],
			"roadmap": [
				"Native mobile app / offline dispatch",
			],
		},
	}

	for key, block in modules.items():
		mod = block["module"]
		block["doctypes"] = _doctype_inventory(mod)
		block["workspace"] = frappe.db.get_value("Workspace", {"module": mod}, "name") or ""
		block["workspace_links"] = frappe.db.count("Workspace Link", {"parent": block["workspace"]}) if block["workspace"] else 0

	scores = {}
	for key, block in modules.items():
		impl = len(block["implemented"])
		gap = len(block.get("gaps") or [])
		scores[key] = round(100.0 * impl / max(1, impl + gap), 1)

	all_at_target = all(s >= MATURITY_TARGET_PERCENT for s in scores.values())

	return {
		"modules": modules,
		"maturity_scores_percent": scores,
		"maturity_target_percent": MATURITY_TARGET_PERCENT,
		"maturity_target_met": all_at_target,
		"summary": (
			"Release-scope maturity meets the "
			f"{MATURITY_TARGET_PERCENT:.0f}% target for all four verticals. "
			"See roadmap items for post-release enhancements."
			if all_at_target
			else "Some verticals still have release-scope gaps — see gaps per module."
		),
	}


@frappe.whitelist()
def get_vertical_audit_report() -> dict[str, Any]:
	frappe.only_for("System Manager")
	return audit_erpgenex_verticals()


@frappe.whitelist()
def get_vertical_audit_html() -> str:
	"""HTML summary for System Manager desk (GAP-X-08)."""
	frappe.only_for("System Manager")
	data = audit_erpgenex_verticals()
	lines = [
		"<h3>ERPGenex vertical maturity</h3>",
		f"<p>Target: {data.get('maturity_target_percent')}% — "
		f"{'<b>met</b>' if data.get('maturity_target_met') else '<b>not met</b>'}</p>",
		"<table border='1' cellpadding='6'><tr><th>Module</th><th>Score %</th></tr>",
	]
	for key, score in data.get("maturity_scores_percent", {}).items():
		lines.append(f"<tr><td>{key}</td><td>{score}</td></tr>")
	lines.append("</table><p>" + frappe.utils.escape_html(data.get("summary", "")) + "</p>")
	for key, block in data.get("modules", {}).items():
		lines.append(f"<h4>{frappe.utils.escape_html(key)}</h4>")
		if block.get("gaps"):
			lines.append("<ul>")
			for g in block["gaps"]:
				lines.append(f"<li><b>Gap:</b> {frappe.utils.escape_html(g)}</li>")
			lines.append("</ul>")
		if block.get("roadmap"):
			lines.append("<p><i>Roadmap:</i></p><ul>")
			for g in block["roadmap"]:
				lines.append(f"<li>{frappe.utils.escape_html(g)}</li>")
			lines.append("</ul>")
	return "".join(lines)
