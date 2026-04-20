from __future__ import annotations

from datetime import datetime, timezone

import frappe

from omnexa_core.omnexa_core.omnexa_license import is_license_status_ok, verify_app_license


NOTICE_INTERVAL_SECONDS = 30 * 60


def _remaining_seconds(result) -> int:
	claims = result.claims or {}
	if not isinstance(claims, dict):
		return 0

	if isinstance(claims.get("remaining_seconds"), int):
		return max(0, int(claims.get("remaining_seconds")))

	if "trial_expires_at" in claims:
		try:
			end = datetime.fromisoformat(str(claims.get("trial_expires_at")))
			now = datetime.now(end.tzinfo) if end.tzinfo else datetime.now()
			return max(0, int((end - now).total_seconds()))
		except Exception:
			return 0

	exp = claims.get("exp")
	if isinstance(exp, (int, float)):
		now_utc = int(datetime.now(timezone.utc).timestamp())
		return max(0, int(exp) - now_utc)

	return 0


def _format_remaining(seconds: int) -> str:
	if seconds <= 0:
		return "0m"
	days, rem = divmod(seconds, 86400)
	hours, rem = divmod(rem, 3600)
	minutes = rem // 60
	parts = []
	if days:
		parts.append(f"{days}d")
	if hours:
		parts.append(f"{hours}h")
	if minutes or not parts:
		parts.append(f"{minutes}m")
	return " ".join(parts)


def _maybe_notify_expiry(app: str, result) -> None:
	if frappe.session.user == "Guest":
		return
	if result.status not in ("licensed", "trial"):
		return

	remaining = _remaining_seconds(result)
	if remaining <= 0:
		return

	now_ts = int(datetime.now(timezone.utc).timestamp())
	notice_key = f"omnexa_license_notice_ts_{frappe.scrub(app)}"
	last_notice = frappe.db.get_default(notice_key)
	try:
		last_notice_ts = int(str(last_notice))
	except Exception:
		last_notice_ts = 0
	if last_notice_ts and now_ts - last_notice_ts < NOTICE_INTERVAL_SECONDS:
		return

	frappe.db.set_default(notice_key, str(now_ts))
	frappe.db.commit()
	frappe.msgprint(
		frappe._("License for {0} expires in {1}. Renew before lock.").format(app, _format_remaining(remaining)),
		title=frappe._("License Notice"),
		indicator="orange",
		alert=True,
	)


def _license_enforcement_enabled() -> bool:
	return frappe.conf.get("omnexa_license_enforce") in (1, True, "1", "true", "True")


def _exempt_api_method(method: str) -> bool:
	"""Allow core Frappe, auth, file, and Omnexa marketplace / license refresh."""
	if not method:
		return True
	m = method.split("?", 1)[0].strip("/")
	low = m.lower()
	if low in ("login", "logout"):
		return True
	if m.startswith("frappe."):
		return True
	if m.startswith("file."):
		return True
	if m.startswith("omnexa_core.omnexa_core.marketplace."):
		return True
	# Boot refresh (module path: omnexa_core.desk_license_boot)
	if m.startswith("omnexa_core.desk_license_boot."):
		return True
	return False


def _app_from_api_method(method: str) -> str | None:
	m = method.split("?", 1)[0].strip("/")
	if not m or "." not in m:
		return None
	head = m.split(".", 1)[0]
	if head.startswith("omnexa_"):
		return head
	return None


def before_request():
	"""
	When ``omnexa_license_enforce`` is set, block API calls whose method namespace is ``omnexa_*``
	if that app's license is not OK. Core ``frappe.*`` calls stay allowed (Desk shell + forms);
	navigation for unlicensed apps is handled client-side via ``desk_license_guard.js``.
	"""
	if not _license_enforcement_enabled():
		return
	if not getattr(frappe.local, "request", None):
		return
	if frappe.session.user == "Guest":
		return

	path = frappe.local.request.path or ""
	for prefix in ("/assets/", "/files/", "/.well-known"):
		if path.startswith(prefix):
			return

	if path.startswith("/api/method/"):
		method = path[len("/api/method/") :].split("?", 1)[0].strip("/")
		if _exempt_api_method(method):
			return
		app = _app_from_api_method(method)
		if not app:
			return
		result = verify_app_license(app)
		if is_license_status_ok(result.status):
			_maybe_notify_expiry(app, result)
			return
		frappe.throw(
			frappe._(
				"Application {0} is not licensed ({1}). Open ErpGenEx Marketplace to add a license or developer key."
			).format(app, result.status),
			title=frappe._("License required"),
		)
