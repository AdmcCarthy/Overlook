# Overlook: working rules

A landing page for the public pages: **advertising, not journalism**. It draws people in and sends them on; it makes no
argument and quotes no figure that would need a source (tests enforce this for the card text).

@../../shared/idiom/CORE.md

Voice and structure of written work (README, docs, published pages) follow Idiom's CORE.md and house style: British English, impersonal, one creative headline then plain varied headings, a section ends on its last point. The import is harmless when the file is absent (CI).

- **Style authority is SubScout.** Colour only from `--ss-*` tokens (never a raw hex in `site/style.css`), Ledger type, Tide palette,
  Nordic cool room, light and dark. `tokens.css`, `base.css` and `subscout.js` are copied from the installed package at build time
  (pinned by tag in `pyproject.toml`), never edited or vendored by hand.
- **Design basis:** calm, photograph-led, rounded cards, slow arrival; one creative headline, plain section headings of different shapes.
  Restraint over effect: nothing loops, `prefers-reduced-motion` switches motion off.
- **Pictures:** originals live outside the repo (`../../Images`, Unsplash); `scripts/build_images.py` detunes each crop into the
  fjord scale (from the tokens) and the WebP files in `images/` are committed. Credit every photographer on the page.
- **The Tools section shows photographs only** (SubScout, Plate, Sheet): tools do not use their own imagery; a test enforces it. Other
  cards use the linked page's own figure where the repo has one, else a photograph.
- **Cards:** one entry in `data/pages.yaml` per public page (live URL, repo, picture crop). Plate and Sheet have no page: link to code.
  Blurbs state only what the page itself says.
- **The older repos are banned.** `data/excluded.yaml` lists the practice and course repos (Enron, baseball, GAN and the like); the
  build refuses to run, and a test fails, if one is a card or is linked anywhere in the page. Never add one; add new older repos to the list.
- Before showing prose: `python scripts/check_banned.py` and `check_voice.py` from Idiom, on `README.md` and the text in `data/pages.yaml`.
- Keep Idiom's `DIRECTORY.md` card for this repo true when it changes.

## Idiom (private repo)

Idiom is Adam McCarthy's private repo (`github.com/AdmcCarthy/Idiom`; `gh repo clone AdmcCarthy/Idiom` with access, normally linked at
`../../shared/idiom`) of voice, house style, working rules and the lookup tables agents use first: `DIRECTORY.md` says which repo already
does a job, `DATASETS.md` gives every dataset's terms, attribution line and status. Read the relevant one before choosing a repo or
using data, and update it when you learn something new. Never copy anything from its `personal/` or `working/` folders into this repo
or quote it in public output; if the folder is not available, say so and carry on with this file.
