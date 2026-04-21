# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint, flt
from frappe.utils import get_bench_path
from frappe.utils.file_manager import save_file


def after_install():
	ensure_omnexa_roles()
	apply_default_branding()


def after_migrate():
	ensure_omnexa_roles()
	apply_default_branding()
	ensure_global_supporting_attachment_fields()
	remove_legacy_people_workspace()
	remove_legacy_finance_workspace()
	try:
		from omnexa_core.omnexa_core.workspace_control_tower import (
			prune_invalid_workspace_kpi_artifacts,
			sync_all_workspace_kpi_layout,
		)

		prune_invalid_workspace_kpi_artifacts()
		sync_all_workspace_kpi_layout()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: sync_all_workspace_kpi_layout")
	try:
		from omnexa_core.workspace_onboarding_sync import enable_onboarding_setting, sync_workspace_database

		enable_onboarding_setting()
		sync_workspace_database()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: workspace onboarding sync")


def remove_legacy_people_workspace():
	"""Single HR desk: drop duplicate Omnexa Core workspace `People` (use `/app/hr`)."""
	if not frappe.db.exists("Workspace", "People"):
		return
	try:
		frappe.delete_doc("Workspace", "People", force=1, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: remove_legacy_people_workspace")


def remove_legacy_finance_workspace():
	"""Single finance desk: `Finance` duplicated links already on Accounting (`/app/accounting`)."""
	if not frappe.db.exists("Workspace", "Finance"):
		return
	try:
		frappe.delete_doc("Workspace", "Finance", force=1, ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: remove_legacy_finance_workspace")


def ensure_omnexa_roles():
	"""Create baseline roles referenced by Omnexa Core DocTypes (see Docs/specs)."""
	for role_name in ("Company Admin", "Tax Integration"):
		if frappe.db.exists("Role", role_name):
			continue
		doc = frappe.new_doc("Role")
		doc.role_name = role_name
		doc.desk_access = 1
		doc.is_custom = 1
		doc.insert(ignore_permissions=True)


def apply_default_branding():
	"""Set ErpGenEx logo as default desk logo after install/migrate."""
	logo_path = Path(get_bench_path()) / "Docs" / "logo" / "logo.png"
	if not logo_path.exists():
		return

	file_name = "erpgenex-logo.png"
	file_url = f"/files/{file_name}"

	# Ensure a public File exists for the logo.
	if not frappe.db.exists("File", {"file_url": file_url}):
		save_file(
			file_name,
			logo_path.read_bytes(),
			"Navbar Settings",
			"Navbar Settings",
			is_private=0,
		)

	try:
		frappe.db.set_single_value("Navbar Settings", "app_logo", file_url)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: set navbar app_logo")


def setup_wizard_create_core_masters(args):
	"""Create company, head branch, tax baseline, and starter CoA from setup wizard."""
	if not isinstance(args, dict):
		args = {}

	company_name = (args.get("omnexa_company_name") or args.get("company_name") or "").strip()
	company_abbr = (args.get("omnexa_company_abbr") or args.get("company_abbr") or "").strip().upper()
	branch_name = (args.get("omnexa_main_branch_name") or "").strip()
	branch_code = (args.get("omnexa_main_branch_code") or "").strip().upper()
	tax_id = (args.get("omnexa_tax_id") or "").strip()
	default_vat_rate = flt(args.get("omnexa_default_vat_rate") or 0)
	enable_starter_coa = cint(args.get("omnexa_enable_starter_coa") or 0)

	# Keep setup wizard resilient even if user skips the custom slide.
	if not company_name:
		company_name = "My Company"
	if not company_abbr:
		company_abbr = "".join(ch for ch in company_name if ch.isalnum())[:4].upper() or "COMP"
	if not branch_name:
		branch_name = "Main Branch"
	if not branch_code:
		branch_code = "MAIN"

	currency = (args.get("currency") or "USD").strip() or "USD"
	country = (args.get("country") or "Egypt").strip() or "Egypt"

	company = _ensure_company(company_name, company_abbr, currency, country, tax_id)
	_ensure_branch(company, branch_name, branch_code, tax_id)
	_ensure_tax_accounts(company, default_vat_rate)
	if enable_starter_coa:
		_ensure_starter_chart_of_accounts(company)


def _ensure_company(company_name, company_abbr, currency, country, tax_id):
	existing = frappe.db.get_value("Company", {"abbr": company_abbr}, "name")
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": company_name,
			"abbr": company_abbr,
			"status": "Active",
			"default_currency": currency,
			"country": country,
			"tax_id": tax_id,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_branch(company, branch_name, branch_code, tax_id):
	branch_docname = f"{company}-{branch_code}"
	if frappe.db.exists("Branch", branch_docname):
		return branch_docname

	doc = frappe.get_doc(
		{
			"doctype": "Branch",
			"branch_name": branch_name,
			"branch_code": branch_code,
			"status": "Active",
			"company": company,
			"is_head_office": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	if tax_id and frappe.db.has_column("Branch", "tax_id"):
		frappe.db.set_value("Branch", doc.name, "tax_id", tax_id, update_modified=False)
	return doc.name


def _ensure_tax_accounts(company, default_vat_rate):
	_ensure_gl_account(company, "2200", "Tax Payable (Output VAT)", "Liability")
	_ensure_gl_account(company, "1400", "Tax Receivable (Input VAT)", "Asset")

	if frappe.db.has_single("Omnexa Core Settings"):
		try:
			frappe.db.set_single_value("Omnexa Core Settings", "default_vat_rate", default_vat_rate or 0)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Omnexa: set default VAT rate")


def _ensure_starter_chart_of_accounts(company):
	root_assets = _ensure_gl_account(company, "1000", "Assets", "Asset", is_group=1)
	root_liabilities = _ensure_gl_account(company, "2000", "Liabilities", "Liability", is_group=1)
	root_equity = _ensure_gl_account(company, "3000", "Equity", "Equity", is_group=1)
	root_income = _ensure_gl_account(company, "4000", "Income", "Income", is_group=1)
	root_expense = _ensure_gl_account(company, "5000", "Expenses", "Expense", is_group=1)

	_ensure_gl_account(company, "1100", "Cash", "Asset", parent_account=root_assets)
	_ensure_gl_account(company, "1200", "Accounts Receivable", "Asset", parent_account=root_assets)
	_ensure_gl_account(company, "2100", "Accounts Payable", "Liability", parent_account=root_liabilities)
	_ensure_gl_account(company, "3100", "Owner Equity", "Equity", parent_account=root_equity)
	_ensure_gl_account(
		company,
		"4100",
		"Sales Revenue",
		"Income",
		parent_account=root_income,
		pl_bucket="Revenue",
	)
	_ensure_gl_account(
		company,
		"5100",
		"Operating Expenses",
		"Expense",
		parent_account=root_expense,
		pl_bucket="Operating Expense",
	)


def _ensure_gl_account(
	company,
	account_number,
	account_name,
	account_type,
	parent_account=None,
	is_group=0,
	pl_bucket=None,
):
	existing = frappe.db.get_value(
		"GL Account",
		{"company": company, "account_number": account_number},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "GL Account",
			"company": company,
			"account_number": account_number,
			"account_name": account_name,
			"account_type": account_type,
			"is_group": cint(is_group),
			"parent_account": parent_account,
			"pl_bucket": pl_bucket,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _last_insert_anchor_fieldname(doctype: str):
	"""Stable anchor at end of form (avoids insert_after on removed layout-only sections)."""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return None
	for df in reversed(meta.fields or []):
		if not df.fieldname or df.fieldtype in ("Tab Break", "Section Break", "Column Break"):
			continue
		return df.fieldname
	return None


def ensure_global_supporting_attachment_fields():
	"""Add a clear attachment area to Omnexa primary DocTypes (non-child, non-single)."""
	try:
		doctypes = frappe.get_all(
			"DocType",
			filters={
				"module": ["like", "Omnexa%"],
				"istable": 0,
				"issingle": 0,
			},
			pluck="name",
		)
		if not doctypes:
			return

		custom_fields_map = {}
		for dt in doctypes:
			anchor = _last_insert_anchor_fieldname(dt)
			if not anchor:
				continue
			custom_fields_map[dt] = [
				{
					"fieldname": "attachments_section",
					"label": "Attachments",
					"fieldtype": "Section Break",
					"insert_after": anchor,
				},
				{
					"fieldname": "supporting_attachment",
					"label": "Supporting Attachment",
					"fieldtype": "Attach",
					"insert_after": "attachments_section",
				},
			]

		create_custom_fields(custom_fields_map, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure_global_supporting_attachment_fields")
