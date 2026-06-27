# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import json
import os

import frappe
from frappe.utils import get_bench_path

from omnexa_core.core_gap_register import get_gap_status
from omnexa_core.core_global_benchmark import get_global_core_score


@frappe.whitelist()
def export_core_global_audit() -> dict:
	"""Export live IC score + gap register for omnexa_core certification."""
	frappe.only_for("System Manager")
	root = os.path.join(get_bench_path(), "Documentation", "2026-06-25", "certificates", "omnexa_core")
	os.makedirs(root, exist_ok=True)
	score = get_global_core_score()
	gaps = get_gap_status()
	for name, payload in (("LIVE_SCORE.json", score), ("GAP_REGISTER.json", gaps)):
		with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
			json.dump(payload, fh, ensure_ascii=False, indent=2)
	return {
		"path": root,
		"weighted_score": score.get("weighted_score"),
		"gaps_open": gaps.get("gaps_open"),
		"global_leader_gate": score.get("global_leader_gate"),
	}
