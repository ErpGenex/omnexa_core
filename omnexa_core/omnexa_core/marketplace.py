from __future__ import annotations

import glob
import hashlib
import hmac
import os
import subprocess
import time
from urllib.parse import urlencode

import frappe
from frappe.utils import get_app_version, get_bench_path
from frappe.utils.backups import new_backup

from omnexa_core.omnexa_core.omnexa_license import is_free_app, set_license_key, verify_app_license


def _platform_base_url() -> str:
	configured = str(frappe.conf.get("omnexa_marketplace_url") or "").strip().rstrip("/")
	official = "https://erpgenex.com"
	if configured.startswith(official):
		return configured
	return official


def _title_from_slug(app_slug: str) -> str:
	parts = app_slug.replace("omnexa_", "").split("_")
	return " ".join(p.capitalize() for p in parts if p)


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
	try:
		all_apps = frappe.get_all_apps(with_internal_apps=True)
	except TypeError:
		all_apps = frappe.get_all_apps()
	omnexa_apps = sorted([a for a in (all_apps or []) if a.startswith("omnexa_")])

	return [
		{
			"app_slug": app_slug,
			"title": _title_from_slug(app_slug),
			"price_type": "free" if is_free_app(app_slug) else "paid",
			"icon_url": _guess_icon_path(app_slug),
		}
		for app_slug in omnexa_apps
	]


def _is_truthy(value) -> bool:
	return value in (1, True, "1", "true", "True", "yes", "on")


def _auto_install_enabled() -> bool:
	return _is_truthy(frappe.conf.get("omnexa_marketplace_auto_install"))


def _approved_repo_for_app(app_slug: str) -> str:
	repos = frappe.conf.get("omnexa_marketplace_repos") or {}
	if isinstance(repos, dict) and isinstance(repos.get(app_slug), str) and repos.get(app_slug).strip():
		return repos.get(app_slug).strip()
	base = str(frappe.conf.get("omnexa_marketplace_github_org") or "https://github.com/erpgenex").rstrip("/")
	return f"{base}/{app_slug}.git"


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
	for row in _catalog_seed():
		app = row["app_slug"]
		status = verify_app_license(app).status
		items.append(
			{
				**row,
				"is_free": is_free_app(app),
				"is_installed": app in (frappe.get_installed_apps() or []),
				"license_status": status,
				"approved_repo": _approved_repo_for_app(app),
				"current_version": get_app_version(app) if app in (frappe.get_installed_apps() or []) else "",
				"whats_new": _app_highlights(app),
			}
		)
	return {
		"platform_url": _platform_base_url(),
		"support_email": str(frappe.conf.get("omnexa_support_email") or "info@erpgenex.com"),
		"items": items,
	}


@frappe.whitelist()
def get_checkout_url(app_slug: str, months: int = 12):
	if not app_slug or not app_slug.startswith("omnexa_"):
		frappe.throw(frappe._("Invalid app slug."))
	months = int(months or 12)
	if months < 1 or months > 36:
		frappe.throw(frappe._("License months must be between 1 and 36."))

	base = _platform_base_url()
	return {"url": base}


@frappe.whitelist()
def activate_app_license(app_slug: str, activation_key: str):
	"""Save customer key (or developer code) and return validation status."""
	set_license_key(app_slug=app_slug, license_value=activation_key)
	status = verify_app_license(app_slug)
	if status.status not in ("licensed", "licensed_free", "licensed_dev_override", "trial"):
		frappe.throw(
			frappe._("License key saved but not valid: {0}").format(status.status),
			title=frappe._("License"),
		)
	install_result = {"installed": False, "message": "auto_install_disabled"}
	if _auto_install_enabled():
		install_result = _install_app_if_needed(
			app_slug,
			repo_url=_approved_repo_for_app(app_slug),
			require_confirmation=False,
		)
	return {"status": status.status, "reason": status.reason, "install": install_result}


@frappe.whitelist()
def get_install_plan(app_slug: str):
	if not app_slug or not app_slug.startswith("omnexa_"):
		frappe.throw(frappe._("Invalid app slug."))
	return {
		"app_slug": app_slug,
		"repo_url": _approved_repo_for_app(app_slug),
		"is_installed": app_slug in (frappe.get_installed_apps() or []),
		"current_version": get_app_version(app_slug) if app_slug in (frappe.get_installed_apps() or []) else "",
		"whats_new": _app_highlights(app_slug),
		"warning": "A full backup will be created before installation to avoid data loss.",
	}


@frappe.whitelist()
def install_app_now(app_slug: str, confirm_install: int = 0):
	"""Manual install action from marketplace UI."""
	if not app_slug or not app_slug.startswith("omnexa_"):
		frappe.throw(frappe._("Invalid app slug."))
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

	install_result = {"installed": False, "message": "auto_install_disabled"}
	if _auto_install_enabled():
		install_result = _install_app_if_needed(
			app_slug,
			repo_url=_approved_repo_for_app(app_slug),
			require_confirmation=False,
		)
	return {"ok": True, "status": status.status, "install": install_result}
