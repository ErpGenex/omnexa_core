# Copyright (c) 2026, ErpGenEx
"""Regression test runner for Global Excellence Loop."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import frappe

from frappe.utils import get_bench_path

# Reference verticals + platform core — full suite deferred (runtime).
_PRIORITY_APPS = [
	"omnexa_core",
	"omnexa_trading",
	"omnexa_healthcare",
	"omnexa_education",
	"erpgenex_legal",
	"omnexa_accounting",
	"omnexa_hr",
	"omnexa_backup",
]


def _run_app_tests(app: str, *, timeout: int = 120) -> dict:
	bench = Path(get_bench_path())
	site = frappe.local.site
	cmd = ["bench", "--site", site, "run-tests", "--app", app]
	try:
		proc = subprocess.run(
			cmd,
			cwd=str(bench),
			capture_output=True,
			text=True,
			timeout=timeout,
		)
		output = (proc.stdout or "") + (proc.stderr or "")
		passed = proc.returncode == 0
		# Parse unittest summary if present
		tests_run = 0
		failures = 0
		for line in output.splitlines():
			if "Ran " in line and " test" in line:
				try:
					tests_run = int(line.split("Ran ")[1].split(" test")[0].strip())
				except Exception:
					pass
			if "FAILED" in line and "failures=" in line:
				try:
					failures = int(line.split("failures=")[1].split(")")[0].strip())
				except Exception:
					pass
		return {
			"app": app,
			"status": "pass" if passed else "fail",
			"exit_code": proc.returncode,
			"tests_run": tests_run,
			"failures": failures,
			"output_tail": output[-1500:] if output else "",
		}
	except subprocess.TimeoutExpired:
		return {"app": app, "status": "timeout", "exit_code": -1, "error": f"timeout after {timeout}s"}
	except Exception as exc:
		return {"app": app, "status": "error", "exit_code": -1, "error": str(exc)}


def run_regression_suite(*, apps: list[str] | None = None, timeout_per_app: int = 120) -> dict:
	target = apps or _PRIORITY_APPS
	results = []
	for app in target:
		if app not in frappe.get_installed_apps():
			results.append({"app": app, "status": "skip", "reason": "not_installed"})
			continue
		results.append(_run_app_tests(app, timeout=timeout_per_app))

	passed = sum(1 for r in results if r.get("status") == "pass")
	failed = sum(1 for r in results if r.get("status") == "fail")
	return {
		"status": "completed",
		"python": sys.version,
		"site": frappe.local.site,
		"apps_tested": len(results),
		"passed": passed,
		"failed": failed,
		"timeout": sum(1 for r in results if r.get("status") == "timeout"),
		"skipped": sum(1 for r in results if r.get("status") == "skip"),
		"results": results,
	}


@frappe.whitelist()
def run_global_regression_tests() -> dict:
	frappe.only_for("System Manager")
	return run_regression_suite()
