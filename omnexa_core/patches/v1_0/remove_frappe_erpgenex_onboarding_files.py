# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Remove ERPGENEX onboarding fixture dirs accidentally written under apps/frappe."""

from __future__ import annotations

import shutil
from pathlib import Path

from frappe.utils import get_bench_path


def _is_erpgenex_onboarding_path(path: Path) -> bool:
	name = path.name.lower()
	return name.startswith("erpgenex") or "erpgenex" in name


def execute() -> dict:
	frappe_root = Path(get_bench_path()) / "apps" / "frappe" / "frappe"
	removed: list[str] = []
	if not frappe_root.is_dir():
		return {"removed": removed}

	for folder_name in ("module_onboarding", "onboarding_step"):
		for parent in frappe_root.rglob(folder_name):
			if not parent.is_dir():
				continue
			for child in list(parent.iterdir()):
				if not _is_erpgenex_onboarding_path(child):
					continue
				if child.is_dir():
					shutil.rmtree(child, ignore_errors=True)
				elif child.is_file():
					child.unlink(missing_ok=True)
				removed.append(str(child.relative_to(frappe_root)))

	return {"removed": removed, "count": len(removed)}
