#!/usr/bin/env python3
# Copyright (c) 2026, ErpGenEx
"""Extract finance app logos from Docs/Logos/Logos.png and deploy to app public folders."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image

BENCH = Path(__file__).resolve().parents[4]
LOGOS_SRC = BENCH / "Docs" / "Logos" / "Logos.png"

# Banking row tiles 11–23 (y band with icon squares only)
ROW_Y0, ROW_Y1 = 258, 338
TILE_COUNT = 13

APPS_BY_TILE = {
	11: "omnexa_finance_engine",
	12: "omnexa_credit_engine",
	13: "omnexa_credit_risk",
	14: "omnexa_alm",
	15: "omnexa_consumer_finance",
	16: "omnexa_vehicle_finance",
	17: "omnexa_mortgage_finance",
	18: "omnexa_factoring",
	19: "omnexa_sme_retail_finance",
	20: "omnexa_sme_microfinance",
	21: "omnexa_leasing_finance",
	22: "omnexa_operational_risk",
	23: "omnexa_accounting",
}


def _crop_tile(im: Image.Image, index: int) -> Image.Image:
	w = im.size[0]
	cell_w = w / TILE_COUNT
	col = index - 11
	x0 = col * cell_w + 14
	x1 = (col + 1) * cell_w - 14
	return im.crop((int(x0), ROW_Y0, int(x1), ROW_Y1))


def deploy(*, size: int = 128) -> list[str]:
	if not LOGOS_SRC.is_file():
		raise FileNotFoundError(LOGOS_SRC)
	im = Image.open(LOGOS_SRC).convert("RGBA")
	deployed: list[str] = []
	for tile, app in APPS_BY_TILE.items():
		app_root = BENCH / "apps" / app
		if not app_root.is_dir():
			print(f"skip missing app {app}", file=sys.stderr)
			continue
		public = app_root / app / "public"
		public.mkdir(parents=True, exist_ok=True)
		icon = _crop_tile(im, tile).resize((size, size), Image.LANCZOS)
		out = public / "logo.png"
		icon.save(out, format="PNG", optimize=True)
		deployed.append(str(out))
		print(f"deployed {out}")
	return deployed


if __name__ == "__main__":
	deploy()
