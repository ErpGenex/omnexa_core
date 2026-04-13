# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.webhook import WebhookRejectedError, process_webhook_event


class TestWebhook(FrappeTestCase):
	def test_process_webhook_records_processed_status(self):
		calls = {"count": 0}

		def processor(payload):
			calls["count"] += 1

		result = process_webhook_event(
			provider="psp_dummy",
			event_id="evt-001",
			payload={"amount": 10},
			processor=processor,
		)
		self.assertEqual(result["status"], "processed")
		self.assertEqual(calls["count"], 1)
		log = frappe.get_doc("Webhook Event Log", {"provider": "psp_dummy", "event_id": "evt-001"})
		self.assertEqual(log.processing_status, "Processed")

	def test_duplicate_webhook_skips_processing(self):
		calls = {"count": 0}

		def processor(payload):
			calls["count"] += 1

		process_webhook_event("psp_dummy", "evt-dup", {"amount": 1}, processor)
		result = process_webhook_event("psp_dummy", "evt-dup", {"amount": 1}, processor)
		self.assertEqual(result["status"], "duplicate")
		self.assertEqual(calls["count"], 1)

	def test_invalid_signature_rejected(self):
		def processor(payload):
			return None

		with self.assertRaises(WebhookRejectedError):
			process_webhook_event(
				provider="bank_csv",
				event_id="evt-sign",
				payload={"rows": 2},
				processor=processor,
				received_signature="bad",
				secret="secret",
			)
