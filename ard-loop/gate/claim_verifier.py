# -*- coding: utf-8 -*-
"""claim_verifier.py — 수확물 주장 검증 하네스 (생성≠검증 분리).

표준 라이브러리만 사용. 네트워크/LLM 호출 0.

G2 원칙 [feedback-verify-runtime-not-source] 이식:
  수확 텍스트 = "주장"일 뿐 "증거"가 아니다. 소스 Read ≠ 배포/런타임 현실.
  따라서 이 모듈의 핵심 불변식은:

    ★ probes(실제 프로브 결과) 없이는 어떤 주장도 VERIFIED가 될 수 없다 ★

  텍스트 안에서 숫자/가격/성능 주장을 추출(extract)하고, 각 주장에
  "무엇을 실제로 찔러야 검증되는가"(required_probe)를 붙인다.
  probes[type]로 실측 결과가 주입될 때만 VERIFIED/CONTRADICTED로 전환된다.
"""
import re
import sys

# (정규식, type, required_probe)
CLAIM_PATTERNS = [
    (re.compile(r"\bfree\b|무료", re.IGNORECASE), "pricing",
     "공급자 pricing·ToS 원문 확인(free-tier 한도·상업용 허용여부). 예: Vercel Hobby=비상업 전용"),
    (re.compile(r"\$\d+"), "cost",
     "실제 청구조건 확인(txn수수료·유저수 상향)"),
    (re.compile(r"\d+\s*%"), "metric_percent",
     "원출처 벤치마크 재현 필요(자기발표치 주의)"),
    (re.compile(r"\d+\s*(?:x|배)\b", re.IGNORECASE), "metric_multiplier",
     "벤치마크 재현 필요"),
    (re.compile(r"\d+\s*(?:hours?|시간|일|days?)", re.IGNORECASE), "time_saving",
     "자기발표 베스트케이스 주의—재현 필요(예: '2일→2시간'은 원문 'days→hours'만 명시)"),
    # popularity: ⭐ 접두 또는 stars/스타 접미 중 하나 필수 (연도·포트·에러코드 오탐 방지),
    # 콤마 천단위 표기 허용("1,234 stars"). 독립검증 지적 반영(2026-07-16).
    (re.compile(r"⭐\s*\d[\d,]*|\d[\d,]*\s*(?:stars?|스타)", re.IGNORECASE), "popularity",
     "스타수≠신뢰. owner allowlist로만 신뢰판정(스타파밍 실측 22.7만)"),
    (re.compile(r"\b(?:fastest|best|revolutionary|절정|최고|완벽)\b", re.IGNORECASE), "superlative",
     "주관 과장—증거 없음"),
]

_POPULARITY_PAT = CLAIM_PATTERNS[5][0]
_VALID_VERDICTS = ("VERIFIED", "CONTRADICTED")


def extract_claims(text: str) -> list:
    """텍스트에서 검증 필요 주장 추출. [{"span","type","required_probe"}]"""
    claims = []
    for pat, ctype, probe in CLAIM_PATTERNS:
        for m in pat.finditer(text or ""):
            span = m.group(0).strip()
            if span:
                claims.append({"span": span, "type": ctype, "required_probe": probe})
    return claims


def _normalize_probe(result):
    """probes[type] 값 정규화 → (verdict, note). dict/bool/str 지원."""
    if isinstance(result, dict):
        return str(result.get("verdict", "")).upper(), result.get("note", "")
    if isinstance(result, bool):
        return ("VERIFIED" if result else "CONTRADICTED"), ""
    return str(result).upper(), ""


def verify_claims(item: dict, probes: dict | None = None) -> dict:
    """아이템의 모든 주장에 판정 부여.

    - 기본 verdict = "UNVERIFIED" (+required_probe 안내)
    - probes[type]가 주어진 type만 VERIFIED/CONTRADICTED로 전환
      → 불변식: probes 없이는 절대 VERIFIED 불가 (소스 텍스트만으론 증거가 아니다)
    - 교차필드: title에 고스타(⭐큰수) 있는데 star_suspect=True면
      popularity 주장은 프로브와 무관하게 CONTRADICTED (파밍 의심 실측이 우선)
    """
    text = " ".join(s for s in [item.get("title"), item.get("content")] if s)
    extracted = extract_claims(text)

    star_farming = bool(item.get("star_suspect")) and bool(
        _POPULARITY_PAT.search(item.get("title") or ""))

    claims = []
    for c in extracted:
        verdict, note = "UNVERIFIED", ""
        if probes and c["type"] in probes:
            pv, pn = _normalize_probe(probes[c["type"]])
            if pv in _VALID_VERDICTS:
                verdict = pv
                note = pn or "프로브 실측 결과 반영"
        if c["type"] == "popularity" and star_farming:
            verdict = "CONTRADICTED"
            note = "고스타·비신뢰=파밍 의심"
        claims.append({
            "claim": c["span"],
            "type": c["type"],
            "verdict": verdict,
            "required_probe": c["required_probe"],
            "note": note,
        })

    summary = {
        "verified": sum(1 for c in claims if c["verdict"] == "VERIFIED"),
        "unverified": sum(1 for c in claims if c["verdict"] == "UNVERIFIED"),
        "contradicted": sum(1 for c in claims if c["verdict"] == "CONTRADICTED"),
        "total": len(claims),
    }
    return {"id": item.get("id", ""), "claims": claims, "summary": summary}


def _print_report(title, report):
    print("--- %s (id=%s) ---" % (title, report["id"]))
    for c in report["claims"]:
        print("  [%-12s] %-18s span=%-14r probe=%s%s" % (
            c["verdict"], c["type"], c["claim"], c["required_probe"],
            (" | note=" + c["note"]) if c["note"] else ""))
    print("  summary:", report["summary"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== claim_verifier demo ===")

    # 소스B형: "$20이면 스타트업 전부 돌아간다, 다 Free" — probes 없음 → 전부 UNVERIFIED
    item_b = {
        "id": "yt:sourceB-20-dollar-stack",
        "title": "The $20 SaaS startup stack",
        "content": "Total monthly cost to run a startup: ~$20, everything Free",
    }
    _print_report("소스B $20/Free 주장 (probes 없음 → VERIFIED 0)", verify_claims(item_b))

    # 스타파밍 아이템: 고스타 + star_suspect → popularity CONTRADICTED
    item_farm = {
        "id": "gh:starfarm/awesome-ai-tool",
        "title": "⭐ 227000 stars — the best AI tool",
        "content": "revolutionary results guaranteed",
        "star_suspect": True,
        "trust_note": "owner allowlist 밖 + 스타 급증 이력",
    }
    _print_report("스타파밍 아이템 (popularity → CONTRADICTED)", verify_claims(item_farm))
