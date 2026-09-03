# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `case_doctype`, `case_name`, `document_type`, `verification_status`
		FROM `tabFinance Borrower Case Document`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Case DocType"), "fieldname": "case_doctype", "fieldtype": "Link", "width": 120},
		{"label": _("Case"), "fieldname": "case_name", "fieldtype": "Data", "width": 120},
		{"label": _("Document Type"), "fieldname": "document_type", "fieldtype": "Link", "width": 120},
		{"label": _("Verification Status"), "fieldname": "verification_status", "fieldtype": "Select", "width": 120}
	]
	return columns, data
