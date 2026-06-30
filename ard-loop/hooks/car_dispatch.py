#!/usr/bin/env python3
"""
CAR Dispatch — UNDERSTAND 단계 트리거 (SessionStart 훅).

큐(~/.claude/ard/queue)에 미처리 자막이 쌓이면, 세션 시작 시 Alpha에게
"CAR을 소환해 큐를 처리하라"는 지시를 자동 주입한다. (G2 cae_autostart 패턴.)
하루 1회만 알림(나깅 방지). harvester가 stale하면 백그라운드로 1회 깨운다.

Claude Code SessionStart 훅으로 등록. stdin(JSON) 무시 가능, stdout으로 컨텍스트 주입.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ARD_DIR = Path.home() / ".claude" / "ard"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "state.json"
DISPATCH_STATE = ARD_DIR / "dispatch_state.json"
HARVESTER = ARD_DIR / "harvester" / "car_harvester.py"
NOTIFY_INTERVAL_HOURS = 20
HARVEST_STALE_HOURS = 36


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
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 3600
    except Exception:
        return None


def maybe_wake_harvester():
    """harvester가 오래 안 돌았으면 백그라운드로 1회 실행(비차단)."""
    state = load(STATE_FILE, {})
    age = hours_since(state.get("last_run"))
    if (age is None or age > HARVEST_STALE_HOURS) and HARVESTER.exists():
        try:
            subprocess.Popen(
                [sys.executable, str(HARVESTER)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def main():
    # stdin 비우기(훅 계약), 내용은 사용 안 함
    try:
        sys.stdin.read()
    except Exception:
        pass

    if not QUEUE_DIR.exists():
        return 0

    pending = [p for p in QUEUE_DIR.glob("*.json")]
    maybe_wake_harvester()

    if not pending:
        return 0

    # 하루 1회만 알림
    dstate = load(DISPATCH_STATE, {})
    age = hours_since(dstate.get("last_notify"))
    if age is not None and age < NOTIFY_INTERVAL_HOURS:
        return 0

    titles = []
    for p in pending[:5]:
        item = load(p, {})
        titles.append(f"  - {item.get('channel','?')}: {item.get('title','?')}")
    more = f"\n  ...외 {len(pending)-5}개" if len(pending) > 5 else ""

    msg = (
        f"[ARD/CAR 자동 디스패치] 미처리 AI-에이전트 영상 자막 {len(pending)}개가 큐에 있습니다.\n"
        f"{chr(10).join(titles)}{more}\n"
        f"→ Alpha는 CAR 에이전트를 소환해 큐를 처리하세요: Agent(\"CAR\").\n"
        f"  큐 경로: {QUEUE_DIR}\n"
        f"  처리 절차: 각 자막 이해 → docs/insights/ 인사이트 작성 → 신뢰출처만 자동적용/"
        f"나머지 승인큐 → 적용물 검증 → docs/reports/ 다이제스트. (페르소나: ARD/agents/CAR.md)"
    )

    # Claude Code SessionStart 컨텍스트 주입 형식 + 평문 폴백
    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }
    print(json.dumps(out, ensure_ascii=False))

    dstate["last_notify"] = datetime.now(timezone.utc).isoformat()
    dstate["last_pending"] = len(pending)
    save(DISPATCH_STATE, dstate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
