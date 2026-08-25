# Copyright (c) 2026, Omnexa — generic workspace catalog for Next.js (all modules)
from __future__ import annotations

import frappe
from frappe.utils import get_fullname

from omnexa_core.omnexa_core.api.desk_module_registry import get_module_by_slug
from omnexa_core.omnexa_core.session_context import get_effective_company, get_view_context

# Page name suffix → Next.js sub-route (within /{slug}/...)
_PAGE_NEXT_SUFFIXES: dict[str, str] = {
	"executive-dashboard": "dashboard",
	"analytics-dashboard": "analytics",
	"employee-self-service": "self-service",
	"operations-desk": "operations",
	"finance-desk": "finance",
	"customer-portal": "customer-portal",
	"workcenter": "workcenter",
}

# HR-specific pages (slug hr)
_HR_PAGE_ROUTES: dict[str, str] = {
	"hr-dashboard": "dashboard",
	"hr-executive-dashboard": "dashboard",
	"hr-analytics-dashboard": "analytics",
	"hr-employee-self-service": "self-service",
	"hr-operations-desk": "operations",
	"hr-workcenter": "workcenter",
	"hr-finance-desk": "finance",
	"hr-customer-portal": "customer-portal",
	"employee-directory": "employee-directory",
}


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "Workspace":
		return bool(frappe.db.exists("Workspace", link_to))
	return False


def _sections_from_app(app: str):
	from omnexa_core.omnexa_core.workspace_site_sync import _sections_from_vertical_app

	sections = _sections_from_vertical_app(app)
	if sections:
		return sections

	mod = get_module_by_slug_from_app(app)
	if mod and mod.get("frappe_workspace") and frappe.db.exists("Workspace", mod["frappe_workspace"]):
		from omnexa_core.omnexa_core.workspace_desk_layouts import (
			get_desk_sections_for_workspace,
			resolve_desk_sections_for_workspace_doc,
		)

		ws = frappe.get_doc("Workspace", mod["frappe_workspace"])
		desk = resolve_desk_sections_for_workspace_doc(ws) or get_desk_sections_for_workspace(mod["frappe_workspace"])
		if desk:
			out = []
			for _card, rows in desk:
				items = []
				for label, link_type, link_to, _ref in rows:
					if (link_type or "").strip() == "URL":
						continue
					items.append((link_type, link_to, label))
				if items:
					out.append((_card or "Links", items))
			return out
	return []


def get_module_by_slug_from_app(app: str):
	from omnexa_core.omnexa_core.api.desk_module_registry import get_all_modules

	for mod in get_all_modules():
		if mod["app"] == app:
			return mod
	return None


def _next_href_for_link(slug: str, link_type: str, link_to: str) -> str | None:
	if link_type != "Page":
		return None
	if slug == "hr" and link_to in _HR_PAGE_ROUTES:
		return f"/hr/{_HR_PAGE_ROUTES[link_to]}"
	if link_to in _HR_PAGE_ROUTES:
		return f"/hr/{_HR_PAGE_ROUTES[link_to]}"
	for suffix, route in _PAGE_NEXT_SUFFIXES.items():
		if link_to == f"{slug}-{suffix}" or link_to.endswith(f"-{suffix}"):
			return f"/{slug}/{route}"
	if link_to.endswith("-workcenter"):
		return f"/{slug}/workcenter"
	return None


def _resolve_link(slug: str, link_type: str, link_to: str) -> dict:
	if link_type == "DocType":
		href = f"/app/List/{frappe.utils.quote(link_to)}"
		return {"href": href, "next_href": href, "external": True, "next_js": False}
	if link_type == "Report":
		href = f"/app/query-report/{frappe.utils.quote(link_to)}"
		return {"href": href, "next_href": href, "external": True, "next_js": False}
	if link_type == "Page":
		frappe_href = f"/app/{link_to}"
		next_href = _next_href_for_link(slug, link_type, link_to)
		if next_href:
			return {"href": frappe_href, "next_href": next_href, "external": False, "next_js": True}
		return {"href": frappe_href, "next_href": frappe_href, "external": True, "next_js": False}
	if link_type == "Workspace":
		href = f"/app/{frappe.scrub(link_to).replace('_', '-')}"
		return {"href": href, "next_href": href, "external": True, "next_js": False}
	href = f"/app/{link_to}"
	return {"href": href, "next_href": href, "external": True, "next_js": False}


def _build_kpis(app: str, sections: list) -> list[dict]:
	kpis = []
	seen_dts: set[str] = set()
	for _section, items in sections or []:
		for link_type, link_to, label in items:
			if link_type != "DocType" or link_to in seen_dts:
				continue
			if not _link_exists(link_type, link_to):
				continue
			seen_dts.add(link_to)
			try:
				count = frappe.db.count(link_to)
			except Exception:
				count = 0
			kpis.append({"label": label, "value": count, "key": frappe.scrub(link_to)})
			if len(kpis) >= 4:
				return kpis
	return kpis


def _quick_actions(sections: list, limit: int = 4) -> list[dict]:
	actions = []
	icons = ["user-plus", "calendar", "building-2", "award"]
	for _section, items in sections or []:
		for link_type, link_to, label in items:
			if link_type not in ("Page", "DocType"):
				continue
			if not _link_exists(link_type, link_to):
				continue
			if link_type == "DocType":
				route = f"/app/List/{frappe.utils.quote(link_to)}"
			else:
				route = f"/app/{link_to}"
			actions.append(
				{
					"label": label,
					"route": route,
					"tone": "blue",
					"icon": icons[len(actions) % len(icons)],
				}
			)
			if len(actions) >= limit:
				return actions
	return actions


def _first_countable_doctype(sections: list) -> str | None:
	for _section, items in sections or []:
		for link_type, link_to, _label in items:
			if link_type == "DocType" and _link_exists(link_type, link_to):
				return link_to
	return None


def _count_trend_7d(doctype: str) -> tuple[list[str], list[int], list[dict]]:
	from frappe.utils import add_days, getdate, nowdate

	labels: list[str] = []
	values: list[int] = []
	today = getdate(nowdate())
	for i in range(6, -1, -1):
		d = add_days(today, -i)
		labels.append(d.strftime("%a"))
		try:
			values.append(
				frappe.db.count(
					doctype,
					filters={"creation": ["between", [f"{d} 00:00:00", f"{d} 23:59:59"]]},
				)
			)
		except Exception:
			values.append(0)
	total = sum(values) or 1
	avg = round(sum(values) / len(values), 1) if values else 0
	best_idx = values.index(max(values)) if values else 0
	stats = [
		{"label": frappe._("Average Activity"), "value": f"{round(avg / max(values + [1]) * 100, 1)}%"},
		{"label": frappe._("Best Day"), "value": labels[best_idx] if labels else "—"},
		{"label": frappe._("Peak Count"), "value": str(max(values) if values else 0)},
		{"label": frappe._("Total (7d)"), "value": str(total)},
	]
	return labels, values, stats


def _recent_activities_from_sections(sections: list, limit: int = 5) -> list[dict]:
	activities: list[dict] = []
	for _section, items in sections or []:
		for link_type, link_to, label in items:
			if link_type != "DocType" or not _link_exists(link_type, link_to):
				continue
			meta = frappe.get_meta(link_to)
			name_field = meta.get("title_field") or "name"
			try:
				rows = frappe.get_all(
					link_to,
					fields=[name_field, "modified", "owner"],
					order_by="modified desc",
					limit=2,
				)
			except Exception:
				continue
			for row in rows:
				display = row.get(name_field) or row.get("name") or label
				activities.append(
					{
						"user": display,
						"action": frappe._("updated {0}").format(label),
						"time": frappe.format(row.modified, {"fieldtype": "Datetime"}),
						"tone": "update",
					}
				)
			if len(activities) >= limit:
				return activities[:limit]
	return activities[:limit]


def _status_summary_from_kpis(kpis: list[dict]) -> list[dict]:
	out = []
	for k in (kpis or [])[:4]:
		val = int(k.get("value") or 0)
		total = max(val * 2, val + 10, 1)
		out.append({"label": k["label"], "used": val, "total": total})
	while len(out) < 4:
		out.append({"label": frappe._("Pending"), "used": 0, "total": 10})
	return out


def _activity_summary_from_sections(sections: list) -> list[dict]:
	statuses = [
		("completed", frappe._("Completed")),
		("ongoing", frappe._("In Progress")),
		("scheduled", frappe._("Scheduled")),
		("participants", frappe._("Total Records")),
	]
	out = []
	idx = 0
	for _section, items in sections or []:
		for link_type, link_to, label in items:
			if link_type != "DocType" or not _link_exists(link_type, link_to):
				continue
			status, default_label = statuses[idx % len(statuses)]
			try:
				count = frappe.db.count(link_to)
			except Exception:
				count = 0
			out.append({"label": label or default_label, "count": count, "status": status})
			idx += 1
			if len(out) >= 4:
				return out
	while len(out) < 4:
		status, default_label = statuses[len(out) % len(statuses)]
		out.append({"label": default_label, "count": 0, "status": status})
	return out


def _generic_announcements(mod: dict) -> list[dict]:
	label = mod.get("label") or mod.get("slug", "Module")
	return [
		{
			"title": frappe._("{0} workspace updated").format(label),
			"date": frappe._("Today"),
			"time": "",
			"type": "info",
		},
		{
			"title": frappe._("Review pending items in {0}").format(label),
			"date": frappe._("This week"),
			"time": "",
			"type": "policy",
		},
		{
			"title": frappe._("{0} analytics available").format(label),
			"date": frappe._("This month"),
			"time": "",
			"type": "training",
		},
	]


def _ensure_five_kpis(kpis: list[dict], mod: dict) -> list[dict]:
	icons = ["users", "user-check", "palmtree", "user-plus", "user-minus"]
	tones = ["purple", "green", "orange", "blue", "red"]
	out = []
	for i, k in enumerate((kpis or [])[:5]):
		val = int(k.get("value") or 0)
		out.append(
			{
				"key": k.get("key", f"kpi-{i}"),
				"label": k["label"],
				"value": val,
				"delta": frappe._("total records"),
				"direction": "neutral",
				"tone": tones[i % 5],
				"icon": icons[i % 5],
			}
		)
	placeholders = [
		frappe._("Active Records"),
		frappe._("Open Items"),
		frappe._("This Month"),
		frappe._("Pending"),
		frappe._("Closed"),
	]
	while len(out) < 5:
		i = len(out)
		out.append(
			{
				"key": f"placeholder-{i}",
				"label": placeholders[i],
				"value": 0,
				"delta": frappe._("no data yet"),
				"direction": "neutral",
				"tone": tones[i % 5],
				"icon": icons[i % 5],
			}
		)
	return out


@frappe.whitelist()
def get_workspace_catalog(module: str | None = None):
	"""Generic workspace hub catalog for any registered module slug."""
	module = (module or "").strip().lower()
	if not module:
		frappe.throw(frappe._("Module slug is required"))

	if module == "hr":
		from omnexa_hr.omnexa_hr.api.hr_workspace_catalog import get_hr_workspace_catalog

		return get_hr_workspace_catalog()

	mod = get_module_by_slug(module)
	if not mod:
		frappe.throw(frappe._("Unknown module: {0}").format(module))

	app = mod["app"]
	sections_raw = _sections_from_app(app)
	sections = []
	for section_label, items in sections_raw or []:
		links = []
		for link_type, link_to, label in items:
			if not _link_exists(link_type, link_to):
				continue
			resolved = _resolve_link(module, link_type, link_to)
			links.append(
				{
					"label": label,
					"link_type": link_type,
					"link_to": link_to,
					**resolved,
				}
			)
		if links:
			sections.append({"title": section_label, "links": links})

	kpis = _build_kpis(app, sections_raw)

	return {
		"module": module,
		"app": app,
		"title": mod["label"],
		"sections": sections,
		"kpis": kpis,
		"workcenter_href": mod.get("workcenter_href"),
		"dashboard_href": mod.get("dashboard_href"),
	}


@frappe.whitelist()
def get_module_dashboard_catalog(module: str | None = None):
	"""Generic executive dashboard catalog for any module."""
	module = (module or "").strip().lower()
	if module == "hr":
		from omnexa_hr.omnexa_hr.api.hr_dashboard import get_hr_dashboard_catalog

		return get_hr_dashboard_catalog()

	mod = get_module_by_slug(module)
	if not mod:
		frappe.throw(frappe._("Unknown module: {0}").format(module))

	user = frappe.session.user
	company = get_effective_company()
	view = get_view_context(user)
	app = mod["app"]
	sections_raw = _sections_from_app(app)
	kpis_raw = _build_kpis(app, sections_raw)
	actions = _quick_actions(sections_raw)
	kpis = _ensure_five_kpis(kpis_raw, mod)

	full_name = get_fullname(user) or user
	chart_labels = [k["label"] for k in kpis_raw[:6]] or [mod["label"]]
	chart_values = [int(k.get("value") or 0) for k in kpis_raw[:6]] or [0]

	doctype = _first_countable_doctype(sections_raw)
	if doctype:
		att_labels, att_values, att_stats = _count_trend_7d(doctype)
	else:
		att_labels, att_values, att_stats = [], [], []

	return {
		"module": module,
		"welcome": {
			"title": frappe._("Welcome back, {0}").format(full_name),
			"subtitle": frappe._("Here's what's happening in your organization today."),
		},
		"quick_actions": actions or [
			{"label": frappe._("Open Workspace"), "route": f"/{module}", "tone": "blue", "icon": "layout-dashboard"},
			{"label": frappe._("Workcenter"), "route": f"/{module}/workcenter", "tone": "purple", "icon": "briefcase"},
		],
		"kpis": kpis,
		"announcements": _generic_announcements(mod),
		"charts": {
			"employee_overview": {
				"type": "donut",
				"title": frappe._("{0} Overview").format(mod["label"]),
				"labels": chart_labels,
				"values": chart_values,
				"tabs": [frappe._("Category"), frappe._("Status"), frappe._("Type")],
			},
			"attendance": {
				"type": "line",
				"title": frappe._("Activity Overview"),
				"subtitle": frappe._("Last 7 Days"),
				"labels": att_labels,
				"values": att_values,
				"stats": att_stats,
			},
		},
		"panels": {
			"leave_summary": _status_summary_from_kpis(kpis_raw),
			"training_summary": _activity_summary_from_sections(sections_raw),
			"recent_activity": _recent_activities_from_sections(sections_raw),
		},
		"panel_labels": {
			"primary": frappe._("Status Summary"),
			"secondary": frappe._("Activity Summary"),
			"activity": frappe._("Recent Activities"),
		},
		"scope": {"company": company, "branch": view.get("branch"), "label": view.get("label")},
	}
