from __future__ import annotations

import frappe


@frappe.whitelist(allow_guest=True)
def sessions_get():
	"""Stable boot endpoint for Desk.

	Frappe Desk calls `frappe.sessions.get` to obtain boot info.
	On some environments, that method is not registered as whitelisted (packaging mismatch),
	which breaks Desk loading. We keep a whitelisted shim here and delegate to the upstream
	implementation.
	"""
	# Import locally to ensure frappe has initialized request/session.
	from frappe.sessions import get as _get

	return _get()

