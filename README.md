# ARD — AI Resource Development

**G2 Company 내부 프로젝트 | AI 조직 역량 개선**

AI 에이전트(Alpha 등)의 도구·스킬·MCP를 자동으로 탐지·업그레이드해서 G2의 AI 운영 수준을 지속 향상시키는 내부 인프라 프로젝트.

---

## 하위 프로젝트

| 프로젝트 | 설명 | 상태 |
|---------|------|------|
| **[ard-loop](./ard-loop/)** ⭐ | **CAR 자율학습 루프(플래그십).** 유튜브 자막·깃허브 → CAR(임원 에이전트)이 보고·이해 → G2 적용·검증·보고·자가개선. HARVEST→UNDERSTAND→APPLY→VERIFY→REPORT→HEAL 6단계 | ✅ 코어 구현(Phase 2~3) |
| [agents/CAR.md](./agents/CAR.md) | CAR 임원 에이전트 페르소나(ard-loop 소유자) | ✅ |
| [Trend-Following-Youtube](./Trend-Following-Youtube/) | (레거시) RSS 텍스트 스크래퍼. ard-loop이 자막 기반으로 대체. [비전 vs 현실](./Trend-Following-Youtube/VISION_VS_REALITY.md) | 🟡 Phase 1 → ard-loop로 승계 |
| [Claude-App-Factory](./Claude-App-Factory/) | Claude 중심 로컬 앱 빌딩 시스템 아키텍처 + 실행 부트스트랩 | 📐 문서+스크립트 |

---

## 프로젝트 철학

> G2의 AI 팀은 스스로 업그레이드한다.
> 사람이 매번 스킬을 찾아서 설치하는 대신, **CAR이 유튜브·깃허브의 바이럴 지식을 보고 이해해서** G2에 자동 적용·검증·보고한다.

설치(회장 로컬 1회): `cd ard-loop/install && pwsh -File install.ps1`
