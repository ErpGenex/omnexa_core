# Copyright (c) 2026, ErpGenEx
"""Role visibility policy for vertical workcenter / role portals."""

from __future__ import annotations

import frappe

ADMIN_ROLES = frozenset({"Administrator", "System Manager", "Company Admin"})

# Frappe roles granted access to each default journey portal (plus admins see all).
DEFAULT_PORTAL_FRAPPE_ROLES: dict[str, list[str]] = {
	"executive-dashboard": ["System Manager", "Company Admin"],
	"operations-desk": ["System Manager", "Company Admin", "Desk User"],
	"finance-desk": ["System Manager", "Company Admin", "Accounts User", "Accounts Manager"],
	"customer-portal": ["System Manager", "Company Admin"],
	"analytics-dashboard": ["System Manager", "Company Admin", "Desk User"],
}


def _valid_roles(roles: list[str]) -> list[str]:
	existing = set(frappe.get_all("Role", pluck="name") or [])
	out: list[str] = []
	for role in roles:
		if role in existing and role not in out:
			out.append(role)
	if not out:
		out = ["System Manager"]
	return out


def frappe_roles_for_portal_key(role_key: str) -> list[str]:
	return _valid_roles(DEFAULT_PORTAL_FRAPPE_ROLES.get(role_key, ["System Manager", "Company Admin"]))


def is_portal_admin(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(ADMIN_ROLES.intersection(set(frappe.get_roles(user) or [])))


def user_can_see_portal(portal: dict, user_roles: set[str] | None = None, *, is_admin: bool | None = None) -> bool:
	if is_admin is None:
		is_admin = is_portal_admin()
	if is_admin:
		return True
	if portal.get("exists") is False:
		return False
	user_roles = user_roles or set(frappe.get_roles() or [])
	allowed_roles = portal.get("roles") or []
	if not allowed_roles:
		return True
	return bool(user_roles.intersection(allowed_roles))


def filter_grouped_portals_for_user(
	groups: list[dict] | None,
	user: str | None = None,
) -> list[dict]:
	user = user or frappe.session.user
	is_admin = is_portal_admin(user)
	user_roles = set(frappe.get_roles(user) or [])
	filtered: list[dict] = []
	for group in groups or []:
		portals = []
		for portal in group.get("portals") or []:
			if user_can_see_portal(portal, user_roles, is_admin=is_admin):
				item = dict(portal)
				item["allowed"] = True
				portals.append(item)
		if portals:
			filtered.append({**group, "portals": portals})
	return filtered


def annotate_portal_access(portals: list[dict]) -> list[dict]:
	is_admin = is_portal_admin()
	user_roles = set(frappe.get_roles() or [])
	out: list[dict] = []
	for portal in portals:
		item = dict(portal)
		item["allowed"] = user_can_see_portal(item, user_roles, is_admin=is_admin)
		out.append(item)
	return out
