#!/usr/bin/env python3
"""Deploy ERPGENEX print HTML templates to all report folders (no Frappe required)."""

from __future__ import annotations

import json
import re
from pathlib import Path

def _find_bench_root() -> Path:
	p = Path(__file__).resolve().parent
	for _ in range(12):
		if (p / "sites" / "apps.txt").is_file():
			return p
		if p.parent == p:
			break
		p = p.parent
	raise SystemExit("Cannot find frappe-bench root (missing sites/apps.txt)")


BENCH = _find_bench_root()
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "report_print" / "templates"
_MARKER = "ERPGENEX report print template"
_AUDIT_KEYWORDS = ("audit", "compliance", "governance", "remediation", "evidence", "control")


def _slug(name: str) -> str:
	return re.sub(r"[^\w\s-]", "", name).strip().lower().replace(" ", "_")


def _is_audit(report_name: str, module: str | None) -> bool:
	blob = f"{report_name} {module or ''}".lower()
	return any(k in blob for k in _AUDIT_KEYWORDS)


def main():
	written = skipped = 0
	for app_dir in sorted((BENCH / "apps").iterdir()):
		if not app_dir.is_dir():
			continue
		if not (app_dir.name.startswith("omnexa_") or app_dir.name.startswith("erpgenex_")):
			continue
		for json_path in app_dir.rglob("report/*/*.json"):
			try:
				doc = json.loads(json_path.read_text(encoding="utf-8"))
			except Exception:
				continue
			if doc.get("doctype") != "Report":
				continue
			report_name = doc.get("name") or json_path.stem
			audit = _is_audit(report_name, doc.get("module"))
			tpl = "erpgenex_audit_report_print.html" if audit else "erpgenex_report_print.html"
			content = (TEMPLATE_DIR / tpl).read_text(encoding="utf-8")
			html_path = json_path.parent / f"{_slug(report_name)}.html"
			if html_path.exists() and _MARKER in html_path.read_text(encoding="utf-8"):
				skipped += 1
				continue
			html_path.write_text(content, encoding="utf-8")
			written += 1
	print(f"html_written={written} html_skipped={skipped}")


if __name__ == "__main__":
	main()
