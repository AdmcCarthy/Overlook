"""Detune the source photographs into SubScout's fjord colour scale.

Each card's picture is a crop of one of the originals (data/pages.yaml), mapped through the fjord ramp by
luminance, its tones compressed so the darkest and lightest stay calm, with a little of the original's colour kept
underneath. The result is written to images/<card>.webp (and images/hero.webp). The originals live outside the
repo; set OVERLOOK_IMAGES or edit `folder` in data/images.yaml.

Usage: python scripts/build_images.py [card ids ...]
"""

from __future__ import annotations

import importlib.resources as res
import os
import re
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CARD_SIZE = (1200, 900)  # 4:3
HERO_WIDTH = 2400


def fjord_ramp() -> np.ndarray:
    """The light-scheme fjord steps 13 (darkest) to 1 (lightest), as 0-1 RGB, from SubScout's tokens."""
    css = (res.files("subscout") / "runtime" / "css" / "tokens.css").read_text(encoding="utf-8")
    steps: dict[int, str] = {}
    for n, hexv in re.findall(r"--ss-fjord-(\d+):\s*(#[0-9a-fA-F]{6})", css):
        steps.setdefault(int(n), hexv)  # the first block is the light scheme
    ramp = [steps[i] for i in range(13, 0, -1)]
    return np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in ramp], dtype=np.float32) / 255


def detune(img: Image.Image, ramp: np.ndarray, low: float, high: float, keep: float) -> Image.Image:
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    lo, hi = np.percentile(lum, [1, 99])
    tone = low + (high - low) * np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1)
    pos = tone * (len(ramp) - 1)
    i0 = np.minimum(pos.astype(int), len(ramp) - 2)
    f = (pos - i0)[..., None]
    duo = ramp[i0] * (1 - f) + ramp[i0 + 1] * f
    soft = np.clip(tone[..., None] + (a - lum[..., None]) * 0.35, 0, 1)  # the original's hue, at the compressed tone
    out = (1 - keep) * duo + keep * soft
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


def crop(img: Image.Image, cx: float, cy: float, w: float, aspect: float) -> Image.Image:
    iw, ih = img.size
    bw = min(w * iw, ih * aspect)
    bh = bw / aspect
    x0 = min(max(cx * iw - bw / 2, 0), iw - bw)
    y0 = min(max(cy * ih - bh / 2, 0), ih - bh)
    return img.crop((round(x0), round(y0), round(x0 + bw), round(y0 + bh)))


def main(only: list[str]) -> None:
    cfg = yaml.safe_load((ROOT / "data" / "images.yaml").read_text(encoding="utf-8"))
    pages = yaml.safe_load((ROOT / "data" / "pages.yaml").read_text(encoding="utf-8"))
    folder = Path(os.environ.get("OVERLOOK_IMAGES") or ROOT / cfg["folder"]).resolve()
    ramp = fjord_ramp()
    out = ROOT / "images"
    out.mkdir(exist_ok=True)
    jobs = [("hero", pages["hero"]["image"], None)]
    for sec in pages["sections"]:
        for c in sec["cards"]:
            jobs.append((c["id"], c["image"]["key"], c["image"]))
    cache: dict[str, Image.Image] = {}
    for name, key, spec in jobs:
        if only and name not in only:
            continue
        if key not in cache:
            cache[key] = ImageOps.exif_transpose(Image.open(folder / cfg["sources"][key]["file"]))
        img = cache[key]
        if spec is None:  # the hero: the whole picture, lighter
            tone, size = cfg["tone"]["hero"], (HERO_WIDTH, round(HERO_WIDTH * img.height / img.width))
            piece = img
        else:
            tone, size = cfg["tone"]["card"], CARD_SIZE
            piece = crop(img, spec["cx"], spec["cy"], spec["w"], CARD_SIZE[0] / CARD_SIZE[1])
        piece = piece.resize(size, Image.LANCZOS)
        result = detune(piece, ramp, tone["low"], tone["high"], cfg["keep"])
        path = out / f"{name}.webp"
        result.save(path, "WEBP", quality=80, method=6)
        print(f"{path.name}: {path.stat().st_size / 1024:.0f} kB")


if __name__ == "__main__":
    main(sys.argv[1:])
