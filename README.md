# git-activity-page

GitHub 風格的每日 commit 熱力圖靜態頁，資料來自本地追蹤的多個 git repo（含未推上遠端的私有專案）。

線上版：GitHub Pages（設定 repo → Settings → Pages → Deploy from branch → `main` / root）

## 隱私邊界（by design）

公開的只有 `activity.json`，內容僅含：

- 每日 commit「次數」（`{"YYYY-MM-DD": n}`）
- 全域語言 → 檔案觸及次數（allowlist 語言名，無副檔名／路徑）
- 匯出時間與總數

repo 名稱、檔案路徑、commit 訊息、作者、diff 統計**皆不在資料集內**，也不經過任何伺服器——由 `scripts/export.py` 從本地 SQLite 離線聚合後手動 push。

語言資料需在本地 `attendance-record` 以 `--numstat` 同步後才會寫入 `git_commits.languages_json`（僅語言名與次數）；重新全量同步後再執行匯出。

## 更新流程

```bash
python3 scripts/export.py --db /path/to/attendance.db
git add activity.json && git commit -m "update activity" && git push
```

（本機可將含實際路徑的指令放在 `local/`，該目錄不進版控。）

## 本機預覽

```bash
python3 -m http.server 8080
# 瀏覽 http://localhost:8080
```

## 結構

```
index.html        # 自包含熱力圖頁（無外部依賴）
activity.json     # 唯一的資料檔（日期 → 次數、語言合計）
scripts/export.py # 聚合匯出 script
```
