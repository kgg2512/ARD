#!/usr/bin/env python3
"""
CAR GitHub Harvester — ARD 자율학습 루프 HARVEST(깃허브 갈래).

AI 에이전트/MCP/스킬 생태계의 깃허브 신호를 수집해 큐에 적재한다:
  1. watch_repos 의 신규 릴리스(또는 최신 커밋) — claude-code·MCP 서버 등 업데이트
  2. search 쿼리로 트렌딩 신규 레포 — 새 MCP/스킬/에이전트 프레임워크 발굴
유튜브 갈래와 같은 큐로 흘러 CAR(Claude)가 이해·적용을 결정한다.
LLM 비호출(저비용). 토큰 있으면(GITHUB_TOKEN/GH_TOKEN) rate limit↑, 없어도 동작(60/h).

실행:
    python car_github_harvester.py            # 12h 게이트
    python car_github_harvester.py --force
"""
import argparse
import json
import os
import socket
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# cp949 콘솔(회장 PC 기본·스케줄러 실행)에서 한글/em-dash 출력이 UnicodeEncodeError로
# 스크립트를 죽이는 함정 방어 — dispatch/supervisor와 동일 패턴(2026-07-20 수확기에도 적용).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ARD_DIR = Path.home() / ".claude" / "ard"
CONFIG_FILE = ARD_DIR / "config" / "sources.json"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "github_state.json"
LOG_FILE = ARD_DIR / "harvester.log.jsonl"
API = "https://api.github.com"
DEFAULT_INTERVAL_HOURS = 12
STAR_FARM_SUSPECT = 50000  # 이 이상인데 owner가 allowlist 밖 = 스타 파밍 의심 (스타수는 신뢰 신호 아님)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def log(event, **kw):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now_iso(), "event": event, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log("load_error", path=str(path), error=str(e))
    return default


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


# ── 수확 쓸모 게이트 배선 (ard-loop/gate/apply_gates.py) ──────────────────
# HARVEST→QUEUE 상류 필터. 게이트 import/실행 실패 시 무게이트로 폴백(회귀 0).
_GATE = None
_GATE_CTX = None


def _init_gate(config, seen_ids):
    """게이트 모듈 로드 + 컨텍스트 구성. 실패해도 하베스터는 정상 동작(fail-open)."""
    global _GATE, _GATE_CTX
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gate"))
        import apply_gates
        _GATE = apply_gates
        _GATE_CTX = apply_gates.build_ctx(config, seen_ids=seen_ids)
    except Exception as e:
        _GATE = None
        log("gate_import_skip", error=str(e))


def _gate_admit(item):
    """큐 적재 허용 여부. **fail-closed(I2, 2026-07-22 H5):** 게이트 평가 불가면 reject.
    무게이트로 미검증 항목이 큐에 새는 것을 막는다(과거 fail-open 폴백 제거)."""
    if not (_GATE and _GATE_CTX):
        log("gate_unavailable_failclosed", id=item.get("id"),
            note="게이트 미로드 → fail-closed reject(I2)")
        return False
    try:
        keep, res = _GATE.should_queue(item, _GATE_CTX)
        if not keep:
            log("gate_reject", id=item.get("id"), score=res.get("score"),
                reasons=res.get("reasons"))
        return keep
    except Exception as e:
        log("gate_error_failclosed", id=item.get("id"), error=str(e),
            note="게이트 평가 예외 → fail-closed reject(I2)")
        return False


def classify_trust(owner, stars, trusted):
    """신뢰 판정 — 스타수가 아니라 OWNER allowlist가 유일한 신뢰 근거.
    실측(2026-07-09): GitHub이 무명 레포 affaan-m/ECC에 22.7만 스타를 반환 = 스타 파밍.
    → 스타수는 관심도/relevance 신호일 뿐, 공급망 신뢰 근거로 쓰면 파밍당한 레포가 게이트 통과.
    반환: (owner_trusted, star_suspect, trust_note)."""
    if owner.lower() in trusted:
        return True, False, "owner allowlist=신뢰(자동적용 후보)"
    if stars >= STAR_FARM_SUSPECT:
        return False, True, (f"⚠️ 고스타({stars})·비신뢰 소유자 — 스타 파밍 가능성. "
                             f"스타수를 신뢰 근거로 쓰지 말 것(수동 확인·승인 큐)")
    return False, False, "비신뢰 소유자 — 스타=관심도일 뿐 신뢰 아님(자동적용 불가, 승인 큐)"


_TOKEN_DISABLED = False  # stale/invalid GH_TOKEN을 한 번 감지하면 이후 무인증으로
_NET = {"ok": 0, "neterr": 0}  # 네트워크 도달성 추적 (2026-07-20: last_run 오염 방어)


def wait_for_network(host="api.github.com", tries=4, delay=3):
    """부팅 직후 스케줄 실행 시 DNS 미준비로 조용히 죽는 것을 방어.
       DNS가 뜰 때까지 최대 tries×delay초(=12s) 대기. 끝내 안 뜨면 False.
       (dispatch 인라인 호출 timeout=25s 예산 안에 맞춤 — 세션 시작 헛대기 방지.)"""
    for _ in range(max(1, tries)):
        try:
            socket.getaddrinfo(host, 443)
            return True
        except OSError:
            time.sleep(delay)
    return False


def gh_get(url):
    """GitHub API GET. 토큰이 있으면 rate↑, 없거나 invalid면 무인증(60/h)으로 동작.

    회장 환경 함정 방어: VS Code 등이 박제한 stale GH_TOKEN이 401을 내면,
    그 토큰을 버리고 무인증으로 1회 폴백한다(이후 호출도 무인증). 무인증이어도
    public read는 core 60/h·search 10/min 한도 내에서 정상 수확된다.
    """
    global _TOKEN_DISABLED
    headers = {
        "User-Agent": "G2-CAR-Harvester",
        "Accept": "application/vnd.github+json",
    }
    token = None if _TOKEN_DISABLED else (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            _NET["ok"] += 1
            return json.loads(resp.read().decode("utf-8", errors="ignore")), None
    except urllib.error.HTTPError as e:
        _NET["ok"] += 1  # 서버가 응답함 = 네트워크 도달 O (HTTP 상태코드는 도달성과 무관)
        if e.code == 401 and token and not _TOKEN_DISABLED:
            _TOKEN_DISABLED = True
            log("token_invalid_fallback_anon", note="GH_TOKEN 401 → 무인증 폴백")
            return gh_get(url)
        return None, f"HTTP {e.code}"
    except Exception as e:
        _NET["neterr"] += 1  # URLError/getaddrinfo/timeout = 네트워크 미도달
        return None, str(e)


def should_run(state, interval_hours, force):
    if force:
        return True
    last = state.get("last_run")
    if not last:
        return True
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(last) > timedelta(hours=interval_hours)
    except Exception:
        return True


def harvest_releases(repo, seen_releases, harvested):
    """watch_repo의 신규 릴리스(없으면 최신 커밋) 감지."""
    data, err = gh_get(f"{API}/repos/{repo}/releases/latest")
    if data and data.get("tag_name"):
        tag = data["tag_name"]
        if seen_releases.get(repo) == tag:
            return
        seen_releases[repo] = tag
        item = {
            "id": f"gh-rel-{repo.replace('/', '-')}-{tag}",
            "source": "github",
            "watched": True,
            "kind": "release",
            "title": f"{repo} {tag} 릴리스",
            "channel": "GitHub",
            "url": data.get("html_url", f"https://github.com/{repo}/releases"),
            "published": data.get("published_at", ""),
            "harvested_at": now_iso(),
            "status": "pending",
            "content": (data.get("body") or "")[:6000],
        }
        if not _gate_admit(item):
            return
        save_json(QUEUE_DIR / f"{item['id']}.json", item)
        harvested.append(item["id"])
        log("gh_release", repo=repo, tag=tag)
        return
    # 릴리스 없음 → 최신 커밋 메시지로 대체(가벼운 변화 신호)
    commits, _ = gh_get(f"{API}/repos/{repo}/commits?per_page=1")
    if commits and isinstance(commits, list) and commits:
        sha = commits[0].get("sha", "")[:7]
        key = f"commit:{sha}"
        if seen_releases.get(repo) == key:
            return
        seen_releases[repo] = key
        msg = commits[0].get("commit", {}).get("message", "")
        item = {
            "id": f"gh-com-{repo.replace('/', '-')}-{sha}",
            "source": "github",
            "watched": True,
            "kind": "commit",
            "title": f"{repo} 최신 커밋 {sha}",
            "channel": "GitHub",
            "url": f"https://github.com/{repo}/commit/{sha}",
            "published": commits[0].get("commit", {}).get("author", {}).get("date", ""),
            "harvested_at": now_iso(),
            "status": "pending",
            "content": msg[:2000],
        }
        if not _gate_admit(item):
            return
        save_json(QUEUE_DIR / f"{item['id']}.json", item)
        harvested.append(item["id"])
        log("gh_commit", repo=repo, sha=sha)


def harvest_search(query, min_stars, days, seen_repos, harvested, max_results, trusted=frozenset()):
    """트렌딩/신규 레포 발굴."""
    q = urllib.parse.quote(query)
    data, err = gh_get(f"{API}/search/repositories?q={q}&sort=stars&order=desc&per_page={max_results}")
    if not data or "items" not in data:
        log("gh_search_fail", query=query, error=err)
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for repo in data["items"]:
        full = repo.get("full_name", "")
        if not full or full in seen_repos:
            continue
        if repo.get("stargazers_count", 0) < min_stars:
            continue
        pushed = repo.get("pushed_at", "")
        try:
            if pushed and datetime.fromisoformat(pushed.replace("Z", "+00:00")) < cutoff:
                continue
        except Exception:
            pass
        seen_repos.append(full)
        stars = repo.get("stargazers_count", 0)
        owner_trusted, star_suspect, trust_note = classify_trust(full.split("/")[0], stars, trusted)
        item = {
            "id": f"gh-repo-{full.replace('/', '-')}",
            "source": "github",
            "kind": "trending_repo",
            "title": f"신규/트렌딩 레포: {full} (⭐{stars})",
            "channel": "GitHub Search",
            "url": repo.get("html_url", ""),
            "published": pushed,
            "harvested_at": now_iso(),
            "status": "pending",
            "owner_trusted": owner_trusted,
            "star_suspect": star_suspect,
            "trust_note": trust_note,
            "content": f"{repo.get('description', '')}\n\nstars: {stars} | "
                       f"language: {repo.get('language', '')} | query: {query}\ntrust: {trust_note}",
        }
        if not _gate_admit(item):
            continue
        save_json(QUEUE_DIR / f"{item['id']}.json", item)
        harvested.append(item["id"])
        log("gh_trending", repo=full, stars=repo.get("stargazers_count", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    ARD_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    config = load_json(CONFIG_FILE, {})
    gh = config.get("github", {})
    if not gh.get("active", False):
        print("[CAR GitHub] github.active=false — 건너뜀 (sources.json에서 활성화)")
        return 0

    interval = gh.get("interval_hours", DEFAULT_INTERVAL_HOURS)
    state = load_json(STATE_FILE, {"last_run": None, "seen_releases": {}, "seen_repos": []})
    if not should_run(state, interval, args.force):
        return 0

    # 부팅 직후 DNS 미준비 방어(2026-07-20): 네트워크가 뜰 때까지 대기.
    # 끝내 안 뜨면 state를 건드리지 않고 종료 → last_run 오염 없음 → 다음 시도가 재수확.
    if not wait_for_network():
        log("gh_run_aborted_network", note="DNS 미준비 — last_run 미갱신, 다음 시도 재수확")
        print("[CAR GitHub] 네트워크 미준비 — 수확 보류(재시도 예정)")
        return 0

    seen_releases = state.get("seen_releases", {})
    seen_repos = state.get("seen_repos", [])
    harvested = []

    # 수확 쓸모 게이트 초기화 — 이미 큐에 있는 id를 dedup seen으로 공급
    existing_ids = [p.stem for p in QUEUE_DIR.glob("*.json")]
    _init_gate(config, existing_ids)

    for repo in gh.get("watch_repos", []):
        harvest_releases(repo, seen_releases, harvested)

    trusted = set(x.lower() for x in config.get("apply_policy", {}).get("trusted_publishers", []))
    search_cfg = gh.get("search", {})
    if search_cfg.get("active", True):
        min_stars = search_cfg.get("min_stars", 200)
        days = search_cfg.get("recent_days", 30)
        max_results = search_cfg.get("max_results", 8)
        for query in search_cfg.get("queries", []):
            harvest_search(query, min_stars, days, seen_repos, harvested, max_results, trusted)

    # 네트워크가 뜬 뒤에도 모든 API 호출이 미도달(getaddrinfo/timeout)했다면 last_run 미갱신.
    # (부분 실패·HTTP 에러는 도달로 간주하고 정상 진행 — seen 갱신으로 재수확 방지.)
    if _NET["ok"] == 0 and _NET["neterr"] > 0:
        log("gh_run_aborted_all_unreachable", neterr=_NET["neterr"])
        print("[CAR GitHub] 전 API 미도달 — 수확 보류(재시도 예정)")
        return 0

    state["last_run"] = now_iso()
    state["seen_releases"] = seen_releases
    state["seen_repos"] = seen_repos[-500:]
    save_json(STATE_FILE, state)

    pending = len(list(QUEUE_DIR.glob("*.json")))
    log("gh_run_complete", harvested=len(harvested), queue_pending=pending)
    print(f"[CAR GitHub] 신규 {len(harvested)}건 수확 · 큐 대기 {pending}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
