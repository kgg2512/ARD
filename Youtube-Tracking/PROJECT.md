# 유튜브 트렉킹 (Youtube-Tracking)

> **ARD 내부 소규모 프로젝트 #1** | 회장 명명 2026-07-01
> 폴더명은 영문(`Youtube-Tracking`), 프로젝트 정식명은 **유튜브 트렉킹**.

## 무엇 (One-liner)
유튜브의 최신 AI/에이전트 트렌드를 **꾸준히 시청·이해·따라가고 G2에 적용**하는 지속 학습 프로젝트. "사람이 매번 찾아 설치"하는 대신 시스템이 스스로 배운다.

## 왜 (배경)
G2의 AI 역량을 복리로 끌어올리려면 외부 최신 지식이 계속 흘러 들어와야 한다. 유튜브는 에이전트·스킬·MCP 트렌드가 가장 빨리 도는 채널. 이 프로젝트는 그 흐름을 **자막 기반으로 수확→이해→적용**하는 파이프라인을 소유한다.

## 실행 코드 위치 (이 폴더는 프로젝트 헌장 홈 — 코드 중복 금지)
- **🟢 라이브:** [`../ard-loop/harvester/`](../ard-loop/harvester/) — 자막 기반 수확기(YouTube transcript). CAR 자율학습 루프의 HARVEST 단계. 2026-06-30 가동검증 PASS(자막 5건 수확).
- **🟡 레거시:** [`../Trend-Following-Youtube/`](../Trend-Following-Youtube/) — 초기 RSS 텍스트 스크래퍼. ard-loop 자막 방식으로 승계됨. [비전 vs 현실](../Trend-Following-Youtube/VISION_VS_REALITY.md).
- **보조:** claude-video-vision 플러그인(ffmpeg 프레임+whisper 자막→Claude 판독) — 자막 못 얻는 영상의 Phase 4 보조.

> 실행 코드는 ard-loop에 있고, **이 폴더는 프로젝트의 헌장·로드맵·학습로그 홈**(관리 계층/코드 계층 분리).

## 파이프라인
HARVEST(자막 수확) → UNDERSTAND(CAR 이해·요약) → APPLY(G2 적용 제안) → VERIFY(검증) → REPORT(회장 보고) → HEAL(자가복구)
🔒 공급망 게이트: 신뢰 출처 + 1K+ 만 자동 설치.

## 현황
- ✅ 자막 수확기 라이브 가동검증(2026-06-30)
- ⏳ 상주 설치(schtasks + settings.json SessionStart 훅) = 회장 승인 대기 (PC 가볍게 유지 원칙)
- 🟡 레거시 Trend-Following-Youtube 정리(아카이브 여부) 미결

## 소유
- 상위: [ARD](../README.md) / 임원: CAR
- 관련: [[project-ard]], [[reference-video-vision]]
