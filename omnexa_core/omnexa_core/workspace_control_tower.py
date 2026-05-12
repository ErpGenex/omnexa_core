# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Enterprise control-tower workspace sync: KPI number cards (with % vs prior period),
dashboard charts (line, bar, donut, pie, percentage strip),
desk layout for registered finance apps plus **generic** public workspaces
(DocTypes inferred from sidebar links, same chart/card binding rules as Frappe Desk),
and **Guided setup** (Module Onboarding) matched per workspace module / title when not overridden.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.workspace_link_prune import prune_workspace_stale_links
from omnexa_core.omnexa_core.workspace_desk_layouts import (
	get_desk_sections_for_workspace,
	resolve_desk_sections_for_workspace_doc,
)
from omnexa_core.workspace_onboarding_sync import onboarding_name_for

_COLORS = ("Cyan", "Blue", "Purple", "Orange", "Green", "Red", "Teal", "Pink")

# Re-sync these last so core desks are not left on stale fixture JSON after other apps' after_migrate hooks.
_DESK_FINAL_PASS_APP_KEYS: tuple[str, ...] = (
	"omnexa_core",
	"omnexa_core_buy",
	"omnexa_core_stock",
	"omnexa_accounting",
	"omnexa_core_finance",
	"omnexa_core_governance",
	"omnexa_core_settings",
)


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
		"icon": "chart",
		"onboarding_name": "ERPGENEX — ALM",
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
	"omnexa_alm_governance": {
		"_requires_app": "omnexa_alm",
		"workspace": "ALM Governance",
		"module": "Omnexa ALM",
		"icon": "retail",
		"headline": "ALM Governance",
		"tagline": "Policy versions and audit snapshots for ALM oversight.",
		"parent_page": "ALM",
		"is_hidden": 1,
		"trend_doctypes": ["ALM Policy Version", "ALM Audit Snapshot"],
		"status_doctypes": ["ALM Policy Version"],
		"kpis": [
			("Policy Versions", "ALM Policy Version", []),
			("Audit Snapshots", "ALM Audit Snapshot", []),
		],
		"shortcuts": [
			("Policy Versions", "DocType", "ALM Policy Version"),
			("Audit Snapshots", "DocType", "ALM Audit Snapshot"),
		],
		"kpi_trends": [
			{"type": "Pie", "doctype": "ALM Policy Version", "group_by": "status", "label": "Policy status"},
		],
		"extra_sections": [],
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
		"icon": "loan",
		"onboarding_name": "ERPGENEX — Factoring",
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
	"omnexa_factoring_governance": {
		"_requires_app": "omnexa_factoring",
		"workspace": "Factoring Governance",
		"module": "Omnexa Factoring",
		"icon": "retail",
		"parent_page": "Factoring",
		"onboarding_name": "ERPGENEX — Factoring Governance",
		"headline": "Factoring Governance",
		"tagline": "Policy versions, audit snapshots, and compliance readiness.",
		"trend_doctypes": ["Factoring Policy Version", "Factoring Audit Snapshot"],
		"status_doctypes": ["Factoring Policy Version"],
		"kpis": [
			("Policy Versions", "Factoring Policy Version", []),
			("Audit Snapshots", "Factoring Audit Snapshot", []),
		],
		"shortcuts": [
			("Policy Versions", "DocType", "Factoring Policy Version"),
			("Audit Snapshots", "DocType", "Factoring Audit Snapshot"),
		],
		"kpi_trends": [
			{"type": "Pie", "doctype": "Factoring Policy Version", "group_by": "status", "label": "Policies by status"},
		],
		"extra_sections": [
			(
				"Governance reports",
				[
					("Governance Overview", "Report", "Governance Overview", "shield"),
				],
			),
		],
	},
	"omnexa_sme_retail_finance": {
		"workspace": "SME Retail Finance",
		"module": "Omnexa SME Retail Finance",
		"icon": "equity",
		"onboarding_name": "ERPGENEX — SME Retail Finance",
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
		"icon": "project",
		"onboarding_name": "ERPGENEX — Leasing Finance",
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
			("GL Accounts", "GL Account", []),
			("Journal Entries", "Journal Entry", []),
			("Payment Entries", "Payment Entry", []),
			("Bank Reconciliations", "Bank Reconciliation", []),
			("Budgets", "Budget", []),
			("Fiscal Years", "Fiscal Year", []),
			("Tax Rules", "Tax Rule", []),
		],
		"shortcuts": [
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
			("Sell Settings", "DocType", "Omnexa Sales Settings"),
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
			("Suppliers", "Supplier", []),
			("Purchase requests", "Purchase Request", []),
			("Purchase orders", "Purchase Order", []),
			("Purchase receipts", "Purchase Receipt", []),
			("Purchase invoices", "Purchase Invoice", []),
			("Landed cost vouchers", "Landed Cost Voucher", []),
			("Purchase approval rules", "Purchase Approval Rule", []),
		],
		"shortcuts": [
			("Buy Settings", "DocType", "Omnexa Purchase Settings"),
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
			("Items", "Item", []),
			("Warehouses", "Warehouse", []),
			("Stock entries", "Stock Entry", []),
			("Stock reconciliations", "Stock Reconciliation", []),
		],
		"shortcuts": [
			("Stock Settings", "DocType", "Omnexa Stock Settings"),
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
			("GL accounts", "GL Account", []),
			("Journal entries", "Journal Entry", []),
			("Payment entries", "Payment Entry", []),
			("Bank reconciliations", "Bank Reconciliation", []),
			("Fiscal years", "Fiscal Year", []),
			("Tax rules", "Tax Rule", []),
			("Budgets", "Budget", []),
		],
		"shortcuts": [
			("Accounting Settings", "DocType", "Omnexa Accounting Settings"),
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
		"workspace": "projects",
		"module": "Omnexa Projects PM",
		"icon": "kanban",
		"headline": "Projects",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Portfolio & programmes — WBS, milestones, CPM, resources, issues, baselines and KPIs; aligned with ISO 21500 / PMBOK delivery expectations.",
		"trend_doctypes": ["PM WBS Task", "PM Issue Log", "PM Milestone"],
		"status_doctypes": ["PM WBS Task", "PM Milestone"],
		"kpis": [
			("Project contracts", "Project Contract", []),
			("WBS tasks", "PM WBS Task", []),
			("Milestones", "PM Milestone", []),
			("Open issues", "PM Issue Log", [["status", "=", "Open"]]),
			("Baseline snapshots", "PM Baseline Snapshot", []),
			("Risk registers", "Risk Register", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "PM WBS Task", "group_by": "status", "label": "Task status"},
			{"type": "Pie", "doctype": "PM Issue Log", "group_by": "severity", "label": "Issue severity"},
			{"type": "Bar", "doctype": "PM Milestone", "group_by": "status", "label": "Milestone status"},
		],
		"extra_sections": [],
	},
	"omnexa_restaurant": {
		"_requires_app": "omnexa_restaurant",
		"workspace": "Restaurant",
		"module": "Omnexa Restaurant",
		"icon": "retail",
		"headline": "Restaurant",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "F&B desk — venue, menu, POS, kitchen, delivery, waste; revenue & gross margin analytics aligned with IFRS 15 revenue recognition.",
		"trend_doctypes": ["Restaurant Order", "Kitchen Ticket", "Waste Log"],
		"status_doctypes": ["Restaurant Order"],
		"kpis": [
			("Submitted orders", "Restaurant Order", [["docstatus", "=", 1]]),
			("Orders in progress", "Restaurant Order", [["status", "=", "In Progress"]]),
			("Kitchen tickets", "Kitchen Ticket", []),
			("Menu items", "Menu Item", []),
			("Restaurant tables", "Restaurant Table", []),
			("Waste logs", "Waste Log", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Restaurant Order", "group_by": "order_type", "label": "Sales by channel"},
			{"type": "Pie", "doctype": "Restaurant Order", "group_by": "status", "label": "Order status"},
			{"type": "Bar", "doctype": "Kitchen Ticket", "group_by": "ticket_status", "label": "Kitchen tickets"},
		],
		"extra_sections": [],
	},
	"omnexa_services": {
		"_requires_app": "omnexa_services",
		"workspace": "Services",
		"module": "Omnexa Services",
		"icon": "tool",
		"headline": "Services",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Professional & field service — tickets, SLAs, timesheets, billing; IFRS 15 revenue schedules and customer satisfaction visibility.",
		"trend_doctypes": ["Service Ticket", "Service Timesheet", "Service Invoice"],
		"status_doctypes": ["Service Ticket"],
		"kpis": [
			("Open tickets", "Service Ticket", [["status", "=", "Open"]]),
			("Tickets in progress", "Service Ticket", [["status", "=", "In Progress"]]),
			("Service timesheets", "Service Timesheet", []),
			("Service invoices", "Service Invoice", []),
			("Service contracts", "Service Contract", []),
			("Revenue schedules", "Service Revenue Schedule", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Service Ticket", "group_by": "priority", "label": "Tickets by priority"},
			{"type": "Pie", "doctype": "Service Ticket", "group_by": "status", "label": "Ticket status"},
			{"type": "Bar", "doctype": "Service Invoice", "group_by": "status", "label": "Invoice status"},
		],
		"extra_sections": [],
	},
	"omnexa_construction": {
		"_requires_app": "omnexa_construction",
		"workspace": "Construction",
		"module": "Omnexa Construction",
		"icon": "tool",
		"headline": "Construction",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "EPC & civil works — contracts, BOQ, site, claims, IPC & WIP; cost and progress analytics aligned with IFRS 15 / IAS 11 contract accounting expectations.",
		"trend_doctypes": ["Project Contract", "Site Daily Report", "IPC Certificate"],
		"status_doctypes": ["Project Contract", "Subcontract Work Order"],
		"kpis": [
			("Project contracts", "Project Contract", []),
			("BOQ lines", "BOQ Item", []),
			("Site daily reports", "Site Daily Report", []),
			("Subcontract work orders", "Subcontract Work Order", []),
			("IPC certificates", "IPC Certificate", []),
			("Construction claims", "Construction Claim", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Project Contract", "group_by": "contract_type", "label": "Contracts by type"},
			{"type": "Pie", "doctype": "Project Contract", "group_by": "status", "label": "Contract status"},
			{"type": "Bar", "doctype": "IPC Certificate", "group_by": "status", "label": "IPC status"},
		],
		"extra_sections": [],
	},
	"omnexa_agriculture": {
		"_requires_app": "omnexa_agriculture",
		"workspace": "Agriculture",
		"module": "Omnexa Agriculture",
		"icon": "agriculture",
		"headline": "Agriculture",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Farm enterprise — land, crops, livestock, harvest & traceability; GlobalG.A.P and IFRS / IAS 41 biological-asset alignment; procurement and revenue integration.",
		"trend_doctypes": ["Farm", "Crop Cycle", "Harvest Record"],
		"status_doctypes": ["Farm", "Crop Cycle"],
		"kpis": [
			("Farms", "Farm", []),
			("Field plots", "Field Plot", []),
			("Crop cycles", "Crop Cycle", []),
			("Livestock animals", "Livestock Animal", []),
			("Vaccination records", "Vaccination Record", []),
			("Harvest records", "Harvest Record", []),
			("Customers", "Customer", []),
			("Purchase orders", "Purchase Order", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Farm", "group_by": "farm_type", "label": "Farm type"},
			{"type": "Pie", "doctype": "Crop Cycle", "group_by": "status", "label": "Crop cycle status"},
			{"type": "Bar", "doctype": "Livestock Animal", "group_by": "animal_type", "label": "Livestock type"},
		],
		"extra_sections": [],
	},
	"omnexa_statutory_audit": {
		"_requires_app": "omnexa_statutory_audit",
		"workspace": "Audit",
		"module": "Omnexa Core",
		"icon": "review",
		"headline": "Audit",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Statutory audit — engagements, evidence, findings & opinion drafts; IFRS financial statement tie-out to trial balance, general ledger, receivables/payables and substantive balance review.",
		"trend_doctypes": ["Audit Engagement", "Audit Finding", "Audit Evidence"],
		"status_doctypes": ["Audit Engagement", "Audit Opinion Draft"],
		"kpis": [
			("Audit engagements", "Audit Engagement", []),
			("Opinion drafts", "Audit Opinion Draft", []),
			("Balance snapshot lines", "Audit Balance Snapshot", []),
			("Audit findings", "Audit Finding", []),
			("Audit evidence items", "Audit Evidence", []),
		],
		"shortcuts": [
			("Audit Engagement", "DocType", "Audit Engagement"),
			("Audit Opinion Draft", "DocType", "Audit Opinion Draft"),
			("Audit Balance Snapshot", "DocType", "Audit Balance Snapshot"),
			("Audit Finding", "DocType", "Audit Finding"),
			("Audit Evidence", "DocType", "Audit Evidence"),
			("General Ledger", "Report", "General Ledger"),
			("General Journal", "Report", "General Journal"),
		],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Audit Engagement", "group_by": "status", "label": "Engagement phase"},
			{"type": "Pie", "doctype": "Audit Finding", "group_by": "severity", "label": "Finding severity"},
			{"type": "Bar", "doctype": "Audit Balance Snapshot", "group_by": "review_status", "label": "Balance review"},
		],
		"extra_sections": [],
	},
	"omnexa_theme_manager": {
		"_requires_app": "omnexa_theme_manager",
		"workspace": "Theme Manager",
		"module": "Theme Manager",
		"icon": "es-line-colour",
		"headline": "Theme Manager",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Company Desk themes — presets, colors, typography, logos; activate per company without code.",
		"trend_doctypes": ["Experience Tenant Theme"],
		"status_doctypes": ["Experience Tenant Theme"],
		"kpis": [
			("Tenant themes", "Experience Tenant Theme", []),
		],
		"shortcuts": [
			("All tenant themes", "DocType", "Experience Tenant Theme"),
			("New tenant theme", "DocType", "Experience Tenant Theme"),
		],
		"kpi_trends": [
			{"type": "Pie", "doctype": "Experience Tenant Theme", "group_by": "theme_preset", "label": "Preset mix"},
			{"type": "Bar", "doctype": "Experience Tenant Theme", "group_by": "desk_theme_mode", "label": "Desk mode"},
			{"type": "Percentage", "doctype": "Experience Tenant Theme", "group_by": "apply_to_desk", "label": "Desk apply"},
		],
		"extra_sections": [],
	},
	"omnexa_customer_core": {
		"_requires_app": "omnexa_customer_core",
		"workspace": "CRM",
		"module": "Omnexa Customer Core",
		"icon": "users",
		"headline": "CRM",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Customer 360, pipeline, cases & campaigns — pipeline value, SLA and revenue analytics for global CRM governance.",
		"trend_doctypes": ["CRM Lead", "CRM Opportunity", "CRM Case Ticket"],
		"status_doctypes": ["CRM Opportunity", "CRM Case Ticket"],
		"kpis": [
			("Customer profiles", "Customer Profile", []),
			("Interaction logs", "CRM Interaction Log", []),
			("Leads", "CRM Lead", []),
			("Opportunities", "CRM Opportunity", []),
			("Case tickets", "CRM Case Ticket", []),
			("Campaigns", "CRM Campaign", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "CRM Lead", "group_by": "lead_status", "label": "Lead status"},
			{"type": "Pie", "doctype": "CRM Opportunity", "group_by": "status", "label": "Opportunity outcome"},
			{"type": "Bar", "doctype": "CRM Case Ticket", "group_by": "status", "label": "Case status"},
		],
		"extra_sections": [],
	},
	"omnexa_tourism": {
		"_requires_app": "omnexa_tourism",
		"workspace": "Tourism",
		"module": "Omnexa Tourism",
		"icon": "map",
		"headline": "Tourism",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Hospitality & travel — properties, bookings, folios and channel performance; UN IRSTS-style operations and revenue analytics.",
		"trend_doctypes": ["Tourism Booking", "Tourism Guest Folio", "Tourism Hotel"],
		"status_doctypes": ["Tourism Hotel", "Tourism Housekeeping Task"],
		"kpis": [
			("Hotels", "Tourism Hotel", []),
			("Bookings", "Tourism Booking", []),
			("Room units", "Tourism Room Unit", []),
			("Guest folios", "Tourism Guest Folio", []),
			("Service orders", "Tourism Service Order", []),
			("Travel packages", "Tourism Travel Package", []),
			("Customers", "Customer", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Tourism Booking", "group_by": "status", "label": "Booking status"},
			{"type": "Pie", "doctype": "Tourism Booking", "group_by": "booking_channel", "label": "Channel mix"},
			{"type": "Bar", "doctype": "Tourism Guest Folio", "group_by": "status", "label": "Folio status"},
		],
		"extra_sections": [],
	},
	"omnexa_healthcare": {
		"_requires_app": "omnexa_healthcare",
		"workspace": "Healthcare",
		"module": "Omnexa Healthcare",
		"icon": "organization",
		"headline": "Healthcare",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "FHIR-aligned care — patients, encounters, scheduling, inpatient and billing; clinical access and revenue analytics.",
		"trend_doctypes": ["Healthcare Encounter", "Healthcare Appointment", "Healthcare Admission"],
		"status_doctypes": ["Healthcare Encounter", "Healthcare Appointment"],
		"kpis": [
			("Patients", "Healthcare Patient", []),
			("Encounters", "Healthcare Encounter", []),
			("Appointments", "Healthcare Appointment", []),
			("Admissions", "Healthcare Admission", []),
			("Service charges", "Healthcare Service Charge", []),
			("Diagnostic reports", "Healthcare Diagnostic Report", []),
			("Facilities", "Healthcare Facility Profile", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Healthcare Encounter", "group_by": "status", "label": "Encounter status"},
			{"type": "Pie", "doctype": "Healthcare Appointment", "group_by": "status", "label": "Appointment status"},
			{"type": "Bar", "doctype": "Healthcare Admission", "group_by": "status", "label": "Admission status"},
		],
		"extra_sections": [],
	},
	"omnexa_education": {
		"_requires_app": "omnexa_education",
		"workspace": "Education",
		"module": "Omnexa Education",
		"icon": "education",
		"headline": "Education",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "K–12 & institutions — curriculum, sections, students, fee billing and finance tie-out; enrollment and revenue analytics.",
		"trend_doctypes": ["Education Student", "Education Billing Invoice", "Education Section"],
		"status_doctypes": ["Education Student", "Education Section"],
		"kpis": [
			("Institutions", "Education Institution", []),
			("Students", "Education Student", []),
			("Sections", "Education Section", []),
			("Billing invoices", "Education Billing Invoice", []),
			("Fee plans", "Education Fee Plan", []),
			("Teachers", "Education Teacher", []),
			("Campuses", "Education Campus", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Education Student", "group_by": "status", "label": "Student status"},
			{"type": "Pie", "doctype": "Education Section", "group_by": "status", "label": "Section status"},
			{"type": "Bar", "doctype": "Education Institution", "group_by": "institution_type", "label": "Institution type"},
		],
		"extra_sections": [],
	},
	"omnexa_manufacturing": {
		"_requires_app": "omnexa_manufacturing",
		"workspace": "Manufacturing",
		"module": "Omnexa Manufacturing",
		"icon": "tool",
		"headline": "Manufacturing",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Shop floor & quality — work orders, production logs, BOMs and costing; OEE, yield and variance analytics.",
		"trend_doctypes": ["Work Order", "Production Log", "Manufacturing Quality Check"],
		"status_doctypes": ["Work Order", "Manufacturing Rework Order"],
		"kpis": [
			("Work orders", "Work Order", []),
			("Production logs", "Production Log", []),
			("Quality checks", "Manufacturing Quality Check", []),
			("Rework orders", "Manufacturing Rework Order", []),
			("BOMs", "Manufacturing BOM", []),
			("Material entries", "Work Order Material Entry", []),
			("Items", "Item", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Work Order", "group_by": "status", "label": "Work order status"},
			{"type": "Pie", "doctype": "Manufacturing Quality Check", "group_by": "status", "label": "QC status"},
			{"type": "Bar", "doctype": "Work Order", "group_by": "manufacturing_mode", "label": "Manufacturing mode"},
		],
		"extra_sections": [],
	},
	"omnexa_car_rental": {
		"_requires_app": "omnexa_car_rental",
		"workspace": "Car Rental",
		"module": "Omnexa Car Rental",
		"icon": "retail",
		"headline": "Car Rental",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Fleet & contracts — bookings, tolls, maintenance and damage exposure; utilization and revenue analytics.",
		"trend_doctypes": ["Rental Contract", "Rental Booking", "Vehicle"],
		"status_doctypes": ["Rental Contract", "Vehicle"],
		"kpis": [
			("Vehicles", "Vehicle", []),
			("Rental bookings", "Rental Booking", []),
			("Rental contracts", "Rental Contract", []),
			("Toll transactions", "Toll Transaction", []),
			("Maintenance records", "Vehicle Maintenance Record", []),
			("Damage reports", "Vehicle Damage Report", []),
			("Customers", "Customer", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Rental Booking", "group_by": "booking_status", "label": "Booking pipeline"},
			{"type": "Pie", "doctype": "Rental Contract", "group_by": "status", "label": "Contract status"},
			{"type": "Bar", "doctype": "Vehicle", "group_by": "status", "label": "Vehicle status"},
		],
		"extra_sections": [],
	},
	"omnexa_trading": {
		"_requires_app": "omnexa_trading",
		"workspace": "Trading",
		"module": "Omnexa Trading",
		"icon": "retail",
		"headline": "Trading",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Van sales & distribution — routes, orders, commissions and tenders; field fulfillment and credit analytics.",
		"trend_doctypes": ["Trading Distribution Order", "Trading Van Sales Invoice", "Trading Route Plan"],
		"status_doctypes": ["Trading Distribution Order", "Trading Tender"],
		"kpis": [
			("Route plans", "Trading Route Plan", []),
			("Distribution orders", "Trading Distribution Order", []),
			("Van sales invoices", "Trading Van Sales Invoice", []),
			("Vehicle transfers", "Trading Vehicle Stock Transfer", []),
			("Tenders", "Trading Tender", []),
			("Commission settlements", "Trading Commission Settlement", []),
			("Trading vehicles", "Trading Vehicle", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Trading Distribution Order", "group_by": "status", "label": "Order status"},
			{"type": "Pie", "doctype": "Trading Van Sales Invoice", "group_by": "status", "label": "Invoice status"},
			{"type": "Bar", "doctype": "Trading Tender", "group_by": "status", "label": "Tender pipeline"},
		],
		"extra_sections": [],
	},
	"omnexa_engineering_consulting": {
		"_requires_app": "omnexa_engineering_consulting",
		"workspace": "engineering-consulting",
		"module": "Omnexa Engineering Consulting",
		"icon": "quality",
		"headline": "Engineering Consulting",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "RIBA Plan of Work 2020 — design stages, submittals, information registers, communications, site records & engagement; procurement and IPC bridge to construction.",
		"trend_doctypes": ["Engineering Stage", "Engineering Submittal", "Client Communication Log"],
		"status_doctypes": ["Engineering Stage", "Engineering Submittal"],
		"kpis": [
			("Project contracts", "Project Contract", []),
			("RIBA engineering stages", "Engineering Stage", []),
			("Engineering submittals", "Engineering Submittal", []),
			("Client communications", "Client Communication Log", []),
			("Document register entries", "Engineering Document Register", []),
			("Site records", "Engineering Site Record", []),
			("Consultant engagements", "Engineering Consultant Engagement", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Engineering Stage", "group_by": "stage", "label": "RIBA stages"},
			{"type": "Pie", "doctype": "Engineering Submittal", "group_by": "workflow_state", "label": "Submittal workflow"},
			{"type": "Bar", "doctype": "Client Communication Log", "group_by": "channel", "label": "Comms channel"},
		],
		"extra_sections": [],
	},
	"omnexa_fixed_assets": {
		"_requires_app": "omnexa_fixed_assets",
		# Must match `tabWorkspace.name` from omnexa_fixed_assets workspace fixture (not label/title casing).
		"workspace": "Fixed Assets",
		"module": "Omnexa Fixed Assets",
		"icon": "folder-normal",
		"headline": "Fixed Assets",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Asset lifecycle workspace — acquisition, capitalization, depreciation, transfer, disposal, maintenance, valuation.",
		"trend_doctypes": [
			"Fixed Asset Acquisition",
			"Fixed Asset Depreciation Entry",
			"Fixed Asset Disposal",
		],
		"status_doctypes": ["Fixed Asset"],
		"kpis": [
			("Assets in register", "Fixed Asset", []),
			("Assets in use", "Fixed Asset", [["status", "=", "in_use"]]),
			("Assets under maintenance", "Fixed Asset", [["status", "=", "under_maintenance"]]),
			("Disposed assets", "Fixed Asset", [["status", "=", "disposed"]]),
			("Depreciation runs", "Fixed Asset Depreciation Entry", []),
			("Asset disposals", "Fixed Asset Disposal", []),
		],
		"shortcuts": [
			("Fixed Asset", "DocType", "Fixed Asset"),
			("Fixed Asset Category", "DocType", "Fixed Asset Category"),
			("Fixed Asset Acquisition", "DocType", "Fixed Asset Acquisition"),
			("Fixed Asset Depreciation Entry", "DocType", "Fixed Asset Depreciation Entry"),
			("Fixed Asset Disposal", "DocType", "Fixed Asset Disposal"),
			("Asset Register Report", "Report", "Asset Register Report"),
			("Asset Depreciation Schedule", "Report", "Asset Depreciation Schedule"),
			("Asset Movement Report", "Report", "Asset Movement Report"),
		],
		"kpi_trends": [
			{"type": "Pie", "doctype": "Fixed Asset", "group_by": "category", "label": "Distribution by category"},
			{"type": "Bar", "doctype": "Fixed Asset", "group_by": "status", "label": "Status breakdown"},
		],
		"extra_sections": [],
	},
	"omnexa_core_governance": {
		"_requires_app": "omnexa_core",
		"workspace": "Governance",
		"module": "Omnexa Core",
		"icon": "setting-gear",
		"headline": "Governance",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Organization, users, roles, permissions, workflows, system settings, audit trail — control & approvals.",
		"trend_doctypes": ["User", "Workflow"],
		"status_doctypes": ["Workflow"],
		"kpis": [
			("Users", "User", []),
			("Roles", "Role", []),
			("Workflows", "Workflow", []),
			("Tax rules", "Tax Rule", []),
			("Error logs", "Error Log", []),
		],
		"shortcuts": [
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
	"omnexa_core_settings": {
		"_requires_app": "omnexa_core",
		"workspace": "Settings",
		"module": "Omnexa Core",
		"icon": "setting",
		"headline": "Settings · Enterprise setup",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Organization, indirect tax (VAT/GST), sales & procurement masters, stock, e-invoicing — IFRS-aligned ERP configuration hub.",
		"trend_doctypes": ["Tax Rule", "Customer", "Supplier", "Item"],
		"status_doctypes": ["Customer", "Supplier"],
		"kpis": [
			("Companies", "Company", []),
			("Branches", "Branch", []),
			("Tax categories", "Tax Category", []),
			("Tax rules", "Tax Rule", []),
			("Customers", "Customer", []),
			("Suppliers", "Supplier", []),
			("Items", "Item", []),
			("Warehouses", "Warehouse", []),
			("Users", "User", []),
		],
		"shortcuts": [],
		"kpi_trends": [
			{"type": "Bar", "doctype": "Tax Rule", "group_by": "tax_type", "label": "Tax rules by treatment"},
			{"type": "Pie", "doctype": "Customer", "group_by": "status", "label": "Customer status"},
			{"type": "Pie", "doctype": "Supplier", "group_by": "status", "label": "Supplier status"},
			{"type": "Bar", "doctype": "Item", "group_by": "product_type", "label": "Item types"},
		],
		"extra_sections": [],
	},
	"omnexa_nursery": {
		"_requires_app": "omnexa_nursery",
		"workspace": "Nursery",
		"module": "Nursery Setup",
		"icon": "heart",
		"headline": "Nursery",
		"parent_page": "",
		"is_hidden": 0,
		"tagline": "Early-years operations — families, programs, attendance, transport, and billing.",
		"trend_doctypes": ["Nursery Student", "Nursery Attendance"],
		"status_doctypes": [],
		"kpis": [
			("Students", "Nursery Student", []),
			("Parents", "Nursery Parent Profile", []),
			("Attendance lines", "Nursery Attendance", []),
		],
		"shortcuts": [
			("Nursery Settings", "DocType", "Nursery Settings"),
			("Students", "DocType", "Nursery Student"),
			("Parents", "DocType", "Nursery Parent Profile"),
			("Attendance", "DocType", "Nursery Attendance"),
			("Students by class", "Report", "Nursery Students by Class"),
			("Attendance summary", "Report", "Nursery Attendance Summary"),
		],
		"kpi_trends": [],
		"extra_sections": [],
	},
}


def _doctype_ready(name: str) -> bool:
	return bool(name and frappe.db.exists("DocType", name))


def _aggregatable_doctype(name: str) -> bool:
	"""DocTypes backed by a normal SQL table — Number Card Count & aggregate charts need this.

	Single DocTypes (e.g. Website Settings) and Virtual DocTypes have no `tab{Doctype}` row set;
	using them raises TableMissingError / ProgrammingError in get_list.
	"""
	if not _doctype_ready(name):
		return False
	try:
		meta = frappe.get_meta(name)
	except Exception:
		return False
	if getattr(meta, "issingle", False):
		return False
	if getattr(meta, "is_virtual", False):
		return False
	return True


def prune_invalid_workspace_kpi_artifacts() -> None:
	"""Remove Number Cards / Dashboard Charts tied to Single (or non-aggregatable) DocTypes; clear Workspace links."""
	singles = frappe.get_all("DocType", filters={"issingle": 1}, pluck="name")
	virtual = frappe.get_all("DocType", filters={"is_virtual": 1}, pluck="name")
	bad = list(dict.fromkeys([*(singles or []), *(virtual or [])]))
	if not bad:
		return
	for row in frappe.get_all(
		"Number Card",
		filters={"type": "Document Type", "document_type": ["in", bad]},
		pluck="name",
	):
		frappe.db.sql("DELETE FROM `tabWorkspace Number Card` WHERE number_card_name = %s", (row,))
		frappe.delete_doc("Number Card", row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Dashboard Chart", filters={"document_type": ["in", bad]}, pluck="name"):
		frappe.db.sql("DELETE FROM `tabWorkspace Chart` WHERE chart_name = %s", (row,))
		frappe.delete_doc("Dashboard Chart", row, force=True, ignore_permissions=True)
	frappe.db.commit()


def _trim_chart_suffix(text: str, max_len: int = 28) -> str:
	s = (text or "").strip()
	return s if len(s) <= max_len else s[:max_len]


def _ensure_timeseries_chart(chart_name: str, module: str, document_type: str, viz: str) -> None:
	if not _aggregatable_doctype(document_type):
		return
	if frappe.db.exists("Dashboard Chart", chart_name):
		# Keep chart globally visible on fresh sites/users (avoid module-gated filtering in Workspace API).
		try:
			frappe.db.set_value("Dashboard Chart", chart_name, "module", None, update_modified=False)
			frappe.db.set_value("Dashboard Chart", chart_name, "is_public", 1, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: normalize chart visibility {chart_name}")
		return
	if viz not in ("Line", "Bar"):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": chart_name,
			"module": None,
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
	if not _aggregatable_doctype(document_type):
		return
	if frappe.db.exists("Dashboard Chart", chart_name):
		try:
			frappe.db.set_value("Dashboard Chart", chart_name, "module", None, update_modified=False)
			frappe.db.set_value("Dashboard Chart", chart_name, "is_public", 1, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: normalize chart visibility {chart_name}")
		return
	if viz not in ("Bar", "Pie", "Donut", "Percentage"):
		return
	if not frappe.get_meta(document_type).has_field(group_field):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": chart_name,
			"module": None,
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

	def has_rows(doctype: str) -> bool:
		# Group-by/Pie/Donut chart payload can be empty on brand-new sites.
		# Keep those charts only when there is at least one source row to render.
		try:
			return bool(doctype) and cint(frappe.db.count(doctype, limit=1)) > 0
		except Exception:
			return False

	def add(chart_name: str) -> None:
		if chart_name and chart_name not in seen and frappe.db.exists("Dashboard Chart", chart_name):
			seen.add(chart_name)
			names.append(chart_name)

	trend = [dt for dt in (spec.get("trend_doctypes") or []) if _aggregatable_doctype(dt)]
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
		if viz not in ("Bar", "Pie", "Percentage") or not dt or not gf or not _aggregatable_doctype(dt):
			continue
		if not has_rows(dt):
			continue
		lbl = _trim_chart_suffix(row.get("label") or str(gf), 22)
		tag = str(viz)[:4]
		cn = f"{prefix} · {lbl} {tag}"
		_ensure_group_by_chart(cn, module, dt, gf, viz, int(row.get("number_of_groups") or 8))
		add(cn)

	for dt in spec.get("status_doctypes") or []:
		if not _aggregatable_doctype(dt):
			continue
		if not has_rows(dt):
			continue
		su = _trim_chart_suffix(dt, 24)
		cn = f"{prefix} · {su} Mix"
		_ensure_donut_chart(cn, module, dt, "status")
		add(cn)

	if not names and module and module != "Desk":
		for dt in _aggregatable_doctypes_for_module(module, limit=20):
			try:
				if not frappe.get_meta(dt).has_field("creation"):
					continue
			except Exception:
				continue
			su = _trim_chart_suffix(dt, 28)
			cn = f"{prefix} · {su} Trend"
			try:
				_ensure_timeseries_chart(cn, module, dt, "Line")
			except Exception:
				continue
			if frappe.db.exists("Dashboard Chart", cn):
				seen.add(cn)
				names.append(cn)
				break

	return names


def _ensure_number_card(label: str, document_type: str, module: str, filters: list | None) -> str | None:
	if not _aggregatable_doctype(document_type):
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


def _workspace_shortcut_es_icon(link_type: str, link_to: str | None) -> str:
	"""Espresso / timeless icon id for desk shortcuts (frappe.utils.icon on the client)."""
	lt = (link_type or "").strip()
	if lt == "URL":
		return "es-line-link"
	if lt == "Report":
		return "es-line-reports"
	if lt == "Dashboard":
		return "es-line-dashboard"
	if lt == "Workspace" and link_to and frappe.db.exists("Workspace", link_to):
		return "es-line-folder-normal"
	if lt == "Page" and link_to and frappe.db.exists("Page", link_to):
		pg = frappe.db.get_value("Page", link_to, "icon")
		if isinstance(pg, str) and pg.startswith("es-"):
			return pg
		if isinstance(pg, str) and pg and " " not in pg and not pg.startswith("fa"):
			return pg
		return "es-line-filetype"
	if lt == "DocType" and link_to and _doctype_ready(link_to):
		di = frappe.db.get_value("DocType", link_to, "icon")
		if isinstance(di, str) and di.startswith("es-"):
			return di
		if isinstance(di, str) and di and " " not in di and not di.startswith("fa"):
			return di
		return "es-line-filetype"
	return "es-line-filetype"


def _card_break_sidebar_es_icon(card_title: str) -> str:
	t = (card_title or "").lower()
	if "report" in t:
		return "es-line-reports"
	if any(k in t for k in ("chart", "kpi", "analytic", "dashboard")):
		return "es-line-dashboard"
	return "es-line-zap"


def _shortcut_seed_ops_before_reports(seed: list[Any]) -> list[Any]:
	"""Stable reorder: DocType / Page / URL before Report — main workspace body matches Operations → Reports."""
	if not seed:
		return seed
	ops: list[Any] = []
	rpts: list[Any] = []
	for sc in seed:
		if not sc or len(sc) < 3:
			continue
		if sc[1] == "Report":
			rpts.append(sc)
		else:
			ops.append(sc)
	return ops + rpts


def _workspace_row_label(link_name: str) -> str:
	"""Label shown on workspace rows; EditorJS blocks match page_data by this label (not Link name)."""
	parts = [p.strip() for p in (link_name or "").split("·")]
	return parts[-1] if parts else (link_name or "").strip()


def _build_content(
	spec: dict[str, Any],
	chart_full_names: list[str],
	number_card_doc_names: list[str],
	shortcut_rows: list[dict[str, Any]],
) -> str:
	slug = _slug(spec["workspace"])
	blocks: list[dict[str, Any]] = []
	onboarding = (spec.get("onboarding_name") or "").strip()
	if onboarding:
		blocks.append(
			{
				"id": "erpgenex-onboarding",
				"type": "onboarding",
				"data": {"onboarding_name": onboarding, "col": 12},
			}
		)
	blocks.append(
		{
			"id": f"{slug}-h",
			"type": "header",
			"data": {"text": f"<span class=\"h4\"><b>{spec['headline']}</b></span>", "col": 12},
		}
	)

	# Strict hierarchy (top -> bottom):
	# 1) Operations, 2) Reports, 3) KPIs, 4) Charts
	operation_shortcuts: list[str] = []
	report_shortcuts: list[str] = []
	for row in shortcut_rows:
		if row.get("type") == "Report":
			report_shortcuts.append(row.get("label"))
		else:
			operation_shortcuts.append(row.get("label"))

	blocks.append(
		{
			"id": f"{slug}-ops",
			"type": "header",
			"data": {"text": "<span class=\"h5\"><b>Operations</b></span>", "col": 12},
		}
	)
	core_ops: list[str] = []
	support_ops: list[str] = []
	master_ops: list[str] = []
	other_ops: list[str] = []
	for sc in operation_shortcuts[:72]:
		if ":" not in sc:
			other_ops.append(sc)
			continue
		prefix, label = [p.strip() for p in sc.split(":", 1)]
		if prefix.lower() == "core transactions":
			core_ops.append(label)
		elif prefix.lower() == "supporting processes":
			support_ops.append(label)
		elif prefix.lower() == "masters":
			master_ops.append(label)
		else:
			other_ops.append(sc)

	grouped_ops = bool(core_ops or support_ops or master_ops)
	# 12-column grid: col 4 → three shortcuts per row (consistent across vertical workspaces)
	op_col = 4
	op_idx = 0

	def _append_ops_group(title: str, items: list[str]) -> None:
		nonlocal op_idx
		if not items:
			return
		blocks.append(
			{
				"id": f"{slug}-opg{op_idx}",
				"type": "header",
				"data": {"text": f"<span class=\"h5\"><b>{title}</b></span>", "col": 12},
			}
		)
		op_idx += 1
		for item in items:
			blocks.append({"id": f"{slug}-op{op_idx}", "type": "shortcut", "data": {"shortcut_name": item, "col": op_col}})
			op_idx += 1

	_append_ops_group("Core Transactions", core_ops)
	_append_ops_group("Supporting Processes", support_ops)
	_append_ops_group("Masters", master_ops)

	if grouped_ops:
		for sc in other_ops:
			blocks.append({"id": f"{slug}-op{op_idx}", "type": "shortcut", "data": {"shortcut_name": sc, "col": op_col}})
			op_idx += 1
	else:
		# Unprefixed desk labels (e.g. full module navigation): flat grid under Operations — no fake Core/Support/Masters buckets.
		for sc in other_ops:
			blocks.append({"id": f"{slug}-op{op_idx}", "type": "shortcut", "data": {"shortcut_name": sc, "col": op_col}})
			op_idx += 1

	blocks.append(
		{
			"id": f"{slug}-rpt",
			"type": "header",
			"data": {"text": "<span class=\"h5\"><b>Reports</b></span>", "col": 12},
		}
	)
	for i, sc in enumerate(report_shortcuts[:18]):
		blocks.append({"id": f"{slug}-rp{i}", "type": "shortcut", "data": {"shortcut_name": sc, "col": 4}})

	blocks.append(
		{
			"id": f"{slug}-kpi",
			"type": "header",
			"data": {"text": "<span class=\"h5\"><b>KPIs</b></span>", "col": 12},
		}
	)
	for i, nm in enumerate(number_card_doc_names):
		blocks.append(
			{
				"id": f"{slug}-nc{i}",
				"type": "number_card",
				"data": {"number_card_name": nm, "col": 4},
			}
		)

	blocks.append(
		{
			"id": f"{slug}-chr",
			"type": "header",
			"data": {"text": "<span class=\"h5\"><b>Charts</b></span>", "col": 12},
		}
	)
	for i, ch_name in enumerate(chart_full_names):
		blocks.append({"id": f"{slug}-ch{i}", "type": "chart", "data": {"chart_name": ch_name, "col": 4}})
	return json.dumps(blocks, separators=(",", ":"))


def _merge_link_sections(ws, sections: list[tuple[str, list[tuple[str, str, str, str]]]]) -> None:
	existing_breaks = {l.get("label") for l in (ws.links or []) if l.get("type") == "Card Break"}
	for break_label, links in sections:
		if break_label in existing_breaks:
			continue
		ws.append(
			"links",
			{
				"type": "Card Break",
				"label": break_label,
				"hidden": 0,
				"icon": _card_break_sidebar_es_icon(break_label),
			},
		)
		for label, link_type, link_to, fourth in links:
			if (link_type or "").strip() == "URL":
				continue
			if link_type == "DocType" and not _doctype_ready(link_to):
				continue
			if link_type == "Report" and not frappe.db.exists("Report", link_to):
				continue
			if link_type == "Page" and not frappe.db.exists("Page", link_to):
				continue
			row = {
				"type": "Link",
				"label": label,
				"link_type": link_type,
				"link_to": link_to,
				"icon": _workspace_shortcut_es_icon(link_type, link_to),
				"hidden": 0,
				"is_query_report": 1 if link_type == "Report" else 0,
			}
			if link_type == "Report":
				ref = (
					fourth
					if fourth and frappe.db.exists("DocType", fourth)
					else frappe.db.get_value("Report", link_to, "ref_doctype")
				)
				if ref:
					row["report_ref_doctype"] = ref
			ws.append("links", row)


_GENERIC_LINK_SKIP = frozenset({"User", "Role", "File", "Comment", "Version"})
# Optional: skip Frappe core maintenance workspaces (avoids dev-export noise on `bench migrate`).
_SKIP_GENERIC_WORKSPACE_NAMES: frozenset[str] = frozenset({"Build"})

# Standard finance desks ship large `links` (sidebar) that repeat Operations `shortcuts` (desk body).
_DEDUPE_SIDEBAR_AGAINST_SHORTCUTS: frozenset[str] = frozenset(
	{
		"Credit Risk",
		"Credit Engine",
		"Finance Engine",
		"Vehicle Finance",
		"Consumer Finance",
		"Mortgage Finance",
		"Operational Risk",
		"ALM",
		"Factoring",
		"SME Retail Finance",
		"Leasing Finance",
		"Fixed Assets",
		"Audit",
	}
)


def _shortcut_nav_keys(ws) -> set[tuple[str, str]]:
	"""(type, link_to_or_url) for workspace shortcuts — align with Workspace Link (link_type, link_to)."""
	keys: set[tuple[str, str]] = set()
	for row in ws.shortcuts or []:
		st = (row.get("type") or "").strip()
		if st == "URL":
			url = (row.get("url") or row.get("link_to") or "").strip()
			if url:
				keys.add(("URL", url))
			continue
		lto = (row.get("link_to") or "").strip()
		if st and lto:
			keys.add((st, lto))
	return keys


def _dedupe_workspace_shortcut_rows(ws) -> None:
	if (ws.name or "") not in _DEDUPE_SIDEBAR_AGAINST_SHORTCUTS:
		return
	seen: set[tuple[str, str]] = set()
	kept: list[dict[str, Any]] = []
	for row in ws.shortcuts or []:
		st = (row.get("type") or "").strip()
		if st == "URL":
			key = ("URL", (row.get("url") or "").strip())
		else:
			key = (st, (row.get("link_to") or "").strip())
		if key[0] != "URL" and not key[1]:
			continue
		if key in seen:
			continue
		seen.add(key)
		kept.append(row)
	ws.shortcuts = []
	for row in kept:
		ws.append("shortcuts", row)


def _prune_workspace_links_duplicate_shortcuts(ws) -> None:
	"""Drop Workspace Link rows that duplicate a shortcut (same navigation target)."""
	if (ws.name or "") not in _DEDUPE_SIDEBAR_AGAINST_SHORTCUTS:
		return
	targets = _shortcut_nav_keys(ws)
	if not targets:
		return
	filtered: list[Any] = []
	for row in ws.links or []:
		if row.get("type") != "Link":
			filtered.append(row)
			continue
		lt = (row.get("link_type") or row.get("type") or "").strip()
		lto = (row.get("link_to") or "").strip()
		if (lt, lto) in targets:
			continue
		filtered.append(row)

	out: list[Any] = []
	i = 0
	n = len(filtered)
	while i < n:
		row = filtered[i]
		if row.get("type") == "Link":
			out.append(row)
			i += 1
			continue
		if row.get("type") == "Card Break":
			br = row
			j = i + 1
			chunk_links: list[Any] = []
			while j < n and filtered[j].get("type") == "Link":
				chunk_links.append(filtered[j])
				j += 1
			if chunk_links:
				out.append(br)
				out.extend(chunk_links)
			i = j
			continue
		i += 1

	ws.links = []
	for row in out:
		ws.append("links", row)


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
		if not dt or dt in _GENERIC_LINK_SKIP or not _aggregatable_doctype(dt):
			continue
		if dt in ordered:
			continue
		ordered.append(dt)
	same_mod = [d for d in ordered if (frappe.db.get_value("DocType", d, "module") or "") == ws_module]
	rest = [d for d in ordered if d not in same_mod]
	return (same_mod + rest)[:20]


def _aggregatable_doctypes_for_module(module: str | None, limit: int = 40) -> list[str]:
	"""DocTypes in this module that support Count / aggregate charts (no dependency on other apps)."""
	mod = (module or "").strip()
	if not mod or mod == "Desk":
		return []
	out: list[str] = []
	for name in frappe.get_all(
		"DocType",
		filters={"module": mod, "istable": 0, "issingle": 0, "is_virtual": 0},
		pluck="name",
		order_by="name asc",
		limit=limit + 20,
	):
		if name in _GENERIC_LINK_SKIP or not _aggregatable_doctype(name):
			continue
		out.append(name)
		if len(out) >= limit:
			break
	return out


def _enrich_spec_analytics_from_module(spec: dict[str, Any], ws) -> None:
	"""Guarantee trend / status / KPI / chart drivers from the workspace module when links are sparse."""
	module = (spec.get("module") or ws.module or "").strip()
	if not module or module == "Desk":
		return
	mod_dts = _aggregatable_doctypes_for_module(module)
	if not mod_dts:
		return

	trend = list(dict.fromkeys(spec.get("trend_doctypes") or []))
	for dt in mod_dts:
		if len(trend) >= 6:
			break
		if dt in trend:
			continue
		try:
			if frappe.get_meta(dt).has_field("creation"):
				trend.append(dt)
		except Exception:
			continue
	spec["trend_doctypes"] = trend

	status = list(dict.fromkeys(spec.get("status_doctypes") or []))
	for dt in mod_dts:
		if len(status) >= 5:
			break
		if dt in status:
			continue
		try:
			if frappe.get_meta(dt).has_field("status"):
				status.append(dt)
		except Exception:
			continue
	if not status and trend:
		status = [trend[0]]
	spec["status_doctypes"] = status

	kpis = list(spec.get("kpis") or [])
	seen_k: set[str] = {str(k[1]) for k in kpis if len(k) > 1}
	for dt in mod_dts:
		if len(kpis) >= 12:
			break
		if dt in seen_k:
			continue
		kpis.append((dt.replace("_", " "), dt, []))
		seen_k.add(dt)
	spec["kpis"] = kpis

	kt = list(spec.get("kpi_trends") or [])
	seen_trend: set[tuple[str, str]] = set()
	for row in kt:
		if row.get("doctype") and row.get("group_by"):
			seen_trend.add((str(row["doctype"]), str(row["group_by"])))
	for dt in mod_dts:
		if len(kt) >= 9:
			break
		for row in _infer_kpi_trends_for_doctype(dt):
			if len(kt) >= 9:
				break
			key = (str(row.get("doctype")), str(row.get("group_by")))
			if key in seen_trend:
				continue
			seen_trend.add(key)
			kt.append(row)
	spec["kpi_trends"] = kt


def _shortcut_seed_key(sc: Any) -> tuple[str, str] | None:
	if not sc or len(sc) < 3:
		return None
	return (str(sc[1]), str(sc[2]))


def _ensure_min_operation_shortcuts_in_seed(shortcut_seed: list[Any], module: str, minimum: int = 4) -> None:
	"""Add DocType shortcuts from the same module so Operations is never empty."""
	mod = (module or "").strip()
	if not mod or mod == "Desk":
		return
	non_report = sum(1 for s in shortcut_seed if _shortcut_seed_key(s) and s[1] != "Report")
	if non_report >= minimum:
		return
	seen = {_shortcut_seed_key(s) for s in shortcut_seed if _shortcut_seed_key(s)}
	for dt in _aggregatable_doctypes_for_module(mod, limit=25):
		if non_report >= minimum:
			break
		key = ("DocType", dt)
		if key in seen:
			continue
		shortcut_seed.append((dt.replace("_", " "), "DocType", dt))
		seen.add(key)
		non_report += 1


def _append_module_reports_to_shortcut_seed(shortcut_seed: list[Any], module: str, minimum_reports: int = 3) -> None:
	"""Add Report shortcuts from the workspace module when desk links skipped optional apps."""
	mod = (module or "").strip()
	if not mod or mod == "Desk":
		return
	report_count = sum(1 for s in shortcut_seed if _shortcut_seed_key(s) and s[1] == "Report")
	if report_count >= minimum_reports:
		return
	seen = {_shortcut_seed_key(s) for s in shortcut_seed if _shortcut_seed_key(s)}
	for name in frappe.get_all("Report", filters={"module": mod}, pluck="name", order_by="name asc", limit=24):
		if report_count >= minimum_reports:
			break
		if not name or not frappe.db.exists("Report", name):
			continue
		key = ("Report", name)
		if key in seen:
			continue
		shortcut_seed.append((name, "Report", name))
		seen.add(key)
		report_count += 1


def _onboarding_title_tail(onboarding_name: str) -> str:
	nm = (onboarding_name or "").strip()
	for sep in ("\u2014", "—"):
		if sep in nm:
			return nm.split(sep, 1)[-1].strip().lower()
	if " - " in nm:
		return nm.split(" - ", 1)[-1].strip().lower()
	return nm.lower()


def _workspace_onboarding_tokens(ws) -> set[str]:
	tokens: set[str] = set()
	for attr in ("name", "title", "label"):
		val = getattr(ws, attr, None)
		if not val:
			continue
		s = str(val).strip().lower()
		if not s:
			continue
		tokens.add(s)
		tokens.add(s.replace(" ", "").replace("-", ""))
		for part in s.replace("_", " ").split():
			if len(part) >= 2:
				tokens.add(part)
	return tokens


def _pick_module_onboarding_name(ws) -> str | None:
	"""Resolve Module Onboarding document name for this workspace (Guided setup widget)."""
	module = (ws.module or "").strip()
	if not module or module == "Desk":
		return None
	candidates = frappe.get_all(
		"Module Onboarding",
		filters={"module": module},
		pluck="name",
		order_by="name asc",
	)
	if not candidates:
		return None
	if len(candidates) == 1:
		return candidates[0]

	ws_tokens = _workspace_onboarding_tokens(ws)
	best: str | None = None
	best_score = -1
	for nm in candidates:
		tail = _onboarding_title_tail(nm)
		tail_c = tail.replace(" ", "")
		nm_l = nm.lower()
		score = 0
		for wt in ws_tokens:
			if len(wt) < 2:
				continue
			if wt == tail or wt == tail_c:
				score += 120
			elif tail.startswith(wt) or wt.startswith(tail):
				score += 80
			elif wt in tail or tail in wt:
				score += 40
			elif len(wt) >= 4 and wt in nm_l.replace(" ", "").replace("\u2014", "").replace("—", ""):
				score += 25
		if score > best_score:
			best_score = score
			best = nm
		elif score == best_score and best and nm and len(nm) > len(best):
			best = nm
	return best if best_score > 0 else candidates[0]


def _infer_kpi_trends_for_doctype(dt: str) -> list[dict[str, Any]]:
	if not _aggregatable_doctype(dt):
		return []
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
		if row.get("link_type") not in ("DocType", "Report", "Page"):
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
		if lt == "Report" and not frappe.db.exists("Report", lto):
			continue
		if lt == "Page" and not frappe.db.exists("Page", lto):
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
			{
				"type": "Card Break",
				"label": card_title,
				"hidden": 0,
				"onboard": 0,
				"link_count": 0,
				"icon": _card_break_sidebar_es_icon(card_title),
			},
		)
		for label, link_type, link_to, ref_doc in rows:
			# Workspace Link rows only support DocType / Page / Report (dynamic link options).
			# Desk tuples may use ("…", "URL", "/app/…") for convenience; those belong in shortcuts, not links.
			if (link_type or "").strip() == "URL":
				continue
			if link_type == "DocType" and not _doctype_ready(link_to):
				continue
			if link_type == "Report" and not frappe.db.exists("Report", link_to):
				continue
			if link_type == "Page" and not frappe.db.exists("Page", link_to):
				continue
			if link_type == "Workspace" and not frappe.db.exists("Workspace", link_to):
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
				"icon": _workspace_shortcut_es_icon(link_type, link_to),
			}
			if link_type == "Report":
				ref_for = (
					ref_doc
					if ref_doc and frappe.db.exists("DocType", ref_doc)
					else frappe.db.get_value("Report", link_to, "ref_doctype")
				)
				if ref_for:
					row["report_ref_doctype"] = ref_for
			if link_type == "Report":
				rt = frappe.db.get_value("Report", link_to, "report_type")
				if rt in ("Query Report", "Script Report", "Custom Report"):
					row["is_query_report"] = 1
			ws.append("links", row)


def infer_workspace_spec(ws) -> dict[str, Any]:
	"""Build a control-tower-style spec from an existing Workspace (sidebar links + shortcuts)."""
	doctypes = _ordered_doctypes_from_workspace(ws)
	headline = ws.title or ws.label or ws.name
	module = ws.module or "Desk"
	if not doctypes and module and module != "Desk":
		doctypes = _aggregatable_doctypes_for_module(module)[:20]
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
	shortcuts = _shortcut_seed_ops_before_reports(_iter_shortcuts_from_workspace(ws))
	_onb_spec: dict[str, Any] = {}
	_bind_workspace_onboarding_name(ws, _onb_spec)
	onb = (_onb_spec.get("onboarding_name") or "").strip()
	return {
		"workspace": ws.name,
		"module": module,
		"headline": headline,
		"tagline": "",
		"onboarding_name": onb,
		"trend_doctypes": trend,
		"status_doctypes": status or (trend[:1] if trend else []),
		"kpis": kpis,
		"kpi_trends": kpi_trends,
		"shortcuts": shortcuts,
		"extra_sections": [],
	}


def _bind_workspace_onboarding_name(ws, spec: dict[str, Any]) -> None:
	"""Wire Guided setup to the Module Onboarding row for this workspace (same id as workspace_onboarding_sync)."""
	if (spec.get("onboarding_name") or "").strip():
		return
	mod = (ws.module or "").strip()
	if not mod or mod == "Desk":
		return
	lbl = (getattr(ws, "label", None) or getattr(ws, "title", None) or ws.name or "").strip()
	if not lbl:
		return
	canon = onboarding_name_for(lbl)
	if frappe.db.exists("Module Onboarding", canon):
		spec["onboarding_name"] = canon
		return
	picked = _pick_module_onboarding_name(ws)
	if picked:
		spec["onboarding_name"] = picked


def _apply_kpi_to_workspace(ws, spec: dict[str, Any], prefix: str) -> None:
	desk = spec.get("desk_link_layout")
	if desk:
		_apply_desk_link_sections(ws, desk)
	module = spec.get("module") or ws.module or "Desk"
	_bind_workspace_onboarding_name(ws, spec)
	_enrich_spec_analytics_from_module(spec, ws)
	chart_names = _collect_workspace_chart_names(spec, prefix, module)
	# Frappe workspace Chart block resolves chart rows by label text equality with block chart_name.
	# Keep row label identical to chart_name to avoid silent chart-block drops in Desk render.
	chart_row_labels = list(chart_names)

	number_card_ids: list[str] = []
	number_card_labels: list[str] = []
	for label, dt, filt in spec.get("kpis", []):
		if not _aggregatable_doctype(dt):
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

	shortcut_seed: list[Any] = list(spec.get("shortcuts") or [])
	if desk:
		shortcut_seed = []
		for _card_title, rows in desk:
			for lbl, ltype, lto, _ref_doc in rows:
				shortcut_seed.append((lbl, ltype, lto))
	_ensure_min_operation_shortcuts_in_seed(shortcut_seed, module)
	_append_module_reports_to_shortcut_seed(shortcut_seed, module)
	shortcut_seed = _shortcut_seed_ops_before_reports(shortcut_seed)

	shortcut_rows: list[dict[str, Any]] = []
	for i, sc in enumerate(shortcut_seed):
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
					"icon": _workspace_shortcut_es_icon("URL", lto),
				}
			)
			continue
		if ltype == "DocType" and not _doctype_ready(lto):
			continue
		if ltype == "Report" and not frappe.db.exists("Report", lto):
			continue
		if ltype == "Page" and not frappe.db.exists("Page", lto):
			continue
		if ltype == "Workspace" and not frappe.db.exists("Workspace", lto):
			continue
		row: dict[str, Any] = {
			"label": lbl,
			"type": ltype,
			"link_to": lto,
			"color": _COLORS[i % len(_COLORS)],
			"icon": _workspace_shortcut_es_icon(ltype, lto),
		}
		if ltype == "DocType":
			row["doc_view"] = "List"
		if ltype == "Report":
			rt_ref = frappe.db.get_value("Report", lto, "ref_doctype")
			if rt_ref:
				row["report_ref_doctype"] = rt_ref
		shortcut_rows.append(row)

	ws.shortcuts = []
	for row in shortcut_rows:
		ws.append("shortcuts", row)

	ws.content = _build_content(
		spec,
		chart_names[:9],
		number_card_ids[:9],
		shortcut_rows[:72],
	)

	_merge_link_sections(ws, spec.get("extra_sections", []))
	_dedupe_workspace_shortcut_rows(ws)
	_prune_workspace_links_duplicate_shortcuts(ws)


def sync_workspace_kpi_generic(ws_name: str) -> None:
	"""Apply KPI + charts + desk content to any public workspace from its links."""
	if not frappe.db.exists("Workspace", ws_name):
		return
	ws = frappe.get_doc("Workspace", ws_name)
	if not ws.public or getattr(ws, "for_user", None):
		return
	spec = infer_workspace_spec(ws)
	canonical = resolve_desk_sections_for_workspace_doc(ws) or get_desk_sections_for_workspace(ws_name)
	if canonical:
		spec["desk_link_layout"] = canonical
	prefix = _chart_prefix_for(ws)
	_apply_kpi_to_workspace(ws, spec, prefix)
	prune_workspace_stale_links(ws)
	ws.save(ignore_permissions=True)


def _ensure_asset_insurance_workspace() -> None:
	"""Create public ``Asset Insurance`` desk when fixed assets is installed (parity with local sidebar)."""
	if not _app_installed("omnexa_fixed_assets"):
		return
	if not get_desk_sections_for_workspace("Asset Insurance"):
		return
	if frappe.db.exists("Workspace", "Asset Insurance"):
		return
	parent = "Finance Group" if frappe.db.exists("Workspace", "Finance Group") else ""
	ws = frappe.new_doc("Workspace")
	ws.module = "Omnexa Fixed Assets"
	ws.label = "Asset Insurance"
	ws.title = "Asset Insurance"
	ws.icon = "shield"
	ws.public = 1
	ws.is_hidden = 0
	if parent:
		ws.parent_page = parent
	ws.sequence_id = 7.62
	ws.insert(ignore_permissions=True)


def _append_finance_group_workspace_nav_link(*, label: str, icon: str, link_to: str) -> None:
	"""Append a Finance Group → Workspace link when the target exists (fixtures may omit it)."""
	if not frappe.db.exists("Workspace", "Finance Group"):
		return
	if not frappe.db.exists("Workspace", link_to):
		return
	fg = frappe.get_doc("Workspace", "Finance Group")
	key = ("Workspace", link_to)
	for row in fg.links or []:
		if row.get("type") == "Link" and (row.get("link_type"), row.get("link_to")) == key:
			return
	fg.append(
		"links",
		{
			"type": "Link",
			"hidden": 0,
			"onboard": 0,
			"label": label,
			"link_type": "Workspace",
			"link_to": link_to,
			"link_count": 0,
			"icon": icon,
		},
	)
	fg.save(ignore_permissions=True)


def sync_all_workspace_kpi_layout() -> None:
	"""Registered finance verticals first, then every other public workspace (Omnexa + ERP)."""
	_ensure_asset_insurance_workspace()
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
			frappe.log_error(title=f"Workspace KPI generic: {name}", message=frappe.get_traceback())
	if _app_installed("omnexa_fixed_assets") and frappe.db.exists("Workspace", "Asset Insurance"):
		_append_finance_group_workspace_nav_link(label="Asset Insurance", icon="shield", link_to="Asset Insurance")
	for app_key in _DESK_FINAL_PASS_APP_KEYS:
		try:
			sync_workspace_for_app(app_key)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: final desk pass failed for `{app_key}`")


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
		pp = spec.get("parent_page")
		if isinstance(pp, str) and pp.strip():
			ws.parent_page = pp.strip()
	elif not ws.parent_page:
		ws.parent_page = "Finance Group"
	if "is_hidden" in spec:
		ws.is_hidden = int(spec["is_hidden"])

	_save_workspace_with_control_tower(ws, spec, prefix)


def _save_workspace_with_control_tower(ws, spec: dict[str, Any], prefix: str) -> None:
	"""Apply KPI/desk, prune stale child rows, save — retry once without ``extra_sections`` on validation errors."""
	_apply_kpi_to_workspace(ws, spec, prefix)
	prune_workspace_stale_links(ws)
	try:
		ws.save(ignore_permissions=True)
	except Exception:
		if spec.get("extra_sections"):
			frappe.log_error(
				frappe.get_traceback(),
				f"Omnexa: workspace save retry without extra_sections ({spec.get('workspace')})",
			)
			spec2 = {**spec, "extra_sections": []}
			ws = frappe.get_doc("Workspace", spec.get("workspace") or ws.name)
			_apply_kpi_to_workspace(ws, spec2, prefix)
			prune_workspace_stale_links(ws)
			ws.save(ignore_permissions=True)
		else:
			frappe.log_error(
				frappe.get_traceback(),
				f"Omnexa: workspace save failed ({spec.get('workspace') or getattr(ws, 'name', '')})",
			)
			raise


def sync_all_finance_workspaces() -> None:
	sync_all_workspace_kpi_layout()
