# Trend-Following-Youtube 🗄️ ARCHIVED (2026-07-02)

> **🗄️ 아카이브됨 — 이 프로젝트는 [ard-loop](../ard-loop/)으로 완전 대체됐다.**
> 레거시 RSS 텍스트 스크래퍼(LLM 0, 회장 비전의 10~15%만 달성). 자막 기반 이해 파이프라인이 아니라 "RSS 제목에서 패키지명 줍는 스크립트"였다.
> **살아있는 후속:** 코드=[`ard-loop/harvester/`](../ard-loop/harvester/) · 헌장=[`Youtube-Tracking/`](../Youtube-Tracking/) · 정직한 실패 사료=[`VISION_VS_REALITY.md`](./VISION_VS_REALITY.md).
> 이 폴더는 **사료(history)로만 보존.** 신규 작업 금지 — 유튜브 학습은 ard-loop에서.

---

**ARD 하위 프로젝트 | YouTube 트렌드 → AI 역량 자동 업그레이드**

Claude Code 스킬과 MCP 서버를 소개하는 YouTube 인플루언서 채널을 자동 모니터링해서,
신규 스킬/MCP가 감지되면 G2의 Claude Code 환경에 자동 설치한다.

---

## 동작 방식

```
[SessionStart, 하루 1회]
↓
YouTube RSS 피드 스캔 (4개 채널)
↓
Claude Code 관련 키워드 감지
↓
스킬/MCP 패키지명 추출
↓
자동 설치 → 보고 (없으면 완전 침묵)
```

## 모니터링 채널

| 채널 | 이유 |
|------|------|
| All About AI | Claude Code MCP/Skill 전문 채널 |
| Fireship | AI 트렌드 즉각 반응, 개발자 영향력 최대 |
| Dave Ebbelaar | MCP 실습 튜토리얼 |
| Liam Ottley | AI 에이전트 자동화 비즈니스 |

채널 추가/제거: `influencer_channels.json` 편집 또는 Alpha에게 요청.

## 파일 구성

| 파일 | 역할 |
|------|------|
| `influencer_monitor.py` | 메인 스캔·분석·설치 스크립트 |
| `influencer_channels.json` | 모니터링 채널 설정 |

## 설치 위치

```
~/.claude/hooks/influencer_monitor.py     ← SessionStart 훅으로 자동 실행
~/.claude/data/influencer_channels.json  ← 채널 설정
~/.claude/data/influencer_monitor_state.json  ← 상태(마지막 체크, 설치 이력)
~/.claude/data/influencer_monitor_log.jsonl   ← 감지·설치 로그
```

## 로그 확인

```bash
cat ~/.claude/data/influencer_monitor_log.jsonl
```
