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


MODELS_OK = 0
MODELS_FAIL = 0


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def models_zh(prompt: str, max_tokens: int = 1200) -> str | None:
    """Call GitHub Models chat completions. Returns text or None."""
    global MODELS_OK, MODELS_FAIL
    tok = github_token()
    if not tok:
        MODELS_FAIL += 1
        print("[warn] GitHub Models skipped: no GITHUB_TOKEN")
        return None
    url = "https://models.github.ai/inference/chat/completions"
    payload = {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是中文科技编辑。只根据用户给出的原文翻译/改写为简洁中文，"
                    "不要编造原文没有的优惠、数字、链接或功能。只输出用户要求的格式。"
                ),
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
            timeout=90,
        )
        if not data:
            MODELS_FAIL += 1
            print("[warn] GitHub Models empty body")
            return None
        content = (((data.get("choices") or [{}])[0]).get("message") or {}).get("content")
        if content and isinstance(content, str) and content.strip():
            MODELS_OK += 1
            return content.strip()
        MODELS_FAIL += 1
        print("[warn] GitHub Models missing content")
    except Exception as e:
        MODELS_FAIL += 1
        print(f"[warn] GitHub Models failed: {type(e).__name__}: {e}")
    return None


def _extract_json_array(text: str) -> list | None:
    if not text:
        return None
    text = text.strip()
    # strip fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict) and isinstance(obj.get("items"), list):
            return obj["items"]
    except Exception:
        pass
    m = re.search(r"\[[\s\S]*\]", text)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, list):
                return obj
        except Exception:
            return None
    return None


def batch_translate(rows: list[dict], kind: str, batch_size: int = 12) -> dict[str, dict]:
    """Translate many items via one Models call per batch.

    rows: [{id, title, text, keep_title?}]
    returns: {id: {title, summary, category?, how?, original_title?}}
    """
    out: dict[str, dict] = {}
    if not rows:
        return out

    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        payload_rows = []
        for r in chunk:
            payload_rows.append(
                {
                    "id": r["id"],
                    "title": (r.get("title") or "")[:180],
                    "text": (r.get("text") or r.get("title") or "")[:500],
                }
            )
        if kind == "deal":
            prompt = (
                "将下列科技/羊毛条目翻译整理为中文。不要编造。\n"
                "对每个元素输出 JSON 数组，元素字段：\n"
                'id, category(只能是: '
                + " / ".join(CATEGORIES)
                + "), title(中文短标题), summary(1-2句中文说明能领到什么/怎么领), how(一句中文领取步骤)\n"
                "只输出 JSON 数组。\n输入="
                + json.dumps(payload_rows, ensure_ascii=False)
            )
        elif kind == "repo":
            prompt = (
                "将下列 GitHub 仓库说明翻译成中文。仓库全名保持英文不要改。\n"
                "输出 JSON 数组，字段：id, title(可用仓库名或中文短名), summary(一句中文简介，不要编造)\n"
                "只输出 JSON 数组。\n输入="
                + json.dumps(payload_rows, ensure_ascii=False)
            )
        else:  # hot
            prompt = (
                "将下列科技热议标题/摘要翻译成中文。不要编造。\n"
                "输出 JSON 数组，字段：id, title(中文短标题), summary(一句中文)\n"
                "只输出 JSON 数组。\n输入="
                + json.dumps(payload_rows, ensure_ascii=False)
            )
        ai = models_zh(prompt, max_tokens=1800)
        parsed = _extract_json_array(ai or "")
        if not parsed:
            print(f"[warn] batch_translate({kind}) fallback keywords for {len(chunk)} items")
            for r in chunk:
                if kind == "deal":
                    cat, title, summary = keyword_classify(f"{r.get('title')} {r.get('text')}")
                    out[r["id"]] = {
                        "category": cat,
                        "title": title,
                        "summary": summary,
                        "how": "打开来源链接按页面说明领取/试用；参与前自行核实。",
                        "translated_by": "keywords",
                    }
                else:
                    title = re.sub(r"\s+", " ", (r.get("title") or "").strip())[:100] or "未命名"
                    summary = re.sub(r"\s+", " ", (r.get("text") or title).strip())[:220]
                    if not has_cjk(title):
                        title = f"【{kind}】{title}"
                    if not has_cjk(summary):
                        summary = f"原文：{summary}"
                    out[r["id"]] = {
                        "title": title,
                        "summary": summary,
                        "translated_by": "keywords",
                    }
            continue

        by_id = {str(x.get("id")): x for x in parsed if isinstance(x, dict) and x.get("id") is not None}
        for r in chunk:
            x = by_id.get(str(r["id"]))
            if not x:
                # fallback single
                cat, title, summary = keyword_classify(f"{r.get('title')} {r.get('text')}")
                out[r["id"]] = {
                    "category": cat if kind == "deal" else None,
                    "title": title if kind != "repo" else (r.get("title") or title),
                    "summary": summary,
                    "how": "打开来源链接按页面说明领取/试用；参与前自行核实。" if kind == "deal" else None,
                    "translated_by": "keywords",
                }
                continue
            title = str(x.get("title") or r.get("title") or "").strip()[:120]
            summary = str(x.get("summary") or "").strip()[:400]
            if kind == "repo":
                # keep repo full name as name; title can be chinese short or name
                if not summary:
                    summary = f"GitHub 仓库：{r.get('title')}"
                out[r["id"]] = {
                    "title": title or r.get("title"),
                    "summary": summary,
                    "translated_by": "models",
                }
            elif kind == "deal":
                cat = str(x.get("category") or "").strip()
                if cat not in CATEGORIES:
                    cat, _, _ = keyword_classify(f"{r.get('title')} {r.get('text')}")
                how = str(x.get("how") or "打开来源链接按页面说明领取/试用；参与前自行核实。").strip()[:200]
                if not has_cjk(title):
                    title = f"【羊毛】{title}"
                if not has_cjk(summary):
                    summary = f"摘要：{summary}"
                out[r["id"]] = {
                    "category": cat,
                    "title": title,
                    "summary": summary,
                    "how": how,
                    "translated_by": "models",
                }
            else:
                if not has_cjk(title):
                    title = f"【热议】{title}"
                if not has_cjk(summary):
                    summary = f"摘要：{summary}"
                out[r["id"]] = {
                    "title": title,
                    "summary": summary,
                    "translated_by": "models",
                }
        time.sleep(0.8)
    return out


def enrich_deal(raw_title: str, raw_text: str, source: str) -> tuple[str, str, str, str]:
    """Single-item fallback (prefer batch_translate)."""
    blob = f"{raw_title}\n{raw_text}"
    cat, title, summary = keyword_classify(blob)
    how = "打开来源链接按页面说明领取/试用；参与前自行核实。"
    return cat, title, summary, how


def enrich_one_liner(raw_title: str, raw_text: str, kind: str) -> tuple[str, str]:
    title = re.sub(r"\s+", " ", (raw_title or "").strip())[:100] or "未命名"
    summary = re.sub(r"\s+", " ", (raw_text or raw_title or "").strip())[:220]
    if not has_cjk(title):
        title = f"【{kind}】{title}"
    if not has_cjk(summary):
        summary = f"{kind}内容：{summary}"
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
        f"topic:ai created:>{since7}",
        f"topic:agents created:>{since14}",
        f"topic:devtools created:>{since14}",
        f"LLM OR \"AI agent\" in:name,description created:>{since7}",
    ]
    seen = set()
    raw = []
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
            raw.append(
                {
                    "id": slug_id("ghot", full),
                    "source": "GitHub",
                    "name": full,
                    "title": full,
                    "summary": desc,
                    "summary_en": desc,
                    "stars": r.get("stargazers_count") or 0,
                    "language": r.get("language") or "未知",
                    "created_at": created.strftime("%Y-%m-%d Asia/Shanghai"),
                    "url": r.get("html_url"),
                    "_raw_title": full,
                    "_raw_text": desc or full,
                }
            )
    raw.sort(key=lambda x: x.get("stars", 0), reverse=True)
    raw = raw[:30]
    tr = batch_translate(
        [{"id": r["id"], "title": r["_raw_title"], "text": r["_raw_text"]} for r in raw],
        kind="repo",
        batch_size=10,
    )
    out = []
    for r in raw:
        t = tr.get(r["id"]) or {}
        r["title"] = t.get("title") or r["name"]
        r["summary"] = t.get("summary") or (r.get("summary_en") and f"简介：{r['summary_en']}") or f"GitHub 仓库 {r['name']}"
        r["translated_by"] = t.get("translated_by") or "keywords"
        r.pop("_raw_title", None)
        r.pop("_raw_text", None)
        out.append(r)
    return out


def fetch_hot_topics(x_items: list[dict] | None = None) -> list[dict]:
    raw = []
    st, data = safe_get("https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode({"tags": "front_page", "hitsPerPage": 20}))
    if data:
        for h in data.get("hits") or []:
            title = h.get("title") or ""
            if looks_blocked(title) or not looks_ai_tech(title):
                continue
            url_s = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            raw.append(
                {
                    "id": slug_id("hnhot", str(h.get("objectID"))),
                    "source": "Hacker News",
                    "title": title,
                    "summary": title,
                    "heat": f"点数 {h.get('points') or 0} · 评论 {h.get('num_comments') or 0}",
                    "points": h.get("points") or 0,
                    "url": url_s,
                    "_raw_title": title,
                    "_raw_text": title,
                    "_need_tr": True,
                }
            )
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
            # V2EX often already Chinese
            already = has_cjk(title)
            raw.append(
                {
                    "id": slug_id("v2hot", str(t.get("id"))),
                    "source": "V2EX",
                    "title": title,
                    "summary": content or title,
                    "heat": f"回复 {t.get('replies') or 0}",
                    "points": t.get("replies") or 0,
                    "url": t.get("url") or f"https://www.v2ex.com/t/{t.get('id')}",
                    "_raw_title": title,
                    "_raw_text": content or title,
                    "_need_tr": not already,
                }
            )
    for it in (x_items or [])[:12]:
        eng = it.get("engagement") or {}
        heat_n = int(eng.get("likes") or 0) + int(eng.get("bookmarks") or 0) * 2 + int(eng.get("impressions") or 0) // 500
        title = it.get("title") or ""
        summary = it.get("summary") or ""
        raw.append(
            {
                "id": slug_id("xhot", it.get("id") or it.get("url") or ""),
                "source": "X",
                "title": title,
                "summary": summary,
                "heat": f"赞 {eng.get('likes', 0)} · 收藏 {eng.get('bookmarks', 0)}",
                "points": heat_n,
                "url": it.get("url"),
                "_need_tr": not (has_cjk(title) and has_cjk(summary)),
                "_raw_title": title,
                "_raw_text": summary or title,
            }
        )

    need = [r for r in raw if r.get("_need_tr")]
    tr = batch_translate(
        [{"id": r["id"], "title": r.get("_raw_title") or "", "text": r.get("_raw_text") or ""} for r in need],
        kind="hot",
        batch_size=12,
    )
    out = []
    seen = set()
    for r in raw:
        u = r.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        if r.get("_need_tr"):
            t = tr.get(r["id"]) or {}
            r["title"] = t.get("title") or r["title"]
            r["summary"] = t.get("summary") or r["summary"]
            r["translated_by"] = t.get("translated_by") or "keywords"
        else:
            r["translated_by"] = "native-zh"
        r.pop("_raw_title", None)
        r.pop("_raw_text", None)
        r.pop("_need_tr", None)
        out.append(r)
    out.sort(key=lambda x: x.get("points") or 0, reverse=True)
    return out[:40]


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


def load_prev_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[warn] cannot read previous {path}: {e}")
    return None


def finalize_deals(raw_items: list[dict]) -> list[dict]:
    seen = set()
    uniq = []
    for it in raw_items:
        url = it.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        uniq.append(it)
        if len(uniq) >= 40:
            break
    tr = batch_translate(
        [
            {
                "id": it["id"],
                "title": it.get("title") or "",
                "text": it.get("_raw") or it.get("title") or "",
            }
            for it in uniq
        ],
        kind="deal",
        batch_size=10,
    )
    out = []
    for it in uniq:
        t = tr.get(it["id"]) or {}
        if t:
            it["category"] = t.get("category") or it.get("category") or "其他科技"
            it["title"] = t.get("title") or it.get("title")
            it["summary"] = t.get("summary") or it.get("summary")
            it["how"] = t.get("how") or "打开来源链接按页面说明领取/试用；参与前自行核实。"
            it["translated_by"] = t.get("translated_by") or "keywords"
        else:
            cat, title, summary, how = enrich_deal(it.get("title") or "", it.get("_raw") or it.get("title") or "", it.get("source") or "")
            it["category"] = cat
            it["title"] = title
            it["summary"] = summary
            it["how"] = how
            it["translated_by"] = "keywords"
        it.pop("_raw", None)
        out.append(it)
    return out


def write_json_safe(path: Path, payload: dict, keep_if_empty_key: str = "items") -> None:
    """Self-healing: never overwrite good previous file with empty items."""
    items = payload.get(keep_if_empty_key)
    prev = load_prev_json(path)
    if (not items) and prev and prev.get(keep_if_empty_key):
        print(f"[heal] keep previous {path.name}: new empty, old has {len(prev.get(keep_if_empty_key) or [])}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[write] {path} items={len(items or [])}")


def main():
    global MODELS_OK, MODELS_FAIL
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
            print(f"[fetch] {name} ERROR {type(e).__name__}: {e} (keeping other sources)")

    day = today_str()
    deal_path = DATA_AUTO / f"{day}.json"
    try:
        deals = finalize_deals(raw)
    except Exception as e:
        print(f"[heal] finalize_deals failed: {e}; keeping previous deals")
        deals = []
    write_json_safe(
        deal_path,
        {
            "date": day,
            "updated_at": now_sh().isoformat(timespec="minutes"),
            "updated_at_label": now_sh().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
            "source": "auto-fetch public APIs",
            "items": deals,
            "models_ok": MODELS_OK,
            "models_fail": MODELS_FAIL,
        },
    )

    x_items = load_latest_x_items()
    hot_path = DATA_AUTO / "github_hot.json"
    try:
        hot_repos = fetch_github_hot()
    except Exception as e:
        print(f"[heal] github_hot failed: {e}")
        hot_repos = []
    write_json_safe(
        hot_path,
        {
            "updated_at_label": now_sh().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
            "items": hot_repos,
            "models_ok": MODELS_OK,
            "models_fail": MODELS_FAIL,
        },
    )

    topics_path = DATA_AUTO / "hot_topics.json"
    try:
        hot_topics = fetch_hot_topics(x_items)
    except Exception as e:
        print(f"[heal] hot_topics failed: {e}")
        hot_topics = []
    write_json_safe(
        topics_path,
        {
            "updated_at_label": now_sh().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
            "items": hot_topics,
            "models_ok": MODELS_OK,
            "models_fail": MODELS_FAIL,
        },
    )

    by_src = {}
    # reload deals file in case healed
    cur = load_prev_json(deal_path) or {"items": deals}
    for it in cur.get("items") or []:
        by_src[it.get("source")] = by_src.get(it.get("source"), 0) + 1
    print("[summary] deals by source", by_src)
    print(f"[summary] models_ok={MODELS_OK} models_fail={MODELS_FAIL}")


if __name__ == "__main__":
    main()
