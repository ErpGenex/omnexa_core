# Copyright (c) 2026, ErpGenEx
"""Desk visibility — manual hide + auto-filter by Company business activity."""

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.app_activity import activity_for_app
from omnexa_core.omnexa_core.company_activity_utils import (
	company_strict_activity_filtering_enabled,
	first_company_activity_value,
)

SETTINGS_DOCTYPE = "Omnexa Marketplace Settings"
MANUAL_CACHE_KEY = "omnexa_desk_hidden_apps"
USER_CACHE_HASH = "omnexa_desk_hidden_by_user"
# Platform shell — never activity-filtered (sector parents, desk chrome).
INFRA_DESK_APPS = frozenset({"frappe", "omnexa_core"})

# Cross-industry apps always visible on Desk (if installed and on apps screen).
PLATFORM_APP_SLUGS = frozenset(
	{
		"omnexa_accounting",
		"omnexa_einvoice",
		"omnexa_fixed_assets",
		"omnexa_reporting_compliance",
		"omnexa_customer_core",
		"omnexa_services",
		"omnexa_projects_pm",
		"omnexa_hr",
		"omnexa_setup_intelligence",
		"omnexa_experience",
		"omnexa_n8n_bridge",
		"omnexa_intelligence_core",
	}
)

_BASE_PLATFORM_LABELS = frozenset(
	{
		"Accounting",
		"Einvoice",
		"Fixed",
		"Reporting",
		"Services",
		"Customer",
		"Projects",
		"Hr",
		"General",
		"Intelligence",
		"Setup",
		"Experience",
		"Bridge",
	}
)

# Company business activity → marketplace activity labels allowed on Desk.
COMPANY_ACTIVITY_ALLOWED: dict[str, frozenset[str]] = {
	"General": _BASE_PLATFORM_LABELS,
	"Healthcare": _BASE_PLATFORM_LABELS | frozenset({"Healthcare"
	}),
	"Education": _BASE_PLATFORM_LABELS | frozenset({"Education"
	}),
	"Construction": _BASE_PLATFORM_LABELS | frozenset({"Construction", "Engineering", "ErpGenEx"}),
	"Engineering Consulting": _BASE_PLATFORM_LABELS | frozenset({"Engineering", "Construction"}),
	"Financial Services": _BASE_PLATFORM_LABELS
	| frozenset({"Finance", "Leasing", "Mortgage", "Factoring", "Credit", "Consumer", "Alm", "Risk", "Mobility", "Sme"}),
	"Trading": _BASE_PLATFORM_LABELS | frozenset({"Trading"
	}),
	"Manufacturing": _BASE_PLATFORM_LABELS | frozenset({"Manufacturing"
	}),
	"Agriculture": _BASE_PLATFORM_LABELS | frozenset({"Agriculture"
	}),
	"Tourism": _BASE_PLATFORM_LABELS | frozenset({"Tourism", "Mobility"}),
	"Hotel Assets": _BASE_PLATFORM_LABELS | frozenset({"Tourism", "ErpGenEx", "Fixed"}),
	"Bakeries": _BASE_PLATFORM_LABELS | frozenset({"Restaurant"
	}),
	"Services": _BASE_PLATFORM_LABELS | frozenset({"Services"
	}),
	"Statutory Audit": _BASE_PLATFORM_LABELS | frozenset({"Audit"})
	}


def _parse_app_list(raw: str | None) -> list[str]:
	if not raw:
		return []
	raw = raw.strip()
	if not raw:
		return []
	if raw.startswith("["):
		try:
			data = json.loads(raw)
			if isinstance(data, list):
				return sorted({str(x).strip() for x in data if str(x).strip()})
		except Exception:
			pass
	return sorted({s.strip() for s in raw.replace("\n", ",").split(",") if s.strip()})


def _normalize_company_activity(raw: str | None) -> str:
	if not raw:
		return "General"
	raw = raw.strip()
	if not raw or raw.lower() == "general":
		return "General"
	if raw.startswith("Bakeries"):
		return "Bakeries"
	if "Hotel Assets" in raw:
		return "Hotel Assets"
	return raw.split("(")[0].strip() or "General"


def get_effective_company_for_activity(user: str | None = None) -> str | None:
	"""Company used for activity filtering (navbar scope, then user default)."""
	from omnexa_core.omnexa_core.session_context import get_effective_company

	return get_effective_company(user)


def get_user_company_activity(user: str | None = None) -> str:
	company = get_effective_company_for_activity(user)
	if not company or not frappe.db.exists("Company", company):
		return "General"
	return _normalize_company_activity(first_company_activity_value(company))


def _allowed_labels_for_company(company_activity: str) -> frozenset[str]:
	normalized = _normalize_company_activity(company_activity)
	allowed = COMPANY_ACTIVITY_ALLOWED.get(normalized, COMPANY_ACTIVITY_ALLOWED["General"])
	override = frappe.conf.get("omnexa_company_activity_allowed") or {}
	if isinstance(override, dict):
		custom = override.get(normalized) or override.get(company_activity)
		if isinstance(custom, (list, tuple, set)):
			return frozenset(str(x).strip() for x in custom if str(x).strip())
	return allowed


def _activity_filter_enabled() -> bool:
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return True
	return bool(frappe.db.get_single_value(SETTINGS_DOCTYPE, "filter_desk_by_company_activity"))


def _activity_filter_exempt_roles() -> set[str]:
	default = {"System Manager"}
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return default
	raw = frappe.db.get_single_value(SETTINGS_DOCTYPE, "activity_filter_exempt_roles") or "System Manager"
	roles = {r.strip() for r in str(raw).replace("\n", ",").split(",") if r.strip()}
	return roles or default


def _activity_filter_applies_to_user(user: str | None = None) -> bool:
	"""True when desk menus should follow the current company's business activity."""
	if not _activity_filter_enabled():
		return False

	user = user or frappe.session.user
	company = get_effective_company_for_activity(user)
	if not company:
		return False
	if not company_strict_activity_filtering_enabled(company):
		return False

	from omnexa_core.omnexa_core.session_context import get_activity_menu_scope

	# Scope drives filtering for every company: company = filter by activity, all = show everything.
	return get_activity_menu_scope(user) == "company"


def _finance_activity_workspace_keys() -> frozenset[str]:
	"""All finance desk workspace keys (names, titles, emoji shortcuts)."""
	keys: set[str] = set(_finance_workspace_aliases().keys())
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import WORKSPACE_APP_LOGO

		keys.update(WORKSPACE_APP_LOGO.keys())
	except Exception:
		pass
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_DEMO_WORKSPACE_NAMES, ROLE_SPECS

		keys.update(ROLE_DEMO_WORKSPACE_NAMES)
		for spec in ROLE_SPECS:
			if spec.get("workspace"):
				keys.add(spec["workspace"])
			if spec.get("title"):
				keys.add(spec["title"])
	except Exception:
		pass
	return frozenset(k for k in keys if k)


def get_activity_hidden_apps(company_activity: str | None = None) -> set[str]:
	"""Installed apps hidden because they do not match the company business activity."""
	activity = company_activity or get_user_company_activity()
	allowed = _allowed_labels_for_company(activity)
	slug_override = frappe.conf.get("omnexa_company_activity_app_slugs") or {}
	if isinstance(slug_override, dict) and activity in slug_override:
		allowed_slugs = frozenset(str(x).strip() for x in slug_override[activity] if str(x).strip())
		hidden: set[str] = set()
		for app in frappe.get_installed_apps() or []:
			if app in PLATFORM_APP_SLUGS or app == "frappe":
				continue
			if app not in allowed_slugs:
				hidden.add(app)
		return hidden - INFRA_DESK_APPS

	hidden = set()
	for app in frappe.get_installed_apps() or []:
		if app in PLATFORM_APP_SLUGS or app in INFRA_DESK_APPS:
			continue
		if activity_for_app(app) not in allowed:
			hidden.add(app)
	return hidden - INFRA_DESK_APPS


def _finance_workspace_aliases() -> dict[str, str]:
	"""Map finance shortcut desks (module Omnexa Core) → owning app."""
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import WORKSPACE_APP_LOGO
	except Exception:
		WORKSPACE_APP_LOGO = {}

	aliases: dict[str, str] = dict(WORKSPACE_APP_LOGO)
	pairs = [
		("Finance Leasing", "Leasing Finance"),
		("Finance Mortgage", "Mortgage Finance"),
		("Finance Factoring", "Factoring"),
		("Finance SME", "SME Retail Finance"),
		("Finance Treasury", "ALM"),
		("Finance Auto", "Vehicle Finance"),
		("Finance Consumer", "Consumer Finance"),
		("Finance Credit Risk", "Credit Risk"),
		("Finance GRC", "Operational Risk"),
		("Finance Microfinance", "SME Microfinance"),
		("📦 Leasing", "Leasing Finance"),
		("🏠 Mortgage", "Mortgage Finance"),
		("📄 Factoring", "Factoring"),
		("🏪 SME Finance", "SME Retail Finance"),
		("💹 Treasury ALM", "ALM"),
		("🚗 Auto Finance", "Vehicle Finance"),
		("🛒 Consumer Lending", "Consumer Finance"),
		("📈 Credit Risk", "Credit Risk"),
		("🛡️ Operational Risk", "Operational Risk"),
		("🤝 Microfinance Field", "SME Microfinance"),
		("🛡️ Credit Origination", "Credit Engine"),
		("Finance Credit Origination", "Credit Engine"),
		("Finance Executive", "Finance Engine"),
		("📊 Group Executive", "Finance Engine"),
	]
	for alias, canonical in pairs:
		app = aliases.get(canonical)
		if app:
			aliases[alias] = app
	return aliases


def _user_cache_key(user: str | None = None) -> str:
	user = user or frappe.session.user
	company = get_effective_company_for_activity(user) or ""
	from omnexa_core.omnexa_core.session_context import get_activity_menu_scope

	scope = get_activity_menu_scope(user)
	strict = int(company_strict_activity_filtering_enabled(company)) if company else 1
	site_on = int(_activity_filter_enabled())
	return f"{user}::{company}::{scope}::{strict}::{site_on}"


def clear_desk_visibility_cache():
	frappe.cache.delete_value(MANUAL_CACHE_KEY)
	frappe.cache.delete_value(USER_CACHE_HASH)


def _ensure_settings_doc():
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return None
	if not frappe.db.exists(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE):
		doc = frappe.get_doc(
			{
				"doctype": SETTINGS_DOCTYPE,
				"filter_desk_by_company_activity": 1,
				"activity_filter_exempt_roles": "System Manager"
	}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
	return SETTINGS_DOCTYPE


def get_hidden_desk_apps() -> set[str]:
	"""Manually hidden apps (Marketplace toggle)."""
	cached = frappe.cache.get_value(MANUAL_CACHE_KEY)
	if cached is not None:
		return set(cached)
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return set()
	raw = frappe.db.get_single_value(SETTINGS_DOCTYPE, "desk_hidden_apps")
	apps = _parse_app_list(raw)
	frappe.cache.set_value(MANUAL_CACHE_KEY, apps)
	return set(apps)


def get_desk_hidden_for_user(user: str | None = None) -> set[str]:
	"""Manual + activity-based hidden apps for the current session user."""
	user = user or frappe.session.user
	bucket = _user_cache_key(user)
	cached = frappe.cache.hget(USER_CACHE_HASH, bucket)
	if cached is not None:
		return set(cached)

	hidden = set(get_hidden_desk_apps())
	if _activity_filter_applies_to_user(user):
		hidden |= get_activity_hidden_apps(get_user_company_activity(user))

	frappe.cache.hset(USER_CACHE_HASH, bucket, list(hidden))
	return hidden


def app_matches_company_activity(app_slug: str, company_activity: str | None = None) -> bool:
	if app_slug in PLATFORM_APP_SLUGS:
		return True
	activity = company_activity or get_user_company_activity()
	allowed = _allowed_labels_for_company(activity)
	return activity_for_app(app_slug) in allowed


def set_desk_app_hidden(app_slug: str, hidden: bool = True) -> list[str]:
	frappe.only_for("System Manager")
	app_slug = (app_slug or "").strip()
	if not app_slug or app_slug in {"frappe", "omnexa_core"}:
		frappe.throw(frappe._("This app cannot be hidden from the desk."))

	_ensure_settings_doc()
	current = get_hidden_desk_apps()
	if hidden:
		current.add(app_slug)
	else:
		current.discard(app_slug)

	payload = json.dumps(sorted(current))
	frappe.db.set_single_value(SETTINGS_DOCTYPE, "desk_hidden_apps", payload)
	clear_desk_visibility_cache()
	frappe.clear_cache()
	return sorted(current)


def set_apps_desk_hidden(app_slugs, hidden: bool = True) -> list[str]:
	"""Hide or show multiple apps on Desk in one action."""
	frappe.only_for("System Manager")
	if isinstance(app_slugs, str):
		text = app_slugs.strip()
		if text.startswith("["):
			try:
				app_slugs = json.loads(text)
			except Exception:
				app_slugs = [s.strip() for s in text.split(",") if s.strip()]
		else:
			app_slugs = [s.strip() for s in text.split(",") if s.strip()]

	_ensure_settings_doc()
	current = get_hidden_desk_apps()
	for raw in app_slugs or []:
		slug = str(raw or "").strip()
		if not slug or slug in {"frappe", "omnexa_core"}:
			continue
		if hidden:
			current.add(slug)
		else:
			current.discard(slug)

	payload = json.dumps(sorted(current))
	frappe.db.set_single_value(SETTINGS_DOCTYPE, "desk_hidden_apps", payload)
	clear_desk_visibility_cache()
	frappe.clear_cache()
	return sorted(current)


@frappe.whitelist()
def get_app_visibility_state() -> dict:
	frappe.only_for("System Manager")
	company_activity = get_user_company_activity()
	return {
		"desk_hidden_apps": sorted(get_hidden_desk_apps()),
		"activity_hidden_apps": sorted(get_activity_hidden_apps(company_activity)),
		"effective_hidden_apps": sorted(get_desk_hidden_for_user()),
		"company_activity": company_activity,
		"allowed_activity_labels": sorted(_allowed_labels_for_company(company_activity)),
		"filter_desk_by_company_activity": _activity_filter_enabled(),
		"activity_filter_exempt_roles": sorted(_activity_filter_exempt_roles()),
		"protected_apps": ["frappe", "omnexa_core"],
		"platform_apps": sorted(PLATFORM_APP_SLUGS)
	}


@frappe.whitelist()
def set_app_desk_visibility(app_slug: str, hidden: int = 1) -> dict:
	hidden_apps = set_desk_app_hidden(app_slug, hidden=bool(int(hidden)))
	clear_desk_visibility_cache()
	return {"app_slug": app_slug, "hidden": bool(int(hidden)), "desk_hidden_apps": hidden_apps
	}


@frappe.whitelist()
def set_apps_desk_visibility(app_slugs, hidden: int = 1) -> dict:
	hidden_apps = set_apps_desk_hidden(app_slugs, hidden=bool(int(hidden)))
	processed = []
	if isinstance(app_slugs, str):
		text = app_slugs.strip()
		if text.startswith("["):
			try:
				processed = json.loads(text)
			except Exception:
				processed = [s.strip() for s in text.split(",") if s.strip()]
		else:
			processed = [s.strip() for s in text.split(",") if s.strip()]
	else:
		processed = list(app_slugs or [])
	return {"hidden": bool(int(hidden)), "desk_hidden_apps": hidden_apps, "count": len(processed)
	}


@frappe.whitelist()
def set_group_desk_visibility(group_key: str, hidden: int = 1) -> dict:
	from omnexa_core.omnexa_core.app_uninstall_groups import get_group_apps

	installed = set(frappe.get_installed_apps() or [])
	slugs = [a for a in get_group_apps(group_key) if a in installed and a not in {"frappe", "omnexa_core"}]
	hidden_apps = set_apps_desk_hidden(slugs, hidden=bool(int(hidden)))
	return {
		"group_key": group_key,
		"hidden": bool(int(hidden)),
		"apps": slugs,
		"count": len(slugs),
		"desk_hidden_apps": hidden_apps
	}


@frappe.whitelist()
def get_apps():
	"""Filter Desk /apps launcher — manual hide + company activity scope."""
	from frappe.apps import get_apps as frappe_get_apps

	apps = frappe_get_apps()
	hidden = get_desk_hidden_for_user()
	if not hidden:
		return apps
	return [app for app in apps if app.get("name") not in hidden]


def _module_app_name(module: str | None) -> str | None:
	if not module:
		return None
	if not hasattr(frappe.local, "module_app") or not frappe.local.module_app:
		frappe.setup_module_map()
	app = frappe.local.module_app.get(module)
	if app:
		return app
	# Fallback: "Omnexa ALM" → omnexa_alm, "ErpGenEx Property Mgmt" → erpgenex_property_mgmt
	installed = set(frappe.get_installed_apps() or [])
	for prefix, slug_prefix in (("Omnexa ", "omnexa_"), ("ErpGenEx ", "erpgenex_")):
		if module.startswith(prefix):
			slug = slug_prefix + module[len(prefix) :].strip().lower().replace(" ", "_").replace("-", "_")
			if slug in installed:
				return slug
	return None


def _workspace_app_slug(page: dict) -> str | None:
	name = (page.get("name") or "").strip()
	title = (page.get("title") or name).strip()
	for key in (name, title):
		if not key:
			continue
		alias_app = _finance_workspace_aliases().get(key)
		if alias_app:
			return alias_app
	try:
		from omnexa_core.omnexa_core.workspace_control_tower import _vertical_app_owns_workspace

		for key in (name, title):
			if not key:
				continue
			owner = _vertical_app_owns_workspace(key)
			if owner:
				return owner
	except Exception:
		pass
	module = page.get("module") or page.get("module_name") or ""
	return _module_app_name(module)


def _workspace_owned_by_hidden_app(page: dict, hidden: set[str]) -> bool:
	app = _workspace_app_slug(page)
	if app and app in hidden:
		return True
	if not hidden:
		return False
	finance_keys = _finance_activity_workspace_keys()
	name = (page.get("name") or "").strip()
	title = (page.get("title") or name).strip()
	if name in finance_keys or title in finance_keys:
		for key in (name, title):
			owner = _finance_workspace_aliases().get(key) or _workspace_app_slug({"name": key, "title": key, "module": ""})
			if owner and owner in hidden:
				return True
	return False


def _workspace_page_keys(page: dict) -> set[str]:
	name = (page.get("name") or "").strip()
	title = (page.get("title") or name).strip()
	return {k for k in (name, title) if k}


def _denied_workspace_keys(pages: list[dict], hidden: set[str]) -> list[str]:
	"""Explicit denylist for client-side sidebar — only out-of-activity workspaces."""
	if not pages or not hidden:
		return []
	denied: set[str] = set()
	for page in pages:
		if _workspace_owned_by_hidden_app(page, hidden):
			denied.update(_workspace_page_keys(page))
	return sorted(denied)


def _sector_parent_titles() -> set[str]:
	try:
		from omnexa_core.omnexa_core.sector_registry import get_sector_parent_titles

		return set(get_sector_parent_titles())
	except Exception:
		return set()


def _filter_workspace_pages(pages: list[dict], hidden: set[str]) -> list[dict]:
	if not pages or not hidden:
		return pages
	hidden = set(hidden) - INFRA_DESK_APPS
	if not hidden:
		return pages

	kept: list[dict] = []
	for page in pages:
		if _workspace_owned_by_hidden_app(page, hidden):
			continue
		kept.append(page)

	child_counts: dict[str, int] = {}
	for page in kept:
		parent = (page.get("parent_page") or "").strip()
		if parent:
			child_counts[parent] = child_counts.get(parent, 0) + 1

	sector_titles = _sector_parent_titles()
	if not sector_titles:
		return kept

	final: list[dict] = []
	for page in kept:
		title = (page.get("title") or page.get("name") or "").strip()
		if title in sector_titles and child_counts.get(title, 0) == 0:
			continue
		final.append(page)
	return final


def filter_workspace_sidebar_by_activity(result: dict) -> dict:
	"""Remove workspaces owned by apps outside the company activity scope."""
	if not _activity_filter_applies_to_user():
		return result
	hidden = get_desk_hidden_for_user()
	pages = result.get("pages") or []
	filtered = _filter_workspace_pages(pages, hidden)
	if len(filtered) != len(pages):
		result = {**result, "pages": filtered}
	return result


def inject_desk_visibility_boot(bootinfo) -> None:
	"""Apply manual + activity app hiding to boot apps list and workspace sidebar."""
	if isinstance(bootinfo, dict) and not isinstance(bootinfo, frappe._dict):
		bootinfo = frappe._dict(bootinfo)
	user = frappe.session.user
	hidden = get_desk_hidden_for_user(user)
	company = get_effective_company_for_activity(user)
	from omnexa_core.omnexa_core.session_context import get_activity_menu_scope, user_can_set_activity_menu_scope

	strict_filtering = company_strict_activity_filtering_enabled(company)
	filter_active = _activity_filter_applies_to_user(user)
	menu_scope = get_activity_menu_scope(user)
	if filter_active and not hidden:
		hidden = get_activity_hidden_apps(get_user_company_activity(user))

	bootinfo.omnexa_activity_filter = {
		"active": filter_active,
		"company": company,
		"company_activity": get_user_company_activity(user),
		"strict_company_filtering": strict_filtering,
		"can_set_activity_menu_scope": user_can_set_activity_menu_scope(user),
		"activity_menu_scope": menu_scope,
		"hidden_apps": sorted(set(hidden) - INFRA_DESK_APPS) if filter_active else [],
	}
	try:
		from omnexa_core.omnexa_core.isolation_middleware import isolation_context_for_boot

		bootinfo.omnexa_isolation_context = isolation_context_for_boot()
	except Exception:
		pass

	if not filter_active:
		bootinfo["omnexa_denied_workspace_keys"] = []
		return

	apps_data = bootinfo.get("apps_data") or {}
	apps_list = apps_data.get("apps") or []
	if apps_list:
		filtered = [a for a in apps_list if a.get("name") not in hidden]
		apps_data["apps"] = filtered
		bootinfo["apps_data"] = apps_data
		if filtered:
			bootinfo.setdefault("apps_data", {})["default_path"] = filtered[0].get("route") or "/app"

	pages = bootinfo.get("allowed_workspaces") or []
	if pages:
		filtered_pages = _filter_workspace_pages(pages, hidden)
		bootinfo["allowed_workspaces"] = filtered_pages
		bootinfo["omnexa_allowed_workspace_names"] = sorted(
			{(p.get("name") or "").strip() for p in filtered_pages if (p.get("name") or "").strip()}
		)
		bootinfo["omnexa_allowed_workspace_titles"] = sorted(
			{(p.get("title") or p.get("name") or "").strip() for p in filtered_pages if (p.get("title") or p.get("name") or "").strip()}
		)
		bootinfo["omnexa_denied_workspace_keys"] = _denied_workspace_keys(pages, hidden)

	page_info = bootinfo.get("page_info") or {}
	if page_info:
		filtered_pages_meta = {}
		for name, meta in page_info.items():
			page_row = {"name": name, "title": (meta or {}).get("title") or name, "module": (meta or {}).get("module") or ""}
			if _workspace_owned_by_hidden_app(page_row, hidden):
				continue
			filtered_pages_meta[name] = meta
		bootinfo["page_info"] = filtered_pages_meta
