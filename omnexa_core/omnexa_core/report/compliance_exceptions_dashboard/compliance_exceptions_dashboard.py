from __future__ import annotations

import json

import frappe
from frappe.utils import cint


def _normalize_hours(filters: dict) -> int:
	hours = cint((filters or {}).get("hours") or 24)
	return max(1, min(hours, 24 * 90))


def _parse_error_payload(row) -> dict:
	payload = (row.get("error") or "").strip()
	if not payload:
		return {}
	try:
		parsed = json.loads(payload)
		return parsed if isinstance(parsed, dict) else {}
	except Exception:
		return {}


def execute(filters=None):
	filters = filters or {}
	hours = _normalize_hours(filters)

	conditions = [
		"method = %(method)s",
		"creation >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)",
	]
	values = {"method": "Global Compliance Guard", "hours": hours}

	log_rows = frappe.db.sql(
		f"""
		SELECT
			name,
			creation,
			method,
			error
		FROM `tabError Log`
		WHERE {' AND '.join(conditions)}
		ORDER BY creation DESC
		LIMIT 2000
		""",
		values=values,
		as_dict=True,
	)

	data = []
	for row in log_rows:
		payload = _parse_error_payload(row)
		entry = {
			"timestamp": row.get("creation"),
			"rule_code": payload.get("rule_code") or "UNKNOWN",
			"reference_doctype": payload.get("doctype"),
			"reference_name": payload.get("name"),
			"company": payload.get("company"),
			"branch": payload.get("branch"),
			"message": payload.get("message") or (row.get("error") or ""),
		}
		data.append(entry)

	if filters.get("company"):
		data = [d for d in data if d.get("company") == filters.get("company")]
	if filters.get("branch"):
		data = [d for d in data if d.get("branch") == filters.get("branch")]
	if filters.get("reference_doctype"):
		data = [d for d in data if d.get("reference_doctype") == filters.get("reference_doctype")]
	if filters.get("rule_code"):
		data = [d for d in data if d.get("rule_code") == filters.get("rule_code")]

	rule_counts = {}
	doctype_counts = {}
	for d in data:
		rule = d.get("rule_code") or "UNKNOWN"
		rule_counts[rule] = int(rule_counts.get(rule) or 0) + 1
		dt = d.get("reference_doctype") or "Unknown DocType"
		doctype_counts[dt] = int(doctype_counts.get(dt) or 0) + 1

	top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:8]
	top_doctypes = sorted(doctype_counts.items(), key=lambda x: x[1], reverse=True)[:6]

	columns = [
		{"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "width": 160},
		{"fieldname": "rule_code", "label": "Rule", "fieldtype": "Data", "width": 220},
		{"fieldname": "reference_doctype", "label": "DocType", "fieldtype": "Data", "width": 170},
		{"fieldname": "reference_name", "label": "Document", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 180},
		{"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 180},
		{"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch", "width": 160},
		{"fieldname": "message", "label": "Message", "fieldtype": "Small Text", "width": 420},
	]

	chart = {
		"data": {
			"labels": [r[0] for r in top_rules],
			"datasets": [{"name": "Exceptions", "values": [r[1] for r in top_rules]}],
		},
		"type": "bar",
	} if top_rules else None

	report_summary = [
		{"label": "Exceptions", "value": len(data), "indicator": "Red" if data else "Green"},
		{"label": "Affected Rules", "value": len(rule_counts), "indicator": "Orange" if rule_counts else "Green"},
		{"label": "Affected Doctypes", "value": len(doctype_counts), "indicator": "Blue" if doctype_counts else "Green"},
	]
	if top_doctypes:
		report_summary.append(
			{
				"label": "Top DocType",
				"value": f"{top_doctypes[0][0]} ({top_doctypes[0][1]})",
				"indicator": "Orange",
			}
		)

	return columns, data, None, chart, report_summary
