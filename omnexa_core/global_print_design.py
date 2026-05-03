"""Global print design system bootstrap for ERPGENEX.

Applies one default Print Style + Print Settings so all modules/reports inherit
consistent print/PDF behavior without per-doctype manual setup.
"""

from __future__ import annotations

import frappe

GLOBAL_PRINT_STYLE_NAME = "ERPGENEX Global Unified"
DEFAULT_PRINT_FORMAT_PREFIX = "ERPGENEX Default - "

GLOBAL_PRINT_CSS = """
@page {
	size: A4 portrait;
	margin-top: 20mm;
	margin-right: 12mm;
	margin-bottom: 18mm;
	margin-left: 12mm;
}

html, body {
	font-family: "Inter", "Cairo", "Noto Sans", "Helvetica Neue", Arial, sans-serif;
	font-size: 11px;
	line-height: 1.45;
	color: #1E293B;
	-webkit-print-color-adjust: exact !important;
	print-color-adjust: exact !important;
}

.print-format {
	color: #1E293B;
}

.print-format h1, .print-format h2, .print-format h3, .print-format h4 {
	color: #0F3D75;
	font-weight: 700;
}

.print-format h1 { font-size: 20px; }
.print-format h2 { font-size: 17px; }
.print-format h3 { font-size: 14px; }

.print-format small, .print-format .small, .text-muted {
	color: #5A6B85 !important;
	font-size: 9px;
}

.print-format .table {
	width: 100%;
	border-collapse: separate;
	border-spacing: 0;
	border: 1px solid #D9E1EC;
	border-radius: 8px;
	overflow: hidden;
}

.print-format .table > thead > tr > th {
	background: #F8FAFC;
	color: #0F3D75;
	font-weight: 600;
	border-bottom: 1px solid #D9E1EC;
	padding: 8px 10px;
}

.print-format .table > tbody > tr > td {
	padding: 8px 10px;
	border-top: 1px solid #EDF2F7;
}

.print-format .table > tbody > tr:nth-child(even) > td {
	background: #FBFDFF;
}

.print-format .total-row td,
.print-format .grand-total td {
	font-weight: 700;
	background: #F8FAFC;
}

.print-format hr {
	border: 0;
	border-top: 1px solid #D9E1EC;
	margin: 8px 0 12px;
}

.print-format .text-right { text-align: right !important; }
.print-format .text-left { text-align: left !important; }

.print-format [dir="rtl"], [dir="rtl"] .print-format {
	direction: rtl;
}

.print-format [dir="ltr"], [dir="ltr"] .print-format {
	direction: ltr;
}
"""


DEFAULT_PRINT_DOCTYPES = (
	# Sales
	"Sales Quotation",
	"Sales Order",
	"Delivery Note",
	"Sales Invoice",
	"Payment Entry",
	# Purchase
	"Purchase Request",
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
	# Inventory
	"Item",
	"Warehouse",
	"Stock Entry",
	"Stock Reconciliation",
	# Accounting
	"Journal Entry",
	"Bank Transaction",
	"Fiscal Year",
	# HR / Payroll
	"Employee",
	"HR Attendance",
	"HR Salary Slip",
	"HR Payroll Entry",
	"HR Payroll Run",
)


def _ensure_default_print_format_for_doctype(doctype: str) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	meta = frappe.get_meta(doctype)
	if meta.istable or meta.issingle:
		return

	format_name = f"{DEFAULT_PRINT_FORMAT_PREFIX}{doctype}"
	existing = frappe.db.get_value("Print Format", {"name": format_name}, "name")
	if not existing:
		doc = frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": format_name,
				"doc_type": doctype,
				"custom_format": 0,
				"standard": "No",
				"disabled": 0,
				"print_format_type": "Jinja",
				"margin_top": 20,
				"margin_bottom": 18,
				"margin_left": 12,
				"margin_right": 12,
				"font": "Inter",
				"font_size": 11,
			}
		)
		doc.insert(ignore_permissions=True)

	# Force default print format to the global one for unified rollout.
	frappe.db.set_value("DocType", doctype, "default_print_format", format_name, update_modified=False)


def ensure_default_print_formats() -> None:
	"""Create and assign ERPGENEX default print formats across core business doctypes."""
	if not frappe.db.exists("DocType", "Print Format"):
		return
	for dt in DEFAULT_PRINT_DOCTYPES:
		try:
			_ensure_default_print_format_for_doctype(dt)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: ensure default print format for {dt}")


def ensure_global_print_design_system() -> None:
	"""Create/update a global print style and set it as site default."""
	if not frappe.db.exists("DocType", "Print Style") or not frappe.db.exists("DocType", "Print Settings"):
		return

	style_name = frappe.db.get_value("Print Style", {"print_style_name": GLOBAL_PRINT_STYLE_NAME}, "name")
	if style_name:
		frappe.db.set_value("Print Style", style_name, "css", GLOBAL_PRINT_CSS, update_modified=False)
		frappe.db.set_value("Print Style", style_name, "disabled", 0, update_modified=False)
	else:
		style_doc = frappe.get_doc(
			{
				"doctype": "Print Style",
				"print_style_name": GLOBAL_PRINT_STYLE_NAME,
				"css": GLOBAL_PRINT_CSS,
				"disabled": 0,
			}
		)
		style_doc.insert(ignore_permissions=True)
		style_name = style_doc.name

	settings = frappe.get_single("Print Settings")
	settings.print_style = style_name
	settings.pdf_page_size = "A4"
	settings.repeat_header_footer = 1
	settings.send_print_as_pdf = 1
	settings.with_letterhead = 1
	settings.allow_page_break_inside_tables = 0
	settings.font = "Inter"
	settings.font_size = 9
	settings.save(ignore_permissions=True)
	ensure_default_print_formats()
