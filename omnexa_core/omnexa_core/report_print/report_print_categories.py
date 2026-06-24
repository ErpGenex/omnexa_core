# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Classify Script Reports for financial / inventory / audit print templates."""

from __future__ import annotations

FINANCIAL_REPORTS = frozenset(
	{
		"Trial Balance",
		"Balance Sheet",
		"Income Statement",
		"Profit and Loss Statement",
		"General Ledger",
		"General Journal",
		"Cash Flow (Simplified)",
		"Cash Flow Simplified",
		"Cash Flow Statement Structured",
		"Cash Flow Statement Indirect",
		"Receivables Aging",
		"Payables Aging",
		"Customer Ledger",
		"Supplier Ledger",
		"Employee Ledger",
		"Financial KPI Summary",
		"Consolidated Trial Balance",
		"Consolidated Financial Statements",
		"Notes to Financial Statements",
		"Budget vs Actual",
		"Bank Balance Summary",
		"Bank Reconciliation Suggestions",
		"Cash Activity Summary",
		"Receivables and DSO",
		"Revenue Analysis",
		"Sales Register",
		"Purchase Register",
		"Inventory Valuation GL",
		"Inventory Valuation Summary",
	}
)

INVENTORY_REPORTS = frozenset(
	{
		"Stock Movement",
		"Stock Ledger",
		"Stock Voucher Register",
		"Stock Summary",
		"Stock Aging Report",
		"Item Stock Balance",
		"Low Stock",
		"Dead Stock Report",
		"Expiry Report",
		"ABC Analysis Report",
		"Warehouse Transfer Report",
		"Inventory KPI Dashboard",
		"Inventory Valuation Summary",
		"Inventory Valuation GL",
	}
)

FINANCIAL_KEYWORDS = (
	"trial_balance",
	"balance_sheet",
	"income_statement",
	"profit_and_loss",
	"cash_flow",
	"general_ledger",
	"general_journal",
	"receivable",
	"payable",
	"aging",
	"ledger",
	"financial",
	"budget",
	"bank_",
	"consolidated",
	"notes_to_financial",
)

INVENTORY_KEYWORDS = (
	"stock_",
	"inventory_",
	"warehouse_",
	"item_stock",
	"low_stock",
	"dead_stock",
	"expiry_",
	"abc_analysis",
)

AUDIT_KEYWORDS = ("audit", "compliance", "governance", "remediation", "evidence", "control")


def report_print_category(report_name: str, module: str | None = None, ref_doctype: str | None = None) -> str:
	"""Return: financial | inventory | audit | standard."""
	name = (report_name or "").strip()
	blob = f"{name} {module or ''} {ref_doctype or ''}".lower()
	slug = name.lower().replace(" ", "_").replace("(", "").replace(")", "")

	if name in FINANCIAL_REPORTS:
		return "financial"
	if name in INVENTORY_REPORTS:
		return "inventory"
	if any(k in blob for k in AUDIT_KEYWORDS):
		return "audit"
	if any(k in slug for k in FINANCIAL_KEYWORDS):
		return "financial"
	if any(k in slug for k in INVENTORY_KEYWORDS):
		return "inventory"
	if ref_doctype in ("Budget", "Journal Entry", "Bank Transaction", "Fiscal Year"):
		return "financial"
	if ref_doctype in ("Stock Entry", "Item", "Warehouse", "Batch"):
		return "inventory"
	return "standard"


def template_filename(category: str) -> str:
	return {
		"financial": "erpgenex_financial_report_print.html",
		"inventory": "erpgenex_inventory_report_print.html",
		"audit": "erpgenex_audit_report_print.html",
	}.get(category, "erpgenex_report_print.html")
