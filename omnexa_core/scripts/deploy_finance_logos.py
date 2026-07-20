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

# icon-only band (exclude catalog number badges in top-left of tile)
ROW_Y0, ROW_Y1 = 272, 328
TILE_COUNT = 13
INSET_X = 22

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
	x0 = col * cell_w + INSET_X
	x1 = (col + 1) * cell_w - INSET_X
	return im.crop((int(x0), ROW_Y0, int(x1), ROW_Y1))


def deploy(*, size: int = 128) -> list[str]:
	if not LOGOS_SRC.is_file():
		raise FileNotFoundError(LOGOS_SRC)
	im = Image.open(LOGOS_SRC).convert("RGBA")
	core_logos = BENCH / "apps" / "omnexa_core" / "omnexa_core" / "public" / "images" / "finance_logos"
	core_logos.mkdir(parents=True, exist_ok=True)
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
		icon.save(core_logos / f"{app}.png", format="PNG", optimize=True)
		print(f"deployed {out}")
	return deployed


if __name__ == "__main__":
	deploy()
