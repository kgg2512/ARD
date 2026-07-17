# 계측기 통계 재분석 — 무엇을 신뢰할 수 있나 (2026-07-14)

> `eval_stats.py`(신설) MODE1 재분석. 회장 지시: "N-반복 유의성 → 헌법개정 결정의 데이터 신뢰성 확보."
> 핵심: 현 데이터는 스킬당 **생성 N=1**. judge 일치도 × |Δ|로 신뢰등급을 매겨 '믿을 결론'과 '노이즈'를 분리한다.
> 방법: `python eval_stats.py --reanalyze data/2026-07-01_panel_raw.json` (통계 정확성 `--selftest` 9/9 PASS)

## 신뢰등급 (재현 가능)

```
스킬                         판정      패널        Δ      일치    신뢰등급
--------------------------------------------------------------------------
systematic-debugging       SKILL   3S-0D-0T  3.0    1.0   HIGH
premium-frontend-ui        DIRECT  0S-3D-0T  -1.7   1.0   HIGH
gtm-0-to-1-launch          SKILL   3S-0D-0T  1.4    1.0   HIGH
seo-audit                  SKILL   3S-0D-0T  1.3    1.0   HIGH
gdpr-compliant             DIRECT  0S-3D-0T  -0.9   1.0   MEDIUM
copywriting                SKILL   3S-0D-0T  0.8    1.0   MEDIUM
marketing-psychology       DIRECT  0S-3D-0T  -0.8   1.0   MEDIUM
security-and-hardening     SKILL   3S-0D-0T  0.7    1.0   MEDIUM
test-driven-development    SKILL   3S-0D-0T  0.7    1.0   MEDIUM
ui-ux-pro-max              DIRECT  0S-3D-0T  -0.6   1.0   MEDIUM
ponytail                   tie     0S-0D-3T  0.0    1.0   LOW
brainstorming              DIRECT  1S-2D-0T  0.1    0.67  NOISE
```

신뢰가능(HIGH/MEDIUM) 10/12 · 노이즈(결론불가) 1(brainstorming)

## 해석

- **HIGH 신뢰 4개** = 이 결론은 즉시 헌법개정 근거로 쓸 수 있다:
  - `systematic-debugging +3.0` → 타깃 라우팅 강제 정당(현 실호출 ≈0 = 최대 기회손실)
  - `premium-frontend-ui −1.7` → 무차별 의무 폐기 정당(오히려 품질 해침)
  - `gtm +1.4`, `seo-audit +1.3` → 라우팅 강화
- **MEDIUM 6개** = 방향은 만장일치지만 효과 0.5~1.0 → 참고 가능, 단독 근거로는 약함
- **NOISE 1개**(brainstorming, 1-2-0 분열 + Δ0.1) = **결론 불가**
- **전체 avgDelta 0.35 = point estimate(N=1) → 단독 신뢰 불가.** "스킬 전체가 미미하게 이득"이라는 서술은 통계적으로 못 박을 수 없다. 신뢰가능한 것은 만장일치+큰효과 극단값뿐 — PROJECT.md §5 한계("Δ ±0.6 이내 노이즈")를 코드가 정량 확정.

## 한계 & 다음 실험 (MODE2로 승격)

- 현 신뢰신호 = **judge 일치도(inter-rater)뿐.** 같은 조건 재생성 시 얼마나 흔들리는가 = **생성분산은 N=1이라 미측정.** 만장일치도 "3 judges가 같은 1쌍을 본 것"이지 생성 반복이 아니다.
- 3차 실험(`experiments/2026-07-01_exp3-*`)은 **variant당 N≥3 생성**으로 설계 → `eval_stats.py` MODE2 `nrep_stats()`가 평균·표준편차·**95% 부트스트랩 CI·Cohen's d·유의판정** 산출 → 진짜 유의성. 그때 MEDIUM 6개가 유의로 굳는지 노이즈로 무너지는지 판가름 난다.
- 이 모듈은 **point estimate 단독 산출을 거부**한다(N=1이면 error, N≥2면 항상 분산+CI 동반). 다른 Claude·회장 지적("노이즈를 신호로 착각")의 코드 차단.

## 소유
ARD 계측기 / CAR. 관련: `PROJECT.md`, `eval_stats.py`, [[project-ard-eval]]
