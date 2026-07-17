# -*- coding: utf-8 -*-
"""usefulness_gate.py — ARD 수확 쓸모 게이트 (HARVEST→QUEUE 상류 필터).

표준 라이브러리만 사용. 네트워크/LLM 호출 0.
큐 아이템({id, source, kind, title, content, owner_trusted?, star_suspect?, trust_note?, ...})을
받아 쓸모 점수(0~100)와 판정(ACCEPT/REVIEW/REJECT)을 낸다.

규칙:
  (a) DEDUP    — id가 seen_ids에 있으면 즉시 REJECT("중복")
  (b) 관련성    — relevance_keywords 매치수 < min_relevance(기본1) → REJECT("관련성 0")
  (c) BASELINE — G2가 이미 커버하는 용어(스킬/MCP/역량) 매치 → 감점 30(후보 강등)
  (d) FOMO     — 클릭베이트 패턴 매치당 감점 8
  (e) 신뢰      — owner_trusted +20 / star_suspect -15(+note)

점수 = clamp(50 + relevance_hits*10(최대+30) - baseline*30 - fomo_hits*8 + trust, 0, 100)
판정 = dedup/관련성미달 → REJECT / score>=60 → ACCEPT / 35~59 → REVIEW / <35 → REJECT
"""
import re
import sys

# 이모지 3개 이상 연속 (🔥🚀💰 등)
_EMOJI_RUN = "[\U0001F300-\U0001FAFF☀-➿⬀-⯿]{3,}"

_FOMO_RAW = [
    r"changed everything",
    r"game[- ]?changer",
    r"미루면",
    r"떨어집니다",
    r"you'?re falling behind",
    r"nobody is talking",
    r"this is insane",
    r"절정",
    r"must[- ]?have",
    r"\$\d+\s*(?:startup|stack|/mo)",
    r"in 202\d you need",
    # 크립토/트레이딩·수익낚시 클릭베이트 (2026-07-16 YouTube 실수확 'trading bot CRUSHING 24/7' 반영)
    r"crushing",
    r"\b\d+/7\b",
    r"to the moon",
    r"passive income",
    r"get rich",
    r"insane\s+(?:gains?|returns?|profit|money)",
    _EMOJI_RUN,
]
FOMO_PATTERNS = [re.compile(p) for p in _FOMO_RAW]

REL_BONUS_PER_HIT = 10
REL_MAX_BONUS = 30
BASELINE_PENALTY = 30
FOMO_PENALTY = 8
TRUST_BONUS = 20
SUSPECT_PENALTY = 15

ACCEPT_MIN = 60
REVIEW_MIN = 35


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, int(v)))


def score_item(item: dict, ctx: dict) -> dict:
    """아이템 1건 채점. 반환: {id, score, verdict, reasons, signals}."""
    item_id = item.get("id", "")
    seen = set(ctx.get("seen_ids") or [])
    reasons = []
    signals = {
        "dedup": False,
        "baseline_covered": False,
        "relevance_hits": 0,
        "fomo_hits": 0,
        "trust": "unknown",
    }

    # (e) 신뢰 신호 (dedup 케이스에도 표기)
    trusted = bool(item.get("owner_trusted"))
    suspect = bool(item.get("star_suspect"))
    signals["trust"] = (
        "trusted+suspect" if (trusted and suspect)
        else "trusted" if trusted
        else "suspect" if suspect
        else "unknown"
    )

    # (a) DEDUP — 즉시 REJECT
    if item_id and item_id in seen:
        signals["dedup"] = True
        reasons.append("중복: 이미 큐/처리/증류된 id")
        return {"id": item_id, "score": 0, "verdict": "REJECT",
                "reasons": reasons, "signals": signals}

    text = ((item.get("title") or "") + " " + (item.get("content") or "")).lower()

    # (b) 관련성
    rel_kws = [k.lower() for k in (ctx.get("relevance_keywords") or []) if k]
    hit_kws = [k for k in rel_kws if k in text]
    signals["relevance_hits"] = len(hit_kws)
    min_rel = int(ctx.get("min_relevance", 1))

    # (c) BASELINE (이미 커버하는 역량 → 강등)
    base_terms = [b.lower() for b in (ctx.get("baseline_terms") or []) if b]
    base_hits = [b for b in base_terms if b in text]
    if base_hits:
        signals["baseline_covered"] = True
        reasons.append("baseline 커버—후보 강등 (%s)" % ", ".join(base_hits))

    # (d) FOMO
    fomo_hits = sum(len(p.findall(text)) for p in FOMO_PATTERNS)
    signals["fomo_hits"] = fomo_hits
    if fomo_hits:
        reasons.append("FOMO/클릭베이트 신호 %d건 (매치당 -%d)" % (fomo_hits, FOMO_PENALTY))

    # (e) 신뢰 가감점
    trust_delta = 0
    if trusted:
        trust_delta += TRUST_BONUS
        reasons.append("owner allowlist 신뢰 +%d" % TRUST_BONUS)
    if suspect:
        trust_delta -= SUSPECT_PENALTY
        note = item.get("trust_note") or "스타수 이상 급증—파밍 의심"
        reasons.append("star_suspect -%d (%s)" % (SUSPECT_PENALTY, note))

    score = _clamp(
        50
        + min(signals["relevance_hits"] * REL_BONUS_PER_HIT, REL_MAX_BONUS)
        - (BASELINE_PENALTY if signals["baseline_covered"] else 0)
        - fomo_hits * FOMO_PENALTY
        + trust_delta
    )

    # watch/trusted 소스는 관련성 하드리젝 면제 — 큐레이션된 출처(watch_repos·allowlist owner)의
    # 업데이트는 커밋 메시지가 키워드 부족해도 유지(정당한 업데이트 유실 방지). dedup·FOMO·baseline은 그대로.
    # 근거: 2026-07-16 실주행 검증에서 anthropics 커밋이 '관련성 0'으로 오탈락한 결함 시정.
    relevance_exempt = trusted or bool(item.get("watched"))
    if signals["relevance_hits"] < min_rel and not relevance_exempt:
        if signals["relevance_hits"] == 0:
            reasons.insert(0, "관련성 0")
        else:
            reasons.insert(0, "관련성 부족 (%d < min %d)" % (signals["relevance_hits"], min_rel))
        verdict = "REJECT"
    else:
        if signals["relevance_hits"] < min_rel:
            reasons.insert(0, "관련성 낮으나 watch/trusted 소스 — 유지")
        else:
            reasons.insert(0, "관련 키워드 %d개 매치 (%s)" % (len(hit_kws), ", ".join(hit_kws)))
        if score >= ACCEPT_MIN:
            verdict = "ACCEPT"
        elif score >= REVIEW_MIN:
            verdict = "REVIEW"
        else:
            verdict = "REJECT"

    return {"id": item_id, "score": score, "verdict": verdict,
            "reasons": reasons, "signals": signals}


def filter_queue(items: list, ctx: dict) -> dict:
    """큐 전체 필터. ACCEPT/REVIEW만 큐 유지 대상, REJECT는 로그용."""
    accepted, review, rejected = [], [], []
    for item in items or []:
        res = score_item(item, ctx)
        if res["verdict"] == "ACCEPT":
            accepted.append(res)
        elif res["verdict"] == "REVIEW":
            review.append(res)
        else:
            rejected.append(res)
    return {
        "accepted": accepted,
        "review": review,
        "rejected": rejected,
        "stats": {
            "total": len(items or []),
            "accepted": len(accepted),
            "review": len(review),
            "rejected": len(rejected),
        },
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    samples = [
        {  # 1) 정상 anthropics 릴리스 → ACCEPT
            "id": "gh:anthropics/claude-code:v2.1.0",
            "source": "github", "kind": "release",
            "title": "anthropics/claude-code — release v2.1.0",
            "content": "Adds agent teams and improved MCP tool loading for Claude workflows",
            "owner_trusted": True,
        },
        {  # 2) 중복 → REJECT(dedup)
            "id": "gh:anthropics/claude-code:v2.0.0",
            "source": "github", "kind": "release",
            "title": "anthropics/claude-code — release v2.0.0",
            "content": "Older release already in queue",
            "owner_trusted": True,
        },
        {  # 3) FOMO 클릭베이트 → REJECT
            "id": "yt:clickbait-001",
            "source": "youtube", "kind": "video",
            "title": "This AI tool changed everything 🔥🔥🔥 (game-changer)",
            "content": "you're falling behind — in 2026 you need this $20/mo stack for your ai agent",
        },
        {  # 4) baseline 커버 → 감점(REVIEW 강등)
            "id": "gh:someone/pw-tips:readme",
            "source": "github", "kind": "repo",
            "title": "agent browser automation with playwright",
            "content": "agent automation tips and tricks",
        },
    ]
    ctx = {
        "seen_ids": ["gh:anthropics/claude-code:v2.0.0"],
        "baseline_terms": ["playwright", "ponytail", "speckit"],
        "relevance_keywords": ["claude", "agent", "mcp", "automation"],
        "min_relevance": 1,
    }

    result = filter_queue(samples, ctx)
    print("=== usefulness_gate demo ===")
    print("%-8s %-5s %-38s %s" % ("VERDICT", "SCORE", "ID", "REASONS"))
    for bucket in ("accepted", "review", "rejected"):
        for r in result[bucket]:
            print("%-8s %-5d %-38s %s" % (r["verdict"], r["score"], r["id"], "; ".join(r["reasons"])))
    print("stats:", result["stats"])
