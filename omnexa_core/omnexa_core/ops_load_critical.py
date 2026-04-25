# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""E5.1 — دخان حمل خفيف مع **نِسَب مئوية** (P50/P95) لمسار DB من طبقة التطبيق.

ليس بديلاً عن k6/Locust على واجهات حقيقية؛ يُستخدم كأدلة أولية وخط أساس قبل/بعد تحسين.

Run::

    bench --site <site> execute omnexa_core.omnexa_core.ops_load_critical.print_critical_load_report \\
        --kwargs '{\"iterations\": 300, \"include_app_roundtrip\": 1}'
"""

from __future__ import annotations

import json
import statistics
import time
from typing import Any

import frappe
from frappe.utils import cint, get_bench_path


def _percentile_ms(sorted_ms: list[float], p: float) -> float | None:
	if not sorted_ms:
		return None
	if len(sorted_ms) == 1:
		return sorted_ms[0]
	k = (len(sorted_ms) - 1) * (p / 100.0)
	f = int(k)
	c = min(f + 1, len(sorted_ms) - 1)
	if f == c:
		return sorted_ms[f]
	return sorted_ms[f] + (sorted_ms[c] - sorted_ms[f]) * (k - f)


def _sample_db_ping(n: int) -> list[float]:
	times: list[float] = []
	for _ in range(n):
		t0 = time.perf_counter()
		frappe.db.sql("SELECT 1")
		times.append(time.perf_counter() - t0)
	return times


def _sample_app_roundtrip(n: int) -> list[float]:
	"""قراءة خفيفة عبر ORM (جدول صغير نسبياً)."""
	times: list[float] = []
	for _ in range(n):
		t0 = time.perf_counter()
		frappe.db.count("User", {"enabled": 1})
		times.append(time.perf_counter() - t0)
	return times


def collect_critical_load_stats(iterations: int = 200, include_app_roundtrip: bool = True) -> dict[str, Any]:
	n = int(iterations)
	n = min(3000, max(20, n))

	db_samples = _sample_db_ping(n)
	db_ms = sorted(x * 1000 for x in db_samples)

	out: dict[str, Any] = {
		"site": getattr(frappe.local, "site", None),
		"iterations": n,
		"db_ping_ms": {
			"mean": round(statistics.mean(db_ms), 4),
			"p50": round(_percentile_ms(db_ms, 50) or 0, 4),
			"p95": round(_percentile_ms(db_ms, 95) or 0, 4),
			"max": round(max(db_ms), 4),
		},
	}

	if include_app_roundtrip:
		app_samples = _sample_app_roundtrip(min(n, 500))
		app_ms = sorted(x * 1000 for x in app_samples)
		out["app_count_user_ms"] = {
			"iterations": len(app_samples),
			"mean": round(statistics.mean(app_ms), 4),
			"p50": round(_percentile_ms(app_ms, 50) or 0, 4),
			"p95": round(_percentile_ms(app_ms, 95) or 0, 4),
			"max": round(max(app_ms), 4),
		}

	return out


@frappe.whitelist()
def print_critical_load_report(iterations: int = 200, include_app_roundtrip: int = 1) -> str:
	frappe.only_for("System Manager")
	payload = collect_critical_load_stats(
		iterations=iterations,
		include_app_roundtrip=bool(cint(include_app_roundtrip)),
	)
	return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


@frappe.whitelist()
def export_critical_load_report_file(iterations: int = 200, include_app_roundtrip: int = 1) -> dict[str, Any]:
	"""يكتب JSON تحت ``logs/load_reports/<site>_<UTC>.json``."""
	from datetime import datetime, timezone
	from pathlib import Path

	frappe.only_for("System Manager")
	body = print_critical_load_report(iterations=iterations, include_app_roundtrip=include_app_roundtrip)
	base = Path(get_bench_path()) / "logs" / "load_reports"
	base.mkdir(parents=True, exist_ok=True)
	stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
	site = getattr(frappe.local, "site", "site")
	out = base / f"{site}_{stamp}.json"
	out.write_text(body, encoding="utf-8")
	return {"ok": True, "path": str(out)}
