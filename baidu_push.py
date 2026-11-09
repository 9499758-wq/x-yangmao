#!/usr/bin/env python3
"""Push URLs to Baidu 普通收录 API when BAIDU_PUSH_TOKEN is set; otherwise no-op."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "seo_config.json"
STATE = ROOT / "data" / "auto" / "baidu_pushed.json"
SITEMAP_TXT = ROOT / "sitemap.txt"


def main() -> int:
    token = (os.environ.get("BAIDU_PUSH_TOKEN") or "").strip()
    if not token:
        print("[baidu_push] BAIDU_PUSH_TOKEN not set — skip silently")
        return 0
    cfg = json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
    site = (cfg.get("baidu_push_site") or cfg.get("canonical") or "").rstrip("/")
    if not site.startswith("http"):
        print("[baidu_push] invalid site — skip")
        return 0
    if not SITEMAP_TXT.exists():
        print("[baidu_push] no sitemap.txt — skip")
        return 0
    urls = [u.strip() for u in SITEMAP_TXT.read_text(encoding="utf-8").splitlines() if u.strip()]
    prev: set[str] = set()
    if STATE.exists():
        try:
            prev = set(json.loads(STATE.read_text(encoding="utf-8")).get("urls") or [])
        except Exception:
            prev = set()
    fresh = [u for u in urls if u not in prev][:20] or urls[:5]
    api = "http://data.zz.baidu.com/urls?site={}&token={}".format(
        urllib.parse.quote(site, safe=":/"), token
    )
    req = urllib.request.Request(
        api, data="\n".join(fresh).encode("utf-8"), method="POST",
        headers={"Content-Type": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[baidu_push] ok n={len(fresh)} resp={resp.read().decode('utf-8','replace')[:300]}")
    except Exception as e:
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
        print(f"[baidu_push] failed: {type(e).__name__}: {e} {detail}")
        return 0
    prev.update(fresh)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps({"urls": sorted(prev)[-5000:]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
