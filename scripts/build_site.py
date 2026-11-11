"""Build the landing page into _site/ from data/pages.yaml.

The page uses SubScout's runtime for colour tokens, base type and the theme switch: tokens.css, base.css and subscout.js
are copied from the installed `subscout` package (pinned by tag in pyproject.toml), never edited. Everything else is
site/style.css, site/main.js and the detuned pictures in images/.

Usage: python scripts/build_site.py [out_dir]
"""

from __future__ import annotations

import html
import importlib.resources as res
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/AdmcCarthy"
SELF_URL = f"{REPO_URL}/Overlook"
TITLE = "Overlook: stories, maps and tools for the subsurface"
DESCRIPTION = (
    "Stories, maps and tools that turn open energy and geoscience data into pictures worth trusting. "
    "Every figure states its source, its units and how sure it is."
)
RUNTIME = ["css/tokens.css", "css/base.css", "js/subscout.js"]


def load() -> tuple[dict, dict]:
    pages = yaml.safe_load((ROOT / "data" / "pages.yaml").read_text(encoding="utf-8"))
    images = yaml.safe_load((ROOT / "data" / "images.yaml").read_text(encoding="utf-8"))
    return pages, images


def cards(pages: dict) -> list[dict]:
    return [c for sec in pages["sections"] for c in sec["cards"]]


def excluded() -> set[str]:
    """Repositories that must never appear (data/excluded.yaml), lower-cased."""
    data = yaml.safe_load((ROOT / "data" / "excluded.yaml").read_text(encoding="utf-8"))
    return {r.lower() for r in data["repos"]}


def banned_links(page_html: str) -> list[str]:
    """Excluded repositories that the built page links to, by GitHub or Pages address."""
    found = re.findall(r"(?:github\.com/AdmcCarthy|admccarthy\.github\.io)/([\w.-]+)", page_html, re.I)
    return sorted({n for n in found if n.lower() in excluded()})


def check(pages: dict, images: dict) -> list[str]:
    """Problems that would break the page: unknown targets or picture keys, missing files, duplicate ids, excluded repos."""
    bad, seen = [], set()
    for c in cards(pages):
        if c["repo"].lower() in excluded():
            bad.append(f"{c['id']}: {c['repo']} is on the exclusion list (data/excluded.yaml)")
    ids = {c["id"] for c in cards(pages)}
    to = pages["hero"]["primary"]["to"]
    if to not in ids:
        bad.append(f"hero primary points at unknown card {to!r}")
    if pages["hero"]["image"] not in images["sources"]:
        bad.append("hero picture key is not in images.yaml")
    for k, s in used_sources(pages, images).items():
        if "file" not in s and "lines" not in s:
            bad.append(f"picture source {k} has no credit lines (use an empty list if none are needed)")
    if not (ROOT / "images" / "hero.webp").exists():
        bad.append("images/hero.webp is missing (run scripts/build_images.py)")
    for c in cards(pages):
        if c["id"] in seen:
            bad.append(f"duplicate card id {c['id']}")
        seen.add(c["id"])
        if c["image"]["key"] not in images["sources"]:
            bad.append(f"{c['id']}: picture key {c['image']['key']!r} is not in images.yaml")
        if not (ROOT / "images" / f"{c['id']}.webp").exists():
            bad.append(f"images/{c['id']}.webp is missing (run scripts/build_images.py)")
    return bad


def e(s: str) -> str:
    return html.escape(s, quote=True)


def card_html(c: dict) -> str:
    live, repo = c.get("live"), f"{REPO_URL}/{c['repo']}"
    main = live or repo
    label = "Open the page" if live else "View on GitHub"
    code = f'<a class="link" href="{e(repo)}" target="_blank" rel="noopener">Code on GitHub</a>' if live else ""
    cls = "card reveal" + (" feature" if c.get("feature") else "")
    return f"""      <article class="{cls}" id="{e(c['id'])}">
        <a class="card-media" href="{e(main)}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">
          <img src="images/{e(c['id'])}.webp" alt="" width="1200" height="800" loading="lazy" decoding="async">
        </a>
        <div class="card-body">
          <p class="kicker">{e(c['kind'])}</p>
          <h3><a href="{e(main)}" target="_blank" rel="noopener">{e(c['title'])}</a></h3>
          <p>{e(c['blurb'])}</p>
          <p class="card-links"><a class="btn btn-primary" href="{e(main)}" target="_blank" rel="noopener">{label}</a>{code}</p>
        </div>
      </article>"""


def section_html(sec: dict) -> str:
    body = "\n".join(card_html(c) for c in sec["cards"])  # a feature card spans the row; the rest sit three across
    return f"""  <section class="band" id="{e(sec['id'])}">
    <div class="wrap">
      <div class="band-head reveal"><h2>{e(sec['heading'])}</h2><p>{e(sec['intro'])}</p></div>
      <div class="grid grid-3">
{body}
      </div>
    </div>
  </section>"""


def used_sources(pages: dict, images: dict) -> dict[str, dict]:
    keys = {pages["hero"]["image"]} | {c["image"]["key"] for c in cards(pages)}
    return {k: s for k, s in images["sources"].items() if k in keys}


def credits(pages: dict, images: dict) -> tuple[str, str]:
    """The footer's picture credits: photographers (Unsplash), and the data lines for pictures cut from the linked pages."""
    used = used_sources(pages, images)
    names = [f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["credit"])}</a>' for s in used.values() if "file" in s]
    photos = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
    lines: list[str] = []
    for s in used.values():
        for ln in s.get("lines", []):
            if ln not in lines:
                lines.append(ln)
    return photos, " ".join(e(ln) for ln in lines)


def page(pages: dict, images: dict) -> str:
    h = pages["hero"]
    to = h["primary"]["to"]
    nav = "".join(f'<a href="#{e(s["id"])}">{e(n)}</a>' for s, n in zip(pages["sections"], ("Stories", "Explore", "Tools", "Libraries"), strict=True))
    sections = "\n".join(section_html(s) for s in pages["sections"])
    photos, lines = credits(pages, images)
    return f"""<!doctype html>
<html lang="en-GB" data-type="ledger" data-palette="tide" data-surface="nordic-cool">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(TITLE)}</title>
<meta name="description" content="{e(DESCRIPTION)}">
<script>document.documentElement.classList.add("js")</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="runtime/css/tokens.css">
<link rel="stylesheet" href="runtime/css/base.css">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top">
  <a class="mark" href="#top">Overlook</a>
  <nav aria-label="Sections">{nav}</nav>
  <div class="ss-seg" id="ctl-theme" role="group" aria-label="Colour scheme"><button data-value="light">Light</button><button data-value="dark">Dark</button></div>
</header>
<main id="top">
  <section class="hero">
    <img class="hero-img" src="images/hero.webp" alt="" width="2400" height="1597" fetchpriority="high">
    <div class="wrap hero-copy">
      <p class="eyebrow">Subsurface stories, maps and tools</p>
      <h1>{e(h['headline'])}</h1>
      <p class="cta"><a class="btn btn-primary" href="#{e(to)}">{e(h['primary']['label'])}</a><a class="btn btn-quiet" href="{e(h['secondary']['to'])}">{e(h['secondary']['label'])}</a></p>
    </div>
  </section>
{sections}
</main>
<footer>
  <div class="wrap">
    <p>Card pictures are cut from the linked pages' own figures, and from photographs by {photos} (Unsplash, Unsplash License), all detuned into the fjord colour scale of SubScout. {lines}</p>
    <p>Colours, type and theme switch from <a href="{REPO_URL}/SubScout" target="_blank" rel="noopener">SubScout</a>. Every page linked here is built from open data and states its sources on the page.</p>
    <p>Built with Overlook by Adam McCarthy (<a href="{SELF_URL}" target="_blank" rel="noopener">{SELF_URL}</a>). MIT License with Acknowledgement.</p>
  </div>
</footer>
<script type="module" src="main.js"></script>
</body>
</html>
"""


def main(out: Path) -> None:
    pages, images = load()
    problems = check(pages, images)
    if problems:
        raise SystemExit("\n".join(problems))
    if out.exists():
        shutil.rmtree(out)
    (out / "runtime" / "css").mkdir(parents=True)
    (out / "runtime" / "js").mkdir(parents=True)
    src = res.files("subscout") / "runtime"
    for rel in RUNTIME:
        (out / "runtime" / rel).write_bytes((src / rel).read_bytes())
    shutil.copytree(ROOT / "images", out / "images")
    for f in ("style.css", "main.js"):
        shutil.copy(ROOT / "site" / f, out / f)
    (out / ".nojekyll").write_text("")
    text = page(pages, images)
    leaked = banned_links(text)
    if leaked:
        raise SystemExit(f"the page links to excluded repositories: {', '.join(leaked)}")
    (out / "index.html").write_text(text, encoding="utf-8")
    print(f"wrote {out / 'index.html'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site")
