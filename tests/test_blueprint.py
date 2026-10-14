"""The weekly amendment blueprint is optional. Older Hermes builds do not have it."""

from __future__ import annotations

import string

import yaml

from conftest import PLUGIN_DIR


def test_register_without_the_blueprint_api_still_registers_three_tools(plugin):
    names = []

    class Ctx:
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            names.append(name)

        def register_skill(self, name, path, description="", frontmatter=None):
            return None

    assert plugin.blueprint.register_blueprint(Ctx()) is False
    plugin.register(Ctx())
    assert names == ["egov_law_search", "egov_law_article", "egov_law_revisions"]


def test_register_sends_the_weekly_watch_when_the_api_exists(plugin):
    seen = {}

    class Ctx:
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            pass

        def register_skill(self, name, path, description="", frontmatter=None):
            return None

        def register_automation_blueprint(self, key, **kwargs):
            seen["key"] = key
            seen.update(kwargs)
            return object()

    assert plugin.register(Ctx()) is None
    assert plugin.blueprint.register_blueprint(Ctx()) is True
    assert seen["key"] == "weekly-amendments"
    assert seen["deliver_default"] == "origin"
    assert seen["schedule_template"] == "{minute} {hour} * * {dow}"
    names = [slot["name"] for slot in seen["slots"]]
    assert names == ["law", "day", "time"]
    assert "deliver" not in names
    day = next(slot for slot in seen["slots"] if slot["name"] == "day")
    assert day["strict"] is True
    assert day["default"] == "monday"
    assert day["options"] == (
        "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"
    )
    assert seen["slots"][0]["default"] == "労働基準法"
    assert seen["slots"][2]["default"] == "09:00"
    assert "Not converted to Japan time" in day["help"]
    assert "not Japan time" not in day["help"]
    assert "Not converted to Japan time" in seen["slots"][2]["help"]


def test_a_failing_skill_does_not_drop_the_tools(plugin):
    names = []
    seen = {}

    class Ctx:
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            names.append(name)

        def register_skill(self, name, path, description="", frontmatter=None):
            raise RuntimeError("skill registrar broken")

        def register_automation_blueprint(self, key, **kwargs):
            seen["key"] = key

    plugin.register(Ctx())
    assert names == ["egov_law_search", "egov_law_article", "egov_law_revisions"]
    assert seen["key"] == "weekly-amendments"


def test_a_failing_blueprint_api_does_not_drop_the_tools(plugin):
    names = []

    class Ctx:
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            names.append(name)

        def register_skill(self, name, path, description="", frontmatter=None):
            return None

        def register_automation_blueprint(self, key, **kwargs):
            raise RuntimeError("registrar broken")

    plugin.register(Ctx())
    assert names == ["egov_law_search", "egov_law_article", "egov_law_revisions"]
    assert plugin.blueprint.register_blueprint(Ctx()) is False


def test_a_rejected_blueprint_is_not_treated_as_registered(plugin):
    class Ctx:
        def register_automation_blueprint(self, key, **kwargs):
            return None

    assert plugin.blueprint.register_blueprint(Ctx()) is False


def test_prompt_states_the_watch_rules(plugin):
    prompt = plugin.blueprint.PROMPT_TEMPLATE
    fields = [name for _, name, _, _ in string.Formatter().parse(prompt) if name]
    assert fields == ["law"]
    assert "Never answer [SILENT]" in prompt
    assert "bad_request or not_found" in prompt
    assert "bad_argument, law_not_found, or ambiguous_law" in prompt
    assert "repealed_on" in prompt and "scheduled_repeal" in prompt
    assert "date_fixed is false" in prompt
    assert "施行令" in prompt and "施行規則" in prompt
    assert "source.attribution" in prompt
    assert "8 MB" in prompt
    assert plugin.blueprint.DESCRIPTION.startswith("Once a week")
    manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8"))
    assert "Disclosure —" in manifest["description"]
    assert "weekly-amendments" in manifest["description"]
    assert "does not create a cron job" in manifest["description"]
    assert "one model turn runs once a week" in manifest["description"]
    assert "at least two model requests" in manifest["description"]
    assert "The agent can schedule it" in manifest["description"]
    assert "scheduling it twice creates two jobs" in manifest["description"]
    assert len(manifest["description"]) <= 1500
