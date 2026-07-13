# 회장 승인 대기 — 2026-07-12 큐 배출

🔒 공급망 게이트: 아래 둘 다 `apply_policy.trusted_publishers` allowlist 밖(anthropics/anthropic-ai/modelcontextprotocol/vercel-labs/microsoft/supabase/cloudflare/stripe/upstash/github만 자동적용 허용) → **자동 설치 0건.** 회장 승인 또는 Alpha 검수 전까지 미설치.

## 1. oraios/serena — 시맨틱 코드 MCP 툴킷
- **무엇:** LSP 기반 코드 시맨틱 검색/편집 MCP 서버("에이전트용 IDE"). ⭐25926.
- **URL:** https://github.com/oraios/serena
- **왜 후보인가:** g2-cto/frontend/backend가 MyFit·welkor·cinderella·saju 등 대형 코드베이스에서 grep 대신 시맨틱 탐색 사용 시 탐색 토큰 절감 가능성.
- **미검증:** "plain grep+Read 대비 실제로 이기는가"(baseline gate)는 실측 안 함 — 설치 승인 시 1개 레포에 시범 적용 후 비교 권장.
- **리스크:** 신규 MCP = settings.json 변경(민감 파일) + 제3자(비신뢰 publisher) 코드 실행.
- **승인 시 조치:** settings.json에 MCP 추가(require_approval_for_settings_json=true 이미 걸려 있음) → g2-cto 1개 작업에 시범 사용 → 효과 실측 후 상시화 여부 재판단.

## 2. mukul975/Anthropic-Cybersecurity-Skills — 보안 스킬 팩(817개)
- **무엇:** MITRE ATT&CK/NIST CSF 2.0/MITRE ATLAS/D3FEND/NIST AI RMF/MITRE F3에 매핑된 구조화 보안 스킬 817개, agentskills.io 표준, Apache 2.0. ⭐23275.
- **URL:** https://github.com/mukul975/Anthropic-Cybersecurity-Skills
- **⚠️ 이름 주의:** 레포명의 "Anthropic-"은 owner(`mukul975`, 개인)가 Anthropic과 무관하게 붙인 이름 — **공식 제휴 아님**(미확인, 브랜드 혼동 소지). 승인 검토 시 이 점을 전제로 콘텐츠 품질을 독립 평가해야 함.
- **왜 후보인가:** ASD(내부 보안 R&D)·SAFE-AI(외부 보안 서비스) 스캐너 룰 개발에 참고 가치 — CISO 도메인 지식 과중(§1.5 매트릭스 "코어 엔진·보안" 행).
- **리스크:** 817개 스킬 전량 설치는 과도 — 부분 채택/참고자료로만 검토 권장. Apache 2.0이라 라이선스 리스크는 낮음.
- **승인 시 조치:** g2-ciso 또는 ASD 담당자가 콘텐츠 샘플 검토 → 실제 스캐너 룰에 참고할 항목만 선별 인용(전량 설치 아님).

---
**결정 대기 항목 = 2건.** 둘 다 즉시 자동 설치 없음, 회장/Alpha 승인 후 진행.
