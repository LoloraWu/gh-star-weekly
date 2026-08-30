#!/usr/bin/env python3
"""評註層：在 mini 上跑 Claude Code headless，讀 README 產出中文說明與判斷。

分兩塊輸出，因為公開版與私人版的尺度不同：
  what    = 這個 repo 做什麼（事實性摘要，公開版也用）
  verdict = 為何上榜的判斷 + tag（**只進私人版**）

用法：  python3 scripts/annotate.py [YYYY-MM-DD]
"""
import json, os, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
RAW = f"{ROOT}/data/raw/{DATE}.json"
OUT = f"{ROOT}/data/notes/{DATE}.json"

TAGS = ["real", "novelty", "fame", "trend", "flood", "mistag", "scam"]

PROMPT = """你在替一份 GitHub 週榜寫評註。以下是本週上榜 repo 的資料（含 README 前段與確定性事實訊號）。

針對每一個 repo，輸出兩個欄位：

1. `what`：這個 repo 做什麼。繁體中文，2～3 句，**只根據 README 陳述事實**，不要評價、不要形容詞堆砌。這段會出現在公開網頁上。
2. `what_en`：同一件事的英文版，2～3 句。**不是逐字翻譯**，是直接用英文把它講清楚——英文讀者看的是這句，寫得像原生英文技術文件，不要中式英文。同樣只陳述事實。
3. `verdict`：它為什麼會上榜。繁體中文，1～3 句，可以下判斷。這段只給作者自己看。
4. `tag`：從這個清單選一個 —— %s
   real=有實質內容／novelty=獵奇整活／fame=作者知名度帶動／trend=蹭當紅題材／
   flood=同期多個高度雷同專案之一／mistag=掛了不屬於它的 topic／scam=疑似冒名或釣魚

判斷 tag 時請善用 signals 欄位：owner_age_days 很小 + owner_followers 接近 0 +
owner_repos 很少 + has_license 為 false，同時 repo 名稱蹭知名品牌 → 高度可疑。
keyword_present 為 false 表示分類關鍵字沒出現在名稱/描述/README/topics 任何地方。
same_owner_in_board > 1 表示同一帳號在本榜佔了多席。

只輸出 JSON，格式為 {"repo/full_name": {"what": "...", "what_en": "...", "verdict": "...", "tag": "..."}, ...}
不要有任何其他文字、不要包在 markdown code fence 裡。

資料：
%s
"""


def main():
    if not os.path.exists(RAW):
        sys.exit(f"找不到 {RAW}，請先跑 fetch.py")
    raw = json.load(open(RAW))

    items = []
    for c in raw["cats"].values():
        for r in c["new"]:
            items.append({
                "name": r["name"], "desc": r["desc"], "lang": r["lang"],
                "topics": r["topics"], "stars": r["stars"], "vel": r["vel"],
                "age_days": r["age_days"], "category": c["label"],
                "readme": r.get("readme", "")[:700], "signals": r["signals"],
            })

    prompt = PROMPT % (" / ".join(TAGS), json.dumps(items, ensure_ascii=False))
    print(f"送出 {len(items)} 個 repo 給 claude -p …")

    # claude -p 的耗時變動很大（實測 5.6 分鐘～超過 15 分鐘），這裡要留足餘裕。
    # 必須小於外層 shell 的 1800 秒，否則會被外層砍掉、看不到這裡的錯誤訊息。
    try:
        p = subprocess.run(["claude", "-p", prompt],
                           capture_output=True, text=True, timeout=1500)
    except subprocess.TimeoutExpired:
        sys.exit("claude -p 超過 1500 秒未回應，本次放棄（下週會重跑）")
    if p.returncode != 0:
        sys.exit(f"claude 失敗：{p.stderr[:500]}")

    txt = p.stdout.strip()
    if txt.startswith("```"):
        txt = txt.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        notes = json.loads(txt)
    except json.JSONDecodeError as ex:
        open(f"{ROOT}/output/annotate-raw.txt", "w").write(txt)
        sys.exit(f"回傳不是合法 JSON（原文存到 output/annotate-raw.txt）：{ex}")

    missing = [i["name"] for i in items if i["name"] not in notes]
    no_en = [k for k, v in notes.items() if not v.get("what_en")]
    if no_en:
        print(f"⚠️  {len(no_en)} 筆缺英文說明：{no_en[:5]}")
    bad = [k for k, v in notes.items() if v.get("tag") not in TAGS]
    if missing:
        print(f"⚠️  {len(missing)} 個 repo 沒拿到評註：{missing[:5]}")
    if bad:
        print(f"⚠️  tag 不在清單內：{bad[:5]}")

    json.dump(notes, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"notes -> data/notes/{DATE}.json（{len(notes)} 筆）")


if __name__ == "__main__":
    main()
