from __future__ import annotations

import glob
import hashlib
import hmac
import importlib
import os
import re
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


def _license_expiry_meta(result) -> tuple[str, str]:
	"""
	Return (expires_on_yyyy_mm_dd_or_empty, source_label).
	- trial_expires_at for trial
	- exp for JWT licenses
	- lock_at for grace/lock policies
	"""
	claims = (result.claims or {}) if result else {}
	if not isinstance(claims, dict):
		return "", ""

	try:
		if claims.get("trial_expires_at"):
			d = datetime.fromisoformat(str(claims.get("trial_expires_at")))
			return d.date().isoformat(), "trial"
	except Exception:
		pass

	try:
		exp = claims.get("exp")
		if isinstance(exp, (int, float)):
			d = datetime.fromtimestamp(int(exp), tz=timezone.utc)
			return d.date().isoformat(), "license"
	except Exception:
		pass

	try:
		lock_at = claims.get("lock_at")
		if isinstance(lock_at, (int, float)):
			d = datetime.fromtimestamp(int(lock_at), tz=timezone.utc)
			return d.date().isoformat(), "lock"
	except Exception:
		pass

	return "", ""


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
	ok, out = _git_update_app_to_ref(app_slug, "")
	return ok, out


def _marketplace_git_cache_ttl() -> int:
	try:
		return max(120, min(86400, int(frappe.conf.get("omnexa_marketplace_update_check_ttl") or 600)))
	except Exception:
		return 600


def _git_app_repo_root(app_slug: str) -> str | None:
	root = os.path.join(get_bench_path(), "apps", app_slug)
	if os.path.isdir(root) and os.path.isdir(os.path.join(root, ".git")):
		return root
	return None


def _git_run(app_root: str, args: list[str], timeout: int = 120) -> tuple[int, str]:
	try:
		p = subprocess.run(
			["git", "-C", app_root, *args],
			capture_output=True,
			text=True,
			timeout=timeout,
			check=False,
		)
		out = (p.stdout or "") + "\n" + (p.stderr or "")
		return p.returncode, out
	except Exception:
		return 1, frappe.get_traceback()[-2000:]


def _git_default_upstream_branch(app_root: str) -> str:
	rc, out = _git_run(app_root, ["symbolic-ref", "-q", "refs/remotes/origin/HEAD"], timeout=30)
	if rc == 0 and out.strip():
		ref = out.strip().split("/")[-1]
		if ref:
			return ref
	rc, out = _git_run(app_root, ["remote", "show", "origin"], timeout=60)
	if rc == 0 and "HEAD branch:" in out:
		for line in out.splitlines():
			if "HEAD branch:" in line:
				name = line.split("HEAD branch:", 1)[-1].strip()
				if name:
					return name
	return "develop"


def _git_local_head(app_root: str) -> str | None:
	rc, out = _git_run(app_root, ["rev-parse", "HEAD"], timeout=30)
	if rc != 0:
		return None
	s = out.strip()
	return s or None


def _git_ls_remote_branch_tip(app_root: str, branch: str) -> str | None:
	rc, out = _git_run(app_root, ["ls-remote", "origin", f"refs/heads/{branch}"], timeout=120)
	if rc != 0 or not out.strip():
		return None
	line = out.strip().splitlines()[0]
	parts = line.split()
	return parts[0] if parts else None


def _git_list_remote_tags(app_root: str, limit: int = 25) -> list[dict[str, str]]:
	rc, out = _git_run(app_root, ["ls-remote", "--tags", "origin"], timeout=180)
	if rc != 0:
		return []
	tags: dict[str, str] = {}
	for line in out.splitlines():
		parts = line.split("\t")
		if len(parts) < 2:
			continue
		sha, ref = parts[0], parts[1]
		if not ref.startswith("refs/tags/") or ref.endswith("^{}"):
			continue
		name = ref[len("refs/tags/") :]
		if name:
			tags[name] = sha[:12]
	try:
		from packaging.version import InvalidVersion, Version

		def sort_key(nm: str):
			try:
				return (0, Version(nm.lstrip("v").split("/")[-1]))
			except (InvalidVersion, ValueError, TypeError):
				return (1, nm)

		names = sorted(tags.keys(), key=sort_key, reverse=True)
	except Exception:
		names = sorted(tags.keys(), reverse=True)
	return [{"ref": n, "sha": tags[n]} for n in names[:limit]]


def get_git_update_meta_for_app(app_slug: str, use_cache: bool = True) -> dict:
	"""Compare local HEAD to remote default-branch tip; list recent tags (cached)."""
	cache_key = f"omnexa_market_git_meta::{app_slug}"
	if use_cache:
		cached = frappe.cache().get_value(cache_key)
		if cached is not None:
			return dict(cached)
	meta: dict = {
		"ok": False,
		"app_slug": app_slug,
		"local_sha": "",
		"remote_sha": "",
		"tracked_branch": "develop",
		"update_available": False,
		"tags_sample": [],
		"error": "",
	}
	root = _git_app_repo_root(app_slug)
	if not root:
		meta["error"] = "no_git_repo"
		frappe.cache().set_value(cache_key, meta, expires_in_sec=_marketplace_git_cache_ttl())
		return meta
	br = _git_default_upstream_branch(root)
	meta["tracked_branch"] = br
	local = _git_local_head(root)
	if local:
		meta["local_sha"] = local[:12]
	remote = _git_ls_remote_branch_tip(root, br)
	if remote:
		meta["remote_sha"] = remote[:12]
	meta["tags_sample"] = _git_list_remote_tags(root, limit=20)
	meta["ok"] = bool(local and remote)
	if local and remote:
		meta["update_available"] = local != remote
	else:
		meta["update_available"] = False
	frappe.cache().set_value(cache_key, meta, expires_in_sec=_marketplace_git_cache_ttl())
	return meta


def _invalidate_git_meta_cache(app_slug: str) -> None:
	try:
		frappe.cache().delete_value(f"omnexa_market_git_meta::{app_slug}")
	except Exception:
		pass


def _build_update_ref_choices(app_slug: str, meta: dict) -> list[dict[str, str]]:
	br = meta.get("tracked_branch") or "develop"
	choices: list[dict[str, str]] = [
		{
			"value": "",
			"label": frappe._("Pull current branch (fast-forward when possible)"),
		},
		{
			"value": br,
			"label": frappe._("Branch {0} — match origin (checkout + pull)").format(br),
		},
	]
	seen = {"", br}
	for t in meta.get("tags_sample") or []:
		ref = t.get("ref")
		if not ref or ref in seen:
			continue
		seen.add(ref)
		choices.append(
			{
				"value": ref,
				"label": frappe._("Tag {0} (commit {1})").format(ref, t.get("sha", "")),
			}
		)
	return choices


def _git_update_app_to_ref(app_slug: str, target_ref: str) -> tuple[bool, str]:
	"""Fetch origin; then ``git pull`` (empty ref) or ``git checkout`` + pull if on that branch."""
	root = _git_app_repo_root(app_slug)
	if not root:
		return False, "missing_app_or_git"
	target_ref = (target_ref or "").strip()
	rc, out = _git_run(root, ["fetch", "origin", "--tags", "--prune"], timeout=600)
	if rc != 0:
		return False, out[-3000:]
	if not target_ref:
		rc, out = _git_run(root, ["pull", "--ff-only"], timeout=600)
		if rc != 0:
			rc, out = _git_run(root, ["pull"], timeout=600)
		return rc == 0, out[-3000:]
	if not re.match(r"^[\w.\-\/]+$", target_ref) or len(target_ref) > 128:
		return False, "invalid_ref"
	rc, out = _git_run(root, ["checkout", target_ref], timeout=600)
	if rc != 0:
		return False, out[-3000:]
	br = _git_default_upstream_branch(root)
	if target_ref == br:
		rc, out = _git_run(root, ["pull", "origin", br], timeout=600)
		return rc == 0, out[-3000:]
	return True, out[-3000:]


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


def _run_post_app_change_hardening(site: str, app_slug: str) -> dict:
	"""Finalize site after install/update so Desk reflects latest modules immediately."""
	ok_mig, out_mig = _run_bench_cmd(["--site", site, "migrate"])
	if not ok_mig:
		return {"ok": False, "message": "migrate_failed", "output": out_mig[-3000:] if out_mig else ""}

	ok_build, out_build = _run_bench_cmd(["build", "--app", app_slug])
	ok_sync, out_sync = _run_bench_cmd(["--site", site, "execute", "omnexa_core.install.run_workspace_desk_sync"])

	return {
		"ok": True,
		"message": "post_app_change_hardening_done",
		"build_ok": bool(ok_build),
		"build_log_tail": out_build[-1500:] if out_build else "",
		"sync_ok": bool(ok_sync),
		"sync_log_tail": out_sync[-1500:] if out_sync else "",
	}


def _can_install_on_this_site(app_slug: str) -> bool:
	try:
		all_apps = set(frappe.get_all_apps(with_internal_apps=True) or [])
	except TypeError:
		all_apps = set(frappe.get_all_apps() or [])
	return app_slug in all_apps


def _uninstall_protected_apps() -> frozenset[str]:
	"""
	Apps that cannot be uninstalled from the marketplace UI.

	Always includes ``omnexa_core`` (hosts ErpGenEx Marketplace — update only) and ``frappe``.
	"""
	out = {"frappe", "omnexa_core"}
	raw = frappe.conf.get("omnexa_marketplace_uninstall_protect")
	if isinstance(raw, (list, tuple, set)):
		out.update(str(x).strip() for x in raw if isinstance(x, str) and str(x).strip())
	elif isinstance(raw, str) and raw.strip():
		out.update(s.strip() for s in raw.split(",") if s.strip())
	return frozenset(out)


def _installed_apps_that_require(app_slug: str) -> list[str]:
	"""
	Mirror ``frappe.installer.remove_app`` dependency rule: another installed app
	lists this app in ``required_apps`` → uninstall that app first.
	"""
	blockers: list[str] = []
	for other in frappe.get_installed_apps() or []:
		if other == app_slug:
			continue
		try:
			app_hooks = frappe.get_hooks(app_name=other)
		except Exception:
			continue
		required = app_hooks.get("required_apps") or []
		if any(isinstance(ra, str) and app_slug in ra for ra in required):
			blockers.append(other)
	return sorted(set(blockers))


def _normalize_install_source(source: str | None) -> str:
	source = (source or "github").strip().lower()
	if source in ("local", "server", "on_server", "existing"):
		return "local"
	return "github"


def _normalize_update_source(source: str | None) -> str:
	source = (source or "github").strip().lower()
	if source in ("local", "server", "on_server", "existing"):
		return "local"
	return "github"


def _install_app_if_needed(
	app_slug: str,
	repo_url: str,
	require_confirmation: bool = True,
	install_source: str = "github",
) -> dict:
	"""Install app on current site when available and not yet installed."""
	if require_confirmation:
		return {"installed": False, "message": "confirmation_required"}

	backup_state = _backup_before_install()
	if not backup_state.get("ok"):
		return {"installed": False, "message": "backup_failed"}

	source = _normalize_install_source(install_source)
	if source == "local":
		if not _can_install_on_this_site(app_slug):
			return {
				"installed": False,
				"message": "app_not_present_on_server",
				"backup": backup_state,
				"install_source": source,
			}
		fetch_state = {"fetched": False, "message": "using_local_server_copy"}
	else:
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
			"install_source": source,
		}
	if not _can_install_on_this_site(app_slug):
		return {"installed": False, "message": "app_not_present_on_server", "backup": backup_state}
	try:
		site = getattr(frappe.local, "site", None) or getattr(frappe.conf, "site_name", None)
		if not site:
			return {"installed": False, "message": "missing_site_context", "backup": backup_state}

		ok_install, out_install = _run_bench_cmd(["--site", site, "install-app", app_slug])
		if not ok_install:
			return {
				"installed": False,
				"message": "install_failed",
				"output": out_install,
				"backup": backup_state,
				"fetch": fetch_state,
				"install_source": source,
			}
		post_state = _run_post_app_change_hardening(site, app_slug)
		if not post_state.get("ok"):
			return {
				"installed": False,
				"message": post_state.get("message") or "post_install_hardening_failed",
				"output": post_state.get("output", ""),
				"backup": backup_state,
				"fetch": fetch_state,
				"install_source": source,
			}
		frappe.clear_cache()
		version = get_app_version(app_slug)
		return {
			"installed": True,
			"message": "installed_now",
			"version": version,
			"backup": backup_state,
			"fetch": fetch_state,
			"install_source": source,
			"install_log_tail": out_install[-1500:] if out_install else "",
			"build_ok": bool(post_state.get("build_ok")),
			"build_log_tail": post_state.get("build_log_tail", ""),
			"sync_ok": bool(post_state.get("sync_ok")),
			"sync_log_tail": post_state.get("sync_log_tail", ""),
			"whats_new": _app_highlights(app_slug),
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Marketplace Auto Install Failed")
		return {"installed": False, "message": "install_failed"}


@frappe.whitelist()
def get_marketplace_catalog(with_git_meta: int = 0):
	"""Return catalog for desk marketplace page."""
	items = []
	bundle_mode = _bundle_mode_enabled()
	use_real = _catalog_show_real_license_status()
	_uninstall_blocked = _uninstall_protected_apps()
	installed_set = set(frappe.get_installed_apps() or [])
	include_git_meta = _is_truthy(with_git_meta)
	for row in _catalog_seed():
		app = row["app_slug"]
		git_meta: dict = {}
		if include_git_meta and app in installed_set:
			git_meta = get_git_update_meta_for_app(app, use_cache=True)
		if bundle_mode and not use_real:
			status = "licensed_bundle"
			result = None
		else:
			result = verify_app_license(app)
			status = result.status
		expires_on, expires_source = _license_expiry_meta(result)
		items.append(
			{
				**row,
				"is_free": is_free_app(app),
				"is_installed": app in installed_set,
				"uninstall_allowed": app not in _uninstall_blocked,
				"license_status": status,
				"license_expires_on": expires_on,
				"license_expiry_source": expires_source,
				"has_stored_license_key": bool(get_stored_license_key(app)),
				"approved_repo": _approved_repo_for_app(app),
				"current_version": get_app_version(app) if app in installed_set else "",
				"updated_at": _app_updated_at(app),
				"whats_new": _app_highlights(app),
				"update_available": bool(app in installed_set and git_meta.get("update_available")),
				"local_git_sha": git_meta.get("local_sha", ""),
				"remote_git_sha": git_meta.get("remote_sha", ""),
				"git_tracked_branch": git_meta.get("tracked_branch", ""),
				"git_update_check_ok": bool(git_meta.get("ok")),
			}
		)
	try:
		refresh_ms = max(60000, min(3600000, int(frappe.conf.get("omnexa_marketplace_catalog_refresh_ms") or 600000)))
	except Exception:
		refresh_ms = 600000
	return {
		"platform_url": _platform_base_url(),
		"github_base": _github_base_url(),
		"support_email": str(frappe.conf.get("omnexa_support_email") or "info@erpgenex.com"),
		"bundle_mode": bundle_mode,
		"catalog_uses_real_license_status": use_real,
		"trial_days": int(TRIAL_DAYS),
		"license_help_html": _license_help_banner_html(bundle_mode, use_real),
		"catalog_auto_refresh_ms": refresh_ms,
		"update_check_ttl_seconds": _marketplace_git_cache_ttl(),
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
	local_available = _can_install_on_this_site(app_slug)
	return {
		"app_slug": app_slug,
		"repo_url": _approved_repo_for_app(app_slug),
		"install_sources": [
			{
				"value": "github",
				"label": "GitHub (approved repo)",
				"enabled": True,
				"note": "Fetch latest code from approved repository, then install on this site.",
			},
			{
				"value": "local",
				"label": "Local server copy",
				"enabled": local_available,
				"note": "Use app already present on this bench server (no get-app).",
			},
		],
		"local_available": local_available,
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
	git_meta = get_git_update_meta_for_app(app_slug, use_cache=False)
	return {
		"app_slug": app_slug,
		"repo_url": _approved_repo_for_app(app_slug),
		"update_sources": [
			{
				"value": "github",
				"label": "GitHub (fetch + pull)",
				"enabled": True,
				"note": "Fetch latest commits/tags from origin, then pull/check out selected ref.",
			},
			{
				"value": "local",
				"label": "Local server copy",
				"enabled": True,
				"note": "Do not pull from remote; run migrate/build using current local code.",
			},
		],
		"current_version": get_app_version(app_slug),
		"whats_new": _app_highlights(app_slug),
		"warning": "A full backup will be created, then git pull, migrate this site, and build assets for this app.",
		"git_meta": git_meta,
		"update_refs": _build_update_ref_choices(app_slug, git_meta),
	}


@frappe.whitelist()
def update_app_now(
	app_slug: str,
	confirm_update: int = 0,
	target_ref: str = "",
	update_source: str = "github",
):
	"""Pull or checkout a ref for an installed app, migrate current site, and build assets."""
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

	update_source_norm = _normalize_update_source(update_source)
	out_pull = ""
	if update_source_norm == "github":
		ok_pull, out_pull = _git_update_app_to_ref(app_slug, target_ref or "")
		if not ok_pull:
			return {
				"updated": False,
				"message": "git_pull_failed",
				"output": out_pull,
				"backup": backup_state,
				"update_source": update_source_norm,
			}

	site = getattr(frappe.local, "site", None) or getattr(frappe.conf, "site_name", None)
	if not site:
		return {
			"updated": False,
			"message": "missing_site_context",
			"backup": backup_state,
			"update_source": update_source_norm,
		}

	post_state = _run_post_app_change_hardening(site, app_slug)
	if not post_state.get("ok"):
		return {
			"updated": False,
			"message": post_state.get("message") or "post_update_hardening_failed",
			"output": post_state.get("output", ""),
			"backup": backup_state,
			"pulled": bool(update_source_norm == "github"),
			"update_source": update_source_norm,
		}
	_invalidate_git_meta_cache(app_slug)
	frappe.clear_cache()
	version = get_app_version(app_slug)
	return {
		"updated": True,
		"message": "updated_now",
		"version": version,
		"backup": backup_state,
		"update_source": update_source_norm,
		"build_ok": bool(post_state.get("build_ok")),
		"build_log_tail": post_state.get("build_log_tail", ""),
		"sync_ok": bool(post_state.get("sync_ok")),
		"sync_log_tail": post_state.get("sync_log_tail", ""),
		"applied_ref": (target_ref or "").strip() or ("pull" if update_source_norm == "github" else "local"),
	}


@frappe.whitelist()
def install_app_now(app_slug: str, confirm_install: int = 0, install_source: str = "github"):
	"""Manual install action from marketplace UI."""
	_assert_marketplace_app_slug(app_slug)
	_license_allows_marketplace_action(app_slug)
	repo_url = _approved_repo_for_app(app_slug)
	confirmed = _is_truthy(confirm_install)
	return _install_app_if_needed(
		app_slug,
		repo_url=repo_url,
		require_confirmation=not confirmed,
		install_source=_normalize_install_source(install_source),
	)


@frappe.whitelist()
def get_uninstall_plan(app_slug: str):
	"""Metadata for uninstall (System Manager)."""
	frappe.only_for("System Manager")
	_assert_marketplace_app_slug(app_slug)
	protected = _uninstall_protected_apps()
	is_installed = app_slug in (frappe.get_installed_apps() or [])
	is_protected = app_slug in protected
	dependents = _installed_apps_that_require(app_slug) if is_installed else []
	can_uninstall = bool(is_installed and not is_protected and not dependents)
	warning = frappe._(
		"This removes the app from this site and deletes its DocTypes and module data. "
		"The marketplace catalog is unchanged: the app row stays visible as long as the app exists on the bench; "
		"only the “installed on this site” state is cleared. "
		"A database backup runs first (unless disabled in site config). "
		"The app folder remains under bench; use `bench uninstall-app` on the server to remove code."
	)
	return {
		"app_slug": app_slug,
		"is_installed": is_installed,
		"is_protected": is_protected,
		"dependents": dependents,
		"can_uninstall": can_uninstall,
		"warning": warning,
	}


@frappe.whitelist()
def uninstall_app_now(app_slug: str, confirm_uninstall: int = 0):
	"""
	Remove app from the current site (same core behavior as ``bench uninstall-app``).

	- System Manager only.
	- Never removes ``frappe`` or ``omnexa_core`` (or extra slugs in ``omnexa_marketplace_uninstall_protect``).
	- Blocked while another installed app lists this app in ``hooks.required_apps``.
	"""
	frappe.only_for("System Manager")
	_assert_marketplace_app_slug(app_slug)
	if not _is_truthy(confirm_uninstall):
		return {"uninstalled": False, "message": "confirmation_required"}

	protected = _uninstall_protected_apps()
	if app_slug in protected:
		frappe.throw(
			frappe._("This app cannot be uninstalled from the marketplace (platform / protected)."),
			title=frappe._("Uninstall blocked"),
		)

	installed = list(frappe.get_installed_apps() or [])
	if app_slug not in installed:
		return {"uninstalled": False, "message": "not_installed"}

	dependents = _installed_apps_that_require(app_slug)
	if dependents:
		frappe.throw(
			frappe._(
				"These apps list {0} as a required dependency: {1}. Uninstall those apps first (or change their hooks), then try again."
			).format(app_slug, ", ".join(dependents)),
			title=frappe._("Uninstall blocked"),
		)

	no_backup = _is_truthy(frappe.conf.get("omnexa_marketplace_uninstall_no_backup"))

	try:
		from frappe.installer import remove_app

		remove_app(app_slug, dry_run=False, yes=True, no_backup=no_backup, force=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Marketplace Uninstall Failed")
		frappe.throw(
			frappe._("Uninstall failed. Check Error Log for details."),
			title=frappe._("Uninstall"),
		)

	if app_slug in (frappe.get_installed_apps() or []):
		return {"uninstalled": False, "message": "still_installed"}

	# Clean license artifacts for this slug (safe even if none were stored).
	try:
		clear_license_key(app_slug)
	except Exception:
		pass
	try:
		clear_trial_for_app(app_slug)
	except Exception:
		pass
	try:
		set_manual_revoke(app_slug, False)
	except Exception:
		pass

	frappe.clear_cache()
	return {"uninstalled": True, "message": "uninstalled_now", "app_slug": app_slug}


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
