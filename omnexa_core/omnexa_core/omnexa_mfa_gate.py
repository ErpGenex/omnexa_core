# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Gradual MFA enforcement — see Documentation/System_Audit/2026-06-25/06_MFA_POLICY_AR.md."""

from __future__ import annotations

import frappe
from frappe import _

DEFAULT_REQUIRED_ROLES = ("System Manager", "Accounts Manager")

DESK_PATH_PREFIXES = ("/app", "/api/method/frappe.desk", "/api/method/frappe.client")


def _is_truthy(value) -> bool:
	return value in (1, True, "1", "true", "True", "yes", "on")


def _required_roles() -> set[str]:
	raw = frappe.conf.get("omnexa_mfa_required_roles")
	if isinstance(raw, (list, tuple, set)):
		return {str(x).strip() for x in raw if str(x).strip()}
	if isinstance(raw, str) and raw.strip():
		return {s.strip() for s in raw.split(",") if s.strip()}
	return set(DEFAULT_REQUIRED_ROLES)


def _user_requires_mfa(user: str) -> bool:
	if not user or user in ("Guest", "Administrator"):
		return False
	roles = set(frappe.get_roles(user) or [])
	return bool(roles & _required_roles())


def _is_desk_request() -> bool:
	path = (getattr(frappe.local, "request", None) and frappe.local.request.path) or ""
	return any(path.startswith(p) for p in DESK_PATH_PREFIXES)


def apply_omnexa_mfa_policy() -> dict:
	"""Enable Frappe 2FA and mark P0 roles — run once per site."""
	frappe.only_for("System Manager")
	from frappe.twofactor import toggle_two_factor_auth

	roles = sorted(_required_roles())
	frappe.db.set_single_value("System Settings", "enable_two_factor_auth", 1)
	toggle_two_factor_auth(1, roles=roles)
	frappe.db.commit()
	return {"ok": True, "enable_two_factor_auth": 1, "roles": roles}


@frappe.whitelist()
def get_mfa_compliance_status() -> dict:
	"""List P0-role users without active 2FA role mapping."""
	frappe.only_for("System Manager")
	from frappe.twofactor import two_factor_is_enabled_for_

	required = _required_roles()
	users = frappe.get_all("User", filters={"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]}, pluck="name")
	non_compliant = []
	for user in users:
		if not (_required_roles() & set(frappe.get_roles(user) or [])):
			continue
		if not two_factor_is_enabled_for_(user):
			non_compliant.append(user)
	return {
		"ok": True,
		"enforce": _is_truthy(frappe.conf.get("omnexa_mfa_enforce")),
		"required_roles": sorted(required),
		"system_2fa_enabled": bool(frappe.db.get_single_value("System Settings", "enable_two_factor_auth")),
		"non_compliant_users": non_compliant,
	}


def before_request():
	if frappe.session.user in ("Guest", "Administrator"):
		return
	if not _is_truthy(frappe.conf.get("omnexa_mfa_enforce")):
		return
	if not _is_desk_request():
		return
	if not _user_requires_mfa(frappe.session.user):
		return

	from frappe.twofactor import two_factor_is_enabled, two_factor_is_enabled_for_

	if not two_factor_is_enabled():
		return
	if two_factor_is_enabled_for_(frappe.session.user):
		return

	frappe.throw(
		_(
			"MFA is required for your role. Ask System Manager to complete MFA setup "
			"(User → Enable Two Factor Auth) or run apply_omnexa_mfa_policy."
		),
		frappe.PermissionError,
	)
