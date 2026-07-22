# 조직 개선 제안: evaluator 루프 재시도 시 세션 지속(SendMessage 재개) 명시 — 콜드스타트 손실 완화

> **이것은 제안서다. CAR은 조직/헌법을 직접 바꾸지 않는다. 회장/Alpha 승인 후에만 적용.**

- **작성:** CAR / **작성일:** 2026-07-22
- **벤치마크 출처:** 이번 세션 ARD 큐 소화 중 확인한 2건의 실제 근거 —
  1. YouTube `wCSPgHpcxdc`(AI Jason, "Tmux + Fable = Cut 35% less token") — 매번 새 stateless subagent를 스폰하면 컨텍스트를 처음부터 다시 읽어 토큰을 낭비하고, 상시세션(persistent sidekick)을 유지해 prompt-cache를 재활용하면 비용이 줄어든다는 실측 주장(2차 출처, ARD `evicted/`가 아니라 `queue/`에 APPLY 대기로 남겨 L3 프로브 검증 대기 중).
  2. GitHub `anthropics/claude-code` v2.1.212 릴리스 노트(신뢰 출처, 이번 세션 확인) — "Reduced token usage in inter-agent messaging: SendMessage bodies are no longer duplicated into replayed history" + `/fork`가 대화를 새 백그라운드 세션으로 복제하는 기능을 공식 지원. 즉 하네스 자체가 세션 지속·재개를 1급 기능으로 이미 제공.
  3. 이 세션의 Agent 도구 설명 자체에 명시된 문구: "To continue a previously spawned agent, use SendMessage with the agent's ID... A new Agent call starts a fresh agent with no memory of prior runs." — 즉 **콜드스타트 회피 메커니즘이 하네스에 이미 있는데, G2 헌법 §3(evaluator 루프)이 이를 쓰라고 명시하지 않음.**
- **현재 스냅샷 기준일:** `G2_ORG_STRUCTURE.md` 2026-06-30 (§3 검증 하드게이트 절 확인) + 원본 CLAUDE.md §3 2026-07-22 확인(1회, stale 여부 대조 완료).
- **개선 유형:** ☑교육(Educate) ☐개발(Develop) ☐개선(Improve)

## 1. 무엇이 문제/기회인가

G2 헌법 §1은 위임의 핵심 비용을 이미 정확히 진단한다: **"핸드오프마다 콜드스타트로 맥락 재구매"·"모든 위임은 의도의 손실 압축"**. 그런데 이 진단이 실제로 반복 위임이 가장 많이 발생하는 지점 — **§3의 evaluator 루프("FAIL = evaluator 루프... 재구현 → 재검증을 PASS될 때까지 반복")** — 에는 처방으로 이어지지 않는다. 현재 §3 절차는 "실행자에 단순화 프롬프트로 재시도"라고만 되어 있고, 그 재시도가 **같은 에이전트 세션을 이어가는지(SendMessage로 재개) vs 매번 새 Agent()를 스폰하는지**를 구분하지 않는다.

이번 세션에 확인된 사실 3건(위 벤치마크 출처)이 공통으로 가리키는 것: 하네스(Claude Code)는 이미 세션 재개(SendMessage-to-agent-id, `/fork`, 백그라운드 세션)를 1급 기능으로 제공하고, 신뢰 출처(anthropics 공식 릴리스)도 이 방향(inter-agent 메시징 토큰 중복 제거)으로 계속 개선 중이다. G2는 이 기능을 "쓰라"고 명시한 적이 없어, 기본값이 매 재시도마다 새 Agent() 스폰(=파일 재탐색·컨텍스트 재구매)으로 흐를 위험이 있다 — 정확히 §1이 경계하는 그 비용이다.

## 2. 구체적 제안 (실행 가능하게)

- **무엇을:** `docs/VERIFICATION_SYSTEM.md`(§3 검증 하드게이트 상세 문서, CLAUDE.md는 이미 "검증 시스템 전체: docs/VERIFICATION_SYSTEM.md"로 위임 중)의 evaluator 루프 절에 1문단 추가: "같은 실행자를 재시도시킬 때는 새 Agent() 호출 대신, 가능하면 SendMessage로 기존 에이전트 세션을 재개해 파일 재탐색·컨텍스트 재구매 비용을 피한다. 격리가 필요한 T1(탐색 과중) 트리거처럼 '깨끗한 컨텍스트'가 목적 자체인 경우는 예외."
- **대상 파일:** `docs/VERIFICATION_SYSTEM.md` (root `CLAUDE.md` 무변경 — 헌법 비대화 금지 준수)
- **변경 전후:**
  - 전: (evaluator 루프 절에 재시도 방식에 대한 언급 없음 — "재구현 → 재검증 반복"만 서술)
  - 후: 위 1문단 추가. 기존 문장·구조는 그대로 두고 예외 조건(T1 격리 목적)까지 포함해 과잉 일반화 방지.

## 3. G2 제약 정합성 검사 (필수)

- [x] **$0 예산:** 신규 유료 도구 없음. 하네스 기존 기능(SendMessage) 재사용.
- [x] **회장 1인:** 다인 협업 전제 아님.
- [x] **반중간계층:** 라우터·피라미드 신설 없음. 1홉 구조 그대로.
- [x] **헌법 비대화 금지:** root `CLAUDE.md` 0줄 변경. `docs/VERIFICATION_SYSTEM.md`(이미 존재하는 전문 문서)에만 1문단.
- [x] **PC 경량:** 새 상주 프로세스 없음. SendMessage는 이미 켜져 있는 세션의 재개일 뿐.
- [x] **검증 게이트 유지:** evaluator 루프의 "PASS까지 반복"·"2회 반복 시 접근법 전환" 원칙 불변, 재시도의 *구현 방식*만 명시.

## 4. 예상 효과 vs 비용 (정직)

- **효과:** evaluator 루프 재시도 시 파일 재탐색·브리핑 재주입 토큰이 줄어듦(정확한 %는 미실측 — 근거 자체가 2차 출처 클레임이라 [추정]). 정성적으로는 §1이 이미 경계한 "콜드스타트 재구매"를 재시도 경로에서도 일관되게 회피.
- **비용/리스크:** ①SendMessage 재개는 이전 세션의 오염된 가정을 그대로 이어갈 위험(잘못된 접근법이 "새 컨텍스트"로 초기화 안 됨) — 그래서 "2회 반복 시 접근법 전환"(이미 §3에 있음) 시점엔 새 Agent()로 리셋하는 편이 나을 수도 있음, 문구에 명시 필요. ②토큰 절감 수치 자체가 이번 세션엔 미검증(claim_verifier 미통과 상태로 ARD 큐에 APPLY 대기) — 효과를 과장하지 않고 "관행 명시"로만 제안.
- **순 판정:** 3/5 — 방향은 근거 있고 비용 0이나, 정량 효과가 아직 [추정]이라 "권장 문구 추가" 수준의 낮은 리스크·낮은 확정효과 제안. 도입 가치가 비용을 넘지만 크지 않음.

## 5. 🔒 적용 경로 (절대 자동 아님)

- **민감도:** 검증 하드게이트 문서 수정 — Alpha 검수 필요(게이트 약화 아님을 확인해야 함, §3 원칙 문구 그대로 유지 확인).
- **승인 필요:** 회장 승인 또는 Alpha 검수 → Alpha가 직접 `docs/VERIFICATION_SYSTEM.md`에 반영. CAR은 파일 직접 수정하지 않음(propose-only).
- **반영 후 검증:** 다음 evaluator 루프 발생 시 Alpha가 실제로 SendMessage 재개를 썼는지 execution_log에 한 줄로 남기면, 채택률을 사후 확인 가능(ARD L4 check_adoption과 유사한 논리).

## 6. 원장 반영

- `~/.claude/ard/applied.json` items[]에 `{type:"org", name:"evaluator-loop-session-persistence", source:"CAR OrgDev 2026-07-22 (wCSPgHpcxdc + claude-code v2.1.212 + Agent tool 문서)", applied_at:"2026-07-22", decision:"proposed"}` 기록.
- `~/.claude/ard/org_state.json`의 `last_review` → 2026-07-22, `due` → false 갱신.
