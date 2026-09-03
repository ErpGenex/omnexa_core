# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `event_name`, `source_doctype`, `source_docname`, `webhook_event_log`, `retry_attempt`
		FROM `tabEvent Dead Letter`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Event Name"), "fieldname": "event_name", "fieldtype": "Data", "width": 120},
		{"label": _("Source DocType"), "fieldname": "source_doctype", "fieldtype": "Data", "width": 120},
		{"label": _("Source Docname"), "fieldname": "source_docname", "fieldtype": "Data", "width": 120},
		{"label": _("Webhook Event Log"), "fieldname": "webhook_event_log", "fieldtype": "Link", "width": 120},
		{"label": _("Retry Attempt"), "fieldname": "retry_attempt", "fieldtype": "Int", "width": 120}
	]
	return columns, data
