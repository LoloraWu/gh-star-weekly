#!/usr/bin/env python3
"""抓 GitHub 榜單 + 快照 + 確定性事實訊號。純 stdlib。

有 GITHUB_TOKEN 就用（Actions 自帶）：search 30/min、core 5000/hr。
沒有也能跑，只是額度剩 10/min 與 60/hr。
"""
import json, os, sys, time, base64, re, datetime, tomllib
import urllib.parse, urllib.request, urllib.error

# 排程時 stdout 導向 log 檔會變成塊緩衝，進度訊息會全部卡到程式結束才吐。
sys.stdout.reconfigure(line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = tomllib.load(open(f"{ROOT}/config.toml", "rb"))
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
TODAY = datetime.date.today()
PAUSE = 0.35 if TOKEN else 6.5          # 未認證時 search 只有 10/min

HDRS = {"User-Agent": "gh-star-weekly", "Accept": "application/vnd.github+json"}
if TOKEN:
    HDRS["Authorization"] = f"Bearer {TOKEN}"


def api(path, params=None):
    url = "https://api.github.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=HDRS), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as ex:
            if ex.code in (403, 429) and attempt < 2:      # rate limited
                wait = int(ex.headers.get("Retry-After", 60))
                print(f"  rate limited, sleep {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            return {"_err": ex.code}
        except Exception as ex:
            return {"_err": str(ex)[:60]}
    return {"_err": "retries exhausted"}


def search(q, per_page):
    d = api("/search/repositories",
            {"q": q, "sort": "stars", "order": "desc", "per_page": per_page})
    time.sleep(PAUSE)
    return d


def readme(full_name, limit):
    j = api(f"/repos/{full_name}/readme")
    if "content" not in j:
        return ""
    try:
        md = base64.b64decode(j["content"]).decode("utf-8", "replace")
    except Exception:
        return ""
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"<[^>]+>", " ", md)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"[#*_>`|-]+", " ", md)
    return re.sub(r"\s+", " ", md).strip()[:limit]


_owner_cache = {}
def owner(login):
    """帳號履歷 — 判斷冒牌與否最有力的確定性訊號。"""
    if login in _owner_cache:
        return _owner_cache[login]
    j = api(f"/users/{login}")
    created = (j.get("created_at") or "")[:10]
    info = {
        "type": j.get("type", "?"),
        "created": created,
        "age_days": (TODAY - datetime.date.fromisoformat(created)).days if created else None,
        "followers": j.get("followers"),
        "public_repos": j.get("public_repos"),
    }
    _owner_cache[login] = info
    return info


def slim(r):
    c = r["created_at"][:10]
    age = max((TODAY - datetime.date.fromisoformat(c)).days, 1)
    return {
        "name": r["full_name"], "url": r["html_url"],
        "owner_login": r["owner"]["login"],
        "stars": r["stargazers_count"], "forks": r["forks_count"],
        "desc": (r.get("description") or "").strip(),
        "lang": r.get("language") or "", "topics": r.get("topics", [])[:8],
        "created": c, "age_days": age,
        "vel": round(r["stargazers_count"] / age, 1),
        "license": (r.get("license") or {}).get("spdx_id"),
        "is_fork": r.get("fork", False),
    }


def signals(rec, cat, board):
    """全部是可驗證的事實，不含任何判斷。公開版只印這些。"""
    o = owner(rec["owner_login"])
    # topic 用連字號（home-assistant）、README 用空格（Home Assistant），
    # 兩邊都正規化成空格才不會誤判成「沒出現」。
    norm = lambda t: re.sub(r"[-_]+", " ", t.lower())
    kw = norm(cat.get("keyword", ""))
    hay = norm(" ".join([rec["name"], rec["desc"], rec.get("readme", ""),
                         " ".join(rec["topics"])]))
    same_owner = sum(1 for x in board if x["owner_login"] == rec["owner_login"])
    return {
        "owner_type": o["type"],
        "owner_age_days": o["age_days"],
        "owner_created": o["created"],
        "owner_followers": o["followers"],
        "owner_repos": o["public_repos"],
        "has_license": bool(rec["license"]),
        "has_desc": bool(rec["desc"]),
        "keyword_present": (kw in hay) if kw else None,
        "keyword": kw or None,
        "same_owner_in_board": same_owner,
        "is_fork": rec["is_fork"],
    }


def main():
    g = CFG["general"]
    # git 不追蹤空目錄，乾淨 clone（例如 Actions runner）上這些夾不存在
    for sub in ("data/snapshots", "data/raw", "data/notes", "output"):
        os.makedirs(f"{ROOT}/{sub}", exist_ok=True)
    out = {"generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "date": TODAY.isoformat(), "authed": bool(TOKEN), "cats": {}}
    snapshot = {}

    for cat in CFG["category"]:
        key, label = cat["key"], cat["label"]
        since = (TODAY - datetime.timedelta(days=cat["days"])).isoformat()
        nq = f'{cat["query"]} created:>={since}'.strip()

        d = search(nq, g["per_board"] + 5)
        if "items" not in d:
            print(f"!! {label} search failed: {d}", file=sys.stderr); continue
        board = [slim(r) for r in d["items"]][: g["per_board"]]

        for rec in board:
            rec["readme"] = readme(rec["name"], g["readme_chars"])
        for rec in board:
            rec["signals"] = signals(rec, cat, board)

        s = search(cat["query"], 100)
        snap = {r["full_name"]: r["stargazers_count"] for r in s.get("items", [])}
        snapshot[key] = snap

        out["cats"][key] = {
            "label": label, "label_en": cat.get("label_en", label),
            "note": cat["note"], "days": cat["days"],
            "query": nq, "total": d["total_count"],
            "snapshot_total": s.get("total_count", 0), "new": board,
        }
        print(f"{label:16} new={d['total_count']:<7} board={len(board)} snap={len(snap)}")

    # ---- 週成長榜：跟上一份快照做 diff ----
    snapdir = f"{ROOT}/data/snapshots"
    prev = sorted(p for p in os.listdir(snapdir) if p.endswith(".json"))
    growth = {}
    if prev:
        old = json.load(open(f"{snapdir}/{prev[-1]}"))
        for key, cur in snapshot.items():
            rows = []
            for name, st in cur.items():
                was = old.get("snapshot", {}).get(key, {}).get(name)
                if was is None or st < g["min_stars_diff"]:
                    continue
                if st - was > 0:
                    rows.append({"name": name, "stars": st, "delta": st - was,
                                 "pct": round((st - was) / was * 100, 1) if was else None})
            growth[key] = sorted(rows, key=lambda r: -r["delta"])[: g["per_board"]]
        out["growth_base"] = prev[-1].replace(".json", "")
    else:
        out["growth_base"] = None
    out["growth"] = growth

    json.dump({"date": TODAY.isoformat(), "snapshot": snapshot},
              open(f"{snapdir}/{TODAY}.json", "w"), ensure_ascii=False)
    json.dump(out, open(f"{ROOT}/data/raw/{TODAY}.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"\nsnapshot -> data/snapshots/{TODAY}.json")
    print(f"raw      -> data/raw/{TODAY}.json")
    print("growth base:", out["growth_base"] or "（無上週快照，成長榜下週才有）")


if __name__ == "__main__":
    main()
