# -*- coding: utf-8 -*-
"""test_harness.py — usefulness_gate + claim_verifier 자가 테스트 (증빙).

표준 라이브러리만. assert 기반. 전부 통과 시 "ALL PASS (N/N)" + exit 0, 실패 시 exit 1.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from usefulness_gate import score_item, filter_queue  # noqa: E402
from claim_verifier import extract_claims, verify_claims  # noqa: E402

CTX = {
    "seen_ids": ["gh:anthropics/claude-code:v2.0.0"],
    "baseline_terms": ["playwright", "ponytail", "speckit"],
    "relevance_keywords": ["claude", "agent", "mcp", "automation"],
    "min_relevance": 1,
}


def case1_dedup_reject():
    """① 중복 아이템 → REJECT(dedup)"""
    item = {"id": "gh:anthropics/claude-code:v2.0.0",
            "title": "anthropics/claude-code — release v2.0.0",
            "content": "claude agent stuff"}
    r = score_item(item, CTX)
    assert r["verdict"] == "REJECT", r
    assert r["signals"]["dedup"] is True, r
    assert any("중복" in reason for reason in r["reasons"]), r


def case2_zero_relevance_reject():
    """② 관련성 0 → REJECT"""
    item = {"id": "yt:cooking-101",
            "title": "Best pasta recipe of the year",
            "content": "boil water, add salt, enjoy"}
    r = score_item(item, CTX)
    assert r["verdict"] == "REJECT", r
    assert r["signals"]["relevance_hits"] == 0, r
    assert any("관련성 0" in reason for reason in r["reasons"]), r


def case3_fomo_clickbait():
    """③ FOMO 클릭베이트 → REJECT/REVIEW + fomo_hits 다수"""
    item = {"id": "yt:clickbait-001",
            "title": "This AI tool changed everything 🔥🔥🔥 (game-changer)",
            "content": "you're falling behind — in 2026 you need this $20/mo stack for your ai agent"}
    r = score_item(item, CTX)
    assert r["verdict"] in ("REJECT", "REVIEW"), r
    assert r["signals"]["fomo_hits"] >= 4, r


def case4_normal_release_accept():
    """④ 정상 anthropics 릴리스 → ACCEPT"""
    item = {"id": "gh:anthropics/claude-code:v2.1.0",
            "title": "anthropics/claude-code — release v2.1.0",
            "content": "Adds agent teams and improved MCP tool loading for Claude workflows",
            "owner_trusted": True}
    r = score_item(item, CTX)
    assert r["verdict"] == "ACCEPT", r
    assert r["score"] >= 60, r
    assert r["signals"]["trust"] == "trusted", r


def case5_baseline_demotion():
    """⑤ baseline 커버 → 감점 30 (동일 아이템 baseline 유/무 대조)"""
    item = {"id": "gh:someone/pw-tips:readme",
            "title": "agent browser automation with playwright",
            "content": "agent automation tips and tricks"}
    ctx_with = dict(CTX)
    ctx_without = dict(CTX, baseline_terms=[])
    r_with = score_item(item, ctx_with)
    r_without = score_item(item, ctx_without)
    assert r_with["signals"]["baseline_covered"] is True, r_with
    assert r_without["signals"]["baseline_covered"] is False, r_without
    assert r_without["score"] - r_with["score"] == 30, (r_with["score"], r_without["score"])


ITEM_B = {
    "id": "yt:sourceB-20-dollar-stack",
    "title": "The $20 SaaS startup stack",
    "content": "Total monthly cost to run a startup: ~$20, everything Free",
}

ALL_TYPES_TEXT = ("Free 무료 $99 40% 10x 3배 24 hours 2시간 "
                  "⭐ 50000 stars fastest best revolutionary")


def case6_unverified_without_probes():
    """⑥ 소스B $20/free → probes 없이는 pricing·cost 전부 UNVERIFIED (불변식 강제)"""
    rep = verify_claims(ITEM_B)  # probes 없음
    types = {c["type"] for c in rep["claims"]}
    assert "pricing" in types and "cost" in types, types
    # 핵심 불변식: probes 없이는 어떤 주장도 VERIFIED 불가
    assert all(c["verdict"] != "VERIFIED" for c in rep["claims"]), rep
    assert rep["summary"]["verified"] == 0, rep["summary"]
    assert all(c["required_probe"] for c in rep["claims"]), rep
    # 불변식을 7개 전 유형에 대해서도 강제
    mega = {"id": "test:all-types", "title": "", "content": ALL_TYPES_TEXT}
    rep2 = verify_claims(mega)
    types2 = {c["type"] for c in rep2["claims"]}
    expected = {"pricing", "cost", "metric_percent", "metric_multiplier",
                "time_saving", "popularity", "superlative"}
    assert expected <= types2, types2
    assert rep2["summary"]["verified"] == 0, rep2["summary"]
    assert all(c["verdict"] != "VERIFIED" for c in rep2["claims"]), rep2


def case7_star_suspect_contradicted():
    """⑦ star_suspect 아이템 → popularity 주장 CONTRADICTED"""
    item = {"id": "gh:starfarm/awesome-ai-tool",
            "title": "⭐ 227000 stars — the best AI tool",
            "content": "revolutionary results guaranteed",
            "star_suspect": True}
    rep = verify_claims(item)
    pops = [c for c in rep["claims"] if c["type"] == "popularity"]
    assert pops, rep
    assert all(c["verdict"] == "CONTRADICTED" for c in pops), pops
    assert any("파밍" in c["note"] for c in pops), pops
    assert rep["summary"]["contradicted"] >= 1, rep["summary"]


def case8_probes_enable_verified():
    """⑧ probes 주입 시에만 VERIFIED 전환 (프로브 안 준 type은 그대로 UNVERIFIED)"""
    probes = {"pricing": {"verdict": "VERIFIED", "note": "공급자 ToS 실확인 완료(상업용 무료 허용)"}}
    rep = verify_claims(ITEM_B, probes=probes)
    pricing = [c for c in rep["claims"] if c["type"] == "pricing"]
    cost = [c for c in rep["claims"] if c["type"] == "cost"]
    assert pricing and all(c["verdict"] == "VERIFIED" for c in pricing), pricing
    assert cost and all(c["verdict"] == "UNVERIFIED" for c in cost), cost
    assert rep["summary"]["verified"] >= 1, rep["summary"]
    # 프로브가 반박이면 CONTRADICTED
    rep2 = verify_claims(ITEM_B, probes={"pricing": False})
    assert all(c["verdict"] == "CONTRADICTED"
               for c in rep2["claims"] if c["type"] == "pricing"), rep2


def case9_popularity_precision():
    """⑨ popularity 정밀도: 연도/포트/에러코드 오탐 0, ⭐·stars·콤마 표기는 탐지"""
    # 오탐이면 안 됨(맨숫자만)
    for t in ["Released in 2026", "listening on port 8080", "error 4044 occurred"]:
        claims = extract_claims(t)
        assert not any(c["type"] == "popularity" for c in claims), (t, claims)
    # 탐지돼야 함(⭐ 접두 / stars 접미 / 콤마 / 한글 스타)
    for t in ["⭐ 227000", "227000 stars", "1,234 stars", "12000 스타"]:
        claims = extract_claims(t)
        assert any(c["type"] == "popularity" for c in claims), (t, claims)


def case10_watched_relevance_exempt():
    """⑩ watch/trusted 소스는 관련성 0이어도 하드리젝 면제(≠REJECT), 무관 일반은 REJECT (실주행 결함 시정)"""
    terse = {"id": "gh-com-anthropics-cookbook-abc",
             "title": "anthropics/anthropic-cookbook 최신 커밋 abc",
             "content": "Update README"}  # 관련 키워드 0
    assert score_item(terse, CTX)["verdict"] == "REJECT", score_item(terse, CTX)
    watched = dict(terse, watched=True)
    assert score_item(watched, CTX)["verdict"] != "REJECT", score_item(watched, CTX)
    trusted = dict(terse, owner_trusted=True)
    assert score_item(trusted, CTX)["verdict"] != "REJECT", score_item(trusted, CTX)


def case11_crypto_clickbait_fomo():
    """⑪ 크립토/트레이딩 수익낚시 클릭베이트 → FOMO 신호 다수 감지(점수 다운그레이드)"""
    item = {"id": "yt:trade-1",
            "title": "This AI Trading Bot Is CRUSHING It 24/7 — passive income to the moon",
            "content": "ai agent automation for crypto trading"}
    r = score_item(item, CTX)
    assert r["signals"]["fomo_hits"] >= 3, r


CASES = [
    ("① 중복→REJECT(dedup)", case1_dedup_reject),
    ("② 관련성0→REJECT", case2_zero_relevance_reject),
    ("③ FOMO 클릭베이트→REJECT/REVIEW", case3_fomo_clickbait),
    ("④ 정상 anthropics 릴리스→ACCEPT", case4_normal_release_accept),
    ("⑤ baseline 커버→감점", case5_baseline_demotion),
    ("⑥ probes 없이 VERIFIED 불가(불변식)", case6_unverified_without_probes),
    ("⑦ star_suspect→popularity CONTRADICTED", case7_star_suspect_contradicted),
    ("⑧ probes 주입시 VERIFIED 전환", case8_probes_enable_verified),
    ("⑨ popularity 정규식 정밀도(오탐 0)", case9_popularity_precision),
    ("⑩ watch/trusted 관련성 면제(실주행 결함 시정)", case10_watched_relevance_exempt),
    ("⑪ 크립토/트레이딩 클릭베이트 FOMO 감지", case11_crypto_clickbait_fomo),
]

if __name__ == "__main__":
    passed = 0
    failed = []
    for name, fn in CASES:
        try:
            fn()
            passed += 1
            print("PASS  %s" % name)
        except AssertionError as e:
            failed.append(name)
            print("FAIL  %s — %r" % (name, e))
    total = len(CASES)
    print("-" * 50)
    print("passed %d / %d" % (passed, total))
    if passed == total:
        print("ALL PASS (%d/%d)" % (passed, total))
        sys.exit(0)
    sys.exit(1)
