# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Canonical Desk sidebar (Card Break + Links) aligned with:
- Docs/.../Global ERP System Architecture Standard.md (local vs global report placement)
- Docs/.../Global ERP Workflow Engine Standard.md (operation order: lead→cash, request→payment, etc.)
- Global readiness: explicit **setup** hubs (company / branch / tax / FX) per domain + **COA** in Accounting.

Applied on workspace_control_tower sync so migrate refreshes links.
"""

from __future__ import annotations

# (card_title, [(label, link_type, link_to, report_ref_doctype|None), ...])
DeskSection = tuple[str, list[tuple[str, str, str, str | None]]]

SELL_DESK: list[DeskSection] = [
	(
		"Sales setup (company, branches, tax & FX)",
		[
			("Company", "DocType", "Company", None),
			("Branch", "DocType", "Branch", None),
			("Tax Rule", "DocType", "Tax Rule", None),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate", None),
		],
	),
	(
		"CRM & pipeline (Lead → Opportunity)",
		[
			("Pipeline Lead", "DocType", "Pipeline Lead", None),
			("Pipeline Opportunity", "DocType", "Pipeline Opportunity", None),
			("CRM Activity", "DocType", "CRM Activity", None),
			("CRM Campaign", "DocType", "CRM Campaign", None),
		],
	),
	(
		"Customer management",
		[
			("Customer", "DocType", "Customer", None),
		],
	),
	(
		"Sales cycle (Quotation → Order → Delivery → Invoice)",
		[
			("Sales Quotation", "DocType", "Sales Quotation", None),
			("Sales Order", "DocType", "Sales Order", None),
			("Delivery Note", "DocType", "Delivery Note", None),
			("Sales Invoice", "DocType", "Sales Invoice", None),
		],
	),
	(
		"Returns, payments & retail",
		[
			("Credit notes & returns", "DocType", "Sales Invoice", None),
			("Payment Entry", "DocType", "Payment Entry", None),
			("Counter sales (Sales Invoice)", "DocType", "Sales Invoice", None),
		],
	),
	(
		"Logistics & fulfillment",
		[
			("Warehouse", "DocType", "Warehouse", None),
			("Stock Entry", "DocType", "Stock Entry", None),
		],
	),
	(
		"E-Invoicing & e-receipt",
		[
			("Sales invoices (e-invoice source)", "DocType", "Sales Invoice", None),
			("Payment entries (e-receipt source)", "DocType", "Payment Entry", None),
			("Authority submissions (invoice & receipt)", "DocType", "E-Document Submission", None),
			("Tax Authority Profile", "DocType", "Tax Authority Profile", None),
			("Signing Profile", "DocType", "Signing Profile", None),
		],
	),
	(
		"Data & imports",
		[
			("Data Import (CRM)", "DocType", "Data Import", None),
		],
	),
	(
		"Local sales reports (workspace only)",
		[
			("Sales Register", "Report", "Sales Register", "Sales Invoice"),
			("Sales by Customer", "Report", "Sales by Customer", "Sales Invoice"),
			("Sales by Item", "Report", "Sales by Item", "Sales Invoice"),
			("Sales by Country", "Report", "Sales by Country", "Sales Invoice"),
			("Pipeline Funnel", "Report", "Pipeline Funnel", "Pipeline Opportunity"),
		],
	),
]

BUY_DESK: list[DeskSection] = [
	(
		"Procurement setup (company, branches, tax & FX)",
		[
			("Company", "DocType", "Company", None),
			("Branch", "DocType", "Branch", None),
			("Tax Rule", "DocType", "Tax Rule", None),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate", None),
		],
	),
	(
		"Suppliers",
		[
			("Supplier", "DocType", "Supplier", None),
		],
	),
	(
		"Procurement cycle (Request → PO → Receipt → Invoice → Payment)",
		[
			("Purchase Request", "DocType", "Purchase Request", None),
			("Purchase Order", "DocType", "Purchase Order", None),
			("Purchase Receipt", "DocType", "Purchase Receipt", None),
			("Purchase Invoice", "DocType", "Purchase Invoice", None),
			("Payment Entry (supplier payments)", "DocType", "Payment Entry", None),
			("Landed Cost Voucher", "DocType", "Landed Cost Voucher", None),
		],
	),
	(
		"Governance & approvals",
		[
			("Purchase Approval Rule", "DocType", "Purchase Approval Rule", None),
		],
	),
	(
		"Local procurement reports (workspace only)",
		[
			("Purchase Register", "Report", "Purchase Register", "Purchase Invoice"),
			("Supplier Ledger", "Report", "Supplier Ledger", "Journal Entry"),
			("Open Purchase Order Lines", "Report", "Open Purchase Order Lines", "Purchase Order"),
			("Purchase Delivery Performance", "Report", "Purchase Delivery Performance", "Purchase Order"),
		],
	),
]

STOCK_DESK: list[DeskSection] = [
	(
		"Master data",
		[
			("Item", "DocType", "Item", None),
			("UOM", "DocType", "UOM", None),
		],
	),
	(
		"Warehouse & inventory setup (company, branches, locations)",
		[
			("Company", "DocType", "Company", None),
			("Branch", "DocType", "Branch", None),
			("Warehouse", "DocType", "Warehouse", None),
		],
	),
	(
		"Movements, reconciliation & batch / serial",
		[
			("Stock Entry", "DocType", "Stock Entry", None),
			("Stock Reconciliation", "DocType", "Stock Reconciliation", None),
		],
	),
	(
		"Local inventory reports (workspace only)",
		[
			("Item Stock Balance", "Report", "Item Stock Balance", "Item"),
			("Stock Movement", "Report", "Stock Movement", "Stock Entry"),
			("Stock Voucher Register", "Report", "Stock Voucher Register", "Stock Entry"),
			("Inventory Valuation Summary", "Report", "Inventory Valuation Summary", "Item"),
			("Inventory Valuation (GL)", "Report", "Inventory Valuation (GL)", "Item"),
			("Low Stock", "Report", "Low Stock", "Item"),
		],
	),
]

ACCOUNTING_DESK: list[DeskSection] = [
	(
		"Chart of accounts, company & dimensions",
		[
			("Company", "DocType", "Company", None),
			("Branch", "DocType", "Branch", None),
			("Chart of Accounts (GL Account)", "DocType", "GL Account", None),
			("Cost Center", "DocType", "Cost Center", None),
			("Fiscal Year", "DocType", "Fiscal Year", None),
			("Tax Rule", "DocType", "Tax Rule", None),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate", None),
			("Bank Account", "DocType", "Bank Account", None),
			("Mode of Payment", "DocType", "Mode of Payment", None),
		],
	),
	(
		"Item master (stock ↔ GL account mapping)",
		[
			("Item", "DocType", "Item", None),
		],
	),
	(
		"Core financial operations",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
			("Payment Entry", "DocType", "Payment Entry", None),
			("Bank Reconciliation", "DocType", "Bank Reconciliation", None),
			("Budget", "DocType", "Budget", None),
		],
	),
	(
		"Global registers & ledgers",
		[
			("General Journal", "Report", "General Journal", "Journal Entry"),
			("General Ledger", "Report", "General Ledger", "Journal Entry"),
			("Customer Ledger", "Report", "Customer Ledger", "Journal Entry"),
			("Supplier Ledger", "Report", "Supplier Ledger", "Journal Entry"),
			("Employee Ledger", "Report", "Employee Ledger", "Journal Entry"),
		],
	),
	(
		"Trial balance & primary statements",
		[
			("Trial Balance", "Report", "Trial Balance", "GL Account"),
			("Income Statement", "Report", "Income Statement", "GL Account"),
			("Balance Sheet", "Report", "Balance Sheet", "GL Account"),
			(
				"Financial Consolidation (Consolidated Trial Balance)",
				"Report",
				"Consolidated Trial Balance",
				"GL Account",
			),
		],
	),
	(
		"Cash flow & liquidity (global)",
		[
			("Cash Activity Summary", "Report", "Cash Activity Summary", "Payment Entry"),
			("Cash Flow (Simplified)", "Report", "Cash Flow (Simplified)", "Payment Entry"),
			(
				"Cash Flow Statement (Structured)",
				"Report",
				"Cash Flow Statement (Structured)",
				"Journal Entry",
			),
			(
				"Cash Flow Statement (Indirect)",
				"Report",
				"Cash Flow Statement (Indirect)",
				"Journal Entry",
			),
		],
	),
	(
		"AR, AP & working capital (global)",
		[
			("Receivables Aging", "Report", "Receivables Aging", "Sales Invoice"),
			("Payables Aging", "Report", "Payables Aging", "Purchase Invoice"),
			("Receivables and DSO", "Report", "Receivables and DSO", "Sales Invoice"),
		],
	),
	(
		"Budget & inventory (financial view)",
		[
			("Budget vs Actual", "Report", "Budget vs Actual", "Budget"),
			("Inventory Valuation Summary", "Report", "Inventory Valuation Summary", "Item"),
			("Inventory Valuation (GL)", "Report", "Inventory Valuation (GL)", "Item"),
		],
	),
	(
		"Executive KPIs (global)",
		[
			("Financial KPI Summary", "Report", "Financial KPI Summary", "GL Account"),
		],
	),
]

GOVERNANCE_DESK: list[DeskSection] = [
	(
		"Organization structure",
		[
			("Company", "DocType", "Company", None),
		],
	),
	(
		"Users, roles & access",
		[
			("User", "DocType", "User", None),
			("Role", "DocType", "Role", None),
			("User Permission", "DocType", "User Permission", None),
		],
	),
	(
		"Approval workflows (state → action → transition)",
		[
			("Workflow", "DocType", "Workflow", None),
		],
	),
	(
		"Tax & e-invoice configuration (global policy)",
		[
			("Tax Rule", "DocType", "Tax Rule", None),
			("Tax Authority Profile", "DocType", "Tax Authority Profile", None),
			("Signing Profile", "DocType", "Signing Profile", None),
		],
	),
	(
		"System configuration",
		[
			("System Settings", "DocType", "System Settings", None),
			("Workspace", "DocType", "Workspace", None),
			("Error Log", "DocType", "Error Log", None),
		],
	),
	(
		"Audit trail & activity",
		[
			("Activity Log", "DocType", "Activity Log", None),
			("Version", "DocType", "Version", None),
		],
	),
]

_BY_WORKSPACE: dict[str, list[DeskSection]] = {
	"Sell": SELL_DESK,
	"Buy": BUY_DESK,
	"Stock": STOCK_DESK,
	"Accounting": ACCOUNTING_DESK,
	"Governance": GOVERNANCE_DESK,
}


def get_desk_sections_for_workspace(workspace_name: str) -> list[DeskSection] | None:
	return _BY_WORKSPACE.get(workspace_name)
