# Copyright (c) 2026, ErpGenEx
"""Verify each Frappe app is self-contained for website install (no Next dependency)."""

from __future__ import annotations

from pathlib import Path

import frappe


def _app_root(app: str) -> Path | None:
	try:
		return Path(frappe.get_app_path(app)).resolve()
	except Exception:
		return None


def verify_app(app: str) -> dict:
	"""Check www/public/hooks packaging for one installed app."""
	root = _app_root(app)
	if not root:
		return {"app": app, "status": "fail", "errors": ["app_path_missing"]}

	errors: list[str] = []
	warnings: list[str] = []
	info: dict = {"app": app, "path": str(root)}

	www = root / "www"
	public = root / "public"
	hooks = root / "hooks.py"

	info["has_www"] = www.is_dir()
	info["has_public"] = public.is_dir()
	info["has_hooks"] = hooks.is_file()

	if not hooks.is_file():
		errors.append("hooks.py missing")

	# Apps that expose public websites should have www + route rules
	www_files = list(www.rglob("*.html")) if www.is_dir() else []
	info["www_html_count"] = len(www_files)

	hooks_text = hooks.read_text(encoding="utf-8", errors="ignore") if hooks.is_file() else ""
	has_routes = "website_route_rules" in hooks_text
	info["has_website_route_rules"] = has_routes

	if www_files and not has_routes:
		warnings.append("www HTML exists but website_route_rules missing in hooks.py")

	# public assets for website apps
	if www_files:
		css = list((public / "css").glob("*")) if (public / "css").is_dir() else []
		js = list((public / "js").glob("*")) if (public / "js").is_dir() else []
		info["public_css"] = len(css)
		info["public_js"] = len(js)
		if not css and not js:
			warnings.append("www present but public/css and public/js empty — site may lack assets")

	# Independence: must not require frontend/erpgenex-web paths inside app code
	forbidden_hits = []
	for pattern in ("frontend/erpgenex-web", "localhost:3001", "erpgenex-web"):
		for fp in root.rglob("*"):
			if fp.suffix not in {".py", ".js", ".html", ".md", ".json"}:
				continue
			if "node_modules" in fp.parts or ".git" in fp.parts:
				continue
			try:
				text = fp.read_text(encoding="utf-8", errors="ignore")
			except Exception:
				continue
			if pattern in text and "APP_PACKAGING" not in text and "OPTIONAL" not in text:
				# allow docs that mention the optional layer
				if fp.name in {"APP_PACKAGING.md", "README_OPTIONAL.md"}:
					continue
				forbidden_hits.append(f"{fp.relative_to(root)}:{pattern}")
				if len(forbidden_hits) >= 5:
					break
		if len(forbidden_hits) >= 5:
			break
	if forbidden_hits:
		warnings.append("references to central Next gateway: " + "; ".join(forbidden_hits[:5]))

	status = "pass"
	if errors:
		status = "fail"
	elif warnings:
		status = "warn"

	return {
		"app": app,
		"status": status,
		"errors": errors,
		"warnings": warnings,
		"info": info,
	}


def verify_installed_website_apps() -> dict:
	"""Verify all installed apps that look like verticals / SaaS."""
	apps = frappe.get_installed_apps()
	results = []
	for app in apps:
		if app in ("frappe", "erpnext"):
			continue
		root = _app_root(app)
		if not root:
			continue
		www = root / "www"
		if not www.is_dir():
			continue
		results.append(verify_app(app))

	passed = sum(1 for r in results if r["status"] == "pass")
	warned = sum(1 for r in results if r["status"] == "warn")
	failed = sum(1 for r in results if r["status"] == "fail")
	return {
		"status": "completed",
		"apps_checked": len(results),
		"pass": passed,
		"warn": warned,
		"fail": failed,
		"results": results,
	}


@frappe.whitelist()
def run_verify_all() -> dict:
	frappe.only_for("System Manager")
	return verify_installed_website_apps()
