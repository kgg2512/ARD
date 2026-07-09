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

# 한글 출력이 cp949 콘솔(회장 PC 기본)에서 크래시하지 않도록 stdout/stderr를 UTF-8로 강제.
# (em-dash 등 cp949 미매핑 문자에서 UnicodeEncodeError로 SessionStart 훅이 죽는 함정 방어.)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ARD_DIR = Path.home() / ".claude" / "ard"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "state.json"
GH_STATE_FILE = ARD_DIR / "github_state.json"
DISPATCH_STATE = ARD_DIR / "dispatch_state.json"
ORG_STATE_FILE = ARD_DIR / "org_state.json"       # 조직 리뷰 주기 (supervisor가 due 세움)
NOTICES_FILE = ARD_DIR / "notices.jsonl"
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


def read_notices():
    """노트북 켤 때마다 surface할 일회성 공지(설치 시 seed). max_shows까지 반복 후 종료."""
    if not NOTICES_FILE.exists():
        return []
    lines, out = [], []
    try:
        raw = NOTICES_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    for ln in raw:
        ln = ln.strip()
        if not ln:
            continue
        try:
            n = json.loads(ln)
        except Exception:
            continue
        shown = n.get("shown", 0)
        maxs = n.get("max_shows", 3)
        if shown < maxs:
            out.append(n.get("text", ""))
            n["shown"] = shown + 1
        lines.append(n)
    try:
        NOTICES_FILE.write_text(
            "\n".join(json.dumps(n, ensure_ascii=False) for n in lines), encoding="utf-8")
    except Exception:
        pass
    return [t for t in out if t]


def try_push(text):
    """설치된 car_notify로 텔레그램 푸시 시도(미설정이면 조용히 무시)."""
    try:
        sys.path.insert(0, str(ARD_DIR / "notifier"))
        import car_notify
        return car_notify.push(text)
    except Exception:
        return False


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

    sections = []

    # (A) 일회성 공지 — 노트북 켤 때마다(max_shows까지) 무조건 surface
    notices = read_notices()
    if notices:
        sections.append("📌 [회장 공지]\n" + "\n\n".join(notices))

    pending = [p for p in QUEUE_DIR.glob("*.json")]

    # (B) 큐 요약 — 하루 1회 게이트
    dstate = load(DISPATCH_STATE, {})
    age = hours_since(dstate.get("last_notify"))
    queue_due = pending and (age is None or age >= NOTIFY_INTERVAL_HOURS)

    # (C) 조직 리뷰 — supervisor가 due 세움. 도구 큐와 독립으로 발화(하루 1회 게이트).
    org = load(ORG_STATE_FILE, {})
    org_notify_age = hours_since(org.get("last_org_notify"))
    org_due = bool(org.get("due")) and (org_notify_age is None or org_notify_age >= NOTIFY_INTERVAL_HOURS)
    if org_due:
        sections.append(
            "[ARD/CAR 조직 리뷰] 조직 리뷰 주기 도래 — G2 조직을 베스트프랙티스와 대조할 시점.\n"
            "→ Alpha는 CAR 소환해 조직 리뷰: Agent(\"CAR\") + \"조직 리뷰\".\n"
            "  절차: docs/G2_ORG_STRUCTURE.md 읽기 → 갭 분석(교육·개발·개선) "
            "→ docs/org_proposals/ 제안서(propose-only) → 회장 승인 → Alpha 반영. (ARD/agents/CAR.md)"
        )
        org["last_org_notify"] = datetime.now(timezone.utc).isoformat()
        save(ORG_STATE_FILE, org)

    if not sections and not queue_due:
        return 0

    if queue_due:
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
        sections.append(
            f"[ARD 큐: 당길 수 있는 지식 {len(pending)}건] (유튜브 {yt} · 깃허브 {gh})\n"
            f"{chr(10).join(titles)}{more}\n"
            f"→ PULL 모델(2026-07-09 개편): 전량 일괄처리 강권 아님. **실작업 중** 더 나은 기법이 필요할 때\n"
            f"   Alpha가 큐를 당긴다:  python ~/.claude/ard/pull/car_pull.py \"<키워드>\"\n"
            f"   당긴 기법이 그 작업의 검증 게이트를 통과하면 → .claude/skills/ard-<이름>/SKILL.md 로 증류(g2_verified).\n"
            f"   전량 이해·다이제스트가 필요하면 그때만 CAR 소환: Agent(\"CAR\"). 큐: {QUEUE_DIR}"
        )
        dstate["last_notify"] = datetime.now(timezone.utc).isoformat()
        dstate["last_pending"] = len(pending)
        save(DISPATCH_STATE, dstate)

    msg = "\n\n".join(sections)

    # 모바일 푸시(Telegram, 설정 시) — Mariah 'Reports via Telegram' 이식
    try_push(msg)

    # Claude Code SessionStart 컨텍스트 주입
    out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
