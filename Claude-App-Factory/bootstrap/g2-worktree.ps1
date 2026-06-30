# g2-worktree.ps1 — Conductor 대체 (Windows)
# Conductor(Mac 전용)가 하는 일 = 여러 Claude 에이전트를 격리된 repo 복사본에서 병렬 구동.
# 그 본질은 git worktree. 이 모듈은 worktree를 한 줄 명령으로 다루게 해준다.
# bootstrap.ps1이 이 파일을 $HOME\.g2\에 복사하고 PowerShell $PROFILE에 dot-source 등록 →
# 노트북 켜고 새 터미널 열면 아래 함수가 바로 쓰인다.

function New-AgentWorktree {
    <#
    .SYNOPSIS  현재 repo의 격리 복사본(worktree)을 새 브랜치로 생성. (Conductor의 "새 에이전트 워크스페이스")
    .EXAMPLE   wtnew featureA              # ../<repo>-featureA 에 featureA 브랜치 worktree 생성
    .EXAMPLE   wtnew bugfix -Open          # 생성 + 새 터미널에서 claude 자동 실행
    #>
    param(
        [Parameter(Mandatory)][string]$Name,
        [string]$Branch = "",
        [switch]$Open
    )
    if (-not $Branch) { $Branch = $Name }
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { Write-Error "git repo 안에서 실행하세요."; return }
    $repoName = Split-Path $root -Leaf
    $parent   = Split-Path $root -Parent
    $path     = Join-Path $parent "$repoName-$Name"
    if (Test-Path $path) { Write-Error "이미 존재: $path"; return }

    # 브랜치가 이미 있으면 그걸 체크아웃, 없으면 새로 만든다
    $exists = (git branch --list $Branch)
    if ($exists) { git worktree add $path $Branch }
    else         { git worktree add -b $Branch $path }
    if ($LASTEXITCODE -ne 0) { Write-Error "worktree 생성 실패"; return }

    Write-Host "✅ worktree: $path  (branch: $Branch)" -ForegroundColor Green
    if ($Open) {
        # 새 PowerShell 창에서 해당 폴더로 이동 후 claude 실행 (동시 작업)
        Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location '$path'; claude"
    } else {
        Write-Host "   이동:  cd `"$path`"   그 후  claude  실행" -ForegroundColor DarkGray
    }
}

function Get-AgentWorktrees {
    <# .SYNOPSIS  현재 repo의 모든 worktree 목록 #>
    git worktree list
}

function Merge-AgentWorktree {
    <#
    .SYNOPSIS  worktree 브랜치를 현재 브랜치에 머지하고 worktree 정리. (Alpha 단일 통합 게이트)
    .EXAMPLE   wtmerge featureA
    #>
    param([Parameter(Mandatory)][string]$Name)
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { Write-Error "git repo 안에서 실행하세요."; return }
    $repoName = Split-Path $root -Leaf
    $parent   = Split-Path $root -Parent
    $path     = Join-Path $parent "$repoName-$Name"
    $branch   = $Name
    Write-Host "머지: $branch → 현재 브랜치" -ForegroundColor Cyan
    git merge $branch
    if ($LASTEXITCODE -ne 0) { Write-Error "머지 충돌 — 수동 해결 후 worktree는 직접 정리하세요."; return }
    if (Test-Path $path) { git worktree remove $path }
    Write-Host "✅ 머지 완료 + worktree 정리: $path" -ForegroundColor Green
}

function Remove-AgentWorktree {
    <# .SYNOPSIS  머지 없이 worktree만 제거. .EXAMPLE  wtrm featureA #>
    param([Parameter(Mandatory)][string]$Name, [switch]$Force)
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { Write-Error "git repo 안에서 실행하세요."; return }
    $repoName = Split-Path $root -Leaf
    $parent   = Split-Path $root -Parent
    $path     = Join-Path $parent "$repoName-$Name"
    if ($Force) { git worktree remove --force $path } else { git worktree remove $path }
    if ($LASTEXITCODE -eq 0) { Write-Host "✅ 제거: $path" -ForegroundColor Green }
}

# 짧은 별칭 (Conductor 버튼 대신 한 단어)
Set-Alias wtnew   New-AgentWorktree
Set-Alias wtls    Get-AgentWorktrees
Set-Alias wtmerge Merge-AgentWorktree
Set-Alias wtrm    Remove-AgentWorktree

# 로드 확인용
if ($env:G2_WT_QUIET -ne '1') {
    Write-Host "[G2] worktree helpers 로드됨: wtnew / wtls / wtmerge / wtrm" -ForegroundColor DarkGray
}
