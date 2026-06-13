# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Retail / counter POS — catalog, draft Sales Invoice cart, checkout."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, get_fullname, nowdate, nowtime

from omnexa_core.omnexa_core.retail_pos_invoicing import (
	dispatch_einvoice_for_sales_invoice,
	ensure_walkin_customer,
	get_einvoice_receipt_context,
	resolve_pos_profile,
	resolve_retail_pos_company_branch,
	resolve_retail_pos_eta_billing_type,
)

CATEGORY_LABELS: dict[str, str] = {
	"Traditional Product": "منتجات",
	"Service": "خدمات",
	"Consumable": "مستهلكات",
	"Kit": "باندل",
	"Raw Material": "خامات",
}

ITEM_GRADIENTS = (
	"linear-gradient(135deg,#d4fc79,#96e6a1)",
	"linear-gradient(135deg,#a8edea,#fed6e3)",
	"linear-gradient(135deg,#ffecd2,#fcb69f)",
	"linear-gradient(135deg,#a1c4fd,#c2e9fb)",
)

_DEMO_ITEM_PREFIXES = ("SIM-", "DEMO-", "OMNEXA-DEMO", "TEST-")


def _is_pos_demo_item(row: dict[str, Any]) -> bool:
	code = (row.get("item_code") or row.get("name") or "").strip().upper()
	name = (row.get("item_name") or "").strip().upper()
	if any(code.startswith(prefix) for prefix in _DEMO_ITEM_PREFIXES):
		return True
	if "SIMULATION" in name or name.startswith("DEMO "):
		return True
	return False


def _item_has_show_in_retail_pos_field() -> bool:
	return bool(frappe.get_meta("Item").has_field("show_in_retail_pos"))


def _item_visible_in_pos(row: dict[str, Any]) -> bool:
	if _is_pos_demo_item(row):
		return False
	if _item_has_show_in_retail_pos_field():
		return bool(cint(row.get("show_in_retail_pos")))
	return bool(cint(row.get("is_sales_item")))


def _pos_product_type_rows() -> list[dict[str, Any]]:
	if frappe.db.exists("DocType", "Product Type"):
		return frappe.get_all(
			"Product Type",
			filters={"disabled": 0, "show_in_pos": 1},
			fields=["product_type_name", "pos_label", "sort_order"],
			order_by="sort_order asc, product_type_name asc",
		)
	return [
		{
			"product_type_name": key,
			"pos_label": label,
			"sort_order": idx * 10,
		}
		for idx, (key, label) in enumerate(CATEGORY_LABELS.items(), 1)
	]


def _pos_category_label(product_type: str | None) -> str:
	product_type = product_type or "Traditional Product"
	if frappe.db.exists("DocType", "Product Type"):
		label = frappe.db.get_value("Product Type", product_type, "pos_label")
		if label:
			return label
	return CATEGORY_LABELS.get(product_type, product_type or "أخرى")


def _pos_visible_product_types() -> set[str]:
	return {row["product_type_name"] for row in _pos_product_type_rows()}


def _pos_category_filters() -> tuple[list[str], dict[str, str], dict[str, str]]:
	rows = _pos_product_type_rows()
	labels = [row["pos_label"] for row in rows]
	label_to_type = {row["pos_label"]: row["product_type_name"] for row in rows}
	type_to_label = {row["product_type_name"]: row["pos_label"] for row in rows}
	return labels, label_to_type, type_to_label


def _branch_address_line(branch: str | None) -> str:
	if not branch:
		return ""
	meta = frappe.get_meta("Branch")
	parts: list[str] = []
	for fieldname in (
		"eta_address_street",
		"eta_address_city",
		"eta_address_governate",
		"eta_address_country",
		"zatca_street",
		"zatca_city",
		"zatca_district",
	):
		if not meta.has_field(fieldname):
			continue
		value = (frappe.db.get_value("Branch", branch, fieldname) or "").strip()
		if value:
			parts.append(value)
	return ", ".join(dict.fromkeys(parts))


def _company_receipt_context(company: str | None) -> dict[str, str]:
	if not company:
		return {
			"store_name_ar": "سوبر ماركت الخير",
			"store_name_en": "AL-KHAIR SUPERMARKET",
			"address": "",
			"phone": "",
			"cr_number": "",
			"tax_id": "",
		}
	doc = frappe.get_cached_doc("Company", company)
	meta = frappe.get_meta("Company")
	phone = ""
	for fieldname in ("phone_no", "phone", "mobile_no", "company_phone"):
		if meta.has_field(fieldname):
			phone = (doc.get(fieldname) or "").strip()
			if phone:
				break
	cr_number = ""
	for fieldname in ("rin", "registration_details", "company_registration", "tax_id"):
		if meta.has_field(fieldname):
			cr_number = (doc.get(fieldname) or "").strip()
			if cr_number:
				break
	tax_id = (doc.get("tax_id") or cr_number or "").strip() if meta.has_field("tax_id") else cr_number
	return {
		"store_name_ar": (doc.get("company_name") or company).strip(),
		"store_name_en": (doc.get("abbr") or company).strip(),
		"address": (doc.get("country") or "").strip(),
		"phone": phone,
		"cr_number": cr_number,
		"tax_id": tax_id,
	}


def _pos_discount_key(invoice_name: str) -> str:
	return f"retail_pos_discount:{invoice_name}"


def _item_selling_rate(item_code: str) -> float:
	std = frappe.db.get_value("Item", item_code, "standard_selling_rate")
	if std and flt(std) > 0:
		return flt(std)
	rate = frappe.db.sql(
		"""
		SELECT rate FROM `tabSales Invoice Item`
		WHERE item_code = %s AND rate > 0
		ORDER BY modified DESC LIMIT 1
		""",
		(item_code,),
	)
	if rate:
		return flt(rate[0][0])
	return 0.0


def _resolve_item(barcode_or_code: str) -> str | None:
	term = (barcode_or_code or "").strip()
	if not term:
		return None
	if frappe.db.exists("Item", term):
		return term
	by_code = frappe.db.get_value("Item", {"item_code": term, "disabled": 0}, "name")
	if by_code:
		return by_code
	barcode = frappe.db.get_value("Item", {"barcode": term, "disabled": 0}, "name")
	if barcode:
		return barcode
	match = frappe.db.get_value(
		"Item",
		{"item_name": ["like", f"%{term}%"], "disabled": 0, "is_sales_item": 1},
		"name",
	)
	return match


def _user_can_edit_pos_price(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	roles = set(frappe.get_roles(user))
	return bool(roles & {"System Manager", "Accounts Manager", "Sales Manager"})


def _serialize_item(row: dict[str, Any]) -> dict[str, Any]:
	code = row.get("name") or row.get("item_code")
	rate = _item_selling_rate(code)
	idx = sum(ord(c) for c in (code or "")) % len(ITEM_GRADIENTS)
	barcode = row.get("barcode") or ""
	return {
		"item_code": code,
		"item_name": row.get("item_name"),
		"barcode": barcode,
		"product_type": row.get("product_type") or "Traditional Product",
		"category_label": _pos_category_label(row.get("product_type")),
		"rate": rate,
		"stock_qty": flt(row.get("current_stock_qty")),
		"image_style": ITEM_GRADIENTS[idx],
	}


def _invoice_financials(invoice, discount: float = 0) -> dict[str, float]:
	subtotal = flt(invoice.net_total)
	discount = flt(discount)
	after_discount = flt(subtotal - discount, 2)
	tax = flt(invoice.tax_total or 0)
	if subtotal and discount:
		tax = flt(tax * (after_discount / subtotal), 2)
		grand = flt(after_discount + tax, 2)
	else:
		grand = flt(invoice.grand_total)
	return {
		"subtotal": subtotal,
		"discount": discount,
		"after_discount": after_discount,
		"tax": tax,
		"grand_total": grand,
	}


def _line_item_name(row) -> str:
	name = getattr(row, "item_name", None)
	if name:
		return name
	code = row.item or row.item_code
	if not code:
		return ""
	return frappe.db.get_value("Item", code, "item_name") or code


def _serialize_invoice(invoice_name: str) -> dict[str, Any]:
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	discount = flt(frappe.cache().get_value(_pos_discount_key(invoice_name)) or 0)
	items = []
	for row in invoice.items:
		items.append(
			{
				"row_name": row.name,
				"item_code": row.item_code,
				"item_name": _line_item_name(row),
				"qty": flt(row.qty),
				"rate": flt(row.rate),
				"amount": flt(row.amount),
			}
		)
	fin = _invoice_financials(invoice, discount)
	return {
		"invoice_name": invoice.name,
		"display_number": (invoice.name or "").split("-")[-1],
		"customer": invoice.customer,
		"items": items,
		"items_count": len(items),
		"cashier": get_fullname(invoice.owner),
		"status": invoice.docstatus,
		**fin,
	}


@frappe.whitelist()
def get_retail_pos_session():
	return {
		"can_edit_price": _user_can_edit_pos_price(),
		"user": frappe.session.user,
		"roles": frappe.get_roles(),
	}


@frappe.whitelist()
def get_retail_catalog(category: str | None = None, search: str | None = None):
	company, _branch = resolve_retail_pos_company_branch()
	visible_types = _pos_visible_product_types()
	filters: dict[str, Any] = {"disabled": 0, "company": company}
	if visible_types:
		filters["product_type"] = ["in", list(visible_types)]
	if _item_has_show_in_retail_pos_field():
		filters["show_in_retail_pos"] = 1
	else:
		filters["is_sales_item"] = 1
	if category and category not in ("All", "الكل"):
		_labels, label_to_type, _type_to_label = _pos_category_filters()
		pt = label_to_type.get(category)
		if not pt:
			rev = {v: k for k, v in CATEGORY_LABELS.items()}
			pt = rev.get(category) or category
		if pt in visible_types or pt in CATEGORY_LABELS:
			filters["product_type"] = pt
	fields = ["name", "item_code", "item_name", "product_type", "current_stock_qty", "is_sales_item"]
	if _item_has_show_in_retail_pos_field():
		fields.append("show_in_retail_pos")
	if frappe.get_meta("Item").has_field("barcode"):
		fields.append("barcode")
	rows = frappe.get_all(
		"Item",
		filters=filters,
		fields=fields,
		order_by="item_name asc",
		limit_page_length=500,
	)
	if search:
		term = search.strip().lower()
		rows = [
			r
			for r in rows
			if term in (r.item_name or "").lower()
			or term in (r.item_code or "").lower()
			or term in (r.name or "").lower()
			or term in ((r.get("barcode") or "")).lower()
		]
	category_labels, _label_to_type, _type_to_label = _pos_category_filters()
	categories = ["الكل"] + category_labels
	items = [
		_serialize_item(r)
		for r in rows
		if (not visible_types or r.get("product_type") in visible_types) and _item_visible_in_pos(r)
	]
	by_cat: dict[str, list[dict]] = {}
	for item in items:
		by_cat.setdefault(item["category_label"], []).append(item)
	return {"categories": categories, "items": items, "items_by_category": by_cat}


@frappe.whitelist()
def get_open_retail_pos_invoices():
	return frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 0, "is_pos": 1},
		fields=["name", "customer", "grand_total", "modified"],
		order_by="modified desc",
		limit_page_length=20,
	)


@frappe.whitelist()
def create_retail_pos_invoice(customer: str | None = None):
	company, branch = resolve_retail_pos_company_branch()
	profile = resolve_pos_profile(company, branch)
	inv = frappe.new_doc("Sales Invoice")
	inv.company = company
	inv.branch = branch
	inv.customer = customer or ensure_walkin_customer(company)
	inv.posting_date = nowdate()
	inv.due_date = nowdate()
	inv.is_pos = 1
	if profile:
		inv.pos_profile = profile
	if inv.meta.has_field("eta_billing_type"):
		inv.eta_billing_type = resolve_retail_pos_eta_billing_type(branch)
	inv.flags.ignore_permissions = True
	inv.insert(ignore_mandatory=True)
	frappe.cache().set_value(_pos_discount_key(inv.name), 0)
	return _serialize_invoice(inv.name)


@frappe.whitelist()
def get_retail_pos_invoice_detail(invoice_name: str):
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Invoice not found."))
	return _serialize_invoice(invoice_name)


@frappe.whitelist()
def add_item_to_retail_pos(invoice_name: str, item_code: str, qty: float | int = 1, rate: float | int | None = None):
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	if invoice.docstatus != 0:
		frappe.throw(_("Invoice is already submitted."))
	code = _resolve_item(item_code) or item_code
	if not frappe.db.exists("Item", code):
		frappe.throw(_("Item not found."))
	item = frappe.get_doc("Item", code)
	if item.company != invoice.company:
		frappe.throw(
			_("Item {0} belongs to a different company than this invoice.").format(item.item_code or code),
			title=_("Item"),
		)
	if _item_has_show_in_retail_pos_field() and not cint(item.show_in_retail_pos):
		frappe.throw(_("Item is not enabled for Retail POS."), title=_("Item"))
	elif not _item_has_show_in_retail_pos_field() and not item.is_sales_item:
		frappe.throw(_("Item is not enabled for sales."))
	if _is_pos_demo_item({"item_code": item.item_code, "item_name": item.item_name, "name": item.name}):
		frappe.throw(_("Demo/simulation items cannot be sold from Retail POS."), title=_("Item"))
	qty = flt(qty or 1)
	if qty <= 0:
		frappe.throw(_("Quantity must be greater than zero."))
	default_rate = _item_selling_rate(code)
	line_rate = flt(rate) if rate is not None and flt(rate) >= 0 else default_rate
	if rate is not None and flt(rate) != flt(default_rate) and not _user_can_edit_pos_price():
		frappe.throw(_("You are not allowed to change item price."), frappe.PermissionError)
	existing = None
	for row in invoice.items:
		if row.item_code == code:
			existing = row
			break
	if existing:
		existing.qty = flt(existing.qty) + qty
		if line_rate or not existing.rate:
			existing.rate = line_rate
	else:
		invoice.append(
			"items",
			{
				"item": code,
				"item_code": item.item_code or code,
				"qty": qty,
				"rate": line_rate,
			},
		)
	invoice.flags.ignore_permissions = True
	invoice.save()
	return _serialize_invoice(invoice.name)


@frappe.whitelist()
def update_retail_pos_line_rate(invoice_name: str, row_name: str, rate: float | int):
	if not _user_can_edit_pos_price():
		frappe.throw(_("You are not allowed to change item price."), frappe.PermissionError)
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	if invoice.docstatus != 0:
		frappe.throw(_("Invoice is already submitted."))
	line_rate = flt(rate)
	if line_rate < 0:
		frappe.throw(_("Price cannot be negative."))
	for row in invoice.items:
		if row.name == row_name:
			row.rate = line_rate
			break
	else:
		frappe.throw(_("Line item not found."))
	invoice.flags.ignore_permissions = True
	invoice.save()
	return _serialize_invoice(invoice.name)


@frappe.whitelist()
def remove_item_from_retail_pos(invoice_name: str, row_name: str):
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	if invoice.docstatus != 0:
		frappe.throw(_("Invoice is already submitted."))
	invoice.items = [row for row in invoice.items if row.name != row_name]
	invoice.flags.ignore_permissions = True
	invoice.save()
	return _serialize_invoice(invoice.name)


@frappe.whitelist()
def apply_retail_pos_discount(invoice_name: str, discount_amount: float | int = 0):
	frappe.cache().set_value(_pos_discount_key(invoice_name), flt(discount_amount))
	return _serialize_invoice(invoice_name)


@frappe.whitelist()
def set_retail_pos_customer(invoice_name: str, customer: str):
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	if invoice.docstatus != 0:
		frappe.throw(_("Invoice is already submitted."))
	invoice.customer = customer
	invoice.flags.ignore_permissions = True
	invoice.save()
	return _serialize_invoice(invoice.name)


@frappe.whitelist()
def complete_retail_pos_sale(invoice_name: str):
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	if invoice.docstatus != 0:
		frappe.throw(_("Invoice is already submitted."))
	if not invoice.items:
		frappe.throw(_("Cart is empty."))
	discount = flt(frappe.cache().get_value(_pos_discount_key(invoice_name)) or 0)
	if discount > 0 and discount < flt(invoice.net_total):
		ratio = 1 - (discount / flt(invoice.net_total))
		for row in invoice.items:
			row.rate = flt(row.rate) * ratio
		invoice.flags.ignore_permissions = True
		invoice.save()
	invoice.flags.ignore_permissions = True
	invoice.submit()
	einvoice = dispatch_einvoice_for_sales_invoice(invoice.name)
	frappe.cache().delete_value(_pos_discount_key(invoice_name))
	receipt_html = ""
	try:
		receipt_html = get_retail_receipt_html(invoice.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Retail POS receipt render")
	return {
		"invoice": invoice.name,
		"einvoice": einvoice,
		"receipt_html": receipt_html,
	}


@frappe.whitelist()
def get_retail_receipt_html(invoice_name: str):
	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	company_ctx = _company_receipt_context(invoice.company)
	address_line = _branch_address_line(invoice.branch) or company_ctx["address"]
	items = []
	for row in invoice.items:
		items.append(
			{
				"name": _line_item_name(row) or row.item_code,
				"qty": flt(row.qty),
				"price": flt(row.rate),
				"total": flt(row.amount),
			}
		)
	discount = flt(frappe.cache().get_value(_pos_discount_key(invoice_name)) or 0)
	fin = _invoice_financials(invoice, discount)
	einv = get_einvoice_receipt_context(invoice.name)
	context = {
		"store_name_ar": company_ctx["store_name_ar"],
		"store_name_en": company_ctx["store_name_en"],
		"address": address_line or "شارع النصر - القاهرة - مصر",
		"phone": company_ctx["phone"] or "—",
		"cr_number": company_ctx["cr_number"] or "—",
		"tax_id": company_ctx["tax_id"] or "—",
		"invoice_number": (invoice.name or "").split("-")[-1],
		"invoice_date": frappe.utils.formatdate(invoice.posting_date, "dd/MM/yyyy"),
		"invoice_time": frappe.utils.format_time(nowtime(), "hh:mm a"),
		"cashier": get_fullname(invoice.owner),
		"items": items,
		"discount": fin["discount"],
		"subtotal_before_discount": fin["subtotal"],
		"grand_total": fin["grand_total"],
		"vat_included": fin["tax"],
		"sales_invoice": invoice.name,
		"qr_image_base64": einv.get("qr_image_base64") or "",
		"einvoice_uuid": einv.get("uuid") or "",
	}
	return frappe.render_template("omnexa_core/templates/retail_thermal_receipt.html", context, is_path=True)


@frappe.whitelist()
def sync_retail_pos_item_visibility(company: str | None = None):
	"""Enable real items for Retail POS and hide demo/simulation rows for a company."""
	if not _item_has_show_in_retail_pos_field():
		frappe.throw(_("Item field Show in Retail POS is not installed. Run migrate on omnexa_core."))
	company = company or resolve_retail_pos_company_branch()[0]
	visible_types = _pos_visible_product_types() or set(CATEGORY_LABELS)
	enabled = 0
	disabled = 0
	for row in frappe.get_all(
		"Item",
		filters={"company": company, "disabled": 0},
		fields=["name", "item_code", "item_name", "product_type", "is_sales_item", "show_in_retail_pos"],
	):
		is_demo = _is_pos_demo_item(row)
		should_show = (not is_demo) and (row.get("product_type") in visible_types)
		if should_show and not cint(row.get("show_in_retail_pos")):
			values = {"show_in_retail_pos": 1}
			if not cint(row.get("is_sales_item")):
				values["is_sales_item"] = 1
			frappe.db.set_value("Item", row.name, values, update_modified=False)
			enabled += 1
		elif is_demo and cint(row.get("show_in_retail_pos")):
			frappe.db.set_value("Item", row.name, "show_in_retail_pos", 0, update_modified=False)
			disabled += 1
	frappe.db.commit()
	return {"company": company, "enabled": enabled, "disabled_demo": disabled}
