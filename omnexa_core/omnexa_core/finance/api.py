from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled
from omnexa_core.omnexa_core.finance.rules import enforce_posting_rules


@frappe.whitelist()
def suggest_bank_reconciliation_matches(
	company: str,
	bank_account: str,
	statement_date: str | None = None,
	tolerance_days: int = 7,
	limit: int = 200,
):
	"""Return candidate Payment Entries for bank statement reconciliation.

	Matching strategy (best-effort):
	- same company and bank account
	- submitted payment entries
	- posting date window around statement date
	"""
	if not company or not bank_account:
		return []
	tolerance_days = max(1, min(cint(tolerance_days or 7), 31))
	limit = max(1, min(cint(limit or 200), 1000))

	base_date = getdate(statement_date) if statement_date else getdate()

	rows = frappe.db.sql(
		"""
		SELECT
			name,
			posting_date,
			party_type,
			party,
			paid_amount,
			mode_of_payment,
			remittance_reference,
			remittance_date,
			remittance_bank_reference
		FROM `tabPayment Entry`
		WHERE docstatus = 1
		  AND company = %(company)s
		  AND bank_account = %(bank_account)s
		  AND posting_date BETWEEN DATE_SUB(%(base_date)s, INTERVAL %(tol)s DAY)
		                       AND DATE_ADD(%(base_date)s, INTERVAL %(tol)s DAY)
		ORDER BY ABS(DATEDIFF(posting_date, %(base_date)s)) ASC, modified DESC
		LIMIT %(limit)s
		""",
		{
			"company": company,
			"bank_account": bank_account,
			"base_date": base_date,
			"tol": tolerance_days,
			"limit": limit,
		},
		as_dict=True,
	)
	return rows


@frappe.whitelist()
def finance_feature_flags():
	return {
		"finance_submit_controls": cint(is_feature_enabled("global_finance_submit_controls", default=True)),
		"bank_rec_suggestions": cint(is_feature_enabled("global_bank_rec_suggestions", default=True)),
	}


def _float_conf(key: str, default: float) -> float:
	conf = frappe.get_conf() or {}
	raw = conf.get(key)
	try:
		return float(raw) if raw is not None else float(default)
	except Exception:
		return float(default)


def _required_approval_level(doctype: str, amount: float) -> str:
	manager_threshold = _float_conf("finance_manager_approval_threshold", 50000.0)
	cfo_threshold = _float_conf("finance_cfo_approval_threshold", 250000.0)
	if amount >= cfo_threshold:
		return "CFO"
	if amount >= manager_threshold:
		return "Manager"
	return "None"


def validate_finance_submit_controls(doc):
	"""Submit-time finance controls (called from compliance guard)."""
	if not is_feature_enabled("global_finance_submit_controls", default=True):
		return
	if not getattr(doc, "doctype", None):
		return

	if doc.doctype == "Journal Entry":
		entry_type = (doc.get("entry_type") or "").strip()
		if entry_type in {"Opening", "Closing"}:
			if not (doc.get("remarks") or "").strip():
				frappe.throw(_("Remarks are required for Opening/Closing journal entries."), title=_("Compliance"))
			roles = set(frappe.get_roles() or [])
			if "System Manager" not in roles and "Accounts Manager" not in roles:
				frappe.throw(_("Opening/Closing journals require Accounts Manager approval role."), title=_("Compliance"))

		total_debit = sum(flt(r.get("debit")) for r in (doc.get("accounts") or []))
		approval_level = _required_approval_level("Journal Entry", total_debit)
		if doc.meta.has_field("required_approval_level"):
			doc.set("required_approval_level", approval_level)
		if approval_level == "CFO":
			roles = set(frappe.get_roles() or [])
			if "System Manager" not in roles and "CFO" not in roles:
				frappe.throw(_("CFO approval is required for high-value journal entries."), title=_("Compliance"))
		elif approval_level == "Manager":
			roles = set(frappe.get_roles() or [])
			if "System Manager" not in roles and "Accounts Manager" not in roles and "CFO" not in roles:
				frappe.throw(_("Manager approval is required for this journal entry amount."), title=_("Compliance"))
		# SoD: creator cannot be approver for sensitive entries.
		if is_feature_enabled("global_finance_sod_enforcement", default=False) and approval_level in {"Manager", "CFO"}:
			creator = (doc.get("owner") or "").strip()
			current_user = (frappe.session.user or "").strip()
			if creator and current_user and creator == current_user:
				frappe.throw(_("SoD policy: creator cannot approve the same high-risk journal entry."), title=_("Compliance"))
		if doc.meta.has_field("approved_by_user"):
			doc.set("approved_by_user", frappe.session.user)

	if doc.doctype == "Payment Entry":
		if flt(doc.get("paid_amount")) <= 0:
			frappe.throw(_("Paid Amount must be greater than zero."), title=_("Compliance"))
		if doc.get("mode_of_payment"):
			mop_type = frappe.db.get_value("Mode of Payment", doc.get("mode_of_payment"), "type") or ""
			if mop_type in {"Bank", "Wire", "Cheque"} and not doc.get("bank_account"):
				frappe.throw(_("Bank Account is required for bank-mode payments."), title=_("Compliance"))

		approval_level = _required_approval_level("Payment Entry", flt(doc.get("paid_amount")))
		if doc.meta.has_field("required_approval_level"):
			doc.set("required_approval_level", approval_level)
		if approval_level == "CFO":
			roles = set(frappe.get_roles() or [])
			if "System Manager" not in roles and "CFO" not in roles:
				frappe.throw(_("CFO approval is required for high-value payments."), title=_("Compliance"))
		elif approval_level == "Manager":
			roles = set(frappe.get_roles() or [])
			if "System Manager" not in roles and "Accounts Manager" not in roles and "CFO" not in roles:
				frappe.throw(_("Manager approval is required for this payment amount."), title=_("Compliance"))
		if is_feature_enabled("global_finance_sod_enforcement", default=False) and approval_level in {"Manager", "CFO"}:
			creator = (doc.get("owner") or "").strip()
			current_user = (frappe.session.user or "").strip()
			if creator and current_user and creator == current_user:
				frappe.throw(_("SoD policy: creator cannot approve the same high-risk payment."), title=_("Compliance"))
		if doc.meta.has_field("approved_by_user"):
			doc.set("approved_by_user", frappe.session.user)

	# Posting Rules Matrix (optional, can be turned on progressively).
	if is_feature_enabled("global_finance_posting_rules", default=False):
		enforce_posting_rules(doc)


def _line_amount(line: dict) -> float:
	debit = flt(line.get("debit"))
	credit = flt(line.get("credit"))
	return max(debit, credit)


def score_bank_statement_candidates(statement_line: dict, candidates: list[dict]) -> list[dict]:
	"""Score candidates by amount/date/reference similarity (0..100)."""
	out = []
	ref = str(statement_line.get("reference") or "").strip().lower()
	desc = str(statement_line.get("description") or "").strip().lower()
	posting_date = getdate(statement_line.get("posting_date")) if statement_line.get("posting_date") else None
	amount = max(flt(statement_line.get("debit")), flt(statement_line.get("credit")))
	for c in candidates or []:
		score = 0.0
		c_amount = flt(c.get("paid_amount"))
		# amount closeness
		if amount > 0:
			diff_ratio = abs(c_amount - amount) / max(amount, 1.0)
			score += max(0.0, 60.0 * (1.0 - min(diff_ratio, 1.0)))
		# date closeness
		if posting_date and c.get("posting_date"):
			days = abs((getdate(c.get("posting_date")) - posting_date).days)
			score += max(0.0, 25.0 - min(days, 25))
		# reference hint
		c_refs = " ".join(
			[
				str(c.get("remittance_reference") or "").lower(),
				str(c.get("remittance_bank_reference") or "").lower(),
				str(c.get("name") or "").lower(),
			]
		)
		if ref and ref in c_refs:
			score += 10.0
		if desc and any(token and token in c_refs for token in desc.split(" ")[:3]):
			score += 5.0
		row = dict(c)
		row["match_score"] = round(score, 2)
		out.append(row)
	out.sort(key=lambda x: float(x.get("match_score") or 0), reverse=True)
	return out


@frappe.whitelist()
def auto_match_bank_statement_import(bank_statement_import: str):
	"""Auto-match bank statement lines with payment entries, best-effort."""
	if not bank_statement_import or not frappe.db.exists("Bank Statement Import", bank_statement_import):
		return {"matched": 0, "total": 0}
	doc = frappe.get_doc("Bank Statement Import", bank_statement_import)
	total = 0
	matched = 0
	for line in doc.get("lines") or []:
		total += 1
		line_data = {
			"posting_date": line.get("posting_date"),
			"reference": line.get("reference"),
			"description": line.get("description"),
			"debit": line.get("debit"),
			"credit": line.get("credit"),
		}
		cands = suggest_bank_reconciliation_matches(
			company=doc.company,
			bank_account=doc.bank_account,
			statement_date=str(line.get("posting_date") or doc.statement_date),
			tolerance_days=7,
			limit=100,
		)
		scored = score_bank_statement_candidates(line_data, cands)
		if scored and float(scored[0].get("match_score") or 0) >= 70:
			line.matched_payment_entry = scored[0].get("name")
			line.match_score = scored[0].get("match_score")
			line.match_status = "Matched"
			matched += 1
		else:
			line.match_status = "Unmatched"
	doc.status = "Matched" if matched and matched == total else "Draft"
	doc.save(ignore_permissions=True)
	return {"matched": matched, "total": total}

