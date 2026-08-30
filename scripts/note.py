#!/usr/bin/env python3
"""把本週榜單寫進 Obsidian vault 的滾動筆記（最新一週在最上面）。

這份是**私人**輸出，所以含判斷標籤——vault 不是公開的。
用法： python3 scripts/note.py [YYYY-MM-DD]
"""
import json, os, sys, datetime, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.environ.get("VAULT", "/Users/lora/Documents/obs_vault/repo/GD_ObsidianVault")
NOTE = f"{VAULT}/01_inbox/GitHub 週榜.md"
DATE = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
PAGE = "https://lolorawu.github.io/gh-star-weekly/zh/"  # 中文版；英文版在站台根目錄

# 全部標籤都會標在條目上；但只有「結構性問題」才進頂端的 callout，
# 否則 40 篇裡有一半會被列進去，等於沒有提示效果。
FLAG = {"scam": "⚠️ 疑似冒牌", "mistag": "誤掛主題", "flood": "同質洗版",
        "novelty": "獵奇", "fame": "名人效應", "trend": "蹭熱點"}
ALERT = ("scam", "mistag", "flood")


def first_sentence(t, n=64):
    s = re.split(r"[。\n]", t.strip())[0]
    return s[:n] + ("…" if len(s) > n else "")


def build_section(raw, notes):
    L = [f"## {DATE}", ""]

    flagged = []
    for c in raw["cats"].values():
        for r in c["new"]:
            tag = notes.get(r["name"], {}).get("tag")
            if tag in ALERT:
                flagged.append((FLAG[tag], r["name"], c["label"]))
    if flagged:
        L.append("> [!tip] 本週值得注意")
        for lab, name, cat in flagged:
            L.append(f"> - **{lab}** — `{name}`（{cat}）")
        L.append("")

    for c in raw["cats"].values():
        L.append(f"### {c['label']}")
        for r in c["new"][:3]:
            n = notes.get(r["name"], {})
            tag = n.get("tag")
            mark = f" ⟨{FLAG[tag]}⟩" if tag in FLAG else ""
            L.append(f"- [{r['name']}]({r['url']}) — **{r['stars']:,}★**"
                     f"（{r['vel']:,.1f}★/天，建立 {r['age_days']} 天）{mark}")
            if n.get("what"):
                L.append(f"\t- {first_sentence(n['what'])}")
        L.append("")

    g = raw.get("growth") or {}
    if any(g.values()):
        L.append("### 週成長")
        for key, rows in g.items():
            if not rows:
                continue
            lab = raw["cats"].get(key, {}).get("label", key)
            top = "、".join(f"`{x['name']}` +{x['delta']:,}" for x in rows[:3])
            L.append(f"- **{lab}**：{top}")
        L.append("")
    else:
        L.append("### 週成長")
        L.append(f"- 無資料（對照基準：{raw.get('growth_base') or '尚無上週快照'}）")
        L.append("")

    L.append(f"- 完整榜單（40 篇，含每篇說明）→ {PAGE}")
    L.append("")
    return "\n".join(L)


def main():
    raw = json.load(open(f"{ROOT}/data/raw/{DATE}.json"))
    npath = f"{ROOT}/data/notes/{DATE}.json"
    notes = json.load(open(npath)) if os.path.exists(npath) else {}
    section = build_section(raw, notes)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if os.path.exists(NOTE):
        s = open(NOTE, encoding="utf-8").read()
        s = re.sub(r'^updated: .*$', f'updated: "{now}"', s, count=1, flags=re.M)
        # 同一天重跑就覆蓋那一段，否則插在分隔線後（最新在最上面）
        pat = re.compile(rf"^## {re.escape(DATE)}\n.*?(?=^## \d{{4}}-\d{{2}}-\d{{2}}\n|\Z)",
                         re.M | re.S)
        if pat.search(s):
            s = pat.sub(section, s, count=1)
        else:
            marker = "\n---\n\n"
            i = s.index(marker) + len(marker)
            s = s[:i] + section + s[i:]
    else:
        s = (f'---\ncreated: "{now}"\nupdated: "{now}"\n'
             f'imageNameKey: gh-star-weekly\naliases:\n  - GitHub 週榜\ntags: []\n---\n\n'
             f'# GitHub 週榜\n\n✅ ACTION\n\n'
             f'- 完整網頁（每週更新）→ {PAGE}\n'
             f'- 這條管線怎麼運作、為什麼不用 Perplexity → [[GitHub 週榜自動化]]\n'
             f'- ⚠️ 標籤是 LLM 判斷不是事實，行動前自行覆核\n\n---\n\n' + section)

    os.makedirs(os.path.dirname(NOTE), exist_ok=True)
    open(NOTE, "w", encoding="utf-8").write(s)
    print(f"note -> {NOTE}")


if __name__ == "__main__":
    main()
