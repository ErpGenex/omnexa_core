# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.report_print.report_query_filters import (
	get_all_filters,
	policy_version_filters,
	prepare_filters,
	sql_conditions,
)



def execute(filters=None):
	columns = [
		{"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "width": 160},
		{"fieldname": "rule_code", "label": "Rule", "fieldtype": "Data", "width": 220},
		{"fieldname": "reference_doctype", "label": "DocType", "fieldtype": "Data", "width": 170},
		{"fieldname": "reference_name", "label": "Document", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 180},
		{"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 180},
		{"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch", "width": 160},
		{"fieldname": "message", "label": "Message", "fieldtype": "Small Text", "width": 420},
	]
	filters = prepare_filters(filters)
	conditions, params = sql_conditions(filters, "Error Log", date_field="creation", company=True, branch=True)
	rows = frappe.db.sql(
		f"""
		SELECT
			name, creation, error
		FROM `tabError Log`
		WHERE {' AND '.join(conditions)}
		GROUP BY 1
		ORDER BY creation DESC
		LIMIT 3000
		""",
		params,
		as_dict=True,
	)
	return columns, rows
