"""Tool handlers: the Hermes handler contract around laws.py.

Every handler takes the model's arguments, always returns a JSON string, and
never raises: e-Gov errors, bad arguments, timeouts and bugs all come back as
{"error": ..., "error_type": ..., "next_step": ...} so cron and gateway runs keep going.
"""

from __future__ import annotations

import json
import logging
from typing import Callable, Dict, Optional

from . import laws
from .client import EgovClient, EgovError

logger = logging.getLogger(__name__)


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _error(kind: str, message: str, hint: str = "", details: Optional[dict] = None) -> str:
    payload = {"error": message, "error_type": kind}
    for key, value in (details or {}).items():
        if key not in payload and value not in (None, ""):
            payload[key] = value
    if hint:
        payload["next_step"] = hint
    return _dump(payload)


def _as_handler(fetch: Callable[[dict], dict]) -> Callable:
    def handler(args: Optional[dict] = None, **kwargs) -> str:
        try:
            return _dump(fetch(dict(args or {})))
        except EgovError as error:
            return _error(error.kind, error.message, error.hint, error.details)
        except Exception as error:  # never let a tool call crash the agent loop
            logger.exception("jp-egov-law tool failed")
            return _error("internal", f"Unexpected error in the e-Gov law plugin: {type(error).__name__}: {error}",
                          "Retry once. If it repeats, tell the user the e-Gov lookup failed and give the "
                          "law's e-Gov page instead.")
    return handler


def make_handlers(client: Optional[EgovClient] = None) -> Dict[str, Callable]:
    """Handlers bound to one client. Tests pass a client with an injected base URL or transport."""
    client = client or EgovClient()

    def search(args: dict) -> dict:
        return laws.search_laws(client, args.get("query"), mode=args.get("mode") or "title",
                                limit=args.get("limit", 10),
                                include_repealed=bool(args.get("include_repealed", False)))

    def article(args: dict) -> dict:
        return laws.get_article(client, args.get("law"), args.get("article"),
                                paragraph=args.get("paragraph"), as_of=args.get("as_of"),
                                max_chars=args.get("max_chars", laws.DEFAULT_MAX_CHARS),
                                compare_with=args.get("compare_with"))

    def revisions(args: dict) -> dict:
        return laws.get_revisions(client, args.get("law"), limit=args.get("limit", 10))

    return {
        "egov_law_search": _as_handler(search),
        "egov_law_article": _as_handler(article),
        "egov_law_revisions": _as_handler(revisions),
    }


HANDLERS = make_handlers()
