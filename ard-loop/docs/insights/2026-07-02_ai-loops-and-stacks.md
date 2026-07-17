# 인사이트 — 2026 AI 활용 4대 게시물: 루프·제2의뇌·로컬스택 (수동 수확)

> **수확 방식:** 회장이 인스타 캐러셀 4건을 스샷으로 전달 → Alpha가 판독·정리(2026-07-02). 인스타는 MCP 연결 불가라 자동 HARVEST 밖 → **수동 수확이지만 CAR 인사이트 포맷을 그대로 따른다.**
> **핵심 결론 한 줄:** 4건이 공통으로 가리키는 축 = **"좋은 프롬프트 쓰기 → 좋은 루프(자율 반복 + 자가검증) 설계하기"로의 이동.** 그리고 그 표준 엔진으로 **Claude Code + Obsidian식 마크다운 제2의뇌 + 로컬 음성/모델**이 반복 등장. **대부분 G2가 이미 보유 — 신규 도입보다 "가진 걸 의식적으로 쓰기"가 실질 갭.**

출처(4건):
1. **chrispathway** — "4 AI Projects you should build in 2026" (6장, 203k 팔로워)
2. **chase.h.ai** — "MEET JARVIS" (8장, 음성 AI 비서)
3. **gymcoding(짐코딩)** — "Claude Code팀이 정의한 루프 4단계" (9장, 한국어)
4. **teu.insight(티이유)** — "이제 프롬프트가 아니라 루프다 — Karpathy 10지침" (9장, 한국어)

---

## A. 게시물별 원문 요지 (판독 [확인] — 스샷 직접)

### A-1. chrispathway — 4 AI Projects
| # | 프로젝트 | 요지 | 원문 스택 |
|---|---------|------|----------|
| 1 | **AI Second Brain(제2의뇌)** | Claude에 나에 대한 모든 맥락을 색인·자동갱신으로 제공 → 매번 설명 불필요. Obsidian 페어링 | Claude Desktop, Obsidian |
| 2 | **Personal Assistant** | WhatsApp·Telegram·Gmail 안에 사는 AI 에이전트. 자체 메모리 + 예약 작업. 내 머신 구동("나만의 자비스") | OpenClaw / NanoClaw |
| 3 | **RAG of your Notes** | 내 PDF·노트·Obsidian을 먹여 **출처와 함께** 답하는 챗봇. 프로덕션 AI 표준 패턴 | Python, LlamaIndex, ChromaDB, Claude |
| 4 | **Local LLM** | 노트북 완전 오프라인. 구독·요청제한·유출 0. 모델 교체 | Ollama, Open WebUI, Llama/Qwen/R1 |

### A-2. chase.h.ai — JARVIS (음성 레이어)
- **구조:** JARVIS = **Claude Code(엔진, 요청 라우팅) + Obsidian(메모리, 결과 저장) 위에 얹은 음성 레이어.**
- 모든 요청이 Claude Code를 거침 → **그 순간 필요한 skill만** 꺼내 씀 (voice/·vault/·metrics/ `SKILL.md`).
- Obsidian = **Karpathy 시스템** 기반 마크다운 제2의뇌(raw/wiki/outputs), DB 없이 링크 그래프.
- **음성 100% 로컬:** 마이크 → `faster-whisper`(STT, 23.6k★) → `Kokoro`(82M TTS, 7.5k★). 프라이빗·사실상 무료.

### A-3. gymcoding — Claude Code 루프 4단계
Claude Code팀 정의: **"멈춤 조건이 충족될 때까지 반복하는 에이전트."** 핵심 = *"무엇을 사람이 넘기나"*:

| 단계 | 이름 | 사람이 맡기는 것 | 도구 |
|------|------|----------------|------|
| 1 | 턴 기반 (매번 확인) | 검수 | 맞춤 검증 `SKILL.md` |
| 2 | 목표 기반 (완료 정의) | 종료 조건 | `/goal` (예: "홈 Lighthouse 90↑, 5회 후 중단") |
| 3 | 시간 기반 (시간이 실행) | 트리거 | `/loop`(로컬) · `/schedule`(클라우드) |
| 4 | 능동형 (사람 없이) | 프롬프트 전체 | 위 전부 + 동적 워크플로우 |

루프 사이클: **prompt → gather context → take action → verify the work → response** (Claude가 완료 판단 or effort budget 소진 시 종료).

### A-4. teu.insight — Karpathy 10지침
- 패러다임: 프롬프트 1회 → AI가 스스로 목표·검증·반복하는 **자율 에이전트.**
- 기초 4: Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution.
- **신규 원칙 "스스로 검증하라":** "된 것 같다" 대신 **테스트 통과로 증명.**
- 규칙: 버그 고치기 전 재현 테스트 먼저 + 구체적 완료 조건 / 오류메시지 끝까지·한 번에 하나 / 모르는 건 모른다.
- **멈춤 실패패턴 3:** Kitchen Sink(과범위) · Optimistic Path(예외 무시) · 폭주 리팩터링.

---

## B. 개념 → 실현 스킬·구현방법 → G2 보유 여부 (핵심 매핑)

> 회장 지시("실현 스킬·구현방법을 정확히 정리"). 각 개념을 **무엇으로 구현하는가 + G2가 이미 가졌는가**로 정리.

| 게시물 개념 | 실현 스킬/도구/구현 | G2 현재 상태 | 갭 |
|---|---|---|---|
| **루프(멈춤조건까지 반복)** | Claude Code 네이티브 `/loop`·`/goal`·`/schedule` 슬래시커맨드 + effort budget | 🟢 **네이티브 보유**(이 세션 available). G2 헌법의 evaluator 루프(§작업지시서 4항)와 동일 계열 | 슬래시커맨드 **실사용 0회** — 헌법엔 개념만, 실제 `/loop`·`/goal` 발화 이력 없음 |
| **자가검증(스스로 검증하라)** | `verification-before-completion` 스킬 + G2 검증 하드게이트 + `g2-qa-tester` | 🟢 **이미 헌법 핵심.** "증빙 없는 완료는 없다" = 이 원칙의 G2판 | 스킬 자체는 계측기 미검증(3차 대상). 게이트는 살아있는 유일 자산 |
| **제2의뇌(색인·자동갱신 맥락)** | Obsidian 링크그래프 마크다운 + `CLAUDE.md`/`MEMORY.md`/mem0 | 🟡 **부분.** G2는 `wiki/`(마크다운 위키)+`memory/`+mem0 MCP로 **이미 Karpathy식 마크다운 제2의뇌를 운영 중** — Obsidian만 안 씀 | Obsidian 도입은 **불필요**(wiki+mem0가 동형). "자동갱신" 부분이 약함 |
| **RAG of Notes(출처 포함 응답)** | Python + LlamaIndex + ChromaDB(로컬 벡터DB) + Claude / 또는 mem0·pinecone MCP | 🔴 **미보유.** G2엔 로컬 벡터RAG 없음. mem0(의미검색)·firecrawl(웹)로 부분 대체 | 진짜 갭. 단 $0·로컬 구축 가능(Chroma 무료). **도입 가치 = 회장 문서량이 임계 넘을 때** |
| **로컬 LLM(오프라인)** | Ollama + Open WebUI + Llama/Qwen/DeepSeek-R1 + Docker | 🔴 미보유(회장=클라우드 Claude 사용) | 프라이버시·무제한 필요 시. 단 Opus 대비 품질↓ — 현 단계 도입 **음의 수익** |
| **로컬 음성(STT/TTS)** | `faster-whisper`(STT) + `Kokoro`(TTS) 로컬 | 🟡 **부분.** claude-video-vision 플러그인이 **로컬 whisper 강제**(영상 자막) — STT는 이미 로컬 보유 | 음성 *대화* 레이어(마이크→명령)는 없음. 회장 1인엔 우선순위 낮음 |
| **Personal Assistant(메신저 상주 에이전트)** | OpenClaw/NanoClaw + 메모리 + 예약작업 | 🟡 **부분.** hermes MCP(텔레그램·슬랙 등 메신저 브리지) + `car_notify.py`(텔레그램 푸시) + schtasks 예약 | 완전한 "메신저 안 상주 에이전트"는 미구현. hermes로 골격은 있음 |
| **skill-on-demand(그 순간 필요한 스킬만)** | Claude Code 스킬 지연로딩 + `find-skills` 자동발동 | 🟢 **네이티브 보유.** 이 세션도 600+ 스킬을 지연로딩 | ⚠️ **계측기 실증: 스킬 실호출 ≈ 0** — 메커니즘은 있으나 발화 안 됨 |
| **Stop 실패패턴(과범위·폭주 리팩터링)** | `ponytail`(YAGNI·최소코드) + Surgical Changes + `Dev Minimal Change Engineer` | 🟢 보유(ponytail 코딩 기본) | ⚠️ **계측기 실증: ponytail 무승부(0.0)** — 의무화가 품질을 안 올림 |

---

## C. G2 적용 판정 (APPLY — CSO 공급망 게이트 통과 여부)

> 자동설치 기준: 신뢰출처 allowlist + 1K+. 인스타发 지식이라 **자동설치 대상 없음** — 전부 판단·수동.

| 후보 | 판정 | 근거 |
|---|---|---|
| **`/loop`·`/goal`·`/schedule` 실사용 시작** | 🟢 **채택(도구 0 추가).** 네이티브 보유 | 반복 작업(PR 확인·CI·정기 감사)에 `/schedule` 적용은 즉시 가치. 회장 "루프 설계" 트렌드와 정합. **비용 0** |
| **로컬 RAG(Chroma+LlamaIndex)** | 🟡 **승인 큐(propose-only).** | $0 구축 가능하나 회장 문서량이 아직 mem0+wiki로 충분. 임계 도달 시 재검토 |
| **로컬 LLM(Ollama)** | 🔴 **기각(현 단계).** | Opus 대비 품질↓ + 회장 PC 경량 원칙 위반(모델 상주 GB). 프라이버시 요구 없음 |
| **Obsidian 제2의뇌** | 🔴 **기각.** | wiki+mem0가 동형 자산. 새 도구=중복. "wiki 자동갱신 강화"로 대체 흡수 |
| **음성 대화 레이어(whisper→kokoro)** | 🔴 **기각(현 단계).** | 회장 1인, 모바일-우선. 음성 대화 가치 < 복잡도. STT는 이미 로컬 보유 |
| **메신저 상주 에이전트(OpenClaw)** | 🟡 **부분 흡수.** | hermes MCP+텔레그램 푸시로 골격 존재. 완전 상주는 PC 경량 원칙과 긴장 → 보류 |

**결론:** 4개 게시물의 6~8개 아이디어 중 **G2가 이미 동형 보유 = 대부분.** 진짜 신규 갭 = ①`/loop`·`/goal`·`/schedule` **실사용**(도구 0, 습관 문제) ②로컬 RAG(문서량 임계 시). 나머지는 도입이 음의 수익. **이 인사이트의 값 = "새 도구 쇼핑 목록"이 아니라 "가진 걸 안 쓰고 있다는 진단."**

---

## D. Claude-App-Factory와의 관계 (통폐합)

이 인사이트의 **스택 축**(chrispathway 4프로젝트·JARVIS 스택)은 [`Claude-App-Factory`](../../../Claude-App-Factory/)의 leadgenman 스택 매핑과 **같은 성격**(외부 바이럴 스택 → G2 MCP 매핑). 중복을 피하려 역할 분담:
- **Claude-App-Factory** = "솔로창업 **빌드 파이프라인**"(설계→빌드→백엔드→배포→측정) 스택 매핑 소유.
- **이 인사이트** = "AI **활용 루프·제2의뇌·로컬** 패러다임" 소유 — 빌드 스택이 아닌 *작동 방식(loop)*·*지식 구조(second brain)* 축.
- 겹치는 도구(Claude Code·MCP·Supabase·Vercel)는 Claude-App-Factory가 정본. 이 문서는 **참조만** 하고 재기술하지 않음.

---

## E. 미결·한계 (정직)

- 인스타发 → **자동 VERIFY 불가**(수동 수확이라 supervisor 추적 밖). `/loop`·`/goal` 실사용은 회장/Alpha가 다음 반복 작업에서 발화해야 측정됨.
- 로컬 RAG·LLM의 "무료 한도/품질" 수치는 [추정] — 도입 직전 재확인.
- 이 문서는 **적용 지시가 아니라 판정.** 채택된 `/schedule` 실사용도 헌법 검증 게이트 그대로 적용.
