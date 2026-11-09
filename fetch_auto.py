#!/usr/bin/env python3
"""Fetch free AI/tech deals + GitHub hot repos + hot discussions from public APIs.
No paid keys. Optional GitHub Models via GITHUB_TOKEN; keyword fallback otherwise.
Writes:
  data/auto/YYYY-MM-DD.json   — freebie/deal items
  data/auto/github_hot.json   — 新热门 repos
  data/auto/hot_topics.json   — 最近热议
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DATA_AUTO = ROOT / "data" / "auto"
TZ = ZoneInfo("Asia/Shanghai")
UTC = timezone.utc
UA = "x-yangmao-bot/1.0 (+https://github.com/9499758-wq/x-yangmao)"
CTX = ssl.create_default_context()

CATEGORIES = [
    "大模型 API 免费额度",
    "AI 产品会员/试用",
    "AI 开发工具与编程助手",
    "云服务/GPU/开发者资源",
    "科技软件/App 限免",
    "其他科技",
]

DEAL_KEYWORDS = [
    "free api", "free credits", "free tier", "free gpu", "free trial",
    "open beta", "no credit card", "free llm", "free tokens", "hobby plan",
    "student free", "免费", "白嫖", "限免", "免费额度", "免费试用", "薅羊毛",
    "api 额度", "free credits", "zero cost",
]
AI_TECH_KEYWORDS = [
    "ai", "llm", "gpt", "claude", "gemini", "deepseek", "qwen", "grok",
    "openai", "model", "agent", "gpu", "cuda", "ml", "machine learning",
    "devtool", "developer", "api", "sdk", "cursor", "copilot", "coding",
    "开源", "大模型", "人工智能", "编程", "开发", "框架", "工具",
]
BLOCK = [
    "airdrop", "crypto giveaway", "send eth", "send sol", "nft mint",
    "credit card offer", "bank bonus", "gambling", "casino", "forex",
    "空投", "信用卡", "银行活动", "返现", "优惠券购物",
]


def now_sh() -> datetime:
    return datetime.now(TZ)


def today_str() -> str:
    return now_sh().strftime("%Y-%m-%d")


def http_json(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None, timeout: int = 35):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
        raw = resp.read()
        if not raw:
            return resp.status, None
        text = raw.decode("utf-8", errors="replace")
        if text.strip() in {"OK", "ok"}:
            return resp.status, None
        return resp.status, json.loads(text)


def safe_get(url: str, **kwargs):
    try:
        return http_json(url, **kwargs)
    except Exception as e:
        print(f"[warn] GET fail {url[:90]} :: {type(e).__name__}: {e}")
        return None, None


def github_token() -> str:
    return (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()


def looks_blocked(text: str) -> bool:
    t = (text or "").lower()
    return any(b.lower() in t for b in BLOCK)


def looks_ai_tech(text: str) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in AI_TECH_KEYWORDS)


def looks_deal(text: str) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in DEAL_KEYWORDS)


def slug_id(prefix: str, url: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", (url or "")[-80:]).strip("-").lower()
    return f"{prefix}-{base[:60]}"


def keyword_classify(text: str) -> tuple[str, str, str]:
    """Return (category, title_zh, summary_zh) via rules."""
    t = text or ""
    low = t.lower()
    if any(k in low for k in ["api", "token", "credits", "neurons", "额度", "llm api"]):
        cat = "大模型 API 免费额度"
    elif any(k in low for k in ["trial", "beta", "pro free", "会员", "试用", "限免会员"]):
        cat = "AI 产品会员/试用"
    elif any(k in low for k in ["cursor", "copilot", "coderabbit", "ide", "编程", "coding assistant", "agent coding"]):
        cat = "AI 开发工具与编程助手"
    elif any(k in low for k in ["gpu", "colab", "kaggle", "vps", "cloud", "compute", "算力", "服务器"]):
        cat = "云服务/GPU/开发者资源"
    elif any(k in low for k in ["app", "限免", "steam", "software", "开源工具"]):
        cat = "科技软件/App 限免"
    else:
        cat = "其他科技"
    # title: first line / first 40 chars
    title = re.split(r"[\n\r]", t.strip())[0]
    title = re.sub(r"\s+", " ", title)[:80] or "未命名科技动态"
    summary = re.sub(r"\s+", " ", t).strip()
    if len(summary) > 280:
        summary = summary[:277] + "…"
    # Prefer Chinese-ish summary label
    if not re.search(r"[\u4e00-\u9fff]", summary):
        summary = f"来源摘要：{summary}"
    if not re.search(r"[\u4e00-\u9fff]", title):
        title = f"【科技】{title}"
    return cat, title, summary


def models_zh(prompt: str) -> str | None:
    tok = github_token()
    if not tok:
        return None
    url = "https://models.github.ai/inference/chat/completions"
    payload = {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.2,
        "max_tokens": 220,
        "messages": [
            {
                "role": "system",
                "content": "你是中文科技编辑。只根据用户给出的原文写简洁中文，不要编造原文没有的优惠/数字/链接。输出纯文本。",
            },
            {"role": "user", "content": prompt},
        ],
    }
    try:
        st, data = http_json(
            url,
            method="POST",
            payload=payload,
            headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
            timeout=50,
        )
        if not data:
            return None
        content = (((data.get("choices") or [{}])[0]).get("message") or {}).get("content")
        if content and isinstance(content, str) and content.strip():
            return content.strip()
    except Exception as e:
        print(f"[warn] GitHub Models failed: {type(e).__name__}: {e}")
    return None


def enrich_deal(raw_title: str, raw_text: str, source: str) -> tuple[str, str, str, str]:
    blob = f"{raw_title}\n{raw_text}"
    cat, title, summary = keyword_classify(blob)
    how = "打开来源链接按页面说明领取/试用；参与前自行核实。"
    ai = models_zh(
        "把下面科技/羊毛信息整理成三行：\n"
        "分类:（只能是：" + " / ".join(CATEGORIES) + "）\n"
        "标题:（中文短标题）\n"
        "摘要:（一两句中文，含能领到什么、怎么领，不要编造）\n\n"
        f"来源平台: {source}\n原文:\n{blob[:1500]}"
    )
    if ai:
        cat_m = re.search(r"分类[:：]\s*(.+)", ai)
        title_m = re.search(r"标题[:：]\s*(.+)", ai)
        sum_m = re.search(r"摘要[:：]\s*(.+)", ai)
        if cat_m and cat_m.group(1).strip() in CATEGORIES:
            cat = cat_m.group(1).strip()
        if title_m and title_m.group(1).strip():
            title = title_m.group(1).strip()[:100]
        if sum_m and sum_m.group(1).strip():
            summary = sum_m.group(1).strip()[:400]
    return cat, title, summary, how


def enrich_one_liner(raw_title: str, raw_text: str, kind: str) -> tuple[str, str]:
    blob = f"{raw_title}\n{raw_text}"
    title = re.sub(r"\s+", " ", (raw_title or "").strip())[:100] or "未命名"
    summary = re.sub(r"\s+", " ", (raw_text or raw_title or "").strip())[:220]
    if not re.search(r"[\u4e00-\u9fff]", title):
        title = f"【{kind}】{title}"
    if not re.search(r"[\u4e00-\u9fff]", summary):
        summary = f"{kind}热度内容：{summary}"
    ai = models_zh(
        f"把下面{kind}内容写成两行中文（不要编造）：\n标题:（短）\n摘要:（一句话）\n\n原文:\n{blob[:1200]}"
    )
    if ai:
        title_m = re.search(r"标题[:：]\s*(.+)", ai)
        sum_m = re.search(r"摘要[:：]\s*(.+)", ai)
        if title_m and title_m.group(1).strip():
            title = title_m.group(1).strip()[:100]
        if sum_m and sum_m.group(1).strip():
            summary = sum_m.group(1).strip()[:280]
    return title, summary


# ---------------- sources: deals ----------------

def fetch_hn_deals() -> list[dict]:
    items = []
    queries = [
        "free API AI",
        "free credits LLM",
        "free GPU",
        "free tier OpenAI OR Claude OR Gemini",
        "\"free trial\" AI developer",
        "Show HN free API",
    ]
    since = (datetime.now(UTC) - timedelta(days=5)).timestamp()
    for q in queries:
        url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(
            {"query": q, "tags": "story", "hitsPerPage": 15, "numericFilters": f"created_at_i>{int(since)}"}
        )
        st, data = safe_get(url)
        time.sleep(0.4)
        if not data:
            continue
        for h in data.get("hits") or []:
            title = h.get("title") or ""
            url_s = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            text = f"{title} {h.get('story_text') or ''}"
            if looks_blocked(text) or not (looks_deal(text) or looks_ai_tech(text)):
                continue
            if not looks_ai_tech(text):
                continue
            created = datetime.fromtimestamp(h.get("created_at_i") or 0, tz=UTC).astimezone(TZ)
            items.append(
                {
                    "id": slug_id("hn", str(h.get("objectID"))),
                    "source": "Hacker News",
                    "category": "",
                    "title": title,
                    "summary": "",
                    "how": "",
                    "deadline": None,
                    "author": h.get("author") or "hn",
                    "url": url_s,
                    "posted_at": created.strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
                    "engagement": {
                        "points": h.get("points") or 0,
                        "comments": h.get("num_comments") or 0,
                    },
                    "_raw": text,
                }
            )
    return items


def fetch_v2ex_deals() -> list[dict]:
    items = []
    endpoints = [
        "https://www.v2ex.com/api/topics/latest.json",
        "https://www.v2ex.com/api/topics/hot.json",
    ]
    for ep in endpoints:
        st, data = safe_get(ep)
        time.sleep(0.8)
        if not isinstance(data, list):
            continue
        for t in data:
            title = t.get("title") or ""
            content = t.get("content") or ""
            text = f"{title}\n{content}"
            if looks_blocked(text):
                continue
            if not (looks_deal(text) and looks_ai_tech(text)):
                # still allow strong deal keywords in tech nodes
                node = ((t.get("node") or {}).get("name") or "")
                if node not in {"create", "programmer", "cloud", "share", "apple", "macos"} or not looks_deal(text):
                    continue
            url_s = t.get("url") or f"https://www.v2ex.com/t/{t.get('id')}"
            created = datetime.fromtimestamp(t.get("created") or 0, tz=UTC).astimezone(TZ)
            items.append(
                {
                    "id": slug_id("v2ex", str(t.get("id"))),
                    "source": "V2EX",
                    "category": "",
                    "title": title,
                    "summary": "",
                    "how": "",
                    "deadline": None,
                    "author": (t.get("member") or {}).get("username") or "v2ex",
                    "url": url_s,
                    "posted_at": created.strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
                    "engagement": {"replies": t.get("replies") or 0},
                    "_raw": text[:2000],
                }
            )
    return items


def fetch_github_deal_repos() -> list[dict]:
    tok = github_token()
    if not tok:
        print("[warn] no GITHUB_TOKEN for repo search")
        return []
    items = []
    queries = [
        "free llm api in:name,description pushed:>" + (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%d"),
        "awesome free api llm in:name,description pushed:>" + (datetime.now(UTC) - timedelta(days=60)).strftime("%Y-%m-%d"),
        "free credits AI API in:readme pushed:>" + (datetime.now(UTC) - timedelta(days=20)).strftime("%Y-%m-%d"),
    ]
    for q in queries:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "updated", "order": "desc", "per_page": 8}
        )
        st, data = safe_get(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
        time.sleep(1.0)
        if not data:
            continue
        for r in data.get("items") or []:
            desc = r.get("description") or ""
            text = f"{r.get('full_name')} {desc}"
            if looks_blocked(text):
                continue
            if not looks_ai_tech(text):
                continue
            created = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")).astimezone(TZ)
            items.append(
                {
                    "id": slug_id("ghdeal", r.get("full_name", "")),
                    "source": "GitHub",
                    "category": "",
                    "title": r.get("full_name") or "",
                    "summary": "",
                    "how": "",
                    "deadline": None,
                    "author": (r.get("owner") or {}).get("login") or "github",
                    "url": r.get("html_url"),
                    "posted_at": created.strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
                    "engagement": {"stars": r.get("stargazers_count") or 0},
                    "_raw": text,
                }
            )
    return items


def fetch_devto_deals() -> list[dict]:
    items = []
    for tag in ["ai", "opensource", "machinelearning"]:
        st, data = safe_get(f"https://dev.to/api/articles?tag={tag}&per_page=10&top=7")
        time.sleep(0.4)
        if not isinstance(data, list):
            continue
        for a in data:
            title = a.get("title") or ""
            text = f"{title} {a.get('description') or ''}"
            if looks_blocked(text) or not looks_deal(text) or not looks_ai_tech(text):
                continue
            items.append(
                {
                    "id": slug_id("devto", str(a.get("id"))),
                    "source": "DEV.to",
                    "category": "",
                    "title": title,
                    "summary": "",
                    "how": "",
                    "deadline": None,
                    "author": ((a.get("user") or {}).get("username")) or "devto",
                    "url": a.get("url"),
                    "posted_at": (a.get("published_at") or "")[:16].replace("T", " ") + " UTC",
                    "engagement": {"reactions": a.get("positive_reactions_count") or 0, "comments": a.get("comments_count") or 0},
                    "_raw": text,
                }
            )
    return items


def fetch_lobsters_deals() -> list[dict]:
    st, data = safe_get("https://lobste.rs/hottest.json")
    if not isinstance(data, list):
        return []
    items = []
    for a in data:
        title = a.get("title") or ""
        tags = " ".join(a.get("tags") or [])
        text = f"{title} {tags}"
        if looks_blocked(text):
            continue
        if not (looks_deal(text) and looks_ai_tech(text)):
            continue
        items.append(
            {
                "id": slug_id("lob", a.get("short_id") or title),
                "source": "Lobsters",
                "category": "",
                "title": title,
                "summary": "",
                "how": "",
                "deadline": None,
                "author": a.get("submitter_user") if isinstance(a.get("submitter_user"), str) else (a.get("submitter_user") or {}).get("username", "lobsters"),
                "url": a.get("url") or a.get("comments_url"),
                "posted_at": (a.get("created_at") or "")[:16].replace("T", " ") + " UTC",
                "engagement": {"score": a.get("score") or 0, "comments": a.get("comment_count") or 0},
                "_raw": text,
            }
        )
    return items


# ---------------- github hot + hot topics ----------------

def fetch_github_hot() -> list[dict]:
    tok = github_token()
    if not tok:
        return []
    since7 = (datetime.now(UTC) - timedelta(days=10)).strftime("%Y-%m-%d")
    since14 = (datetime.now(UTC) - timedelta(days=14)).strftime("%Y-%m-%d")
    queries = [
        f"topic:llm created:>{since14}",
        f"topic:ai created:>{since10 if False else since7}",
        f"topic:agents created:>{since14}",
        f"topic:devtools created:>{since14}",
        f"LLM OR \"AI agent\" in:name,description created:>{since7}",
    ]
    # fix the silly ternary
    queries[1] = f"topic:ai created:>{since7}"
    seen = set()
    out = []
    for q in queries:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "stars", "order": "desc", "per_page": 10}
        )
        st, data = safe_get(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
        time.sleep(1.0)
        if not data:
            continue
        for r in data.get("items") or []:
            full = r.get("full_name")
            if not full or full in seen:
                continue
            desc = r.get("description") or ""
            text = f"{full} {desc}"
            if looks_blocked(text) or not looks_ai_tech(text):
                continue
            seen.add(full)
            created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).astimezone(TZ)
            title, summary = enrich_one_liner(full, desc or full, "GitHub")
            out.append(
                {
                    "id": slug_id("ghot", full),
                    "source": "GitHub",
                    "name": full,
                    "title": title,
                    "summary": summary,
                    "stars": r.get("stargazers_count") or 0,
                    "language": r.get("language") or "未知",
                    "created_at": created.strftime("%Y-%m-%d Asia/Shanghai"),
                    "url": r.get("html_url"),
                }
            )
    out.sort(key=lambda x: x.get("stars", 0), reverse=True)
    return out[:30]


def fetch_hot_topics(x_items: list[dict] | None = None) -> list[dict]:
    out = []
    # HN front page
    st, data = safe_get("https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode({"tags": "front_page", "hitsPerPage": 20}))
    if data:
        for h in data.get("hits") or []:
            title = h.get("title") or ""
            text = title
            if looks_blocked(text) or not looks_ai_tech(text):
                continue
            url_s = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            zh_title, zh_sum = enrich_one_liner(title, title, "HN")
            out.append(
                {
                    "id": slug_id("hnhot", str(h.get("objectID"))),
                    "source": "Hacker News",
                    "title": zh_title,
                    "summary": zh_sum,
                    "heat": f"点数 {h.get('points') or 0} · 评论 {h.get('num_comments') or 0}",
                    "points": h.get("points") or 0,
                    "url": url_s,
                }
            )
    # V2EX hot/latest
    for ep in ["https://www.v2ex.com/api/topics/hot.json", "https://www.v2ex.com/api/topics/latest.json"]:
        st, data = safe_get(ep)
        time.sleep(0.8)
        if not isinstance(data, list):
            continue
        for t in data:
            title = t.get("title") or ""
            content = (t.get("content") or "")[:300]
            text = f"{title}\n{content}"
            if looks_blocked(text) or not looks_ai_tech(text):
                continue
            zh_title, zh_sum = enrich_one_liner(title, content or title, "V2EX")
            out.append(
                {
                    "id": slug_id("v2hot", str(t.get("id"))),
                    "source": "V2EX",
                    "title": zh_title,
                    "summary": zh_sum,
                    "heat": f"回复 {t.get('replies') or 0}",
                    "points": t.get("replies") or 0,
                    "url": t.get("url") or f"https://www.v2ex.com/t/{t.get('id')}",
                }
            )
    # top X items from routine data
    for it in (x_items or [])[:12]:
        eng = it.get("engagement") or {}
        heat_n = int(eng.get("likes") or 0) + int(eng.get("bookmarks") or 0) * 2 + int(eng.get("impressions") or 0) // 500
        out.append(
            {
                "id": slug_id("xhot", it.get("id") or it.get("url") or ""),
                "source": "X",
                "title": it.get("title") or "",
                "summary": it.get("summary") or "",
                "heat": f"赞 {eng.get('likes', 0)} · 收藏 {eng.get('bookmarks', 0)}",
                "points": heat_n,
                "url": it.get("url"),
            }
        )
    # de-dupe by url
    seen = set()
    uniq = []
    for it in out:
        u = it.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(it)
    uniq.sort(key=lambda x: x.get("points") or 0, reverse=True)
    return uniq[:40]


def load_latest_x_items() -> list[dict]:
    data_dir = ROOT / "data"
    files = sorted(data_dir.glob("????-??-??.json"), reverse=True)
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            return d.get("items") or []
        except Exception:
            continue
    return []


def finalize_deals(raw_items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for it in raw_items:
        url = it.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        cat, title, summary, how = enrich_deal(it.get("title") or "", it.get("_raw") or it.get("title") or "", it.get("source") or "")
        it["category"] = cat
        it["title"] = title
        it["summary"] = summary
        it["how"] = how
        it.pop("_raw", None)
        # drop expired-ish if deadline past — none usually
        out.append(it)
        if len(out) >= 40:
            break
    return out


def main():
    DATA_AUTO.mkdir(parents=True, exist_ok=True)
    print("[fetch] start", now_sh().isoformat())
    raw = []
    for name, fn in [
        ("HN", fetch_hn_deals),
        ("V2EX", fetch_v2ex_deals),
        ("GitHub", fetch_github_deal_repos),
        ("DEV.to", fetch_devto_deals),
        ("Lobsters", fetch_lobsters_deals),
    ]:
        try:
            got = fn()
            print(f"[fetch] {name}: {len(got)}")
            raw.extend(got)
        except Exception as e:
            print(f"[fetch] {name} ERROR {type(e).__name__}: {e}")

    deals = finalize_deals(raw)
    day = today_str()
    deal_path = DATA_AUTO / f"{day}.json"
    payload = {
        "date": day,
        "updated_at": now_sh().isoformat(timespec="minutes"),
        "updated_at_label": now_sh().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "source": "auto-fetch public APIs",
        "items": deals,
    }
    deal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[write] {deal_path} items={len(deals)}")

    x_items = load_latest_x_items()
    hot_repos = fetch_github_hot()
    (DATA_AUTO / "github_hot.json").write_text(
        json.dumps({"updated_at_label": now_sh().strftime("%Y-%m-%d %H:%M Asia/Shanghai"), "items": hot_repos}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"[write] github_hot.json items={len(hot_repos)}")

    hot_topics = fetch_hot_topics(x_items)
    (DATA_AUTO / "hot_topics.json").write_text(
        json.dumps({"updated_at_label": now_sh().strftime("%Y-%m-%d %H:%M Asia/Shanghai"), "items": hot_topics}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"[write] hot_topics.json items={len(hot_topics)}")

    by_src = {}
    for it in deals:
        by_src[it.get("source")] = by_src.get(it.get("source"), 0) + 1
    print("[summary] deals by source", by_src)


if __name__ == "__main__":
    main()
