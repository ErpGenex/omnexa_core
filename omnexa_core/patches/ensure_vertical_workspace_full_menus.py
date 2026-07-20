# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Restore full Healthcare/Education/Construction workspace sidebars after control-tower drift."""

from __future__ import annotations

from omnexa_core.install import sync_vertical_app_workspace_menus


def execute():
	sync_vertical_app_workspace_menus()
