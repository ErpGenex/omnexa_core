from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.event_dispatcher import get_event_pipeline_health


def execute(filters=None):
	filters = filters or {}
	hours = int(filters.get("hours") or 24)
	hours = max(1, min(720, hours))

	health = get_event_pipeline_health(hours=hours)
	counts = health.get("status_counts") or {}
	columns = [
		{"fieldname": "window_hours", "label": "Window (Hours)", "fieldtype": "Int", "width": 130},
		{"fieldname": "provider", "label": "Provider", "fieldtype": "Data", "width": 160},
		{"fieldname": "received", "label": "Received", "fieldtype": "Int", "width": 110},
		{"fieldname": "processed", "label": "Processed", "fieldtype": "Int", "width": 110},
		{"fieldname": "error", "label": "Error", "fieldtype": "Int", "width": 90},
		{"fieldname": "rejected", "label": "Rejected", "fieldtype": "Int", "width": 100},
		{"fieldname": "duplicate", "label": "Duplicate", "fieldtype": "Int", "width": 100},
		{"fieldname": "dead_letter_count", "label": "Dead Letter", "fieldtype": "Int", "width": 120},
	]
	data = [
		{
			"window_hours": int(health.get("window_hours") or hours),
			"provider": str(health.get("provider") or "erpgenex_core"),
			"received": int(counts.get("Received") or 0),
			"processed": int(counts.get("Processed") or 0),
			"error": int(counts.get("Error") or 0),
			"rejected": int(counts.get("Rejected") or 0),
			"duplicate": int(counts.get("Duplicate") or 0),
			"dead_letter_count": int(health.get("dead_letter_count") or 0),
		}
	]
	chart = {
		"data": {
			"labels": ["Received", "Processed", "Error", "Dead Letter"],
			"datasets": [
				{
					"name": "Events",
					"values": [
						data[0]["received"],
						data[0]["processed"],
						data[0]["error"],
						data[0]["dead_letter_count"],
					],
				}
			],
		},
		"type": "bar",
	}
	report_summary = [
		{"value": data[0]["processed"], "label": "Processed", "indicator": "Green"},
		{"value": data[0]["error"], "label": "Errors", "indicator": "Red" if data[0]["error"] else "Green"},
		{
			"value": data[0]["dead_letter_count"],
			"label": "Dead Letter",
			"indicator": "Red" if data[0]["dead_letter_count"] else "Green",
		},
	]
	return columns, data, None, chart, report_summary
