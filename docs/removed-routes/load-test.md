# Removed route: `/load-test` — "Large Static Load-Test Page"

Removed from crawl_test_site on 2026-06-16. This note preserves the spec so the
route can be recreated if needed.

## What it did

Served a single very large **static** HTML page (≥ 7,500,000 bytes / ~7.5 MB of
initial HTML, no JavaScript) at `GET /load-test`.

Its purpose was to stress a crawler's **download, HTML parsing, text extraction,
and static-export output size** with one huge synchronous response — without
relying on delayed/JS-rendered content.

Body structure:
- Intro paragraph stating it's a large static load-test route with at least N bytes of initial HTML.
- A second paragraph explaining it repeats a 10-paragraph lorem ipsum block to stress crawler download/parsing/extraction/export size.
- A `<nav>` with three intra-site links carrying a `?from=load-test` query: `/about/`, `/many-links/`, `/structured-content/`.
- Then repeated `<article class="load-test-section" id="load-section-{index:05d}">` blocks — each with `<h2>Lorem Ipsum Block {index:05d}</h2>` and 10 `<p data-paragraph="{n:02d}">` paragraphs — appended in a loop until the encoded full document reached the byte target.

Constants/helpers used: `LOAD_TEST_TARGET_BYTES = 7_500_000`, `LOAD_TEST_TITLE`,
`LOAD_TEST_LOREM_PARAGRAPHS` (10 items), `load_test_section()`, and an
`@lru_cache`-d `load_test_body()`.

## Prompt to recreate

> Add a FastAPI route `GET /load-test` returning HTMLResponse with title
> "Large Static Load-Test Page". The page must be a large *static* HTML document
> of at least 7,500,000 bytes with no JavaScript dependency. Build the body by:
> (1) an intro paragraph stating it's a large static load-test route with at
> least N bytes of initial HTML; (2) a second paragraph explaining it repeats a
> 10-paragraph lorem ipsum block to stress crawler download, parsing, text
> extraction, and static export size; (3) a nav with links to
> `/about/?from=load-test`, `/many-links/?from=load-test`,
> `/structured-content/?from=load-test`; then (4) append
> `<article class="load-test-section" id="load-section-{index:05d}">` blocks —
> each containing `<h2>Lorem Ipsum Block {index:05d}</h2>` and the 10 lorem
> paragraphs as `<p data-paragraph="{n:02d}">` — looping until the encoded full
> document reaches the byte target. Cache the generated body (e.g. `lru_cache`).
> Use a `LOAD_TEST_TARGET_BYTES = 7_500_000` constant.

## Where it was wired up (for re-adding)

- `app/main.py` — route handler, `load_test_body()` / `load_test_section()` helpers, `LOAD_TEST_*` constants.
- `app/test_catalog.py` — catalog entry (`category: large_static_payload`) + home link.
- `VALID_URLS.md` — `/load-test` entry under "Scale and Graph Shape" + three `?from=load-test` referrer links.
