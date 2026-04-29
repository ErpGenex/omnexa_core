# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled


_SKIP_DOCTYPES = {
	"DocType",
	"Custom Field",
	"Property Setter",
	"Patch Log",
	"Version",
	"Error Log",
	"File",
	"Module Def",
}


def _is_runtime_safe() -> bool:
	return not any(
		[
			getattr(frappe.flags, "in_install", False),
			getattr(frappe.flags, "in_migrate", False),
			getattr(frappe.flags, "in_patch", False),
			getattr(frappe.flags, "in_import", False),
		]
	)


def _strict_enabled() -> bool:
	# Default ON to satisfy enterprise governance baseline.
	return is_feature_enabled("global_enterprise_compliance_strict", default=True)


def _require_cost_center() -> bool:
	# Optional hardening; can be enabled globally when teams are ready.
	return is_feature_enabled("global_require_cost_center", default=False)


def enforce_global_enterprise_compliance(doc, method=None):
	"""Global non-destructive compliance guard for all business documents.

	Designed for cross-app usage without breaking framework internals:
	- Enforces company / branch / currency / FX coherence when fields exist.
	- Enforces due_date >= posting_date when both are present.
	- Optionally enforces cost_center on item rows via feature flag.
	"""
	if not _is_runtime_safe() or not _strict_enabled():
		return

	if not getattr(doc, "doctype", None) or doc.doctype in _SKIP_DOCTYPES:
		return

	meta = getattr(doc, "meta", None)
	if not meta:
		return

	has_field = meta.has_field

	if has_field("company") and not doc.get("company"):
		frappe.throw(_("Company is mandatory for compliance."), title=_("Compliance"))

	if has_field("branch") and not doc.get("branch"):
		frappe.throw(_("Branch is mandatory for compliance."), title=_("Compliance"))

	if has_field("currency"):
		currency = (doc.get("currency") or "").strip()
		if not currency:
			frappe.throw(_("Currency is mandatory for compliance."), title=_("Compliance"))
		if not frappe.db.exists("Currency", currency):
			frappe.throw(_("Currency {0} does not exist.").format(currency), title=_("Compliance"))

		if has_field("conversion_rate") and doc.get("company"):
			company_currency = frappe.db.get_value("Company", doc.get("company"), "default_currency")
			if company_currency and currency != company_currency and flt(doc.get("conversion_rate")) <= 0:
				frappe.throw(
					_("Conversion Rate must be greater than zero for foreign-currency transactions."),
					title=_("Compliance"),
				)

	if has_field("posting_date") and has_field("due_date") and doc.get("posting_date") and doc.get("due_date"):
		if getdate(doc.get("due_date")) < getdate(doc.get("posting_date")):
			frappe.throw(_("Due Date cannot be before Posting Date."), title=_("Compliance"))

	if not _require_cost_center():
		return

	# Optional strict dimensional governance on child rows.
	for table_field in ("items", "accounts"):
		if not has_field(table_field):
			continue
		for row in doc.get(table_field) or []:
			row_meta = getattr(row, "meta", None)
			if not row_meta:
				continue
			if row_meta.has_field("cost_center") and not row.get("cost_center"):
				frappe.throw(
					_("Row {0}: Cost Center is required by global policy.").format(row.idx),
					title=_("Compliance"),
				)
