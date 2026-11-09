#!/usr/bin/env python3
"""Build index.html from data/*.json (X routine) + data/auto/*.json (Actions fetch)."""
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
OUT = SITE / "index.html"
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
    # try find YYYY-MM-DD
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", s)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TZ)
    except Exception:
        return None


def is_expired(item: dict, now: datetime) -> bool:
    dl = parse_deadline(item.get("deadline"))
    if dl and dl.date() < now.date():
        return True
    return False


def norm_url(u: str) -> str:
    return (u or "").strip().rstrip("/")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"skip {path}: {e}")
        return None


def collect_deal_items() -> tuple[list[dict], str, str]:
    now = datetime.now(TZ)
    items: list[dict] = []
    latest_label = ""
    latest_date = ""

    # X / manual daily files
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

    # auto deals: data/auto/YYYY-MM-DD.json (and ignore github_hot/hot_topics)
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

    # dedupe by url, prefer earlier (newer files first already via reverse sort append order — keep first)
    seen = set()
    uniq = []
    for it in items:
        u = norm_url(it.get("url") or "")
        if not u or u in seen:
            continue
        if is_expired(it, now):
            continue
        # only allowed categories / tech
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


def card_deal(item: dict) -> str:
    deadline = item.get("deadline")
    deadline_html = (
        f'<div class="meta"><span class="tag warn">截止</span> {esc(deadline)}</div>' if deadline else ""
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
    search_blob = " ".join([title, summary, how, author, url, cat, source])
    return f"""
<article class="card" data-cat="{esc(cat)}" data-text="{esc(search_blob)}">
  <div class="badgerow"><span class="badge">{esc(cat)}</span><span class="src">来源：{esc(source)}</span></div>
  <h3 class="title">{esc(title)}</h3>
  <p class="summary">{esc(summary)}</p>
  {how_html}
  {deadline_html}
  <div class="meta author"><strong>作者：</strong>@{esc(author)} · {esc(posted)}</div>
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
  <div class="badgerow"><span class="badge">GitHub 新热门</span><span class="src">来源：GitHub</span></div>
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
  <div class="badgerow"><span class="badge">最近热议</span><span class="src">来源：{esc(source)}</span></div>
  <h3 class="title">{esc(title)}</h3>
  <p class="summary">{esc(summary)}</p>
  <div class="meta">热度：{esc(heat)}</div>
  <div class="linkrow"><strong>链接：</strong><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


def build() -> Path:
    items, date, updated = collect_deal_items()
    repos, repos_updated = load_section("github_hot.json")
    topics, topics_updated = load_section("hot_topics.json")

    counts = {c: 0 for c in CATEGORIES}
    src_counts: dict[str, int] = {}
    for it in items:
        c = it.get("category") or "其他科技"
        counts[c] = counts.get(c, 0) + 1
        s = it.get("source") or "?"
        src_counts[s] = src_counts.get(s, 0) + 1

    tabs = [f'<button class="tab active" data-filter="全部">羊毛全部 <em>{len(items)}</em></button>']
    for c in CATEGORIES:
        if counts.get(c, 0):
            tabs.append(f'<button class="tab" data-filter="{esc(c)}">{esc(c)} <em>{counts[c]}</em></button>')

    sections = []
    for c in CATEGORIES:
        cat_items = [it for it in items if it.get("category") == c]
        if not cat_items:
            continue
        cards = "\n".join(card_deal(it) for it in cat_items)
        sections.append(
            f'<section class="section deal-section" data-section="{esc(c)}"><h2 id="{esc(c)}">{esc(c)} <span>({len(cat_items)})</span></h2><div class="grid">{cards}</div></section>'
        )

    repo_html = ""
    if repos:
        repo_html = f"""
<section class="section" id="github-hot">
  <h2>GitHub 新热门 <span>({len(repos)})</span></h2>
  <p class="sec-desc">近 7–14 天创建、按星标排序的 AI / LLM / Agent / 开发工具仓库。更新：{esc(repos_updated)}</p>
  <div class="grid">{"".join(card_repo(r) for r in repos)}</div>
</section>"""

    hot_html = ""
    if topics:
        hot_html = f"""
<section class="section" id="hot-topics">
  <h2>最近热议 <span>({len(topics)})</span></h2>
  <p class="sec-desc">Hacker News / V2EX / X 等科技与 AI 热议。更新：{esc(topics_updated)}</p>
  <div class="grid">{"".join(card_hot(t) for t in topics)}</div>
</section>"""

    # archive
    archive = []
    for f in sorted(DATA.glob("????-??-??.json"), reverse=True):
        d = load_json(f) or {}
        dd = d.get("date") or f.stem
        n = len(d.get("items") or [])
        cls = "current" if dd == date else ""
        archive.append(f'<a class="arch {cls}" href="data/{esc(dd)}.json" target="_blank" rel="noopener">{esc(dd)}（{n}）</a>')
    for f in sorted(AUTO.glob("????-??-??.json"), reverse=True):
        d = load_json(f) or {}
        dd = d.get("date") or f.stem
        n = len(d.get("items") or [])
        archive.append(f'<a class="arch" href="data/auto/{esc(f.name)}" target="_blank" rel="noopener">auto {esc(dd)}（{n}）</a>')

    now_label = datetime.now(TZ).strftime("%Y-%m-%d %H:%M Asia/Shanghai")
    src_pills = "".join(f'<div class="pill">来源 {esc(k)} <b>{v}</b></div>' for k, v in sorted(src_counts.items()))

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>X 羊毛情报站 · AI / 科技</title>
<meta name="description" content="AI/科技羊毛 + GitHub 新热门 + 最近热议，免费自动更新" />
<style>
:root {{
  --bg:#0b1020; --panel:#121933; --card:#171f3d; --line:#2a3560;
  --text:#e8ecff; --muted:#9aa3c7; --accent:#6ea8ff; --accent2:#7dffa6; --warn:#ffc857;
}}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; overflow-wrap:anywhere; word-break:break-word; }}
body {{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:radial-gradient(1200px 600px at 10% -10%, #1a2758 0%, transparent 55%),
             radial-gradient(900px 500px at 100% 0%, #132a3f 0%, transparent 50%), var(--bg);
  color:var(--text); line-height:1.6; min-height:100vh;
}}
a {{ color:var(--accent); text-decoration:none; overflow-wrap:anywhere; }}
a:hover {{ text-decoration:underline; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:20px 14px 64px; }}
header {{
  background:linear-gradient(135deg, rgba(110,168,255,.16), rgba(125,255,166,.08));
  border:1px solid var(--line); border-radius:18px; padding:22px 18px; margin-bottom:18px;
}}
header h1 {{ margin:0 0 8px; font-size:clamp(1.25rem, 4vw, 1.55rem); }}
header p {{ margin:0; color:var(--muted); font-size:.95rem; }}
.stats {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.pill {{ background:rgba(0,0,0,.25); border:1px solid var(--line); border-radius:999px; padding:6px 12px; font-size:.85rem; color:var(--muted); }}
.pill b {{ color:var(--accent2); font-weight:600; }}
.nav {{ display:flex; flex-wrap:wrap; gap:10px; margin:0 0 14px; }}
.nav a {{ border:1px solid var(--line); border-radius:999px; padding:8px 12px; background:var(--panel); color:var(--text); font-size:.88rem; }}
.toolbar {{ position:sticky; top:0; z-index:20; backdrop-filter:blur(10px); background:rgba(11,16,32,.9); border:1px solid var(--line); border-radius:14px; padding:10px; margin-bottom:16px; }}
#q {{ width:100%; padding:12px 14px; border-radius:10px; border:1px solid var(--line); background:var(--panel); color:var(--text); font-size:1rem; outline:none; }}
#q:focus {{ border-color:var(--accent); }}
.tabs {{ display:flex; gap:8px; overflow-x:auto; padding:10px 2px 2px; scrollbar-width:thin; -webkit-overflow-scrolling:touch; }}
.tab {{ flex:0 0 auto; border:1px solid var(--line); background:var(--panel); color:var(--muted); border-radius:999px; padding:8px 12px; cursor:pointer; font-size:.85rem; white-space:nowrap; }}
.tab em {{ font-style:normal; color:var(--accent); margin-left:4px; }}
.tab.active, .tab:hover {{ color:var(--text); border-color:var(--accent); }}
.section {{ margin:22px 0; }}
.section h2 {{ font-size:1.15rem; margin:0 0 8px; }}
.section h2 span {{ color:var(--muted); font-weight:500; font-size:.9rem; }}
.sec-desc {{ margin:0 0 12px; color:var(--muted); font-size:.9rem; }}
.grid {{ display:grid; grid-template-columns:1fr; gap:14px; }}
@media (min-width:720px) {{ .grid {{ grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); }} }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 14px 14px; height:auto; max-height:none; overflow:visible; }}
.badgerow {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:8px; }}
.badge {{ display:inline-block; font-size:.72rem; color:#cfe0ff; background:rgba(110,168,255,.15); border:1px solid rgba(110,168,255,.35); border-radius:999px; padding:3px 8px; }}
.src {{ font-size:.75rem; color:var(--accent2); }}
.title {{ margin:0 0 10px; font-size:1.05rem; line-height:1.45; font-weight:650; overflow-wrap:anywhere; white-space:normal; }}
.summary, .how, .meta, .linkrow, .author {{ margin:0 0 10px; overflow:visible; overflow-wrap:anywhere; word-break:break-word; white-space:normal; max-height:none; }}
.summary {{ color:var(--muted); font-size:.95rem; }}
.how {{ font-size:.9rem; color:#d7defa; background:rgba(255,255,255,.04); border-radius:8px; padding:10px 12px; }}
.meta {{ font-size:.88rem; color:var(--warn); }}
.author {{ color:var(--muted); }}
.tag {{ display:inline-block; border-radius:6px; padding:1px 6px; margin-right:4px; background:rgba(255,200,87,.15); border:1px solid rgba(255,200,87,.35); }}
.linkrow {{ font-size:.86rem; color:var(--muted); }}
.fulllink {{ color:var(--accent); overflow-wrap:anywhere; word-break:break-word; white-space:normal; }}
.hidden {{ display:none !important; }}
.archive, .disclaimer {{ margin-top:28px; padding:16px; border-radius:14px; border:1px solid var(--line); background:var(--panel); }}
.archive h2, .disclaimer h2 {{ margin:0 0 10px; font-size:1rem; }}
.arch {{ display:inline-block; margin:0 8px 8px 0; padding:6px 10px; border-radius:8px; border:1px solid var(--line); color:var(--muted); background:rgba(0,0,0,.2); }}
.arch.current {{ color:var(--accent2); border-color:rgba(125,255,166,.45); }}
.disclaimer p {{ margin:0; color:var(--muted); font-size:.88rem; }}
.empty {{ text-align:center; color:var(--muted); padding:40px 10px; }}
footer {{ margin-top:24px; color:var(--muted); font-size:.8rem; text-align:center; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🐑 X 羊毛情报站 · AI / 科技</h1>
    <p>只收大模型与科技类羊毛（免费 API、AI 工具、云 GPU、开发者资源、科技 App）。另附 GitHub 新热门与最近热议。信息来自公开网页与 X 帖子，GitHub Action 每日自动更新。每条展示完整标题、说明、领取方式、截止时间、作者、时间与链接。</p>
    <div class="stats">
      <div class="pill">更新日期 <b>{esc(date)}</b></div>
      <div class="pill">羊毛条目 <b>{len(items)}</b></div>
      <div class="pill">新热门 <b>{len(repos)}</b></div>
      <div class="pill">热议 <b>{len(topics)}</b></div>
      <div class="pill">页面生成 <b>{esc(now_label)}</b></div>
      <div class="pill">数据更新 <b>{esc(updated)}</b></div>
      {src_pills}
    </div>
  </header>

  <div class="nav">
    <a href="#deals">羊毛情报</a>
    <a href="#github-hot">GitHub 新热门</a>
    <a href="#hot-topics">最近热议</a>
  </div>

  <div class="toolbar" id="deals">
    <input id="q" type="search" placeholder="搜索标题 / 内容 / 作者 / 链接 / 来源…" autocomplete="off" />
    <div class="tabs">{''.join(tabs)}</div>
  </div>

  <div id="list">
    {''.join(sections) if sections else '<div class="empty">暂无羊毛条目</div>'}
  </div>
  <div id="empty" class="empty hidden">没有匹配的羊毛条目，换个关键词试试。</div>

  {repo_html}
  {hot_html}

  <div class="archive">
    <h2>历史存档（JSON）</h2>
    <div>{''.join(archive) if archive else '<span>暂无</span>'}</div>
  </div>

  <div class="disclaimer">
    <h2>免责声明</h2>
    <p>信息来自公开网页与 X 帖子，自动整理，可能过期、不准确或含推广。参与前请自行核实官网与活动规则，谨防诈骗、钓鱼与盗号。本站不保证任何活动有效，也不提供领奖代操作。</p>
  </div>
  <footer>Yi Kos · 免费自动更新 · 仅 AI / 科技类</footer>
</div>
<script>
(function(){{
  const q = document.getElementById('q');
  const tabs = [...document.querySelectorAll('.tab')];
  const cards = [...document.querySelectorAll('.deal-section .card')];
  const sections = [...document.querySelectorAll('.deal-section')];
  const empty = document.getElementById('empty');
  let filter = '全部';
  function apply(){{
    const term = (q.value || '').trim().toLowerCase();
    let shown = 0;
    cards.forEach(card => {{
      const cat = card.getAttribute('data-cat') || '';
      const text = (card.getAttribute('data-text') || '').toLowerCase();
      const okCat = filter === '全部' || cat === filter;
      const okTerm = !term || text.includes(term);
      const ok = okCat && okTerm;
      card.classList.toggle('hidden', !ok);
      if (ok) shown++;
    }});
    sections.forEach(sec => {{
      const any = [...sec.querySelectorAll('.card')].some(c => !c.classList.contains('hidden'));
      sec.classList.toggle('hidden', !any);
    }});
    empty.classList.toggle('hidden', shown > 0 || cards.length === 0);
  }}
  tabs.forEach(btn => btn.addEventListener('click', () => {{
    tabs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filter = btn.getAttribute('data-filter') || '全部';
    apply();
  }}));
  q.addEventListener('input', apply);
}})();
</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} deals={len(items)} repos={len(repos)} topics={len(topics)} date={date}")
    for c in CATEGORIES:
        if counts.get(c, 0):
            print(f"  {c}: {counts[c]}")
    print("  sources:", src_counts)
    return OUT


if __name__ == "__main__":
    build()
