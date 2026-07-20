#!/usr/bin/env python3
"""
digest_triage.py — 쌓인 큐를 '판단·검증 가능하게' 만드는 소화 하네스 (QUEUE→판정).

회장 질문(2026-07-20): "큐 59건을 판단하고, 검증할 수 있는 방법이나 하네스는 없냐?"

■ 문제
  usefulness_gate(수확 상류 필터)·claim_verifier(주장 검증)·supervisor.check_adoption
  (사후 채택 검증)은 이미 있었으나, **쌓인 큐 전체에 대한 판정 패스가 없어** 조립이 안 됐다.
  결과: 수확만 되고 소화가 멎음(loop_health stalled).

■ 4층 하네스에서 이 파일의 자리 = L1 + L2 준비
  L1 [기계 분류, LLM 0원]  ← 이 파일. 명백한 잡음을 근거와 함께 제거. 재현·검증 가능.
  L2 [LLM 판정, 구조 강제]  ← 이 파일이 만든 review_list를 CAR가 읽고 판정. 자유서술 금지,
       반드시 {claim, g2_applies_to, baseline_covered, required_probe, verdict} 구조로.
       baseline_covered=true면 자동 EVICT(가지치기 교리 = "추가는 baseline 이길 때만").
  L3 [주장 검증]  ← claim_verifier: required_probe 실행 결과 없으면 VERIFIED 불가 → 적용 불가.
  L4 [사후 채택 검증]  ← supervisor.check_adoption: 적용 후 7일+ 0회 호출 = 판정 오류 신호.
       이 피드백이 L2 판정 기준을 자기교정한다(하네스가 스스로 배운다).

■ L1 기계 규칙 (실측 큐 59건에서 관찰된 잡음 패턴 기반 — 근거 없는 휴리스틱 아님)
  - GH awesome-list '최신 커밋': 커밋 해시만 있고 내용 없음 → 학습가치 0
  - GH 고스타 비신뢰 소유자: 스타=관심도이지 신뢰 아님 → 자동적용 불가(승인 대기)
  - YT 자막 < MIN_TRANSCRIPT: 실질 내용 없음(쇼츠·티저)
  - YT 뉴스/랭킹형 제목: 사건 나열이라 재사용 기법 없음
  판정은 전부 reason과 함께 원장에 남는다 → 사람이 재검토·반박 가능(불투명 필터 금지).

실행:
    python digest_triage.py              # 판정 + 원장 기록 + 요약 출력
    python digest_triage.py --review     # L2로 넘길 항목(CAR 판정 대상)만 출력
산출: ~/.claude/ard/triage/<날짜>_triage.json (판정 원장)
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ARD_DIR = Path.home() / ".claude" / "ard"
QUEUE_DIR = ARD_DIR / "queue"
TRIAGE_DIR = ARD_DIR / "triage"
CONFIG_FILE = ARD_DIR / "config" / "sources.json"

MIN_TRANSCRIPT = 3000        # 이보다 짧은 자막 = 실질 내용 없음(관찰: 1.6k~1.8k는 티저/쇼츠)
STAR_UNTRUSTED = 50000       # 고스타+비신뢰 소유자 = 스타파밍 의심(하베스터 정책과 동일 상수)

# 뉴스/랭킹형 = 사건 나열이라 '재사용 가능한 기법'이 없음 → 저가치
NEWS_PAT = re.compile(
    r"(AI News|News:|INSANE|Which AI Is Better|Things You May|Breakdown|"
    r"Explained!|vs\.?\s|Top \d+|Best .* Tools|Only AI Tools)", re.I)
# awesome-list류 = 커밋 이벤트일 뿐 내용 없음
AWESOME_PAT = re.compile(r"(awesome-|-prompts|최신 커밋)", re.I)

# ── 주제 밀도(G2 코어 용어) ────────────────────────────────────────────────
# 관찰: '길이'는 판별력이 없다(악성코드 인터뷰 43k자 > 에이전트 기법 17k자).
# 진짜 판별자는 '자막 본문에 G2가 실제로 쓰는 기법 용어가 얼마나 조밀한가'.
# 가중치: 특이 기술어(고신호) 3점 / 일반 에이전트어(중신호) 1점. 'AI'처럼 어디나 있는 말은 제외.
CORE_TERMS_HIGH = [
    "claude code", "agentic", "subagent", "sub-agent", "mcp", "model context protocol",
    "orchestration", "orchestrator", "multi-agent", "context engineering", "context window",
    "tool call", "tool use", "system prompt", "skill", "hook", "harness", "eval",
    "spec-driven", "codebase", "refactor", "cli", "git worktree",
]
CORE_TERMS_MED = [
    "agent", "workflow", "prompt", "token", "llm", "automation", "pipeline",
    "verification", "test", "debug", "api", "framework",
]
DENSITY_MIN = 12.0   # 10k자당 가중점수. 이 미만 = 주제 무관(뉴스·인터뷰·잡담)


def topic_density(text):
    """자막 1만자당 G2 코어 용어 가중 점수. 기계적·재현가능(LLM 0원)."""
    if not text:
        return 0.0
    low = text.lower()
    score = sum(low.count(t) * 3 for t in CORE_TERMS_HIGH)
    score += sum(low.count(t) for t in CORE_TERMS_MED)
    return round(score / (len(low) / 10000.0), 1) if low else 0.0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_items():
    out = []
    if not QUEUE_DIR.exists():
        return out
    for p in sorted(QUEUE_DIR.glob("*.json")):
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return out


def classify(item):
    """L1 기계 분류. 반환 (verdict, reason).
       verdict: EVICT(잡음 확정) / REVIEW(LLM 판정 필요) / APPROVAL(신뢰경계 — 회장/보안 판단)"""
    src = item.get("source")
    title = str(item.get("title") or "")
    if src == "github":
        kind = item.get("kind", "")
        repo = str(item.get("repo") or "")
        if kind == "commit" or AWESOME_PAT.search(title) or AWESOME_PAT.search(repo):
            return "EVICT", "awesome-list/커밋 이벤트 — 커밋 해시만 있고 재사용 기법 없음"
        stars = item.get("stars") or 0
        trusted = item.get("trusted") or item.get("owner_trusted")
        if stars >= STAR_UNTRUSTED and not trusted:
            return "APPROVAL", f"고스타(⭐{stars:,}) 비신뢰 소유자 — 스타=관심도이지 신뢰 아님, 자동적용 불가"
        if kind == "release":
            return "REVIEW", "릴리스 노트 — 실제 변경점에 적용가치 있을 수 있음"
        return "REVIEW", "트렌딩 레포 — 내용 판정 필요"
    # YouTube
    chars = item.get("transcript_chars") or len(item.get("transcript") or "")
    if chars < MIN_TRANSCRIPT:
        return "EVICT", f"자막 {chars}자 < {MIN_TRANSCRIPT} — 실질 내용 없음(티저/쇼츠)"
    if NEWS_PAT.search(title):
        return "EVICT", "뉴스/랭킹형 — 사건 나열, 재사용 가능한 기법 없음"
    dens = topic_density(item.get("transcript") or "")
    if dens < DENSITY_MIN:
        return "EVICT", f"주제밀도 {dens} < {DENSITY_MIN} — 길지만 G2 기법과 무관(인터뷰·잡담)"
    return "REVIEW", f"기법형 후보(밀도 {dens}, 자막 {chars:,}자) — CAR 구조 판정 필요"


def archive_evicted(results, items_by_file):
    """EVICT 판정분을 큐에서 evicted/로 이동(삭제 아님 — 되돌릴 수 있게).
       판정만 하고 큐에 두면 '소화'가 아니다. 잡음을 실제로 배출해야 loop_health가
       진짜 신호만 센다. 각 항목에 triage_reason을 박아 사후 반박·감사 가능."""
    EVICTED_DIR = ARD_DIR / "evicted"
    EVICTED_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for r in results:
        if r["verdict"] != "EVICT":
            continue
        src = QUEUE_DIR / r["file"]
        if not src.exists():
            continue
        try:
            d = json.loads(src.read_text(encoding="utf-8"))
            d["triage_verdict"] = "EVICT"
            d["triage_reason"] = r["reason"]
            d["triage_at"] = now_iso()
            (EVICTED_DIR / r["file"]).write_text(
                json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            src.unlink()
            moved += 1
        except Exception:
            continue
    return moved


def apply_l2(verdicts_path):
    """L2(CAR 구조판정) 결과를 큐에 반영 — 판정만 하고 큐에 두면 '소화'가 아니다.
       EVICT→evicted/ · APPROVAL→approval/(회장 판단 대기) · APPLY→큐 잔류(프로브 검증 전엔 적용 불가).
       각 항목에 claim/baseline_covered/required_probe/reason을 박아 판정 근거를 영구 보존."""
    try:
        data = json.loads(Path(verdicts_path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[apply-l2] 판정 파일 읽기 실패: {e}")
        return {}
    items = data.get("items") or []
    dests = {"EVICT": ARD_DIR / "evicted", "APPROVAL": ARD_DIR / "approval"}
    moved = {"EVICT": 0, "APPROVAL": 0, "APPLY": 0, "미발견": 0}
    for v in items:
        vid, verdict = v.get("id"), (v.get("verdict") or "").upper()
        src = QUEUE_DIR / f"{vid}.json"
        if not src.exists():
            moved["미발견"] += 1
            continue
        if verdict == "APPLY":          # 프로브 검증 통과 전엔 큐에 남긴다(생성≠검증)
            moved["APPLY"] += 1
            continue
        dest_dir = dests.get(verdict)
        if not dest_dir:
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            d = json.loads(src.read_text(encoding="utf-8"))
            d.update({
                "l2_verdict": verdict,
                "l2_claim": v.get("claim"),
                "l2_g2_applies_to": v.get("g2_applies_to"),
                "l2_baseline_covered": v.get("baseline_covered"),
                "l2_required_probe": v.get("required_probe"),
                "l2_reason": v.get("reason"),
                "l2_at": now_iso(),
            })
            (dest_dir / src.name).write_text(
                json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            src.unlink()
            moved[verdict] += 1
        except Exception:
            continue
    return moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true", help="L2 판정 대상만 출력")
    ap.add_argument("--apply", action="store_true",
                    help="EVICT 판정분을 큐 → evicted/ 로 실제 배출(되돌릴 수 있음)")
    ap.add_argument("--apply-l2", metavar="VERDICTS_JSON",
                    help="L2(CAR) 구조판정 결과를 큐에 반영: EVICT→evicted/, APPROVAL→approval/")
    args = ap.parse_args()

    if args.apply_l2:
        m = apply_l2(args.apply_l2)
        remain = len(list(QUEUE_DIR.glob("*.json")))
        print(f"[apply-l2] EVICT {m.get('EVICT',0)} → evicted/ · APPROVAL {m.get('APPROVAL',0)} → approval/ "
              f"· APPLY {m.get('APPLY',0)} 큐잔류(프로브 대기) · 미발견 {m.get('미발견',0)}")
        print(f"           큐 잔여 {remain}건")
        return 0

    items = load_items()
    if not items:
        print("[triage] 큐 비어있음")
        return 0

    results, counts = [], {"EVICT": 0, "REVIEW": 0, "APPROVAL": 0}
    for path, it in items:
        verdict, reason = classify(it)
        counts[verdict] += 1
        results.append({
            "id": it.get("id") or path.stem,
            "source": "github" if it.get("source") == "github" else "youtube",
            "channel": it.get("channel") or it.get("repo") or "?",
            "title": str(it.get("title") or "")[:120],
            "chars": it.get("transcript_chars") or 0,
            "density": topic_density(it.get("transcript") or ""),
            "verdict": verdict,
            "reason": reason,
            "file": path.name,
        })

    TRIAGE_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    ledger = {"ts": now_iso(), "total": len(results), "counts": counts, "items": results}
    (TRIAGE_DIR / f"{date}_triage.json").write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.review:
        # L2(CAR 판정) 대상만 — 자막 긴 순(정보량 순)
        rev = sorted([r for r in results if r["verdict"] == "REVIEW"],
                     key=lambda r: -r["density"])
        for r in rev:
            print(f"{r['source']:8s} [{r['channel'][:18]:18s}] {r['title'][:58]:58s} 밀도{r['density']:>6} {r['chars']:>7,}자  id={r['id']}")
        print(f"\nL2 판정 대상 {len(rev)}건 (CAR가 구조 판정: claim/g2_applies_to/baseline_covered/required_probe/verdict)")
        return 0

    print(f"[triage] 큐 {len(results)}건 판정 → EVICT {counts['EVICT']} · REVIEW {counts['REVIEW']} · APPROVAL {counts['APPROVAL']}")
    print(f"  신호비율(REVIEW+APPROVAL): {(counts['REVIEW']+counts['APPROVAL'])/len(results):.0%}")
    print("\n--- EVICT 근거별 ---")
    from collections import Counter
    for reason, n in Counter(r["reason"] for r in results if r["verdict"] == "EVICT").most_common():
        print(f"  {n:3d}건  {reason}")
    print("\n--- L2 판정 대상 상위 10(정보량 순) ---")
    for r in sorted([r for r in results if r["verdict"] == "REVIEW"], key=lambda r: -r["density"])[:12]:
        print(f"  밀도{r['density']:>6}  [{r['channel'][:16]:16s}] {r['title'][:56]:56s} {r['chars']:>7,}자")
    if args.apply:
        moved = archive_evicted(results, None)
        remain = len(list(QUEUE_DIR.glob("*.json")))
        print(f"\n[apply] EVICT {moved}건을 evicted/로 배출 → 큐 잔여 {remain}건(진짜 신호만)")
        print(f"        되돌리기: {ARD_DIR / 'evicted'} 에서 queue/로 복사")

    print(f"\n원장: {TRIAGE_DIR / f'{date}_triage.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
