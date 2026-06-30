# 로컬 설치 체크리스트 — 노트북에 처음부터 구축

> 회장 환경 = **Windows / PowerShell** 기준. 0에서 시작해 "Claude 중심 앱 빌딩 시스템"을 로컬에 세운다.
> 회장은 G2에서 이미 대부분 구축돼 있으므로, 이 문서는 **새 노트북·새 환경에서 재현**하거나 **빠진 조각만 채울** 때 쓴다.

---

## 0. 사전 준비 (토대)

| 항목 | 설치/확인 | 비고 |
|------|----------|------|
| Node.js (LTS) | nodejs.org | npm 포함. MCP·Vercel·스킬의 기반 |
| Git | git-scm.com | worktree·버전관리 |
| Claude Code | `npm i -g @anthropic-ai/claude-code` 또는 공식 설치 | 시스템의 두뇌. Pro/Max 구독 필요 |
| GitHub 계정 | kgg2512 (보유) | 코드 저장소 |
| VS Code (선택) | code.visualstudio.com | 편집·터미널 |

확인:
```powershell
node -v ; git --version ; claude --version
```

---

## 1. MCP 서버 연결 (시스템의 신경망)

Claude Code 설정 파일(`settings.json` 또는 `~/.claude.json`)에 MCP 서버를 등록한다. **회장 G2엔 이미 등록돼 있음** — 새 환경에서만 필요.

핵심 5종(사진 스택 최소 구성):

| MCP | 역할 | 필요 인증 |
|-----|------|----------|
| `github` | 코드 저장·PR·이슈 | GitHub 토큰 |
| `vercel` | 배포 | Vercel 로그인 |
| `supabase` | DB·인증·스토리지 | Supabase 프로젝트 키 |
| `figma` (또는 `stitch`) | 디자인 | Figma 토큰 |
| `filesystem` | 로컬 파일 접근 | 없음 |

등록 예 (개념 — 실제 키는 각 서비스 대시보드에서 발급):
```jsonc
{
  "mcpServers": {
    "github":   { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                  "env": { "GITHUB_TOKEN": "ghp_..." } },
    "supabase": { "command": "npx", "args": ["-y", "@supabase/mcp-server-supabase"],
                  "env": { "SUPABASE_ACCESS_TOKEN": "sbp_..." } },
    "vercel":   { "command": "npx", "args": ["-y", "vercel-mcp"] }
    // figma, filesystem 등 동일 패턴
  }
}
```
> ⚠️ 키·토큰은 절대 git에 커밋 금지. `.env` / OS 환경변수로만.

연결 확인: Claude Code 재시작 후 `/mcp` 또는 도구 목록에 `mcp__supabase__*` 등이 보이면 성공.

---

## 2. 각 서비스 계정 (무료 티어)

| 서비스 | 가입 | 무료 한도 [추정·가입시 재확인] |
|--------|------|------|
| Supabase | supabase.com | 프로젝트 2개 |
| Vercel | vercel.com (GitHub 연동) | 취미 플랜 |
| PostHog | posthog.com (트래픽 생기면) | 월 100만 이벤트 |
| Dribbble | dribbble.com (열람만) | 무료 |

---

## 3. 병렬 빌드 (Conductor 대체, Windows)

Conductor는 Mac 전용이라 설치 안 함. 대신 git worktree로 동일 효과:

```powershell
cd C:\Users\kgg25\Desktop\myapp
git worktree add ..\myapp-A featureA   # 신기능용 격리 복사본
git worktree add ..\myapp-B bugfix     # 버그픽스용 격리 복사본
# 터미널 2개에서 각각 claude 실행 → 동시 작업, 충돌 0
```
+ Claude Code 내부 서브에이전트(Task/Agent) 병렬도 함께 활용.

---

## 4. 첫 앱 만들어 보기 (스모크 테스트 — 시스템이 도는지 확인)

Claude Code 안에서 자연어로:

```
1. "Next.js로 할 일 앱 만들어. Supabase로 로그인·데이터 저장."
   → Claude가 코드 작성 + supabase MCP로 테이블·인증 구성
2. "GitHub에 올리고 Vercel로 배포해."
   → Claude가 git push + vercel MCP로 배포 → 라이브 URL 반환
3. 그 URL 접속 → 동작 확인
```

이 3단계가 끝까지 돌면 **시스템 구축 성공**. (= 설계·빌드·백엔드·배포·버전관리가 한 줄 명령으로 연결됨)

---

## 5. 완료 기준 체크리스트

- [ ] `node -v` / `git` / `claude --version` 정상
- [ ] `/mcp` 에 github·supabase·vercel 최소 3종 연결 확인
- [ ] Supabase·Vercel 계정 생성 + 토큰 발급
- [ ] git worktree 병렬 1회 실습
- [ ] §4 스모크 테스트 앱이 라이브 URL로 배포됨
- [ ] (선택) 실사용자 트래픽 발생 시 PostHog 도입

---

## 6. 회장 맞춤 권고

회장은 **G2 환경에 이미 1~3번이 다 돼 있다.** 그러므로:
- 새 도구 설치 ❌ — 이미 보유.
- 진짜 할 일 = **§4 워크플로우를 의식적으로 한 사이클 돌려보고**, 막히는 지점(MCP 인증 만료 등)만 고치는 것.
- 새 노트북/새 직원 AI 셋업 시에만 이 문서를 0번부터 따라가면 됨.
</content>
