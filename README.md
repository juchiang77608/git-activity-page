# git-activity-page

GitHub 風格的每日 commit 熱力圖靜態頁，資料來自本地追蹤的多個 git repo（含未推上遠端的私有專案）。

線上版：GitHub Pages（設定 repo → Settings → Pages → Deploy from branch → `main` / root）

## 隱私邊界（by design）

公開的只有 `activity.json`，內容僅含：

- 每日 commit「次數」（`{"YYYY-MM-DD": n}`）
- 全域／各年語言 → 檔案觸及次數（allowlist 語言名，無副檔名／路徑）
- 匯出時間與總數

repo 名稱、檔案路徑、commit 訊息、作者、diff 統計**皆不在資料集內**，也不經過任何伺服器——由 `scripts/export.py` 從本地 SQLite 離線聚合後手動 push。

語言次數在本機同步時就聚合成語言名（不含路徑）；匯出時再以 allowlist 過濾。架構取捨見線上頁 [`adr.html`](adr.html)。

## 更新流程

```bash
python3 scripts/export.py --db /path/to/local.sqlite
git add activity.json && git commit -m "update activity" && git push
```

含本機實際路徑的指令可放在 `local/`（該目錄不進版控）。

## 本機預覽

```bash
python3 -m http.server 8080
# 瀏覽 http://localhost:8080
```

## 架構決策（ADR）

訪客從熱力圖頁可進 [`adr.html`](adr.html)（排版過的 HTML，不必讀 Markdown）。Markdown 原文在 [`docs/adr/`](docs/adr/README.md)。

## 結構

```
index.html        # 自包含熱力圖頁（無外部依賴）
adr.html          # 公開架構決策（給訪客看的 HTML）
activity.json     # 唯一的資料檔（日期 → 次數、語言合計／分年）
scripts/export.py # 聚合匯出 script
docs/adr/         # 同一組決策的 Markdown 原文
```
