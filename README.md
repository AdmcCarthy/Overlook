# Overlook

**What lies beneath, made clear.** A calm landing page that gathers the public pages built so far: stories, maps and
the tools behind them, each one a click away. It is for browsing and sharing, not for argument; the arguments live in
the pages it links to.

The cards come from [`data/pages.yaml`](data/pages.yaml): Tulip, Wildcat, APA_awards, Pinpoints-and-Echoes and
Sand-from-the-Source (stories); seismic_art_gallery, volve-surfaces, Relief and Bedrock (to explore); SubScout, Plate
and Sheet (tools). Plate and Sheet have no published page, so their cards link to the code. A new page is one entry in that file
and one picture crop. The older practice and course repositories in the same account are kept off the page on purpose:
[`data/excluded.yaml`](data/excluded.yaml) lists them, and the build and the tests fail if any is a card or is linked.

## Design

The look follows the calm, photograph-led pattern of consumer wellbeing sites (a large soft hero, rounded cards,
slow arrivals, one quiet action per card) and keeps SubScout's own restraint: Ledger type (Newsreader, Instrument
Sans, JetBrains Mono), the Tide palette, the Nordic cool room and a light and dark switch. Colours come only from
SubScout's `--ss-*` tokens; `tests/test_site.py` fails if `site/style.css` carries a raw colour.

Motion is a slow settle of the hero picture and a fade as each card arrives. Nothing loops, and `prefers-reduced-motion`
turns all of it off.

### Pictures

The five photographs (Unsplash) sit outside the repo, in an `Images` folder beside `Volve`. `scripts/build_images.py`
**detunes** each crop into the fjord colour scale of SubScout: luminance through the fjord ramp, tones compressed so
nothing is black or white, and a fifth of the original's colour kept underneath. Every card picture then belongs to the same
family. The detuned WebP files in `images/` are committed; the originals are not.

## Build

```
uv sync
uv run python scripts/build_images.py     # images/*.webp from the originals (set OVERLOOK_IMAGES to move them)
uv run python scripts/build_site.py       # -> _site/ (SubScout runtime copied from the installed package)
uv run pytest                             # data, pictures, markup; OVERLOOK_LINKS=1 also checks every live link
```

`?theme=light` or `?theme=dark` on the page forces a scheme (for screenshots). Pushing to `main` runs the tests,
builds and deploys to GitHub Pages.

## Licence and acknowledgement

MIT License with Acknowledgement ([LICENSE](LICENSE)): the MIT terms plus one condition. Anything built with this work says so,
visibly and in plain words, and does not imply endorsement: "Built with Overlook by Adam McCarthy (https://github.com/AdmcCarthy/Overlook)".
The wording is custom, so the licence is not OSI-approved.

Third-party material keeps its own terms. Photographs: Dan Meyers, NASA, Patrick Robert Doyle, Savannah Wakefield and USGS,
via Unsplash, under the Unsplash License, credited on the page. Colour tokens, type pairing and the theme switch are
[SubScout](https://github.com/AdmcCarthy/SubScout)'s, copied unchanged at build time from the pinned release.
