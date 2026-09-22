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
from omnexa_core.omnexa_core.company_activity_utils import (
	company_strict_activity_filtering_enabled,
	first_company_activity_value,
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


def _candidate_apps_to_remove(keep: set[str]) -> set[str]:
	from omnexa_core.omnexa_core.marketplace import _uninstall_protected_apps

	protected = _uninstall_protected_apps()
	remove: set[str] = set()
	for app in frappe.get_installed_apps() or []:
		if app in keep or app in protected:
			continue
		remove.add(app)
	return remove


def _resolve_remove_list(keep: set[str]) -> tuple[list[str], list[dict], list[dict]]:
	"""
	Build final uninstall list.

	Apps required by a *kept* installed app (e.g. maintenance for Fixed Assets) are skipped,
	not treated as a hard block for the whole operation.
	"""
	from omnexa_core.omnexa_core.marketplace import _installed_apps_that_require, _uninstall_protected_apps

	protected = _uninstall_protected_apps()
	remove = _candidate_apps_to_remove(keep)
	skipped: list[dict] = []
	blocked: list[dict] = []

	changed = True
	while changed:
		changed = False
		for app in list(remove):
			dependents = _installed_apps_that_require(app)
			kept_dependents = [d for d in dependents if d in keep]
			if kept_dependents:
				remove.discard(app)
				skipped.append({"app": app, "kept_because_required_by": kept_dependents
	})
				changed = True
				continue
			hard = [d for d in dependents if d not in keep and d not in remove and d not in protected]
			if hard:
				blocked.append({"app": app, "blocked_by_installed": hard
	})

	return sorted(remove), skipped, blocked


def get_apps_to_uninstall_for_activity(company_activity: str | None) -> list[str]:
	keep = get_apps_to_keep_for_activity(company_activity)
	remove, _skipped, _blocked = _resolve_remove_list(keep)
	return remove


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


def _list_site_companies() -> list[str]:
	companies = frappe.get_all("Company", pluck="name", order_by="creation asc")
	if companies:
		return companies
	default_company = frappe.db.get_single_value("Global Defaults", "default_company")
	return [default_company] if default_company else []


def _company_profile_drift(target_activity: str) -> list[dict]:
	"""Companies whose activity or strict desk flag does not match the target scope."""
	activity = _normalize_company_activity(target_activity)
	drift: list[dict] = []
	for company in _list_site_companies():
		if not company or not frappe.db.exists("Company", company):
			continue
		current = _normalize_company_activity(first_company_activity_value(company))
		strict = company_strict_activity_filtering_enabled(company)
		if current != activity or not strict:
			drift.append(
				{
					"company": company,
					"business_activity": current,
					"strict_activity_menu_filtering": int(strict),
				}
			)
	return drift


def _apply_all_companies_activity(company_activity: str) -> list[str]:
	"""Set business activity + strict menu filtering on every Company on this site."""
	from omnexa_core.install import _apply_company_profile_fields

	activity = _normalize_company_activity(company_activity)
	updated: list[str] = []
	for company in _list_site_companies():
		if not company or not frappe.db.exists("Company", company):
			continue
		_apply_company_profile_fields(company, activity, activity)
		if frappe.db.has_column("Company", "strict_activity_menu_filtering"):
			frappe.db.set_value(
				"Company",
				company,
				"strict_activity_menu_filtering",
				1,
				update_modified=False,
			)
		updated.append(company)
	if updated:
		frappe.db.commit()
	return updated


def _installed_out_of_scope(keep: set[str]) -> list[str]:
	installed = set(frappe.get_installed_apps() or [])
	return sorted(
		app
		for app in installed
		if app not in keep and not is_mandatory_site_app(app)
	)


def _vertical_apps_status(activity: str) -> dict:
	from omnexa_core.omnexa_core.activity_registry import get_activity

	spec = get_activity(activity)
	installed = set(frappe.get_installed_apps() or [])
	expected = list(spec.vertical_apps)
	missing = [app for app in expected if app not in installed]
	present = [app for app in expected if app in installed]
	return {
		"vertical_apps_expected": expected,
		"vertical_apps_present": present,
		"vertical_apps_missing": missing,
	}


def _reconcile_desk_hidden_for_activity(keep: set[str]) -> list[str]:
	"""Persist Desk hide for installed apps that remain outside the activity keep-set."""
	out = _installed_out_of_scope(keep)
	if not out:
		return []
	_ensure_settings_doc()
	hidden = get_hidden_desk_apps() | set(out)
	frappe.db.set_single_value(
		"Omnexa Marketplace Settings",
		"desk_hidden_apps",
		frappe.as_json(sorted(hidden)),
	)
	clear_desk_visibility_cache()
	return out


def _sync_desk_after_scope(activity: str) -> dict:
	stats: dict = {}
	try:
		from omnexa_core.install import run_workspace_desk_sync, sync_vertical_app_workspace_menus

		stats["vertical_menus"] = sync_vertical_app_workspace_menus()
		run_workspace_desk_sync()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Activity scope workspace sync")
	stats["activity"] = _normalize_company_activity(activity)
	return stats


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

	keep_set = get_apps_to_keep_for_activity(activity)
	keep = sorted(keep_set)
	remove, skipped, blocked = _resolve_remove_list(keep_set)
	order = _uninstall_order(set(remove))
	current = get_user_company_activity()
	activity_changed = activity != current
	profile_drift = _company_profile_drift(activity)
	out_of_scope_installed = _installed_out_of_scope(keep_set)
	vertical = _vertical_apps_status(activity)
	needs_reconcile = bool(remove or activity_changed or profile_drift or out_of_scope_installed)

	return {
		"company_activity": activity,
		"current_company_activity": current,
		"activity_changed": activity_changed,
		"companies_on_site": _list_site_companies(),
		"companies_profile_drift": profile_drift,
		"allowed_activity_labels": sorted(_allowed_labels_for_company(activity)),
		"mandatory_apps": sorted(MANDATORY_INFRA_APPS | _PLATFORM_APP_SLUGS),
		"apps_to_keep": keep,
		"apps_to_remove": remove,
		"apps_out_of_scope_still_installed": out_of_scope_installed,
		"apps_skipped_dependency": skipped,
		"uninstall_order": order,
		"blocked": blocked,
		"can_apply": not blocked and needs_reconcile,
		"already_scoped": not blocked and not needs_reconcile,
		"strict_menu_filtering_on_apply": True,
		**vertical,
		"warning": frappe._(
			"This uninstalls every app that does not match the selected business activity. "
			"All companies on this site get the same business activity and strict desk menu filtering. "
			"Platform apps (Accounting, HR, Core, Theme, Backup, etc.) stay installed. "
			"Apps that cannot be uninstalled stay hidden on Desk. "
			"A database backup runs first unless disabled in site config."
		),
	}


def apply_activity_scope(company_activity: str, confirm: int = 0) -> dict:
	"""Uninstall out-of-scope apps and set default Company business activity."""
	frappe.only_for("System Manager")
	if not int(confirm or 0):
		return {"applied": False, "message": "confirmation_required"
	}

	plan = get_activity_scope_plan(company_activity)
	if plan.get("blocked"):
		frappe.throw(
			frappe._("Cannot apply scope — some apps have dependencies outside the removal list."),
			title=frappe._("Activity scope blocked"),
		)
	if plan.get("already_scoped"):
		return {
			"applied": False,
			"message": "already_scoped",
			"company_activity": plan["company_activity"],
		}

	from omnexa_core.omnexa_core.marketplace import (
		_elevate_to_administrator_for_uninstall,
		_finalize_uninstall_session,
		_is_truthy,
		_restore_frappe_session_snapshot,
	)
	from omnexa_core.omnexa_core.omnexa_license import clear_license_key, clear_trial_for_app, set_manual_revoke
	from frappe.utils.backups import new_backup

	no_backup = _is_truthy(frappe.conf.get("omnexa_marketplace_uninstall_no_backup"))
	if not (plan.get("apps_to_remove") or []) and not _is_truthy(
		frappe.conf.get("omnexa_activity_scope_backup_when_no_uninstall")
	):
		no_backup = True
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
	session_snap = _elevate_to_administrator_for_uninstall()
	try:
		for app_slug in plan["uninstall_order"]:
			if app_slug not in (frappe.get_installed_apps() or []):
				continue
			try:
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
				failed.append({"app": app_slug, "error": str(exc)
	})
				frappe.log_error(frappe.get_traceback(), f"Activity scope uninstall failed: {app_slug}")
	finally:
		_restore_frappe_session_snapshot(session_snap)

	_prune_desk_hidden(set(uninstalled))
	companies_updated = _apply_all_companies_activity(activity)
	desk_hidden = _reconcile_desk_hidden_for_activity(set(plan["apps_to_keep"]))
	frappe.db.set_single_value("Omnexa Marketplace Settings", "filter_desk_by_company_activity", 1)
	clear_desk_visibility_cache()
	desk_sync = _sync_desk_after_scope(activity)

	frappe.clear_cache()
	_finalize_uninstall_session()
	return {
		"applied": True,
		"company_activity": activity,
		"companies_updated": companies_updated,
		"uninstalled": uninstalled,
		"failed": failed,
		"apps_kept": plan["apps_to_keep"],
		"desk_hidden_out_of_scope": desk_hidden,
		"desk_sync": desk_sync,
		"backup_ok": backup_ok,
	}
