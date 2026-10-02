"""HTTP client for the e-Gov Law API v2 (https://laws.e-gov.go.jp/api/2).

Standard library only, so the plugin installs with no dependencies. No
credentials: the API is public and unauthenticated. Every request goes to
the e-Gov host only, carries a timeout, and is read with a size cap, so a
slow or broken upstream turns into an error message instead of a hung agent.
"""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from typing import Callable, Optional, Tuple

from .version import __version__

API_BASE = "https://laws.e-gov.go.jp/api/2"
SITE_BASE = "https://laws.e-gov.go.jp"
USER_AGENT = f"hermes-plugin-egov-law/{__version__} (+https://github.com/TakeshiTGAL/hermes-plugin-egov-law)"
TIMEOUT_SECONDS = 15.0
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MIN_INTERVAL_SECONDS = 1.0  # at most one request per second to e-Gov from this process (a shared public service)

_pace_lock = threading.Lock()
_last_request = [0.0]


def _pace(interval: float) -> None:
    """Sleep so that requests from this process are at least `interval` seconds apart."""
    if interval <= 0:
        return
    with _pace_lock:
        wait = _last_request[0] + interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_request[0] = time.monotonic()

# A transport takes (url, timeout) and returns (http_status, body_bytes).
Transport = Callable[[str, float], Tuple[int, bytes]]


class EgovError(Exception):
    """A request that failed. `kind` is machine-readable, `hint` says what to do next, `details`
    are extra fields for the tool's error reply."""

    def __init__(self, kind: str, message: str, hint: str = "", status: Optional[int] = None,
                 api_code: str = "", details: Optional[dict] = None):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.hint = hint
        self.status = status
        self.api_code = api_code
        self.details = details or {}


ALLOWED_HOST = "laws.e-gov.go.jp"


class _EgovOnlyRedirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to https://laws.e-gov.go.jp; refuse any other host or plain HTTP."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(urllib.parse.urljoin(req.full_url, newurl))
        if target.scheme != "https" or target.hostname != ALLOWED_HOST:
            raise urllib.error.URLError(
                f"refused a redirect to {target.scheme}://{target.hostname} "
                f"(this plugin only contacts https://{ALLOWED_HOST})")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# build_opener keeps urllib's defaults, including the proxy settings from the environment (HTTPS_PROXY).
_OPENER = urllib.request.build_opener(_EgovOnlyRedirects)


def urllib_transport(url: str, timeout: float) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            return response.status, response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        try:
            body = error.read(64 * 1024)
        except Exception:
            body = b""
        return error.code, body


class EgovClient:
    """GET JSON from the e-Gov Law API. `base_url` and `transport` exist so tests can inject them."""

    def __init__(self, base_url: str = API_BASE, timeout: float = TIMEOUT_SECONDS,
                 transport: Optional[Transport] = None, min_interval: Optional[float] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport or urllib_transport
        # Real network calls are paced; injected test transports are not unless asked.
        self.min_interval = (MIN_INTERVAL_SECONDS if transport is None else 0.0) if min_interval is None else min_interval
        self.resolve_cache: "OrderedDict[str, dict]" = OrderedDict()  # law name -> law ID, memory only

    def url_for(self, path: str, params: Optional[dict] = None) -> str:
        quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.strip("/").split("/"))
        url = f"{self.base_url}/{quoted}"
        clean = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
        return url

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        url = self.url_for(path, params)
        _pace(self.min_interval)
        try:
            status, body = self.transport(url, self.timeout)
        except (socket.timeout, TimeoutError) as error:
            raise EgovError(
                "timeout",
                f"e-Gov Law API did not answer within {self.timeout:g} seconds ({_host(url)}).",
                "The service may be slow or under maintenance. Wait a minute and call the tool again; "
                "do not loop more than twice.",
            ) from error
        except urllib.error.URLError as error:
            reason = error.reason
            if isinstance(reason, (socket.timeout, TimeoutError)):
                raise EgovError(
                    "timeout",
                    f"e-Gov Law API did not answer within {self.timeout:g} seconds ({_host(url)}).",
                    "The service may be slow or under maintenance. Wait a minute and call the tool again; "
                    "do not loop more than twice.",
                ) from error
            raise EgovError(
                "network",
                f"Could not reach the e-Gov Law API at {_host(url)}: {reason}.",
                "Check that this machine can open https://laws.e-gov.go.jp/ (network, proxy, DNS), "
                "then call the tool again.",
            ) from error
        except OSError as error:
            raise EgovError(
                "network",
                f"Could not reach the e-Gov Law API at {_host(url)}: {error}.",
                "Check that this machine can open https://laws.e-gov.go.jp/ (network, proxy, DNS), "
                "then call the tool again.",
            ) from error

        if len(body) > MAX_RESPONSE_BYTES:
            raise EgovError(
                "too_large",
                "The e-Gov response was larger than this plugin accepts (8 MB).",
                "Ask for one article (egov_law_article with `article`) instead of a whole law.",
            )
        data = _parse_json(body)
        if status >= 400 or (isinstance(data, dict) and "code" in data and "message" in data
                             and len(data) <= 3):
            api_code = str((data or {}).get("code", "")) if isinstance(data, dict) else ""
            api_message = str((data or {}).get("message", "")) if isinstance(data, dict) else ""
            kind = "not_found" if status == 404 else ("bad_request" if status == 400 else "upstream")
            hints = {
                "not_found": "Check the law name, number or ID with egov_law_search, then call again.",
                "bad_request": "e-Gov rejected an argument (its message is above). Fix that argument and call again.",
                "upstream": "This is a problem on the e-Gov side. Wait a few minutes and call the tool again.",
            }
            raise EgovError(
                kind,
                f"e-Gov Law API returned HTTP {status}"
                + (f" ({api_code}: {api_message})" if api_message else "") + ".",
                hints[kind],
                status=status,
                api_code=api_code,
            )
        if not isinstance(data, dict):
            raise EgovError(
                "bad_response",
                "e-Gov Law API returned something that is not a JSON object.",
                "The API may have changed or be under maintenance. Try again later.",
                status=status,
            )
        return data


def _parse_json(body: bytes):
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _host(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc or url


def law_page_url(law_id: str) -> str:
    """The human-readable e-Gov page for a law (always the current version)."""
    return f"{SITE_BASE}/law/{urllib.parse.quote(law_id, safe='')}"
