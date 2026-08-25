"""One-off audit: activity menu filtering per company."""
from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_visibility import (
	clear_desk_visibility_cache,
	get_desk_hidden_for_user,
	get_user_company_activity,
)
from omnexa_core.omnexa_core.finance_desktop_sidebar import get_workspace_sidebar_items


def run(companies=None):
	frappe.set_user("Administrator")
	companies = companies or ["AB-FIN", "AB-HC", "AB-EDU", "HD2", "AB-CON", "AB-TRD", "OMNX-T72AD"]
	for company in companies:
		if not frappe.db.exists("Company", company):
			print(f"missing {company}")
			continue
		for scope in ("company", "all"):
			frappe.defaults.set_user_default("omnexa_view_company", company, "Administrator")
			frappe.defaults.set_user_default("omnexa_admin_activity_scope", scope, "Administrator")
			clear_desk_visibility_cache()
			act = get_user_company_activity()
			dh = get_desk_hidden_for_user()
			pages = get_workspace_sidebar_items().get("pages") or []
			titles = sorted({(p.get("title") or p.get("name") or "").strip() for p in pages})
			checks = ["Healthcare", "Mortgage Finance", "Tourism", "Finance Engine"]
			visible = {k: k in titles for k in checks}
			print(f"{company}\tscope={scope}\tact={act}\tpages={len(titles)}\t{visible}")
