#!/usr/bin/env python3
"""渲染 HTML。兩種模式：

  --public   只印確定性事實，不含任何判斷 → docs/（GitHub Pages）
  （預設）    含 LLM 判斷與標籤 → output/（自己看）

用法： python3 scripts/render.py [--public] [YYYY-MM-DD]
"""
import json, os, sys, html, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
PUBLIC = "--public" in sys.argv
DATE = args[0] if args else datetime.date.today().isoformat()
e = html.escape

TAGS = {"real": ("真材實料", "real"), "novelty": ("獵奇", "novelty"),
        "fame": ("名人效應", "fame"), "trend": ("蹭熱點", "trend"),
        "flood": ("同質洗版", "flood"), "mistag": ("誤掛主題", "mistag"),
        "scam": ("疑似冒牌", "scam")}

CSS = open(f"{ROOT}/scripts/style.css", encoding="utf-8").read()


def md(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(s))


def facts_line(sg):
    """全部可驗證。公開版靠這一行讓讀者自己判斷。"""
    p = []
    t = "組織" if sg["owner_type"] == "Organization" else "個人帳號"
    age = sg["owner_age_days"]
    if age is not None:
        yrs = age / 365
        agestr = f"{yrs:.1f} 年" if yrs >= 1 else f"{age} 天"
        p.append(f"擁有者 {t} · 註冊 {sg['owner_created']}（{agestr}）")
    else:
        p.append(f"擁有者 {t}")
    if sg["owner_followers"] is not None:
        p.append(f"{sg['owner_followers']:,} followers")
    if sg["owner_repos"] is not None:
        p.append(f"{sg['owner_repos']:,} 個公開 repo")
    p.append("有授權條款" if sg["has_license"] else "無授權條款")
    if not sg["has_desc"]:
        p.append("無 description")
    if sg["is_fork"]:
        p.append("是 fork")
    if sg["keyword_present"] is False:
        p.append(f"名稱／描述／README／topics 皆未出現「{sg['keyword']}」")
    if sg["same_owner_in_board"] > 1:
        p.append(f"同一擁有者在本榜佔 {sg['same_owner_in_board']} 席")
    return " · ".join(p)


def rows(cat, notes):
    items = cat["new"]
    mx = max((r["vel"] for r in items), default=1) or 1
    out = []
    for i, r in enumerate(items, 1):
        n = notes.get(r["name"], {})
        what = n.get("what", "（尚無說明）")
        kind = n.get("tag", "real")
        label, cls = TAGS.get(kind, TAGS["real"])
        pill = "" if PUBLIC else f'<span class="pill {cls}">{label}</span>'
        judge = "" if PUBLIC or not n.get("verdict") else \
            f'<div class="why {cls}"><b>為何上榜 ▸</b> {md(n["verdict"])}</div>'
        chips = "".join(f'<span class="chip">{e(t)}</span>'
                        for t in ([r["lang"]] if r["lang"] else []) + r["topics"][:4])
        orig = (f'<div class="origdesc">{e(r["desc"])}</div>' if r["desc"]
                else '<div class="origdesc">— 作者沒有寫任何 description —</div>')
        pct = max(r["vel"] / mx * 100, 2)
        out.append(f"""      <div class="row">
        <div class="rank">{i:02d}</div>
        <div class="repo">
          <div class="titleline">
            <a href="{e(r['url'])}" target="_blank" rel="noopener">{e(r['name'])}</a>
            {pill}
          </div>
          {orig}
          <div class="what">{md(what)}</div>
          {judge}
          <div class="facts">{e(facts_line(r["signals"]))}</div>
          <div class="chips">{chips}</div>
        </div>
        <div class="data">
          <div class="stars">{r['stars']:,}<span> ★</span></div>
          <div class="vel">{r['vel']:,.1f} ★/天</div>
          <div class="bar"><i style="width:{pct:.1f}%"></i></div>
          <div class="age">建立 {r['age_days']} 天</div>
        </div>
      </div>""")
    return "\n".join(out)


def growth_section(raw):
    g = raw.get("growth") or {}
    base = raw.get("growth_base")
    if not base or not any(g.values()):
        return """  <section id="growth">
    <div class="sechead"><h2>既有 repo 週成長榜</h2>
      <div class="q">快照 diff · <b>下週</b>才有數字</div></div>
    <div class="pending"><h3>本週無資料 — 這是預期行為</h3>
      <p>週成長要靠「本週快照 − 上週快照」算出來。目前只有一份快照，算不出 diff。
         下一次執行、第二份快照落地後，這一區就會填上真實數字。</p></div>
  </section>"""
    blocks = []
    for key, rowsg in g.items():
        if not rowsg:
            continue
        label = raw["cats"].get(key, {}).get("label", key)
        trs = "".join(
            f'<tr><td class="r">{i:02d}</td><td class="n">'
            f'<a href="https://github.com/{e(x["name"])}" target="_blank" rel="noopener">{e(x["name"])}</a></td>'
            f'<td class="num up">+{x["delta"]:,}</td>'
            f'<td class="num">{x["pct"]:+.1f}%</td>'
            f'<td class="num">{x["stars"]:,}</td></tr>'
            for i, x in enumerate(rowsg, 1))
        blocks.append(
            f'<h3 class="gsub">{e(label)}</h3><div class="tablewrap"><table>'
            f'<thead><tr><th>#</th><th>REPO</th><th class="num">本週增加</th>'
            f'<th class="num">成長率</th><th class="num">總星數</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div>')
    return f"""  <section id="growth">
    <div class="sechead"><h2>既有 repo 週成長榜</h2>
      <div class="q">對照基準 <b>{e(base)}</b> · 依絕對增量排序</div></div>
    {''.join(blocks)}
  </section>"""


def main():
    raw = json.load(open(f"{ROOT}/data/raw/{DATE}.json"))
    npath = f"{ROOT}/data/notes/{DATE}.json"
    notes = json.load(open(npath)) if os.path.exists(npath) else {}
    if not notes:
        print("⚠️  沒有評註檔，只會渲染事實層（先跑 annotate.py）")

    navs = "".join(f'<a href="#{k}">{e(c["label"])}</a>' for k, c in raw["cats"].items())
    legend = "" if PUBLIC else '<div class="legend">' + "".join(
        f'<span class="pill {c}">{l}</span>' for l, c in TAGS.values()) + "</div>"

    secs = []
    for k, c in raw["cats"].items():
        secs.append(f"""  <section id="{k}">
    <div class="sechead"><h2>{e(c['label'])}</h2>
      <div class="q">近 {c['days']} 天建立 · {e(c['note'])}<br>命中 <b>{c['total']:,}</b> 個 · 取前 {len(c['new'])}</div>
    </div>
    <div class="rows">
{rows(c, notes)}
    </div>
  </section>""")

    kind = "公開版" if PUBLIC else "完整版"
    disclaimer = ("<span><b>這一版只陳述可驗證的事實</b>："
                  "帳號註冊日、follower 數、公開 repo 數、授權條款、關鍵字是否出現在 README —— "
                  "全部由 GitHub API 取得。要不要據此下結論，請讀者自己判斷。</span>"
                  if PUBLIC else
                  "<span><b>標籤與「為何上榜」是判斷不是事實</b>，行動前請自行覆核。</span>")

    body = f"""
<div class="wrap">
  <header class="mast">
    <h1>GitHub 星數週榜</h1>
    <div class="meta">
      <span>產出 <b>{e(raw['generated'])}</b></span>
      <span>來源 <b>GitHub Search API</b>{'' if raw.get('authed') else '（未認證）'}</span>
      <span>{kind}</span>
    </div>
    {legend}
  </header>
  <nav>{navs}<a href="#growth">成長榜</a></nav>
{chr(10).join(secs)}
{growth_section(raw)}
  <footer>
    <span><b>★/天</b> = 總星數 ÷ 建立天數，用來區分「爆紅」與「慢慢累積」。強度條在<b>各分類內部</b>正規化。</span>
    {disclaimer}
    <span>資料與程式碼：<a href="https://github.com/LoloraWu/gh-star-weekly">gh-star-weekly</a></span>
  </footer>
</div>"""

    page = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>GitHub 星數週榜 {DATE}</title>\n<style>\n{CSS}\n</style>\n'
            f'</head>\n<body>{body}\n</body>\n</html>\n')

    if PUBLIC:
        os.makedirs(f"{ROOT}/docs/archive", exist_ok=True)
        for p in (f"{ROOT}/docs/index.html", f"{ROOT}/docs/archive/{DATE}.html"):
            open(p, "w", encoding="utf-8").write(page)
        print(f"public -> docs/index.html + docs/archive/{DATE}.html")
    else:
        os.makedirs(f"{ROOT}/output", exist_ok=True)
        p = f"{ROOT}/output/{DATE}.html"
        open(p, "w", encoding="utf-8").write(page)
        print(f"private -> output/{DATE}.html")


if __name__ == "__main__":
    main()
