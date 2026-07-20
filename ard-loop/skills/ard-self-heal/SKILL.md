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

## 4.5 큐를 판단·검증하는 소화 하네스 (4층) — "수확만 되고 소화가 멎을 때"
> 회장 질문(2026-07-20) "큐 N건을 판단하고 검증할 방법이나 하네스는?"의 답.
> 부품(usefulness_gate·claim_verifier·check_adoption)은 있었으나 **쌓인 큐 전체에 대한
> 판정 패스가 없어 조립이 안 돼 있었다.** 아래 4층이 그 조립.

| 층 | 무엇 | 도구 | 비용 |
|---|---|---|---|
| **L1 기계 분류** | 명백한 잡음을 근거와 함께 배출 | `gate/digest_triage.py --apply` | LLM 0원 |
| **L2 LLM 판정** | 남은 신호만 구조 판정(자유서술 금지) | CAR 소환 | 토큰 |
| **L3 주장 검증** | required_probe 실행 전엔 VERIFIED 불가 | `gate/claim_verifier.py` | 프로브 |
| **L4 사후 채택** | 적용 후 7일+ 0회 호출 = 판정 오류 신호 | `car_supervisor.check_adoption` | 자동 |

- **L1 판별자는 '길이'가 아니라 '주제 밀도'** — 실측: 악성코드 인터뷰 43k자(밀도 8.0) < 에이전트 기법 17k자(밀도 176). `topic_density()`가 G2 코어 용어를 가중 집계. 잡음은 `evicted/`로 **이동(삭제 아님)** + `triage_reason` 박아 사후 반박 가능.
- **L2 판정 계약(필수 구조)**: `claim` / `g2_applies_to` / `baseline_covered` / `required_probe` / `verdict(APPLY·APPROVAL·EVICT)`. **`baseline_covered=true`면 무조건 EVICT**(교리: "추가는 baseline 이길 때만"). **대다수 EVICT가 정상 출력** — 억지 APPLY 금지.
- **L3 불변식**: 프로브 결과 없이는 어떤 주장도 VERIFIED 안 됨 → 적용 불가. 소스 텍스트는 증거가 아니다.
- **L4가 하네스를 자기교정**: APPLY로 판정해 적용한 게 안 쓰이면 L2 판정 기준이 틀린 것.

### ⚠️ L2.5 적대적 재검증 (필수 — 2026-07-20 실증으로 추가)
**L4는 과잉포함(적용했는데 안 씀)만 잡고 과잉가지치기(버렸는데 값졌음)는 못 잡는다.** 교리가
EVICT 쪽으로 미는데 반대방향 견제가 없으면 판정은 통계적으로 EVICT로 흐른다. 실증: CAR의
EVICT 7건을 적대적 재검증한 결과 **오판 2건 + 근거오류 1건** 발견.

**발견된 3대 편향과 시정:**
| 편향 | 실증 | 시정 |
|---|---|---|
| **증거 부담 비대칭** | EVICT 7건 중 6건의 `required_probe`가 "해당없음", APPROVAL엔 5단계 프로브 | `digest_triage.validate_l2()`가 근거 없는 EVICT를 **코드로 거부** |
| **baseline=true 무조건 EVICT가 품질비교 생략** | "같은 범주에 뭔가 있다"≠"있는 게 낫다". 오판 2건 모두 이 규칙 통과 | `baseline_covered=true`면 **기능 동등성 프로브 흔적 필수** |
| **도전받는 교리가 판사석** | G2 위임기각 결정을 문제 삼는 입력을, 그 결정을 인용해 기각 | **G2 기존 결정을 문제 삼는 입력은 그 결정을 소유한 컨텍스트가 단독 EVICT 금지** → 별도 컨텍스트로 라우팅 |

- **기계 게이트의 한계를 알 것**: `validate_l2()`는 *증거 부재*는 잡지만 *오독·교리 자기변호*는 못 잡는다(실증: Pi 건은 거부, CMUX 건은 통과). 그건 **적대적 재검증 에이전트**만 잡는다.
- **절차**: L2 판정 후 EVICT 표본에 대해 독립 에이전트(CAR 아닌 다른 계열)에게 **"이 EVICT를 반박하라"**를 시킨다. 기본값은 회의(skeptical) — "판정이 맞다"는 결론은 실제 확인 후에만. 오판 발견 시 `l2_overturned` 박아 큐로 복원.
- **자동화**: self_heal GOAP에 `queue_triaged` 목표 + `triage_queue` 액션으로 편입 → 매일 기계 소화가 자동 수행. (이 편입 자체가 §3 확장 절차의 실사용 예.)

## 4.6 자동화 생존성 감시(watchdog) — "설치했는데 안 도는" 계통 문제
> 회장 지시(2026-07-20). 이 세션에서만 **"등록됐는데 발화 안 함"을 3건** 발견:
> car_dispatch 8일 / skill_usage_logger matcher 매칭실패 / curator_check 36일(+skill_updater 34일).
> "설치했다"는 기록과 "실제로 돈다"는 현실의 괴리 = G2 인프라 계통 문제.

- **self_heal `WATCHDOG` 레지스트리**: `(이름, 흔적파일, stale_h, 스크립트, stdin필요, heavy)`.
  각 자동화의 고유 흔적을 감시하다 stale하면 **self_heal이 직접 대신 실행**(훅 발화 비의존).
  **새 자동화는 이 표에 1줄 추가** = 그때부터 감시·소생 대상. (§3 확장의 인프라판.)
- **heavy=True**(예: skill_updater 8분) → **백그라운드 발사**(비차단). self_heal은 매일 heartbeat라
  무거운 소생에 블로킹되면 안 됨. 흔적 갱신은 다음 사이클이 확인.
- **streak 추적**(`self_heal_revive.json`): 소생해도 흔적이 계속 stale이면 = 진짜 고장.
  `RETRY_H`로 재시도 억제(나깅 방지), `DEAD_STREAK`회 연속 실패 시 Telegram+notice escalate.
- **로거 유실 검증**(회장 "큐레이터가 잘 되는지 검증"): `car_supervisor.check_skill_logger`가
  always-on dashboard 로거(전 도구)와 skill_usage 로거를 **7일 창으로 교차대조**. dashboard엔
  Skill이 있는데 usage엔 없으면 = 로거 유실 = **큐레이터 판단근거 오염** → health.json FAIL.
  (이번 matcher 버그를 자동 감지하도록 설계 — 재발 시 즉시 잡힌다. 양성/음성 실측 통과.)

## 5. 마무리
- 커밋: `Desktop/ARD` 레포 `git add -A && git commit && git push origin master`.
- 배포 정합성: `md5sum` 레포 vs `~/.claude/ard/` 일치 확인.
- 헌법 §D 준수: "고쳤다"는 소스가 아니라 **런타임 프로브 결과**([확인])로만 보고.
