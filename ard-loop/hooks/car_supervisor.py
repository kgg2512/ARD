#!/usr/bin/env python3
"""
CAR Supervisor — 감독·평가·자가복구 (스케줄 실행).

회장 정의의 "자동화": 특정 시점에 시스템이 잘 도는지 관리·감독·평가하고,
보고하고, 문제 시 개선·보완. 이 스크립트가 그 감독관이다.

점검 항목:
  1. harvester 가동성 — 마지막 실행이 너무 오래됐나 (stale → 자가 재실행)
  2. 큐 적체 — 미처리 자막이 임계 초과인가 (CAR 처리 촉구 플래그)
  3. 적용물 채택 — 적용한 스킬/MCP가 실제로 호출되는가 (0회 = 적용 실패)
  4. 종합 건강 리포트 + 회장 플래그 출력

실행: Task Scheduler 주 1회, 또는 시간 게이트 SessionStart 보조.
산출: ~/.claude/ard/reports/<날짜>_health.json  (CAR이 레포 docs/reports로 승격)
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 한글 출력이 cp949 콘솔(회장 PC 기본)에서 크래시하지 않도록 stdout/stderr를 UTF-8로 강제.
# (em-dash 등 cp949 미매핑 문자에서 UnicodeEncodeError로 훅이 죽는 함정 방어.)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ARD_DIR = Path.home() / ".claude" / "ard"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "state.json"
APPLIED_FILE = ARD_DIR / "applied.json"          # CAR이 적용할 때마다 기록하는 원장
ORG_STATE_FILE = ARD_DIR / "org_state.json"      # 조직 리뷰 주기 상태 (OrgDev 트랙)
SUP_STATE_FILE = ARD_DIR / "supervisor_state.json"  # 감독 마지막 실행 마커(SSOT) — self_heal·dispatch가 신선도 판정
REPORTS_DIR = ARD_DIR / "reports"
HARVESTER = ARD_DIR / "harvester" / "car_harvester.py"
SKILL_USAGE = Path.home() / ".claude" / "skill_usage.jsonl"   # G2 기존 사용 신호
DASHBOARD_EVENTS = Path.home() / ".claude" / ".dashboard-events.jsonl"  # always-on 전 도구 로거(교차대조용)

HARVEST_STALE_HOURS = 48
QUEUE_BACKLOG_WARN = 15
VALUE_REVIEW_GATE = 20          # 큐가 이 이상이면 회장에게 '이 루프 존폐 가치판정'을 자동 요청 (회장 지시 2026-07-12)
ADOPTION_GRACE_DAYS = 7
ORG_REVIEW_DAYS = 7              # 조직 리뷰 주기 — N일 지나면 CAR 조직 리뷰 촉구 (큐레이터 7일과 정합)
LOOP_STALL_BACKLOG = 25         # 수확대기가 이 이상 + 최근 적용 없음 → 루프 정체(FAIL)
LOOP_STALL_DAYS = 3             # 마지막 '적용'이 이보다 오래됐고 큐가 쌓이면 = 소화 멎음 (회장 지시 2026-07-21: 8일 방치 금지, 3일에 정체 판정→조기 escalate)


def load(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def hours_since(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(str(iso))
        if dt.tzinfo is None:              # date-only("2026-07-01")·naive → UTC로 간주 (적용원장 날짜 대응)
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return None


def check_harvester(findings):
    state = load(STATE_FILE, {})
    age = hours_since(state.get("last_run"))
    if age is None:
        findings.append(("WARN", "harvester", "한 번도 실행된 적 없음"))
        return "never"
    if age > HARVEST_STALE_HOURS:
        findings.append(("FAIL", "harvester", f"마지막 실행 {age:.0f}h 전 (stale) → 자가 재실행 시도"))
        if HARVESTER.exists():
            try:
                subprocess.Popen([sys.executable, str(HARVESTER)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        return "stale_healing"
    findings.append(("OK", "harvester", f"마지막 실행 {age:.0f}h 전"))
    return "ok"


def check_queue(findings):
    pending = len(list(QUEUE_DIR.glob("*.json"))) if QUEUE_DIR.exists() else 0
    if pending > QUEUE_BACKLOG_WARN:
        findings.append(("WARN", "queue", f"미처리 {pending}개 적체 (임계 {QUEUE_BACKLOG_WARN}) → CAR 처리 촉구"))
    else:
        findings.append(("OK", "queue", f"미처리 {pending}개"))
    return pending


def load_skill_usage_names():
    names = set()
    if not SKILL_USAGE.exists():
        return names
    try:
        for line in SKILL_USAGE.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            n = rec.get("skill") or rec.get("name") or rec.get("skill_name")
            if n:
                names.add(str(n).lower())
    except Exception:
        pass
    return names


def check_adoption(findings):
    """적용한 스킬/MCP가 채택 유예기간 후에도 0회 호출이면 '적용 실패'."""
    applied = load(APPLIED_FILE, {"items": []})
    items = applied.get("items", [])
    if not items:
        findings.append(("OK", "adoption", "적용 이력 없음"))
        return {"checked": 0, "unused": []}
    used = load_skill_usage_names()
    unused = []
    for it in items:
        name = str(it.get("name", "")).lower()
        applied_at = it.get("applied_at")
        age_h = hours_since(applied_at)
        if it.get("type") == "skill" and age_h and age_h > ADOPTION_GRACE_DAYS * 24:
            short = name.split("/")[-1].replace("-mcp", "")
            if not any(short in u for u in used):
                unused.append(it.get("name"))
    if unused:
        findings.append(("WARN", "adoption",
                         f"적용 후 {ADOPTION_GRACE_DAYS}일+ 미사용(채택 실패 의심): {', '.join(unused)}"))
    else:
        findings.append(("OK", "adoption", f"적용 {len(items)}건 채택 양호"))
    return {"checked": len(items), "unused": unused}


def check_skill_logger(findings):
    """스킬 사용 로거 유실 검증 (회장 지시 2026-07-20 — '큐레이터가 잘 되는지 검증').
    큐레이터는 skill_usage.jsonl로 미사용 스킬을 판정한다. 그런데 그 로거가 조용히 유실하면
    (matcher 매칭실패 등) 큐레이터는 '전부 미사용'으로 오판한다 — 판단 근거가 썩는다.
    검증: always-on dashboard 로거(전 도구 기록)의 Skill 호출 수와 skill_usage.jsonl을 교차대조.
    dashboard엔 Skill이 있는데 usage 로거엔 없으면 = 로거 유실 = 큐레이터 근거 오염."""
    WINDOW_DAYS = 7   # 최근 창만 비교 → '지금 로거가 작동하나'만 본다(과거 이력 false-positive 방지).
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)

    def in_window_epoch_or_iso(v):
        """dashboard=epoch(ms/s), usage=ISO 둘 다 지원 → 최근 WINDOW_DAYS 내인가."""
        try:
            f = float(v)
            if f > 1e12:
                f /= 1000.0
            return datetime.fromtimestamp(f, timezone.utc) >= cutoff
        except (TypeError, ValueError):
            try:
                dt = datetime.fromisoformat(str(v))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt >= cutoff
            except Exception:
                return False

    def skill_events_in_dashboard():
        if not DASHBOARD_EVENTS.exists():
            return None
        n = 0
        try:
            lines = DASHBOARD_EVENTS.read_text(encoding="utf-8", errors="replace").splitlines()[-5000:]
            for l in lines:
                if '"Skill"' not in l:
                    continue
                try:
                    d = json.loads(l)
                except Exception:
                    continue
                if (d.get("tool") == "Skill" or d.get("tool_name") == "Skill") and \
                   in_window_epoch_or_iso(d.get("ts") or d.get("timestamp")):
                    n += 1
        except Exception:
            return None
        return n
    d = skill_events_in_dashboard()
    if d is None:
        findings.append(("OK", "skill_logger", "대시보드 로그 없음 — 교차대조 생략"))
        return {"dashboard": None}
    u = 0
    if SKILL_USAGE.exists():
        try:
            for l in SKILL_USAGE.read_text(encoding="utf-8").splitlines():
                if not l.strip():
                    continue
                try:
                    rec = json.loads(l)
                except Exception:
                    continue
                if in_window_epoch_or_iso(rec.get("ts")):
                    u += 1
        except Exception:
            u = 0
    # dashboard가 Skill을 여러 번 봤는데 usage 로거가 거의 못 잡았으면 = 유실
    if d >= 3 and u < max(2, d * 0.5):
        findings.append(("FAIL", "skill_logger",
                         f"스킬 사용 로거 유실 의심 — 대시보드 Skill {d}건 vs usage 로거 {u}건. "
                         f"큐레이터 판단 근거 오염(matcher/스크립트 점검)"))
    else:
        findings.append(("OK", "skill_logger", f"로거 정합 — 대시보드 {d} · usage {u}"))
    return {"dashboard": d, "usage": u}


def check_org_review(findings):
    """조직 트랙(OrgDev): 마지막 조직 리뷰가 ORG_REVIEW_DAYS 지났으면 due 플래그.
    → dispatch가 SessionStart에 'CAR 소환해 조직 리뷰'를 surface. 도구 큐와 독립."""
    org = load(ORG_STATE_FILE, {})
    age_h = hours_since(org.get("last_review"))
    due = age_h is None or age_h > ORG_REVIEW_DAYS * 24
    if due:
        when = "한 번도 없음" if age_h is None else f"{age_h/24:.0f}일 전"
        findings.append(("WARN", "org_review",
                         f"마지막 조직 리뷰 {when} (주기 {ORG_REVIEW_DAYS}일) → CAR 조직 리뷰 촉구"))
    else:
        findings.append(("OK", "org_review", f"마지막 조직 리뷰 {age_h/24:.0f}일 전"))
    org["due"] = due
    try:
        ORG_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        ORG_STATE_FILE.write_text(json.dumps(org, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return due


def check_loop_health(findings, pending):
    """소화 건강도 — 수확(입력)이 쌓이는데 적용/검증(출력)이 멎었나.
    ARD 핵심 실패모드 = '개발이 아니라 저장'(hoarding). liveness가 아니라 outcome을 본다.
    (회장 질문 '스스로 검증하려면?'의 답 = 이 자기점검: 루프가 실제로 닫히는지 자가진단.)"""
    state = load(STATE_FILE, {})
    processed = len(state.get("processed_ids", []))
    items = load(APPLIED_FILE, {"items": []}).get("items", [])
    applied_total = len(items)
    applied_tool = sum(1 for it in items if it.get("type") in ("skill", "mcp"))
    ages = [hours_since(it.get("applied_at")) for it in items]
    ages = [a for a in ages if a is not None]
    days_since_applied = (min(ages) / 24) if ages else None
    digestion = processed / (processed + pending) if (processed + pending) else 1.0
    stalled = (pending >= LOOP_STALL_BACKLOG and
               (days_since_applied is None or days_since_applied > LOOP_STALL_DAYS))
    recent = "없음" if days_since_applied is None else f"{days_since_applied:.0f}일전"
    detail = (f"수확대기 {pending}·처리 {processed}·적용 {applied_total}"
              f"(도구트랙 {applied_tool})·소화율 {digestion:.0%}·최근적용 {recent}")
    if stalled:
        findings.append(("FAIL", "loop_health", f"루프 정체(수확만 되고 소화·적용 멎음) — {detail}"))
    elif pending >= QUEUE_BACKLOG_WARN:
        findings.append(("WARN", "loop_health", detail))
    else:
        findings.append(("OK", "loop_health", detail))
    return {"processed": processed, "applied_total": applied_total,
            "applied_tool": applied_tool, "digestion": round(digestion, 2),
            "days_since_applied": days_since_applied, "stalled": stalled}


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    findings = []
    harvester_status = check_harvester(findings)
    pending = check_queue(findings)
    loop = check_loop_health(findings, pending)
    adoption = check_adoption(findings)
    skill_logger = check_skill_logger(findings)
    org_review_due = check_org_review(findings)

    has_fail = any(f[0] == "FAIL" for f in findings)
    has_warn = any(f[0] == "WARN" for f in findings)
    health = "RED" if has_fail else ("YELLOW" if has_warn else "GREEN")

    # 회장 가치판정 게이트 (2026-07-12): 큐가 VALUE_REVIEW_GATE 도달 = 5번(루프 존폐)의 자동화.
    # 무인 CAR 자동배출(토큰 낭비)이 아니라, 정량 근거로 회장에게 '이 루프 계속할 가치 있나'를 올린다.
    value_review_due = pending >= VALUE_REVIEW_GATE

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "health": health,
        "harvester_status": harvester_status,
        "queue_pending": pending,
        "loop_health": loop,
        "adoption": adoption,
        "skill_logger": skill_logger,
        "org_review_due": org_review_due,
        "value_review_due": value_review_due,
        "findings": [{"level": l, "area": a, "detail": d} for (l, a, d) in findings],
    }
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    try:
        (REPORTS_DIR / f"{date}_health.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # 감독 실행 마커(SSOT) — 누가 실행하든(schtask·dispatch·self_heal) 여기 기록.
    # self_heal의 supervision_live 목표가 이 마커로 신선도를 판정한다(예전엔 dispatch만 찍어
    # self_heal이 직접 돌려도 마커 미갱신 → 목표 영구 미충족 버그가 있었음, 2026-07-20 수정).
    try:
        SUP_STATE_FILE.write_text(
            json.dumps({"last_run": report["ts"]}, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # 회장 다이제스트 (GREEN이면 조용히, YELLOW/RED만 출력 + 폰 푸시)
    if health != "GREEN" or value_review_due:
        lines = [f"[ARD/CAR 감독] 건강도: {health}"]
        for (l, a, d) in findings:
            if l != "OK":
                lines.append(f"  [{l}] {a}: {d}")
        lines.append("→ Alpha/CAR 후속 조치 필요.")
        # 🔔 회장 가치판정 요청 (큐 20+ 도달 = 5번 자동화). 회장이 계속/조준수정/중단을 정량 근거로 결정.
        if value_review_due:
            dsa = loop.get("days_since_applied")
            recent = "없음" if dsa is None else f"{dsa:.0f}일 전"
            lines.append("")
            lines.append(f"🔔 [회장 가치판정 요청] 큐 {pending}건 도달 (게이트 {VALUE_REVIEW_GATE}) — 이 루프가 회장께 값진지 판정할 시점.")
            lines.append(f"   누적 실적: 처리 {loop.get('processed', 0)} · 도구적용 {loop.get('applied_tool', 0)}건 · "
                         f"소화율 {loop.get('digestion', 0):.0%} · 최근적용 {recent}")
            lines.append("   → 회장 판정: ① 계속(현 조준 유지)  ② 조준수정(sources.json)  ③ 중단(루프 정지)")
        digest = "\n".join(lines)
        print(digest)
        # Telegram 푸시(설정 시) — Mariah 'Reports via Telegram' 이식
        try:
            sys.path.insert(0, str(ARD_DIR / "notifier"))
            import car_notify
            car_notify.push(digest)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
