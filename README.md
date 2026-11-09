# X 羊毛情报站 · AI / 科技

静态站，由 GitHub Actions **免费**每日自动更新（无需 Grok / 付费 API）。

- 羊毛数据：`data/YYYY-MM-DD.json`（可由 X 日常例程写入）+ `data/auto/`（Action 抓取）
- 构建：`python3 build.py` → `index.html`
- 自动抓取：`python3 fetch_auto.py`（HN / V2EX / GitHub / DEV.to / Lobsters）
- 栏目：羊毛分类、**GitHub 新热门**、**最近热议**
- GitHub Pages：仓库 `main` 根目录
- Netlify `aiyangmao`：反向代理到 GitHub Pages

例程侧只需推送新的 `data/YYYY-MM-DD.json`，Action 会重建页面。
