# 조직 개선 제안: 실행자 에이전트 cold-start 도구 룩업 체크리스트 주입

> **이것은 제안서다. CAR은 조직/헌법을 직접 바꾸지 않는다. 회장/Alpha 승인 후에만 적용.**

- **작성:** CAR / **작성일:** 2026-06-30
- **벤치마크 출처:** ORG_BENCHMARK.md §2 갭 분석(Mariah 대비 G2 도구 활용률 0회 실증) + G2_ORG_STRUCTURE.md §5 자동화 3층 검증루프 + MEMORY.md "[도구 라우팅 맵 + 사용량 검증 루프]" 항목([확인]: 이 세션 파일 직접 Read)
- **현재 스냅샷 기준일:** 2026-06-30 (G2_ORG_STRUCTURE.md)
- **개선 유형:** ☑ **교육(Educate)** — 기존 실행자 에이전트의 시작 체크리스트 향상

---

## 1. 무엇이 문제/기회인가

### 현재 상태 ([확인])
- G2 헌법 CLAUDE.md에 "작업 유형→도구 자동매핑 표"가 존재한다.
- G2_ORG_STRUCTURE.md §5에 "검증=tool_usage_audit.py(0회 호출=라우팅 실패 탐지)"가 명시된다.
- MEMORY.md에 "스킬 449+가 사실상 0호출이던 것 감사로 적발", "gcal/drive/canva 연결됐으나 0회"가 기록돼 있다.

### 근본 원인 ([추정]: 구조 분석)
실행자 에이전트(g2-cto, g2-frontend-engineer, g2-backend-engineer 등)는 소환될 때 **자신의 페르소나 파일**(`C:\Users\kgg25\.claude\agents\*.md` 또는 동등 위치)만 로드한다. 이 파일들에는 **"작업 전 CLAUDE.md 매핑 표를 룩업하라"는 체크리스트가 없다.** CLAUDE.md가 있어도 실행자 cold-start 시 전체 헌법을 읽는 것은 비현실적(토큰 과다, 로드 보장 안 됨).

결과: 매핑 표는 **Alpha 브리핑 단계에서만 활성화**되고, 실행자가 독립 판단해야 할 순간(Alpha 브리핑 없이 직접 소환 또는 브리핑 불완전 시)에는 **도구 선택이 실행자 즉흥 판단**으로 떨어진다.

### 베스트프랙티스 대조
Mariah 조직의 핵심 철학: **"각 기능은 전용 도구 1개."** 각 역할이 자기 도구를 명확히 알고 있다. G2는 **도구가 있어도 실행자가 모르거나 빠뜨리는 구조** — 이 갭이 0회 호출로 나타났다.

**갭 유형: 교육 갭(Educate).** 도구는 있다. 매핑도 있다. 실행자가 시작할 때 자기 도구를 체크하는 습관(체크리스트)이 없다.

---

## 2. 구체적 제안

### 대상: 실행자 페르소나 파일 3개에 "작업 시작 체크리스트" 섹션 추가

**무엇을:**
g2-cto, g2-frontend-engineer, g2-backend-engineer 각 페르소나 파일 최상단(역할 정의 직후)에 **"## 작업 시작 체크리스트 (매 소환 필수)"** 섹션을 추가. 내용: 이 역할에 해당하는 도구 자동매핑 항목을 페르소나 파일 안에 **직접 박아** 넣는다(CLAUDE.md 읽기 의존 제거).

**대상 파일:**
```
C:\Users\kgg25\.claude\agents\g2-cto.md           (또는 동등 경로)
C:\Users\kgg25\.claude\agents\g2-frontend-engineer.md
C:\Users\kgg25\.claude\agents\g2-backend-engineer.md
```
> ⚠️ [추정]: 위 경로는 일반적 Claude Code 에이전트 파일 위치 추정. Alpha가 실제 경로 확인 후 반영 요망.

**변경 전 (현재 — g2-cto.md 상정):**
```markdown
# g2-cto

G2 Company 엔지니어링 총괄. 모든 코딩 작업의 1순위 실행 주체...
```

**변경 후:**
```markdown
# g2-cto

G2 Company 엔지니어링 총괄. 모든 코딩 작업의 1순위 실행 주체...

## 작업 시작 체크리스트 (매 소환 필수 — Alpha 브리핑 유무 불문)

1. **ponytail lite 기본 적용** — 요청대로 풀버전 빌드 + 더 게으른 대안 1줄 제시. `Skill("ponytail")` lite.
2. **Spec Kit 자동 발동 여부 확인** — 신규 화면/기능/다중파일(T4급)이면 `.specify/` 존재 확인 → 없으면 `specify init --here --integration claude --script ps --force`. 소형(4~20줄)·버그픽스는 제외.
3. **security-and-hardening** — 인증·결제·보안 변경이면 `Skill("security-and-hardening")` 자동 적용.
4. **verification-before-completion** — 중형+ 완료 전 `Skill("verification-before-completion")`.
5. **§1.5 도메인 주입 확인** — 🔒 유형(인증·결제·보안·개인정보·코어엔진) 포함 시 CTO+CSO 체크리스트 완료 기준에 명시 + 독립검증 의무.
6. **증빙 첨부** — 빌드/테스트 실행 출력. "완료 예정"·선언형 금지.
```

**g2-frontend-engineer.md 추가 내용:**
```markdown
## 작업 시작 체크리스트

1. **Stitch MCP + @21st-dev/magic** — 디자인 작업이면 `mcp__stitch__generate_screen_from_text` 호출.
2. **before/after 스크린샷** — UI 변경은 변경 전 스크린샷 먼저 캡처, 변경 후도 캡처 필수. console 0 확인.
3. **CDO 체크리스트** — 신규 화면은 CDO(디자인·접근성) 채점 기준 완료 조건에 명시.
4. **verification-before-completion** — 중형+ `Skill("verification-before-completion")`.
```

**g2-backend-engineer.md 추가 내용:**
```markdown
## 작업 시작 체크리스트

1. **Supabase/Cloudflare 작업이면 MCP 직접 호출** — `mcp__supabase__*` / `mcp__cloudflare__*`.
2. **실호출 증빙** — API 변경은 성공 1회 + 에러 1회 실호출 결과 필수.
3. **CISO+CSO 체크리스트** — 인증·결제 포함 시 즉시 명시 + 독립검증 의무.
4. **배포 증빙** — 라이브 URL 실접속 결과 첨부.
```

---

## 3. G2 제약 정합성 검사

- [x] **$0 예산:** 새 도구 불필요. 기존 스킬·MCP·헌법 규칙을 페르소나 파일에 복사하는 것뿐. **PASS**
- [x] **회장 1인:** 다인 협업 전제 없음. 실행자와 Alpha 사이의 자동화 개선. **PASS**
- [x] **반중간계층:** 새 라우터 계층 없음. 기존 실행자의 체크리스트 추가만. 1홉 구조 유지. **PASS**
- [x] **헌법 비대화 금지:** CLAUDE.md를 건드리지 않음. 변경 대상은 **전문가(실행자) 파일** — 헌법이 원래 지시하는 방향("디테일은 전문가 파일로"). **PASS**
- [x] **PC 경량:** 새 상주 프로세스 없음. 파일 텍스트 편집만. **PASS**
- [x] **검증 게이트 유지:** 체크리스트 자체가 verification-before-completion·증빙 의무를 재확인 — 게이트 강화 방향. **PASS**

**6항목 전부 PASS → 자가기각 없음.**

---

## 4. 예상 효과 vs 비용

**효과:**
- 실행자 cold-start 시 CLAUDE.md 의존 없이 핵심 체크항목 로드 → **도구 0회 호출 문제 구조적 감소**
- Alpha 브리핑이 불완전하거나 직접 소환 시에도 실행자가 자기 도구를 빠뜨리지 않음
- "ponytail lite 기본", "Spec Kit 발동 기준", "증빙 첨부 의무"가 매 소환마다 가시화 → 작업 품질 일관성 ↑
- 측정 방법: `tool_usage_audit.py` 호출 수 — 체크리스트 도입 전후 비교 가능

**비용/리스크:**
- 페르소나 파일 변경 → 에이전트 재로드 필요 (Claude Code 세션 재시작, 비용 낮음)
- 체크리스트가 너무 길면 실행자 첫 토큰 소비 증가 → 현재 제안은 6항목 이하로 간결하게 설계
- 자기참조 위험: 체크리스트가 헌법과 어긋날 경우 혼란 → Alpha가 반영 시 헌법 §1.5와 대조 검수 필요

**순 판정: 4/5**
"$0, 상주 0, 헌법 비대화 방향과 정합, 실증된 0회 호출 문제에 직접 대응." 반영 비용 < 1시간(Alpha 파일 수정). 효과는 매 세션 누적.

---

## 5. 🔒 적용 경로

- **민감도:** 에이전트 페르소나 파일 변경 — **민감** (G2_ORG_STRUCTURE.md §8: 에이전트 파일 수정 = 제안만·승인 후 Alpha 반영)
- **승인 필요:** 회장 승인 또는 Alpha 검수 → **Alpha가 직접 페르소나 파일 3개 수정**
- **먼저 확인:** Alpha가 실제 에이전트 파일 경로 확인(`.claude/agents/` 또는 `.claude/g2/` 하위), 기존 내용 Read 후 섹션 append
- **반영 후 검증:** 다음 g2-cto·g2-frontend 소환 시 체크리스트 섹션이 실행자 출력에 자연 반영되는지 확인. `tool_usage_audit.py` 1주 후 호출 수 변화 체크(CAE 감사 포함).

---

## 6. 원장 반영

`~/.claude/ard/applied.json` items[]에 아래 기록 예정:
```json
{
  "type": "org",
  "name": "executor-agent-tool-checklist",
  "source": "ORG_BENCHMARK.md + G2_ORG_STRUCTURE.md (CAR OrgDev 1차 리뷰 2026-06-30)",
  "applied_at": "2026-06-30",
  "decision": "proposed"
}
```

---

## 7. Alpha 검수 노트 (2026-06-30 — 독립 검증)

CAR의 제안을 Alpha가 실제 페르소나 파일(`.claude/agents/g2/g2-cto.md`)을 직접 Read하여 검수함. CAR은 탐색 상한 때문에 페르소나 파일을 못 읽고 [추정]으로 진행했으므로, 전제를 실측으로 교정한다.

**전제 정정 ([확인] — g2-cto.md 직접 Read):**
- CAR 주장 "실행자 페르소나에 시작 체크리스트가 **없다**"는 **과장.** g2-cto.md엔 이미 ① 5단계 엔지니어링 파이프라인(현실파악→설계→구현→자가검증→보고) ② 4단계 증빙 의무 ③ `<!-- G2-SKILLS-START -->` **자동주입 스킬표(22개)** ④ UI 디자인 툴 3단계 ⑤ 보안 규칙이 **이미 존재**한다.
- 따라서 "도구가 페르소나에 도달 안 함"이라는 진단은 부분적으로 **틀렸다** — 스킬은 이미 자동주입된다.

**그러나 진짜 갭은 좁게 실재:**
- 페르소나에 **없는 것** = ⓐ **ponytail lite 기본 적용**(헌법 코딩 기본값) ⓑ **Spec Kit 발동 기준**(T4급) ⓒ **§1.5 도메인 주입 의무**(🔒 유형). 이 3개는 CLAUDE.md에만 있고 실행자 cold-start에 안 박힌다 → CAR 제안의 **타당한 핵심**.

**Alpha 판정 — 방향 승인, 구현 방식은 축소·교정:**
1. CAR 제안대로 체크리스트를 **손으로 박지 말 것** → 이미 `<!-- G2-SKILLS-START/END -->` 자동주입 메커니즘이 있으므로 **그 생성기에 ⓐⓑⓒ 3줄을 추가**(또는 동형의 `<!-- G2-CHECKLIST -->` 블록 신설)해 **단일 소스 유지.** 손으로 박으면 CLAUDE.md ↔ 페르소나 **이중관리(drift)** — CAR도 §4에서 이 위험을 인지함.
2. 대상 경로 정정: `.claude/agents/g2/{g2-cto,g2-frontend-engineer,g2-backend-engineer}.md` ([확인] Glob).
3. 범위: 스킬표 재주입 불필요(이미 있음). **신규는 ⓐⓑⓒ 3항목뿐** → 변경 최소(헌법 효율·ponytail 원칙 정합).

**수정 순 판정: 3/5** (CAR 4/5에서 하향 — 전제 과장·기존 메커니즘 간과 반영. 단 좁힌 갭 ⓐⓑⓒ는 실제 가치 있음).

**상태: 회장 승인 대기.** 승인 시 Alpha가 자동주입 생성기 경유로 ⓐⓑⓒ만 반영(검증 게이트·§1.5 대조 적용).
