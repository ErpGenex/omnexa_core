# Copyright (c) 2026, ErpGenEx
"""Wave 8b — Thin bridge for vertical apps → integration bus (no direct accounting imports)."""

from __future__ import annotations

from typing import Any

import frappe

from omnexa_core.omnexa_core.integration_bus import IntegrationCommandResult, IntegrationBusError, dispatch_command


def _source_app(source_app: str | None) -> str:
	if source_app:
		return source_app
	return getattr(frappe.local, "app_name", None) or "unknown"


def create_sales_invoice(
	payload: dict[str, Any],
	*,
	source_app: str | None = None,
	idempotency_key: str | None = None,
	submit: bool = False,
) -> IntegrationCommandResult:
	body = dict(payload)
	if submit:
		body["submit"] = True
	return dispatch_command(
		"accounting.create_sales_invoice",
		body,
		source_app=_source_app(source_app),
		idempotency_key=idempotency_key,
	)


def create_purchase_invoice(
	payload: dict[str, Any],
	*,
	source_app: str | None = None,
	idempotency_key: str | None = None,
	submit: bool = False,
) -> IntegrationCommandResult:
	body = dict(payload)
	if submit:
		body["submit"] = True
	return dispatch_command(
		"accounting.create_purchase_invoice",
		body,
		source_app=_source_app(source_app),
		idempotency_key=idempotency_key,
	)


def create_journal_entry(
	payload: dict[str, Any],
	*,
	source_app: str | None = None,
	idempotency_key: str | None = None,
	submit: bool = False,
) -> IntegrationCommandResult:
	body = dict(payload)
	if submit:
		body["submit"] = True
	return dispatch_command(
		"accounting.create_journal_entry",
		body,
		source_app=_source_app(source_app),
		idempotency_key=idempotency_key,
	)


def create_stock_entry(
	payload: dict[str, Any],
	*,
	source_app: str | None = None,
	idempotency_key: str | None = None,
	submit: bool = False,
) -> IntegrationCommandResult:
	body = dict(payload)
	if submit:
		body["submit"] = True
	return dispatch_command(
		"inventory.create_stock_entry",
		body,
		source_app=_source_app(source_app),
		idempotency_key=idempotency_key,
	)


def financial_snapshot(company: str, *, source_app: str | None = None) -> IntegrationCommandResult:
	return dispatch_command(
		"reporting.get_financial_snapshot",
		{"company": company},
		source_app=_source_app(source_app),
	)


def inventory_snapshot(company: str, *, source_app: str | None = None) -> IntegrationCommandResult:
	return dispatch_command(
		"reporting.get_inventory_snapshot",
		{"company": company},
		source_app=_source_app(source_app),
	)


def require_ok(result: IntegrationCommandResult, *, title: str = "Integration") -> str:
	if not result.ok or not result.reference_name:
		raise IntegrationBusError(result.message or f"{title} failed")
	return result.reference_name
