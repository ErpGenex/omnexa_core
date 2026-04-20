from __future__ import annotations

import glob
import hashlib
import hmac
import importlib
import os
import subprocess
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import frappe
from frappe.utils import get_app_version, get_bench_path
from frappe.utils.backups import new_backup

from omnexa_core.omnexa_core.omnexa_license import (
	TRIAL_DAYS,
	clear_license_key,
	clear_trial_for_app,
	get_stored_license_key,
	is_free_app,
	record_online_license_check,
	set_license_key,
	set_manual_revoke,
	verify_app_license,
)


def _platform_base_url() -> str:
	configured = str(frappe.conf.get("omnexa_marketplace_url") or "").strip().rstrip("/")
	official = "https://erpgenex.com"
	if configured.startswith(official):
		return configured
	return official


def _catalog_exclude() -> set[str]:
	"""Apps never shown in marketplace (bench core)."""
	out = {"frappe"}
	raw = frappe.conf.get("omnexa_marketplace_catalog_exclude")
	if isinstance(raw, (list, tuple, set)):
		for x in raw:
			if isinstance(x, str) and x.strip():
				out.add(x.strip())
	elif isinstance(raw, str) and raw.strip():
		out.update(s.strip() for s in raw.split(",") if s.strip())
	return out


def _marketplace_catalog_slugs() -> list[str]:
	"""
	All marketplace rows share one GitHub org/base URL pattern via ``_approved_repo_for_app``.

	- Default: every app returned by ``get_all_apps`` except excluded (always ``frappe``).
	- Optional ``omnexa_marketplace_catalog_slugs`` (list): replace the default list entirely.
	- Optional ``omnexa_marketplace_extra_catalog_slugs`` (list): add slugs not yet on bench (install uses get-app).
	"""
	override = frappe.conf.get("omnexa_marketplace_catalog_slugs")
	if isinstance(override, (list, tuple)):
		return sorted({str(x).strip() for x in override if str(x).strip()})

	try:
		on_bench = list(frappe.get_all_apps(with_internal_apps=True) or [])
	except TypeError:
		on_bench = list(frappe.get_all_apps() or [])
	exc = _catalog_exclude()
	slugs = {a for a in on_bench if isinstance(a, str) and a and a not in exc}

	extra = frappe.conf.get("omnexa_marketplace_extra_catalog_slugs") or []
	if isinstance(extra, (list, tuple)):
		slugs.update(str(x).strip() for x in extra if isinstance(x, str) and str(x).strip())

	return sorted(slugs)


def _title_from_slug(app_slug: str) -> str:
	parts = [p for p in app_slug.replace("omnexa_", "").split("_") if p]
	if not parts:
		return app_slug
	return " ".join(p.capitalize() for p in parts)


def _app_display_meta(app_slug: str) -> tuple[str, str]:
	"""
	Human title and short description for the marketplace.

	Priority: ``site_config`` overrides → ``{app}.hooks`` (``app_title``, ``app_description``) → derived title / empty description.

	Optional ``site_config`` dicts:

	- ``omnexa_marketplace_app_titles``: ``{ "omnexa_accounting": "Custom title" }``
	- ``omnexa_marketplace_app_descriptions``: ``{ "omnexa_accounting": "..." }``
	"""
	title_ov = frappe.conf.get("omnexa_marketplace_app_titles") or {}
	desc_ov = frappe.conf.get("omnexa_marketplace_app_descriptions") or {}

	title_from_conf = None
	if isinstance(title_ov, dict):
		v = title_ov.get(app_slug)
		if isinstance(v, str) and v.strip():
			title_from_conf = v.strip()

	desc_from_conf = None
	if isinstance(desc_ov, dict):
		v = desc_ov.get(app_slug)
		if isinstance(v, str) and v.strip():
			desc_from_conf = v.strip()

	app_title = None
	app_description = None
	try:
		mod = importlib.import_module(f"{app_slug}.hooks")
		app_title = getattr(mod, "app_title", None)
		app_description = getattr(mod, "app_description", None)
	except Exception:
		pass

	title = title_from_conf
	if not title:
		if isinstance(app_title, str) and app_title.strip():
			title = app_title.strip()
		else:
			title = _title_from_slug(app_slug)

	if desc_from_conf is not None:
		description = desc_from_conf
	elif isinstance(app_description, str) and app_description.strip():
		description = app_description.strip()
	else:
		description = ""

	return title, description


def _guess_icon_path(app_slug: str) -> str:
	"""Resolve icon from app public assets; fallback to generic icon."""
	try:
		app_path = frappe.get_app_path(app_slug)
	except Exception:
		return "/assets/frappe/images/frappe-framework-logo.svg"

	public_path = os.path.join(app_path, "public")
	if not os.path.isdir(public_path):
		return "/assets/frappe/images/frappe-framework-logo.svg"

	patterns = [
		os.path.join(public_path, "**", "*icon*.svg"),
		os.path.join(public_path, "**", "*logo*.svg"),
		os.path.join(public_path, "**", "*.svg"),
		os.path.join(public_path, "**", "*icon*.png"),
		os.path.join(public_path, "**", "*logo*.png"),
		os.path.join(public_path, "**", "*.png"),
	]
	for pat in patterns:
		matches = glob.glob(pat, recursive=True)
		if matches:
			rel = os.path.relpath(matches[0], public_path).replace(os.sep, "/")
			return f"/assets/{app_slug}/{rel}"

	return "/assets/frappe/images/frappe-framework-logo.svg"


def _catalog_seed() -> list[dict]:
	rows = []
	for app_slug in _marketplace_catalog_slugs():
		display_title, short_description = _app_display_meta(app_slug)
		rows.append(
			{
				"app_slug": app_slug,
				"title": display_title,
				"short_description": short_description,
				"price_type": "free" if is_free_app(app_slug) else "paid",
				"icon_url": _guess_icon_path(app_slug),
				"activity": _activity_for_app(app_slug),
			}
		)
	return rows


def _activity_for_app(app_slug: str) -> str:
	"""Resolve app activity/domain for marketplace filtering."""
	custom = frappe.conf.get("omnexa_marketplace_activity_map") or {}
	if isinstance(custom, dict):
		val = custom.get(app_slug)
		if isinstance(val, str) and val.strip():
			return val.strip()

	if app_slug.startswith("erpgenex_"):
		return "ErpGenEx"
	parts = [p for p in app_slug.replace("omnexa_", "").split("_") if p]
	if not parts:
		return "General"
	if "finance" in parts:
		return "Finance"
	if "risk" in parts:
		return "Risk"
	if "rental" in parts or "vehicle" in parts:
		return "Mobility"
	if "healthcare" in parts:
		return "Healthcare"
	if "education" in parts:
		return "Education"
	if "construction" in parts:
		return "Construction"
	if "agriculture" in parts:
		return "Agriculture"
	if "manufacturing" in parts:
		return "Manufacturing"
	if "trading" in parts:
		return "Trading"
	if "tourism" in parts:
		return "Tourism"
	if "restaurant" in parts:
		return "Restaurant"
	return parts[0].capitalize()


def _app_updated_at(app_slug: str) -> str:
	"""Best-effort app update timestamp (UTC ISO) from app directory mtime."""
	try:
		app_path = frappe.get_app_path(app_slug)
		ts = os.path.getmtime(app_path)
		return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
	except Exception:
		return ""


def _github_base_url() -> str:
	return str(frappe.conf.get("omnexa_marketplace_github_org") or "https://github.com/ErpGenex").rstrip("/")


def _assert_marketplace_app_slug(app_slug: str) -> None:
	if not app_slug or not isinstance(app_slug, str):
		frappe.throw(frappe._("Invalid app slug."))
	if app_slug not in set(_marketplace_catalog_slugs()):
		frappe.throw(frappe._("This app is not in the marketplace catalog."))


def _is_truthy(value) -> bool:
	return value in (1, True, "1", "true", "True", "yes", "on")


def _auto_install_enabled() -> bool:
	return _is_truthy(frappe.conf.get("omnexa_marketplace_auto_install"))


def _bundle_mode_enabled() -> bool:
	"""
	When enabled, marketplace actions do not require per-app license purchase/activation.
	This supports a single bundle/commercial model for all Omnexa apps on the site.
	"""
	return _is_truthy(frappe.conf.get("omnexa_marketplace_bundle_mode"))


def _catalog_show_real_license_status() -> bool:
	"""
	When True, catalog rows use ``verify_app_license`` instead of forcing ``licensed_bundle``.
	Use for testing (developer_mode) or explicit site_config.
	"""
	if _is_truthy(frappe.conf.get("omnexa_marketplace_show_real_license_status")):
		return True
	return bool(frappe.conf.get("developer_mode"))


def _license_help_banner_html(bundle_mode: bool, use_real: bool) -> str:
	"""HTML snippets for marketplace meta (Desk)."""
	parts = []
	if bundle_mode and not use_real:
		parts.append(
			'<div class="alert alert-warning mb-2">'
			+ frappe._(
				"Bundle mode is active: every app shows as licensed_bundle and license prompts are hidden. "
				"To test per-app trial and activation, set {0} to 1 in site_config.json, or enable developer_mode on this site."
			).format("<code>omnexa_marketplace_show_real_license_status</code>")
			+ "</div>"
		)
	if use_real and bundle_mode:
		parts.append(
			'<div class="alert alert-info mb-2">'
			+ frappe._(
				"You are viewing real license/trial status while bundle mode is still on for server-side rules where applicable. "
				"See {0} for test keys and JWT notes."
			).format(
				'<a href="https://github.com/ErpGenex/omnexa_core/blob/develop/docs/LICENSE_TESTING.md" target="_blank" rel="noopener noreferrer">LICENSE_TESTING.md</a>'
			)
			+ "</div>"
		)
	elif not bundle_mode:
		parts.append(
			'<div class="alert alert-secondary mb-2 small">'
			+ frappe._("Trial length: {0} days without a key (paid apps). Help: {1}").format(
				int(TRIAL_DAYS),
				'<a href="https://github.com/ErpGenex/omnexa_core/blob/develop/docs/LICENSE_TESTING.md" target="_blank" rel="noopener noreferrer">LICENSE_TESTING.md</a>',
			)
			+ "</div>"
		)
	return "".join(parts) if parts else ""


def _approved_repo_for_app(app_slug: str) -> str:
	repos = frappe.conf.get("omnexa_marketplace_repos") or {}
	if isinstance(repos, dict) and isinstance(repos.get(app_slug), str) and repos.get(app_slug).strip():
		return repos.get(app_slug).strip()
	return f"{_github_base_url()}/{app_slug}.git"


def _app_highlights(app_slug: str) -> str:
	raw = frappe.conf.get("omnexa_marketplace_whats_new") or {}
	if isinstance(raw, dict) and isinstance(raw.get(app_slug), str) and raw.get(app_slug).strip():
		return raw.get(app_slug).strip()
	return "Latest security fixes, performance improvements, and updated module capabilities."


def _run_bench_cmd(args: list[str]) -> tuple[bool, str]:
	bench_path = get_bench_path()
	try:
		p = subprocess.run(
			["bench", *args],
			cwd=bench_path,
			capture_output=True,
			text=True,
			check=False,
		)
		output = (p.stdout or "") + "\n" + (p.stderr or "")
		return p.returncode == 0, output[-3000:]
	except Exception:
		return False, frappe.get_traceback()[-3000:]


def _git_pull_app(app_slug: str) -> tuple[bool, str]:
	"""Pull latest commits for ``apps/<app_slug>`` (must be a git checkout)."""
	app_root = os.path.join(get_bench_path(), "apps", app_slug)
	git_dir = os.path.join(app_root, ".git")
	if not os.path.isdir(app_root) or not os.path.isdir(git_dir):
		return False, "missing_app_or_git"
	try:
		p = subprocess.run(
			["git", "-C", app_root, "pull"],
			capture_output=True,
			text=True,
			check=False,
			timeout=600,
		)
		output = (p.stdout or "") + "\n" + (p.stderr or "")
		return p.returncode == 0, output[-3000:]
	except Exception:
		return False, frappe.get_traceback()[-3000:]


def _license_allows_marketplace_action(app_slug: str) -> None:
	if _bundle_mode_enabled():
		return
	st = verify_app_license(app_slug).status
	if st not in ("licensed", "licensed_free", "licensed_dev_override", "trial"):
		frappe.throw(
			frappe._("A valid license or trial is required for this action."),
			title=frappe._("License"),
		)


def _ensure_app_present_from_repo(app_slug: str, repo_url: str, branch: str | None = None) -> dict:
	if _can_install_on_this_site(app_slug):
		return {"fetched": False, "message": "app_already_present_on_server"}

	args = ["get-app", app_slug, repo_url]
	if branch:
		args += ["--branch", branch]
	ok, out = _run_bench_cmd(args)
	if not ok:
		return {"fetched": False, "message": "get_app_failed", "output": out}
	return {"fetched": True, "message": "fetched_from_github", "output": out}


def _backup_before_install() -> dict:
	try:
		backup = new_backup(force=True, ignore_files=False, compress=True, verbose=False)
		return {
			"ok": True,
			"message": "backup_created",
			"backup_path_db": getattr(backup, "backup_path_db", None),
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Marketplace Backup Failed")
		return {"ok": False, "message": "backup_failed"}


def _can_install_on_this_site(app_slug: str) -> bool:
	try:
		all_apps = set(frappe.get_all_apps(with_internal_apps=True) or [])
	except TypeError:
		all_apps = set(frappe.get_all_apps() or [])
	return app_slug in all_apps


def _install_app_if_needed(app_slug: str, repo_url: str, require_confirmation: bool = True) -> dict:
	"""Install app on current site when available and not yet installed."""
	if require_confirmation:
		return {"installed": False, "message": "confirmation_required"}

	backup_state = _backup_before_install()
	if not backup_state.get("ok"):
		return {"installed": False, "message": "backup_failed"}

	fetch_state = _ensure_app_present_from_repo(app_slug, repo_url)
	if fetch_state.get("message") == "get_app_failed":
		return {"installed": False, "message": "get_app_failed", "output": fetch_state.get("output")}

	installed = set(frappe.get_installed_apps() or [])
	if app_slug in installed:
		return {
			"installed": True,
			"message": "already_installed",
			"backup": backup_state,
			"fetch": fetch_state,
		}
	if not _can_install_on_this_site(app_slug):
		return {"installed": False, "message": "app_not_present_on_server", "backup": backup_state}
	try:
		from frappe.installer import install_app as _install_app

		_install_app(app_slug, verbose=False, set_as_patched=True, force=False)
		frappe.clear_cache()
		version = get_app_version(app_slug)
		return {
			"installed": True,
			"message": "installed_now",
			"version": version,
			"backup": backup_state,
			"fetch": fetch_state,
			"whats_new": _app_highlights(app_slug),
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Marketplace Auto Install Failed")
		return {"installed": False, "message": "install_failed"}


@frappe.whitelist()
def get_marketplace_catalog():
	"""Return catalog for desk marketplace page."""
	items = []
	bundle_mode = _bundle_mode_enabled()
	use_real = _catalog_show_real_license_status()
	for row in _catalog_seed():
		app = row["app_slug"]
		if bundle_mode and not use_real:
			status = "licensed_bundle"
		else:
			status = verify_app_license(app).status
		items.append(
			{
				**row,
				"is_free": is_free_app(app),
				"is_installed": app in (frappe.get_installed_apps() or []),
				"license_status": status,
				"has_stored_license_key": bool(get_stored_license_key(app)),
				"approved_repo": _approved_repo_for_app(app),
				"current_version": get_app_version(app) if app in (frappe.get_installed_apps() or []) else "",
				"updated_at": _app_updated_at(app),
				"whats_new": _app_highlights(app),
			}
		)
	return {
		"platform_url": _platform_base_url(),
		"github_base": _github_base_url(),
		"support_email": str(frappe.conf.get("omnexa_support_email") or "info@erpgenex.com"),
		"bundle_mode": bundle_mode,
		"catalog_uses_real_license_status": use_real,
		"trial_days": int(TRIAL_DAYS),
		"license_help_html": _license_help_banner_html(bundle_mode, use_real),
		"items": items,
	}


@frappe.whitelist()
def revoke_app_license(app_slug: str, remove_key: int = 1, clear_trial: int = 0):
	"""
	Remove stored license key and/or reset trial clock (System Manager).
	Free apps: only trial reset is allowed (no key to remove).
	"""
	frappe.only_for("System Manager")
	_assert_marketplace_app_slug(app_slug)
	if not app_slug.startswith("omnexa_"):
		frappe.throw(frappe._("Only Omnexa apps (omnexa_*) support this action."))

	remove_key = bool(int(remove_key or 0))
	clear_trial = bool(int(clear_trial or 0))
	if not remove_key and not clear_trial:
		frappe.throw(frappe._("Choose at least one: remove stored key or reset trial."))

	if is_free_app(app_slug):
		if remove_key:
			frappe.throw(frappe._("This app is free: there is no license key to remove."))
		clear_trial_for_app(app_slug)
		frappe.clear_cache()
		return {"ok": True, "status": verify_app_license(app_slug).status}

	if remove_key:
		clear_license_key(app_slug)
		set_manual_revoke(app_slug, True)
	if clear_trial:
		clear_trial_for_app(app_slug)
	frappe.clear_cache()
	return {"ok": True, "status": verify_app_license(app_slug).status}


@frappe.whitelist()
def get_checkout_url(app_slug: str, months: int = 12):
	_assert_marketplace_app_slug(app_slug)
	months = int(months or 12)
	if months < 1 or months > 36:
		frappe.throw(frappe._("License months must be between 1 and 36."))

	base = _platform_base_url()
	return {"url": base}


@frappe.whitelist()
def activate_app_license(app_slug: str, activation_key: str):
	"""Save customer key (or developer code) only when verification accepts it."""
	if not app_slug or not app_slug.startswith("omnexa_"):
		frappe.throw(frappe._("License activation is only supported for Omnexa apps (omnexa_*)."))
	previous = get_stored_license_key(app_slug)
	set_license_key(app_slug=app_slug, license_value=activation_key)
	status = verify_app_license(app_slug)
	if status.status not in ("licensed", "licensed_free", "licensed_dev_override", "trial"):
		if previous:
			set_license_key(app_slug=app_slug, license_value=previous)
		else:
			clear_license_key(app_slug)
		frappe.throw(
			frappe._("License key was not accepted: {0}").format(status.status),
			title=frappe._("License"),
		)
	# Online activation moment counts as a fresh online validation.
	set_manual_revoke(app_slug, False)
	record_online_license_check(app_slug)
	install_result = {"installed": False, "message": "auto_install_disabled"}
	if _auto_install_enabled():
		install_result = _install_app_if_needed(
			app_slug,
			repo_url=_approved_repo_for_app(app_slug),
			require_confirmation=False,
		)
	frappe.clear_cache()
	return {"status": status.status, "reason": status.reason, "install": install_result}


@frappe.whitelist()
def get_install_plan(app_slug: str):
	_assert_marketplace_app_slug(app_slug)
	return {
		"app_slug": app_slug,
		"repo_url": _approved_repo_for_app(app_slug),
		"is_installed": app_slug in (frappe.get_installed_apps() or []),
		"current_version": get_app_version(app_slug) if app_slug in (frappe.get_installed_apps() or []) else "",
		"whats_new": _app_highlights(app_slug),
		"warning": "A full backup will be created before installation to avoid data loss.",
	}


@frappe.whitelist()
def get_update_plan(app_slug: str):
	"""Return metadata for updating an already-installed app from its Git remote."""
	_assert_marketplace_app_slug(app_slug)
	installed = frappe.get_installed_apps() or []
	if app_slug not in installed:
		frappe.throw(frappe._("App must be installed before it can be updated from here."))
	return {
		"app_slug": app_slug,
		"repo_url": _approved_repo_for_app(app_slug),
		"current_version": get_app_version(app_slug),
		"whats_new": _app_highlights(app_slug),
		"warning": "A full backup will be created, then git pull, migrate this site, and build assets for this app.",
	}


@frappe.whitelist()
def update_app_now(app_slug: str, confirm_update: int = 0):
	"""Pull latest code for an installed app, migrate current site, and build assets."""
	_assert_marketplace_app_slug(app_slug)
	if not _is_truthy(confirm_update):
		return {"updated": False, "message": "confirmation_required"}

	_license_allows_marketplace_action(app_slug)
	installed = frappe.get_installed_apps() or []
	if app_slug not in installed:
		frappe.throw(frappe._("App is not installed on this site."))

	backup_state = _backup_before_install()
	if not backup_state.get("ok"):
		return {"updated": False, "message": "backup_failed"}

	ok_pull, out_pull = _git_pull_app(app_slug)
	if not ok_pull:
		return {
			"updated": False,
			"message": "git_pull_failed",
			"output": out_pull,
			"backup": backup_state,
		}

	site = getattr(frappe.local, "site", None) or getattr(frappe.conf, "site_name", None)
	if not site:
		return {"updated": False, "message": "missing_site_context", "backup": backup_state}

	ok_mig, out_mig = _run_bench_cmd(["--site", site, "migrate"])
	if not ok_mig:
		return {
			"updated": False,
			"message": "migrate_failed",
			"output": out_mig,
			"backup": backup_state,
			"pulled": True,
		}

	ok_build, out_build = _run_bench_cmd(["build", "--app", app_slug])
	frappe.clear_cache()
	version = get_app_version(app_slug)
	return {
		"updated": True,
		"message": "updated_now",
		"version": version,
		"backup": backup_state,
		"build_ok": ok_build,
		"build_log_tail": out_build[-1500:] if out_build else "",
	}


@frappe.whitelist()
def install_app_now(app_slug: str, confirm_install: int = 0):
	"""Manual install action from marketplace UI."""
	_assert_marketplace_app_slug(app_slug)
	_license_allows_marketplace_action(app_slug)
	repo_url = _approved_repo_for_app(app_slug)
	confirmed = _is_truthy(confirm_install)
	return _install_app_if_needed(app_slug, repo_url=repo_url, require_confirmation=not confirmed)


def _compute_signature(secret: str, app_slug: str, activation_key: str, timestamp: str) -> str:
	payload = f"{app_slug}|{activation_key}|{timestamp}"
	return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


@frappe.whitelist(allow_guest=True)
def auto_activate_from_platform(app_slug: str, activation_key: str, timestamp: str, signature: str):
	"""
	Automatic activation endpoint called by ErpGenEx platform after payment.
	Uses HMAC signature (sha256) with shared secret in site config:
	  omnexa_marketplace_webhook_secret
	"""
	secret = str(frappe.conf.get("omnexa_marketplace_webhook_secret") or "").strip()
	if not secret:
		frappe.throw(frappe._("Marketplace webhook secret is not configured."))

	try:
		ts = int(timestamp)
	except Exception:
		frappe.throw(frappe._("Invalid timestamp."))
	now_ts = int(time.time())
	if abs(now_ts - ts) > 300:
		frappe.throw(frappe._("Webhook timestamp expired."))

	expected = _compute_signature(secret, app_slug, activation_key, str(ts))
	if not hmac.compare_digest(expected, (signature or "").strip()):
		frappe.throw(frappe._("Invalid webhook signature."))

	set_license_key(app_slug=app_slug, license_value=activation_key)
	status = verify_app_license(app_slug)
	if status.status not in ("licensed", "licensed_free", "licensed_dev_override", "trial"):
		frappe.throw(
			frappe._("Activation received but key is invalid: {0}").format(status.status),
			title=frappe._("License"),
		)
	record_online_license_check(app_slug)
	set_manual_revoke(app_slug, False)

	install_result = {"installed": False, "message": "auto_install_disabled"}
	if _auto_install_enabled():
		install_result = _install_app_if_needed(
			app_slug,
			repo_url=_approved_repo_for_app(app_slug),
			require_confirmation=False,
		)
	return {"ok": True, "status": status.status, "install": install_result}
