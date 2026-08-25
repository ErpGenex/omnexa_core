# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

SKIP_DOCTYPES = frozenset(
	{
		"Company",
		"Branch",
		"User",
		"User Branch Access",
		"Global Defaults",
		"System Settings",
		"Navbar Settings",
		"Report",
		"Print Format",
		"Workspace",
		"Dashboard",
		"Dashboard Chart",
		"Number Card",
	}
)

SCOPE_FIELDS = ("company", "branch")
SCOPE_FIELD_PROPS = (
	("hidden", "1", "Check"),
	("read_only", "1", "Check"),
	("in_standard_filter", "0", "Check"),
)


def _upsert_property_setter(
	doctype: str,
	fieldname: str,
	property: str,
	value: str,
	property_type: str,
) -> None:
	name = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": fieldname, "property": property},
		"name",
	)
	if name:
		current = frappe.db.get_value("Property Setter", name, "value")
		if current == value:
			return
		frappe.db.set_value("Property Setter", name, "value", value, update_modified=False)
		return

	make_property_setter(
		doctype,
		fieldname,
		property,
		value,
		property_type,
		validate_fields_for_doctype=False,
	)


def _doctype_has_scope_field(doctype: str, fieldname: str) -> bool:
	try:
		return bool(frappe.get_meta(doctype).has_field(fieldname))
	except Exception:
		return False


def ensure_navbar_scope_fields_hidden() -> dict:
	"""Hide company/branch on all transaction forms; values come from navbar context."""
	updated = 0
	skipped = 0
	cleared_doctypes: set[str] = set()

	for row in frappe.get_all(
		"DocType",
		filters={"istable": ("in", [0, 1]), "issingle": 0, "custom": ("in", [0, 1])},
		fields=["name"],
	):
		doctype = row.name
		if doctype in SKIP_DOCTYPES:
			skipped += 1
			continue

		touched = False
		for fieldname in SCOPE_FIELDS:
			if not _doctype_has_scope_field(doctype, fieldname):
				continue
			for prop, value, prop_type in SCOPE_FIELD_PROPS:
				_upsert_property_setter(doctype, fieldname, prop, value, prop_type)
				updated += 1
				touched = True

		if touched:
			cleared_doctypes.add(doctype)

	for doctype in cleared_doctypes:
		frappe.clear_cache(doctype=doctype)

	return {
		"property_setters_upserted": updated,
		"doctypes_touched": len(cleared_doctypes),
		"doctypes_skipped": skipped,
	}
