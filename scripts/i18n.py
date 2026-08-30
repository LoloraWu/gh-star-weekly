#!/usr/bin/env python3
"""介面字串。新增語言只要多一個 key，render.py 不用改。"""

BASE = "/gh-star-weekly/"          # GitHub Pages 的 project 路徑
LANGS = ["en", "zh"]
OTHER = {"en": "zh", "zh": "en"}
SWITCH_LABEL = {"en": "中文", "zh": "English"}

STR = {
"en": {
  "html_lang": "en",
  "title": "GitHub Star Weekly",
  "generated": "generated", "source": "source", "unauthed": " (unauthenticated)",
  "kind_public": "facts only", "kind_private": "full",
  "created_days": "created in the last {d} days",
  "hits": "<b>{n:,}</b> matches · top {m}",
  "per_day": "★/day", "age": "{d} days old",
  "no_desc": "— the author wrote no description —",
  "no_what": "(no summary yet)",
  "growth_title": "Weekly star growth",
  "growth_pending_q": "snapshot diff · available from the <b>second</b> run",
  "growth_pending_h": "No data this run — this is expected",
  "growth_pending_p": ("Weekly growth is this run's snapshot minus the previous one. "
                       "With only one snapshot on file there is nothing to diff. "
                       "Once a second snapshot lands, this section fills in with real numbers."),
  "growth_q": "baseline <b>{base}</b> · ranked by absolute gain",
  "th_rank": "#", "th_repo": "repo", "th_delta": "gained", "th_pct": "growth", "th_stars": "stars",
  "foot_vel": ("<b>★/day</b> is total stars ÷ days since creation — it separates "
               "\"4,000 stars in three days\" from \"4,000 stars over three years\". "
               "Bars are normalized <b>within each board</b>."),
  "foot_facts": ("<b>This page states only verifiable facts</b>: account registration date, "
                 "follower count, public repo count, license, whether the board's keyword "
                 "actually appears in the README — all straight from the GitHub API. "
                 "Drawing a conclusion is left to you."),
  "foot_judge": "<b>Tags and \"why it ranked\" are judgements, not facts.</b> Verify before acting.",
  "foot_src": 'Data and source: <a href="https://github.com/LoloraWu/gh-star-weekly">gh-star-weekly</a>',
  # --- facts line ---
  "f_org": "organization", "f_user": "personal account",
  "f_owner": "Owner: {t} · registered {d} ({age})",
  "f_years": "{y:.1f} yrs", "f_days": "{d} days",
  "f_followers": "{n:,} followers", "f_repos": "{n:,} public repos",
  "f_lic_yes": "licensed", "f_lic_no": "no license",
  "f_nodesc": "no description", "f_fork": "is a fork",
  "f_nokw": "“{kw}” appears nowhere in name / description / README / topics",
  "f_same": "same owner holds {n} slots on this board",
},
"zh": {
  "html_lang": "zh-Hant",
  "title": "GitHub 星數週榜",
  "generated": "產出", "source": "來源", "unauthed": "（未認證）",
  "kind_public": "公開版", "kind_private": "完整版",
  "created_days": "近 {d} 天建立",
  "hits": "命中 <b>{n:,}</b> 個 · 取前 {m}",
  "per_day": "★/天", "age": "建立 {d} 天",
  "no_desc": "— 作者沒有寫任何 description —",
  "no_what": "（尚無說明）",
  "growth_title": "既有 repo 週成長榜",
  "growth_pending_q": "快照 diff · <b>第二次</b>執行起才有",
  "growth_pending_h": "本次無資料 — 這是預期行為",
  "growth_pending_p": ("週成長要靠「本次快照 − 上次快照」算出來。目前只有一份快照，算不出 diff。"
                       "第二份快照落地後，這一區就會填上真實數字。"),
  "growth_q": "對照基準 <b>{base}</b> · 依絕對增量排序",
  "th_rank": "#", "th_repo": "REPO", "th_delta": "本次增加", "th_pct": "成長率", "th_stars": "總星數",
  "foot_vel": ("<b>★/天</b> = 總星數 ÷ 建立天數，用來區分「三天四千星」與「三年四千星」。"
               "強度條在<b>各分類內部</b>正規化。"),
  "foot_facts": ("<b>這一版只陳述可驗證的事實</b>：帳號註冊日、follower 數、公開 repo 數、"
                 "授權條款、關鍵字是否出現在 README —— 全部由 GitHub API 取得。"
                 "要不要據此下結論，請讀者自己判斷。"),
  "foot_judge": "<b>標籤與「為何上榜」是判斷不是事實</b>，行動前請自行覆核。",
  "foot_src": '資料與程式碼：<a href="https://github.com/LoloraWu/gh-star-weekly">gh-star-weekly</a>',
  "f_org": "組織", "f_user": "個人帳號",
  "f_owner": "擁有者 {t} · 註冊 {d}（{age}）",
  "f_years": "{y:.1f} 年", "f_days": "{d} 天",
  "f_followers": "{n:,} followers", "f_repos": "{n:,} 個公開 repo",
  "f_lic_yes": "有授權條款", "f_lic_no": "無授權條款",
  "f_nodesc": "無 description", "f_fork": "是 fork",
  "f_nokw": "名稱／描述／README／topics 皆未出現「{kw}」",
  "f_same": "同一擁有者在本榜佔 {n} 席",
},
}
