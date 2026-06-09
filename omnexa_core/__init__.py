__version__ = "2026.05.20"


def _bootstrap_session_guard() -> None:
	try:
		from omnexa_core.omnexa_core.session_guard import apply_session_guard

		apply_session_guard()
	except Exception:
		pass


_bootstrap_session_guard()
