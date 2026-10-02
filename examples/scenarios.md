# Recorded scenarios

Eight requests a Japanese developer's agent gets, run end to end. The agent was a separate Claude Opus 5.5 instance that saw only what Hermes shows a model: the deferred-tool catalog line per tool, and whatever `tool_describe` returned when it chose to call it (S1 and S8). Each request was handled as a new conversation, with a budget of 20 tool calls for all eight (it used 16). Every tool call went through Hermes's own dispatcher (`model_tools.handle_function_call`, Tool Search bridge active) with this plugin installed and enabled, against the live e-Gov API on 2026-10-02. The final answers are the agent's own text, unedited. Results are shown in full as returned. Recorded with an earlier build of this plugin; two wordings changed after it: `law_version.status` for a future `as_of` (S8 now reads "in force now (also the version on …)") and the `text_notes` sentence about 附則 that read an article (S4, S8).

## S1: Writing work rules: quote the statutory working hours

> 就業規則の『労働時間』の章を作っています。労基法の法定労働時間の条文（32条）を正確に引用したいので、条文を出して。

**Call 1** `tool_describe`

```json
{"names": ["egov_law_article"]}
```

Result: the full schemas of egov_law_article (omitted here).

**Call 2** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "労基法", "article": "32"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "article": "第三十二条",
 "caption": "（労働時間）",
 "text": "（労働時間）\n第三十二条　使用者は、労働者に、休憩時間を除き一週間について四十時間を超えて、労働させてはならない。\n２　使用者は、一週間の各日については、労働者に、休憩時間を除き一日について八時間を超えて、労働させてはならない。",
 "paragraphs": 2,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-07-17",
  "status": "in force now",
  "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060"
 },
 "as_of": "2026-10-02",
 "resolved_by": "abbreviation",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 }
}
```

Tool calls: 2.

Final answer written by the agent:

> 労働基準法第32条（労働時間）の条文です。本日（2026-10-02）時点で施行されている文言です。
>
> （労働時間）
> 第三十二条　使用者は、労働者に、休憩時間を除き一週間について四十時間を超えて、労働させてはならない。
> ２　使用者は、一週間の各日については、労働者に、休憩時間を除き一日について八時間を超えて、労働させてはならない。
>
> - 法令番号: 昭和二十二年法律第四十九号
> - 法令全体の最新版は 2026-07-17 施行（労働者災害補償保険法等の一部を改正する法律〔令和八年法律第六十号〕による改正）です。これは法令全体の版の日付で、第32条がこの改正で変わったという意味ではありません。
> - e-Gov: https://laws.e-gov.go.jp/law/322AC0000000049
>
> 就業規則に引くときは「第1項＝週40時間」「第2項＝1日8時間」と項を分けると、変形労働時間制など例外の条項と対応させやすくなります。
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S2: Contract review: check the Civil Code provision on damages

> 業務委託契約書をレビュー中です。損害賠償の条項が民法のどの規定に沿っているか確かめたいので、民法第四百十五条の条文を見せてください。

**Call 1** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "民法", "article": "第四百十五条"}}]}
```

Result:

```json
{
 "law_title": "民法",
 "law_num": "明治二十九年法律第八十九号",
 "law_id": "129AC0000000089",
 "article": "第四百十五条",
 "caption": "（債務不履行による損害賠償）",
 "text": "（債務不履行による損害賠償）\n第四百十五条　債務者がその債務の本旨に従った履行をしないとき又は債務の履行が不能であるときは、債権者は、これによって生じた損害の賠償を請求することができる。ただし、その債務の不履行が契約その他の債務の発生原因及び取引上の社会通念に照らして債務者の責めに帰することができない事由によるものであるときは、この限りでない。\n２　前項の規定により損害賠償の請求をすることができる場合において、債権者は、次に掲げるときは、債務の履行に代わる損害賠償の請求をすることができる。\n　一　債務の履行が不能であるとき。\n　二　債務者がその債務の履行を拒絶する意思を明確に表示したとき。\n　三　債務が契約によって生じたものである場合において、その契約が解除され、又は債務の不履行による契約の解除権が発生したとき。",
 "paragraphs": 2,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-06-24",
  "status": "in force now",
  "last_amended_by": "民法等の一部を改正する法律（令和八年法律第四十五号）",
  "law_revision_id": "129AC0000000089_20260624_508AC0000000045"
 },
 "as_of": "2026-10-02",
 "resolved_by": "exact title",
 "url": "https://laws.e-gov.go.jp/law/129AC0000000089",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 }
}
```

Tool calls: 1.

Final answer written by the agent:

> 民法第415条（債務不履行による損害賠償）の条文です。本日（2026-10-02）時点で施行されている文言です。
>
> （債務不履行による損害賠償）
> 第四百十五条　債務者がその債務の本旨に従った履行をしないとき又は債務の履行が不能であるときは、債権者は、これによって生じた損害の賠償を請求することができる。ただし、その債務の不履行が契約その他の債務の発生原因及び取引上の社会通念に照らして債務者の責めに帰することができない事由によるものであるときは、この限りでない。
> ２　前項の規定により損害賠償の請求をすることができる場合において、債権者は、次に掲げるときは、債務の履行に代わる損害賠償の請求をすることができる。
> 　一　債務の履行が不能であるとき。
> 　二　債務者がその債務の履行を拒絶する意思を明確に表示したとき。
> 　三　債務が契約によって生じたものである場合において、その契約が解除され、又は債務の不履行による契約の解除権が発生したとき。
>
> 契約書の損害賠償条項と照らし合わせるときは、次の3点を見てください。
> 1. 帰責事由: 第1項ただし書により、債務者の責めに帰することができない事由なら責任を負いません。契約書が「故意又は重過失に限る」などと絞っていれば、民法より債務者に有利な特約です。
> 2. 履行に代わる損害賠償: 第2項の3つの場合に請求できます。契約書の解除条項とつながっているか確かめてください。
> 3. 賠償の範囲: 第415条は請求できるかどうかの根拠です。どこまで賠償するかは第416条の範囲です。上限額の特約や予定賠償額（第420条）があるかも確認してください。必要なら第416条・第420条も出します。
>
> 法令番号: 明治二十九年法律第八十九号。e-Gov: https://laws.e-gov.go.jp/law/129AC0000000089
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S3: Amendment check: when does the next change take effect

> 個人情報保護法、次の改正はいつ施行されますか？

**Call 1** `tool_call`

```json
{"calls": [{"name": "egov_law_revisions", "arguments": {"law": "個人情報保護法"}}]}
```

Result:

```json
{
 "law_title": "個人情報の保護に関する法律",
 "law_num": "平成十五年法律第五十七号",
 "law_id": "415AC0000000057",
 "promulgation_date": "2003-05-30",
 "next_amendment": {
  "in_force_since": "2026-11-02",
  "status": "not yet in force (scheduled)",
  "amended_by": "防災庁設置法の施行に伴う関係法律の整備等に関する法律（令和八年法律第六十二号）",
  "change": "amendment",
  "title_names_this_law": false,
  "follow_up_of": "防災庁設置法",
  "amendment_promulgated": "2026-07-17",
  "date_fixed": true,
  "law_revision_id": "415AC0000000057_20261102_508AC0000000062",
  "check": {
   "as_of": "2026-11-01",
   "compare_with": "2026-11-02"
  },
  "steps_already_in_force": [
   "2026-07-17"
  ]
 },
 "scheduled_repeal": null,
 "scheduled_amendments": [
  {
   "in_force_since": "2026-11-02",
   "status": "not yet in force (scheduled)",
   "amended_by": "防災庁設置法の施行に伴う関係法律の整備等に関する法律（令和八年法律第六十二号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "防災庁設置法",
   "amendment_promulgated": "2026-07-17",
   "date_fixed": true,
   "law_revision_id": "415AC0000000057_20261102_508AC0000000062",
   "check": {
    "as_of": "2026-11-01",
    "compare_with": "2026-11-02"
   },
   "steps_already_in_force": [
    "2026-07-17"
   ]
  },
  {
   "in_force_since": "2027-01-17",
   "status": "not yet in force (scheduled)",
   "amended_by": "個人情報の保護に関する法律等の一部を改正する法律（令和八年法律第五十六号）",
   "change": "amendment",
   "title_names_this_law": true,
   "amendment_promulgated": "2026-07-17",
   "date_fixed": true,
   "law_revision_id": "415AC0000000057_20270117_508AC0000000056",
   "check": {
    "as_of": "2027-01-16",
    "compare_with": "2027-01-17"
   },
   "steps_already_in_force": [
    "2026-07-17"
   ]
  },
  {
   "in_force_since": "2027-04-01",
   "status": "not yet in force (scheduled)",
   "amended_by": "出入国管理及び難民認定法及び外国人の技能実習の適正な実施及び技能実習生の保護に関する法律の一部を改正する法律（令和六年法律第六十号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2024-06-21",
   "date_fixed": true,
   "law_revision_id": "415AC0000000057_20270401_506AC0000000060",
   "check": {
    "as_of": "2027-03-31",
    "compare_with": "2027-04-01"
   }
  },
  {
   "in_force_since": "2027-04-16",
   "status": "not yet in force (scheduled)",
   "amended_by": "科学技術・イノベーション創出の活性化に関する法律の一部を改正する法律（令和八年法律第五十九号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2026-07-17",
   "enforcement_note": "公布の日から起算して九月を超えない範囲内において政令で定める日",
   "date_fixed": false,
   "law_revision_id": "415AC0000000057_20270416_508AC0000000059",
   "check": {
    "as_of": "2027-04-15",
    "compare_with": "2027-04-16"
   }
  },
  {
   "in_force_since": "2028-07-16",
   "status": "not yet in force (scheduled)",
   "amended_by": "個人情報の保護に関する法律等の一部を改正する法律（令和八年法律第五十六号）",
   "change": "amendment",
   "title_names_this_law": true,
   "amendment_promulgated": "2026-07-17",
   "enforcement_note": "公布の日から起算して二年を超えない範囲内において政令で定める日",
   "date_fixed": false,
   "law_revision_id": "415AC0000000057_20280716_508AC0000000056",
   "check": {
    "as_of": "2028-07-15",
    "compare_with": "2028-07-16"
   },
   "steps_already_in_force": [
    "2026-07-17"
   ]
  },
  {
   "in_force_since": "2028-12-23",
   "status": "not yet in force (scheduled)",
   "amended_by": "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法等の一部を改正する法律",
   "amendment_promulgated": "2026-06-24",
   "enforcement_note": "民法等の一部を改正する法律（令和八年法律第四十五号）の施行の日",
   "date_fixed": false,
   "law_revision_id": "415AC0000000057_20281223_508AC0000000046",
   "check": {
    "as_of": "2028-12-22",
    "compare_with": "2028-12-23"
   },
   "steps_already_in_force": [
    "2026-06-24"
   ]
  }
 ],
 "in_force_now": {
  "in_force_since": "2026-10-01",
  "status": "in force now",
  "amended_by": "日本学術会議法（令和七年法律第七十号）",
  "change": "amendment",
  "title_names_this_law": false,
  "amendment_promulgated": "2025-06-18",
  "law_revision_id": "415AC0000000057_20261001_507AC0000000070",
  "check": {
   "as_of": "2026-09-30",
   "compare_with": "2026-10-01"
  }
 },
 "earlier_versions": [
  {
   "in_force_since": "2026-07-17",
   "status": "superseded (older version)",
   "amended_by": "防災庁設置法の施行に伴う関係法律の整備等に関する法律（令和八年法律第六十二号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "防災庁設置法",
   "amendment_promulgated": "2026-07-17",
   "law_revision_id": "415AC0000000057_20260717_508AC0000000062",
   "check": {
    "as_of": "2026-07-16",
    "compare_with": "2026-07-17"
   }
  },
  {
   "in_force_since": "2026-07-17",
   "status": "superseded (older version)",
   "amended_by": "個人情報の保護に関する法律等の一部を改正する法律（令和八年法律第五十六号）",
   "change": "amendment",
   "title_names_this_law": true,
   "amendment_promulgated": "2026-07-17",
   "law_revision_id": "415AC0000000057_20260717_508AC0000000056",
   "check": {
    "as_of": "2026-07-16",
    "compare_with": "2026-07-17"
   }
  },
  {
   "in_force_since": "2026-06-24",
   "status": "superseded (older version)",
   "amended_by": "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法等の一部を改正する法律",
   "amendment_promulgated": "2026-06-24",
   "law_revision_id": "415AC0000000057_20260624_508AC0000000046",
   "check": {
    "as_of": "2026-06-23",
    "compare_with": "2026-06-24"
   }
  },
  {
   "in_force_since": "2026-05-21",
   "status": "superseded (older version)",
   "amended_by": "民事訴訟法等の一部を改正する法律（令和四年法律第四十八号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2022-05-25",
   "law_revision_id": "415AC0000000057_20260521_504AC0000000048",
   "check": {
    "as_of": "2026-05-20",
    "compare_with": "2026-05-21"
   }
  },
  {
   "in_force_since": "2025-06-01",
   "status": "superseded (older version)",
   "amended_by": "刑法等の一部を改正する法律の施行に伴う関係法律の整理等に関する法律　抄（令和四年法律第六十八号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "刑法等の一部を改正する法律",
   "amendment_promulgated": "2022-06-17",
   "law_revision_id": "415AC0000000057_20250601_504AC0000000068",
   "check": {
    "as_of": "2025-05-31",
    "compare_with": "2025-06-01"
   }
  },
  {
   "in_force_since": "2025-04-01",
   "status": "superseded (older version)",
   "amended_by": "情報通信技術の活用による行政手続等に係る関係者の利便性の向上並びに行政運営の簡素化及び効率化を図るためのデジタル社会形成基本法等の一部を改正する法律（令和六年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2024-06-07",
   "law_revision_id": "415AC0000000057_20250401_506AC0000000046",
   "check": {
    "as_of": "2025-03-31",
    "compare_with": "2025-04-01"
   }
  },
  {
   "in_force_since": "2025-04-01",
   "status": "superseded (older version)",
   "amended_by": "国立健康危機管理研究機構法の施行に伴う関係法律の整備に関する法律（令和五年法律第四十七号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "国立健康危機管理研究機構法",
   "amendment_promulgated": "2023-06-07",
   "law_revision_id": "415AC0000000057_20250401_505AC0000000047",
   "check": {
    "as_of": "2025-03-31",
    "compare_with": "2025-04-01"
   }
  },
  {
   "in_force_since": "2024-04-01",
   "status": "superseded (older version)",
   "amended_by": "金融商品取引法等の一部を改正する法律（令和五年法律第七十九号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2023-11-29",
   "law_revision_id": "415AC0000000057_20240401_505AC0000000079",
   "check": {
    "as_of": "2024-03-31",
    "compare_with": "2024-04-01"
   }
  },
  {
   "in_force_since": "2024-02-16",
   "status": "superseded (older version)",
   "amended_by": "脱炭素成長型経済構造への円滑な移行の推進に関する法律（令和五年法律第三十二号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2023-05-19",
   "law_revision_id": "415AC0000000057_20240216_505AC0000000032",
   "check": {
    "as_of": "2024-02-15",
    "compare_with": "2024-02-16"
   }
  },
  {
   "in_force_since": "2024-02-01",
   "status": "superseded (older version)",
   "amended_by": "金融商品取引法等の一部を改正する法律（令和五年法律第七十九号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2023-11-29",
   "law_revision_id": "415AC0000000057_20240201_505AC0000000079",
   "check": {
    "as_of": "2024-01-31",
    "compare_with": "2024-02-01"
   }
  }
 ],
 "total_versions": 35,
 "scope": "Amendments already promulgated (公布) and recorded in e-Gov for this law only. Bills still in the Diet and changes to its 施行令/施行規則 (separate laws) are not included; say so when you answer.",
 "note": "scheduled_amendments: soonest first, not yet in force; next_amendment is the first of them. change: amendment, repeal, or this law's own provisions taking effect. title_names_this_law: whether the amending law's title names this law; follow_up_of: for a law titled '〈X〉の施行に伴う…', the law X it follows up. Neither says how much an article changes. To see one amendment's effect on an article, call egov_law_article with that row's check arguments (as_of = the day before, compare_with = the day): one call returns changed true/false and a diff. Amendments taking effect on the same day cannot be told apart. date_fixed=false means the law does not state the date (see enforcement_note): in_force_since is e-Gov's provisional date, for '…を超えない範囲内において政令で定める日' the latest possible day (say 'by' that date, and it may come before other scheduled dates), for '…の施行の日' a placeholder until the other law's date is set. A staged amendment appears once per step: steps already in force are in earlier_versions and listed in steps_already_in_force. earlier_versions: newest first.",
 "url": "https://laws.e-gov.go.jp/law/415AC0000000057",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "next_step": "To check whether the next amendment changes an article, call egov_law_article with as_of='2026-11-01', compare_with='2026-11-02' (one call: changed + diff). Lists cut at limit=10 (6 scheduled, 28 earlier); raise limit (max 50) to see more."
}
```

Tool calls: 1.

Final answer written by the agent:

> 個人情報保護法（個人情報の保護に関する法律）の次の改正は 2026年11月2日に施行されます（日付は確定）。ただし、これは防災庁設置法の施行に伴う関係法律の整備法（令和八年法律第六十二号）による改正です。法律の題名に個人情報保護法の名前はなく、他の法律の新設に合わせた改正です。
>
> 個人情報保護法そのものを改正する法律（個人情報の保護に関する法律等の一部を改正する法律、令和八年法律第五十六号、2026-07-17 公布）は段階的に施行されます。
> - 2027年1月17日: 施行（日付は確定）
> - 2028年7月16日までに: 残りの部分を施行（「公布の日から起算して二年を超えない範囲内において政令で定める日」なので、これより早まる可能性があります）
> - なお、この法律の一部はすでに 2026-07-17 に施行されています
>
> ほかに予定されている改正（いずれも他の法律に伴う改正）:
> - 2027年4月1日: 出入国管理及び難民認定法等の一部を改正する法律（令和六年法律第六十号）
> - 2027年4月16日までに: 科学技術・イノベーション創出の活性化に関する法律の一部を改正する法律（令和八年法律第五十九号）。政令で日付が決まります
> - 民法等の一部を改正する法律（令和八年法律第四十五号）の施行の日: 民法等改正の施行に伴う整備法（令和八年法律第四十六号）による改正。e-Gov は暫定で 2028-12-23 と表示していますが、日付はまだ決まっていません
>
> 注意: この一覧は、すでに公布され e-Gov に登録された改正だけです。国会に出ている法案や、施行令・施行規則の改正は入っていません。特定の条文がどの改正でどう変わるかは、条文ごとに新旧を比べて確認できます。
>
> e-Gov: https://laws.e-gov.go.jp/law/415AC0000000057
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S4: Asking by topic: annual paid leave

> 年次有給休暇の付与日数を定めている条文はどれ？条文も見たい。

**Call 1** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "労働基準法", "article": "39"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "article": "第三十九条",
 "caption": "（年次有給休暇）",
 "text": "（年次有給休暇）\n第三十九条　使用者は、その雇入れの日から起算して六箇月間継続勤務し全労働日の八割以上出勤した労働者に対して、継続し、又は分割した十労働日の有給休暇を与えなければならない。\n２　使用者は、一年六箇月以上継続勤務した労働者に対しては、雇入れの日から起算して六箇月を超えて継続勤務する日（以下「六箇月経過日」という。）から起算した継続勤務年数一年ごとに、前項の日数に、次の表の上欄に掲げる六箇月経過日から起算した継続勤務年数の区分に応じ同表の下欄に掲げる労働日を加算した有給休暇を与えなければならない。ただし、継続勤務した期間を六箇月経過日から一年ごとに区分した各期間（最後に一年未満の期間を生じたときは、当該期間）の初日の前日の属する期間において出勤した日数が全労働日の八割未満である者に対しては、当該初日以後の一年間においては有給休暇を与えることを要しない。\n　六箇月経過日から起算した継続勤務年数｜労働日\n　一年｜一労働日\n　二年｜二労働日\n　三年｜四労働日\n　四年｜六労働日\n　五年｜八労働日\n　六年以上｜十労働日\n３　次に掲げる労働者（一週間の所定労働時間が厚生労働省令で定める時間以上の者を除く。）の有給休暇の日数については、前二項の規定にかかわらず、これらの規定による有給休暇の日数を基準とし、通常の労働者の一週間の所定労働日数として厚生労働省令で定める日数（第一号において「通常の労働者の週所定労働日数」という。）と当該労働者の一週間の所定労働日数又は一週間当たりの平均所定労働日数との比率を考慮して厚生労働省令で定める日数とする。\n　一　一週間の所定労働日数が通常の労働者の週所定労働日数に比し相当程度少ないものとして厚生労働省令で定める日数以下の労働者\n　二　週以外の期間によつて所定労働日数が定められている労働者については、一年間の所定労働日数が、前号の厚生労働省令で定める日数に一日を加えた日数を一週間の所定労働日数とする労働者の一年間の所定労働日数その他の事情を考慮して厚生労働省令で定める日数以下の労働者\n４　使用者は、当該事業場に、労働者の過半数で組織する労働組合があるときはその労働組合、労働者の過半数で組織する労働組合がないときは労働者の過半数を代表する者との書面による協定により、次に掲げる事項を定めた場合において、第一号に掲げる労働者の範囲に属する労働者が有給休暇を時間を単位として請求したときは、前三項の規定による有給休暇の日数のうち第二号に掲げる日数については、これらの規定にかかわらず、当該協定で定めるところにより時間を単位として有給休暇を与えることができる。\n　一　時間を単位として有給休暇を与えることができることとされる労働者の範囲\n　二　時間を単位として与えることができることとされる有給休暇の日数（五日以内に限る。）\n　三　その他厚生労働省令で定める事項\n５　使用者は、前各項の規定による有給休暇を労働者の請求する時季に与えなければならない。ただし、請求された時季に有給休暇を与えることが事業の正常な運営を妨げる場合においては、他の時季にこれを与えることができる。\n６　使用者は、当該事業場に、労働者の過半数で組織する労働組合がある場合においてはその労働組合、労働者の過半数で組織する労働組合がない場合においては労働者の過半数を代表する者との書面による協定により、第一項から第三項までの規定による有給休暇を与える時季に関する定めをしたときは、これらの規定による有給休暇の日数のうち五日を超える部分については、前項の規定にかかわらず、その定めにより有給休暇を与えることができる。\n７　使用者は、第一項から第三項までの規定による有給休暇（これらの規定により使用者が与えなければならない有給休暇の日数が十労働日以上である労働者に係るものに限る。以下この項及び次項において同じ。）の日数のうち五日については、基準日（継続勤務した期間を六箇月経過日から一年ごとに区分した各期間（最後に一年未満の期間を生じたときは、当該期間）の初日をいう。以下この項において同じ。）から一年以内の期間に、労働者ごとにその時季を定めることにより与えなければならない。ただし、第一項から第三項までの規定による有給休暇を当該有給休暇に係る基準日より前の日から与えることとしたときは、厚生労働省令で定めるところにより、労働者ごとにその時季を定めることにより与えなければならない。\n８　前項の規定にかかわらず、第五項又は第六項の規定により第一項から第三項までの規定による有給休暇を与えた場合においては、当該与えた有給休暇の日数（当該日数が五日を超える場合には、五日とする。）分については、時季を定めることにより与えることを要しない。\n９　使用者は、第一項から第三項までの規定による有給休暇の期間又は第四項の規定による有給休暇の時間については、就業規則その他これに準ずるもので定めるところにより、それぞれ、平均賃金若しくは所定労働時間労働した場合に支払われる通常の賃金又はこれらの額を基準として厚生労働省令で定めるところにより算定した額の賃金を支払わなければならない。ただし、当該事業場に、労働者の過半数で組織する労働組合がある場合においてはその労働組合、労働者の過半数で組織する労働組合がない場合においては労働者の過半数を代表する者との書面による協定により、その期間又はその時間について、それぞれ、健康保険法（大正十一年法律第七十号）第四十条第一項に規定する標準報酬月額の三十分の一に相当する金額（その金額に、五円未満の端数があるときは、これを切り捨て、五円以上十円未満の端数があるときは、これを十円に切り上げるものとする。）又は当該金額を基準として厚生労働省令で定めるところにより算定した金額を支払う旨を定めたときは、これによらなければならない。\n１０　労働者が業務上負傷し、又は疾病にかかり療養のために休業した期間及び育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律第二条第一号に規定する育児休業又は同条第二号に規定する介護休業をした期間並びに産前産後の女性が第六十五条の規定によつて休業した期間は、第一項及び第二項の規定の適用については、これを出勤したものとみなす。",
 "paragraphs": 10,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-07-17",
  "status": "in force now",
  "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060"
 },
 "as_of": "2026-10-02",
 "resolved_by": "exact title",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "text_notes": "This article contains a table, flattened to one row per line with ｜ between cells. Tables with multi-row headers do not line up column by column. 附則第百三十四条・附則第百三十五条 of this law's 附則 changes how this article applies for the time being (…の規定の適用については…). Read it with article='附則第百三十四条' before answering; the wording above alone may not be what applies today. (Notes, not part of the law text.)"
}
```

**Call 2** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "労働基準法", "article": "附則第百三十四条"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "article": "附則第百三十四条",
 "provision": "附則: the law's own supplementary provisions (including articles inserted later, such as 労基法 附則第143条); the separate 附則 of each amending law is not included",
 "text": "第百三十四条　常時三百人以下の労働者を使用する事業に係る第三十九条の規定の適用については、昭和六十六年三月三十一日までの間は同条第一項中「十労働日」とあるのは「六労働日」と、同年四月一日から昭和六十九年三月三十一日までの間は同項中「十労働日」とあるのは「八労働日」とする。",
 "paragraphs": 1,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-07-17",
  "status": "in force now",
  "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060"
 },
 "as_of": "2026-10-02",
 "resolved_by": "exact title",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 }
}
```

**Call 3** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "労働基準法", "article": "附則第百三十五条"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "article": "附則第百三十五条",
 "provision": "附則: the law's own supplementary provisions (including articles inserted later, such as 労基法 附則第143条); the separate 附則 of each amending law is not included",
 "text": "第百三十五条　六箇月経過日から起算した継続勤務年数が四年から八年までのいずれかの年数に達する日の翌日が平成十一年四月一日から平成十二年三月三十一日までの間にある労働者に関する第三十九条の規定の適用については、同日までの間は、次の表の上欄に掲げる当該六箇月経過日から起算した継続勤務年数の区分に応じ、同条第二項の表中次の表の中欄に掲げる字句は、同表の下欄に掲げる字句とする。\n　四年｜六労働日｜五労働日\n　五年｜八労働日｜六労働日\n　六年｜十労働日｜七労働日\n　七年｜十労働日｜八労働日\n　八年｜十労働日｜九労働日\n２　六箇月経過日から起算した継続勤務年数が五年から七年までのいずれかの年数に達する日の翌日が平成十二年四月一日から平成十三年三月三十一日までの間にある労働者に関する第三十九条の規定の適用については、平成十二年四月一日から平成十三年三月三十一日までの間は、次の表の上欄に掲げる当該六箇月経過日から起算した継続勤務年数の区分に応じ、同条第二項の表中次の表の中欄に掲げる字句は、同表の下欄に掲げる字句とする。\n　五年｜八労働日｜七労働日\n　六年｜十労働日｜八労働日\n　七年｜十労働日｜九労働日\n３　前二項の規定は、第七十二条に規定する未成年者については、適用しない。",
 "paragraphs": 3,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-07-17",
  "status": "in force now",
  "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060"
 },
 "as_of": "2026-10-02",
 "resolved_by": "exact title",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "text_notes": "This article contains a table, flattened to one row per line with ｜ between cells. Tables with multi-row headers do not line up column by column. (Notes, not part of the law text.)"
}
```

Tool calls: 3.

Final answer written by the agent:

> 年次有給休暇の付与日数を定めているのは、労働基準法第39条（年次有給休暇）の第1項〜第3項です。
>
> - 第1項: 雇入れから6か月継続勤務し、全労働日の8割以上出勤した労働者に 10労働日
> - 第2項: その後1年ごとの加算日数（表）
> - 第3項: 週の所定労働日数が少ない労働者（パートなど）の比例付与。日数そのものは厚生労働省令（労働基準法施行規則の第24条の3）で定められています。施行規則は今回取得していません。必要なら出します
>
> 条文（第1項〜第3項。本日 2026-10-02 時点で施行されている文言）:
>
> 第三十九条　使用者は、その雇入れの日から起算して六箇月間継続勤務し全労働日の八割以上出勤した労働者に対して、継続し、又は分割した十労働日の有給休暇を与えなければならない。
> ２　使用者は、一年六箇月以上継続勤務した労働者に対しては、雇入れの日から起算して六箇月を超えて継続勤務する日（以下「六箇月経過日」という。）から起算した継続勤務年数一年ごとに、前項の日数に、次の表の上欄に掲げる六箇月経過日から起算した継続勤務年数の区分に応じ同表の下欄に掲げる労働日を加算した有給休暇を与えなければならない。ただし、継続勤務した期間を六箇月経過日から一年ごとに区分した各期間（最後に一年未満の期間を生じたときは、当該期間）の初日の前日の属する期間において出勤した日数が全労働日の八割未満である者に対しては、当該初日以後の一年間においては有給休暇を与えることを要しない。
> 　六箇月経過日から起算した継続勤務年数｜労働日
> 　一年｜一労働日
> 　二年｜二労働日
> 　三年｜四労働日
> 　四年｜六労働日
> 　五年｜八労働日
> 　六年以上｜十労働日
> ３　次に掲げる労働者（一週間の所定労働時間が厚生労働省令で定める時間以上の者を除く。）の有給休暇の日数については、前二項の規定にかかわらず、これらの規定による有給休暇の日数を基準とし、通常の労働者の一週間の所定労働日数として厚生労働省令で定める日数（第一号において「通常の労働者の週所定労働日数」という。）と当該労働者の一週間の所定労働日数又は一週間当たりの平均所定労働日数との比率を考慮して厚生労働省令で定める日数とする。
> 　一　一週間の所定労働日数が通常の労働者の週所定労働日数に比し相当程度少ないものとして厚生労働省令で定める日数以下の労働者
> 　二　週以外の期間によつて所定労働日数が定められている労働者については、一年間の所定労働日数が、前号の厚生労働省令で定める日数に一日を加えた日数を一週間の所定労働日数とする労働者の一年間の所定労働日数その他の事情を考慮して厚生労働省令で定める日数以下の労働者
>
> 第1項の10日と第2項の表の加算日数を足すと、付与日数は勤続6か月で10日、1年6か月で11日、2年6か月で12日、3年6か月で14日、4年6か月で16日、5年6か月で18日、6年6か月以上で20日になります。
>
> 補足: 労基法附則第134条・第135条には第39条の日数を読み替える経過措置があります。ただし期限は昭和69年3月31日と平成13年3月31日で、どちらもすでに過ぎています。いまは第39条の本文どおりに適用されます。第39条にはこのほか、時間単位年休（第4項）、時季指定権（第5項）、計画的付与（第6項）、年5日の時季指定義務（第7項）なども定められています。
>
> 法令番号: 昭和二十二年法律第四十九号。e-Gov: https://laws.e-gov.go.jp/law/322AC0000000049
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S5: A full official title

> 地方公務員の育休の法律で、育児休業の承認を定めた第2条を見せて。

**Call 1** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "地方公務員の育児休業等に関する法律", "article": "2"}}]}
```

Result:

```json
{
 "law_title": "地方公務員の育児休業等に関する法律",
 "law_num": "平成三年法律第百十号",
 "law_id": "403AC0000000110",
 "article": "第二条",
 "caption": "（育児休業の承認）",
 "text": "（育児休業の承認）\n第二条　職員（第十八条第一項の規定により採用された同項に規定する短時間勤務職員、臨時的に任用される職員その他その任用の状況がこれらに類する職員として条例で定める職員を除く。）は、任命権者（地方公務員法第六条第一項に規定する任命権者及びその委任を受けた者をいう。以下同じ。）の承認を受けて、当該職員の子（民法（明治二十九年法律第八十九号）第八百十七条の二第一項の規定により職員が当該職員との間における同項に規定する特別養子縁組の成立について家庭裁判所に請求した者（当該請求に係る家事審判事件が裁判所に係属している場合に限る。）であって、当該職員が現に監護するもの、児童福祉法（昭和二十二年法律第百六十四号）第二十七条第一項第三号の規定により同法第六条の四第二号に規定する養子縁組里親である職員に委託されている児童その他これらに準ずる者として条例で定める者を含む。以下同じ。）を養育するため、当該子が三歳に達する日（非常勤職員にあっては、当該子の養育の事情に応じ、一歳に達する日から一歳六か月に達する日までの間で条例で定める日（当該子の養育の事情を考慮して特に必要と認められる場合として条例で定める場合に該当するときは、二歳に達する日））まで、育児休業をすることができる。ただし、当該子について、既に二回の育児休業（次に掲げる育児休業を除く。）をしたことがあるときは、条例で定める特別の事情がある場合を除き、この限りでない。\n　一　子の出生の日から国家公務員の育児休業等に関する法律（平成三年法律第百九号。以下「国家公務員育児休業法」という。）第三条第一項第一号の規定により人事院規則で定める期間を基準として条例で定める期間内に、職員（当該期間内に労働基準法（昭和二十二年法律第四十九号）第六十五条第二項の規定により勤務しない職員を除く。）が当該子についてする育児休業（次号に掲げる育児休業を除く。）のうち最初のもの及び二回目のもの\n　二　任期を定めて採用された職員が当該任期の末日を育児休業の期間の末日としてする育児休業（当該職員が、当該任期を更新され、又は当該任期の満了後引き続いて任命権者を同じくする職に採用されることに伴い、当該育児休業に係る子について、当該更新前の任期の末日の翌日又は当該採用の日を育児休業の期間の初日とする育児休業をする場合に限る。）\n２　育児休業の承認を受けようとする職員は、育児休業をしようとする期間の初日及び末日を明らかにして、任命権者に対し、その承認を請求するものとする。\n３　任命権者は、前項の規定による請求があったときは、当該請求に係る期間について当該請求をした職員の業務を処理するための措置を講ずることが著しく困難である場合を除き、これを承認しなければならない。",
 "paragraphs": 3,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2025-10-01",
  "status": "in force now",
  "last_amended_by": "地方公務員の育児休業等に関する法律の一部を改正する法律（令和七年法律第五号）",
  "law_revision_id": "403AC0000000110_20251001_507AC0000000005"
 },
 "as_of": "2026-10-02",
 "resolved_by": "exact title",
 "url": "https://laws.e-gov.go.jp/law/403AC0000000110",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 }
}
```

Tool calls: 1.

Final answer written by the agent:

> 地方公務員の育児休業等に関する法律（平成三年法律第百十号）第2条（育児休業の承認）です。本日（2026-10-02）時点で施行されている文言です。
>
> （育児休業の承認）
> 第二条　職員（第十八条第一項の規定により採用された同項に規定する短時間勤務職員、臨時的に任用される職員その他その任用の状況がこれらに類する職員として条例で定める職員を除く。）は、任命権者（地方公務員法第六条第一項に規定する任命権者及びその委任を受けた者をいう。以下同じ。）の承認を受けて、当該職員の子（民法（明治二十九年法律第八十九号）第八百十七条の二第一項の規定により職員が当該職員との間における同項に規定する特別養子縁組の成立について家庭裁判所に請求した者（当該請求に係る家事審判事件が裁判所に係属している場合に限る。）であって、当該職員が現に監護するもの、児童福祉法（昭和二十二年法律第百六十四号）第二十七条第一項第三号の規定により同法第六条の四第二号に規定する養子縁組里親である職員に委託されている児童その他これらに準ずる者として条例で定める者を含む。以下同じ。）を養育するため、当該子が三歳に達する日（非常勤職員にあっては、当該子の養育の事情に応じ、一歳に達する日から一歳六か月に達する日までの間で条例で定める日（当該子の養育の事情を考慮して特に必要と認められる場合として条例で定める場合に該当するときは、二歳に達する日））まで、育児休業をすることができる。ただし、当該子について、既に二回の育児休業（次に掲げる育児休業を除く。）をしたことがあるときは、条例で定める特別の事情がある場合を除き、この限りでない。
> 　一　子の出生の日から国家公務員の育児休業等に関する法律（平成三年法律第百九号。以下「国家公務員育児休業法」という。）第三条第一項第一号の規定により人事院規則で定める期間を基準として条例で定める期間内に、職員（当該期間内に労働基準法（昭和二十二年法律第四十九号）第六十五条第二項の規定により勤務しない職員を除く。）が当該子についてする育児休業（次号に掲げる育児休業を除く。）のうち最初のもの及び二回目のもの
> 　二　任期を定めて採用された職員が当該任期の末日を育児休業の期間の末日としてする育児休業（当該職員が、当該任期を更新され、又は当該任期の満了後引き続いて任命権者を同じくする職に採用されることに伴い、当該育児休業に係る子について、当該更新前の任期の末日の翌日又は当該採用の日を育児休業の期間の初日とする育児休業をする場合に限る。）
> ２　育児休業の承認を受けようとする職員は、育児休業をしようとする期間の初日及び末日を明らかにして、任命権者に対し、その承認を請求するものとする。
> ３　任命権者は、前項の規定による請求があったときは、当該請求に係る期間について当該請求をした職員の業務を処理するための措置を講ずることが著しく困難である場合を除き、これを承認しなければならない。
>
> 要点:
> - 子が3歳に達する日まで、任命権者の承認を受けて取れます（非常勤職員は条例で定める日まで）。
> - 原則は2回までです。出生直後の期間に取る育休（第1号）などは回数に数えません。
> - 第3項により、業務を処理する措置を講ずることが著しく困難な場合を除き、任命権者は承認しなければなりません。
>
> 法令全体の最新版は 2025-10-01 施行（地方公務員の育児休業等に関する法律の一部を改正する法律、令和七年法律第五号）です。e-Gov: https://laws.e-gov.go.jp/law/403AC0000000110
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S6: Recovering from a vague law name

> 公務員の育休の法律の第2条を見せて。

**Call 1** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "公務員の育児休業等に関する法律", "article": "2"}}]}
```

Result:

```json
{
 "error": "2 laws match '公務員の育児休業等に関する法律'; none is an exact title or abbreviation.",
 "error_type": "ambiguous_law",
 "next_step": "Pick one candidate and call the same tool again with law='<its law_id>' (or its exact title). If the user's words fit several, read each or ask the user. If none fits, call egov_law_search with a longer part of the name or a higher limit. Candidates (Acts first): 国家公務員の育児休業等に関する法律 [403AC0000000109]; 地方公務員の育児休業等に関する法律 [403AC0000000110]"
}
```

**Call 2** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "403AC0000000109", "article": "2"}}]}
```

Result:

```json
{
 "law_title": "国家公務員の育児休業等に関する法律",
 "law_num": "平成三年法律第百九号",
 "law_id": "403AC0000000109",
 "article": "第二条",
 "caption": "（定義）",
 "text": "（定義）\n第二条　この法律において「職員」とは、第二十七条を除き、国家公務員法（昭和二十二年法律第百二十号）第二条に規定する一般職に属する国家公務員をいう。\n２　この法律において「任命権者」とは、国家公務員法第五十五条第一項に規定する任命権者及び法律で別に定められた任命権者並びにその委任を受けた者をいう。\n３　この法律において「各省各庁の長」とは、一般職の職員の勤務時間、休暇等に関する法律（平成六年法律第三十三号。以下「勤務時間法」という。）第三条に規定する各省各庁の長及びその委任を受けた者をいう。",
 "paragraphs": 3,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-10-01",
  "status": "in force now",
  "last_amended_by": "防衛省設置法等の一部を改正する法律（令和七年法律第四十四号）",
  "law_revision_id": "403AC0000000109_20261001_507AC0000000044"
 },
 "as_of": "2026-10-02",
 "resolved_by": "law ID",
 "url": "https://laws.e-gov.go.jp/law/403AC0000000109",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 }
}
```

**Call 3** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "403AC0000000110", "article": "2"}}]}
```

Result:

```json
{
 "law_title": "地方公務員の育児休業等に関する法律",
 "law_num": "平成三年法律第百十号",
 "law_id": "403AC0000000110",
 "article": "第二条",
 "caption": "（育児休業の承認）",
 "text": "（育児休業の承認）\n第二条　職員（第十八条第一項の規定により採用された同項に規定する短時間勤務職員、臨時的に任用される職員その他その任用の状況がこれらに類する職員として条例で定める職員を除く。）は、任命権者（地方公務員法第六条第一項に規定する任命権者及びその委任を受けた者をいう。以下同じ。）の承認を受けて、当該職員の子（民法（明治二十九年法律第八十九号）第八百十七条の二第一項の規定により職員が当該職員との間における同項に規定する特別養子縁組の成立について家庭裁判所に請求した者（当該請求に係る家事審判事件が裁判所に係属している場合に限る。）であって、当該職員が現に監護するもの、児童福祉法（昭和二十二年法律第百六十四号）第二十七条第一項第三号の規定により同法第六条の四第二号に規定する養子縁組里親である職員に委託されている児童その他これらに準ずる者として条例で定める者を含む。以下同じ。）を養育するため、当該子が三歳に達する日（非常勤職員にあっては、当該子の養育の事情に応じ、一歳に達する日から一歳六か月に達する日までの間で条例で定める日（当該子の養育の事情を考慮して特に必要と認められる場合として条例で定める場合に該当するときは、二歳に達する日））まで、育児休業をすることができる。ただし、当該子について、既に二回の育児休業（次に掲げる育児休業を除く。）をしたことがあるときは、条例で定める特別の事情がある場合を除き、この限りでない。\n　一　子の出生の日から国家公務員の育児休業等に関する法律（平成三年法律第百九号。以下「国家公務員育児休業法」という。）第三条第一項第一号の規定により人事院規則で定める期間を基準として条例で定める期間内に、職員（当該期間内に労働基準法（昭和二十二年法律第四十九号）第六十五条第二項の規定により勤務しない職員を除く。）が当該子についてする育児休業（次号に掲げる育児休業を除く。）のうち最初のもの及び二回目のもの\n　二　任期を定めて採用された職員が当該任期の末日を育児休業の期間の末日としてする育児休業（当該職員が、当該任期を更新され、又は当該任期の満了後引き続いて任命権者を同じくする職に採用されることに伴い、当該育児休業に係る子について、当該更新前の任期の末日の翌日又は当該採用の日を育児休業の期間の初日とする育児休業をする場合に限る。）\n２　育児休業の承認を受けようとする職員は、育児休業をしようとする期間の初日及び末日を明らかにして、任命権者に対し、その承認を請求するものとする。\n３　任命権者は、前項の規定による請求があったときは、当該請求に係る期間について当該請求をした職員の業務を処理するための措置を講ずることが著しく困難である場合を除き、これを承認しなければならない。",
 "paragraphs": 3,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2025-10-01",
  "status": "in force now",
  "last_amended_by": "地方公務員の育児休業等に関する法律の一部を改正する法律（令和七年法律第五号）",
  "law_revision_id": "403AC0000000110_20251001_507AC0000000005"
 },
 "as_of": "2026-10-02",
 "resolved_by": "law ID",
 "url": "https://laws.e-gov.go.jp/law/403AC0000000110",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 }
}
```

Tool calls: 3.

Final answer written by the agent:

> 「公務員の育休の法律」には次の2本があります。どちらか分からなかったので、両方の第2条を出します。
>
> 1. 国家公務員の育児休業等に関する法律（平成三年法律第百九号）
> 2. 地方公務員の育児休業等に関する法律（平成三年法律第百十号）
>
> 同じ第2条でも中身が違います。国家公務員の法律の第2条は用語の定義です。育児休業そのもの（承認）を定めた条文は国家公務員の法律では第3条にあり、地方公務員の法律では第2条にあります。国家公務員の方をお探しなら、第3条も出します。
>
> ■ 国家公務員の育児休業等に関する法律 第2条（定義）（2026-10-02 時点で施行されている文言）
> （定義）
> 第二条　この法律において「職員」とは、第二十七条を除き、国家公務員法（昭和二十二年法律第百二十号）第二条に規定する一般職に属する国家公務員をいう。
> ２　この法律において「任命権者」とは、国家公務員法第五十五条第一項に規定する任命権者及び法律で別に定められた任命権者並びにその委任を受けた者をいう。
> ３　この法律において「各省各庁の長」とは、一般職の職員の勤務時間、休暇等に関する法律（平成六年法律第三十三号。以下「勤務時間法」という。）第三条に規定する各省各庁の長及びその委任を受けた者をいう。
> e-Gov: https://laws.e-gov.go.jp/law/403AC0000000109
>
> ■ 地方公務員の育児休業等に関する法律 第2条（育児休業の承認）（2026-10-02 時点で施行されている文言）
> （育児休業の承認）
> 第二条　職員（第十八条第一項の規定により採用された同項に規定する短時間勤務職員、臨時的に任用される職員その他その任用の状況がこれらに類する職員として条例で定める職員を除く。）は、任命権者（地方公務員法第六条第一項に規定する任命権者及びその委任を受けた者をいう。以下同じ。）の承認を受けて、当該職員の子（民法（明治二十九年法律第八十九号）第八百十七条の二第一項の規定により職員が当該職員との間における同項に規定する特別養子縁組の成立について家庭裁判所に請求した者（当該請求に係る家事審判事件が裁判所に係属している場合に限る。）であって、当該職員が現に監護するもの、児童福祉法（昭和二十二年法律第百六十四号）第二十七条第一項第三号の規定により同法第六条の四第二号に規定する養子縁組里親である職員に委託されている児童その他これらに準ずる者として条例で定める者を含む。以下同じ。）を養育するため、当該子が三歳に達する日（非常勤職員にあっては、当該子の養育の事情に応じ、一歳に達する日から一歳六か月に達する日までの間で条例で定める日（当該子の養育の事情を考慮して特に必要と認められる場合として条例で定める場合に該当するときは、二歳に達する日））まで、育児休業をすることができる。ただし、当該子について、既に二回の育児休業（次に掲げる育児休業を除く。）をしたことがあるときは、条例で定める特別の事情がある場合を除き、この限りでない。
> 　一　子の出生の日から国家公務員の育児休業等に関する法律（平成三年法律第百九号。以下「国家公務員育児休業法」という。）第三条第一項第一号の規定により人事院規則で定める期間を基準として条例で定める期間内に、職員（当該期間内に労働基準法（昭和二十二年法律第四十九号）第六十五条第二項の規定により勤務しない職員を除く。）が当該子についてする育児休業（次号に掲げる育児休業を除く。）のうち最初のもの及び二回目のもの
> 　二　任期を定めて採用された職員が当該任期の末日を育児休業の期間の末日としてする育児休業（当該職員が、当該任期を更新され、又は当該任期の満了後引き続いて任命権者を同じくする職に採用されることに伴い、当該育児休業に係る子について、当該更新前の任期の末日の翌日又は当該採用の日を育児休業の期間の初日とする育児休業をする場合に限る。）
> ２　育児休業の承認を受けようとする職員は、育児休業をしようとする期間の初日及び末日を明らかにして、任命権者に対し、その承認を請求するものとする。
> ３　任命権者は、前項の規定による請求があったときは、当該請求に係る期間について当該請求をした職員の業務を処理するための措置を講ずることが著しく困難である場合を除き、これを承認しなければならない。
> e-Gov: https://laws.e-gov.go.jp/law/403AC0000000110
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S7: Reviewing work rules: is a change coming

> 就業規則を見直したい。労基法で、次に施行される改正はある？

**Call 1** `tool_call`

```json
{"calls": [{"name": "egov_law_revisions", "arguments": {"law": "労基法"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "promulgation_date": "1947-04-07",
 "next_amendment": {
  "in_force_since": "2027-04-01",
  "status": "not yet in force (scheduled)",
  "amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "change": "amendment",
  "title_names_this_law": false,
  "amendment_promulgated": "2026-07-17",
  "date_fixed": true,
  "law_revision_id": "322AC0000000049_20270401_508AC0000000060",
  "check": {
   "as_of": "2027-03-31",
   "compare_with": "2027-04-01"
  },
  "steps_already_in_force": [
   "2026-07-17"
  ]
 },
 "scheduled_repeal": null,
 "scheduled_amendments": [
  {
   "in_force_since": "2027-04-01",
   "status": "not yet in force (scheduled)",
   "amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2026-07-17",
   "date_fixed": true,
   "law_revision_id": "322AC0000000049_20270401_508AC0000000060",
   "check": {
    "as_of": "2027-03-31",
    "compare_with": "2027-04-01"
   },
   "steps_already_in_force": [
    "2026-07-17"
   ]
  },
  {
   "in_force_since": "2028-12-23",
   "status": "not yet in force (scheduled)",
   "amended_by": "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法等の一部を改正する法律",
   "amendment_promulgated": "2026-06-24",
   "enforcement_note": "民法等の一部を改正する法律（令和八年法律第四十五号）の施行の日",
   "date_fixed": false,
   "law_revision_id": "322AC0000000049_20281223_508AC0000000046",
   "check": {
    "as_of": "2028-12-22",
    "compare_with": "2028-12-23"
   },
   "steps_already_in_force": [
    "2026-06-24"
   ]
  }
 ],
 "in_force_now": {
  "in_force_since": "2026-07-17",
  "status": "in force now",
  "amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "change": "amendment",
  "title_names_this_law": false,
  "amendment_promulgated": "2026-07-17",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060",
  "check": {
   "as_of": "2026-07-16",
   "compare_with": "2026-07-17"
  }
 },
 "earlier_versions": [
  {
   "in_force_since": "2026-06-24",
   "status": "superseded (older version)",
   "amended_by": "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法等の一部を改正する法律",
   "amendment_promulgated": "2026-06-24",
   "law_revision_id": "322AC0000000049_20260624_508AC0000000046",
   "check": {
    "as_of": "2026-06-23",
    "compare_with": "2026-06-24"
   }
  },
  {
   "in_force_since": "2025-06-01",
   "status": "superseded (older version)",
   "amended_by": "刑法等の一部を改正する法律の施行に伴う関係法律の整理等に関する法律　抄（令和四年法律第六十八号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "刑法等の一部を改正する法律",
   "amendment_promulgated": "2022-06-17",
   "law_revision_id": "322AC0000000049_20250601_504AC0000000068",
   "check": {
    "as_of": "2025-05-31",
    "compare_with": "2025-06-01"
   }
  },
  {
   "in_force_since": "2025-04-01",
   "status": "superseded (older version)",
   "amended_by": "育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律及び次世代育成支援対策推進法の一部を改正する法律（令和六年法律第四十二号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2024-05-31",
   "law_revision_id": "322AC0000000049_20250401_506AC0000000042",
   "check": {
    "as_of": "2025-03-31",
    "compare_with": "2025-04-01"
   }
  },
  {
   "in_force_since": "2024-05-31",
   "status": "superseded (older version)",
   "amended_by": "育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律及び次世代育成支援対策推進法の一部を改正する法律（令和六年法律第四十二号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2024-05-31",
   "law_revision_id": "322AC0000000049_20240531_506AC0000000042",
   "check": {
    "as_of": "2024-05-30",
    "compare_with": "2024-05-31"
   }
  },
  {
   "in_force_since": "2023-04-01",
   "status": "superseded (older version)",
   "amended_by": "働き方改革を推進するための関係法律の整備に関する法律（平成三十年法律第七十一号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2018-07-06",
   "law_revision_id": "322AC0000000049_20230401_430AC0000000071",
   "check": {
    "as_of": "2023-03-31",
    "compare_with": "2023-04-01"
   }
  },
  {
   "in_force_since": "2022-06-17",
   "status": "superseded (older version)",
   "amended_by": "刑法等の一部を改正する法律の施行に伴う関係法律の整理等に関する法律（令和四年法律第六十八号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "刑法等の一部を改正する法律",
   "amendment_promulgated": "2022-06-17",
   "law_revision_id": "322AC0000000049_20220617_504AC0000000068",
   "check": {
    "as_of": "2022-06-16",
    "compare_with": "2022-06-17"
   }
  },
  {
   "in_force_since": "2020-04-01",
   "status": "superseded (older version)",
   "amended_by": "労働基準法の一部を改正する法律（令和二年法律第十三号）",
   "change": "amendment",
   "title_names_this_law": true,
   "amendment_promulgated": "2020-03-31",
   "law_revision_id": "322AC0000000049_20200401_502AC0000000013",
   "check": {
    "as_of": "2020-03-31",
    "compare_with": "2020-04-01"
   }
  },
  {
   "in_force_since": "2020-04-01",
   "status": "superseded (older version)",
   "amended_by": "民法の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（平成二十九年法律第四十五号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法の一部を改正する法律",
   "amendment_promulgated": "2017-06-02",
   "law_revision_id": "322AC0000000049_20200401_429AC0000000045",
   "check": {
    "as_of": "2020-03-31",
    "compare_with": "2020-04-01"
   }
  },
  {
   "in_force_since": "2019-04-01",
   "status": "superseded (older version)",
   "amended_by": "働き方改革を推進するための関係法律の整備に関する法律（平成三十年法律第七十一号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2018-07-06",
   "law_revision_id": "322AC0000000049_20190401_430AC0000000071",
   "check": {
    "as_of": "2019-03-31",
    "compare_with": "2019-04-01"
   }
  },
  {
   "in_force_since": "2018-07-06",
   "status": "superseded (older version)",
   "amended_by": "働き方改革を推進するための関係法律の整備に関する法律（平成三十年法律第七十一号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2018-07-06",
   "law_revision_id": "322AC0000000049_20180706_430AC0000000071",
   "check": {
    "as_of": "2018-07-05",
    "compare_with": "2018-07-06"
   }
  }
 ],
 "total_versions": 15,
 "scope": "Amendments already promulgated (公布) and recorded in e-Gov for this law only. Bills still in the Diet and changes to its 施行令/施行規則 (separate laws) are not included; say so when you answer.",
 "note": "scheduled_amendments: soonest first, not yet in force; next_amendment is the first of them. change: amendment, repeal, or this law's own provisions taking effect. title_names_this_law: whether the amending law's title names this law; follow_up_of: for a law titled '〈X〉の施行に伴う…', the law X it follows up. Neither says how much an article changes. To see one amendment's effect on an article, call egov_law_article with that row's check arguments (as_of = the day before, compare_with = the day): one call returns changed true/false and a diff. Amendments taking effect on the same day cannot be told apart. date_fixed=false means the law does not state the date (see enforcement_note): in_force_since is e-Gov's provisional date, for '…を超えない範囲内において政令で定める日' the latest possible day (say 'by' that date, and it may come before other scheduled dates), for '…の施行の日' a placeholder until the other law's date is set. A staged amendment appears once per step: steps already in force are in earlier_versions and listed in steps_already_in_force. earlier_versions: newest first.",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "next_step": "To check whether the next amendment changes an article, call egov_law_article with as_of='2027-03-31', compare_with='2027-04-01' (one call: changed + diff). Lists cut at limit=10 (2 scheduled, 12 earlier); raise limit (max 50) to see more."
}
```

Tool calls: 1.

Final answer written by the agent:

> はい、あります。労働基準法の次の改正は 2027年4月1日施行です（日付は確定）。
>
> - 改正する法律: 労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）。2026-07-17 公布で、一部はすでに同日に施行済みです。2027-04-01 は残りの段階です。
> - その後の予定: 民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）による改正があります。施行日は「民法等の一部を改正する法律（令和八年法律第四十五号）の施行の日」で、まだ決まっていません（e-Gov は暫定で 2028-12-23 と表示）。
>
> ただし、この一覧からは「どの条文がどう変わるか」までは分かりません。法律の題名にも労働基準法の名前は入っていません。就業規則で引いている条文（例: 労働時間、休憩、年休、賃金、時効など）を教えてもらえれば、その条文ごとに 2027-03-31 と 2027-04-01 の文言を比べ、変わるかどうかと差分をお見せできます。
>
> 注意: すでに公布され e-Gov に登録された改正だけが対象です。国会に出ている法案や、労働基準法施行規則など省令の改正は入っていません。就業規則の見直しでは、施行規則の改正も別に確認することをおすすめします。
>
> 現在の版: 2026-07-17 施行（令和八年法律第六十号による改正）。e-Gov: https://laws.e-gov.go.jp/law/322AC0000000049
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）

## S8: Checking one article against an amendment

> 就業規則の『賃金請求権の時効』の規定を見直しています。労基法115条は、2027年4月1日に施行される改正で変わりますか？変わるならどこが変わるか教えて。

**Call 1** `tool_describe`

```json
{"names": ["egov_law_article", "egov_law_revisions"]}
```

Result: the full schemas of egov_law_article, egov_law_revisions (omitted here).

**Call 2** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "労基法", "article": "115", "as_of": "2027-03-31", "compare_with": "2027-04-01"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "article": "第百十五条",
 "caption": "（時効）",
 "text": "（時効）\n第百十五条　この法律の規定による賃金の請求権はこれを行使することができる時から五年間、この法律の規定による災害補償その他の請求権（賃金の請求権を除く。）はこれを行使することができる時から二年間行わない場合においては、時効によつて消滅する。",
 "paragraphs": 1,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-07-17",
  "status": "not yet in force: the text as scheduled to read on 2027-03-31",
  "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060"
 },
 "as_of": "2027-03-31",
 "resolved_by": "abbreviation",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "text_notes": "附則第百四十三条 of this law's 附則 changes how this article applies for the time being (…の規定の適用については…). Read it with article='附則第百四十三条' before answering; the wording above alone may not be what applies today. (Notes, not part of the law text.)",
 "comparison": {
  "as_of": "2027-04-01",
  "changed": true,
  "law_version_in_force_since": "2027-04-01",
  "diff": [
   "-第百十五条　この法律の規定による賃金の請求権はこれを行使することができる時から五年間、この法律の規定による災害補償その他の請求権（賃金の請求権を除く。）はこれを行使することができる時から二年間行わない場合においては、時効によつて消滅する。",
   "+第百十五条　この法律の規定による賃金の請求権はこれを行使することができる時から五年間、その他の請求権（この法律の規定による災害補償の請求権を除く。）はこれを行使することができる時から二年間行わない場合においては、時効によつて消滅する。",
   "+２　この法律の規定による災害補償の請求権は、これを行使することができる時から二年間行わない場合においては、時効によつて消滅する。ただし、この法律の規定による災害補償の原因である事故に係る疾病が、その性質上、第七十五条第一項、第七十六条第一項、第七十七条、第七十九条又は第八十条に規定する災害補償の事由に該当するものかどうかを容易に判断することができない疾病として政令で定めるものである場合には、当該災害補償の請求権については、この項本文中「二年間」とあるのは、「五年間」とする。"
  ],
  "text": "（時効）\n第百十五条　この法律の規定による賃金の請求権はこれを行使することができる時から五年間、その他の請求権（この法律の規定による災害補償の請求権を除く。）はこれを行使することができる時から二年間行わない場合においては、時効によつて消滅する。\n２　この法律の規定による災害補償の請求権は、これを行使することができる時から二年間行わない場合においては、時効によつて消滅する。ただし、この法律の規定による災害補償の原因である事故に係る疾病が、その性質上、第七十五条第一項、第七十六条第一項、第七十七条、第七十九条又は第八十条に規定する災害補償の事由に該当するものかどうかを容易に判断することができない疾病として政令で定めるものである場合には、当該災害補償の請求権については、この項本文中「二年間」とあるのは、「五年間」とする。",
  "note": "diff compares whole paragraph/item lines: '-' is the wording on as_of (the main text above), '+' on this date."
 }
}
```

**Call 3** `tool_call`

```json
{"calls": [{"name": "egov_law_revisions", "arguments": {"law": "労基法", "limit": 3}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "promulgation_date": "1947-04-07",
 "next_amendment": {
  "in_force_since": "2027-04-01",
  "status": "not yet in force (scheduled)",
  "amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "change": "amendment",
  "title_names_this_law": false,
  "amendment_promulgated": "2026-07-17",
  "date_fixed": true,
  "law_revision_id": "322AC0000000049_20270401_508AC0000000060",
  "check": {
   "as_of": "2027-03-31",
   "compare_with": "2027-04-01"
  },
  "steps_already_in_force": [
   "2026-07-17"
  ]
 },
 "scheduled_repeal": null,
 "scheduled_amendments": [
  {
   "in_force_since": "2027-04-01",
   "status": "not yet in force (scheduled)",
   "amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2026-07-17",
   "date_fixed": true,
   "law_revision_id": "322AC0000000049_20270401_508AC0000000060",
   "check": {
    "as_of": "2027-03-31",
    "compare_with": "2027-04-01"
   },
   "steps_already_in_force": [
    "2026-07-17"
   ]
  },
  {
   "in_force_since": "2028-12-23",
   "status": "not yet in force (scheduled)",
   "amended_by": "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法等の一部を改正する法律",
   "amendment_promulgated": "2026-06-24",
   "enforcement_note": "民法等の一部を改正する法律（令和八年法律第四十五号）の施行の日",
   "date_fixed": false,
   "law_revision_id": "322AC0000000049_20281223_508AC0000000046",
   "check": {
    "as_of": "2028-12-22",
    "compare_with": "2028-12-23"
   },
   "steps_already_in_force": [
    "2026-06-24"
   ]
  }
 ],
 "in_force_now": {
  "in_force_since": "2026-07-17",
  "status": "in force now",
  "amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "change": "amendment",
  "title_names_this_law": false,
  "amendment_promulgated": "2026-07-17",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060",
  "check": {
   "as_of": "2026-07-16",
   "compare_with": "2026-07-17"
  }
 },
 "earlier_versions": [
  {
   "in_force_since": "2026-06-24",
   "status": "superseded (older version)",
   "amended_by": "民法等の一部を改正する法律の施行に伴う関係法律の整備等に関する法律（令和八年法律第四十六号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "民法等の一部を改正する法律",
   "amendment_promulgated": "2026-06-24",
   "law_revision_id": "322AC0000000049_20260624_508AC0000000046",
   "check": {
    "as_of": "2026-06-23",
    "compare_with": "2026-06-24"
   }
  },
  {
   "in_force_since": "2025-06-01",
   "status": "superseded (older version)",
   "amended_by": "刑法等の一部を改正する法律の施行に伴う関係法律の整理等に関する法律　抄（令和四年法律第六十八号）",
   "change": "amendment",
   "title_names_this_law": false,
   "follow_up_of": "刑法等の一部を改正する法律",
   "amendment_promulgated": "2022-06-17",
   "law_revision_id": "322AC0000000049_20250601_504AC0000000068",
   "check": {
    "as_of": "2025-05-31",
    "compare_with": "2025-06-01"
   }
  },
  {
   "in_force_since": "2025-04-01",
   "status": "superseded (older version)",
   "amended_by": "育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律及び次世代育成支援対策推進法の一部を改正する法律（令和六年法律第四十二号）",
   "change": "amendment",
   "title_names_this_law": false,
   "amendment_promulgated": "2024-05-31",
   "law_revision_id": "322AC0000000049_20250401_506AC0000000042",
   "check": {
    "as_of": "2025-03-31",
    "compare_with": "2025-04-01"
   }
  }
 ],
 "total_versions": 15,
 "scope": "Amendments already promulgated (公布) and recorded in e-Gov for this law only. Bills still in the Diet and changes to its 施行令/施行規則 (separate laws) are not included; say so when you answer.",
 "note": "scheduled_amendments: soonest first, not yet in force; next_amendment is the first of them. change: amendment, repeal, or this law's own provisions taking effect. title_names_this_law: whether the amending law's title names this law; follow_up_of: for a law titled '〈X〉の施行に伴う…', the law X it follows up. Neither says how much an article changes. To see one amendment's effect on an article, call egov_law_article with that row's check arguments (as_of = the day before, compare_with = the day): one call returns changed true/false and a diff. Amendments taking effect on the same day cannot be told apart. date_fixed=false means the law does not state the date (see enforcement_note): in_force_since is e-Gov's provisional date, for '…を超えない範囲内において政令で定める日' the latest possible day (say 'by' that date, and it may come before other scheduled dates), for '…の施行の日' a placeholder until the other law's date is set. A staged amendment appears once per step: steps already in force are in earlier_versions and listed in steps_already_in_force. earlier_versions: newest first.",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "next_step": "To check whether the next amendment changes an article, call egov_law_article with as_of='2027-03-31', compare_with='2027-04-01' (one call: changed + diff). Lists cut at limit=3 (2 scheduled, 12 earlier); raise limit (max 50) to see more."
}
```

**Call 4** `tool_call`

```json
{"calls": [{"name": "egov_law_article", "arguments": {"law": "労基法", "article": "附則第百四十三条", "as_of": "2027-03-31", "compare_with": "2027-04-01"}}]}
```

Result:

```json
{
 "law_title": "労働基準法",
 "law_num": "昭和二十二年法律第四十九号",
 "law_id": "322AC0000000049",
 "article": "附則第百四十三条",
 "provision": "附則: the law's own supplementary provisions (including articles inserted later, such as 労基法 附則第143条); the separate 附則 of each amending law is not included",
 "text": "第百四十三条　第百九条の規定の適用については、当分の間、同条中「五年間」とあるのは、「三年間」とする。\n２　第百十四条の規定の適用については、当分の間、同条ただし書中「五年」とあるのは、「三年」とする。\n３　第百十五条の規定の適用については、当分の間、同条中「賃金の請求権はこれを行使することができる時から五年間」とあるのは、「退職手当の請求権はこれを行使することができる時から五年間、この法律の規定による賃金（退職手当を除く。）の請求権はこれを行使することができる時から三年間」とする。",
 "paragraphs": 3,
 "law_version": {
  "note": "Version of the whole law. This article did not necessarily change in it.",
  "in_force_since": "2026-07-17",
  "status": "not yet in force: the text as scheduled to read on 2027-03-31",
  "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）",
  "law_revision_id": "322AC0000000049_20260717_508AC0000000060"
 },
 "as_of": "2027-03-31",
 "resolved_by": "abbreviation",
 "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
 "source": {
  "attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）",
  "retrieved_on": "2026-10-02",
  "note": "Show this attribution with any law text you give the user (e-Gov terms, PDL1.0)."
 },
 "comparison": {
  "as_of": "2027-04-01",
  "changed": true,
  "law_version_in_force_since": "2027-04-01",
  "diff": [
   "-３　第百十五条の規定の適用については、当分の間、同条中「賃金の請求権はこれを行使することができる時から五年間」とあるのは、「退職手当の請求権はこれを行使することができる時から五年間、この法律の規定による賃金（退職手当を除く。）の請求権はこれを行使することができる時から三年間」とする。",
   "+３　第百十五条第一項の規定の適用については、当分の間、同項中「賃金の請求権はこれを行使することができる時から五年間」とあるのは、「退職手当の請求権はこれを行使することができる時から五年間、この法律の規定による賃金（退職手当を除く。）の請求権はこれを行使することができる時から三年間」とする。"
  ],
  "text": "第百四十三条　第百九条の規定の適用については、当分の間、同条中「五年間」とあるのは、「三年間」とする。\n２　第百十四条の規定の適用については、当分の間、同条ただし書中「五年」とあるのは、「三年」とする。\n３　第百十五条第一項の規定の適用については、当分の間、同項中「賃金の請求権はこれを行使することができる時から五年間」とあるのは、「退職手当の請求権はこれを行使することができる時から五年間、この法律の規定による賃金（退職手当を除く。）の請求権はこれを行使することができる時から三年間」とする。",
  "note": "diff compares whole paragraph/item lines: '-' is the wording on as_of (the main text above), '+' on this date."
 }
}
```

Tool calls: 4.

Final answer written by the agent:

> 結論: 第115条の文言は 2027年4月1日に変わります。ただし、賃金請求権の時効は変わりません（本則5年、当分の間は3年、退職手当は5年のまま）。変わるのは災害補償の請求権の扱いです。賃金請求権の時効の規定は、見直しの必要はないと考えられます。
>
> 改正する法律は、労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号、2026-07-17 公布）です。e-Gov の改正履歴でも、2027-04-01 施行と確定しています。
>
> ■ 第115条の変化（2027-03-31 → 2027-04-01）
> 改正前（2027-03-31 時点の文言）:
> 第百十五条　この法律の規定による賃金の請求権はこれを行使することができる時から五年間、この法律の規定による災害補償その他の請求権（賃金の請求権を除く。）はこれを行使することができる時から二年間行わない場合においては、時効によつて消滅する。
>
> 改正後（2027-04-01 からの文言）:
> 第百十五条　この法律の規定による賃金の請求権はこれを行使することができる時から五年間、その他の請求権（この法律の規定による災害補償の請求権を除く。）はこれを行使することができる時から二年間行わない場合においては、時効によつて消滅する。
> ２　この法律の規定による災害補償の請求権は、これを行使することができる時から二年間行わない場合においては、時効によつて消滅する。ただし、この法律の規定による災害補償の原因である事故に係る疾病が、その性質上、第七十五条第一項、第七十六条第一項、第七十七条、第七十九条又は第八十条に規定する災害補償の事由に該当するものかどうかを容易に判断することができない疾病として政令で定めるものである場合には、当該災害補償の請求権については、この項本文中「二年間」とあるのは、「五年間」とする。
>
> 変わる点:
> 1. 賃金の請求権の部分（行使できる時から5年間）は、文言もそのままです。
> 2. 災害補償の請求権が第1項から外れ、新しい第2項になります。原則は2年のままです。業務が原因かどうかすぐには判断しにくい疾病として政令で定めるものに限り、5年になります。対象の疾病は政令で決まり、今回は確認していません。
> 3. その他の請求権（災害補償を除く）は、これまでどおり2年です。
>
> ■ 実際に適用される年数（附則第143条の経過措置）
> 第115条の本文は「賃金5年」ですが、附則第143条第3項により、当分の間は退職手当は5年、それ以外の賃金は3年と読み替えられます。2027-04-01 の改正でこの附則は、読み替える対象が「第百十五条」から「第百十五条第一項」に変わるだけです（条文に第2項ができることに合わせた整理）。年数は変わりません。
>
> 2027-04-01 以降の附則第143条第3項:
> ３　第百十五条第一項の規定の適用については、当分の間、同項中「賃金の請求権はこれを行使することができる時から五年間」とあるのは、「退職手当の請求権はこれを行使することができる時から五年間、この法律の規定による賃金（退職手当を除く。）の請求権はこれを行使することができる時から三年間」とする。
>
> 就業規則への影響:
> - 賃金請求権の時効（賃金3年・退職手当5年）の規定は、そのままで改正後とずれません。
> - 就業規則が「労基法第115条」と条番号だけで引いている場合は、2027-04-01 以降は「第115条第1項」と項まで書くと正確です。
> - 就業規則に災害補償の請求権の時効を書いているなら、第2項の新設（一定の疾病は5年）に合わせた見直しが要ります。
>
> 注意: すでに公布され e-Gov に登録された改正だけで確認しました。審議中の法案や、対象の疾病を定める政令は含みません。
>
> 法令番号: 昭和二十二年法律第四十九号。e-Gov: https://laws.e-gov.go.jp/law/322AC0000000049
>
> 出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）
