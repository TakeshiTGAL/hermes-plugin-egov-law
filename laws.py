"""Law lookup logic: resolve a law the way people name it, then fetch, render and trim.

Every public function returns a plain dict ready for JSON, or raises EgovError
with a message and a next step. tools.py turns both into the handler contract.
"""

from __future__ import annotations

import datetime as _dt
import difflib
import json
import re
from collections import OrderedDict
from typing import Dict, Iterable, List, Optional

from .client import EgovClient, EgovError, law_page_url
from .numbers_ja import (
    LAW_ID_RE,
    LAW_REVISION_ID_RE,
    ArticleRef,
    as_law_num,
    int_to_kanji,
    normalize_text,
    parse_article,
    parse_paragraph,
)

ATTRIBUTION = (
    "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを "
    "hermes-plugin-egov-law が取得・整形（条単位の抽出等）"
)
ATTRIBUTION_NOTE = "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."

EARLIEST_AS_OF = "2017-04-01"  # e-Gov API 400044: asof must be 2017-04-01 or later (checked 2026-10-02)
DEFAULT_MAX_CHARS = 4000
MAX_MAX_CHARS = 20000
MIN_MAX_CHARS = 300

# Common short names that e-Gov does not index as a title or abbreviation
# (checked against the API on 2026-10-02). Value: law_id.
ALIASES: Dict[str, str] = {
    "個情法": "415AC0000000057",          # 個人情報の保護に関する法律
    "特商法": "351AC0000000057",          # 特定商取引に関する法律
    "下請法": "331AC0000000120",          # 製造委託等に係る中小受託事業者に対する代金の支払の遅延等の防止に関する法律
    "雇保法": "349AC0000000116",          # 雇用保険法
    "育介法": "403AC0000000076",          # 育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律
    "育児休業法": "403AC0000000076",      # former title (育児休業等に関する法律) still used colloquially
    "パート法": "405AC0000000076",        # 短時間労働者及び有期雇用労働者の雇用管理の改善等に関する法律
    "パート有期法": "405AC0000000076",
    "パートタイム・有期雇用労働法": "405AC0000000076",
    "フリーランス法": "505AC0000000025",  # 特定受託事業者に係る取引の適正化等に関する法律
    "フリーランス新法": "505AC0000000025",
    "派遣法": "360AC0000000088",          # 労働者派遣事業の適正な運営の確保及び派遣労働者の保護等に関する法律
    "均等法": "347AC0000000113",          # 雇用の分野における男女の均等な機会及び待遇の確保等に関する法律
    "憲法": "321CONSTITUTION",            # 日本国憲法
    "健保法": "211AC0000000070",          # 健康保険法
    "厚年法": "329AC0000000115",          # 厚生年金保険法
    "パワハラ防止法": "341AC0000000132",  # 労働施策の総合的な推進並びに…（労働施策総合推進法）
    "高年法": "346AC0000000068",          # 高年齢者等の雇用の安定等に関する法律
    "労基則": "322M40000100023",          # 労働基準法施行規則
    "労規則": "322M40000100023",
    "雇保則": "350M50002000003",          # 雇用保険法施行規則
    "電帳法": "410AC0000000025",          # 電子計算機を使用して作成する国税関係帳簿書類の保存方法等の特例に関する法律
}
_ALIASES_NORMALIZED = {normalize_text(k): v for k, v in ALIASES.items()}

LAW_TYPE_LABELS = {
    "Constitution": "憲法",
    "Act": "法律",
    "CabinetOrder": "政令",
    "ImperialOrder": "勅令",
    "MinisterialOrdinance": "府省令",
    "Rule": "規則",
    "Misc": "その他",
}
_LAW_TYPE_RANK = {"Constitution": 0, "Act": 0, "CabinetOrder": 1, "ImperialOrder": 1,
                  "MinisterialOrdinance": 2, "Rule": 3, "Misc": 4}
STATUS_LABELS = {
    "CurrentEnforced": "in force now",
    "PreviousEnforced": "superseded (older version)",
    "UnEnforced": "not yet in force (scheduled)",
    "Repeal": "repealed",
}

_RESOLVE_CACHE_MAX = 256  # name -> law ID answers kept per client (process memory only)


# --- Small helpers ---------------------------------------------------------

def _today_jst() -> str:
    return (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=9)).date().isoformat()


def _source() -> dict:
    return {"attribution": ATTRIBUTION, "retrieved_on": _today_jst(), "note": ATTRIBUTION_NOTE}


def _clamp(value, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _check_date(value: Optional[str], name: str) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        _dt.date.fromisoformat(text)
    except ValueError:
        raise EgovError("bad_argument", f"{name} must be a date like 2024-04-01, got {value!r}.",
                        f"Pass {name} as YYYY-MM-DD, or leave it out for the version in force today.")
    return text


def _status(revision: dict) -> str:
    if (revision.get("repeal_status") or "None") != "None":
        return "repealed" if revision.get("repeal_status") == "Repeal" else str(revision.get("repeal_status"))
    raw = revision.get("current_revision_status") or ""
    return STATUS_LABELS.get(raw, raw)


def _status_of_latest(revision: dict) -> str:
    """Status of the version e-Gov serves as current (`current_revision_info`, or law_data without asof).

    e-Gov sometimes still labels the newest enforced version PreviousEnforced for a while after a
    new version starts (seen 2026-10-02 on 個人情報保護法), so we trust the API's choice of version
    rather than its label.
    """
    status = _status(revision)
    if status in (STATUS_LABELS["PreviousEnforced"], STATUS_LABELS["CurrentEnforced"]):
        return STATUS_LABELS["CurrentEnforced"]
    return status


def _newest_passed(revisions: List[dict], today: str) -> Optional[int]:
    """Index of the newest version whose enforcement date has passed and that is not marked UnEnforced."""
    best, best_date = None, ""
    for index, revision in enumerate(revisions):
        date = _enforcement_date(revision) or ""
        if revision.get("current_revision_status") == "UnEnforced" or date > today:
            continue
        if best is None or date > best_date:
            best, best_date = index, date
    return best


def _repealed_index(revisions: List[dict], today: str) -> Optional[int]:
    """Index of the repeal row when the law's repeal has already taken effect, else None."""
    index = _newest_passed(revisions, today)
    if index is not None and _change_type(revisions[index]) == CHANGE_REPEAL:
        return index
    return None


def _pick_in_force(revisions: List[dict], today: str) -> Optional[int]:
    """Index of the version in force today: the one e-Gov marks CurrentEnforced, else the newest
    version whose enforcement date has passed and that is not marked UnEnforced. None when no version
    is in force: the law is not in force yet, or its repeal has taken effect (a repeal row is never
    a version in force)."""
    for index, revision in enumerate(revisions):
        if revision.get("current_revision_status") == "CurrentEnforced" and _change_type(revision) != CHANGE_REPEAL:
            return index
    if _repealed_index(revisions, today) is not None:
        return None
    return _newest_passed(revisions, today)


def _type_label(law_type: str) -> str:
    label = LAW_TYPE_LABELS.get(law_type or "")
    return f"{law_type} ({label})" if label else (law_type or "")


def _summary(entry: dict, match: str = "") -> dict:
    """One law from /laws or /keyword, trimmed to what a model needs."""
    info = entry.get("law_info") or {}
    revision = entry.get("revision_info") or {}
    current = entry.get("current_revision_info") or revision
    out = {
        "law_title": revision.get("law_title"),
        "law_num": info.get("law_num"),
        "law_id": info.get("law_id"),
        "law_type": _type_label(info.get("law_type") or revision.get("law_type")),
        "abbrev": revision.get("abbrev") or None,
        "promulgation_date": info.get("promulgation_date"),
        "current_version_in_force_since": current.get("amendment_enforcement_date"),
        "status": _status_of_latest(current),
        "url": law_page_url(info.get("law_id") or ""),
    }
    if match:
        out["match"] = match
    return {k: v for k, v in out.items() if v not in (None, "")}


def _match_kind(entry: dict, query_norm: str) -> str:
    revision = entry.get("revision_info") or {}
    if normalize_text(revision.get("law_title")) == query_norm:
        return "exact title"
    abbrevs = [normalize_text(a) for a in (revision.get("abbrev") or "").split(",") if a]
    if query_norm in abbrevs:
        return "abbreviation"
    return "partial title"


def _rank(entries: Iterable[dict], query_norm: str) -> List[dict]:
    order = {"alias": 0, "exact title": 0, "abbreviation": 1, "partial title": 2}

    def key(entry):
        revision = entry.get("revision_info") or {}
        info = entry.get("law_info") or {}
        kind = entry.get("_match") or _match_kind(entry, query_norm)
        title = normalize_text(revision.get("law_title"))
        starts = 0 if title.startswith(query_norm) else 1
        return (order.get(kind, 3), _LAW_TYPE_RANK.get(info.get("law_type"), 5), starts, len(title))

    return sorted(entries, key=key)


def _cache(client: EgovClient) -> "OrderedDict[str, dict]":
    return client.resolve_cache


def _cache_put(client: EgovClient, key: str, value: dict) -> None:
    cache = _cache(client)
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > _RESOLVE_CACHE_MAX:
        cache.popitem(last=False)


# --- Resolving a law -------------------------------------------------------

def resolve_law(client: EgovClient, law: str) -> dict:
    """Turn what the user typed into {'key': <law_id or law_num>, 'how': ...}.

    Accepts a law ID (322AC0000000049), a law number (昭和二十二年法律第四十九号 or
    昭和22年法律第49号), the official title, an e-Gov abbreviation (労基法) or a
    common short name from ALIASES (個情法). Ambiguous names raise with candidates.
    """
    raw = str(law or "").strip()
    if not raw:
        raise EgovError("bad_argument", "`law` is empty.",
                        "Pass a law name such as 労働基準法 or 労基法, a law number, or a law ID.")
    compact = re.sub(r"\s+", "", raw)
    if LAW_ID_RE.match(compact) or LAW_REVISION_ID_RE.match(compact):
        return {"key": compact, "how": "law ID"}
    law_num = as_law_num(compact)
    if law_num:
        return {"key": law_num, "how": "law number"}

    query = normalize_text(compact)
    if query in _ALIASES_NORMALIZED:
        return {"key": _ALIASES_NORMALIZED[query], "how": f"common short name {raw!r}"}
    cache = _cache(client)
    if query in cache:
        cache.move_to_end(query)
        return cache[query]

    data = client.get("laws", {"law_title": compact, "repeal_status": "None", "limit": 100})
    entries = data.get("laws") or []
    total = int(data.get("total_count") or len(entries))
    if not entries:
        raise EgovError(
            "law_not_found",
            f"No law in force has a title or abbreviation containing {raw!r}.",
            "If this is a nickname, call again with the official title or e-Gov abbreviation (e.g. "
            "パワハラ防止法 is 労働施策総合推進法). Otherwise call egov_law_search with a shorter part of the "
            "name, or with mode='text' to search inside law text.",
        )
    exact = [e for e in entries if _match_kind(e, query) == "exact title"]
    abbrev = [e for e in entries if _match_kind(e, query) == "abbreviation"]
    if not exact and not abbrev and total > len(entries):
        # More than one page of partial matches: the exact law may sit past it. Acts are what
        # people usually mean, so look again among Acts and the Constitution only.
        acts = client.get("laws", {"law_title": compact, "repeal_status": "None", "limit": 100,
                                   "law_type": "Constitution,Act"}).get("laws") or []
        exact = [e for e in acts if _match_kind(e, query) == "exact title"]
        abbrev = [e for e in acts if _match_kind(e, query) == "abbreviation"]
    chosen, how = None, ""
    if exact:
        chosen, how = _rank(exact, query)[0], "exact title"
    elif abbrev:
        chosen, how = _rank(abbrev, query)[0], "abbreviation"
    elif len(entries) == 1:
        chosen, how = entries[0], "only law whose title contains the name"
    if chosen is None:
        candidates = [_summary(e, _match_kind(e, query)) for e in _rank(entries, query)[:8]]
        raise EgovError(
            "ambiguous_law",
            f"{total} laws match {raw!r}; none is an exact title or abbreviation.",
            "Pick one candidate and call the same tool again with law='<its law_id>' (or its exact title). "
            "If the user's words fit several, read each or ask the user. If none fits, call "
            "egov_law_search with a longer part of the name or a higher limit. Candidates (Acts first): "
            + "; ".join(f"{c.get('law_title')} [{c.get('law_id')}]" for c in candidates),
        )
    info = chosen.get("law_info") or {}
    result = {
        "key": info.get("law_id"),
        "how": how,
        "law_title": (chosen.get("revision_info") or {}).get("law_title"),
    }
    _cache_put(client, query, result)
    return result


# --- Search ----------------------------------------------------------------

def search_laws(client: EgovClient, query: str, mode: str = "title", limit=10,
                include_repealed: bool = False) -> dict:
    raw = str(query or "").strip()
    if not raw:
        raise EgovError("bad_argument", "`query` is empty.",
                        "Pass a law name (労働基準法), an abbreviation (労基法) or, with mode='text', a phrase.")
    limit = _clamp(limit, 10, 1, 50)
    mode = (mode or "title").strip().lower()
    if mode not in ("title", "text"):
        raise EgovError("bad_argument", f"mode must be 'title' or 'text', got {mode!r}.",
                        "Use mode='title' to find a law by name, mode='text' to find laws that mention a phrase.")
    if mode == "text":
        return _search_text(client, raw, limit)

    compact = re.sub(r"\s+", "", raw)
    query_norm = normalize_text(compact)
    params = {"limit": 100}
    if not include_repealed:
        params["repeal_status"] = "None"
    if LAW_ID_RE.match(compact):
        params["law_id"] = compact
    elif as_law_num(compact):
        params["law_num"] = as_law_num(compact)
    else:
        params["law_title"] = compact
    data = client.get("laws", params)
    entries = list(data.get("laws") or [])
    total = int(data.get("total_count") or len(entries))

    alias_id = _ALIASES_NORMALIZED.get(query_norm)
    if alias_id and not any((e.get("law_info") or {}).get("law_id") == alias_id for e in entries):
        alias_data = client.get("laws", {"law_id": alias_id, "limit": 1})
        for entry in alias_data.get("laws") or []:
            entry["_match"] = "alias"
            entries.insert(0, entry)
            total += 1

    ranked = _rank(entries, query_norm)
    results = [_summary(e, e.get("_match") or _match_kind(e, query_norm)) for e in ranked[:limit]]
    out = {
        "query": raw,
        "mode": "title",
        "total_matches": total,
        "returned": len(results),
        "results": results,
        "source": _source(),
    }
    if not results:
        out["message"] = (
            f"0 laws found: no law {'' if include_repealed else 'in force '}has a title or abbreviation "
            f"containing {raw!r}."
        )
        out["next_step"] = (
            "Try a shorter or official name (e.g. 個人情報の保護に関する法律), "
            "or call egov_law_search again with mode='text' to search inside law text."
        )
    elif total > len(results):
        out["next_step"] = ("More laws match than shown. Results are sorted with exact titles and Acts first; "
                            "narrow the query if the law you want is missing.")
    return out


def _clean_snippet(text: str) -> str:
    text = re.sub(r"</?span[^>]*>", "", str(text or ""))
    return re.sub(r"<[^>]+>", "", text).strip()


def _search_text(client: EgovClient, phrase: str, limit: int) -> dict:
    try:
        data = client.get("keyword", {"keyword": phrase, "limit": min(100, limit * 5)})
    except EgovError as error:
        if error.api_code != "404001":  # e-Gov answers "0 results" with HTTP 404 / 404001
            raise
        data = {"total_count": 0, "items": []}
    grouped: "OrderedDict[str, dict]" = OrderedDict()
    for item in data.get("items") or []:
        info = item.get("law_info") or {}
        law_id = info.get("law_id") or ""
        if law_id not in grouped:
            if len(grouped) >= limit:
                continue
            summary = _summary(item)
            summary["snippets"] = []
            grouped[law_id] = summary
        snippets = grouped[law_id]["snippets"]
        for sentence in item.get("sentences") or []:
            if sentence.get("position") in ("toc", "mainprovisiontoc"):
                continue
            text = _clean_snippet(sentence.get("text"))
            if text and text not in snippets and len(snippets) < 3:
                snippets.append(text)
    results = list(grouped.values())
    out = {
        "query": phrase,
        "mode": "text",
        "total_matching_sentences": data.get("total_count"),
        "returned_laws": len(results),
        "results": results,
        "source": _source(),
    }
    if not results:
        out["message"] = f"0 laws found: no law text contains {phrase!r}."
        out["next_step"] = ("Laws use formal wording: try it (e.g. パワーハラスメント → 優越的な関係を背景とした言動), "
                            "fewer words, or mode='title' if this is part of a law's name.")
    else:
        out["next_step"] = ("Snippets carry no article numbers. Call egov_law_article on the article you think "
                            "applies and check its caption; snippets that are only a caption, like （年次有給休暇）, "
                            "show which law to look in.")
    return out


# --- Article text ----------------------------------------------------------

_BLOCK_TAGS = {"Paragraph", "Item"} | {f"Subitem{i}" for i in range(1, 11)}
_TITLE_TAGS = {"ParagraphNum", "ItemTitle"} | {f"Subitem{i}Title" for i in range(1, 11)}
_SENTENCE_TAGS = {"ParagraphSentence", "ItemSentence"} | {f"Subitem{i}Sentence" for i in range(1, 11)}
_FULLWIDTH = str.maketrans("0123456789", "０１２３４５６７８９")


def _children(node) -> list:
    return node.get("children") or [] if isinstance(node, dict) else []


def _tag(node) -> str:
    return node.get("tag", "") if isinstance(node, dict) else ""


def text_of(node) -> str:
    """Plain text of a law-XML node: ruby readings (Rt) dropped, everything else concatenated."""
    if isinstance(node, str):
        return node.strip()
    if not isinstance(node, dict) or _tag(node) == "Rt":
        return ""
    return "".join(text_of(child) for child in _children(node))


def _sentence_text(node) -> str:
    parts = []
    for child in _children(node):
        if _tag(child) == "Column":
            parts.append(("　" if parts else "") + text_of(child))
        else:
            parts.append(text_of(child))
    return "".join(parts)


def _other_lines(node) -> List[str]:
    if _tag(node) == "TableStruct":
        rows = []
        for table in _children(node):
            for row in _children(table):
                if _tag(row) == "TableRow":
                    rows.append("｜".join(text_of(col) for col in _children(row)))
        return rows or [text_of(node)]
    text = text_of(node)
    return [text] if text else []


def _render_block(node, depth: int, lines: List[str]) -> None:
    title, sentence, rest = "", "", []
    for child in _children(node):
        tag = _tag(child)
        if tag in _TITLE_TAGS:
            title = text_of(child)
        elif tag in _SENTENCE_TAGS:
            sentence = _sentence_text(child)
        elif isinstance(child, dict):
            rest.append(child)
    if _tag(node) == "Paragraph" and not title:
        num = str((node.get("attr") or {}).get("Num") or "")
        title = "" if num in ("", "1") else num.translate(_FULLWIDTH)
    indent = "　" * depth
    lines.append(indent + (f"{title}　" if title else "") + sentence)
    for child in rest:
        if _tag(child) in _BLOCK_TAGS:
            _render_block(child, depth + 1, lines)
        else:
            lines.extend(indent + "　" + line for line in _other_lines(child))


def render_article(node) -> dict:
    """Render an Article (or Paragraph) node to {'title','caption','text','paragraphs'}."""
    if isinstance(node, list):
        rendered = [render_article(n) for n in node if isinstance(n, dict)]
        return {
            "title": " / ".join(r["title"] for r in rendered if r["title"]),
            "caption": " / ".join(r["caption"] for r in rendered if r["caption"]),
            "text": "\n".join(r["text"] for r in rendered),
            "paragraphs": sum(r["paragraphs"] for r in rendered),
        }
    tag = _tag(node)
    if tag == "SupplProvision":
        return _render_suppl(node)
    if tag == "Paragraph":
        lines: List[str] = []
        _render_block(node, 0, lines)
        return {"title": "", "caption": "", "text": "\n".join(lines).strip(), "paragraphs": 1}
    caption = title = ""
    lines = []
    paragraphs = 0
    for child in _children(node):
        child_tag = _tag(child)
        if child_tag == "ArticleCaption":
            caption = text_of(child)
        elif child_tag == "ArticleTitle":
            title = text_of(child)
        elif child_tag == "Paragraph":
            paragraphs += 1
            _render_block(child, 0, lines)
        elif isinstance(child, dict):
            lines.extend(_other_lines(child))
    if lines and title:
        first = lines[0].lstrip("　")
        lines[0] = f"{title}　{first}"
    elif title:
        lines.insert(0, title)
    if caption:
        lines.insert(0, caption)
    return {"title": title, "caption": caption, "text": "\n".join(lines).strip(), "paragraphs": paragraphs}


def _render_suppl(node) -> dict:
    """A whole 附則: its label, then each article or paragraph (chapters are walked through)."""
    lines: List[str] = []
    paragraphs = 0

    def walk(parent):
        nonlocal paragraphs
        for child in _children(parent):
            tag = _tag(child)
            if tag == "SupplProvisionLabel":
                lines.append(text_of(child))
            elif tag == "Article":
                rendered = render_article(child)
                lines.append(rendered["text"])
                paragraphs += rendered["paragraphs"]
            elif tag == "Paragraph":
                paragraphs += 1
                _render_block(child, 0, lines)
            elif tag.endswith("Title") and tag != "ArticleTitle":
                lines.append(text_of(child))
            elif isinstance(child, dict):
                walk(child)

    walk(node)
    return {"title": "", "caption": "", "text": "\n".join(l for l in lines if l).strip(), "paragraphs": paragraphs}


def _split_suppl(article) -> tuple:
    """('附則第143条' -> (True, '第143条')), ('第32条' -> (False, '第32条'))."""
    text = str(article).strip()
    match = re.match(r"^(?:附則|supplementary\s+provisions?|suppl\.?)\s*(?:の)?", text, re.I)
    if not match:
        return False, text
    return True, text[match.end():].strip()


def _trim(text: str, max_chars: int):
    if len(text) <= max_chars:
        return text, False
    cut = text.rfind("\n", 0, max_chars)  # nothing is appended: `truncated` says the text was cut
    if cut < max_chars // 2:
        cut = max_chars
    return text[:cut].rstrip(), True


def get_article(client: EgovClient, law: str, article, paragraph=None, as_of: Optional[str] = None,
                max_chars=DEFAULT_MAX_CHARS, compare_with: Optional[str] = None) -> dict:
    if article in (None, ""):
        raise EgovError("bad_argument", "`article` is required.",
                        "Pass the article number, e.g. '第32条', '32', or '第三十二条の二'. "
                        "Use egov_law_search to look up a law without reading an article.")
    if re.search(r"別表|様式|別記|別図|付録", str(article)):
        resolve_law(client, law)  # an unknown or ambiguous law name is reported first
        url = _url_for(client, law)
        raise EgovError(
            "not_covered",
            f"{str(article)!r} is an appended table or form; this tool reads articles of 本則 and of the "
            "law's own 附則 only.",
            "Do not retry with another number. Give the user the law's e-Gov page"
            + (f" {url}" if url else " (egov_law_search returns its url)")
            + " and say that 別表 and forms must be read there.",
        )
    suppl, rest = _split_suppl(article)
    rest, dropped = _drop_sub_paragraph(rest)
    try:
        explicit_paragraph = parse_paragraph(paragraph)
        if suppl and not rest:
            ref = None  # the whole 附則, or one of its paragraphs
            suppl_paragraph = explicit_paragraph
        elif suppl and re.fullmatch(r"第?[0-9０-９〇一二三四五六七八九十百千]+項", rest):
            ref, suppl_paragraph = None, parse_paragraph(rest)
        else:
            ref = parse_article(rest)
            suppl_paragraph = None
    except ValueError as error:
        raise EgovError("bad_argument", str(error),
                        "Fix the number and call again. Items (号), 本文 and ただし書 cannot be selected; "
                        "ask for the article or its paragraph.") from None
    if ref is not None and explicit_paragraph:
        ref = ArticleRef(numbers=ref.numbers, paragraph=explicit_paragraph)
    as_of = _check_date(as_of, "as_of")
    compare_with = _check_date(compare_with, "compare_with")
    for name, value in (("as_of", as_of), ("compare_with", compare_with)):
        if value and value < EARLIEST_AS_OF:
            raise EgovError(
                "bad_argument",
                f"e-Gov keeps law versions from {EARLIEST_AS_OF} onward; {name}={value} is earlier.",
                f"Use a {name} date on or after {EARLIEST_AS_OF}, or call egov_law_revisions to see which amendment "
                "was in force on the date you need (older wording is not available through e-Gov).",
            )
    max_chars = _clamp(max_chars, DEFAULT_MAX_CHARS, MIN_MAX_CHARS, MAX_MAX_CHARS)

    resolved = resolve_law(client, law)
    if ref is None and suppl_paragraph:
        _require_suppl_without_articles(client, resolved, law, suppl_paragraph, as_of)
    if ref is None:  # 附則 without an article number
        elm = "SupplProvision" + (f"-Paragraph_{suppl_paragraph}" if suppl_paragraph else "")
        label = "附則" + (f"第{int_to_kanji(suppl_paragraph)}項" if suppl_paragraph else "")
    else:
        elm = (("SupplProvision-" if suppl else "MainProvision-") + ref.elm_article
               + (f"-Paragraph_{ref.paragraph}" if ref.paragraph else ""))
        label = ("附則" if suppl else "") + ref.label
    part = "its own supplementary provisions (附則)" if suppl else "its main provisions"
    try:
        data = client.get(f"law_data/{resolved['key']}",
                          {"elm": elm, "json_format": "full", "asof": as_of,
                           "omit_amendment_suppl_provision": "true"})
    except EgovError as error:
        name = resolved.get("law_title") or _title_for(client, resolved["key"]) or str(law)
        if ref is not None and ref.paragraph and not suppl and (
                error.api_code == "400021" or (error.status == 400 and "elm" in error.message)):
            count = _paragraph_count(client, resolved["key"], ref, as_of)
            if count:
                raise EgovError(
                    "paragraph_not_found",
                    f"{name} {ArticleRef(ref.numbers, None).label} has {count} paragraph(s); "
                    f"there is no 第{int_to_kanji(ref.paragraph)}項.",
                    f"Call again with paragraph between 1 and {count}, or without paragraph for the whole article. "
                    "If the paragraph is added by an upcoming amendment, call with as_of=<its in_force_since>.",
                    status=error.status, api_code=error.api_code,
                ) from None
        if error.api_code == "400021" or (error.status == 400 and "elm" in error.message):
            law_id, moved = None, None
            if ref is not None and not as_of and not LAW_REVISION_ID_RE.match(resolved["key"]):
                law_id, moved = _article_before_current_version(client, resolved["key"], suppl, ref)
            url = (law_page_url(resolved["key"]) if LAW_ID_RE.match(resolved["key"])
                   else law_page_url(law_id) if law_id else _url_for(client, law))
            if moved:
                article_label = ("附則" if suppl else "") + ArticleRef(ref.numbers, None).label
                caption = moved["caption"]
                words = caption.strip("（）() ")
                raise EgovError(
                    "article_not_found",
                    f"{name} has no {label} in {part} today. {article_label} existed in the version in force on "
                    f"{moved['existed_on']}; the amendment that took effect on {moved['changed_on']}"
                    + (f" ({moved['changed_by']})" if moved["changed_by"] else "")
                    + " moved or deleted it.",
                    "Do not guess the new number. "
                    + (f"Call egov_law_search with mode='text' and query='{words}' (the words of the old caption), "
                       if words else
                       f"Read the old wording with as_of='{moved['existed_on']}' and call egov_law_search with "
                       "mode='text' on a distinctive phrase from it, ")
                    + "or check the new number on the law's e-Gov page"
                    + (f" {url}" if url else "") + ".",
                    status=error.status, api_code=error.api_code,
                    details={"previous_caption": caption or None, "existed_on": moved["existed_on"],
                             "changed_on": moved["changed_on"], "changed_by": moved["changed_by"], "url": url},
                ) from None
            hint = ("Do not try nearby numbers at random. Branch articles are written '32の2'. "
                    "The article may have been deleted (some are deleted as a range, 第十条から第十二条まで　削除) "
                    "or be added only by an upcoming amendment (then call with as_of=<its in_force_since>).")
            if suppl:
                hint = ("This tool reads the law's own 附則 only; transitional rules in an amending law's own 附則 "
                        "are not available. A 附則 without articles is read with article='附則'. " + hint)
            raise EgovError(
                "article_not_found",
                f"{name} has no {label} in {part}"
                + (f" as of {as_of}" if as_of else "") + ".",
                hint + (f" Give the user the law's page {url}." if url else ""),
                status=error.status, api_code=error.api_code,
            ) from None
        if error.status == 404:
            raise EgovError(
                "law_not_found",
                f"e-Gov has no law text for {law!r}" + (f" as of {as_of}" if as_of else "") + ".",
                "Check the law ID or number with egov_law_search; if you passed as_of, the law may not "
                "have existed yet on that date.",
                status=404, api_code=error.api_code,
            ) from None
        raise

    info = data.get("law_info") or {}
    revision = data.get("revision_info") or {}
    full_text = data.get("law_full_text")
    if not full_text:
        raise EgovError("bad_response", "e-Gov returned no text for this article.",
                        "Try again later; if it repeats, open the url in a browser to read the law.")
    rendered = render_article(full_text)
    text, truncated = _trim(rendered["text"], max_chars)
    has_table = '"TableStruct"' in json.dumps(full_text, ensure_ascii=False)
    out = {
        "law_title": revision.get("law_title"),
        "law_num": info.get("law_num"),
        "law_id": info.get("law_id"),
        "article": ("附則" if suppl and rendered["title"] else "") + rendered["title"] if rendered["title"] else label,
        "requested": label,
        "provision": ("附則: the law's own supplementary provisions (including articles inserted later, such "
                      "as 労基法 附則第143条); the separate 附則 of each amending law is not included") if suppl else None,
        "caption": rendered["caption"] or None,
        "text": text,
        "paragraphs": rendered["paragraphs"] or None,
        "law_version": {
            "note": "Version of the whole law. This article did not necessarily change in it.",
            "in_force_since": _enforcement_date(revision),
            "status": _version_status(revision, as_of),
            "last_amended_by": _amended_by(revision),
            "law_revision_id": revision.get("law_revision_id"),
        },
        "as_of": as_of or _today_jst(),
        "resolved_by": resolved["how"],
        "url": law_page_url(info.get("law_id") or ""),
        "source": _source(),
    }
    if ref is not None and ref.paragraph:
        out["article"] = label
    if out["requested"] == out["article"]:
        out.pop("requested")
    notes = []
    if has_table:
        notes.append("This article contains a table, flattened to one row per line with ｜ between cells. "
                     "Tables with multi-row headers do not line up column by column.")
    if isinstance(full_text, dict) and (full_text.get("attr") or {}).get("Extract") == "true":
        notes.append("e-Gov carries only an excerpt (抄) of this part, so some of it may be missing.")
    if revision.get("repeal_status") == "Repeal":
        notes.append(f"This law was repealed on {_enforcement_date(revision)}"
                     + (f" by {_amended_by(revision)}" if _amended_by(revision) else "")
                     + "; this is its wording when repealed, not law in force.")
    if dropped:
        notes.append(f"{dropped} cannot be selected on its own; the whole "
                     + ("paragraph" if ref is not None and ref.paragraph else "article") + " is returned.")
    if not suppl and ref is not None and rendered["title"]:
        readings = _suppl_readings(client, resolved["key"], as_of, rendered["title"])
        if readings:
            notes.append(f"{'・'.join(readings)} of this law's 附則 says how this article applies "
                         "(…の規定の適用については…). Some such transitional rules still apply and some have expired; "
                         "if the answer depends on what applies, read it with article='" + readings[0] + "'.")
    if notes:
        out["text_notes"] = " ".join(notes) + " (Notes, not part of the law text.)"
    if compare_with:
        out["comparison"] = _compare(client, resolved["key"], elm, rendered["text"], compare_with, max_chars)
    if truncated:
        total = len(rendered["text"])
        out["truncated"] = True
        out["total_chars"] = total
        out["next_step"] = (f"Text cut at {max_chars} of {total} characters. Call again with max_chars={total}."
                            if total <= MAX_MAX_CHARS else
                            f"Text cut at {max_chars} of {total} characters. Read it one paragraph at a time "
                            "with `paragraph`.")
    out["law_version"] = {k: v for k, v in out["law_version"].items() if v}
    return {k: v for k, v in out.items() if v not in (None, "")}


_SUB_PARAGRAPH_RE = re.compile(r"(第?[0-9０-９〇一二三四五六七八九十百千]+号|本文|ただし書き?|前段|後段|柱書)+$")


def _version_status(revision: dict, as_of: Optional[str]) -> str:
    """Status of the version returned for as_of, judged by its own enforcement date."""
    if not as_of:
        return _status_of_latest(revision)
    since = _enforcement_date(revision) or ""
    today = _today_jst()
    if since > today:
        return f"not yet in force (takes effect {since}): the text as scheduled to read on {as_of}"
    if as_of > today:
        return f"in force now (also the version on {as_of}, unless a later amendment is promulgated)"
    return f"version in force on {as_of}"


def _drop_sub_paragraph(rest: str):
    """'第32条第1項第2号' -> ('第32条第1項', '第2号'): items and 本文/ただし書 cannot be selected."""
    text = str(rest or "").strip()
    match = _SUB_PARAGRAPH_RE.search(text)
    if not match or match.start() == 0:
        return text, None
    return text[:match.start()], match.group(0)


def _require_suppl_without_articles(client, resolved, law, paragraph_no, as_of) -> None:
    """'附則第2項' only exists when the 附則 has no articles; otherwise e-Gov would match a paragraph
    nested in some article and we would mislabel it."""
    try:
        data = client.get(f"law_data/{resolved['key']}", {"elm": "SupplProvision", "json_format": "full",
                                                          "asof": as_of, "omit_amendment_suppl_provision": "true"})
    except EgovError:
        return
    node = data.get("law_full_text") or {}
    if any(_tag(child) == "Article" for child in _children(node)):
        raise EgovError(
            "article_not_found",
            f"The 附則 of {resolved.get('law_title') or law} is divided into articles, so it has no "
            f"附則第{int_to_kanji(paragraph_no)}項 of its own.",
            "Call again with article='附則第N条' and paragraph=" + str(paragraph_no) + ".",
        )


def _suppl_readings(client: EgovClient, key: str, as_of: Optional[str], article_title: str) -> List[str]:
    """Articles of the law's own 附則 that read this article differently (…第N条の規定の適用については).
    One request per law and date, cached on the client; any failure just means no note."""
    cache = client.resolve_cache
    cache_key = f"suppl::{key}::{as_of or ''}"
    if cache_key not in cache:
        try:
            data = client.get(f"law_data/{key}", {"elm": "SupplProvision", "json_format": "full", "asof": as_of,
                                                  "omit_amendment_suppl_provision": "true"})
            node = data.get("law_full_text") or {}
            articles = []
            stack = [node]
            while stack:
                current = stack.pop()
                for child in _children(current):
                    if _tag(child) == "Article":
                        title = "".join(text_of(c) for c in _children(child) if _tag(c) == "ArticleTitle")
                        articles.append(("附則" + title, text_of(child)))
                    elif isinstance(child, dict):
                        stack.append(child)
            _cache_put(client, cache_key, {"articles": articles})
        except EgovError:
            _cache_put(client, cache_key, {"articles": []})
    pattern = re.compile(re.escape(article_title) + r"(?:第[〇一二三四五六七八九十百千]+項)?(?:及び[^の]*)?の規定の適用については")
    found = [label for label, text in cache[cache_key]["articles"] if pattern.search(text)]
    return sorted(set(found), key=found.index)


def _compare(client: EgovClient, key: str, elm: str, text: str, other_date: str, max_chars: int) -> dict:
    """The same article on another date: whether it changed, a line diff, and the other wording."""
    try:
        data = client.get(f"law_data/{key}", {"elm": elm, "json_format": "full", "asof": other_date,
                                              "omit_amendment_suppl_provision": "true"})
    except EgovError as error:
        if error.api_code == "400021" or error.status in (400, 404):
            return {"as_of": other_date, "exists": False, "changed": True,
                    "note": "This article (or paragraph) does not exist in the version in force on that date."}
        raise
    other = render_article(data.get("law_full_text") or {})["text"]
    revision = data.get("revision_info") or {}
    if other == text:
        return {"as_of": other_date, "changed": False,
                "law_version_in_force_since": _enforcement_date(revision),
                "note": "Identical wording on both dates."}
    diff = [line for line in difflib.unified_diff(text.splitlines(), other.splitlines(), lineterm="", n=0)
            if not line.startswith(("---", "+++", "@@"))]
    other_text, cut = _trim(other, max_chars)
    kept, used = [], 0
    for line in diff:  # the diff obeys max_chars too
        if used + len(line) > max_chars:
            cut = True
            break
        kept.append(line)
        used += len(line)
    result = {"as_of": other_date, "changed": True,
              "law_version_in_force_since": _enforcement_date(revision),
              "diff": kept, "text": other_text,
              "note": ("diff compares whole paragraph/item lines: '-' is the wording on as_of (the main text "
                       "above), '+' on this date.")}
    if cut:
        result["truncated"] = True
    return result


def _article_before_current_version(client: EgovClient, key: str, suppl: bool, ref: ArticleRef):
    """For an article missing today: was it in the version just before the one in force now?

    Two requests at most (the law's revision list, then the article as it read the day before the
    current version took effect), made once. Returns (law_id or None, None or {'existed_on',
    'changed_on', 'changed_by', 'caption'}). Any failure only means there is nothing to add."""
    try:
        data = client.get(f"law_revisions/{key}")
    except EgovError:
        return None, None
    law_id = (data.get("law_info") or {}).get("law_id") or None
    revisions = data.get("revisions") or []
    index = _pick_in_force(revisions, _today_jst())
    if index is None:
        return law_id, None
    current = revisions[index]
    since = _enforcement_date(current)
    dates = _check_dates(since)
    if not dates:
        return law_id, None
    try:
        old = client.get(f"law_data/{key}", {"elm": ("SupplProvision-" if suppl else "MainProvision-") + ref.elm_article,
                                            "json_format": "full", "asof": dates["as_of"],
                                            "omit_amendment_suppl_provision": "true"})
    except EgovError:
        return law_id, None
    rendered = render_article(old.get("law_full_text") or {})
    if not rendered["text"]:
        return law_id, None
    return law_id, {"existed_on": dates["as_of"], "changed_on": since, "changed_by": _amended_by(current),
                    "caption": rendered["caption"]}


def _url_for(client: EgovClient, law: str) -> Optional[str]:
    """e-Gov page of a law, or None when the name cannot be resolved (used in error hints)."""
    try:
        key = resolve_law(client, law)["key"]
        if not LAW_ID_RE.match(key.split("_", 1)[0]):
            laws = client.get("laws", {"law_num": key, "limit": 1}).get("laws") or []
            key = (laws[0].get("law_info") or {}).get("law_id") if laws else None
    except EgovError:
        return None
    return law_page_url(key.split("_", 1)[0]) if key else None


def _title_for(client: EgovClient, key: str) -> Optional[str]:
    """Law title for an ID or number, for error messages. None if the lookup fails."""
    try:
        params = {"law_id": key} if LAW_ID_RE.match(key) else {"law_num": key}
        laws = client.get("laws", {**params, "limit": 1}).get("laws") or []
    except EgovError:
        return None
    return (laws[0].get("revision_info") or {}).get("law_title") if laws else None


def _paragraph_count(client: EgovClient, key: str, ref: ArticleRef, as_of: Optional[str]) -> int:
    """Number of paragraphs of the article (0 if the article itself does not exist)."""
    try:
        data = client.get(f"law_data/{key}", {"elm": "MainProvision-" + ref.elm_article, "json_format": "full",
                                              "asof": as_of, "omit_amendment_suppl_provision": "true"})
    except EgovError:
        return 0
    return render_article(data.get("law_full_text") or {}).get("paragraphs") or 0


def _enforcement_date(revision: dict) -> Optional[str]:
    """The version's enforcement date; e-Gov leaves amendment_enforcement_date empty for some
    scheduled versions and puts the date in amendment_scheduled_enforcement_date instead."""
    return revision.get("amendment_enforcement_date") or revision.get("amendment_scheduled_enforcement_date")


def _amended_by(revision: dict) -> Optional[str]:
    title = revision.get("amendment_law_title")
    num = revision.get("amendment_law_num")
    if not title and not num:
        return None
    if not title:
        return f"{num} (e-Gov has no title for this amending law)"
    return f"{title}（{num}）" if num else title


# --- Revisions -------------------------------------------------------------

def get_revisions(client: EgovClient, law: str, limit=10) -> dict:
    limit = _clamp(limit, 10, 1, 50)
    resolved = resolve_law(client, law)
    key = resolved["key"]
    if LAW_REVISION_ID_RE.match(key):
        key = key.split("_", 1)[0]
    try:
        data = client.get(f"law_revisions/{key}")
    except EgovError as error:
        if error.status == 404:
            raise EgovError("law_not_found", f"e-Gov has no revision history for {law!r}.",
                            "Check the law ID or number with egov_law_search.",
                            status=404, api_code=error.api_code) from None
        raise
    info = data.get("law_info") or {}
    revisions = data.get("revisions") or []
    all_titles = {r.get("law_title") for r in revisions if r.get("law_title")} | {resolved.get("law_title")}
    rows = [_revision_row(r, sorted(t for t in all_titles if t)) for r in revisions]
    today = _today_jst()
    current_index = _pick_in_force(revisions, today)
    for index, row in enumerate(rows):
        if index == current_index:
            row["status"] = STATUS_LABELS["CurrentEnforced"]
        elif revisions[index].get("current_revision_status") == "CurrentEnforced":
            row["status"] = STATUS_LABELS["PreviousEnforced"]
    current = rows[current_index] if current_index is not None else None
    repealed_index = _repealed_index(revisions, today)
    repealed = rows[repealed_index] if repealed_index is not None else None
    upcoming_ids = {id(row) for row, r in zip(rows, revisions)
                    if r.get("current_revision_status") == "UnEnforced" or (_enforcement_date(r) or "") > today}
    upcoming = [row for row in rows if id(row) in upcoming_ids]
    for row in upcoming:
        row["status"] = ("repeal scheduled (not yet in force)" if row.get("change") == CHANGE_REPEAL
                         else STATUS_LABELS["UnEnforced"])
    for row, revision in zip(rows, revisions):  # stages of the same amending law already in force
        num = revision.get("amendment_law_num")
        if id(row) in upcoming_ids and num:
            done = sorted({_enforcement_date(r) for r2, r in zip(rows, revisions)
                           if id(r2) not in upcoming_ids and r.get("amendment_law_num") == num and _enforcement_date(r)})
            if done:
                row["steps_already_in_force"] = done
    upcoming.sort(key=lambda row: row.get("in_force_since") or "9999")  # soonest first
    earlier = [row for index, row in enumerate(rows)
               if id(row) not in upcoming_ids and index != current_index]  # newest first, as e-Gov sends them
    latest_title = (revisions[0].get("law_title") if revisions else None) or resolved.get("law_title")
    title = (current or {}).get("law_title") or latest_title
    for row in rows:
        if row.get("law_title") == title:
            row.pop("law_title", None)  # only keep a version's title when the law was renamed
    out = {
        "law_title": title,
        "law_num": info.get("law_num"),
        "law_id": info.get("law_id"),
        "promulgation_date": info.get("promulgation_date"),
        "next_amendment": upcoming[0] if upcoming else None,
        "scheduled_repeal": next((row for row in upcoming if row.get("change") == CHANGE_REPEAL), None),
        "scheduled_amendments": upcoming[:limit],
        "in_force_now": current,
        "repealed_on": (repealed or {}).get("in_force_since"),
        "earlier_versions": earlier[:limit],
        "total_versions": len(rows),
        "scope": ("Amendments already promulgated (公布) and recorded in e-Gov for this law only. Bills still in "
                  "the Diet and changes to its 施行令/施行規則 (separate laws) are not included; say so when you answer."),
        "note": ("scheduled_amendments: soonest first, not yet in force; next_amendment is the first of them. "
                 "change: amendment, repeal, or this law's own provisions taking effect. "
                 "title_names_this_law: whether the amending law's title names this law; follow_up_of: for a "
                 "law titled '〈X〉の施行に伴う…', the law X it follows up. Neither says how much an article "
                 "changes. To see one amendment's effect on an article, call egov_law_article with that row's "
                 "check arguments (as_of = the day before, compare_with = the day): one call returns changed "
                 "true/false and a diff. A repeal row's check has as_of only (the day before), which reads the "
                 "law's last wording. Amendments taking effect on the same day cannot be told apart. "
                 "date_fixed=false means the law does not state the date (see enforcement_note): in_force_since "
                 "is e-Gov's provisional date, for '…を超えない範囲内において政令で定める日' the latest possible "
                 "day (say 'by' that date, and it may come before other scheduled dates), for '…の施行の日' a "
                 "placeholder until the other law's date is set. A staged amendment appears once per step: steps "
                 "already in force are in earlier_versions and listed in steps_already_in_force. "
                 "earlier_versions: newest first."),
        "url": law_page_url(info.get("law_id") or ""),
        "source": _source(),
    }
    if repealed is None:
        out.pop("repealed_on")  # only present for a law whose repeal has taken effect
    messages = []
    if repealed is not None:
        last_day = (repealed.get("check") or {}).get("as_of")
        messages.append(f"This law was repealed on {repealed.get('in_force_since')}"
                        + (f" by {repealed['amended_by']}" if repealed.get("amended_by") else "")
                        + "; it is not in force.")
    elif current is None:
        own = next((row for row in upcoming if row.get("change") == CHANGE_OWN), None)
        messages.append("This law is not in force yet" + (f"; its provisions take effect on {own.get('in_force_since')}"
                                                          if own else "") + ".")
    if out["scheduled_repeal"]:
        messages.append(f"This law is scheduled to be repealed on {out['scheduled_repeal'].get('in_force_since')}.")
    if repealed is not None:
        out["next_step"] = ("Tell the user the law is repealed and not in force. "
                            + (f"To read its last wording, call egov_law_article with as_of='{last_day}' "
                               "(the day before the repeal took effect)." if last_day else
                               "Its last wording is older than e-Gov's versions (2017-04-01 onward)."))
    elif not upcoming:
        messages.append("No promulgated amendment of this law is waiting to take effect in e-Gov's data "
                        "(bills still in the Diet are not covered).")
        out["next_step"] = ("Answer that no amendment is scheduled. To see what a past amendment changed in an "
                            "article, call egov_law_article with that row's check arguments.")
    else:
        check = upcoming[0].get("check")
        if check and "compare_with" not in check:  # a scheduled repeal: there is no wording to compare with
            check = None
        out["next_step"] = ("To check whether the next amendment changes an article, call egov_law_article with "
                            + (f"as_of='{check['as_of']}', compare_with='{check['compare_with']}'" if check
                               else "compare_with=<its in_force_since>") + " (one call: changed + diff).")
    if messages:
        out["message"] = " ".join(messages)
    if len(upcoming) > limit or len(earlier) > limit:
        out["next_step"] += (f" Lists cut at limit={limit} ({len(upcoming)} scheduled, {len(earlier)} earlier); "
                             "raise limit (max 50) to see more.")
    return out


def _date_fixed(revision: dict) -> Optional[bool]:
    """False when the enforcement date is not written in the law (enforcement_note says how it will be
    set, e.g. 政令で定める日); e-Gov then shows a provisional date. None for versions already in force."""
    if revision.get("current_revision_status") != "UnEnforced":
        return None
    return not revision.get("amendment_enforcement_comment")


def _is_name_char(ch: str) -> bool:
    """Kanji or katakana (the whole katakana block, ・ and ー included): characters that can be part of
    a longer law name, so a title found right after one is not a word of its own."""
    code = ord(ch)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0x30A0 <= code <= 0x30FF or ch in "々〆"


def title_names_this_law(amending_title: str, law_titles) -> bool:
    """True when one of this law's titles (current or former) appears in the amending law's title as a
    word of its own: at the start, or right after a character that is not kanji or katakana.
    雇用保険法 does not name 保険法; ...のための国民年金法等... names 国民年金法.
    Says nothing about how much the law changes; compare articles for that."""
    amending = normalize_text(amending_title)
    for title in (normalize_text(t) for t in law_titles if t):
        start = amending.find(title)
        while title and start != -1:
            if start == 0 or not _is_name_char(amending[start - 1]):
                return True
            start = amending.find(title, start + 1)
    return False


_FOLLOW_UP_RE = re.compile(r"^(?P<base>.+?)の施行に伴う")


def follow_up_of(amending_title: str) -> Optional[str]:
    """For a 整備法 titled '〈X〉の施行に伴う…', the name X of the law whose start it follows."""
    match = _FOLLOW_UP_RE.match(str(amending_title or "").strip())
    return match.group("base") if match else None


def _revision_row(revision: dict, law_titles=()) -> dict:
    amending = revision.get("amendment_law_title")
    titles = list(law_titles) or [revision.get("law_title") or ""]
    change = _change_type(revision)
    row = {
        "in_force_since": _enforcement_date(revision),
        "status": _status(revision),
        "amended_by": _amended_by(revision),
        "change": change,
        "title_names_this_law": None if (change != "amendment" or not amending) else title_names_this_law(amending, titles),
        "follow_up_of": None if change != "amendment" else follow_up_of(amending),
        "amendment_promulgated": revision.get("amendment_promulgate_date"),
        "enforcement_note": revision.get("amendment_enforcement_comment"),
        "date_fixed": _date_fixed(revision),
        "law_title": revision.get("law_title"),
        "law_revision_id": revision.get("law_revision_id"),
        "check": (_check_dates(_enforcement_date(revision)) if change == "amendment" else
                  _last_day(_enforcement_date(revision)) if change == CHANGE_REPEAL else None),
    }
    return {k: v for k, v in row.items() if v is not None and v != ""}


CHANGE_OWN = "this law's own provisions take effect"
CHANGE_REPEAL = "repeal (廃止)"


def _change_type(revision: dict) -> str:
    """'amendment', a repeal, or this law's own provisions taking effect (enactment, or a later stage
    of its own provisions: e-Gov then records no amending law, law ID 000000000000000)."""
    if revision.get("repeal_status") == "Repeal" or revision.get("amendment_type") == "8":
        return CHANGE_REPEAL
    amending_id = str(revision.get("amendment_law_id") or "")
    if revision.get("amendment_type") == "1" or (not revision.get("amendment_law_title")
                                                 and (not amending_id or set(amending_id) == {"0"})):
        return CHANGE_OWN
    return "amendment"


def _last_day(date: Optional[str]) -> Optional[dict]:
    """For a repeal row: as_of for egov_law_article that reads the law's last wording (the day before)."""
    dates = _check_dates(date)
    return {"as_of": dates["as_of"]} if dates else None


def _check_dates(date: Optional[str]) -> Optional[dict]:
    """Arguments for egov_law_article that isolate this version's change: the day before vs the day."""
    if not date:
        return None
    try:
        before = (_dt.date.fromisoformat(date) - _dt.timedelta(days=1)).isoformat()
    except ValueError:
        return None
    if before < EARLIEST_AS_OF:
        return None
    return {"as_of": before, "compare_with": date}
