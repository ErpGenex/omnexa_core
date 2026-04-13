# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.constants import (
	CLOSED_PIPELINE_STAGES,
	DOC_STATUS_QUEUED,
	OPEN_PIPELINE_STAGES,
)
from omnexa_core.omnexa_core.integration_hub import IntegrationHubError, get_default_hub


class TestIntegrationHub(FrappeTestCase):
	def test_psp_adapter_authorize(self):
		hub = get_default_hub()
		result = hub.dispatch(
			"psp_dummy",
			{"action": "authorize", "amount": 125.5, "currency": "EGP"},
			idempotency_key="txn-1",
		)
		self.assertEqual(result.status, "ok")
		self.assertTrue(result.provider_reference.startswith("PSP-AUTHORIZE"))

	def test_bank_csv_adapter_parses_totals(self):
		hub = get_default_hub()
		result = hub.dispatch(
			"bank_csv",
			{"csv_content": "account,amount,currency\nACC1,100.5,EGP\nACC2,50,EGP"},
			idempotency_key="bank-1",
		)
		self.assertEqual(result.status, "ok")
		self.assertEqual(result.data["rows"], 2)
		self.assertEqual(result.data["total_amount"], 150.5)
		self.assertEqual(result.data["currencies"], ["EGP"])

	def test_bank_csv_adapter_rejects_invalid_amount(self):
		hub = get_default_hub()
		with self.assertRaises(IntegrationHubError):
			hub.dispatch(
				"bank_csv",
				{"csv_content": "ACC1,abc,EGP"},
				idempotency_key="bank-invalid",
			)

	def test_idempotency_returns_same_result(self):
		hub = get_default_hub()
		first = hub.dispatch(
			"psp_dummy",
			{"action": "capture", "amount": 10, "currency": "EGP"},
			idempotency_key="dup-key",
		)
		second = hub.dispatch(
			"psp_dummy",
			{"action": "capture", "amount": 999, "currency": "EGP"},
			idempotency_key="dup-key",
		)
		self.assertEqual(first.provider_reference, second.provider_reference)

	def test_unknown_adapter_raises(self):
		hub = get_default_hub()
		with self.assertRaises(IntegrationHubError):
			hub.dispatch("missing_adapter", {}, idempotency_key="x")

	def test_shared_constants_available(self):
		self.assertEqual(DOC_STATUS_QUEUED, "Queued")
		self.assertIn("Prospecting", OPEN_PIPELINE_STAGES)
		self.assertIn("Won", CLOSED_PIPELINE_STAGES)
