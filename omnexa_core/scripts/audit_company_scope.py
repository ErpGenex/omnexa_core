import frappe
from omnexa_core.omnexa_core.session_scope import resolve_effective_company, resolve_effective_branch

def run():
	c = resolve_effective_company()
	return {"ok": True, "app": "omnexa_core", "company": c, "uses_session_context": bool(c)}
