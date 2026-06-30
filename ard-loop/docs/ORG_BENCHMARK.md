# 조직 벤치마크 — Mariah Brunner vs G2

> 출처: @itsmariahbrunner "Meet the Team Running my 2 Ecommerce Brands & Social Media" (인스타, 1.4K좋아요).
> 솔로 창업가가 **각 역할을 특정 도구에 매핑**하고 Claude를 Co-Founder(두뇌)로 두는 조직도. G2와 비교해 개선점 도출·구현.

---

## 1. Mariah의 조직도 (역할 = 도구)

| 계층 | 역할 | 도구 |
|------|------|------|
| 창업 | Founder / **Co-Founder** | Mariah / **Claude** |
| 인프라 | Build in / Lives in / **Reports via** | Claude Code / OpenClaw / **Telegram** |
| 임원 | Head of Knowledge | Notion |
| | Email Marketer | Klaviyo |
| | Paid Ad Creative | Higgsfield |
| | Engineer | Codex |
| | Head of Growth | Meta(광고) |
| | Head Researcher | Perplexity |
| | Head of Competitor Intel | Apify |
| 실무 | Community Manager | ManyChat |
| | Designers | Claude Design · Nano Banana · Gamma |
| | Voice Input | Wispr Flow |
| | Meeting Notetaker | Granola |

**철학:** 사람은 의도만, **각 기능은 전용 도구 1개**, Claude가 오케스트레이션, 결과는 **폰(Telegram)으로 푸시**.

---

## 2. G2와의 차이 (그녀 ↔ 회장)

| 항목 | Mariah | G2 | 판정 |
|------|--------|-----|------|
| 두뇌·오케스트레이션 | Claude | Alpha(Claude) + 실행 에이전트 | G2 우위(검증 게이트·CAE) |
| 빌드 | Claude Code | Claude Code | 동등 |
| **보고 채널** | **Telegram 푸시(폰)** | 파일(회장이 열어야 함) | ❌ **G2 열위 — 최대 갭** |
| 엔지니어링 | Codex 1개 | g2-cto/frontend/backend + 리뷰/QA | G2 우위 |
| 디자인 | Claude/NanoBanana/Gamma | Stitch+Figma+ui-ux 스킬 | 동등+ |
| 리서치 | Perplexity | firecrawl/arxiv/deep-research | 동등+ |
| **경쟁사 인텔** | **Apify(전담)** | 없음(CSO는 렌즈만) | ❌ **G2 공백** |
| **그로스/마케팅 실행** | Klaviyo·Meta·ManyChat | CMO는 렌즈만, 실행 도구 없음 | ❌ **G2 공백(구조)** |
| 지식 관리 | Notion(전담) | Notion 연결됐으나 미활용 | 🟡 G2 보유·미가동 |
| 음성/회의록 | Wispr·Granola | 없음 | 🟡 낮은 우선순위 |

---

## 3. 개선점 & 구현 결정

### ✅ 구현함 (이번 작업, $0)
1. **Reports via Telegram (최대 갭 해소).** `notifier/car_notify.py` 신설 — ARD 보고·감독 결과를 회장 폰으로 푸시. supervisor·dispatch가 자동 호출. 회장은 모바일-우선(인스타 스샷도 폰) → 보고가 파일에 갇히던 구조를 폰 푸시로 전환. **이게 스크린샷의 1등 교훈.**
2. **경쟁사 인텔 공백 → 기존 자산으로 메움.** G2엔 이미 `ads-competitor` 스킬(설치됨)이 있다. CLAUDE.md 라우팅에 "경쟁사 광고·인텔" 행 추가 → CSO 렌즈가 죽은 렌즈에서 **실행 도구**를 갖게 됨. (Apify는 유료 → 무료 스킬로 대체.)

### 🟡 구조만 정의(가동은 회장/매출 시점)
3. **그로스/마케팅 실행 레인.** Mariah의 Klaviyo·Meta·ManyChat은 **유료 + 매출 전제.** G2는 $0·pre-revenue라 지금 도입은 음의 수익. → org-chart에 "그로스 실행 레인"을 **구조로만** 명시하고, 무료 대체(이메일=Resend 무료티어, 커뮤니티=직접)부터, 유료는 **매출 발생 시** 켜기로 플래그.
4. **Notion 지식 동기화 가동.** Notion MCP는 연결됐으나 미활용(G2 감사 확인). 정식 보고·인사이트를 Notion에 미러링하는 건 ARD 다이제스트가 안정화된 뒤.

### ❌ 채택 안 함 (현 단계 부적합)
5. **Wispr(음성)·Granola(회의록)·OpenClaw.** 회장은 1인이라 회의록 불필요, 음성입력은 개인 취향 영역. 도입 가치 < 복잡도.

---

## 4. 한 줄 결론

> Mariah는 **폭(마케팅·그로스·경쟁사까지 도구 풀세트)**이 강하고, G2는 **깊이(엔지니어링·검증·거버넌스)**가 강하다.
> 회장이 당장 취할 것 = **그녀의 'Reports via Telegram'(구현 완료)** + **경쟁사 인텔 가동(구현 완료)**.
> 그로스 도구 풀세트는 매출이 생기면 — 지금 $0에 Klaviyo 켜는 건 그녀를 흉내내다 비용만 쓰는 짓.
</content>
