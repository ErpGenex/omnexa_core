# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.marketplace import _restore_frappe_session_user
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

	def test_restore_session_user_restores_real_user(self):
		if not frappe.db.exists("User", "Administrator"):
			self.skipTest("no Administrator")
		frappe.set_user("Administrator")
		_restore_frappe_session_user("Administrator")
		self.assertEqual(frappe.session.user, "Administrator")
