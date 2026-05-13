# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Canonical Desk sidebar (Card Break + Links) aligned with:
- Docs/.../Global ERP System Architecture Standard.md

Pattern (same as Sell): **Operations** (and for Accounting **Financial Operations**) first in document order,
then **Local … Reports** / **Global Financial Reports** / **System Reports** as named in the standard,
then supporting cards (setup, approvals, extra registers).

Applied on workspace_control_tower sync (`sync_workspace_for_app` + `sync_workspace_kpi_generic`) so migrate refreshes links.
"""

from __future__ import annotations

# (card_title, [(label, link_type, link_to, report_ref_doctype|None), ...])
DeskSection = tuple[str, list[tuple[str, str, str, str | None]]]

# When desk_link_layout applies, workspace spec shortcuts are replaced by desk rows only — include settings here.
_DESK_ERP_SETTINGS_URL: tuple[str, str, str, str | None] = ("ERP Settings", "URL", "/app/settings", None)

# --- SALES (Global ERP § Sales workspace — lines «Operations» + «Local Sales Reports» first) ---
SELL_DESK: list[DeskSection] = [
	(
		"Operations",
		[
			# Single DocType — must live in desk seed; spec["shortcuts"] are dropped when desk_link_layout applies.
			("Sales Settings", "DocType", "Omnexa Sales Settings", None),
			("Leads Management", "DocType", "Pipeline Lead", None),
			("Opportunities", "DocType", "Pipeline Opportunity", None),
			# Pipeline board / funnel context (same DocType as opportunities in Omnexa; listed twice per standard wording)
			("Sales Pipeline", "DocType", "Pipeline Opportunity", None),
			("Quotations", "DocType", "Sales Quotation", None),
			("Sales Orders", "DocType", "Sales Order", None),
			("Deliveries", "DocType", "Delivery Note", None),
			("Invoices", "DocType", "Sales Invoice", None),
			("Returns", "DocType", "Sales Invoice", None),
			("Customer Management", "DocType", "Customer", None),
		],
	),
	(
		"Local Sales Reports",
		[
			("Sales Performance Report", "Report", "Sales Performance", "Sales Invoice"),
			("Sales by Customer", "Report", "Sales by Customer", "Sales Invoice"),
			("Sales by Product", "Report", "Sales by Item", "Sales Invoice"),
			("Sales by Region", "Report", "Sales by Country", "Sales Invoice"),
			("Pipeline Conversion Report", "Report", "Pipeline Funnel", "Pipeline Opportunity"),
			("Revenue Analysis Report", "Report", "Revenue Analysis", "Sales Invoice"),
		],
	),
	(
		"Domain setup (tax · FX)",
		[
			("Tax Rule", "DocType", "Tax Rule", None),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate", None),
		],
	),
	(
		"CRM & campaigns (supporting)",
		[
			("CRM Activity", "DocType", "CRM Activity", None),
			("CRM Campaign", "DocType", "CRM Campaign", None),
		],
	),
	(
		"Payments · counter sales",
		[
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
			("E-Document Submission", "DocType", "E-Document Submission", None),
			("Tax Authority Profile", "DocType", "Tax Authority Profile", None),
			("Signing Profile", "DocType", "Signing Profile", None),
		],
	),
	(
		"Data & imports",
		[
			("Data Import", "DocType", "Data Import", None),
		],
	),
	(
		"Additional sales reports",
		[
			("Sales Register", "Report", "Sales Register", "Sales Invoice"),
		],
	),
]

# --- PROCUREMENT (Global ERP § Procurement — Operations + Local Procurement Reports first) ---
BUY_DESK: list[DeskSection] = [
	(
		"Operations",
		[
			("Purchase Settings", "DocType", "Omnexa Purchase Settings", None),
			("Purchase Requests", "DocType", "Purchase Request", None),
			("Supplier Management", "DocType", "Supplier", None),
			("Purchase Orders", "DocType", "Purchase Order", None),
			("Goods Receipt", "DocType", "Purchase Receipt", None),
			("Purchase Invoices", "DocType", "Purchase Invoice", None),
			("Supplier Payments", "DocType", "Payment Entry", None),
		],
	),
	(
		"Local Procurement Reports",
		[
			("Purchase Summary Report", "Report", "Purchase Register", "Purchase Invoice"),
			("Supplier Performance Report", "Report", "Supplier Ledger", "Journal Entry"),
			("Cost Analysis Report", "Report", "Purchase Cost Analysis", "Purchase Invoice"),
			("Pending Orders Report", "Report", "Open Purchase Order Lines", "Purchase Order"),
			("Delivery Delay Report", "Report", "Purchase Delivery Performance", "Purchase Order"),
		],
	),
	(
		"Domain setup (tax · FX)",
		[
			("Tax Rule", "DocType", "Tax Rule", None),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate", None),
		],
	),
	(
		"Supporting (approvals · landed cost)",
		[
			("Purchase Approval Rule", "DocType", "Purchase Approval Rule", None),
			("Landed Cost Voucher", "DocType", "Landed Cost Voucher", None),
		],
	),
]

# --- INVENTORY (Global ERP § Inventory — Operations + Local Inventory Reports first) ---
STOCK_DESK: list[DeskSection] = [
	(
		"Operations",
		[
			("Stock Settings", "DocType", "Omnexa Stock Settings", None),
			("Item Master", "DocType", "Item", None),
			("Warehouses", "DocType", "Warehouse", None),
			("Stock Movements", "DocType", "Stock Entry", None),
			("Transfers", "DocType", "Stock Entry", None),
			("Stock Adjustments", "DocType", "Stock Reconciliation", None),
			("Batch / Serial Tracking", "DocType", "Item", None),
		],
	),
	(
		"Local Inventory Reports",
		[
			("Stock Summary Report", "Report", "Stock Summary", "Item"),
			("Stock Ledger Report", "Report", "Stock Ledger", "Stock Entry"),
			("Inventory Valuation Report", "Report", "Inventory Valuation Summary", "Item"),
			("Stock Movement Report", "Report", "Stock Movement", "Stock Entry"),
			("Low Stock Report", "Report", "Low Stock", "Item"),
			("Expiry Report", "Report", "Expiry Report", "Item"),
		],
	),
	(
		"Domain setup · UOM",
		[
			("UOM", "DocType", "UOM", None),
		],
	),
	(
		"Additional inventory reports",
		[
			("Inventory Valuation (GL)", "Report", "Inventory Valuation (GL)", "Item"),
			("Stock Voucher Register", "Report", "Stock Voucher Register", "Stock Entry"),
			("Item Stock Balance", "Report", "Item Stock Balance", "Item"),
		],
	),
]

# --- ACCOUNTING CORE (Global ERP § Accounting — Financial Operations + Global Financial Reports first) ---
ACCOUNTING_DESK: list[DeskSection] = [
	(
		"Financial Operations",
		[
			("Accounting Settings", "DocType", "Omnexa Accounting Settings", None),
			("Chart of Accounts", "DocType", "GL Account", None),
			("General Ledger", "Report", "General Ledger", "Journal Entry"),
			("Journal Entries", "DocType", "Journal Entry", None),
			("Accounts Receivable (AR)", "Report", "Customer Ledger", "Journal Entry"),
			("Accounts Payable (AP)", "Report", "Supplier Ledger", "Journal Entry"),
			("Cost Centers", "DocType", "Cost Center", None),
			("Banking Transactions", "DocType", "Payment Entry", None),
		],
	),
	(
		"Global Financial Reports",
		[
			("Trial Balance (periodic — primary)", "Report", "Trial Balance", "GL Account"),
			("Profit & Loss Statement", "Report", "Income Statement", "GL Account"),
			("Balance Sheet", "Report", "Balance Sheet", "GL Account"),
			("Cash Flow Statement", "Report", "Cash Flow Statement (Structured)", "Journal Entry"),
			("AR Aging Report", "Report", "Receivables Aging", "Sales Invoice"),
			("AP Aging Report", "Report", "Payables Aging", "Purchase Invoice"),
			("Budget vs Actual Report", "Report", "Budget vs Actual", "Budget"),
			("Financial Consolidation Report", "Report", "Consolidated Trial Balance", "GL Account"),
		],
	),
	(
		"Supporting setup & dimensions",
		[
			("Fiscal Year", "DocType", "Fiscal Year", None),
			("Tax Rule", "DocType", "Tax Rule", None),
			("Currency Exchange Rate", "DocType", "Currency Exchange Rate", None),
			("Bank Account", "DocType", "Bank Account", None),
			("Mode of Payment", "DocType", "Mode of Payment", None),
			("Bank Reconciliation", "DocType", "Bank Reconciliation", None),
			("Budget (document)", "DocType", "Budget", None),
			("Item (stock ↔ GL)", "DocType", "Item", None),
		],
	),
	(
		"Additional global registers & cash flow views",
		[
			("General Journal", "Report", "General Journal", "Journal Entry"),
			("Employee Ledger", "Report", "Employee Ledger", "Journal Entry"),
			("Cash Activity Summary", "Report", "Cash Activity Summary", "Payment Entry"),
			("Cash Flow (simplified)", "Report", "Cash Flow (Simplified)", "Payment Entry"),
			("Cash Flow (indirect)", "Report", "Cash Flow Statement (Indirect)", "Journal Entry"),
			("Financial KPI Summary", "Report", "Financial KPI Summary", "GL Account"),
			("Receivables and DSO", "Report", "Receivables and DSO", "Sales Invoice"),
		],
	),
]

# HR: policy & workforce register → time → leave → payroll → talent → analytics (ISO 30414–style workforce metrics).
HR_DESK: list[DeskSection] = [
	(
		"Policy & organization",
		[
			("HR / Payroll settings", "DocType", "HR Payroll Company Settings", None),
			("User Branch Access", "DocType", "User Branch Access", None),
			("Employee", "DocType", "Employee", None),
			("HR Leave Type", "DocType", "HR Leave Type", None),
			("Leave Policy", "DocType", "Leave Policy", None),
		],
	),
	(
		"Time & attendance",
		[
			("HR Attendance", "DocType", "HR Attendance", None),
		],
	),
	(
		"Leave",
		[
			("HR Leave Application", "DocType", "HR Leave Application", None),
		],
	),
	(
		"Payroll & benefits",
		[
			("HR Payroll Company Settings", "DocType", "HR Payroll Company Settings", None),
			("HR Salary Slip", "DocType", "HR Salary Slip", None),
			("HR Payroll Run", "DocType", "HR Payroll Run", None),
			("HR Salary Advance", "DocType", "HR Salary Advance", None),
			("HR End of Service Settlement", "DocType", "HR End of Service Settlement", None),
			("HR Payroll Entry", "DocType", "HR Payroll Entry", None),
		],
	),
	(
		"Recruitment & development",
		[
			("HR Recruitment Request", "DocType", "HR Recruitment Request", None),
			("HR Interview", "DocType", "HR Interview", None),
			("HR Training Record", "DocType", "HR Training Record", None),
		],
	),
	(
		"Finance (payroll GL)",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
		],
	),
	(
		"Reports · Workforce",
		[
			("Headcount", "Report", "HR Headcount", "Employee"),
			("Payroll register", "Report", "HR Payroll Register", "HR Payroll Entry"),
		],
	),
	(
		"Reports · Time & leave",
		[
			("Attendance summary", "Report", "HR Attendance Summary", "HR Attendance"),
			("Monthly attendance rate", "Report", "HR Monthly Attendance Rate", "HR Attendance"),
			("Leave summary", "Report", "HR Leave Application Summary", "HR Leave Application"),
		],
	),
	(
		"Reports · Payroll & talent",
		[
			("Payroll summary", "Report", "HR Payroll Summary", "HR Payroll Entry"),
			("Salary slip register", "Report", "HR Salary Slip Register", "HR Salary Slip"),
			("Training summary", "Report", "HR Training Summary", "HR Training Record"),
			("Recruitment pipeline", "Report", "HR Recruitment Pipeline", "HR Recruitment Request"),
		],
	),
]

# ISO 21500 / PMBOK-style portfolio → WBS & milestones → delivery → performance; schedule analytics (CPM) + resource loading.
PROJECTS_DESK: list[DeskSection] = [
	(
		"Policy & access",
		[
			_DESK_ERP_SETTINGS_URL,
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Portfolio",
		[
			("Project Contract", "DocType", "Project Contract", None),
		],
	),
	(
		"Scope & schedule",
		[
			("PM WBS Task", "DocType", "PM WBS Task", None),
			("PM Milestone", "DocType", "PM Milestone", None),
			("PM Schedule (Gantt)", "Page", "pm_schedule_gantt", None),
		],
	),
	(
		"Delivery & resources",
		[
			("PM Issue Log", "DocType", "PM Issue Log", None),
			("PM Resource Assignment", "DocType", "PM Resource Assignment", None),
		],
	),
	(
		"Performance & risk",
		[
			("PM Baseline Snapshot", "DocType", "PM Baseline Snapshot", None),
			("PM KPI Snapshot", "DocType", "PM KPI Snapshot", None),
			("Risk Register", "DocType", "Risk Register", None),
		],
	),
	(
		"AEC & engineering",
		[
			("BOQ Item", "DocType", "BOQ Item", None),
			("Engineering Stage", "DocType", "Engineering Stage", None),
		],
	),
	(
		"Finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
		],
	),
	(
		"Reports · Schedule & resources",
		[
			("CPM groundwork", "Report", "PM CPM Groundwork", "PM WBS Task"),
			("Resource loading", "Report", "PM Resource Loading", "PM Resource Assignment"),
		],
	),
	(
		"Reports · Issues & milestones",
		[
			("Issue summary", "Report", "PM Issue Log Summary", "PM Issue Log"),
			("Milestone summary", "Report", "PM Milestone Summary", "PM Milestone"),
		],
	),
	(
		"Reports · Risk & earned value",
		[
			("Risk register summary", "Report", "PM Risk Register Summary", "Risk Register"),
			("EVM / KPI snapshot summary", "Report", "PM KPI Snapshot Summary", "PM KPI Snapshot"),
		],
	),
]

PROJECTS_GENERIC_DESK = PROJECTS_DESK

# --- ENTERPRISE SETTINGS (Operations → configuration reports; KPI/chart rows from control tower) ---
SETTINGS_DESK: list[DeskSection] = [
	(
		"Operations",
		[
			("Company Settings", "DocType", "Company", None),
			("Branches", "DocType", "Branch", None),
			("Taxes (Categories)", "DocType", "Tax Category", None),
			("Taxes (Rules & Rates)", "DocType", "Tax Rule", None),
			("Chart of accounts", "DocType", "GL Account", None),
			("Fiscal years", "DocType", "Fiscal Year", None),
			("Cost centers", "DocType", "Cost Center", None),
			("Currency exchange rates", "DocType", "Currency Exchange Rate", None),
			("Customers (AR master)", "DocType", "Customer", None),
			("Suppliers (AP master)", "DocType", "Supplier", None),
			("Purchase approval rules", "DocType", "Purchase Approval Rule", None),
			("Items (product master)", "DocType", "Item", None),
			("Warehouses", "DocType", "Warehouse", None),
			("Units of measure", "DocType", "UOM", None),
			("Tax authority profile", "DocType", "Tax Authority Profile", None),
			("E-Invoice Signing Profile", "DocType", "Signing Profile", None),
			("E-Invoice Submissions", "DocType", "E-Document Submission", None),
			("Users", "DocType", "User", None),
			("Roles", "DocType", "Role", None),
			("User permissions", "DocType", "User Permission", None),
			("Workflows", "DocType", "Workflow", None),
			("System settings", "DocType", "System Settings", None),
			("Activity log", "DocType", "Activity Log", None),
		],
	),
	(
		"Reports · setup & compliance audit",
		[
			("Tax configuration summary", "Report", "Tax Configuration Summary", "Tax Rule"),
			("Configuration change summary", "Report", "Configuration Change Summary", "Version"),
			("User activity summary", "Report", "User Activity Summary", "Activity Log"),
			("Access control summary", "Report", "Access Control Summary", "User Permission"),
			("Audit trail summary", "Report", "Audit Trail Summary", "Version"),
			("Workflow execution summary", "Report", "Workflow Execution Summary", "Workflow Action"),
		],
	),
]

# --- SYSTEM GOVERNANCE (Global ERP § System Governance — Operations + System Reports first) ---
GOVERNANCE_DESK: list[DeskSection] = [
	(
		"Operations",
		[
			("Users", "DocType", "User", None),
			("Roles", "DocType", "Role", None),
			("Permissions & Access Control", "DocType", "User Permission", None),
			("Approval Workflows", "DocType", "Workflow", None),
			("Tax categories (VAT / GST)", "DocType", "Tax Category", None),
			("Tax rules", "DocType", "Tax Rule", None),
			("Integrations", "DocType", "E-Document Submission", None),
			("Audit Logs", "DocType", "Activity Log", None),
			("Document versions", "DocType", "Version", None),
		],
	),
	(
		"System Reports",
		[
			("User Activity Report", "Report", "User Activity Summary", "Activity Log"),
			("Access Control Report", "Report", "Access Control Summary", "User Permission"),
			("Audit Trail Report", "Report", "Audit Trail Summary", "Version"),
			("Workflow Execution Report", "Report", "Workflow Execution Summary", "Workflow Action"),
			("Configuration Change Report", "Report", "Configuration Change Summary", "Version"),
		],
	),
	(
		"Supporting (e-invoice · integrations · desk)",
		[
			("Tax Authority Profile", "DocType", "Tax Authority Profile", None),
			("Signing Profile", "DocType", "Signing Profile", None),
			("Payment Intent", "DocType", "Payment Intent", None),
			("Web Order", "DocType", "Web Order", None),
			("System Settings", "DocType", "System Settings", None),
			("Workspace", "DocType", "Workspace", None),
			("Error Log", "DocType", "Error Log", None),
		],
	),
]

# IAS 16 / IFRS cost model: policy & register → recognition → depreciation → derecognition → assurance.
FIXED_ASSETS_DESK: list[DeskSection] = [
	(
		"Policy & master data",
		[
			_DESK_ERP_SETTINGS_URL,
			("Fixed Asset Category", "DocType", "Fixed Asset Category", None),
			("Fixed Asset Depreciation Method", "DocType", "Fixed Asset Depreciation Method", None),
			("Fixed Asset Location", "DocType", "Fixed Asset Location", None),
			("Fixed Asset Status", "DocType", "Fixed Asset Status", None),
			("Fixed Asset Auto Depreciation Policy", "DocType", "Fixed Asset Auto Depreciation Policy", None),
		],
	),
	(
		"Asset register",
		[
			("Fixed Asset", "DocType", "Fixed Asset", None),
		],
	),
	(
		"Recognition & capitalization",
		[
			("Fixed Asset Acquisition", "DocType", "Fixed Asset Acquisition", None),
			("Fixed Asset Revaluation", "DocType", "Fixed Asset Revaluation", None),
		],
	),
	(
		"Depreciation & impairment runs",
		[
			("Fixed Asset Depreciation Entry", "DocType", "Fixed Asset Depreciation Entry", None),
		],
	),
	(
		"Transfers & derecognition",
		[
			("Fixed Asset Transfer", "DocType", "Fixed Asset Transfer", None),
			("Fixed Asset Disposal", "DocType", "Fixed Asset Disposal", None),
			("Fixed Asset Write-Off", "DocType", "Fixed Asset Write-Off", None),
		],
	),
	(
		"Physical assurance",
		[
			("Fixed Asset Maintenance", "DocType", "Fixed Asset Maintenance", None),
			("Fixed Asset Inspection", "DocType", "Fixed Asset Inspection", None),
			("Fixed Asset Movement Log", "DocType", "Fixed Asset Movement Log", None),
		],
	),
	(
		"Finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
			("GL Account", "DocType", "GL Account", None),
			("Cost Center", "DocType", "Cost Center", None),
		],
	),
	(
		"Reports · Register & valuation",
		[
			("Asset register", "Report", "Asset Register Report", "Fixed Asset"),
			("Asset valuation", "Report", "Asset Valuation Report", "Fixed Asset"),
			("Fixed asset summary", "Report", "Fixed Asset Summary", "Fixed Asset"),
			("NBV by category", "Report", "Fixed Asset NBV by Category", "Fixed Asset"),
		],
	),
	(
		"Reports · Depreciation & traceability",
		[
			("Depreciation schedule", "Report", "Asset Depreciation Schedule", "Fixed Asset"),
			("Depreciation posting summary", "Report", "Fixed Asset Depreciation Posting Summary", "Fixed Asset Depreciation Entry"),
			("Movement report", "Report", "Asset Movement Report", "Fixed Asset"),
		],
	),
	(
		"Reports · Lifecycle & maintenance",
		[
			("Disposal report", "Report", "Asset Disposal Report", "Fixed Asset Disposal"),
			("Maintenance report", "Report", "Asset Maintenance Report", "Fixed Asset Maintenance"),
		],
	),
	(
		"Reports · Finance",
		[
			("Trial balance", "Report", "Trial Balance", "Journal Entry"),
			("General ledger", "Report", "General Ledger", "Journal Entry"),
		],
	),
	(
		"Asset warranty & insurance",
		[
			("Asset Insurance", "Workspace", "Asset Insurance", None),
		],
	),
]

# Asset insurance (policies, claims, renewals) — satellite desk under Fixed Assets.
ASSET_INSURANCE_DESK: list[DeskSection] = [
	(
		"Master data",
		[
			("Insurance Company", "DocType", "Insurance Company", None),
			("Insurance Coverage Type", "DocType", "Insurance Coverage Type", None),
		],
	),
	(
		"Operations",
		[
			("Insurance Policy", "DocType", "Insurance Policy", None),
			("Insurance Renewal", "DocType", "Insurance Renewal", None),
			("Insurance Incident", "DocType", "Insurance Incident", None),
			("Insurance Claim", "DocType", "Insurance Claim", None),
		],
	),
	(
		"Analytics",
		[
			("Asset Insurance Register", "Report", "Asset Insurance Register", "Insurance Policy"),
			("Expiring Policies Report", "Report", "Expiring Policies Report", "Insurance Policy"),
			("Uninsured Assets Report", "Report", "Uninsured Assets Report", "Fixed Asset"),
			("Claims Register", "Report", "Claims Register", "Insurance Claim"),
		],
	),
]

# --- Vertical workspaces: Tourism (full module navigation; sync replaces Workspace.links from this list) ---
TOURISM_DESK: list[DeskSection] = [
	(
		"Portfolio & setup",
		[
			_DESK_ERP_SETTINGS_URL,
			("Operation Model", "DocType", "Tourism Operation Model", None),
			("Hotel", "DocType", "Tourism Hotel", None),
			("Hotel Floor", "DocType", "Tourism Hotel Floor", None),
			("Restaurant Venue", "DocType", "Tourism Restaurant Venue", None),
			("Beach Facility", "DocType", "Tourism Beach Facility", None),
			("Travel Vendor", "DocType", "Tourism Travel Vendor", None),
			("Vendor Contract", "DocType", "Tourism Vendor Contract", None),
			("Travel Package", "DocType", "Tourism Travel Package", None),
			("Pricing Rule", "DocType", "Tourism Pricing Rule", None),
		],
	),
	(
		"Hotels & rooms",
		[
			("Room Type", "DocType", "Tourism Room Type", None),
			("Room Unit", "DocType", "Tourism Room Unit", None),
			("Housekeeping Task", "DocType", "Tourism Housekeeping Task", None),
		],
	),
	(
		"Bookings & travel",
		[
			("Booking", "DocType", "Tourism Booking", None),
			("Package Booking", "DocType", "Tourism Package Booking", None),
			("Transport Booking", "DocType", "Tourism Transport Booking", None),
			("Flight Booking", "DocType", "Tourism Flight Booking", None),
			("Activity Booking", "DocType", "Tourism Activity Booking", None),
			("Beach Booking", "DocType", "Tourism Beach Booking", None),
			("Restaurant Reservation", "DocType", "Tourism Restaurant Reservation", None),
			("Online Booking Request", "DocType", "Tourism Online Booking Request", None),
		],
	),
	(
		"Guests & CRM",
		[
			("Customer", "DocType", "Customer", None),
			("Customer Profile", "DocType", "Customer Profile", None),
		],
	),
	(
		"Guest services & folio",
		[
			("Guest Folio", "DocType", "Tourism Guest Folio", None),
			("Service Order", "DocType", "Tourism Service Order", None),
			("Charge Entry", "DocType", "Tourism Charge Entry", None),
		],
	),
	(
		"Finance",
		[
			("Sales Invoice", "DocType", "Sales Invoice", None),
			("Journal Entry", "DocType", "Journal Entry", None),
			("Cost Center", "DocType", "Cost Center", None),
			("Project", "DocType", "Project", None),
		],
	),
	# Hospitality / UN IRSTS-style grouping: operations & demand first, then commercial performance.
	(
		"Reports · Operations & demand",
		[
			("Occupancy", "Report", "Tourism Occupancy", "Tourism Room Unit"),
			("Booking status summary", "Report", "Tourism Booking Status Summary", "Tourism Booking"),
			("Channel performance", "Report", "Tourism Channel Performance", "Tourism Booking"),
			("Lead time analysis", "Report", "Tourism Lead Time Analysis", "Tourism Booking"),
			("Cancellation & no-show", "Report", "Tourism Cancellation & No-show", "Tourism Booking"),
			("Housekeeping performance", "Report", "Tourism Housekeeping Performance", "Tourism Housekeeping Task"),
		],
	),
	(
		"Reports · Revenue & profitability",
		[
			("KPI summary (ADR/RevPAR)", "Report", "Tourism KPI Summary", "Tourism Booking"),
			("Daily revenue", "Report", "Tourism Daily Revenue", "Tourism Booking"),
			("Room type performance", "Report", "Tourism Room Type Performance", "Tourism Booking"),
			("Service profitability", "Report", "Tourism Service Profitability", "Tourism Booking"),
			("Package profitability", "Report", "Tourism Package Profitability", "Tourism Package Booking"),
			("Flight ticket sales", "Report", "Tourism Flight Ticket Sales", "Tourism Flight Booking"),
			("Guest folio outstanding", "Report", "Tourism Guest Folio Outstanding", "Tourism Guest Folio"),
		],
	),
	(
		"Integrations",
		[
			("Restaurant Order", "DocType", "Restaurant Order", None),
			("Service Ticket", "DocType", "Service Ticket", None),
		],
	),
]

# FHIR-aligned grouping: setup → facility → patient journey → clinical → ancillary → billing → supply.
HEALTHCARE_DESK: list[DeskSection] = [
	(
		"Setup",
		[
			_DESK_ERP_SETTINGS_URL,
			("Healthcare settings", "DocType", "Healthcare Settings", None),
		],
	),
	(
		"Organization & facility",
		[
			("Facility profile", "DocType", "Healthcare Facility Profile", None),
			("Department", "DocType", "Healthcare Department", None),
			("Service unit", "DocType", "Healthcare Service Unit", None),
		],
	),
	(
		"Patients & visits",
		[
			("Patient", "DocType", "Healthcare Patient", None),
			("Encounter", "DocType", "Healthcare Encounter", None),
		],
	),
	(
		"Scheduling",
		[
			("Appointment", "DocType", "Healthcare Appointment", None),
		],
	),
	(
		"Care episodes",
		[
			("Episode of care", "DocType", "Healthcare Episode Of Care", None),
		],
	),
	(
		"Inpatient & wards",
		[
			("Bed", "DocType", "Healthcare Bed", None),
			("Admission", "DocType", "Healthcare Admission", None),
		],
	),
	(
		"Problems & allergies",
		[
			("Clinical condition", "DocType", "Healthcare Clinical Condition", None),
			("Allergy intolerance", "DocType", "Healthcare Allergy Intolerance", None),
		],
	),
	(
		"Immunizations",
		[
			("Immunization", "DocType", "Healthcare Immunization", None),
		],
	),
	(
		"Pharmacy & prescriptions",
		[
			("Medication statement", "DocType", "Healthcare Medication Statement", None),
			("Medication dispense", "DocType", "Healthcare Medication Dispense", None),
		],
	),
	(
		"Vitals & observations",
		[
			("Observation", "DocType", "Healthcare Observation", None),
		],
	),
	(
		"Laboratory & diagnostics",
		[
			("Service request", "DocType", "Healthcare Service Request", None),
			("Diagnostic report", "DocType", "Healthcare Diagnostic Report", None),
			("Lab sample", "DocType", "Healthcare Lab Sample", None),
		],
	),
	(
		"Hospital billing",
		[
			("Service charge", "DocType", "Healthcare Service Charge", None),
			("Sales Invoice", "DocType", "Sales Invoice", None),
		],
	),
	(
		"Stock & warehouse",
		[
			("Item", "DocType", "Item", None),
			("Warehouse", "DocType", "Warehouse", None),
			("Stock Entry", "DocType", "Stock Entry", None),
			("Stock Reconciliation", "DocType", "Stock Reconciliation", None),
			("UOM", "DocType", "UOM", None),
		],
	),
	(
		"Reports · Clinical & access",
		[
			("Encounter summary", "Report", "Healthcare Encounter Summary", "Healthcare Encounter"),
			("Appointment utilization", "Report", "Healthcare Appointment Utilization", "Healthcare Appointment"),
			("Inpatient occupancy", "Report", "Healthcare Inpatient Occupancy", "Healthcare Admission"),
			("Appointment status summary", "Report", "Healthcare Appointment Status Summary", "Healthcare Appointment"),
			("Admission LOS analysis", "Report", "Healthcare Admission LOS Analysis", "Healthcare Admission"),
		],
	),
	(
		"Reports · Revenue & diagnostics",
		[
			("Service charge summary", "Report", "Healthcare Service Charge Summary", "Healthcare Service Charge"),
			("Diagnostic category summary", "Report", "Healthcare Diagnostic Category Summary", "Healthcare Diagnostic Report"),
		],
	),
]

# K–12 / school management grouping: institution → curriculum → sections & learners → fee & billing → finance & ops.
EDUCATION_DESK: list[DeskSection] = [
	(
		"Institution & people",
		[
			_DESK_ERP_SETTINGS_URL,
			("Institution", "DocType", "Education Institution", None),
			("Campus", "DocType", "Education Campus", None),
			("Department", "DocType", "Education Department", None),
			("Teacher", "DocType", "Education Teacher", None),
		],
	),
	(
		"Academic structure",
		[
			("Curriculum", "DocType", "Education Curriculum", None),
			("Academic Year", "DocType", "Education Academic Year", None),
			("Term", "DocType", "Education Term", None),
			("Grade Level", "DocType", "Education Grade Level", None),
			("Subject", "DocType", "Education Subject", None),
		],
	),
	(
		"Sections & students",
		[
			("Section", "DocType", "Education Section", None),
			("Student", "DocType", "Education Student", None),
		],
	),
	(
		"Fee catalog & billing setup",
		[
			("Fee Item", "DocType", "Education Fee Item", None),
			("Fee Plan", "DocType", "Education Fee Plan", None),
			("Discount Rule", "DocType", "Education Discount Rule", None),
			("Late Fee Rule", "DocType", "Education Late Fee Rule", None),
			("Billing Cycle", "DocType", "Education Billing Cycle", None),
		],
	),
	(
		"Billing",
		[
			("Billing Invoice", "DocType", "Education Billing Invoice", None),
		],
	),
	(
		"Finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
			("GL Account", "DocType", "GL Account", None),
		],
	),
	(
		"Operational expenses",
		[
			("Supplier", "DocType", "Supplier", None),
			("Purchase Invoice", "DocType", "Purchase Invoice", None),
			("Payment Entry", "DocType", "Payment Entry", None),
			("Cost Center", "DocType", "Cost Center", None),
		],
	),
	(
		"Administration",
		[
			("Employee", "DocType", "Employee", None),
			("Leave Policy", "DocType", "Leave Policy", None),
			("Purchase Approval Rule", "DocType", "Purchase Approval Rule", None),
		],
	),
	(
		"Reports · Enrollment & capacity",
		[
			("Enrollment summary", "Report", "Education Enrollment Summary", "Education Student"),
			("Section utilization", "Report", "Education Section Utilization", "Education Section"),
			("Grade level profitability", "Report", "Education Grade Level Profitability", "Education Student"),
		],
	),
	(
		"Reports · Billing & finance",
		[
			("Fee aging", "Report", "Education Fee Aging", "Education Billing Invoice"),
			("Billing summary", "Report", "Education Billing Summary", "Education Billing Invoice"),
			("Fee revenue by item", "Report", "Education Fee Revenue by Item", "Education Billing Invoice"),
			("Expense by branch", "Report", "Education Expense by Branch", "Purchase Invoice"),
		],
	),
]

# Nursery / early-years: setup → programs & fees → daily ops → local reports (aligned with omnexa_nursery).
NURSE_DESK: list[DeskSection] = [
	(
		"Setup & people",
		[
			("Nursery Settings", "DocType", "Nursery Settings", None),
			("Students", "DocType", "Nursery Student", None),
			("Parents", "DocType", "Nursery Parent Profile", None),
		],
	),
	(
		"Programs, fees & activities",
		[
			("Educational activities", "DocType", "Nursery Educational Activity", None),
			("Activity enrollments", "DocType", "Nursery Activity Enrollment", None),
			("Fee structure", "DocType", "Nursery Fee Structure", None),
		],
	),
	(
		"Daily operations",
		[
			("Attendance", "DocType", "Nursery Attendance", None),
			("Daily observation", "DocType", "Nursery Daily Observation", None),
			("Transport", "DocType", "Nursery Transport", None),
		],
	),
	(
		"Reports · Safeguarding & health",
		[
			("Medical & allergy register", "Report", "Nursery Medical & Allergy Register", "Nursery Student"),
		],
	),
	(
		"Reports · Enrollment & capacity",
		[
			("Students by class", "Report", "Nursery Students by Class", "Nursery Student"),
			("Enrollment by age group", "Report", "Nursery Enrollment by Age Group", "Nursery Student"),
			("Pipeline by status", "Report", "Nursery Pipeline by Status", "Nursery Student"),
		],
	),
	(
		"Reports · Learning & wellbeing",
		[
			("Daily wellbeing summary", "Report", "Nursery Daily Wellbeing Summary", "Nursery Daily Observation"),
			("Observation coverage gaps", "Report", "Nursery Observation Coverage Gaps", "Nursery Student"),
		],
	),
	(
		"Reports · Operations",
		[
			("Attendance summary", "Report", "Nursery Attendance Summary", "Nursery Attendance"),
			("Attendance rate by class", "Report", "Nursery Attendance Rate by Class", "Nursery Attendance"),
			("Activity enrollment summary", "Report", "Nursery Activity Enrollment Summary", "Nursery Activity Enrollment"),
			("Transport routes", "Report", "Nursery Transport Routes", "Nursery Transport"),
			("Parent directory", "Report", "Nursery Parent Directory", "Nursery Parent Profile"),
		],
	),
]

# ISO-style flow: engineering master data → shop floor → quality → inventory bridge → costing; then KPI-style reports.
MANUFACTURING_DESK: list[DeskSection] = [
	(
		"Master data & engineering",
		[
			("Stock Settings", "DocType", "Omnexa Stock Settings", None),
			("Work Center", "DocType", "Work Center", None),
			("Manufacturing Routing", "DocType", "Manufacturing Routing", None),
			("Manufacturing Product Profile", "DocType", "Manufacturing Product Profile", None),
			("Item", "DocType", "Item", None),
			("Manufacturing BOM", "DocType", "Manufacturing BOM", None),
		],
	),
	(
		"Shop floor execution",
		[
			("Work Order", "DocType", "Work Order", None),
			("Production Log", "DocType", "Production Log", None),
			("Work Order Material Entry", "DocType", "Work Order Material Entry", None),
			("Work Order Cost Entry", "DocType", "Work Order Cost Entry", None),
		],
	),
	(
		"Quality & non-conformance",
		[
			("Manufacturing Quality Check", "DocType", "Manufacturing Quality Check", None),
			("Manufacturing Rework Order", "DocType", "Manufacturing Rework Order", None),
			("Work Order Scrap Entry", "DocType", "Work Order Scrap Entry", None),
		],
	),
	(
		"Inventory & procurement",
		[
			("Stock Entry", "DocType", "Stock Entry", None),
			("Warehouse", "DocType", "Warehouse", None),
			("Purchase Order", "DocType", "Purchase Order", None),
		],
	),
	(
		"Costing & finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
			("GL Account", "DocType", "GL Account", None),
			("Cost Center", "DocType", "Cost Center", None),
		],
	),
	(
		"Reports · Operations & performance",
		[
			("Work order status", "Report", "Production Work Order Status", "Work Order"),
			("Schedule risk", "Report", "Production Schedule Risk", "Work Order"),
			("OEE overview", "Report", "Production OEE Overview", "Production Log"),
			("First pass yield", "Report", "Production First Pass Yield", "Manufacturing Quality Check"),
			("Rework analysis", "Report", "Production Rework Analysis", "Manufacturing Rework Order"),
			("Scrap analysis", "Report", "Production Scrap Analysis", "Work Order Scrap Entry"),
		],
	),
	(
		"Reports · Cost & materials",
		[
			("Cost variance", "Report", "Production Cost Variance", "Work Order"),
			("Material consumption", "Report", "Production Material Consumption Summary", "Work Order Material Entry"),
			("Output & yield volume", "Report", "Production Output & Yield Summary", "Production Log"),
		],
	),
]

# Global car rental / ACRISS-style journey: organization → booking & contract → tolls → maintenance & risk → finance.
CAR_RENTAL_DESK: list[DeskSection] = [
	(
		"Organization & fleet",
		[
			_DESK_ERP_SETTINGS_URL,
			("Customer Profile", "DocType", "Customer Profile", None),
			("Customer", "DocType", "Customer", None),
			("Vehicle", "DocType", "Vehicle", None),
			("Rental Driver", "DocType", "Rental Driver", None),
			("Vehicle Insurance Policy", "DocType", "Vehicle Insurance Policy", None),
		],
	),
	(
		"Reservations & contracts",
		[
			("Rental Booking", "DocType", "Rental Booking", None),
			("Rental Contract", "DocType", "Rental Contract", None),
			("Supplier Fleet Contract", "DocType", "Supplier Fleet Contract", None),
		],
	),
	(
		"Tolls & road charges",
		[
			("Toll Provider", "DocType", "Toll Provider", None),
			("Toll Allocation Rule", "DocType", "Toll Allocation Rule", None),
			("Toll Transaction", "DocType", "Toll Transaction", None),
			("Toll Invoice Line", "DocType", "Toll Invoice Line", None),
		],
	),
	(
		"Fleet care & risk",
		[
			("Vehicle Maintenance Record", "DocType", "Vehicle Maintenance Record", None),
			("Vehicle Fuel Log", "DocType", "Vehicle Fuel Log", None),
			("Vehicle Damage Report", "DocType", "Vehicle Damage Report", None),
		],
	),
	(
		"Commercial & finance",
		[
			("Sales Invoice", "DocType", "Sales Invoice", None),
			("Payment Entry", "DocType", "Payment Entry", None),
			("Journal Entry", "DocType", "Journal Entry", None),
			("GL Account", "DocType", "GL Account", None),
			("Cost Center", "DocType", "Cost Center", None),
		],
	),
	(
		"Reports · Fleet & utilization",
		[
			("Fleet utilization", "Report", "Fleet Utilization", "Rental Contract"),
			("Revenue per vehicle", "Report", "Revenue per Vehicle", "Rental Contract"),
			("Maintenance cost analysis", "Report", "Maintenance Cost Analysis", "Vehicle Maintenance Record"),
			("Toll cost summary", "Report", "Toll Cost Summary", "Toll Transaction"),
		],
	),
	(
		"Reports · Demand & exposure",
		[
			("Booking pipeline", "Report", "Rental Booking Pipeline", "Rental Booking"),
			("Contract summary", "Report", "Rental Contract Summary", "Rental Contract"),
			("Fuel & energy cost", "Report", "Fuel & Energy Cost Summary", "Vehicle Fuel Log"),
			("Damage & liability", "Report", "Damage & Liability Exposure", "Vehicle Damage Report"),
		],
	),
	(
		"Reports · Finance",
		[
			("Sales register", "Report", "Sales Register", "Sales Invoice"),
			("Customer ledger", "Report", "Customer Ledger", "Journal Entry"),
			("General ledger", "Report", "General Ledger", "Journal Entry"),
		],
	),
]

# Van sales / route accounting journey: network → field execution → commissions → tenders & credit → finance (global distribution KPIs).
TRADING_DESK: list[DeskSection] = [
	(
		"Organization & network",
		[
			("Sales Settings", "DocType", "Omnexa Sales Settings", None),
			("Customer Profile", "DocType", "Customer Profile", None),
			("Customer", "DocType", "Customer", None),
			("Distribution Zone", "DocType", "Distribution Zone", None),
			("Trading Vehicle", "DocType", "Trading Vehicle", None),
			("Trading Sales Representative", "DocType", "Trading Sales Representative", None),
		],
	),
	(
		"Field sales & distribution",
		[
			("Trading Route Plan", "DocType", "Trading Route Plan", None),
			("Trading Distribution Order", "DocType", "Trading Distribution Order", None),
			("Trading Van Sales Invoice", "DocType", "Trading Van Sales Invoice", None),
			("Trading Vehicle Stock Transfer", "DocType", "Trading Vehicle Stock Transfer", None),
		],
	),
	(
		"Commissions & incentives",
		[
			("Trading Commission Rule", "DocType", "Trading Commission Rule", None),
			("Trading Commission Settlement", "DocType", "Trading Commission Settlement", None),
		],
	),
	(
		"Commercial strategy & credit",
		[
			("Trading Tender", "DocType", "Trading Tender", None),
			("Trading Installment Contract", "DocType", "Trading Installment Contract", None),
		],
	),
	(
		"Finance",
		[
			("Sales Invoice", "DocType", "Sales Invoice", None),
			("Payment Entry", "DocType", "Payment Entry", None),
			("Journal Entry", "DocType", "Journal Entry", None),
			("GL Account", "DocType", "GL Account", None),
			("Cost Center", "DocType", "Cost Center", None),
		],
	),
	(
		"Reports · Sales & routes",
		[
			("Sales summary", "Report", "Trading Sales Summary", "Trading Van Sales Invoice"),
			("Distribution fulfillment", "Report", "Trading Distribution Fulfillment", "Trading Distribution Order"),
			("Vehicle transfer summary", "Report", "Trading Vehicle Transfer Summary", "Trading Vehicle Stock Transfer"),
			("Route efficiency", "Report", "Trading Route Efficiency", "Trading Route Plan"),
			("Rep target tracking", "Report", "Trading Rep Target Tracking", "Trading Sales Representative"),
		],
	),
	(
		"Reports · Commissions & pipeline",
		[
			("Commission summary", "Report", "Trading Commission Summary", "Trading Commission Settlement"),
			("Tender pipeline", "Report", "Trading Tender Pipeline", "Trading Tender"),
			("Installment portfolio", "Report", "Trading Installment Portfolio", "Trading Installment Contract"),
		],
	),
	(
		"Reports · Finance",
		[
			("Sales register", "Report", "Sales Register", "Sales Invoice"),
			("Customer ledger", "Report", "Customer Ledger", "Journal Entry"),
			("General ledger", "Report", "General Ledger", "Journal Entry"),
		],
	),
]

# F&B: venue & menu → service/POS → delivery & waste → revenue & COGS analytics (IFRS 15 revenue; margin visibility).
RESTAURANT_DESK: list[DeskSection] = [
	(
		"Policy & venue",
		[
			_DESK_ERP_SETTINGS_URL,
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Floor & menu",
		[
			("Restaurant Floor", "DocType", "Restaurant Floor", None),
			("Restaurant Table", "DocType", "Restaurant Table", None),
			("Menu Item", "DocType", "Menu Item", None),
			("Restaurant Recipe", "DocType", "Restaurant Recipe", None),
			("Kitchen Station", "DocType", "Kitchen Station", None),
		],
	),
	(
		"Kitchen & printing",
		[
			("Kitchen Printer", "DocType", "Kitchen Printer", None),
			("Kitchen Print Template", "DocType", "Kitchen Print Template", None),
		],
	),
	(
		"Service & POS",
		[
			("Restaurant Order", "DocType", "Restaurant Order", None),
			("Restaurant POS", "Page", "restaurant-pos", None),
			("Kitchen Display", "Page", "kitchen-display", None),
			("Kitchen Ticket", "DocType", "Kitchen Ticket", None),
		],
	),
	(
		"Delivery & waste",
		[
			("Delivery Zone", "DocType", "Delivery Zone", None),
			("Delivery Driver", "DocType", "Delivery Driver", None),
			("Waste Log", "DocType", "Waste Log", None),
		],
	),
	(
		"Finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
		],
	),
	(
		"Reports · Revenue & margin",
		[
			("Sales summary", "Report", "Restaurant Sales Summary", "Restaurant Order"),
			("Daily sales", "Report", "Restaurant Daily Sales", "Restaurant Order"),
			("Margin summary", "Report", "Restaurant Margin Summary", "Restaurant Order"),
			("Item profitability", "Report", "Item Profitability", "Menu Item"),
		],
	),
	(
		"Reports · Kitchen & waste",
		[
			("Station performance", "Report", "Kitchen Station Performance", "Kitchen Station"),
			("Waste analysis", "Report", "Waste Analysis", "Waste Log"),
		],
	),
]

# Professional services: policy → catalog & IFRS 15 schedules → delivery → revenue & utilisation analytics.
SERVICES_DESK: list[DeskSection] = [
	(
		"Policy & access",
		[
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Catalog & contracts",
		[
			("Service Skill", "DocType", "Service Skill", None),
			("Service Resource", "DocType", "Service Resource", None),
			("Service Definition", "DocType", "Service Definition", None),
			("Service SLA Policy", "DocType", "Service SLA Policy", None),
			("Service Contract", "DocType", "Service Contract", None),
			("Service Revenue Schedule", "DocType", "Service Revenue Schedule", None),
		],
	),
	(
		"Service delivery",
		[
			("Service Portal", "Page", "service-portal", None),
			("Service Ticket", "DocType", "Service Ticket", None),
			("Service Timesheet", "DocType", "Service Timesheet", None),
			("Service Invoice", "DocType", "Service Invoice", None),
			("Service Escalation Rule", "DocType", "Service Escalation Rule", None),
		],
	),
	(
		"Finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
		],
	),
	(
		"Reports · Delivery & quality",
		[
			("SLA compliance", "Report", "SLA Compliance", "Service Ticket"),
			("Ticket backlog", "Report", "Ticket Backlog", "Service Ticket"),
			("CSAT summary", "Report", "Service CSAT Summary", "Service Ticket"),
		],
	),
	(
		"Reports · Revenue & utilisation",
		[
			("Revenue summary", "Report", "Service Revenue Summary", "Service Invoice"),
			("Timesheet hours", "Report", "Service Timesheet Hours Summary", "Service Timesheet"),
		],
	),
]

# Customer 360 → pipeline → service & marketing; analytics last (ISO-style CRM documentation).
CRM_DESK: list[DeskSection] = [
	(
		"Policy & access",
		[
			("Sales Settings", "DocType", "Omnexa Sales Settings", None),
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Customer 360",
		[
			("Customer Profile", "DocType", "Customer Profile", None),
			("CRM Interaction Log", "DocType", "CRM Interaction Log", None),
		],
	),
	(
		"Pipeline",
		[
			("CRM Lead", "DocType", "CRM Lead", None),
			("CRM Opportunity", "DocType", "CRM Opportunity", None),
		],
	),
	(
		"Service & marketing",
		[
			("CRM Case Ticket", "DocType", "CRM Case Ticket", None),
			("CRM Campaign", "DocType", "CRM Campaign", None),
		],
	),
	(
		"Reports · CRM analytics",
		[
			("Pipeline value", "Report", "CRM Pipeline Value", "CRM Opportunity"),
			("Case SLA compliance", "Report", "CRM Case SLA Compliance", "CRM Case Ticket"),
			("Customer revenue", "Report", "CRM Customer Revenue", "Customer Profile"),
		],
	),
]

# ISA-style engagement & evidence; IFRS financial-statement tie-out to trial balance, GL, and substantive balance review.
AUDIT_DESK: list[DeskSection] = [
	(
		"Policy & access",
		[
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Engagement & opinion",
		[
			("Audit Engagement", "DocType", "Audit Engagement", None),
			("Audit Opinion Draft", "DocType", "Audit Opinion Draft", None),
		],
	),
	(
		"Substantive balances",
		[
			("Audit Balance Snapshot", "DocType", "Audit Balance Snapshot", None),
		],
	),
	(
		"Evidence & findings",
		[
			("Audit Finding", "DocType", "Audit Finding", None),
			("Audit Evidence", "DocType", "Audit Evidence", None),
		],
	),
	(
		"Reports · IFRS statements & ledgers",
		[
			("Trial balance", "Report", "Trial Balance", "GL Account"),
			("Income statement", "Report", "Income Statement", "GL Account"),
			("Balance sheet", "Report", "Balance Sheet", "GL Account"),
			("Cash flow (structured)", "Report", "Cash Flow Statement (Structured)", "Journal Entry"),
			("General Ledger", "Report", "General Ledger", "Journal Entry"),
			("General Journal", "Report", "General Journal", "Journal Entry"),
			("Receivables aging", "Report", "Receivables Aging", "Sales Invoice"),
			("Payables aging", "Report", "Payables Aging", "Purchase Invoice"),
		],
	),
	(
		"Reports · Audit registers",
		[
			("Engagement summary", "Report", "Audit Engagement Summary", "Audit Engagement"),
			("Finding summary", "Report", "Audit Finding Summary", "Audit Finding"),
			("Evidence summary", "Report", "Audit Evidence Summary", "Audit Evidence"),
		],
	),
]

# GlobalG.A.P / traceability visibility, IFRS / IAS 41 biological-asset hooks, farm-to-fork operations & commercial bridge.
AGRICULTURE_DESK: list[DeskSection] = [
	(
		"Policy & access",
		[
			_DESK_ERP_SETTINGS_URL,
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Farm master & land",
		[
			("Farm", "DocType", "Farm", None),
			("Field Plot", "DocType", "Field Plot", None),
		],
	),
	(
		"Crop production",
		[
			("Crop Cycle", "DocType", "Crop Cycle", None),
		],
	),
	(
		"Livestock & herd health",
		[
			("Livestock Animal", "DocType", "Livestock Animal", None),
			("Vaccination Record", "DocType", "Vaccination Record", None),
		],
	),
	(
		"Harvest & post-harvest",
		[
			("Harvest Record", "DocType", "Harvest Record", None),
		],
	),
	(
		"Commercial integration",
		[
			("Customer", "DocType", "Customer", None),
			("Purchase Order", "DocType", "Purchase Order", None),
			("Sales Invoice", "DocType", "Sales Invoice", None),
		],
	),
	(
		"Reports · Yield, health & economics",
		[
			("Crop yield", "Report", "Crop Yield Report", "Harvest Record"),
			("Vaccination status", "Report", "Vaccination Status Report", "Vaccination Record"),
			("Farm cost & profitability", "Report", "Farm Cost Profitability", "Harvest Record"),
			("Global farm compliance", "Report", "Global Farm Compliance Summary", "Farm"),
		],
	),
]

# RIBA Plan of Work 2020 — keep in lockstep with
# ``omnexa_engineering_consulting/.../workspace/engineering_consulting/engineering_consulting.json`` ``links``.
# Control-tower sync replaces Workspace.links from this list; a short desk truncates the live workspace.
ENGINEERING_CONSULTING_DESK: list[DeskSection] = [
	(
		"Policy & access",
		[
			_DESK_ERP_SETTINGS_URL,
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Projects & PM",
		[
			("Project Contract", "DocType", "Project Contract", None),
			("PM Milestone", "DocType", "PM Milestone", None),
			("PM WBS Task", "DocType", "PM WBS Task", None),
			("Client Communication Log", "DocType", "Client Communication Log", None),
			("RIBA Sequence Policy", "DocType", "Engineering Project RIBA Sequence Policy", None),
		],
	),
	(
		"Design (RIBA 0–4)",
		[
			("Engineering Stage", "DocType", "Engineering Stage", None),
			("Engineering Submittal", "DocType", "Engineering Submittal", None),
			("Engineering Document Register", "DocType", "Engineering Document Register", None),
			("Engineering Document Transmittal", "DocType", "Engineering Document Transmittal", None),
			("Built Environment Code", "DocType", "Engineering Built Environment Code", None),
			("Document Issue Bundle", "DocType", "Engineering Document Issue Bundle", None),
			("Document Issue Template", "DocType", "Engineering Document Issue Template", None),
			("Document Edition Group", "DocType", "Engineering Document Edition Group", None),
			("PID Record (19650)", "DocType", "Engineering PID Record", None),
			("OIR Record", "DocType", "Engineering OIR Record", None),
			("AIR Record", "DocType", "Engineering AIR Record", None),
			("PIR Record", "DocType", "Engineering PIR Record", None),
			("Engineering Risk", "DocType", "Engineering Risk", None),
			("Engineering Change Request", "DocType", "Engineering Change Request", None),
			("Earned Value Entry", "DocType", "Engineering Earned Value Entry", None),
		],
	),
	(
		"RIBA register & quality",
		[
			("RIBA Stage Register", "Report", "RIBA Stage Register", "Engineering Stage"),
			("RIBA Project Coverage", "Report", "RIBA Project Coverage", "Engineering Stage"),
			("Design Delay Report", "Report", "Design Delay Report", "Engineering Stage"),
			("Consultant Workload Summary", "Report", "Consultant Workload Summary", "Engineering Stage"),
			("Engineering Review Workload", "Report", "Engineering Review Workload", "Engineering Stage"),
			("Engineering Risk Summary", "Report", "Engineering Risk Summary", "Engineering Risk"),
			("Engineering Change Request Summary", "Report", "Engineering Change Request Summary", "Engineering Change Request"),
			("Engineering Submittal SLA Watchlist", "Report", "Engineering Submittal SLA Watchlist", "Engineering Submittal"),
			("Escalation Policy", "DocType", "Engineering Escalation Policy", None),
		],
	),
	(
		"Standards & compliance toolkit",
		[
			("Engineering Standard Mapping", "DocType", "Engineering Standard Mapping", None),
			("Engineering Standard Crosswalk", "DocType", "Engineering Standard Crosswalk", None),
			("Engineering Compliance Rule", "DocType", "Engineering Compliance Rule", None),
			("Engineering Compliance Overview", "Report", "Engineering Compliance Overview", "Engineering Standard Mapping"),
			("Engineering Project Compliance Snapshot", "Report", "Engineering Project Compliance Snapshot", "Engineering Project Compliance Profile"),
			("Engineering Site Observation Dashboard", "Report", "Engineering Site Observation Dashboard", "Engineering Site Observation"),
			("Engineering Regulatory Profile", "DocType", "Engineering Regulatory Profile", None),
			("Engineering Project Compliance Profile", "DocType", "Engineering Project Compliance Profile", None),
			("Engineering Consulting Settings", "DocType", "Engineering Consulting Settings", None),
			("Engineering Portal Membership", "DocType", "Engineering Portal Membership", None),
		],
	),
	(
		"Site & handover (RIBA 5–7)",
		[
			("Engineering Site Record", "DocType", "Engineering Site Record", None),
			("Engineering Site Observation", "DocType", "Engineering Site Observation", None),
			("Engineering Site Incident", "DocType", "Engineering Site Incident", None),
			("Engineering Handover Certificate", "DocType", "Engineering Handover Certificate", None),
			("Engineering Supervision Register", "Report", "Engineering Supervision Register", "Engineering Site Record"),
			("CDM Site Risk Register", "DocType", "Engineering CDM Site Risk Register", None),
			("Statutory Payment Certificate", "DocType", "Engineering Statutory Payment Certificate", None),
			("Contract Workflow Binding", "DocType", "Engineering Contract Workflow Binding", None),
			("CDE Provider", "DocType", "Engineering CDE Provider", None),
			("Legal Signature Event", "DocType", "Engineering Legal Signature Event", None),
			("Site communication", "DocType", "Client Communication Log", None),
		],
	),
	(
		"External & integration",
		[
			("Consultant Engagement", "DocType", "Engineering Consultant Engagement", None),
			("CDE Webhook Log", "DocType", "Engineering CDE Webhook Log", None),
			("Purchase Order", "DocType", "Purchase Order", None),
			("Supplier", "DocType", "Supplier", None),
		],
	),
	(
		"Construction",
		[
			("BOQ Item", "DocType", "BOQ Item", None),
			("IPC Certificate", "DocType", "IPC Certificate", None),
		],
	),
]

# EPC / infrastructure: contract & BOQ → site → change/claims → IPC & WIP → procurement; IFRS 15 / IAS 11–style visibility.
CONSTRUCTION_DESK: list[DeskSection] = [
	(
		"Policy & organisation",
		[
			_DESK_ERP_SETTINGS_URL,
			("User Branch Access", "DocType", "User Branch Access", None),
		],
	),
	(
		"Contracts & scope",
		[
			("Project Contract", "DocType", "Project Contract", None),
			("BOQ Item", "DocType", "BOQ Item", None),
		],
	),
	(
		"Schedule",
		[
			("PM WBS Task", "DocType", "PM WBS Task", None),
		],
	),
	(
		"Site operations",
		[
			("Site Daily Report", "DocType", "Site Daily Report", None),
			("Subcontract Work Order", "DocType", "Subcontract Work Order", None),
		],
	),
	(
		"Change, time & claims",
		[
			("Construction Change Order", "DocType", "Construction Change Order", None),
			("Extension of Time (EOT)", "DocType", "Construction Extension of Time", None),
			("Construction Claim", "DocType", "Construction Claim", None),
		],
	),
	(
		"Billing & WIP",
		[
			("IPC Certificate", "DocType", "IPC Certificate", None),
			("Subcontract Payment Certificate", "DocType", "Subcontract Payment Certificate", None),
			("Project WIP Snapshot", "DocType", "Project WIP Snapshot", None),
		],
	),
	(
		"Procurement",
		[
			("Purchase Order", "DocType", "Purchase Order", None),
			("Supplier", "DocType", "Supplier", None),
		],
	),
	(
		"Engineering (RIBA)",
		[
			("Engineering Stage", "DocType", "Engineering Stage", None),
			("Engineering Submittal", "DocType", "Engineering Submittal", None),
		],
	),
	(
		"Finance",
		[
			("Journal Entry", "DocType", "Journal Entry", None),
		],
	),
	(
		"Reports · Contract & cost",
		[
			("BOQ progress", "Report", "BOQ Progress", "BOQ Item"),
			("BOQ cost overrun", "Report", "BOQ Cost Overrun", "BOQ Item"),
			("Contract control", "Report", "Construction Contract Control", "Project Contract"),
			("International contract summary", "Report", "Construction Contract International Summary", "Project Contract"),
			("Project profitability", "Report", "Project Profitability (Construction)", "Project Contract"),
		],
	),
	(
		"Reports · Applications & billing",
		[
			("IPC summary", "Report", "IPC Certificate Summary", "IPC Certificate"),
		],
	),
]

_BY_WORKSPACE: dict[str, list[DeskSection]] = {
	"Sell": SELL_DESK,
	"Buy": BUY_DESK,
	"Stock": STOCK_DESK,
	"Accounting": ACCOUNTING_DESK,
	"Settings": SETTINGS_DESK,
	"settings": SETTINGS_DESK,
	"Governance": GOVERNANCE_DESK,
	"Fixed Assets": FIXED_ASSETS_DESK,
	"Fixed assets": FIXED_ASSETS_DESK,
	"fixed-assets": FIXED_ASSETS_DESK,
	"fixed_assets": FIXED_ASSETS_DESK,
	"Asset Insurance": ASSET_INSURANCE_DESK,
	"asset insurance": ASSET_INSURANCE_DESK,
	"asset-insurance": ASSET_INSURANCE_DESK,
	"asset_insurance": ASSET_INSURANCE_DESK,
	"Tourism": TOURISM_DESK,
	"tourism": TOURISM_DESK,
	"omnexa_tourism": TOURISM_DESK,
	"Healthcare": HEALTHCARE_DESK,
	"healthcare": HEALTHCARE_DESK,
	"omnexa_healthcare": HEALTHCARE_DESK,
	"Education": EDUCATION_DESK,
	"education": EDUCATION_DESK,
	"omnexa_education": EDUCATION_DESK,
	"Nursery": NURSE_DESK,
	"nursery": NURSE_DESK,
	"omnexa_nursery": NURSE_DESK,
	"Manufacturing": MANUFACTURING_DESK,
	"manufacturing": MANUFACTURING_DESK,
	"omnexa_manufacturing": MANUFACTURING_DESK,
	"Car Rental": CAR_RENTAL_DESK,
	"car-rental": CAR_RENTAL_DESK,
	"car rental": CAR_RENTAL_DESK,
	"CarRental": CAR_RENTAL_DESK,
	"car_rental": CAR_RENTAL_DESK,
	"omnexa_car_rental": CAR_RENTAL_DESK,
	"Trading": TRADING_DESK,
	"trading": TRADING_DESK,
	"omnexa_trading": TRADING_DESK,
	"Restaurant": RESTAURANT_DESK,
	"restaurant": RESTAURANT_DESK,
	"food-service": RESTAURANT_DESK,
	"food_service": RESTAURANT_DESK,
	"Services": SERVICES_DESK,
	"services": SERVICES_DESK,
	"professional-services": SERVICES_DESK,
	"professional_services": SERVICES_DESK,
	"field-service": SERVICES_DESK,
	"field_service": SERVICES_DESK,
	"Construction": CONSTRUCTION_DESK,
	"construction": CONSTRUCTION_DESK,
	"epc": CONSTRUCTION_DESK,
	"infrastructure": CONSTRUCTION_DESK,
	"HR": HR_DESK,
	"hr": HR_DESK,
	"human-resources": HR_DESK,
	"human_resources": HR_DESK,
	"Projects PM": PROJECTS_DESK,
	"projects": PROJECTS_DESK,
	"Projects": PROJECTS_DESK,
	"project-management": PROJECTS_DESK,
	"project_management": PROJECTS_DESK,
	"pmo": PROJECTS_DESK,
	"projects-pm": PROJECTS_DESK,
	"engineering-consulting": ENGINEERING_CONSULTING_DESK,
	"Engineering Consulting": ENGINEERING_CONSULTING_DESK,
	"engineering_consulting": ENGINEERING_CONSULTING_DESK,
	"riba": ENGINEERING_CONSULTING_DESK,
	"RIBA": ENGINEERING_CONSULTING_DESK,
	"Agriculture": AGRICULTURE_DESK,
	"agriculture": AGRICULTURE_DESK,
	"Audit": AUDIT_DESK,
	"audit": AUDIT_DESK,
	"CRM": CRM_DESK,
	"crm": CRM_DESK,
	"customer-core": CRM_DESK,
	"customer_core": CRM_DESK,
}

# Normalize titles/labels from sites that renamed workspaces or use Arabic titles in `name`.
_DESK_NAME_ALIASES: dict[str, str] = {
	"fixed assets": "Fixed Assets",
	"omnexa fixed assets": "Fixed Assets",
	"asset insurance": "Asset Insurance",
	"تأمين الأصول": "Asset Insurance",
	"sell": "Sell",
	"buy": "Buy",
	"stock": "Stock",
	"accounting": "Accounting",
	"settings": "Settings",
	"governance": "Governance",
}


def _normalize_desk_workspace_key(name: str) -> str:
	return " ".join((name or "").strip().lower().replace("_", " ").replace("-", " ").split())


def get_desk_sections_for_workspace(workspace_name: str) -> list[DeskSection] | None:
	if not workspace_name:
		return None
	raw = workspace_name.strip()
	if raw in _BY_WORKSPACE:
		return _BY_WORKSPACE[raw]
	nk = _normalize_desk_workspace_key(raw)
	mapped = _DESK_NAME_ALIASES.get(nk)
	if mapped and mapped in _BY_WORKSPACE:
		return _BY_WORKSPACE[mapped]
	for k, sections in _BY_WORKSPACE.items():
		if _normalize_desk_workspace_key(k) == nk:
			return sections
	return None


def resolve_desk_sections_for_workspace_doc(ws) -> list[DeskSection] | None:
	"""Like :func:`get_desk_sections_for_workspace` but also tries ``title`` / ``label`` on the doc."""
	for candidate in (
		getattr(ws, "name", None),
		getattr(ws, "title", None),
		getattr(ws, "label", None),
	):
		if not candidate:
			continue
		sections = get_desk_sections_for_workspace(str(candidate).strip())
		if sections:
			return sections
	return None
