# bootstrap/ — 노트북 켜면 바로 적용되는 자동 설치

사진 스택에서 회장에게 빠져 있던 두 조각(**Conductor 대체 = git worktree**, **PostHog = 측정**)을
**실행 가능한 형태**로 만든 폴더. 문서가 아니라 돌리면 적용된다.

---

## 한 번만: 설치

새 노트북/새 환경에서 ARD 레포를 받은 뒤, 이 폴더에서:

```powershell
cd <ARD경로>\Claude-App-Factory\bootstrap
pwsh -File bootstrap.ps1        # 또는 PowerShell에서  .\bootstrap.ps1
```

이게 하는 일:
1. `git`/`node`/`claude` 설치 여부 점검
2. 스크립트 3종을 `$HOME\.g2\` 에 비치
3. PowerShell `$PROFILE` 에 worktree 헬퍼를 등록 → **이후 모든 새 터미널에서 자동 로드** (= "노트북 켜면 바로")
4. 현재 세션에도 즉시 로드

멱등(idempotent) — 여러 번 실행해도 중복 등록 안 됨.

> ⚠️ 실행 정책 막히면(스크립트 차단): `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 한 번.

---

## 매일: git worktree (Conductor 대체)

repo 안에서:

```powershell
wtnew featureA          # ../<repo>-featureA 에 격리 복사본 + featureA 브랜치
wtnew bugfix -Open      # 생성하면서 새 터미널에서 claude 자동 실행
wtls                    # worktree 목록
wtmerge featureA        # featureA를 현재 브랜치에 머지 + worktree 정리
wtrm featureA           # 머지 없이 제거
```

→ "A 터미널은 신기능, B 터미널은 버그픽스"를 **동시에**, 서로 파일 안 건드리고. Conductor의 핵심 기능을 GUI 없이 Windows에서 그대로.

---

## 필요할 때: PostHog (측정)

PostHog 계정·프로젝트 생성 후 Project API Key(`phc_...`)를 들고:

```powershell
& "$HOME\.g2\add-posthog.ps1" -ProjectPath C:\Users\kgg25\Desktop\myapp -ApiKey phc_xxx
```

- Node 프로젝트면 `posthog-js` 설치 + init 파일 자동 생성 (Next.js는 `instrumentation-client.js`, 그 외 `posthog.js`)
- 정적 HTML이면 스니펫을 출력 → `<head>`에 붙여넣기

> PostHog는 외부 계정·키가 있어야 하므로 100% 무인 자동화는 불가. 다만 위 한 줄이면 끝.
> 키는 **런타임 인자**로만 받는다 — 레포·스크립트에 하드코딩 안 함(보안). PostHog 프로젝트 키는 원래 프론트에 노출되는 공개 키라 init 파일에 들어가는 건 정상.

---

## 파일

| 파일 | 역할 |
|------|------|
| `bootstrap.ps1` | 메인 설치 (한 번 실행) |
| `g2-worktree.ps1` | worktree 헬퍼 함수 (PROFILE에 등록됨) |
| `add-posthog.ps1` | 프로젝트에 PostHog 주입 |
| `posthog-snippet.html` | 비-Node 프로젝트용 웹 스니펫 |

---

## ⚠️ 검증 상태 (정직성)

- 이 스크립트들은 **Linux 원격 환경에서 작성**돼 PowerShell **실행 테스트는 못 했다**(해당 환경에 pwsh 없음). 문법·로직·멱등성·보안(키 하드코딩 없음)은 검수 완료.
- **회장 첫 실행 시** `bootstrap.ps1`이 정상 동작하는지, `wtnew`로 worktree 1회, `add-posthog`로 테스트 프로젝트 1회 확인 후 이상 있으면 알려주시면 즉시 수정.
</content>
