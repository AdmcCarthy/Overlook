"""Fetch the originals for the picture sources that are figures, not photographs.

Each `capture` source in data/images.yaml is a screenshot of a published page (headless Chrome, light scheme where the
page allows it); each `download` source is one file from a repository. They are written to <folder>/captures/<key>.png
(or .jpg), outside the repo, and scripts/build_images.py cuts and detunes them. Nothing here is committed.

Usage: python scripts/grab_images.py [keys ...]
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def folder(cfg: dict) -> Path:
    return Path(os.environ.get("OVERLOOK_IMAGES") or ROOT / cfg["folder"]).resolve() / "captures"


def original(cfg: dict, key: str) -> Path:
    """Where a figure source's original lives (a download keeps its own extension)."""
    src = cfg["sources"][key]
    suffix = Path(src["download"]).suffix if "download" in src else ".png"
    return folder(cfg) / f"{key}{suffix}"


def main(only: list[str]) -> None:
    cfg = yaml.safe_load((ROOT / "data" / "images.yaml").read_text(encoding="utf-8"))
    out = folder(cfg)
    out.mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME") or cfg["chrome"]
    for key, src in cfg["sources"].items():
        if "file" in src or (only and key not in only):
            continue
        path = original(cfg, key)
        if "download" in src:
            urllib.request.urlretrieve(src["download"], path)
        else:
            w, h = src["capture"]["window"]
            subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--blink-settings=preferredColorScheme=0",
                 f"--window-size={w},{h}",
                 "--virtual-time-budget=60000", f"--screenshot={path}", src["capture"]["url"]],
                check=True, capture_output=True,
            )
        print(f"{path.name}: {path.stat().st_size / 1024:.0f} kB")


if __name__ == "__main__":
    main(sys.argv[1:])
