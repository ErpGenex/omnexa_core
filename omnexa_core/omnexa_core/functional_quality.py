# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Functional quality gates — full test suite + gap backlog (Wave 7)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from frappe.utils import get_bench_path

SWEEP_PATH = Path(get_bench_path()) / "Docs/2026-08-24" / "WAVE7_TEST_SWEEP.json"
REPORTS_ROOT = Path(get_bench_path()) / "Docs/2026-08-24" / "reports"


def _load_sweep() -> dict | None:
	if not SWEEP_PATH.is_file():
		return None
	try:
		return json.loads(SWEEP_PATH.read_text(encoding="utf-8"))
	except Exception:
		return None


def get_app_test_result(app: str) -> dict | None:
	data = _load_sweep()
	if not data:
		return None
	for row in data.get("results") or []:
		if row.get("app") == app:
			return row
	return None


def gate_full_test_suite(app: str) -> bool:
	data = _load_sweep()
	if not data:
		return False
	results = data.get("results") or []
	if app == "omnexa_core":
		peers = [r for r in results if r.get("app") != "omnexa_core"]
		return len(peers) >= 51 and all(r.get("status") == "OK" for r in peers)
	row = get_app_test_result(app)
	if not row:
		return False
	return row.get("status") == "OK"


def _p0_open_items(text: str) -> list[str]:
	"""Return open P0 gap IDs from a 05_gap_backlog.md file."""
	lines = text.splitlines()
	in_p0 = False
	open_items: list[str] = []
	for line in lines:
		if re.match(r"^##\s+P0", line, re.I):
			in_p0 = True
			continue
		if in_p0 and line.startswith("## "):
			break
		if not in_p0 or not line.strip().startswith("|"):
			continue
		if re.match(r"^\|\s*ID\s*\|", line, re.I) or re.match(r"^\|[-:| ]+\|$", line):
			continue
		cells = [c.strip() for c in line.strip("|").split("|")]
		if len(cells) < 2:
			continue
		gap_id, desc = cells[0], cells[1]
		if not gap_id or gap_id.upper() == "NONE":
			continue
		row_text = " | ".join(cells)
		closed = (
			"~~" in row_text
			or "**Fixed**" in row_text
			or "**Closed**" in row_text
			or "Fixed —" in row_text
			or "Closed —" in row_text
			or row_text.strip().endswith("Fixed")
			or ("✅" in row_text and "Closed" in row_text)
		)
		if not closed and "None identified" not in row_text:
			open_items.append(gap_id)
	return open_items


def gate_no_open_p0_gaps(app: str) -> tuple[bool, list[str]]:
	path = REPORTS_ROOT / app / "05_gap_backlog.md"
	if not path.is_file():
		return True, []
	open_items = _p0_open_items(path.read_text(encoding="utf-8"))
	return len(open_items) == 0, open_items


def functional_gates(app: str) -> dict:
	p0_ok, p0_open = gate_no_open_p0_gaps(app)
	test_row = get_app_test_result(app)
	return {
		"full_test_suite": gate_full_test_suite(app),
		"no_open_p0_gaps": p0_ok,
		"p0_open_items": p0_open,
		"test_status": (test_row or {}).get("status"),
		"tests_ran": (test_row or {}).get("ran"),
		"sweep_available": bool(test_row),
	}
