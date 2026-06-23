# Copyright (c) 2026, ErpGenEx
"""Ensure default journey role portal pages exist for tier 1–2 vertical apps."""

from __future__ import annotations

from omnexa_core.vertical_workcenter.journey_portal_scaffold import scaffold_all_journey_portals


def execute():
	scaffold_all_journey_portals()
