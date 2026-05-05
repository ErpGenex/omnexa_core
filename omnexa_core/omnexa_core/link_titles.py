# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def _link_title_style_enabled():
	return int(frappe.conf.get("omnexa_link_title_style_enabled", 1) or 0) == 1


def _link_title_style_mode():
	mode = (frappe.conf.get("omnexa_link_title_style_mode", "code_name") or "code_name").strip().lower()
	if mode not in {"code_name", "name_code"}:
		return "code_name"
	return mode


def _format_code_name(code, name, fallback):
	code = (code or "").strip()
	name = (name or "").strip()
	fallback = (fallback or "").strip()
	if code and name:
		if _link_title_style_mode() == "name_code":
			return f"{name} - {code}"
		return f"{code} - {name}"
	if name:
		return name
	if code:
		return code
	return fallback


def _pick_existing_value(doc, fieldnames):
	for fieldname in fieldnames:
		value = (doc.get(fieldname) or "").strip()
		if value:
			return value
	return ""


def _dynamic_code_name_title(doctype, docname):
	"""Auto-discover code/name fields for any doctype and format as CODE - NAME."""
	meta = frappe.get_meta(doctype)
	fieldnames = {df.fieldname for df in (meta.fields or []) if getattr(df, "fieldname", None)}

	common_code_candidates = [
		"code",
		"item_code",
		"customer_code",
		"supplier_code",
		"employee_code",
		"account_number",
		"asset_number",
		"asset_code",
		"asset_tag",
		"iban",
	]
	common_name_candidates = [
		"item_name",
		"customer_name",
		"supplier_name",
		"employee_name",
		"account_name",
		"asset_name",
		"project_name",
		"bank_name",
	]

	code_candidates = [f for f in common_code_candidates if f in fieldnames]
	name_candidates = [f for f in common_name_candidates if f in fieldnames]

	# Generic heuristic for any custom model using *_code / *_name.
	code_candidates.extend(
		sorted(
			f for f in fieldnames if f.endswith("_code") and f not in code_candidates and f != "workflow_state"
		)
	)
	name_candidates.extend(
		sorted(
			f
			for f in fieldnames
			if f.endswith("_name") and f not in name_candidates and f != "naming_series"
		)
	)
	# `name` is usually the internal ID; use it only as a last fallback.
	if "name" in fieldnames:
		name_candidates.append("name")

	# Avoid unnecessary query for doctypes with neither code nor name candidates.
	if not code_candidates and not name_candidates:
		return ""

	row = frappe.db.get_value(doctype, docname, code_candidates + name_candidates, as_dict=True) or {}
	code = _pick_existing_value(row, code_candidates)
	name = _pick_existing_value(row, name_candidates)
	return _format_code_name(code, name, "")


@frappe.whitelist()
def get_link_title(doctype, docname):
	"""Global link-title policy: show code+name where available."""
	if not doctype or not docname:
		return docname
	if not _link_title_style_enabled():
		meta = frappe.get_meta(doctype)
		if meta.show_title_field_in_link and meta.title_field:
			return frappe.db.get_value(doctype, docname, meta.title_field) or docname
		return docname

	if doctype == "Customer":
		row = frappe.db.get_value("Customer", docname, ["customer_code", "customer_name"], as_dict=True)
		return _format_code_name(getattr(row, "customer_code", ""), getattr(row, "customer_name", ""), docname)

	if doctype == "Supplier":
		row = frappe.db.get_value("Supplier", docname, ["supplier_code", "supplier_name"], as_dict=True)
		return _format_code_name(getattr(row, "supplier_code", ""), getattr(row, "supplier_name", ""), docname)

	if doctype == "Employee":
		row = frappe.db.get_value("Employee", docname, ["employee_code", "employee_name"], as_dict=True)
		return _format_code_name(getattr(row, "employee_code", ""), getattr(row, "employee_name", ""), docname)

	if doctype == "Project":
		row = frappe.db.get_value("Project", docname, ["project_name"], as_dict=True)
		return _format_code_name("", getattr(row, "project_name", ""), docname)

	if doctype in ("GL Account", "Account"):
		row = frappe.db.get_value("GL Account", docname, ["account_number", "account_name"], as_dict=True)
		return _format_code_name(getattr(row, "account_number", ""), getattr(row, "account_name", ""), docname)

	if doctype == "Item":
		row = frappe.db.get_value("Item", docname, ["item_code", "item_name"], as_dict=True)
		return _format_code_name(getattr(row, "item_code", ""), getattr(row, "item_name", ""), docname)

	if doctype == "Fixed Asset":
		row = frappe.db.get_value("Fixed Asset", docname, ["asset_tag", "asset_name"], as_dict=True)
		return _format_code_name(getattr(row, "asset_tag", ""), getattr(row, "asset_name", ""), docname)

	if doctype == "Bank Account":
		row = frappe.db.get_value("Bank Account", docname, ["account_number", "account_name"], as_dict=True)
		return _format_code_name(getattr(row, "account_number", ""), getattr(row, "account_name", ""), docname)

	dynamic_title = _dynamic_code_name_title(doctype, docname)
	if dynamic_title:
		return dynamic_title

	meta = frappe.get_meta(doctype)
	if meta.show_title_field_in_link and meta.title_field:
		return frappe.db.get_value(doctype, docname, meta.title_field) or docname
	return docname


def ensure_link_title_policy_defaults():
	"""Force human-readable link titles for core doctypes across modules."""
	policy = {
		"GL Account": "account_name",
		"Customer": "customer_name",
		"Supplier": "supplier_name",
		"Employee": "employee_name",
		"Project": "project_name",
		"Item": "item_name",
	}
	for dt, title_field in policy.items():
		try:
			if not frappe.db.exists("DocType", dt):
				continue
			meta = frappe.get_meta(dt)
			if not meta.has_field(title_field):
				continue
			frappe.db.set_value("DocType", dt, "title_field", title_field, update_modified=False)
			frappe.db.set_value("DocType", dt, "show_title_field_in_link", 1, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: ensure link title policy ({dt})")

