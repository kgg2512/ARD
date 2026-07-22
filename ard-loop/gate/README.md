# ard-loop/gate — 수확 쓸모 게이트 + 주장 검증 하네스 (배선)

> **원본 SSOT:** [kgg2512/g2-loop-harness](https://github.com/kgg2512/g2-loop-harness) `harness/`.
> 여기 `usefulness_gate.py`·`claim_verifier.py`는 **벤더링 사본**(ARD 독립 실행용). drift 시 원본에서 재복사.
> **계기:** 2026-07-16, 회장 지시 — "ARD의 쓸모있는 수확·검증 부족" 보완. SNS AI스택 8소스 분석(소스 A `proofreading`·`dispatcher`) 반영.

## 무엇을 채우나 (ARD 두 구멍)

```
 HARVEST ──▶ [쓸모 게이트]          ──▶ QUEUE ──▶ [주장 검증]              ──▶ PULL/APPLY
             usefulness_gate.py               claim_verifier.py
             중복·baseline·FOMO 필터            프로브 없이 VERIFIED 불가
```

| 파일 | 역할 |
|------|------|
| `usefulness_gate.py` | HARVEST→QUEUE 상류 필터. 중복(dispatcher)·G2 baseline 커버·FOMO 클릭베이트 판별로 큐 부풀림 차단 |
| `claim_verifier.py` | 생성≠검증 분리. 수확물 주장(숫자·무료·N배·스타)을 추출→required_probe 부여. **소스 텍스트만으론 절대 VERIFIED 안 됨** |
| `apply_gates.py` | 위 둘을 하베스터/pull이 부르는 얇은 배선(build_ctx·should_queue·verify_item) |
| `test_gate.py` | 자가 테스트(9/9). `python test_gate.py` → EXIT 0 |

## 배선 상태

- **하베스터(`car_github_harvester.py`·`car_harvester.py`):** `save_json(QUEUE_DIR/…)` 직전 `apply_gates.should_queue()` 호출. REJECT면 큐에 안 넣고 `log("gate_reject", …)`. **게이트 평가 불가(import/실행 실패) 시 fail-closed reject(I2, 2026-07-22 H5)** — 미검증 항목이 큐에 새지 않게. 과거 '무게이트 폴백(fail-open)'은 제거. 게이트 고장은 log(`gate_*_failclosed`) + harvest stale로 supervisor가 감지.
- **pull(`car_pull.py`):** 후보 아이템에 `verify_item()` 실행 → UNVERIFIED 주장 목록을 CAR에 제시(적용·증류 전 원본/런타임 확인 강제).

## 실행

```
cd ard-loop/gate
python test_gate.py        # 9/9 ALL PASS
python apply_gates.py      # 게이트+검증 데모
```

## 원칙
- **stdlib·LLM0·네트워크0.** 프로브 실행(원본 fetch·런타임 찌르기)은 게이트된 APPLY 단계이지 자동 아님.
- **가지치기 > 축적.** 게이트의 목적은 "많이 줍기"가 아니라 "쓸모없는 것을 상류에서 버리기".
- 상세: g2-loop-harness `docs/02_ARD_SUPPLEMENT.md`.
