import asyncio
from agents import function_tool
from ddgs import DDGS


def _ddg_text(query: str, max_results: int) -> list[dict]:
    return DDGS().text(query, max_results=max_results)


@function_tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for the given query and return the top results with title, URL, and snippet."""
    results = await asyncio.to_thread(_ddg_text, query, max_results)

    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}\n   {r['href']}\n   {r['body']}")
    return "\n\n".join(lines)
