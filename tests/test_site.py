"""The landing page's data are consistent, its pictures are the right size and its markup is sound."""

import html
import os
import re
import urllib.request
from pathlib import Path

import numpy as np
import pytest
import yaml
from PIL import Image

import build_images
import build_site

ROOT = Path(__file__).resolve().parents[1]
PAGES = yaml.safe_load((ROOT / "data" / "pages.yaml").read_text(encoding="utf-8"))
IMAGES = yaml.safe_load((ROOT / "data" / "images.yaml").read_text(encoding="utf-8"))
CARDS = build_site.cards(PAGES)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    build_site.main(out)
    return out, (out / "index.html").read_text(encoding="utf-8")


def test_data_are_consistent():
    assert build_site.check(PAGES, IMAGES) == []


def test_older_repos_never_appear(built):
    out, page = built
    ban = build_site.excluded()
    assert len(ban) >= 20 and not {c["repo"].lower() for c in CARDS} & ban
    assert build_site.banned_links(page) == []
    # the guard bites: a card for an excluded repo fails the check, and a link to one is found
    bad = {**PAGES, "sections": [{**PAGES["sections"][0], "cards": [{**CARDS[0], "repo": "Red_Wines"}]}]}
    assert any("exclusion list" in p for p in build_site.check(bad, IMAGES))
    assert build_site.banned_links('<a href="https://github.com/AdmcCarthy/Stroop_Effect">x</a>') == ["Stroop_Effect"]
    # every text file the build writes is clean too, not only the page
    for f in out.rglob("*.html"):
        assert build_site.banned_links(f.read_text(encoding="utf-8")) == [], f.name


def test_live_links_point_at_their_own_repo():
    for c in CARDS:
        if c.get("live"):
            assert c["live"] == f"https://admccarthy.github.io/{c['repo']}/", c["id"]


def test_one_feature_card_and_no_numbers_in_blurbs():
    assert sum(1 for c in CARDS if c.get("feature")) == 1
    # blurbs quote no figures except paper sizes, so none needs a source line (the truth gate)
    for c in CARDS:
        assert not re.search(r"\d", re.sub(r"A4 to A0", "", c["blurb"])), c["id"]


def test_pictures_have_the_stated_size():
    for c in CARDS:
        with Image.open(ROOT / "images" / f"{c['id']}.webp") as im:
            assert im.size == build_images.CARD_SIZE, c["id"]
    with Image.open(ROOT / "images" / "hero.webp") as im:
        assert im.width == build_images.HERO_WIDTH
    for f in (ROOT / "images").glob("*.webp"):
        assert f.stat().st_size < 600 * 1024, f.name


def test_fjord_ramp_comes_from_the_tokens():
    ramp = build_images.fjord_ramp()
    assert ramp.shape == (13, 3)
    assert ramp[0].sum() < ramp[-1].sum()  # darkest first, lightest last


def test_detuned_picture_stays_inside_the_ramp_tones():
    ramp = build_images.fjord_ramp()
    darkest = ramp[0] @ [0.299, 0.587, 0.114] * 255
    for f in (ROOT / "images").glob("*.webp"):
        with Image.open(f) as im:
            lum = np.asarray(im.convert("L"))
        assert lum.min() >= darkest - 20, f.name  # no black: the tones are compressed
        assert lum.max() <= 253, f.name  # and no pure white (a figure's paper becomes the palest fjord step)


def test_markup(built):
    _, page = built
    for c in CARDS:
        assert f'id="{c["id"]}"' in page and c["title"] in page
    assert all(re.search(r'alt=""|alt="[^"]+"', m) for m in re.findall(r"<img[^>]*>", page))
    for a in re.findall(r"<a [^>]*target=\"_blank\"[^>]*>", page):
        assert 'rel="noopener"' in a
    assert page.count("<h1") == 1
    assert 'lang="en-GB"' in page
    text = re.sub(r"<[^>]+>", "", page)  # the acknowledgement is plain words once the link markup is gone
    assert "Built with Overlook by Adam McCarthy (https://github.com/AdmcCarthy/Overlook)" in text


def test_every_credit_the_pictures_need_appears(built):
    _, page = built
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    used = build_site.used_sources(PAGES, IMAGES)
    for k, s in used.items():
        if "file" in s:
            assert s["credit"] in text, k  # the photographer
        for line in s.get("lines", []):
            assert line in text, k  # the data lines for pictures cut from the linked pages
    # the Volve picture carries the Volve terms' line, generalised
    assert "Contains data from the Volve data village" in text and "Generalised for display." in text
    assert "Source: Sodir." in text


def test_tools_use_photographs_not_their_own_figures():
    tools = next(s for s in PAGES["sections"] if s["id"] == "tools")
    assert {c["id"] for c in tools["cards"]} >= {"subscout", "plate", "sheet"}
    for c in tools["cards"]:
        assert "file" in IMAGES["sources"][c["image"]["key"]], c["id"]  # a photograph, never a capture or download


def test_removed_things_stay_removed(built):
    _, page = built
    assert "Who is behind this" not in page and 'class="about' not in page
    assert 'class="lede"' not in page  # no text under the headline
    assert "Forty-Eight" not in page and "Viz_demo_generic" not in page
    assert "viz_demo_generic" in build_site.excluded()
    assert "forty-eight" not in {c["id"] for c in CARDS}


def test_style_uses_tokens_not_colours():
    css = (ROOT / "site" / "style.css").read_text(encoding="utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)  # colours come from --ss-* tokens; shadows use rgb()


def test_runtime_is_copied_from_subscout(built):
    out, _ = built
    for rel in build_site.RUNTIME:
        assert (out / "runtime" / rel).stat().st_size > 1000


@pytest.mark.network
@pytest.mark.skipif(not os.environ.get("OVERLOOK_LINKS"), reason="set OVERLOOK_LINKS=1 to check live links")
def test_live_links_answer():
    for c in CARDS:
        for url in (c.get("live"), f"{build_site.REPO_URL}/{c['repo']}"):
            if url:
                with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
                    assert r.status == 200, url


def test_libraries_are_open_code_with_photographs_and_no_page_of_their_own():
    libs = next(s for s in PAGES["sections"] if s["id"] == "libraries")
    assert {c["repo"] for c in libs["cards"]} == {"ep-physics-base", "ep-wellbore", "ep-thermal", "ep-pressure-pvt-fluids", "ep-seismic", "ep-depth-velocity", "ep-petrophysics"}
    for c in libs["cards"]:
        assert not c.get("live") and "file" in IMAGES["sources"][c["image"]["key"]], c["id"]      # no page: the card links to the code; a photograph, never a figure
