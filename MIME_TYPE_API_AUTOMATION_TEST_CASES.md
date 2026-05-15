# MIME Type API Automation Test Cases

This file is an automation reference only. It is not linked from the crawl test
site, not listed in the page manifest, and not exported as a crawlable route.

Use `{{BASE_URL}}` as the deployed test-site origin.

## Crawl URL Set

Required URLs for MIME type classification automation:

```text
{{BASE_URL}}/
{{BASE_URL}}/structured-content/markdown/sample.md
{{BASE_URL}}/robots.txt
{{BASE_URL}}/files/sample.pdf
{{BASE_URL}}/files/sample.docx
{{BASE_URL}}/media/pixel.jpg
```

Optional mismatch / edge-case URLs:

```text
{{BASE_URL}}/wrong-content-type-html-as-text
{{BASE_URL}}/wrong-content-type-json-as-html
{{BASE_URL}}/sitemap-discovery-fail.xml
```

There is no required crawl URL for `none`; use a synthetic API fixture or an
uncategorized response outside the crawl site for that classification.

| Type | Expected `mimeType` | Endpoint | Expected classification notes |
|---|---|---|---|
| `none` | `null`, empty, or unknown | No dedicated endpoint currently | Use a synthetic API fixture or an uncategorized response outside the crawl site. |
| `html` | `text/html` | `{{BASE_URL}}/` | Normal HTML page. |
| `markdown` | `text/markdown` | `{{BASE_URL}}/structured-content/markdown/sample.md` | Raw Markdown document with inline, reference, and list links. |
| `txt` | `text/plain` | `{{BASE_URL}}/robots.txt` | Plain text document. |
| `pdf` | `application/pdf` | `{{BASE_URL}}/files/sample.pdf` | Minimal PDF asset. |
| `docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `{{BASE_URL}}/files/sample.docx` | Minimal valid DOCX package. |
| `image` | `image/jpeg` | `{{BASE_URL}}/media/pixel.jpg` | Minimal JPEG asset. |

## Additional Image MIME Values

The recommended `image` type also allows these MIME values, but the current test
site does not expose standalone endpoints for them yet:

| MIME value | Endpoint |
|---|---|
| `image/png` | Not currently available |
| `image/gif` | Not currently available |
| `image/webp` | Not currently available |
| `image/svg+xml` | Not currently available as a standalone endpoint |

## Mismatch / Edge Fixtures

These are useful for API automation that validates MIME-vs-content behavior:

| Endpoint | Actual `mimeType` | Body shape |
|---|---|---|
| `{{BASE_URL}}/wrong-content-type-html-as-text` | `text/plain` | HTML body served as plain text. |
| `{{BASE_URL}}/wrong-content-type-json-as-html` | `text/html` | JSON-shaped body served as HTML. |
| `{{BASE_URL}}/sitemap-discovery-fail.xml` | `application/xml` | Invalid sitemap response with `503`. |
