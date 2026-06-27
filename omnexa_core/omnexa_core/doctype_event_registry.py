# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Curated DocType lists for global hooks (replaces doc_events['*'])."""

from __future__ import annotations

# Business documents that commonly carry company/branch/currency fields.
OMNEXA_GLOBAL_COMPLIANCE_DOCTYPES = [
	"Sales Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Journal Entry",
	"Delivery Note",
	"Purchase Receipt",
	"Sales Order",
	"Purchase Order",
	"Quotation",
	"Supplier Quotation",
	"Stock Entry",
	"Stock Reconciliation",
	"Landed Cost Voucher",
	"Expense Claim",
	"Payroll Entry",
	"Asset",
	"Asset Depreciation Schedule",
	"GL Entry",
	"Budget",
	"Project",
	"Task",
	"Branch",
	"Company",
	"Customer",
	"Supplier",
	"Employee",
	"Item",
	"Warehouse",
	"Production Plan",
	"Work Order",
	"BOM",
	"Material Request",
	"Purchase Requisition",
]


def build_global_doc_event_handlers() -> dict:
	"""Return before_validate/validate handlers keyed per DocType."""
	handlers = {
		"before_validate": [
			"omnexa_core.omnexa_core.user_context.apply_company_branch_defaults",
			"omnexa_core.omnexa_core.compliance_guard.enforce_global_enterprise_compliance",
		],
		"validate": [
			"omnexa_core.omnexa_core.branch_access.enforce_branch_company_coherence",
			"omnexa_core.omnexa_core.branch_access.enforce_branch_access",
		],
	}
	out = {}
	for dt in OMNEXA_GLOBAL_COMPLIANCE_DOCTYPES:
		out[dt] = dict(handlers)
	return out
