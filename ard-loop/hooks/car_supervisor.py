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

ARD_DIR = Path.home() / ".claude" / "ard"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "state.json"
APPLIED_FILE = ARD_DIR / "applied.json"          # CAR이 적용할 때마다 기록하는 원장
REPORTS_DIR = ARD_DIR / "reports"
HARVESTER = ARD_DIR / "harvester" / "car_harvester.py"
SKILL_USAGE = Path.home() / ".claude" / "skill_usage.jsonl"   # G2 기존 사용 신호

HARVEST_STALE_HOURS = 48
QUEUE_BACKLOG_WARN = 15
ADOPTION_GRACE_DAYS = 7


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
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 3600
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


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    findings = []
    harvester_status = check_harvester(findings)
    pending = check_queue(findings)
    adoption = check_adoption(findings)

    has_fail = any(f[0] == "FAIL" for f in findings)
    has_warn = any(f[0] == "WARN" for f in findings)
    health = "RED" if has_fail else ("YELLOW" if has_warn else "GREEN")

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "health": health,
        "harvester_status": harvester_status,
        "queue_pending": pending,
        "adoption": adoption,
        "findings": [{"level": l, "area": a, "detail": d} for (l, a, d) in findings],
    }
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    try:
        (REPORTS_DIR / f"{date}_health.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # 회장 다이제스트 (GREEN이면 조용히, YELLOW/RED만 출력 + 폰 푸시)
    if health != "GREEN":
        lines = [f"[ARD/CAR 감독] 건강도: {health}"]
        for (l, a, d) in findings:
            if l != "OK":
                lines.append(f"  [{l}] {a}: {d}")
        lines.append("→ Alpha/CAR 후속 조치 필요.")
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
