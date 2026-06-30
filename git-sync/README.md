# Universal Git Sync — 원격·로컬 단일 브랜치 동기화

> 회장 지시(2026-06-30): 원격(폰/클라우드 클로드코드)과 로컬(노트북 클로드코드)이 **항상 같은 브랜치**를 쓰게 하라. ARD뿐 아니라 **모든 레포·모든 코딩**에 동일 적용.

## 문제

GitHub이 원격↔로컬의 **유일한 다리**다. 그런데 원격 세션은 세션 브랜치(`claude/...`)에 push하고 로컬은 `master`에 있어서, 양쪽이 **다른 브랜치를 보면 다리가 끊긴다.** → "로컬 클로드가 오늘 아침 작업을 못 본다."

## 원칙 — Trunk 단일화

1. **Trunk = origin 기본 브랜치(보통 `master`, saju-paljja만 `main`).** 모든 영구 작업의 단일 진실.
2. **세션 시작:** trunk를 **자동 fetch + ff-only pull**(클린 트리에서만) → 항상 최신에서 시작.
3. **세션 종료:** 미푸시 커밋 **경고** → push 하고 끝내라(안 하면 다른 기기에서 못 봄).
4. **원격 세션이 피처 브랜치에 갇히면:** 작업을 **trunk로 수렴(merge)** 시킨 뒤 끝낸다. 로컬은 `git pull origin <trunk>`만 하면 전부 본다.

## 안전 원칙 (CSO — 절대)

- **force 금지 · 더티 트리 자동 머지 금지 · 블라인드 auto-push 금지.** (회장이 과거 auto-push를 쓰레기 푸시 때문에 제거한 이력 존중.)
- 자동화는 **읽기 위주(fetch) + 클린 트리 ff-only pull**만. 위험하면 손대지 않고 **알림만** 띄운다.

## 설치 (회장 1회 — 글로벌, 모든 레포 적용)

```powershell
cd <ARD>\git-sync\install
pwsh -File install.ps1
```
→ `~/.claude/hooks/git_sync.py` 비치 + `settings.json`에 SessionStart(동기화)·Stop(미푸시 경고) 글로벌 훅 등록. 이후 **어느 레포에서 세션을 열든** 자동 적용.

## 동작

| 시점 | 동작 |
|------|------|
| SessionStart | `git fetch` → trunk면 ff-only pull(클린 시), 다른 브랜치면 "trunk로 수렴하라" 안내 + 뒤짐 커밋 수 |
| Stop | 업스트림 대비 미푸시 커밋 N개 경고 |

## 파일
| 파일 | 역할 |
|------|------|
| `git_sync.py` | 훅 본체(--mode start/stop). 크로스플랫폼(py). |
| `install/install.ps1` | 글로벌 훅 등록(멱등·백업) |

## 검증 상태
- `py_compile` 통과 + **이 레포(원격, 피처 브랜치)에서 라이브 실행** → "현재 브랜치 ≠ trunk master, master로 수렴하라" 정확 탐지 [확인].
- 회장 로컬 설치 후 새 세션 1회로 "⬇️ master 동기화됨" 또는 안내가 뜨는지 확인 권장.
</content>
