# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from omnexa_core.omnexa_core.workspace_repair import repair_all_empty_public_workspaces


def execute():
	from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_SPECS, hide_role_demo_workspaces, sync_role_workspace

	for spec in ROLE_SPECS:
		sync_role_workspace(spec)
	hide_role_demo_workspaces()
	repair_all_empty_public_workspaces(save=True)
