"""Weekly e-Gov amendment watch, registered only when Hermes has the blueprint API.

Hermes v0.21.4 and v0.21.5 have no ``ctx.register_automation_blueprint``. Those
builds keep the three tools and skip this catalog entry. The method is also
what the plugin host announces, so ``hasattr`` matches in-process and host
isolation (``RemotePluginContext``).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

KEY = "weekly-amendments"
TITLE = "Weekly law amendment watch"
DESCRIPTION = (
    "Once a week, check one Japanese law on e-Gov for a promulgated amendment "
    "or repeal that is not in force yet. Bills still in the Diet, and a "
    "separate 施行令 or 施行規則, are not included. A law that is already "
    "repealed is reported as repealed, not as a future change."
)
SCHEDULE_TEMPLATE = "{minute} {hour} * * {dow}"
PROMPT_TEMPLATE = """\
Check one Japanese law for a promulgated change that is not in force yet. \
Call egov_law_revisions exactly once with law="{law}" and limit=50. Use only that JSON. \
Do not invent dates, article text, or a status the JSON does not state.

Send one short message. Never answer [SILENT]. Start by saying whether e-Gov answered. \
A missing message is not a result.

If the JSON has error_type:
- timeout, network, upstream, or bad_response: e-Gov could not be read. Name error_type. \
Do not say that no amendment is scheduled.
- too_large: the response was over this plugin's 8 MB cap. Not an outage and not "no amendment".
- bad_argument, law_not_found, or ambiguous_law: the law name is unusable. Quote next_step. \
This is not an e-Gov outage.
- bad_request or not_found: e-Gov rejected the lookup. Quote error and next_step. \
Not an outage, and not "no amendment".
- internal: this plugin failed. Do not call that an e-Gov outage.
If the tool is missing: say jp-egov-law is not loaded. Do not guess.

If there is no error_type:
- Include source.attribution unchanged.
- If repealed_on is present: the repeal has already taken effect. Say that date. \
This is not a future repeal.
- If scheduled_repeal is present: a repeal is scheduled and not yet in force. Say its date. \
Do not call it an ordinary amendment.
- If next_amendment is present: report that row's in_force_since, amended_by, change, and date_fixed. \
If date_fixed is false, quote the tool's note and that row's enforcement_note, and do not call \
in_force_since a fixed day.
- Otherwise, if message says no promulgated amendment is waiting: say that. Also say that bills \
still in the Diet, and a separate 施行令 or 施行規則, are outside this check.
- Do not say which articles change. A row's check dates are only a later egov_law_article lookup.
- next_amendment is the soonest upcoming row, even when next_step says a list was cut. \
If it says that, say the list is incomplete.
"""
SLOTS = (
    {
        "name": "law",
        "type": "text",
        "label": "Which law?",
        "default": "労働基準法",
        "help": "Official title, e-Gov abbreviation, or law number. Example: 労働基準法. "
        "The name is stored in the cron prompt as typed.",
    },
    {
        "name": "day",
        "type": "enum",
        "label": "Which day?",
        "default": "monday",
        "options": ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"),
        "strict": True,
        "help": "A weekday name. Hermes's timezone, or the computer's clock if none is set. "
        "Not converted to Japan time.",
    },
    {
        "name": "time",
        "type": "time",
        "label": "What time?",
        "default": "09:00",
        "help": "24-hour time in Hermes's timezone, or the computer's clock if none is set. "
        "Not converted to Japan time. Example: 09:00.",
    },
)
DELIVER_DEFAULT = "origin"


def register_blueprint(ctx) -> bool:
    """Register the watch when this Hermes build has the API. Never raises.

    Returns True only when Hermes accepted the blueprint. A missing method, a
    rejected blueprint (``None``), or an unexpected error leaves the three tools
    in place and skips the catalog entry.
    """
    register = getattr(ctx, "register_automation_blueprint", None)
    if not callable(register):
        return False
    try:
        accepted = register(
            KEY,
            title=TITLE,
            description=DESCRIPTION,
            category="weekly",
            schedule_template=SCHEDULE_TEMPLATE,
            prompt_template=PROMPT_TEMPLATE,
            slots=list(SLOTS),
            deliver_default=DELIVER_DEFAULT,
            skills=[],
            tags=["japan", "law"],
        )
    except Exception:
        logger.warning("jp-egov-law: automation blueprint was not registered", exc_info=True)
        return False
    return accepted is not None
