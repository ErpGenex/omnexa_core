# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `product_type_name`, `pos_label`, `show_in_pos`, `sort_order`
		FROM `tabProduct Type`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Product Type"), "fieldname": "product_type_name", "fieldtype": "Select", "width": 120},
		{"label": _("POS Label"), "fieldname": "pos_label", "fieldtype": "Data", "width": 120},
		{"label": _("Show in Retail POS"), "fieldname": "show_in_pos", "fieldtype": "Check", "width": 120},
		{"label": _("Sort Order"), "fieldname": "sort_order", "fieldtype": "Int", "width": 120}
	]
	return columns, data
