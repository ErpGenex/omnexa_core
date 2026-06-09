# Copyright (c) 2026, ErpGenEx
"""Marketplace — scope site to one business activity (uninstall out-of-scope verticals)."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_activity import activity_for_app
from omnexa_core.omnexa_core.app_visibility import (
	COMPANY_ACTIVITY_ALLOWED,
	_allowed_labels_for_company,
	_ensure_settings_doc,
	_normalize_company_activity,
	clear_desk_visibility_cache,
	get_hidden_desk_apps,
	get_user_company_activity,
)
from omnexa_core.omnexa_core.app_visibility import PLATFORM_APP_SLUGS as _PLATFORM_APP_SLUGS

# Always kept on site: Frappe, core, backup, theme, cross-industry platform stack.
MANDATORY_INFRA_APPS = frozenset(
	{
		"frappe",
		"omnexa_core",
		"omnexa_backup",
		"erpgenex_theme_0426",
	}
)


def list_company_activities() -> list[str]:
	return sorted(COMPANY_ACTIVITY_ALLOWED.keys())


def _is_theme_app(app_slug: str) -> bool:
	return app_slug.startswith("erpgenex_theme")


def is_mandatory_site_app(app_slug: str) -> bool:
	if app_slug in MANDATORY_INFRA_APPS or app_slug in _PLATFORM_APP_SLUGS:
		return True
	if _is_theme_app(app_slug):
		return True
	extra = frappe.conf.get("omnexa_activity_scope_always_keep") or []
	if isinstance(extra, (list, tuple, set)):
		return app_slug in extra
	return False


def get_apps_to_keep_for_activity(company_activity: str | None) -> set[str]:
	"""Installed + would-keep slugs for the selected company business activity."""
	activity = _normalize_company_activity(company_activity)
	keep: set[str] = set(MANDATORY_INFRA_APPS) | set(_PLATFORM_APP_SLUGS)
	allowed = _allowed_labels_for_company(activity)

	slug_override = frappe.conf.get("omnexa_company_activity_app_slugs") or {}
	if isinstance(slug_override, dict) and activity in slug_override:
		keep |= {str(x).strip() for x in slug_override[activity] if str(x).strip()}

	for app in frappe.get_installed_apps() or []:
		if is_mandatory_site_app(app):
			keep.add(app)
			continue
		if activity_for_app(app) in allowed:
			keep.add(app)
	return keep


def get_apps_to_uninstall_for_activity(company_activity: str | None) -> list[str]:
	from omnexa_core.omnexa_core.marketplace import _installed_apps_that_require, _uninstall_protected_apps

	keep = get_apps_to_keep_for_activity(company_activity)
	protected = _uninstall_protected_apps()
	remove: list[str] = []
	for app in frappe.get_installed_apps() or []:
		if app in keep or app in protected:
			continue
		remove.append(app)
	return sorted(set(remove))


def _uninstall_order(remove: set[str]) -> list[str]:
	from omnexa_core.omnexa_core.marketplace import _installed_apps_that_require

	order: list[str] = []
	left = set(remove)
	while left:
		ready = []
		for app in left:
			dependents = [d for d in _installed_apps_that_require(app) if d in left]
			if not dependents:
				ready.append(app)
		if not ready:
			ready = [sorted(left)[0]]
		for app in sorted(ready):
			order.append(app)
			left.discard(app)
	return order


def _set_default_company_activity(company_activity: str) -> str | None:
	company = frappe.defaults.get_user_default("Company")
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company or not frappe.db.exists("Company", company):
		return None
	activity = _normalize_company_activity(company_activity)
	if frappe.db.has_column("Company", "business_activity"):
		frappe.db.set_value("Company", company, "business_activity", activity, update_modified=True)
	elif frappe.db.has_column("Company", "custom_business_activity"):
		frappe.db.set_value("Company", company, "custom_business_activity", activity, update_modified=True)
	frappe.db.commit()
	return company


def _prune_desk_hidden(removed: set[str]) -> None:
	if not removed or not frappe.db.exists("DocType", "Omnexa Marketplace Settings"):
		return
	hidden = get_hidden_desk_apps() - removed
	frappe.db.set_single_value(
		"Omnexa Marketplace Settings",
		"desk_hidden_apps",
		frappe.as_json(sorted(hidden)),
	)
	clear_desk_visibility_cache()


def get_activity_scope_plan(company_activity: str) -> dict:
	frappe.only_for("System Manager")
	activity = _normalize_company_activity(company_activity)
	if activity not in COMPANY_ACTIVITY_ALLOWED:
		frappe.throw(frappe._("Unknown business activity: {0}").format(company_activity))

	keep = sorted(get_apps_to_keep_for_activity(activity))
	remove = get_apps_to_uninstall_for_activity(activity)
	order = _uninstall_order(set(remove))
	blocked: list[dict] = []
	from omnexa_core.omnexa_core.marketplace import _installed_apps_that_require, _uninstall_protected_apps

	protected = _uninstall_protected_apps()
	for app in remove:
		deps = _installed_apps_that_require(app)
		outside = [d for d in deps if d not in remove and d not in protected]
		if outside:
			blocked.append({"app": app, "blocked_by_installed": outside})

	return {
		"company_activity": activity,
		"current_company_activity": get_user_company_activity(),
		"allowed_activity_labels": sorted(_allowed_labels_for_company(activity)),
		"mandatory_apps": sorted(MANDATORY_INFRA_APPS | _PLATFORM_APP_SLUGS),
		"apps_to_keep": keep,
		"apps_to_remove": remove,
		"uninstall_order": order,
		"blocked": blocked,
		"can_apply": not blocked and bool(remove or activity != get_user_company_activity()),
		"warning": frappe._(
			"This uninstalls every app that does not match the selected business activity. "
			"Platform apps (Accounting, HR, Core, Theme, Backup, etc.) stay installed. "
			"A database backup runs first unless disabled in site config."
		),
	}


def apply_activity_scope(company_activity: str, confirm: int = 0) -> dict:
	"""Uninstall out-of-scope apps and set default Company business activity."""
	frappe.only_for("System Manager")
	if not int(confirm or 0):
		return {"applied": False, "message": "confirmation_required"}

	plan = get_activity_scope_plan(company_activity)
	if plan.get("blocked"):
		frappe.throw(
			frappe._("Cannot apply scope — some apps have dependencies outside the removal list."),
			title=frappe._("Activity scope blocked"),
		)

	from omnexa_core.omnexa_core.marketplace import _is_truthy, _restore_frappe_session_user
	from omnexa_core.omnexa_core.omnexa_license import clear_license_key, clear_trial_for_app, set_manual_revoke
	from frappe.utils.backups import new_backup

	no_backup = _is_truthy(frappe.conf.get("omnexa_marketplace_uninstall_no_backup"))
	backup_ok = True
	if not no_backup:
		try:
			new_backup(ignore_files=False)
		except Exception:
			backup_ok = False
			if not _is_truthy(frappe.conf.get("omnexa_activity_scope_allow_backup_failure")):
				frappe.throw(frappe._("Backup failed before activity scope apply."), title=frappe._("Backup"))

	_ensure_settings_doc()
	activity = plan["company_activity"]
	uninstalled: list[str] = []
	failed: list[dict] = []
	previous_user = getattr(frappe.session, "user", None)

	for app_slug in plan["uninstall_order"]:
		if app_slug not in (frappe.get_installed_apps() or []):
			continue
		try:
			frappe.set_user("Administrator")
			from frappe.installer import remove_app

			remove_app(app_slug, dry_run=False, yes=True, no_backup=True, force=False)
			frappe.db.commit()
			for fn in (clear_license_key, clear_trial_for_app):
				try:
					fn(app_slug)
				except Exception:
					pass
			try:
				set_manual_revoke(app_slug, False)
			except Exception:
				pass
			uninstalled.append(app_slug)
		except Exception as exc:
			frappe.db.rollback()
			failed.append({"app": app_slug, "error": str(exc)})
			frappe.log_error(frappe.get_traceback(), f"Activity scope uninstall failed: {app_slug}")
		finally:
			_restore_frappe_session_user(previous_user)

	_prune_desk_hidden(set(uninstalled))
	_set_default_company_activity(activity)
	frappe.db.set_single_value("Omnexa Marketplace Settings", "filter_desk_by_company_activity", 1)
	clear_desk_visibility_cache()

	try:
		from omnexa_core.install import run_workspace_desk_sync

		run_workspace_desk_sync()
	except Exception:
		pass

	frappe.clear_cache()
	return {
		"applied": True,
		"company_activity": activity,
		"uninstalled": uninstalled,
		"failed": failed,
		"apps_kept": plan["apps_to_keep"],
		"backup_ok": backup_ok,
	}
