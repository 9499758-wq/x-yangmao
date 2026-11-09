#!/usr/bin/env python3
"""Build SEO Chinese site: index + daily archives + sitemap + robots."""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SITE = Path(__file__).resolve().parent
DATA = SITE / "data"
AUTO = DATA / "auto"
ARCHIVES = SITE / "archives"
OUT = SITE / "index.html"

# Brand / Baidu SEO
SITE_NAME = "AI大模型免费资源导航"
SITE_TAGLINE = "大模型免费API · AI工具限免 · GitHub热门项目 · 每日自动更新"
CANONICAL = "https://aidamoxing-mianfei.netlify.app/"
KEYWORDS = (
    "AI大模型免费资源,大模型免费API,AI工具免费,GitHub热门项目,"
    "免费API额度,AI开发工具,LLM免费额度,ChatGPT免费,Claude免费,"
    "AI编程助手,云GPU免费,科技App限免"
)
META_DESC = (
    "AI大模型免费资源导航：汇总大模型免费API额度、AI工具会员试用、"
    "GitHub热门AI项目与科技限免资讯，每日自动抓取翻译更新，方便百度搜索。"
)

TZ = ZoneInfo("Asia/Shanghai")
CATEGORIES = [
    "大模型 API 免费额度",
    "AI 产品会员/试用",
    "AI 开发工具与编程助手",
    "云服务/GPU/开发者资源",
    "科技软件/App 限免",
    "其他科技",
]


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def parse_deadline(s: str | None) -> datetime | None:
    if not s:
        return None
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", s)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TZ)
    except Exception:
        return None


def is_expired(item: dict, now: datetime) -> bool:
    dl = parse_deadline(item.get("deadline"))
    return bool(dl and dl.date() < now.date())


def norm_url(u: str) -> str:
    return (u or "").strip().rstrip("/")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"skip {path}: {e}")
        return None


def ym_label(date_str: str) -> str:
    """2026-11-09 -> 2026年11月最新"""
    m = re.match(r"(20\d{2})-(\d{2})", date_str or "")
    if m:
        return f"{m.group(1)}年{int(m.group(2))}月最新"
    now = datetime.now(TZ)
    return f"{now.year}年{now.month}月最新"


def collect_deal_items() -> tuple[list[dict], str, str]:
    now = datetime.now(TZ)
    items: list[dict] = []
    latest_label = ""
    latest_date = ""

    for f in sorted(DATA.glob("????-??-??.json"), reverse=True):
        d = load_json(f)
        if not d:
            continue
        if not latest_date:
            latest_date = d.get("date") or f.stem
            latest_label = d.get("updated_at_label") or ""
        for it in d.get("items") or []:
            it = dict(it)
            it.setdefault("source", "X")
            items.append(it)

    for f in sorted(AUTO.glob("????-??-??.json"), reverse=True):
        d = load_json(f)
        if not d:
            continue
        if not latest_label:
            latest_label = d.get("updated_at_label") or ""
        if not latest_date:
            latest_date = d.get("date") or f.stem
        for it in d.get("items") or []:
            it = dict(it)
            it.setdefault("source", "auto")
            items.append(it)

    seen = set()
    uniq = []
    for it in items:
        u = norm_url(it.get("url") or "")
        if not u or u in seen:
            continue
        if is_expired(it, now):
            continue
        cat = it.get("category") or "其他科技"
        if cat not in CATEGORIES:
            it["category"] = "其他科技"
        seen.add(u)
        uniq.append(it)

    if not latest_date:
        latest_date = now.strftime("%Y-%m-%d")
    if not latest_label:
        latest_label = now.strftime("%Y-%m-%d %H:%M Asia/Shanghai")
    return uniq, latest_date, latest_label


def load_section(name: str) -> tuple[list[dict], str]:
    path = AUTO / name
    d = load_json(path) if path.exists() else None
    if not d:
        return [], ""
    return d.get("items") or [], d.get("updated_at_label") or ""


def list_archive_dates() -> list[str]:
    dates = set()
    for f in DATA.glob("????-??-??.json"):
        dates.add(f.stem)
    for f in AUTO.glob("????-??-??.json"):
        dates.add(f.stem)
    return sorted(dates, reverse=True)


def items_for_date(day: str) -> list[dict]:
    now = datetime.now(TZ)
    items = []
    for base in (DATA, AUTO):
        p = base / f"{day}.json"
        if not p.exists():
            continue
        d = load_json(p) or {}
        for it in d.get("items") or []:
            it = dict(it)
            if is_expired(it, now):
                continue
            cat = it.get("category") or "其他科技"
            if cat not in CATEGORIES:
                it["category"] = "其他科技"
            items.append(it)
    seen = set()
    uniq = []
    for it in items:
        u = norm_url(it.get("url") or "")
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(it)
    return uniq


CSS = r"""
:root {
  --bg: #070b16;
  --bg2: #0d1428;
  --panel: rgba(18, 26, 52, 0.72);
  --panel-solid: #121a34;
  --card: rgba(22, 32, 64, 0.78);
  --card-hover: rgba(30, 44, 88, 0.92);
  --line: rgba(120, 150, 220, 0.22);
  --line-strong: rgba(140, 175, 255, 0.38);
  --text: #eef2ff;
  --muted: #9aa6c9;
  --accent: #6ea8ff;
  --accent2: #5ef0c0;
  --accent3: #a78bfa;
  --warn: #ffc857;
  --danger: #ff7b8a;
  --shadow: 0 18px 50px rgba(0,0,0,.35);
  --radius: 18px;
  --glass: blur(18px) saturate(1.35);
  --hero-a: rgba(110,168,255,.22);
  --hero-b: rgba(167,139,250,.16);
  --hero-c: rgba(94,240,192,.10);
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #f4f7ff;
    --bg2: #e8eefc;
    --panel: rgba(255,255,255,.78);
    --panel-solid: #ffffff;
    --card: rgba(255,255,255,.86);
    --card-hover: #ffffff;
    --line: rgba(70, 100, 180, 0.16);
    --line-strong: rgba(70, 110, 210, 0.32);
    --text: #12182b;
    --muted: #5b6688;
    --accent: #2f6df6;
    --accent2: #0f9f75;
    --accent3: #6d4ce0;
    --warn: #c27a00;
    --danger: #d6455a;
    --shadow: 0 16px 40px rgba(40,70,140,.12);
    --hero-a: rgba(47,109,246,.14);
    --hero-b: rgba(109,76,224,.10);
    --hero-c: rgba(15,159,117,.08);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
html, body {
  margin: 0; padding: 0;
  overflow-wrap: anywhere; word-break: break-word;
}
body {
  font-family: "PingFang SC","Hiragino Sans GB","Noto Sans SC","Microsoft YaHei",
               -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color: var(--text);
  background:
    radial-gradient(1200px 700px at 8% -12%, var(--hero-a), transparent 55%),
    radial-gradient(900px 560px at 92% 0%, var(--hero-b), transparent 50%),
    radial-gradient(800px 500px at 50% 110%, var(--hero-c), transparent 55%),
    linear-gradient(180deg, var(--bg), var(--bg2) 40%, var(--bg));
  min-height: 100vh;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1120px; margin: 0 auto; padding: 22px 16px 72px; }

.hero {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--line-strong);
  border-radius: 24px;
  padding: 28px 22px 22px;
  margin-bottom: 18px;
  background:
    linear-gradient(135deg, var(--hero-a), transparent 42%),
    linear-gradient(225deg, var(--hero-b), transparent 40%),
    var(--panel);
  backdrop-filter: var(--glass);
  -webkit-backdrop-filter: var(--glass);
  box-shadow: var(--shadow);
}
.hero::after {
  content: "";
  position: absolute; inset: auto -20% -40% 40%;
  height: 180px;
  background: radial-gradient(circle, var(--hero-c), transparent 70%);
  pointer-events: none;
}
.brand {
  display: inline-flex; align-items: center; gap: 10px;
  font-size: .78rem; letter-spacing: .08em; text-transform: uppercase;
  color: var(--accent2); font-weight: 600; margin-bottom: 10px;
}
.brand .dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent2); box-shadow: 0 0 0 4px rgba(94,240,192,.18);
  animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 4px rgba(94,240,192,.15); }
  50% { box-shadow: 0 0 0 8px rgba(94,240,192,.05); }
}
.hero h1 {
  margin: 0 0 10px;
  font-size: clamp(1.45rem, 4.6vw, 2.05rem);
  font-weight: 720; letter-spacing: -.02em; line-height: 1.25;
}
.hero .tagline { margin: 0; color: var(--muted); font-size: 1rem; max-width: 52rem; }
.stats {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px;
}
.pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(0,0,0,.18);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: .84rem;
  color: var(--muted);
}
@media (prefers-color-scheme: light) {
  .pill { background: rgba(255,255,255,.55); }
}
.pill b { color: var(--accent2); font-weight: 650; }
.pill .k { color: var(--muted); }

.sticky-nav {
  position: sticky; top: 10px; z-index: 40;
  display: flex; flex-wrap: wrap; gap: 8px;
  margin: 0 0 14px;
  padding: 10px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--panel);
  backdrop-filter: var(--glass);
  -webkit-backdrop-filter: var(--glass);
  box-shadow: 0 10px 30px rgba(0,0,0,.12);
}
.sticky-nav a {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(255,255,255,.03);
  color: var(--text);
  font-size: .86rem;
  transition: border-color .2s, transform .15s, background .2s;
}
.sticky-nav a:hover {
  border-color: var(--accent);
  text-decoration: none;
  transform: translateY(-1px);
  background: rgba(110,168,255,.10);
}

.toolbar {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 12px;
  margin-bottom: 16px;
  background: var(--panel);
  backdrop-filter: var(--glass);
  -webkit-backdrop-filter: var(--glass);
}
#q {
  width: 100%;
  padding: 13px 16px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--panel-solid);
  color: var(--text);
  font-size: 1rem;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
}
#q:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(110,168,255,.18);
}
.tabs {
  display: flex; gap: 8px; overflow-x: auto;
  padding: 10px 2px 2px;
  scrollbar-width: thin;
  -webkit-overflow-scrolling: touch;
}
.tab {
  flex: 0 0 auto;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  border-radius: 999px;
  padding: 8px 13px;
  cursor: pointer;
  font-size: .85rem;
  white-space: nowrap;
  transition: all .18s ease;
}
.tab em { font-style: normal; color: var(--accent); margin-left: 4px; }
.tab.active, .tab:hover {
  color: var(--text);
  border-color: var(--accent);
  background: rgba(110,168,255,.12);
}

.section { margin: 26px 0; }
.section h2 {
  font-size: 1.18rem; margin: 0 0 8px;
  display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;
}
.section h2 span { color: var(--muted); font-weight: 500; font-size: .9rem; }
.sec-desc { margin: 0 0 14px; color: var(--muted); font-size: .92rem; }

.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
@media (min-width: 720px) {
  .grid { grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); }
}

.card {
  position: relative;
  background:
    linear-gradient(160deg, rgba(110,168,255,.08), transparent 42%),
    var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 15px 14px;
  overflow: visible;
  max-height: none;
  transition: transform .18s ease, border-color .18s ease, background .18s ease, box-shadow .18s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.card:hover {
  transform: translateY(-3px);
  border-color: var(--line-strong);
  background:
    linear-gradient(160deg, rgba(110,168,255,.14), transparent 45%),
    var(--card-hover);
  box-shadow: var(--shadow);
}
.card.repo {
  background:
    linear-gradient(160deg, rgba(167,139,250,.10), transparent 42%),
    var(--card);
}
.card.hot {
  background:
    linear-gradient(160deg, rgba(94,240,192,.08), transparent 42%),
    var(--card);
}
.badgerow {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px;
}
.badge {
  display: inline-block;
  font-size: .72rem;
  color: #d7e6ff;
  background: linear-gradient(135deg, rgba(110,168,255,.22), rgba(167,139,250,.16));
  border: 1px solid rgba(110,168,255,.35);
  border-radius: 999px;
  padding: 3px 9px;
  font-weight: 600;
}
@media (prefers-color-scheme: light) {
  .badge { color: #244a9a; }
}
.src-tag, .dl-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: .72rem;
  border-radius: 999px;
  padding: 3px 9px;
  border: 1px solid var(--line);
  color: var(--muted);
  background: rgba(255,255,255,.04);
}
.src-tag { color: var(--accent2); border-color: rgba(94,240,192,.28); }
.dl-tag { color: var(--warn); border-color: rgba(255,200,87,.35); }
.title {
  margin: 0 0 10px;
  font-size: 1.05rem;
  line-height: 1.45;
  font-weight: 650;
  overflow-wrap: anywhere;
  white-space: normal;
}
.summary, .how, .meta, .linkrow, .author {
  margin: 0 0 10px;
  overflow: visible;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
  max-height: none;
}
.summary { color: var(--muted); font-size: .95rem; }
.how {
  font-size: .9rem;
  color: var(--text);
  background: rgba(255,255,255,.04);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
}
@media (prefers-color-scheme: light) {
  .how { background: rgba(47,109,246,.04); }
}
.meta { font-size: .88rem; color: var(--warn); }
.author { color: var(--muted); }
.linkrow { font-size: .86rem; color: var(--muted); }
.fulllink {
  color: var(--accent);
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
}
.hidden { display: none !important; }

.panel-box {
  margin-top: 28px;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--panel);
  backdrop-filter: var(--glass);
  -webkit-backdrop-filter: var(--glass);
}
.panel-box h2 { margin: 0 0 10px; font-size: 1rem; }
.arch {
  display: inline-block;
  margin: 0 8px 8px 0;
  padding: 7px 11px;
  border-radius: 10px;
  border: 1px solid var(--line);
  color: var(--muted);
  background: rgba(0,0,0,.15);
  transition: border-color .15s, color .15s;
}
.arch:hover { border-color: var(--accent); color: var(--text); text-decoration: none; }
.arch.current { color: var(--accent2); border-color: rgba(94,240,192,.45); }
.disclaimer p { margin: 0; color: var(--muted); font-size: .88rem; }
.empty { text-align: center; color: var(--muted); padding: 48px 10px; }
footer {
  margin-top: 28px;
  color: var(--muted);
  font-size: .8rem;
  text-align: center;
}
.crumbs { margin: 0 0 14px; color: var(--muted); font-size: .9rem; }
.crumbs a { color: var(--accent); }
"""


def head_block(title: str, description: str, canonical: str, og_title: str | None = None) -> str:
    og_title = og_title or title
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="renderer" content="webkit" />
<meta name="force-rendering" content="webkit" />
<meta name="applicable-device" content="pc,mobile" />
<meta name="MobileOptimized" content="width" />
<meta name="HandheldFriendly" content="true" />
<meta name="format-detection" content="telephone=no" />
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}" />
<meta name="keywords" content="{esc(KEYWORDS)}" />
<meta name="robots" content="index,follow" />
<meta name="author" content="{esc(SITE_NAME)}" />
<link rel="canonical" href="{esc(canonical)}" />
<meta property="og:type" content="website" />
<meta property="og:locale" content="zh_CN" />
<meta property="og:site_name" content="{esc(SITE_NAME)}" />
<meta property="og:title" content="{esc(og_title)}" />
<meta property="og:description" content="{esc(description)}" />
<meta property="og:url" content="{esc(canonical)}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{esc(og_title)}" />
<meta name="twitter:description" content="{esc(description)}" />
<style>
{CSS}
</style>
</head>
"""


def card_deal(item: dict) -> str:
    deadline = item.get("deadline")
    deadline_html = (
        f'<span class="dl-tag">截止 {esc(deadline)}</span>' if deadline else ""
    )
    how = item.get("how") or ""
    how_html = f'<div class="how"><strong>怎么领：</strong>{esc(how)}</div>' if how else ""
    url = item.get("url") or ""
    author = item.get("author") or ""
    posted = item.get("posted_at") or ""
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    cat = item.get("category") or ""
    source = item.get("source") or "未知"
    author_html = ""
    if author or posted:
        author_html = f'<div class="meta author"><strong>作者：</strong>@{esc(author)} · {esc(posted)}</div>'
    search_blob = " ".join([title, summary, how, author, url, cat, source])
    return f"""
<article class="card" data-cat="{esc(cat)}" data-text="{esc(search_blob)}">
  <div class="badgerow">
    <span class="badge">{esc(cat)}</span>
    <span class="src-tag">来源 {esc(source)}</span>
    {deadline_html}
  </div>
  <h3 class="title">{esc(title)}</h3>
  <p class="summary">{esc(summary)}</p>
  {how_html}
  {author_html}
  <div class="linkrow"><strong>原帖：</strong><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


def card_repo(item: dict) -> str:
    url = item.get("url") or ""
    title = item.get("title") or item.get("name") or ""
    summary = item.get("summary") or ""
    name = item.get("name") or ""
    stars = item.get("stars") or 0
    lang = item.get("language") or ""
    created = item.get("created_at") or ""
    search_blob = " ".join([title, summary, name, lang])
    return f"""
<article class="card repo" data-text="{esc(search_blob)}">
  <div class="badgerow">
    <span class="badge">GitHub 新热门</span>
    <span class="src-tag">来源 GitHub</span>
  </div>
  <h3 class="title">{esc(title)}</h3>
  <p class="summary">{esc(summary)}</p>
  <div class="meta">⭐ {esc(stars)} · {esc(lang)} · 创建 {esc(created)}</div>
  <div class="meta author"><strong>仓库：</strong>{esc(name)}</div>
  <div class="linkrow"><strong>链接：</strong><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


def card_hot(item: dict) -> str:
    url = item.get("url") or ""
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    source = item.get("source") or ""
    heat = item.get("heat") or ""
    search_blob = " ".join([title, summary, source, heat])
    return f"""
<article class="card hot" data-text="{esc(search_blob)}">
  <div class="badgerow">
    <span class="badge">最近热议</span>
    <span class="src-tag">来源 {esc(source)}</span>
  </div>
  <h3 class="title">{esc(title)}</h3>
  <p class="summary">{esc(summary)}</p>
  <div class="meta">热度：{esc(heat)}</div>
  <div class="linkrow"><strong>链接：</strong><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


SEARCH_JS = r"""
(function(){
  const q = document.getElementById('q');
  const tabs = [...document.querySelectorAll('.tab')];
  const cards = [...document.querySelectorAll('.deal-section .card')];
  const sections = [...document.querySelectorAll('.deal-section')];
  const empty = document.getElementById('empty');
  if (!q) return;
  let filter = '全部';
  function apply(){
    const term = (q.value || '').trim().toLowerCase();
    let shown = 0;
    cards.forEach(card => {
      const cat = card.getAttribute('data-cat') || '';
      const text = (card.getAttribute('data-text') || '').toLowerCase();
      const okCat = filter === '全部' || cat === filter;
      const okTerm = !term || text.includes(term);
      const ok = okCat && okTerm;
      card.classList.toggle('hidden', !ok);
      if (ok) shown++;
    });
    sections.forEach(sec => {
      const any = [...sec.querySelectorAll('.card')].some(c => !c.classList.contains('hidden'));
      sec.classList.toggle('hidden', !any);
    });
    if (empty) empty.classList.toggle('hidden', shown > 0 || cards.length === 0);
  }
  tabs.forEach(btn => btn.addEventListener('click', () => {
    tabs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filter = btn.getAttribute('data-filter') || '全部';
    apply();
  }));
  q.addEventListener('input', apply);
})();
"""


def write_robots() -> None:
    (SITE / "robots.txt").write_text(
        f"""User-agent: *
Allow: /
User-agent: Baiduspider
Allow: /
User-agent: Baiduspider-render
Allow: /
Sitemap: {CANONICAL}sitemap.xml
""",
        encoding="utf-8",
    )


def write_sitemap(dates: list[str]) -> None:
    now = datetime.now(TZ).strftime("%Y-%m-%d")
    urls = [
        f"""  <url>
    <loc>{CANONICAL}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>"""
    ]
    for d in dates:
        urls.append(
            f"""  <url>
    <loc>{CANONICAL}archives/{d}.html</loc>
    <lastmod>{d}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>"""
        )
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )


def build_archive_page(day: str, items: list[dict], all_dates: list[str]) -> None:
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    ym = ym_label(day)
    title = f"{SITE_NAME} · {day} 存档 · {ym}"
    desc = f"{SITE_NAME} {day} 日归档：大模型免费API、AI工具免费与GitHub热门项目汇总。"
    canonical = f"{CANONICAL}archives/{day}.html"
    counts = {c: 0 for c in CATEGORIES}
    for it in items:
        c = it.get("category") or "其他科技"
        counts[c] = counts.get(c, 0) + 1
    sections = []
    for c in CATEGORIES:
        cat_items = [it for it in items if it.get("category") == c]
        if not cat_items:
            continue
        cards = "\n".join(card_deal(it) for it in cat_items)
        sections.append(
            f'<section class="section deal-section" data-section="{esc(c)}">'
            f'<h2>{esc(c)} <span>({len(cat_items)})</span></h2>'
            f'<div class="grid">{cards}</div></section>'
        )
    arch_links = []
    for d in all_dates[:60]:
        cls = "current" if d == day else ""
        arch_links.append(
            f'<a class="arch {cls}" href="{esc(d)}.html">{esc(d)}</a>'
        )
    page = f"""{head_block(title, desc, canonical)}
<body>
<div class="wrap">
  <div class="crumbs"><a href="../">← 返回首页</a> · 日归档 · {esc(day)}</div>
  <header class="hero">
    <div class="brand"><span class="dot"></span> DAILY ARCHIVE</div>
    <h1>{esc(SITE_NAME)} · {esc(day)}</h1>
    <p class="tagline">{esc(ym)} 存档页 · 共 {len(items)} 条 AI / 科技免费资源</p>
    <div class="stats">
      <div class="pill"><span class="k">日期</span> <b>{esc(day)}</b></div>
      <div class="pill"><span class="k">条目</span> <b>{len(items)}</b></div>
    </div>
  </header>
  <nav class="sticky-nav" aria-label="栏目导航">
    <a href="../">首页</a>
    <a href="../#deals">免费资源</a>
    <a href="../#github-hot">GitHub 热门</a>
    <a href="../#hot-topics">最近热议</a>
  </nav>
  <div id="list">
    {''.join(sections) if sections else '<div class="empty">该日暂无条目（可能源站暂无更新，首页仍保留最近可用数据）</div>'}
  </div>
  <div class="panel-box">
    <h2>更多日期存档</h2>
    <div>{''.join(arch_links)}</div>
  </div>
  <div class="panel-box disclaimer">
    <h2>免责声明</h2>
    <p>信息来自公开网页与社区帖子，自动整理，可能过期或不准确。参与前请自行核实官网与活动规则。</p>
  </div>
  <footer>{esc(SITE_NAME)} · 日归档 {esc(day)} · 百度友好 SEO</footer>
</div>
</body>
</html>
"""
    (ARCHIVES / f"{day}.html").write_text(page, encoding="utf-8")


def build() -> Path:
    items, date, updated = collect_deal_items()
    repos, repos_updated = load_section("github_hot.json")
    topics, topics_updated = load_section("hot_topics.json")
    dates = list_archive_dates()
    ym = ym_label(date)

    # Never leave empty: if somehow no items, keep whatever sections we can
    counts = {c: 0 for c in CATEGORIES}
    src_counts: dict[str, int] = {}
    for it in items:
        c = it.get("category") or "其他科技"
        counts[c] = counts.get(c, 0) + 1
        s = it.get("source") or "?"
        src_counts[s] = src_counts.get(s, 0) + 1

    tabs = [f'<button class="tab active" data-filter="全部">全部资源 <em>{len(items)}</em></button>']
    for c in CATEGORIES:
        if counts.get(c, 0):
            tabs.append(
                f'<button class="tab" data-filter="{esc(c)}">{esc(c)} <em>{counts[c]}</em></button>'
            )

    sections = []
    for c in CATEGORIES:
        cat_items = [it for it in items if it.get("category") == c]
        if not cat_items:
            continue
        cards = "\n".join(card_deal(it) for it in cat_items)
        sections.append(
            f'<section class="section deal-section" data-section="{esc(c)}" id="cat-{esc(c)}">'
            f'<h2>{esc(c)} <span>({len(cat_items)})</span></h2>'
            f'<div class="grid">{cards}</div></section>'
        )

    repo_html = ""
    if repos:
        repo_html = f"""
<section class="section" id="github-hot">
  <h2>GitHub 热门项目 <span>({len(repos)})</span></h2>
  <p class="sec-desc">近 7–14 天创建、按星标排序的 AI / 大模型 / Agent / 开发工具仓库。更新：{esc(repos_updated)}</p>
  <div class="grid">{"".join(card_repo(r) for r in repos)}</div>
</section>"""

    hot_html = ""
    if topics:
        hot_html = f"""
<section class="section" id="hot-topics">
  <h2>最近热议 <span>({len(topics)})</span></h2>
  <p class="sec-desc">Hacker News / V2EX / X 等 AI 与科技热议。更新：{esc(topics_updated)}</p>
  <div class="grid">{"".join(card_hot(t) for t in topics)}</div>
</section>"""

    arch_links = []
    for d in dates[:90]:
        n = len(items_for_date(d))
        cls = "current" if d == date else ""
        arch_links.append(
            f'<a class="arch {cls}" href="archives/{esc(d)}.html">{esc(d)}（{n}）</a>'
        )

    now_label = datetime.now(TZ).strftime("%Y-%m-%d %H:%M Asia/Shanghai")
    src_pills = "".join(
        f'<div class="pill"><span class="k">来源 {esc(k)}</span> <b>{v}</b></div>'
        for k, v in sorted(src_counts.items())
    )

    page_title = f"{SITE_NAME} · {ym} · 大模型免费API与AI工具"
    page = f"""{head_block(page_title, META_DESC, CANONICAL, SITE_NAME + ' · ' + ym)}
<body>
<div class="wrap">
  <header class="hero">
    <div class="brand"><span class="dot"></span> LIVE · AUTO UPDATE</div>
    <h1>{esc(SITE_NAME)}</h1>
    <p class="tagline">{esc(SITE_TAGLINE)} · {esc(ym)}</p>
    <div class="stats">
      <div class="pill"><span class="k">更新日期</span> <b>{esc(date)}</b></div>
      <div class="pill"><span class="k">免费资源</span> <b>{len(items)}</b></div>
      <div class="pill"><span class="k">GitHub热门</span> <b>{len(repos)}</b></div>
      <div class="pill"><span class="k">热议</span> <b>{len(topics)}</b></div>
      <div class="pill"><span class="k">最近更新</span> <b>{esc(updated)}</b></div>
      <div class="pill"><span class="k">页面生成</span> <b>{esc(now_label)}</b></div>
      {src_pills}
    </div>
  </header>

  <nav class="sticky-nav" aria-label="栏目导航">
    <a href="#deals">免费资源</a>
    <a href="#github-hot">GitHub 热门项目</a>
    <a href="#hot-topics">最近热议</a>
    <a href="#archives">每日存档</a>
  </nav>

  <div class="toolbar" id="deals">
    <input id="q" type="search" placeholder="搜索标题 / 内容 / 作者 / 链接 / 来源…（支持中文关键词）" autocomplete="off" />
    <div class="tabs">{''.join(tabs)}</div>
  </div>

  <div id="list">
    {''.join(sections) if sections else '<div class="empty">暂无资源条目，系统将自动保留上一次有效数据并在下次抓取时恢复。</div>'}
  </div>
  <div id="empty" class="empty hidden">没有匹配条目，换个关键词试试。</div>

  {repo_html}
  {hot_html}

  <div class="panel-box" id="archives">
    <h2>每日存档（可被百度收录）</h2>
    <div>{''.join(arch_links) if arch_links else '<span>暂无</span>'}</div>
  </div>

  <div class="panel-box disclaimer">
    <h2>免责声明</h2>
    <p>信息来自公开网页与社区帖子，由 GitHub Actions 自动抓取与翻译整理，可能过期、不准确或含推广。参与前请自行核实官网与活动规则，谨防诈骗、钓鱼与盗号。本站不保证任何活动有效，也不提供代操作。</p>
  </div>
  <footer>{esc(SITE_NAME)} · 全自动更新 · 仅 AI / 科技类 · {esc(CANONICAL)}</footer>
</div>
<script>
{SEARCH_JS}
</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")

    # daily archive pages
    for d in dates:
        build_archive_page(d, items_for_date(d), dates)

    write_robots()
    write_sitemap(dates)

    # Netlify: keep proxy to GitHub Pages as source of truth mirror optional;
    # also write a lightweight _redirects for SPA-ish archive fallback none needed.
    print(
        f"wrote {OUT} deals={len(items)} repos={len(repos)} topics={len(topics)} "
        f"date={date} archives={len(dates)}"
    )
    for c in CATEGORIES:
        if counts.get(c, 0):
            print(f"  {c}: {counts[c]}")
    print("  sources:", src_counts)
    return OUT


if __name__ == "__main__":
    build()
