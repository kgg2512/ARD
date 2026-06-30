#!/usr/bin/env python3
"""
CAR Notify — 보고 푸시 채널 (Mariah 조직도의 'Reports via Telegram' 이식).

회장은 모바일-우선. 보고서를 파일에 가두지 말고 폰으로 푸시한다.
Telegram Bot API(무료) 사용. 환경변수 없으면 no-op(설치만, 키는 회장).

설정(회장 1회):
  1. 텔레그램 @BotFather 로 봇 생성 → 토큰
  2. 봇과 대화 시작 후 chat_id 확인
  3. 환경변수: ARD_TELEGRAM_TOKEN, ARD_TELEGRAM_CHAT_ID
       setx ARD_TELEGRAM_TOKEN "123:abc"
       setx ARD_TELEGRAM_CHAT_ID "987654321"

사용:
  python car_notify.py "보고 내용"
  from car_notify import push; push("내용")
"""
import json
import os
import sys
import urllib.request
import urllib.error


def push(text):
    """Telegram으로 텍스트 푸시. 성공 True / 미설정·실패 False."""
    token = os.environ.get("ARD_TELEGRAM_TOKEN")
    chat_id = os.environ.get("ARD_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_configured():
    return bool(os.environ.get("ARD_TELEGRAM_TOKEN") and os.environ.get("ARD_TELEGRAM_CHAT_ID"))


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) or "[ARD] 테스트 메시지"
    if not is_configured():
        print("[CAR Notify] ARD_TELEGRAM_TOKEN/CHAT_ID 미설정 — 푸시 건너뜀 (설정법은 파일 상단 주석)")
        sys.exit(0)
    ok = push(msg)
    print("[CAR Notify]", "전송 성공" if ok else "전송 실패")
    sys.exit(0 if ok else 1)
