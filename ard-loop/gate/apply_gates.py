# -*- coding: utf-8 -*-
"""apply_gates.py — ARD 하베스터/pull이 g2-loop-harness 게이트를 호출하는 얇은 배선.

원본 SSOT = kgg2512/g2-loop-harness (harness/). 이 폴더의 usefulness_gate.py·claim_verifier.py는
**벤더링 사본**(ARD가 Desktop/ARD에서 독립 실행되므로 sibling 레포 import 불가 → 사본).
drift 시 원본에서 재복사(`cp g2-loop-harness/harness/*.py ard-loop/gate/`).

배선 지점 2곳:
  1. HARVEST→QUEUE 상류: 하베스터가 save_json 직전 should_queue() 호출 → REJECT면 큐에 안 넣음.
  2. PULL/검증: car_pull.py가 후보에 verify_item() 호출 → UNVERIFIED 주장을 CAR에 함께 제시.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from usefulness_gate import score_item, filter_queue  # noqa: E402,F401
from claim_verifier import verify_claims  # noqa: E402

# G2가 이미 커버하는 구체 도구/스킬 = 수확 중복(baseline) 후보.
# ⚠️ 도메인 키워드(agent/mcp/claude)를 넣지 말 것 — 그건 relevance_keywords이지 baseline이 아니다.
DEFAULT_BASELINE_TERMS = [
    "playwright", "firecrawl", "supabase", "vercel", "cloudflare", "stitch",
    "figma", "mem0", "context7", "ponytail", "speckit", "higgsfield",
    "claude-flow", "ruflo", "n8n", "langgraph", "autogen", "crewai",
]


def build_ctx(config, seen_ids=None):
    """sources.json config + 큐 상태로 게이트 컨텍스트 구성."""
    harvest = (config or {}).get("harvest", {})
    return {
        "seen_ids": list(seen_ids or []),
        "relevance_keywords": harvest.get("relevance_keywords", []),
        "baseline_terms": list(DEFAULT_BASELINE_TERMS) + list(harvest.get("baseline_terms", [])),
        "min_relevance": int(harvest.get("min_relevance", 1)),
    }


def should_queue(item, ctx):
    """수확 아이템을 큐에 넣을지 판정. 반환 (keep: bool, result: dict).
    keep=False(REJECT)면 하베스터는 큐에 안 넣고 log("gate_reject", ...)."""
    res = score_item(item, ctx)
    return res["verdict"] != "REJECT", res


def verify_item(item, probes=None):
    """큐/pull 단계 주장 검증. 프로브 없이는 어떤 주장도 VERIFIED 불가(런타임≠소스)."""
    return verify_claims(item, probes=probes)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = {"harvest": {"relevance_keywords": ["claude", "agent", "mcp", "skill", "automation"]}}
    ctx = build_ctx(cfg, seen_ids=["gh-repo-old-dup"])
    samples = [
        {"id": "gh-repo-anthropics-x", "title": "anthropics/x MCP agent skill",
         "content": "new claude agent skill for orchestration", "owner_trusted": True},
        {"id": "gh-repo-old-dup", "title": "dup", "content": "claude agent"},
        {"id": "gh-repo-foo-pw", "title": "playwright helper",
         "content": "agent automation over playwright"},
        {"id": "yt-hype", "title": "This changed everything \U0001F525\U0001F525\U0001F525",
         "content": "in 2026 you need this $20/mo stack agent"},
    ]
    print("=== apply_gates demo — 수확 게이트 (KEEP/DROP) ===")
    for it in samples:
        keep, res = should_queue(it, ctx)
        print("%-4s %-4d %-24s %s" % (
            "KEEP" if keep else "DROP", res["score"], it["id"], "; ".join(res["reasons"])[:56]))

    print("\n=== apply_gates demo — 주장 검증 ===")
    v = verify_item({"id": "x", "title": "10x faster, only $20, everything Free",
                     "content": "50000 stars, the best tool"})
    print("summary:", v["summary"])
    for c in v["claims"]:
        print("  [%-11s] %-16s %s" % (c["verdict"], c["type"], c["claim"]))
