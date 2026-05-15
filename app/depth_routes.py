from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.depth_config import MAX_DEPTH_LEVEL, TOTAL_DEPTH_PAGES

depth_router = APIRouter()


def depth_html_page(level: int, next_path: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Depth Level {level}</title>
  </head>
  <body>
    <header>
      <h1>Depth Level {level}</h1>
    </header>
    <main>
      <p>Depth test level {level}. This chain has {TOTAL_DEPTH_PAGES} pages, from /depth/0 through /depth/{MAX_DEPTH_LEVEL}.</p>
      <p>After level {MAX_DEPTH_LEVEL}, the chain exits to the About page.</p>
      <a href="{next_path}">Next depth target</a>
    </main>
  </body>
</html>"""
    )


def register_depth_route(level: int) -> None:
    async def depth_level() -> HTMLResponse:
        next_path = f"/depth/{level + 1}" if level < MAX_DEPTH_LEVEL else "/about"
        return depth_html_page(level, next_path)

    depth_level.__name__ = f"depth_level_{level}"
    depth_router.add_api_route(
        f"/depth/{level}",
        depth_level,
        methods=["GET"],
        response_class=HTMLResponse,
        name=f"depth_level_{level}",
    )


for depth_level_number in range(1, TOTAL_DEPTH_PAGES):
    register_depth_route(depth_level_number)
