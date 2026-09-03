# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `company_name`, `abbr`, `status`, `default_currency`
		FROM `tabCompany`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Legal Name"), "fieldname": "company_name", "fieldtype": "Data", "width": 120},
		{"label": _("Abbreviation"), "fieldname": "abbr", "fieldtype": "Data", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120},
		{"label": _("Default Currency"), "fieldname": "default_currency", "fieldtype": "Link", "width": 120}
	]
	return columns, data
