# ARD Loop — CAR 자율학습·자가발전 시스템

**소유자: CAR (Chief of AI-agent Resources)** — G2의 AI 에이전트 자원 담당 임원.
**한 줄 정의:** 유튜브·깃허브에 바이럴되는 AI 에이전트/오케스트라/스킬/MCP/1인 스타트업 자동화 지식을 CAR이 **보고·이해**하고, G2에 **적용·구현**하고, **검증·평가**하고, 회장께 **보고**하고, 문제는 **자가개선**하는 닫힌 루프.

> 이 문서 = 이 시스템의 작업지시서(단일 진실 원천). 원격 환경에 `specify` CLI가 없어 Spec Kit 대신 본 설계서가 spec 역할.

---

## 0. 왜 유튜브인가 (회장 근거)

AI 오케스트라/에이전트를 쓰는 주체도, 그걸 홍보·바이럴하는 주체도 **사람**이다. 사람에게 가장 편한 바이럴 매체 = **영상.** 회장이 영상을 가장 많이 보는 인스타는 **MCP/API 연결 불가**. 반면 유튜브는 **API 연결 가능 + 자막 풍부** → 텍스트로 CAR의 이해도를 높이기에 최적. (영상 자체가 필요할 땐 회장 로컬의 video-reading 스킬을 Phase 4에서 보조 활용.)

GitHub도 1급 소스 — 릴리스·awesome 목록·트렌딩 레포에서 신규 스킬/MCP/패턴을 잡는다.

---

## 1. 6단계 파이프라인

```
   [HARVEST]        [UNDERSTAND]        [APPLY]           [VERIFY]         [REPORT]        [HEAL]
   car_harvester ─▶ CAR(Claude) 읽고 ─▶ 신뢰출처=자동   ─▶ 설치/연결    ─▶ 회장 다이제 ─▶ supervisor
   유튜브 RSS       구조화 인사이트     그 외=승인 큐      실제 됐나·       스트 보고       주기 점검·
   →자막→큐         (template 채움)                       호출되나 평가                    stale 자가복구
   (Python·LLM 0)   (LLM)              (CAR)             (CAR+감사훅)     (CAR/MCP)       (Python)
```

| 단계 | 주체 | 산출물 | 비용 |
|------|------|--------|------|
| **HARVEST** | `car_harvester.py` (Python, LLM 0) | `~/.claude/ard/queue/<id>.json` (자막 포함) | $0 |
| **UNDERSTAND** | CAR (Claude) | `docs/insights/<날짜>_<slug>.md` (구조화 인사이트) | LLM |
| **APPLY** | CAR | 스킬/MCP 설치·CLAUDE.md 룰 제안. `applied.json` 원장 | LLM |
| **VERIFY** | CAR + 기존 `tool_usage_audit` | 적용 항목별 PASS/FAIL (설치됨? 실제 호출됨?) | LLM |
| **REPORT** | CAR (옵션 Notion/Slack MCP) | `docs/reports/<날짜>_digest.md` | LLM |
| **HEAL/감독** | `car_supervisor.py` (스케줄) | `~/.claude/ard/reports/<날짜>_health.json` + 회장 플래그 | $0 |

**핵심 분리 원칙:** *수확(Harvest)은 싸야 하니 Python·LLM 0.* *이해/적용/평가는 판단이니 CAR(Claude).* 이전 `influencer_monitor`가 "RSS 정규식"에 머문 이유가 이 분리 부재였다.

---

## 2. 🔒 보안 — 자동적용의 공급망 게이트 (CSO 핵심)

> ⚠️ 유튜브 자막에서 뽑은 **임의 패키지를 자동 설치 = 공급망 공격 표면.** (기존 influencer_monitor는 아무 `-mcp` 패키지나 settings.json에 자동 추가했음 — 구멍.)

**규칙 (config `trusted_publishers`):**
- **자동 적용 허용:** 신뢰 출처(`anthropics`, `modelcontextprotocol`, `vercel-labs`, `microsoft`, `supabase`, `cloudflare` 등 allowlist) + 설치수 1K+ 만.
- **그 외 전부 = 회장 승인 큐** (`docs/reports`에 "승인 대기"로 적고 자동 설치 금지).
- 설치 전 CAR은 패키지명을 npm 실재 확인. settings.json 수정은 백업 후.

---

## 3. 자동화 = 스케줄 + 자가감독 (회장 정의 충실)

회장 정의: *"특정 시점/시간에 이 시스템이 잘 도는지 관리·감독·평가하고, 보고하고, 문제 시 개선·보완."*

- **HARVEST 스케줄:** Windows Task Scheduler 일 1회(`install.ps1`이 등록) — Claude 세션 없이도 자막이 쌓인다.
- **UNDERSTAND 트리거:** SessionStart 훅 `car_dispatch.py` — 큐에 N개 쌓이면 회장 세션 시작 시 "CAR 소환해 처리" 지시 자동 주입(G2의 cae_autostart 패턴과 동일).
- **감독/평가/자가복구:** `car_supervisor.py`(주 1회+) — harvester가 멈췄는지, 큐가 적체됐는지, **적용한 스킬/MCP가 실제로 호출되는지(0회=적용 실패)**, 적용물이 여전히 건강한지 점검 → 건강 리포트 + 문제 플래그 → stale하면 harvester 자가 재실행.

---

## 4. CAR — 신설 임원

- **역할:** AI 에이전트 자원(스킬·MCP·워크플로우·오케스트라 패턴) 담당 임원. ARD 루프 전체 소유.
- **소환:** Alpha가 ARD 큐 처리·정기 보고 때 1홉 소환(`Agent("CAR")`). 페르소나 = `ARD/agents/CAR.md`.
- **G2 조직 등록:** `wiki/wiki/agents/org-chart.md`에 등재(회장 직속 비동급 아님 — Alpha 산하 도메인 소유 전문가).
- **검증 하드게이트 면제 없음:** CAR이 G2에 적용하는 변경도 §1.5 도메인 주입·검증 게이트·CAE 감사 그대로 적용.

---

## 4.5 조직 트랙 (OrgDev) — CAR이 G2 조직 자체를 개선

> 회장 지시(2026-06-30): "G2 조직구조를 ARD에 올리고, CAR이 그걸 토대로 G2를 계속 교육·개발·개선하라."

도구 트랙(외부 지식→G2 스킬·MCP)과 **별개의 두 번째 사명.** 같은 6단계 루프를 **'조직 렌즈'로 재사용**한다 — 새 파이프라인 없음.

- **입력(정본):** `docs/G2_ORG_STRUCTURE.md` = G2 현재 조직 스냅샷(헌법+org-chart 동기화). Alpha가 G2 헌법 개정 시 갱신.
- **3렌즈:** **교육**(기존 에이전트 프롬프트·체크리스트 향상) · **개발**(조직 공백 메울 신규 에이전트·역할 신설) · **개선**(라우팅·검증 게이트·구조 리팩토링).
- **🔒 propose-only (핵심 안전 경계):** CAR은 조직/헌법/페르소나 파일을 **직접 수정하지 않는다.** `docs/org_proposals/<날짜>_<slug>.md` 제안서만 작성 → **회장 승인 또는 Alpha 검수 → Alpha가 반영.** 자동 적용 0. 헌법 자기개정 폭주를 구조로 차단.
- **제약 정합성:** 모든 제안은 $0 예산·회장 1인·반중간계층·헌법 비대화 금지·PC 경량·게이트 약화 금지를 통과해야 함(못 하면 CAR 스스로 기각).
- **cadence(계속 보장):** `car_supervisor.py`가 마지막 조직 리뷰로부터 **7일** 경과 시(큐레이터 7일과 정합) `~/.claude/ard/org_state.json`에 `due=true` → `car_dispatch.py`가 SessionStart에 "CAR 소환해 조직 리뷰"를 surface(**도구 큐와 독립**). 새 상주 프로세스 없음 — 기존 주기 실행 재사용.
- **절차 상세:** `../agents/CAR.md` "조직 리뷰 절차(OrgDev)". 출력=`docs/reports/<날짜>_org_digest.md` + 폰 푸시.

## 5. 파일 구성

| 경로 | 역할 | 실행 위치 |
|------|------|----------|
| `config/sources.json` | 유튜브 채널 + 깃허브 레포/검색 + 신뢰출처 allowlist | → `~/.claude/ard/config/` |
| `harvester/car_harvester.py` | HARVEST(유튜브): RSS→자막→큐 | Task Scheduler 일 1회 |
| `harvester/car_github_harvester.py` | HARVEST(깃허브): 릴리스·커밋·트렌딩 검색→큐 | Task Scheduler 일 + **로그온** + SessionStart 인라인 |
| `hooks/car_dispatch.py` | UNDERSTAND 트리거(큐 surface). **세션 시작 시 깃허브 인라인 즉시 확인** | SessionStart |
| `hooks/car_supervisor.py` | 감독·평가·자가복구 | 스케줄/주기 |
| `notifier/car_notify.py` | **보고 폰 푸시(Telegram)** — Mariah 'Reports via Telegram' 이식 | supervisor·CAR 호출 |
| `templates/insight_template.md` | CAR 인사이트 구조(도구 트랙) | CAR이 채움 |
| `templates/org_improvement_template.md` | CAR 조직 개선 제안서 구조(조직 트랙) | CAR이 채움 |
| `VERIFY_CHECKLIST.md` | 설치 후 회장 검증 체크리스트 | 회장 1회 |
| `docs/G2_ORG_STRUCTURE.md` | **G2 조직 스냅샷(정본) — 조직 트랙 입력** | Alpha 갱신 |
| `docs/org_proposals/` | CAR 조직 개선 제안서(propose-only) | CAR이 생성 |
| `docs/ORG_BENCHMARK.md` | Mariah 조직도 vs G2 비교·개선(씨앗) | 참고 |
| `install/install.ps1` | 의존성·복사·스케줄(로그온 포함)·훅 배선 | 회장 1회 |
| `../agents/CAR.md` | CAR 페르소나·처리 지시 | Claude 소환 |

**"노트북 켜면 바로 깃허브 확인" 보장 (이중):** ① Task Scheduler `ONLOGON` 트리거 ② SessionStart 훅이 깃허브 stale(12h+) 시 인라인 즉시 실행 → 큐 갱신 → CAR 소환 지시 주입. 유튜브 자막은 느려서 백그라운드.

운영 데이터(큐·상태·로그·헬스) = `~/.claude/ard/` (git 비추적, ephemeral).
지식 자산(인사이트·다이제스트) = **이 레포 `docs/`** (git 추적, 회장이 본다). CAR이 커밋.

---

## 6. 설치 (회장 로컬, 1회)

```powershell
cd <ARD>\ard-loop\install
pwsh -File install.ps1
```
→ `youtube-transcript-api` 설치 + 스크립트 비치 + Task Scheduler 등록 + SessionStart 훅 배선 안내.

## 7. ⚠️ 검증 상태 (정직)

- **✅ 2026-07-09 Push→Pull 개편 구현:** `pull/car_pull.py`(큐 키워드 조회 프리미티브, LLM0·네트워크0) 신설 — 실제 34건 큐로 검증 PASS(쿼리 'agent memory'→스코어 67/6/5 랭킹, 매치0 폴백). `car_dispatch.py`를 "전량 처리 강권"→"실작업이 당길 때 조회" 안내로 전환. 소비 경로가 push(적체)→pull(당김)로 바뀜. **주의: 큐/스크립트는 존재하나 dispatch·supervisor 상주 배선은 여전히 Step3(install.ps1, 회장 로컬) 대기.**

- **🔴 2026-07-09 실측 자기진단(RED — 루프 정체):** 수확 45건 대기 / 처리 12 / 적용 **1**(도구트랙 **0**) / 소화율 **21%** / 최근적용 8일 전. **수확(입력)은 도는데 이해→적용→검증(출력)이 멎음 = '자기발전'이 아니라 '저장'.** 원인 ①비싼 판단 팔이 수동 CAR 소환에 묶임(안 불리면 큐만 쌓임) ②감독관(schtasks) 미상주로 자체가 9일 안 돎.
- **자기검증 업그레이드(이 세션):** `car_supervisor.py`·`ard_gov_check.py`에 **loop_health 자가점검** 추가 — liveness('스크립트 돌았나')가 아니라 **outcome 대리지표('소화·적용됐나')**로 정체를 FAIL/RED 판정 → SessionStart 표면화 + 폰 푸시. 정체를 조용히 넘기던 구조를 시끄럽게 만듦(회장 질문 "스스로 검증"의 답).
- **남은 진짜 과제(회장 결정 대기):** (a)ARD를 **세션트리거 배치**로 정직하게 재정의(상주 0·소화 상한 N건·무가치 큐 폐기 정책), 또는 (b)경량 스케줄 자기점검 1개 승인. 어느 쪽이든 다음 액션 = **CAR 소환해 상위 3건 배치 소화**로 도구트랙 첫 적용·검증 실증.
- Python 3종은 원격 Linux에서 **`py_compile` 통과(문법 검증)**. 단 **유튜브 네트워크·자막 라이브러리·Claude 루프 라이브 테스트는 이 환경에서 불가**(유튜브 차단·lib 미설치·Claude 런타임 없음).
- **회장 첫 설치 후** harvester 1회 수동 실행(`python car_harvester.py --force`)으로 큐에 자막이 실제로 쌓이는지 확인 → 이상 시 보고하면 즉시 수정.
- 현재 버전 = Phase 2~3 코어(수확·이해·적용·기초 평가/감독). Phase 4(영상 멀티모달·GitHub 트렌딩 심화)는 후속.
</content>
