#!/usr/bin/env python3
"""
CAR Pull — ARD 큐를 '실작업이 당길 때만' 조회하는 프리미티브 (Push→Pull 개편, 2026-07-09).

배경(회장 지시): 기존 dispatch는 "CAR 소환해 큐 N건 전량 처리"를 매일 강권(PUSH)했고,
아무도 처리 안 해 45건이 적체됐다. 개편 = **실작업 중 "더 나은 기법 없나?" 할 때
Alpha가 이 스크립트로 관련 지식만 당긴다(PULL).** 당긴 기법이 그 작업의 검증 게이트를
통과하면 스킬로 증류(g2_verified). 안 당겨진 항목은 저비용 수확물이라 그냥 둔다(supervisor가 노화 정리).

원칙: LLM 0 · 네트워크 0 · 순수 로컬 검색. 판단(이해·적용)은 이 결과를 읽는 Alpha/CAR가 한다.

사용:
    python car_pull.py "size table parser"       # 관련 상위 5건
    python car_pull.py "rate limit" -n 8          # 상위 8건
    python car_pull.py --list                     # 큐 전체 목록(제목만)
    python car_pull.py --show <id>                # 한 항목 본문 전체(자막/릴리스노트)
    python car_pull.py "agent memory" --json      # 기계 판독용 JSON
"""
import argparse
import json
import os
import sys
import glob

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

QUEUE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "ard", "queue")

# ── 주장 검증 하네스 배선 (ard-loop/gate/apply_gates.py) ──────────────────
# pull한 항목을 실작업에 적용·증류하기 전 주장을 검증(프로브 없이는 VERIFIED 아님).
# 게이트 import 실패 시 검증 없이 정상 동작(fail-open, 회귀0).
_VERIFY = None
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gate"))
    from apply_gates import verify_item as _VERIFY
except Exception:
    _VERIFY = None


def verify_report(item):
    """항목 주장 검증 리포트(dict) 또는 None(게이트 미탑재/오류). content=자막·본문."""
    if not _VERIFY:
        return None
    try:
        return _VERIFY({"id": item.get("id", ""), "title": item.get("title", ""),
                        "content": item.get("_body", ""),
                        "star_suspect": bool(item.get("star_suspect", False))})
    except Exception:
        return None


def _print_verify(item):
    rep = verify_report(item)
    if not rep or not rep.get("claims"):
        return
    print("\n" + "-" * 60)
    print("[주장 검증] 적용·증류 전 확인 — 프로브 없이는 VERIFIED 아님 (수확 텍스트=주장, 소스≠런타임):")
    print("  summary:", rep["summary"])
    for c in rep["claims"]:
        if c["verdict"] != "VERIFIED":
            print("  [%s] %s — %s" % (c["verdict"], c["claim"], c["required_probe"]))


def load_items():
    items = []
    for f in glob.glob(os.path.join(QUEUE_DIR, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        d["_file"] = f
        d["_body"] = d.get("transcript") or d.get("content") or ""
        items.append(d)
    return items


def score_item(item, terms):
    hay = (item.get("title", "") + " " + item.get("channel", "") + " " + item["_body"]).lower()
    return sum(hay.count(t) for t in terms)


def snippet(item, terms, width=200):
    body = item["_body"]
    low = body.lower()
    pos = -1
    for t in terms:
        pos = low.find(t)
        if pos != -1:
            break
    if pos == -1:
        return body[:width].replace("\n", " ").strip()
    start = max(0, pos - width // 3)
    return ("…" if start > 0 else "") + body[start:start + width].replace("\n", " ").strip() + "…"


def fmt_meta(item):
    src = item.get("source", "youtube")
    tag = "GH" if src == "github" else "YT"
    return "[%s] %s | %s" % (tag, item.get("channel", "?"), item.get("title", "?"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("-n", "--limit", type=int, default=5)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show", metavar="ID")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    items = load_items()
    if not items:
        print("[car_pull] 큐 비어있음:", QUEUE_DIR)
        return 0

    if args.list:
        for it in sorted(items, key=lambda x: x.get("harvested_at", ""), reverse=True):
            print("%-14s %s" % (it.get("id", "?"), fmt_meta(it)))
        print("\n총 %d건. 조회: car_pull.py \"<키워드>\"" % len(items))
        return 0

    if args.show:
        hit = next((it for it in items if it.get("id") == args.show), None)
        if not hit:
            print("[car_pull] id 없음:", args.show)
            return 1
        print("# " + fmt_meta(hit))
        print("URL:", hit.get("url", ""))
        print("published:", hit.get("published", ""), "| chars:", len(hit["_body"]))
        print("-" * 60)
        print(hit["_body"])
        _print_verify(hit)
        return 0

    if not args.query:
        print("사용: car_pull.py \"<키워드>\"  |  --list  |  --show <id>")
        return 1

    terms = [t for t in args.query.lower().split() if t]
    scored = [(score_item(it, terms), it) for it in items]
    scored = [(s, it) for s, it in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: args.limit]

    if args.json:
        out = []
        for s, it in top:
            rep = verify_report(it) or {}
            out.append({"id": it.get("id"), "score": s, "source": it.get("source", "youtube"),
                        "title": it.get("title"), "channel": it.get("channel"), "url": it.get("url"),
                        "snippet": snippet(it, terms),
                        "verify": rep.get("summary"),
                        "unverified_claims": [c for c in rep.get("claims", [])
                                              if c["verdict"] != "VERIFIED"]})
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if not top:
        print("[car_pull] '%s' 관련 큐 항목 없음 (%d건 중 매치 0). 다른 키워드로 재시도하거나 직접 수행."
              % (args.query, len(items)))
        return 0

    print("[car_pull] '%s' 관련 상위 %d건 (당겨서 실작업에 참고 → 검증 통과 시 스킬로 증류):\n"
          % (args.query, len(top)))
    for s, it in top:
        print("  (%d) %-14s %s" % (s, it.get("id", "?"), fmt_meta(it)))
        print("       %s" % it.get("url", ""))
        print("       …%s" % snippet(it, terms))
        _rep = verify_report(it)
        if _rep and _rep["summary"]["total"]:
            _u = _rep["summary"]["unverified"] + _rep["summary"]["contradicted"]
            if _u:
                print("       ⚠ 미검증 주장 %d건 — 적용 전 원본/런타임 확인(--show)" % _u)
        print("       전체보기: car_pull.py --show %s\n" % it.get("id", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
