# erpgenex_license_key_generator_windows

Python tool (Windows-friendly) to generate Omnexa **time-based license keys**:

- **JWT** (RS256) that matches `omnexa_core/omnexa_core/omnexa_license.py`
- **Offline activation key** that starts with `ERPGX1-...` and contains the JWT inside a base64url JSON envelope

## Requirements

- Windows 10/11
- Python 3.10+ (recommended)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run Windows GUI (recommended)

```bash
python gui.py
```

If you see `tkinter is not available`, install Python from `python.org` on Windows (it includes Tk by default).

You can then:
- browse/select the **private key PEM**
- choose **app slug** and **plan months**
- generate **JWT** or **ERPGX1-...** and copy it

## Generate JWT (recommended for `omnexa_licenses`)

```bash
python generator.py generate ^
  --mode jwt ^
  --private-key "omnexa-private.pem" ^
  --app omnexa_tourism ^
  --aud "erpgenex.local.site" ^
  --months 12 ^
  --customer "cust-1001" ^
  --kid "shop-2026-1"
```

Copy the output JWT into site config:

- `omnexa_licenses_json` (recommended) or `omnexa_licenses`
- ensure `omnexa_license_public_key_pem` (or `omnexa_license_public_keys_by_kid`) is configured
- ensure `omnexa_license_expected_aud` equals the value you used in `--aud`

## Generate Offline Activation Key (`ERPGX1-...`)

```bash
python generator.py generate ^
  --mode offline ^
  --private-key "omnexa-private.pem" ^
  --app omnexa_tourism ^
  --aud "erpgenex.local.site" ^
  --months 12 ^
  --customer "cust-1001" ^
  --kid "shop-2026-1" ^
  --padding-bytes 1024
```

## Notes (matching server verification)

- Claims used: `iss`, `sub`, `app`, `vendor`, `support_email`, `aud`, `iat`, `nbf`, `exp`
- Algorithm: **RS256**
- JWT header supports `kid` (optional). If you use `kid`, the server must have a matching PEM in `omnexa_license_public_keys_by_kid`.
- `aud` must match `omnexa_license_expected_aud` if that is set in site config.
