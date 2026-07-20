# Copyright (c) 2026, ErpGenEx
"""Recover from corrupt Frappe sessions (e.g. user stored as None after marketplace uninstall)."""

from __future__ import annotations

import frappe

_INVALID_USERS = frozenset({"", "none", "null", "undefined"})


def is_invalid_session_user(user: str | None) -> bool:
	if user is None:
		return True
	return str(user).strip().lower() in _INVALID_USERS


def purge_corrupt_sessions() -> dict:
	"""Delete Sessions rows / cache entries with missing or invalid user ids."""
	stats = {"db_deleted": 0, "cache_deleted": 0
	}
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return stats

	rows = frappe.db.sql(
		"""
		SELECT sid FROM `tabSessions`
		WHERE user IS NULL OR TRIM(user) = '' OR LOWER(TRIM(user)) IN ('none', 'null', 'undefined')
		""",
		as_dict=True,
	)
	for row in rows:
		sid = row.get("sid")
		if not sid:
			continue
		frappe.db.delete("Sessions", {"sid": sid
	})
		frappe.cache.hdel("session", sid)
		frappe.cache.hdel("last_db_session_update", sid)
		stats["db_deleted"] += 1

	try:
		cache = frappe.cache.hgetall("session") or {}
	except Exception:
		cache = {}

	for sid, payload in cache.items():
		user = None
		if isinstance(payload, dict):
			user = payload.get("user")
			inner = payload.get("data")
			if is_invalid_session_user(user) and isinstance(inner, dict):
				user = inner.get("user")
		if is_invalid_session_user(user):
			frappe.cache.hdel("session", sid)
			frappe.cache.hdel("last_db_session_update", sid)
			stats["cache_deleted"] += 1

	if stats["db_deleted"]:
		frappe.db.commit()
	return stats


def apply_session_guard() -> None:
	"""Monkey-patch Session.validate_user once per worker."""
	import frappe.sessions

	cls = frappe.sessions.Session
	if getattr(cls.validate_user, "_omnexa_session_guard", False):
		return

	_original = cls.validate_user

	def validate_user(self):
		if is_invalid_session_user(self.user):
			sid = getattr(self, "sid", None)
			if sid and sid != "Guest":
				frappe.sessions.delete_session(sid, reason="Corrupt session user")
			self.user = "Guest"
			self.data["user"] = "Guest"
			inner = self.data.get("data")
			if isinstance(inner, dict):
				inner["user"] = "Guest"
			return
		return _original(self)

	validate_user._omnexa_session_guard = True
	cls.validate_user = validate_user


@frappe.whitelist()
def purge_corrupt_sessions_now():
	frappe.only_for("System Manager")
	stats = purge_corrupt_sessions()
	frappe.clear_cache()
	return stats
