# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Heuristic Desk filters when Script Report Python has no filters.get()."""

from __future__ import annotations

from pathlib import Path

from omnexa_core.omnexa_core.report_print.report_filter_specs import (
	INFERRED_FILTER_TEMPLATES,
)

_POLICY_STATUS_FILTER = {
	"fieldname": "policy_status",
	"fieldtype": "Select",
	"label": "Policy Status",
	"options": "\n\nPENDING_APPROVAL\nAPPROVED\nREJECTED",
	"width": "160px",
}

# ref_doctype → ordered fieldnames
_REF_DOCTYPE_FIELDS: dict[str, list[str]] = {
	"Consumer Finance Case": ["from_date", "to_date"],
	"Consumer Collections Action": ["from_date", "to_date"],
	"Credit Decision Case": ["from_date", "to_date", "country_code"],
	"Mortgage Finance Case": ["company", "from_date", "to_date"],
	"Mortgage Finance Legal Case": ["company", "from_date", "to_date"],
	"SME Retail Finance Case": ["company", "from_date", "to_date"],
	"SME Portfolio Cluster": ["company"],
	"Vehicle Finance Case": ["company", "from_date", "to_date"],
	"Vehicle Finance Recovery Case": ["company", "from_date", "to_date"],
	"Vehicle Finance Insurance Policy": ["company"],
	"Project Contract": ["company", "branch", "project_contract"],
	"BOQ Item": ["company", "project_contract"],
	"Leasing Finance Contract": ["company", "from_date", "to_date"],
	"Leasing Finance Schedule": ["company", "from_date", "to_date"],
	"Leasing Finance Risk Snapshot": ["company", "from_date", "to_date"],
	"Factoring Invoice": ["company", "from_date", "to_date"],
	"Factoring Collection Event": ["company", "from_date", "to_date"],
	"Factoring Settlement Run": ["company", "from_date", "to_date"],
	"Factoring Debtor Exposure": ["company"],
	"Operational Compliance Mapping": ["company"],
	"Operational Risk Incident": ["company", "from_date", "to_date"],
	"Operational Loss Event": ["company", "from_date", "to_date"],
	"Operational Risk Control": ["company"],
	"PM WBS Task": ["company", "from_date", "to_date"],
	"Restaurant Order": ["company", "branch", "from_date", "to_date"],
	"Menu Item": ["company"],
	"Waste Log": ["company", "from_date", "to_date"],
	"Service Ticket": ["company", "from_date", "to_date"],
	"ALM Daily Run": ["company", "from_date", "to_date"],
	"ALM Position Snapshot": ["company"],
	"Compliance Control": ["company", "status", "risk_level"],
	"Compliance Evidence": ["company", "from_date", "to_date"],
	"Compliance Remediation": ["company", "status"],
	"Compliance Test Result": ["company", "from_date", "to_date"],
	"Compliance Control Test": ["company", "from_date", "to_date"],
	"Error Log": ["hours"],
}

_EXTRA_FIELD_TEMPLATES: dict[str, dict] = {
	"country_code": {
		"fieldname": "country_code",
		"fieldtype": "Data",
		"label": "Country Code",
		"width": "120px",
	},
	"project_contract": {
		"fieldname": "project_contract",
		"fieldtype": "Link",
		"label": "Project Contract",
		"options": "Project Contract",
		"width": "200px",
	},
	"status": {
		"fieldname": "status",
		"fieldtype": "Data",
		"label": "Status",
		"width": "140px",
	},
	"risk_level": {
		"fieldname": "risk_level",
		"fieldtype": "Data",
		"label": "Risk Level",
		"width": "140px",
	},
	"older_than_days": {
		"fieldname": "older_than_days",
		"fieldtype": "Int",
		"label": "Older Than (days)",
		"default": "30",
		"width": "120px",
	},
}

_POLICY_VERSION_DOCTYPES = frozenset(
	{
		"Consumer Finance Policy Version",
		"Credit Policy Version",
		"Credit Risk Policy Version",
		"Factoring Policy Version",
		"Finance Policy Version",
		"Mortgage Finance Policy Version",
		"Operational Risk Policy Version",
		"SME Retail Finance Policy Version",
		"Vehicle Finance Policy Version",
	}
)


def infer_filters_heuristic(
	ref_doctype: str | None,
	report_name: str | None,
	py_path: Path | None = None,
) -> list[dict]:
	"""Return Desk filter rows from ref_doctype / report name heuristics."""
	name = (report_name or "").lower()
	ref = (ref_doctype or "").strip()

	if "governance overview" in name or ref in _POLICY_VERSION_DOCTYPES:
		return [dict(_POLICY_STATUS_FILTER)]

	if "evidence aging" in name:
		return [dict(_EXTRA_FIELD_TEMPLATES["older_than_days"])]

	if ref == "Compliance Control":
		return [
			dict(INFERRED_FILTER_TEMPLATES["company"]),
			dict(_EXTRA_FIELD_TEMPLATES["status"]),
			dict(_EXTRA_FIELD_TEMPLATES["risk_level"]),
		]

	fieldnames = list(_REF_DOCTYPE_FIELDS.get(ref, []))
	if not fieldnames and ref:
		# Generic operational/financial doc with company+dates
		if any(x in ref for x in ("Case", "Contract", "Invoice", "Order", "Ticket", "Event")):
			fieldnames = ["company", "from_date", "to_date"]
		elif "Snapshot" in ref or "Schedule" in ref:
			fieldnames = ["company", "from_date", "to_date"]

	if not fieldnames:
		return []

	filters: list[dict] = []
	for fn in fieldnames:
		tpl = INFERRED_FILTER_TEMPLATES.get(fn) or _EXTRA_FIELD_TEMPLATES.get(fn)
		if tpl:
			filters.append(dict(tpl))
	return filters
