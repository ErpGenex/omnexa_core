# Copyright (c) 2026, ErpGenEx
"""Finance Workcenter — primary portal entry for all finance roles (replaces Demo Hub)."""

from __future__ import annotations

import frappe
from frappe import _

WORKCENTER_PAGE = "finance-workcenter"
LEGACY_DEMO_PAGE = "finance-demo-hub"
WORKCENTER_ROUTE = f"/app/{WORKCENTER_PAGE}"


def _is_admin_user(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Administrator", "Guest"):
		return user == "Administrator"
	return "System Manager" in (frappe.get_roles(user) or [])


def _finance_roles(user: str | None = None) -> set[str]:
	return {r for r in (frappe.get_roles(user) or []) if r.startswith("Finance ")}


def get_user_primary_portal_route(user: str | None = None) -> str:
	"""Default portal route for a finance user (non-admin → role servicing portal)."""
	user = user or frappe.session.user
	if _is_admin_user(user):
		return WORKCENTER_ROUTE
	from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_SPECS

	roles = set(frappe.get_roles(user) or [])
	for spec in ROLE_SPECS:
		if spec["role"] in roles:
			return spec.get("default_route") or WORKCENTER_ROUTE
	return WORKCENTER_ROUTE


def get_workcenter_context(user: str | None = None) -> dict:
	"""Payload for Workcenter page — admin vs role-scoped portal catalog."""
	user = user or frappe.session.user
	roles = frappe.get_roles(user) or []
	is_admin = _is_admin_user(user)
	finance_roles = _finance_roles(user)
	primary = get_user_primary_portal_route(user)

	from omnexa_core.omnexa_core.finance_demo.finance_portal_catalog import (
		CATEGORY_LABELS,
		get_portal_catalog,
	)

	catalog = get_portal_catalog(include_missing=0)
	if not is_admin:
		allowed = set(roles)
		catalog = [p for p in catalog if p.get("category") != "admin" and set(p.get("roles") or []) & allowed]

	groups: dict[str, list] = {}
	for row in catalog:
		groups.setdefault(row["category"], []).append(row)
	grouped = []
	for cat, portals in groups.items():
		labels = CATEGORY_LABELS.get(cat, {"ar": cat, "en": cat})
		grouped.append({"category": cat, "label_ar": labels["ar"], "label_en": labels["en"], "portals": portals})

	from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_SPECS

	role_label = ""
	for spec in ROLE_SPECS:
		if spec["role"] in roles:
			role_label = spec.get("title") or spec["role"]
			break

	return {
		"page": WORKCENTER_PAGE,
		"route": WORKCENTER_ROUTE,
		"primary_portal_route": primary,
		"is_admin": is_admin,
		"is_finance_user": bool(finance_roles),
		"portal_entry_mode": bool(finance_roles) and not is_admin,
		"role_label": role_label,
		"grouped_portals": grouped,
	}


def inject_finance_workcenter_boot(bootinfo) -> None:
	"""Desk boot — workcenter routing for finance users."""
	if frappe.session.user == "Guest":
		return
	ctx = get_workcenter_context()
	bootinfo.finance_workcenter = {
		"page": ctx["page"],
		"route": ctx["route"],
		"primary_portal_route": ctx["primary_portal_route"],
		"is_admin": ctx["is_admin"],
		"is_finance_user": ctx["is_finance_user"],
		"portal_entry_mode": ctx["portal_entry_mode"],
		"role_label": ctx.get("role_label") or "",
	}


def sync_workcenter_page_roles() -> None:
	"""Ensure finance roles can open Workcenter (filtered view)."""
	if not frappe.db.exists("Page", WORKCENTER_PAGE):
		return
	from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_SPECS, _ensure_role

	page = frappe.get_doc("Page", WORKCENTER_PAGE)
	# Remove stale Page Role rows when Role master is missing (fresh/partial sites).
	kept = [r for r in page.roles if r.role and frappe.db.exists("Role", r.role)]
	if len(kept) != len(page.roles):
		page.set("roles", [{"role": r.role} for r in kept])

	existing = {r.role for r in page.roles}
	all_roles = {"System Manager", "Finance Group Executive"}
	all_roles.update(s["role"] for s in ROLE_SPECS)
	changed = len(kept) != len(page.roles)
	for role in sorted(all_roles):
		if role != "System Manager":
			_ensure_role(role)
		if not frappe.db.exists("Role", role):
			continue
		if role not in existing:
			page.append("roles", {"role": role})
			changed = True
	if changed:
		page.flags.ignore_permissions = True
		page.save()


def ensure_workcenter_page() -> dict:
	"""Create or update Workcenter page metadata (idempotent)."""
	if frappe.db.exists("Page", WORKCENTER_PAGE):
		frappe.db.set_value("Page", WORKCENTER_PAGE, "title", _("Finance Workcenter"), update_modified=False)
	else:
		page = frappe.get_doc(
			{
				"doctype": "Page",
				"module": "Omnexa Core",
				"name": WORKCENTER_PAGE,
				"page_name": WORKCENTER_PAGE,
				"title": _("Finance Workcenter"),
				"standard": "Yes",
			}
		)
		page.append("roles", {"role": "System Manager"})
		page.insert(ignore_permissions=True)
	sync_workcenter_page_roles()
	frappe.db.commit()
	return {"ok": True, "page": WORKCENTER_PAGE}


@frappe.whitelist()
def get_workcenter_context_api() -> dict:
	return get_workcenter_context()


@frappe.whitelist()
def get_grouped_portal_catalog_for_user(include_missing: int = 0) -> list[dict]:
	ctx = get_workcenter_context()
	if ctx["is_admin"]:
		from omnexa_core.omnexa_core.finance_demo.finance_portal_catalog import get_grouped_portal_catalog

		return get_grouped_portal_catalog(include_missing=include_missing)
	return ctx["grouped_portals"]
