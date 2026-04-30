from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate


def validate_budget_for_purchase(doc, *, amount_field: str = "grand_total"):
	"""Optional budget check for purchasing (best-effort).

	Data source:
	- `Purchase Budget` + `Purchase Budget Line` (omnexa_accounting)

	Policy:
	- Match by company + branch (if present) + fiscal_year.
	- Match by cost_center when document has item rows with cost_center.
	- Fail if document amount exceeds remaining budget (with simple aggregation).
	"""
	if not getattr(doc, "doctype", None):
		return

	if not (frappe.db.exists("DocType", "Purchase Budget") and frappe.db.exists("DocType", "Purchase Budget Line")):
		return

	company = doc.get("company") if doc.meta.has_field("company") else None
	branch = doc.get("branch") if doc.meta.has_field("branch") else None
	if not company:
		return

	posting_date = None
	for f in ("posting_date", "transaction_date", "quotation_date"):
		if doc.meta.has_field(f) and doc.get(f):
			posting_date = getdate(doc.get(f))
			break
	posting_date = posting_date or getdate()

	# Best-effort fiscal year mapping via Fiscal Year table, otherwise fallback to calendar year.
	fy = None
	if frappe.db.exists("DocType", "Fiscal Year"):
		fy = frappe.db.get_value(
			"Fiscal Year",
			{"year_start_date": ("<=", posting_date), "year_end_date": (">=", posting_date)},
			"name",
		)
	if not fy:
		fy = str(posting_date.year)

	amount = flt(doc.get(amount_field))
	if amount <= 0:
		return

	# Determine cost centers involved (if any).
	cost_centers = set()
	if doc.meta.has_field("items"):
		for row in doc.get("items") or []:
			cc = row.get("cost_center") if hasattr(row, "get") else None
			if cc:
				cost_centers.add(cc)

	# Aggregate remaining budget from active budgets.
	budget_filters = {"company": company, "fiscal_year": fy, "is_active": 1, "docstatus": 1}
	if branch and frappe.get_meta("Purchase Budget").has_field("branch"):
		budget_filters["branch"] = branch

	budgets = frappe.get_all("Purchase Budget", filters=budget_filters, pluck="name", limit_page_length=50)
	if not budgets:
		# no budgets configured: do nothing (non-breaking)
		return

	# Sum limits across matched lines (cc-specific if doc has cc).
	placeholders = ",".join(["%s"] * len(budgets))
	params = list(budgets)

	where = [f"pbl.parent in ({placeholders})"]
	if cost_centers:
		cc_placeholders = ",".join(["%s"] * len(cost_centers))
		where.append(f"(pbl.cost_center in ({cc_placeholders}))")
		params.extend(list(cost_centers))

	limit_total = frappe.db.sql(
		f"""
		SELECT COALESCE(SUM(pbl.budget_amount), 0)
		FROM `tabPurchase Budget Line` pbl
		WHERE {' AND '.join(where)}
		""",
		tuple(params),
	)[0][0]
	limit_total = flt(limit_total)
	if limit_total <= 0:
		return

	# Simple spent approximation: sum of submitted Purchase Invoices in same company/branch/fy (best-effort).
	spent_filters = {"company": company, "docstatus": 1}
	if branch and frappe.db.exists("DocType", "Purchase Invoice") and frappe.get_meta("Purchase Invoice").has_field("branch"):
		spent_filters["branch"] = branch

	# FY filter: posting_date within FY range if possible.
	fy_start = None
	fy_end = None
	if frappe.db.exists("Fiscal Year", fy):
		fy_start, fy_end = frappe.db.get_value("Fiscal Year", fy, ["year_start_date", "year_end_date"])

	date_clause = ""
	date_params = []
	if fy_start and fy_end:
		date_clause = " AND posting_date BETWEEN %s AND %s"
		date_params = [fy_start, fy_end]

	spent = 0.0
	if frappe.db.exists("DocType", "Purchase Invoice") and frappe.db.table_exists("tabPurchase Invoice"):
		spent = frappe.db.sql(
			f"""
			SELECT COALESCE(SUM(grand_total),0)
			FROM `tabPurchase Invoice`
			WHERE docstatus=1 AND company=%s
			{(" AND branch=%s" if branch else "")}
			{date_clause}
			""",
			tuple([company] + ([branch] if branch else []) + date_params),
		)[0][0]
	spent = flt(spent)

	remaining = limit_total - spent
	if remaining < 0:
		remaining = 0

	if amount - remaining > 0.0001:
		frappe.throw(
			_(
				"Budget control: document amount exceeds remaining budget. Remaining={0}, Amount={1}"
			).format(remaining, amount),
			title=_("Compliance"),
		)

