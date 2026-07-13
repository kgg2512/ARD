# 인사이트 배치: 큐 배출 2026-07-12 — A등급 나머지 5건

50건 pending 큐 전량 처리(1회성 소비) 중 pip/uv 항목(별도 파일 `2026-07-12_pip-supply-chain-uv-lock.md`) 외 A등급 5건. 각 항목 = GitHub 트렌딩 레포(메타데이터+description만 확보, 딥 README 미독).

---

## gh-repo-hesreallyhim-awesome-claude-code (⭐47632)
- **무엇:** Claude Code용 스킬·훅·슬래시커맨드·에이전트 오케스트레이터·플러그인 큐레이션 리스트.
- **G2 관련성:** Claude Code가 G2의 핵심 실행 도구 — 향후 스킬/훅 발굴 채널로 가치.
- **적용:** `ard-loop/config/sources.json`의 `github.watch_repos`에 추가 완료(다음 하베스트부터 커밋 추적) — 신규 소프트웨어 설치 아님, 저위험.
- **결정:** insight + watch_repos 등재.

## gh-repo-punkpeye-awesome-mcp-servers (⭐90027)
- **무엇:** MCP 서버 큐레이션 리스트(대형).
- **G2 관련성:** 신규 MCP 발굴 채널.
- **신규성:** **중복 — 이미 `sources.json` watch_repos에 등재돼 있었음**(확인: 기존 목록에 이미 포함). 이번 큐 항목(trending_repo 재포착 + 별도 commit 추적 항목 `gh-com-punkpeye-awesome-mcp-servers-040b77d`)은 이미 아는 채널의 재수확 — 액션 불요.
- **결정:** insight only (신규 액션 없음, 이미 커버됨). commit 추적 사본은 C등급으로 evict.

## gh-repo-PrefectHQ-fastmcp (⭐25883)
- **무엇:** Python MCP 서버/클라이언트 구축 표준 프레임워크(Prefect사).
- **G2 관련성:** G2는 현재 기존 MCP를 *연결*만 하고 *자체 MCP 서버를 만들지 않음*(ASD/SAFE-AI가 향후 자체 API를 MCP로 노출한다면 후보).
- **가치:** 참고 지식으로 보관, 즉시 실행 액션 없음(트리거된 프로젝트 없음).
- **결정:** insight only. `pending_approval`에는 올리지 않음(승인 요청할 실사용 결정이 아직 없음 — 결정 없는 항목을 승인 큐에 넣는 건 노이즈).

## gh-repo-oraios-serena (⭐25926)
- **무엇:** 코딩 에이전트용 시맨틱 코드 검색/편집 MCP 툴킷("에이전트용 IDE") — LSP 기반.
- **G2 관련성:** g2-cto/frontend/backend가 대형 코드베이스(MyFit·welkor·cinderella·saju)에서 grep 대신 시맨틱 탐색을 쓸 수 있으면 탐색 토큰 절감 가능성.
- **🔒 출처 게이트:** publisher `oraios`는 `trusted_publishers` allowlist 밖 → 자동설치 불가.
- **③ 베이스라인 게이트 [추정, 미검증]:** "plain grep+Read보다 실제로 이기는가"는 이 세션에서 실측 안 함 — 승인 후 실제 사용해봐야 판정 가능.
- **결정:** pending_approval (회장 승인 대기, `20260712_pending_approval.md` 등재).

## gh-repo-mukul975-Anthropic-Cybersecurity-Skills (⭐23275)
- **무엇:** MITRE ATT&CK/NIST CSF/D3FEND 등 6개 프레임워크에 매핑된 817개 구조화 보안 스킬 팩(agentskills.io 표준, Apache 2.0).
- **⚠️ 이름 주의 [확인]:** 레포명에 "Anthropic-"이 붙어 있으나 owner는 `mukul975`(개인)이지 Anthropic 공식이 아님 — Anthropic 제휴/승인 여부 미확인. 이름만으로 신뢰 격상하면 안 됨(브랜드 혼동 리스크, `trusted_publishers`에 mukul975는 없음).
- **G2 관련성:** ASD(내부 보안 R&D)·SAFE-AI(외부 보안 서비스) 프로젝트의 스캐너 룰 개발에 참고 가치 — CISO 도메인.
- **결정:** pending_approval, CISO/ASD 리뷰 시 **①이름의 비공식성 명시** 필수 조건으로 등재.

---

## 부가 발견 (harvester 개선 여지, [확인])
- `insight_template.md`가 언급하는 `owner_trusted`/`star_suspect` 플래그는 **큐 항목 raw JSON에 실재하지 않음**(7건 샘플 검사, 필드=id/source/kind/title/channel/url/published/harvested_at/status뿐). 스타 수 기반 자동 신뢰 신호는 harvester가 아직 부착 안 함 — 이번 배출은 수동으로 `sources.json.apply_policy.trusted_publishers`만 대조. **[제안, 실행 안 함]** harvester가 owner를 allowlist와 대조해 플래그를 미리 부착하면 다음 배출이 더 빨라짐 — CAR 소관 밖(harvester는 Python 자동화, Alpha 승인 후 별도 작업).

## 원장 반영
- `applied.json`에 각 항목 `{type, name, source, applied_at:"2026-07-12", decision}` 기록 (스크립트로 일괄 append, 본문 하단 참고).
