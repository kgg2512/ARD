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

## 5. 파일 구성

| 경로 | 역할 | 실행 위치 |
|------|------|----------|
| `config/sources.json` | 유튜브 채널 + 깃허브 레포/검색 + 신뢰출처 allowlist | → `~/.claude/ard/config/` |
| `harvester/car_harvester.py` | HARVEST(유튜브): RSS→자막→큐 | Task Scheduler 일 1회 |
| `harvester/car_github_harvester.py` | HARVEST(깃허브): 릴리스·커밋·트렌딩 검색→큐 | Task Scheduler 일 + **로그온** + SessionStart 인라인 |
| `hooks/car_dispatch.py` | UNDERSTAND 트리거(큐 surface). **세션 시작 시 깃허브 인라인 즉시 확인** | SessionStart |
| `hooks/car_supervisor.py` | 감독·평가·자가복구 | 스케줄/주기 |
| `notifier/car_notify.py` | **보고 폰 푸시(Telegram)** — Mariah 'Reports via Telegram' 이식 | supervisor·CAR 호출 |
| `templates/insight_template.md` | CAR 인사이트 구조 | CAR이 채움 |
| `VERIFY_CHECKLIST.md` | 설치 후 회장 검증 체크리스트 | 회장 1회 |
| `docs/ORG_BENCHMARK.md` | Mariah 조직도 vs G2 비교·개선 | 참고 |
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

- Python 3종은 원격 Linux에서 **`py_compile` 통과(문법 검증)**. 단 **유튜브 네트워크·자막 라이브러리·Claude 루프 라이브 테스트는 이 환경에서 불가**(유튜브 차단·lib 미설치·Claude 런타임 없음).
- **회장 첫 설치 후** harvester 1회 수동 실행(`python car_harvester.py --force`)으로 큐에 자막이 실제로 쌓이는지 확인 → 이상 시 보고하면 즉시 수정.
- 현재 버전 = Phase 2~3 코어(수확·이해·적용·기초 평가/감독). Phase 4(영상 멀티모달·GitHub 트렌딩 심화)는 후속.
</content>
