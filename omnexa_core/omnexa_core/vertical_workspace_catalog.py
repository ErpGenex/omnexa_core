# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Build complete vertical workspace catalogs from base sections + live module inventory."""

from __future__ import annotations

import os
from collections import OrderedDict
from typing import Any

import frappe
from frappe.utils import get_bench_path

WorkspaceLink = tuple[str, str, str]
WorkspaceSections = list[tuple[str, list[WorkspaceLink]]]


def _normalize_link(item: Any) -> WorkspaceLink | None:
	if not item or len(item) < 2:
		return None
	link_type, link_to = item[0], item[1]
	label = item[2] if len(item) > 2 else link_to
	return (link_type, link_to, label)


def _normalize_sections(sections: WorkspaceSections) -> WorkspaceSections:
	out: WorkspaceSections = []
	for section, items in sections or []:
		normalized: list[WorkspaceLink] = []
		for item in items:
			link = _normalize_link(item)
			if link:
				normalized.append(link)
		if normalized:
			out.append((section, normalized))
	return out

GLOBAL_MIN_LINKS = 50
_REPORTS_PER_SECTION = 6
_DOCTYPES_PER_SECTION = 8

_DOMAIN_SECTIONS: dict[str, str] = {
	"digital": "📊 Dashboards & portals",
	"organization": "🏢 Organization",
	"portfolio": "🏢 Portfolio",
	"operations": "📋 Operations",
	"field_sales": "🚚 Field operations",
	"commercial": "📋 Commercial",
	"finance": "💰 Finance & ERP",
	"reporting": "📈 Reports",
	"analytics": "📊 Analytics",
	"compliance": "🛡️ Compliance",
	"integration": "🔗 Integration",
}

_ERP_INTEGRATION_LINKS: list[WorkspaceLink] = [
	("DocType", "Customer", "Customer"),
	("DocType", "Supplier", "Supplier"),
	("DocType", "Item", "Item"),
	("DocType", "Sales Invoice", "Sales Invoice"),
	("DocType", "Purchase Invoice", "Purchase Invoice"),
	("DocType", "Payment Entry", "Payment Entry"),
	("DocType", "Journal Entry", "Journal Entry"),
	("DocType", "GL Account", "GL Account"),
	("DocType", "Cost Center", "Cost Center"),
	("DocType", "Company", "Company"),
	("DocType", "Branch", "Branch"),
	("Report", "General Ledger", "General Ledger"),
	("Report", "Trial Balance", "Trial Balance"),
	("Report", "Accounts Receivable", "Accounts Receivable"),
	("Report", "Accounts Payable", "Accounts Payable"),
	("Report", "Sales Register", "Sales Register"),
	("Report", "Purchase Register", "Purchase Register"),
	("Report", "Profit and Loss Statement", "Profit and Loss"),
	("Report", "Balance Sheet", "Balance Sheet"),
	("Report", "Governance Overview", "Governance Overview"),
]


def _supplement_standard_erp_catalog(seen: set[tuple[str, str]]) -> WorkspaceSections:
	"""Pad small vertical desks with standard ERPNext masters/reports (site-local)."""
	extra_sections: WorkspaceSections = []
	doctype_links: list[WorkspaceLink] = []
	report_links: list[WorkspaceLink] = []

	for lt, lto, lbl in _ERP_INTEGRATION_LINKS:
		key = (lt, lto)
		if key in seen or not _link_exists(lt, lto):
			continue
		if lt == "Report":
			report_links.append((lt, lto, lbl))
		else:
			doctype_links.append((lt, lto, lbl))
		seen.add(key)

	erp_modules = (
		"Omnexa Accounting",
		"omnexa_accounting",
		"Omnexa Hr",
		"Omnexa Projects Pm",
		"Omnexa Trading",
		"Omnexa Reporting Compliance",
		"Omnexa Core",
		"Omnexa Services",
		"Omnexa Fixed Assets",
		"Accounts",
		"Stock",
		"Selling",
		"Buying",
		"Projects",
		"HR",
		"Assets",
		"Manufacturing",
		"Setup",
	)
	target = GLOBAL_MIN_LINKS
	for module in erp_modules:
		if len(seen) >= target:
			break
		for dt in frappe.get_all(
			"DocType",
			filters={"module": module, "istable": 0, "issingle": 0},
			pluck="name",
			order_by="name asc",
			limit=120,
		):
			if len(seen) >= target:
				break
			key = ("DocType", dt)
			if key in seen:
				continue
			if _link_exists("DocType", dt):
				doctype_links.append(("DocType", dt, _human_label("DocType", dt)))
				seen.add(key)
		for rep in frappe.get_all(
			"Report",
			filters={"module": module, "report_type": "Report"},
			pluck="name",
			order_by="name asc",
			limit=80,
		):
			if len(seen) >= target:
				break
			key = ("Report", rep)
			if key in seen:
				continue
			if _link_exists("Report", rep):
				report_links.append(("Report", rep, _human_label("Report", rep)))
				seen.add(key)

	if doctype_links:
		extra_sections.extend(_split_links_into_sections("💳 ERP masters", doctype_links, _DOCTYPES_PER_SECTION))
	if report_links:
		extra_sections.extend(_split_links_into_sections("📈 ERP reports", report_links, _REPORTS_PER_SECTION))
	return extra_sections


def _app_installed(app_name: str) -> bool:
	try:
		return bool(app_name) and app_name in frappe.get_installed_apps()
	except Exception:
		return False


def _resolve_module(app_name: str) -> str | None:
	try:
		from omnexa_core.omnexa_core.workspace_control_tower import _APP_SPECS

		spec = _APP_SPECS.get(app_name) or {}
		module = (spec.get("module") or "").strip()
		if module:
			return module
	except Exception:
		pass
	app_title = app_name.replace("_", " ").replace("erpgenex ", "Erpgenex ").title()
	if app_title.startswith("Omnexa "):
		return app_title
	if app_title.startswith("Erpgenex "):
		return app_title
	return None


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	return False


def _human_label(link_type: str, link_to: str) -> str:
	if link_type == "DocType":
		return frappe.db.get_value("DocType", link_to, "name") or link_to
	return link_to


def _gap_register_module(app_name: str):
	root = os.path.join(get_bench_path(), "apps", app_name, app_name)
	if os.path.isdir(root):
		for fname in sorted(os.listdir(root)):
			if fname.endswith("_gap_register.py"):
				try:
					return frappe.get_module(f"{app_name}.{fname[:-3]}")
				except Exception:
					continue
	prefix = app_name.split("_")[-1]
	for mod_path in (f"{app_name}.{prefix}_gap_register",):
		try:
			return frappe.get_module(mod_path)
		except Exception:
			continue
	return None


def _links_from_gap_register(app_name: str) -> list[tuple[str, str, str, str]]:
	"""Return (link_type, link_to, label, domain) from gap register detect fields."""
	mod = _gap_register_module(app_name)
	if not mod:
		return []
	gaps = getattr(mod, "GAP_DEFINITIONS", None) or []
	out: list[tuple[str, str, str, str]] = []
	for gap in gaps:
		detect = (gap.get("detect") or "").strip()
		domain = (gap.get("domain") or "operations").strip()
		if detect.startswith("doctype:"):
			out.append(("DocType", detect.split(":", 1)[1], gap.get("title") or detect.split(":", 1)[1], domain))
		elif detect.startswith("report:"):
			out.append(("Report", detect.split(":", 1)[1], gap.get("title") or detect.split(":", 1)[1], domain))
		elif detect.startswith("page:"):
			out.append(("Page", detect.split(":", 1)[1], gap.get("title") or detect.split(":", 1)[1], domain))
	return out


def _links_from_control_tower(app_name: str) -> list[WorkspaceLink]:
	try:
		from omnexa_core.omnexa_core.workspace_control_tower import _APP_SPECS

		spec = _APP_SPECS.get(app_name) or {}
	except Exception:
		return []
	out: list[WorkspaceLink] = []
	for sc in spec.get("shortcuts") or []:
		if sc and len(sc) >= 3:
			out.append((sc[1], sc[2], sc[0]))
	for _section, rows in spec.get("extra_sections") or []:
		for row in rows:
			if row and len(row) >= 3:
				out.append((row[1], row[2], row[0]))
	return out


def _links_from_module_inventory(module: str) -> tuple[list[WorkspaceLink], list[WorkspaceLink], list[WorkspaceLink]]:
	pages: list[WorkspaceLink] = []
	doctypes: list[WorkspaceLink] = []
	reports: list[WorkspaceLink] = []
	if not module:
		return pages, doctypes, reports
	for dt in frappe.get_all(
		"DocType",
		filters={"module": module, "istable": 0, "issingle": 0},
		pluck="name",
		order_by="name asc",
	):
		doctypes.append(("DocType", dt, _human_label("DocType", dt)))
	for rep in frappe.get_all("Report", filters={"module": module}, pluck="name", order_by="name asc"):
		reports.append(("Report", rep, _human_label("Report", rep)))
	return pages, doctypes, reports


def _links_from_app_pages(app_name: str) -> list[WorkspaceLink]:
	root = os.path.join(get_bench_path(), "apps", app_name, app_name, "page")
	if not os.path.isdir(root):
		root = os.path.join(get_bench_path(), "apps", app_name, app_name, app_name, "page")
	if not os.path.isdir(root):
		return []
	out: list[WorkspaceLink] = []
	for entry in sorted(os.listdir(root)):
		page_dir = os.path.join(root, entry)
		if not os.path.isdir(page_dir):
			continue
		if not frappe.db.exists("Page", entry):
			continue
		label = entry.replace("-", " ").title()
		out.append(("Page", entry, label))
	return out


def _split_links_into_sections(prefix: str, links: list[WorkspaceLink], chunk: int) -> WorkspaceSections:
	if not links:
		return []
	if len(links) <= chunk:
		return [(prefix, links)]
	sections: WorkspaceSections = []
	for i in range(0, len(links), chunk):
		part = links[i : i + chunk]
		suffix = f" · {i // chunk + 1}" if len(links) > chunk else ""
		sections.append((f"{prefix}{suffix}", part))
	return sections


def _count_links(sections: WorkspaceSections) -> int:
	return sum(len(items) for _section, items in sections)


def _merge_sections(base: WorkspaceSections, extra_sections: WorkspaceSections) -> WorkspaceSections:
	merged: OrderedDict[str, list[WorkspaceLink]] = OrderedDict()
	seen: set[tuple[str, str]] = set()

	def _add(section: str, link: WorkspaceLink) -> None:
		key = (link[0], link[1])
		if key in seen or not _link_exists(key[0], key[1]):
			return
		seen.add(key)
		merged.setdefault(section, []).append(link)

	for section, items in base:
		for item in items:
			_add(section, item)
	for section, items in extra_sections:
		for item in items:
			_add(section, item)
	return [(section, items) for section, items in merged.items() if items]


def get_effective_workspace_sections(app_name: str, base_sections: WorkspaceSections) -> WorkspaceSections:
	"""Merge curated sections with gap register, module inventory, control tower, and ERP glue."""
	base_sections = _normalize_sections(base_sections)

	sections = _merge_sections(base_sections, [])
	seen = {(lt, lto) for _s, items in sections for lt, lto, _lbl in items}
	module = _resolve_module(app_name)

	# Gap register + control tower
	domain_buckets: dict[str, list[WorkspaceLink]] = {}
	for lt, lto, lbl, domain in _links_from_gap_register(app_name):
		key = (lt, lto)
		if key in seen:
			continue
		section = _DOMAIN_SECTIONS.get(domain, "📋 Operations")
		domain_buckets.setdefault(section, []).append((lt, lto, lbl))
		seen.add(key)

	for lt, lto, lbl in _links_from_control_tower(app_name):
		key = (lt, lto)
		if key in seen:
			continue
		if lt == "Report":
			domain_buckets.setdefault("📈 Reports", []).append((lt, lto, lbl))
		elif lt == "Page":
			domain_buckets.setdefault("📊 Dashboards & portals", []).append((lt, lto, lbl))
		else:
			domain_buckets.setdefault("📋 Operations", []).append((lt, lto, lbl))
		seen.add(key)

	_pages, module_dts, module_reports = _links_from_module_inventory(module or "")
	for lt, lto, lbl in _links_from_app_pages(app_name):
		key = (lt, lto)
		if key in seen:
			continue
		domain_buckets.setdefault("📊 Dashboards & portals", []).append((lt, lto, lbl))
		seen.add(key)

	missing_dts = [(lt, lto, lbl) for lt, lto, lbl in module_dts if (lt, lto) not in seen]
	missing_reports = [(lt, lto, lbl) for lt, lto, lbl in module_reports if (lt, lto) not in seen]
	for lt, lto, lbl in missing_dts:
		seen.add((lt, lto))
	for lt, lto, lbl in missing_reports:
		seen.add((lt, lto))

	extra: WorkspaceSections = []
	for section, items in domain_buckets.items():
		if items:
			extra.append((section, items))
	extra.extend(_split_links_into_sections("📋 Module operations", missing_dts, _DOCTYPES_PER_SECTION))
	extra.extend(_split_links_into_sections("📈 Module reports", missing_reports, _REPORTS_PER_SECTION))

	sections = _merge_sections(sections, extra)

	seen = {(lt, lto) for _s, items in sections for lt, lto, _lbl in items}
	if _count_links(sections) < GLOBAL_MIN_LINKS:
		sections = _merge_sections(sections, _supplement_standard_erp_catalog(seen))

	return sections


def get_workspace_catalog_stats(app_name: str, base_sections: WorkspaceSections) -> dict[str, Any]:
	effective = get_effective_workspace_sections(app_name, base_sections)
	links = [(lt, lto) for _s, items in effective for lt, lto, _lbl in items if _link_exists(lt, lto)]
	return {
		"app": app_name,
		"sections": len(effective),
		"links_catalogued": len(links),
		"meets_global_min": len(links) >= GLOBAL_MIN_LINKS,
		"global_min_links": GLOBAL_MIN_LINKS,
	}
