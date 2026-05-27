import json
import logging
import os
from typing import Any, Optional
from urllib.parse import quote_plus

import httpx
from agents import function_tool


BRIGHT_DATA_REQUEST_URL = "https://api.brightdata.com/request"
logger = logging.getLogger(__name__)


class BrightDataConfigError(RuntimeError):
    pass


class BrightDataApiError(RuntimeError):
    pass


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise BrightDataConfigError(f"Missing required environment variable: {name}")
    return value


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_required_env('BRIGHT_DATA_API_TOKEN')}",
        "Content-Type": "application/json",
    }


def _trim_text(value: Any, max_chars: int) -> str:
    text = value if isinstance(value, str) else str(value)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[truncated]"


def _raise_for_brightdata_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    try:
        detail = response.json()
    except ValueError:
        detail = response.text
    raise BrightDataApiError(
        f"Bright Data API returned {response.status_code}: {detail}"
    )


def _unwrap_body_json(data: Any) -> Any:
    if isinstance(data, dict) and isinstance(data.get("body"), str):
        try:
            return json.loads(data["body"])
        except json.JSONDecodeError:
            return data
    return data


@function_tool
async def brightdata_serp_search(
    query: str,
    country: Optional[str] = None,
    max_results: int = 5,
) -> dict[str, Any]:
    """Search Google through Bright Data SERP API and return top organic results."""
    logger.info(
        "Agent tool call: brightdata_serp_search query=%r country=%s max_results=%s",
        query,
        country or os.getenv("BRIGHT_DATA_COUNTRY", "us"),
        max_results,
    )
    return await serp_search_api(query, country=country, max_results=max_results)


async def serp_search_api(
    query: str,
    country: Optional[str] = None,
    max_results: int = 5,
) -> dict[str, Any]:
    token_country = country or os.getenv("BRIGHT_DATA_COUNTRY", "us")
    zone = _required_env("BRIGHT_DATA_SERP_ZONE")
    search_url = (
        f"https://www.google.com/search?q={quote_plus(query)}"
        f"&hl=en&gl={quote_plus(token_country)}"
    )
    payload = {
        "zone": zone,
        "url": search_url,
        "format": "json",
        "method": "GET",
        "country": token_country,
        "data_format": "parsed_light",
    }

    logger.info("Bright Data SERP request: country=%s query=%r", token_country, query)
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            BRIGHT_DATA_REQUEST_URL, headers=_headers(), json=payload
        )
        logger.info(
            "Bright Data SERP response: status=%s bytes=%s",
            response.status_code,
            len(response.content),
        )
        _raise_for_brightdata_error(response)
        data = _unwrap_body_json(response.json())

    organic = data.get("organic", [])
    results = []
    for item in organic[: max(1, min(max_results, 10))]:
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("link"),
                "source": item.get("source") or item.get("display_link"),
                "description": item.get("description") or item.get("snippet"),
                "rank": item.get("rank"),
            }
        )

    logger.info(
        "Surfaced SERP results: returned=%s available=%s",
        len(results),
        len(organic),
    )
    return {
        "query": query,
        "country": token_country,
        "results": results,
        "result_count": len(results),
    }


@function_tool
async def brightdata_unlock_url(
    url: str,
    country: Optional[str] = None,
    max_chars: int = 12000,
) -> dict[str, Any]:
    """Fetch a public webpage through Bright Data Unlocker API as clean markdown."""
    logger.info(
        "Agent tool call: brightdata_unlock_url url=%s country=%s max_chars=%s",
        url,
        country or os.getenv("BRIGHT_DATA_COUNTRY", "us"),
        max_chars,
    )
    return await unlock_url_api(url, country=country, max_chars=max_chars)


async def unlock_url_api(
    url: str,
    country: Optional[str] = None,
    max_chars: int = 12000,
) -> dict[str, Any]:
    token_country = country or os.getenv("BRIGHT_DATA_COUNTRY", "us")
    zone = _required_env("BRIGHT_DATA_UNLOCKER_ZONE")
    payload = {
        "zone": zone,
        "url": url,
        "format": "json",
        "method": "GET",
        "country": token_country,
        "data_format": "markdown",
    }

    logger.info("Bright Data Unlocker request: country=%s url=%s", token_country, url)
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            BRIGHT_DATA_REQUEST_URL, headers=_headers(), json=payload
        )
        logger.info(
            "Bright Data Unlocker response: status=%s bytes=%s url=%s",
            response.status_code,
            len(response.content),
            url,
        )
        _raise_for_brightdata_error(response)
        data = response.json()

    body = data.get("body", data)
    content = _trim_text(body, max(1000, min(max_chars, 50000)))
    logger.info(
        "Surfaced page content: url=%s status_code=%s chars=%s",
        url,
        data.get("status_code"),
        len(content),
    )
    return {
        "url": url,
        "country": token_country,
        "status_code": data.get("status_code"),
        "content": content,
    }
