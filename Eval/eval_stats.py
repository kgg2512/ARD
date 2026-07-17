"""eval_stats.py — 계측기 A/B 결과에 '통계적 신뢰'를 부여하는 계측기.

WHY (다른 Claude·회장 지적):
  현 계측기는 스킬당 N=1 생성(1쌍을 judge 3명이 채점) + avgDelta 0.35 같은 point
  estimate 단독. 표본크기·신뢰구간이 없어 '노이즈를 신호로 착각'할 위험 — 이 위에
  헌법개정을 결정하면 거짓 표본 위에 서는 것. 이 모듈이 두 축으로 그걸 막는다:

  [MODE 1] judge-agreement 재분석 (현 N=1 데이터에 즉시 적용 가능)
    3 judges 판정의 '일치도'(3-0-0 만장일치 vs 2-1-0 분열)와 Δ 크기로 각 스킬 결론의
    신뢰등급(HIGH/MEDIUM/LOW/NOISE)을 매긴다. → "전체 avgDelta 0.35"는 못 믿어도
    "systematic-debugging +3.0(만장일치)"는 믿을 수 있음을 통계로 못박는다.

  [MODE 2] N-반복 유의성 (미래 실험 프로토콜의 계측기)
    variant당 N회 생성 점수 배열 2개 → 평균·표준편차·95% CI(부트스트랩)·Cohen's d·
    유의판정. point estimate 단독 산출을 코드가 금지한다(항상 분산+CI 동반).

의존성 0: 표준 라이브러리(statistics, random)만. numpy 불필요(경량).
재현성: 부트스트랩은 seed 고정.

사용:
  python eval_stats.py --reanalyze data/2026-07-01_panel_raw.json   # MODE1 재분석 리포트
  python eval_stats.py --selftest                                    # 통계 정확성 자가검증
소유: CAR / ARD 계측기. 관련: PROJECT.md, results/, [[project-ard-eval]]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
BOOTSTRAP_ITERS = 2000
BOOTSTRAP_SEED = 20260714


# ════════════════════════════════════════════════════════════════════════
# MODE 2 — N-반복 유의성 (variant당 N회 점수 → 분산+CI, point estimate 금지)
# ════════════════════════════════════════════════════════════════════════
def _pooled_sd(a: list[float], b: list[float]) -> float:
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return float("nan")
    s1, s2 = statistics.variance(a), statistics.variance(b)
    return math.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))


def _bootstrap_ci_diff(a: list[float], b: list[float], iters: int, seed: int,
                       alpha: float = 0.05) -> tuple[float, float]:
    """두 표본 평균차(a-b)의 (1-alpha) 부트스트랩 신뢰구간."""
    rng = random.Random(seed)
    diffs = []
    for _ in range(iters):
        ra = [rng.choice(a) for _ in a]
        rb = [rng.choice(b) for _ in b]
        diffs.append(statistics.mean(ra) - statistics.mean(rb))
    diffs.sort()
    lo = diffs[int((alpha / 2) * iters)]
    hi = diffs[int((1 - alpha / 2) * iters) - 1]
    return lo, hi


def nrep_stats(scores_a: list[float], scores_b: list[float],
               label_a: str = "A", label_b: str = "B") -> dict:
    """variant A(스킬팔) vs B(직접팔)의 N-반복 점수 → 완전한 통계 요약.
    point estimate(평균차)만 반환하지 않는다 — 항상 분산·CI·효과크기·유의판정 동반."""
    if len(scores_a) < 2 or len(scores_b) < 2:
        return {"error": f"N-반복 통계는 각 팔 N>=2 필요 (현재 {label_a}={len(scores_a)}, "
                         f"{label_b}={len(scores_b)}). N=1은 point estimate라 유의성 판정 불가."}
    ma, mb = statistics.mean(scores_a), statistics.mean(scores_b)
    sa, sb = statistics.stdev(scores_a), statistics.stdev(scores_b)
    diff = ma - mb
    psd = _pooled_sd(scores_a, scores_b)
    cohen_d = diff / psd if psd and not math.isnan(psd) and psd != 0 else float("inf") if diff else 0.0
    lo, hi = _bootstrap_ci_diff(scores_a, scores_b, BOOTSTRAP_ITERS, BOOTSTRAP_SEED)
    significant = (lo > 0) or (hi < 0)  # 95% CI가 0을 안 품으면 유의
    return {
        "label_a": label_a, "label_b": label_b,
        "n_a": len(scores_a), "n_b": len(scores_b),
        "mean_a": round(ma, 3), "mean_b": round(mb, 3),
        "sd_a": round(sa, 3), "sd_b": round(sb, 3),
        "mean_diff": round(diff, 3),
        "ci95_diff": [round(lo, 3), round(hi, 3)],
        "cohen_d": round(cohen_d, 3),
        "significant_95": significant,
        "verdict": (f"{label_a} 우세(유의)" if significant and diff > 0 else
                    f"{label_b} 우세(유의)" if significant and diff < 0 else
                    "유의차 없음(노이즈 가능 — CI가 0 포함)"),
    }


# ════════════════════════════════════════════════════════════════════════
# MODE 1 — judge-agreement 재분석 (현 N=1 데이터의 신뢰등급)
# ════════════════════════════════════════════════════════════════════════
def _parse_panel(panel: str) -> tuple[int, int, int]:
    """'3S-0D-0T' → (skill, direct, tie)."""
    s = d = t = 0
    for part in panel.replace(" ", "").split("-"):
        if part.endswith("S"): s = int(part[:-1])
        elif part.endswith("D"): d = int(part[:-1])
        elif part.endswith("T"): t = int(part[:-1])
    return s, d, t


def judge_confidence(entry: dict) -> dict:
    """스킬 1개 판정의 신뢰등급. 일치도(만장일치 여부) x |Δ| 효과크기.
    N=1(생성 1회)이므로 생성분산은 알 수 없다 — inter-judge 일치도가 유일한 신뢰 신호."""
    s, d, t = _parse_panel(entry.get("panel", ""))
    total = s + d + t or 1
    winner = max(s, d, t)
    agreement = winner / total                 # 3/3=1.0 만장일치, 2/3≈0.67 분열
    delta = abs(entry.get("delta", 0.0))
    unanimous = (winner == total)
    # 신뢰등급: 만장일치 + 큰효과 = HIGH / 만장일치 + 작은효과 = MEDIUM /
    #           분열 = LOW / 분열 + 미세Δ = NOISE
    if unanimous and delta >= 1.0:
        grade = "HIGH"
    elif unanimous and delta >= 0.5:
        grade = "MEDIUM"
    elif unanimous:
        grade = "LOW"            # 방향 일치하나 효과 미미(±0.5 미만)
    elif delta < 0.3:
        grade = "NOISE"          # 분열 + 미세차 = 결론 불가
    else:
        grade = "LOW"
    return {
        "key": entry.get("key"), "cat": entry.get("cat"),
        "verdict": entry.get("verdict"), "panel": entry.get("panel"),
        "delta": entry.get("delta"), "agreement": round(agreement, 2),
        "confidence": grade,
        "trustworthy": grade in ("HIGH", "MEDIUM"),
    }


def reanalyze(raw_path: Path) -> dict:
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    per = data.get("perSkill", [])
    graded = [judge_confidence(e) for e in per]
    trustworthy = [g for g in graded if g["trustworthy"]]
    noise = [g for g in graded if g["confidence"] == "NOISE"]
    return {
        "experiment": data.get("experiment"),
        "n_skills": len(per),
        "reps_per_skill": 1,   # 현 데이터의 생성 반복(=N). 이게 1이라 유의성 한계
        "graded": graded,
        "trustworthy_keys": [g["key"] for g in trustworthy],
        "noise_keys": [g["key"] for g in noise],
        "overall_avgDelta_point_estimate": data.get("overall", {}).get("avgDelta"),
    }


# ════════════════════════════════════════════════════════════════════════
def _print_reanalysis(r: dict) -> None:
    print(f"# 계측기 재분석 (통계 신뢰등급) — {r['experiment']}")
    print(f"생성 반복 N = {r['reps_per_skill']}/스킬  → N=1은 생성분산 미측정. "
          f"신뢰신호 = judge 일치도 x |Δ| 뿐.\n")
    print(f"{'스킬':26} {'판정':7} {'패널':9} {'Δ':6} {'일치':5} {'신뢰등급'}")
    print("-" * 74)
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NOISE": 3}
    for g in sorted(r["graded"], key=lambda x: (order[x["confidence"]], -abs(x["delta"] or 0))):
        print(f"{(g['key'] or ''):26} {(g['verdict'] or ''):7} {(g['panel'] or ''):9} "
              f"{str(g['delta']):6} {str(g['agreement']):5} {g['confidence']}")
    print("-" * 74)
    print(f"신뢰가능(HIGH/MEDIUM) {len(r['trustworthy_keys'])}/{r['n_skills']}: {r['trustworthy_keys']}")
    print(f"노이즈(결론불가) {len(r['noise_keys'])}: {r['noise_keys']}")
    print(f"\n[핵심] 전체 avgDelta={r['overall_avgDelta_point_estimate']}는 point estimate(N=1)라 "
          f"단독 신뢰 불가. 신뢰가능한 결론은 위 만장일치+큰효과 스킬뿐.")


def _selftest() -> int:
    """통계 정확성 자가검증 — 수기 계산과 대조."""
    fails = 0
    def check(name, cond):
        nonlocal fails
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        fails += (not cond)

    # 1) 완전 분리: [8,8,8] vs [5,5,5] → diff=3, sd=0, 명확 유의
    r = nrep_stats([8, 8, 8], [5.0, 5, 5], "skill", "direct")
    check("완전분리 mean_diff=3.0", abs(r["mean_diff"] - 3.0) < 1e-9)
    check("완전분리 유의(significant)", r["significant_95"] is True)
    check("완전분리 CI 하한>0", r["ci95_diff"][0] > 0)

    # 2) 겹침: [8,7,9] vs [7,8,8] → 평균차 작고 분산 커 비유의 기대
    r2 = nrep_stats([8, 7, 9], [7, 8, 8], "skill", "direct")
    check("겹침 비유의", r2["significant_95"] is False)

    # 3) Cohen's d 수기 대조: [10,10,10,10] vs [8,8,8,8]
    #    diff=2, pooled_sd=0 → d=inf(분산0). 대신 분산 있는 케이스로:
    #    [10,12] vs [8,10]: m1=11,m2=9,diff=2; var each=2 → pooled_sd=sqrt(2)=1.414; d=1.414
    r3 = nrep_stats([10, 12], [8, 10])
    check("Cohen d≈1.414 (수기)", abs(r3["cohen_d"] - 1.414) < 0.01)

    # 4) N=1 거부
    r4 = nrep_stats([8], [5])
    check("N=1은 error 반환(유의성 불가)", "error" in r4)

    # 5) judge_confidence: 3-0-0 +3.0 → HIGH / 1-2-0 +0.1 → NOISE
    hi = judge_confidence({"key": "x", "panel": "3S-0D-0T", "delta": 3.0})
    lo = judge_confidence({"key": "y", "panel": "1S-2D-0T", "delta": 0.1})
    med = judge_confidence({"key": "z", "panel": "3S-0D-0T", "delta": 0.7})
    check("만장일치+큰Δ = HIGH", hi["confidence"] == "HIGH")
    check("분열+미세Δ = NOISE", lo["confidence"] == "NOISE")
    check("만장일치+중Δ(0.7) = MEDIUM", med["confidence"] == "MEDIUM")

    print(f"\n=== selftest: {'ALL PASS' if not fails else f'{fails} FAIL'} ===")
    return fails


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reanalyze", metavar="RAW_JSON",
                    help="현 판정 데이터(panel_raw.json)를 통계 신뢰등급으로 재분석")
    ap.add_argument("--selftest", action="store_true", help="통계 정확성 자가검증")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(1 if _selftest() else 0)
    if args.reanalyze:
        p = Path(args.reanalyze)
        if not p.is_absolute():
            p = HERE / p
        _print_reanalysis(reanalyze(p))
        sys.exit(0)
    ap.print_help()


if __name__ == "__main__":
    main()
