# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.marketplace import (
	_bulk_uninstall_plan,
	_capture_frappe_session,
	_parse_app_slug_list,
	_restore_frappe_session_snapshot,
	_restore_frappe_session_user,
)
from omnexa_core.omnexa_core.session_guard import apply_session_guard, is_invalid_session_user


class TestMarketplaceUninstall(FrappeTestCase):
	def test_restore_session_user_handles_none(self):
		frappe.set_user("Administrator")
		_restore_frappe_session_user(None)
		self.assertEqual(frappe.session.user, "Administrator")

	def test_restore_session_user_handles_empty(self):
		frappe.set_user("Administrator")
		_restore_frappe_session_user("")
		self.assertEqual(frappe.session.user, "Administrator")

	def test_invalid_session_user_detects_none(self):
		self.assertTrue(is_invalid_session_user(None))
		self.assertTrue(is_invalid_session_user("None"))
		self.assertFalse(is_invalid_session_user("Administrator"))

	def test_session_guard_patches_validate_user(self):
		apply_session_guard()
		from frappe.sessions import Session

		session = Session.__new__(Session)
		session.user = None
		session.sid = "test-corrupt-sid-does-not-exist"
		session.data = frappe._dict({"user": None, "data": {}})
		session.validate_user()
		self.assertEqual(session.user, "Guest")

	def test_restore_session_snapshot_preserves_sid(self):
		original_sid = frappe.session.sid
		snap = _capture_frappe_session()
		frappe.local.session.user = "Guest"
		frappe.local.session.sid = "corrupted-by-set-user"
		_restore_frappe_session_snapshot(snap)
		self.assertEqual(frappe.session.user, snap.get("user"))
		self.assertEqual(frappe.session.sid, original_sid)

	def test_restore_session_user_legacy_wrapper_keeps_sid(self):
		frappe.local.session.sid = "my-real-session-id"
		_restore_frappe_session_user("Administrator")
		self.assertEqual(frappe.session.user, "Administrator")
		self.assertEqual(frappe.session.sid, "my-real-session-id")

	def test_parse_app_slug_list_json(self):
		self.assertEqual(_parse_app_slug_list('["omnexa_a", "omnexa_b"]'), ["omnexa_a", "omnexa_b"])

	def test_bulk_uninstall_plan_blocks_protected(self):
		frappe.set_user("Administrator")
		plan = _bulk_uninstall_plan(["omnexa_core", "frappe"])
		self.assertFalse(plan["can_uninstall"])
		self.assertEqual([x["app"] for x in plan["protected"]], ["omnexa_core"])
		self.assertTrue(any(x["app"] == "frappe" for x in plan["blocked"]))

	def test_bulk_uninstall_plan_installed_app(self):
		frappe.set_user("Administrator")
		installed = [a for a in (frappe.get_installed_apps() or []) if a not in ("frappe", "omnexa_core")]
		eligible_slug = None
		for slug in installed:
			plan = _bulk_uninstall_plan([slug])
			if plan["eligible"]:
				eligible_slug = slug
				break
		if not eligible_slug:
			self.skipTest("no installed app without dependency blockers")
		plan = _bulk_uninstall_plan([eligible_slug])
		self.assertIn(eligible_slug, plan["eligible"])
		self.assertEqual(plan["uninstall_order"], [eligible_slug])
