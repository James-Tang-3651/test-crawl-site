from typing import Any, Dict, Iterator, Tuple


PRODUCT_DEFAULT_COLOR = "steel-blue"
PRODUCT_DEFAULT_SIZE = "24oz"

PRODUCT_BRAND = "Northstar Bottle Co."
PRODUCT_NAME = "TrailForge Insulated Water Bottle"
PRODUCT_RATING = "4.8"
PRODUCT_REVIEW_COUNT = "1,284"

PRODUCT_COLORS: Dict[str, Dict[str, Any]] = {
    "steel-blue": {
        "name": "Steel Blue",
        "code": "STB",
        "swatch": "#4d7898",
        "finish": "satin blue powder coat",
        "visual_label": "Steel blue bottle with glacier cap",
        "finish_feature": "Cool blue finish resists scuffs from backpack pockets.",
        "price_delta": 1,
    },
    "sage-green": {
        "name": "Sage Green",
        "code": "SGG",
        "swatch": "#78926f",
        "finish": "soft green powder coat",
        "visual_label": "Sage green bottle with trail cap",
        "finish_feature": "Soft green finish hides trail dust and daily carry marks.",
        "price_delta": 2,
    },
    "matte-black": {
        "name": "Matte Black",
        "code": "MBK",
        "swatch": "#222222",
        "finish": "matte black powder coat",
        "visual_label": "Matte black bottle with charcoal cap",
        "finish_feature": "Matte black finish keeps a low-profile desk and gym look.",
        "price_delta": 0,
    },
}

PRODUCT_SIZES: Dict[str, Dict[str, Any]] = {
    "18oz": {
        "name": "18 oz",
        "code": "18",
        "capacity": "18 ounces / 532 ml",
        "dimensions": "8.2 in x 2.8 in",
        "weight": "10.4 oz",
        "base_price": 28,
        "fit_note": "Compact size fits small cup holders and short day packs.",
    },
    "24oz": {
        "name": "24 oz",
        "code": "24",
        "capacity": "24 ounces / 710 ml",
        "dimensions": "10.1 in x 3.0 in",
        "weight": "12.7 oz",
        "base_price": 34,
        "fit_note": "Everyday size balances commute, desk, and gym use.",
    },
    "32oz": {
        "name": "32 oz",
        "code": "32",
        "capacity": "32 ounces / 946 ml",
        "dimensions": "11.8 in x 3.4 in",
        "weight": "15.6 oz",
        "base_price": 40,
        "fit_note": "Large size supports long hikes and refill-light workdays.",
    },
}

PRODUCT_STOCK: Dict[Tuple[str, str], int] = {
    ("steel-blue", "18oz"): 42,
    ("steel-blue", "24oz"): 17,
    ("steel-blue", "32oz"): 8,
    ("sage-green", "18oz"): 0,
    ("sage-green", "24oz"): 22,
    ("sage-green", "32oz"): 5,
    ("matte-black", "18oz"): 64,
    ("matte-black", "24oz"): 31,
    ("matte-black", "32oz"): 12,
}


def product_variant_key(color_slug: str, size_slug: str) -> str:
    return f"{color_slug}|{size_slug}"


def product_stock_status(quantity: int) -> str:
    if quantity == 0:
        return "Backorder"
    if quantity <= 8:
        return "Low stock"
    return "In stock"


def product_shipping_message(color_slug: str, size_slug: str, quantity: int) -> str:
    color = PRODUCT_COLORS[color_slug]
    size = PRODUCT_SIZES[size_slug]
    if quantity == 0:
        return f"{color['name']} {size['name']} backorders ship in 10 business days."
    if quantity <= 8:
        return f"{color['name']} {size['name']} ships in 2 business days while stock lasts."
    return f"{color['name']} {size['name']} ships next business day from the main warehouse."


def product_variant(color_slug: str, size_slug: str) -> Dict[str, Any]:
    color = PRODUCT_COLORS[color_slug]
    size = PRODUCT_SIZES[size_slug]
    quantity = PRODUCT_STOCK[(color_slug, size_slug)]
    price = size["base_price"] + color["price_delta"]

    return {
        "key": product_variant_key(color_slug, size_slug),
        "color_slug": color_slug,
        "size_slug": size_slug,
        "color_name": color["name"],
        "size_name": size["name"],
        "sku": f"TF-{color['code']}-{size['code']}",
        "price": f"${price}.00",
        "stock_quantity": quantity,
        "stock_status": product_stock_status(quantity),
        "capacity": size["capacity"],
        "dimensions": size["dimensions"],
        "weight": size["weight"],
        "shipping_message": product_shipping_message(color_slug, size_slug, quantity),
        "visual_label": color["visual_label"],
        "swatch": color["swatch"],
        "finish": color["finish"],
        "feature_bullets": [
            "Double-wall vacuum insulation keeps drinks cold through long crawl runs.",
            "Leakproof carry cap locks tight inside a laptop bag.",
            color["finish_feature"],
            size["fit_note"],
        ],
    }


def iter_product_variants() -> Iterator[Dict[str, Any]]:
    for color_slug in PRODUCT_COLORS:
        for size_slug in PRODUCT_SIZES:
            yield product_variant(color_slug, size_slug)


def product_data_payload() -> Dict[str, Any]:
    return {
        "product": {
            "brand": PRODUCT_BRAND,
            "name": PRODUCT_NAME,
            "rating": PRODUCT_RATING,
            "review_count": PRODUCT_REVIEW_COUNT,
            "default_color": PRODUCT_DEFAULT_COLOR,
            "default_size": PRODUCT_DEFAULT_SIZE,
        },
        "colors": PRODUCT_COLORS,
        "sizes": PRODUCT_SIZES,
        "variants": {
            variant["key"]: variant
            for variant in iter_product_variants()
        },
    }


LAPTOP_CONFIGURATOR_DEFAULTS = {
    "cpu": "core-8",
    "memory": "16gb",
    "storage": "256gb",
    "keyboard": "us",
    "gpu": "integrated",
}

LAPTOP_CONFIGURATOR_PAYLOAD: Dict[str, Any] = {
    "product": {
        "brand": "Forge Systems",
        "name": "ForgeBook 16 Modular Laptop",
        "rating": "4.7",
        "review_count": "842",
        "base_price": 1399,
        "base_sku": "FB16",
        "visual_label": "Modular 16 inch laptop with configurable expansion bay",
        "description": "A fictional modular laptop configurator built to test dependent product options, disabled choices, and client-rendered configuration summaries.",
        "availability": {
            "standard": "Ships in 5 business days after module assembly.",
            "creator": "Creator GPU builds ship in 7 business days after thermal validation.",
            "high_memory": "High-memory builds ship in 6 business days after memory validation.",
        },
        "upgrade_notes": [
            "Memory and storage modules can be replaced after purchase.",
            "Expansion bay graphics modules require the larger cooling profile.",
            "Keyboard modules can be swapped without replacing the top cover.",
        ],
        "included_modules": [
            "USB-C expansion card",
            "HDMI expansion card",
            "Modular input deck",
            "180W compact power adapter",
        ],
        "accessories": [
            {"label": "Expansion card pack", "href": "/query-page?accessory=expansion-card-pack"},
            {"label": "Laptop sleeve", "href": "/query-page?accessory=laptop-sleeve"},
            {"label": "Spare input deck", "href": "/query-page?accessory=input-deck"},
        ],
    },
    "defaults": LAPTOP_CONFIGURATOR_DEFAULTS,
    "options": {
        "cpu": [
            {
                "id": "core-8",
                "label": "Core 8",
                "sku_code": "C8",
                "price_delta": 0,
                "spec": "8-core performance mainboard",
                "summary": "Balanced thermals for everyday development and office workloads.",
            },
            {
                "id": "core-12",
                "label": "Core 12",
                "sku_code": "C12",
                "price_delta": 260,
                "spec": "12-core performance mainboard",
                "summary": "Higher sustained compile and rendering throughput.",
            },
        ],
        "memory": [
            {
                "id": "16gb",
                "label": "16GB",
                "sku_code": "M16",
                "price_delta": 0,
                "spec": "16GB DDR5-5600 dual-channel memory",
                "summary": "Everyday multitasking memory kit.",
            },
            {
                "id": "32gb",
                "label": "32GB",
                "sku_code": "M32",
                "price_delta": 180,
                "spec": "32GB DDR5-5600 dual-channel memory",
                "summary": "Recommended memory kit for virtual machines and large browser sessions.",
            },
            {
                "id": "64gb",
                "label": "64GB",
                "sku_code": "M64",
                "price_delta": 420,
                "spec": "64GB DDR5-5600 dual-channel memory",
                "summary": "Maximum memory kit for heavy local data and build workloads.",
            },
        ],
        "storage": [
            {
                "id": "256gb",
                "label": "256GB",
                "sku_code": "S256",
                "price_delta": 0,
                "spec": "256GB NVMe storage module",
                "summary": "Entry storage module for light local files.",
            },
            {
                "id": "512gb",
                "label": "512GB",
                "sku_code": "S512",
                "price_delta": 95,
                "spec": "512GB NVMe storage module",
                "summary": "Balanced storage module for development tools and media.",
            },
            {
                "id": "1tb",
                "label": "1TB",
                "sku_code": "S1T",
                "price_delta": 180,
                "spec": "1TB NVMe storage module",
                "summary": "Large storage module for projects, games, and local datasets.",
            },
            {
                "id": "2tb",
                "label": "2TB",
                "sku_code": "S2T",
                "price_delta": 340,
                "spec": "2TB NVMe storage module",
                "summary": "Maximum storage module for media-heavy workflows.",
            },
        ],
        "keyboard": [
            {
                "id": "us",
                "label": "US",
                "sku_code": "KUS",
                "price_delta": 0,
                "spec": "US English keyboard module",
                "summary": "ANSI layout keyboard module.",
            },
            {
                "id": "iso",
                "label": "ISO",
                "sku_code": "KISO",
                "price_delta": 20,
                "spec": "ISO keyboard module",
                "summary": "ISO layout keyboard module.",
            },
        ],
        "gpu": [
            {
                "id": "integrated",
                "label": "Integrated",
                "sku_code": "GI",
                "price_delta": 0,
                "spec": "Integrated graphics expansion bay shell",
                "summary": "Lighter build with the standard expansion bay shell.",
            },
            {
                "id": "creator-gpu",
                "label": "Creator GPU",
                "sku_code": "GC",
                "price_delta": 520,
                "spec": "Creator GPU expansion bay module",
                "summary": "Discrete graphics module for accelerated rendering and external displays.",
            },
        ],
    },
    "compatibility_rules": [
        {
            "id": "memory-32gb-storage-floor",
            "when": {"memory": "32gb"},
            "disable": {"storage": ["256gb"]},
            "fallback": {"storage": "512gb"},
            "message": "32GB memory configurations require 512GB or larger storage; 256GB storage is unavailable for this memory kit.",
        }
    ],
}


def laptop_configurator_data_payload() -> Dict[str, Any]:
    return LAPTOP_CONFIGURATOR_PAYLOAD
