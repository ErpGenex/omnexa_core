# Copyright (c) 2026, ErpGenEx
"""Wave 8 — Request-level activity isolation middleware."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

import frappe
from frappe import _

from omnexa_core.omnexa_core.activity_registry import apps_allowed_for_activity, get_activity, resolve_company_activity
from omnexa_core.omnexa_core.app_activity import activity_for_app
from omnexa_core.omnexa_core.session_context import get_activity_menu_scope, get_effective_company, user_can_set_activity_menu_scope


@dataclass(frozen=True)
class IsolationContext:
	company: str | None
	branch: str | None
	activity_id: str
	activity_label_en: str
	menu_scope: str
	strict_activity_filtering: bool
	allowed_apps: frozenset[str]
	user: str

	def app_allowed(self, app_slug: str) -> bool:
		if app_slug in self.allowed_apps:
			return True
		if self.menu_scope == "all" and user_can_set_activity_menu_scope(self.user):
			return True
		return False


def get_isolation_context(user: str | None = None) -> IsolationContext:
	user = user or frappe.session.user
	company = get_effective_company(user)
	spec = resolve_company_activity(company)
	allowed = apps_allowed_for_activity(spec.id)
	from omnexa_core.omnexa_core.company_activity_utils import company_strict_activity_filtering_enabled

	return IsolationContext(
		company=company,
		branch=None,
		activity_id=spec.id,
		activity_label_en=spec.label_en,
		menu_scope=get_activity_menu_scope(user),
		strict_activity_filtering=company_strict_activity_filtering_enabled(company) if company else False,
		allowed_apps=frozenset(allowed),
		user=user,
	)


def validate_cross_activity_app_access(app_slug: str, user: str | None = None) -> None:
	"""Raise if user/session activity does not allow target app."""
	ctx = get_isolation_context(user)
	if ctx.app_allowed(app_slug):
		return
	label = activity_for_app(app_slug)
	frappe.throw(
		_("App {0} ({1}) is outside the allowed scope for activity {2}.").format(app_slug, label, ctx.activity_label_en),
		frappe.PermissionError,
	)


def require_app_in_activity(app_slug: str | None = None):
	"""Decorator for whitelisted APIs — enforce activity isolation."""

	def decorator(fn: Callable):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			slug = app_slug
			if not slug:
				slug = frappe.local.form_dict.get("source_app") or frappe.local.form_dict.get("app")
			if slug:
				validate_cross_activity_app_access(slug)
			return fn(*args, **kwargs)

		return wrapper

	return decorator


def isolation_context_for_boot() -> dict[str, Any]:
	ctx = get_isolation_context()
	return {
		"company": ctx.company,
		"activity_id": ctx.activity_id,
		"activity_label_en": ctx.activity_label_en,
		"menu_scope": ctx.menu_scope,
		"strict_activity_filtering": ctx.strict_activity_filtering,
		"allowed_apps": sorted(ctx.allowed_apps),
	}


@frappe.whitelist()
def get_isolation_context_api() -> dict[str, Any]:
	return isolation_context_for_boot()
