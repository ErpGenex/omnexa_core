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

See Docs/Omnexa_App_License_Serial_and_Laravel_Key_Generation_MVP.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import frappe

TRIAL_DAYS = 7


def _trial_key(app_slug: str) -> str:
	return f"omnexa_trial_started_{frappe.scrub(app_slug)}"


@dataclass(frozen=True)
class LicenseCheckResult:
	"""Outcome of verify_app_license."""

	status: str
	"""licensed | trial | expired_trial | expired_license | invalid | misconfigured"""
	reason: str = ""
	claims: Optional[dict[str, Any]] = None


def _get_conf_licenses() -> dict[str, str]:
	raw = frappe.conf.get("omnexa_licenses") or {}
	if not isinstance(raw, dict):
		return {}
	out = {}
	for k, v in raw.items():
		if v and isinstance(k, str) and isinstance(v, str):
			out[k] = v.strip()
	return out


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
		return LicenseCheckResult(status="trial", reason="trial_started")

	try:
		started = datetime.fromisoformat(str(start_s))
	except Exception:
		frappe.db.set_default(key, now.isoformat())
		frappe.db.commit()
		return LicenseCheckResult(status="trial", reason="trial_reset_invalid_ts")

	end = started + timedelta(days=TRIAL_DAYS)
	if now <= end:
		return LicenseCheckResult(status="trial", reason="in_trial_window")
	return LicenseCheckResult(status="expired_trial", reason="trial_ended")


def verify_app_license(app_slug: str) -> LicenseCheckResult:
	"""
	Verify license for a Frappe app (e.g. omnexa_einvoice).

	- If omnexa_licenses[app_slug] is set: verify JWT (PEM from kid map or omnexa_license_public_key_pem;
	  optional omnexa_license_expected_aud).
	- Else: trial for TRIAL_DAYS from first call (stored in Defaults).
	"""
	licenses = _get_conf_licenses()
	token = licenses.get(app_slug)

	if token:
		public_pem, pem_reason = _get_verifying_pem(token)
		if not public_pem:
			return LicenseCheckResult(
				status="misconfigured",
				reason=pem_reason or "public key missing but omnexa_licenses has an entry",
			)
		return _decode_license_jwt(token, public_pem, expect_app=app_slug)

	return _trial_result(app_slug)


def assert_app_licensed_or_raise(app_slug: str) -> None:
	"""
	Raise frappe.ValidationError if license is not valid and site enforces licenses.

	site_config: omnexa_license_enforce = 1 / true
	"""
	enforce = frappe.conf.get("omnexa_license_enforce") in (1, True, "1", "true", "True")
	if not enforce:
		return

	r = verify_app_license(app_slug)
	if r.status in ("licensed", "trial"):
		return

	frappe.throw(
		frappe._(
			"App {0} is not licensed ({1}). Configure omnexa_licenses and omnexa_license_public_key_pem."
		).format(app_slug, r.status),
		title=frappe._("License"),
	)
