# Copyright (c) 2026, ErpGenEx
"""Dynamic permission engine — role config + Frappe permission checks."""

from __future__ import annotations

from typing import Any

import frappe

from omnexa_core.multi_portal.config_loader import ConfigLoader


class DynamicPermissionEngine:
	"""Manages portal permissions from role JSON and Frappe DocType permissions."""

	def __init__(self):
		self.config_loader = ConfigLoader()

	def _cache_key(self, application_id: str, role_id: str) -> str:
		return f"multi_portal:permissions:{application_id}:{role_id}"

	def load_permissions(self, application_id: str, role_id: str) -> dict[str, Any]:
		cache_key = self._cache_key(application_id, role_id)
		cached = frappe.cache.get_value(cache_key)
		if cached:
			return cached

		role_config = self.config_loader.load_role_config(application_id, role_id)
		permissions_config = role_config.get("permissions", {})
		permissions = {
			"allowed_doctypes": permissions_config.get("allowed_doctypes", []),
			"allowed_actions": permissions_config.get("allowed_actions", []),
			"restricted_doctypes": permissions_config.get("restricted_doctypes", [])}
		frappe.cache.set_value(cache_key, permissions, expires_in_sec=3600)
		return permissions

	def validate_permission(
		self,
		user: str,
		doctype: str,
		action: str,
		application_id: str,
		role_id: str,
	) -> bool:
		if not user or not doctype or not action:
			return False

		permissions = self.load_permissions(application_id, role_id)
		if doctype in permissions.get("restricted_doctypes", []):
			return False
		if permissions.get("allowed_doctypes") and doctype not in permissions["allowed_doctypes"]:
			return False
		if permissions.get("allowed_actions") and action not in permissions["allowed_actions"]:
			return False

		permtype = {"read": "read", "create": "create", "write": "write", "delete": "delete"
	}.get(
			action, "read"
		)
		return frappe.has_permission(doctype, permtype, user=user)

	def get_allowed_doctypes(self, application_id: str, role_id: str) -> list[str]:
		return self.load_permissions(application_id, role_id).get("allowed_doctypes", [])

	def get_restricted_doctypes(self, application_id: str, role_id: str) -> list[str]:
		return self.load_permissions(application_id, role_id).get("restricted_doctypes", [])

	def get_allowed_actions(self, application_id: str, role_id: str) -> list[str]:
		return self.load_permissions(application_id, role_id).get("allowed_actions", [])

	def check_doctype_access(self, doctype: str, application_id: str, role_id: str) -> bool:
		permissions = self.load_permissions(application_id, role_id)
		if doctype in permissions.get("restricted_doctypes", []):
			return False
		if permissions.get("allowed_doctypes"):
			return doctype in permissions["allowed_doctypes"]
		return True

	def check_action_access(self, action: str, application_id: str, role_id: str) -> bool:
		permissions = self.load_permissions(application_id, role_id)
		if permissions.get("allowed_actions"):
			return action in permissions["allowed_actions"]
		return True

	def invalidate_permission_cache(self, application_id: str, role_id: str) -> None:
		frappe.cache.delete_value(self._cache_key(application_id, role_id))

	def invalidate_all_permission_cache(self) -> None:
		frappe.cache.delete_keys("multi_portal:permissions:")

	def get_permission_statistics(self) -> dict[str, Any]:
		return {"engine": "dynamic_permission_engine", "cache_prefix": "multi_portal:permissions:"
	}
