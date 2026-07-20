#!/usr/bin/env python3
"""
CAR Self-Heal — ARD 루프의 자가치유 하네스 (GOAP 엔진).

회장 요구(2026-07-20): "루프가 돌다가 검증(진단) 단계에서 문제를 스스로 발견하고
고치거나 복구하고, 재발해도 자아복구하는 하네스를 골모드로 씌워라."

■ 왜 별도 스크립트인가 (구조적 교훈)
  내재화 촉구가 'SessionStart 10번째 훅(car_dispatch)'이라는 취약점에 매달려 8일간
  조용히 죽었다(로컬 세션 20+회에도 미발화 — 순차실행·8분 skill_updater·타임아웃 굶김).
  → 자가치유는 **신뢰 가능한 경로(Task Scheduler, 매일)**에서 돌아 Claude 세션·취약 훅에
    의존하지 않는다. 훅이 죽어도 기계수준 복구(재수확·재감독·오염정리·escalate)는 계속된다.

■ 골모드 = GOAP (Goal-Oriented Action Planning)
  목표상태(GOALS) ← 현재상태(world) ← 복구액션(ACTIONS: precondition+effect)을 두고,
  불충족 목표를 향해 실행 가능한 액션을 계획·실행·재측정하는 닫힌 루프.
  새 실패모드가 생기면 ACTIONS/GOALS에 1개만 추가하면 된다(확장형 — "앞으로도 자가복구").

  GOALS (모두 충족 = 루프 GREEN):
    - fresh_harvest   : 수확이 신선(YT<STALE_YT_H, GH<STALE_GH_H) — 부팅 네트워크 실패로 멎지 않음
    - supervision_live: 감독이 신선(supervisor<STALE_SUP_H) — 훅이 죽어도 여기서 살림
    - surfaced        : 큐 적체가 조용히 방치되지 않음(임계 도달 시 push+영속 notice로 반드시 알림)

  ACTIONS (precondition 충족 시 실행, 목표를 effect로 겨냥):
    - a_reharvest_yt / a_reharvest_gh : 수확 stale & 네트워크 up → --force 재수확
    - a_run_supervisor                : 감독 stale → supervisor 실행(신선 health.json 생성)
    - a_escalate_backlog              : 큐 임계 & 최근 surface 없음 → Telegram push + 영속 notice

산출: ~/.claude/ard/self_heal.jsonl (자가치유 원장 — 무엇을 감지해 어떻게 고쳤나)
      ~/.claude/ard/self_heal_state.json (마지막 실행·결과 요약)
실행: Task Scheduler 매일(신뢰 heartbeat) + car_dispatch가 세션에서 보조 호출.
"""
import json
import subprocess
import sys
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

# cp949 콘솔(회장 PC·스케줄러)에서 한글/em-dash 출력 크래시 방어 — 수확기/dispatch와 동일 패턴.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ARD_DIR = Path.home() / ".claude" / "ard"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "state.json"                 # YT 수확 상태
GH_STATE_FILE = ARD_DIR / "github_state.json"       # GH 수확 상태
SUP_STATE_FILE = ARD_DIR / "supervisor_state.json"  # 감독 마지막 실행
DISPATCH_STATE = ARD_DIR / "dispatch_state.json"    # 세션 surface 마지막
HEAL_LOG = ARD_DIR / "self_heal.jsonl"              # 자가치유 원장
HEAL_STATE = ARD_DIR / "self_heal_state.json"
ESCALATE_STATE = ARD_DIR / "self_heal_escalate.json"  # 마지막 out-of-band escalate 시각(surfaced 목표 판정)
NOTICES_FILE = ARD_DIR / "notices.jsonl"            # car_dispatch가 세션에서 surface하는 영속 공지
HARVESTER = ARD_DIR / "harvester" / "car_harvester.py"
GH_HARVESTER = ARD_DIR / "harvester" / "car_github_harvester.py"
SUPERVISOR = ARD_DIR / "hooks" / "car_supervisor.py"
REPORTS_DIR = ARD_DIR / "reports"                   # supervisor가 쓰는 <date>_health.json
TRIAGE = ARD_DIR / "gate" / "digest_triage.py"      # 큐 판정·잡음 배출(소화 하네스 L1)
TRIAGE_DIR = ARD_DIR / "triage"

# 임계값 (schtask 매일 실행 가정 — 하루 놓쳐도 다음날 복구되게 여유)
STALE_YT_H = 30       # YT 수확 신선 기준 (24h 스케줄 + 여유)
STALE_GH_H = 18       # GH 수확 신선 기준 (12h 스케줄 + 여유)
STALE_SUP_H = 30      # 감독 신선 기준
BACKLOG_GATE = 20     # 큐 적체 escalate 게이트 (supervisor VALUE_REVIEW_GATE와 정합)
SURFACE_STALE_H = 48  # 큐가 쌓였는데 이 시간 이상 surface/push 없었으면 = 조용히 방치 → escalate
TRIAGE_STALE_H = 24   # 큐 판정(잡음 배출) 신선 기준
MAX_ITERS = 8         # GOAP 수렴 상한(무한루프 방지 — 액션 수보다 크게)


def now():
    return datetime.now(timezone.utc)


def now_iso():
    return now().isoformat()


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
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now() - dt).total_seconds() / 3600
    except Exception:
        return None


def log_heal(event, **kw):
    rec = {"ts": now_iso(), "event": event, **kw}
    try:
        with open(HEAL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def net_up(host="www.youtube.com"):
    try:
        socket.getaddrinfo(host, 443)
        return True
    except OSError:
        return False


def run_script(path, args=None, timeout=120):
    """스크립트를 서브프로세스로 실행. (ok, note) 반환. self_heal 자신은 죽지 않음."""
    if not Path(path).exists():
        return False, "missing"
    try:
        p = subprocess.run([sys.executable, str(path)] + (args or []),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        return (p.returncode == 0), (p.stdout or "").strip()[-400:]
    except Exception as e:
        return False, str(e)


def push(text):
    """Telegram 푸시(설정 시). 세션·훅과 무관한 out-of-band 알림 — 훅이 죽어도 회장께 닿는다."""
    try:
        sys.path.insert(0, str(ARD_DIR / "notifier"))
        import car_notify
        return bool(car_notify.push(text))
    except Exception:
        return False


def add_persistent_notice(text, max_shows=5):
    """car_dispatch가 세션 시작마다 max_shows까지 surface하는 영속 공지 append.
       훅 발화가 flaky해도 세션이 열릴 때마다 반복 노출돼 결국 회장 눈에 닿는다(중복 방지)."""
    try:
        NOTICES_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if NOTICES_FILE.exists():
            for ln in NOTICES_FILE.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if ln:
                    try:
                        existing.append(json.loads(ln))
                    except Exception:
                        pass
        # 같은 text가 이미 미소진(shown<max) 상태로 있으면 중복 추가 안 함
        for n in existing:
            if n.get("text") == text and n.get("shown", 0) < n.get("max_shows", 3):
                return
        existing.append({"text": text, "shown": 0, "max_shows": max_shows, "src": "self_heal", "ts": now_iso()})
        NOTICES_FILE.write_text(
            "\n".join(json.dumps(n, ensure_ascii=False) for n in existing), encoding="utf-8")
    except Exception:
        pass


def _triage_age():
    """마지막 큐 판정(triage) 이후 경과시간. 원장 파일 mtime 기준."""
    try:
        files = sorted(TRIAGE_DIR.glob("*_triage.json"))
        if not files:
            return None
        import os
        mt = datetime.fromtimestamp(os.path.getmtime(files[-1]), timezone.utc)
        return (now() - mt).total_seconds() / 3600
    except Exception:
        return None


def read_supervisor_health():
    """supervisor가 쓴 최신 health.json의 종합 건강도(GREEN/YELLOW/RED) 반환.
       self_heal의 3개 GOAP 목표는 '부품이 도는가'만 보고, supervisor는 '루프가 값을 내는가'
       (소화·적용 정체)까지 본다. 이걸 self_heal 판정에 통합해야 self_heal.jsonl만 보고
       GREEN 오판하는 사각(독립검증 V8)이 사라진다. 없으면 None."""
    try:
        reports = sorted(REPORTS_DIR.glob("*_health.json"))
        if not reports:
            return None
        return json.loads(reports[-1].read_text(encoding="utf-8")).get("health")
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# GOAP: 현재상태 측정
# ─────────────────────────────────────────────────────────────────────────────
def measure():
    """세계 상태를 실측(파일·네트워크 직접 프로브 — 소스가 아니라 현실)."""
    qn = len(list(QUEUE_DIR.glob("*.json"))) if QUEUE_DIR.exists() else 0
    disp = load(DISPATCH_STATE, {})
    esc = load(ESCALATE_STATE, {})
    # surfaced 판정: 세션 surface(dispatch) OR self_heal out-of-band escalate 중 더 최근 것.
    disp_age = hours_since(disp.get("last_notify"))
    esc_age = hours_since(esc.get("last_escalate"))
    ages = [a for a in (disp_age, esc_age) if a is not None]
    ws = {
        "net": net_up(),
        "yt_age": hours_since(load(STATE_FILE, {}).get("last_run")),
        "gh_age": hours_since(load(GH_STATE_FILE, {}).get("last_run")),
        "sup_age": hours_since(load(SUP_STATE_FILE, {}).get("last_run")),
        "queue": qn,
        "surface_age": min(ages) if ages else None,
        "triage_age": _triage_age(),
    }
    return ws


# ─────────────────────────────────────────────────────────────────────────────
# GOAP: 목표 술어 (world_state -> 충족 여부)
#   age가 None(한 번도 실행 안 됨)이면 불충족으로 본다.
# ─────────────────────────────────────────────────────────────────────────────
def g_fresh_harvest(ws):
    return (ws["yt_age"] is not None and ws["yt_age"] < STALE_YT_H and
            ws["gh_age"] is not None and ws["gh_age"] < STALE_GH_H)


def g_supervision_live(ws):
    return ws["sup_age"] is not None and ws["sup_age"] < STALE_SUP_H


def g_surfaced(ws):
    # 큐가 게이트 미만이면 자동 충족. 게이트 이상인데 최근 surface/push가 오래됐으면 불충족.
    if ws["queue"] < BACKLOG_GATE:
        return True
    return ws["surface_age"] is not None and ws["surface_age"] < SURFACE_STALE_H


def g_queue_triaged(ws):
    """큐에 잡음이 방치되지 않음 = 최근 triage(판정·배출)가 돌았나.
       (2026-07-20 추가 — 회장 '큐를 판단·검증할 하네스' 요구. 스킬 ard-self-heal §3
        '새 목표+액션 1개 추가' 절차를 그대로 적용한 확장 실증.)"""
    if ws["queue"] == 0:
        return True
    return ws["triage_age"] is not None and ws["triage_age"] < TRIAGE_STALE_H


GOALS = [
    ("fresh_harvest", g_fresh_harvest),
    ("supervision_live", g_supervision_live),
    ("surfaced", g_surfaced),
    ("queue_triaged", g_queue_triaged),
]


# ─────────────────────────────────────────────────────────────────────────────
# GOAP: 복구 액션 (precondition, run, targets=겨냥하는 목표)
#   run(ws) -> (ok, note). 액션이 상태를 바꾸면 다음 measure에 반영된다.
# ─────────────────────────────────────────────────────────────────────────────
def a_reharvest_yt(ws):
    ok, note = run_script(HARVESTER, ["--force"], timeout=150)
    return ok, f"YT 재수확: {note[:120]}"


def a_reharvest_gh(ws):
    ok, note = run_script(GH_HARVESTER, ["--force"], timeout=120)
    return ok, f"GH 재수확: {note[:120]}"


def a_run_supervisor(ws):
    ok, note = run_script(SUPERVISOR, [], timeout=60)
    first = note.splitlines()[0] if note else ""
    return ok, f"감독 실행 → {first[:80]}"


def a_escalate_backlog(ws):
    age = int(ws['surface_age']) if ws['surface_age'] is not None else '∞'
    msg = (f"🔴 [ARD 자가치유] 큐 {ws['queue']}건 적체 + 최근 surface {age}h 무발화.\n"
           f"내재화가 멎었습니다 — Alpha 세션에서 큐를 당기거나(car_pull.py) CAR 소환 필요.\n"
           f"(자가치유가 out-of-band로 알림 — SessionStart 훅이 죽어도 이 신호는 닿습니다.)")
    pushed = push(msg)
    add_persistent_notice(msg, max_shows=5)
    # surface 마커 기록 → surfaced 목표 충족(수렴). 다음 실행은 SURFACE_STALE_H 지나야 재escalate.
    save(ESCALATE_STATE, {"last_escalate": now_iso(), "queue": ws["queue"]})
    return True, f"escalate: push={'OK' if pushed else '미설정'} + 영속 notice"


def a_triage_queue(ws):
    """큐를 판정하고 잡음(EVICT)을 evicted/로 배출 — 판정 근거를 항목에 박아 되돌릴 수 있게.
       기계가 할 수 있는 소화는 기계가 한다(LLM은 남은 신호에만 쓴다)."""
    ok, note = run_script(TRIAGE, ["--apply"], timeout=90)
    tail = [l for l in note.splitlines() if "[apply]" in l or "판정 →" in l]
    return ok, f"큐 판정·배출 → {tail[-1].strip() if tail else note[:80]}"


ACTIONS = [
    # (name, precondition(ws)->bool, run, targets)
    ("reharvest_yt", lambda ws: ws["net"] and (ws["yt_age"] is None or ws["yt_age"] >= STALE_YT_H),
     a_reharvest_yt, "fresh_harvest"),
    ("reharvest_gh", lambda ws: ws["net"] and (ws["gh_age"] is None or ws["gh_age"] >= STALE_GH_H),
     a_reharvest_gh, "fresh_harvest"),
    ("run_supervisor", lambda ws: ws["sup_age"] is None or ws["sup_age"] >= STALE_SUP_H,
     a_run_supervisor, "supervision_live"),
    ("triage_queue", lambda ws: ws["queue"] > 0 and
     (ws["triage_age"] is None or ws["triage_age"] >= TRIAGE_STALE_H),
     a_triage_queue, "queue_triaged"),
    ("escalate_backlog", lambda ws: ws["queue"] >= BACKLOG_GATE and
     (ws["surface_age"] is None or ws["surface_age"] >= SURFACE_STALE_H),
     a_escalate_backlog, "surfaced"),
]


def unmet_goals(ws):
    return [name for (name, pred) in GOALS if not pred(ws)]


def plan_step(ws, done_actions):
    """불충족 목표를 겨냥하며 precondition 충족하는 다음 액션 1개 선택(각 액션 1회)."""
    unmet = set(unmet_goals(ws))
    for (name, pre, run, target) in ACTIONS:
        if name in done_actions:
            continue
        if target in unmet and pre(ws):
            return (name, run)
    return None


def main():
    ARD_DIR.mkdir(parents=True, exist_ok=True)
    started = now_iso()
    ws = measure()
    initial_unmet = unmet_goals(ws)
    log_heal("cycle_start", world=ws, unmet=initial_unmet)

    done, actions_taken = set(), []
    for _ in range(MAX_ITERS):
        ws = measure()
        if not unmet_goals(ws):
            break
        step = plan_step(ws, done)
        if not step:
            break  # 남은 불충족 목표에 적용 가능한 액션 없음 → escalate(있으면 이미 함) 또는 복구불가
        name, run = step
        done.add(name)
        # 네트워크가 필요한데 down이면 재수확 시도 자체를 건너뜀(precondition에서 이미 걸러짐)
        ok, note = run(ws)
        actions_taken.append({"action": name, "ok": ok, "note": note})
        log_heal("action", action=name, ok=ok, note=note)

    final_ws = measure()
    remaining = unmet_goals(final_ws)
    # 기계 건강도(GOAP 3목표 = '루프 부품이 도는가').
    mech = "GREEN" if not remaining else ("RED" if "fresh_harvest" in remaining or "supervision_live" in remaining else "YELLOW")
    # 소화 건강도(supervisor loop_health = '루프가 값을 내는가'). self_heal이 기계로 못 고치는 영역이지만
    # 여기 반영하지 않으면 self_heal.jsonl만 보고 GREEN으로 오판할 수 있음(독립검증 V8 지적) → 통합.
    sup = read_supervisor_health()
    order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    health = mech if order[mech] >= order.get(sup, 0) else sup  # 더 심각한 쪽으로

    # 복구 불가(네트워크 다운으로 재수확 실패 등)면 out-of-band escalate(중복 방지).
    if remaining and health == "RED":
        detail = ", ".join(remaining)
        if not final_ws["net"]:
            detail += " (네트워크 다운 — 복구 대기)"
        msg = f"🔴 [ARD 자가치유] 복구 후에도 미해결: {detail}. 자동복구 한계 — 회장/Alpha 확인 필요."
        push(msg)
        add_persistent_notice(msg, max_shows=5)
        log_heal("escalate_unresolved", remaining=remaining, net=final_ws["net"])

    summary = {
        "ts": started,
        "health_after": health,          # 통합(더 심각한 쪽)
        "health_mechanical": mech,       # GOAP 3목표(부품 가동)
        "health_digestion": sup,         # supervisor loop_health(값 산출)
        "initial_unmet": initial_unmet,
        "remaining_unmet": remaining,
        "actions": actions_taken,
        "world_after": final_ws,
    }
    save(HEAL_STATE, summary)
    log_heal("cycle_end", health=health, mech=mech, digestion=sup,
             remaining=remaining, n_actions=len(actions_taken))

    # 회장/Alpha 다이제스트 — 통합 GREEN이고 아무 액션 없었으면 조용히(nagging 방지).
    if health != "GREEN" or actions_taken:
        print(f"[ARD 자가치유] 통합 {health} (기계 {mech}·소화 {sup or 'n/a'}) | "
              f"초기 미충족: {initial_unmet or '없음'} | 조치 {len(actions_taken)}건 | 잔여: {remaining or '없음'}")
        for a in actions_taken:
            print(f"  - {a['action']}: {'OK' if a['ok'] else 'FAIL'} {a['note']}")
        if sup == "RED" and mech == "GREEN":
            print("  ※ 기계는 정상이나 소화(적용) 정체 = self_heal이 못 고치는 영역 → CAR/Alpha 큐 처리 필요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
