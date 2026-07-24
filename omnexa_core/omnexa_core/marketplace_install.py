# Copyright (c) 2026, ErpGenEx
"""Marketplace install — ensure core/basic apps only; skip full ``required_apps`` chains."""

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe.installer import (
	add_module_defs,
	add_to_installed_apps,
	parse_app_name,
	set_all_patches_as_completed,
)
from frappe.utils.dashboard import sync_dashboards

from omnexa_core.omnexa_core.install_pkg.constants import BASIC_PLATFORM_APPS


def _is_truthy(value) -> bool:
	return value in (1, True, "1", "true", "True", "yes", "on")


def _install_stack() -> set[str]:
	"""Track in-flight marketplace installs to avoid circular prerequisite recursion."""
	stack = getattr(frappe.flags, "omnexa_marketplace_install_stack", None)
	if isinstance(stack, set):
		return stack
	if stack is None:
		stack = set()
	elif isinstance(stack, (list, tuple, set)):
		stack = set(stack)
	else:
		stack = set()
	frappe.flags.omnexa_marketplace_install_stack = stack
	return stack


@contextmanager
def _push_install_stack(app_slug: str):
	stack = _install_stack()
	if app_slug in stack:
		yield False
		return
	stack.add(app_slug)
	try:
		yield True
	finally:
		stack.discard(app_slug)
		if not stack:
			try:
				delattr(frappe.flags, "omnexa_marketplace_install_stack")
			except Exception:
				pass


def marketplace_basic_deps_only_enabled() -> bool:
	"""Default: marketplace installs only pull core/basic apps, not full ``required_apps``."""
	if _is_truthy(frappe.conf.get("omnexa_marketplace_full_required_apps")):
		return False
	return True


def basic_platform_apps() -> list[str]:
	"""Ordered platform apps to ensure before installing a marketplace app."""
	custom = frappe.conf.get("omnexa_marketplace_basic_apps")
	if isinstance(custom, (list, tuple)):
		return [str(x).strip() for x in custom if str(x).strip()]
	return list(BASIC_PLATFORM_APPS)


def _app_on_bench(app_slug: str) -> bool:
	try:
		return app_slug in (frappe.get_all_apps() or [])
	except Exception:
		return False


def missing_basic_platform_apps(exclude: str | None = None) -> list[str]:
	installed = set(frappe.get_installed_apps() or [])
	out: list[str] = []
	for app in basic_platform_apps():
		if app == exclude:
			continue
		if app not in installed and _app_on_bench(app):
			out.append(app)
	return out


def skipped_required_apps_for(app_slug: str) -> list[str]:
	"""Apps declared in ``required_apps`` but not auto-installed by marketplace policy."""
	if not marketplace_basic_deps_only_enabled():
		return []
	try:
		app_hooks = frappe.get_hooks(app_name=app_slug)
	except Exception:
		return []
	required = app_hooks.get("required_apps") or []
	basics = set(basic_platform_apps())
	installed = set(frappe.get_installed_apps() or [])
	skipped: list[str] = []
	for dep in required:
		dep_slug = parse_app_name(dep)
		if dep_slug in basics or dep_slug in installed or dep_slug == app_slug:
			continue
		if _app_on_bench(dep_slug):
			skipped.append(dep_slug)
	return sorted(set(skipped))


def install_app_on_site(app_slug: str, *, force: bool = False, verbose: bool = False) -> None:
	"""
	Install one app on the current site.

	When ``marketplace_basic_deps_only_enabled()`` (default), only ``basic_platform_apps``
	are installed as prerequisites — not the full ``hooks.required_apps`` chain.
	"""
	from frappe.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
	from frappe.model.sync import sync_for
	from frappe.modules.utils import sync_customizations
	from frappe.utils.fixtures import sync_fixtures

	with _push_install_stack(app_slug) as entered:
		if not entered:
			return

		if not _app_on_bench(app_slug):
			raise frappe.ValidationError(frappe._("App {0} is not available on this bench.").format(app_slug))

		installed = list(frappe.get_installed_apps() or [])

		if marketplace_basic_deps_only_enabled():
			for basic in basic_platform_apps():
				if basic == app_slug or basic in installed or not _app_on_bench(basic):
					continue
				install_app_on_site(basic, force=force, verbose=verbose)
				installed = list(frappe.get_installed_apps() or [])
		elif not force:
			from frappe.installer import install_app

			app_hooks = frappe.get_hooks(app_name=app_slug)
			for app in app_hooks.get("required_apps") or []:
				required_app = parse_app_name(app)
				if required_app not in (frappe.get_installed_apps() or []):
					install_app(required_app, verbose=verbose, force=force)

		installed = list(frappe.get_installed_apps() or [])
		if not force and app_slug in installed:
			return

		frappe.flags.in_install = app_slug
		frappe.flags.ignore_in_install = False
		try:
			frappe.clear_cache()
			app_hooks = frappe.get_hooks(app_name=app_slug)

			if app_slug != "frappe":
				frappe.only_for("System Manager")

			for before_install in app_hooks.before_install or []:
				out = frappe.get_attr(before_install)()
				if out is False:
					return

			for fn in frappe.get_hooks("before_app_install"):
				frappe.get_attr(fn)(app_slug)

			if app_slug != "frappe":
				add_module_defs(app_slug, ignore_if_duplicate=force)

			sync_for(app_slug, force=force, reset_permissions=True)
			add_to_installed_apps(app_slug)

			try:
				frappe.get_doc("Portal Settings", "Portal Settings").sync_menu()
			except Exception:
				pass

			set_all_patches_as_completed(app_slug)

			for after_install in app_hooks.after_install or []:
				frappe.get_attr(after_install)()

			for fn in frappe.get_hooks("after_app_install"):
				frappe.get_attr(fn)(app_slug)

			sync_jobs()
			sync_fixtures(app_slug)
			sync_customizations(app_slug)
			sync_dashboards(app_slug)

			for after_sync in app_hooks.after_sync or []:
				frappe.get_attr(after_sync)()

			frappe.clear_cache()
		finally:
			frappe.flags.in_install = False
