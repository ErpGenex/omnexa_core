# Copyright (c) 2026, ErpGenEx
"""Desk visibility — manual hide + auto-filter by Company business activity."""

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.app_activity import activity_for_app

SETTINGS_DOCTYPE = "Omnexa Marketplace Settings"
MANUAL_CACHE_KEY = "omnexa_desk_hidden_apps"
USER_CACHE_HASH = "omnexa_desk_hidden_by_user"

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
	"Healthcare": _BASE_PLATFORM_LABELS | frozenset({"Healthcare"}),
	"Education": _BASE_PLATFORM_LABELS | frozenset({"Education"}),
	"Construction": _BASE_PLATFORM_LABELS | frozenset({"Construction", "Engineering", "ErpGenEx"}),
	"Engineering Consulting": _BASE_PLATFORM_LABELS | frozenset({"Engineering", "Construction"}),
	"Financial Services": _BASE_PLATFORM_LABELS
	| frozenset({"Finance", "Leasing", "Mortgage", "Factoring", "Credit", "Consumer", "Alm", "Risk", "Mobility", "Sme"}),
	"Trading": _BASE_PLATFORM_LABELS | frozenset({"Trading"}),
	"Manufacturing": _BASE_PLATFORM_LABELS | frozenset({"Manufacturing"}),
	"Agriculture": _BASE_PLATFORM_LABELS | frozenset({"Agriculture"}),
	"Tourism": _BASE_PLATFORM_LABELS | frozenset({"Tourism", "Mobility"}),
	"Hotel Assets": _BASE_PLATFORM_LABELS | frozenset({"Tourism", "ErpGenEx", "Fixed"}),
	"Bakeries": _BASE_PLATFORM_LABELS | frozenset({"Restaurant"}),
	"Services": _BASE_PLATFORM_LABELS | frozenset({"Services"}),
	"Statutory Audit": _BASE_PLATFORM_LABELS | frozenset({"Audit"}),
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


def get_user_company_activity() -> str:
	company = frappe.defaults.get_user_default("Company")
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company or not frappe.db.exists("Company", company):
		return "General"
	row = frappe.db.get_value(
		"Company",
		company,
		["business_activity", "industry_sector", "production_demo_activity"],
		as_dict=True,
	)
	if not row:
		return "General"
	for key in ("business_activity", "industry_sector", "production_demo_activity"):
		val = (row.get(key) or "").strip()
		if val and val.lower() not in ("", "general"):
			return _normalize_company_activity(val)
	return "General"


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


def _activity_filter_applies_to_user() -> bool:
	if not _activity_filter_enabled():
		return False
	if set(frappe.get_roles()) & _activity_filter_exempt_roles():
		return False
	return True


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
		return hidden

	hidden = set()
	for app in frappe.get_installed_apps() or []:
		if app in PLATFORM_APP_SLUGS or app == "frappe":
			continue
		if activity_for_app(app) not in allowed:
			hidden.add(app)
	return hidden


def _user_cache_key() -> str:
	company = frappe.defaults.get_user_default("Company") or ""
	return f"{frappe.session.user}::{company}"


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
				"activity_filter_exempt_roles": "System Manager",
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


def get_desk_hidden_for_user() -> set[str]:
	"""Manual + activity-based hidden apps for the current session user."""
	bucket = _user_cache_key()
	cached = frappe.cache.hget(USER_CACHE_HASH, bucket)
	if cached is not None:
		return set(cached)

	hidden = set(get_hidden_desk_apps())
	if _activity_filter_applies_to_user():
		hidden |= get_activity_hidden_apps()

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
		"platform_apps": sorted(PLATFORM_APP_SLUGS),
	}


@frappe.whitelist()
def set_app_desk_visibility(app_slug: str, hidden: int = 1) -> dict:
	hidden_apps = set_desk_app_hidden(app_slug, hidden=bool(int(hidden)))
	clear_desk_visibility_cache()
	return {"app_slug": app_slug, "hidden": bool(int(hidden)), "desk_hidden_apps": hidden_apps}


@frappe.whitelist()
def get_apps():
	"""Filter Desk /apps launcher — manual hide + company activity scope."""
	from frappe.apps import get_apps as frappe_get_apps

	apps = frappe_get_apps()
	hidden = get_desk_hidden_for_user()
	if not hidden:
		return apps
	return [app for app in apps if app.get("name") not in hidden]
