# 스택 매핑 — 사진 스택 ↔ 회장 G2 보유 스택

> leadgenman 사진 속 도구를, 회장이 **이미 G2에 연결해 둔 것**과 1:1로 대조한다.
> 핵심 메시지: **새로 살 게 거의 없다. 이미 가진 걸 의식적으로 쓰면 된다.**

---

## 1. 1:1 매핑 표

| 공정 | 사진 도구 | 회장 G2 현재 대응 | 상태 | 액션 |
|------|----------|------------------|------|------|
| 두뇌 | Claude Code | Claude Code (Alpha 운영체제) | ✅ 동일·가동 중 | 없음 |
| 설계 | Dribbble | **Stitch MCP** + **Figma MCP** + `ui-ux-pro-max` 스킬 | ✅ 더 강력 | Dribbble은 영감용 웹열람만, 실제 생성은 Stitch/Figma |
| 병렬 빌드 | Conductor (Mac) | git worktree 병렬 (G2 CLAUDE.md에 이미 규정) | ⚠️ 도구는 없음, 기법은 있음 | §3 Windows 대안 |
| 백엔드 | Supabase | **supabase MCP** | ✅ 동일·연결됨 | 그냥 쓰면 됨 |
| 배포 | Vercel | **vercel MCP** | ✅ 동일·연결됨 | 그냥 쓰면 됨 |
| 버전관리 | (GitHub) | **github MCP** | ✅ 연결됨 | 그냥 쓰면 됨 |
| 측정 | PostHog | ❌ 없음 | ❌ 미보유 | §4 도입 검토 |

**판정:** 7개 공정 중 5개를 회장이 **이미 동일하거나 더 강한 형태로 보유**. 실질 갭은 **Conductor 대안**과 **PostHog** 둘뿐.

---

## 2. 회장이 추가로 더 가진 것 (사진엔 없지만 G2엔 있음)

사진의 스택은 "최소 솔로 창업 스택"이다. 회장의 G2는 이미 그보다 넓다:

- **Cloudflare MCP** — Workers 배포 (Vercel 외 옵션, 사주팔자가 이걸 씀)
- **Notion / Gmail / Google Calendar / Slack MCP** — 운영·협업 자동화 (사진 스택엔 전무)
- **Higgsfield / Canva / Figma MCP** — 이미지·영상·디자인 생성
- **mem0 MCP** — 세션 간 메모리
- **Spec Kit** — 명세 주도 개발(바이브 코딩 방지)
- **C레벨 검증 게이트 + CAE 감사** — 사진 속 솔로 창업가에겐 없는 품질 안전망

→ 즉 회장의 시스템은 사진보다 이미 **상위 호환**이다. 이 문서의 가치는 "새 도구 쇼핑"이 아니라 **이미 가진 MCP를 사진처럼 한 줄로 꿰는 워크플로우 의식화**에 있다.

---

## 3. Conductor 대체 (Windows) — 가장 중요한 갭

**Conductor의 본질:** 여러 Claude Code 에이전트를, 각자 **격리된 repo 복사본**에서 동시에 굴려 충돌 없이 병렬 작업. GUI는 그 위에 입힌 껍데기일 뿐.
**회장 환경:** Windows라 Conductor 앱 자체는 설치 불가 [확인 — Mac 전용].
**그러나** 그 기능은 회장이 **이미 G2 헌법에 보유**하고 있다:

> G2 CLAUDE.md §1: *"인터페이스(파일 경계·API 계약)를 먼저 문서로 고정한 진짜 독립 모듈만 worktree 병렬 허용 — 같은 파일 접촉 0 + 머지·통합 검증은 Alpha 단일 게이트."*

재현 방법 (Windows / PowerShell):

```powershell
# 1) 메인 repo에서 작업별 격리 복사본(worktree) 생성
git worktree add ../myapp-featureA featureA
git worktree add ../myapp-bugfix   bugfix

# 2) 각 폴더에서 별도 Claude Code 인스턴스 실행 (터미널 2개)
#    → A는 신기능, B는 버그픽스를 동시에. 서로의 파일 안 건드림.

# 3) 완료 후 머지 + 통합 검증은 한 곳(Alpha 게이트)에서
git merge featureA
git worktree remove ../myapp-featureA
```

추가로 Claude Code 자체의 **서브에이전트 병렬 실행**(Task/Agent 도구)이 Conductor의 "여러 에이전트 동시" 욕구를 이미 상당 부분 충족한다. 즉 **Conductor 없이도 회장은 병렬 빌드가 가능**하다 — GUI 편의만 포기.

---

## 4. PostHog — 유일한 진짜 신규 도입 후보

사진 스택에서 회장이 **유일하게 안 가진 카테고리 = 제품 분석(measure)**.

- **무엇:** 세션 리플레이(사용자 화면 녹화) + 클릭/전환 분석 + 에러 추적 + 기능 플래그
- **왜 중요:** 회장 프로젝트(MyFit·신데렐라·welkor 등)가 실제 사용자를 받기 시작하면 "어디서 이탈하는지"를 눈으로 봐야 개선 루프가 돈다. 지금은 이 눈이 없음.
- **무료 한도:** 월 100만 이벤트 [추정 — 도입 시 공식 재확인]
- **MCP:** 현재 G2에 PostHog MCP 미연결. 도입 시 스니펫 한 줄을 앱에 심는 것부터 시작(MCP 없이도 작동).
- **대안:** Vercel Analytics(이미 보유) / Supabase 로그로 최소 측정은 가능. PostHog는 "제대로 측정"이 필요할 때.

> 권고: 지금 당장 도입 X. **첫 프로젝트가 실사용자 트래픽을 받는 시점**에 도입. 그 전엔 측정할 데이터가 없어 무의미.

---

## 5. 한눈에 보는 우선순위

1. **지금 당장 가능 (도구 0개 추가):** Stitch+Figma(설계) → Claude Code(빌드) → Supabase MCP(백엔드) → GitHub MCP(버전) → Vercel MCP(배포). **이미 전부 연결됨. 의식적으로 한 줄로 꿰기만 하면 됨.**
2. **필요 시 (Windows 대안):** git worktree 병렬 = Conductor 대체.
3. **나중에 (트래픽 생기면):** PostHog 도입.
</content>
