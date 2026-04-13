# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _


class IntegrationHubError(frappe.ValidationError):
	pass


@dataclass(frozen=True)
class IntegrationResult:
	status: str
	provider_reference: str
	message: str = ""
	data: dict[str, Any] | None = None


class InMemoryIdempotencyStore:
	def __init__(self):
		self._results: dict[str, IntegrationResult] = {}

	def get(self, key: str) -> IntegrationResult | None:
		return self._results.get(key)

	def set(self, key: str, result: IntegrationResult):
		self._results[key] = result


class PSPAdapter:
	name = "psp_dummy"

	def process(self, payload: dict[str, Any]) -> IntegrationResult:
		action = payload.get("action")
		amount = float(payload.get("amount") or 0)
		currency = payload.get("currency") or "EGP"
		if action not in {"authorize", "capture", "refund"}:
			raise IntegrationHubError(_("Unsupported PSP action."))
		if amount <= 0:
			raise IntegrationHubError(_("PSP amount must be greater than zero."))
		ref = f"PSP-{action.upper()}-{currency}-{int(amount * 100)}"
		return IntegrationResult(status="ok", provider_reference=ref, data={"action": action, "amount": amount})


class BankCsvAdapter:
	name = "bank_csv"

	def process(self, payload: dict[str, Any]) -> IntegrationResult:
		content = (payload.get("csv_content") or "").strip()
		if not content:
			raise IntegrationHubError(_("Bank CSV content is required."))
		total = 0.0
		rows = 0
		currencies: set[str] = set()
		for index, line in enumerate(content.splitlines(), start=1):
			parts = [p.strip() for p in line.split(",")]
			if len(parts) != 3:
				raise IntegrationHubError(_("Invalid bank CSV row format."))
			if index == 1 and [p.lower() for p in parts] == ["account", "amount", "currency"]:
				continue
			try:
				amount = float(parts[1])
			except ValueError as exc:
				raise IntegrationHubError(_("Invalid amount in bank CSV row {0}.").format(index)) from exc
			if amount <= 0:
				raise IntegrationHubError(_("Bank CSV amount must be greater than zero in row {0}.").format(index))
			total += amount
			currencies.add(parts[2])
			rows += 1
		if rows == 0:
			raise IntegrationHubError(_("Bank CSV must contain at least one data row."))
		ref = f"BANK-CSV-{rows}"
		return IntegrationResult(
			status="ok",
			provider_reference=ref,
			data={"rows": rows, "total_amount": total, "currencies": sorted(currencies)},
		)


class EInvoiceAdapter:
	name = "einvoice_stub"

	def process(self, payload: dict[str, Any]) -> IntegrationResult:
		reference = payload.get("reference_name")
		if not reference:
			raise IntegrationHubError(_("reference_name is required for e-invoice dispatch."))
		return IntegrationResult(status="queued", provider_reference=f"EINV-{reference}")


class IntegrationHub:
	def __init__(self, idempotency_store: InMemoryIdempotencyStore | None = None):
		self.adapters: dict[str, Any] = {}
		self.idempotency_store = idempotency_store or InMemoryIdempotencyStore()

	def register(self, adapter):
		self.adapters[adapter.name] = adapter

	def register_country_adapter(self, country_code: str, adapter):
		country_code = (country_code or "").strip().upper()
		if not country_code:
			raise IntegrationHubError(_("country_code is required to register a country adapter."))
		if not getattr(adapter, "name", None):
			raise IntegrationHubError(_("Adapter must define a name."))
		self.register(adapter)

	def dispatch(self, adapter_name: str, payload: dict[str, Any], idempotency_key: str | None = None) -> IntegrationResult:
		adapter = self.adapters.get(adapter_name)
		if not adapter:
			raise IntegrationHubError(_("Adapter {0} is not registered.").format(adapter_name))
		key = f"{adapter_name}:{idempotency_key}" if idempotency_key else None
		if key:
			existing = self.idempotency_store.get(key)
			if existing:
				return existing
		result = adapter.process(payload)
		if key:
			self.idempotency_store.set(key, result)
		return result


def get_default_hub() -> IntegrationHub:
	hub = IntegrationHub()
	hub.register(PSPAdapter())
	hub.register(BankCsvAdapter())
	hub.register(EInvoiceAdapter())
	for path in frappe.get_hooks("omnexa_register_integration_hub", default=None) or []:
		try:
			frappe.get_attr(path)(hub)
		except Exception:
			frappe.log_error(
				title="omnexa_register_integration_hub hook failed",
				message=f"Hook: {path}\n{frappe.get_traceback()}",
			)
	return hub
