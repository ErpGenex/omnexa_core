# Copyright (c) 2026, ErpGenEx
"""Scope vertical website CSS/JS to matching public route prefixes."""

from __future__ import annotations

from pathlib import Path

import frappe

_CACHE_KEY = "omnexa_scoped_web_assets_registry"

_ALWAYS_INCLUDE_PREFIXES = (
	"/assets/frappe/",
)


def _as_list(value) -> list[str]:
	if not value:
		return []
	if isinstance(value, str):
		return [value]
	return list(value)


def _route_base(from_route: str) -> str | None:
	if not from_route:
		return None
	base = from_route.split("<", 1)[0].rstrip("/")
	return base or "/"


def _www_route_prefixes(app_name: str) -> list[str]:
	try:
		www = Path(frappe.get_app_path(app_name)) / "www"
	except Exception:
		return []
	if not www.is_dir():
		return []
	prefixes: list[str] = []
	for child in www.iterdir():
		if child.is_dir() and not child.name.startswith(("_", ".")):
			prefixes.append(f"/{child.name}")
	return prefixes


def _route_prefixes_for_app(app_name: str) -> list[str]:
	seen: set[str] = set()
	prefixes: list[str] = []

	for rule in frappe.get_hooks("website_route_rules", app_name=app_name) or []:
		if not isinstance(rule, dict):
			continue
		base = _route_base(rule.get("from_route") or "")
		if base and base not in seen:
			seen.add(base)
			prefixes.append(base)

	for pack in frappe.get_hooks("activity_website_packs", app_name=app_name) or []:
		if not isinstance(pack, dict):
			continue
		for key in ("base_path", "legacy_base_path"):
			base = _route_base(pack.get(key) or "")
			if base and base not in seen:
				seen.add(base)
				prefixes.append(base)

	for base in _www_route_prefixes(app_name):
		if base not in seen:
			seen.add(base)
			prefixes.append(base)

	return prefixes


def _build_app_asset_registry() -> dict[str, dict]:
	registry: dict[str, dict] = {}
	for app in frappe.get_installed_apps():
		css = _as_list(frappe.get_hooks("web_include_css", app_name=app) or [])
		js = _as_list(frappe.get_hooks("web_include_js", app_name=app) or [])
		if not css and not js:
			continue
		registry[app] = {
			"css": css,
			"js": js,
			"prefixes": _route_prefixes_for_app(app),
		}
	return registry


def _get_registry() -> dict[str, dict]:
	cached = frappe.cache.get_value(_CACHE_KEY)
	if cached:
		return cached
	registry = _build_app_asset_registry()
	frappe.cache.set_value(_CACHE_KEY, registry, expires_in_sec=3600)
	return registry


def clear_scoped_website_assets_cache():
	frappe.cache.delete_value(_CACHE_KEY)


def path_matches_prefix(path: str, prefix: str) -> bool:
	"""Return True when ``path`` is inside the public route ``prefix``."""
	normalized = (path or "/").split("?", 1)[0].rstrip("/") or "/"
	prefix_norm = (prefix or "/").rstrip("/") or "/"
	if prefix_norm == "/":
		return normalized == "/"
	if normalized == prefix_norm:
		return True
	return normalized.startswith(prefix_norm + "/")


def app_matches_path(prefixes: list[str], path: str) -> bool:
	if not prefixes:
		return False
	return any(path_matches_prefix(path, prefix) for prefix in prefixes)


def _current_path(context) -> str:
	path = context.get("path") or context.get("pathname")
	if not path and getattr(frappe.local, "path", None):
		path = frappe.local.path
	if not path and getattr(frappe.local, "request", None):
		path = frappe.local.request.path
	path = (path or "/").split("?", 1)[0]
	if not path.startswith("/"):
		path = f"/{path}"
	return path.rstrip("/") or "/"


def _asset_key(asset: str) -> str:
	return (asset or "").split("?", 1)[0]


def _filter_assets(all_assets: list[str], path: str, kind: str) -> list[str]:
	registry = _get_registry()
	allowed: set[str] = set()
	vertical_assets: set[str] = set()

	for spec in registry.values():
		for asset in spec[kind]:
			vertical_assets.add(_asset_key(asset))
		if app_matches_path(spec["prefixes"], path):
			for asset in spec[kind]:
				allowed.add(_asset_key(asset))

	filtered: list[str] = []
	for asset in all_assets:
		key = _asset_key(asset)
		if any(key.startswith(prefix) for prefix in _ALWAYS_INCLUDE_PREFIXES):
			filtered.append(asset)
			continue
		if key in allowed:
			filtered.append(asset)
			continue
		if key not in vertical_assets:
			filtered.append(asset)
	return filtered


def update_website_context(context):
	"""Frappe hook: keep only vertical website assets whose routes match the page."""
	if not frappe.conf.get("omnexa_scope_website_assets", 1):
		return {}

	path = _current_path(context)
	css = _as_list(context.get("web_include_css"))
	js = _as_list(context.get("web_include_js"))
	return {
		"web_include_css": _filter_assets(css, path, "css"),
		"web_include_js": _filter_assets(js, path, "js"),
	}
