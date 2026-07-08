#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARD 거버넌스 세션 점검 — 경량 절충안 (회장 승인 2026-07-01).

schtasks/상시 백그라운드/네트워크 harvest 없이, SessionStart에서만 하루 1회 게이트로
두 가지 거버넌스만 점검·surface (PC 부담 최소):
  1) 조직 리뷰 7일 주기 도래 → CAR 소환 리마인드
  2) tool_usage_audit: 활성화됐으나 최근 N일 0회 호출 도구 → 미활용 경고 (Q2 자동화)

판정할 게 없으면 조용(GREEN silence). 텔레그램 car_notify가 설치돼 있으면 폰 푸시.
tool_usage_audit 로직은 G2 scripts/tool_usage_audit.py를 import 재사용(단일 진실 원천,
리포트 파일은 쓰지 않음). schtasks 상주는 회장 미승인 — 이 훅이 그 경량 대체.
"""
import json
import sys
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

# cp949 콘솔 크래시 방지 (reference-cae-auto-trigger 교훈)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ARD = Path.home() / ".claude" / "ard"
GOV_STATE = ARD / "gov_state.json"      # 하루 1회 게이트 (이 훅 전용)
ORG_STATE = ARD / "org_state.json"      # 조직 리뷰 주기 (supervisor와 공유 스키마)
GATE_HOURS = 20
ORG_REVIEW_DAYS = 7
AUDIT_WINDOW_DAYS = 7

# tool_usage_audit.py 재사용 경로 후보 (단일 진실 원천).
AUDIT_CANDIDATES = [
    Path(r"C:\Users\kgg25\Desktop\G2 Company Ltd\scripts\tool_usage_audit.py"),
]


def load(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save(path, obj):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def hours_since(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(str(iso))
        if dt.tzinfo is None:              # date-only("2026-06-30")·naive → UTC로 간주
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return None


def import_audit():
    for p in AUDIT_CANDIDATES:
        if p.exists():
            try:
                spec = importlib.util.spec_from_file_location("tua", str(p))
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)   # __main__ 아님 → main() 안 돌고 리포트 안 씀
                return m
            except Exception:
                return None
    return None


def check_org(sections):
    org = load(ORG_STATE, {})
    age_h = hours_since(org.get("last_review"))
    due = age_h is None or age_h > ORG_REVIEW_DAYS * 24
    if due:
        when = "한 번도 없음" if age_h is None else f"{age_h/24:.0f}일 전"
        sections.append(
            f"[조직 리뷰] 마지막 조직 리뷰 {when} (주기 {ORG_REVIEW_DAYS}일) — 도래.\n"
            f"→ Alpha는 CAR 소환: Agent(\"CAR\") + \"조직 리뷰\". "
            f"절차: G2_ORG_STRUCTURE.md → 갭분석 → org_proposals/ (propose-only) → 회장 승인 → 반영."
        )
    org["due"] = due
    save(ORG_STATE, org)


def check_audit(sections):
    m = import_audit()
    if not m:
        return
    try:
        rows = m.load_events()
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        since = now_ms - AUDIT_WINDOW_DAYS * 86400_000
        zero = []
        for _group, items in m.TARGET_CATALOG.items():
            for label, prefix in items.items():
                if label in m.EXPECTED_ACTIVE and m.count_window(rows, since, prefix) == 0:
                    zero.append(label)
        if zero:
            sections.append(
                f"[도구 감사] 활성화됐으나 최근 {AUDIT_WINDOW_DAYS}일 0회 호출({len(zero)}종): "
                f"{', '.join(zero)}\n"
                f"→ 라우팅(docs/TOOL_ROUTING.md) 미작동 신호. 해당 작업 발생 시 Alpha가 이 도구를 우선 사용."
            )
    except Exception:
        pass


def check_loop(sections):
    """ARD 루프 소화 건강 — 수확(입력)만 쌓이고 적용/검증(출력)이 멎었나.
    schtasks 상주 미승인이라 이 SessionStart 훅이 실질 verifier.
    liveness('돌았나')가 아니라 outcome('G2가 나아졌나')의 대리지표를 surface."""
    queue = ARD / "queue"
    pending = len(list(queue.glob("*.json"))) if queue.exists() else 0
    applied = load(ARD / "applied.json", {"items": []}).get("items", [])
    tool_applied = sum(1 for it in applied if it.get("type") in ("skill", "mcp"))
    ages = [hours_since(it.get("applied_at")) for it in applied]
    ages = [a for a in ages if a is not None]
    days_since = (min(ages) / 24) if ages else None
    stalled = pending >= 25 and (days_since is None or days_since > 7)
    if stalled:
        recent = "없음" if days_since is None else f"{days_since:.0f}일 전"
        sections.append(
            f"[ARD 루프 정체] 수확대기 {pending}건인데 도구트랙 적용 {tool_applied}건·최근적용 {recent} "
            f"— '개발'이 아니라 '저장' 상태.\n"
            f"→ Alpha: CAR(또는 general-purpose+CAR.md) 소환해 **상위 3건만 배치 소화**(전량 금지). "
            f"소화 후 미적용이면 그 항목 기각·큐 정리. 방치 = 루프 죽음."
        )


def try_push(text):
    try:
        sys.path.insert(0, str(ARD / "notifier"))
        import car_notify
        car_notify.push(text)
    except Exception:
        pass


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass

    # 하루 1회 게이트 — 세션마다 반복 발화 방지
    gov = load(GOV_STATE, {})
    age = hours_since(gov.get("last_run"))
    if age is not None and age < GATE_HOURS:
        return 0

    sections = []
    check_loop(sections)
    check_org(sections)
    check_audit(sections)

    gov["last_run"] = datetime.now(timezone.utc).isoformat()
    save(GOV_STATE, gov)

    if not sections:
        return 0

    msg = "\n\n".join(sections)
    try_push(msg)
    out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
