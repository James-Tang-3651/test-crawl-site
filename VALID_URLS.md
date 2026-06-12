# Crawl Test Site Valid URLs

Generated from `app/test_catalog.py`, `app/depth_routes.py`, `app/product_catalog.py`, and `app/main.py` on 2026-05-24.

Use these as path-relative URLs under whichever base URL the test site is running on, for example `http://localhost:8000`.

Notes:
- The manifest section lists unique crawl-worthy paths from `PAGE_MANIFEST`, including generated `/depth/*`, `/many/item/*`, and product variant pages.
- The route-only section lists valid app endpoints that are not unique manifest content pages, including JSON endpoints, server-only fragments, redirect aliases, sitemap files, robots-blocked targets, and downloadable/media assets.
- Status-code test endpoints such as `/status/404` are valid test routes even though they intentionally return non-2xx responses.
- `/share-links` exposes share-widget anchors (AddToAny/Facebook style) that point at `/weather/vancouver-daily-report` standing in for the share service, with a percent-encoded URL of this site's About page embedded in their query string or fragment. The valid discovered URLs there are the weather report URLs only; `/about/?campaign_id=share-fragment`, `/about/?campaign_id=share-query`, and `/about/?campaign_id=share-double-encoded` must NOT appear in a crawl — their presence means the crawler decoded a URL embedded inside another URL.

## Manifest URLs (213)

### Core URL Handling (18)

- `/` - Root page
- `/about` - Relative About
- `/absolute` - Absolute link
- `/protocol-relative-target` - Protocol-relative link
- `/docs` - Docs without slash
- `/docs/` - Docs with slash
- `/CasePage` - Uppercase path
- `/casepage` - Lowercase path
- `/SameContent` - Uppercase path same content
- `/samecontent` - Lowercase path same content
- `/base-tag` - Base tag page
- `/docs/child-from-base` - Base tag child page
- `/query-page` - Query variants
- `/localhost-link` - Localhost absolute links
- `/share-links` - Share widget links with embedded encoded URLs
- `/long-href` - Long href over 2048 characters
- `/long-href-target` - Long href target
- `/legacy.php` - Legacy PHP-style page

### Redirects (5)

- `/redirect-start` - Redirect chain
- `/redirect-target` - Redirect target
- `/button-redirect` - Button redirect page
- `/button-redirect-target` - Button redirect target
- `/redirect-loop-a` - Redirect loop page

### Dynamic Content (17)

- `/client` - Client-rendered page
- `/delayed` - Delayed page
- `/article-related-load` - Article related links after load
- `/article-related-load-empty` - Article related links empty after load
- `/shadow` - Shadow DOM page
- `/load-more` - Load more page - Hidden DOM
- `/infinite` - Infinite scroll page
- `/modal-popup` - Modal popup page - Hidden DOM
- `/accordion` - Accordion page - Hidden DOM
- `/tabs` - Tab page - Hidden DOM
- `/css-generated` - CSS generated content page
- `/carousel` - Horizontal carousel page
- `/carousel-arrows` - Horizontal carousel with arrow navigation page
- `/chatbot-widget` - Chatbot widget page
- `/scroll-reveal` - Scroll reveal page
- `/blocking-popup` - Blocking popup page
- `/javascript-created-links` - JavaScript created links page

### Security Test (9)

- `/security/cookie-theft` - XSS Cookie Theft payloads
- `/security/storage-theft` - XSS Storage Theft payloads
- `/security/page-hijack` - XSS Page Hijack payloads
- `/security/phishing` - XSS Phishing payloads
- `/security/keylogger` - XSS Keylogger payloads
- `/security/beacon-recon` - XSS Beacon and Recon payloads
- `/security/obfuscated` - XSS Obfuscated payloads
- `/security/bad-links` - XSS Bad Link payloads
- `/security/clean-controls` - Security clean control cases

### Errors and Status (13)

- `/broken` - Broken HTML
- `/slow` - Slow page
- `/transient-load` - Transient load failure then success
- `/transient-load-child` - Transient load child page
- `/empty` - Empty 200 page
- `/soft-error` - Soft error page
- `/status/403` - 403 page
- `/status/404` - 404 page
- `/status/429` - 429 page
- `/status/500` - 500 page
- `/status/504` - 504 page
- `/wrong-content-type-html-as-text` - HTML served as text/plain page
- `/wrong-content-type-json-as-html` - JSON served as text/html page

### Media and Embeds (5)

- `/iframe-host` - Iframe host
- `/iframe-content` - Iframe content
- `/iframe-pdf` - Iframe PDF page
- `/custom-video` - Custom video control page
- `/image-link` - Image link page

### Discovery and Policy (5)

- `/sitemap-only` - Sitemap-only page
- `/sitemap-exclusive-edge-case` - Unique sitemap-only edge case page
- `/sitemap-discovery-fail` - Failing sitemap discovery page
- `/robots.txt` - Robots.txt
- `/sitemap.xml` - Sitemap XML

### Char Limit Tests (3)

- `/oversized-title` - Oversized title
- `/oversized-charset` - Oversized charset
- `/oversized-mime-type` - Oversized MIME type

### weather daily update changeFrequency (1)

- `/weather/vancouver-daily-report` - Vancouver daily weather report

### Scale and Graph Shape (108)

- `/many-links` - Many links page
- `/load-test` - Large static load-test page
- `/self-reference-direct` - Direct self-reference page
- `/self-reference-cycle-a` - Two-page self-reference cycle
- `/self-reference-cycle-b` - Self-reference cycle B
- `/sub-page-main-reference` - Sub-page back to main page
- `/depth/0` - Max depth test page
- `/many/item/0` - Many item 0
- `/many/item/1` - Many item 1
- `/many/item/2` - Many item 2
- `/many/item/3` - Many item 3
- `/many/item/4` - Many item 4
- `/many/item/5` - Many item 5
- `/many/item/6` - Many item 6
- `/many/item/7` - Many item 7
- `/many/item/8` - Many item 8
- `/many/item/9` - Many item 9
- `/many/item/10` - Many item 10
- `/many/item/11` - Many item 11
- `/many/item/12` - Many item 12
- `/many/item/13` - Many item 13
- `/many/item/14` - Many item 14
- `/many/item/15` - Many item 15
- `/many/item/16` - Many item 16
- `/many/item/17` - Many item 17
- `/many/item/18` - Many item 18
- `/many/item/19` - Many item 19
- `/many/item/20` - Many item 20
- `/many/item/21` - Many item 21
- `/many/item/22` - Many item 22
- `/many/item/23` - Many item 23
- `/many/item/24` - Many item 24
- `/many/item/25` - Many item 25
- `/many/item/26` - Many item 26
- `/many/item/27` - Many item 27
- `/many/item/28` - Many item 28
- `/many/item/29` - Many item 29
- `/many/item/30` - Many item 30
- `/many/item/31` - Many item 31
- `/many/item/32` - Many item 32
- `/many/item/33` - Many item 33
- `/many/item/34` - Many item 34
- `/many/item/35` - Many item 35
- `/many/item/36` - Many item 36
- `/many/item/37` - Many item 37
- `/many/item/38` - Many item 38
- `/many/item/39` - Many item 39
- `/depth/1` - Depth level 1
- `/depth/2` - Depth level 2
- `/depth/3` - Depth level 3
- `/depth/4` - Depth level 4
- `/depth/5` - Depth level 5
- `/depth/6` - Depth level 6
- `/depth/7` - Depth level 7
- `/depth/8` - Depth level 8
- `/depth/9` - Depth level 9
- `/depth/10` - Depth level 10
- `/depth/11` - Depth level 11
- `/depth/12` - Depth level 12
- `/depth/13` - Depth level 13
- `/depth/14` - Depth level 14
- `/depth/15` - Depth level 15
- `/depth/16` - Depth level 16
- `/depth/17` - Depth level 17
- `/depth/18` - Depth level 18
- `/depth/19` - Depth level 19
- `/depth/20` - Depth level 20
- `/depth/21` - Depth level 21
- `/depth/22` - Depth level 22
- `/depth/23` - Depth level 23
- `/depth/24` - Depth level 24
- `/depth/25` - Depth level 25
- `/depth/26` - Depth level 26
- `/depth/27` - Depth level 27
- `/depth/28` - Depth level 28
- `/depth/29` - Depth level 29
- `/depth/30` - Depth level 30
- `/depth/31` - Depth level 31
- `/depth/32` - Depth level 32
- `/depth/33` - Depth level 33
- `/depth/34` - Depth level 34
- `/depth/35` - Depth level 35
- `/depth/36` - Depth level 36
- `/depth/37` - Depth level 37
- `/depth/38` - Depth level 38
- `/depth/39` - Depth level 39
- `/depth/40` - Depth level 40
- `/depth/41` - Depth level 41
- `/depth/42` - Depth level 42
- `/depth/43` - Depth level 43
- `/depth/44` - Depth level 44
- `/depth/45` - Depth level 45
- `/depth/46` - Depth level 46
- `/depth/47` - Depth level 47
- `/depth/48` - Depth level 48
- `/depth/49` - Depth level 49
- `/depth/50` - Depth level 50
- `/depth/51` - Depth level 51
- `/depth/52` - Depth level 52
- `/depth/53` - Depth level 53
- `/depth/54` - Depth level 54
- `/depth/55` - Depth level 55
- `/depth/56` - Depth level 56
- `/depth/57` - Depth level 57
- `/depth/58` - Depth level 58
- `/depth/59` - Depth level 59
- `/depth/60` - Depth level 60
- `/depth/61` - Depth level 61

### Localization and State (3)

- `/consent` - Consent page
- `/accept-consent` - Accept consent route
- `/fr/about` - French About page with /fr path

### Product Pages (13)

- `/product-pages/separate-pages` - Product variants - Separate pages
- `/product-pages/javascript-calculated` - Product variants - JavaScript calculated
- `/product-pages/javascript-rendered-grid` - Product collection - JavaScript rendered grid
- `/product-pages/laptop-configurator` - Laptop configurator - Dependent options
- `/product-pages/separate-pages/steel-blue/18oz` - Product variant page: Steel Blue / 18 oz
- `/product-pages/separate-pages/steel-blue/24oz` - Product variant page: Steel Blue / 24 oz
- `/product-pages/separate-pages/steel-blue/32oz` - Product variant page: Steel Blue / 32 oz
- `/product-pages/separate-pages/sage-green/18oz` - Product variant page: Sage Green / 18 oz
- `/product-pages/separate-pages/sage-green/24oz` - Product variant page: Sage Green / 24 oz
- `/product-pages/separate-pages/sage-green/32oz` - Product variant page: Sage Green / 32 oz
- `/product-pages/separate-pages/matte-black/18oz` - Product variant page: Matte Black / 18 oz
- `/product-pages/separate-pages/matte-black/24oz` - Product variant page: Matte Black / 24 oz
- `/product-pages/separate-pages/matte-black/32oz` - Product variant page: Matte Black / 32 oz

### Structured Content (13)

- `/structured-content` - Structured Content hub
- `/structured-content/table` - Structured table content hub
- `/structured-content/table/content` - Table content page
- `/structured-content/table/links` - Table cell link page
- `/structured-content/list` - Structured list content hub
- `/structured-content/list/basic` - Basic list content page
- `/structured-content/list/nested` - Nested list content page
- `/structured-content/markdown` - Structured markdown content hub
- `/structured-content/markdown/inline-links` - Markdown inline links page
- `/structured-content/markdown/reference-links` - Markdown reference links page
- `/structured-content/markdown/sample.md` - Raw Markdown document
- `/structured-content/article` - Structured article content hub
- `/structured-content/article/paywall-preview` - Paywall preview page

## Data and Server-Only Endpoints (13)

- `/product-pages/javascript-calculated/data.json`
- `/product-pages/javascript-rendered-grid/data.json`
- `/product-pages/laptop-configurator/data.json`
- `/server-only/accordion/dry`
- `/server-only/accordion/soup`
- `/server-only/article-related-links`
- `/server-only/article-related-links-empty`
- `/server-only/load-more`
- `/server-only/modal-popup`
- `/server-only/tabs/broth`
- `/server-only/tabs/links`
- `/server-only/tabs/toppings`
- `/weather/vancouver-daily-report/data.json`

## Redirect and Legacy Alias Endpoints (5)

- `/paywall-preview`
- `/redirect-loop-b`
- `/redirect-middle`
- `/table-content`
- `/table-link`

## Sitemap, Robots, and Policy Endpoints (19)

- `/robots-blocked`
- `/sitemap-discovery-fail.xml`
- `/sitemap-invalid-404`
- `/sitemaps/core-url-handling.xml`
- `/sitemaps/discovery-policy.xml`
- `/sitemaps/dynamic-content.xml`
- `/sitemaps/errors-status.xml`
- `/sitemaps/localized-state.xml`
- `/sitemaps/media-embeds.xml`
- `/sitemaps/product-pages.xml`
- `/sitemaps/redirects.xml`
- `/sitemaps/scale-graph.xml`
- `/sitemaps/security-test.xml`
- `/sitemaps/structured-content.xml`
- `/sitemaps/structured-content/article.xml`
- `/sitemaps/structured-content/list.xml`
- `/sitemaps/structured-content/markdown.xml`
- `/sitemaps/structured-content/table.xml`
- `/sitemaps/weather-daily-update-changefrequency.xml`

## Asset URLs (9)

- `/download/sample.zip`
- `/files/sample.docx`
- `/files/sample.pdf`
- `/media/bank-card-svgrepo-com.svg`
- `/media/gif-example.gif`
- `/media/pixel.jpg`
- `/media/png-example.png`
- `/media/shrek-rizz-face.jpg`
- `/media/webpfile.webp`

## Other Route-Only URLs (2)

- `/_manifest`
- `/fr/noodles`

## Known Link Variants With Query, Fragment, or Absolute Host Form (101)

- `//{HOST}/protocol-relative-target`
- `/about/?from=article-related-load`
- `/about/?from=basic-list`
- `/about/?from=button-target`
- `/about/?from=html-as-text`
- `/about/?from=image-link`
- `/about/?from=javascript-created`
- `/about/?from=load-test`
- `/about/?from=markdown-inline`
- `/about/?from=robots-blocked`
- `/about/?from=sitemap-discovery-fail`
- `/about/?from=table-cell`
- `/many-links/?from=infinite`
- `/many-links/?from=load-test`
- `/many-links/?from=server-load-more`
- `/many/item/0/?ref=list`
- `/many/item/10/?ref=list`
- `/many/item/11/?ref=list`
- `/many/item/12/?ref=list`
- `/many/item/13/?ref=list`
- `/many/item/14/?ref=list`
- `/many/item/15/?ref=list`
- `/many/item/16/?ref=list`
- `/many/item/17/?ref=list`
- `/many/item/18/?ref=list`
- `/many/item/19/?ref=list`
- `/many/item/1/?ref=list`
- `/many/item/20/?ref=list`
- `/many/item/21/?ref=list`
- `/many/item/22/?ref=list`
- `/many/item/23/?ref=list`
- `/many/item/24/?ref=list`
- `/many/item/25/?ref=list`
- `/many/item/26/?ref=list`
- `/many/item/27/?ref=list`
- `/many/item/28/?ref=list`
- `/many/item/29/?ref=list`
- `/many/item/2/?ref=list`
- `/many/item/30/?ref=list`
- `/many/item/31/?ref=list`
- `/many/item/32/?ref=list`
- `/many/item/33/?ref=list`
- `/many/item/34/?ref=list`
- `/many/item/35/?ref=list`
- `/many/item/36/?ref=list`
- `/many/item/37/?ref=list`
- `/many/item/38/?ref=list`
- `/many/item/39/?ref=list`
- `/many/item/3/?ref=list`
- `/many/item/4/?ref=list`
- `/many/item/5/?ref=list`
- `/many/item/6/?ref=list`
- `/many/item/7/?ref=list`
- `/many/item/8/?ref=list`
- `/many/item/9/?ref=list`
- `/query-page/?accessory=carry-sling`
- `/query-page/?accessory=cleaning-kit`
- `/query-page/?accessory=expansion-card-pack`
- `/query-page/?accessory=input-deck`
- `/query-page/?accessory=laptop-sleeve`
- `/query-page/?accessory=straw-lid`
- `/query-page/?category=chili&from=nested-list`
- `/query-page/?category=miso&from=nested-list`
- `/query-page/?category=sesame&from=nested-list`
- `/query-page/?category=shoyu&from=nested-list`
- `/query-page/?consent=1`
- `/query-page/?dish=chili-garlic&from=table-cell`
- `/query-page/?dish=mushroom&from=basic-list`
- `/query-page/?dish=server-dry-noodles`
- `/query-page/?dish=server-soup-noodles`
- `/query-page/?dish=sesame&from=basic-list`
- `/query-page/?dish=sesame-scallion&from=table-cell`
- `/query-page/?from=article-related-load-1`
- `/query-page/?from=blocking-popup`
- `/query-page/?from=carousel`
- `/query-page/?from=carousel-arrows`
- `/query-page/?from=chatbot-widget`
- `/query-page/?from=javascript-created`
- `/query-page/?from=legacy-php`
- `/query-page/?from=paywall-preview`
- `/query-page/?from=paywall-subscribe`
- `/query-page/?from=scroll-reveal`
- `/query-page/?from=server-modal-popup`
- `/query-page/?from=server-tab-broth`
- `/query-page/?from=server-tab-links`
- `/query-page/?from=server-tab-toppings`
- `/query-page/?from=sitemap-discovery-fail`
- `/query-page/?q=hello+world&encoded=%252Fdocs`
- `/query-page/?ref=abc`
- `/query-page/?ref=slow`
- `/query-page/?ref=xyz#frag`
- `/query-page/?sort=price`
- `/query-page/?topic=broth&from=markdown-inline`
- `/query-page/?topic=toppings&from=markdown-reference`
- `/structured-content/list/basic/?from=markdown-reference`
- `/structured-content/table/links/?from=sitemap-discovery-fail`
- `/structured-content/?from=load-test`
- `/weather/vancouver-daily-report#url=https%3A%2F%2F{HOST}%2Fabout%2F%3Fcampaign_id%3Dshare-fragment&title=About%20the%20noodle%20stand`
- `/weather/vancouver-daily-report#url=https%253A%252F%252F{HOST}%252Fabout%252F%253Fcampaign_id%253Dshare-double-encoded&title=About%20the%20noodle%20stand`
- `/weather/vancouver-daily-report/?u=https%3A%2F%2F{HOST}%2Fabout%2F%3Fcampaign_id%3Dshare-query`
- `{BASE_URL}/absolute`
