# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Scan whitelisted APIs for missing company/branch scope patterns."""

from __future__ import annotations

import ast
import os
import re

import frappe
from frappe.utils import get_bench_path

_SCOPE_MARKERS = (
	"get_effective_company",
	"get_effective_branch",
	"get_effective_branch_list",
	"get_view_context",
	"apply_scope_filters",
	"get_api_scope",
	"permission_query_conditions",
)


@frappe.whitelist()
def audit_api_scope(apps: list[str] | None = None) -> dict:
	frappe.only_for("System Manager")
	apps = apps or _installed_custom_apps()
	findings = []
	for app in apps:
		root = os.path.join(get_bench_path(), "apps", app)
		if not os.path.isdir(root):
			continue
		for dirpath, _, filenames in os.walk(root):
			if "node_modules" in dirpath or ".git" in dirpath:
				continue
			for fn in filenames:
				if not fn.endswith(".py"):
					continue
				path = os.path.join(dirpath, fn)
				findings.extend(_scan_file(app, path))

	gaps = [f for f in findings if f["status"] == "GAP"]
	ok = [f for f in findings if f["status"] == "OK"]
	report_path = _write_gaps_report(gaps)
	return {
		"total_whitelisted": len(findings),
		"scoped_ok": len(ok),
		"gaps": len(gaps),
		"report_path": report_path,
		"gap_samples": gaps[:40],
	}


def _installed_custom_apps() -> list[str]:
	return [
		a
		for a in frappe.get_all_apps()
		if a not in ("frappe",) and os.path.isdir(os.path.join(get_bench_path(), "apps", a))
	]


def _scan_file(app: str, path: str) -> list[dict]:
	try:
		source = open(path, encoding="utf-8").read()
	except OSError:
		return []
	if "@frappe.whitelist" not in source:
		return []

	results = []
	try:
		tree = ast.parse(source)
	except SyntaxError:
		return []

	for node in ast.walk(tree):
		if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
			continue
		if not _has_whitelist_decorator(node):
			continue
		body_source = ast.get_source_segment(source, node) or ""
		status = "OK" if any(m in body_source for m in _SCOPE_MARKERS) else "GAP"
		if status == "GAP" and _is_exempt(node.name, path, body_source):
			status = "EXEMPT"
		results.append(
			{
				"app": app,
				"file": path.replace(get_bench_path() + os.sep, ""),
				"function": node.name,
				"status": status,
			}
		)
	return results


def _has_whitelist_decorator(node) -> bool:
	for dec in node.decorator_list:
		name = ""
		if isinstance(dec, ast.Attribute):
			name = dec.attr
		elif isinstance(dec, ast.Name):
			name = dec.id
		elif isinstance(dec, ast.Call):
			if isinstance(dec.func, ast.Attribute):
				name = dec.func.attr
		if name == "whitelist":
			return True
	return False


def _is_exempt(func_name: str, path: str, body_source: str = "") -> bool:
	if func_name.startswith("test_"):
		return True
	if "frappe.only_for(" in body_source or "only_for(" in body_source:
		return True
	if func_name.startswith(
		(
			"audit_",
			"export_",
			"scan_",
			"get_global_",
			"run_",
			"print_",
			"bootstrap_",
			"preview_",
		)
	):
		return True
	exempt_files = (
		"/install.py",
		"/patches/",
		"/test_",
		"/tests/",
		"/backups/",
		"permission.py",
		"boot.py",
		"hooks.py",
	)
	return any(x in path for x in exempt_files)


def _write_gaps_report(gaps: list[dict]) -> str:
	lines = ["# API Scope Gaps", "", f"Total gaps: {len(gaps)}", ""]
	lines.append("| App | Function | File |")
	lines.append("|-----|----------|------|")
	for row in gaps:
		lines.append(f"| {row['app']} | `{row['function']}` | {row['file']} |")
	path = os.path.join(
		get_bench_path(),
		"Docs",
		"2026-08-06_OMNEXA_ISOLATION_AND_HR",
		"API_GAPS.md",
	)
	with open(path, "w", encoding="utf-8") as fh:
		fh.write("\n".join(lines) + "\n")
	return path
