# Architecture Decision Records

本目錄記錄 **git-activity-page** 的公開架構決策：本機蒐集、離線聚合、靜態發布。

訪客請看網站上的 [`adr.html`](../../adr.html)，不必讀這些 Markdown。

這是依既有實作整理的公開改寫，不含本機目錄、私有程式路徑，也不描述未公開系統的內部模組。完整實作仍只留在本機。

每份 ADR 採用 [Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) 精簡版：狀態、背景、決策、理由、後果、替代方案。

| 編號 | 標題 | 狀態 |
|------|------|------|
| [0001](0001-local-collect-public-static-slice.md) | 本機蒐集、公開靜態切片 | 已接受 |
| [0002](0002-aggregates-only-privacy-boundary.md) | 公開資料僅含聚合統計 | 已接受 |
| [0003](0003-language-allowlist-no-paths.md) | 語言 allowlist，不公開路徑 | 已接受 |
| [0004](0004-offline-export-manual-publish.md) | 離線匯出、手動發布 | 已接受 |
