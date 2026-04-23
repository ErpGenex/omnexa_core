from __future__ import annotations

import argparse
import base64
import json
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional


def _b64url_encode(raw: bytes) -> str:
	return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _utc_now_ts() -> int:
	return int(datetime.now(tz=timezone.utc).timestamp())


def _months_add_no_overflow(dt: datetime, months: int) -> datetime:
	"""
	Add N months while clamping the day to last day of target month.
	Matches Laravel Carbon::addMonthsNoOverflow behavior closely enough for licensing.
	"""
	if dt.tzinfo is None:
		raise ValueError("dt must be timezone-aware")
	if months < 0:
		raise ValueError("months must be >= 0")

	year = dt.year + (dt.month - 1 + months) // 12
	month = (dt.month - 1 + months) % 12 + 1

	# compute last day of target month
	if month == 12:
		next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
	else:
		next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
	last_day = (next_month - timedelta(days=1)).day

	day = min(dt.day, last_day)
	return dt.replace(year=year, month=month, day=day)


def _read_text(path: Path) -> str:
	try:
		return path.read_text(encoding="utf-8").strip()
	except Exception as e:
		raise SystemExit(f"Failed to read {path}: {e}")


def _ensure_app_slug(app_slug: str) -> str:
	app_slug = (app_slug or "").strip()
	if not app_slug.startswith("omnexa_"):
		raise SystemExit("Invalid --app. Expected omnexa_* slug.")
	return app_slug


def _ensure_months(months: int) -> int:
	try:
		months = int(months)
	except Exception:
		raise SystemExit("Invalid --months. Must be an integer between 1 and 36.")
	if months < 1 or months > 36:
		raise SystemExit("Invalid --months. Must be between 1 and 36.")
	return months


@dataclass(frozen=True)
class LicenseClaims:
	iss: str
	sub: str
	app: str
	vendor: str
	support_email: str
	aud: str
	iat: int
	nbf: int
	exp: int

	def as_dict(self) -> dict[str, Any]:
		return {
			"iss": self.iss,
			"sub": self.sub,
			"app": self.app,
			"vendor": self.vendor,
			"support_email": self.support_email,
			"aud": self.aud,
			"iat": self.iat,
			"nbf": self.nbf,
			"exp": self.exp,
		}


def generate_license_jwt(
	private_key_pem: str,
	app_slug: str,
	site_aud: str,
	months: int,
	customer_id: str,
	key_id: Optional[str] = None,
	issuer: str = "https://erpgenex.com",
	support_email: str = "info@erpgenex.com",
	now_ts: Optional[int] = None,
) -> str:
	app_slug = _ensure_app_slug(app_slug)
	months = _ensure_months(months)

	try:
		import jwt  # PyJWT
	except Exception as e:
		raise SystemExit(f"PyJWT is required. Install requirements.txt. ({e})")

	now_ts = int(now_ts or _utc_now_ts())
	now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)
	exp_dt = _months_add_no_overflow(now_dt, months)

	claims = LicenseClaims(
		iss=issuer,
		sub=str(customer_id),
		app=app_slug,
		vendor="ErpGenEx",
		support_email=support_email,
		aud=str(site_aud),
		iat=now_ts,
		nbf=now_ts,
		exp=int(exp_dt.timestamp()),
	)

	headers = {}
	if key_id:
		headers["kid"] = str(key_id)

	return jwt.encode(
		payload=claims.as_dict(),
		key=private_key_pem,
		algorithm="RS256",
		headers=headers or None,
	)


def generate_offline_activation_key(
	private_key_pem: str,
	app_slug: str,
	site_aud: str,
	months: int,
	customer_id: str,
	key_id: Optional[str] = None,
	issuer: str = "https://erpgenex.com",
	support_email: str = "info@erpgenex.com",
	padding_bytes: int = 1024,
) -> str:
	if padding_bytes < 0 or padding_bytes > 16384:
		raise SystemExit("Invalid --padding-bytes. Must be between 0 and 16384.")

	jwt_value = generate_license_jwt(
		private_key_pem=private_key_pem,
		app_slug=app_slug,
		site_aud=site_aud,
		months=months,
		customer_id=customer_id,
		key_id=key_id,
		issuer=issuer,
		support_email=support_email,
	)

	envelope = {
		"v": 1,
		"type": "omnexa_offline_activation",
		"issuer": "erpgenex.com",
		"jwt": jwt_value,
		"pad": _b64url_encode(secrets.token_bytes(padding_bytes)) if padding_bytes else "",
	}
	json_bytes = json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
	encoded = _b64url_encode(json_bytes)

	chunks = [encoded[i : i + 64] for i in range(0, len(encoded), 64)]
	return "ERPGX1-" + "-".join(chunks)


def _cmd_generate(args: argparse.Namespace) -> int:
	private_key_pem = _read_text(Path(args.private_key))
	app_slug = _ensure_app_slug(args.app)
	months = _ensure_months(args.months)

	if args.mode == "jwt":
		out = generate_license_jwt(
			private_key_pem=private_key_pem,
			app_slug=app_slug,
			site_aud=args.aud,
			months=months,
			customer_id=args.customer,
			key_id=args.kid,
			issuer=args.issuer,
			support_email=args.support_email,
		)
		print(out)
		return 0

	if args.mode == "offline":
		out = generate_offline_activation_key(
			private_key_pem=private_key_pem,
			app_slug=app_slug,
			site_aud=args.aud,
			months=months,
			customer_id=args.customer,
			key_id=args.kid,
			issuer=args.issuer,
			support_email=args.support_email,
			padding_bytes=args.padding_bytes,
		)
		print(out)
		return 0

	raise SystemExit("Unknown mode")


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(
		prog="erpgenex_license_key_generator_windows",
		description="Generate Omnexa license JWTs and offline activation keys (Windows-friendly).",
	)
	sub = p.add_subparsers(dest="command", required=True)

	gen = sub.add_parser("generate", help="Generate a JWT or offline activation key.")
	gen.add_argument("--mode", choices=["jwt", "offline"], required=True)
	gen.add_argument("--private-key", required=True, help="Path to RSA private key PEM (PKCS#8 or PKCS#1).")
	gen.add_argument("--app", required=True, help="App slug (must start with omnexa_).")
	gen.add_argument("--aud", required=True, help="Audience: must match site_config omnexa_license_expected_aud.")
	gen.add_argument("--months", type=int, required=True, help="License duration in months (1..36).")
	gen.add_argument("--customer", required=True, help="Customer ID (sub claim).")
	gen.add_argument("--kid", default=None, help="Optional key id placed in JWT header (kid).")
	gen.add_argument("--issuer", default="https://erpgenex.com", help="JWT issuer (iss).")
	gen.add_argument("--support-email", default="info@erpgenex.com", help="Support email claim.")
	gen.add_argument("--padding-bytes", type=int, default=1024, help="Offline key padding bytes (0..16384).")
	gen.set_defaults(func=_cmd_generate)

	return p


def main(argv: list[str]) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)
	return int(args.func(args))


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

