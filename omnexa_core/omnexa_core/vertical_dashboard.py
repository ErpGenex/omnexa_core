# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Shared vertical dashboard payload with session-scoped company/branch."""

from __future__ import annotations

from omnexa_core.omnexa_core.session_scope import resolve_effective_branch, resolve_effective_company
from omnexa_core.omnexa_core.world_class import certify_app


def build_vertical_dashboard_payload(
	app: str,
	company: str | None = None,
	branch: str | None = None,
	**extra,
) -> dict:
	company = company or resolve_effective_company()
	branch = branch or resolve_effective_branch(company)
	cert = certify_app(app)
	return {
		"company": company,
		"branch": branch,
		"app": app,
		"status": "healthy",
		"score": cert["weighted_score"],
		"score_100": cert["score_100"],
		"certification_level": cert["certification_level"],
		"world_class_gate": cert["world_class_gate"],
		"uses_session_context": bool(company),
		"world_class": cert,
		**extra,
	}
