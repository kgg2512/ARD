# ARD — AI Resource Development

**G2 Company 내부 프로젝트 | AI 조직 역량의 현황 파악 · 평가 · 개선**

ARD는 G2의 AI 에이전트(Alpha·C레벨·실행 전문가)들이 **지금 어느 수준인지 현황을 파악**하고, 그것이 **실제로 효과가 있는지 증거로 평가·검증**하고, 그 결과로 **조직과 도구를 개선**하는 내부 인프라 프로젝트다. 제품이 아니라 **G2의 AI 운영 수준 자체를 복리로 끌어올리는 우산 프로젝트.**

> **왜 필요한가:** "스킬 449개 설치·MCP 20여 개 연결"은 *설치*됐다는 뜻일 뿐 *효과*가 있다는 뜻이 아니다. ARD는 그 착각을 깨는 장치 — 무엇이 실제로 품질을 올리고 무엇이 토큰만 쓰는지를 **측정**한다.

> 🧭 **구조 개편(2026-07-02):** ARD를 **"증거로 오르는 루프 사다리"**로 재정의했다 → **[ARCHITECTURE.md](./ARCHITECTURE.md)** (정본). 한 줄: *세상이 떠드는 "루프" 4단계를 G2는 이미 흩어진 채 전부 굴리고 있다(CAE=라이브 Loop 4). 부족한 건 루프가 아니라 **"검증(Loop 2)이 통과시킨 것만 자동화로 승격하는 규율."*** ARD = 개선 엔진이 아니라 **증거 엔진.**

---

## 세 가지 축 — 검증이 게이트다 (assess → **verify(GATE)** → improve)

```
 ① 파악·학습          →   ② 평가·검증 (게이트)   →   ③ 개선 (승격)
 Loop 3 스케줄 수확        Loop 2 계측기 증거        증거 통과분만 자동화(L1→L3→L4)
 "싸게 많이 줍는다"        "이게 진짜 효과 있나?"      "증명된 것만 손에 쥔다"
 ─────────────────        ─────────────────          ─────────────────
 ard-loop HARVEST          계측기 (측정)             CAR OrgDev (propose→증거→반영)
 + docs/insights (지식)    ⛔통과 못하면 여기서 폐기    git-sync (인프라 위생)
 + Claude-App-Factory      "스킬 vs 직접, 뭐가 나은가"  CAE (L4 작동 증명)
```

> **핵심:** 어떤 지식·스킬·조직변경도 **계측기식 증거를 통과하기 전엔 Loop 3/4(자율)로 못 올라간다.** ard-loop이 배선 상태로 멈춘 이유 = 증거 없이 Loop 3/4로 건너뜀(Karpathy 실패패턴 "Optimistic Path"). 상세·루프 매핑표: [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 하위 프로젝트 (통폐합 후)

### ① 파악·학습 — 외부 최신 현황을 흡수

| 프로젝트 | 설명 | 상태 |
|---------|------|------|
| **[ard-loop](./ard-loop/)** ⭐ | **CAR 자율학습 루프(플래그십·엔진).** 유튜브 자막·깃허브 → CAR(임원 에이전트)이 보고·이해 → G2 적용·검증·보고·자가개선. HARVEST→UNDERSTAND→APPLY→VERIFY→REPORT→HEAL 6단계. **YouTube·GitHub 수확기(HARVEST)를 흡수** — 아래 유튜브 트렉킹의 실행 코드가 여기 있음 | 🟡 코어 구현(Phase 2~3) · **라이브 루프 미검증**(설치·회장 승인 대기) |
| [agents/CAR.md](./agents/CAR.md) | CAR 임원 페르소나(ard-loop 소유자, 도구 트랙 + 조직 트랙) | ✅ |
| [Youtube-Tracking](./Youtube-Tracking/) (유튜브 트렉킹) | 유튜브 트렌드 지속 학습 **프로젝트 헌장 홈**(코드 아님, 코드는 ard-loop/harvester). | 🟢 헌장 |
| [ard-loop/docs/insights/](./ard-loop/docs/insights/) | **수확 인사이트 지식 자산.** 예: [2026-07-02 AI 루프·제2의뇌·로컬스택 4대 게시물](./ard-loop/docs/insights/2026-07-02_ai-loops-and-stacks.md)(개념→실현 스킬→G2 보유 매핑) | 🟢 축적 중 |
| [Claude-App-Factory](./Claude-App-Factory/) | leadgenman "솔로+AI 창업" 스택 → G2 MCP 매핑(설계·빌드·배포 파이프라인). 회장 80% 이미 보유 | 📐 문서+부트스트랩 |

### ② 평가·검증 — 효과가 진짜인지 증거로 확인 (ARD의 심장)

| 프로젝트 | 설명 | 상태 |
|---------|------|------|
| **[계측기](./Eval/)** (계측기) | **"에이전트 직접 수행 vs 스킬 명시호출, 뭐가 나은가"** 증거기반 A/B 연구. 블라인드 opus 심사 패널. **1차 결과(핵심): 스킬 강제의 평균 이득 +0.35/10 = 동전던지기(6승5패1무). 가장 강하게 의무화된 스킬(ponytail·ui-ux-pro-max)이 무승부·음수.** 최대 승자 systematic-debugging(+3.0)은 호출 ≈0. ★propose-only | 🟢 1차 완료 · 📐 3차 설계(회장 승인 대기) |

### ③ 개선 — 검증 결과로 조직·인프라를 손봄 (propose-only)

| 프로젝트 | 설명 | 상태 |
|---------|------|------|
| CAR **조직 트랙(OrgDev)** | ard-loop 안에 통합. G2 조직 스냅샷([docs/G2_ORG_STRUCTURE.md](./ard-loop/docs/G2_ORG_STRUCTURE.md)) ↔ 베스트프랙티스 대조 → 조직 개선 **제안만**(회장/Alpha 승인 후 Alpha 반영). 벤치마크: [ORG_BENCHMARK.md](./ard-loop/docs/ORG_BENCHMARK.md)(Mariah vs G2) | 🟢 1차 리뷰 완료 |
| **[git-sync](./git-sync/)** | 원격·로컬 단일 브랜치 동기화(모든 레포 공통) 글로벌 훅. 세션시작 자동 동기화 + 종료 미푸시 경고 | ✅ 구현·라이브검증 |

### 🗄️ 아카이브 (통폐합으로 격하)

| 항목 | 사유 |
|------|------|
| [Trend-Following-Youtube](./Trend-Following-Youtube/) | **레거시 RSS 텍스트 스크래퍼**(LLM 0, 비전의 10~15%만 달성). ard-loop 자막 파이프라인으로 **완전 대체**. 정직한 실패 기록 [VISION_VS_REALITY.md](./Trend-Following-Youtube/VISION_VS_REALITY.md)만 사료로 보존. 유튜브 트렉킹 아래 격하 |

---

## 통폐합 요약 (2026-07-02)

- **YouTube 3중복 정리:** `Youtube-Tracking`(헌장) + `Trend-Following-Youtube`(레거시) + `ard-loop/harvester`(코드) → **코드 단일화(ard-loop), 헌장 단일화(Youtube-Tracking), 레거시 아카이브.**
- **스택 인사이트 분리:** 신규 4대 게시물은 `ard-loop/docs/insights/`에 CAR 포맷으로 수확, `Claude-App-Factory`와 역할 분담(빌드 스택 vs 활용 루프).
- **개선 축 명시화:** CAR OrgDev + git-sync를 "③ 개선" 축으로 묶어 assess→verify→improve 서사 확립.

---

## 프로젝트 철학

> G2의 AI 팀은 스스로 **측정하고** 업그레이드한다.
> 사람이 매번 스킬을 찾아 설치하는 대신, CAR이 외부 지식을 보고 이해해 G2에 적용하고 — **무엇보다 그게 실제로 효과가 있는지 계측기가 증거로 검증한다.** 효과 없는 의무는 걷어내고, 효과 있는데 안 쓰이는 것은 라우팅한다(★반영은 회장 승인 후).

설치(회장 로컬 1회): `cd ard-loop/install && pwsh -File install.ps1`
