#!/usr/bin/env python3
"""Build multi-page Baidu-SEO site: landing + module pages + items + archives."""
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
MODS = SITE / "m"
CFG_PATH = SITE / "seo_config.json"
TZ = ZoneInfo("Asia/Shanghai")

DEFAULT_CFG = {
    "site_name": "AI大模型免费资源导航",
    "canonical": "https://ai168.netlify.app/",
    "baidu_site_verification": "",
    "baidu_push_site": "https://ai168.netlify.app",
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
    "大模型 API 免费额度": "汇总大模型免费API、免费GPT、Claude免费、DeepSeek免费额度等公开试用与免费Token信息，方便对照领取入口与规则。",
    "AI 产品会员/试用": "精选 AI 工具免费试用与会员限免资讯，覆盖写作、绘画、语音与办公类产品，附完整说明与来源。",
    "AI 开发工具与编程助手": "面向开发者的 AI 编程助手、Agent 与代码工具导航，适合关注 AI开源项目推荐与效率提升。",
    "云服务/GPU/开发者资源": "免费GPU、云算力试用与开发者资源入口，便于训练、推理与实验前快速筛选。",
    "科技软件/App 限免": "科技软件与 App 限免、开源替代精选，强调 AI / 开发相关。",
    "其他科技": "其他与大模型、AI 工具相关的科技资讯与资源补充阅读。",
}

LONGTAIL = "大模型免费API、免费GPT、Claude免费、DeepSeek免费额度、AI工具免费、免费GPU、GitHub热门项目、最新AI新闻"
KEYWORDS = (
    "AI大模型免费资源,大模型免费API,免费GPT,Claude免费,DeepSeek免费额度,"
    "AI工具免费,免费GPU,GitHub热门项目,AI开源项目推荐,最新AI新闻"
)

MODULES = [
    ("damoxing-mianfei-api", "大模型 API 免费额度", "免费GPT / Claude / DeepSeek 等额度入口", "c/damoxing-mianfei-api.html", "cat", "大模型 API 免费额度"),
    ("ai-huiyuan-shiyong", "AI 产品会员/试用", "AI工具免费试用与会员限免", "c/ai-huiyuan-shiyong.html", "cat", "AI 产品会员/试用"),
    ("ai-kaifa-gongju", "AI 开发工具与编程助手", "编程助手、Agent、开发效率工具", "c/ai-kaifa-gongju.html", "cat", "AI 开发工具与编程助手"),
    ("mianfei-gpu-yunfuwu", "免费GPU / 云服务", "算力试用与开发者云资源", "c/mianfei-gpu-yunfuwu.html", "cat", "云服务/GPU/开发者资源"),
    ("keji-app-xianmian", "科技软件 / App 限免", "限免与开源替代精选", "c/keji-app-xianmian.html", "cat", "科技软件/App 限免"),
    ("github-hot", "GitHub 新热门", "AI / 大模型开源项目推荐", "m/github-hot.html", "github", None),
    ("hot-topics", "最近热议", "最新AI新闻与社区热议", "m/hot-topics.html", "hot", None),
]

CSS = '\n:root {\n  --bg0: #05070f;\n  --bg1: #0a1022;\n  --panel: rgba(12, 18, 36, 0.62);\n  --panel2: rgba(16, 24, 48, 0.78);\n  --card: rgba(14, 22, 44, 0.72);\n  --line: rgba(120, 200, 255, 0.14);\n  --line2: rgba(168, 140, 255, 0.28);\n  --text: #eef3ff;\n  --muted: #8b97b8;\n  --cyan: #5ce1ff;\n  --violet: #a78bfa;\n  --mint: #5ef0c0;\n  --warn: #ffd08a;\n  --glow: 0 0 40px rgba(92, 225, 255, 0.12);\n  --radius: 20px;\n  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;\n  --sans: "PingFang SC","Hiragino Sans GB","Noto Sans SC","Microsoft YaHei",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;\n}\n@media (prefers-color-scheme: light) {\n  :root {\n    --bg0: #f3f6ff; --bg1: #e8eefc;\n    --panel: rgba(255,255,255,.72); --panel2: rgba(255,255,255,.88);\n    --card: rgba(255,255,255,.82);\n    --line: rgba(60,100,180,.14); --line2: rgba(110,80,220,.22);\n    --text: #0e1528; --muted: #5a6688;\n    --cyan: #0891b2; --violet: #6d28d9; --mint: #0f766e; --warn: #b45309;\n    --glow: 0 0 36px rgba(8,145,178,.10);\n  }\n}\n* { box-sizing: border-box; }\nhtml { scroll-behavior: smooth; color-scheme: dark; }\nhtml, body { margin:0; padding:0; overflow-wrap:anywhere; word-break:break-word; }\nbody {\n  font-family: var(--sans);\n  color: var(--text);\n  background: var(--bg0);\n  min-height: 100vh;\n  line-height: 1.65;\n  -webkit-font-smoothing: antialiased;\n}\nbody::before {\n  content:"";\n  position: fixed; inset: 0; pointer-events: none; z-index: 0;\n  background:\n    radial-gradient(900px 500px at 12% -10%, rgba(92,225,255,.16), transparent 55%),\n    radial-gradient(800px 520px at 88% 0%, rgba(167,139,250,.18), transparent 50%),\n    radial-gradient(700px 480px at 50% 110%, rgba(94,240,192,.08), transparent 55%),\n    linear-gradient(180deg, var(--bg0), var(--bg1) 45%, var(--bg0));\n}\nbody::after {\n  content:"";\n  position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: .35;\n  background-image:\n    linear-gradient(rgba(92,225,255,.045) 1px, transparent 1px),\n    linear-gradient(90deg, rgba(92,225,255,.045) 1px, transparent 1px);\n  background-size: 56px 56px;\n  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);\n}\n@media (prefers-reduced-motion: no-preference) {\n  body::before { animation: aurora 18s ease-in-out infinite alternate; }\n  @keyframes aurora {\n    0% { filter: hue-rotate(0deg) saturate(1); }\n    100% { filter: hue-rotate(18deg) saturate(1.15); }\n  }\n}\na { color: var(--cyan); text-decoration: none; }\na:hover { text-decoration: underline; }\n.wrap { position: relative; z-index: 1; max-width: 1120px; margin: 0 auto; padding: 20px 18px 80px; }\n\n.topnav {\n  position: sticky; top: 12px; z-index: 50;\n  display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;\n  margin-bottom: 28px; padding: 10px 12px;\n  border-radius: 16px; border: 1px solid var(--line);\n  background: var(--panel); backdrop-filter: blur(18px) saturate(1.4);\n  -webkit-backdrop-filter: blur(18px) saturate(1.4);\n  box-shadow: var(--glow);\n}\n.brand-mini {\n  display: inline-flex; align-items: center; gap: 10px;\n  font-weight: 700; letter-spacing: -.01em; color: var(--text); text-decoration: none;\n}\n.brand-mini .mark {\n  width: 10px; height: 10px; border-radius: 3px;\n  background: linear-gradient(135deg, var(--cyan), var(--violet));\n  box-shadow: 0 0 16px rgba(92,225,255,.55);\n}\n.navlinks { display: flex; flex-wrap: wrap; gap: 6px; }\n.navlinks a {\n  color: var(--muted); font-size: .82rem; padding: 7px 11px; border-radius: 999px;\n  border: 1px solid transparent; text-decoration: none;\n}\n.navlinks a:hover { color: var(--text); border-color: var(--line); background: rgba(92,225,255,.06); text-decoration: none; }\n\n.hero {\n  position: relative; overflow: hidden;\n  border: 1px solid var(--line2); border-radius: 28px;\n  padding: clamp(28px, 5vw, 52px) clamp(20px, 4vw, 40px);\n  margin-bottom: 28px;\n  background:\n    linear-gradient(135deg, rgba(92,225,255,.10), transparent 40%),\n    linear-gradient(225deg, rgba(167,139,250,.12), transparent 42%),\n    var(--panel);\n  backdrop-filter: blur(20px) saturate(1.35);\n  -webkit-backdrop-filter: blur(20px) saturate(1.35);\n  box-shadow: var(--glow);\n}\n.eyebrow {\n  display: inline-flex; align-items: center; gap: 8px;\n  font-family: var(--mono); font-size: .75rem; letter-spacing: .12em; text-transform: uppercase;\n  color: var(--mint); margin-bottom: 14px;\n}\n.eyebrow i { width: 7px; height: 7px; border-radius: 50%; background: var(--mint); display: inline-block;\n  box-shadow: 0 0 0 4px rgba(94,240,192,.15); }\n.hero h1 {\n  margin: 0 0 14px; font-size: clamp(1.8rem, 5.2vw, 3rem); line-height: 1.15;\n  font-weight: 780; letter-spacing: -.03em;\n  background: linear-gradient(105deg, #fff 10%, var(--cyan) 45%, var(--violet) 85%);\n  -webkit-background-clip: text; background-clip: text; color: transparent;\n}\n@media (prefers-color-scheme: light) {\n  .hero h1 { background: linear-gradient(105deg, #0b1224 5%, var(--cyan) 45%, var(--violet) 90%);\n    -webkit-background-clip: text; background-clip: text; color: transparent; }\n}\n.hero .lead { margin: 0; max-width: 46rem; color: var(--muted); font-size: 1.05rem; }\n.stats { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }\n.pill {\n  font-family: var(--mono); font-size: .75rem; color: var(--muted);\n  border: 1px solid var(--line); border-radius: 999px; padding: 7px 12px;\n  background: rgba(255,255,255,.03);\n}\n.pill b { color: var(--cyan); font-weight: 650; }\n\n.module-grid {\n  display: grid; grid-template-columns: 1fr; gap: 16px; margin: 8px 0 28px;\n}\n@media (min-width: 720px) {\n  .module-grid { grid-template-columns: repeat(2, 1fr); }\n}\n@media (min-width: 980px) {\n  .module-grid { grid-template-columns: repeat(3, 1fr); }\n}\n.module-tile {\n  display: flex; flex-direction: column; gap: 12px;\n  padding: 20px 18px; border-radius: var(--radius);\n  border: 1px solid var(--line);\n  background: linear-gradient(160deg, rgba(92,225,255,.07), transparent 42%), var(--card);\n  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);\n  text-decoration: none; color: inherit;\n  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;\n}\n.module-tile:hover {\n  transform: translateY(-4px); text-decoration: none;\n  border-color: rgba(92,225,255,.45);\n  box-shadow: 0 0 0 1px rgba(167,139,250,.18), 0 20px 50px rgba(0,0,0,.35), 0 0 36px rgba(92,225,255,.12);\n}\n.module-tile h2 {\n  margin: 0; font-size: 1.12rem; letter-spacing: -.01em;\n  display: flex; justify-content: space-between; gap: 10px; align-items: baseline;\n}\n.module-tile h2 em {\n  font-style: normal; font-family: var(--mono); font-size: .78rem; color: var(--cyan);\n  border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px;\n}\n.module-tile .desc { margin: 0; color: var(--muted); font-size: .9rem; }\n.module-tile ol { margin: 0; padding-left: 1.1rem; color: var(--muted); font-size: .88rem; }\n.module-tile ol li { margin: 0 0 6px; }\n.module-tile .go { margin-top: auto; font-family: var(--mono); font-size: .75rem; color: var(--violet); letter-spacing: .04em; }\n\n.toolbar {\n  border: 1px solid var(--line); border-radius: 16px; padding: 12px; margin-bottom: 16px;\n  background: var(--panel); backdrop-filter: blur(14px);\n}\n#q {\n  width: 100%; padding: 13px 16px; border-radius: 12px; border: 1px solid var(--line);\n  background: rgba(0,0,0,.25); color: var(--text); font-size: 1rem; outline: none;\n}\n#q:focus { border-color: var(--cyan); box-shadow: 0 0 0 3px rgba(92,225,255,.15); }\n.grid { display: grid; grid-template-columns: 1fr; gap: 14px; }\n@media (min-width: 720px) { .grid { grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); } }\n\n.card {\n  position: relative; padding: 16px 15px 14px; border-radius: var(--radius);\n  border: 1px solid var(--line);\n  background: linear-gradient(160deg, rgba(92,225,255,.06), transparent 40%), var(--card);\n  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);\n  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;\n  overflow: visible; max-height: none;\n}\n.card:hover {\n  transform: translateY(-3px);\n  border-color: rgba(92,225,255,.4);\n  box-shadow: 0 18px 40px rgba(0,0,0,.28), 0 0 28px rgba(167,139,250,.12);\n}\n.badgerow { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }\n.badge, .src-tag, .dl-tag {\n  font-family: var(--mono); font-size: .7rem; border-radius: 999px; padding: 3px 9px; border: 1px solid var(--line);\n}\n.badge { color: var(--cyan); background: rgba(92,225,255,.08); border-color: rgba(92,225,255,.28); }\n.src-tag { color: var(--mint); border-color: rgba(94,240,192,.25); }\n.dl-tag { color: var(--warn); border-color: rgba(255,208,138,.3); }\n.title { margin: 0 0 8px; font-size: 1.05rem; font-weight: 650; line-height: 1.4; }\n.title a { color: inherit; text-decoration: none; }\n.title a:hover { color: var(--cyan); }\n.summary, .how, .meta, .linkrow, .author, .orig {\n  margin: 0 0 10px; overflow: visible; max-height: none; white-space: normal; overflow-wrap: anywhere;\n}\n.summary { color: var(--muted); font-size: .95rem; }\n.orig { font-size: .78rem; color: var(--muted); opacity: .8; margin-top: -4px; }\n.how { font-size: .9rem; border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; background: rgba(255,255,255,.03); }\n.meta, .author { font-family: var(--mono); font-size: .78rem; color: var(--warn); }\n.author { color: var(--muted); }\n.linkrow { font-size: .86rem; color: var(--muted); }\n.fulllink { color: var(--cyan); }\n.hidden { display: none !important; }\n.panel-box {\n  margin-top: 22px; padding: 18px; border-radius: 18px; border: 1px solid var(--line);\n  background: var(--panel); backdrop-filter: blur(14px);\n}\n.panel-box h2 { margin: 0 0 10px; font-size: 1rem; }\n.arch {\n  display: inline-block; margin: 0 8px 8px 0; padding: 7px 11px; border-radius: 10px;\n  border: 1px solid var(--line); color: var(--muted); font-family: var(--mono); font-size: .78rem;\n}\n.arch:hover { color: var(--text); border-color: var(--cyan); text-decoration: none; }\n.arch.current { color: var(--mint); border-color: rgba(94,240,192,.4); }\n.crumbs { margin: 0 0 16px; color: var(--muted); font-size: .9rem; }\n.btn {\n  display: inline-block; padding: 10px 16px; border-radius: 12px; border: 1px solid var(--line2);\n  background: linear-gradient(135deg, rgba(92,225,255,.16), rgba(167,139,250,.12));\n  color: var(--text); font-weight: 600; text-decoration: none;\n}\n.btn:hover { text-decoration: none; box-shadow: 0 0 24px rgba(92,225,255,.18); }\n.empty { text-align: center; color: var(--muted); padding: 48px 10px; }\nfooter { margin-top: 36px; text-align: center; color: var(--muted); font-family: var(--mono); font-size: .75rem; }\n.section { margin: 22px 0; }\n.section h2 { margin: 0 0 12px; font-size: 1.2rem; }\n.sec-desc { margin: 0 0 14px; color: var(--muted); }\n.intro p { margin: 0; color: var(--muted); }\n'


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
    if "aidamoxing-mianfei" in cfg["canonical"] or "aiyangmao" in cfg["canonical"]:
        cfg["canonical"] = "https://ai168.netlify.app/"
        cfg["baidu_push_site"] = "https://ai168.netlify.app"
    return cfg


CFG = load_cfg()
SITE_NAME = CFG["site_name"]
CANONICAL = CFG["canonical"]
META_DESC = (
    f"{SITE_NAME}汇总大模型免费API、免费GPT、Claude免费、DeepSeek免费额度、"
    f"AI工具免费、免费GPU与GitHub热门项目，每日更新。"
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
        if not u or u in seen or is_expired(it, now):
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
    dates = set(f.stem for f in DATA.glob("????-??-??.json"))
    dates |= set(f.stem for f in AUTO.glob("????-??-??.json"))
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


def json_ld(obj) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def head_block(title, description, canonical, og_title=None, pubdate=None, extra_ld=None):
    og_title = og_title or title
    verify = (CFG.get("baidu_site_verification") or "").strip()
    verify_meta = (
        f'<meta name="baidu-site-verification" content="{esc(verify)}" />'
        if verify
        else "<!-- VERIFY_BAIDU / seo_config.baidu_site_verification -->"
    )
    pub_meta = ""
    if pubdate:
        pub_meta = (
            f'<meta property="og:article:published_time" content="{esc(pubdate)}" />\n'
            f'<meta name="pubdate" content="{esc(pubdate)}" />'
        )
    ld_html = "\n".join(json_ld(x) for x in (extra_ld or []))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
<meta name="color-scheme" content="dark light" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="renderer" content="webkit" />
<meta name="force-rendering" content="webkit" />
<meta name="applicable-device" content="pc,mobile" />
<meta name="MobileOptimized" content="width" />
<meta name="HandheldFriendly" content="true" />
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
{pub_meta}
<style>
{CSS}
</style>
{ld_html}
</head>
"""


def topnav(prefix="./"):
    links = "".join(
        f'<a href="{prefix}{esc(href)}">{esc(title)}</a>'
        for _, title, _, href, _, _ in MODULES
    )
    return f"""
<header class="topnav">
  <a class="brand-mini" href="{prefix}"><span class="mark"></span>{esc(SITE_NAME)}</a>
  <nav class="navlinks" aria-label="模块导航">{links}</nav>
</header>"""


def orig_html(main: str, original: str) -> str:
    if not original or original == main:
        return ""
    return f'<p class="orig">原文：{esc(original)}</p>'


def card_deal(item, prefix=""):
    deadline = item.get("deadline")
    deadline_html = f'<span class="dl-tag">截止 {esc(deadline)}</span>' if deadline else ""
    how = item.get("how") or ""
    how_html = f'<div class="how"><strong>怎么领：</strong>{esc(how)}</div>' if how else ""
    url = item.get("url") or ""
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    cat = item.get("category") or ""
    source = item.get("source") or "未知"
    slug_path = prefix + (item.get("_path") or f"item/{item_slug(item)}.html")
    author = item.get("author") or ""
    posted = item.get("posted_at") or ""
    author_html = f'<div class="meta author">@{esc(author)} · {esc(posted)}</div>' if (author or posted) else ""
    blob = " ".join([title, summary, how, author, url, cat, source])
    return f"""
<article class="card" data-text="{esc(blob)}">
  <div class="badgerow"><span class="badge">{esc(cat)}</span><span class="src-tag">来源 {esc(source)}</span>{deadline_html}</div>
  <h3 class="title"><a href="{esc(slug_path)}">{esc(title)}</a></h3>
  {orig_html(title, item.get("original_title") or "")}
  <p class="summary">{esc(summary)}</p>
  {orig_html(summary, item.get("original_summary") or "")}
  {how_html}{author_html}
  <div class="linkrow"><a href="{esc(slug_path)}">详情与领取方法</a> · <a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">原帖</a></div>
</article>"""


def card_repo(item):
    url = item.get("url") or ""
    title = item.get("title") or item.get("name") or ""
    summary = item.get("summary") or ""
    name = item.get("name") or ""
    return f"""
<article class="card" data-text="{esc(title + ' ' + summary + ' ' + name)}">
  <div class="badgerow"><span class="badge">GitHub 新热门</span><span class="src-tag">来源 GitHub</span></div>
  <h3 class="title">{esc(title)}</h3>
  {orig_html(title, item.get("original_title") or name)}
  <p class="summary">{esc(summary)}</p>
  {orig_html(summary, item.get("original_summary") or "")}
  <div class="meta">⭐ {esc(item.get("stars") or 0)} · {esc(item.get("language") or "")} · {esc(item.get("created_at") or "")}</div>
  <div class="meta author">仓库：{esc(name)}</div>
  <div class="linkrow"><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


def card_hot(item):
    url = item.get("url") or ""
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    return f"""
<article class="card" data-text="{esc(title + ' ' + summary)}">
  <div class="badgerow"><span class="badge">最近热议</span><span class="src-tag">来源 {esc(item.get("source") or "")}</span></div>
  <h3 class="title">{esc(title)}</h3>
  {orig_html(title, item.get("original_title") or "")}
  <p class="summary">{esc(summary)}</p>
  {orig_html(summary, item.get("original_summary") or "")}
  <div class="meta">热度：{esc(item.get("heat") or "")}</div>
  <div class="linkrow"><a class="fulllink" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(url)}</a></div>
</article>"""


SEARCH_JS = r"""
(function(){
  const q=document.getElementById('q'); if(!q) return;
  const cards=[...document.querySelectorAll('.card')];
  const empty=document.getElementById('empty');
  q.addEventListener('input',()=>{
    const t=(q.value||'').trim().toLowerCase();
    let n=0;
    cards.forEach(c=>{
      const ok=!t||(c.getAttribute('data-text')||'').toLowerCase().includes(t);
      c.classList.toggle('hidden',!ok); if(ok) n++;
    });
    if(empty) empty.classList.toggle('hidden', n>0 || !cards.length);
  });
})();
"""


def write_sitemaps(urls):
    now = datetime.now(TZ).strftime("%Y-%m-%d")
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
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
    (SITE / "sitemap_index.xml").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>{CANONICAL}sitemap.xml</loc><lastmod>{now}</lastmod></sitemap>
  <sitemap><loc>{CANONICAL}sitemap.txt</loc><lastmod>{now}</lastmod></sitemap>
</sitemapindex>
""",
        encoding="utf-8",
    )
    (SITE / "robots.txt").write_text(
        f"""User-agent: *
Allow: /
User-agent: Baiduspider
Allow: /
User-agent: Baiduspider-render
Allow: /
Sitemap: {CANONICAL}sitemap_index.xml
Sitemap: {CANONICAL}sitemap.xml
Sitemap: {CANONICAL}sitemap.txt
""",
        encoding="utf-8",
    )


def related_items(item, all_items, n=6):
    cat = item.get("category")
    same = [x for x in all_items if x is not item and x.get("category") == cat]
    others = [x for x in all_items if x is not item and x.get("category") != cat]
    out = same[:n]
    if len(out) < n:
        out += others[: n - len(out)]
    return out


def write_item_pages(all_items, date):
    ITEMS.mkdir(parents=True, exist_ok=True)
    paths = []
    for it in all_items:
        slug = it["_slug"]
        title_zh = it.get("title") or "资源详情"
        page_title = f"{title_zh} - 免费领取方法 | {SITE_NAME}"
        desc = (it.get("summary") or title_zh)[:150]
        canonical = f"{CANONICAL}item/{slug}.html"
        cat = it.get("category") or "其他科技"
        cat_slug = CAT_SLUG.get(cat, "qita-keji")
        pub = it.get("posted_at") or date
        rel = related_items(it, all_items)
        rel_html = "".join(f'<a href="{esc(r["_slug"])}.html">{esc(r.get("title") or "")}</a><br/>' for r in rel)
        how = it.get("how") or "打开来源链接，按页面说明领取或试用；参与前请自行核实。"
        ld = [
            {"@context": "https://schema.org", "@type": "Article", "headline": title_zh, "description": desc,
             "datePublished": str(pub), "dateModified": date, "mainEntityOfPage": canonical,
             "author": {"@type": "Organization", "name": SITE_NAME}},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "首页", "item": CANONICAL},
                {"@type": "ListItem", "position": 2, "name": cat, "item": f"{CANONICAL}c/{cat_slug}.html"},
                {"@type": "ListItem", "position": 3, "name": title_zh, "item": canonical},
            ]},
        ]
        page = f"""{head_block(page_title, desc, canonical, title_zh, pubdate=str(pub), extra_ld=ld)}
<body>
<div class="wrap">
  {topnav("../")}
  <div class="crumbs"><a href="../">首页</a> › <a href="../c/{esc(cat_slug)}.html">{esc(cat)}</a> › {esc(title_zh)}</div>
  <header class="hero">
    <div class="eyebrow"><i></i> DETAIL</div>
    <h1>{esc(title_zh)}</h1>
    <p class="lead">{esc(cat)} · 来源 {esc(it.get("source") or "公开网页")}</p>
  </header>
  <section class="panel-box intro">
    <h2>资源说明</h2>
    <p>{esc(it.get("summary") or title_zh)}</p>
    {orig_html(it.get("summary") or "", it.get("original_summary") or "")}
    <div class="how"><strong>免费领取方法：</strong>{esc(how)}</div>
    <p style="margin-top:14px"><a class="btn" href="{esc(it.get("url") or "#")}" target="_blank" rel="noopener noreferrer">打开原帖 / 官网</a>
    <a class="btn" href="../c/{esc(cat_slug)}.html">同分类更多</a></p>
  </section>
  <section class="panel-box"><h2>相关推荐</h2>{rel_html or "暂无"}</section>
  <footer>{esc(SITE_NAME)}</footer>
</div>
</body></html>"""
        (ITEMS / f"{slug}.html").write_text(page, encoding="utf-8")
        paths.append(f"item/{slug}.html")
    return paths


def write_category_pages(all_items, date, ym):
    CATS.mkdir(parents=True, exist_ok=True)
    paths = []
    for cat in CATEGORIES:
        slug = CAT_SLUG[cat]
        cat_items = [it for it in all_items if it.get("category") == cat]
        page_title = f"{cat} | {SITE_NAME} · {ym}"
        intro = CAT_INTRO[cat]
        canonical = f"{CANONICAL}c/{slug}.html"
        cards = "\n".join(card_deal(it, prefix="../") for it in cat_items) or '<div class="empty">本分类暂无条目</div>'
        ld = [
            {"@context": "https://schema.org", "@type": "CollectionPage", "name": page_title, "url": canonical, "description": intro},
            {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": f"{CANONICAL}{it['_path']}", "name": it.get("title") or ""}
                for i, it in enumerate(cat_items[:50])
            ]},
        ]
        page = f"""{head_block(page_title, intro, canonical, extra_ld=ld)}
<body>
<div class="wrap">
  {topnav("../")}
  <div class="crumbs"><a href="../">首页</a> › {esc(cat)}</div>
  <header class="hero">
    <div class="eyebrow"><i></i> MODULE</div>
    <h1>{esc(cat)}</h1>
    <p class="lead">{esc(intro)}</p>
    <div class="stats"><div class="pill">条目 <b>{len(cat_items)}</b></div><div class="pill">更新 <b>{esc(date)}</b></div></div>
  </header>
  <div class="toolbar"><input id="q" type="search" placeholder="在本模块内搜索…" autocomplete="off" /></div>
  <div class="grid">{cards}</div>
  <div id="empty" class="empty hidden">没有匹配条目</div>
  <footer>{esc(SITE_NAME)} · {esc(cat)}</footer>
</div>
<script>{SEARCH_JS}</script>
</body></html>"""
        (CATS / f"{slug}.html").write_text(page, encoding="utf-8")
        paths.append(f"c/{slug}.html")
    return paths


def write_module_special(repos, topics, date, ym):
    MODS.mkdir(parents=True, exist_ok=True)
    paths = []
    # github
    cards = "\n".join(card_repo(r) for r in repos) or '<div class="empty">暂无</div>'
    page = f"""{head_block(f"GitHub 新热门 | {SITE_NAME} · {ym}", f"{SITE_NAME} GitHub热门项目与AI开源项目推荐", f"{CANONICAL}m/github-hot.html")}
<body>
<div class="wrap">
  {topnav("../")}
  <div class="crumbs"><a href="../">首页</a> › GitHub 新热门</div>
  <header class="hero">
    <div class="eyebrow"><i></i> GITHUB</div>
    <h1>GitHub 新热门</h1>
    <p class="lead">近 7–14 天创建的 AI / 大模型 / Agent 开源项目，按星标整理，中文说明 + 原文对照。</p>
    <div class="stats"><div class="pill">项目 <b>{len(repos)}</b></div><div class="pill">更新 <b>{esc(date)}</b></div></div>
  </header>
  <div class="toolbar"><input id="q" type="search" placeholder="搜索仓库 / 简介…" autocomplete="off" /></div>
  <div class="grid">{cards}</div>
  <div id="empty" class="empty hidden">没有匹配条目</div>
  <footer>{esc(SITE_NAME)}</footer>
</div>
<script>{SEARCH_JS}</script>
</body></html>"""
    (MODS / "github-hot.html").write_text(page, encoding="utf-8")
    paths.append("m/github-hot.html")

    cards = "\n".join(card_hot(t) for t in topics) or '<div class="empty">暂无</div>'
    page = f"""{head_block(f"最近热议 / 最新AI新闻 | {SITE_NAME} · {ym}", f"{SITE_NAME}最新AI新闻与社区热议", f"{CANONICAL}m/hot-topics.html")}
<body>
<div class="wrap">
  {topnav("../")}
  <div class="crumbs"><a href="../">首页</a> › 最近热议</div>
  <header class="hero">
    <div class="eyebrow"><i></i> PULSE</div>
    <h1>最近热议</h1>
    <p class="lead">Hacker News / V2EX / X 等渠道的 AI 与科技热议，标题与摘要已尽量译为中文。</p>
    <div class="stats"><div class="pill">话题 <b>{len(topics)}</b></div><div class="pill">更新 <b>{esc(date)}</b></div></div>
  </header>
  <div class="toolbar"><input id="q" type="search" placeholder="搜索热议…" autocomplete="off" /></div>
  <div class="grid">{cards}</div>
  <div id="empty" class="empty hidden">没有匹配条目</div>
  <footer>{esc(SITE_NAME)}</footer>
</div>
<script>{SEARCH_JS}</script>
</body></html>"""
    (MODS / "hot-topics.html").write_text(page, encoding="utf-8")
    paths.append("m/hot-topics.html")
    return paths


def write_archive_page(day, items, all_dates):
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    ym = ym_label(day)
    title = f"{SITE_NAME} · {day} 存档 · {ym}"
    desc = f"{SITE_NAME} {day} 日归档"
    canonical = f"{CANONICAL}archives/{day}.html"
    sections = []
    for c in CATEGORIES:
        cat_items = [it for it in items if it.get("category") == c]
        if not cat_items:
            continue
        cards = "\n".join(card_deal(it, prefix="../") for it in cat_items)
        sections.append(f'<section class="section"><h2>{esc(c)} <span>({len(cat_items)})</span></h2><div class="grid">{cards}</div></section>')
    arch = "".join(f'<a class="arch {"current" if d==day else ""}" href="{esc(d)}.html">{esc(d)}</a>' for d in all_dates[:60])
    page = f"""{head_block(title, desc, canonical)}
<body>
<div class="wrap">
  {topnav("../")}
  <div class="crumbs"><a href="../">首页</a> › 日归档 › {esc(day)}</div>
  <header class="hero"><div class="eyebrow"><i></i> ARCHIVE</div><h1>{esc(day)}</h1>
  <p class="lead">{esc(ym)} · {len(items)} 条</p></header>
  {''.join(sections) or '<div class="empty">暂无</div>'}
  <div class="panel-box"><h2>更多日期</h2>{arch}</div>
  <footer>{esc(SITE_NAME)}</footer>
</div></body></html>"""
    (ARCHIVES / f"{day}.html").write_text(page, encoding="utf-8")


def write_404():
    (SITE / "404.html").write_text(
        f"""{head_block(f"页面未找到 | {SITE_NAME}", META_DESC, CANONICAL + "404.html")}
<body><div class="wrap">{topnav("./")}<header class="hero"><h1>404</h1>
<p class="lead">页面不存在，返回首页继续浏览大模型免费资源。</p>
<p><a class="btn" href="./">返回首页</a></p></header></div></body></html>""",
        encoding="utf-8",
    )


def build():
    global CFG, SITE_NAME, CANONICAL, META_DESC
    CFG = load_cfg()
    SITE_NAME = CFG["site_name"]
    CANONICAL = CFG["canonical"]
    META_DESC = (
        f"{SITE_NAME}汇总大模型免费API、免费GPT、Claude免费、DeepSeek免费额度、"
        f"AI工具免费、免费GPU与GitHub热门项目，每日更新。"
    )

    items, date, updated = collect_deal_items()
    repos, repos_updated = load_section("github_hot.json")
    topics, topics_updated = load_section("hot_topics.json")
    dates = list_archive_dates()
    ym = ym_label(date)

    item_paths = write_item_pages(items, date)
    cat_paths = write_category_pages(items, date, ym)
    mod_paths = write_module_special(repos, topics, date, ym)
    for d in dates:
        write_archive_page(d, items_for_date(d), dates)
    write_404()

    # landing tiles
    tiles = []
    for mid, title, desc, href, kind, cat in MODULES:
        if kind == "cat":
            subset = [it for it in items if it.get("category") == cat]
        elif kind == "github":
            subset = repos
        else:
            subset = topics
        top3 = subset[:3]
        lis = "".join(f"<li>{esc((it.get('title') or it.get('name') or '')[:60])}</li>" for it in top3) or "<li>暂无条目</li>"
        tiles.append(
            f"""<a class="module-tile" href="{esc(href)}">
  <h2>{esc(title)} <em>{len(subset)}</em></h2>
  <p class="desc">{esc(desc)}</p>
  <ol>{lis}</ol>
  <div class="go">进入模块 →</div>
</a>"""
        )

    arch_links = "".join(
        f'<a class="arch {"current" if d==date else ""}" href="archives/{esc(d)}.html">{esc(d)}</a>' for d in dates[:30]
    )
    now_label = datetime.now(TZ).strftime("%Y-%m-%d %H:%M Asia/Shanghai")
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
    page_title = f"{SITE_NAME} · {ym} · 大模型免费API / 免费GPT / Claude免费"
    page = f"""{head_block(page_title, META_DESC, CANONICAL, SITE_NAME + " · " + ym, extra_ld=[website_ld])}
<body>
<div class="wrap">
  {topnav("./")}
  <header class="hero">
    <div class="eyebrow"><i></i> LIVE FREE AI RESOURCES</div>
    <h1>{esc(SITE_NAME)}</h1>
    <p class="lead">帮你一站看清大模型免费API、免费GPT、Claude免费额度、DeepSeek免费额度、AI工具免费试用、免费GPU，以及值得关注的 GitHub 热门项目与最新AI新闻。每个模块独立成页，信息每日自动更新；参与前请以官网规则为准。</p>
    <div class="stats">
      <div class="pill">更新日期 <b>{esc(date)}</b></div>
      <div class="pill">免费资源 <b>{len(items)}</b></div>
      <div class="pill">GitHub热门 <b>{len(repos)}</b></div>
      <div class="pill">热议 <b>{len(topics)}</b></div>
      <div class="pill">更新 <b>{esc(updated)}</b></div>
      <div class="pill">生成 <b>{esc(now_label)}</b></div>
    </div>
  </header>

  <section class="section">
    <h2>选择模块</h2>
    <p class="sec-desc">点击进入对应专题页，浏览完整列表与中文说明。</p>
    <div class="module-grid">{''.join(tiles)}</div>
  </section>

  <div class="panel-box" id="archives"><h2>每日存档</h2>{arch_links or "暂无"}</div>
  <div class="panel-box"><h2>免责声明</h2>
    <p class="sec-desc" style="margin:0">信息来自公开网页与社区，自动整理，可能过期或不准确。参与前请自行核实官网规则，谨防诈骗。</p>
  </div>
  <footer>{esc(SITE_NAME)} · {esc(CANONICAL)}</footer>
</div>
</body></html>"""
    (SITE / "index.html").write_text(page, encoding="utf-8")

    url_entries = [("", date, "hourly", "1.0"), ("404.html", date, "yearly", "0.1")]
    for pth in cat_paths + mod_paths:
        url_entries.append((pth, date, "daily", "0.9"))
    for pth in item_paths:
        url_entries.append((pth, date, "weekly", "0.8"))
    for d in dates:
        url_entries.append((f"archives/{d}.html", d, "weekly", "0.7"))
    write_sitemaps(url_entries)
    print(
        f"wrote landing modules={len(MODULES)} deals={len(items)} repos={len(repos)} "
        f"topics={len(topics)} items={len(item_paths)} canonical={CANONICAL}"
    )


if __name__ == "__main__":
    build()
