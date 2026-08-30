#!/bin/zsh
# gh-star-weekly 每週排程的實際執行體（正本在 repo，別直接改 ~/.local/libexec 那份）。
# 由 ~/Applications/GhStarWeekly.app 呼叫 —— 目的跟 daily-summary 一樣：
# 讓 TCC 身分認在固定路徑的 app 上，而不是 claude 那個每天更新就會變的版本化路徑。
#
# 抓取（fetch.py）不在這裡，那步跑在 GitHub Actions（額度大，且本機沒開機也不會斷快照）。
# 這裡只做：拉資料 → 評註 → 渲染 → 寫 vault 筆記 → 推回。

export PATH="/Users/lora/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO=${0:A:h:h}          # 這個腳本在 <repo>/scripts/ 底下，往上兩層就是 repo
VAULT=/Users/lora/Documents/obs_vault/repo/GD_ObsidianVault
PY=/opt/homebrew/bin/python3
LOG=/Users/lora/Library/Logs/gh-star-weekly.log

notify() { /usr/bin/osascript -e "display notification \"$1\" with title \"GitHub 週榜排程\"" >/dev/null 2>&1; }
run() { /usr/bin/perl -e 'alarm shift; exec @ARGV' "$@"; }

exec >> "$LOG" 2>&1
echo "===== $(date '+%F %T') START (host $(scutil --get LocalHostName)) ====="

cd "$REPO" || { echo "cd 失敗"; exit 1; }

# 這裡刻意不做 TCC preflight。annotate／render／push 全在 ~/repo 底下，
# 不受「文件」檔案夾權限管轄，沒必要因為 vault 讀不到就整條停掉。
# TCC 只在最後寫 vault 筆記那步才檢查。

# --- preflight：Actions 今天的資料到了嗎 ---
git pull --rebase --quiet || { echo "git pull 失敗"; notify "git pull 失敗"; exit 1; }
DATE=$(date '+%F')
if [[ ! -f "data/raw/$DATE.json" ]]; then
	echo "!!!!! 沒有 data/raw/$DATE.json —— Actions 可能還沒跑完或失敗了"
	LATEST=$(ls -1 data/raw/*.json 2>/dev/null | tail -1)
	echo "!!!!! 最新的是 ${LATEST:-無}"
	notify "今天沒有新資料，Actions 可能失敗了"
	exit 75
fi

step() {
	local label=$1; shift
	run 1800 "$@"
	local rc=$?
	echo "----- $label rc=$rc -----"
	[[ $rc -ne 0 ]] && notify "$label 失敗 rc=$rc"
	return $rc
}

step "annotate" $PY -u scripts/annotate.py "$DATE" || exit 1
step "render-public" $PY -u scripts/render.py --public "$DATE"
step "render-private" $PY -u scripts/render.py "$DATE"

# vault 在 ~/Documents 底下，受 TCC 管。授權沒給就只跳過這步，網頁照樣更新。
if run 10 /bin/ls "$VAULT/01_inbox" >/dev/null 2>&1; then
	step "vault-note" $PY -u scripts/note.py "$DATE"
else
	echo "----- vault-note SKIPPED：TCC 未授權 -----"
	echo "      系統設定 → 隱私權與安全性 → 檔案與檔案夾 → 允許 GhStarWeekly 存取「文件」"
	notify "vault 筆記沒寫（TCC 未授權），網頁已更新"
fi

git add -A
if git diff --staged --quiet; then
	echo "沒有變更可提交"
else
	git -c user.name="LoloraWu" -c user.email="lorawu.sin@gmail.com" \
		commit -q -m "週榜 $DATE：評註與網頁"
	git push -q && echo "pushed" || { echo "push 失敗"; notify "push 失敗"; }
fi

echo "===== $(date '+%F %T') END ====="
