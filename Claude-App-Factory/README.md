# Claude App Factory — Claude 중심 로컬 앱 빌딩 시스템

**ARD 하위 프로젝트 | "솔로 창업가 + AI 한 명이 스타트업 전체를 만드는" 표준 아키텍처**

> 출처: leadgenman 인스타 캐러셀("I built my whole startup solo. Just me + AI") 분석 + G2 현재 MCP 스택 매핑.
> 목적: 회장이 **로컬 노트북에서 Claude를 중심으로 앱을 처음부터 끝까지 만드는 시스템**을 실제로 설치·운영할 수 있게 정리.

---

## 0. 한 줄 요약

**Claude = 두뇌. MCP = 신경망. 나머지 도구 = 손발.**
하나의 아이디어가 *설계 → 빌드 → 백엔드 → 배포 → 측정 → 개선*의 컨베이어 벨트를 타고 흐르며, 각 공정마다 전담 도구가 하나씩 붙는다. 사람은 "무엇을 원하는지"만 말하고, Claude가 도구들을 오케스트레이션한다.

---

## 1. 전체 파이프라인 (조립 라인)

```
                          ┌─────────────────────────────┐
                          │   Claude Code  (두뇌·중심)    │
                          │   - 코드 작성·수정            │
                          │   - 도구 오케스트레이션       │
                          │   - MCP로 모든 외부 도구 제어 │
                          └──────────────┬──────────────┘
                                         │  MCP (Model Context Protocol)
        ┌────────────┬───────────────┬──┴───────────┬───────────────┬──────────────┐
        ▼            ▼               ▼              ▼               ▼              ▼
   ① 설계        ② 병렬빌드        ③ 백엔드        ④ 배포          ⑤ 측정       ⑥ 버전관리
   Dribbble      Conductor        Supabase        Vercel          PostHog       GitHub
   (영감)        (멀티에이전트)   (DB·인증)       (라이브)        (분석)        (코드 저장)

   아이디어 ──▶ 디자인 참고 ──▶ Claude가 코드 작성 ──▶ DB 연결 ──▶ 배포 ──▶ 사용자 행동 측정 ──▶ 개선 루프
```

**핵심 사상:** 각 단계는 "한 가지만 잘하는" 도구 하나로 막힌다. 도구를 늘리는 게 아니라, 단계마다 **Claude가 그 도구를 대신 조작**하게 만드는 것이 이 시스템의 본질이다.

---

## 2. 구성 요소 (사진 기준 + 보강)

사진에서 직접 확인한 도구는 #2~#6. #1과 #7~#8은 보지 못해 [추정] 표기.

| # | 도구 | 공정 | 무엇 | 왜 | 무료 한도 | 회장 보유 여부 |
|---|------|------|------|-----|----------|---------------|
| #1 | **Claude Code** [추정] | 두뇌 | AI 코딩 에이전트. 자연어→코드, 도구 제어 | 시스템 전체의 중심. 나머지는 전부 Claude가 조작하는 손발 | Pro/Max 구독 | ✅ 보유·사용 중 |
| #2 | **Conductor** | 병렬 빌드 | Claude Code 에이전트 **여러 명**을 동시 구동. 각자 격리된 repo 복사본(git worktree)에서 작업 | "A는 신기능, B는 버그픽스"를 **동시에**. 충돌 0 | 무료(Mac 전용) | ❌ **회장=Windows, 사용 불가** → §5 대안 |
| #3 | **Dribbble** | 설계 | UI/UX 디자인 영감 갤러리 | 화면·카드·색상·레이아웃 참고. "남들은 어떻게 디자인했나" | 무료(열람) | ⚠️ 웹사이트 직접 사용. (G2엔 Figma·Stitch MCP가 더 강력) |
| #4 | **Supabase** | 백엔드 | Postgres DB + 인증 + 스토리지 + 실시간, 올인원 | "진짜 백엔드"가 필요할 때. 직접 서버 안 짜도 됨 | 무료 프로젝트 2개 | ✅ **supabase MCP 연결됨** |
| #5 | **PostHog** | 측정 | 세션 리플레이 + 제품 분석 + 에러 추적 + 기능 플래그 | 출시 후 "사용자가 실제로 어떻게 쓰나" 파악 | 무료 월 100만 이벤트 | ❌ **미보유 → 유일한 신규 도입 후보** |
| #6 | **Vercel** | 배포 | GitHub push → 전 세계 자동 빌드·배포 (수초) | 앱이 "실제로 라이브로 나가는" 곳 | 무료(취미) | ✅ **vercel MCP 연결됨** |
| #7~8 | (미확인) [추정] | — | 캐러셀 8장 중 못 본 슬라이드. 결제(Stripe)·이메일(Resend)·도메인 등일 가능성 | — | — | — |

> **결론:** 회장은 이 스택의 핵심을 **이미 80% 보유**하고 있다(MCP로 Vercel·Supabase·GitHub·Figma·Stitch 연결됨). 실제로 새로 필요한 건 ①Conductor의 Windows 대안 ②PostHog뿐. 자세한 매핑은 [STACK_MAPPING.md](./STACK_MAPPING.md).

---

## 3. MCP가 이 시스템의 심장인 이유

사진 속 모든 도구는 따로 놀면 그냥 "탭 10개"다. 이걸 **하나의 시스템**으로 묶는 접착제가 **MCP(Model Context Protocol)** 다.

- MCP 없이: 회장이 Supabase 콘솔 열고, 테이블 만들고, Vercel 대시보드 가서 배포하고… (사람이 도구마다 손으로 조작)
- MCP로: Claude에게 "이 앱에 사용자 테이블 만들고 배포해줘" → Claude가 `supabase MCP`로 테이블 생성, `vercel MCP`로 배포. **사람은 한 문장만.**

이게 "Claude 중심"의 진짜 의미다. 도구가 많은 게 핵심이 아니라, **모든 도구를 Claude가 대신 조작**하는 것이 핵심.

상세 설치·연결법: [SETUP_LOCAL.md](./SETUP_LOCAL.md)

---

## 4. 빌드 워크플로우 (실제 한 번 도는 사이클)

```
1. [설계]   "이런 앱 만들고 싶어" → Claude가 Dribbble/Figma 참고해 화면 구조 제안
2. [빌드]   Claude Code가 코드 작성 (큰 작업이면 Conductor/worktree로 병렬)
3. [백엔드] "사용자 로그인 필요해" → Claude가 supabase MCP로 DB·인증 구성
4. [버전]   Claude가 git commit + GitHub push
5. [배포]   push 즉시 Vercel이 자동 빌드·배포 → 라이브 URL
6. [측정]   PostHog가 사용자 행동·에러 수집
7. [개선]   "이탈률 높은 화면 고쳐줘" → 1번으로 루프
```

---

## 5. ⚠️ 회장 환경(Windows) 핵심 차이점

**Conductor는 Mac 전용 앱이라 회장은 못 쓴다.** (회장 환경 = Windows / PowerShell 5.1 — G2 CLAUDE.md 기준 [확인])
하지만 Conductor가 하는 일(= 여러 Claude 에이전트를 격리된 repo 복사본에서 병렬 구동)은 **Windows에서도 그대로 재현 가능**하다. Conductor는 git worktree 위에 입힌 GUI 껍데기일 뿐이기 때문.

→ Windows 대안과 재현 방법은 [STACK_MAPPING.md](./STACK_MAPPING.md) §"Conductor 대체" 참조.

---

## 6. 이 문서 묶음

| 파일 | 내용 |
|------|------|
| `README.md` (이 파일) | 전체 아키텍처·철학·파이프라인 |
| [`STACK_MAPPING.md`](./STACK_MAPPING.md) | 사진 스택 ↔ 회장 현재 G2 MCP 스택 1:1 매핑 + Windows 대안 |
| [`SETUP_LOCAL.md`](./SETUP_LOCAL.md) | 로컬 노트북에 처음부터 설치하는 단계별 체크리스트 |

---

## 7. 검증 메모 (정직성)

- **[확인]** 사진 #2~#6 5장의 텍스트는 직접 판독함. 도구명·역할·"Mac app"·무료성 일부는 사진 본문에 명시됨.
- **[추정]** #1(Claude Code)·#7~#8 슬라이드는 보지 못함. 무료 한도 수치(PostHog 100만/Supabase 2개 등)는 파라미터 지식 기반이라 도입 직전 공식 페이지 재확인 필요.
- **[확인]** 회장의 G2 MCP 보유 목록(vercel·supabase·github·figma·stitch)은 G2 CLAUDE.md settings.json 목록에서 확인.
</content>
</invoke>
