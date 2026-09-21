# Copyright (c) 2026, ErpGenEx
"""In-app website → Desk portal bridge (no Next.js)."""

from __future__ import annotations

import frappe
from urllib.parse import quote

from frappe import _


def bridge_to_desk_portal(*, desk_page: str, login_redirect: str | None = None, title: str | None = None):
	"""
	Redirect Guest to login, authenticated users to /app/<desk_page>.
	Call from www/<slug>/portal.py get_context.
	"""
	if not desk_page:
		frappe.throw(_("Portal page is not configured"))

	target = f"/app/{desk_page.lstrip('/')}"
	if frappe.session.user == "Guest":
		nxt = login_redirect or target
		frappe.local.flags.redirect_location = f"/login?redirect-to={quote(nxt)}"
		raise frappe.Redirect

	frappe.local.flags.redirect_location = target
	raise frappe.Redirect
