# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""Minimal DB latency smoke (E5.1 starter) — not a full load test.

Repeated lightweight queries to estimate DB round-trip stability from the app tier.
For real load testing, use dedicated tools (e.g. locust/k6) against representative APIs.
For **P50/P95** on the same DB ping plus a light ORM round-trip, see ``omnexa_core.omnexa_core.ops_load_critical``.

Run::

    bench --site <site> execute omnexa_core.omnexa_core.ops_load_smoke.print_db_ping_latency_stats --kwargs '{\"iterations\": 200}'
"""

from __future__ import annotations

import json
import time

import frappe


@frappe.whitelist()
def print_db_ping_latency_stats(iterations: int = 100) -> str:
	frappe.only_for("System Manager")
	n = int(iterations)
	n = min(5000, max(10, n))
	t0 = time.perf_counter()
	for _ in range(n):
		frappe.db.sql("SELECT 1")
	dt = time.perf_counter() - t0
	payload = {
		"site": getattr(frappe.local, "site", None),
		"iterations": n,
		"total_sec": round(dt, 4),
		"per_query_ms": round(dt / n * 1000, 4) if n else None,
	}
	return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
