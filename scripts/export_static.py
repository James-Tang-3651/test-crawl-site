from __future__ import annotations

import asyncio
import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.main import app
from app.test_catalog import PAGE_MANIFEST, SECTION_METADATA


DIST_DIR = ROOT_DIR / "dist"
ROUTES_DIR = DIST_DIR / "__routes"

STRUCTURED_CONTENT_GROUPS = ["table", "list", "markdown", "article"]
SITEMAP_PATHS = [
    *[f"/sitemaps/{section['id']}.xml" for section in SECTION_METADATA],
    *[f"/sitemaps/structured-content/{group}.xml" for group in STRUCTURED_CONTENT_GROUPS],
]

EXTRA_PATHS = [
    "/_manifest",
    "/table-content",
    "/table-link",
    "/paywall-preview",
    *SITEMAP_PATHS,
    "/redirect-middle",
    "/redirect-loop-b",
    "/fr/noodles",
    "/sitemap-discovery-fail.xml",
    "/sitemap-invalid-404",
    "/server-only/article-related-links",
    "/server-only/article-related-links-empty",
    "/server-only/load-more",
    "/server-only/modal-popup",
    "/server-only/accordion/soup",
    "/server-only/accordion/dry",
    "/server-only/tabs/broth",
    "/server-only/tabs/toppings",
    "/server-only/tabs/links",
    "/product-pages/javascript-calculated/data.json",
    "/product-pages/laptop-configurator/data.json",
    "/files/sample.pdf",
    "/files/sample.docx",
    "/media/pixel.jpg",
    "/media/png-example.png",
    "/media/gif-example.gif",
    "/media/webpfile.webp",
    "/media/bank-card-svgrepo-com.svg",
    "/media/shrek-rizz-face.jpg",
    "/download/sample.zip",
]

# These routes need request-time behavior that cannot be faithfully represented
# by static files and Netlify redirect rules alone.
FUNCTION_PATHS = {
    "/accept-consent",
    "/about",
    "/localhost-link",
    "/query-page",
    "/redirect-middle",
    "/slow",
    "/status/504",
    "/weather/vancouver-daily-report",
    "/weather/vancouver-daily-report/data.json",
    "/weather/vancouver-weekly-report",
}

CONTENT_TYPE_EXTENSIONS = {
    "application/json": ".json",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/xml": ".xml",
    "application/zip": ".zip",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
    "text/html": ".html",
    "text/markdown": ".md",
    "text/plain": ".txt",
    "text/xml": ".xml",
}

PRESERVED_HEADERS = {
    "content-type",
    "retry-after",
}


@dataclass
class ExportedRoute:
    source_path: str
    target_path: str
    status_code: int
    headers: dict[str, str]


@dataclass
class RedirectRoute:
    source_path: str
    target_path: str
    status_code: int


async def call_asgi_app(path: str, base_url: str) -> tuple[int, dict[str, str], bytes]:
    base = urlsplit(base_url)
    request_url = urlsplit(base_url.rstrip("/") + path)
    host = base.hostname or "localhost"
    port = base.port or (443 if base.scheme == "https" else 80)

    response_start: dict[str, object] = {}
    body_parts: list[bytes] = []
    request_sent = False

    async def receive() -> dict[str, object]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, object]) -> None:
        if message["type"] == "http.response.start":
            response_start.update(message)
        elif message["type"] == "http.response.body":
            body_parts.append(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": base.scheme or "http",
        "path": request_url.path,
        "raw_path": request_url.path.encode("ascii"),
        "query_string": request_url.query.encode("ascii"),
        "headers": [
            (b"host", base.netloc.encode("ascii")),
            (b"user-agent", b"crawl-test-static-export"),
            (b"accept", b"*/*"),
        ],
        "client": ("127.0.0.1", 0),
        "server": (host, port),
        "root_path": "",
    }

    await app(scope, receive, send)

    status_code = int(response_start.get("status", 500))
    headers = {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in response_start.get("headers", [])
    }
    return status_code, headers, b"".join(body_parts)


def export_base_url() -> str:
    value = (
        os.environ.get("STATIC_EXPORT_BASE_URL")
        or os.environ.get("URL")
        or os.environ.get("DEPLOY_PRIME_URL")
        or "http://localhost:9000"
    ).strip()
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    return value.rstrip("/")


def ordered_unique(paths: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_paths: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique_paths.append(path)
    return unique_paths


def export_paths() -> list[str]:
    manifest_paths = [entry["path"] for entry in PAGE_MANIFEST]
    return ordered_unique([*manifest_paths, *EXTRA_PATHS])


def extension_for(headers: dict[str, str]) -> str:
    content_type = headers.get("content-type", "application/octet-stream")
    media_type = content_type.split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(media_type, ".bin")


def route_target_path(path: str, headers: dict[str, str]) -> str:
    if path == "/":
        slug = "index"
    else:
        # Strip query string and fragment so ? and # never appear in the filename.
        # Netlify rejects filenames containing either character.
        # The full path (with query/fragment) is still used for the hash so every
        # distinct URL gets its own unique file even when paths share a base.
        clean_path = path.split("?")[0].split("#")[0]
        slug = clean_path.strip("/").replace("/", "__").replace(".", "-") or "index"
    slug = slug[:30].rstrip("-_")
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
    return f"/__routes/{slug}-{digest}{extension_for(headers)}"


def write_route_file(target_path: str, content: bytes) -> None:
    file_path = DIST_DIR / target_path.lstrip("/")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)


def is_redirect(status_code: int, headers: dict[str, str]) -> bool:
    return 300 <= status_code < 400 and "location" in headers


def redirect_target(headers: dict[str, str]) -> str:
    return headers["location"]


def forceable_status(status_code: int) -> str:
    return f"{status_code}!"


def render_redirects(exported: list[ExportedRoute], redirects: list[RedirectRoute]) -> str:
    lines = [
        "# Generated by scripts/export_static.py. Do not edit directly.",
        "# Request-time routes are handled by netlify/functions/crawl-dynamic.mjs.",
    ]

    for route in redirects:
        lines.append(f"{route.source_path:<34} {route.target_path:<44} {route.status_code}")

    for route in exported:
        lines.append(
            f"{route.source_path:<34} {route.target_path:<44} {forceable_status(route.status_code)}"
        )

    return "\n".join(lines) + "\n"


def render_headers(exported: list[ExportedRoute]) -> str:
    lines = ["# Generated by scripts/export_static.py. Do not edit directly."]

    for route in exported:
        preserved = {
            key: value
            for key, value in route.headers.items()
            if key in PRESERVED_HEADERS
        }
        if not preserved:
            continue

        for path in (route.source_path, route.target_path):
            lines.append(path)
            for key, value in preserved.items():
                header_name = "-".join(part.capitalize() for part in key.split("-"))
                lines.append(f"  {header_name}: {value}")

    return "\n".join(lines) + "\n"


async def export() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)

    base_url = export_base_url()
    exported_routes: list[ExportedRoute] = []
    redirect_routes: list[RedirectRoute] = []
    function_routes: list[str] = []

    for path in export_paths():
        if path in FUNCTION_PATHS:
            function_routes.append(path)
            continue

        status_code, headers, body = await call_asgi_app(path, base_url)
        if is_redirect(status_code, headers):
            redirect_routes.append(
                RedirectRoute(
                    source_path=path,
                    target_path=redirect_target(headers),
                    status_code=status_code,
                )
            )
            continue

        target_path = route_target_path(path, headers)
        write_route_file(target_path, body)
        exported_routes.append(
            ExportedRoute(
                source_path=path,
                target_path=target_path,
                status_code=status_code,
                headers=headers,
            )
        )

        if path == "/" and headers.get("content-type", "").startswith("text/html"):
            write_route_file("/index.html", body)

    (DIST_DIR / "_redirects").write_text(
        render_redirects(exported_routes, redirect_routes),
        encoding="utf-8",
    )
    (DIST_DIR / "_headers").write_text(
        render_headers(exported_routes),
        encoding="utf-8",
    )

    print(f"Export base URL: {base_url}")
    print(f"Static routes exported: {len(exported_routes)}")
    print(f"Redirect routes exported: {len(redirect_routes)}")
    print(f"Function routes skipped: {len(function_routes)}")
    print(f"Publish directory: {DIST_DIR}")


def main() -> None:
    asyncio.run(export())


if __name__ == "__main__":
    main()
