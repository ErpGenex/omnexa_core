# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Desk filter definitions for top financial Script Reports (W1-5 / FIELD-07)."""

from __future__ import annotations

# Reusable filter fragments (Frappe Report JSON shape)
_COMPANY = {
	"fieldname": "company",
	"fieldtype": "Link",
	"label": "Company",
	"options": "Company",
	"reqd": 1,
	"width": "180px",
}
_FROM = {"fieldname": "from_date", "fieldtype": "Date", "label": "From Date", "reqd": 1, "width": "120px"}
_TO = {"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "reqd": 1, "width": "120px"}
_TO_OPT = {"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "width": "120px"}
_AS_OF = {"fieldname": "as_of_date", "fieldtype": "Date", "label": "As Of Date", "width": "120px"}
_BRANCH = {
	"fieldname": "branch",
	"fieldtype": "Link",
	"label": "Branch",
	"options": "Branch",
	"width": "180px",
}
_COMPANIES = {
	"fieldname": "companies",
	"fieldtype": "Data",
	"label": "Companies (comma-separated)",
	"reqd": 1,
	"width": "320px",
}
_ACCOUNT = {
	"fieldname": "account",
	"fieldtype": "Link",
	"label": "Account",
	"options": "GL Account",
	"width": "180px",
}
_PARTY_CUSTOMER = {
	"fieldname": "party",
	"fieldtype": "Link",
	"label": "Customer",
	"options": "Customer",
	"width": "180px",
}
_PARTY_SUPPLIER = {
	"fieldname": "party",
	"fieldtype": "Link",
	"label": "Supplier",
	"options": "Supplier",
	"width": "180px",
}
_BUDGET = {
	"fieldname": "budget",
	"fieldtype": "Link",
	"label": "Budget",
	"options": "Budget",
	"reqd": 1,
	"width": "200px",
}
_COST_CENTER = {
	"fieldname": "cost_center",
	"fieldtype": "Link",
	"label": "Cost Center",
	"options": "Cost Center",
	"width": "180px",
}
_BANK = {
	"fieldname": "bank_account",
	"fieldtype": "Link",
	"label": "Bank Account",
	"options": "Bank Account",
	"reqd": 1,
	"width": "200px",
}
_PERIOD_DAYS = {
	"fieldname": "period_days",
	"fieldtype": "Int",
	"label": "Period (days)",
	"default": "90",
	"width": "100px",
}
_STMT_DATE = {"fieldname": "statement_date", "fieldtype": "Date", "label": "Statement Date", "width": "120px"}
_TOLERANCE = {
	"fieldname": "tolerance_days",
	"fieldtype": "Int",
	"label": "Tolerance (days)",
	"default": "7",
	"width": "100px",
}
_LIMIT = {"fieldname": "limit", "fieldtype": "Int", "label": "Limit", "default": "200", "width": "80px"}

# Report name → filters list (omnexa_accounting W1 top 20)
ACCOUNTING_REPORT_FILTERS: dict[str, list[dict]] = {
	"Trial Balance": [_COMPANY, _FROM, _TO, _BRANCH],
	"Balance Sheet": [_COMPANY, _TO_OPT, _BRANCH],
	"Income Statement": [_COMPANY, _FROM, _TO, _BRANCH],
	"General Ledger": [_COMPANY, _FROM, _TO, _ACCOUNT, _BRANCH],
	"General Journal": [_COMPANY, _FROM, _TO, _BRANCH],
	"Cash Flow Simplified": [_COMPANY, _FROM, _TO, _BRANCH],
	"Cash Flow Statement Structured": [_COMPANY, _FROM, _TO, _BRANCH],
	"Cash Flow Statement Indirect": [_COMPANY, _FROM, _TO, _BRANCH],
	"Cash Activity Summary": [_COMPANY, _FROM, _TO, _BRANCH],
	"Receivables Aging": [_COMPANY, _AS_OF],
	"Payables Aging": [_COMPANY, _AS_OF],
	"Receivables and DSO": [_COMPANY, _AS_OF, _PERIOD_DAYS],
	"Consolidated Trial Balance": [_COMPANIES, _FROM, _TO, _BRANCH],
	"Customer Ledger": [_COMPANY, _FROM, _TO, _PARTY_CUSTOMER, _BRANCH],
	"Supplier Ledger": [_COMPANY, _FROM, _TO, _PARTY_SUPPLIER, _BRANCH],
	"Financial KPI Summary": [_COMPANY, _FROM, _TO, _BRANCH],
	"Budget vs Actual": [_BUDGET, _BRANCH, _COST_CENTER],
	"Inventory Valuation GL": [_COMPANY, {**_AS_OF, "reqd": 1}],
	"Bank Reconciliation Suggestions": [_COMPANY, _BANK, _STMT_DATE, _TOLERANCE, _LIMIT],
	"Consolidated Financial Statements": [
		_COMPANIES,
		_FROM,
		_TO,
		{"fieldname": "apply_eliminations", "fieldtype": "Check", "label": "Apply Intercompany Eliminations", "default": "1", "width": "80px"},
		{"fieldname": "show_consolidated_total", "fieldtype": "Check", "label": "Show Consolidated Totals", "default": "1", "width": "80px"},
	],
}
