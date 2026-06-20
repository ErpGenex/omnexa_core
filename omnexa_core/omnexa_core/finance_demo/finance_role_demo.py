# Copyright (c) 2026, ErpGenEx
"""Finance Group role workspaces + demo users (mirrors Healthcare role demo)."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.vertical_workspace_sync import build_content_from_link_rows

DEMO_PASSWORD = "Finance@Demo2026"

ROLE_SPECS: list[dict] = [
	{
		"role": "Finance Group Executive",
		"workspace": "Finance Executive",
		"title": "📊 Group Executive",
		"default_route": "/app/fe-executive-dashboard",
		"email": "executive@demo.finance",
		"first_name": "Karim",
		"last_name": "Executive",
		"sections": [
			("📊 Group", [
				("Page", "fe-executive-dashboard", "Finance Engine"),
				("Page", "finance-demo-hub", "Demo Hub"),
			]),
		],
	},
	{
		"role": "Finance Credit Officer",
		"workspace": "Finance Credit Origination",
		"title": "🛡️ Credit Origination",
		"default_route": "/app/ce-servicing-portal",
		"email": "credit@demo.finance",
		"first_name": "Nadia",
		"last_name": "Credit",
		"sections": [
			("🛡️ Origination", [
				("Page", "ce-servicing-portal", "Origination Portal"),
				("Page", "ce-executive-dashboard", "Credit Executive"),
			]),
		],
	},
	{
		"role": "Finance Risk Analyst",
		"workspace": "Finance Credit Risk",
		"title": "📈 Credit Risk",
		"default_route": "/app/rk-servicing-portal",
		"email": "risk@demo.finance",
		"first_name": "Omar",
		"last_name": "Risk",
		"sections": [
			("📈 Risk", [
				("Page", "rk-servicing-portal", "Risk Portal"),
				("Page", "rk-executive-dashboard", "Risk Executive"),
			]),
		],
	},
	{
		"role": "Finance Treasury Officer",
		"workspace": "Finance Treasury",
		"title": "💹 Treasury ALM",
		"default_route": "/app/al-servicing-portal",
		"email": "treasury@demo.finance",
		"first_name": "Hana",
		"last_name": "Treasury",
		"sections": [
			("💹 ALM", [
				("Page", "al-servicing-portal", "ALM Portal"),
				("Page", "al-executive-dashboard", "ALM Executive"),
			]),
		],
	},
	{
		"role": "Finance Consumer Officer",
		"workspace": "Finance Consumer",
		"title": "🛒 Consumer Lending",
		"default_route": "/app/cf-servicing-portal",
		"email": "consumer@demo.finance",
		"first_name": "Sara",
		"last_name": "Consumer",
		"sections": [
			("🛒 Consumer", [
				("Page", "cf-servicing-portal", "Consumer Portal"),
				("Page", "cf-executive-dashboard", "Consumer Executive"),
			]),
		],
	},
	{
		"role": "Finance Auto Officer",
		"workspace": "Finance Auto",
		"title": "🚗 Auto Finance",
		"default_route": "/app/vf-servicing-portal",
		"email": "auto@demo.finance",
		"first_name": "Ahmed",
		"last_name": "Auto",
		"sections": [
			("🚗 Auto", [
				("Page", "vf-servicing-portal", "Auto Portal"),
				("Page", "vf-executive-dashboard", "Auto Executive"),
			]),
		],
	},
	{
		"role": "Finance Mortgage Officer",
		"workspace": "Finance Mortgage",
		"title": "🏠 Mortgage",
		"default_route": "/app/mg-servicing-portal",
		"email": "mortgage@demo.finance",
		"first_name": "Layla",
		"last_name": "Mortgage",
		"sections": [
			("🏠 Mortgage", [
				("Page", "mg-servicing-portal", "Mortgage Portal"),
				("Page", "mg-executive-dashboard", "Mortgage Executive"),
			]),
		],
	},
	{
		"role": "Finance Factoring Officer",
		"workspace": "Finance Factoring",
		"title": "📄 Factoring",
		"default_route": "/app/fc-servicing-portal",
		"email": "factoring@demo.finance",
		"first_name": "Youssef",
		"last_name": "Factoring",
		"sections": [
			("📄 Factoring", [
				("Page", "fc-servicing-portal", "Factoring Portal"),
				("Page", "fc-executive-dashboard", "Factoring Executive"),
			]),
		],
	},
	{
		"role": "Finance SME Officer",
		"workspace": "Finance SME",
		"title": "🏪 SME Finance",
		"default_route": "/app/sr-servicing-portal",
		"email": "sme@demo.finance",
		"first_name": "Mona",
		"last_name": "SME",
		"sections": [
			("🏪 SME", [
				("Page", "sr-servicing-portal", "SME Portal"),
				("Page", "sr-executive-dashboard", "SME Executive"),
			]),
		],
	},
	{
		"role": "Finance Leasing Officer",
		"workspace": "Finance Leasing",
		"title": "📦 Leasing",
		"default_route": "/app/lf-servicing-portal",
		"email": "leasing@demo.finance",
		"first_name": "Tarek",
		"last_name": "Leasing",
		"sections": [
			("📦 Leasing", [
				("Page", "lf-servicing-portal", "Leasing Portal"),
				("Page", "lf-executive-dashboard", "Leasing Executive"),
			]),
		],
	},
	{
		"role": "Finance GRC Officer",
		"workspace": "Finance GRC",
		"title": "🛡️ Operational Risk",
		"default_route": "/app/or-grc-portal",
		"email": "grc@demo.finance",
		"first_name": "Dina",
		"last_name": "GRC",
		"sections": [
			("🛡️ GRC", [
				("Page", "or-grc-portal", "GRC Portal"),
				("Page", "or-executive-dashboard", "Risk Executive"),
			]),
		],
	},
	{
		"role": "Finance Accounting Controller",
		"workspace": "Finance Accounting",
		"title": "📒 Accounting",
		"default_route": "/app/acct-executive-dashboard",
		"email": "accounting@demo.finance",
		"first_name": "Hana",
		"last_name": "Accounting",
		"sections": [
			("📒 GL", [
				("Page", "acct-executive-dashboard", "Accounting Executive"),
				("Page", "finance-control-center", "Finance Control Center"),
				("Page", "accounting-close-dashboard", "Close Dashboard"),
			]),
		],
	},
	{
		"role": "Finance Microfinance Officer",
		"workspace": "Finance Microfinance",
		"title": "🤝 Microfinance Field",
		"default_route": "/app/mf-servicing-portal",
		"email": "micro@demo.finance",
		"first_name": "Fatma",
		"last_name": "Micro",
		"sections": [
			("🤝 Micro", [
				("Page", "mf-servicing-portal", "Field Portal"),
				("Page", "mf-executive-dashboard", "Micro Executive"),
			]),
		],
	},
]

FINANCE_MODULES = frozenset({
	"Omnexa Core",
	"Omnexa Finance Engine",
	"Omnexa Credit Engine",
	"Omnexa Credit Risk",
	"Omnexa ALM",
	"Omnexa Consumer Finance",
	"Omnexa Vehicle Finance",
	"Omnexa Mortgage Finance",
	"Omnexa Factoring",
	"Omnexa SME Retail Finance",
	"Omnexa SME Microfinance",
	"Omnexa Leasing Finance",
	"Omnexa Operational Risk",
	"Omnexa Accounting",
})


def _ensure_role(role_name: str) -> None:
	if not frappe.db.exists("Role", role_name):
		frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)


def _exists_link(link_type: str, link_to: str) -> bool:
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	return False


def _build_rows(sections: list) -> list[dict]:
	rows: list[dict] = []
	for label, items in sections:
		valid = [(t, to, lbl) for t, to, lbl in items if _exists_link(t, to)]
		if not valid:
			continue
		rows.append({"label": label, "type": "Card Break", "link_type": "DocType"})
		for link_type, link_to, lbl in valid:
			row = {"type": "Link", "label": lbl, "link_type": link_type, "link_to": link_to}
			if link_type == "Report":
				row["is_query_report"] = 1
			rows.append(row)
	return rows


def sync_role_workspace(spec: dict) -> str:
	role = spec["role"]
	ws_name = spec["workspace"]
	_ensure_role(role)
	rows = _build_rows(spec["sections"])
	if not frappe.db.exists("Workspace", ws_name):
		ws = frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": ws_name,
				"title": ws_name,
				"module": "Omnexa Core",
				"public": 0,
				"for_user": "",
				"content": "[]",
				"sequence_id": 2.0,
			}
		)
		ws.insert(ignore_permissions=True)
	else:
		ws = frappe.get_doc("Workspace", ws_name)

	ws.set("links", [])
	for row in rows:
		ws.append("links", row)
	ws.set("roles", [{"role": role}])
	ws.title = spec.get("title") or ws_name
	ws.content = build_content_from_link_rows(rows, ws, title=ws.title, slug=frappe.scrub(ws_name))
	ws.flags.ignore_permissions = True
	ws.save()
	return ws.name


def _block_non_finance_modules(user_doc) -> None:
	all_modules = frappe.get_all("Module Def", pluck="name")
	blocked = [m for m in all_modules if m not in FINANCE_MODULES and m not in ("Core", "Desk", "Integrations")]
	user_doc.set("block_modules", [{"module": m} for m in blocked[:40]])


def _resolve_demo_company_branch(
	company: str | None = None, branch: str | None = None
) -> tuple[str, str]:
	"""Resolve Company/Branch for demo seed — user defaults, then site defaults, then first records."""
	company = (company or "").strip() or (frappe.defaults.get_user_default("Company") or "").strip()
	branch = (branch or "").strip() or (frappe.defaults.get_user_default("Branch") or "").strip()
	if not company:
		company = (frappe.db.get_single_value("Global Defaults", "default_company") or "").strip()
	if not company:
		company = frappe.db.get_value("Company", {}, "name", order_by="creation asc") or ""
	if company and not branch:
		branch = frappe.db.get_value(
			"Branch", {"company": company}, "name", order_by="creation asc"
		) or ""
	if not branch:
		branch = frappe.db.get_value("Branch", {}, "name", order_by="creation asc") or ""
	if not company:
		frappe.throw(
			_("No Company found. Create a Company first, or set Global Defaults → default company.")
		)
	if not branch:
		frappe.throw(
			_("No Branch found for {0}. Create a Branch or set your user Branch default.").format(company)
		)
	return company, branch


@frappe.whitelist()
def get_finance_demo_defaults() -> dict:
	"""Companies and branches available for finance role demo seed."""
	frappe.only_for("System Manager")
	companies = frappe.get_all("Company", fields=["name"], order_by="name asc", limit=50)
	branches = frappe.get_all("Branch", fields=["name", "company"], order_by="name asc", limit=200)
	try:
		company, branch = _resolve_demo_company_branch()
	except Exception:
		company, branch = "", ""
	return {
		"companies": companies,
		"branches": branches,
		"default_company": company,
		"default_branch": branch,
	}


def _ensure_demo_user(spec: dict, company: str, branch: str) -> str:
	email = spec["email"]
	role = spec["role"]
	ws = spec["workspace"]
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": spec["first_name"],
				"last_name": spec["last_name"],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user.enabled = 1
	user.new_password = DEMO_PASSWORD
	if not user.roles or not any(r.role == role for r in user.roles):
		user.append("roles", {"role": role})
	_block_non_finance_modules(user)
	user.default_workspace = ws
	user.save(ignore_permissions=True)
	frappe.defaults.set_user_default("Company", company, email)
	frappe.defaults.set_user_default("Branch", branch, email)
	return email


@frappe.whitelist()
def seed_finance_role_demo(company: str | None = None, branch: str | None = None) -> dict:
	"""Create finance role workspaces + demo users (System Manager)."""
	frappe.only_for("System Manager")
	company, branch = _resolve_demo_company_branch(company, branch)

	workspaces = []
	users = []
	for spec in ROLE_SPECS:
		workspaces.append(sync_role_workspace(spec))
		users.append(_ensure_demo_user(spec, company, branch))

	from omnexa_core.omnexa_core.finance_demo.finance_group_workspace import sync_finance_group_home

	sync_finance_group_home()
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe import sync_all_finance_vertical_bpe

		sync_all_finance_vertical_bpe()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "seed_finance_role_demo: vertical bpe sync")

	frappe.db.commit()
	return {
		"ok": True,
		"password": DEMO_PASSWORD,
		"company": company,
		"branch": branch,
		"workspaces": workspaces,
		"users": get_finance_demo_credentials()["users"],
		"message": _("Finance role demo ready. Each user sees only their workspace."),
	}


@frappe.whitelist()
def get_finance_demo_credentials() -> dict:
	frappe.only_for("System Manager")
	return {
		"password": DEMO_PASSWORD,
		"users": [
			{
				"role": s["role"],
				"email": s["email"],
				"workspace": s["workspace"],
				"route": s["default_route"],
				"name": f"{s['first_name']} {s['last_name']}",
			}
			for s in ROLE_SPECS
		],
	}
