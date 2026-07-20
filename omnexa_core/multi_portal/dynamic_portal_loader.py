# Copyright (c) 2026, ErpGenEx
"""Dynamic portal loader with Frappe cache."""

from __future__ import annotations

from typing import Any

import frappe

from omnexa_core.multi_portal.portal_factory import Portal, PortalFactory


class DynamicPortalLoader:
	"""Loads and caches portal instances per user/application/role."""

	def __init__(self):
		self.portal_factory = PortalFactory()

	def _cache_key(self, user: str, application_id: str, role_id: str) -> str:
		return f"multi_portal:portal:{user}:{application_id}:{role_id}"

	def load_portal(self, user: str, application_id: str, role_id: str) -> Portal:
		cache_key = self._cache_key(user, application_id, role_id)
		cached = frappe.cache.get_value(cache_key)
		if cached:
			return cached

		portal = self.portal_factory.create_portal(application_id, role_id)
		frappe.cache.set_value(cache_key, portal, expires_in_sec=3600)
		return portal

	def load_portal_modules(self, application_id: str) -> list[str]:
		app_config = self.portal_factory.config_loader.load_application_config(application_id)
		return app_config.get("modules", [])

	def preload_critical_modules(self, application_id: str) -> None:
		for module in self.load_portal_modules(application_id)[:3]:
			if module:
				frappe.cache.set_value(f"multi_portal:module_preloaded:{application_id}:{module}", True, expires_in_sec=86400)

	def invalidate_user_cache(self, user: str) -> None:
		frappe.cache.delete_keys(f"multi_portal:portal:{user}:")

	def invalidate_application_cache(self, application_id: str) -> None:
		frappe.cache.delete_keys(f"multi_portal:portal:*:{application_id}:")

	def get_portal_statistics(self) -> dict[str, Any]:
		return {"engine": "dynamic_portal_loader", "cache_prefix": "multi_portal:portal:"}
