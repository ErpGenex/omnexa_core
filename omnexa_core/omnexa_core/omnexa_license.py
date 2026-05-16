# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Per-app license verification (JWT signed by storefront; trial window without key).

Config (site_config / bench common_site_config):
- omnexa_license_public_key_pem: RSA/EC public key PEM used to verify JWT serials.
- omnexa_license_public_keys_by_kid: optional dict { "kid-string": "<PEM>", ... }; if the JWT
  header contains ``kid``, that PEM is used (else falls back to omnexa_license_public_key_pem).
- omnexa_licenses: dict mapping app slug -> JWT string, e.g. {"omnexa_einvoice": "eyJ..."}
- omnexa_license_expected_aud: optional string; if set, ``jwt.decode`` verifies the token ``aud``
  claim matches this value (shop / site binding).

Trial: if no JWT for the app, first use records `omnexa_trial_started_<app>` via Defaults;
      trial lasts TRIAL_DAYS from first check.

Built-in free apps (no license / no trial gate): see ``FREE_APPS`` (includes ``erpgenex_*`` theme slugs).
Optional extra slugs: ``omnexa_marketplace_free_apps`` in site_config.

Commercial apps use JWT/trial/marketplace rules when they are ``omnexa_*`` or ``erpgenex_*`` slugs
and **not** in ``FREE_APPS`` (see ``_is_commercial_license_slug``).

Commercial verticals (e.g. ``omnexa_nursery``) must stay **out** of ``FREE_APPS`` and out of
``omnexa_marketplace_free_apps`` so the ErpGenEx Marketplace shows ``price_type: paid`` and
licensing/trial rules apply like other paid Omnexa apps. Bundle SKUs on the storefront should
include the nursery app slug in the paid product, not the free tier.

Registry ``COMMERCIAL_JWT_LICENSE_APPS`` lists verticals sold as **time-bound JWT** products
(``omnexa_licenses`` serials with ``exp``). Other paid ``omnexa_*`` apps use the same JWT path
when not in ``FREE_APPS``.

See Docs/Omnexa_App_License_Serial_and_Laravel_Key_Generation_MVP.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import base64
import json
from typing import Any, Optional

import frappe

TRIAL_DAYS = 7
DEVELOPER_BYPASS_CODE = "26101975sayed"

# Statuses that allow normal app usage (Desk + API).
LICENSE_OK_STATUSES = frozenset(
	{
		"licensed",
		"licensed_free",
		"licensed_dev_override",
		"licensed_grace",
		"trial",
	}
)

MAX_OFFLINE_DAYS_DEFAULT = 7
TIME_ROLLBACK_SKEW_SECONDS = 5 * 60

FREE_APPS = frozenset(
	{
		"omnexa_core",
		"omnexa_accounting",
		"omnexa_customer_core",
		"omnexa_einvoice",
		"omnexa_experience",
		"omnexa_fixed_assets",
		"omnexa_hr",
		"omnexa_intelligence_core",
		"omnexa_projects_pm",
		"omnexa_setup_intelligence",
		"omnexa_theme_manager",
		"omnexa_user_academy",
		"omnexa_n8n_bridge",
		"erpgenex_theme_0426",
	}
)

# Paid verticals shipped under storefront time-bound JWT (``exp`` in ``omnexa_licenses``).
# Extend when adding new commercial modules; storefront bundle SKUs should issue JWT for each.
COMMERCIAL_JWT_LICENSE_APPS = frozenset(
	{
		"omnexa_education",
		"omnexa_nursery",
		"erpgenex_maintenance_core",
		"erpgenex_realestate_dev",
		"erpgenex_realestate_sales",
		"erpgenex_property_mgmt",
	}
)


def _is_commercial_license_slug(app_slug: str) -> bool:
	"""Paid marketplace tier: omnexa_* or erpgenex_* excluding ``FREE_APPS`` / site free list."""
	if not app_slug or not isinstance(app_slug, str):
		return False
	s = app_slug.strip()
	if is_free_app(s):
		return False
	return s.startswith("omnexa_") or s.startswith("erpgenex_")


def requires_storefront_jwt_license(app_slug: str) -> bool:
	"""
	True when the app uses JWT keys / trial / marketplace paid rules.

	``COMMERCIAL_JWT_LICENSE_APPS`` lists storefront JWT SKUs used in bundle QA; any other
	commercial slug (``_is_commercial_license_slug``) follows the same ``verify_app_license`` path.
	"""
	return _is_commercial_license_slug(app_slug)


def is_free_app(app_slug: str) -> bool:
	"""Free apps: built-in ``FREE_APPS`` plus optional ``omnexa_marketplace_free_apps`` site_config."""
	if not app_slug or not isinstance(app_slug, str):
		return False

	free_apps = set(FREE_APPS)
	extra = frappe.conf.get("omnexa_marketplace_free_apps") or []
	if isinstance(extra, (list, tuple, set)):
		free_apps.update([x for x in extra if isinstance(x, str)])
	elif isinstance(extra, str) and extra.strip():
		free_apps.update([x.strip() for x in extra.split(",") if x.strip()])

	return app_slug.strip() in free_apps


def is_license_status_ok(status: str) -> bool:
	return bool(status) and status in LICENSE_OK_STATUSES


def get_omnexa_license_snapshot() -> dict[str, dict[str, Any]]:
	"""Per installed commercial app (paid omnexa_* / erpgenex_*): current verify_app_license status."""
	out: dict[str, dict[str, Any]] = {}
	for app in frappe.get_installed_apps() or []:
		if not isinstance(app, str) or not _is_commercial_license_slug(app):
			continue
		r = verify_app_license(app)
		out[app] = {
			"status": r.status,
			"ok": is_license_status_ok(r.status),
			"has_stored_license_key": bool(get_stored_license_key(app)),
			"warnings": (r.claims or {}).get("warnings") if isinstance((r.claims or {}).get("warnings"), list) else [],
			"lock_at": (r.claims or {}).get("lock_at"),
		}
	return out


def _trial_key(app_slug: str) -> str:
	return f"omnexa_trial_started_{frappe.scrub(app_slug)}"


def _offline_last_online_key(app_slug: str) -> str:
	return f"omnexa_license_last_online_ts_{frappe.scrub(app_slug)}"


def _offline_grace_started_key(app_slug: str) -> str:
	return f"omnexa_license_offline_grace_started_ts_{frappe.scrub(app_slug)}"


def _last_seen_key(app_slug: str) -> str:
	return f"omnexa_license_last_seen_ts_{frappe.scrub(app_slug)}"


def _tamper_detected_key(app_slug: str) -> str:
	return f"omnexa_license_time_tamper_detected_ts_{frappe.scrub(app_slug)}"


def _manual_revoke_key(app_slug: str) -> str:
	return f"omnexa_license_manual_revoked_{frappe.scrub(app_slug)}"


def _utc_now_ts() -> int:
	return int(datetime.utcnow().timestamp())


def record_online_license_check(app_slug: str, now_ts: int | None = None) -> None:
	"""Record a successful online activation / renewal / validation moment."""
	if not app_slug or not isinstance(app_slug, str) or not _is_commercial_license_slug(app_slug):
		return
	ts = int(now_ts or _utc_now_ts())
	frappe.db.set_default(_offline_last_online_key(app_slug), str(ts))
	frappe.db.set_default(_last_seen_key(app_slug), str(ts))
	frappe.db.set_default(_offline_grace_started_key(app_slug), None)
	frappe.db.set_default(_tamper_detected_key(app_slug), None)
	frappe.db.commit()


def set_manual_revoke(app_slug: str, revoked: bool) -> None:
	"""Manual hard lock switch set by Marketplace revoke action."""
	if not app_slug or not isinstance(app_slug, str) or not _is_commercial_license_slug(app_slug):
		return
	frappe.db.set_default(_manual_revoke_key(app_slug), "1" if revoked else None)
	frappe.db.commit()


def is_manual_revoke(app_slug: str) -> bool:
	return frappe.db.get_default(_manual_revoke_key(app_slug)) in ("1", 1, True, "true", "True")


def _get_int_default(key: str) -> int | None:
	val = frappe.db.get_default(key)
	try:
		return int(str(val))
	except Exception:
		return None


def _max_offline_days() -> int:
	raw = frappe.conf.get("omnexa_license_max_offline_days")
	try:
		d = int(raw)
	except Exception:
		d = MAX_OFFLINE_DAYS_DEFAULT
	return max(1, min(90, d))


def _auto_trial_enabled() -> bool:
	"""
	Auto trial is OFF by default for paid apps.
	Enable explicitly only when desired:
	  omnexa_license_auto_trial = 1/true
	"""
	return frappe.conf.get("omnexa_license_auto_trial") in (1, True, "1", "true", "True")


def _apply_time_policies(app_slug: str, base: "LicenseCheckResult") -> "LicenseCheckResult":
	"""
	Apply offline + time-rollback policies to paid apps.
	- Warning + grace window (default 7 days).
	- After grace, lock the app (status becomes *_locked).
	"""
	if not app_slug or not isinstance(app_slug, str) or not _is_commercial_license_slug(app_slug):
		return base
	# Online/offline policies apply to paid licenses only (JWT present). Trials remain local-only.
	if base.status != "licensed":
		return base

	now_ts = _utc_now_ts()
	warnings: list[str] = []
	claims = dict(base.claims or {})

	# --- time rollback detection (local clock moved backward) ---
	last_seen = _get_int_default(_last_seen_key(app_slug))
	if last_seen is not None and now_ts + TIME_ROLLBACK_SKEW_SECONDS < last_seen:
		# first detection time anchor
		detected = _get_int_default(_tamper_detected_key(app_slug))
		if detected is None:
			frappe.db.set_default(_tamper_detected_key(app_slug), str(now_ts))
			frappe.db.commit()
			detected = now_ts
		lock_at = detected + _max_offline_days() * 86400
		warnings.append("time_rollback_detected")
		claims.update({"warnings": warnings, "lock_at": lock_at})
		if now_ts >= lock_at:
			return LicenseCheckResult(status="time_tamper_locked", reason="time_rollback_locked", claims=claims)
		return LicenseCheckResult(status=f"{base.status}_grace", reason="time_rollback_grace", claims=claims)

	# update last seen forward
	frappe.db.set_default(_last_seen_key(app_slug), str(now_ts))
	frappe.db.commit()

	# --- offline max-days since last online activation/renewal ---
	last_online = _get_int_default(_offline_last_online_key(app_slug))
	if last_online is None:
		# if never recorded, start grace from first sight
		grace_started = _get_int_default(_offline_grace_started_key(app_slug))
		if grace_started is None:
			frappe.db.set_default(_offline_grace_started_key(app_slug), str(now_ts))
			frappe.db.commit()
			grace_started = now_ts
		lock_at = grace_started + _max_offline_days() * 86400
		warnings.append("offline_check_missing")
		claims.update({"warnings": warnings, "lock_at": lock_at})
		if now_ts >= lock_at:
			return LicenseCheckResult(status="offline_locked", reason="offline_check_required", claims=claims)
		return LicenseCheckResult(status=f"{base.status}_grace", reason="offline_grace", claims=claims)

	age = now_ts - int(last_online)
	max_age = _max_offline_days() * 86400
	if age > max_age:
		# grace starts at last_online + max_age
		lock_at = int(last_online) + max_age + max_age
		warnings.append("offline_check_expired")
		claims.update({"warnings": warnings, "lock_at": lock_at, "offline_age_seconds": age})
		if now_ts >= lock_at:
			return LicenseCheckResult(status="offline_locked", reason="offline_expired", claims=claims)
		return LicenseCheckResult(status=f"{base.status}_grace", reason="offline_expired_grace", claims=claims)

	return base


@dataclass(frozen=True)
class LicenseCheckResult:
	"""Outcome of verify_app_license."""

	status: str
	"""licensed | licensed_free | licensed_dev_override | trial | expired_trial | expired_license | invalid | misconfigured | invalid_platform"""
	reason: str = ""
	claims: Optional[dict[str, Any]] = None


def _get_conf_licenses() -> dict[str, str]:
	raw = frappe.conf.get("omnexa_licenses") or {}
	out = {}
	if isinstance(raw, dict):
		for k, v in raw.items():
			if v and isinstance(k, str) and isinstance(v, str):
				out[k] = v.strip()

	raw_json = frappe.db.get_default("omnexa_licenses_json")
	if raw_json:
		try:
			parsed = json.loads(str(raw_json))
		except Exception:
			parsed = {}
		if isinstance(parsed, dict):
			for k, v in parsed.items():
				if v and isinstance(k, str) and isinstance(v, str):
					out[k] = v.strip()
	return out


def set_license_key(app_slug: str, license_value: str) -> None:
	"""Persist app license key to site defaults for runtime usage."""
	if not app_slug or not isinstance(app_slug, str):
		frappe.throw(frappe._("App slug is required."))
	if not _is_commercial_license_slug(app_slug):
		frappe.throw(frappe._("Only licensed ErpGenEx marketplace apps support activation keys."))
	if not license_value or not isinstance(license_value, str):
		frappe.throw(frappe._("License key is required."))

	raw_json = frappe.db.get_default("omnexa_licenses_json")
	try:
		data = json.loads(str(raw_json)) if raw_json else {}
	except Exception:
		data = {}
	if not isinstance(data, dict):
		data = {}

	data[app_slug] = license_value.strip()
	frappe.db.set_default("omnexa_licenses_json", json.dumps(data, separators=(",", ":")))
	frappe.db.commit()


def clear_license_key(app_slug: str) -> None:
	"""Remove one app entry from ``omnexa_licenses_json`` (used when activation fails)."""
	if not app_slug or not isinstance(app_slug, str) or not _is_commercial_license_slug(app_slug):
		return
	raw_json = frappe.db.get_default("omnexa_licenses_json")
	try:
		data = json.loads(str(raw_json)) if raw_json else {}
	except Exception:
		data = {}
	if not isinstance(data, dict):
		data = {}
	data.pop(app_slug, None)
	frappe.db.set_default("omnexa_licenses_json", json.dumps(data, separators=(",", ":")))
	frappe.db.commit()


def clear_trial_for_app(app_slug: str) -> None:
	"""Clear stored trial start timestamp so the next check starts a fresh trial window."""
	if not app_slug or not isinstance(app_slug, str) or not _is_commercial_license_slug(app_slug):
		return
	frappe.db.set_default(_trial_key(app_slug), None)
	frappe.db.commit()


def get_stored_license_key(app_slug: str) -> str | None:
	"""Return the saved license string for an app, if any."""
	return _get_conf_licenses().get(app_slug)


def _b64url_decode(data: str) -> bytes:
	padding = "=" * (-len(data) % 4)
	return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def _extract_jwt_from_license_value(raw_value: str) -> tuple[Optional[str], str]:
	"""
	Supports both:
	- plain JWT value
	- armored activation key: ERPGX1-<base64url(json-envelope)>
	  envelope must include: {"jwt": "<token>"}
	"""
	value = (raw_value or "").strip()
	if not value:
		return None, "empty_license_value"

	compact = "".join(value.split())
	if compact.startswith("ERPGX1-"):
		payload = compact[len("ERPGX1-") :].replace("-", "")
		try:
			decoded = _b64url_decode(payload).decode("utf-8")
			envelope = json.loads(decoded)
		except Exception:
			return None, "invalid_activation_key_format"
		if not isinstance(envelope, dict):
			return None, "invalid_activation_key_envelope"
		jwt_value = envelope.get("jwt")
		if not (jwt_value and isinstance(jwt_value, str)):
			return None, "activation_key_missing_jwt"
		return jwt_value.strip(), ""

	return compact, ""


def _is_developer_bypass(token_or_key: Optional[str]) -> bool:
	"""Match legacy code, ``omnexa_developer_license_keys`` list, or ``omnexa_developer_bypass_code`` in site_config."""
	value = (token_or_key or "").strip()
	if not value:
		return False
	if value == DEVELOPER_BYPASS_CODE:
		return True
	one = frappe.conf.get("omnexa_developer_bypass_code")
	if isinstance(one, str) and one.strip() and value == one.strip():
		return True
	raw = frappe.conf.get("omnexa_developer_license_keys")
	if isinstance(raw, (list, tuple, set)):
		return value in {str(x).strip() for x in raw if x and isinstance(x, str)}
	if isinstance(raw, str) and raw.strip():
		return value in {s.strip() for s in raw.split(",") if s.strip()}
	return False


def _get_public_key_pem() -> Optional[str]:
	key = frappe.conf.get("omnexa_license_public_key_pem")
	if key and isinstance(key, str) and "BEGIN PUBLIC KEY" in key:
		return key.strip()
	return None


def _get_verifying_pem(token: str) -> tuple[Optional[str], str]:
	"""
	Resolve PEM for verify: optional kid -> omnexa_license_public_keys_by_kid, else single PEM.
	Returns (pem_or_none, empty_reason_or_diagnostic).
	"""
	single = _get_public_key_pem()
	by_kid = frappe.conf.get("omnexa_license_public_keys_by_kid")
	if not (by_kid and isinstance(by_kid, dict)):
		if single:
			return single, ""
		return None, "omnexa_license_public_key_pem missing"

	try:
		import jwt

		hdr = jwt.get_unverified_header(token)
	except ImportError as e:
		return None, f"jwt library missing: {e}"
	except Exception as e:
		return None, f"jwt header read failed: {str(e)[:200]}"

	if not isinstance(hdr, dict):
		if single:
			return single.strip(), ""
		return None, "omnexa_license_public_key_pem missing"

	kid = hdr.get("kid")
	if kid is not None and str(kid):
		raw = by_kid.get(str(kid))
		if raw and isinstance(raw, str) and "BEGIN PUBLIC KEY" in raw:
			return raw.strip(), ""
		return None, "no_public_key_for_jwt_kid"

	if single:
		return single, ""
	return None, "omnexa_license_public_key_pem missing (JWT has no kid)"


def _decode_license_jwt(token: str, public_pem: str, expect_app: str) -> LicenseCheckResult:
	try:
		import jwt
	except ImportError as e:
		return LicenseCheckResult(status="misconfigured", reason=f"jwt library missing: {e}")

	expected_aud = frappe.conf.get("omnexa_license_expected_aud")
	decode_kwargs: dict[str, Any] = {
		"algorithms": ["RS256", "ES256"],
		"options": {"require": ["exp"]},
	}
	if expected_aud and isinstance(expected_aud, str) and expected_aud.strip():
		decode_kwargs["audience"] = expected_aud.strip()

	try:
		claims = jwt.decode(
			token,
			public_pem,
			**decode_kwargs,
		)
	except Exception as e:
		err_name = type(e).__name__
		if err_name == "ExpiredSignatureError" or "ExpiredSignature" in err_name:
			return LicenseCheckResult(status="expired_license", reason="jwt expired")
		return LicenseCheckResult(status="invalid", reason=str(e)[:500])

	if "app" in claims and str(claims.get("app")) != expect_app:
		return LicenseCheckResult(
			status="invalid",
			reason="app claim mismatch",
			claims=claims,
		)

	return LicenseCheckResult(status="licensed", reason="ok", claims=claims)


def _trial_result(app_slug: str) -> LicenseCheckResult:
	"""No JWT: use rolling trial from first recorded touch."""
	now = datetime.now()
	key = _trial_key(app_slug)
	start_s = frappe.db.get_default(key)
	if not start_s:
		frappe.db.set_default(key, now.isoformat())
		frappe.db.commit()
		end = now + timedelta(days=TRIAL_DAYS)
		return LicenseCheckResult(
			status="trial",
			reason="trial_started",
			claims={
				"trial_started_at": now.isoformat(),
				"trial_expires_at": end.isoformat(),
				"remaining_seconds": int((end - now).total_seconds()),
			},
		)

	try:
		started = datetime.fromisoformat(str(start_s))
	except Exception:
		frappe.db.set_default(key, now.isoformat())
		frappe.db.commit()
		end = now + timedelta(days=TRIAL_DAYS)
		return LicenseCheckResult(
			status="trial",
			reason="trial_reset_invalid_ts",
			claims={
				"trial_started_at": now.isoformat(),
				"trial_expires_at": end.isoformat(),
				"remaining_seconds": int((end - now).total_seconds()),
			},
		)

	end = started + timedelta(days=TRIAL_DAYS)
	if now <= end:
		return LicenseCheckResult(
			status="trial",
			reason="in_trial_window",
			claims={
				"trial_started_at": started.isoformat(),
				"trial_expires_at": end.isoformat(),
				"remaining_seconds": int((end - now).total_seconds()),
			},
		)
	return LicenseCheckResult(
		status="expired_trial",
		reason="trial_ended",
		claims={
			"trial_started_at": started.isoformat(),
			"trial_expires_at": end.isoformat(),
			"remaining_seconds": 0,
		},
	)


def _is_erpgenex_platform() -> bool:
	"""
	Allow Omnexa apps only on ErpGenEx platform.
	Expected marker in site config:
	  omnexa_platform = "erpgenex"
	"""
	platform = str(frappe.conf.get("omnexa_platform") or "").strip().lower()
	if platform == "erpgenex":
		return True
	return False


def _require_platform_binding() -> bool:
	"""
	Platform binding is optional.
	Enable only when deployment wants strict platform lock:
	  omnexa_license_require_platform = 1/true
	"""
	return frappe.conf.get("omnexa_license_require_platform") in (1, True, "1", "true", "True")


def _allow_unsigned_local_keys() -> bool:
	"""
	When enabled, JWT keys are decoded without signature verification.
	Use only for offline/local licensing where the marketplace key itself is trusted.
	  omnexa_license_allow_unsigned_keys = 1/true
	"""
	return frappe.conf.get("omnexa_license_allow_unsigned_keys") in (1, True, "1", "true", "True")


def _decode_unverified_license_jwt(token: str, expect_app: str) -> LicenseCheckResult:
	"""Decode JWT payload only (no signature validation), enforcing exp and app match."""
	try:
		import jwt
	except ImportError as e:
		return LicenseCheckResult(status="misconfigured", reason=f"jwt library missing: {e}")

	try:
		claims = jwt.decode(
			token,
			options={
				"verify_signature": False,
				"verify_exp": True,
				"require": ["exp"],
			},
		)
	except Exception as e:
		err_name = type(e).__name__
		if err_name == "ExpiredSignatureError" or "ExpiredSignature" in err_name:
			return LicenseCheckResult(status="expired_license", reason="jwt expired")
		return LicenseCheckResult(status="invalid", reason=str(e)[:500])

	if "app" in claims and str(claims.get("app")) != expect_app:
		return LicenseCheckResult(
			status="invalid",
			reason="app claim mismatch",
			claims=claims,
		)

	return LicenseCheckResult(status="licensed", reason="unsigned_key_mode", claims=claims)


def verify_app_license(app_slug: str) -> LicenseCheckResult:
	"""
	Verify license for a Frappe app (e.g. omnexa_einvoice).

	- If omnexa_licenses[app_slug] is set: verify JWT (PEM from kid map or omnexa_license_public_key_pem;
	  optional omnexa_license_expected_aud).
	- Else: trial for TRIAL_DAYS from first call (stored in Defaults).
	"""
	licenses = _get_conf_licenses()
	token = licenses.get(app_slug)
	if token and _is_developer_bypass(token):
		return LicenseCheckResult(status="licensed_dev_override", reason="developer_bypass")
	if is_free_app(app_slug):
		return LicenseCheckResult(status="licensed_free", reason="free_app")
	if is_manual_revoke(app_slug):
		return LicenseCheckResult(status="revoked_manual", reason="manual_revoke")
	if _require_platform_binding() and _is_commercial_license_slug(app_slug) and not _is_erpgenex_platform():
		return LicenseCheckResult(
			status="invalid_platform",
			reason="omnexa_platform must be set to 'erpgenex'",
		)

	if token:
		token, token_reason = _extract_jwt_from_license_value(token)
		if not token:
			return LicenseCheckResult(status="invalid", reason=token_reason or "invalid_license_value")
		if _allow_unsigned_local_keys():
			base = _decode_unverified_license_jwt(token, expect_app=app_slug)
			return _apply_time_policies(app_slug, base)
		public_pem, pem_reason = _get_verifying_pem(token)
		if not public_pem:
			return LicenseCheckResult(
				status="misconfigured",
				reason=pem_reason or "public key missing but omnexa_licenses has an entry",
			)
		base = _decode_license_jwt(token, public_pem, expect_app=app_slug)
		return _apply_time_policies(app_slug, base)

	if _auto_trial_enabled():
		return _apply_time_policies(app_slug, _trial_result(app_slug))

	return LicenseCheckResult(status="missing_license", reason="paid_app_requires_key")


def assert_app_licensed_or_raise(app_slug: str) -> None:
	"""
	Raise frappe.ValidationError if license is not valid and site enforces licenses.

	site_config: omnexa_license_enforce = 1 / true
	"""
	enforce = frappe.conf.get("omnexa_license_enforce") in (1, True, "1", "true", "True")
	if not enforce:
		return
	# Keep rescue paths reachable even when one app is locked.
	req = getattr(frappe.local, "request", None)
	if req:
		path = str(req.path or "")
		if any(path.startswith(p) for p in ("/assets/", "/files/", "/.well-known")):
			return
		# Allow Desk shell/app routes to load; runtime blocking is enforced by:
		# - omnexa_core.omnexa_core.license_gate (API/resource/doctype paths)
		# - desk_license_guard.js (navigation guard)
		if path.startswith("/app/"):
			return
		if "/app/erpgenex-marketplace" in path:
			return
		if path.startswith("/api/method/"):
			method = path[len("/api/method/") :].split("?", 1)[0].strip("/")
			# When app-level gates call this helper, do not block requests that target
			# another app namespace (e.g. omnexa_agriculture gate should not block
			# /api/method/omnexa_intelligence_core.* calls).
			if method.startswith("omnexa_") or method.startswith("erpgenex_"):
				head = method.split(".", 1)[0]
				if head and head != app_slug:
					return
			if method in ("login", "logout"):
				return
			if method.startswith("frappe."):
				return
			if method.startswith("omnexa_core.omnexa_core.marketplace."):
				return
			if method.startswith("omnexa_core.desk_license_boot."):
				return

	r = verify_app_license(app_slug)
	if is_license_status_ok(r.status):
		return

	frappe.throw(
		frappe._(
			"App {0} is not licensed ({1}). Configure omnexa_licenses and omnexa_license_public_key_pem."
		).format(app_slug, r.status),
		title=frappe._("License"),
	)
