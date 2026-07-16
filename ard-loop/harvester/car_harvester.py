#!/usr/bin/env python3
"""
CAR Harvester — ARD 자율학습 루프 1단계 (HARVEST).

유튜브 채널 RSS에서 신규 영상을 찾아 자막(transcript)을 수집해 큐에 적재한다.
LLM을 호출하지 않는 저비용 단계 — 이해/적용은 CAR(Claude)가 큐를 읽어 수행한다.
(이전 influencer_monitor가 'RSS 제목 정규식'에 머문 한계를 자막 수집으로 돌파.)

실행:
    python car_harvester.py            # 24h 게이트 적용, 정기 실행용(Task Scheduler)
    python car_harvester.py --force    # 게이트 무시 즉시 실행
    python car_harvester.py --limit 3  # 채널당 최대 N개

운영 데이터: ~/.claude/ard/  (큐·상태·로그)
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ARD_DIR = Path.home() / ".claude" / "ard"
CONFIG_FILE = ARD_DIR / "config" / "sources.json"
QUEUE_DIR = ARD_DIR / "queue"
STATE_FILE = ARD_DIR / "state.json"
LOG_FILE = ARD_DIR / "harvester.log.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def log(event, **kw):
    rec = {"ts": now_iso(), "event": event, **kw}
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
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


# ── 수확 쓸모 게이트 배선 (ard-loop/gate/apply_gates.py) — fail-open, 회귀0 ──
_GATE = None
_GATE_CTX = None


def _init_gate(config, seen_ids):
    """게이트 로드 + 컨텍스트. 실패해도 하베스터 정상 동작(fail-open)."""
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
    """큐 적재 허용 여부. REJECT면 False + log("gate_reject"). 오류 시 fail-open(True)."""
    if not (_GATE and _GATE_CTX):
        return True
    try:
        keep, res = _GATE.should_queue(item, _GATE_CTX)
        if not keep:
            log("gate_reject", id=item.get("id"), score=res.get("score"),
                reasons=res.get("reasons"))
        return keep
    except Exception as e:
        log("gate_error_admit", error=str(e))
        return True


def should_run(state, interval_hours, force):
    if force:
        return True
    last = state.get("last_run")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        return datetime.now(timezone.utc) - last_dt > timedelta(hours=interval_hours)
    except Exception:
        return True


def fetch_rss(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        log("rss_fetch_error", channel_id=channel_id, error=str(e))
        return None


def parse_rss(xml_text):
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    out = []
    try:
        root = ET.fromstring(xml_text)
        for entry in root.findall("atom:entry", ns):
            vid = entry.find("yt:videoId", ns)
            if vid is None or not vid.text:
                continue
            title = entry.find("atom:title", ns)
            published = entry.find("atom:published", ns)
            desc = entry.find(".//media:description", ns)
            out.append({
                "id": vid.text,
                "title": (title.text or "") if title is not None else "",
                "published": (published.text or "") if published is not None else "",
                "description": (desc.text or "") if desc is not None else "",
                "url": f"https://www.youtube.com/watch?v={vid.text}",
            })
    except Exception as e:
        log("rss_parse_error", error=str(e))
    return out


def get_transcript(video_id, languages):
    """자막 수집. youtube-transcript-api 필요(install.ps1이 설치). 실패는 graceful."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, "youtube-transcript-api 미설치 — install.ps1 실행 필요"
    try:
        # 신/구 버전 API 모두 시도
        try:
            segments = YouTubeTranscriptApi().fetch(video_id, languages=languages)
            segments = [{"text": s.text} for s in segments]
        except Exception:
            segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        text = " ".join(seg.get("text", "") for seg in segments).strip()
        return (text or None), (None if text else "빈 자막")
    except Exception as e:
        return None, str(e)


def is_relevant(text, keywords):
    low = text.lower()
    return any(kw in low for kw in keywords)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    ARD_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    config = load_json(CONFIG_FILE, {})
    if not config:
        print("[CAR Harvester] config 없음:", CONFIG_FILE, "(install.ps1 실행 필요)")
        return 1

    h = config.get("harvest", {})
    interval = h.get("interval_hours", 24)
    max_per = args.limit or h.get("max_per_channel", 5)
    langs = h.get("transcript_languages", ["en", "ko"])
    keywords = [k.lower() for k in h.get("relevance_keywords", [])]

    state = load_json(STATE_FILE, {"last_run": None, "processed_ids": []})
    if not should_run(state, interval, args.force):
        return 0

    processed = set(state.get("processed_ids", []))
    channels = [c for c in config.get("youtube", []) if c.get("active", True)]

    # 수확 쓸모 게이트 초기화 — 이미 큐에 있는 id를 dedup seen으로 공급
    _init_gate(config, [p.stem for p in QUEUE_DIR.glob("*.json")])
    harvested, skipped_irrelevant, no_transcript, gate_rejected = 0, 0, 0, 0

    for ch in channels:
        cid = ch.get("channel_id", "")
        if not cid:
            continue
        xml = fetch_rss(cid)
        if not xml:
            continue
        for video in parse_rss(xml)[:max_per]:
            vid = video["id"]
            if vid in processed:
                continue
            processed.add(vid)

            # 1차 관련성: 제목+설명
            if keywords and not is_relevant(f"{video['title']} {video['description']}", keywords):
                # 자막까지 받아 2차 판정하기엔 비용 → 제목/설명에서 무관하면 skip
                skipped_irrelevant += 1
                continue

            transcript, err = get_transcript(vid, langs)
            if not transcript:
                no_transcript += 1
                log("no_transcript", id=vid, title=video["title"], reason=err)
                continue

            item = {
                "id": vid,
                "title": video["title"],
                "channel": ch["name"],
                "url": video["url"],
                "published": video["published"],
                "harvested_at": now_iso(),
                "status": "pending",
                "transcript_chars": len(transcript),
                "transcript": transcript,
            }
            # 쓸모 게이트: 자막을 content로 넘겨 중복·baseline·FOMO 판정
            if not _gate_admit({**item, "content": transcript}):
                gate_rejected += 1
                continue
            save_json(QUEUE_DIR / f"{vid}.json", item)
            harvested += 1
            log("harvested", id=vid, title=video["title"], channel=ch["name"], chars=len(transcript))

    state["last_run"] = now_iso()
    state["processed_ids"] = list(processed)[-2000:]
    save_json(STATE_FILE, state)

    summary = {
        "harvested": harvested,
        "skipped_irrelevant": skipped_irrelevant,
        "gate_rejected": gate_rejected,
        "no_transcript": no_transcript,
        "queue_pending": len(list(QUEUE_DIR.glob("*.json"))),
    }
    log("run_complete", **summary)
    print(f"[CAR Harvester] 수확 {harvested} · 무관 skip {skipped_irrelevant} · "
          f"게이트 reject {gate_rejected} · 자막없음 {no_transcript} · 큐 대기 {summary['queue_pending']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
