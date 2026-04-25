# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import os
import shutil
import subprocess
from pathlib import Path

import frappe
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
]

# Auto `bench get-app` for REQUIRED_SITE_APPS when sources are missing (set OMNEXA_AUTO_GET_APPS=0 to disable).
DEFAULT_APPS_GIT_ORG = os.environ.get("ERPGENEX_GITHUB_ORG", "ErpGenex")
DEFAULT_APPS_GIT_BRANCH = os.environ.get("OMNEXA_APPS_BRANCH", "develop")


def _auto_get_apps_enabled() -> bool:
	return str(os.environ.get("OMNEXA_AUTO_GET_APPS", "1")).strip().lower() not in (
		"0",
		"false",
		"no",
		"off",
	)


def _required_app_hooks_path(app: str) -> Path:
	return Path(get_bench_path()) / "apps" / app / app / "hooks.py"


def _app_source_present(app: str) -> bool:
	return _required_app_hooks_path(app).is_file()


def _run_bench_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
	bench_cmd = shutil.which("bench")
	if not bench_cmd:
		frappe.throw(
			"The `bench` CLI is not in PATH; cannot clone ErpGenEx apps automatically. "
			"Add bench to PATH or run `bench get-app` for missing apps, then install omnexa_core again."
		)
	bench_path = get_bench_path()
	return subprocess.run(
		[bench_cmd, *args],
		cwd=bench_path,
		capture_output=True,
		text=True,
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

	missing = [app for app in REQUIRED_SITE_APPS if not _app_source_present(app)]
	if not missing:
		return

	org = (os.environ.get("ERPGENEX_GITHUB_ORG") or DEFAULT_APPS_GIT_ORG).strip()
	branch = (os.environ.get("OMNEXA_APPS_BRANCH") or DEFAULT_APPS_GIT_BRANCH).strip()

	for app in missing:
		url = f"https://github.com/{org}/{app}.git"
		_bench_cli_or_throw(
			["get-app", url, "--branch", branch, "--skip-assets"],
			f"Failed to fetch app `{app}` from {url} (branch {branch}).",
		)

	_bench_cli_or_throw(
		["setup", "requirements"],
		"Fetched required apps but `bench setup requirements` failed.",
	)


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
	ensure_global_supporting_attachment_fields()
	remove_legacy_people_workspace()
	remove_legacy_finance_workspace()
	remove_legacy_finance_group_stub_workspaces()
	run_workspace_desk_sync()
	ensure_site_runtime_ready()


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

	current = [line.strip() for line in apps_txt.read_text().splitlines() if line.strip()]
	missing_in_txt = []
	for app in REQUIRED_SITE_APPS:
		if app in current:
			continue
		if (apps_dir / app).exists():
			missing_in_txt.append(app)

	if not missing_in_txt:
		return

	with apps_txt.open("a", encoding="utf-8") as f:
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


def install_required_site_apps():
	"""Install required apps once omnexa_core is installed on a site.

	Important: This runs after omnexa_core install to avoid circular required_apps recursion.
	Frappe installer already skips apps that are already installed.
	"""
	available = set(frappe.get_all_apps())
	installed = set(frappe.get_installed_apps())

	missing_sources = [app for app in REQUIRED_SITE_APPS if app not in available]
	if missing_sources:
		ensure_required_apps_fetched()
		ensure_required_apps_are_registered()
		available = set(frappe.get_all_apps())
		missing_sources = [app for app in REQUIRED_SITE_APPS if app not in available]
	if missing_sources:
		frappe.throw(
			"Required apps are missing from bench (apps.txt): "
			+ ", ".join(missing_sources)
			+ ". Run `bench get-app` for them (or set OMNEXA_AUTO_GET_APPS=1 and ensure `bench` is on PATH), "
			"then install omnexa_core again."
		)

	frappe.flags.omnexa_suppress_after_app_workspace_sync = True
	try:
		for app in REQUIRED_SITE_APPS:
			if app in installed:
				continue
			install_site_app(app, verbose=False, set_as_patched=True, force=False)
	finally:
		frappe.flags.omnexa_suppress_after_app_workspace_sync = False


def _missing_source_apps() -> list[str]:
	available = set(frappe.get_all_apps())
	return [app for app in REQUIRED_SITE_APPS if app not in available]


def _install_missing_required_apps() -> tuple[list[str], list[str]]:
	installed = set(frappe.get_installed_apps())
	installed_now = []
	skipped = []
	frappe.flags.omnexa_suppress_after_app_workspace_sync = True
	try:
		for app in REQUIRED_SITE_APPS:
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

	company = _ensure_company(company_name, company_abbr, currency, country, tax_id)
	_apply_company_profile_fields(company, business_activity, industry_sector)
	branch = _ensure_branch(company, branch_name, branch_code, branch_tax_id)
	_ensure_tax_accounts(company, company_abbr, branch_code, default_vat_rate, use_advanced_numbering)
	_set_default_company_branch(company=company, branch=branch, args=args)
	if enable_starter_coa:
		_ensure_starter_chart_of_accounts(company, company_abbr, branch_code, use_advanced_numbering)
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

		seed_activity_demo_data(
			company=company,
			branch=branch,
			activity=activity or "General",
			include_transactions=0,
		)
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


def _ensure_starter_chart_of_accounts(company, company_abbr, branch_code, use_advanced_numbering):
	root_assets = _ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Asset", "CA", "1000", "00", use_advanced_numbering),
		"Assets",
		"Asset",
		is_group=1,
	)
	root_liabilities = _ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Liability", "AP", "2000", "00", use_advanced_numbering),
		"Liabilities",
		"Liability",
		is_group=1,
	)
	root_equity = _ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Equity", "OE", "3000", "00", use_advanced_numbering),
		"Equity",
		"Equity",
		is_group=1,
	)
	root_income = _ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Income", "RV", "4000", "00", use_advanced_numbering),
		"Income",
		"Income",
		is_group=1,
	)
	root_expense = _ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Expense", "OE", "5000", "00", use_advanced_numbering),
		"Expenses",
		"Expense",
		is_group=1,
	)

	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Asset", "CS", "1100", "01", use_advanced_numbering),
		"Cash",
		"Asset",
		parent_account=root_assets,
	)
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Asset", "AR", "1200", "01", use_advanced_numbering),
		"Accounts Receivable",
		"Asset",
		parent_account=root_assets,
	)
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Liability", "AP", "2100", "01", use_advanced_numbering),
		"Accounts Payable",
		"Liability",
		parent_account=root_liabilities,
	)
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Equity", "OE", "3100", "01", use_advanced_numbering),
		"Owner Equity",
		"Equity",
		parent_account=root_equity,
	)
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Income", "RV", "4100", "01", use_advanced_numbering),
		"Sales Revenue",
		"Income",
		parent_account=root_income,
		pl_bucket="Revenue",
	)
	_ensure_gl_account(
		company,
		_account_no(company_abbr, branch_code, "Expense", "OE", "5100", "01", use_advanced_numbering),
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
