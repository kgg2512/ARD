# ✅ 설치 후 검증 체크리스트 (회장 필수 — 한 번)

> "설치 완료"는 증빙이 아니다. 아래를 **실제 실행해 결과를 눈으로 확인**해야 진짜 완료다.
> `<OPS>` = `%USERPROFILE%\.claude\ard`

## 1. 깃허브 수확 (라이브 — 이 갈래는 G2 원격에서 33개 수집 검증됨)
```powershell
python "<OPS>\harvester\car_github_harvester.py" --force
```
- [ ] `[CAR GitHub] 신규 N건 수확 · 큐 대기 M` 출력되나 (N>0 기대)
- [ ] `<OPS>\queue\` 에 `gh-*.json` 파일이 생겼나
- [ ] 한 번 더 실행 → 신규 0건이면 dedup 정상

## 2. 유튜브 수확 (회장 직접 셋업 — 자막 라이브러리 필요)
```powershell
python -m pip install youtube-transcript-api    # 설치 안 됐으면
python "<OPS>\harvester\car_harvester.py" --force --limit 2
```
- [ ] `[CAR Harvester] 수확 N ...` 출력되나
- [ ] `queue\` 에 자막 포함 항목(`transcript_chars` > 0) 생겼나
- [ ] **자막 0건이면:** 채널 자막 유무·언어(en/ko)·차단 여부 점검 후 Alpha 보고

## 3. 스케줄 등록
```powershell
schtasks /query /TN "G2-ARD-GitHub"
schtasks /query /TN "G2-ARD-GitHub-Logon"
schtasks /query /TN "G2-ARD-Harvester"
schtasks /query /TN "G2-ARD-Supervisor"
```
- [ ] 4개 다 `Ready` 상태인가 (없으면 관리자 PowerShell로 install.ps1 재실행)

## 4. SessionStart 훅 배선
- [ ] `%USERPROFILE%\.claude\settings.json` 의 `hooks.SessionStart` 에 `car_dispatch` 들어갔나
- [ ] `settings.json.bak` 백업 생성됐나
- [ ] **새 Claude 세션 1회 열기** → "📌 [회장 공지]" + 큐 요약이 뜨나

## 5. (선택) 텔레그램 폰 푸시 — Mariah 'Reports via Telegram' 이식
```powershell
setx ARD_TELEGRAM_TOKEN "봇토큰"
setx ARD_TELEGRAM_CHAT_ID "챗ID"
python "<OPS>\notifier\car_notify.py" "ARD 테스트"
```
- [ ] 폰 텔레그램에 "ARD 테스트" 도착하나
- 미설정이어도 시스템은 동작(파일/세션 보고로 폴백). 설정하면 보고가 폰으로 온다.

---

**하나라도 ❌ 나오면 그 항목·출력 그대로 Alpha에게 붙여넣어라 → 즉시 수정.**
</content>
