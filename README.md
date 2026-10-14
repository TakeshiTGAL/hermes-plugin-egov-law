# jp-egov-law: Japanese laws for Hermes Agent, built on the e-Gov Law API

Ask your Hermes agent about Japanese law. When it calls a tool, you get the official text of the article, with its law
number, the date the current version took effect, and a link to the source.

The data comes from the API of [e-Gov 法令検索](https://laws.e-gov.go.jp/), the law database run by the
Digital Agency of Japan (デジタル庁). No API key, no account, read-only.

> **日本語の要約**：エージェントに「労基法32条」「民法第四百十五条」「個人情報保護法の次の改正はいつ？」と聞くと、
> e-Gov の公式な条文・法令番号・施行日・出典を返します。導入はコマンド1行、APIキー不要。
> 改正は施行予定日と改正法の名前まで返し、条文が変わるかは同じ道具で1回で確かめられます。詳しくは [日本語の節](#日本語)。

## What you can ask

| You are... | You ask | What the agent does |
|---|---|---|
| Writing work rules (就業規則) | 「労基法の法定労働時間（32条）の条文を出して」 | One `egov_law_article` call: 労働基準法 第三十二条, both paragraphs, with the law number and the date the current version took effect |
| Reviewing a contract | 「民法第四百十五条の条文を見せて」 | One `egov_law_article` call: 第四百十五条（債務不履行による損害賠償）with its numbered items |
| Checking an amendment | 「個人情報保護法の次の改正はいつ施行？」 | One `egov_law_revisions` call: `next_amendment` (the soonest scheduled change), every scheduled change with its date and amending law, and the version in force now |
| Asking by topic | 「年次有給休暇の付与日数を定めている条文は？」 | The agent knows the topic lives in 労基法39条: one `egov_law_article` call, whose `text_notes` points to the 附則 articles that read 第三十九条 differently; the agent read them too. When it does not know the article, `egov_law_search` with `mode="text"` finds the laws that mention the phrase first |
| Using a vague name | 「公務員の育休の法律の第2条を見せて」 | The first call returns `ambiguous_law` with candidate law IDs; the agent reads 第2条 of both the 国家公務員 and the 地方公務員 law |
| Reviewing work rules for changes | 「労基法で、次に施行される改正はある？」 | One `egov_law_revisions` call: the next amendment and its date; each row's `check` pair then shows whether a given article changes |
| Checking one article against an amendment | 「労基法115条は2027年4月の改正で変わる？」 | One `egov_law_article` call with `as_of` (the day before) and `compare_with` (the day): changed or not, the line diff and the new wording. `text_notes` also points to 附則第143条, which for the time being reads retirement-allowance claims as five years and other wage claims as three years; the same tool reads it |

[`examples/scenarios.md`](examples/scenarios.md) is a record of an earlier end-to-end run. This
revision was not run through a model again.

## Install

```bash
hermes plugins install TakeshiTGAL/hermes-plugin-egov-law --enable
hermes chat -Q -q "労働基準法第32条の条文を見せて"
```

The first line installs and enables the plugin (nothing else to install: standard library only).
The second asks one question with the model you already configured in Hermes; the answer should
quote 第三十二条 and cite e-Gov.

- Needs Hermes v0.21.4 or later (`hermes --version`); on an older one, run `hermes update` first.
- Installed without `--enable`? Run `hermes plugins enable jp-egov-law`.
- Using the messaging gateway? Run `hermes gateway restart` once.
- Installing from a local clone instead of GitHub: the directory must be a git clone. Run
  `hermes plugins install file:///path/to/hermes-plugin-egov-law --enable`; Hermes warns
  "Using insecure/local URL scheme" and installs it.
- Once the plugin is in the Hermes catalog: `hermes plugins install jp-egov-law --enable`.
- Checked against Hermes main at commit 0a374d16 (2026-10-02): `hermes plugins validate` passes, and
  the plugin installs, enables and answers through Hermes's own tool dispatcher.

Hermes lists plugin tools behind its tool search, so the model sees a one-line entry per tool
(for example `egov_law_article: Japanese law article: law='労基法', article='32' or '三十二条の二'.`) and
loads the full schema when it needs it. No configuration is required.

## Tools

| Tool | Use it when | Main arguments |
|---|---|---|
| `egov_law_article` | The user names a law and an article, or you need the wording of a provision, or whether an amendment changes it | `law`, `article`, optional `paragraph`, `as_of`, `compare_with`, `max_chars` |
| `egov_law_search` | You do not know the exact law, need its number or ID, or want laws that mention a phrase | `query`, `mode` (`title` or `text`), `limit`, `include_repealed` |
| `egov_law_revisions` | The question is about when something took or takes effect, or upcoming amendments | `law`, `limit` |

### Ways to name a law (`law`)

- Official title: `労働基準法`, `個人情報の保護に関する法律`
- e-Gov abbreviation: `労基法`, `個人情報保護法`, `安衛法`, `労契法`
- Common short names e-Gov does not index, built in: `個情法`, `特商法`, `下請法`, `雇保法`, `育介法`, `育児休業法`,
  `パート法`, `パート有期法`, `パートタイム・有期雇用労働法`, `フリーランス法`, `フリーランス新法`, `派遣法`, `均等法`,
  `憲法`, `健保法`, `厚年法`, `パワハラ防止法`, `高年法`, `労基則`, `労規則`, `雇保則`, `電帳法`
- Law number, kanji or digits: `昭和二十二年法律第四十九号`, `昭和22年法律第49号`
- e-Gov law ID: `322AC0000000049`

If a partial name matches several laws (`労働`), the tool returns an error that lists the candidates
with their law IDs, so the agent can pick one and call again.

### Ways to write an article (`article`)

`第32条`, `32条`, `32`, `三十二条`, `第三十二条`, `第３２条`, `Article 32`.
Branch articles: `第三十二条の二`, `32の2`, `32-2`. With a paragraph: `第32条第2項` (or `paragraph: 2`).
The law's own 附則: `附則第143条`, or `附則` for one without articles. Items (号), 本文 and ただし書 cannot be
selected: `第32条第1項第2号` returns paragraph 1 with a note.

### What comes back

`egov_law_article` for `{"law": "労基法", "article": "三十二条"}` (shortened; data as of 2026-10-02):

```json
{
  "law_title": "労働基準法",
  "law_num": "昭和二十二年法律第四十九号",
  "law_id": "322AC0000000049",
  "article": "第三十二条",
  "caption": "（労働時間）",
  "text": "（労働時間）\n第三十二条　使用者は、労働者に、休憩時間を除き一週間について四十時間を超えて、労働させてはならない。\n２　使用者は、一週間の各日については、労働者に、休憩時間を除き一日について八時間を超えて、労働させてはならない。",
  "paragraphs": 2,
  "law_version": {"note": "Version of the whole law. This article did not necessarily change in it.", "in_force_since": "2026-07-17", "status": "in force now", "last_amended_by": "労働者災害補償保険法等の一部を改正する法律（令和八年法律第六十号）"},
  "url": "https://laws.e-gov.go.jp/law/322AC0000000049",
  "source": {"attribution": "出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）", "retrieved_on": "2026-10-02"}
}
```

Long articles are cut at `max_chars` (default 4,000 characters), at a line break when one falls in the
second half of the budget and mid-line otherwise. Nothing is added to the text. The result is marked
`"truncated": true` with `total_chars`, and `next_step` says which `max_chars` (up to 20,000) gets the rest.
`as_of: "2018-01-01"` returns the wording in force on that date (e-Gov keeps versions from
2017-04-01), and a future date returns the text as a scheduled amendment will make it read.
When that version's `date_fixed` is false, `law_version.status` calls `in_force_since` a provisional
date, not a fixed day, and `enforcement_note` quotes the law's own words for how the day is set.
`url` always opens the law's current version on e-Gov, even when you asked for another date.

`compare_with` adds a `comparison` in the same call: `changed` (true or false), a `diff` of whole
paragraph and item lines (`-` the text on `as_of`, `+` the text on `compare_with`) and the wording on
`compare_with`. The diff is also kept within `max_chars`. Only HTTP 400 with body code `400021` means
that article is absent on the comparison date. HTTP 404 with body code `404004` means e-Gov has no law
text for that date, so the comparison says the article does not exist then, and the call still returns
the article. HTTP 400 code `400038` is a bad element name. Any other 400, and any other 404, fails the
whole call. It is not a report that the wording changed. To see what one amendment does to an article,
use the `check` pair that `egov_law_revisions` gives each amendment: `as_of` = the day before it takes
effect, `compare_with` = the day. Amendments taking effect on the same day cannot be told apart.

When an article of the law's own 附則 says how the article applies (「第百十五条の規定の適用については…」),
`text_notes` names that 附則 article. Some of these transitional rules still apply and some have expired;
the note does not tell which.

### When something goes wrong

Tools never raise. Every failure is a JSON object with `error`, `error_type` and a `next_step`
that tells the agent what to do:

| `error_type` | Example | `next_step` says |
|---|---|---|
| `article_not_found` | 労働基準法 第九九九九条 | do not guess nearby numbers; it may be deleted or only added by an upcoming amendment; the e-Gov page. If the article was in the version just before the current one, see Limitations |
| `paragraph_not_found` | 第三十六条 with `paragraph: 99` | how many paragraphs the article has |
| `not_covered` | `別表第一`, `様式` | do not retry; give the user the e-Gov page (its URL is in `next_step`) |
| `law_not_found` | a law name that matches nothing | search with a shorter name or `mode="text"` |
| `ambiguous_law` | `労働` | pick one of the listed law IDs, or search with a longer name |
| `bad_argument` | `as_of: "2000-01-01"` | use a date on or after 2017-04-01 |
| `timeout` / `network` | e-Gov unreachable | wait and retry, at most twice / check the connection |
| `upstream` / `bad_response` | e-Gov maintenance | try again later |
| `not_found` / `bad_request` | e-Gov rejected a lookup | its message, and to check the law with `egov_law_search` / fix the argument |
| `too_large` | a response over 8 MB | ask for one article |
| `internal` | an unexpected error in the plugin | retry once, then give the user the e-Gov page |

A search with no hits is not an error: it returns `"total_matches": 0` with a message and a next step.

## Weekly amendment watch

On a Hermes build that has plugin Automation Blueprints (not v0.21.4 or v0.21.5), the plugin registers `jp-egov-law:weekly-amendments` on `/blueprint` and the dashboard. It does not create a cron job. The agent can schedule it. When you create a job from that blueprint, the default is Monday at 09:00 in Hermes's timezone, or on the computer's clock if no timezone is set. It is not converted to Japan time. Each run is one unattended agent turn that is asked to call `egov_law_revisions` once. A turn that calls a tool is at least two model requests. There is no daily cap. Scheduling it twice creates two jobs.

The message is about a promulgated amendment or repeal that is not in force yet. Bills still in the Diet, and a separate 施行令 or 施行規則, are outside the check. A law that is already repealed is said to be repealed, not "no change". The prompt asks the model to include `source.attribution` unchanged. It also asks the model never to answer `[SILENT]`. That is not a guarantee: if no message arrives, check `hermes cron runs`. Silence is not "no amendment".

e-Gov read errors (`timeout`, `network`, `upstream`, `bad_response`) are to be repeated on each weekly run. A bad law name is not an outage. `bad_request` and `not_found` mean e-Gov rejected the lookup. A response over 8 MB is `too_large`, not an outage. You can go up to 7 days without a notice, because the job runs once a week.

Each request to e-Gov waits at most 15 seconds, and this process sends at most one per second. A tool call makes at most six requests, and none when the arguments are rejected before any request, so a hung e-Gov ends that call in about a minute and a half. This plugin does not cap how long the model turn waits.

Delivery is `origin`: the chat where you created the job, or the home channel when that chat was not recorded (the dashboard drops it). If there is no such chat and no home channel, Hermes keeps the text on the job (`last_output`) and does not send it, and does not mark that as a failure. Read it with `hermes cron runs`. This plugin does not take a destination, so a schedule word cannot be stored as one. To send it somewhere else after the job exists, use Hermes's own `hermes cron edit <id> --deliver ...`. This plugin does not change an existing destination.

The job is an ordinary cron job in that profile's `cron/jobs.json` (`<HERMES_HOME>/cron/jobs.json`, or `profiles/<name>/cron/jobs.json`). It is not under `plugin-data`. Uninstalling the plugin removes the blueprint from the catalog and leaves the job. Unschedule it with `hermes cron remove <id>`. The job is not a sandbox: it is a normal agent turn. The cron prompt stores the law name and the schedule. This plugin writes no speaker name or id. When the agent creates the job from a chat, Hermes stores that chat's origin on the job: platform, chat id, chat name, thread id, user id, and scope id, for the values that session has. Creating it from the dashboard drops that origin.

`egov_law_search`, `egov_law_article`, and `egov_law_revisions` stay available on v0.21.4 and v0.21.5, where the blueprint is skipped. Those tools are on for every platform by default, including gateways, so a guest a gateway admits can call them. Disable a platform with `hermes tools`. `tests/` is not loaded by `register()`.

## Network, data and privacy

- **One host.** The plugin sends HTTPS GET requests only to `https://laws.e-gov.go.jp`, under the
  path `/api/2`, and nowhere else. The request contains what the agent looks up (a law name, article
  number or search phrase).
  Redirects are followed only to `https://laws.e-gov.go.jp`; one to another host or to plain HTTP is refused.
- **No credentials.** The API is public; the plugin reads no environment variables and stores no keys.
  (Python's `urllib` still uses the system proxy settings such as `HTTPS_PROXY`.)
- **Nothing written by the plugin.** No plugin-data files, no database, no telemetry. Name-to-law-ID
  answers and the law's own 附則 articles read for `text_notes` are kept in process memory (at most 256
  entries together, oldest dropped first) and disappear when Hermes exits. Scheduling the weekly
  blueprint stores a Hermes cron job, which remains after uninstall (`hermes cron remove <id>`).
- **Never waits for input.** No prompts. A tool call makes at most six requests, and none when the
  arguments are rejected before any request. Those requests are a name lookup, the text, the 附則 check,
  a comparison, and error details such as the previous version of a missing article. The process sends
  at most one per second, each with a 15-second socket timeout and an 8 MB response cap.
  Even when e-Gov hangs, a call ends with an error in about a minute and a half, so cron jobs and the
  gateway are not stuck.
- **Gentle on e-Gov.** The one-request-per-second pace is built in; e-Gov is a public service.
- **No self-updates, no shell commands, no background processes.**

## Source and attribution

Law data is published by the Digital Agency of Japan on e-Gov. The terms of use of e-gov.go.jp and
its subdomains ([利用規約](https://www.e-gov.go.jp/terms), checked 2026-10-02) apply the Public Data
License 1.0 (公共データ利用規約 第1.0版) and ask users to:

1. show the source, e.g. `出典：e-Gov法令検索（https://laws.e-gov.go.jp/）`, and
2. when content is edited or processed, say so and who did it, without presenting the result as the
   government's unedited original.

Every successful tool result carries `source.attribution`
(`出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）`)
and `retrieved_on`; the `egov_law_article` description and the `source.note` in every result ask the
model to show it with any law text it quotes.
The plugin retrieves law text; it does not give legal advice.

## Limitations

- `egov_law_article` reads the main provisions (本則) and the law's own supplementary provisions (附則),
  including articles later inserted into them such as 労基法 `附則第143条`. The separate 附則 that each
  amending law carries (where many transitional measures of later reforms live), appended tables (別表)
  and forms are not returned. Where e-Gov holds only an excerpt (抄) of a 附則, `text_notes` says so.
- Articles deleted as a range (第十条から第十二条まで　削除) cannot be fetched one by one.
- An article renumbered or deleted by an amendment is `article_not_found` under its old number, and
  the tool does not give the new number. When `as_of` is left out, the tool looks once at the version
  in force the day before the current version took effect. If the article is there, the error says so:
  the date it last existed, the date and the amending law (title and number) of the amendment that moved
  or deleted it, the old caption (`previous_caption`), and a `next_step` to search for the caption's
  words with `mode="text"` or check the e-Gov page. Example: 労働施策総合推進法 (パワハラ防止法) 第三十条の二,
  moved or deleted by the amendment that took effect on 2026-10-01. An article that went in an earlier
  amendment gets the plain error; reading it with `as_of` before that amendment still works.
- `mode="text"` snippets come without article numbers; use them to find the law, then read the article.
- Tables inside an article are flattened to one line per row with `｜` between cells, and the result
  says so in `text_notes` (outside the law text). Tables with multi-row headers do not line up column by column.
- In revisions, `title_names_this_law` only says whether the amending law's title names this law
  (as a word of its own, current or former title), and `follow_up_of` only names X in a title
  「〈X〉の施行に伴う…」. Neither says how much the law changes: a reform titled after another law can
  change this one a lot.
- Revisions say when and by which law a law changes, not which articles change. Check an article with
  the row's `check` pair (changed or not, and the diff, in one call). Each row also says `change`:
  an amendment, a repeal (`scheduled_repeal` at the top), or the law's own provisions taking effect.
  For a law whose repeal has taken effect, `in_force_now` is empty and `repealed_on`, the message and
  `next_step` say so, with `as_of` = the day before the repeal for reading its last wording.
- For a scheduled amendment whose date the law leaves to a cabinet order (`date_fixed: false`, see
  `enforcement_note`), e-Gov shows a provisional date; for 「…を超えない範囲内において政令で定める日」 it is
  the latest possible day, so the change may come earlier than amendments listed before it.
- e-Gov labels the JSON form of its law-text API as a trial (試行版). If e-Gov changes it, the
  plugin returns an error rather than wrong text, and the fix is a new release.
- When e-Gov marks no version as current (it happens for a while after a new version takes effect),
  `egov_law_revisions` picks the newest version whose enforcement date has passed.

## Development

Test dependencies: pytest 8 and PyYAML 6.

```bash
pytest -q                    # offline tests + live tests when e-Gov answers (about 35 paced requests). If it cannot be reached, the live tests are skipped.
pytest -q -m "not live"      # offline only (recorded responses in tests/fixtures)
python tests/record_fixtures.py   # re-record the responses the offline tests replay
hermes plugins validate . --install-deps   # the check the Hermes plugin catalog runs
```

Offline tests were run on Python 3.12 and 3.14. Python 3.11 was not checked. Hermes asks for Python 3.11 or newer. No runtime dependencies.

## 日本語

e-Gov 法令 API（v2）を活用して、Hermes Agent から日本の法令を引けるようにしたプラグインです。
データはデジタル庁の e-Gov 法令検索から取り、APIキーもアカウントも要りません。

- 条文を読む（`egov_law_article`）：「労基法32条」「民法第四百十五条」「個人情報保護法 第二十七条」のように、
  法令名・略称・法令番号と条番号を渡します。条番号は 第32条／32条／三十二条／32の2 のどれでも通り、1回で条文が返ります。
  法律本体の附則（後から足された附則第143条なども含む）も「附則第143条」の形で読めます。改正法それぞれの附則は読めません。
  経過措置の附則がその条を当分の間読み替えているときは、`text_notes` がその附則の条を示します。
- 改正で条文が変わるか確かめる：`egov_law_article` に `as_of`（施行日の前日）と `compare_with`（施行日）を付けると、差分が同じ1回で返ります。
  比較先の HTTP 400 で code が `400021` のとき、または HTTP 404 で code が `404004` のとき（その日の法令本文ファイルが無い）は、本文を残したまま「その日には無い」と返します。`400038`（要素名の誤り）と、それ以外の 400 と 404 は、呼び出し全体が失敗し、文言が変わったことにはしません。
  この2つの日付は `egov_law_revisions` の各改正の `check` に入っています。
- 法令を探す（`egov_law_search`）：法令名・略称で探します（既定）。`mode="text"` にすると本文の語句から探します。
- 改正と施行日を確かめる（`egov_law_revisions`）：いま施行中の版、施行予定の改正と日付、過去の版を返します。
  `next_amendment` は最も近い予定の改正です。`title_names_this_law` は改正法の題名にこの法律の名前があるか、
  `follow_up_of` は「〈X〉の施行に伴う…」という題名の X です。どちらも中身がどれだけ変わるかは表しません。
  条文が変わるかは `check` の日付で確かめてください。廃止の予定は `scheduled_repeal` に出ます。
  すでに廃止された法律は `in_force_now` が空になり、`repealed_on` と、最後の文言を読むための `as_of`（廃止日の前日）を返します。

Hermes に Automation Blueprints の登録口がある版では、`jp-egov-law:weekly-amendments` をひな型として登録するだけで、cron ジョブは作りません。エージェント自身もこのひな型からジョブを作れます。2回作るとジョブが2つできます。利用者がひな型からジョブを作ると、週1回（既定は月曜 09:00。Hermes のタイムゾーン、未設定ならコンピュータの時計。日本時間へは変換しません）モデルが1ターン動き、`egov_law_revisions` を1回呼ぶよう頼まれます。道具を呼ぶとそのターンはモデルへの要求が2回以上になり、日次の上限はありません。届け先は作ったチャット、無ければホームチャネルです。どちらも無いときはジョブに残り、送信せず、失敗にもしません。v0.21.4 と v0.21.5 にはこの口が無く、3つの道具だけが動きます。届かないことは「改正なし」ではありません。`hermes cron runs` を見てください。プラグインを消しても cron は残るので、`hermes cron remove <id>` で消します。このプラグイン自身は話者の名前や ID を書きません。エージェントがチャットからジョブを作ると、Hermes がそのジョブに、そのチャットの識別子（プラットフォーム、チャット ID、チャット名、スレッド ID、ユーザー ID、スコープ ID。セッションにあるもの）を残します。ダッシュボードから作ると、その識別子は捨てます。

導入1行、動作確認1行です。

```bash
hermes plugins install TakeshiTGAL/hermes-plugin-egov-law --enable
hermes chat -Q -q "労働基準法第32条の条文を見せて"
```

略称は e-Gov の略称（労基法・個人情報保護法・安衛法など）に加え、個情法・特商法・下請法・雇保法・育介法・育児休業法・
パート法・パート有期法・パートタイム・有期雇用労働法・フリーランス法・フリーランス新法・派遣法・均等法・憲法・健保法・厚年法・
電帳法・パワハラ防止法・高年法・労基則・労規則・雇保則を組み込んでいます。

Hermes は v0.21.4 以上が必要です（`hermes --version` で確認）。古い場合は先に `hermes update` を打ってください。
`--enable` を付け忘れたら `hermes plugins enable jp-egov-law` を打ってください。
GitHub ではなく手元から入れる場合は、git clone したディレクトリを
`hermes plugins install file:///path/to/hermes-plugin-egov-law --enable` で指定します（「Using insecure/local URL scheme」という警告が出ますが、導入されます）。
メッセージ連携（gateway）を使っている場合は、`hermes gateway restart` を一度打ってください。

通信先は `https://laws.e-gov.go.jp` の `/api/2` だけで、e-Gov 以外へは何も送りません。ファイルも書きません。
1回のツール呼び出しで e-Gov への問い合わせは最大6回です（引数が悪く、通信の前に拒んだときは0回）。1秒に1回までに抑えています。1回ごとに通信が15秒止まれば打ち切るので、
e-Gov が止まっていても入力待ちにはならず、1分半ほどでエラーが返ります。
返り値には出典表示 `出典：e-Gov法令検索（https://laws.e-gov.go.jp/）のデータを hermes-plugin-egov-law が取得・整形（条単位の抽出等）`
が入ります。e-Gov の利用規約（公共データ利用規約 第1.0版）に沿って、条文を見せるときはこの出典も一緒に示してください。

できないこと：
- 改正法それぞれの附則・別表・様式は返しません（別表・様式は `not_covered` のエラーで e-Gov のページを案内します）。
- 号・本文・ただし書だけを取り出すことはできません（項までを返し、注記を付けます）。範囲で削除された条は1条ずつ取れません。
- 本文検索（`mode="text"`）の抜粋には条番号が付きません。過去の版は 2017-04-01 以降だけです。
- 施行日を政令に任せた改正（`date_fixed: false`）は、e-Gov の仮の日付です。「…を超えない範囲内」の場合は最も遅い日です。
- 改正で番号が変わった条や削除された条は、旧い番号では `article_not_found` になり、新しい番号は返しません。
  `as_of` を付けないときは、現行版の施行日の前日の版を1回だけ確かめます。そこに条があれば、いつまであったか・どの改正（施行日と改正法の題名・番号）で動いたか・旧い見出し（`previous_caption`）をエラーに入れ、見出しの語で `mode="text"` 検索するか e-Gov のページで確かめるよう案内します。
- 条文中の表は1行ずつ「｜」区切りに平らにします。e-Gov の本文取得 API は試行版の扱いです。
本プラグインは条文を取り出す道具で、法的助言はしません。

## How this was checked

Offline tests replay recorded e-Gov responses. They were run on Python 3.12 and 3.14. Python 3.11 was not checked. A later run of five models, 40 sessions (39 answered) and 158 turns, counted 22 `bypass` hits: a built-in tool (web_search, read_file, terminal, or another in that set) was used instead of this plugin. Separately, `missing_tool` was 6 (the reply did not call the plugin tool that turn required) and `unsourced_claim` was 1 (the reply said the text had been fetched without a plugin call). The `read-law` skill asks the model to pass `source.retrieved_at`, `source.url`, and `source.as_of` when the tool returned them, and to say the text was not fetched instead of writing an article from memory. That request is not a guarantee. The skill is registered with `requires_toolsets: [egov_law]`, so a host that filters skills by toolset omits it when that toolset is off. A host that does not pass toolset info still lists the skill.

## どう確かめているか

オフラインのテストは、記録した e-Gov の応答を再生する。走らせたのは Python 3.12 と 3.14 で、3.11 は確かめていない。あとからの 5 モデル・40 セッション（答えたもの 39）・158 ターンでは、`bypass` が 22 件だった。プラグインの代わりに本体の道具（web_search、read_file、terminal など）を使った hit である。別に、`missing_tool` は 6 件（呼ぶべきプラグインの道具を呼ばずに答えた）、`unsourced_claim` は 1 件（プラグインを呼ばずに、取得したと名乗った）。`read-law` の skill は、道具が返した `source.retrieved_at`・`source.url`・返したときだけ `source.as_of` を一緒に出すこと、呼んでいないときは取得していないと言うことをモデルに求める。必ずそうする保証ではない。skill は `requires_toolsets: [egov_law]` で登録するので、道具セットで絞り込む Hermes は、そのセットが無いとき skill を出さない。道具セットの情報を渡さない Hermes は、skill を出したままにする。

## License

MIT. See [LICENSE](LICENSE). Law data: e-Gov 法令検索, Digital Agency of Japan, under PDL 1.0.
