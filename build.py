#!/usr/bin/env python3
"""Build Baidu-SEO static site: index, categories, items, archives, sitemaps, 404."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SITE = Path(__file__).resolve().parent
DATA = SITE / "data"
AUTO = DATA / "auto"
ARCHIVES = SITE / "archives"
ITEMS = SITE / "item"
CATS = SITE / "c"
CFG_PATH = SITE / "seo_config.json"
TZ = ZoneInfo("Asia/Shanghai")

DEFAULT_CFG = {
    "site_name": "AI大模型免费资源导航",
    "canonical": "https://aidamoxing-mianfei.netlify.app/",
    "baidu_site_verification": "",
    "baidu_push_site": "https://aidamoxing-mianfei.netlify.app",
}

CATEGORIES = [
    "大模型 API 免费额度",
    "AI 产品会员/试用",
    "AI 开发工具与编程助手",
    "云服务/GPU/开发者资源",
    "科技软件/App 限免",
    "其他科技",
]

CAT_SLUG = {
    "大模型 API 免费额度": "damoxing-mianfei-api",
    "AI 产品会员/试用": "ai-huiyuan-shiyong",
    "AI 开发工具与编程助手": "ai-kaifa-gongju",
    "云服务/GPU/开发者资源": "mianfei-gpu-yunfuwu",
    "科技软件/App 限免": "keji-app-xianmian",
    "其他科技": "qita-keji",
}

CAT_INTRO = {
    "大模型 API 免费额度": (
        "本栏目持续整理大模型免费API、免费GPT接口、Claude免费额度、DeepSeek免费额度与各类"
        "LLM Token 试用信息。内容来自公开网页与社区帖子，经自动抓取汇总，方便开发者快速对比"
        "免费API额度与领取入口。请以官网活动规则为准，注意密钥安全，勿轻信私下代充。"
    ),
    "AI 产品会员/试用": (
        "这里汇总 AI 工具免费试用、会员限免与公开 Beta 资讯，覆盖写作、绘画、语音与办公类"
        "产品。关键词包括 AI工具免费、免费会员试用等。每条保留完整说明与来源链接，便于判断"
        "是否仍有效。参与前请核对官网与支付条款，避免误绑信用卡产生费用。"
    ),
    "AI 开发工具与编程助手": (
        "面向程序员的 AI 开发工具与编程助手导航：代码补全、Agent、评测与开源助手等。适合搜索"
        "AI编程助手、AI开源项目推荐。页面展示完整标题、说明与仓库/官网链接，并与 GitHub 热门"
        "项目互相跳转。工具能力以官方文档为准，注意权限与隐私设置。"
    ),
    "云服务/GPU/开发者资源": (
        "收集免费GPU、云算力试用、开发者资源与相关免费额度信息，方便训练、推理与实验。适合"
        "检索免费GPU、云服务免费额度。条目来自公开来源自动整理，可能随时变更；使用前确认区域、"
        "配额与实名要求，谨防钓鱼站点。"
    ),
    "科技软件/App 限免": (
        "科技软件与 App 限免、开源替代与效率工具精选，强调 AI / 开发相关，不收录购物返利。"
        "适合关注科技App限免、AI工具免费。每条含来源与原文链接，建议尽快核验是否仍限免，"
        "并注意应用权限与隐私政策。"
    ),
    "其他科技": (
        "其他与大模型、AI 工具、开发者生态相关的科技资讯与资源入口。可作为「最新AI新闻」与"
        "长尾关键词补充阅读。内容保持全文展示，并链回分类页与相关条目，便于百度抓取更多"
        "内链。信息自动更新，时效性请以原文为准。"
    ),
}

LONGTAIL = (
    "大模型免费API、免费GPT、Claude免费、DeepSeek免费额度、AI工具免费、"
    "免费GPU、GitHub热门项目、AI开源项目推荐、最新AI新闻"
)

KEYWORDS = (
    "AI大模型免费资源,大模型免费API,免费GPT,Claude免费,DeepSeek免费额度,"
    "AI工具免费,免费GPU,GitHub热门项目,AI开源项目推荐,最新AI新闻,"
    "免费API额度,AI开发工具,LLM免费额度,AI编程助手"
)


def load_cfg() -> dict:
    cfg = dict(DEFAULT_CFG)
    if CFG_PATH.exists():
        try:
            cfg.update(json.loads(CFG_PATH.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"[warn] seo_config: {e}")
    env_v = (os.environ.get("VERIFY_BAIDU") or os.environ.get("BAIDU_SITE_VERIFICATION") or "").strip()
    if env_v:
        cfg["baidu_site_verification"] = env_v
    cfg["canonical"] = (cfg.get("canonical") or DEFAULT_CFG["canonical"]).rstrip("/") + "/"
    return cfg


CFG = load_cfg()
SITE_NAME = CFG["site_name"]
CANONICAL = CFG["canonical"]
META_DESC = (
    f"{SITE_NAME}汇总大模型免费API、免费GPT、Claude免费、DeepSeek免费额度、"
    f"AI工具免费、免费GPU与GitHub热门项目，每日自动更新，方便百度搜索与收藏。"
)


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def parse_deadline(s: str | None):
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
    m = re.match(r"(20\d{2})-(\d{2})", date_str or "")
    if m:
        return f"{m.group(1)}年{int(m.group(2))}月最新"
    now = datetime.now(TZ)
    return f"{now.year}年{now.month}月最新"


def item_slug(item: dict) -> str:
    url = item.get("url") or item.get("id") or item.get("title") or ""
    h = hashlib.sha1(str(url).encode("utf-8")).hexdigest()[:10]
    title = item.get("title") or ""
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    ascii_part = re.sub(r"-{2,}", "-", ascii_part)[:36].strip("-")
    cat = CAT_SLUG.get(item.get("category") or "", "item")
    if ascii_part and len(ascii_part) >= 4:
        return f"{ascii_part}-{h}"
    return f"{cat}-{h}"


def collect_deal_items():
    now = datetime.now(TZ)
    items = []
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
        if (it.get("category") or "其他科技") not in CATEGORIES:
            it["category"] = "其他科技"
        it["_slug"] = item_slug(it)
        it["_path"] = f"item/{it['_slug']}.html"
        seen.add(u)
        uniq.append(it)
    if not latest_date:
        latest_date = now.strftime("%Y-%m-%d")
    if not latest_label:
        latest_label = now.strftime("%Y-%m-%d %H:%M Asia/Shanghai")
    return uniq, latest_date, latest_label


def load_section(name: str):
    path = AUTO / name
    d = load_json(path) if path.exists() else None
    if not d:
        return [], ""
    return d.get("items") or [], d.get("updated_at_label") or ""


def list_archive_dates():
    dates = set()
    for f in DATA.glob("????-??-??.json"):
        dates.add(f.stem)
    for f in AUTO.glob("????-??-??.json"):
        dates.add(f.stem)
    return sorted(dates, reverse=True)


def items_for_date(day: str):
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
            if (it.get("category") or "其他科技") not in CATEGORIES:
                it["category"] = "其他科技"
            it["_slug"] = item_slug(it)
            it["_path"] = f"item/{it['_slug']}.html"
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


CSS = """
:root {
  --bg: #070b16; --bg2: #0d1428; --panel: rgba(18, 26, 52, 0.72); --panel-solid: #121a34;
  --card: rgba(22, 32, 64, 0.78); --card-hover: rgba(30, 44, 88, 0.92);
  --line: rgba(120, 150, 220, 0.22); --line-strong: rgba(140, 175, 255, 0.38);
  --text: #eef2ff; --muted: #9aa6c9; --accent: #6ea8ff; --accent2: #5ef0c0;
  --accent3: #a78bfa; --warn: #ffc857; --shadow: 0 18px 50px rgba(0,0,0,.35);
  --radius: 18px; --glass: blur(18px) saturate(1.35);
  --hero-a: rgba(110,168,255,.22); --hero-b: rgba(167,139,250,.16); --hero-c: rgba(94,240,192,.10);
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #f4f7ff; --bg2: #e8eefc; --panel: rgba(255,255,255,.78); --panel-solid: #fff;
    --card: rgba(255,255,255,.86); --card-hover: #fff;
    --line: rgba(70,100,180,.16); --line-strong: rgba(70,110,210,.32);
    --text: #12182b; --muted: #5b6688; --accent: #2f6df6; --accent2: #0f9f75;
    --accent3: #6d4ce0; --warn: #c27a00; --shadow: 0 16px 40px rgba(40,70,140,.12);
    --hero-a: rgba(47,109,246,.14); --hero-b: rgba(109,76,224,.10); --hero-c: rgba(15,159,117,.08);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
html, body { margin:0; padding:0; overflow-wrap:anywhere; word-break:break-word; }
body {
  font-family: "PingFang SC","Hiragino Sans GB","Noto Sans SC","Microsoft YaHei",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color: var(--text);
  background:
    radial-gradient(1200px 700px at 8% -12%, var(--hero-a), transparent 55%),
    radial-gradient(900px 560px at 92% 0%, var(--hero-b), transparent 50%),
    radial-gradient(800px 500px at 50% 110%, var(--hero-c), transparent 55%),
    linear-gradient(180deg, var(--bg), var(--bg2) 40%, var(--bg));
  min-height: 100vh; line-height: 1.65; -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1120px; margin: 0 auto; padding: 22px 16px 72px; }
.hero {
  position: relative; overflow: hidden; border: 1px solid var(--line-strong); border-radius: 24px;
  padding: 28px 22px 22px; margin-bottom: 18px;
  background: linear-gradient(135deg, var(--hero-a), transparent 42%), linear-gradient(225deg, var(--hero-b), transparent 40%), var(--panel);
  backdrop-filter: var(--glass); -webkit-backdrop-filter: var(--glass); box-shadow: var(--shadow);
}
.brand { display: inline-flex; align-items: center; gap: 10px; font-size: .78rem; letter-spacing: .08em;
  color: var(--accent2); font-weight: 600; margin-bottom: 10px; }
.brand .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent2);
  box-shadow: 0 0 0 4px rgba(94,240,192,.18); }
.hero h1 { margin: 0 0 10px; font-size: clamp(1.35rem, 4.4vw, 2rem); font-weight: 720; letter-spacing: -.02em; line-height: 1.25; }
.hero .tagline { margin: 0; color: var(--muted); font-size: .98rem; max-width: 52rem; }
.stats { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.pill { display: inline-flex; align-items: center; gap: 6px; background: rgba(0,0,0,.18);
  border: 1px solid var(--line); border-radius: 999px; padding: 7px 12px; font-size: .84rem; color: var(--muted); }
@media (prefers-color-scheme: light) { .pill { background: rgba(255,255,255,.55); } }
.pill b { color: var(--accent2); font-weight: 650; }
.sticky-nav {
  position: sticky; top: 10px; z-index: 40; display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px;
  padding: 10px; border-radius: 16px; border: 1px solid var(--line); background: var(--panel);
  backdrop-filter: var(--glass); -webkit-backdrop-filter: var(--glass); box-shadow: 0 10px 30px rgba(0,0,0,.12);
}
.sticky-nav a {
  border: 1px solid var(--line); border-radius: 999px; padding: 8px 12px; background: rgba(255,255,255,.03);
  color: var(--text); font-size: .86rem; transition: border-color .2s, transform .15s, background .2s;
}
.sticky-nav a:hover { border-color: var(--accent); text-decoration: none; transform: translateY(-1px); background: rgba(110,168,255,.10); }
.toolbar { border: 1px solid var(--line); border-radius: 16px; padding: 12px; margin-bottom: 16px; background: var(--panel);
  backdrop-filter: var(--glass); -webkit-backdrop-filter: var(--glass); }
#q { width: 100%; padding: 13px 16px; border-radius: 12px; border: 1px solid var(--line); background: var(--panel-solid);
  color: var(--text); font-size: 1rem; outline: none; }
#q:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(110,168,255,.18); }
.tabs { display: flex; gap: 8px; overflow-x: auto; padding: 10px 2px 2px; scrollbar-width: thin; -webkit-overflow-scrolling: touch; }
.tab { flex: 0 0 auto; border: 1px solid var(--line); background: transparent; color: var(--muted); border-radius: 999px;
  padding: 8px 13px; cursor: pointer; font-size: .85rem; white-space: nowrap; }
.tab em { font-style: normal; color: var(--accent); margin-left: 4px; }
.tab.active, .tab:hover { color: var(--text); border-color: var(--accent); background: rgba(110,168,255,.12); }
.section { margin: 26px 0; }
.section h2 { font-size: 1.18rem; margin: 0 0 8px; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.section h2 span { color: var(--muted); font-weight: 500; font-size: .9rem; }
.sec-desc { margin: 0 0 14px; color: var(--muted); font-size: .92rem; }
.grid { display: grid; grid-template-columns: 1fr; gap: 14px; }
@media (min-width: 720px) { .grid { grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); } }
.card {
  position: relative; background: linear-gradient(160deg, rgba(110,168,255,.08), transparent 42%), var(--card);
  border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 15px 14px; overflow: visible; max-height: none;
  transition: transform .18s ease, border-color .18s ease, background .18s ease, box-shadow .18s ease;
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
}
.card:hover { transform: translateY(-3px); border-color: var(--line-strong); box-shadow: var(--shadow);
  background: linear-gradient(160deg, rgba(110,168,255,.14), transparent 45%), var(--card-hover); }
.card.repo { background: linear-gradient(160deg, rgba(167,139,250,.10), transparent 42%), var(--card); }
.card.hot { background: linear-gradient(160deg, rgba(94,240,192,.08), transparent 42%), var(--card); }
.badgerow { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px; }
.badge { display: inline-block; font-size: .72rem; color: #d7e6ff;
  background: linear-gradient(135deg, rgba(110,168,255,.22), rgba(167,139,250,.16));
  border: 1px solid rgba(110,168,255,.35); border-radius: 999px; padding: 3px 9px; font-weight: 600; }
@media (prefers-color-scheme: light) { .badge { color: #244a9a; } }
.src-tag, .dl-tag { display: inline-flex; font-size: .72rem; border-radius: 999px; padding: 3px 9px;
  border: 1px solid var(--line); color: var(--muted); background: rgba(255,255,255,.04); }
.src-tag { color: var(--accent2); border-color: rgba(94,240,192,.28); }
.dl-tag { color: var(--warn); border-color: rgba(255,200,87,.35); }
.title { margin: 0 0 10px; font-size: 1.05rem; line-height: 1.45; font-weight: 650; overflow-wrap: anywhere; white-space: normal; }
.title a { color: inherit; }
.summary, .how, .meta, .linkrow, .author { margin: 0 0 10px; overflow: visible; overflow-wrap: anywhere;
  word-break: break-word; white-space: normal; max-height: none; }
.summary { color: var(--muted); font-size: .95rem; }
.how { font-size: .9rem; color: var(--text); background: rgba(255,255,255,.04); border: 1px solid var(--line);
  border-radius: 12px; padding: 10px 12px; }
.meta { font-size: .88rem; color: var(--warn); }
.author { color: var(--muted); }
.linkrow { font-size: .86rem; color: var(--muted); }
.fulllink { color: var(--accent); overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
.hidden { display: none !important; }
.panel-box { margin-top: 28px; padding: 16px; border-radius: 16px; border: 1px solid var(--line); background: var(--panel);
  backdrop-filter: var(--glass); -webkit-backdrop-filter: var(--glass); }
.panel-box h2 { margin: 0 0 10px; font-size: 1rem; }
.arch { display: inline-block; margin: 0 8px 8px 0; padding: 7px 11px; border-radius: 10px; border: 1px solid var(--line);
  color: var(--muted); background: rgba(0,0,0,.15); }
.arch:hover { border-color: var(--accent); color: var(--text); text-decoration: none; }
.arch.current { color: var(--accent2); border-color: rgba(94,240,192,.45); }
.disclaimer p, .intro p { margin: 0 0 10px; color: var(--muted); font-size: .92rem; }
.intro p:last-child { margin-bottom: 0; }
.empty { text-align: center; color: var(--muted); padding: 48px 10px; }
footer { margin-top: 28px; color: var(--muted); font-size: .8rem; text-align: center; }
.crumbs { margin: 0 0 14px; color: var(--muted); font-size: .9rem; }
.crumbs a { color: var(--accent); }
.related a { display: block; margin: 0 0 8px; }
.detail-actions { display: flex; flex-wrap: wrap; gap: 10px; margin: 14px 0; }
.btn {
  display: inline-block; padding: 10px 16px; border-radius: 12px; border: 1px solid var(--line-strong);
  background: linear-gradient(135deg, rgba(110,168,255,.2), rgba(167,139,250,.12)); color: var(--text); font-weight: 600;
}
.btn:hover { text-decoration: none; border-color: var(--accent); }
"""

SEARCH_JS = """
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
      const ok = (filter === '全部' || cat === filter) && (!term || text.includes(term));
      card.classList.toggle('hidden', !ok);
      if (ok) shown++;
    });
    sections.forEach(sec => {
      sec.classList.toggle('hidden', ![...sec.querySelectorAll('.card')].some(c => !c.classList.contains('hidden')));
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


def json_ld(obj) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def head_block(title: str, description: str, canonical: str, og_title: str | None = None,
               pubdate: str | None = None, extra_ld: list | None = None) -> str:
    og_title = og_title or title
    verify = (CFG.get("baidu_site_verification") or "").strip()
    verify_meta = f'<meta name="baidu-site-verification" content="{esc(verify)}" />' if verify else (
        '<!-- Set VERIFY_BAIDU env or seo_config.json baidu_site_verification after 站长平台验证 -->'
    )
    pub_meta = f'<meta property="og:article:published_time" content="{esc(pubdate)}" />\n<meta name="pubdate" content="{esc(pubdate)}" />' if pubdate else ""
    ld_html = "\n".join(json_ld(x) for x in (extra_ld or []))
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
{verify_meta}
<link rel="canonical" href="{esc(canonical)}" />
<meta property="og:type" content="website" />
<meta property="og:locale" content="zh_CN" />
<meta property="og:site_name" content="{esc(SITE_NAME)}" />
<meta property="og:title" content="{esc(og_title)}" />
<meta property="og:description" content="{esc(description)}" />
<meta property="og:url" content="{esc(canonical)}" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{esc(og_title)}" />
<meta name="twitter:description" content="{esc(description)}" />
{pub_meta}
<style>
{CSS}
</style>
{ld_html}
</head>
"""


def card_deal(item: dict, prefix: str = "") -> str:
    deadline = item.get("deadline")
    deadline_html = f'<span class="dl-tag">截止 {esc(deadline)}</span>' if deadline else ""
    how = item.get("how") or ""
    how_html = f'<div class="how"><strong>怎么领：</strong>{esc(how)}</div>' if how else ""
    url = item.get("url") or ""
    author = item.get("author") or ""
    posted = item.get("posted_at") or ""
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    cat = item.get("category") or ""
    source = item.get("source") or "未知"
    slug_path = prefix + (item.get("_path") or f"item/{item_slug(item)}.html")
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
  <h3 class="title"><a href="{esc(slug_path)}">{esc(title)}</a></h3>
  <p class="summary">{esc(summary)}</p>
  {how_html}
  {author_html}
  <div class="linkrow"><strong>详情页：</strong><a href="{esc(slug_path)}">查看免费领取方法</a>
   · <strong>原帖：</strong><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


def card_repo(item: dict) -> str:
    url = item.get("url") or ""
    title = item.get("title") or item.get("name") or ""
    summary = item.get("summary") or ""
    name = item.get("name") or ""
    stars = item.get("stars") or 0
    lang = item.get("language") or ""
    created = item.get("created_at") or ""
    search_blob = " ".join([title, summary, name, str(lang)])
    return f"""
<article class="card repo" data-text="{esc(search_blob)}">
  <div class="badgerow"><span class="badge">GitHub热门项目</span><span class="src-tag">来源 GitHub</span></div>
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
  <div class="badgerow"><span class="badge">最新AI新闻 / 热议</span><span class="src-tag">来源 {esc(source)}</span></div>
  <h3 class="title">{esc(title)}</h3>
  <p class="summary">{esc(summary)}</p>
  <div class="meta">热度：{esc(heat)}</div>
  <div class="linkrow"><strong>链接：</strong><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


def nav(prefix: str = "") -> str:
    return f"""
<nav class="sticky-nav" aria-label="栏目导航">
  <a href="{prefix}./">首页</a>
  <a href="{prefix}c/damoxing-mianfei-api.html">大模型免费API</a>
  <a href="{prefix}c/ai-huiyuan-shiyong.html">AI工具免费</a>
  <a href="{prefix}c/ai-kaifa-gongju.html">AI开发工具</a>
  <a href="{prefix}c/mianfei-gpu-yunfuwu.html">免费GPU</a>
  <a href="{prefix}#github-hot">GitHub热门项目</a>
  <a href="{prefix}#hot-topics">最新AI新闻</a>
  <a href="{prefix}#archives">每日存档</a>
</nav>"""


def related_items(item: dict, all_items: list[dict], n: int = 6) -> list[dict]:
    cat = item.get("category")
    same = [x for x in all_items if x is not item and x.get("category") == cat]
    others = [x for x in all_items if x is not item and x.get("category") != cat]
    out = same[:n]
    if len(out) < n:
        out += others[: n - len(out)]
    return out


def write_item_pages(all_items: list[dict], date: str) -> list[str]:
    ITEMS.mkdir(parents=True, exist_ok=True)
    paths = []
    for it in all_items:
        slug = it["_slug"]
        path = ITEMS / f"{slug}.html"
        title_zh = it.get("title") or "资源详情"
        page_title = f"{title_zh} - 免费领取方法 | {SITE_NAME}"
        desc = (it.get("summary") or title_zh)[:150]
        if len(desc) < 40:
            desc = f"{title_zh}：{it.get('category')}免费资源说明与领取方法，来自{SITE_NAME}。"
        canonical = f"{CANONICAL}item/{slug}.html"
        cat = it.get("category") or "其他科技"
        cat_slug = CAT_SLUG.get(cat, "qita-keji")
        pub = it.get("posted_at") or date
        rel = related_items(it, all_items)
        rel_html = "".join(
            f'<a href="{esc(r["_slug"])}.html">{esc(r.get("title") or "")}</a>' for r in rel
        )
        how = it.get("how") or "打开来源链接，按页面说明领取或试用；参与前请自行核实官网信息。"
        ld = [
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": title_zh,
                "description": desc,
                "datePublished": pub,
                "dateModified": date,
                "author": {"@type": "Organization", "name": SITE_NAME},
                "mainEntityOfPage": canonical,
                "keywords": f"{cat},大模型免费API,AI工具免费",
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "首页", "item": CANONICAL},
                    {"@type": "ListItem", "position": 2, "name": cat, "item": f"{CANONICAL}c/{cat_slug}.html"},
                    {"@type": "ListItem", "position": 3, "name": title_zh, "item": canonical},
                ],
            },
        ]
        page = f"""{head_block(page_title, desc, canonical, title_zh, pubdate=str(pub), extra_ld=ld)}
<body>
<div class="wrap">
  <div class="crumbs">
    <a href="../">首页</a> ›
    <a href="../c/{esc(cat_slug)}.html">{esc(cat)}</a> ›
    <span>{esc(title_zh)}</span>
  </div>
  {nav("../")}
  <header class="hero">
    <div class="brand"><span class="dot"></span> DETAIL</div>
    <h1>{esc(title_zh)}</h1>
    <p class="tagline">{esc(cat)} · 来源 {esc(it.get("source") or "公开网页")} · 长尾词覆盖：大模型免费API / AI工具免费</p>
    <div class="stats">
      <div class="pill">分类 <b>{esc(cat)}</b></div>
      <div class="pill">更新 <b>{esc(date)}</b></div>
      {"<div class='pill'>截止 <b>"+esc(it.get("deadline"))+"</b></div>" if it.get("deadline") else ""}
    </div>
  </header>
  <section class="panel-box intro">
    <h2>资源说明</h2>
    <p>{esc(it.get("summary") or title_zh)}</p>
    <div class="how"><strong>免费领取方法：</strong>{esc(how)}</div>
    <div class="detail-actions">
      <a class="btn" href="{esc(it.get("url") or "#")}" target="_blank" rel="noopener noreferrer">打开原帖 / 官网</a>
      <a class="btn" href="../c/{esc(cat_slug)}.html">同分类更多</a>
    </div>
    <p class="meta author">作者：@{esc(it.get("author") or "未知")} · {esc(it.get("posted_at") or "")}</p>
    <p class="linkrow">原文链接：<a class="fulllink" href="{esc(it.get("url") or "")}" target="_blank" rel="noopener noreferrer">{esc(it.get("url") or "")}</a></p>
  </section>
  <section class="panel-box">
    <h2>相关资源推荐</h2>
    <div class="related">{rel_html or "<span>暂无</span>"}</div>
  </section>
  <section class="panel-box disclaimer">
    <h2>免责声明</h2>
    <p>信息自动整理，可能过期或不准确。参与前请自行核实官网与活动规则，谨防诈骗。</p>
  </section>
  <footer>{esc(SITE_NAME)} · 条目详情 · 百度 SEO</footer>
</div>
</body>
</html>
"""
        path.write_text(page, encoding="utf-8")
        paths.append(f"item/{slug}.html")
    return paths


def write_category_pages(all_items: list[dict], date: str, ym: str) -> list[str]:
    CATS.mkdir(parents=True, exist_ok=True)
    paths = []
    for cat in CATEGORIES:
        slug = CAT_SLUG[cat]
        cat_items = [it for it in all_items if it.get("category") == cat]
        page_title = f"{cat} - 大模型免费API与AI工具免费 | {SITE_NAME} · {ym}"
        intro = CAT_INTRO[cat]
        desc = intro[:120]
        canonical = f"{CANONICAL}c/{slug}.html"
        cards = "\n".join(card_deal(it, prefix="../") for it in cat_items) if cat_items else '<div class="empty">本分类暂无条目，系统将保留历史数据并在下次抓取时恢复。</div>'
        ld = [
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": page_title,
                "description": desc,
                "url": canonical,
            },
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "url": f"{CANONICAL}{it['_path']}",
                        "name": it.get("title") or "",
                    }
                    for i, it in enumerate(cat_items[:50])
                ],
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "首页", "item": CANONICAL},
                    {"@type": "ListItem", "position": 2, "name": cat, "item": canonical},
                ],
            },
        ]
        other = "".join(
            f'<a class="arch" href="{esc(CAT_SLUG[c])}.html">{esc(c)}</a>' for c in CATEGORIES if c != cat
        )
        page = f"""{head_block(page_title, desc, canonical, f"{cat} | {SITE_NAME}", extra_ld=ld)}
<body>
<div class="wrap">
  <div class="crumbs"><a href="../">首页</a> › <span>{esc(cat)}</span></div>
  {nav("../")}
  <header class="hero">
    <div class="brand"><span class="dot"></span> CATEGORY</div>
    <h1>{esc(cat)} · {esc(ym)}</h1>
    <p class="tagline">聚焦长尾词：{esc(LONGTAIL)}</p>
    <div class="stats">
      <div class="pill">条目 <b>{len(cat_items)}</b></div>
      <div class="pill">更新 <b>{esc(date)}</b></div>
    </div>
  </header>
  <section class="panel-box intro">
    <h2>{esc(cat)}栏目介绍</h2>
    <p>{esc(intro)}</p>
  </section>
  <section class="section deal-section">
    <h2>{esc(cat)}资源列表 <span>({len(cat_items)})</span></h2>
    <div class="grid">{cards}</div>
  </section>
  <section class="panel-box">
    <h2>其他分类</h2>
    <div>{other}</div>
  </section>
  <footer>{esc(SITE_NAME)} · 分类着陆页</footer>
</div>
</body>
</html>
"""
        (CATS / f"{slug}.html").write_text(page, encoding="utf-8")
        paths.append(f"c/{slug}.html")
    return paths


def write_archive_page(day: str, items: list[dict], all_dates: list[str]):
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    ym = ym_label(day)
    title = f"{SITE_NAME} · {day} 存档 · {ym}"
    desc = f"{SITE_NAME} {day} 日归档：大模型免费API、AI工具免费、GitHub热门项目汇总。"
    canonical = f"{CANONICAL}archives/{day}.html"
    sections = []
    for c in CATEGORIES:
        cat_items = [it for it in items if it.get("category") == c]
        if not cat_items:
            continue
        cards = "\n".join(card_deal(it, prefix="../") for it in cat_items)
        sections.append(
            f'<section class="section deal-section"><h2>{esc(c)} <span>({len(cat_items)})</span></h2><div class="grid">{cards}</div></section>'
        )
    arch_links = "".join(
        f'<a class="arch {"current" if d==day else ""}" href="{esc(d)}.html">{esc(d)}</a>' for d in all_dates[:60]
    )
    page = f"""{head_block(title, desc, canonical)}
<body>
<div class="wrap">
  <div class="crumbs"><a href="../">首页</a> › 日归档 › {esc(day)}</div>
  {nav("../")}
  <header class="hero">
    <div class="brand"><span class="dot"></span> DAILY ARCHIVE</div>
    <h1>{esc(SITE_NAME)} · {esc(day)}</h1>
    <p class="tagline">{esc(ym)} 存档 · 共 {len(items)} 条 · 覆盖大模型免费API与AI工具免费</p>
  </header>
  <div id="list">{''.join(sections) if sections else '<div class="empty">该日暂无条目</div>'}</div>
  <div class="panel-box"><h2>更多日期</h2><div>{arch_links}</div></div>
  <footer>{esc(SITE_NAME)} · 日归档</footer>
</div>
</body>
</html>
"""
    (ARCHIVES / f"{day}.html").write_text(page, encoding="utf-8")


def write_404():
    page = f"""{head_block(f"页面未找到 | {SITE_NAME}", META_DESC, CANONICAL + "404.html")}
<body>
<div class="wrap">
  <header class="hero">
    <h1>404 · 页面不存在</h1>
    <p class="tagline">链接可能已更新。请返回首页查看大模型免费API、AI工具免费与GitHub热门项目。</p>
  </header>
  {nav("./")}
  <p><a class="btn" href="./">返回首页</a></p>
</div>
</body>
</html>
"""
    (SITE / "404.html").write_text(page, encoding="utf-8")


def write_sitemaps(urls: list[tuple[str, str, str, str]]):
    """urls: (loc_path, lastmod, changefreq, priority)"""
    now = datetime.now(TZ).strftime("%Y-%m-%d")
    # main sitemap
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    abs_urls = []
    for path, lastmod, freq, pri in urls:
        loc = CANONICAL if path in ("", "/") else f"{CANONICAL}{path.lstrip('/')}"
        abs_urls.append(loc)
        body.append(
            f"  <url><loc>{esc(loc)}</loc><lastmod>{esc(lastmod or now)}</lastmod>"
            f"<changefreq>{esc(freq)}</changefreq><priority>{esc(pri)}</priority></url>"
        )
    body.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(body) + "\n", encoding="utf-8")
    (SITE / "sitemap.txt").write_text("\n".join(abs_urls) + "\n", encoding="utf-8")
    # sitemap index
    idx = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>{CANONICAL}sitemap.xml</loc><lastmod>{now}</lastmod></sitemap>
  <sitemap><loc>{CANONICAL}sitemap.txt</loc><lastmod>{now}</lastmod></sitemap>
</sitemapindex>
"""
    (SITE / "sitemap_index.xml").write_text(idx, encoding="utf-8")
    robots = f"""User-agent: *
Allow: /
User-agent: Baiduspider
Allow: /
User-agent: Baiduspider-render
Allow: /
Sitemap: {CANONICAL}sitemap_index.xml
Sitemap: {CANONICAL}sitemap.xml
Sitemap: {CANONICAL}sitemap.txt
"""
    (SITE / "robots.txt").write_text(robots, encoding="utf-8")
    return abs_urls


def build() -> Path:
    global CFG, SITE_NAME, CANONICAL, META_DESC
    CFG = load_cfg()
    SITE_NAME = CFG["site_name"]
    CANONICAL = CFG["canonical"]
    META_DESC = (
        f"{SITE_NAME}汇总大模型免费API、免费GPT、Claude免费、DeepSeek免费额度、"
        f"AI工具免费、免费GPU与GitHub热门项目，每日自动更新，方便百度搜索与收藏。"
    )

    items, date, updated = collect_deal_items()
    repos, repos_updated = load_section("github_hot.json")
    topics, topics_updated = load_section("hot_topics.json")
    dates = list_archive_dates()
    ym = ym_label(date)

    item_paths = write_item_pages(items, date)
    cat_paths = write_category_pages(items, date, ym)
    for d in dates:
        write_archive_page(d, items_for_date(d), dates)
    write_404()

    counts = {c: 0 for c in CATEGORIES}
    src_counts = {}
    for it in items:
        c = it.get("category") or "其他科技"
        counts[c] = counts.get(c, 0) + 1
        s = it.get("source") or "?"
        src_counts[s] = src_counts.get(s, 0) + 1

    tabs = [f'<button class="tab active" data-filter="全部">全部资源 <em>{len(items)}</em></button>']
    for c in CATEGORIES:
        if counts.get(c, 0):
            tabs.append(f'<button class="tab" data-filter="{esc(c)}">{esc(c)} <em>{counts[c]}</em></button>')

    sections = []
    for c in CATEGORIES:
        cat_items = [it for it in items if it.get("category") == c]
        if not cat_items:
            continue
        slug = CAT_SLUG[c]
        cards = "\n".join(card_deal(it) for it in cat_items)
        sections.append(
            f'<section class="section deal-section" id="cat-{esc(slug)}">'
            f'<h2><a href="c/{esc(slug)}.html">{esc(c)}</a> <span>({len(cat_items)})</span></h2>'
            f'<p class="sec-desc">{esc(CAT_INTRO[c][:90])}… <a href="c/{esc(slug)}.html">进入分类页</a></p>'
            f'<div class="grid">{cards}</div></section>'
        )

    repo_html = ""
    if repos:
        repo_html = f"""
<section class="section" id="github-hot">
  <h2>GitHub热门项目 / AI开源项目推荐 <span>({len(repos)})</span></h2>
  <p class="sec-desc">近 7–14 天创建的 AI / 大模型 / Agent 仓库。更新：{esc(repos_updated)}</p>
  <div class="grid">{"".join(card_repo(r) for r in repos)}</div>
</section>"""
    hot_html = ""
    if topics:
        hot_html = f"""
<section class="section" id="hot-topics">
  <h2>最新AI新闻 / 最近热议 <span>({len(topics)})</span></h2>
  <p class="sec-desc">Hacker News / V2EX / X。更新：{esc(topics_updated)}</p>
  <div class="grid">{"".join(card_hot(t) for t in topics)}</div>
</section>"""

    arch_links = "".join(
        f'<a class="arch {"current" if d==date else ""}" href="archives/{esc(d)}.html">{esc(d)}</a>'
        for d in dates[:90]
    )
    cat_links = "".join(
        f'<a class="arch" href="c/{esc(CAT_SLUG[c])}.html">{esc(c)}（{counts.get(c,0)}）</a>' for c in CATEGORIES
    )
    now_label = datetime.now(TZ).strftime("%Y-%m-%d %H:%M Asia/Shanghai")
    src_pills = "".join(
        f'<div class="pill">来源 {esc(k)} <b>{v}</b></div>' for k, v in sorted(src_counts.items())
    )

    website_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": CANONICAL,
        "description": META_DESC,
        "inLanguage": "zh-CN",
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{CANONICAL}?q={{search_term_string}}",
            "query-input": "required name=search_term_string",
        },
    }
    itemlist_ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{CANONICAL}{it['_path']}", "name": it.get("title") or ""}
            for i, it in enumerate(items[:40])
        ],
    }

    page_title = f"{SITE_NAME} · {ym} · 大模型免费API / 免费GPT / Claude免费 / DeepSeek免费额度"
    page = f"""{head_block(page_title, META_DESC, CANONICAL, SITE_NAME + " · " + ym, extra_ld=[website_ld, itemlist_ld])}
<body>
<div class="wrap">
  <header class="hero">
    <div class="brand"><span class="dot"></span> LIVE · AUTO UPDATE</div>
    <h1>{esc(SITE_NAME)}</h1>
    <p class="tagline">大模型免费API · 免费GPT · Claude免费 · DeepSeek免费额度 · AI工具免费 · 免费GPU · GitHub热门项目 · {esc(ym)}</p>
    <div class="stats">
      <div class="pill">更新日期 <b>{esc(date)}</b></div>
      <div class="pill">免费资源 <b>{len(items)}</b></div>
      <div class="pill">详情页 <b>{len(item_paths)}</b></div>
      <div class="pill">GitHub热门 <b>{len(repos)}</b></div>
      <div class="pill">热议 <b>{len(topics)}</b></div>
      <div class="pill">最近更新 <b>{esc(updated)}</b></div>
      <div class="pill">页面生成 <b>{esc(now_label)}</b></div>
      {src_pills}
    </div>
  </header>
  {nav("./")}
  <section class="panel-box intro" id="deals">
    <h2>站点导读</h2>
    <p>{esc(SITE_NAME)}面向百度用户整理 AI / 大模型免费资源，覆盖{esc(LONGTAIL)}。
    全站静态 HTML，条目、分类与日归档互相内链，便于收录。数据由 GitHub Actions 每 6 小时自动抓取；
    翻译服务不可用时自动回退，绝不留下空白页。</p>
  </section>
  <div class="toolbar">
    <input id="q" type="search" placeholder="搜索标题 / 内容 / 作者 / 链接 / 来源…" autocomplete="off" />
    <div class="tabs">{''.join(tabs)}</div>
  </div>
  <div id="list">{''.join(sections) if sections else '<div class="empty">暂无资源，将自动保留上次数据。</div>'}</div>
  <div id="empty" class="empty hidden">没有匹配条目。</div>
  {repo_html}
  {hot_html}
  <div class="panel-box"><h2>分类着陆页</h2><div>{cat_links}</div></div>
  <div class="panel-box" id="archives"><h2>每日存档</h2><div>{arch_links}</div></div>
  <div class="panel-box disclaimer"><h2>免责声明</h2>
    <p>信息来自公开网页与社区，自动整理，可能过期或不准确。参与前请自行核实官网规则，谨防诈骗。</p>
  </div>
  <footer>{esc(SITE_NAME)} · 全自动更新 · {esc(CANONICAL)}</footer>
</div>
<script>
{SEARCH_JS}
</script>
</body>
</html>
"""
    out = SITE / "index.html"
    out.write_text(page, encoding="utf-8")

    url_entries = [("", date, "hourly", "1.0"), ("404.html", date, "yearly", "0.1")]
    for p in cat_paths:
        url_entries.append((p, date, "daily", "0.9"))
    for p in item_paths:
        url_entries.append((p, date, "weekly", "0.8"))
    for d in dates:
        url_entries.append((f"archives/{d}.html", d, "weekly", "0.7"))
    write_sitemaps(url_entries)

    print(
        f"wrote index deals={len(items)} items_pages={len(item_paths)} cats={len(cat_paths)} "
        f"archives={len(dates)} repos={len(repos)} topics={len(topics)}"
    )
    return out


if __name__ == "__main__":
    build()
