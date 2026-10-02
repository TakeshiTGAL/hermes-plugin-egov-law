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
        "Find Japanese laws: query='労基法'; mode='text' searches text. "
        "Searches e-Gov, the official law database of the Digital Agency of Japan. Returns title, "
        "law number (法令番号), law ID, type, abbreviation, the date the current version took effect, "
        "and the e-Gov page URL. "
        "Use it when you do not know which law applies, need a law's number or ID, or want to see related "
        "laws (施行令, 施行規則). mode='title' (default) matches names and abbreviations; "
        "mode='text' finds laws whose text contains a phrase (e.g. 年次有給休暇) and returns matching "
        "sentences; they carry no article numbers, so read the likely article with egov_law_article next. "
        "Do NOT call this first when the user already named a law and an article: call egov_law_article "
        "directly, it accepts names and abbreviations itself."
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
                "enum": ["title", "text"],
                "default": "title",
                "description": "'title' searches names and abbreviations; 'text' searches the body of laws.",
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
        "required": ["query"],
    },
}

ARTICLE = {
    "name": "egov_law_article",
    "description": (
        "Japanese law article: law='労基法', article='32' or '三十二条の二'. "
        "Official text from e-Gov (Digital Agency of Japan), as in force today or on a given date. "
        "One call is enough: pass the law by name or abbreviation and the article number in "
        "any common form. Returns the article title and caption, the text with paragraph (項) and item (号) "
        "numbering, the law number, the date this version took effect, the e-Gov URL and the attribution "
        "to show (source.attribution: show it with any text you quote, as e-Gov's terms require). "
        "Use it whenever the user cites or needs a provision, e.g. 労基法32条, 民法第415条, "
        "個人情報保護法 第二十七条, or when you know the article that governs a topic. "
        "To check whether an amendment changes the article, pass as_of=<the day before it takes effect> and "
        "compare_with=<the day it takes effect> (egov_law_revisions gives both as each row's check): the same "
        "call returns changed true/false, a line diff and the new wording. "
        "Reads the main provisions (本則) and the law's own 附則 (article='附則第143条', or '附則' for one without "
        "articles); not the separate 附則 of amending laws, 別表 or forms. A transitional 附則 can change how "
        "an article applies for the time being without changing its wording; text_notes then names it. "
        "Items (号), 本文 and ただし書 cannot be selected on their own."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "law": _LAW_ARG,
            "article": {
                "type": "string",
                "description": (
                    "Article number as a string, in any form: 第32条, 32条, 32, 三十二条, 第三十二条. "
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
                    "Optional date YYYY-MM-DD, 2017-04-01 or later (e-Gov keeps versions from then). A past "
                    "date returns the text in force that day; a future date returns the text as already-passed "
                    "amendments will make it read. Leave out for the current text."
                ),
            },
            "compare_with": {
                "type": "string",
                "description": (
                    "Optional second date YYYY-MM-DD (2017-04-01 or later). Adds `comparison`: whether this "
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
        "required": ["law", "article"],
    },
}

REVISIONS = {
    "name": "egov_law_revisions",
    "description": (
        "Japanese law amendment & enforcement dates: law='民法'. "
        "From e-Gov (改正履歴・施行日): which version is in force now and since when, "
        "amendments already passed but not yet in force with their scheduled dates, "
        "and older versions with the amending law's name and number. next_amendment is the soonest scheduled "
        "one. Each entry says change (amendment, repeal, or this law's own provisions taking effect), "
        "title_names_this_law (does the amending law's title name this law) and, for a law titled "
        "'〈X〉の施行に伴う…', follow_up_of=X. Neither tells how much an article changes: each amendment row "
        "carries check = {as_of, compare_with} to pass to egov_law_article for that. Each enforcement step of a staged "
        "amendment is its own version with its own date. Covers amendments already promulgated (公布) and "
        "recorded in e-Gov for this one law; bills still in the Diet, and changes to its 施行令/施行規則 "
        "(separate laws: call again with their names), are not included. Use it to answer 'when did/does this "
        "change take effect' or 'is there an upcoming amendment'. "
        "To read the wording of a specific version, call egov_law_article with as_of."
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
        "required": ["law"],
    },
}

ALL_SCHEMAS = [SEARCH, ARTICLE, REVISIONS]
BY_NAME = {schema["name"]: schema for schema in ALL_SCHEMAS}
