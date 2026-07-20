# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""One-shot: EG-prefixed Workspaces → final names after labels were stabilized."""

from __future__ import annotations

from omnexa_core.patches.fix_eg_workspace_routes import _normalize_workspace


def execute() -> None:
	for old, canon in (
		("EG Property Management", "Property Management"),
		("EG RE Development", "RE Development"),
		("EG RE Marketing", "RE Marketing"),
	):
		_normalize_workspace(old, canon)
