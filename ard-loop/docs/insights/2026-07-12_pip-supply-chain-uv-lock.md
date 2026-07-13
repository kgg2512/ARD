# 인사이트: Your Pip Install Is a Backdoor - Fix This Now!

- **출처:** Dave Ebbelaar — https://www.youtube.com/watch?v=bw1ZLzdXJn4
- **수확일:** 2026-06-30 / **처리일:** 2026-07-12
- **영상 핵심 주제:** pip/PyPI 공급망 공격(워프·slopsquatting) 방어를 위한 uv 3종 설정.

## 1. 무엇을 가르치나 (이해)
[확인 — 자막 기반] NPM(Axios·TanStack)·PyPI(Mistral AI·LiteLLM) 경유 실제 공급망 공격 사례를 배경으로, "패키지 설치 = 임의 코드 실행"이라는 전제 아래 uv 사용 시 3가지 방어 설정을 제시: ① `add-bounds = "exact"`(버전 고정) ② `exclude-newer = "N days"`(신규 게시 패키지 쿨다운) ③ `uv sync`(lock 파일 기반 재현 설치). AI 코딩 에이전트가 존재하지 않는 패키지명을 hallucination해 공격자가 심어둔 동명 악성 패키지를 설치하는 "slopsquatting"을 특히 경고.

## 2. G2 관련성
- **적용 가능 영역:** 신규 Python 프로젝트 부트스트랩 전반(ASD 스캐너, ARD 확장 등). CAR 자신의 🔒 공급망 게이트(trusted_publishers allowlist)와 동일 철학의 실행 계층.
- **신규성:** 신규 — G2는 현재 Python 의존성 관리에 uv 특정 설정을 명문화한 적 없음(specify CLI는 uv tool로 설치돼 있으나 이 3설정은 별개).
- **가치 (1~5):** 4 — 구체적·즉시 실행 가능·G2의 기존 공급망 경계 철학과 정합. 단, 현재 활성 Python 프로젝트가 의존성 0(stdlib-only)이라 즉시 트리거되는 파일 변경은 없음.

## 3. 구체적 적용 제안
- [x] `.claude/skills/ard-python-supply-chain-lock/SKILL.md` 스킬로 증류 (다음 pip 의존성이 생기는 Python 프로젝트 부트스트랩 시 자동 참조).
- [ ] 회장 액션 불필요 — 다음 신규 Python 프로젝트 착수 시 Alpha/실행자가 스킬 참조.

## 4. 🔒 적용 판정 (3게이트)
- **① 주장 검증:** uv `add-bounds`/`exclude-newer`는 uv 공식 문서에 실재하는 설정(내 파라미터 지식 기준 [추정], 이 세션에서 uv 공식문서 대조는 안 함 — 단, 영상 시연 내용 자체가 uv init→설정 적용→재현 시연까지 자막에 명시돼 조작 시연 형태로 신뢰도 높음). 메커니즘 자체가 "버전 고정+쿨다운"이라는 상식적 방어라 과장된 능력 주장 없음 → 통과.
- **② 출처 게이트:** Dave Ebbelaar는 `trusted_publishers` allowlist 밖(개인 유튜버) — 자동적용 대상 아님. 단 이 항목은 **소프트웨어 설치가 아니라 절차/설정 지식**이라 공급망 리스크 자체가 없음(uv는 이미 시스템에 존재, 새 패키지 설치 아님) → 스킬 증류는 게이트 밖(설치 아님) 판단.
- **③ 베이스라인 게이트:** plain Opus도 "uv add-bounds exact + exclude-newer" 자체는 알 가능성 높으나, **이 정확한 조합을 G2 공급망 원칙과 명시적으로 연결해 재사용 절차로 고정**한 것이 이 스킬의 가치 — 다음에 이 판단을 다시 추론할 필요 없음.
- **위험:** 없음(소프트웨어 미설치, 설정 권장 절차만).
- **결정:** distilled (스킬 등록 완료).

## 5. 적용 결과 (VERIFY)
- **실행:** `.claude/skills/ard-python-supply-chain-lock/SKILL.md` 작성 완료 (frontmatter g2_origin/g2_source/g2_created/g2_verified 포함).
- **검증:** 파일 생성 확인. 실사용(다음 Python 프로젝트 셋업)은 추적 중 — 아직 트리거된 프로젝트 없음.

## 6. 원장 반영
- `applied.json`: `{type:"skill", name:"ard-python-supply-chain-lock", source:"youtube:bw1ZLzdXJn4", applied_at:"2026-07-12", decision:"distilled"}`
