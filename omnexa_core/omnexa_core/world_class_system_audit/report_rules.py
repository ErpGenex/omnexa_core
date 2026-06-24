# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Report transparency rules aligned with omnexa_accounting report columns."""

from __future__ import annotations

FINANCIAL_REPORT_REQUIREMENTS: dict[str, list[str]] = {
	"General Ledger": [
		"posting_date",
		"account",
		"voucher",
		"debit",
		"credit",
		"balance",
		"branch",
		"reference",
	],
	"Trial Balance": [
		"account",
		"account_name",
		"opening_debit",
		"opening_credit",
		"closing_debit",
		"closing_credit",
	],
	"Profit and Loss Statement": ["account", "account_name", "amount", "section"],
	"Balance Sheet": ["account", "account_name", "balance", "section"],
	"General Journal": ["voucher", "account", "debit", "credit"],
	"Income Statement": ["account", "account_name", "amount", "section"],
	"Stock Ledger": ["posting_date", "item", "warehouse", "qty", "stock_value"],
	"Stock Balance": ["item", "item_name", "item_code", "current_stock_qty"],
}

CRITICAL_REPORT_FIELDS = ("posting_date", "date", "voucher", "debit", "credit", "account", "account_name")

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
	"opening": ("opening_debit", "opening_credit", "opening"),
	"closing": ("closing_debit", "closing_credit", "closing"),
	"debit": ("debit", "period_debit", "opening_debit", "closing_debit"),
	"credit": ("credit", "period_credit", "opening_credit", "closing_credit"),
	"qty": ("qty", "quantity", "actual_qty"),
	"value": ("value", "stock_value", "valuation_rate", "balance"),
	"amount": ("amount", "balance", "stock_value"),
	"remarks": ("remarks", "narration", "description", "reference"),
	"date": ("posting_date", "date", "transaction_date"),
}
