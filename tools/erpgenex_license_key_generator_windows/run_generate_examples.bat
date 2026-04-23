@echo off
REM Example usage for Windows (cmd.exe). Adjust paths/values as needed.

REM 1) JWT
python generator.py generate --mode jwt ^
  --private-key "omnexa-private.pem" ^
  --app omnexa_tourism ^
  --aud "erpgenex.local.site" ^
  --months 12 ^
  --customer "cust-1001" ^
  --kid "shop-2026-1"

REM 2) Offline activation key
python generator.py generate --mode offline ^
  --private-key "omnexa-private.pem" ^
  --app omnexa_tourism ^
  --aud "erpgenex.local.site" ^
  --months 12 ^
  --customer "cust-1001" ^
  --kid "shop-2026-1" ^
  --padding-bytes 1024
