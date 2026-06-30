# bootstrap.ps1 — 노트북 켜고 한 번만 실행하면 "Claude App Factory"의 빠진 조각이 적용된다.
# 적용 대상:
#   1) git worktree 헬퍼(Conductor 대체) → PowerShell $PROFILE에 등록 → 새 터미널마다 자동 로드
#   2) PostHog 주입 스크립트 → $HOME\.g2\ 에 비치 (프로젝트에서 키와 함께 1회 실행)
#
# 실행:
#   pwsh -File bootstrap.ps1        (또는 PowerShell에서  .\bootstrap.ps1)
# 멱등(idempotent): 여러 번 돌려도 안전. $PROFILE 중복 등록 안 함.

$ErrorActionPreference = 'Stop'
Write-Host "=== G2 Claude App Factory — bootstrap ===" -ForegroundColor Cyan

# 1) 사전 도구 확인 (없으면 경고만, 중단 안 함)
foreach ($t in 'git','node','claude') {
    $ok = Get-Command $t -ErrorAction SilentlyContinue
    $tag = if ($ok) { 'OK     ' } else { 'MISSING' }
    $col = if ($ok) { 'Green' } else { 'Yellow' }
    Write-Host ("  [{0}] {1}" -f $tag, $t) -ForegroundColor $col
}

# 2) ~/.g2 에 스크립트 비치
$dest = Join-Path $HOME '.g2'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($f in 'g2-worktree.ps1','add-posthog.ps1','posthog-snippet.html') {
    Copy-Item (Join-Path $PSScriptRoot $f) $dest -Force
}
Write-Host "  스크립트 비치: $dest" -ForegroundColor Green

# 3) $PROFILE 에 worktree 헬퍼 dot-source 등록 (새 셸마다 자동 로드 = "켜면 바로 적용")
$wt = Join-Path $dest 'g2-worktree.ps1'
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
$already = Select-String -Path $PROFILE -SimpleMatch 'g2-worktree.ps1' -Quiet -ErrorAction SilentlyContinue
if (-not $already) {
    Add-Content -Path $PROFILE -Value "`n# G2 Claude App Factory — worktree 헬퍼 (Conductor 대체)`n. `"$wt`""
    Write-Host "  PROFILE 등록 완료: $PROFILE" -ForegroundColor Green
} else {
    Write-Host "  PROFILE 이미 등록됨 (건너뜀)" -ForegroundColor DarkGray
}

# 4) 지금 이 세션에서도 즉시 로드
$env:G2_WT_QUIET = '1'
. $wt

Write-Host ""
Write-Host "✅ 완료. 지금부터 (그리고 새 터미널에서) 사용 가능:" -ForegroundColor Green
Write-Host "   wtnew <이름> [-Open]   격리 worktree 생성 (병렬 작업)"
Write-Host "   wtls                   worktree 목록"
Write-Host "   wtmerge <이름>         브랜치 머지 + worktree 정리"
Write-Host "   wtrm <이름>            worktree 제거"
Write-Host ""
Write-Host "📊 PostHog는 프로젝트마다 키와 함께 1회 실행:" -ForegroundColor Cyan
Write-Host "   & `"$dest\add-posthog.ps1`" -ProjectPath <앱경로> -ApiKey phc_xxx"
