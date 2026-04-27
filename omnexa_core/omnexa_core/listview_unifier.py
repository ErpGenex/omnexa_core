from __future__ import annotations

import json

import frappe


DATE_FIELD_CANDIDATES: tuple[str, ...] = (
	"posting_date",
	"transaction_date",
	"date",
	"creation",
	"modified",
)

STATUS_FIELD_CANDIDATES: tuple[str, ...] = (
	"status",
	"workflow_state",
	"docstatus",
)

AMOUNT_FIELD_CANDIDATES: tuple[str, ...] = (
	"grand_total",
	"rounded_total",
	"base_grand_total",
	"net_total",
	"total",
	"amount",
	"paid_amount",
	"outstanding_amount",
)


def _first_existing_field(meta, fieldnames: tuple[str, ...]) -> str | None:
	for fn in fieldnames:
		if meta.has_field(fn):
			return fn
	return None


def _build_fields_payload(doctype: str) -> list[dict]:
	meta = frappe.get_meta(doctype)
	fields: list[dict] = []

	status_field = _first_existing_field(meta, STATUS_FIELD_CANDIDATES)
	if status_field:
		fields.append({"fieldname": status_field, "label": "Status"})

	if meta.has_field("company"):
		fields.append({"fieldname": "company", "label": "Company"})
	if meta.has_field("branch"):
		fields.append({"fieldname": "branch", "label": "Branch"})

	date_field = _first_existing_field(meta, DATE_FIELD_CANDIDATES)
	if date_field and date_field not in ("creation", "modified"):
		fields.append({"fieldname": date_field, "label": "Date"})
	elif date_field:
		fields.append({"fieldname": date_field, "label": date_field.replace("_", " ").title()})

	amount_field = _first_existing_field(meta, AMOUNT_FIELD_CANDIDATES)
	if amount_field:
		fields.append({"fieldname": amount_field, "label": "Amount"})

	return fields


def _is_eligible_doctype(doctype: str) -> bool:
	if not doctype:
		return False
	# Skip child tables and single doctypes.
	row = frappe.db.get_value("DocType", doctype, ["istable", "issingle"], as_dict=True)
	if not row:
		return False
	if int(row.istable or 0) == 1:
		return False
	if int(row.issingle or 0) == 1:
		return False
	return True


@frappe.whitelist(methods=["POST"])
def apply_unified_list_view_columns(target: str | None = None) -> dict:
	"""Enforce unified columns across list views.

	Columns goal (when fields exist on a DocType):
	- ID (always)
	- Status
	- Company
	- Branch
	- Date
	- Amount
	"""
	frappe.only_for("System Manager")

	if target:
		doctypes = [target]
	else:
		doctypes = frappe.get_all("DocType", pluck="name")

	updated = 0
	skipped = 0
	errors: list[str] = []

	for doctype in doctypes:
		try:
			if not _is_eligible_doctype(doctype):
				skipped += 1
				continue

			fields = _build_fields_payload(doctype)
			# If we can't contribute anything, don't override.
			if not fields:
				skipped += 1
				continue

			from frappe.desk.doctype.list_view_settings.list_view_settings import save_listview_settings

			save_listview_settings(
				doctype,
				{
					"total_fields": "10",
					"fields": json.dumps(fields),
				},
				[],
			)
			updated += 1
		except Exception:
			errors.append(f"{doctype}: {frappe.get_traceback()}")

	return {"ok": True, "updated": updated, "skipped": skipped, "errors": errors[:20]}

