#!/usr/bin/env python3
# Copyright (c) 2026, ErpGenEx
"""Deploy app logos from Docs/Logos/{n}.jpg into each app's public/logo.png."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

BENCH = Path(__file__).resolve().parents[4]
LOGOS_DIR = BENCH / "Docs" / "Logos"

sys.path.insert(0, str(BENCH / "apps" / "omnexa_core"))
from omnexa_core.omnexa_core.app_logo_registry import APP_LOGO_FILES  # noqa: E402


def _extract_icon(im: Image.Image, *, size: int = 128) -> Image.Image:
	"""Crop marketing JPG (icon + wordmark) to square icon."""
	w, h = im.size
	# Icon sits in upper ~58% of the wide banner.
	icon_h = int(h * 0.58)
	left = int(w * 0.22)
	right = int(w * 0.78)
	crop = im.crop((left, 0, right, icon_h)).convert("RGBA")
	# Trim near-white margins
	bg = crop.getpixel((crop.width // 2, crop.height // 2))
	if isinstance(bg, tuple) and len(bg) >= 3:
		threshold = 245
		pixels = crop.load()
		xs, ys = [], []
		for y in range(crop.height):
			for x in range(crop.width):
				r, g, b = pixels[x, y][:3]
				if r < threshold or g < threshold or b < threshold:
					xs.append(x)
					ys.append(y)
		if xs and ys:
			pad = max(2, int(min(crop.width, crop.height) * 0.04))
			x0 = max(0, min(xs) - pad)
			y0 = max(0, min(ys) - pad)
			x1 = min(crop.width, max(xs) + pad)
			y1 = min(crop.height, max(ys) + pad)
			crop = crop.crop((x0, y0, x1, y1))
	side = max(crop.width, crop.height)
	square = Image.new("RGBA", (side, side), (255, 255, 255, 0))
	ox = (side - crop.width) // 2
	oy = (side - crop.height) // 2
	square.paste(crop, (ox, oy))
	return square.resize((size, size), Image.LANCZOS)


def deploy(*, size: int = 128) -> list[str]:
	if not LOGOS_DIR.is_dir():
		raise FileNotFoundError(LOGOS_DIR)
	core_cache = BENCH / "apps" / "omnexa_core" / "omnexa_core" / "public" / "images" / "app_logos"
	core_cache.mkdir(parents=True, exist_ok=True)
	deployed: list[str] = []
	for app, file_no in sorted(APP_LOGO_FILES.items(), key=lambda x: x[0]):
		src = LOGOS_DIR / f"{file_no}.jpg"
		if not src.is_file():
			print(f"skip missing logo source {src}", file=sys.stderr)
			continue
		app_root = BENCH / "apps" / app
		if not app_root.is_dir():
			print(f"skip missing app {app}", file=sys.stderr)
			continue
		public = app_root / app / "public"
		public.mkdir(parents=True, exist_ok=True)
		im = Image.open(src)
		icon = _extract_icon(im, size=size)
		out = public / "logo.png"
		icon.save(out, format="PNG", optimize=True)
		icon.save(core_cache / f"{app}.png", format="PNG", optimize=True)
		deployed.append(str(out))
		print(f"deployed {out}  <= {src.name}")
	return deployed


if __name__ == "__main__":
	deploy()
