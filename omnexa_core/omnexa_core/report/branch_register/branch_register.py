# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `branch_name`, `branch_code`, `status`, `company`, `branch_demo_activity`
		FROM `tabBranch`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Branch Name"), "fieldname": "branch_name", "fieldtype": "Data", "width": 120},
		{"label": _("Branch Code"), "fieldname": "branch_code", "fieldtype": "Data", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "width": 120},
		{"label": _("Branch Demo Activity"), "fieldname": "branch_demo_activity", "fieldtype": "Select", "width": 120}
	]
	return columns, data
