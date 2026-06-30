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
GH_STATE_FILE = ARD_DIR / "github_state.json"
DISPATCH_STATE = ARD_DIR / "dispatch_state.json"
HARVESTER = ARD_DIR / "harvester" / "car_harvester.py"
GH_HARVESTER = ARD_DIR / "harvester" / "car_github_harvester.py"
NOTIFY_INTERVAL_HOURS = 20
HARVEST_STALE_HOURS = 36          # 유튜브(자막 느림) → 백그라운드
GH_STALE_HOURS = 12               # 깃허브(빠름) → 세션 시작 시 인라인 즉시 확인


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


def maybe_wake_harvesters():
    """노트북 켜고 세션 시작 시:
       - 깃허브(빠름): stale하면 인라인 즉시 실행 → 큐가 '바로' 갱신됨(회장 요구).
       - 유튜브(자막 느림): stale하면 백그라운드(비차단)."""
    # 깃허브 인라인 (짧은 타임아웃, 막히면 포기하고 진행)
    gh_age = hours_since(load(GH_STATE_FILE, {}).get("last_run"))
    if (gh_age is None or gh_age > GH_STALE_HOURS) and GH_HARVESTER.exists():
        try:
            subprocess.run([sys.executable, str(GH_HARVESTER)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
        except Exception:
            pass
    # 유튜브 백그라운드
    yt_age = hours_since(load(STATE_FILE, {}).get("last_run"))
    if (yt_age is None or yt_age > HARVEST_STALE_HOURS) and HARVESTER.exists():
        try:
            subprocess.Popen([sys.executable, str(HARVESTER)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def main():
    # stdin 비우기(훅 계약), 내용은 사용 안 함
    try:
        sys.stdin.read()
    except Exception:
        pass

    if not QUEUE_DIR.exists():
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    # 노트북 켜는 순간 깃허브를 바로 확인(인라인) + 유튜브 백그라운드
    maybe_wake_harvesters()

    pending = [p for p in QUEUE_DIR.glob("*.json")]
    if not pending:
        return 0

    # 하루 1회만 알림
    dstate = load(DISPATCH_STATE, {})
    age = hours_since(dstate.get("last_notify"))
    if age is not None and age < NOTIFY_INTERVAL_HOURS:
        return 0

    yt, gh, titles = 0, 0, []
    for p in pending:
        item = load(p, {})
        if item.get("source") == "github":
            gh += 1
        else:
            yt += 1
    for p in pending[:6]:
        item = load(p, {})
        tag = "📦GH" if item.get("source") == "github" else "🎬YT"
        titles.append(f"  {tag} {item.get('channel','?')}: {item.get('title','?')}")
    more = f"\n  ...외 {len(pending)-6}개" if len(pending) > 6 else ""

    msg = (
        f"[ARD/CAR 자동 디스패치] 미처리 AI-에이전트 지식 {len(pending)}건 "
        f"(유튜브 {yt} · 깃허브 {gh})이 큐에 있습니다.\n"
        f"{chr(10).join(titles)}{more}\n"
        f"→ Alpha는 CAR 에이전트를 소환해 큐를 처리하세요: Agent(\"CAR\").\n"
        f"  큐 경로: {QUEUE_DIR}\n"
        f"  처리 절차: 각 항목(자막/릴리스/레포) 이해 → docs/insights/ 작성 → 신뢰출처만 "
        f"자동적용/나머지 승인큐 → 적용물 검증 → docs/reports/ 다이제스트. (페르소나: ARD/agents/CAR.md)"
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
