# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Enterprise control-tower workspace sync: KPI number cards (with % vs prior period),
dashboard charts (line, bar, donut, pie, percentage strip),
and desk layout for registered finance apps plus **generic** public workspaces
(DocTypes inferred from sidebar links, same chart/card binding rules as Frappe Desk).
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.workspace_desk_layouts import get_desk_sections_for_workspace

_COLORS = ("Cyan", "Blue", "Purple", "Orange", "Green", "Red", "Teal", "Pink")


def _app_installed(app_name: str) -> bool:
	try:
		return bool(app_name) and app_name in frappe.get_installed_apps()
	except Exception:
		return False


# Registry key = app_name in hooks (e.g. omnexa_finance_engine)
_APP_SPECS: dict[str, dict[str, Any]] = {
	"omnexa_finance_engine": {
		"workspace": "Finance Engine",
		"module": "Omnexa Finance Engine",
		"icon": "bank",
		"headline": "Finance Engine",
		"tagline": "360° control tower — products, contracts, schedules, liquidity events, governance.",
		"trend_doctypes": ["Finance Contract Account", "Finance Calc Run"],
		"status_doctypes": ["Finance Product"],
		"kpis": [
			("Active Products", "Finance Product", [["status", "=", "ACTIVE"]]),
			("Contract Accounts", "Finance Contract Account", []),
			("Calc Runs", "Finance Calc Run", []),
			("Scenario Runs", "Finance Scenario Run", []),
			("Pending Outbox", "Finance Event Outbox", [["status", "=", "PENDING"]]),
			("Accounting Templates", "Finance Accounting Event Template", [["status", "=", "ACTIVE"]]),
		],
		"shortcuts": [
			("Finance Products", "DocType", "Finance Product"),
			("Contract Accounts", "DocType", "Finance Contract Account"),
			("Calculation Runs", "DocType", "Finance Calc Run"),
			("Scenario Runs", "DocType", "Finance Scenario Run"),
			("Event Outbox", "DocType", "Finance Event Outbox"),
			("Accounting Templates", "DocType", "Finance Accounting Event Template"),
			("General Ledger", "Report", "General Ledger"),
			("Trial Balance", "Report", "Trial Balance"),
			("Governance Overview", "Report", "Governance Overview"),
			("Policy Versions", "DocType", "Finance Policy Version"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Finance Contract Account", "group_by": "status", "label": "Book by status"},
			{"type": "Pie", "doctype": "Finance Contract Account", "group_by": "ifrs9_stage", "label": "IFRS9 mix"},
			{"type": "Percentage", "doctype": "Finance Calc Run", "group_by": "run_type", "label": "Calc run mix"},
		],
		"extra_sections": [
			(
				"Reports & Analytics",
				[
					("Governance Overview", "Report", "Governance Overview", "activity"),
					("General Ledger", "Report", "General Ledger", "book"),
					("Trial Balance", "Report", "Trial Balance", "list"),
				],
			),
		],
	},
	"omnexa_credit_engine": {
		"workspace": "Credit Engine",
		"module": "Omnexa Credit Engine",
		"icon": "shield",
		"headline": "Credit Engine",
		"tagline": "Origination, scorecards, strategies, bureau/KYC connectors, explainable approvals.",
		"trend_doctypes": ["Credit Decision Case", "Credit Connector Request"],
		"status_doctypes": ["Credit Rule Profile", "Credit Scorecard"],
		"kpis": [
			("Decision Cases", "Credit Decision Case", []),
			("Active Rule Profiles", "Credit Rule Profile", [["status", "=", "ACTIVE"]]),
			("Active Scorecards", "Credit Scorecard", [["status", "=", "ACTIVE"]]),
			("Active Strategies", "Credit Strategy Route", [["status", "=", "ACTIVE"]]),
			("Pending Overrides", "Credit Decision Override", [["workflow_status", "=", "PENDING"]]),
			("Pending Connectors", "Credit Connector Request", [["status", "=", "PENDING"]]),
		],
		"shortcuts": [
			("Rule Profiles", "DocType", "Credit Rule Profile"),
			("Decision Cases", "DocType", "Credit Decision Case"),
			("Scorecards", "DocType", "Credit Scorecard"),
			("Strategy Routes", "DocType", "Credit Strategy Route"),
			("Decision Overrides", "DocType", "Credit Decision Override"),
			("Connector Requests", "DocType", "Credit Connector Request"),
			("Decision SLA Monitor", "Report", "Decision SLA Monitor"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Credit Decision Case", "group_by": "decision_status", "label": "Decision funnel"},
			{"type": "Pie", "doctype": "Credit Decision Case", "group_by": "risk_grade", "label": "Risk grades"},
			{"type": "Percentage", "doctype": "Credit Connector Request", "group_by": "status", "label": "Connector outcomes"},
		],
		"extra_sections": [
			(
				"Analytics Reports",
				[
					("Decision SLA Monitor", "Report", "Decision SLA Monitor", "activity"),
					("Decision Outcome Distribution", "Report", "Decision Outcome Distribution", "pie-chart"),
					("Reason Code Distribution", "Report", "Reason Code Distribution", "bookmark"),
					("Country Product Heatmap", "Report", "Country Product Segment Heatmap", "grid"),
				],
			),
		],
	},
	"omnexa_credit_risk": {
		"workspace": "Credit Risk",
		"module": "Omnexa Credit Risk",
		"icon": "trending-up",
		"headline": "Credit Risk",
		"tagline": "PD/LGD/EAD, IFRS9 stages, stress, calibration, ECL bridges, regulatory packs.",
		"trend_doctypes": ["Credit Risk Account Snapshot", "Credit Risk Portfolio Stress Run"],
		"status_doctypes": ["Credit Risk Calibration Run"],
		"kpis": [
			("Account Snapshots", "Credit Risk Account Snapshot", []),
			("Stress Runs", "Credit Risk Portfolio Stress Run", []),
			("Model Validations", "Credit Risk Model Validation Run", []),
			("Backtest Datasets", "Credit Risk Backtest Dataset", []),
			("Calibration Runs", "Credit Risk Calibration Run", []),
			("ECL Movements", "Credit Risk ECL Movement", []),
		],
		"shortcuts": [
			("Account Snapshots", "DocType", "Credit Risk Account Snapshot"),
			("Stress Runs", "DocType", "Credit Risk Portfolio Stress Run"),
			("Backtest Datasets", "DocType", "Credit Risk Backtest Dataset"),
			("Calibration Runs", "DocType", "Credit Risk Calibration Run"),
			("ECL Movements", "DocType", "Credit Risk ECL Movement"),
			("Model Validations", "DocType", "Credit Risk Model Validation Run"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Credit Risk Account Snapshot", "group_by": "ifrs9_stage", "label": "ECL stage bars"},
			{"type": "Pie", "doctype": "Credit Risk Account Snapshot", "group_by": "segment", "label": "Segments"},
			{"type": "Percentage", "doctype": "Credit Risk Calibration Run", "group_by": "calibration_method", "label": "Calibration methods"},
		],
		"extra_sections": [
			(
				"IFRS9 & Stress Analytics",
				[
					("Governance Overview", "Report", "Governance Overview", "shield"),
				],
			),
		],
	},
	"omnexa_operational_risk": {
		"workspace": "Operational Risk",
		"module": "Omnexa Operational Risk",
		"icon": "alert-octagon",
		"headline": "Operational Risk",
		"tagline": "Incidents, controls, loss events, compliance mapping, SLA analytics.",
		"trend_doctypes": ["Operational Risk Incident", "Operational Loss Event"],
		"status_doctypes": ["Operational Risk Incident"],
		"kpis": [
			("Open Incidents", "Operational Risk Incident", []),
			("Loss Events YTD", "Operational Loss Event", []),
			("Active Controls", "Operational Risk Control", []),
			("Open Audit Issues", "Operational Audit Issue", []),
			("Active RCA Playbooks", "Operational RCA Playbook", [["status", "=", "ACTIVE"]]),
			("Escalation Matrices", "Operational Escalation Matrix", [["status", "=", "ACTIVE"]]),
			("Ingestion Pending", "Operational External Ingestion Event", [["status", "=", "PENDING"]]),
		],
		"shortcuts": [
			("Incidents", "DocType", "Operational Risk Incident"),
			("Loss Events", "DocType", "Operational Loss Event"),
			("Controls", "DocType", "Operational Risk Control"),
			("RCA Playbooks", "DocType", "Operational RCA Playbook"),
			("Escalation Matrices", "DocType", "Operational Escalation Matrix"),
			("External Ingestion", "DocType", "Operational External Ingestion Event"),
			("Incident SLA Monitor", "Report", "Incident SLA Monitor"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Operational Risk Incident", "group_by": "event_type", "label": "Events by type"},
			{"type": "Pie", "doctype": "Operational Risk Incident", "group_by": "risk_rating", "label": "Risk rating"},
			{"type": "Percentage", "doctype": "Operational Compliance Mapping", "group_by": "compliance_status", "label": "Compliance mix"},
		],
		"extra_sections": [
			(
				"Risk Analytics",
				[
					("Loss Event Trend", "Report", "Loss Event Trend", "trending-up"),
					("Control Effectiveness", "Report", "Control Effectiveness Overview", "shield"),
					("Compliance Gap Register", "Report", "Compliance Gap Register", "alert-circle"),
				],
			),
		],
	},
	"omnexa_alm": {
		"workspace": "ALM",
		"module": "Omnexa ALM",
		"icon": "activity",
		"headline": "Asset & Liability Management",
		"tagline": "Gap, LCR/NSFR, IRRBB outliers, FTP margin, behavioral assumptions, contingency playbooks.",
		"trend_doctypes": ["ALM Daily Run", "ALM Position Snapshot"],
		"status_doctypes": ["ALM Stress Scenario"],
		"kpis": [
			("Daily ALM Runs", "ALM Daily Run", []),
			("Position Snapshots", "ALM Position Snapshot", []),
			("Stress Scenarios", "ALM Stress Scenario", []),
			("FTP Curves", "ALM FTP Curve", [["status", "=", "ACTIVE"]]),
			("IRRBB Assessments Pending", "ALM IRRBB Outlier Assessment", [["workflow_status", "=", "PENDING"]]),
			("Active Playbooks", "ALM Contingency Playbook", [["status", "=", "ACTIVE"]]),
		],
		"shortcuts": [
			("Daily Runs", "DocType", "ALM Daily Run"),
			("Position Snapshots", "DocType", "ALM Position Snapshot"),
			("Stress Scenarios", "DocType", "ALM Stress Scenario"),
			("FTP Curves", "DocType", "ALM FTP Curve"),
			("IRRBB Assessments", "DocType", "ALM IRRBB Outlier Assessment"),
			("Contingency Playbooks", "DocType", "ALM Contingency Playbook"),
			("Gap Report", "Report", "ALM Gap Report"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "ALM Position Snapshot", "group_by": "book", "label": "ALM book bars"},
			{"type": "Pie", "doctype": "ALM Stress Scenario", "group_by": "status", "label": "Scenarios"},
			{"type": "Percentage", "doctype": "ALM Daily Run", "group_by": "run_status", "label": "Run outcomes"},
		],
		"extra_sections": [
			(
				"ALM Analytics",
				[
					("Liquidity Compliance", "Report", "ALM Liquidity Compliance Monitor", "droplet"),
					("NII / EVE Sensitivity", "Report", "ALM NII EVE Sensitivity", "bar-chart-2"),
					("Stress Outlier", "Report", "ALM Stress Outlier Report", "alert-triangle"),
				],
			),
		],
	},
	"omnexa_consumer_finance": {
		"workspace": "Consumer Finance",
		"module": "Omnexa Consumer Finance",
		"icon": "shopping-cart",
		"headline": "Consumer Finance",
		"tagline": "Lifecycle, schedules, collections PAR/NPL, restructuring, omnichannel servicing.",
		"trend_doctypes": ["Consumer Finance Case", "Consumer Repayment Schedule"],
		"status_doctypes": ["Consumer Finance Case"],
		"kpis": [
			("Finance Cases", "Consumer Finance Case", []),
			("Repayment Schedules", "Consumer Repayment Schedule", []),
			("Collections Actions", "Consumer Collections Action", []),
		],
		"shortcuts": [
			("Finance Cases", "DocType", "Consumer Finance Case"),
			("Repayment Schedules", "DocType", "Consumer Repayment Schedule"),
			("PAR Monitor", "Report", "Consumer PAR Monitor"),
			("NPL Summary", "Report", "Consumer NPL Summary"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Consumer Finance Case", "group_by": "collection_stage", "label": "DPD buckets"},
			{"type": "Pie", "doctype": "Consumer Finance Case", "group_by": "ifrs9_stage", "label": "IFRS9"},
			{"type": "Percentage", "doctype": "Consumer Finance Case", "group_by": "application_channel", "label": "Channels"},
		],
		"extra_sections": [
			(
				"Portfolio Analytics",
				[
					("Roll Rate Matrix", "Report", "Consumer Roll Rate Matrix", "layers"),
					("Collections Performance", "Report", "Consumer Collections Performance", "target"),
				],
			),
		],
	},
	"omnexa_vehicle_finance": {
		"workspace": "Vehicle Finance",
		"module": "Omnexa Vehicle Finance",
		"icon": "truck",
		"headline": "Vehicle Finance",
		"tagline": "Collateral, insurance, LTV, recovery pipeline, legal workflows.",
		"trend_doctypes": ["Vehicle Finance Case", "Vehicle Finance Asset Registry"],
		"status_doctypes": ["Vehicle Finance Case"],
		"kpis": [
			("Vehicle Cases", "Vehicle Finance Case", []),
			("Asset Registry Rows", "Vehicle Finance Asset Registry", []),
		],
		"shortcuts": [
			("Vehicle Cases", "DocType", "Vehicle Finance Case"),
			("Asset Registry", "DocType", "Vehicle Finance Asset Registry"),
			("LTV Monitor", "Report", "Vehicle LTV Monitor"),
			("Portfolio Mix", "Report", "Vehicle Portfolio Mix"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Vehicle Finance Case", "group_by": "lifecycle_stage", "label": "Lifecycle"},
			{"type": "Pie", "doctype": "Vehicle Finance Case", "group_by": "recovery_stage", "label": "Recovery"},
			{"type": "Percentage", "doctype": "Vehicle Finance Case", "group_by": "vehicle_type", "label": "Vehicle mix"},
		],
		"extra_sections": [
			(
				"Risk & Recovery",
				[
					("Insurance Compliance", "Report", "Vehicle Insurance Compliance", "shield"),
					("Recovery Pipeline", "Report", "Vehicle Recovery Pipeline", "git-branch"),
				],
			),
		],
	},
	"omnexa_mortgage_finance": {
		"workspace": "Mortgage Finance",
		"module": "Omnexa Mortgage Finance",
		"icon": "home",
		"headline": "Mortgage Finance",
		"tagline": "Property valuations, covenants, escrow, conduct & disclosure readiness.",
		"trend_doctypes": ["Mortgage Finance Case", "Mortgage Finance Valuation"],
		"status_doctypes": ["Mortgage Finance Case"],
		"kpis": [
			("Mortgage Cases", "Mortgage Finance Case", []),
			("Valuations", "Mortgage Finance Valuation", []),
		],
		"shortcuts": [
			("Mortgage Cases", "DocType", "Mortgage Finance Case"),
			("Valuations", "DocType", "Mortgage Finance Valuation"),
			("LTV / DSTI Monitor", "Report", "Mortgage LTV DSTI Monitor"),
			("Legal Pipeline", "Report", "Mortgage Legal Pipeline"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Mortgage Finance Case", "group_by": "lifecycle_stage", "label": "Lifecycle"},
			{"type": "Pie", "doctype": "Mortgage Finance Case", "group_by": "legal_stage", "label": "Legal stage"},
			{"type": "Percentage", "doctype": "Mortgage Finance Case", "group_by": "ifrs9_stage", "label": "IFRS9 mix"},
		],
		"extra_sections": [
			(
				"Compliance Analytics",
				[
					("Disclosure Readiness", "Report", "Mortgage Disclosure Readiness", "file-text"),
					("Repricing Risk", "Report", "Mortgage Repricing Risk", "trending-up"),
				],
			),
		],
	},
	"omnexa_factoring": {
		"workspace": "Factoring",
		"module": "Omnexa Factoring",
		"icon": "percent",
		"headline": "Factoring",
		"tagline": "Invoice lifecycle, debtor exposure, collections, settlement reconciliation.",
		"trend_doctypes": ["Factoring Case", "Factoring Invoice"],
		"status_doctypes": ["Factoring Invoice"],
		"kpis": [
			("Factoring Cases", "Factoring Case", []),
			("Factoring Invoices", "Factoring Invoice", []),
		],
		"shortcuts": [
			("Factoring Cases", "DocType", "Factoring Case"),
			("Invoices", "DocType", "Factoring Invoice"),
			("Invoice Lifecycle", "Report", "Factoring Invoice Lifecycle"),
			("Debtor Exposure", "Report", "Factoring Debtor Exposure Dashboard"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Factoring Invoice", "group_by": "invoice_status", "label": "Invoice status"},
			{"type": "Pie", "doctype": "Factoring Case", "group_by": "lifecycle_stage", "label": "Case lifecycle"},
			{"type": "Percentage", "doctype": "Factoring Case", "group_by": "recourse_type", "label": "Recourse mix"},
		],
		"extra_sections": [
			(
				"Collections & Settlement",
				[
					("Collections Tracker", "Report", "Factoring Collections Tracker", "dollar-sign"),
					("Settlement Reconciliation", "Report", "Factoring Settlement Reconciliation", "book"),
				],
			),
		],
	},
	"omnexa_sme_retail_finance": {
		"workspace": "SME Retail Finance",
		"module": "Omnexa SME Retail Finance",
		"icon": "briefcase",
		"headline": "SME Retail Finance",
		"tagline": "SME cases, clusters, watchlist, credit quality & default analytics.",
		"trend_doctypes": ["SME Retail Finance Case", "SME Portfolio Cluster"],
		"status_doctypes": ["SME Retail Finance Case"],
		"kpis": [
			("SME Cases", "SME Retail Finance Case", []),
			("Portfolio Clusters", "SME Portfolio Cluster", []),
			("Watchlist Events", "SME Portfolio Watchlist Event", []),
		],
		"shortcuts": [
			("SME Cases", "DocType", "SME Retail Finance Case"),
			("Portfolio Clusters", "DocType", "SME Portfolio Cluster"),
			("Credit Quality Monitor", "Report", "SME Credit Quality Monitor"),
			("Sector Heatmap", "Report", "SME Sector Risk Heatmap"),
			("Governance Overview", "Report", "Governance Overview"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "SME Retail Finance Case", "group_by": "lifecycle_stage", "label": "Lifecycle"},
			{"type": "Pie", "doctype": "SME Retail Finance Case", "group_by": "sector_risk_band", "label": "Sector risk"},
			{"type": "Percentage", "doctype": "SME Retail Finance Case", "group_by": "portfolio_cluster", "label": "Clusters"},
		],
		"extra_sections": [
			(
				"Advanced Analytics",
				[
					("Cluster Dashboard", "Report", "SME Portfolio Cluster Dashboard", "grid"),
					("Default Prediction", "Report", "SME Default Prediction Tracker", "activity"),
				],
			),
		],
	},
	"omnexa_leasing_finance": {
		"workspace": "Leasing Finance",
		"module": "Omnexa Leasing Finance",
		"icon": "layers",
		"headline": "Leasing Finance",
		"tagline": "IFRS16 contracts, assets, schedules, payments, risk & portfolio analytics.",
		"trend_doctypes": ["Leasing Finance Contract", "Leasing Finance Payment"],
		"status_doctypes": ["Leasing Finance Contract"],
		"kpis": [
			("Lease Contracts", "Leasing Finance Contract", []),
			("Lease Assets", "Leasing Finance Asset", []),
			("Open Schedules", "Leasing Finance Schedule", []),
		],
		"shortcuts": [
			("Lease Contracts", "DocType", "Leasing Finance Contract"),
			("Lease Assets", "DocType", "Leasing Finance Asset"),
			("Lease Schedules", "DocType", "Leasing Finance Schedule"),
			("Lease Payments", "DocType", "Leasing Finance Payment"),
			("Leasing Portfolio", "Report", "Leasing Portfolio"),
			("Leasing Delinquency", "Report", "Leasing Delinquency"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Leasing Finance Contract", "group_by": "lifecycle_stage", "label": "Lease lifecycle"},
			{"type": "Pie", "doctype": "Leasing Finance Contract", "group_by": "lease_type", "label": "Lease types"},
			{"type": "Percentage", "doctype": "Leasing Finance Contract", "group_by": "ifrs9_stage", "label": "IFRS9 mix"},
		],
		"extra_sections": [
			(
				"Leasing Analytics & IFRS16",
				[
					("Leasing Portfolio", "Report", "Leasing Portfolio", "pie-chart"),
					("Lease Liability Report", "Report", "Lease Liability Report", "book"),
					("Residual Exposure", "Report", "Residual Exposure", "alert-circle"),
					("Leasing Revenue Forecast", "Report", "Leasing Revenue Forecast", "trending-up"),
					("Leasing Delinquency", "Report", "Leasing Delinquency", "activity"),
				],
			),
		],
	},
	"omnexa_accounting": {
		"workspace": "Accounting",
		"module": "Omnexa Accounting",
		"icon": "accounting",
		"headline": "Accounting",
		"tagline": "Global financial truth — GL, banking, journals, statutory statements, AR/AP, cash flow & consolidation.",
		"parent_page": "",
		"is_hidden": 0,
		"trend_doctypes": ["Journal Entry", "Payment Entry", "Bank Reconciliation"],
		"status_doctypes": ["Journal Entry", "Bank Reconciliation"],
		"kpis": [
			("Companies", "Company", []),
			("Branches", "Branch", []),
			("GL Accounts", "GL Account", []),
			("Journal Entries", "Journal Entry", []),
			("Payment Entries", "Payment Entry", []),
			("Bank Reconciliations", "Bank Reconciliation", []),
			("Budgets", "Budget", []),
			("Fiscal Years", "Fiscal Year", []),
			("Tax Rules", "Tax Rule", []),
		],
		"shortcuts": [
			("Company", "DocType", "Company"),
			("Branch", "DocType", "Branch"),
			("GL Account", "DocType", "GL Account"),
			("Item (stock↔GL)", "DocType", "Item"),
			("Budget", "DocType", "Budget"),
			("Journal Entry", "DocType", "Journal Entry"),
			("Payment Entry", "DocType", "Payment Entry"),
			("Bank Reconciliation", "DocType", "Bank Reconciliation"),
			("General Ledger", "Report", "General Ledger"),
			("Trial Balance", "Report", "Trial Balance"),
			("Receivables Aging", "Report", "Receivables Aging"),
			("Payables Aging", "Report", "Payables Aging"),
			("Consolidated Trial Balance", "Report", "Consolidated Trial Balance"),
			("Sell — operational desk", "URL", "/app/sell"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Journal Entry", "group_by": "docstatus", "label": "JE status"},
			{"type": "Pie", "doctype": "Payment Entry", "group_by": "docstatus", "label": "PE status"},
			{"type": "Percentage", "doctype": "Bank Reconciliation", "group_by": "status", "label": "Bank rec status"},
		],
		"extra_sections": [],
	},
	"omnexa_hr": {
		"workspace": "HR",
		"module": "Omnexa Hr",
		"icon": "users",
		"headline": "Human Resources",
		"tagline": "Headcount, employees, attendance, leave, payroll, hiring & training — single HR desk.",
		"parent_page": "",
		"is_hidden": 0,
		"trend_doctypes": ["HR Attendance", "HR Recruitment Request", "HR Leave Application"],
		"status_doctypes": ["HR Interview", "HR Payroll Entry"],
		"kpis": [
			("Employees", "Employee", []),
			("Attendance Rows", "HR Attendance", []),
			("Leave Applications", "HR Leave Application", []),
			("Recruitment Requests", "HR Recruitment Request", []),
			("Interviews", "HR Interview", []),
			("Payroll Batches", "HR Payroll Entry", []),
			("Training Records", "HR Training Record", []),
		],
		"shortcuts": [
			("Employee", "DocType", "Employee"),
			("HR Attendance", "DocType", "HR Attendance"),
			("HR Leave Type", "DocType", "HR Leave Type"),
			("HR Leave Application", "DocType", "HR Leave Application"),
			("HR Payroll Entry", "DocType", "HR Payroll Entry"),
			("Recruitment", "DocType", "HR Recruitment Request"),
			("Interviews", "DocType", "HR Interview"),
			("Training", "DocType", "HR Training Record"),
			("Leave Policy", "DocType", "Leave Policy"),
			("Headcount", "Report", "HR Headcount"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "HR Leave Application", "group_by": "status", "label": "Leave workflow"},
			{"type": "Pie", "doctype": "HR Recruitment Request", "group_by": "status", "label": "Recruitment status"},
			{"type": "Percentage", "doctype": "HR Interview", "group_by": "status", "label": "Interview pipeline"},
			{"type": "Bar", "doctype": "HR Payroll Entry", "group_by": "status", "label": "Payroll batches"},
			{"type": "Pie", "doctype": "HR Attendance", "group_by": "status", "label": "Attendance status"},
		],
		"extra_sections": [],
	},
	"omnexa_core": {
		"workspace": "Sell",
		"module": "Omnexa Core",
		"icon": "sell",
		"headline": "Sell",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Lead-to-cash workspace — pipeline, quotes, orders, delivery, invoicing, returns; local sales analytics only.",
		"trend_doctypes": ["Sales Quotation", "Sales Order", "Delivery Note", "Sales Invoice"],
		"status_doctypes": ["Pipeline Opportunity", "CRM Activity"],
		"kpis": [
			("Companies", "Company", []),
			("Branches", "Branch", []),
			("Customers", "Customer", []),
			("Sales quotations", "Sales Quotation", []),
			("Sales orders", "Sales Order", []),
			("Delivery notes", "Delivery Note", []),
			("Sales invoices", "Sales Invoice", []),
			("Credit notes (returns)", "Sales Invoice", [["is_return", "=", 1]]),
			("Payment entries", "Payment Entry", []),
			("Pipeline opportunities", "Pipeline Opportunity", []),
		],
		"shortcuts": [
			("Company", "DocType", "Company"),
			("Branch", "DocType", "Branch"),
			("Tax Rule", "DocType", "Tax Rule"),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate"),
			("Customer", "DocType", "Customer"),
			("Sales Quotation", "DocType", "Sales Quotation"),
			("Sales Order", "DocType", "Sales Order"),
			("Delivery Note", "DocType", "Delivery Note"),
			("Sales Invoice", "DocType", "Sales Invoice"),
			("Payment Entry", "DocType", "Payment Entry"),
			("Sales Register", "Report", "Sales Register"),
			("Sales by Customer", "Report", "Sales by Customer"),
			("Pipeline Funnel", "Report", "Pipeline Funnel"),
			("Accounting — global financials", "URL", "/app/accounting"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Sales Quotation", "group_by": "order_status", "label": "Quotation status"},
			{"type": "Pie", "doctype": "Sales Order", "group_by": "docstatus", "label": "Order state"},
			{"type": "Percentage", "doctype": "Delivery Note", "group_by": "docstatus", "label": "Delivery state"},
			{"type": "Bar", "doctype": "Sales Invoice", "group_by": "docstatus", "label": "Invoice state"},
			{"type": "Pie", "doctype": "Sales Invoice", "group_by": "is_return", "label": "Sales vs credit"},
			{"type": "Percentage", "doctype": "Customer", "group_by": "status", "label": "Customer status"},
		],
		"extra_sections": [
			(
				"Field sales (optional)",
				[
					("Sales representatives", "DocType", "Trading Sales Representative", "user"),
					("Van sales invoice", "DocType", "Trading Van Sales Invoice", "truck"),
				],
			),
		],
	},
	"omnexa_core_buy": {
		"_requires_app": "omnexa_core",
		"workspace": "Buy",
		"module": "Omnexa Core",
		"icon": "buying",
		"headline": "Buy",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Request-to-pay — suppliers, PR/PO, receipt, invoice, supplier payments; local procurement analytics only.",
		"trend_doctypes": ["Purchase Order", "Purchase Receipt", "Purchase Invoice"],
		"status_doctypes": ["Purchase Invoice", "Purchase Order"],
		"kpis": [
			("Companies", "Company", []),
			("Branches", "Branch", []),
			("Suppliers", "Supplier", []),
			("Purchase requests", "Purchase Request", []),
			("Purchase orders", "Purchase Order", []),
			("Purchase receipts", "Purchase Receipt", []),
			("Purchase invoices", "Purchase Invoice", []),
			("Landed cost vouchers", "Landed Cost Voucher", []),
			("Purchase approval rules", "Purchase Approval Rule", []),
		],
		"shortcuts": [
			("Company", "DocType", "Company"),
			("Branch", "DocType", "Branch"),
			("Tax Rule", "DocType", "Tax Rule"),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate"),
			("Supplier", "DocType", "Supplier"),
			("Purchase Request", "DocType", "Purchase Request"),
			("Purchase Order", "DocType", "Purchase Order"),
			("Purchase Receipt", "DocType", "Purchase Receipt"),
			("Purchase Invoice", "DocType", "Purchase Invoice"),
			("Payment Entry", "DocType", "Payment Entry"),
			("Purchase Register", "Report", "Purchase Register"),
			("Open Purchase Order Lines", "Report", "Open Purchase Order Lines"),
			("Purchase Delivery Performance", "Report", "Purchase Delivery Performance"),
			("Accounting — global financials", "URL", "/app/accounting"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Purchase Order", "group_by": "docstatus", "label": "PO state"},
			{"type": "Pie", "doctype": "Purchase Invoice", "group_by": "docstatus", "label": "PI state"},
			{"type": "Percentage", "doctype": "Purchase Receipt", "group_by": "docstatus", "label": "Receipt state"},
			{"type": "Bar", "doctype": "Purchase Invoice", "group_by": "is_return", "label": "PI vs debit"},
		],
		"extra_sections": [],
	},
	"omnexa_core_stock": {
		"_requires_app": "omnexa_core",
		"workspace": "Stock",
		"module": "Omnexa Core",
		"icon": "stock",
		"headline": "Stock",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Items, warehouses, movements, reconciliation, batch/serial on vouchers & local stock analytics.",
		"trend_doctypes": ["Stock Entry", "Stock Reconciliation", "Item"],
		"status_doctypes": ["Stock Entry"],
		"kpis": [
			("Companies", "Company", []),
			("Branches", "Branch", []),
			("Items", "Item", []),
			("Warehouses", "Warehouse", []),
			("Stock entries", "Stock Entry", []),
			("Stock reconciliations", "Stock Reconciliation", []),
		],
		"shortcuts": [
			("Company", "DocType", "Company"),
			("Branch", "DocType", "Branch"),
			("Warehouse", "DocType", "Warehouse"),
			("Item", "DocType", "Item"),
			("Stock Entry", "DocType", "Stock Entry"),
			("Stock Reconciliation", "DocType", "Stock Reconciliation"),
			("Item Stock Balance", "Report", "Item Stock Balance"),
			("Low Stock", "Report", "Low Stock"),
			("Inventory Valuation Summary", "Report", "Inventory Valuation Summary"),
			("Inventory Valuation (GL)", "Report", "Inventory Valuation (GL)"),
			("Accounting — global financials", "URL", "/app/accounting"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Stock Entry", "group_by": "purpose", "label": "Movement purpose"},
			{"type": "Pie", "doctype": "Item", "group_by": "product_type", "label": "Item types"},
			{"type": "Percentage", "doctype": "Stock Reconciliation", "group_by": "cadence", "label": "Reconciliation cadence"},
		],
		"extra_sections": [],
	},
	"omnexa_core_finance": {
		"_requires_app": "omnexa_accounting",
		"workspace": "Accounting",
		"module": "Omnexa Accounting",
		"icon": "accounting",
		"headline": "Accounting",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Global financial truth — GL, banking, journals, statutory statements, AR/AP aging, cash flow, consolidation & KPIs.",
		"trend_doctypes": ["Journal Entry", "Payment Entry", "Bank Reconciliation"],
		"status_doctypes": ["Journal Entry", "Bank Reconciliation"],
		"kpis": [
			("Companies", "Company", []),
			("Branches", "Branch", []),
			("GL accounts", "GL Account", []),
			("Journal entries", "Journal Entry", []),
			("Payment entries", "Payment Entry", []),
			("Bank reconciliations", "Bank Reconciliation", []),
			("Fiscal years", "Fiscal Year", []),
			("Tax rules", "Tax Rule", []),
			("Budgets", "Budget", []),
		],
		"shortcuts": [
			("Company", "DocType", "Company"),
			("Branch", "DocType", "Branch"),
			("GL Account", "DocType", "GL Account"),
			("Item (stock↔GL)", "DocType", "Item"),
			("Budget", "DocType", "Budget"),
			("Journal Entry", "DocType", "Journal Entry"),
			("Payment Entry", "DocType", "Payment Entry"),
			("Bank Reconciliation", "DocType", "Bank Reconciliation"),
			("General Ledger", "Report", "General Ledger"),
			("Trial Balance", "Report", "Trial Balance"),
			("Income Statement", "Report", "Income Statement"),
			("Balance Sheet", "Report", "Balance Sheet"),
			("Consolidated Trial Balance", "Report", "Consolidated Trial Balance"),
			("Cash Flow Statement (Structured)", "Report", "Cash Flow Statement (Structured)"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Journal Entry", "group_by": "docstatus", "label": "JE status"},
			{"type": "Pie", "doctype": "Payment Entry", "group_by": "docstatus", "label": "PE status"},
			{"type": "Percentage", "doctype": "Bank Reconciliation", "group_by": "status", "label": "Bank rec status"},
		],
		"extra_sections": [],
	},
	"omnexa_projects_pm": {
		"_requires_app": "omnexa_projects_pm",
		"workspace": "Projects PM",
		"module": "Omnexa Projects PM",
		"icon": "project",
		"headline": "Projects PM",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "WBS, milestones, issues, baselines, KPI snapshots, and risk — when Omnexa Projects PM is installed.",
		"trend_doctypes": ["PM WBS Task", "PM Issue Log"],
		"status_doctypes": ["PM WBS Task"],
		"kpis": [
			("WBS tasks", "PM WBS Task", []),
			("Milestones", "PM Milestone", []),
			("Issues", "PM Issue Log", []),
			("Baseline snapshots", "PM Baseline Snapshot", []),
		],
		"shortcuts": [
			("PM WBS Task", "DocType", "PM WBS Task"),
			("PM Milestone", "DocType", "PM Milestone"),
			("PM Issue Log", "DocType", "PM Issue Log"),
			("PM Baseline Snapshot", "DocType", "PM Baseline Snapshot"),
			("PM KPI Snapshot", "DocType", "PM KPI Snapshot"),
			("PM Resource Assignment", "DocType", "PM Resource Assignment"),
			("Risk Register", "DocType", "Risk Register"),
			("PM CPM Groundwork", "Report", "PM CPM Groundwork"),
			("PM Resource Loading", "Report", "PM Resource Loading"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "PM WBS Task", "group_by": "status", "label": "Task status"},
			{"type": "Pie", "doctype": "PM Issue Log", "group_by": "severity", "label": "Issue severity"},
		],
		"extra_sections": [],
	},
	"omnexa_core_governance": {
		"_requires_app": "omnexa_core",
		"workspace": "Governance",
		"module": "Omnexa Core",
		"icon": "shield",
		"headline": "Governance",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Organization, users, roles, permissions, workflows, system settings, audit trail — control & approvals.",
		"trend_doctypes": ["User", "Workflow"],
		"status_doctypes": ["Workflow"],
		"kpis": [
			("Companies", "Company", []),
			("Users", "User", []),
			("Roles", "Role", []),
			("Workflows", "Workflow", []),
			("Tax rules", "Tax Rule", []),
			("Error logs", "Error Log", []),
		],
		"shortcuts": [
			("Company", "DocType", "Company"),
			("User", "DocType", "User"),
			("Role", "DocType", "Role"),
			("User Permission", "DocType", "User Permission"),
			("Workflow", "DocType", "Workflow"),
			("Tax Rule", "DocType", "Tax Rule"),
			("Tax Authority Profile", "DocType", "Tax Authority Profile"),
			("Signing Profile", "DocType", "Signing Profile"),
			("System Settings", "DocType", "System Settings"),
			("Error Log", "DocType", "Error Log"),
			("Activity Log", "DocType", "Activity Log"),
			("Version", "DocType", "Version"),
			("Workspace", "DocType", "Workspace"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "User", "group_by": "enabled", "label": "Users enabled"},
			{"type": "Pie", "doctype": "Workflow", "group_by": "is_active", "label": "Workflows active"},
		],
		"extra_sections": [],
	},
}


def _doctype_ready(name: str) -> bool:
	return bool(name and frappe.db.exists("DocType", name))


def _trim_chart_suffix(text: str, max_len: int = 28) -> str:
	s = (text or "").strip()
	return s if len(s) <= max_len else s[:max_len]


def _ensure_timeseries_chart(chart_name: str, module: str, document_type: str, viz: str) -> None:
	if frappe.db.exists("Dashboard Chart", chart_name) or not _doctype_ready(document_type):
		return
	if viz not in ("Line", "Bar"):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": chart_name,
			"module": module,
			"is_public": 1,
			"chart_type": "Count",
			"document_type": document_type,
			"based_on": "creation",
			"timeseries": 1,
			"timespan": "Last Month",
			"time_interval": "Daily",
			"type": viz,
			"filters_json": "[]",
		}
	)
	doc.insert(ignore_permissions=True)


def _ensure_line_chart(chart_name: str, module: str, document_type: str) -> None:
	_ensure_timeseries_chart(chart_name, module, document_type, "Line")


def _ensure_group_by_chart(
	chart_name: str,
	module: str,
	document_type: str,
	group_field: str,
	viz: str,
	number_of_groups: int = 8,
) -> None:
	if frappe.db.exists("Dashboard Chart", chart_name) or not _doctype_ready(document_type):
		return
	if viz not in ("Bar", "Pie", "Donut", "Percentage"):
		return
	if not frappe.get_meta(document_type).has_field(group_field):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": chart_name,
			"module": module,
			"is_public": 1,
			"chart_type": "Group By",
			"document_type": document_type,
			"group_by_type": "Count",
			"group_by_based_on": group_field,
			"timeseries": 0,
			"type": viz,
			"filters_json": "[]",
			"number_of_groups": int(number_of_groups),
		}
	)
	doc.insert(ignore_permissions=True)


def _ensure_donut_chart(chart_name: str, module: str, document_type: str, group_field: str) -> None:
	_ensure_group_by_chart(chart_name, module, document_type, group_field, "Donut", 8)


def _collect_workspace_chart_names(spec: dict[str, Any], prefix: str, module: str) -> list[str]:
	"""Line + bar volume trends, tactical Bar/Pie/Percentage splits, then status donuts."""
	names: list[str] = []
	seen: set[str] = set()

	def add(chart_name: str) -> None:
		if chart_name and chart_name not in seen and frappe.db.exists("Dashboard Chart", chart_name):
			seen.add(chart_name)
			names.append(chart_name)

	trend = spec.get("trend_doctypes") or []
	for dt in trend:
		su = _trim_chart_suffix(dt, 28)
		cn = f"{prefix} · {su} Trend"
		_ensure_timeseries_chart(cn, module, dt, "Line")
		add(cn)

	if trend:
		d0 = trend[0]
		su = _trim_chart_suffix(d0, 24)
		cn = f"{prefix} · {su} Vol"
		_ensure_timeseries_chart(cn, module, d0, "Bar")
		add(cn)

	for row in spec.get("kpi_trends") or []:
		viz = row.get("type")
		dt = row.get("doctype")
		gf = row.get("group_by")
		if viz not in ("Bar", "Pie", "Percentage") or not dt or not gf:
			continue
		lbl = _trim_chart_suffix(row.get("label") or str(gf), 22)
		tag = str(viz)[:4]
		cn = f"{prefix} · {lbl} {tag}"
		_ensure_group_by_chart(cn, module, dt, gf, viz, int(row.get("number_of_groups") or 8))
		add(cn)

	for dt in spec.get("status_doctypes") or []:
		su = _trim_chart_suffix(dt, 24)
		cn = f"{prefix} · {su} Mix"
		_ensure_donut_chart(cn, module, dt, "status")
		add(cn)

	return names


def _ensure_number_card(label: str, document_type: str, module: str, filters: list | None) -> str | None:
	if not _doctype_ready(document_type):
		return None
	filters_json = json.dumps(filters or [], separators=(",", ":"))
	existing = frappe.db.get_value(
		"Number Card",
		{"label": label, "document_type": document_type, "function": "Count"},
		"name",
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Number Card",
			"label": label,
			"type": "Document Type",
			"document_type": document_type,
			"function": "Count",
			"filters_json": filters_json,
			"module": module,
			"is_public": 1,
			"show_percentage_stats": 1,
			"stats_time_interval": "Monthly",
			"show_full_number": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _slug(text: str) -> str:
	return "".join(c if c.isalnum() else "-" for c in text.lower())[:24].strip("-") or "ws"


def _workspace_row_label(link_name: str) -> str:
	"""Label shown on workspace rows; EditorJS blocks match page_data by this label (not Link name)."""
	parts = [p.strip() for p in (link_name or "").split("·")]
	return parts[-1] if parts else (link_name or "").strip()


def _build_content(
	spec: dict[str, Any],
	chart_block_labels: list[str],
	number_card_block_labels: list[str],
	shortcut_labels: list[str],
) -> str:
	slug = _slug(spec["workspace"])
	blocks: list[dict[str, Any]] = []
	blocks.append(
		{
			"id": f"{slug}-h",
			"type": "header",
			"data": {"text": f"<span class=\"h4\"><b>{spec['headline']}</b></span>", "col": 12},
		}
	)
	for i, nl in enumerate(number_card_block_labels):
		blocks.append(
			{
				"id": f"{slug}-nc{i}",
				"type": "number_card",
				"data": {"number_card_name": nl, "col": 4},
			}
		)
	for i, cl in enumerate(chart_block_labels):
		blocks.append({"id": f"{slug}-ch{i}", "type": "chart", "data": {"chart_name": cl, "col": 4}})
	blocks.append({"id": f"{slug}-ops", "type": "header", "data": {"text": "<b>Quick Actions</b>", "col": 12}})
	for i, sc in enumerate(shortcut_labels):
		blocks.append({"id": f"{slug}-sc{i}", "type": "shortcut", "data": {"shortcut_name": sc, "col": 3}})
	return json.dumps(blocks, separators=(",", ":"))


def _merge_link_sections(ws, sections: list[tuple[str, list[tuple[str, str, str, str]]]]) -> None:
	existing_breaks = {l.get("label") for l in (ws.links or []) if l.get("type") == "Card Break"}
	for break_label, links in sections:
		if break_label in existing_breaks:
			continue
		ws.append("links", {"type": "Card Break", "label": break_label, "hidden": 0})
		for label, link_type, link_to, icon in links:
			if link_type == "DocType" and not _doctype_ready(link_to):
				continue
			if link_type == "Report" and not frappe.db.exists("Report", link_to):
				continue
			ws.append(
				"links",
				{
					"type": "Link",
					"label": label,
					"link_type": link_type,
					"link_to": link_to,
					"icon": icon,
					"hidden": 0,
					"is_query_report": 1 if link_type == "Report" else 0,
				},
			)


_GENERIC_LINK_SKIP = frozenset({"User", "Role", "File", "Comment", "Version"})
# Optional: skip Frappe core maintenance workspaces (avoids dev-export noise on `bench migrate`).
_SKIP_GENERIC_WORKSPACE_NAMES: frozenset[str] = frozenset({"Build"})


def _registry_workspace_titles() -> set[str]:
	return {str(s.get("workspace", "")) for s in _APP_SPECS.values() if s.get("workspace")}


def _chart_prefix_for(ws) -> str:
	base = (ws.name or "ws").replace(" ", "")
	return base[:18] if len(base) > 1 else "ws"


def _ordered_doctypes_from_workspace(ws) -> list[str]:
	ws_module = (ws.module or "").strip()
	ordered: list[str] = []
	for row in ws.get("links") or []:
		if row.get("type") != "Link" or row.get("link_type") != "DocType":
			continue
		dt = row.get("link_to")
		if not dt or dt in _GENERIC_LINK_SKIP or not _doctype_ready(dt):
			continue
		if dt in ordered:
			continue
		ordered.append(dt)
	same_mod = [d for d in ordered if (frappe.db.get_value("DocType", d, "module") or "") == ws_module]
	rest = [d for d in ordered if d not in same_mod]
	return (same_mod + rest)[:20]


def _infer_kpi_trends_for_doctype(dt: str) -> list[dict[str, Any]]:
	meta = frappe.get_meta(dt)
	out: list[dict[str, Any]] = []
	viz_cycle = ("Bar", "Pie", "Percentage")
	for fn in ("status", "workflow_state", "docstatus"):
		if len(out) >= 3:
			break
		if not meta.has_field(fn):
			continue
		fd = meta.get_field(fn)
		if not fd or fd.fieldtype not in ("Select", "Data", "Int", "Link", "Read Only"):
			continue
		out.append(
			{
				"type": viz_cycle[len(out) % 3],
				"doctype": dt,
				"group_by": fn,
				"label": f"{fn.replace('_', ' ').title()}",
			}
		)
	return out


def _iter_shortcuts_from_workspace(ws) -> list[tuple[str, str, str]]:
	rows: list[tuple[str, str, str]] = []
	seen: set[tuple[str, str]] = set()
	for s in ws.get("shortcuts") or []:
		if not s.get("link_to") or not s.get("type"):
			continue
		key = (s.type, s.link_to)
		if key in seen:
			continue
		seen.add(key)
		rows.append((s.label or s.link_to, s.type, s.link_to))
	for row in ws.get("links") or []:
		if row.get("type") != "Link":
			continue
		if row.get("link_type") not in ("DocType", "Report"):
			continue
		lt = row.get("link_type")
		lto = row.get("link_to")
		if not lto:
			continue
		key = (lt, lto)
		if key in seen:
			continue
		if lt == "DocType" and (not _doctype_ready(lto) or lto in _GENERIC_LINK_SKIP):
			continue
		seen.add(key)
		rows.append((row.get("label") or lto, lt, lto))
		if len(rows) >= 14:
			break
	return rows[:14]


def _apply_desk_link_sections(ws, sections: list[tuple[str, list[tuple[str, str, str, str | None]]]]) -> None:
	"""Replace Workspace sidebar links from canonical desk layout (card breaks + links)."""
	ws.links = []
	for card_title, rows in sections:
		ws.append(
			"links",
			{"type": "Card Break", "label": card_title, "hidden": 0, "onboard": 0, "link_count": 0},
		)
		for label, link_type, link_to, ref_doc in rows:
			if link_type == "DocType" and not _doctype_ready(link_to):
				continue
			if link_type == "Report" and not frappe.db.exists("Report", link_to):
				continue
			row: dict[str, Any] = {
				"type": "Link",
				"hidden": 0,
				"onboard": 0,
				"label": label,
				"link_type": link_type,
				"link_to": link_to,
				"link_count": 0,
				"is_query_report": 0,
			}
			if link_type == "Report" and ref_doc:
				row["report_ref_doctype"] = ref_doc
			ws.append("links", row)


def infer_workspace_spec(ws) -> dict[str, Any]:
	"""Build a control-tower-style spec from an existing Workspace (sidebar links + shortcuts)."""
	doctypes = _ordered_doctypes_from_workspace(ws)
	headline = ws.title or ws.label or ws.name
	module = ws.module or "Desk"
	trend: list[str] = []
	for dt in doctypes:
		if frappe.get_meta(dt).has_field("creation"):
			trend.append(dt)
		if len(trend) >= 3:
			break
	status: list[str] = []
	for dt in doctypes:
		if frappe.get_meta(dt).has_field("status"):
			status.append(dt)
		if len(status) >= 2:
			break
	kpis: list[tuple[str, str, list]] = []
	for dt in doctypes[:8]:
		lbl = None
		for row in ws.get("links") or []:
			if row.get("link_to") == dt and row.get("label"):
				lbl = row.get("label")
				break
		kpis.append((lbl or dt.replace("_", " "), dt, []))
	kpi_trends: list[dict[str, Any]] = []
	for dt in doctypes[:4]:
		for row in _infer_kpi_trends_for_doctype(dt):
			if len(kpi_trends) >= 6:
				break
			kpi_trends.append(row)
		if len(kpi_trends) >= 6:
			break
	shortcuts = _iter_shortcuts_from_workspace(ws)
	return {
		"workspace": ws.name,
		"module": module,
		"headline": headline,
		"tagline": "",
		"trend_doctypes": trend,
		"status_doctypes": status or (trend[:1] if trend else []),
		"kpis": kpis,
		"kpi_trends": kpi_trends,
		"shortcuts": shortcuts,
		"extra_sections": [],
	}


def _apply_kpi_to_workspace(ws, spec: dict[str, Any], prefix: str) -> None:
	desk = spec.get("desk_link_layout")
	if desk:
		_apply_desk_link_sections(ws, desk)
	module = spec.get("module") or ws.module or "Desk"
	chart_names = _collect_workspace_chart_names(spec, prefix, module)
	chart_row_labels = [_workspace_row_label(ch) for ch in chart_names]

	number_card_ids: list[str] = []
	number_card_labels: list[str] = []
	for label, dt, filt in spec.get("kpis", []):
		if not _doctype_ready(dt):
			continue
		nm = _ensure_number_card(label, dt, module, filt)
		if nm:
			number_card_ids.append(nm)
			number_card_labels.append(label)

	ws.charts = []
	for ch, row_label in zip(chart_names[:12], chart_row_labels[:12]):
		ws.append("charts", {"chart_name": ch, "label": row_label})

	ws.number_cards = []
	for nm, row_lbl in zip(number_card_ids[:12], number_card_labels[:12]):
		ws.append("number_cards", {"number_card_name": nm, "label": row_lbl})

	shortcut_rows: list[dict[str, Any]] = []
	for i, sc in enumerate(spec.get("shortcuts", [])):
		if not sc or len(sc) < 3:
			continue
		lbl, ltype, lto = sc[0], sc[1], sc[2]
		if ltype == "URL":
			shortcut_rows.append(
				{
					"label": lbl,
					"type": "URL",
					"url": lto,
					"color": _COLORS[i % len(_COLORS)],
				}
			)
			continue
		if ltype == "DocType" and not _doctype_ready(lto):
			continue
		if ltype == "Report" and not frappe.db.exists("Report", lto):
			continue
		row: dict[str, Any] = {
			"label": lbl,
			"type": ltype,
			"link_to": lto,
			"color": _COLORS[i % len(_COLORS)],
		}
		if ltype == "DocType":
			row["doc_view"] = "List"
		shortcut_rows.append(row)

	ws.shortcuts = []
	for row in shortcut_rows:
		ws.append("shortcuts", row)

	shortcut_labels = [r["label"] for r in shortcut_rows]
	ws.content = _build_content(
		spec,
		chart_row_labels[:9],
		number_card_labels[:9],
		shortcut_labels[:14],
	)

	_merge_link_sections(ws, spec.get("extra_sections", []))


def sync_workspace_kpi_generic(ws_name: str) -> None:
	"""Apply KPI + charts + desk content to any public workspace from its links."""
	if not frappe.db.exists("Workspace", ws_name):
		return
	ws = frappe.get_doc("Workspace", ws_name)
	if not ws.public or getattr(ws, "for_user", None):
		return
	spec = infer_workspace_spec(ws)
	prefix = _chart_prefix_for(ws)
	_apply_kpi_to_workspace(ws, spec, prefix)
	ws.save(ignore_permissions=True)


def sync_all_workspace_kpi_layout() -> None:
	"""Registered finance verticals first, then every other public workspace (Omnexa + ERP)."""
	for app in _APP_SPECS:
		sync_workspace_for_app(app)
	registered = _registry_workspace_titles()
	for row in frappe.get_all("Workspace", filters={"public": 1}, fields=["name"], order_by="name asc"):
		name = row.name
		if name in registered or name in _SKIP_GENERIC_WORKSPACE_NAMES:
			continue
		try:
			sync_workspace_kpi_generic(name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), title=f"Workspace KPI generic: {name}")


def sync_workspace_for_app(app_name: str) -> None:
	"""Entry point from each app's workspace_enhancer.after_migrate."""
	spec = _APP_SPECS.get(app_name)
	if not spec:
		return
	required_app = spec.get("_requires_app", app_name)
	if not _app_installed(required_app):
		return
	spec = {**spec}
	ws_label = spec["workspace"]
	desk = get_desk_sections_for_workspace(ws_label)
	if desk:
		spec["desk_link_layout"] = desk
	module = spec["module"]
	prefix = ws_label[:12].replace(" ", "")

	if not frappe.db.exists("Workspace", ws_label):
		ws = frappe.new_doc("Workspace")
		ws.label = ws_label
		ws.title = ws_label
		ws.module = module
		ws.icon = spec.get("icon", "folder-normal")
		ws.public = 1
		ws.parent_page = "Finance Group"
		ws.sequence_id = 15.0
		ws.insert(ignore_permissions=True)
	else:
		ws = frappe.get_doc("Workspace", ws_label)

	ws.icon = spec.get("icon", ws.icon)
	ws.module = module
	ws.public = 1
	if "parent_page" in spec:
		ws.parent_page = spec["parent_page"]
	elif not ws.parent_page:
		ws.parent_page = "Finance Group"
	if "is_hidden" in spec:
		ws.is_hidden = int(spec["is_hidden"])

	_apply_kpi_to_workspace(ws, spec, prefix)
	ws.save(ignore_permissions=True)


def sync_all_finance_workspaces() -> None:
	sync_all_workspace_kpi_layout()
