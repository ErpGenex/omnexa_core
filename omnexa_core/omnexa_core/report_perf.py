# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Report execution performance instrumentation."""

from __future__ import annotations

import time

import frappe

from omnexa_core.omnexa_core.structured_logging import log_event

def _slow_report_threshold() -> float:
	try:
		return float(frappe.conf.get("omnexa_slow_report_seconds") or 3.0)
	except Exception:
		return 3.0


def record_report_run(report_name: str, filters, result: dict, elapsed: float) -> None:
	row_count = 0
	if isinstance(result, dict) and isinstance(result.get("result"), list):
		row_count = len(result["result"])
	fields = {
		"report": report_name,
		"elapsed_ms": int(elapsed * 1000),
		"row_count": row_count,
		"filters": filters if isinstance(filters, dict) else None}
	if elapsed >= _slow_report_threshold():
		log_event("slow_report", level="warning", **fields)
	else:
		log_event("report_run", **fields)


def timed_report_run(run_fn, report_name, filters=None, **kwargs):
	start = time.perf_counter()
	result = run_fn(report_name, filters=filters, **kwargs)
	record_report_run(report_name, filters, result if isinstance(result, dict) else {}, time.perf_counter() - start)
	return result
