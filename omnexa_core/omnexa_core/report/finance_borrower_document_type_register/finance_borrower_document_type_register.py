# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `document_code`, `document_name_en`, `document_name_ar`
		FROM `tabFinance Borrower Document Type`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Document Code"), "fieldname": "document_code", "fieldtype": "Data", "width": 120},
		{"label": _("Document Name (EN)"), "fieldname": "document_name_en", "fieldtype": "Data", "width": 120},
		{"label": _("Document Name (AR)"), "fieldname": "document_name_ar", "fieldtype": "Data", "width": 120}
	]
	return columns, data
