from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import frappe


@dataclass
class ReadinessItem:
	key: str
	label: str
	status: str  # pass | fail | no_data
	details: str = ""


PROCESS_REQUIREMENTS: list[dict[str, Any]] = [
	{
		"key": "p2p",
		"label": "Procure-to-Pay",
		"required_doctypes": ["Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry"],
		"required_reports": ["Accounts Payable", "Supplier Ledger Summary"],
	},
	{
		"key": "inventory",
		"label": "Inventory",
		"required_doctypes": ["Stock Entry", "Stock Reconciliation", "Bin", "Item"],
		"required_reports": ["Stock Ledger", "Stock Summary"],
	},
	{
		"key": "o2c",
		"label": "Order-to-Cash",
		"required_doctypes": ["Sales Order", "Delivery Note", "Sales Invoice", "Payment Entry"],
		"required_reports": ["Accounts Receivable", "Sales by Customer"],
	},
	{
		"key": "banking",
		"label": "Banking and Treasury",
		"required_doctypes": ["Payment Entry", "Bank Reconciliation Tool"],
		"required_reports": ["Bank Reconciliation Statement"],
	},
	{
		"key": "gl",
		"label": "General Ledger",
		"required_doctypes": ["Journal Entry", "GL Entry", "Account"],
		"required_reports": ["General Ledger", "Trial Balance"],
	},
	{
		"key": "payroll",
		"label": "Payroll",
		"required_doctypes": ["Salary Slip", "Payroll Entry", "Employee"],
		"required_reports": ["Salary Register"],
	},
	{
		"key": "budgeting",
		"label": "Budgeting",
		"required_doctypes": ["Budget", "Cost Center"],
		"required_reports": ["Budget Variance Report", "Budget vs Actual"],
	},
	{
		"key": "financial_statements",
		"label": "Financial Statements",
		"required_doctypes": ["GL Entry", "Account"],
		"required_reports": ["Balance Sheet", "Profit and Loss Statement", "Cash Flow Statement"],
	},
]


def _exists(doctype: str, name: str) -> bool:
	return bool(frappe.db.exists(doctype, name))


def _evaluate_process_requirement(spec: dict[str, Any]) -> ReadinessItem:
	missing_doctypes = [d for d in spec.get("required_doctypes", []) if not _exists("DocType", d)]
	missing_reports = [r for r in spec.get("required_reports", []) if not _exists("Report", r)]
	if not missing_doctypes and not missing_reports:
		return ReadinessItem(key=spec["key"], label=spec["label"], status="pass")
	parts = []
	if missing_doctypes:
		parts.append(f"missing_doctypes={','.join(missing_doctypes)}")
	if missing_reports:
		parts.append(f"missing_reports={','.join(missing_reports)}")
	return ReadinessItem(key=spec["key"], label=spec["label"], status="fail", details="; ".join(parts))


def _count_gl_entries(voucher_type: str) -> int:
	return int(
		frappe.db.sql(
			"SELECT COUNT(*) FROM `tabGL Entry` WHERE voucher_type=%s",
			(voucher_type,),
		)[0][0]
	)


def _must_pass_item(key: str, label: str, voucher_type: str, prerequisite_doctypes: list[str]) -> ReadinessItem:
	missing = [d for d in prerequisite_doctypes if not _exists("DocType", d)]
	if missing:
		return ReadinessItem(key=key, label=label, status="fail", details=f"missing_doctypes={','.join(missing)}")
	count = _count_gl_entries(voucher_type=voucher_type)
	if count <= 0:
		return ReadinessItem(key=key, label=label, status="no_data", details="no_posted_transactions_yet")
	return ReadinessItem(key=key, label=label, status="pass", details=f"gl_rows={count}")


def _run_must_pass_matrix() -> list[ReadinessItem]:
	items = [
		_must_pass_item(
			"sales_invoice_gl_ar_inventory",
			"Sales Invoice -> GL + AR + Inventory",
			"Sales Invoice",
			["Sales Invoice", "GL Entry"],
		),
		_must_pass_item(
			"purchase_invoice_gl_ap_inventory",
			"Purchase Invoice -> GL + AP + Inventory/Expense",
			"Purchase Invoice",
			["Purchase Invoice", "GL Entry"],
		),
		_must_pass_item(
			"payment_entry_gl_settlement",
			"Payment Entry -> GL + AR/AP settlement",
			"Payment Entry",
			["Payment Entry", "GL Entry"],
		),
		_must_pass_item(
			"payroll_entry_gl_liabilities",
			"Payroll Entry -> GL + Employee Liabilities",
			"Payroll Entry",
			["Payroll Entry", "GL Entry"],
		),
		_must_pass_item(
			"stock_reconciliation_gl_impact",
			"Stock Reconciliation -> Inventory + GL impact",
			"Stock Reconciliation",
			["Stock Reconciliation", "GL Entry"],
		),
	]
	if _exists("DocType", "Budget"):
		budget_count = int(frappe.db.count("Budget"))
		items.append(
			ReadinessItem(
				key="budget_control",
				label="Budget control policy path",
				status="pass" if budget_count > 0 else "no_data",
				details=f"budget_rows={budget_count}",
			)
		)
	else:
		items.append(ReadinessItem(key="budget_control", label="Budget control policy path", status="fail", details="missing_doctype=Budget"))

	fin_missing_reports = [r for r in ("Trial Balance", "Balance Sheet", "Profit and Loss Statement") if not _exists("Report", r)]
	items.append(
		ReadinessItem(
			key="financial_statements_tb_gl",
			label="Financial Statements -> TB -> GL drill-down",
			status="pass" if not fin_missing_reports else "fail",
			details="" if not fin_missing_reports else f"missing_reports={','.join(fin_missing_reports)}",
		)
	)
	return items


def _percent(passed: int, total: int) -> float:
	if total <= 0:
		return 0.0
	return round((passed / total) * 100.0, 2)


@frappe.whitelist()
def get_core_erp_readiness_snapshot() -> dict[str, Any]:
	"""
	Compute a practical readiness snapshot aligned with CORE_ERP_99_READINESS_PLAN_AR.
	This is a baseline operational checker; it does not replace full UAT sign-off.
	"""
	process_items = [_evaluate_process_requirement(spec) for spec in PROCESS_REQUIREMENTS]
	must_pass_items = _run_must_pass_matrix()

	all_items = process_items + must_pass_items
	pass_count = sum(1 for i in all_items if i.status == "pass")
	fail_count = sum(1 for i in all_items if i.status == "fail")
	no_data_count = sum(1 for i in all_items if i.status == "no_data")

	scored_items = pass_count + fail_count
	readiness_score = _percent(pass_count, scored_items)

	return {
		"summary": {
			"readiness_score": readiness_score,
			"pass_count": pass_count,
			"fail_count": fail_count,
			"no_data_count": no_data_count,
			"go_live_ready": fail_count == 0 and readiness_score >= 99.0,
		},
		"process_checks": [asdict(x) for x in process_items],
		"must_pass_matrix": [asdict(x) for x in must_pass_items],
	}

