# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Inject Omnexa license snapshot into Desk boot (client-side navigation guard)."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.omnexa_license import get_omnexa_license_snapshot


def inject_omnexa_license_boot(bootinfo) -> None:
	"""Called from ``boot_session`` after core boot data is loaded."""
	if frappe.session.user == "Guest":
		return

	enforce = frappe.conf.get("omnexa_license_enforce") in (1, True, "1", "true", "True")
	bootinfo.omnexa_license_enforce = bool(enforce)
	bootinfo.omnexa_license_by_app = get_omnexa_license_snapshot()
	bootinfo.omnexa_marketplace_route = "/app/erpgenex-marketplace"
	# Safe Desk paths (always reachable to activate / read help)
	bootinfo.omnexa_license_safe_route_hints = (
		"erpgenex-marketplace",
		"marketplace",
	)


@frappe.whitelist()
def get_omnexa_license_snapshot_for_desk():
	"""Refresh license snapshot after activate/revoke (any logged-in user)."""
	if frappe.session.user == "Guest":
		frappe.throw(frappe._("Login required"), frappe.AuthenticationError)
	return {
		"omnexa_license_by_app": get_omnexa_license_snapshot(),
		"omnexa_license_enforce": frappe.conf.get("omnexa_license_enforce")
		in (1, True, "1", "true", "True"),
	}
