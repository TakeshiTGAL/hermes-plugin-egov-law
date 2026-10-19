"""Tool schemas: what the model reads to decide which tool to call and how."""

_LAW_ARG = {
    "type": "string",
    "description": (
        "The law, written any way a person would: official title (労働基準法, 個人情報の保護に関する法律), "
        "e-Gov abbreviation (労基法, 個人情報保護法, 安衛法), common short name (個情法, 下請法, 派遣法, 憲法), "
        "law number (昭和二十二年法律第四十九号 or 昭和22年法律第49号) or e-Gov law ID (322AC0000000049). "
        "An exact official title or abbreviation always wins (民法 is 民法, not 民法施行法). Only when a partial "
        "name matches several laws and none exactly does the tool return an error listing candidates with law_id."
    ),
}

SEARCH = {
    "name": "egov_law_search",
    "description": (
        "Japan laws (e-Gov): find a statute by name. "
        "Read-only. source.url is the e-Gov top page (https://laws.e-gov.go.jp/), not one law's page. "
        "source has retrieved_at and url, and does not include as_of. "
        "If you did not call this tool, say you did not search and do not invent a law number. "
        "mode title matches names and abbreviations; mode text finds a phrase and returns sentences without article numbers, so call egov_law_article next. "
        "Do not call this first when the user already named a law and an article. "
        "Use it to find official Japanese legislation and legal text in e-Gov, such as the Civil Code on a contract, a sale, a lease, or a loan, "
        "the Labor Standards Act, the childcare leave act, or the National Public Service Act for civil servants and public officers. "
        "egov_law_article then takes the article number as digits, for example 32."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "mode='title': part of a law name, abbreviation, law number or law ID (労働基準法, 労基法, "
                    "個人情報). mode='text': a word or phrase to find inside law text (時間外労働)."
                ),
            },
            "mode": {
                "type": "string",
                "default": "title",
                "description": "mode is title or text. title matches names and abbreviations; text matches the body of laws.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10,
                "description": "How many laws to return (default 10, max 50). Exact title matches and Acts come first.",
            },
            "include_repealed": {
                "type": "boolean",
                "default": False,
                "description": "Include repealed laws in title search (default false: laws in force only).",
            },
        },
        "required": [],
    },
}

ARTICLE = {
    "name": "egov_law_article",
    "description": (
        "Japan laws (e-Gov): read one article's text. "
        "Read-only. Returns the wording, source.as_of, source.retrieved_at, and source.url. "
        "If you did not call this tool, say you did not fetch it and do not write the article from memory. "
        "Pass the law by name or abbreviation and the article number. "
        "Show source.attribution with any text you quote. "
        "To compare an amendment, pass as_of and compare_with from egov_law_revisions. "
        "Reads the main provisions and the law's own 附則, not 別表 or forms. "
        "It returns the full text of that article, whether it is a Civil Code rule on a sale or a lease, "
        "a duty of civil servants and public officers, or a childcare leave rule. "
        "Pass the article number as digits, for example 32 or 32-2."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "law": _LAW_ARG,
            "article": {
                "type": "string",
                "description": (
                    "Article number as digits or another written form: 32, 第32条, 32条, 三十二条, 第三十二条. "
                    "Branch articles: 第三十二条の二, 32の2, 32-2. A paragraph may be included: 第32条第2項."
                ),
            },
            "paragraph": {
                "type": "integer",
                "minimum": 1,
                "description": (
                    "Optional paragraph (項) number to return only that paragraph, e.g. 2 for 第2項. "
                    "Overrides a paragraph written inside `article`."
                ),
            },
            "as_of": {
                "type": "string",
                "description": (
                    "YYYY-MM-DD on or after 2017-04-01. A past "
                    "date returns the text in force that day; a future date returns the text as already-passed "
                    "amendments will make it read. Leave out for the current text."
                ),
            },
            "compare_with": {
                "type": "string",
                "description": (
                    "YYYY-MM-DD on or after 2017-04-01. Adds `comparison`: whether this "
                    "article reads differently on that date than on as_of (today if omitted), a line diff and "
                    "that wording, in the same call. To isolate one amendment, use the check pair from "
                    "egov_law_revisions: as_of = the day before, compare_with = the day it takes effect."
                ),
            },
            "max_chars": {
                "type": "integer",
                "minimum": 300,
                "maximum": 20000,
                "default": 4000,
                "description": (
                    "Cut the text after this many characters (default 4000, enough for almost every article; "
                    "e.g. 労基法39条 with its table is about 2600). If cut, the result says truncated=true."
                ),
            },
        },
        "required": [],
    },
}

REVISIONS = {
    "name": "egov_law_revisions",
    "description": (
        "Japan laws (e-Gov): when an amendment takes effect. "
        "Read-only. Returns enforcement dates, the law's e-Gov page URL, and source.retrieved_at. "
        "Does not return source.as_of (only egov_law_article returns that wording date). "
        "If you did not call this tool, say you did not fetch the history and do not invent an act number. "
        "Each row's check pair is as_of and compare_with for egov_law_article. "
        "Bills still in the Diet, and changes to a separate 施行令 or 施行規則, are not included. "
        "It works for any law in e-Gov, including the laws on civil servants and on childcare leave, and the Civil Code rules on a loan. "
        "To read an article afterwards, pass its number as digits, such as 32, to egov_law_article."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "law": _LAW_ARG,
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10,
                "description": "Max entries in each list (scheduled amendments, earlier versions); default 10, max 50.",
            },
        },
        "required": [],
    },
}

ALL_SCHEMAS = [SEARCH, ARTICLE, REVISIONS]
BY_NAME = {schema["name"]: schema for schema in ALL_SCHEMAS}
