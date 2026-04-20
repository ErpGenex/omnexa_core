# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from datetime import datetime, timedelta, timezone
import base64
import json

import frappe
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.omnexa_license import (
	DEVELOPER_BYPASS_CODE,
	FREE_APPS,
	assert_app_licensed_or_raise,
	set_manual_revoke,
	verify_app_license,
)


def _rsa_pair():
	priv = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
	public_key = priv.public_key()
	pub_pem = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo,
	).decode("utf-8")
	return priv, pub_pem


class TestOmnexaLicense(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self._old_platform = frappe.local.conf.get("omnexa_platform")
		frappe.local.conf["omnexa_platform"] = "erpgenex"

	def tearDown(self):
		if self._old_platform is None:
			frappe.local.conf.pop("omnexa_platform", None)
		else:
			frappe.local.conf["omnexa_platform"] = self._old_platform
		super().tearDown()

	def test_omnexa_apps_blocked_outside_erpgenex_platform(self):
		old_platform = frappe.local.conf.get("omnexa_platform")
		try:
			frappe.local.conf["omnexa_platform"] = "erpnext"
			r = verify_app_license("omnexa_tourism")
			self.assertEqual(r.status, "invalid_platform")
		finally:
			if old_platform is None:
				frappe.local.conf.pop("omnexa_platform", None)
			else:
				frappe.local.conf["omnexa_platform"] = old_platform

	def test_free_apps_are_always_licensed(self):
		for app in FREE_APPS:
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed_free")

	def test_trial_starts_without_license_config(self):
		app = "thirdparty_testapp_xyz"
		key = f"omnexa_trial_started_{frappe.scrub(app)}"
		frappe.db.set_default(key, None)
		frappe.db.commit()

	def test_all_paid_omnexa_apps_start_as_trial_without_key(self):
		try:
			all_apps = frappe.get_all_apps(with_internal_apps=True)
		except TypeError:
			all_apps = frappe.get_all_apps()

		paid_apps = [a for a in (all_apps or []) if a.startswith("omnexa_") and not a.endswith("_core")]
		paid_apps = [a for a in paid_apps if a not in FREE_APPS]

		# Ensure trial is applied consistently to every paid app.
		for app in paid_apps:
			key = f"omnexa_trial_started_{frappe.scrub(app)}"
			old_lic = frappe.local.conf.get("omnexa_licenses")
			old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
			try:
				set_manual_revoke(app, False)
				frappe.db.set_default(key, None)
				frappe.db.commit()
				frappe.local.conf.pop("omnexa_licenses", None)
				frappe.local.conf.pop("omnexa_license_public_key_pem", None)
				r = verify_app_license(app)
				self.assertEqual(r.status, "trial", msg=f"{app} should start in trial without key")
			finally:
				if old_lic is not None:
					frappe.local.conf["omnexa_licenses"] = old_lic
				if old_pk is not None:
					frappe.local.conf["omnexa_license_public_key_pem"] = old_pk
				frappe.db.set_default(key, None)
				frappe.db.commit()

	def test_paid_app_trial_expires_after_one_week(self):
		app = "omnexa_tourism"
		key = f"omnexa_trial_started_{frappe.scrub(app)}"
		old = frappe.db.get_default(key)
		try:
			set_manual_revoke(app, False)
			old_dt = datetime.now() - timedelta(days=8)
			frappe.db.set_default(key, old_dt.isoformat())
			frappe.db.commit()
			r = verify_app_license(app)
			self.assertEqual(r.status, "expired_trial")
		finally:
			frappe.db.set_default(key, old)
			frappe.db.commit()
		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
		try:
			frappe.local.conf.pop("omnexa_licenses", None)
			frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			r = verify_app_license(app)
			self.assertEqual(r.status, "trial")
			self.assertIn("remaining_seconds", (r.claims or {}))
		finally:
			if old_lic is not None:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_pk is not None:
				frappe.local.conf["omnexa_license_public_key_pem"] = old_pk

	def test_developer_bypass_code_grants_license(self):
		app = "thirdparty_paid_app"
		old_lic = frappe.local.conf.get("omnexa_licenses")
		try:
			frappe.local.conf["omnexa_licenses"] = {app: DEVELOPER_BYPASS_CODE}
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed_dev_override")
		finally:
			if old_lic is None:
				frappe.local.conf.pop("omnexa_licenses", None)
			else:
				frappe.local.conf["omnexa_licenses"] = old_lic

	def test_developer_bypass_works_without_platform_marker(self):
		app = "omnexa_tourism"
		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_platform = frappe.local.conf.get("omnexa_platform")
		try:
			frappe.local.conf["omnexa_licenses"] = {app: DEVELOPER_BYPASS_CODE}
			frappe.local.conf.pop("omnexa_platform", None)
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed_dev_override")
		finally:
			if old_lic is None:
				frappe.local.conf.pop("omnexa_licenses", None)
			else:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_platform is None:
				frappe.local.conf.pop("omnexa_platform", None)
			else:
				frappe.local.conf["omnexa_platform"] = old_platform

	def test_jwt_licensed_valid_rs256(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "thirdparty_paid_app"
		now = datetime.now(timezone.utc)
		payload = {
			"app": app,
			"iat": now,
			"exp": now + timedelta(days=30),
			"sub": "cust-1",
		}
		token = jwt.encode(payload, priv, algorithm="RS256")
		if isinstance(token, bytes):
			token = token.decode("utf-8")

		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
		try:
			frappe.local.conf["omnexa_licenses"] = {app: token}
			frappe.local.conf["omnexa_license_public_key_pem"] = pub_pem
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed")
			self.assertEqual(r.claims.get("app"), app)
		finally:
			if old_lic is None:
				frappe.local.conf.pop("omnexa_licenses", None)
			else:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_pk is None:
				frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			else:
				frappe.local.conf["omnexa_license_public_key_pem"] = old_pk

	def test_jwt_expired_returns_expired_license(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "thirdparty_paid_app"
		now = datetime.now(timezone.utc)
		payload = {
			"app": app,
			"iat": now - timedelta(hours=2),
			"exp": now - timedelta(hours=1),
			"sub": "cust-1",
		}
		token = jwt.encode(payload, priv, algorithm="RS256")
		if isinstance(token, bytes):
			token = token.decode("utf-8")

		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
		try:
			frappe.local.conf["omnexa_licenses"] = {app: token}
			frappe.local.conf["omnexa_license_public_key_pem"] = pub_pem
			r = verify_app_license(app)
			self.assertEqual(r.status, "expired_license")
		finally:
			if old_lic is None:
				frappe.local.conf.pop("omnexa_licenses", None)
			else:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_pk is None:
				frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			else:
				frappe.local.conf["omnexa_license_public_key_pem"] = old_pk

	def test_misconfigured_when_license_but_no_public_key(self):
		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
		try:
			frappe.local.conf["omnexa_licenses"] = {"thirdparty_paid_app": "eyJhbGciOiJIUzI1NiJ9.e30.x"}
			frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			r = verify_app_license("thirdparty_paid_app")
			self.assertEqual(r.status, "misconfigured")
		finally:
			if old_lic is None:
				frappe.local.conf.pop("omnexa_licenses", None)
			else:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_pk is not None:
				frappe.local.conf["omnexa_license_public_key_pem"] = old_pk

	def test_assert_app_licensed_or_raise_respects_enforce_flag(self):
		old_enf = frappe.local.conf.get("omnexa_license_enforce")
		old_lic = frappe.local.conf.get("omnexa_licenses")
		try:
			frappe.local.conf["omnexa_license_enforce"] = False
			frappe.local.conf.pop("omnexa_licenses", None)
			assert_app_licensed_or_raise("thirdparty_paid_app")
		finally:
			if old_enf is None:
				frappe.local.conf.pop("omnexa_license_enforce", None)
			else:
				frappe.local.conf["omnexa_license_enforce"] = old_enf
			if old_lic is not None:
				frappe.local.conf["omnexa_licenses"] = old_lic

	def test_jwt_audience_verified_when_expected_aud_set(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "thirdparty_paid_app"
		now = datetime.now(timezone.utc)
		payload = {
			"app": app,
			"aud": "https://shop.example",
			"iat": now,
			"exp": now + timedelta(days=30),
			"sub": "cust-1",
		}
		token = jwt.encode(payload, priv, algorithm="RS256")
		if isinstance(token, bytes):
			token = token.decode("utf-8")

		old = {}
		for k in (
			"omnexa_licenses",
			"omnexa_license_public_key_pem",
			"omnexa_license_expected_aud",
		):
			old[k] = frappe.local.conf.get(k)
		try:
			frappe.local.conf["omnexa_licenses"] = {app: token}
			frappe.local.conf["omnexa_license_public_key_pem"] = pub_pem
			frappe.local.conf["omnexa_license_expected_aud"] = "https://shop.example"
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed")
		finally:
			for k, v in old.items():
				if v is None:
					frappe.local.conf.pop(k, None)
				else:
					frappe.local.conf[k] = v

	def test_jwt_wrong_audience_invalid_when_expected_aud_set(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "thirdparty_paid_app"
		now = datetime.now(timezone.utc)
		payload = {
			"app": app,
			"aud": "https://other.example",
			"iat": now,
			"exp": now + timedelta(days=30),
			"sub": "cust-1",
		}
		token = jwt.encode(payload, priv, algorithm="RS256")
		if isinstance(token, bytes):
			token = token.decode("utf-8")

		old = {}
		for k in (
			"omnexa_licenses",
			"omnexa_license_public_key_pem",
			"omnexa_license_expected_aud",
		):
			old[k] = frappe.local.conf.get(k)
		try:
			frappe.local.conf["omnexa_licenses"] = {app: token}
			frappe.local.conf["omnexa_license_public_key_pem"] = pub_pem
			frappe.local.conf["omnexa_license_expected_aud"] = "https://shop.example"
			r = verify_app_license(app)
			self.assertEqual(r.status, "invalid")
		finally:
			for k, v in old.items():
				if v is None:
					frappe.local.conf.pop(k, None)
				else:
					frappe.local.conf[k] = v

	def test_jwt_kid_selects_public_key_from_map(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "thirdparty_paid_app"
		now = datetime.now(timezone.utc)
		payload = {
			"app": app,
			"iat": now,
			"exp": now + timedelta(days=30),
			"sub": "cust-1",
		}
		token = jwt.encode(payload, priv, algorithm="RS256", headers={"kid": "shop-2026-1"})
		if isinstance(token, bytes):
			token = token.decode("utf-8")

		old = {}
		for k in ("omnexa_licenses", "omnexa_license_public_key_pem", "omnexa_license_public_keys_by_kid"):
			old[k] = frappe.local.conf.get(k)
		try:
			frappe.local.conf["omnexa_licenses"] = {app: token}
			frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			frappe.local.conf["omnexa_license_public_keys_by_kid"] = {"shop-2026-1": pub_pem}
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed")
		finally:
			for k, v in old.items():
				if v is None:
					frappe.local.conf.pop(k, None)
				else:
					frappe.local.conf[k] = v

	def test_armored_activation_key_is_supported(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "thirdparty_paid_app"
		now = datetime.now(timezone.utc)
		payload = {
			"app": app,
			"iat": now,
			"exp": now + timedelta(days=30),
			"sub": "cust-1",
		}
		token = jwt.encode(payload, priv, algorithm="RS256")
		if isinstance(token, bytes):
			token = token.decode("utf-8")

		envelope = {
			"v": 1,
			"jwt": token,
			"pad": base64.urlsafe_b64encode(b"X" * 256).decode("utf-8"),
		}
		encoded = base64.urlsafe_b64encode(json.dumps(envelope).encode("utf-8")).decode("utf-8").rstrip("=")
		armored = "ERPGX1-" + "-".join(encoded[i : i + 64] for i in range(0, len(encoded), 64))

		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
		try:
			frappe.local.conf["omnexa_licenses"] = {app: armored}
			frappe.local.conf["omnexa_license_public_key_pem"] = pub_pem
			r = verify_app_license(app)
			self.assertEqual(r.status, "licensed")
		finally:
			if old_lic is None:
				frappe.local.conf.pop("omnexa_licenses", None)
			else:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_pk is None:
				frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			else:
				frappe.local.conf["omnexa_license_public_key_pem"] = old_pk
