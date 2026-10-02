"""Load the repo root as a package, the way Hermes loads an installed plugin directory,
and provide clients that replay recorded e-Gov responses or talk to the live API."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PACKAGE = "egov_law_plugin"


def load_plugin():
    if PACKAGE in sys.modules:
        return sys.modules[PACKAGE]
    spec = importlib.util.spec_from_file_location(
        PACKAGE, PLUGIN_DIR / "__init__.py", submodule_search_locations=[str(PLUGIN_DIR)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = module
    spec.loader.exec_module(module)
    return module


def fixture_name(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".json"


class ReplayTransport:
    """Answers from tests/fixtures; an unrecorded URL fails the test loudly."""

    def __init__(self):
        self.urls = []

    def __call__(self, url: str, timeout: float):
        self.urls.append(url)
        path = FIXTURES / fixture_name(url)
        if not path.is_file():
            raise AssertionError(f"no recorded response for {url} (run tests/record_fixtures.py)")
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["url"] == url
        return record["status"], json.dumps(record["body"], ensure_ascii=False).encode("utf-8")


@pytest.fixture(scope="session")
def plugin():
    return load_plugin()


@pytest.fixture
def replay(plugin):
    """Handlers whose HTTP is served from recorded responses."""
    transport = ReplayTransport()
    client = plugin.client.EgovClient(transport=transport)
    handlers = plugin.tools.make_handlers(client)
    handlers["_transport"] = transport
    return handlers


LIVE_REQUESTS = []


@pytest.fixture(scope="session")
def live(plugin):
    """Handlers that call the real e-Gov API: one shared client (its name cache keeps the request count
    down) paced at one request per second. The run prints how many requests the live tests made."""
    def counted(url, timeout):
        LIVE_REQUESTS.append(url)
        return plugin.client.urllib_transport(url, timeout)

    return plugin.tools.make_handlers(plugin.client.EgovClient(transport=counted, min_interval=1.0))


def pytest_terminal_summary(terminalreporter):
    if LIVE_REQUESTS:
        terminalreporter.write_line(f"live e-Gov requests from the `live` fixture: {len(LIVE_REQUESTS)}")


def call(handlers, name, **args):
    return json.loads(handlers[name](args))
