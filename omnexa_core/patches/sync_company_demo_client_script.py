"""Re-sync Company demo Client Script after hub/API rewrite."""

from omnexa_core.patches.install_company_demo_client_script import execute as _sync


def execute() -> None:
	_sync()
