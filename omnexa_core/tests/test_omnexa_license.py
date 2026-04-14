# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from datetime import datetime, timedelta, timezone

import frappe
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.omnexa_license import assert_app_licensed_or_raise, verify_app_license


def _rsa_pair():
	priv = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
	public_key = priv.public_key()
	pub_pem = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo,
	).decode("utf-8")
	return priv, pub_pem


class TestOmnexaLicense(FrappeTestCase):
	def test_trial_starts_without_license_config(self):
		app = "omnexa_testapp_xyz"
		key = f"omnexa_trial_started_{frappe.scrub(app)}"
		frappe.db.set_default(key, None)
		frappe.db.commit()
		old_lic = frappe.local.conf.get("omnexa_licenses")
		old_pk = frappe.local.conf.get("omnexa_license_public_key_pem")
		try:
			frappe.local.conf.pop("omnexa_licenses", None)
			frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			r = verify_app_license(app)
			self.assertEqual(r.status, "trial")
		finally:
			if old_lic is not None:
				frappe.local.conf["omnexa_licenses"] = old_lic
			if old_pk is not None:
				frappe.local.conf["omnexa_license_public_key_pem"] = old_pk
			frappe.db.set_default(key, None)
			frappe.db.commit()

	def test_jwt_licensed_valid_rs256(self):
		import jwt

		priv, pub_pem = _rsa_pair()
		app = "omnexa_einvoice"
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
		app = "omnexa_einvoice"
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
			frappe.local.conf["omnexa_licenses"] = {"omnexa_einvoice": "eyJhbGciOiJIUzI1NiJ9.e30.x"}
			frappe.local.conf.pop("omnexa_license_public_key_pem", None)
			r = verify_app_license("omnexa_einvoice")
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
			assert_app_licensed_or_raise("omnexa_einvoice")
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
		app = "omnexa_einvoice"
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
		app = "omnexa_einvoice"
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
		app = "omnexa_einvoice"
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
