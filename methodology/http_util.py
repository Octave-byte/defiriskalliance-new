"""Tiny JSON HTTP GET (stdlib only)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any

# Several provider APIs sit behind Cloudflare and reject the default
# ``Python-urllib/x.y`` User-Agent with an Error 1010 ("Access denied")
# 403 page (e.g. api.pharos.watch). Sending a real browser UA avoids the
# bot challenge for all callers; individual providers can still override
# this by passing their own ``User-Agent`` header.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 "
    "DRA/3.0 (+https://github.com/jumperapps/agg_scoring_dra)"
)


class HttpError(Exception):
    pass


def get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 60.0) -> Any:
    merged: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        merged.update(headers)
    req = urllib.request.Request(url, headers=merged, method="GET")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        raise HttpError(f"HTTP {e.code} for {url}") from e
    except Exception as e:
        raise HttpError(str(e)) from e
