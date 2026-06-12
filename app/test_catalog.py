from typing import Any, Dict, Iterator, List

from app.depth_config import MAX_DEPTH_LEVEL, TOTAL_DEPTH_PAGES
from app.product_catalog import iter_product_variants


INTERNAL_ENTRY_KEYS = {"home_links", "include_in_manifest"}


TEST_SECTIONS: List[Dict[str, Any]] = [
    {
        "id": "core-url-handling",
        "title": "Core URL Handling",
        "entries": [
            {"path": "/", "crawl_worthy": True, "category": "root", "label": "Root page"},
            {
                "path": "/about",
                "crawl_worthy": True,
                "category": "server_rendered",
                "label": "Relative About",
                "home_links": [{"href": "/about", "label": "Relative About"}],
            },
            {
                "path": "/absolute",
                "crawl_worthy": True,
                "category": "absolute_link",
                "label": "Absolute link",
                "home_links": [{"href": "{base}/absolute", "label": "Absolute link"}],
            },
            {
                "path": "/protocol-relative-target",
                "crawl_worthy": True,
                "category": "protocol_relative",
                "label": "Protocol-relative link",
                "home_links": [{"href": "//{netloc}/protocol-relative-target", "label": "Protocol-relative link"}],
            },
            {
                "path": "/docs",
                "crawl_worthy": True,
                "category": "trailing_slash",
                "label": "Docs without slash",
                "home_links": [{"href": "/docs", "label": "Docs without slash"}],
            },
            {
                "path": "/docs/",
                "crawl_worthy": True,
                "category": "trailing_slash_duplicate",
                "label": "Docs with slash",
                "home_links": [{"href": "/docs/", "label": "Docs with slash"}],
            },
            {
                "path": "/CasePage",
                "crawl_worthy": True,
                "category": "case_sensitive",
                "label": "Uppercase path",
                "home_links": [{"href": "/CasePage", "label": "Uppercase path"}],
            },
            {
                "path": "/casepage",
                "crawl_worthy": True,
                "category": "case_sensitive",
                "label": "Lowercase path",
                "home_links": [{"href": "/casepage", "label": "Lowercase path"}],
            },
            {
                "path": "/SameContent",
                "crawl_worthy": True,
                "category": "case_sensitive_same_content",
                "label": "Uppercase path same content",
                "home_links": [{"href": "/SameContent", "label": "Uppercase path same content"}],
            },
            {
                "path": "/samecontent",
                "crawl_worthy": True,
                "category": "case_sensitive_same_content",
                "label": "Lowercase path same content",
                "home_links": [{"href": "/samecontent", "label": "Lowercase path same content"}],
            },
            {
                "path": "/base-tag",
                "crawl_worthy": True,
                "category": "base_tag",
                "label": "Base tag page",
                "home_links": [{"href": "/base-tag", "label": "Base tag page"}],
            },
            {
                "path": "/docs/child-from-base",
                "crawl_worthy": True,
                "category": "base_tag_child",
                "label": "Base tag child page",
            },
            {
                "path": "/query-page",
                "crawl_worthy": True,
                "category": "query_variants",
                "label": "Query variants",
                "home_links": [
                    {"href": "/query-page/?{encoded_query}", "label": "Encoded query link"},
                    {"href": "/query-page/?ref=abc", "label": "Query variant A"},
                    {"href": "/query-page/?ref=xyz#frag", "label": "Query variant B"},
                ],
            },
            {
                "path": "/localhost-link",
                "crawl_worthy": True,
                "category": "localhost_links",
                "label": "Localhost absolute links",
                "home_links": [{"href": "/localhost-link", "label": "Localhost absolute links page"}],
            },
            {
                "path": "/long-href",
                "crawl_worthy": True,
                "category": "long_href",
                "href_length_gt": 2048,
                "label": "Long href over 2048 characters",
                "home_links": [{"href": "/long-href", "label": "Long href over 2048 characters"}],
            },
            {
                "path": "/long-href-target",
                "crawl_worthy": True,
                "category": "long_href_target",
                "label": "Long href target",
            },
            {
                "path": "/legacy.php",
                "crawl_worthy": True,
                "category": "php_path",
                "label": "Legacy PHP-style page",
                "home_links": [{"href": "/legacy.php", "label": "Legacy PHP-style page"}],
            },
            {
                "category": "anchor_only",
                "include_in_manifest": False,
                "label": "Anchor only",
                "home_links": [{"href": "#local-anchor", "label": "Anchor only"}],
            },
            {
                "category": "javascript_href",
                "include_in_manifest": False,
                "label": "JavaScript pseudo link",
                "home_links": [{"href": "javascript:void(0)", "label": "JavaScript pseudo link"}],
            },
            {
                "category": "mailto_href",
                "include_in_manifest": False,
                "label": "Mailto",
                "home_links": [{"href": "mailto:test@example.com", "label": "Mailto"}],
            },
            {
                "category": "tel_href",
                "include_in_manifest": False,
                "label": "Tel",
                "home_links": [{"href": "tel:+15550101", "label": "Tel"}],
            },
            {
                "category": "empty_href",
                "include_in_manifest": False,
                "label": "Empty href",
                "home_links": [{"href": "", "label": "Empty href"}],
            },
            {
                "category": "missing_href",
                "include_in_manifest": False,
                "label": "Missing href",
                "home_links": [{"label": "Missing href"}],
            },
            {
                "category": "whitespace_href",
                "include_in_manifest": False,
                "label": "Whitespace href",
                "home_links": [{"href": "   /about%20  ", "label": "Whitespace href"}],
            },
            {
                "category": "external_url",
                "include_in_manifest": False,
                "label": "External URL",
                "home_links": [{"href": "https://example.org/external", "label": "External URL"}],
            },
            {
                "path": "/share-links",
                "crawl_worthy": True,
                "category": "share_widget_links",
                "label": "Share widget links with embedded encoded URLs",
                "home_links": [
                    {"href": "/share-links", "label": "Share widget links with embedded encoded URLs"},
                ],
            },
        ],
    },
    {
        "id": "hash-navigation",
        "title": "Hash Navigation",
        "entries": [
            {
                "path": "/hash-anchors",
                "crawl_worthy": True,
                "category": "hash_anchor_navigation",
                "label": "Hash anchor sections page",
                "home_links": [
                    {"href": "/hash-anchors", "label": "Hash anchor sections page"},
                    {"href": "/hash-anchors#section-a", "label": "Hash anchor - Section A"},
                    {"href": "/hash-anchors#section-b", "label": "Hash anchor - Section B"},
                    {"href": "/hash-anchors#section-c", "label": "Hash anchor - Section C"},
                ],
            },
            {
                "path": "/hash-router",
                "crawl_worthy": True,
                "category": "hash_spa_routing",
                "label": "Hash router (SPA-style) page",
                "home_links": [
                    {"href": "/hash-router", "label": "Hash router (SPA-style) page"},
                    {"href": "/hash-router#overview", "label": "Hash router - Overview"},
                    {"href": "/hash-router#specs", "label": "Hash router - Specs"},
                    {"href": "/hash-router#reviews", "label": "Hash router - Reviews"},
                ],
            },
            {
                "path": "/hash-path-router",
                "crawl_worthy": True,
                "category": "hash_path_routing",
                "label": "Hash-path router (Angular / Vue hash mode style) page",
                "home_links": [
                    {"href": "/hash-path-router", "label": "Hash-path router page"},
                ],
            },
            {
                "path": "/hash-query-combo",
                "crawl_worthy": True,
                "category": "hash_query_combo",
                "label": "Query string + hash fragment combo page",
                "home_links": [
                    {"href": "/hash-query-combo", "label": "Query string + hash fragment combo page"},
                    {"href": "/hash-query-combo/?q=test#results", "label": "Hash query combo - q=test"},
                    {"href": "/hash-query-combo/?q=other#results", "label": "Hash query combo - q=other"},
                ],
            },
            {
                "path": "/hashbang-router",
                "crawl_worthy": True,
                "category": "hashbang_routing",
                "label": "Hashbang router (#! pattern) page",
                "home_links": [
                    {"href": "/hashbang-router", "label": "Hashbang router page"},
                ],
            },
            {
                "path": "/percent-encoded-hash",
                "crawl_worthy": True,
                "category": "percent_encoded_hash",
                "label": "Percent-encoded hash (%23) vs fragment (#) page",
                "home_links": [
                    {"href": "/percent-encoded-hash", "label": "Percent-encoded hash demo page"},
                    {"href": "/percent-encoded-hash#real-anchor", "label": "Percent-encoded hash - real fragment"},
                    {"href": "/percent-encoded-hash%23real-anchor", "label": "Percent-encoded hash - %23 in path (expect 404)"},
                ],
            },
            {
                "path": "/hash-drawer",
                "crawl_worthy": True,
                "category": "hash_drawer",
                "label": "Hash drawer pattern page",
                "home_links": [
                    {"href": "/hash-drawer", "label": "Hash drawer page"},
                ],
            },
        ],
    },
    {
        "id": "redirects",
        "title": "Redirects",
        "entries": [
            {
                "path": "/redirect-start",
                "crawl_worthy": True,
                "category": "redirect",
                "label": "Redirect chain",
                "home_links": [{"href": "/redirect-start", "label": "Redirect chain"}],
            },
            {"path": "/redirect-target", "crawl_worthy": True, "category": "redirect_target", "label": "Redirect target"},
            {
                "path": "/button-redirect",
                "crawl_worthy": True,
                "category": "button_redirect",
                "requires_interaction": True,
                "label": "Button redirect page",
                "home_links": [{"href": "/button-redirect", "label": "Button redirect page"}],
            },
            {
                "path": "/button-redirect-target",
                "crawl_worthy": True,
                "category": "button_redirect_target",
                "label": "Button redirect target",
            },
            {
                "path": "/redirect-loop-a",
                "crawl_worthy": True,
                "category": "redirect_loop",
                "label": "Redirect loop page",
                "home_links": [{"href": "/redirect-loop-a", "label": "Redirect loop page"}],
            },
        ],
    },
    {
        "id": "dynamic-content",
        "title": "Dynamic Content",
        "entries": [
            {
                "path": "/client",
                "crawl_worthy": True,
                "category": "client_rendered",
                "label": "Client-rendered page",
                "home_links": [{"href": "/client", "label": "Client-rendered page"}],
            },
            {
                "path": "/delayed",
                "crawl_worthy": True,
                "category": "delayed_async",
                "label": "Delayed page",
                "home_links": [{"href": "/delayed", "label": "Delayed page"}],
            },
            {
                "path": "/article-related-load",
                "crawl_worthy": True,
                "category": "article_related_load_fetch",
                "requires_javascript": True,
                "dynamic_content_generated": True,
                "data_not_in_initial_dom": True,
                "server_loaded_after_page_load": True,
                "label": "Article related links after load",
                "home_links": [{"href": "/article-related-load", "label": "Article related links after load"}],
            },
            {
                "path": "/article-related-load-empty",
                "crawl_worthy": True,
                "category": "article_related_load_empty_fetch",
                "requires_javascript": True,
                "dynamic_content_generated": True,
                "data_not_in_initial_dom": True,
                "server_loaded_after_page_load": True,
                "expected_link_count": 0,
                "label": "Article related links empty after load",
                "home_links": [
                    {"href": "/article-related-load-empty", "label": "Article related links empty after load"}
                ],
            },
            {
                "path": "/shadow",
                "crawl_worthy": True,
                "category": "shadow_dom",
                "label": "Shadow DOM page",
                "home_links": [{"href": "/shadow", "label": "Shadow DOM page"}],
            },
            {
                "path": "/load-more",
                "crawl_worthy": True,
                "category": "load_more_hidden_dom",
                "requires_interaction": True,
                "dynamic_content_generated": True,
                "not_in_initial_dom": True,
                "removes_from_dom_on_close": True,
                "label": "Load more page - Hidden DOM",
                "home_links": [{"href": "/load-more", "label": "Load more page - Hidden DOM"}],
            },
            {
                "path": "/infinite",
                "crawl_worthy": True,
                "category": "infinite_scroll",
                "label": "Infinite scroll page",
                "home_links": [{"href": "/infinite", "label": "Infinite scroll page"}],
            },
            {
                "path": "/modal-popup",
                "crawl_worthy": True,
                "category": "modal_popup_hidden_dom",
                "requires_interaction": True,
                "dynamic_content_generated": True,
                "not_in_initial_dom": True,
                "removes_from_dom_on_close": True,
                "label": "Modal popup page - Hidden DOM",
                "home_links": [{"href": "/modal-popup", "label": "Modal popup page - Hidden DOM"}],
            },
            {
                "path": "/accordion",
                "crawl_worthy": True,
                "category": "accordion_hidden_dom",
                "requires_interaction": True,
                "dynamic_content_generated": True,
                "not_in_initial_dom": True,
                "removes_from_dom_on_close": True,
                "label": "Accordion page - Hidden DOM",
                "home_links": [{"href": "/accordion", "label": "Accordion page - Hidden DOM"}],
            },
            {
                "path": "/tabs",
                "crawl_worthy": True,
                "category": "tabs_hidden_dom",
                "requires_interaction": True,
                "dynamic_content_generated": True,
                "footer_reflow_on_interaction": True,
                "not_in_initial_dom": True,
                "removes_from_dom_on_close": True,
                "label": "Tab page - Hidden DOM",
                "home_links": [{"href": "/tabs", "label": "Tab page - Hidden DOM"}],
            },
            {
                "path": "/css-generated",
                "crawl_worthy": True,
                "category": "css_generated_content",
                "label": "CSS generated content page",
                "home_links": [{"href": "/css-generated", "label": "CSS generated content page"}],
            },
            {
                "path": "/carousel",
                "crawl_worthy": True,
                "category": "horizontal_carousel",
                "label": "Horizontal carousel page",
                "home_links": [{"href": "/carousel", "label": "Horizontal carousel page"}],
            },
            {
                "path": "/carousel-arrows",
                "crawl_worthy": True,
                "category": "horizontal_carousel_arrow_navigation",
                "requires_interaction": True,
                "label": "Horizontal carousel with arrow navigation page",
                "home_links": [{"href": "/carousel-arrows", "label": "Horizontal carousel with arrow navigation page"}],
            },
            {
                "path": "/chatbot-widget",
                "crawl_worthy": True,
                "category": "chatbot_widget",
                "label": "Chatbot widget page",
                "home_links": [{"href": "/chatbot-widget", "label": "Chatbot widget page"}],
            },
            {
                "path": "/scroll-reveal",
                "crawl_worthy": True,
                "category": "scroll_triggered_reveal",
                "requires_interaction": True,
                "label": "Scroll reveal page",
                "home_links": [{"href": "/scroll-reveal", "label": "Scroll reveal page"}],
            },
            {
                "path": "/blocking-popup",
                "crawl_worthy": True,
                "category": "blocking_popup",
                "requires_interaction": True,
                "label": "Blocking popup page",
                "home_links": [{"href": "/blocking-popup", "label": "Blocking popup page"}],
            },
            {
                "path": "/javascript-created-links",
                "crawl_worthy": True,
                "category": "javascript_created_links",
                "label": "JavaScript created links page",
                "home_links": [{"href": "/javascript-created-links", "label": "JavaScript created links page"}],
            },
            {
                "path": "/editable",
                "crawl_worthy": True,
                "category": "editable_page",
                "label": "Inline-editable PUT page",
                "home_links": [{"href": "/editable", "label": "Editable Page (PUT)"}],
            },
        ],
    },
    {
        "id": "security-test",
        "title": "Security Test",
        "entries": [
            {
                "path": "/security/cookie-theft",
                "crawl_worthy": True,
                "category": "security_cookie_theft",
                "security_group": "cookie-theft",
                "payloads_are_escaped": True,
                "label": "XSS Cookie Theft payloads",
                "home_links": [{"href": "/security/cookie-theft", "label": "Cookie Theft"}],
            },
            {
                "path": "/security/storage-theft",
                "crawl_worthy": True,
                "category": "security_storage_theft",
                "security_group": "storage-theft",
                "payloads_are_escaped": True,
                "label": "XSS Storage Theft payloads",
                "home_links": [{"href": "/security/storage-theft", "label": "Storage Theft"}],
            },
            {
                "path": "/security/page-hijack",
                "crawl_worthy": True,
                "category": "security_page_hijack",
                "security_group": "page-hijack",
                "payloads_are_escaped": True,
                "label": "XSS Page Hijack payloads",
                "home_links": [{"href": "/security/page-hijack", "label": "Page Hijack"}],
            },
            {
                "path": "/security/phishing",
                "crawl_worthy": True,
                "category": "security_phishing",
                "security_group": "phishing",
                "payloads_are_escaped": True,
                "label": "XSS Phishing payloads",
                "home_links": [{"href": "/security/phishing", "label": "Phishing"}],
            },
            {
                "path": "/security/keylogger",
                "crawl_worthy": True,
                "category": "security_keylogger",
                "security_group": "keylogger",
                "payloads_are_escaped": True,
                "label": "XSS Keylogger payloads",
                "home_links": [{"href": "/security/keylogger", "label": "Keylogger"}],
            },
            {
                "path": "/security/beacon-recon",
                "crawl_worthy": True,
                "category": "security_beacon_recon",
                "security_group": "beacon-recon",
                "payloads_are_escaped": True,
                "label": "XSS Beacon and Recon payloads",
                "home_links": [{"href": "/security/beacon-recon", "label": "Beacon / Recon"}],
            },
            {
                "path": "/security/obfuscated",
                "crawl_worthy": True,
                "category": "security_obfuscated",
                "security_group": "obfuscated",
                "payloads_are_escaped": True,
                "label": "XSS Obfuscated payloads",
                "home_links": [{"href": "/security/obfuscated", "label": "Obfuscated"}],
            },
            {
                "path": "/security/bad-links",
                "crawl_worthy": True,
                "category": "security_bad_links",
                "security_group": "bad-links",
                "payloads_are_escaped": True,
                "label": "XSS Bad Link payloads",
                "home_links": [
                    {"href": "/security/bad-links", "label": "Bad Links"},
                    {"href": "/security/bad-links/javascript-href", "label": "H1: javascript: Href"},
                    {"href": "/security/bad-links/data-url", "label": "H2: data: URL Href"},
                    {"href": "/security/bad-links/tabnabbing", "label": "H3: Tabnabbing"},
                ],
            },
            {
                "path": "/security/bad-links/javascript-href",
                "crawl_worthy": True,
                "category": "security_bad_links_javascript_href",
                "label": "H1: javascript: Href mock test",
            },
            {
                "path": "/security/bad-links/data-url",
                "crawl_worthy": True,
                "category": "security_bad_links_data_url",
                "label": "H2: data: URL Href mock test",
            },
            {
                "path": "/security/bad-links/tabnabbing",
                "crawl_worthy": True,
                "category": "security_bad_links_tabnabbing",
                "label": "H3: Tabnabbing mock test",
            },
            {
                "path": "/security/clean-controls",
                "crawl_worthy": True,
                "category": "security_clean_controls",
                "security_group": "clean-controls",
                "payloads_are_escaped": True,
                "label": "Security clean control cases",
                "home_links": [{"href": "/security/clean-controls", "label": "Clean Controls"}],
            },
        ],
    },
    {
        "id": "errors-status",
        "title": "Errors and Status",
        "entries": [
            {
                "path": "/broken",
                "crawl_worthy": True,
                "category": "broken_html",
                "label": "Broken HTML",
                "home_links": [{"href": "/broken", "label": "Broken HTML"}],
            },
            {
                "path": "/slow",
                "crawl_worthy": True,
                "category": "slow_page",
                "label": "Slow page",
                "home_links": [{"href": "/slow", "label": "Slow page"}],
            },
            {
                "path": "/transient-load",
                "crawl_worthy": True,
                "category": "transient_load",
                "failure_count_before_success": 5,
                "reset_path": "/transient-load/reset",
                "label": "Transient load failure then success",
                "home_links": [
                    {
                        "href": "/transient-load/?key=homepage",
                        "label": "Transient load failure then success",
                        "actions": [
                            {
                                "href": "/transient-load/reset?key=homepage",
                                "status_href": "/transient-load/status?key=homepage",
                                "label": "Reset homepage transient key",
                            }
                        ],
                    }
                ],
            },
            {
                "path": "/transient-load-child",
                "crawl_worthy": True,
                "category": "transient_load_child",
                "label": "Transient load child page",
            },
            {
                "path": "/intermittent-error",
                "crawl_worthy": True,
                "category": "intermittent_error",
                "label": "Intermittent error page (503 half of each hour)",
                "home_links": [
                    {"href": "/intermittent-error", "label": "Intermittent error page (timed 503 windows)"},
                ],
            },
            {
                "path": "/empty",
                "crawl_worthy": True,
                "category": "empty_200",
                "label": "Empty 200 page",
                "home_links": [{"href": "/empty", "label": "Empty 200 page"}],
            },
            {
                "path": "/soft-error",
                "crawl_worthy": True,
                "category": "soft_error",
                "label": "Soft error page",
                "home_links": [{"href": "/soft-error", "label": "Soft error page"}],
            },
            {
                "path": "/status/403",
                "crawl_worthy": True,
                "category": "status_page",
                "label": "403 page",
                "home_links": [{"href": "/status/403", "label": "403 page"}],
            },
            {
                "path": "/status/404",
                "crawl_worthy": True,
                "category": "status_page",
                "label": "404 page",
                "home_links": [{"href": "/status/404", "label": "404 page"}],
            },
            {
                "path": "/status/429",
                "crawl_worthy": True,
                "category": "status_page",
                "label": "429 page",
                "home_links": [{"href": "/status/429", "label": "429 page"}],
            },
            {
                "path": "/status/500",
                "crawl_worthy": True,
                "category": "status_page",
                "label": "500 page",
                "home_links": [{"href": "/status/500", "label": "500 page"}],
            },
            {
                "path": "/status/504",
                "crawl_worthy": True,
                "category": "status_page",
                "expected_status": 504,
                "label": "504 page",
                "home_links": [{"href": "/status/504", "label": "504 page"}],
            },
            {
                "path": "/status/504-html-external-link",
                "crawl_worthy": True,
                "category": "status_page",
                "expected_status": 504,
                "label": "504 page with HTML body linking to a nowhere page",
                "home_links": [
                    {"href": "/status/504-html-external-link", "label": "504 HTML body with link to nowhere"}
                ],
            },
            {
                "path": "/error-link-to-nowhere",
                "crawl_worthy": True,
                "category": "status_page",
                "label": "Link-to-nowhere landing page (reached only from 504 HTML body)",
                "home_links": [],
            },
            {
                "path": "/wrong-content-type-html-as-text",
                "crawl_worthy": True,
                "category": "wrong_content_type",
                "label": "HTML served as text/plain page",
                "home_links": [{"href": "/wrong-content-type-html-as-text", "label": "HTML served as text/plain page"}],
            },
            {
                "path": "/wrong-content-type-json-as-html",
                "crawl_worthy": True,
                "category": "wrong_content_type",
                "label": "JSON served as text/html page",
                "home_links": [{"href": "/wrong-content-type-json-as-html", "label": "JSON served as text/html page"}],
            },
        ],
    },
    {
        "id": "media-embeds",
        "title": "Media and Embeds",
        "entries": [
            {
                "path": "/iframe-host",
                "crawl_worthy": True,
                "category": "iframe_host",
                "label": "Iframe host",
                "home_links": [{"href": "/iframe-host", "label": "Iframe host"}],
            },
            {"path": "/iframe-content", "crawl_worthy": True, "category": "iframe_content", "label": "Iframe content"},
            {
                "path": "/iframe-pdf",
                "crawl_worthy": True,
                "category": "iframe_pdf",
                "label": "Iframe PDF page",
                "home_links": [{"href": "/iframe-pdf", "label": "Iframe PDF page"}],
            },
            {
                "path": "/custom-video",
                "crawl_worthy": True,
                "category": "custom_video_control",
                "label": "Custom video control page",
                "home_links": [{"href": "/custom-video", "label": "Custom video control page"}],
            },
            {
                "path": "/image-link",
                "crawl_worthy": True,
                "category": "image_link",
                "label": "Image link page",
                "home_links": [{"href": "/image-link", "label": "Image link page"}],
            },
            {
                "category": "pdf_asset",
                "include_in_manifest": False,
                "label": "PDF file",
                "home_links": [{"href": "/files/sample.pdf", "label": "PDF file"}],
            },
            {
                "category": "docx_asset",
                "include_in_manifest": False,
                "label": "DOCX file",
                "home_links": [{"href": "/files/sample.docx", "label": "DOCX file"}],
            },
            {
                "category": "image_asset",
                "include_in_manifest": False,
                "label": "Image file",
                "home_links": [{"href": "/media/pixel.jpg", "label": "Image file"}],
            },
            {
                "category": "image_png_asset",
                "include_in_manifest": False,
                "label": "PNG image file",
                "home_links": [{"href": "/media/png-example.png", "label": "PNG image file"}],
            },
            {
                "category": "image_gif_asset",
                "include_in_manifest": False,
                "label": "GIF image file",
                "home_links": [{"href": "/media/gif-example.gif", "label": "GIF image file"}],
            },
            {
                "category": "image_webp_asset",
                "include_in_manifest": False,
                "label": "WebP image file",
                "home_links": [{"href": "/media/webpfile.webp", "label": "WebP image file"}],
            },
            {
                "category": "image_svg_asset",
                "include_in_manifest": False,
                "label": "SVG image file",
                "home_links": [{"href": "/media/bank-card-svgrepo-com.svg", "label": "SVG image file"}],
            },
            {
                "category": "zip_asset",
                "include_in_manifest": False,
                "label": "ZIP file",
                "home_links": [{"href": "/download/sample.zip", "label": "ZIP file"}],
            },
        ],
    },
    {
        "id": "discovery-policy",
        "title": "Discovery and Policy",
        "entries": [
            {
                "path": "/sitemap-only",
                "crawl_worthy": True,
                "category": "sitemap_only",
                "discovery_method": "sitemap",
                "html_linked": False,
                "label": "Sitemap-only page",
            },
            {
                "path": "/sitemap-exclusive-edge-case",
                "crawl_worthy": True,
                "category": "sitemap_only_unique",
                "discovery_method": "sitemap",
                "html_linked": False,
                "label": "Unique sitemap-only edge case page",
            },
            {
                "path": "/sitemap-discovery-fail",
                "crawl_worthy": True,
                "category": "sitemap_discovery_failure",
                "sitemap_url": "/sitemap-discovery-fail.xml",
                "expected_sitemap_status": 503,
                "fallback_links_should_sync": True,
                "label": "Failing sitemap discovery page",
                "home_links": [{"href": "/sitemap-discovery-fail", "label": "Failing sitemap discovery page"}],
            },
            {"path": "/sitemap.xml", "crawl_worthy": True, "category": "sitemap_xml", "label": "Sitemap XML"},
        ],
    },
    {
        "id": "char-limit-tests",
        "title": "Char Limit Tests",
        "entries": [
            {
                "path": "/oversized-title",
                "crawl_worthy": True,
                "category": "char_limit_oversized_title",
                "title_length_gt": 1024,
                "label": "Oversized title",
                "home_links": [{"href": "/oversized-title", "label": "Oversized title"}],
            },
            {
                "path": "/oversized-charset",
                "crawl_worthy": True,
                "category": "char_limit_oversized_charset",
                "charset_length_gt": 256,
                "label": "Oversized charset",
                "home_links": [{"href": "/oversized-charset", "label": "Oversized charset"}],
            },
            {
                "path": "/oversized-mime-type",
                "crawl_worthy": True,
                "category": "char_limit_oversized_mime_type",
                "mime_type_length_gt": 256,
                "may_download_in_browser": True,
                "label": "Oversized MIME type",
                "home_links": [{"href": "/oversized-mime-type", "label": "Oversized MIME type"}],
            },
        ],
    },
    {
        "id": "weather-daily-update-changefrequency",
        "title": "weather update changeFrequency",
        "entries": [
            {
                "path": "/weather/vancouver-daily-report",
                "crawl_worthy": True,
                "category": "weather_daily_update_changefreq",
                "sitemap_changefreq": "daily",
                "updates_daily_at": "00:00 America/Vancouver",
                "location": "Vancouver, BC, Canada",
                "label": "Vancouver daily weather report",
                "home_links": [{"href": "/weather/vancouver-daily-report", "label": "Vancouver daily weather report"}],
            },
            {
                "path": "/weather/vancouver-weekly-report",
                "crawl_worthy": True,
                "category": "weather_weekly_update_changefreq",
                "sitemap_changefreq": "weekly",
                "updates_weekly_at": "Monday 00:00 America/Vancouver",
                "location": "Vancouver, BC, Canada",
                "label": "Vancouver weekly weather report",
                "home_links": [{"href": "/weather/vancouver-weekly-report", "label": "Vancouver weekly weather report"}],
            },
        ],
    },
    {
        "id": "scale-graph",
        "title": "Scale and Graph Shape",
        "entries": [
            {
                "path": "/many-links",
                "crawl_worthy": True,
                "category": "large_link_set",
                "label": "Many links page",
                "home_links": [{"href": "/many-links", "label": "Many links page"}],
            },
            {
                "path": "/load-test",
                "crawl_worthy": True,
                "category": "large_static_payload",
                "target_payload_bytes": 7_500_000,
                "target_payload_label": "7.5 MB",
                "label": "Large static load-test page",
                "home_links": [{"href": "/load-test", "label": "Large static load-test page"}],
            },
            {
                "path": "/self-reference-direct",
                "crawl_worthy": True,
                "category": "self_reference_direct",
                "label": "Direct self-reference page",
                "home_links": [{"href": "/self-reference-direct", "label": "Direct self-reference page"}],
            },
            {
                "path": "/self-reference-cycle-a",
                "crawl_worthy": True,
                "category": "self_reference_cycle",
                "label": "Two-page self-reference cycle",
                "home_links": [{"href": "/self-reference-cycle-a", "label": "Two-page self-reference cycle"}],
            },
            {"path": "/self-reference-cycle-b", "crawl_worthy": True, "category": "self_reference_cycle", "label": "Self-reference cycle B"},
            {
                "path": "/sub-page-main-reference",
                "crawl_worthy": True,
                "category": "main_reference",
                "label": "Sub-page back to main page",
                "home_links": [{"href": "/sub-page-main-reference", "label": "Sub-page back to main page"}],
            },
            {
                "path": "/depth/0",
                "crawl_worthy": True,
                "category": "max_depth_test",
                "depth_level": 0,
                "next_path": "/depth/1",
                "total_depth_pages": TOTAL_DEPTH_PAGES,
                "label": "Max depth test page",
                "home_links": [{"href": "/depth/0", "label": "Max depth test page"}],
            },
        ],
    },
    {
        "id": "localized-state",
        "title": "Localization and State",
        "entries": [
            {
                "path": "/consent",
                "crawl_worthy": True,
                "category": "cookie_sensitive",
                "label": "Consent page",
                "home_links": [{"href": "/consent", "label": "Consent page"}],
            },
            {
                "path": "/accept-consent",
                "crawl_worthy": True,
                "category": "cookie_setup",
                "label": "Accept consent route",
                "home_links": [{"href": "/accept-consent", "label": "Accept consent route"}],
            },
            {
                "path": "/fr/about",
                "crawl_worthy": True,
                "category": "localized_path",
                "label": "French About page with /fr path",
                "home_links": [{"href": "/fr/about", "label": "French About page with /fr path"}],
            },
            {
                "path": "/about",
                "crawl_worthy": True,
                "category": "localized_same_url",
                "accept_language": "fr",
                "sets_cookie_on_click": True,
                "label": "Localized alt: French /about without /fr path",
                "home_links": [
                    {
                        "href": "/about",
                        "label": "Localized alt: French /about without /fr path",
                        "attrs": {
                            "hreflang": "fr",
                            "lang": "fr",
                            "onclick": "document.cookie='site_language=fr; Max-Age=60; Path=/; SameSite=Lax'",
                        },
                    }
                ],
            },
        ],
    },
    {
        "id": "product-pages",
        "title": "Product Pages",
        "entries": [
            {
                "path": "/product-pages/separate-pages",
                "crawl_worthy": True,
                "category": "product_variant_pages",
                "product_variant_strategy": "separate_pages",
                "label": "Product variants - Separate pages",
                "home_links": [{"href": "/product-pages/separate-pages", "label": "Product variants - Separate pages"}],
            },
            {
                "path": "/product-pages/query-params",
                "crawl_worthy": True,
                "category": "product_variant_pages",
                "product_variant_strategy": "query_params",
                "label": "Product variants - Query params",
                "home_links": [{"href": "/product-pages/query-params", "label": "Product variants - Query params"}],
            },
            {
                "path": "/product-pages/javascript-calculated",
                "crawl_worthy": True,
                "category": "product_variant_javascript_calculated",
                "product_variant_strategy": "javascript_calculated",
                "requires_javascript": True,
                "data_not_in_initial_dom": True,
                "javascript_calculated_variants": True,
                "label": "Product variants - JavaScript calculated",
                "home_links": [
                    {
                        "href": "/product-pages/javascript-calculated",
                        "label": "Product variants - JavaScript calculated",
                    }
                ],
            },
            {
                "path": "/product-pages/javascript-rendered-grid",
                "crawl_worthy": True,
                "category": "javascript_rendered_product_grid",
                "product_variant_strategy": "javascript_rendered_collection_grid",
                "requires_javascript": True,
                "data_not_in_initial_dom": True,
                "javascript_rendered_product_grid": True,
                "label": "Product collection - JavaScript rendered grid",
                "home_links": [
                    {
                        "href": "/product-pages/javascript-rendered-grid",
                        "label": "Product collection - JavaScript rendered grid",
                    }
                ],
            },
            {
                "path": "/product-pages/laptop-configurator",
                "crawl_worthy": True,
                "category": "laptop_configurator_dependent_options",
                "product_variant_strategy": "javascript_configurator",
                "requires_javascript": True,
                "data_not_in_initial_dom": True,
                "dependent_options": True,
                "label": "Laptop configurator - Dependent options",
                "home_links": [
                    {
                        "href": "/product-pages/laptop-configurator",
                        "label": "Laptop configurator - Dependent options",
                    }
                ],
            },
        ],
    },
    {
        "id": "structured-content",
        "title": "Structured Content",
        "entries": [
            {
                "path": "/structured-content",
                "crawl_worthy": True,
                "category": "structured_content_hub",
                "label": "Structured Content hub",
                "home_links": [{"href": "/structured-content", "label": "Structured Content hub"}],
            },
            {
                "path": "/structured-content/table",
                "crawl_worthy": True,
                "category": "structured_table_hub",
                "structured_group": "table",
                "label": "Structured table content hub",
            },
            {
                "path": "/structured-content/table/content",
                "crawl_worthy": True,
                "category": "table_content",
                "structured_group": "table",
                "label": "Table content page",
            },
            {
                "path": "/structured-content/table/links",
                "crawl_worthy": True,
                "category": "table_cell_link",
                "structured_group": "table",
                "label": "Table cell link page",
            },
            {
                "path": "/structured-content/list",
                "crawl_worthy": True,
                "category": "structured_list_hub",
                "structured_group": "list",
                "label": "Structured list content hub",
            },
            {
                "path": "/structured-content/list/basic",
                "crawl_worthy": True,
                "category": "list_content",
                "structured_group": "list",
                "label": "Basic list content page",
            },
            {
                "path": "/structured-content/list/nested",
                "crawl_worthy": True,
                "category": "nested_list_content",
                "structured_group": "list",
                "label": "Nested list content page",
            },
            {
                "path": "/structured-content/markdown",
                "crawl_worthy": True,
                "category": "structured_markdown_hub",
                "structured_group": "markdown",
                "label": "Structured markdown content hub",
            },
            {
                "path": "/structured-content/markdown/inline-links",
                "crawl_worthy": True,
                "category": "markdown_inline_links",
                "structured_group": "markdown",
                "label": "Markdown inline links page",
            },
            {
                "path": "/structured-content/markdown/reference-links",
                "crawl_worthy": True,
                "category": "markdown_reference_links",
                "structured_group": "markdown",
                "label": "Markdown reference links page",
            },
            {
                "path": "/structured-content/markdown/sample.md",
                "crawl_worthy": True,
                "category": "markdown_document",
                "structured_group": "markdown",
                "label": "Raw Markdown document",
            },
            {
                "path": "/structured-content/article",
                "crawl_worthy": True,
                "category": "structured_article_hub",
                "structured_group": "article",
                "label": "Structured article content hub",
            },
            {
                "path": "/structured-content/article/paywall-preview",
                "crawl_worthy": True,
                "category": "paywall_preview",
                "structured_group": "article",
                "label": "Paywall preview page",
            },
        ],
    },
]


def _scale_graph_entries() -> Iterator[Dict[str, Any]]:
    for index in range(40):
        yield {
            "path": f"/many/item/{index}",
            "crawl_worthy": True,
            "category": "large_link_child",
            "label": f"Many item {index}",
        }

    for depth_level_number in range(1, TOTAL_DEPTH_PAGES):
        yield {
            "path": f"/depth/{depth_level_number}",
            "crawl_worthy": True,
            "category": "max_depth_test",
            "depth_level": depth_level_number,
            "next_path": f"/depth/{depth_level_number + 1}" if depth_level_number < MAX_DEPTH_LEVEL else "/about",
            "total_depth_pages": TOTAL_DEPTH_PAGES,
            "label": f"Depth level {depth_level_number}",
        }


def _product_variant_entries() -> Iterator[Dict[str, Any]]:
    for variant in iter_product_variants():
        yield {
            "path": f"/product-pages/separate-pages/{variant['color_slug']}/{variant['size_slug']}",
            "crawl_worthy": True,
            "category": "product_variant_page",
            "product_variant_strategy": "separate_pages",
            "color": variant["color_name"],
            "size": variant["size_name"],
            "sku": variant["sku"],
            "label": f"Product variant page: {variant['color_name']} / {variant['size_name']}",
        }


def _product_variant_qp_entries() -> Iterator[Dict[str, Any]]:
    for variant in iter_product_variants():
        yield {
            "path": f"/product-pages/query-params/?color={variant['color_slug']}&size={variant['size_slug']}",
            "crawl_worthy": True,
            "category": "product_variant_page",
            "product_variant_strategy": "query_params",
            "color": variant["color_name"],
            "size": variant["size_name"],
            "sku": variant["sku"],
            "label": f"Product variant query param page: {variant['color_name']} / {variant['size_name']}",
        }


def _add_generated_entries() -> None:
    for section in TEST_SECTIONS:
        if section["id"] == "scale-graph":
            section["entries"].extend(_scale_graph_entries())
        if section["id"] == "product-pages":
            section["entries"].extend(_product_variant_entries())
            section["entries"].extend(_product_variant_qp_entries())


def _build_page_manifest() -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    for section in TEST_SECTIONS:
        for entry in section["entries"]:
            if not entry.get("path") or entry.get("include_in_manifest") is False:
                continue

            item = {key: value for key, value in entry.items() if key not in INTERNAL_ENTRY_KEYS}
            item["section_id"] = section["id"]
            item["section_title"] = section["title"]
            pages.append(item)
    return pages


_add_generated_entries()

SECTION_METADATA = [{"id": section["id"], "title": section["title"]} for section in TEST_SECTIONS]
PAGE_MANIFEST = _build_page_manifest()
