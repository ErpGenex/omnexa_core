# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import os
import shutil
import subprocess
import sys
import importlib
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from pathlib import Path
from json import dumps
from json import loads

import frappe
from frappe import _
from frappe.installer import install_app as install_site_app
from frappe.installer import update_site_config
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint, flt
from frappe.utils import get_bench_path
from frappe.utils.file_manager import save_file


SUPPORTED_FRAPPE_MAJOR = 15
REQUIRED_SITE_APPS = [
	"omnexa_accounting",
	"erpgenex_theme_0426",
	"omnexa_backup",
	"omnexa_customer_core",
	"omnexa_einvoice",
	"omnexa_experience",
	"omnexa_fixed_assets",
	"omnexa_hr",
	"omnexa_intelligence_core",
	"omnexa_projects_pm",
	"omnexa_reporting_compliance",
	"omnexa_services",
	"omnexa_setup_intelligence",
	"omnexa_statutory_audit",
	"omnexa_theme_manager",
	"omnexa_trading",
	"omnexa_user_academy",
	"omnexa_n8n_bridge",
]

# Auto `bench get-app` for REQUIRED_SITE_APPS when sources are missing (set OMNEXA_AUTO_GET_APPS=0 to disable).
DEFAULT_APPS_GIT_ORG = os.environ.get("ERPGENEX_GITHUB_ORG", "ErpGenex")
DEFAULT_APPS_GIT_BRANCH = os.environ.get("OMNEXA_APPS_BRANCH", "develop")
GITHUB_API_BASE = "https://api.github.com"
CORE_APP_SLUG = "omnexa_core"
_DISCOVERED_ORG_APP_DEFAULT_BRANCH: dict[str, str] = {}


def _auto_get_apps_enabled() -> bool:
	return str(os.environ.get("OMNEXA_AUTO_GET_APPS", "1")).strip().lower() not in (
		"0",
		"false",
		"no",
		"off",
	)


def _auto_discover_github_apps_enabled() -> bool:
	return str(os.environ.get("OMNEXA_INSTALL_ALL_GITHUB_APPS", "1")).strip().lower() not in (
		"0",
		"false",
		"no",
		"off",
	)


def _is_installable_omnexa_repo(repo_name: str) -> bool:
	name = (repo_name or "").strip()
	if not name or name == CORE_APP_SLUG:
		return False
	if name in {"frappe", "erpnext", "payments"}:
		return False
	return name.startswith("omnexa_") or name.startswith("erpgenex_")


def _discover_org_apps_from_github() -> list[str]:
	"""List installable app repositories from the configured GitHub organization."""
	global _DISCOVERED_ORG_APP_DEFAULT_BRANCH
	org = (os.environ.get("ERPGENEX_GITHUB_ORG") or DEFAULT_APPS_GIT_ORG).strip()
	token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
	page = 1
	per_page = 100
	found: list[str] = []
	_DISCOVERED_ORG_APP_DEFAULT_BRANCH = {}

	while True:
		url = f"{GITHUB_API_BASE}/orgs/{quote(org)}/repos?type=all&per_page={per_page}&page={page}"
		req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "omnexa-core-installer"})
		if token:
			req.add_header("Authorization", f"Bearer {token}")
		try:
			with urlopen(req, timeout=30) as resp:
				payload = loads(resp.read().decode("utf-8"))
		except (HTTPError, URLError, TimeoutError):
			frappe.log_error(frappe.get_traceback(), "Omnexa: GitHub app discovery failed")
			return []
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Omnexa: GitHub app discovery failed")
			return []

		if not isinstance(payload, list) or not payload:
			break

		for repo in payload:
			name = str((repo or {}).get("name") or "").strip()
			is_archived = bool((repo or {}).get("archived"))
			default_branch = str((repo or {}).get("default_branch") or "").strip()
			repo_size = int((repo or {}).get("size") or 0)
			if _is_installable_omnexa_repo(name):
				if is_archived:
					continue
				# Empty repositories (size=0 / no default branch) cannot be installed via bench get-app.
				if repo_size <= 0 or not default_branch:
					continue
				found.append(name)
				_DISCOVERED_ORG_APP_DEFAULT_BRANCH[name] = default_branch

		if len(payload) < per_page:
			break
		page += 1

	return sorted(set(found))


def _branch_candidates_for_app(app: str) -> list[str]:
	"""Build branch fallback order for cloning an app."""
	candidates: list[str] = []
	seen = set()
	for item in (
		(os.environ.get("OMNEXA_APPS_BRANCH") or "").strip(),
		(_DISCOVERED_ORG_APP_DEFAULT_BRANCH.get(app) or "").strip(),
		DEFAULT_APPS_GIT_BRANCH.strip(),
		"develop",
		"main",
		"master",
	):
		if not item or item in seen:
			continue
		seen.add(item)
		candidates.append(item)
	return candidates


def _target_site_apps() -> list[str]:
	"""Apps that should be fetched/installed with omnexa_core bootstrap."""
	out = list(REQUIRED_SITE_APPS)
	if _auto_discover_github_apps_enabled():
		for app in _discover_org_apps_from_github():
			if app not in out:
				out.append(app)
	return out


def _required_app_hooks_path(app: str) -> Path:
	return Path(get_bench_path()) / "apps" / app / app / "hooks.py"


def _app_source_present(app: str) -> bool:
	return _required_app_hooks_path(app).is_file()


def _ensure_app_import_path(app: str) -> None:
	"""Make a fetched app importable in the current Python process."""
	app_root = str(Path(get_bench_path()) / "apps" / app)
	if app_root not in sys.path:
		sys.path.insert(0, app_root)


def _ensure_required_apps_importable() -> None:
	for app in _target_site_apps():
		if _app_source_present(app):
			_ensure_app_import_path(app)
	importlib.invalidate_caches()


def _repair_apps_txt_entries(lines: list[str]) -> list[str]:
	"""Repair malformed apps.txt entries where two app names were concatenated."""
	known = ["frappe", "erpnext", "payments", *REQUIRED_SITE_APPS]
	known_set = set(known)
	out = []
	changed = False

	for raw in lines:
		line = (raw or "").strip()
		if not line:
			continue
		if line in known_set:
			out.append(line)
			continue

		# Try splitting concatenated app names (e.g. omnexa_coreerpgenex_theme_0426).
		split_done = False
		for left in known:
			if not line.startswith(left):
				continue
			right = line[len(left) :]
			if right in known_set:
				out.extend([left, right])
				changed = True
				split_done = True
				break
		if split_done:
			continue

		out.append(line)

	# Preserve order while removing duplicates.
	deduped = []
	seen = set()
	for app in out:
		if app in seen:
			if app in known_set:
				changed = True
			continue
		seen.add(app)
		deduped.append(app)

	return deduped if changed else [ln.strip() for ln in lines if (ln or "").strip()]


def _run_bench_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
	bench_cmd = shutil.which("bench")
	if not bench_cmd:
		frappe.throw(
			"The `bench` CLI is not in PATH; cannot clone ErpGenEx apps automatically. "
			"Add bench to PATH or run `bench get-app` for missing apps, then install omnexa_core again."
		)
	bench_path = get_bench_path()
	env = os.environ.copy()
	# Never block waiting for interactive git credentials during automated app discovery.
	env["GIT_TERMINAL_PROMPT"] = "0"
	return subprocess.run(
		[bench_cmd, *args],
		cwd=bench_path,
		capture_output=True,
		text=True,
		env=env,
		timeout=3600,
		check=False,
	)


def _bench_cli_or_throw(args: list[str], intro: str) -> None:
	proc = _run_bench_cli(args)
	if proc.returncode != 0:
		err = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"
		frappe.throw(f"{intro}\n{err}")


def ensure_required_apps_fetched():
	"""Clone missing ErpGenEx apps into the bench via `bench get-app` (skip-assets build race).

	Called from before_install / before_migrate so sources exist before site install and migrate.
	"""
	if not _auto_get_apps_enabled():
		return

	target_apps = _target_site_apps()
	missing = [app for app in target_apps if not _app_source_present(app)]
	if not missing:
		return

	org = (os.environ.get("ERPGENEX_GITHUB_ORG") or DEFAULT_APPS_GIT_ORG).strip()
	required_set = set(REQUIRED_SITE_APPS)
	required_failures = []

	for app in missing:
		url = f"https://github.com/{org}/{app}.git"
		fetched = False
		last_err = ""

		for branch in _branch_candidates_for_app(app):
			proc = _run_bench_cli(["get-app", url, "--branch", branch, "--skip-assets"])
			if proc.returncode == 0:
				fetched = True
				break
			last_err = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"

		if not fetched:
			proc = _run_bench_cli(["get-app", url, "--skip-assets"])
			if proc.returncode == 0:
				fetched = True
			else:
				last_err = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"

		if fetched:
			continue

		if app in required_set:
			required_failures.append((app, url, last_err))
		else:
			frappe.log_error(
				title="Omnexa: optional org app fetch skipped",
				message=f"App: {app}\nURL: {url}\nError:\n{last_err}",
			)

	if required_failures:
		first = required_failures[0]
		frappe.throw(
			f"Failed to fetch required app `{first[0]}` from {first[1]}.\n{first[2]}"
		)

	_bench_cli_or_throw(
		["setup", "requirements"],
		"Fetched required apps but `bench setup requirements` failed.",
	)
	_ensure_required_apps_importable()


def before_install():
	enforce_supported_frappe_version()
	ensure_required_apps_fetched()
	ensure_required_apps_are_registered()


def before_migrate():
	enforce_supported_frappe_version()
	ensure_required_apps_fetched()
	ensure_required_apps_are_registered()


def enforce_supported_frappe_version():
	"""Fail early when running on an unsupported Frappe major release."""
	version_text = (getattr(frappe, "__version__", "") or "").strip()
	if not version_text:
		return

	major_token = version_text.split(".", 1)[0]
	try:
		major = int(major_token)
	except ValueError:
		return

	if major != SUPPORTED_FRAPPE_MAJOR:
		frappe.throw(
			f"Unsupported Frappe version '{version_text}' for omnexa_core. "
			f"Supported range is >=15.0,<16.0.",
			frappe.ValidationError,
		)


def run_workspace_desk_sync():
	"""Guided setup + control-tower desk (KPIs, charts, Operations) after all apps exist.

	Called from `after_migrate`, `after_install`, and `after_any_app_install` (Frappe hook) so
	new sites and later `bench install-app` runs do not require
	`bench execute ... sync_all_workspace_kpi_layout` manually.
	"""
	try:
		from omnexa_core.workspace_onboarding_sync import enable_onboarding_setting, sync_workspace_database

		enable_onboarding_setting()
		# Must run before control-tower so Module Onboarding rows exist when desk content is rebuilt
		# (Operations / Reports / KPIs / Charts + Guided setup widget use the same onboarding id).
		sync_workspace_database()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: workspace onboarding sync")
	try:
		from omnexa_core.omnexa_core.workspace_control_tower import (
			prune_invalid_workspace_kpi_artifacts,
			sync_all_workspace_kpi_layout,
		)

		prune_invalid_workspace_kpi_artifacts()
		sync_all_workspace_kpi_layout()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: sync_all_workspace_kpi_layout")


def after_any_app_install(app_name: str):
	"""Re-build desks whenever another app is installed (doctypes + workspace specs may be new).

	Skipped during batched `install_required_site_apps` (defer flag) and right after
	`omnexa_core` itself because `after_install` already runs a full desk sync.
	"""
	if not app_name or app_name in ("frappe", "omnexa_core"):
		return
	if getattr(frappe.flags, "omnexa_suppress_after_app_workspace_sync", False):
		return
	run_workspace_desk_sync()


def after_install():
	enforce_supported_frappe_version()
	ensure_global_defaults_compat()
	install_required_site_apps()
	ensure_omnexa_roles()
	apply_default_branding()
	run_site_hardening_after_app_changes()


def after_migrate():
	enforce_supported_frappe_version()
	ensure_global_defaults_compat()
	ensure_omnexa_roles()
	apply_default_branding()
	run_site_hardening_after_app_changes()


def run_site_hardening_after_app_changes():
	"""Run all site-side fixes so fresh installs and migrations behave the same."""
	ensure_company_branding_fields()
	ensure_global_supporting_attachment_fields()
	ensure_procurement_enterprise_fields()
	ensure_inventory_enterprise_fields()
	ensure_finance_enterprise_fields()
	ensure_project_contract_link_compat()
	remove_legacy_people_workspace()
	remove_legacy_finance_workspace()
	remove_legacy_finance_group_stub_workspaces()
	run_workspace_desk_sync()
	ensure_default_sidebar_workspace_order()
	ensure_unified_list_view_columns()
	ensure_default_workspace_dashboard()
	ensure_dashboard_compliance_cards()
	ensure_dashboard_inventory_cards()
	backfill_bank_statement_line_company()
	ensure_dashboard_finance_cards()
	ensure_finance_workflow_templates()
	ensure_global_print_design_system()
	ensure_link_title_policy_defaults()
	ensure_site_runtime_ready()


def ensure_global_print_design_system():
	"""Apply a single print design system default across all modules/reports."""
	try:
		from omnexa_core.global_print_design import ensure_global_print_design_system as _ensure

		_ensure()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure global print design system")


def ensure_link_title_policy_defaults():
	"""Force human-readable link titles instead of internal IDs."""
	try:
		from omnexa_core.omnexa_core.link_titles import ensure_link_title_policy_defaults as _ensure

		_ensure()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure link title policy defaults")


def ensure_unified_list_view_columns():
	"""Standardize list view columns across doctypes (best-effort)."""
	try:
		from omnexa_core.omnexa_core.listview_unifier import apply_unified_list_view_columns

		apply_unified_list_view_columns()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: unified listview columns")


def ensure_default_workspace_dashboard():
	"""Set default landing page to /app/dashboard by setting User.default_workspace."""
	try:
		if not frappe.db.exists("Workspace", "Dashboard"):
			return
		# Apply to system users only (non Website User) and force default workspace.
		frappe.db.sql(
			"""
			UPDATE `tabUser`
			SET default_workspace = 'Dashboard'
			WHERE user_type != 'Website User'
			  AND enabled = 1
			"""
		)
		# Ensure Administrator always lands on Dashboard.
		frappe.db.set_value("User", "Administrator", "default_workspace", "Dashboard", update_modified=False)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure default workspace dashboard")


def ensure_dashboard_compliance_cards():
	"""Seed default compliance KPIs into Dashboard workspace (best-effort)."""
	try:
		if not frappe.db.exists("Workspace", "Dashboard"):
			return
		if not frappe.db.exists("DocType", "Number Card"):
			return

		def upsert_card(label: str, filters: list[tuple[str, str, str]]):
			"""Keep filters in sync on migrate (global scope — payloads may omit company)."""
			fj = dumps(filters, separators=(",", ":"))
			card_name = frappe.db.get_value("Number Card", {"label": label}, "name")
			if card_name:
				frappe.db.set_value("Number Card", card_name, "filters_json", fj)
				return card_name
			doc = frappe.get_doc(
				{
					"doctype": "Number Card",
					"label": label,
					"type": "Document Type",
					"document_type": "Error Log",
					"function": "Count",
					"filters_json": fj,
					"module": "Omnexa Core",
					"is_public": 1,
					"show_percentage_stats": 1,
					"stats_time_interval": "Daily",
					"show_full_number": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			return doc.name

		upsert_card("Compliance Exceptions", [["method", "=", "Global Compliance Guard"]])
		upsert_card(
			"Compliance Exceptions (IFRS)",
			[["method", "=", "Global Compliance Guard"], ["error", "like", "%IFRS%"]],
		)
		upsert_card(
			"Compliance Exceptions (Tax)",
			[["method", "=", "Global Compliance Guard"], ["error", "like", "%Tax Rule%"]],
		)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure dashboard compliance cards")


def ensure_dashboard_inventory_cards():
	"""Seed default inventory KPIs into Dashboard workspace (best-effort)."""
	try:
		if not frappe.db.exists("Workspace", "Dashboard"):
			return
		if not frappe.db.exists("DocType", "Number Card"):
			return

		def upsert_card(label: str, filters: list[tuple[str, str, str]]):
			fj = dumps(filters, separators=(",", ":"))
			card_name = frappe.db.get_value("Number Card", {"label": label}, "name")
			if card_name:
				frappe.db.set_value("Number Card", card_name, "filters_json", fj)
				return card_name
			doc = frappe.get_doc(
				{
					"doctype": "Number Card",
					"label": label,
					"type": "Document Type",
					"document_type": "Item",
					"function": "Count",
					"filters_json": fj,
					"module": "Omnexa Core",
					"is_public": 1,
					"show_percentage_stats": 1,
					"stats_time_interval": "Daily",
					"show_full_number": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			return doc.name

		upsert_card("Inventory Stock Items", [["is_stock_item", "=", "1"], ["disabled", "=", "0"]])
		upsert_card("Inventory Low Stock Items", [["is_stock_item", "=", "1"], ["disabled", "=", "0"], ["current_stock_qty", "<=", "0"]])
		upsert_card("Inventory Reorder Needed", [["is_stock_item", "=", "1"], ["disabled", "=", "0"], ["reorder_level", ">", "0"]])
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure dashboard inventory cards")


def backfill_bank_statement_line_company():
	"""Copy Company from Bank Statement Import onto each line for KPI filters (non-destructive)."""
	try:
		if not frappe.db.exists("DocType", "Bank Statement Line"):
			return
		if not frappe.db.has_column("Bank Statement Line", "company"):
			return
		frappe.db.sql(
			"""
			update `tabBank Statement Line` child
			inner join `tabBank Statement Import` par
				on par.name = child.parent and child.parenttype = %s
			set child.company = par.company
			where ifnull(child.company, '') = ''
			   or child.company != par.company
			""",
			("Bank Statement Import",),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: backfill bank statement line company")


def ensure_dashboard_finance_cards():
	"""Seed finance control KPIs into Dashboard workspace (best-effort)."""
	try:
		if not frappe.db.exists("Workspace", "Dashboard"):
			return
		if not frappe.db.exists("DocType", "Number Card"):
			return

		default_company = ""
		try:
			default_company = (frappe.db.get_single_value("Global Defaults", "default_company") or "").strip()
		except Exception:
			default_company = ""

		def upsert_error_log_card(label: str, filters: list[tuple[str, str, str]]):
			card_filters = list(filters or [])
			if default_company:
				card_filters.append(["error", "like", f'%\"company\": \"{default_company}\"%'])
			fj = dumps(card_filters, separators=(",", ":"))
			card_name = frappe.db.get_value("Number Card", {"label": label}, "name")
			if card_name:
				frappe.db.set_value("Number Card", card_name, "filters_json", fj)
				return card_name
			doc = frappe.get_doc(
				{
					"doctype": "Number Card",
					"label": label,
					"type": "Document Type",
					"document_type": "Error Log",
					"function": "Count",
					"filters_json": fj,
					"module": "Omnexa Core",
					"is_public": 1,
					"show_percentage_stats": 1,
					"stats_time_interval": "Daily",
					"show_full_number": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			return doc.name

		upsert_error_log_card(
			"Finance Control Violations",
			[
				["method", "=", "Global Compliance Guard"],
				["error", "like", "%FINANCE_%"],
			],
		)
		upsert_error_log_card(
			"Finance SoD Blocks",
			[
				["method", "=", "Global Compliance Guard"],
				["error", "like", "%SoD policy%"],
			],
		)
		# Unmatched statement lines; scoped by default company when set (see `company` on child row).
		if frappe.db.exists("DocType", "Bank Statement Line"):
			bank_filters: list[tuple[str, str, str]] = [["match_status", "=", "Unmatched"]]
			if default_company:
				bank_filters.append(["company", "=", default_company])
			fj_bank = dumps(bank_filters, separators=(",", ":"))
			bank_card = frappe.db.get_value("Number Card", {"label": "Bank Unmatched Statement Lines"}, "name")
			if bank_card:
				frappe.db.set_value("Number Card", bank_card, "filters_json", fj_bank)
			else:
				doc = frappe.get_doc(
					{
						"doctype": "Number Card",
						"label": "Bank Unmatched Statement Lines",
						"type": "Document Type",
						"document_type": "Bank Statement Line",
						"function": "Count",
						"filters_json": fj_bank,
						"module": "Omnexa Core",
						"is_public": 1,
						"show_percentage_stats": 1,
						"stats_time_interval": "Daily",
						"show_full_number": 1,
					}
				)
				doc.insert(ignore_permissions=True)

		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure dashboard finance cards")


def ensure_procurement_enterprise_fields():
	"""Add enterprise purchasing fields (supplier + PO lines) without breaking standard doctypes."""
	try:
		custom_fields_map = {}

		if frappe.db.exists("DocType", "Supplier"):
			meta = frappe.get_meta("Supplier")
			anchor = _last_insert_anchor_fieldname("Supplier")
			if anchor and not meta.has_field("supplier_name_ar"):
				custom_fields_map.setdefault("Supplier", []).extend(
					[
						{
							"fieldname": "enterprise_section",
							"label": "Enterprise Procurement",
							"fieldtype": "Section Break",
							"insert_after": anchor,
						},
						{
							"fieldname": "supplier_name_ar",
							"label": "Supplier Name (Arabic)",
							"fieldtype": "Data",
							"insert_after": "enterprise_section",
						},
						{
							"fieldname": "supplier_category",
							"label": "Supplier Category",
							"fieldtype": "Link",
							"options": "Supplier Category",
							"insert_after": "supplier_name_ar",
						},
						{
							"fieldname": "is_vat_registered",
							"label": "VAT Registered",
							"fieldtype": "Check",
							"default": "0",
							"insert_after": "supplier_category",
						},
						{
							"fieldname": "trn",
							"label": "TRN / VAT Registration No.",
							"fieldtype": "Data",
							"depends_on": "eval:doc.is_vat_registered==1",
							"insert_after": "is_vat_registered",
						},
						{
							"fieldname": "credit_limit",
							"label": "Credit Limit",
							"fieldtype": "Currency",
							"insert_after": "trn",
						},
						{
							"fieldname": "performance_rating",
							"label": "Performance Rating (0-5)",
							"fieldtype": "Float",
							"precision": "2",
							"insert_after": "credit_limit",
						},
					]
				)

		# Line-level enterprise fields for Purchase Order Item.
		if frappe.db.exists("DocType", "Purchase Order Item"):
			meta = frappe.get_meta("Purchase Order Item")
			anchor = _last_insert_anchor_fieldname("Purchase Order Item")
			if anchor and not meta.has_field("schedule_date"):
				custom_fields_map.setdefault("Purchase Order Item", []).extend(
					[
						{
							"fieldname": "schedule_date",
							"label": "Delivery Schedule Date",
							"fieldtype": "Date",
							"insert_after": anchor,
						},
						{
							"fieldname": "warehouse",
							"label": "Warehouse",
							"fieldtype": "Link",
							"options": "Warehouse",
							"insert_after": "schedule_date",
						},
						{
							"fieldname": "discount_percentage",
							"label": "Discount %",
							"fieldtype": "Float",
							"precision": "2",
							"default": "0",
							"insert_after": "warehouse",
						},
						{
							"fieldname": "tax_rule",
							"label": "Tax Rule",
							"fieldtype": "Link",
							"options": "Tax Rule",
							"insert_after": "discount_percentage",
						},
					]
				)

		# Approval helper fields (optional enforcement via feature flags).
		for dt in ("Purchase Order", "Purchase Invoice"):
			if not frappe.db.exists("DocType", dt):
				continue
			meta = frappe.get_meta(dt)
			anchor = _last_insert_anchor_fieldname(dt)
			if not anchor:
				continue
			if not meta.has_field("required_approver_role"):
				custom_fields_map.setdefault(dt, []).extend(
					[
						{
							"fieldname": "approval_section",
							"label": "Approvals",
							"fieldtype": "Section Break",
							"insert_after": anchor,
							"collapsible": 1,
						},
						{
							"fieldname": "required_approver_role",
							"label": "Required Approver Role",
							"fieldtype": "Link",
							"options": "Role",
							"read_only": 1,
							"insert_after": "approval_section",
						},
					]
				)

		# Quotation reference field on Purchase Order (optional, for traceability).
		if frappe.db.exists("DocType", "Purchase Order"):
			meta = frappe.get_meta("Purchase Order")
			anchor = _last_insert_anchor_fieldname("Purchase Order")
			if anchor and not meta.has_field("purchase_quotation"):
				custom_fields_map.setdefault("Purchase Order", []).append(
					{
						"fieldname": "purchase_quotation",
						"label": "Purchase Quotation",
						"fieldtype": "Link",
						"options": "Purchase Quotation",
						"insert_after": anchor,
					}
				)

		if custom_fields_map:
			create_custom_fields(custom_fields_map, update=True)
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure_procurement_enterprise_fields")


def ensure_inventory_enterprise_fields():
	"""Add enterprise inventory fields to Item/Warehouse/Stock Entry (non-breaking)."""
	try:
		custom_fields_map = {}

		if frappe.db.exists("DocType", "Item"):
			meta = frappe.get_meta("Item")
			anchor = _last_insert_anchor_fieldname("Item")
			if anchor and not meta.has_field("item_name_ar"):
				custom_fields_map.setdefault("Item", []).extend(
					[
						{"fieldname": "inventory_enterprise_section", "label": "Enterprise Inventory", "fieldtype": "Section Break", "insert_after": anchor},
						{"fieldname": "item_name_ar", "label": "Item Name (Arabic)", "fieldtype": "Data", "insert_after": "inventory_enterprise_section"},
						{"fieldname": "barcode", "label": "Barcode", "fieldtype": "Data", "insert_after": "item_name_ar"},
						{"fieldname": "qr_code", "label": "QR Code", "fieldtype": "Data", "insert_after": "barcode"},
						{"fieldname": "has_serial_no", "label": "Track Serial Numbers", "fieldtype": "Check", "default": "0", "insert_after": "qr_code"},
						{"fieldname": "reorder_level", "label": "Reorder Level", "fieldtype": "Float", "default": "0", "insert_after": "has_serial_no"},
						{"fieldname": "safety_stock", "label": "Safety Stock", "fieldtype": "Float", "default": "0", "insert_after": "reorder_level"},
						{
							"fieldname": "valuation_method",
							"label": "Valuation Method",
							"fieldtype": "Select",
							"options": "FIFO\nWeighted Average",
							"default": "FIFO",
							"insert_after": "safety_stock",
						},
						{"fieldname": "default_purchase_account", "label": "Default Purchase Account", "fieldtype": "Link", "options": "GL Account", "insert_after": "valuation_method"},
						{"fieldname": "default_sales_account", "label": "Default Sales Account", "fieldtype": "Link", "options": "GL Account", "insert_after": "default_purchase_account"},
					]
				)

		if frappe.db.exists("DocType", "Warehouse"):
			meta = frappe.get_meta("Warehouse")
			anchor = _last_insert_anchor_fieldname("Warehouse")
			if anchor and not meta.has_field("warehouse_type"):
				custom_fields_map.setdefault("Warehouse", []).extend(
					[
						{"fieldname": "warehouse_enterprise_section", "label": "Enterprise Warehouse", "fieldtype": "Section Break", "insert_after": anchor},
						{"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch", "insert_after": "warehouse_enterprise_section"},
						{
							"fieldname": "warehouse_type",
							"label": "Warehouse Type",
							"fieldtype": "Select",
							"options": "Main\nSub\nTransit\nPOS",
							"default": "Main",
							"insert_after": "branch",
						},
						{"fieldname": "capacity_qty", "label": "Capacity (Qty)", "fieldtype": "Float", "insert_after": "warehouse_type"},
						{"fieldname": "location_code", "label": "Location/Bin Code", "fieldtype": "Data", "insert_after": "capacity_qty"},
					]
				)

		if frappe.db.exists("DocType", "Stock Entry"):
			meta = frappe.get_meta("Stock Entry")
			anchor = _last_insert_anchor_fieldname("Stock Entry")
			if anchor and not meta.has_field("entry_type"):
				custom_fields_map.setdefault("Stock Entry", []).extend(
					[
						{"fieldname": "inventory_control_section", "label": "Inventory Controls", "fieldtype": "Section Break", "insert_after": anchor, "collapsible": 1},
						{
							"fieldname": "entry_type",
							"label": "Entry Type",
							"fieldtype": "Select",
							"options": "Standard\nStock Adjustment\nOpening Stock",
							"default": "Standard",
							"insert_after": "inventory_control_section",
						},
						{
							"fieldname": "adjustment_reason",
							"label": "Adjustment Reason",
							"fieldtype": "Link",
							"options": "Stock Adjustment Reason",
							"depends_on": "eval:doc.entry_type=='Stock Adjustment' || doc.entry_type=='Opening Stock'",
							"insert_after": "entry_type",
						},
						{"fieldname": "quality_check_required", "label": "Quality Check Required", "fieldtype": "Check", "default": "0", "insert_after": "adjustment_reason"},
						{"fieldname": "transfer_request", "label": "Transfer Request", "fieldtype": "Link", "options": "Stock Transfer Request", "insert_after": "quality_check_required"},
					]
				)

		if custom_fields_map:
			create_custom_fields(custom_fields_map, update=True)
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure_inventory_enterprise_fields")


def ensure_finance_enterprise_fields():
	"""Add enterprise accounting/banking helper fields (non-breaking)."""
	try:
		custom_fields_map = {}

		if frappe.db.exists("DocType", "Journal Entry"):
			meta = frappe.get_meta("Journal Entry")
			anchor = _last_insert_anchor_fieldname("Journal Entry")
			if anchor and not meta.has_field("approval_reference"):
				custom_fields_map.setdefault("Journal Entry", []).extend(
					[
						{"fieldname": "finance_control_section", "label": "Finance Controls", "fieldtype": "Section Break", "insert_after": anchor, "collapsible": 1},
						{"fieldname": "approval_reference", "label": "Approval Reference", "fieldtype": "Data", "insert_after": "finance_control_section"},
						{"fieldname": "approved_by_user", "label": "Approved By User", "fieldtype": "Link", "options": "User", "read_only": 1, "insert_after": "approval_reference"},
						{"fieldname": "required_approval_level", "label": "Required Approval Level", "fieldtype": "Select", "options": "None\nManager\nCFO", "read_only": 1, "insert_after": "approved_by_user"},
					]
				)

		if frappe.db.exists("DocType", "Payment Entry"):
			meta = frappe.get_meta("Payment Entry")
			anchor = _last_insert_anchor_fieldname("Payment Entry")
			if anchor and not meta.has_field("cheque_no"):
				custom_fields_map.setdefault("Payment Entry", []).extend(
					[
						{"fieldname": "banking_control_section", "label": "Banking Controls", "fieldtype": "Section Break", "insert_after": anchor, "collapsible": 1},
						{"fieldname": "cheque_no", "label": "Cheque No.", "fieldtype": "Data", "insert_after": "banking_control_section"},
						{"fieldname": "cheque_date", "label": "Cheque Date", "fieldtype": "Date", "insert_after": "cheque_no"},
						{"fieldname": "value_date", "label": "Value Date", "fieldtype": "Date", "insert_after": "cheque_date"},
						{"fieldname": "required_approval_level", "label": "Required Approval Level", "fieldtype": "Select", "options": "None\nManager\nCFO", "read_only": 1, "insert_after": "value_date"},
						{"fieldname": "approved_by_user", "label": "Approved By User", "fieldtype": "Link", "options": "User", "read_only": 1, "insert_after": "required_approval_level"},
					]
				)

		if frappe.db.exists("DocType", "Bank Reconciliation"):
			meta = frappe.get_meta("Bank Reconciliation")
			anchor = _last_insert_anchor_fieldname("Bank Reconciliation")
			if anchor and not meta.has_field("import_source"):
				custom_fields_map.setdefault("Bank Reconciliation", []).extend(
					[
						{"fieldname": "statement_control_section", "label": "Statement Controls", "fieldtype": "Section Break", "insert_after": anchor, "collapsible": 1},
						{"fieldname": "import_source", "label": "Import Source", "fieldtype": "Select", "options": "Manual\nCSV\nAPI", "default": "Manual", "insert_after": "statement_control_section"},
						{"fieldname": "statement_reference", "label": "Statement Reference", "fieldtype": "Data", "insert_after": "import_source"},
					]
				)

		if custom_fields_map:
			create_custom_fields(custom_fields_map, update=True)
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure_finance_enterprise_fields")


def ensure_finance_workflow_templates():
	"""Seed workflow templates for JE/Payment (best-effort, skip if custom workflows already exist)."""
	try:
		if not frappe.db.exists("DocType", "Workflow"):
			return

		def _has_existing(doc_type: str) -> bool:
			try:
				return bool(frappe.db.get_value("Workflow", {"document_type": doc_type, "is_active": 1}, "name"))
			except Exception:
				return False

		def _make_workflow(name: str, doc_type: str, states: list[dict], transitions: list[dict]):
			if _has_existing(doc_type):
				return
			if frappe.db.exists("Workflow", name):
				return
			wf = frappe.new_doc("Workflow")
			if wf.meta.has_field("workflow_name"):
				wf.workflow_name = name
			wf.document_type = doc_type
			if wf.meta.has_field("workflow_state_field"):
				wf.workflow_state_field = "workflow_state"
			if wf.meta.has_field("is_active"):
				wf.is_active = 1
			if wf.meta.has_field("send_email_alert"):
				wf.send_email_alert = 0

			for s in states:
				wf.append("states", s)
			for t in transitions:
				wf.append("transitions", t)
			wf.insert(ignore_permissions=True)
			frappe.db.commit()

		_make_workflow(
			name="Omnexa Journal Entry Approval",
			doc_type="Journal Entry",
			states=[
				{"state": "Draft", "doc_status": 0, "allow_edit": "Accounts User"},
				{"state": "Manager Approved", "doc_status": 0, "allow_edit": "Accounts Manager"},
				{"state": "CFO Approved", "doc_status": 1, "allow_edit": "CFO"},
			],
			transitions=[
				{"state": "Draft", "action": "Manager Review", "next_state": "Manager Approved", "allowed": "Accounts Manager"},
				{"state": "Manager Approved", "action": "CFO Approve", "next_state": "CFO Approved", "allowed": "CFO"},
			],
		)

		_make_workflow(
			name="Omnexa Payment Entry Approval",
			doc_type="Payment Entry",
			states=[
				{"state": "Draft", "doc_status": 0, "allow_edit": "Accounts User"},
				{"state": "Manager Approved", "doc_status": 0, "allow_edit": "Accounts Manager"},
				{"state": "CFO Approved", "doc_status": 1, "allow_edit": "CFO"},
			],
			transitions=[
				{"state": "Draft", "action": "Manager Review", "next_state": "Manager Approved", "allowed": "Accounts Manager"},
				{"state": "Manager Approved", "action": "CFO Approve", "next_state": "CFO Approved", "allowed": "CFO"},
			],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure_finance_workflow_templates")


def ensure_default_sidebar_workspace_order():
	"""Apply default left-sidebar workspace order across the site."""
	try:
		workspaces = frappe.get_all(
			"Workspace",
			filters={"public": 1, "is_hidden": 0},
			fields=["name", "title", "module", "sequence_id"],
			limit_page_length=1000,
		)
		if not workspaces:
			return

		# Requested fixed order at top.
		priority_buckets = [
			{"dashboard"},
			{"accounting"},
			{"sell", "sales"},
			{"buy", "purchase", "purchasing"},
			{"stock", "inventory", "warehouse"},
			{"hr", "employee", "employees"},
			{"settings", "core"},
			{"marketplace", "market"},
		]

		def norm(text):
			return (text or "").strip().lower()

		def workspace_tokens(ws):
			# For the top fixed order, match by workspace identity (name/title), not module.
			return {norm(ws.get("name")), norm(ws.get("title"))}

		used = set()
		ordered = []
		for bucket in priority_buckets:
			for ws in workspaces:
				if ws["name"] in used:
					continue
				tokens = workspace_tokens(ws)
				if tokens & bucket:
					ordered.append(ws)
					used.add(ws["name"])
					break

		remaining = [ws for ws in workspaces if ws["name"] not in used]

		# Logical fallback by app install order (from installed apps list), then previous sequence/title.
		installed_apps = frappe.get_installed_apps()
		app_rank = {app: idx for idx, app in enumerate(installed_apps)}
		module_rows = frappe.get_all("Module Def", fields=["name", "app_name"], limit_page_length=2000)
		module_to_app = {row.name: row.app_name for row in module_rows}

		def remaining_sort_key(ws):
			app_name = module_to_app.get(ws.get("module"))
			return (
				app_rank.get(app_name, 10_000),
				float(ws.get("sequence_id") or 9999),
				norm(ws.get("title")) or norm(ws.get("name")),
			)

		remaining.sort(key=remaining_sort_key)
		ordered.extend(remaining)

		for idx, ws in enumerate(ordered, start=1):
			frappe.db.set_value("Workspace", ws["name"], "sequence_id", idx, update_modified=False)

		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure default sidebar workspace order")


def ensure_site_runtime_ready():
	"""Prevent stale 'Updating / 503' after app install on fresh environments.

	Some benches keep maintenance/scheduler flags from earlier operations in common/site config.
	Force site runtime to ready state after successful install/migrate flows.
	"""
	try:
		update_site_config("maintenance_mode", 0)
		update_site_config("pause_scheduler", 0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: clear maintenance/pause flags")

	try:
		from frappe.utils.scheduler import enable_scheduler

		enable_scheduler()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: enable scheduler")


def ensure_required_apps_are_registered():
	"""Ensure required apps are present in sites/apps.txt when app folders exist."""
	bench_path = Path(get_bench_path())
	apps_txt = bench_path / "sites" / "apps.txt"
	apps_dir = bench_path / "apps"
	if not apps_txt.exists() or not apps_dir.exists():
		return

	raw_text = apps_txt.read_text(encoding="utf-8")
	lines = raw_text.splitlines()
	current = _repair_apps_txt_entries(lines)
	normalized_text = ("\n".join(current) + "\n") if current else ""
	if normalized_text != raw_text:
		apps_txt.write_text(normalized_text, encoding="utf-8")

	missing_in_txt = []
	for app in _target_site_apps():
		if app in current:
			continue
		if (apps_dir / app).exists():
			missing_in_txt.append(app)

	if not missing_in_txt:
		return

	with apps_txt.open("a", encoding="utf-8") as f:
		# Ensure previous line is terminated to avoid concatenated app names.
		if apps_txt.stat().st_size > 0:
			with apps_txt.open("rb") as r:
				r.seek(-1, 2)
				if r.read(1) != b"\n":
					f.write("\n")
		for app in missing_in_txt:
			f.write(f"{app}\n")


def ensure_global_defaults_compat():
	"""Provide Global Defaults compatibility on sites where this DocType is absent.

	Some custom modules still read `Global Defaults.default_company/default_currency`.
	On environments where this DocType is not present, setup wizard can show
	"DocType Global Defaults not found". This creates a lightweight Single DocType
	once, then seeds basic values from Company if available.
	"""
	if frappe.db.exists("DocType", "Global Defaults"):
		return

	# On pure-Frappe sites (no ERPNext), DocTypes like Company/Currency might not exist.
	# Use Data fields in that case to avoid invalid Link options during DocType validation.
	company_exists = frappe.db.exists("DocType", "Company")
	currency_exists = frappe.db.exists("DocType", "Currency")

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": "Global Defaults",
			"module": "Omnexa Core",
			"custom": 1,
			"issingle": 1,
			"istable": 0,
			"editable_grid": 0,
			"fields": [
				{
					"fieldname": "default_company",
					"label": "Default Company",
					"fieldtype": "Link" if company_exists else "Data",
					"options": "Company" if company_exists else "",
				},
				{
					"fieldname": "default_currency",
					"label": "Default Currency",
					"fieldtype": "Link" if currency_exists else "Data",
					"options": "Currency" if currency_exists else "",
				},
			],
			"permissions": [
				{
					"role": "System Manager",
					"read": 1,
					"write": 1,
					"create": 1,
					"delete": 1,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)

	if not company_exists:
		frappe.clear_cache()
		return

	company = frappe.db.get_value("Company", {}, "name")
	if company:
		frappe.db.set_single_value("Global Defaults", "default_company", company)
		currency = frappe.db.get_value("Company", company, "default_currency")
		if currency:
			frappe.db.set_single_value("Global Defaults", "default_currency", currency)

	frappe.clear_cache()


def ensure_project_contract_link_compat():
	"""Fallback Link->Data when `Project Contract` DocType is unavailable.

	Several PM doctypes use `project` Link fields targeting `Project Contract`.
	On stacks where this DocType is not present, Frappe raises:
	`Field project is referring to non-existing doctype Project Contract`.
	To keep installs/migrations stable, downgrade these links to Data until
	the target DocType is available.
	"""
	if frappe.db.exists("DocType", "Project Contract"):
		return

	patched = 0

	docfields = frappe.get_all(
		"DocField",
		filters={"fieldtype": "Link", "options": "Project Contract"},
		fields=["name", "parent", "fieldname"],
		limit_page_length=500,
	)
	for row in docfields:
		frappe.db.set_value(
			"DocField",
			row["name"],
			{"fieldtype": "Data", "options": ""},
			update_modified=False,
		)
		patched += 1

	custom_fields = frappe.get_all(
		"Custom Field",
		filters={"fieldtype": "Link", "options": "Project Contract"},
		fields=["name", "dt", "fieldname"],
		limit_page_length=500,
	)
	for row in custom_fields:
		frappe.db.set_value(
			"Custom Field",
			row["name"],
			{"fieldtype": "Data", "options": ""},
			update_modified=False,
		)
		patched += 1

	if patched:
		frappe.clear_cache()


def install_required_site_apps():
	"""Install required apps once omnexa_core is installed on a site.

	Important: This runs after omnexa_core install to avoid circular required_apps recursion.
	Frappe installer already skips apps that are already installed.
	"""
	target_apps = _target_site_apps()
	available = set(frappe.get_all_apps())
	installed = set(frappe.get_installed_apps())
	missing_on_disk_required = [app for app in REQUIRED_SITE_APPS if not _app_source_present(app)]

	missing_sources_required = [app for app in REQUIRED_SITE_APPS if app not in available or app in missing_on_disk_required]
	if missing_sources_required:
		ensure_required_apps_fetched()
		ensure_required_apps_are_registered()
		available = set(frappe.get_all_apps())
		missing_on_disk_required = [app for app in REQUIRED_SITE_APPS if not _app_source_present(app)]
		missing_sources_required = [app for app in REQUIRED_SITE_APPS if app not in available or app in missing_on_disk_required]
	_ensure_required_apps_importable()
	if missing_sources_required:
		frappe.throw(
			"Required apps are missing from bench sources/apps.txt (mandatory core set): "
			+ ", ".join(missing_sources_required)
			+ ". Run `bench get-app` for them (or set OMNEXA_AUTO_GET_APPS=1 and ensure `bench` is on PATH), "
			"then install omnexa_core again."
		)

	install_candidates = [app for app in target_apps if app in available and _app_source_present(app)]
	frappe.flags.omnexa_suppress_after_app_workspace_sync = True
	try:
		for app in install_candidates:
			if app in installed:
				continue
			install_site_app(app, verbose=False, set_as_patched=True, force=False)
	finally:
		frappe.flags.omnexa_suppress_after_app_workspace_sync = False


def _missing_source_apps() -> list[str]:
	available = set(frappe.get_all_apps())
	return [app for app in REQUIRED_SITE_APPS if app not in available or not _app_source_present(app)]


def _install_missing_required_apps() -> tuple[list[str], list[str]]:
	target_apps = [app for app in _target_site_apps() if _app_source_present(app)]
	installed = set(frappe.get_installed_apps())
	installed_now = []
	skipped = []
	frappe.flags.omnexa_suppress_after_app_workspace_sync = True
	try:
		for app in target_apps:
			if app in installed:
				skipped.append(app)
				continue
			install_site_app(app, verbose=False, set_as_patched=True, force=False)
			installed_now.append(app)
			installed.add(app)
	finally:
		frappe.flags.omnexa_suppress_after_app_workspace_sync = False
	return installed_now, skipped


@frappe.whitelist()
def sync_stack(run_migrate=1, skip_search_index=1):
	"""One-shot stack sync for omnexa_core required apps.

	Usage:
	bench --site <site> execute "omnexa_core.install.sync_stack"
	bench --site <site> execute "omnexa_core.install.sync_stack" --kwargs "{'run_migrate': 0}"
	"""
	enforce_supported_frappe_version()
	ensure_required_apps_fetched()
	ensure_required_apps_are_registered()

	missing_sources = _missing_source_apps()
	if missing_sources:
		frappe.throw(
			"Required apps are missing from bench (apps.txt): "
			+ ", ".join(missing_sources)
			+ ". Run `bench get-app` for them or enable auto-fetch (OMNEXA_AUTO_GET_APPS=1, `bench` on PATH)."
		)

	installed_now, skipped = _install_missing_required_apps()
	# Ensure workspaces/charts are materialized even when caller skips migrate.
	run_site_hardening_after_app_changes()
	result = {
		"installed_now": installed_now,
		"already_installed": skipped,
		"migrated": False,
	}

	if cint(run_migrate):
		from frappe.migrate import SiteMigration

		site_name = frappe.local.site
		SiteMigration(skip_search_index=bool(cint(skip_search_index))).run(site=site_name)
		result["migrated"] = True

	return result


@frappe.whitelist()
def debug_workspace_payload(workspace_name="Trading"):
	"""Diagnostics: inspect workspace payload as served by Desk API."""
	from frappe.desk.desktop import get_desktop_page

	ws = frappe.get_doc("Workspace", workspace_name)
	payload = get_desktop_page(dumps({"name": ws.name, "title": ws.title, "public": ws.public}))
	charts = ((payload or {}).get("charts") or {}).get("items") or []
	number_cards = ((payload or {}).get("number_cards") or {}).get("items") or []
	shortcuts = ((payload or {}).get("shortcuts") or {}).get("items") or []
	return {
		"workspace": workspace_name,
		"charts_count": len(charts),
		"chart_names": [c.get("chart_name") for c in charts],
		"number_cards_count": len(number_cards),
		"shortcuts_count": len(shortcuts),
	}


@frappe.whitelist()
def force_repair_workspace_charts():
	"""Force-repair Workspace Chart rows from workspace content blocks.

	This bypasses full Workspace save/validation (which may fail on unrelated broken links)
	and keeps chart rows aligned with chart blocks so Desk chart widgets always resolve.
	"""
	workspaces = frappe.get_all("Workspace", fields=["name", "content"])
	patched = 0
	inserted = 0
	missing_dashboard_charts = []

	for ws in workspaces:
		content = ws.get("content") or "[]"
		try:
			blocks = loads(content)
		except Exception:
			blocks = []

		chart_names = []
		for b in blocks:
			if (b or {}).get("type") != "chart":
				continue
			chart_name = ((b or {}).get("data") or {}).get("chart_name")
			if chart_name and chart_name not in chart_names:
				chart_names.append(chart_name)

		if not chart_names:
			continue

		# Keep label identical to chart_name so workspace chart block lookup succeeds.
		frappe.db.sql(
			"""
			UPDATE `tabWorkspace Chart`
			SET label = chart_name
			WHERE parent = %s
			""",
			(ws["name"],),
		)

		existing_rows = frappe.db.sql(
			"""
			SELECT chart_name
			FROM `tabWorkspace Chart`
			WHERE parent = %s
			""",
			(ws["name"],),
			as_list=True,
		)
		existing = {row[0] for row in existing_rows if row and row[0]}

		next_idx = cint(
			frappe.db.sql(
				"SELECT COALESCE(MAX(idx), 0) FROM `tabWorkspace Chart` WHERE parent = %s",
				(ws["name"],),
			)[0][0]
		)

		for chart_name in chart_names:
			if not frappe.db.exists("Dashboard Chart", chart_name):
				missing_dashboard_charts.append({"workspace": ws["name"], "chart_name": chart_name})
				continue
			if chart_name in existing:
				continue

			next_idx += 1
			inserted += 1
			frappe.db.sql(
				"""
				INSERT INTO `tabWorkspace Chart`
					(name, creation, modified, modified_by, owner, docstatus, idx, parent, parentfield, parenttype, chart_name, label)
				VALUES
					(%s, NOW(), NOW(), %s, %s, 0, %s, %s, 'charts', 'Workspace', %s, %s)
				""",
				(
					frappe.generate_hash(length=10),
					frappe.session.user,
					frappe.session.user,
					next_idx,
					ws["name"],
					chart_name,
					chart_name,
				),
			)
		patched += 1

	frappe.db.commit()
	return {
		"patched_workspaces": patched,
		"inserted_rows": inserted,
		"missing_dashboard_charts": missing_dashboard_charts[:100],
		"missing_dashboard_charts_count": len(missing_dashboard_charts),
	}


@frappe.whitelist()
def force_seed_workspace_charts(workspace_name="Fixed Assets", limit=4):
	"""Seed charts for one workspace when chart blocks/rows are missing."""
	limit = max(1, min(cint(limit), 8))
	if not frappe.db.exists("Workspace", workspace_name):
		return {"workspace": workspace_name, "seeded": 0, "reason": "workspace_not_found"}

	ws = frappe.get_doc("Workspace", workspace_name)
	module = ws.module or ""
	title = ws.title or ws.name

	# Pick aggregatable doctypes from same module.
	dts = frappe.get_all(
		"DocType",
		fields=["name"],
		filters={"module": module, "issingle": 0, "is_virtual": 0},
		order_by="modified desc",
		limit_page_length=40,
	)
	doctypes = [d["name"] for d in dts if d.get("name")]
	if not doctypes:
		return {"workspace": workspace_name, "seeded": 0, "reason": "no_doctypes"}

	charts = []
	for dt in doctypes:
		if len(charts) >= limit:
			break
		chart_name = f"{title} · {dt[:28]} Trend"
		if not frappe.db.exists("Dashboard Chart", chart_name):
			doc = frappe.get_doc(
				{
					"doctype": "Dashboard Chart",
					"chart_name": chart_name,
					"module": None,
					"is_public": 1,
					"chart_type": "Count",
					"document_type": dt,
					"based_on": "creation",
					"timeseries": 1,
					"timespan": "Last Month",
					"time_interval": "Daily",
					"type": "Line",
					"filters_json": "[]",
				}
			)
			doc.insert(ignore_permissions=True)
		charts.append(chart_name)

	# Rebuild workspace chart child rows.
	ws.charts = []
	for ch in charts:
		ws.append("charts", {"chart_name": ch, "label": ch})

	# Ensure chart blocks exist in content.
	try:
		blocks = loads(ws.content or "[]")
		if not isinstance(blocks, list):
			blocks = []
	except Exception:
		blocks = []

	blocks = [b for b in blocks if (b or {}).get("type") != "chart"]
	header_idx = None
	for i, b in enumerate(blocks):
		if (b or {}).get("type") == "header":
			text = (((b or {}).get("data") or {}).get("text") or "").lower()
			if "charts" in text:
				header_idx = i
				break

	new_chart_blocks = []
	for i, ch in enumerate(charts):
		new_chart_blocks.append(
			{"id": f"seed-ch-{i}", "type": "chart", "data": {"chart_name": ch, "col": 4}}
		)

	if header_idx is None:
		blocks.append({"id": "seed-ch-h", "type": "header", "data": {"text": "<span class=\"h5\"><b>Charts</b></span>", "col": 12}})
		blocks.extend(new_chart_blocks)
	else:
		blocks[header_idx + 1 : header_idx + 1] = new_chart_blocks

	ws.content = dumps(blocks)
	ws.save(ignore_permissions=True)
	frappe.db.commit()

	return {"workspace": workspace_name, "seeded": len(charts), "chart_names": charts}




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


def remove_legacy_finance_group_stub_workspaces():
	"""Remove Omnexa Core stub workspaces that duplicated real finance apps under Finance Group."""
	for name in (
		"ALM Workspace",
		"Credit Risk Workspace",
		"Credit Engine Workspace",
		"Consumer Finance Workspace",
	):
		if not frappe.db.exists("Workspace", name):
			continue
		try:
			frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: remove_legacy_finance_group_stub {name}")
	frappe.db.commit()


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
	"""Set desk/login logo to the canonical `logo.svg` shipped with omnexa_core.

	We store it as a public File so it works consistently on any new server.
	"""
	bench_path = Path(get_bench_path())

	# Preferred source: packaged file inside omnexa_core.
	app_logo_svg_path = Path(__file__).resolve().parent / "public" / "images" / "logo.svg"
	logo_file_name = "logo.svg"
	logo_file_url = f"/files/{logo_file_name}"

	# Legacy fallback (previous requirement).
	legacy_png_path = bench_path / "Docs" / "OLDDOC" / "docs" / "Docs" / "logo" / "logo.png"
	legacy_png_file_name = "erpgenex-logo.png"
	legacy_png_file_url = f"/files/{legacy_png_file_name}"

	target_logo_url = ""
	try:
		# 1) Canonical logo.svg from inside the app (preferred).
		if app_logo_svg_path.exists():
			# Replace stale File record so content updates.
			for old_file in frappe.get_all("File", filters={"file_url": logo_file_url}, pluck="name"):
				try:
					frappe.delete_doc("File", old_file, force=1, ignore_permissions=True)
				except Exception:
					pass

			save_file(
				logo_file_name,
				app_logo_svg_path.read_bytes(),
				"Navbar Settings",
				"Navbar Settings",
				is_private=0,
			)
			target_logo_url = logo_file_url

		# 2) Optional compatibility: older setups where logo.svg existed in bench root.
		else:
			bench_logo_svg_path = bench_path / "Docs" / "logo.svg"
			if bench_logo_svg_path.exists():
				for old_file in frappe.get_all("File", filters={"file_url": logo_file_url}, pluck="name"):
					try:
						frappe.delete_doc("File", old_file, force=1, ignore_permissions=True)
					except Exception:
						pass

				save_file(
					logo_file_name,
					bench_logo_svg_path.read_bytes(),
					"Navbar Settings",
					"Navbar Settings",
					is_private=0,
				)
				target_logo_url = logo_file_url

			# 3) Legacy PNG fallback (previous requirement).
			elif legacy_png_path.exists():
				for old_file in frappe.get_all("File", filters={"file_url": legacy_png_file_url}, pluck="name"):
					try:
						frappe.delete_doc("File", old_file, force=1, ignore_permissions=True)
					except Exception:
						pass

				save_file(
					legacy_png_file_name,
					legacy_png_path.read_bytes(),
					"Navbar Settings",
					"Navbar Settings",
					is_private=0,
				)
				target_logo_url = legacy_png_file_url

			# 4) Last resort: app-bundled placeholder.
			else:
				target_logo_url = "/assets/omnexa_core/images/erpgenex-logo.svg"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: set navbar app_logo")

	try:
		frappe.db.set_single_value("Navbar Settings", "app_logo", target_logo_url)
		# Login page uses Website Settings.app_logo with higher priority than Navbar Settings.
		# Keep them in sync so /login shows the same logo everywhere.
		if frappe.db.has_column("Website Settings", "app_logo"):
			frappe.db.set_single_value("Website Settings", "app_logo", target_logo_url, update_modified=False)
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
	branch_tax_id = (args.get("omnexa_branch_tax_id") or tax_id).strip()
	business_activity = (args.get("omnexa_business_activity") or "").strip()
	industry_sector = (args.get("omnexa_industry_sector") or "").strip()
	numbering_mode = (args.get("omnexa_account_numbering_mode") or "").strip()
	default_vat_rate = flt(args.get("omnexa_default_vat_rate") or 0)
	enable_starter_coa = cint(args.get("omnexa_enable_starter_coa") or 0)
	seed_demo_data = cint(args.get("omnexa_seed_demo_data") or 0)

	# Keep setup wizard resilient even if user skips the custom slide.
	if not company_name:
		company_name = "My Company"
	if not company_abbr:
		company_abbr = "".join(ch for ch in company_name if ch.isalnum())[:4].upper() or "COMP"
	if not branch_name:
		branch_name = "Main Branch"
	if not branch_code:
		branch_code = "HO"

	currency = (args.get("currency") or "USD").strip() or "USD"
	country = (args.get("omnexa_country") or args.get("country") or "Egypt").strip() or "Egypt"
	use_advanced_numbering = numbering_mode.lower().startswith("advanced")

	# Ensure Custom Field rows exist and tables are altered before first Company/Branch INSERT
	# (avoids Unknown column 'supporting_attachment' if install hooks ran out of order).
	ensure_company_branding_fields()
	ensure_global_supporting_attachment_fields()

	company = _ensure_company(company_name, company_abbr, currency, country, tax_id)
	_apply_company_profile_fields(company, business_activity, industry_sector)
	branch = _ensure_branch(company, branch_name, branch_code, branch_tax_id)
	_ensure_tax_accounts(company, company_abbr, branch_code, default_vat_rate, use_advanced_numbering)
	_set_default_company_branch(company=company, branch=branch, args=args)
	if enable_starter_coa:
		_ensure_starter_chart_of_accounts(
			company=company,
			branch=branch,
			activity=business_activity or industry_sector or "General",
			use_advanced_numbering=use_advanced_numbering,
		)
	if seed_demo_data:
		_seed_demo_data(company=company, branch=branch, activity=business_activity or industry_sector)
	_grant_full_access_to_setup_user(args)


def _apply_company_profile_fields(company: str, business_activity: str, industry_sector: str) -> None:
	if not company:
		return
	try:
		if business_activity:
			if frappe.db.has_column("Company", "business_activity"):
				frappe.db.set_value("Company", company, "business_activity", business_activity, update_modified=False)
			elif frappe.db.has_column("Company", "custom_business_activity"):
				frappe.db.set_value(
					"Company",
					company,
					"custom_business_activity",
					business_activity,
					update_modified=False,
				)
		if industry_sector:
			if frappe.db.has_column("Company", "industry_sector"):
				frappe.db.set_value("Company", company, "industry_sector", industry_sector, update_modified=False)
			elif frappe.db.has_column("Company", "industry"):
				frappe.db.set_value("Company", company, "industry", industry_sector, update_modified=False)
			elif frappe.db.has_column("Company", "custom_industry_sector"):
				frappe.db.set_value(
					"Company",
					company,
					"custom_industry_sector",
					industry_sector,
					update_modified=False,
				)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: apply company profile fields")


def _seed_demo_data(company: str, branch: str, activity: str) -> None:
	try:
		if "omnexa_accounting" not in set(frappe.get_installed_apps()):
			return
		from omnexa_accounting.utils.production_readiness import seed_activity_demo_data
		from omnexa_accounting.utils.demo_workspace_seed import ensure_demo_workspace_seed

		# Seed masters + a small transaction chain, then run the full aligned demo horizon
		# so cross-module reports (sell/buy/stock/accounting) are not empty by default.
		seed_activity_demo_data(
			company=company,
			branch=branch,
			activity=activity or "General",
			include_transactions=1,
		)
		ensure_demo_workspace_seed(company=company, branch=branch, forced=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: setup wizard demo data seed")


def _grant_full_access_to_setup_user(args: dict) -> None:
	"""Grant broad access to the first setup user as requested by project policy."""
	try:
		email = (args.get("email") or "").strip()
		if not email or not frappe.db.exists("User", email):
			return

		user_doc = frappe.get_doc("User", email)
		user_doc.user_type = "System User"
		user_doc.enabled = 1

		# Keep safe exclusions; "Guest"/"All" are not assignable business roles.
		excluded_roles = {"Guest", "All"}
		all_roles = [
			r.name
			for r in frappe.get_all("Role", fields=["name"])
			if r.name not in excluded_roles
		]

		existing = {row.role for row in (user_doc.roles or []) if row.role}
		for role_name in all_roles:
			if role_name in existing:
				continue
			user_doc.append("roles", {"role": role_name})

		user_doc.flags.ignore_permissions = True
		user_doc.save(ignore_permissions=True)

		# Prefer head-office context for first login.
		company = frappe.db.get_single_value("Global Defaults", "default_company") if frappe.db.exists("DocType", "Global Defaults") else None
		if company:
			head_branch = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name")
			if head_branch:
				frappe.db.set_default("Branch", head_branch, parent=email)
			frappe.db.set_default("Company", company, parent=email)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: grant full access to setup user")


def _set_default_company_branch(company: str, branch: str, args: dict) -> None:
	"""Ensure system defaults and the setup user start from head-office branch context."""
	try:
		if company:
			frappe.db.set_default("Company", company)
		if branch:
			frappe.db.set_default("Branch", branch)
		email = (args.get("email") or "").strip()
		if email and frappe.db.exists("User", email):
			if company:
				frappe.db.set_default("Company", company, parent=email)
			if branch:
				frappe.db.set_default("Branch", branch, parent=email)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: set default company/branch")


def _sync_doctype_database_schema(doctype: str) -> None:
	"""Align MySQL columns with DocType meta (custom fields e.g. supporting_attachment).

	Setup wizard can run when Custom Field rows exist but ``updatedb`` was skipped on an edge install path.
	"""
	if not frappe.db.exists("DocType", doctype):
		return
	try:
		frappe.db.updatedb(doctype)
		frappe.clear_cache(doctype=doctype)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Omnexa: updatedb {doctype} (schema sync)")


def _ensure_company(company_name, company_abbr, currency, country, tax_id):
	existing = frappe.db.get_value("Company", {"abbr": company_abbr}, "name")
	if existing:
		return existing

	_sync_doctype_database_schema("Company")

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
	# Setup Wizard may already create a head-office branch before omnexa_core hook runs.
	# Reuse it to avoid: "Only one head office branch is allowed per company."
	existing_head_office = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name")
	if existing_head_office:
		if tax_id and frappe.db.has_column("Branch", "tax_id"):
			current_tax_id = frappe.db.get_value("Branch", existing_head_office, "tax_id")
			if not current_tax_id:
				frappe.db.set_value("Branch", existing_head_office, "tax_id", tax_id, update_modified=False)
		return existing_head_office

	existing_same_code = frappe.db.get_value("Branch", {"company": company, "branch_code": branch_code}, "name")
	if existing_same_code:
		frappe.db.set_value("Branch", existing_same_code, "is_head_office", 1, update_modified=False)
		if tax_id and frappe.db.has_column("Branch", "tax_id"):
			current_tax_id = frappe.db.get_value("Branch", existing_same_code, "tax_id")
			if not current_tax_id:
				frappe.db.set_value("Branch", existing_same_code, "tax_id", tax_id, update_modified=False)
		return existing_same_code

	_sync_doctype_database_schema("Branch")

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


def _normalize_code(value: str | None, length: int = 2, fallback: str = "XX") -> str:
	s = "".join(ch for ch in (value or "").upper() if ch.isalnum())
	if len(s) >= length:
		return s[:length]
	return (s + fallback)[:length]


def _account_type_code(account_type: str | None) -> str:
	return {
		"Asset": "AS",
		"Liability": "LI",
		"Equity": "EQ",
		"Income": "IN",
		"Expense": "EX",
	}.get(account_type or "", "OT")


def _compose_account_number(
	company_abbr: str,
	branch_code: str,
	account_type: str,
	subtype_code: str,
	main_no: str,
	child_no: str,
) -> str:
	# Format requested:
	# Company(2)-Branch(2)-AccountType(2)-SubType(2)-Main(4)-Child(2)
	co = _normalize_code(company_abbr, 2, "CO")
	br = _normalize_code(branch_code, 2, "BR")
	ty = _account_type_code(account_type)
	st = _normalize_code(subtype_code, 2, "GN")
	main = "".join(ch for ch in str(main_no) if ch.isdigit()).zfill(4)[-4:]
	child = "".join(ch for ch in str(child_no) if ch.isdigit()).zfill(2)[-2:]
	return f"{co}-{br}-{ty}-{st}-{main}-{child}"


def _account_no(
	company_abbr: str,
	branch_code: str,
	account_type: str,
	subtype_code: str,
	main_no: str,
	child_no: str,
	use_advanced_numbering: bool,
) -> str:
	if use_advanced_numbering:
		return _compose_account_number(company_abbr, branch_code, account_type, subtype_code, main_no, child_no)
	main = "".join(ch for ch in str(main_no) if ch.isdigit()).zfill(4)[-4:]
	child = "".join(ch for ch in str(child_no) if ch.isdigit()).zfill(2)[-2:]
	return f"{main}{child}"


def _ensure_tax_accounts(company, company_abbr, branch_code, default_vat_rate, use_advanced_numbering):
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Liability", "TX", "2200", "01", use_advanced_numbering),
		"Tax Payable (Output VAT)",
		"Liability",
	)
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Asset", "TX", "1400", "01", use_advanced_numbering),
		"Tax Receivable (Input VAT)",
		"Asset",
	)

	try:
		# has_single is not available on MariaDBDatabase in this stack;
		# guard by checking DocType existence instead.
		if frappe.db.exists("DocType", "Omnexa Core Settings"):
			frappe.db.set_single_value("Omnexa Core Settings", "default_vat_rate", default_vat_rate or 0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: set default VAT rate")


def _ensure_starter_chart_of_accounts(
	company: str,
	branch: str | None = None,
	activity: str | None = None,
	use_advanced_numbering: bool | int = 0,
):
	"""Generate a production-ready IFRS-oriented CoA and seed cost centers.

	The professional CoA lives in `omnexa_accounting.utils.coa_seed_templates.BASE_COA_TEMPLATE`
	and its activity extensions. We apply it from setup wizard so every new company starts
	with a consistent, enterprise-ready hierarchy.
	"""
	try:
		if "omnexa_accounting" not in set(frappe.get_installed_apps()):
			return
		from omnexa_accounting.utils.production_readiness import generate_professional_chart_of_accounts

		generate_professional_chart_of_accounts(company=company, branch=branch, activity=activity or "General")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: setup wizard professional CoA seed failed")

	# Seed simple cost centers for branch / departments / projects.
	try:
		if not frappe.db.exists("DocType", "Cost Center"):
			return
		cc_names = [
			f"{branch} – Branch" if branch else "Head Office – Branch",
			"Sales – Department",
			"Purchasing – Department",
			"Warehouse – Department",
			"Manufacturing – Department",
			"Finance – Department",
			"Administration – Department",
			"Projects – Cost Center",
		]
		for cc in cc_names:
			if frappe.db.exists("Cost Center", {"company": company, "cost_center_name": cc}):
				continue
			doc = frappe.get_doc({"doctype": "Cost Center", "company": company, "cost_center_name": cc})
			doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: setup wizard cost center seed failed")


def _ensure_gl_account(
	company,
	account_number,
	account_name,
	account_type,
	parent_account=None,
	is_group=0,
	pl_bucket=None,
):
	def _apply_gl_labels(gl_doc) -> None:
		account_name_value = (gl_doc.account_name or "").strip()
		account_number_value = (gl_doc.account_number or "").strip()
		gl_doc.account_label = account_name_value or _("Unnamed Account")
		gl_doc.tree_label = (
			f"{account_name_value} - {account_number_value}"
			if account_name_value and account_number_value
			else (account_name_value or account_number_value or _("Unnamed Account"))
		)

	def _ensure_gl_account_doctype_binding() -> None:
		"""Ensure GL Account DocType points to omnexa_accounting controller.

		On some restored/misaligned databases, `DocType.module/app` for "GL Account" may incorrectly
		point to `frappe.core...`, which causes setup wizard to crash when `frappe.get_doc` tries to
		import the controller.
		"""
		try:
			if not frappe.db.exists("DocType", "GL Account"):
				return
			# Frappe v15 has `app` column on DocType; keep backwards-safe access.
			fields = ["module"]
			if frappe.db.has_column("DocType", "app"):
				fields.append("app")
			if frappe.db.has_column("DocType", "custom"):
				fields.append("custom")
			row = frappe.db.get_value("DocType", "GL Account", fields, as_dict=True) or {}

			current_module = (row.get("module") or "").strip()
			current_app = (row.get("app") or "").strip()
			# Desired binding for controller: omnexa_accounting/omnexa_accounting/doctype/gl_account/gl_account.py
			desired_module = "Omnexa Accounting"
			desired_app = "omnexa_accounting"

			needs_fix = False
			if current_module.lower() in {"core", "frappe"}:
				needs_fix = True
			if current_app and current_app.lower() == "frappe":
				needs_fix = True

			if needs_fix:
				frappe.db.set_value("DocType", "GL Account", "module", desired_module, update_modified=False)
				if frappe.db.has_column("DocType", "app"):
					frappe.db.set_value("DocType", "GL Account", "app", desired_app, update_modified=False)
				frappe.clear_cache(doctype="GL Account")
		except Exception:
			# Never fail setup wizard due to a repair attempt; original error will surface if still broken.
			frappe.log_error(frappe.get_traceback(), "Omnexa: ensure GL Account DocType binding")

	_ensure_gl_account_doctype_binding()

	if not frappe.db.exists("DocType", "GL Account"):
		frappe.throw(
			_("GL Account DocType is missing. Please run bench migrate / install omnexa_accounting."),
			title=_("Setup Wizard"),
		)

	existing = frappe.db.get_value(
		"GL Account",
		{"company": company, "account_number": account_number},
		"name",
	)
	if existing:
		# Legacy wizard runs may have created rows with missing labels.
		try:
			existing_doc = frappe.get_doc("GL Account", existing)
			if not (existing_doc.account_label or "").strip() or not (existing_doc.tree_label or "").strip():
				_apply_gl_labels(existing_doc)
				existing_doc.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Omnexa: backfill existing GL labels in setup")
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
	_apply_gl_labels(doc)
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


def ensure_company_branding_fields():
	"""Ensure Company has a dedicated logo field for branding."""
	try:
		if not frappe.db.exists("DocType", "Company"):
			return
		meta = frappe.get_meta("Company")
		if meta.has_field("company_logo"):
			return

		anchor = _last_insert_anchor_fieldname("Company")
		if not anchor:
			return

		create_custom_fields(
			{
				"Company": [
					{
						"fieldname": "branding_section",
						"label": "Branding",
						"fieldtype": "Section Break",
						"insert_after": anchor,
					},
					{
						"fieldname": "company_logo",
						"label": "Company Logo",
						"fieldtype": "Attach Image",
						"insert_after": "branding_section",
						"description": "Used as desk app logo when this company is active/default.",
					},
				]
			},
			update=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: ensure_company_branding_fields")


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
