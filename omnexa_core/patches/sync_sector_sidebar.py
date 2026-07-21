# Copyright (c) 2026, ErpGenEx
"""Post-migrate patch: sync sector sidebar grouping for existing sites."""

from __future__ import annotations


def execute() -> None:
	from omnexa_core.omnexa_core.sector_sidebar_sync import sync_sector_sidebar

	sync_sector_sidebar()
