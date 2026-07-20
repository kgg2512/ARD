---
name: ard-self-heal
description: >
  ARD 자율학습 루프가 오작동할 때(RED/stalled·수확 정지·훅 미발화·큐 적체) 진단(=검증)하고
  고치는(=개선) 절차. 그리고 새 실패모드를 자가치유 하네스(car_self_heal.py GOAP)에
  '영구 편입'하는 법. "ARD 루프/하네스 점검·수리·개선" 요청 시 사용.
g2_origin: agent-created
g2_created: 2026-07-20
g2_verified: true
---

# ARD Self-Heal — 진단·수리·하네스 확장 플레이북

> 원칙: **진단 = 검증(runtime probe), 버그픽스 = 개선.** 이 둘은 일회성이 아니라
> 루프/하네스의 상시 부품이다. 새 실패모드는 고치는 데서 끝내지 말고 **GOAP 엔진에
> 액션 1개로 편입**해 "다음에 또 나면 자동 복구"로 만든다.

## 0. 구조 지도 (무엇이 어디서 도나)
- 수확: `~/.claude/ard/harvester/car_harvester.py`(YT)·`car_github_harvester.py`(GH) — schtask `G2-ARD-Harvester`(일 09:00)·`G2-ARD-GitHub`(일 09:15).
- 자가치유(GOAP): `~/.claude/ard/hooks/car_self_heal.py` — schtask `G2-ARD-SelfHeal`(일 09:30). **신뢰 heartbeat.**
- 감독: `car_supervisor.py`(self_heal이 내부 실행) → `reports/<date>_health.json`.
- 세션 surface: `car_dispatch.py`(SessionStart 훅 3번째, 빠른 표시만) — self_heal을 백그라운드 kick.
- 소스(레포): `Desktop/ARD/ard-loop/`. **배포본(`~/.claude/ard/`)이 실제 실행됨 — 반드시 둘 다 갱신(소스≠배포 함정).**

## 1. 진단 = 검증 (소스 Read 금지, 런타임 실측만)
아래를 실행해 **현실**을 본다(파일 Read는 '의도'일 뿐):
```bash
# (a) 스케줄 살아있나
schtasks //query //tn "G2-ARD-*" //fo LIST | grep -i "작업\|다음"
# (b) 수확 로그 — 네트워크 실패(getaddrinfo)·harvested 0 연속?
tail -25 ~/.claude/ard/harvester.log.jsonl
# (c) 상태 신선도 — last_run이 오래됐나
cat ~/.claude/ard/state.json ~/.claude/ard/github_state.json ~/.claude/ard/supervisor_state.json
# (d) 자가치유 원장 — 무엇을 감지해 어떻게 고쳤나
tail -10 ~/.claude/ard/self_heal.jsonl
# (e) 감독 최신 건강도
cat "$(ls -t ~/.claude/ard/reports/*_health.json | head -1)"
# (f) 지금 자가치유 1회 수동 실행 → 스스로 복구되나
python ~/.claude/ard/hooks/car_self_heal.py
```
판정 기준: health RED·`loop_health.stalled=true`·`days_since_applied` 큼·큐 ≥ 20 = 정체.
수확 로그에 `getaddrinfo`/`rss_fetch_error` 연속 = 네트워크/스케줄 타이밍 실패.

## 2. 알려진 실패모드 (이미 자동 복구됨 — car_self_heal.py가 처리)
| 실패모드 | 감지(목표 술어) | 복구 액션 |
|---|---|---|
| 부팅 DNS 미준비로 수확 정지 | `fresh_harvest` 미충족 | 수확기 `wait_for_network`+실패 시 last_run 미오염 → 재수확 |
| 감독 정지(훅 미발화) | `supervision_live` 미충족 | self_heal이 supervisor 직접 실행 |
| 큐 적체 조용히 방치 | `surfaced` 미충족 | Telegram push + 영속 notice(세션마다 재노출) |
> 수확기 last_run 오염 버그와 SessionStart 훅 미발화(무거운 작업을 취약 10번째 훅에서 돌리던 것)는
> 2026-07-20 구조 수정(수확기 자가치유 + car_dispatch 슬림화 + self_heal schtask 배선)으로 근본 제거.

## 3. 새 실패모드 편입 = 하네스 확장 (핵심 — "앞으로도 자가복구")
novel 버그를 고쳤으면 **그 자리에서 `car_self_heal.py`에 GOAP 부품을 추가**한다:
1. **목표 술어** 추가: `def g_<name>(ws): return <정상조건>` → `GOALS`에 `("<name>", g_<name>)`.
2. **월드 측정** 추가: `measure()`의 `ws`에 필요한 사실(파일 age·프로브 결과) 1줄.
3. **복구 액션** 추가: `def a_<fix>(ws): ...; return ok, note` → `ACTIONS`에
   `("<fix>", <precondition(ws)>, a_<fix>, "<target goal>")`.
4. 배포: 레포 → `~/.claude/ard/hooks/car_self_heal.py` 복사, `py_compile`.
GOAP 엔진이 자동으로 그 목표를 향해 액션을 계획·실행·재측정한다(코드 변경 0으로 새 모드 흡수).

## 4. 완료 전 검증 (반드시 — 주입 테스트)
고친 실패를 **일부러 주입**해 self_heal이 실제 복구하는지 실측:
```python
# 예: supervision_live 복구 검증
import json,subprocess,sys; from pathlib import Path
S=Path.home()/".claude"/"ard"/"supervisor_state.json"
json.dump({"last_run":"2026-07-10T00:00:00+00:00"}, open(S,"w"))   # 10일전으로 오염
subprocess.run([sys.executable, str(Path.home()/".claude"/"ard"/"hooks"/"car_self_heal.py")])
print("복구됨" if json.load(open(S))["last_run"]!="2026-07-10T00:00:00+00:00" else "미복구")
```
기대: self_heal이 감지→액션→`GREEN` 수렴, 원장(`self_heal.jsonl`)에 action 기록, 2회차 조용(멱등).

## 5. 마무리
- 커밋: `Desktop/ARD` 레포 `git add -A && git commit && git push origin master`.
- 배포 정합성: `md5sum` 레포 vs `~/.claude/ard/` 일치 확인.
- 헌법 §D 준수: "고쳤다"는 소스가 아니라 **런타임 프로브 결과**([확인])로만 보고.
