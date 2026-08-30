# gh-star-weekly

每週把 GitHub 上「新竄起」與「星數成長最快」的專案整理成一頁，分四個分類：
**大雜燴 / Agent / Obsidian / Home Assistant**。

網頁：<https://lolorawu.github.io/gh-star-weekly/>

## 兩種榜

| 榜 | 怎麼算 | 什麼時候有 |
|---|---|---|
| 新 repo 總星數榜 | `created:>=N天前` 依星數排序 | 當次執行就有 |
| 既有 repo 週成長榜 | 本週快照 − 上週快照 | **第二次執行起** |

星數成長沒有官方 API 欄位，只能自己每週存快照再 diff。第一次跑必然沒有成長榜，
這是物理限制不是壞掉。

## ★/天

`總星數 ÷ 建立天數`，用來區分「三天衝四千星」與「三年累積四千星」。
強度條在**各分類內部**正規化 —— 跨分類的量級可以差到兩個數量級。

## 為什麼分兩段跑

抓取在 **GitHub Actions**，評註在 **本機（mini）**。

- Actions 自帶 `GITHUB_TOKEN`，API 額度從 10 req/min、60 req/hr 變成 30 req/min、5000 req/hr。
  抓 README 與帳號履歷才有足夠額度。
- 更重要的是：**快照序列不能斷**。成長榜依賴每週都有一份快照，
  放在 Actions 就不會因為本機沒開機而缺一週。
- 評註需要 LLM，跑在本機用既有訂閱，不另外開 API 計費。
  本機晚跑幾天只會讓網頁晚更新，不會破壞資料。

## 兩種輸出

| | 內容 | 位置 |
|---|---|---|
| `--public` | **只有可驗證的事實**：帳號註冊日、follower 數、公開 repo 數、授權條款、關鍵字是否出現在 README | `docs/` → GitHub Pages |
| 預設 | 額外含 LLM 的判斷與標籤（真材實料／獵奇／名人效應／蹭熱點／同質洗版／誤掛主題／疑似冒牌） | `output/`（未進版控） |

公開版刻意不下結論。同樣一組數字 ——「個人帳號、註冊 44 天、0 followers、
1 個公開 repo、無授權條款」—— 讀者自己看得出來，不需要我替他們判斷。

## 跑法

```bash
python3 scripts/fetch.py                 # 抓榜單 + 快照 + 事實訊號
python3 scripts/annotate.py              # 讀 README 產評註（需要 claude CLI）
python3 scripts/render.py --public       # → docs/
python3 scripts/render.py                # → output/
```

分類與查詢條件全部在 `config.toml`。

## 資料

`data/snapshots/` 是每週的 `repo → 星數` 快照，git 追蹤，
所以星數歷史會自然累積成一份可回溯的資料集。
