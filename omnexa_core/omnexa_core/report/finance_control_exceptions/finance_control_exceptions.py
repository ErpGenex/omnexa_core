from __future__ import annotations

import json

import frappe
from frappe.utils import cint


def _normalize_hours(filters: dict) -> int:
	hours = cint((filters or {}).get("hours") or 24)
	return max(1, min(hours, 24 * 90))


def _parse_payload(raw: str) -> dict:
	if not (raw or "").strip():
		return {}
	try:
		parsed = json.loads(raw)
		return parsed if isinstance(parsed, dict) else {}
	except Exception:
		return {}


def execute(filters=None):
	filters = filters or {}
	hours = _normalize_hours(filters)
	rows = frappe.db.sql(
		"""
		SELECT name, creation, error
		FROM `tabError Log`
		WHERE method='Global Compliance Guard'
		  AND creation >= DATE_SUB(NOW(), INTERVAL %(hours)s HOUR)
		ORDER BY creation DESC
		LIMIT 3000
		""",
		{"hours": hours},
		as_dict=True,
	)

	data = []
	for r in rows:
		p = _parse_payload(r.get("error") or "")
		rule = str(p.get("rule_code") or "UNKNOWN")
		msg = str(p.get("message") or r.get("error") or "")
		is_finance = (
			rule.startswith("FINANCE_")
			or "SoD" in msg
			or "journal" in msg.lower()
			or "payment" in msg.lower()
			or "posting rule" in msg.lower()
		)
		if not is_finance:
			continue
		row = {
			"timestamp": r.get("creation"),
			"rule_code": rule,
			"reference_doctype": p.get("doctype"),
			"reference_name": p.get("name"),
			"company": p.get("company"),
			"branch": p.get("branch"),
			"message": msg,
		}
		data.append(row)

	if filters.get("company"):
		data = [d for d in data if d.get("company") == filters.get("company")]
	if filters.get("branch"):
		data = [d for d in data if d.get("branch") == filters.get("branch")]
	if filters.get("reference_doctype"):
		data = [d for d in data if d.get("reference_doctype") == filters.get("reference_doctype")]
	if filters.get("rule_code"):
		data = [d for d in data if d.get("rule_code") == filters.get("rule_code")]

	rule_counts = {}
	for d in data:
		rule_counts[d.get("rule_code") or "UNKNOWN"] = rule_counts.get(d.get("rule_code") or "UNKNOWN", 0) + 1
	top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:8]

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
		"data": {"labels": [x[0] for x in top_rules], "datasets": [{"name": "Finance Exceptions", "values": [x[1] for x in top_rules]}]},
		"type": "bar",
	} if top_rules else None
	summary = [
		{"label": "Exceptions", "value": len(data), "indicator": "Red" if data else "Green"},
		{"label": "Rules Hit", "value": len(rule_counts), "indicator": "Orange" if rule_counts else "Green"},
	]
	return columns, data, None, chart, summary

