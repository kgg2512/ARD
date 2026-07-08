# 인사이트: anthropics/claude-plugins-official — 공식 Claude Code 플러그인 마켓플레이스

- **출처:** GitHub(anthropics 공식 org) — https://github.com/anthropics/claude-plugins-official
- **수확일:** 2026-06-30 / **처리일:** 2026-07-09
- **핵심 주제:** Anthropic이 직접 큐레이션·품질/보안 검증하는 공식 Claude Code 플러그인 디렉토리(커뮤니티 `npx skills` 인덱스와는 별개 채널).

## 1. 무엇을 가르치나 (이해)
[확인] (WebFetch로 README 직접 확인, 2026-07-09): `anthropics/claude-plugins-official`은 Anthropic이 운영하는 공식 Claude Code 플러그인 마켓플레이스다. 구조는 `/plugins`(Anthropic 자체 개발·유지) + `/external_plugins`(파트너·커뮤니티, 제출폼 경유 심사)로 나뉘고, 플러그인은 "품질·보안 기준"을 통과해야 등재된다. 설치는 `/plugin install {name}@claude-plugins-official` 또는 `/plugin > Discover` 브라우징으로 이뤄진다(G2가 현재 쓰는 `npx skills add`와는 다른 네이티브 경로). MCP 서버 구성·다중 스킬 번들도 포함 가능. 단 README 자체가 "Anthropic이 MCP서버/파일/소프트웨어 내용을 전부 검증하진 않는다"는 신뢰 경고를 명시 — external_plugins는 무조건 안전하다는 뜻은 아님.

## 2. G2 관련성
- **적용 가능 영역:** ARD 하베스트 소스 설정(`ard-loop/config/sources.json`) — 향후 스킬/플러그인 발굴 채널.
- **신규성:** **신규.** G2의 현행 스킬 발견 경로는 `npx skills find/add`(커뮤니티 인덱스, CLAUDE.md 스킬 자동탐색 의무 절 참조)뿐이며, Anthropic 자체 공식 마켓플레이스는 watch 대상에도 CLAUDE.md 도구매핑표에도 없었다(이번 GitHub 트렌딩 스캔에서 우연히 1회 포착됐을 뿐, 상시 추적 안 됨).
- **가치 (1~5): 3** — 특정 플러그인 하나를 당장 채택할 근거는 없지만(콘텐츠 목록까지는 확인 안 함), "신뢰 채널 자체를 지속 관찰"하는 구조적 가치가 있음. 회장이 겪은 "스킬 449+가 사실상 0호출"(reference-tool-routing-audit.md) 문제의 근본 원인 중 하나 = 커뮤니티 인덱스 과잉·신뢰도 낮은 롱테일. 공식 채널을 별도로 관찰하면 더 높은 신뢰도의 후보만 선별 가능.

## 3. 구체적 적용 제안
- [x] **ARD 자체 하베스트 소스 등록** — `ard-loop/config/sources.json`의 `github.watch_repos`에 `anthropics/claude-plugins-official` 추가 완료(이 세션에서 실행). 앞으로 이 레포에 새 플러그인이 올라오면 ARD 큐에 자동 포착됨.
- [ ] **G2 CLAUDE.md 도구매핑표 반영 여부** — CAR 권한 밖(ARD 레포 외부 수정 금지, 헌법 §5 CLAUDE.md 수정은 민감파일). Alpha가 검수 후 "스킬 자동 탐색 의무" 절에 "공식 마켓플레이스(`/plugin > Discover` 또는 `claude-plugins-official`)도 신뢰 우선순위로 병행 확인" 1줄 추가할지 판단 필요.
- [ ] 특정 플러그인 설치는 **아직 없음** — 마켓플레이스 존재 자체를 등록한 것이지, 개별 플러그인 자동설치는 하지 않음(공급망 게이트 유지).

## 4. 🔒 적용 판정 (3게이트)
- **① 주장 검증 (claim gate):** [확인] — WebFetch로 README 직접 확인. "공식·큐레이션·품질검증" 주장은 과장 없이 레포 구조(plugins/external_plugins 분리, 제출폼, 설치 커맨드)로 뒷받침됨. 단 "external_plugins가 전부 안전"이라는 주장은 없음(README 자체가 경고) — 과장 아님, 그대로 채택.
- **② 출처 게이트 (supply-chain):** PASS — `anthropics` 공식 org, `apply_policy.trusted_publishers`에 이미 등재된 최상위 신뢰 퍼블리셔. 스타 31,338 (>1,000 기준 충족).
- **③ 베이스라인 게이트 (핵심):** PASS(제한적) — "이 채널의 존재를 알고 지속 관찰"하는 것은 plain Opus 단일호출이 우연히 알 가능성보다 명확히 낫다(G2 스킬 발견 경로가 커뮤니티 인덱스 하나로 편중된 실측 문제를 완화). 다만 **특정 플러그인 채택 우위**는 아직 검증 안 됨(콘텐츠 목록 미확인) — 그래서 "채널 등록"만 적용하고 "개별 플러그인 설치"는 하지 않음.
- **위험:** 낮음. 설치 아님, 단순 하베스트 watch 대상 추가. 비용 $0.
- **결정:** **applied** (ARD 자체 config 반영 한정). G2 CLAUDE.md 반영은 별도 승인 큐.

## 5. 적용 결과 (VERIFY)
- **실행:** `ard-loop/config/sources.json` → `github.watch_repos`에 `"anthropics/claude-plugins-official"` 추가. Edit 성공(diff 확인).
- **검증:** 파일 재확인 결과 배열에 정상 반영됨(추가 항목 1건, 기존 5건 보존). 실제 신규 플러그인 포착은 다음 하베스트 주기(12h)에 확인 필요 — "추적 중".

## 6. 원장 반영
- `applied.json`에 기록: `{type: "mcp", name: "anthropics/claude-plugins-official (watch source)", source: "github.com/anthropics/claude-plugins-official", applied_at: "2026-07-09", decision: "applied"}`
