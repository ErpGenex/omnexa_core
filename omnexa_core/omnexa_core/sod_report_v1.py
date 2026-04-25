# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""SoD v1 — role-pair conflict snapshot (E4.1 starter, DEVELOPMENT_PLAN_95_A_PLUS_AR.md).

Detects enabled users who hold **both** roles in any configured pair (conservative defaults).
Extend via site_config ``omnexa_sod_v1_role_pairs``: list of ``[role_a, role_b]`` strings.

Run::

    bench --site <site> execute omnexa_core.omnexa_core.sod_report_v1.print_sod_v1_role_conflict_report
"""

from __future__ import annotations

import json
from typing import Any

import frappe

# ERPNext-style role names; override entirely via site_config if needed.
_DEFAULT_ROLE_PAIRS: tuple[tuple[str, str], ...] = (
	("Accounts Manager", "Purchase Manager"),
	("Sales Manager", "Purchase Manager"),
)


def _configured_role_pairs() -> list[tuple[str, str]]:
	raw = frappe.conf.get("omnexa_sod_v1_role_pairs")
	if not raw:
		return list(_DEFAULT_ROLE_PAIRS)
	out: list[tuple[str, str]] = []
	for row in raw:
		if isinstance(row, (list, tuple)) and len(row) == 2:
			a, b = str(row[0]).strip(), str(row[1]).strip()
			if a and b:
				out.append((a, b))
	return out or list(_DEFAULT_ROLE_PAIRS)


def collect_sod_v1_role_conflicts() -> list[dict[str, Any]]:
	"""Return list of {user, role_a, role_b} for users matching any configured toxic pair."""
	pairs = _configured_role_pairs()
	conflicts: list[dict[str, Any]] = []
	for user in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"):
		if user in ("Administrator", "Guest"):
			continue
		roles = set(frappe.get_roles(user))
		for a, b in pairs:
			if a in roles and b in roles:
				conflicts.append({"user": user, "role_a": a, "role_b": b})
	return conflicts


@frappe.whitelist()
def print_sod_v1_role_conflict_report() -> str:
	frappe.only_for("System Manager")
	conflicts = collect_sod_v1_role_conflicts()
	payload = {
		"site": getattr(frappe.local, "site", None),
		"pairs_checked": _configured_role_pairs(),
		"conflicts": conflicts,
		"conflict_count": len(conflicts),
	}
	return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
