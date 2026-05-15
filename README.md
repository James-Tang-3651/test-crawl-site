# Crawl Test Site

Local multi-page site designed to exercise crawler edge cases.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

## Deployment Strategy

This site supports two deployment targets:

- Netlify remains the known-good fallback deployment.
- Railway runs the live FastAPI app directly and should be treated as the
  experimental deployment until it passes verification.

Do not remove or reconfigure the Netlify files until the Railway deployment has
been verified against the crawler test routes.

## Deploy on Railway

Railway should deploy the live FastAPI app from the same public GitHub repo used
by Netlify.

Railway settings are committed in `railway.json`:

- Builder: Railpack
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-9000}`
- Healthcheck path: `/`
- Python version: `3.10`, pinned by `.python-version`

Recommended Railway flow:

1. Publish this folder to a public GitHub repo.
2. In Railway, create a new project from that GitHub repo.
3. Generate a Railway `.railway.app` domain.
4. Verify the Railway URL before moving any crawler tests away from Netlify.

Railway does not use the generated `dist` folder. It serves request-time routes
directly from `app.main:app`, so the Netlify Function shim is not part of the
Railway runtime.

## Deploy on Netlify

This project is authored as a FastAPI app, but Netlify does not run a long-lived
Uvicorn process. Deployment uses a build-time static export plus Netlify routing
files and one small Netlify Function for request-time crawl cases.

Netlify settings are committed in `netlify.toml`:

- Build command: `python scripts/export_static.py`
- Publish directory: `dist`
- Python version: `3.10`
- Node version: `20`
- Functions directory: `netlify/functions`

Netlify will install `requirements.txt` before the build, run the exporter, and
deploy the generated `dist` folder. The exporter writes `_redirects` and
`_headers` into `dist` so extensionless routes, media assets, custom status
codes, and redirects are available from the deployed site.

Routes with request-time behavior, including localized `/about`, are served by
`netlify/functions/crawl-dynamic.mjs`.

Netlify files intentionally remain unchanged so the existing deployment can be
used as a rollback path if Railway deployment or verification fails.

For local export verification:

```bash
python scripts/export_static.py
```

The exporter uses `STATIC_EXPORT_BASE_URL`, `URL`, or `DEPLOY_PRIME_URL` to build
absolute URLs in `/_manifest`, `robots.txt`, and `sitemap.xml`. Production `URL`
wins over Netlify deploy-permalink hosts unless `STATIC_EXPORT_BASE_URL` is set
explicitly.

## Deployment Verification

After both deployments are available, compare the Netlify URL and Railway URL for
these routes:

- `/`
- `/_manifest`
- `/about`
- `/query-page?sort=price`
- `/status/404`
- `/status/429`
- `/status/500`
- `/status/504`
- `/files/sample.pdf`
- `/files/sample.docx`
- `/media/png-example.png`
- `/weather/vancouver-daily-report/data.json`

Railway should serve dynamic routes from FastAPI directly instead of
`netlify/functions/crawl-dynamic.mjs`, but status codes, content types, and
crawler-facing behavior should match Netlify.

## Helpful Endpoints

- `/` root page with mixed links
- `/_manifest` machine-readable page inventory
- `/files/sample.pdf` sample file link
- `/media/pixel.jpg` sample image link

## Test Data Sections

The homepage groups existing crawl cases into visible sections, and `/_manifest`
adds matching `section_id` and `section_title` metadata to each page entry.
Sections are organization only: individual pages keep their original URLs.

Current sections:

- Core URL Handling
- Redirects
- Dynamic Content
- Security Test
- Errors and Status
- Media and Embeds
- Discovery and Policy
- Scale and Graph Shape
- Localization and State
- Product Pages
- Structured Content
