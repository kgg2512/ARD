# install.ps1 — Universal Git Sync를 글로벌 훅으로 등록 (모든 레포 적용)
# SessionStart: trunk 자동 동기화 / Stop: 미푸시 경고. 한 번 실행하면 회장의 모든 레포 세션에 적용.
# 멱등. 안전: 기존 settings.json 백업 후 병합, 중복 등록 안 함.

$ErrorActionPreference = 'Stop'
Write-Host "=== Universal Git Sync 설치 ===" -ForegroundColor Cyan

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')   # <ARD>
$src      = Join-Path $repoRoot 'git-sync\git_sync.py'
$hooksDir = Join-Path $HOME '.claude\hooks'
$dest     = Join-Path $hooksDir 'git_sync.py'

$py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command py -ErrorAction SilentlyContinue)
if (-not $py) { Write-Host "[MISSING] python" -ForegroundColor Yellow; return }
$pyExe = $py.Source

New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
Copy-Item $src $dest -Force
Write-Host "  훅 스크립트 비치: $dest" -ForegroundColor Green

$settings = Join-Path $HOME '.claude\settings.json'
$startCmd = "`"$pyExe`" `"$dest`" --mode start"
$stopCmd  = "`"$pyExe`" `"$dest`" --mode stop"

try {
    if (Test-Path $settings) { Copy-Item $settings "$settings.bak" -Force }
    $cfg = if (Test-Path $settings) { Get-Content $settings -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    if (-not $cfg.hooks) { $cfg | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{}) -Force }

    foreach ($evt in @(@{name='SessionStart'; cmd=$startCmd}, @{name='Stop'; cmd=$stopCmd})) {
        if (-not $cfg.hooks.($evt.name)) {
            $cfg.hooks | Add-Member -NotePropertyName $evt.name -NotePropertyValue @() -Force
        }
        $exists = ($cfg.hooks.($evt.name) | ConvertTo-Json -Depth 10) -match 'git_sync'
        if (-not $exists) {
            $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $evt.cmd }) }
            $cfg.hooks.($evt.name) = @($cfg.hooks.($evt.name)) + $entry
            Write-Host "  ✅ $($evt.name) 훅 등록" -ForegroundColor Green
        } else {
            Write-Host "  $($evt.name) 훅 이미 등록됨" -ForegroundColor DarkGray
        }
    }
    ($cfg | ConvertTo-Json -Depth 12) | Set-Content $settings -Encoding UTF8
    Write-Host "  settings.json 저장(백업 .bak)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ settings.json 병합 실패. 수동 등록:" -ForegroundColor Yellow
    Write-Host "     SessionStart: $startCmd" -ForegroundColor Yellow
    Write-Host "     Stop: $stopCmd" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ 완료. 이제 모든 레포에서 세션 시작 시 trunk(master) 자동 동기화," -ForegroundColor Green
Write-Host "   종료 시 미푸시 경고가 뜹니다. 원격·로컬 단절 끝." -ForegroundColor Green
