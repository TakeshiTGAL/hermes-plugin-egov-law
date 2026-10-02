"""Japanese legal numbering: kanji numerals, article references and law numbers.

Users and models write the same article many ways: 第32条, 32条, 三十二条,
第三十二条の二, 32の2, 32-2, "Article 32", 第32条第2項. This module turns all of
them into the element path the e-Gov API expects (Article_32_2, Paragraph_2).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

_KANJI_DIGITS = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                 "六": 6, "七": 7, "八": 8, "九": 9}
_KANJI_UNITS = {"十": 10, "百": 100, "千": 1000}
_NUM = r"(?:[0-9]+|[〇零一二三四五六七八九十百千]+)"


def kanji_to_int(text: str) -> int:
    """'三十二' -> 32, '百二' -> 102, '千百十一' -> 1111, '32' -> 32."""
    if text.isdigit():
        return int(text)
    total, current, last_was_digit = 0, 0, False
    for ch in text:
        if ch in _KANJI_DIGITS:
            digit = _KANJI_DIGITS[ch]
            current = current * 10 + digit if last_was_digit else digit
            last_was_digit = True
        elif ch in _KANJI_UNITS:
            total += (current or 1) * _KANJI_UNITS[ch]
            current, last_was_digit = 0, False
        else:
            raise ValueError(f"not a number: {text!r}")
    return total + current


def int_to_kanji(value: int) -> str:
    """49 -> '四十九', 22 -> '二十二', 120 -> '百二十', 1 -> '一' (as written in law numbers)."""
    if value <= 0 or value >= 10000:
        raise ValueError(f"out of range: {value}")
    digits = "〇一二三四五六七八九"
    out = []
    for unit_value, unit in ((1000, "千"), (100, "百"), (10, "十")):
        count, value = divmod(value, unit_value)
        if count:
            out.append(("" if count == 1 else digits[count]) + unit)
    if value:
        out.append(digits[value])
    return "".join(out)


def normalize_text(text: str) -> str:
    """NFKC + strip whitespace and quote brackets, for comparing names."""
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = re.sub(r"[\s「」『』\"']", "", text)
    return text


@dataclass(frozen=True)
class ArticleRef:
    numbers: List[int]          # [32] or [32, 2] for 第三十二条の二
    paragraph: Optional[int]    # 2 for 第2項

    @property
    def elm_article(self) -> str:
        return "Article_" + "_".join(str(n) for n in self.numbers)

    @property
    def label(self) -> str:
        head = f"第{int_to_kanji(self.numbers[0])}条"
        tail = "".join(f"の{int_to_kanji(n)}" for n in self.numbers[1:])
        para = f"第{int_to_kanji(self.paragraph)}項" if self.paragraph else ""
        return head + tail + para


_ARTICLE_RE = re.compile(
    # A paragraph needs 条 or 第 before it, so "第32項" is rejected instead of read as 第3条第2項.
    rf"^第?(?P<main>{_NUM})条?(?P<branches>(?:[の之\-_.]{_NUM})*)条?(?:(?:(?<=条)第?|第)(?P<para>{_NUM})項)?$"
)


def parse_article(text) -> ArticleRef:
    """Parse an article reference. Raises ValueError with a readable message."""
    if isinstance(text, int):
        text = str(text)
    raw = str(text or "")
    s = unicodedata.normalize("NFKC", raw).strip().lower()
    s = re.sub(r"^(article|art\.?|§)\s*", "", s)
    s = re.sub(r"\s+", "", s)
    match = _ARTICLE_RE.match(s)
    if not match:
        raise ValueError(
            f"Could not read the article number {raw!r}. Use a form like '第32条', '32', '三十二条', "
            "'第三十二条の二' or '32の2'."
        )
    numbers = [kanji_to_int(match.group("main"))]
    numbers += [kanji_to_int(n) for n in re.findall(_NUM, match.group("branches") or "")]
    if any(n <= 0 for n in numbers):
        raise ValueError(f"Article numbers start at 1, got {raw!r}.")
    para = match.group("para")
    return ArticleRef(numbers=numbers, paragraph=kanji_to_int(para) if para else None)


def parse_paragraph(value) -> Optional[int]:
    """'2', 2, '第2項', '二', '第二項' -> 2. Empty -> None."""
    if value is None or value == "":
        return None
    if isinstance(value, int):
        number = value
    else:
        s = unicodedata.normalize("NFKC", str(value)).strip()
        s = re.sub(r"^(paragraph|para\.?)\s*", "", s, flags=re.I)
        match = re.fullmatch(rf"第?({_NUM})項?", s)
        if not match:
            raise ValueError(f"Could not read the paragraph number {value!r}. Use a number like 2 or '第2項'.")
        number = kanji_to_int(match.group(1))
    if number <= 0:
        raise ValueError(f"Paragraph numbers start at 1, got {value!r}.")
    return number


_ERAS = "明治|大正|昭和|平成|令和"
_LAW_NUM_RE = re.compile(rf"^(?P<era>{_ERAS})(?P<year>元|{_NUM})年(?P<kind>.+?)第(?P<num>{_NUM})号$")
LAW_ID_RE = re.compile(r"^[0-9]{3}[A-Z0-9]{12}$")
LAW_REVISION_ID_RE = re.compile(r"^[0-9]{3}[A-Z0-9]{12}_[0-9]{8}_[A-Z0-9]{15}$")


def as_law_num(text: str) -> Optional[str]:
    """Return the canonical kanji law number for '昭和22年法律第49号' / '昭和二十二年法律第四十九号', else None."""
    s = normalize_text(text)
    match = _LAW_NUM_RE.match(s)
    if not match:
        return None
    year = match.group("year")
    year_value = 1 if year == "元" else kanji_to_int(year)
    year_kanji = "元" if year_value == 1 else int_to_kanji(year_value)  # e-Gov writes 令和元年, not 令和一年
    num_kanji = int_to_kanji(kanji_to_int(match.group("num")))
    return f"{match.group('era')}{year_kanji}年{match.group('kind')}第{num_kanji}号"
