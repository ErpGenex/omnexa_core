# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.messaging_bounce import (
	mark_recipient_bounced,
	normalize_bounce_event,
	should_suppress_recipient,
)


class TestMessagingBounce(FrappeTestCase):
	def tearDown(self):
		super().tearDown()
		frappe.cache().hdel("omnexa_bounce_registry", "user@example.com")
		frappe.cache().hdel("omnexa_bounce_registry", "+201000000000")

	def test_normalize_bounce_event(self):
		event = normalize_bounce_event(
			"email",
			{"recipient": "User@example.com", "event_type": "hard_bounce", "provider_ref": "evt-1"},
		)
		self.assertEqual(event["recipient"], "user@example.com")
		self.assertEqual(event["event_type"], "hard_bounce")

	def test_mark_bounce_enables_suppression(self):
		mark_recipient_bounced(
			"email",
			{"recipient": "user@example.com", "event_type": "hard_bounce"},
		)
		self.assertTrue(should_suppress_recipient("user@example.com", "email"))
		self.assertFalse(should_suppress_recipient("user@example.com", "sms"))

	def test_sms_invalid_number_enables_sms_suppression(self):
		mark_recipient_bounced(
			"sms",
			{"recipient": "+201000000000", "event_type": "invalid_number"},
		)
		self.assertTrue(should_suppress_recipient("+201000000000", "sms"))
