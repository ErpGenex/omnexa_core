# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""Read-only operations snapshot for weekly Error budget / SLO review.

Run (from bench root)::

    bench --site <site> execute omnexa_core.omnexa_core.ops_weekly_health.print_ops_weekly_health_report
"""

import json
from collections.abc import Mapping

import frappe
from frappe.utils import add_to_date, cint, now_datetime
from frappe.utils.background_jobs import get_queue, get_queue_list
from frappe.utils.scheduler import get_scheduler_status


def collect_ops_health() -> dict:
	"""Return a small JSON-serializable dict: errors, scheduler, queue depths (no side effects)."""
	now = now_datetime()
	since_24h = add_to_date(now, days=-1, as_datetime=True)
	since_7d = add_to_date(now, days=-7, as_datetime=True)

	data: dict = {
		"site": getattr(frappe.local, "site", None),
		"errors_error_log_24h": 0,
		"errors_error_log_7d": 0,
		"top_error_methods": [],
		"scheduler": None,
		"queues": {},
	}

	# Error Log: primary signal for "operational noise" in weekly review
	if frappe.db.has_table("Error Log"):
		data["errors_error_log_24h"] = frappe.db.count(
			"Error Log",
			{"creation": (">", since_24h)},
		)
		data["errors_error_log_7d"] = frappe.db.count(
			"Error Log",
			{"creation": (">", since_7d)},
		)
		data["top_error_methods"] = frappe.db.sql(
			"""
			SELECT `method` AS method, COUNT(*) AS count
			FROM `tabError Log`
			GROUP BY `method`
			ORDER BY count DESC
			LIMIT 15
			""",
			as_dict=True,
		) or []

	try:
		data["scheduler"] = get_scheduler_status()
	except Exception as e:
		data["scheduler"] = {"_error": repr(e)}

	queues: dict = {}
	try:
		for name in get_queue_list():
			q = get_queue(name)
			queues[name] = {"pending": cint(q.count)}
	except Exception as e:
		queues = {"_error": repr(e)}
	data["queues"] = queues
	return data


def _normalize_for_json(obj: object) -> object:
	"""Make scheduler status and similar Mapping objects JSON-safe."""
	if isinstance(obj, Mapping):
		return {k: _normalize_for_json(v) for k, v in obj.items()}
	if isinstance(obj, (list, tuple)):
		return [_normalize_for_json(x) for x in obj]
	return obj


@frappe.whitelist()
def print_ops_weekly_health_report() -> str:
	"""System Manager: one JSON line (bench execute prints the return value; use for weekly Error budget)."""
	frappe.only_for("System Manager")
	payload = _normalize_for_json(collect_ops_health())
	return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
