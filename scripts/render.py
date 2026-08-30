#!/usr/bin/env python3
"""渲染 HTML。

  --public   只印確定性事實、不含任何判斷 → docs/（英文）與 docs/zh/（中文）
  （預設）    含 LLM 判斷與標籤，中文 → output/（不進版控）

用法： python3 scripts/render.py [--public] [--lang en|zh] [YYYY-MM-DD]
"""
import json, os, sys, html, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n import STR, LANGS, OTHER, SWITCH_LABEL, BASE

# 排程時 stdout 導向 log 檔會變成塊緩衝，進度訊息會全部卡到程式結束才吐。
sys.stdout.reconfigure(line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[1:]
PUBLIC = "--public" in argv
LANG_ARG = argv[argv.index("--lang") + 1] if "--lang" in argv else None
pos = [a for a in argv if not a.startswith("--") and a != LANG_ARG]
DATE = pos[0] if pos else datetime.date.today().isoformat()
e = html.escape

TAGS = {"real": ("真材實料", "real"), "novelty": ("獵奇", "novelty"),
        "fame": ("名人效應", "fame"), "trend": ("蹭熱點", "trend"),
        "flood": ("同質洗版", "flood"), "mistag": ("誤掛主題", "mistag"),
        "scam": ("疑似冒牌", "scam")}

CSS = open(f"{ROOT}/scripts/style.css", encoding="utf-8").read()


def md(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(s))


def facts_line(sg, T):
    """全部可驗證。公開版靠這一行讓讀者自己判斷。"""
    p = []
    t = T["f_org"] if sg["owner_type"] == "Organization" else T["f_user"]
    age = sg["owner_age_days"]
    if age is not None:
        yrs = age / 365
        agestr = T["f_years"].format(y=yrs) if yrs >= 1 else T["f_days"].format(d=age)
        p.append(T["f_owner"].format(t=t, d=sg["owner_created"], age=agestr))
    else:
        p.append(T["f_owner"].format(t=t, d="?", age="?"))
    if sg["owner_followers"] is not None:
        p.append(T["f_followers"].format(n=sg["owner_followers"]))
    if sg["owner_repos"] is not None:
        p.append(T["f_repos"].format(n=sg["owner_repos"]))
    p.append(T["f_lic_yes"] if sg["has_license"] else T["f_lic_no"])
    if not sg["has_desc"]:
        p.append(T["f_nodesc"])
    if sg["is_fork"]:
        p.append(T["f_fork"])
    if sg["keyword_present"] is False:
        p.append(T["f_nokw"].format(kw=sg["keyword"]))
    if sg["same_owner_in_board"] > 1:
        p.append(T["f_same"].format(n=sg["same_owner_in_board"]))
    return " · ".join(p)


def rows(cat, notes, lang, T):
    items = cat["new"]
    mx = max((r["vel"] for r in items), default=1) or 1
    out = []
    for i, r in enumerate(items, 1):
        n = notes.get(r["name"], {})
        what = (n.get("what_en") or n.get("what")) if lang == "en" else n.get("what")
        what = what or T["no_what"]
        kind = n.get("tag", "real")
        label, cls = TAGS.get(kind, TAGS["real"])
        pill = "" if PUBLIC else f'<span class="pill {cls}">{label}</span>'
        judge = "" if PUBLIC or not n.get("verdict") else \
            f'<div class="why {cls}"><b>為何上榜 ▸</b> {md(n["verdict"])}</div>'
        chips = "".join(f'<span class="chip">{e(t)}</span>'
                        for t in ([r["lang"]] if r["lang"] else []) + r["topics"][:4])
        orig = (f'<div class="origdesc">{e(r["desc"])}</div>' if r["desc"]
                else f'<div class="origdesc">{T["no_desc"]}</div>')
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
          <div class="facts">{e(facts_line(r["signals"], T))}</div>
          <div class="chips">{chips}</div>
        </div>
        <div class="data">
          <div class="stars">{r['stars']:,}<span> ★</span></div>
          <div class="vel">{r['vel']:,.1f} {T['per_day']}</div>
          <div class="bar"><i style="width:{pct:.1f}%"></i></div>
          <div class="age">{T['age'].format(d=r['age_days'])}</div>
        </div>
      </div>""")
    return "\n".join(out)


def cat_label(c, lang):
    return c.get("label_en", c["label"]) if lang == "en" else c["label"]


def growth_section(raw, lang, T):
    g = raw.get("growth") or {}
    base = raw.get("growth_base")
    if not base or not any(g.values()):
        return f"""  <section id="growth">
    <div class="sechead"><h2>{T['growth_title']}</h2>
      <div class="q">{T['growth_pending_q']}</div></div>
    <div class="pending"><h3>{T['growth_pending_h']}</h3>
      <p>{T['growth_pending_p']}</p></div>
  </section>"""
    blocks = []
    for key, rowsg in g.items():
        if not rowsg:
            continue
        lab = cat_label(raw["cats"].get(key, {"label": key}), lang)
        trs = "".join(
            f'<tr><td class="r">{i:02d}</td><td class="n">'
            f'<a href="https://github.com/{e(x["name"])}" target="_blank" rel="noopener">{e(x["name"])}</a></td>'
            f'<td class="num up">+{x["delta"]:,}</td>'
            f'<td class="num">{x["pct"]:+.1f}%</td>'
            f'<td class="num">{x["stars"]:,}</td></tr>'
            for i, x in enumerate(rowsg, 1))
        blocks.append(
            f'<h3 class="gsub">{e(lab)}</h3><div class="tablewrap"><table>'
            f'<thead><tr><th>{T["th_rank"]}</th><th>{T["th_repo"]}</th>'
            f'<th class="num">{T["th_delta"]}</th><th class="num">{T["th_pct"]}</th>'
            f'<th class="num">{T["th_stars"]}</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div>')
    return f"""  <section id="growth">
    <div class="sechead"><h2>{T['growth_title']}</h2>
      <div class="q">{T['growth_q'].format(base=e(base))}</div></div>
    {''.join(blocks)}
  </section>"""


def build(raw, notes, lang, depth):
    """depth = 這個頁面相對站台根目錄的層數，用來組語言切換連結。"""
    T = STR[lang]
    other = OTHER[lang]
    home = BASE if other == "en" else BASE + "zh/"
    switch = f'<a class="lang" href="{home}">{SWITCH_LABEL[lang]}</a>'

    navs = "".join(f'<a href="#{k}">{e(cat_label(c, lang))}</a>'
                   for k, c in raw["cats"].items())
    legend = "" if PUBLIC else '<div class="legend">' + "".join(
        f'<span class="pill {c}">{l}</span>' for l, c in TAGS.values()) + "</div>"

    secs = []
    for k, c in raw["cats"].items():
        secs.append(f"""  <section id="{k}">
    <div class="sechead"><h2>{e(cat_label(c, lang))}</h2>
      <div class="q">{T['created_days'].format(d=c['days'])} · {e(c['note'])}<br>
        {T['hits'].format(n=c['total'], m=len(c['new']))}</div>
    </div>
    <div class="rows">
{rows(c, notes, lang, T)}
    </div>
  </section>""")

    kind = T["kind_public"] if PUBLIC else T["kind_private"]
    disclaimer = T["foot_facts"] if PUBLIC else T["foot_judge"]

    body = f"""
<div class="wrap">
  <header class="mast">
    <h1>{T['title']}</h1>
    <div class="meta">
      <span>{T['generated']} <b>{e(raw['generated'])}</b></span>
      <span>{T['source']} <b>GitHub Search API</b>{'' if raw.get('authed') else T['unauthed']}</span>
      <span>{kind}</span>
      {switch}
    </div>
    {legend}
  </header>
  <nav>{navs}<a href="#growth">{T['growth_title']}</a></nav>
{chr(10).join(secs)}
{growth_section(raw, lang, T)}
  <footer>
    <span>{T['foot_vel']}</span>
    <span>{disclaimer}</span>
    <span>{T['foot_src']}</span>
  </footer>
</div>"""

    return (f'<!doctype html>\n<html lang="{T["html_lang"]}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{T["title"]} {DATE}</title>\n<style>\n{CSS}\n</style>\n'
            f'</head>\n<body>{body}\n</body>\n</html>\n')


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)


def resolve_date(root, wanted):
    """跨午夜手動執行時，「今天」常常沒有資料。找不到就退回最新那份並講清楚。"""
    if os.path.exists(f"{root}/data/raw/{wanted}.json"):
        return wanted
    import glob
    have = sorted(glob.glob(f"{root}/data/raw/*.json"))
    if not have:
        sys.exit(f"data/raw/ 裡沒有任何資料，請先跑 fetch.py")
    latest = os.path.basename(have[-1])[:-5]
    print(f"⚠️  沒有 {wanted} 的資料，改用最新的 {latest}")
    return latest


def main():
    global DATE
    DATE = resolve_date(ROOT, DATE)
    raw = json.load(open(f"{ROOT}/data/raw/{DATE}.json"))
    npath = f"{ROOT}/data/notes/{DATE}.json"
    notes = json.load(open(npath)) if os.path.exists(npath) else {}
    if not notes:
        print("⚠️  沒有評註檔，只會渲染事實層（先跑 annotate.py）")

    if PUBLIC:
        for lang in ([LANG_ARG] if LANG_ARG else LANGS):
            sub = "" if lang == "en" else f"{lang}/"
            page = build(raw, notes, lang, depth=1 if sub else 0)
            write(f"{ROOT}/docs/{sub}index.html", page)
            write(f"{ROOT}/docs/{sub}archive/{DATE}.html", page)
            print(f"public[{lang}] -> docs/{sub}index.html + docs/{sub}archive/{DATE}.html")
    else:
        lang = LANG_ARG or "zh"
        write(f"{ROOT}/output/{DATE}.html", build(raw, notes, lang, depth=0))
        print(f"private[{lang}] -> output/{DATE}.html")


if __name__ == "__main__":
    main()
